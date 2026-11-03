from copy import deepcopy
from datetime import datetime, timedelta, timezone
import unittest
from campuslab.rules import analyze, compare, task


def evidence(spec=None):
    spec = spec or task()
    return dict(schema=1, task_id=spec['id'], collected_at=datetime.now(timezone.utc).isoformat(),
                target=dict(requested='C:\\Course\\python.exe', actual='C:\\Course\\python.exe', exists=True),
                facts=dict(os='Windows', python='3.13.9', packages={'requests':'2.32.5'},
                           verification=dict(returncode=0, stdout='OK\n', error='')))


class RulesTest(unittest.TestCase):
    def test_complete_pass(self):
        self.assertTrue(analyze(task(), evidence())['passed'])

    def test_missing_and_failure(self):
        a = evidence(); a['facts']['packages']['requests'] = None
        a['facts']['verification'].update(returncode=1, stdout='', error='ModuleNotFoundError')
        states = [x['status'] for x in analyze(task(), a)['checks']]
        self.assertEqual(states, ['pass', 'pass', 'missing', 'mismatch'])

    def test_unknown_never_pass(self):
        a = evidence(); a['target'].update(actual=None, exists=False)
        a['facts'].update(python=None, packages={'requests':None}, verification=dict(returncode=None,stdout='',error='missing'))
        self.assertFalse(analyze(task(), a)['passed'])
        self.assertEqual([x['status'] for x in analyze(task(), a)['checks']], ['pass','missing','unknown','unknown'])

    def test_identity_and_incomplete_rejected(self):
        for mutate in (lambda a:a['target'].update(actual='C:\\Other\\python.exe'),
                       lambda a:a['target'].update(requested='python'),
                       lambda a:a['facts'].pop('verification'),
                       lambda a:a['facts']['packages'].clear(),
                       lambda a:a.update(task_id='wrong'),
                       lambda a:a.update(collected_at='2026-11-03T01:00:00'),
                       lambda a:a['facts']['verification'].update(returncode=False),
                       lambda a:a['target'].update(actual=None)):
            with self.subTest(mutate=mutate):
                a=evidence(); mutate(a)
                with self.assertRaises(ValueError): analyze(task(), a)

    def test_task_changes_rejected(self):
        a=task(); a['python']['min']='3.14'
        with self.assertRaises(ValueError): analyze(a, evidence())
        with self.assertRaises(ValueError): task('nodejs')
        with self.assertRaises(ValueError): task(python_min='3.14',python_max='3.13')

    def test_real_state_comparison_contract(self):
        a=evidence(); b=deepcopy(a)
        b['collected_at']=(datetime.now(timezone.utc)+timedelta(seconds=1)).isoformat()
        self.assertEqual(compare(task(),a,b)['outcome'],'stable-pass')
        a['facts']['packages']['requests']=None
        a['facts']['verification'].update(returncode=1, stdout='')
        self.assertEqual(compare(task(),a,b)['outcome'],'repaired')
        b['target'].update(requested='C:\\Else\\python.exe', actual='C:\\Else\\python.exe')
        with self.assertRaises(ValueError): compare(task(),a,b)

    def test_incorrect_stdout_not_success(self):
        a=evidence(); a['facts']['verification']['stdout']='looks fine'
        self.assertFalse(analyze(task(),a)['passed'])

    def test_incompatible_versions(self):
        a=evidence(); a['facts']['python']='3.9.9'
        self.assertEqual(analyze(task(),a)['checks'][1]['status'],'mismatch')


if __name__ == '__main__': unittest.main()
