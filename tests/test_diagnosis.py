from http.server import BaseHTTPRequestHandler,HTTPServer
import json
import os
import threading
import unittest
from unittest.mock import patch
from campuslab.diagnosis import diagnose,redact
from campuslab.guidance import plan
from campuslab.rules import task


class MockModel(BaseHTTPRequestHandler):
    body={'choices':[{'message':{'content':'依据缺失项手动处理，再使用同一环境复检。'},'finish_reason':'stop'}]}
    count=0
    def do_POST(self):
        type(self).count+=1
        self.rfile.read(int(self.headers['Content-Length']))
        raw=json.dumps(type(self).body).encode()
        self.send_response(200); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(raw))); self.end_headers(); self.wfile.write(raw)
    def log_message(self,*a): pass


class DiagnosisTest(unittest.TestCase):
    def test_three_modes_same_requirements(self):
        spec=task(); original=json.dumps(spec,sort_keys=True)
        modes=[plan(spec,m) for m in ('novice','standard','quick')]
        self.assertNotEqual(len(modes[0]['steps']),len(modes[2]['steps']))
        self.assertEqual(json.dumps(spec,sort_keys=True),original)
        self.assertIn('尚无有效内存证据',plan(task('local-qwen'))['recommendation'])
        self.assertIn('云端结果不能替代',plan(task('local-qwen'),resources={'ram_bytes':1024})['recommendation'])

    def test_no_consent_no_request(self):
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaises(ValueError): diagnose('test',True)
            with self.assertRaises(ValueError): diagnose('test',False)

    def test_local_protocol_simulation_success_and_failure(self):
        server=HTTPServer(('127.0.0.1',0),MockModel)
        thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start()
        try:
            with patch.dict(os.environ,{'CAMPUSLAB_AI_URL':f'http://127.0.0.1:{server.server_port}/chat','CAMPUSLAB_AI_MODEL':'protocol-fixture','CAMPUSLAB_AI_KEY':''}):
                MockModel.body={'choices':[{'message':{'content':'手动检查'},'finish_reason':'stop'}]}
                self.assertTrue(diagnose('explicit mock evidence',True)['completed'])
                MockModel.body={'text':'invalid protocol fixture'}
                self.assertFalse(diagnose('explicit mock evidence',True)['completed'])
        finally:
            server.shutdown(); server.server_close(); thread.join()

    def test_basic_redaction(self):
        text=redact('C:\\Users\\Alice\\x token sk-abcdefghijklmnop 192.168.1.2 a@example.com')
        for raw in ('Alice','sk-abcdefghijklmnop','192.168.1.2','a@example.com'): self.assertNotIn(raw,text)


if __name__=='__main__': unittest.main()
