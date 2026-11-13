"""Controlled fixtures, not evidence about any installed course environment."""
import json
import os
from pathlib import Path
import tempfile
import threading
import time
import subprocess
import sys
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch

from campuslab.local_check import LocalCheckService, MAX_JOBS
from campuslab.owned_process import OwnedProcess
from campuslab.rules import task
from campuslab.web import AppServer
from test_rules import evidence


def report(spec, target, cancelled):
    result = evidence(spec)
    result['target'].update(requested=target, actual=target)
    return result


def finished(service, identity):
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        result = service.status(identity)
        if result['state'] not in ('running', 'cancelling'):
            return result
        time.sleep(.005)
    raise AssertionError('Job did not finish')


class LocalCheckTest(unittest.TestCase):
    def service(self, choices=None, runner=report):
        service = LocalCheckService(lambda: choices if choices is not None else [(r'C:\Course\python.exe', 'fixture')], runner)
        service.available = True
        self.addCleanup(service.close)
        return service

    def start(self, service, **extra):
        return service.start(dict(task=task(), consent=True, **extra))['id']

    def test_no_execution_until_explicit_click_and_closed_parameters(self):
        calls = []
        service = self.service(runner=lambda *args: calls.append(args))
        service.configuration()
        self.assertEqual(calls, [])
        for fields in [dict(consent=False), dict(command='whoami'), dict(target=r'C:\Other\python.exe'),
                       dict(task=task('pytorch-gpu')), dict(consent=1)]:
            body = dict(task=task(), consent=True); body.update(fields)
            with self.assertRaises(ValueError): service.start(body)
        self.assertEqual(calls, [])

    def test_multiple_environments_are_separate_and_bounded(self):
        calls = []
        def run(spec, target, cancelled):
            calls.append(target); result = report(spec, target, cancelled)
            if 'Env1' in target:
                result['facts']['python'] = '3.9.0'
            return result
        service = self.service([(fr'C:\Env{i}\python.exe', 'fixture') for i in range(10)], run)
        result = finished(service, self.start(service))
        self.assertEqual(len(result['results']), 8)
        self.assertTrue(result['limited'])
        self.assertFalse(result['results'][1]['analysis']['passed'])
        self.assertTrue(result['results'][0]['analysis']['passed'])
        self.assertEqual(len(calls), 8)
        result['results'].clear()
        self.assertEqual(len(service.status(result['id'])['results']), 8)

    def test_no_candidates_does_not_claim_pass_or_missing_installation(self):
        service = self.service([])
        result = finished(service, self.start(service))
        self.assertEqual(result['results'], [])
        self.assertNotIn('passed', result)

    def test_unknown_bad_identity_and_failure_never_pass(self):
        for runner in [lambda *a: {}, lambda *a: (_ for _ in ()).throw(OSError()),
                       lambda spec, target, cancel: evidence(spec)]:
            service = self.service([(r'C:\Other\python.exe', 'fixture')], runner)
            item = finished(service, self.start(service))['results'][0]
            self.assertTrue(item['error']); self.assertNotIn('analysis', item)

    def test_recheck_uses_stored_target_and_original_baseline(self):
        service = self.service()
        first = finished(service, self.start(service))
        for _ in range(2):
            previous = first
            first = finished(service, self.start(service, previous_job=previous['id'], target_id=previous['results'][0]['id']))
            self.assertEqual(first['results'][0]['target'], r'C:\Course\python.exe')
            self.assertEqual(first['results'][0]['comparison']['outcome'], 'stable-pass')
            self.assertEqual(first['results'][0]['before']['target'], previous['results'][0]['report']['target'])
        for extra in [dict(previous_job='unknown', target_id='x'), dict(previous_job=first['id'], target_id='x')]:
            with self.assertRaises(ValueError): self.start(service, **extra)
        with self.assertRaises(ValueError):
            service.start(dict(task=task(title='different'), consent=True, previous_job=first['id'], target_id=first['results'][0]['id']))

    def test_cancel_busy_and_shutdown(self):
        entered = threading.Event()
        def wait(spec, target, cancel):
            entered.set(); cancel.wait(2); return report(spec, target, cancel)
        service = self.service(runner=wait)
        identity = self.start(service); self.assertTrue(entered.wait(1))
        with self.assertRaises(ValueError): self.start(service)
        service.cancel(identity)
        result = finished(service, identity)
        self.assertEqual(result['state'], 'cancelled'); self.assertEqual(result['results'], [])
        self.start(service); service.close()
        with self.assertRaises(ValueError): self.start(service)

    def test_history_is_bounded_and_tokens_are_instance_specific(self):
        service = self.service([])
        first = None
        for _ in range(MAX_JOBS + 2):
            identity = self.start(service); first = first or identity; finished(service, identity)
        self.assertEqual(len(service.jobs), MAX_JOBS)
        with self.assertRaises(ValueError): service.status(first)
        for token in ['', 'wrong', '中文', None, self.service().token]:
            with self.assertRaises(ValueError): service.authorize(token)
        service.authorize(service.token)

    def test_embedded_tool_runtime_is_not_executed(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'python.exe'; path.touch()
            (path.parent / '.campuslab-tool-runtime').touch()
            service = self.service([(str(path), 'fixture')], lambda *a: self.fail('runtime executed'))
            self.assertEqual(finished(service, self.start(service))['total'], 0)

    def test_disconnected_page_lease_cancels_job(self):
        def wait(spec, target, cancel):
            cancel.wait(2); return report(spec, target, cancel)
        with patch('campuslab.local_check.LEASE_SECONDS', .1):
            service = self.service(runner=wait)
            result = finished(service, self.start(service))
            self.assertEqual(result['state'], 'cancelled')
            self.assertEqual(result['results'], [])

    @unittest.skipUnless(os.name == 'nt', 'Windows owned process tree')
    def test_owned_process_tree_cleanup_preserves_unrelated_process(self):
        # Both helpers belong to this test; only the first tree is cancelled.
        flags = subprocess.CREATE_NO_WINDOW
        unrelated = subprocess.Popen([sys.executable,'-B','-I','-c','import time;time.sleep(30)'], creationflags=flags)
        try:
            with tempfile.TemporaryDirectory(prefix='kehang-process-test-') as folder:
                pidfile = Path(folder) / 'child.txt'
                script = 'import subprocess,sys,time;from pathlib import Path;sys.stdin.buffer.read(1);p=subprocess.Popen([sys.executable,"-B","-I","-c","import time;time.sleep(30)"]);ready=Path(sys.argv[1]);pending=ready.with_suffix(".pending");pending.write_text(str(p.pid));pending.replace(ready);time.sleep(30)'
                owned = OwnedProcess([sys.executable,'-B','-I','-c',script,str(pidfile)])
                try:
                    deadline = time.monotonic()+5
                    while not pidfile.exists() and time.monotonic()<deadline: time.sleep(.02)
                    self.assertTrue(pidfile.exists())
                    child = int(pidfile.read_text())
                    owned.close()
                    self.assertIsNotNone(owned.process.poll()); self.assertIsNone(unrelated.poll())
                    # query-only handle check; no process lookup or user-PID termination.
                    import ctypes
                    handle=ctypes.windll.kernel32.OpenProcess(0x1000,False,child)
                    if handle:
                        code=ctypes.c_ulong();ctypes.windll.kernel32.GetExitCodeProcess(handle,ctypes.byref(code));ctypes.windll.kernel32.CloseHandle(handle)
                        self.assertNotEqual(code.value,259)
                finally: owned.close()
        finally: unrelated.kill(); unrelated.wait(timeout=5)


class LocalCheckHTTPTest(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.server = AppServer(0, Path(self.folder.name) / 'courses.sqlite')
        self.server.local_check.close()
        self.server.local_check = LocalCheckService(lambda: [], report)
        self.server.local_check.available = True
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True); self.thread.start()
        self.base = 'http://127.0.0.1:' + str(self.server.server_port)

    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join(); self.folder.cleanup()

    def request(self, path, body=None, token=True, **headers):
        if token: headers['X-Kehang-Local'] = self.server.local_check.token
        if body is not None: headers['Content-Type'] = 'application/json'
        return json.load(urlopen(Request(self.base + path, data=json.dumps(body).encode() if body is not None else None, headers=headers), timeout=3))

    def test_token_origin_and_no_arbitrary_execution(self):
        for extra in [dict(token=False), {'Origin':'https://evil.invalid'}, {'Host':'evil.invalid'}]:
            with self.assertRaises(HTTPError): self.request('/api/local-check', dict(task=task(), consent=True), **extra)
        with self.assertRaises(HTTPError): self.request('/api/execute', dict(command='x'))
        with self.assertRaises(HTTPError): self.request('/api/local-check')
        identity = self.request('/api/local-check', dict(task=task(), consent=True))['id']
        finished(self.server.local_check, identity)
        self.assertEqual(self.request('/api/local-check/jobs/' + identity)['state'], 'done')
        with self.assertRaises(HTTPError): self.request('/api/local-check/jobs/' + identity, token=False)
        with self.assertRaises(HTTPError): self.request('/api/local-check/cancel', dict(id=identity, pid=123))


if __name__ == '__main__': unittest.main()
