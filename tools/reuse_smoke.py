"""Actual Python CLI startup and downloaded tool/report routes; never change execution policy."""
from io import BytesIO
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from urllib.error import URLError
from urllib.request import Request,urlopen
import zipfile
from campuslab.rules import task,NEW_COURSES

ROOT=Path(__file__).resolve().parents[1]
def main():
    port=8781
    with socket.socket() as probe:
        probe.bind(('127.0.0.1',port))
    scenarios=['python-basics','node-basics','local-qwen','pytorch-cpu','pytorch-gpu','vm-linux',*NEW_COURSES]
    checks=[]
    with tempfile.TemporaryDirectory(prefix='campuslab-release-smoke-') as temporary:
        folder=Path(temporary);database=folder/'new-course.sqlite'
        argv=[sys.executable,'-B','-m','campuslab.web','--port',str(port),'--database',str(database),'--runtime-zip',str(ROOT/'vendor/python-3.13.17-embed-amd64.zip')]
        process=subprocess.Popen(argv,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=='win32' else 0)
        base=f'http://127.0.0.1:{port}'
        try:
            for _ in range(60):
                if process.poll() is not None:raise ValueError('New CLI exited before ready')
                try:
                    with urlopen(base+'/api/config',timeout=1) as response:assert json.load(response)['portable_available']
                    break
                except (URLError,OSError):time.sleep(.1)
            else:raise ValueError('New CLI did not become ready')
            with urlopen(base,timeout=5) as response:assert response.status==200
            for scenario in scenarios:
                with urlopen(base+'/api/tool?goal='+scenario,timeout=10) as response,zipfile.ZipFile(BytesIO(response.read())) as z:
                    assert z.testzip() is None and json.loads(z.read('task.json'))==task(scenario)
                    assert 'runtime/python.exe' in z.namelist()
                    if scenario=='notebook-data':assert 'campuslab/data/notebook_scores.csv' in z.namelist()
                checks.append(scenario+' snapshot/tool/runtime/CRC')
            spec=task('java-jdk')
            from campuslab.collect import collect
            report=collect(spec,r'C:\CampusLab-Release-Missing-JDK')
            request=Request(base+'/api/analyze',data=json.dumps(dict(task=spec,report=report)).encode(),headers={'Content-Type':'application/json'})
            with urlopen(request,timeout=5) as response:assert not json.load(response)['passed']
            checks.append('Actual report import endpoint retains missing target')
        finally:
            process.terminate()
            try:process.communicate(timeout=10)
            except subprocess.TimeoutExpired:process.kill();process.communicate(timeout=5)
    print(json.dumps(dict(root=str(ROOT),passed=True,checks=checks,port=port,argv=argv,execution_policy_changed=False,service_stopped=process.poll() is not None,
        database_scope='new temporary course library only; removed after stopping own process',actual_api_calls=0,actual_dsh_runs=0)))
if __name__=='__main__':main()
