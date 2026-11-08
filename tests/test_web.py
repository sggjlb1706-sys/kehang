from io import BytesIO
import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import zipfile

from campuslab.web import AppServer
from test_rules import evidence


class WebTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.app=AppServer(0,Path(cls.temp.name)/'courses.sqlite')
        cls.thread=threading.Thread(target=cls.app.serve_forever,daemon=True); cls.thread.start()
        cls.base='http://127.0.0.1:'+str(cls.app.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.app.shutdown(); cls.app.server_close(); cls.thread.join(); cls.temp.cleanup()

    def request(self,path,body=None,headers=None):
        raw=json.dumps(body).encode() if body is not None else None
        return urlopen(Request(self.base+path,data=raw,headers=headers or ({'Content-Type':'application/json'} if raw else {})),timeout=5)

    def test_immutable_courses_and_shared_analysis(self):
        a=json.load(self.request('/api/course',dict(title='第一版',python_min='3.10')))
        b=json.load(self.request('/api/course',dict(title='第二版',python_min='3.14')))
        self.assertNotEqual(a['code'],b['code'])
        self.assertEqual(json.load(self.request('/api/course/'+a['code'])),a['task'])
        report=evidence(a['task'])
        self.assertTrue(json.load(self.request('/api/analyze',dict(task=a['task'],report=report)))['passed'])
        with self.assertRaises(HTTPError): self.request('/api/analyze',dict(task=b['task'],report=report))

    def test_unknown_goal_and_cross_origin_rejected(self):
        with self.assertRaises(HTTPError): self.request('/api/goal?goal=nodejs')
        with self.assertRaises(HTTPError): self.request('/api/course',{}, {'Content-Type':'application/json','Origin':'https://evil.invalid'})
        with self.assertRaises(HTTPError): self.request('/api/goal',headers={'Host':'evil.invalid'})

    def test_tool_has_only_explicit_source_and_snapshot(self):
        raw=self.request('/api/tool').read()
        with zipfile.ZipFile(BytesIO(raw)) as z:
            self.assertEqual(set(z.namelist()),{'campuslab/__init__.py','campuslab/collect.py','campuslab/probe.py','campuslab/rules.py','campuslab/preparation.py','task.json','README.txt'})
            self.assertEqual(z.testzip(),None)
        response=self.request('/')
        self.assertIn("script-src 'self'",response.headers['Content-Security-Policy'])
        self.assertNotIn('unsafe-inline',response.headers['Content-Security-Policy'])

    def test_no_execution_endpoint(self):
        with self.assertRaises(HTTPError) as caught: self.request('/api/execute',{'command':'test'})
        self.assertEqual(caught.exception.code,404)

    def test_node_tool_has_matching_target_example_and_snapshot(self):
        spec = json.load(self.request('/api/goal?goal=node-basics'))
        with zipfile.ZipFile(BytesIO(self.request('/api/tool?goal=node-basics').read())) as z:
            self.assertEqual(json.loads(z.read('task.json')), spec)
            self.assertTrue({'campuslab/node_collect.py','campuslab/node_probe.js'} <= set(z.namelist()))
            self.assertIn(r'--target "C:\CourseNode\node.exe"', z.read('README.txt').decode('utf-8'))
            self.assertNotIn(r'--target "C:\Course\python.exe"', z.read('README.txt').decode('utf-8'))


if __name__=='__main__': unittest.main()
