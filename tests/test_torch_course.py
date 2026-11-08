"""Constructed protocol evidence; real device records live under records/courses/torch."""
from copy import deepcopy
from datetime import datetime, timezone
import tempfile
from pathlib import Path
import unittest

from campuslab.torch_course import make_task, validate_spec, analyze, compare_identity, collect
from campuslab.rules import seal


def evidence(gpu_required=False):
    spec = make_task(gpu_required=gpu_required)
    result = dict(schema=1, task_id=spec['id'], collected_at=datetime.now(timezone.utc).isoformat(),
                  target=dict(requested=r'C:\Course\python.exe', actual=r'C:\Course\python.exe', exists=True),
                  facts=dict(os='Windows', python='3.11.16',
                             torch=dict(installed=True, version='2.14.0+cu126', imported=True, error=''),
                             cpu=dict(returncode=0, result=[[4, 4], [10, 8]], device='cpu', error=''),
                             gpu=dict(build='12.6', available=True,
                                      device=dict(index=0, uuid='GPU-1234', name='Test GPU', total_memory=8192),
                                      run=dict(requested=gpu_required, returncode=0 if gpu_required else None,
                                               result=[[4, 4], [10, 8]] if gpu_required else None,
                                               device='cuda:0' if gpu_required else None,
                                               device_uuid='GPU-1234' if gpu_required else None, error=''), error='')))
    return spec, result


class TorchCourseTest(unittest.TestCase):
    def test_cpu_and_gpu_are_distinct_fixed_tasks(self):
        cpu, report = evidence()
        gpu, gpu_report = evidence(True)
        self.assertNotEqual(cpu['id'], gpu['id'])
        self.assertTrue(analyze(cpu, report)['passed'])
        self.assertTrue(analyze(gpu, gpu_report)['passed'])
        self.assertEqual(cpu['tensor_dtype'], 'float32')
        changed = deepcopy(gpu); changed['packages']['torch'] = '1.0'
        with self.assertRaises(ValueError): validate_spec(seal(changed))

    def test_cpu_success_never_substitutes_for_gpu(self):
        spec, report = evidence(True)
        report['facts']['gpu']['run'].update(requested=False, returncode=None, result=None, device=None, device_uuid=None)
        states = {c['id']: c['status'] for c in analyze(spec, report)['checks']}
        self.assertEqual(states['torch:cpu'], 'pass')
        self.assertEqual(states['torch:gpu-run'], 'unknown')
        self.assertFalse(analyze(spec, report)['passed'])

    def test_build_availability_and_actual_run_are_separate(self):
        spec, report = evidence(True)
        report['facts']['gpu'].update(build=None, available=False, device=None)
        report['facts']['gpu']['run'].update(returncode=None, result=None, device=None, device_uuid=None)
        result = analyze(spec, report)
        states = {c['id']: c['status'] for c in result['checks']}
        self.assertEqual(states['torch:cuda-build'], 'missing')
        self.assertEqual(states['torch:gpu-available'], 'missing')
        self.assertEqual(states['torch:gpu-run'], 'unknown')
        self.assertFalse(result['passed'])

    def test_missing_interpreter_preserves_unknown_dependencies(self):
        spec = make_task()
        report = collect(spec, r'C:\CampusLab-Nonexistent\python.exe')
        states = {c['id']: c['status'] for c in analyze(spec, report)['checks']}
        self.assertEqual(states['python'], 'missing')
        self.assertEqual(states['package:torch'], 'unknown')
        self.assertEqual(states['torch:cpu'], 'unknown')

    def test_missing_framework_and_import_failure_are_different(self):
        spec, report = evidence()
        report['facts']['torch'].update(installed=False, version=None, imported=False, error='not installed')
        report['facts']['cpu'].update(returncode=None, result=None, device=None)
        report['facts']['gpu'].update(build=None, available=None, device=None)
        self.assertEqual({c['id']: c['status'] for c in analyze(spec, report)['checks']}['package:torch'], 'missing')
        report['facts']['torch'].update(installed=True, version='2.14.0', imported=False, error='DLL load failed')
        self.assertEqual({c['id']: c['status'] for c in analyze(spec, report)['checks']}['torch:import'], 'mismatch')

    def test_strict_types_partial_fields_and_impossible_identity_rejected(self):
        mutations = [lambda r: r['facts'].pop('cpu'),
                     lambda r: r['facts']['cpu'].update(returncode=False),
                     lambda r: r['facts']['cpu'].update(result=[[True, 4], [10, 8]]),
                     lambda r: r['facts']['cpu'].update(result=[[float('nan'), 4], [10, 8]]),
                     lambda r: r['facts']['gpu'].update(available='true'),
                     lambda r: r['facts']['gpu']['device'].update(index=True),
                     lambda r: r['facts']['gpu']['run'].update(device_uuid='GPU-other'),
                     lambda r: r['target'].update(actual=r'C:\Other\python.exe'),
                     lambda r: r['target'].update(actual=None),
                     lambda r: r.update(task_id='other'),
                     lambda r: r.update(collected_at='2026-11-08T10:00:00')]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                spec, report = evidence(True); mutation(report)
                with self.assertRaises(ValueError): analyze(spec, report)

    def test_wrong_tensor_or_device_does_not_pass(self):
        for section, key, value in [('cpu', 'result', [[0, 0], [0, 0]]),
                                    ('cpu', 'device', 'cuda:0'),
                                    ('gpu', 'run', dict(requested=True, returncode=0, result=[[4, 4], [10, 8]], device='cpu', device_uuid='GPU-1234', error=''))]:
            spec, report = evidence(True)
            report['facts'][section][key] = value
            self.assertFalse(analyze(spec, report)['passed'])

    def test_gpu_probe_error_cannot_be_complete(self):
        spec, report = evidence(True)
        report['facts']['gpu']['error'] = 'device query failed'
        result = analyze(spec, report)
        self.assertFalse(result['passed'])
        self.assertEqual({c['id']: c['status'] for c in result['checks']}['torch:gpu-available'], 'unknown')

    def test_recheck_separate_interpreter_and_gpu_identity(self):
        _, before = evidence(True); after = deepcopy(before)
        compare_identity(before, after)
        after['facts']['gpu']['device']['uuid'] = 'GPU-other'
        with self.assertRaises(ValueError): compare_identity(before, after)
        after = deepcopy(before); after['target']['requested'] = r'C:\Other\python.exe'
        with self.assertRaises(ValueError): compare_identity(before, after)
        after = deepcopy(before); before['facts']['gpu']['device'] = None
        compare_identity(before, after)

    def test_tool_runtime_refused_and_gpu_trigger_is_boolean(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory); (folder/'.campuslab-tool-runtime').touch()
            with self.assertRaises(ValueError): collect(make_task(), str(folder/'python.exe'))
        with self.assertRaises(ValueError): collect(make_task(gpu_required=True), r'C:\Course\python.exe', gpu_run='yes')


if __name__ == '__main__':
    unittest.main()
