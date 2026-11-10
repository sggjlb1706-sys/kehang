"""Read-only independent brand review. No real model, DSH or VM execution."""
from datetime import datetime,timezone
from io import BytesIO
import hashlib,json,subprocess,sys,tempfile,threading
from pathlib import Path
from urllib.request import Request,urlopen
import zipfile

ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT.parent/'competition-reuse-ai-20261109'
sys.path.insert(0,str(ROOT))
from campuslab.rules import task,NEW_COURSES,analyze,compare
from campuslab.portable import import_package,export_package,guide_html
from campuslab.web import AppServer

def sha(raw):return hashlib.sha256(raw).hexdigest().upper()
def git(*args):return subprocess.check_output(['git','-c','safe.directory='+ROOT.as_posix(),*args],cwd=ROOT)
def main():
    manifest=ROOT/'records/review/kehang-candidate.json';raw=manifest.read_bytes()
    assert sha(raw)=='C7E498D16997F5E6343383823C21A9527DB07BC7E4217AA33A7EFFF007A78E9B'
    frozen=json.loads(raw);head=frozen['product_head'];git('merge-base','--is-ancestor',head,'HEAD')
    for name,digest in frozen['source_sha256'].items():
        data=(ROOT/name).read_bytes();assert sha(data)==digest
        assert git('show',head+':'+name)==data
    browser=json.loads((ROOT/frozen['browser_record']).read_text(encoding='utf-8'))
    assert browser['status']=='passed' and len(browser['checks'])==9
    assert all(sha((ROOT/n).read_bytes())==h for n,h in browser['source_sha256'].items())
    scenarios=['python-basics','node-basics','local-qwen','pytorch-cpu','pytorch-gpu','vm-linux',*NEW_COURSES]
    previous=json.loads(subprocess.check_output([sys.executable,'-B','-c','import json; from campuslab.rules import task,NEW_COURSES; print(json.dumps({s:task(s) for s in ["python-basics","node-basics","local-qwen","pytorch-cpu","pytorch-gpu","vm-linux",*NEW_COURSES]}))'],cwd=BASE))
    assert {s:task(s) for s in scenarios}==previous
    changed=git('diff','--name-only','fc14fc752a83709df496b386e4ce950b01996afe',head,'--','campuslab','web').decode().splitlines()
    assert set(changed)=={'campuslab/guest_probe.py','campuslab/portable.py','campuslab/teaching.py','campuslab/web.py','web/app.js','web/index.html'}
    prefixes=[]
    for name in ('README.md','PRODUCT.md','DESIGN.md','TASK.md','PLAN.md','HANDOFF.md','REVIEW.md','PROVENANCE.md'):
        assert (ROOT/name).read_bytes().endswith(git('show','fc14fc752a83709df496b386e4ce950b01996afe:'+name));prefixes.append(name)
    reanalysis=[]
    for s in ('notebook-data','java-jdk','sqlite-basics','deepseek-api','ai-web-deepseek','dsh-desktop','dsh-cli'):
        relative='records/reuse-ai/browser-'+('data/20261110T003103340935Z' if s in ('notebook-data','java-jdk','sqlite-basics') else 'ai/20261110T003136119642Z')
        folder=ROOT/relative;spec=task(s)
        a=json.loads((folder/(s+'-A.json')).read_text(encoding='utf-8'));b=json.loads((folder/(s+'-B.json')).read_text(encoding='utf-8'))
        result=compare(spec,a,b)
        package=json.loads((folder/(s+'-course.json')).read_text(encoding='utf-8'))
        assert import_package(package)==spec and export_package(spec)==package
        guide=guide_html(spec);assert '<title>课航' in guide and '计算机课程学习与实训助手' in guide and spec['id'] in guide
        reanalysis.append(dict(scenario=s,outcome=result['outcome'],passed=result['after']['passed'],checks=len(result['after']['checks']),legacy_package_unchanged=True))
    endpoints=[]
    with tempfile.TemporaryDirectory(prefix='kehang-independent-') as temp:
        server=AppServer(0,Path(temp)/'independent.sqlite',ROOT/'vendor/python-3.13.17-embed-amd64.zip')
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();base=f'http://127.0.0.1:{server.server_port}'
        try:
            with urlopen(base,timeout=5) as response:
                html=response.read().decode('utf-8');assert '<title>课航——计算机课程学习与实训助手</title>' in html
                assert '>课航</a>' in html and 'CAMPUS LAB' not in html and 'AI实验环境管家' not in html
            for s in scenarios:
                with urlopen(base+'/api/tool?goal='+s,timeout=10) as response:
                    assert response.headers.get_filename()=='Kehang-tool.zip'
                    with zipfile.ZipFile(BytesIO(response.read())) as z:
                        assert z.testzip() is None and 'runtime/python.exe' in z.namelist() and '课航——计算机课程学习与实训助手' in z.read('README.txt').decode('utf-8')
                        assert json.loads(z.read('task.json'))==previous[s]
                request=Request(base+'/api/guide',data=json.dumps(dict(task=task(s))).encode(),headers={'Content-Type':'application/json'})
                with urlopen(request,timeout=5) as response:
                    assert response.headers.get_filename()=='Kehang-guide.html' and '课航' in response.read().decode('utf-8')
                endpoints.append(s)
        finally:server.shutdown();server.server_close();thread.join()
    results=dict(checked_at=datetime.now(timezone.utc).isoformat(),head=head,manifest_sha256=sha(raw),source_files=len(frozen['source_sha256']),source_and_head_match=True,
        browser_groups=9,browser_final_source_matches=True,task_snapshots_equal=len(scenarios),changed_product_files=changed,history_doc_suffixes_equal=prefixes,
        prior_report_reanalysis=reanalysis,thirteen_tool_and_guide_endpoints=endpoints,owned_service_stopped=True,actual_api_dsh_vm_calls=0,
        actual_new_course_collection=False,scope='Independent unit/protocol and old report reanalysis; archived browser source match. Not a new physical device, actual model or Agent task.')
    (Path(__file__).parent/'checks.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(source_files=len(frozen['source_sha256']),snapshots=len(scenarios),prior_reports=len(reanalysis),http_tool_and_guide_routes=len(endpoints)*2,passed=True)))
if __name__=='__main__':main()
