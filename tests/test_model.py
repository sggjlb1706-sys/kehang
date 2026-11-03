from copy import deepcopy
from datetime import datetime, timedelta, timezone
import unittest
from campuslab.rules import MODEL_SHA,analyze,compare,task
from test_rules import evidence


def model_evidence():
    spec=task('local-qwen'); report=evidence(spec)
    report['facts']['packages']={'torch':'2.14.0+cu126','transformers':'4.57.1'}
    report['model']=dict(directory='D:\\Models\\Qwen',weights_sha256=MODEL_SHA,
                         inference=dict(offline=True,local=True,output='2',ended_with_eos=True,device='cuda',error=''))
    return report


class ModelTest(unittest.TestCase):
    def test_fixed_full_report(self):
        self.assertTrue(analyze(task('local-qwen'),model_evidence())['passed'])

    def test_not_run_is_unknown(self):
        r=model_evidence(); r['model']['inference']=None
        result=analyze(task('local-qwen'),r)
        self.assertFalse(result['passed']); self.assertEqual(result['checks'][-1]['status'],'unknown')

    def test_cloud_wrong_answer_wrong_weights_never_pass(self):
        for name,value in [('offline',False),('local',False),('output','3'),('ended_with_eos',False),('error','OutOfMemory')]:
            r=model_evidence(); r['model']['inference'][name]=value
            self.assertFalse(analyze(task('local-qwen'),r)['passed'])
        r=model_evidence(); r['model']['weights_sha256']='0'*64
        self.assertFalse(analyze(task('local-qwen'),r)['passed'])

    def test_changed_model_directory_not_same_target(self):
        a=model_evidence(); b=deepcopy(a)
        b['collected_at']=(datetime.now(timezone.utc)+timedelta(seconds=1)).isoformat()
        b['model']['directory']='D:\\Other'
        with self.assertRaises(ValueError): compare(task('local-qwen'),a,b)


if __name__=='__main__': unittest.main()
