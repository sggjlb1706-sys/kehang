from copy import deepcopy
from io import BytesIO
import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import zipfile

from campuslab import practice
from campuslab.rules import task
from campuslab.web import AppServer


class PracticeTest(unittest.TestCase):
    def setUp(self):
        self.spec = practice.make_practice()
        self.good = practice.submission_template(self.spec)
        self.good['notebook'] = dict(rows=3, array_sum=42, group_totals={'A':30, 'B':12})
        self.good['sqlite'] = [['A',2,30],['B',1,12]]

    def test_fixed_components_and_portable_content(self):
        self.assertEqual(self.spec['component_task_ids'], {
            'notebook':task('notebook-data')['id'], 'sqlite':task('sqlite-basics')['id']})
        package = practice.export_package(self.spec)
        self.assertEqual(practice.import_package(package), self.spec)
        for changed in ({}, {**package, 'commands':['run me']},
                        {**package, 'sha256':'0'*64}):
            with self.assertRaises(ValueError): practice.import_package(changed)
        changed = deepcopy(package)
        changed['practice']['expected']['notebook']['array_sum'] = 43
        with self.assertRaises(ValueError): practice.import_package(changed)
        changed = deepcopy(package); changed['schema'] = True
        with self.assertRaises(ValueError): practice.import_package(changed)
        changed = deepcopy(self.spec); changed['expected']['notebook']['rows'] = 3.0
        with self.assertRaises(ValueError): practice.validate_practice(changed)

    def test_result_states_and_scope(self):
        for value in (None, {}):
            self.assertEqual(practice.check(self.spec,value)['status'],'missing')
        self.assertEqual(practice.check(self.spec,[])['status'],'invalid')
        self.assertEqual(practice.check(self.spec,practice.submission_template(self.spec))['status'],'missing')
        wrong = deepcopy(self.good); wrong['notebook']['array_sum'] = 43
        result = practice.check(self.spec,wrong)
        self.assertEqual(result['status'],'mismatch')
        self.assertEqual(result['components']['sqlite']['status'],'pass')
        self.assertFalse(result['passed'])
        result = practice.check(self.spec,self.good)
        self.assertTrue(result['passed'])
        self.assertEqual(result['status'],'pass')
        self.assertIn('原创',result['scope'])
        self.assertNotIn('environment_passed',result)

    def test_result_does_not_echo_unrecognized_group_names(self):
        sample = deepcopy(self.good)
        sample['notebook']['group_totals']['PRIVATE-GROUP-TEST'] = 5
        sample['sqlite'][0][0] = 'PRIVATE-GROUP-TEST'
        result = practice.check(self.spec, sample)
        self.assertEqual(result['status'], 'mismatch')
        self.assertNotIn('PRIVATE-GROUP-TEST', json.dumps(result))

    def test_stale_task_material_and_tampered_data_distinguished(self):
        for key,value in [('practice_id','0'*64),('material_version','2025-v0'),
                          ('dataset_sha256','0'*64),('component_task_ids',{'notebook':'0'*64,'sqlite':'0'*64})]:
            changed = deepcopy(self.good); changed[key] = value
            self.assertEqual(practice.check(self.spec,changed)['status'],'obsolete',key)
        for key,value in [('schema',True),('notebook',{'rows':True,'array_sum':42,'group_totals':{'A':30,'B':12}}),
                          ('sqlite',[['A',True,30],['B',1,12]]),('unexpected','python evil.py')]:
            changed = deepcopy(self.good); changed[key] = value
            self.assertEqual(practice.check(self.spec,changed)['status'],'invalid',key)

    def test_material_zip_has_complete_fixed_data_and_editable_templates(self):
        with zipfile.ZipFile(BytesIO(practice.materials_zip(self.spec))) as z:
            self.assertIsNone(z.testzip())
            self.assertEqual(set(z.namelist()),{'课堂资料包.json','README.md','scores.csv',
                '01_Notebook练习.ipynb','02_SQLite练习.py','成果模板.json'})
            self.assertEqual(z.read('scores.csv').decode(),practice.CSV)
            self.assertEqual(practice.import_package(json.loads(z.read('课堂资料包.json'))),self.spec)
            notebook = json.loads(z.read('01_Notebook练习.ipynb'))
            self.assertEqual(notebook['nbformat'],4)
            self.assertIn('TODO',str(notebook))
            guide = z.read('README.md').decode()
            for phrase in ('kernel.json','scores.sqlite','首次错误','实际操作','原创','同一电脑'):
                self.assertIn(phrase,guide)


class PracticeWebTest(unittest.TestCase):
    def test_two_local_libraries_publish_import_and_reject_old_results(self):
        with tempfile.TemporaryDirectory(prefix='课航 实训 ') as temp:
            servers = [AppServer(0,Path(temp)/str(i)/'courses.sqlite') for i in range(2)]
            threads = [threading.Thread(target=s.serve_forever,daemon=True) for s in servers]
            for thread in threads: thread.start()
            def request(i,path,body=None):
                raw=json.dumps(body).encode() if body is not None else None
                headers={'Content-Type':'application/json'} if raw else {}
                return urlopen(Request(f'http://127.0.0.1:{servers[i].server_port}'+path,data=raw,headers=headers),timeout=5)
            try:
                initial=json.load(request(0,'/api/practice'))
                teacher=json.load(request(0,'/api/practice/publish',{}))
                learner=json.load(request(1,'/api/practice/import',{'package':teacher['package']}))
                self.assertEqual(initial['practice'],learner['practice'])
                self.assertEqual(teacher['practice'],learner['practice'])
                for key,scenario in [('notebook','notebook-data'),('sqlite','sqlite-basics')]:
                    self.assertEqual(teacher['courses'][key]['task'],task(scenario))
                    self.assertEqual(json.load(request(1,'/api/course/'+learner['courses'][key]['code'])),task(scenario))
                with zipfile.ZipFile(BytesIO(request(1,'/api/practice/materials').read())) as z:
                    self.assertIsNone(z.testzip())
                response=json.load(request(1,'/api/practice/check',{'practice':learner['practice'],'submission':None}))
                self.assertEqual(response['status'],'missing')
                self.assertIn('checked_at',response)
                bad=deepcopy(teacher['package']);bad['practice']['title']='tampered'
                with self.assertRaises(HTTPError):request(1,'/api/practice/import',{'package':bad})
            finally:
                for server in servers:server.shutdown();server.server_close()
                for thread in threads:thread.join()


if __name__ == '__main__':unittest.main()
