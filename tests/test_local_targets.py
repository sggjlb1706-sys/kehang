"""Controlled targets and collectors; these tests prove no installed environment."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from campuslab.local_check import LocalCheckService
from campuslab.local_targets import FIELDS, TargetStore
from campuslab.rules import task
from test_local_check import finished, report


class TargetSelectionTest(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.python = self.root / 'python.exe'; self.python.touch()
        self.store = TargetStore()
        self.spec = task()

    def selected(self, spec=None, field='target', path=None):
        return self.store.register(spec or self.spec, field, str(path or self.python), 'controlled fixture')['id']

    def test_selections_do_not_execute_and_are_bound_to_task_and_field(self):
        identity = self.selected()
        self.assertEqual(self.store.resolve(self.spec, {'target': identity}, {}), {'target': str(self.python)})
        for spec, selections in [(task(title='another'), {'target': identity}), (self.spec, {'target': str(self.python)}),
                                 (task('notebook-data'), {'target': identity, 'kernel_spec': identity})]:
            with self.assertRaises(ValueError): self.store.resolve(spec, selections, {})

    def test_required_fields_and_closed_options(self):
        for scenario in FIELDS:
            with self.assertRaises(ValueError): self.store.resolve(task(scenario), {}, {})
        identity = self.selected()
        for options in [{'command': 'whoami'}, {'infer': True}, {'gpu_run': True}, {'api_send': True}]:
            with self.assertRaises(ValueError): self.store.resolve(self.spec, {'target': identity}, options)

    def test_missing_or_changed_target_must_be_selected_again(self):
        identity = self.selected(); self.python.unlink()
        with self.assertRaises(ValueError): self.store.resolve(self.spec, {'target': identity}, {})

    def test_gpu_and_model_execution_require_boolean_opt_in(self):
        spec = task('pytorch-gpu'); identity = self.selected(spec)
        self.assertNotIn('gpu_run', self.store.resolve(spec, {'target': identity}, {}))
        self.assertTrue(self.store.resolve(spec, {'target': identity}, {'gpu_run': True})['gpu_run'])
        with self.assertRaises(ValueError): self.store.resolve(spec, {'target': identity}, {'gpu_run': 1})

    def test_picker_cancel_and_late_selection_never_start_a_job(self):
        with patch('campuslab.local_targets.choose_native', return_value=None):
            self.assertIsNone(self.store.pick(self.spec, 'target')['selected'])
        self.assertFalse(self.store.entries)
        with patch('campuslab.local_targets.choose_native', return_value=str(self.python)):
            self.assertTrue(self.store.pick(self.spec, 'target')['selected']['id'])

    def test_wrong_file_type_and_tool_runtime_rejected(self):
        for name in ['something.cmd', 'pythonw.exe', 'node.exe']:
            file = self.root / name; file.touch()
            with self.assertRaises(ValueError): self.selected(path=file)
        (self.root / '.campuslab-tool-runtime').touch()
        with self.assertRaises(ValueError): self.selected()

    def test_recheck_uses_pinned_options_and_failed_recheck_keeps_original(self):
        service = LocalCheckService(runner=report); service.available = True; service.targets = self.store
        self.addCleanup(service.close)
        first = finished(service, service.start(dict(task=self.spec, consent=True, selections={'target': self.selected()}, options={}))['id'])
        original = first['results'][0]
        body = dict(task=self.spec, consent=True, previous_job=first['id'], target_id=original['id'])
        with self.assertRaises(ValueError): service.start(dict(body, selections={}))
        service.runner = lambda *args: (_ for _ in ()).throw(OSError())
        second = finished(service, service.start(body)['id'])
        self.assertTrue(second['results'][0]['error'])
        self.assertEqual(service.status(first['id'])['results'][0]['report'], original['report'])

    def test_web_course_has_no_fabricated_environment_check(self):
        self.assertEqual(self.store.discover(task('ai-web-deepseek'))['fields'], {})

    def test_vm_host_only_is_explicit_and_never_selects_an_instance(self):
        spec = task('vm-linux'); program = self.root / 'vmrun.exe'; program.touch()
        selections = {'target': self.selected(spec, path=program)}
        with self.assertRaises(ValueError): self.store.resolve(spec, selections, {})
        self.assertNotIn('vm_id', self.store.resolve(spec, selections, {'host_only': True}))
        with self.assertRaises(ValueError): self.store.resolve(spec, selections, {'host_only': 'yes'})

    def test_inaccessible_optional_kernel_directory_preserves_other_candidates(self):
        original = Path.is_dir
        def is_dir(path):
            if 'jupyter' in str(path): raise PermissionError('controlled denied directory')
            return original(path)
        with patch('campuslab.local_targets.python_choices', return_value=[(str(self.python), 'fixture')]), patch.object(Path, 'is_dir', is_dir):
            value = self.store.discover(task('notebook-data'))
        self.assertEqual(len(value['fields']['target']['choices']), 1)
        self.assertEqual(value['fields']['kernel_spec']['choices'], [])

    def test_native_picker_and_discovery_http_require_page_identity(self):
        from campuslab.web import AppServer
        from urllib.request import Request, urlopen
        from urllib.error import HTTPError
        import json, threading
        server = AppServer(0, self.root / 'http.sqlite')
        thread = threading.Thread(target=server.serve_forever, daemon=True);thread.start()
        try:
            for endpoint in ('options', 'discover', 'pick'):
                body = dict(task=self.spec)
                if endpoint == 'pick': body['field'] = 'target'
                request = Request('http://127.0.0.1:'+str(server.server_port)+'/api/local-check/'+endpoint,
                                  data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
                with self.assertRaises(HTTPError):urlopen(request, timeout=3)
            self.assertFalse(server.local_check.jobs)
        finally:server.shutdown();server.server_close();thread.join()


if __name__ == '__main__': unittest.main()
