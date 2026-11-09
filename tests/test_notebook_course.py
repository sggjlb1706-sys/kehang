"""Constructed notebook protocol tests; real runs are recorded separately."""
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from campuslab.notebook_course import make_task, validate_spec, analyze, collect, compare_identity
from campuslab.rules import seal


def evidence():
    spec = make_task()
    report = dict(schema=1, task_id=spec['id'], collected_at=datetime.now(timezone.utc).isoformat(),
        target=dict(requested=r'C:\Course\python.exe', actual=r'C:\Course\python.exe', exists=True),
        facts=dict(os='Windows', python='3.13.9',
            dependencies={name: dict(installed=True, version=value, error='') for name, value in [('jupyter_client','8.6.3'),('ipykernel','6.30.1')]},
            kernel=dict(spec_path=r'C:\Course\kernel.json', exists=True, spec_sha256='A'*64,
                argv=[r'C:\Course\python.exe','-m','ipykernel_launcher','-f','{connection_file}'],
                validated=True, started=True, actual=r'C:\Course\python.exe', python='3.13.9', error=''),
            packages={name:dict(installed=True, version=value, imported=True, path=rf'C:\Course\Lib\site-packages\{name}\__init__.py',error='') for name,value in [('numpy','2.3.4'),('pandas','3.0.3')]},
            run=dict(returncode=0, result=dict(array_sum=42, group_totals={'A':30,'B':12},rows=3), stdout='CAMPUSLAB_RESULT', error='', executed_at=datetime.now(timezone.utc).isoformat()),
            cleanup=dict(kernel_stopped=True,channels_stopped=True,error='')))
    return spec, report


class NotebookCourseTest(unittest.TestCase):
    def test_complete_fixed_kernel_and_data_pass(self):
        spec, report=evidence()
        self.assertTrue(analyze(spec,report)['passed'])
        changed=deepcopy(spec);changed['verify']='user-notebook'
        with self.assertRaises(ValueError):validate_spec(seal(changed))

    def test_normal_python_or_wrong_kernel_cannot_pass(self):
        for change in [lambda r:r['facts']['kernel'].update(actual=r'C:\Other\python.exe'),
                       lambda r:r['facts']['kernel'].update(started=False),
                       lambda r:r['facts']['run'].update(returncode=1,error='cell failed'),
                       lambda r:r['facts']['run'].update(result={'array_sum':0,'group_totals':{},'rows':3})]:
            spec,r=evidence();change(r)
            self.assertFalse(analyze(spec,r)['passed'])

    def test_dependency_missing_and_wrong_version(self):
        spec,r=evidence();r['facts']['packages']['pandas'].update(installed=False,version=None,imported=False,path=None,error='missing')
        r['facts']['run'].update(returncode=1,result=None,error='ModuleNotFoundError')
        self.assertEqual({c['id']:c['status'] for c in analyze(spec,r)['checks']}['package:pandas'],'missing')
        spec,r=evidence();r['facts']['packages']['numpy']['version']='1.20.0'
        self.assertEqual({c['id']:c['status'] for c in analyze(spec,r)['checks']}['package:numpy'],'mismatch')
        spec,r=evidence();r['facts']['dependencies']['jupyter_client']['error']='import failed'
        self.assertFalse(analyze(spec,r)['passed'])

    def test_partial_types_unknown_and_task_rejected(self):
        for change in [lambda r:r['facts'].pop('kernel'),lambda r:r['facts']['kernel'].update(started='yes'),
                       lambda r:r['facts']['run'].update(returncode=False),lambda r:r.update(task_id='other'),
                       lambda r:r.update(collected_at='2026-11-09T10:00:00'),
                       lambda r:r['facts']['run'].update(result={'array_sum':True,'group_totals':{'A':30,'B':12},'rows':3})]:
            spec,r=evidence();change(r)
            with self.assertRaises(ValueError):analyze(spec,r)

    def test_retest_binds_interpreter_kernel_path_hash_and_argv(self):
        _,a=evidence()
        for change in [lambda r:r['target'].update(requested=r'C:\Other\python.exe'),
                       lambda r:r['facts']['kernel'].update(spec_path=r'C:\Other\kernel.json'),
                       lambda r:r['facts']['kernel'].update(spec_sha256='B'*64),
                       lambda r:r['facts']['kernel'].update(actual=r'C:\Other\python.exe')]:
            b=deepcopy(a);change(b)
            with self.assertRaises(ValueError):compare_identity(a,b)

    def test_missing_target_and_missing_spec_do_not_pass(self):
        result=analyze(make_task(),collect(make_task(),r'C:\CampusLab-Missing\python.exe',r'C:\CampusLab-Missing\kernel.json'))
        self.assertFalse(result['passed'])
        self.assertIn('missing',[c['status'] for c in result['checks']])

    def test_unreviewed_kernelspec_is_not_executed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'kernel.json';path.write_text('{"argv":["cmd.exe","/c","echo bad"],"language":"python"}',encoding='utf-8')
            from campuslab.notebook_course import inspect_kernel
            self.assertFalse(inspect_kernel(str(path),r'C:\Course\python.exe')['validated'])
            path.write_text('{"argv":["C:\\\\Course\\\\python.exe","-m","ipykernel_launcher","-f","{connection_file}"],"env":{"PYTHONSTARTUP":"bad.py"},"language":"python"}',encoding='utf-8')
            self.assertFalse(inspect_kernel(str(path),r'C:\Course\python.exe')['validated'])


if __name__=='__main__':unittest.main()
