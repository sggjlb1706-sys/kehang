"""Real loopback HTTP responses; no external model or credentials."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import threading
import unittest
from unittest.mock import patch

from campuslab.diagnosis import model_request


class TransportFixture(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def do_POST(self):
        self.rfile.read(int(self.headers['Content-Length']))
        raw = json.dumps({'choices': [{'message': {'content': '本机协议夹具'},
                                      'finish_reason': 'stop'}]}).encode()
        kind = self.path.rsplit('/', 1)[1]
        replies = {
            'json-list': [],
            'multiple': {'choices': [{'message': {'content': 'a'}, 'finish_reason': 'stop'}] * 2},
            'length-stop': {'choices': [{'message': {'content': 'partial'}, 'finish_reason': 'length'}]},
            'tools': {'choices': [{'message': {'content': 'a', 'tool_calls': [{}]}, 'finish_reason': 'stop'}]},
            'nontext': {'choices': [{'message': {'content': []}, 'finish_reason': 'stop'}]},
            'empty': {'choices': [{'message': {'content': '  '}, 'finish_reason': 'stop'}]},
        }
        if kind in replies:
            raw = json.dumps(replies[kind]).encode()
        self.send_response(302 if kind == 'redirect' else 200)
        self.send_header('Content-Type', 'text/plain' if kind == 'wrong-type' else 'application/json')
        if kind == 'redirect':
            self.send_header('Location', '/valid')
        if kind in ('wrong-type', 'fixed', 'mismatch', 'invalid-length', 'oversize-length', 'redirect'):
            length = {'mismatch': str(len(raw) + 5), 'invalid-length': 'invalid',
                      'oversize-length': '131073'}.get(kind, str(len(raw)))
            self.send_header('Content-Length', length)
            self.close_connection = True
        elif kind == 'close-delimited':
            self.send_header('Connection', 'close')
            self.close_connection = True
        else:
            self.send_header('Transfer-Encoding', 'chunked')
        self.end_headers()
        try:
            if kind in ('wrong-type', 'fixed', 'mismatch', 'invalid-length', 'oversize-length', 'redirect', 'close-delimited'):
                self.wfile.write(raw)
                return
            if kind == 'broken':
                self.wfile.write(b'100\r\nshort\r\n')
                self.wfile.flush()
                self.close_connection = True
                return
            if kind == 'oversize':
                raw = b' ' * 131073 + raw
            elif kind == 'truncated-json':
                raw = raw[:-5]
            for chunk in (b'\n\n', raw[:10], raw[10:]):
                self.wfile.write(f'{len(chunk):X}\r\n'.encode() + chunk + b'\r\n')
            self.wfile.write(b'0\r\n\r\n')
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass  # Rejected-response fixtures may be closed before their body is read.

    def log_message(self, *args):
        pass


class ModelTransportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), TransportFixture)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def request(self, kind):
        config = dict(destination=f'http://127.0.0.1:{self.server.server_port}/{kind}',
                      model='loopback-transport-fixture')
        with patch.dict(os.environ, {'CAMPUSLAB_AI_KEY': ''}):
            return model_request(config, [dict(role='user', content='本机协议测试')])

    def test_chunked_json_with_keepalive_whitespace_is_accepted(self):
        result = self.request('valid')
        self.assertTrue(result['completed'])
        self.assertEqual(result['explanation'], '本机协议夹具')
        self.assertFalse(result['evidence_verdict_changed'])

    def test_oversize_chunked_response_is_rejected(self):
        self.assertFalse(self.request('oversize')['completed'])

    def test_truncated_json_is_rejected(self):
        self.assertFalse(self.request('truncated-json')['completed'])

    def test_broken_chunked_response_fails_without_escaping(self):
        self.assertFalse(self.request('broken')['completed'])

    def test_wrong_content_type_is_rejected(self):
        self.assertFalse(self.request('wrong-type')['completed'])

    def test_present_content_length_still_requires_exact_valid_size(self):
        self.assertTrue(self.request('fixed')['completed'])
        for kind in ('mismatch', 'invalid-length', 'oversize-length'):
            with self.subTest(kind=kind):
                result = self.request(kind)
                self.assertFalse(result['completed'])
                self.assertFalse(result['evidence_verdict_changed'])

    def test_close_delimited_json_without_length_is_accepted(self):
        self.assertTrue(self.request('close-delimited')['completed'])

    def test_json_and_final_answer_constraints_are_preserved(self):
        for kind in ('json-list', 'multiple', 'length-stop', 'tools', 'nontext', 'empty'):
            with self.subTest(kind=kind):
                result = self.request(kind)
                self.assertFalse(result['completed'])
                self.assertFalse(result['evidence_verdict_changed'])

    def test_redirect_remains_rejected(self):
        result = self.request('redirect')
        self.assertFalse(result['completed'])
        self.assertEqual(result['error'], 'HTTPError')
