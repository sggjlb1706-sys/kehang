"""Fixed JDK protocol tests, distinct from real compiler records."""
from copy import deepcopy
from datetime import datetime, timezone
import unittest
from campuslab.java_course import make_task, validate_spec, analyze, compare_identity, collect
from campuslab.rules import seal


def evidence():
    spec=make_task(); home=r'C:\CourseJDK'
    tools={name:dict(path=home+'\\bin\\'+name+'.exe',sha256=('A' if name=='java' else 'B')*64,exists=True,version='21.0.9',home=home,returncode=0,error='') for name in ('java','javac')}
    return spec,dict(schema=1,task_id=spec['id'],collected_at=datetime.now(timezone.utc).isoformat(),
        target=dict(requested=home,actual=home,exists=True),facts=dict(os='Windows',tools=tools,
        compile=dict(returncode=0,stdout='',error=''),run=dict(returncode=0,stdout='42\n'+home+'\n',error='',home=home)))


class JavaCourseTest(unittest.TestCase):
    def test_complete_fixed_compile_and_run(self):
        spec,r=evidence();self.assertTrue(analyze(spec,r)['passed'])
        spec['verify']='anything';
        with self.assertRaises(ValueError):validate_spec(seal(spec))

    def test_java_and_javac_must_belong_to_selected_home(self):
        for tool in ('java','javac'):
            spec,r=evidence();r['facts']['tools'][tool]['home']=r'C:\OtherJDK'
            self.assertFalse(analyze(spec,r)['passed'])
            spec,r=evidence();r['facts']['tools'][tool]['path']='C:\\OtherJDK\\bin\\'+tool+'.exe'
            with self.assertRaises(ValueError):analyze(spec,r)

    def test_versions_compiler_and_runtime_are_independent(self):
        spec,r=evidence();r['facts']['tools']['javac']['version']='17.0.9'
        self.assertFalse(analyze(spec,r)['passed'])
        spec,r=evidence();r['facts']['compile'].update(returncode=1,error='compile failed');r['facts']['run'].update(returncode=None,stdout='',home=None)
        self.assertEqual({c['id']:c['status'] for c in analyze(spec,r)['checks']}['java:compile'],'mismatch')
        spec,r=evidence();r['facts']['run']['stdout']='looks done'
        self.assertFalse(analyze(spec,r)['passed'])

    def test_retest_rejects_other_jdk_or_binary(self):
        _,a=evidence()
        for change in [lambda r:r['target'].update(requested=r'C:\OtherJDK'),lambda r:r['facts']['tools']['javac'].update(sha256='C'*64)]:
            b=deepcopy(a);change(b)
            with self.assertRaises(ValueError):compare_identity(a,b)

    def test_missing_target_never_uses_path_compiler(self):
        spec=make_task();r=collect(spec,r'C:\CampusLab-MissingJDK')
        self.assertFalse(analyze(spec,r)['passed'])
        self.assertIsNone(r['facts']['run']['returncode'])
        self.assertEqual(r['commands'],[])

    def test_incomplete_or_wrong_types_rejected(self):
        for change in [lambda r:r['facts']['tools'].pop('javac'),lambda r:r['facts']['compile'].update(returncode=False),
                       lambda r:r.update(task_id='other'),lambda r:r.update(collected_at='2026-11-09'),lambda r:r['target'].update(actual=None)]:
            spec,r=evidence();change(r)
            with self.assertRaises(ValueError):analyze(spec,r)


if __name__=='__main__':unittest.main()
