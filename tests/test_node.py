"""Constructed contract tests; these are not real-device evidence."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from campuslab.collect import collect
from campuslab.courses import CourseStore
from campuslab.rules import analyze, compare, task


def node_evidence(spec=None):
    spec = spec or task('node-basics')
    target = r'C:\CourseNode\node.exe'
    return dict(schema=1, task_id=spec['id'], collected_at=datetime.now(timezone.utc).isoformat(),
                target=dict(requested=target, actual=target, exists=True),
                facts=dict(os='Windows', node='24.21.0',
                           npm=dict(path=r'C:\CourseNode\node_modules\npm\bin\npm-cli.js',
                                    node=target, exists=True, version='11.19.0', returncode=0, error=''),
                           verification=dict(returncode=0, stdout='OK\n', error='')))


class NodeTest(unittest.TestCase):
    def test_shared_fixed_snapshot_and_immutable_course(self):
        spec = task('node-basics')
        self.assertIn('演示', spec['source'])
        self.assertEqual(spec, task('node-basics', python_min='9.0'))
        with tempfile.TemporaryDirectory() as folder:
            store = CourseStore(Path(folder)/'course.sqlite')
            course = store.publish(spec)
            self.assertEqual(spec, store.get(course['code']))
            self.assertTrue(analyze(store.get(course['code']), node_evidence())['passed'])
            changed = store.publish(task('node-basics', title='另一个快照'))
            self.assertEqual(spec, store.get(course['code']))
            with self.assertRaises(ValueError):
                analyze(store.get(changed['code']), node_evidence())

    def test_all_facts_and_four_states(self):
        spec = task('node-basics')
        self.assertTrue(analyze(spec, node_evidence())['passed'])
        for key, old, new in [('node','20.1.0','25.0.0'), ('npm','9.9.0','12.0.0')]:
            for value in (old, new):
                report = node_evidence()
                if key == 'node': report['facts']['node'] = value
                else: report['facts']['npm']['version'] = value
                result = analyze(spec, report)
                self.assertFalse(result['passed'])
                self.assertEqual(next(c['status'] for c in result['checks'] if c['id'] == key), 'mismatch')
        report = node_evidence()
        report['facts']['npm'].update(exists=False, node=None, version=None, returncode=None, error='CLI missing')
        self.assertEqual(analyze(spec, report)['checks'][2]['status'], 'missing')
        report['facts']['npm'].update(exists=True, node=report['target']['actual'], error='timed out')
        self.assertEqual(analyze(spec, report)['checks'][2]['status'], 'unknown')

    def test_missing_target_collects_complete_unknown_report(self):
        with tempfile.TemporaryDirectory() as folder:
            report = collect(task('node-basics'), str(Path(folder)/'missing-node.exe'))
        result = analyze(task('node-basics'), report)
        self.assertFalse(result['passed'])
        self.assertEqual([c['status'] for c in result['checks']], ['pass','missing','unknown','unknown'])
        self.assertTrue(report['facts']['verification']['error'])

    def test_incomplete_or_mixed_identity_rejected(self):
        mutations = [lambda r:r['target'].update(actual=r'C:\Other\node.exe'),
                     lambda r:r['facts']['npm'].update(node=r'C:\Other\node.exe'),
                     lambda r:r['facts']['npm'].update(path=r'C:\Other\node_modules\npm\bin\npm-cli.js'),
                     lambda r:r['facts'].pop('verification'),
                     lambda r:r['facts']['npm'].pop('exists'),
                     lambda r:r['facts']['npm'].update(returncode=False),
                     lambda r:r['facts']['npm'].update(exists='yes'),
                     lambda r:r['facts']['npm'].update(version=[]),
                     lambda r:r['target'].update(actual=None),
                     lambda r:r.update(collected_at='2026-11-08T00:00:00')]
        for mutation in mutations:
            report = node_evidence(); mutation(report)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                analyze(task('node-basics'), report)

    def test_partial_and_failed_results_cannot_pass(self):
        for mutation in [lambda r:r['facts'].update(node=None),
                         lambda r:r['facts'].update(node='24.0.0-nightly'),
                         lambda r:r['facts']['npm'].update(version=None),
                         lambda r:r['facts']['npm'].update(version='11.0.0-beta'),
                         lambda r:r['facts']['npm'].update(returncode=1),
                         lambda r:r['facts']['npm'].update(error='execution error'),
                         lambda r:r['facts']['verification'].update(error='runtime error'),
                         lambda r:r['facts']['verification'].update(returncode=None),
                         lambda r:r['facts']['verification'].update(stdout='looks good')]:
            report = node_evidence(); mutation(report)
            with self.subTest(mutation=mutation):
                self.assertFalse(analyze(task('node-basics'), report)['passed'])

    def test_retest_requires_snapshot_target_and_later_time(self):
        spec = task('node-basics'); before = node_evidence(); after = deepcopy(before)
        with self.assertRaises(ValueError): compare(spec, before, after)
        after['collected_at'] = (datetime.now(timezone.utc)+timedelta(seconds=1)).isoformat()
        self.assertEqual(compare(spec, before, after)['outcome'], 'stable-pass')
        after['task_id'] = task('node-basics', title='不同任务')['id']
        with self.assertRaises(ValueError): compare(spec, before, after)
        after = deepcopy(before)
        after['collected_at'] = (datetime.now(timezone.utc)+timedelta(seconds=1)).isoformat()
        after['target'].update(requested=r'C:\Other\node.exe', actual=r'C:\Other\node.exe')
        after['facts']['npm'].update(node=r'C:\Other\node.exe', path=r'C:\Other\node_modules\npm\bin\npm-cli.js')
        with self.assertRaises(ValueError): compare(spec, before, after)
        from test_rules import evidence
        with self.assertRaises(ValueError): compare(spec, before, evidence())

    def test_changed_node_task_even_resealed_is_rejected(self):
        from campuslab.rules import seal
        spec = task('node-basics'); spec['node']['min'] = '20.0'
        with self.assertRaises(ValueError): analyze(seal(spec), node_evidence())


if __name__ == '__main__': unittest.main()
