"""Loopback smoke on the copied release; evidence import is not new device collection."""
from io import BytesIO
import json
from pathlib import Path
import tempfile
import threading
from urllib.request import urlopen
import zipfile
from campuslab.rules import analyze,task
from campuslab.web import AppServer


def main():
    root=Path(__file__).resolve().parents[1]
    checks=[]
    with tempfile.TemporaryDirectory() as directory:
        server=AppServer(0,Path(directory)/'smoke.sqlite',root/'vendor/python-3.13.17-embed-amd64.zip')
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            base=f'http://127.0.0.1:{server.server_port}'
            with urlopen(base,timeout=5) as r:assert 'PyTorch'.encode() in r.read()
            with urlopen(base+'/api/config',timeout=5) as r:assert json.load(r)['portable_available']
            for scenario in ('python-basics','node-basics','local-qwen','pytorch-cpu','pytorch-gpu','vm-linux'):
                with urlopen(base+'/api/tool?goal='+scenario,timeout=10) as r,zipfile.ZipFile(BytesIO(r.read())) as archive:
                    assert archive.testzip() is None
                    assert json.loads(archive.read('task.json'))==task(scenario)
                    assert 'runtime/python.exe' in archive.namelist()
                checks.append(scenario+' tool/snapshot/runtime')
            for scenario,path in [('pytorch-gpu','records/courses/torch/float32-retest/gpu-B.json'),
                                  ('local-qwen','records/courses/model/20261108T103903Z/B.json')]:
                report=json.loads((root/path).read_text(encoding='utf-8'))
                assert analyze(task(scenario),report)['passed']
                checks.append(scenario+' current rules accept original real evidence')
        finally:server.shutdown();server.server_close();thread.join()
    print(json.dumps(dict(root=str(root),passed=True,checks=checks,service_stopped=True,new_hardware_collection=False)))


if __name__=='__main__':main()
