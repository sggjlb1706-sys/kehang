from copy import deepcopy
from io import BytesIO
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from campuslab.courses import CourseStore
from campuslab.guidance import plan
from campuslab.portable import export_package, import_package
from campuslab.rules import task, analyze, compare
from campuslab.web import AppServer
from test_rules import evidence
import test_web


class CourseFlowTest(unittest.TestCase):
    setUpClass=classmethod(test_web.WebTest.setUpClass.__func__)
    tearDownClass=classmethod(test_web.WebTest.tearDownClass.__func__)
    request=test_web.WebTest.request
    def test_text_error_without_report_is_explicitly_unknown(self):
        result=json.load(self.request('/api/preview',dict(error='ModuleNotFoundError sk-abcdefghijklmnop')))
        self.assertIn('没有检测证据',result['preview'])
        self.assertNotIn('sk-abcdefghijklmnop',result['preview'])
        self.assertEqual(json.loads(result['preview'])['checks'],[])
        with self.assertRaises(Exception):self.request('/api/diagnose',dict(preview=result['preview'],consent=False))

    def test_portable_independent_store_and_tools(self):
        for scenario in ('python-basics','node-basics','pytorch-cpu','pytorch-gpu','vm-linux','local-qwen'):
            spec=task(scenario,title='跨实例 '+scenario)
            package=json.load(self.request('/api/package',dict(task=spec)))
            with tempfile.TemporaryDirectory() as temp:
                store=CourseStore(Path(temp)/'other.sqlite')
                result=store.publish(import_package(package))
                self.assertEqual(store.get(result['code']),spec)
            result=json.load(self.request('/api/import-course',dict(package=package)))
            self.assertEqual(result['task'],spec)
            with zipfile.ZipFile(BytesIO(self.request('/api/tool?course='+result['code']).read())) as archive:
                self.assertEqual(json.loads(archive.read('task.json')),spec)
                self.assertIn('campuslab/preparation.py',archive.namelist())
                if scenario=='vm-linux':self.assertIn('guest_probe.py',archive.namelist())
            guide=self.request('/api/guide',dict(task=spec)).read().decode('utf-8')
            self.assertIn(spec['id'],guide)

    def test_guidance_uses_actual_differences_and_explicit_target(self):
        report=evidence();report['target']['requested']=report['target']['actual']='C:\\Course O\'Brien $x\\python.exe'
        report['facts']['packages']['requests']=None
        actions=plan(task(),report=report)['remediation']
        self.assertEqual(actions[0]['status'],'missing')
        self.assertIn('Course O\'Brien `$x',actions[0]['body'])
        self.assertIn('-m pip',actions[0]['body'])
        self.assertFalse(analyze(task(),report)['passed'])

    def test_report_share_redacts_nested_values_and_is_not_raw_report(self):
        report=evidence();report['facts']['verification']['error']='password=secret1 user@example.com'
        value=json.load(self.request('/api/share',dict(task=task(),report=report)))
        self.assertTrue(value['share_only'])
        self.assertNotIn('secret1',json.dumps(value));self.assertNotIn('user@example.com',json.dumps(value))
        with self.assertRaises(ValueError):analyze(task(),value)


if __name__=='__main__':unittest.main()
