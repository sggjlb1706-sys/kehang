"""Educates derivative mapping tests; no terminal or remote verifier."""
import unittest
from campuslab.teaching import lesson_checks, validate_action


class TeachingTests(unittest.TestCase):
    def test_fixed_check_mapping_and_four_states(self):
        result=dict(task_id='a'*64,checks=[dict(id='dsh:software',status='missing',observed=None,requirement='fixed'),
                                         dict(id='dsh:tools',status='unknown',observed=None,requirement='fixed')])
        items=lesson_checks(result)
        self.assertEqual([a['status'] for a in items],['missing','unknown'])
        self.assertEqual(items[0]['action'],'manual-recollect')
        self.assertFalse(items[0]['success'])
        self.assertEqual(items[0]['task_id'],'a'*64)

    def test_rejects_arbitrary_action_fields(self):
        for bad in [dict(name='shell.run',title='x',description='x',cooldown=3),
                    dict(name='dsh:software',title='x',description='x',cooldown=3,args=['evil']),
                    dict(name='dsh:software',title='x',description='x',cooldown=-1)]:
            with self.subTest(bad=bad),self.assertRaises(ValueError):validate_action(bad)

    def test_unknown_check_never_becomes_executable(self):
        with self.assertRaises(ValueError):lesson_checks(dict(task_id='a'*64,checks=[dict(id='arbitrary',status='pass')]))
