"""Actual Edge + downloaded runtime + PS5.1. Not a clean-device or novice-user test."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import threading
import zipfile

from playwright.sync_api import sync_playwright
from campuslab.rules import analyze
from campuslab.web import AppServer

ROOT=Path(__file__).resolve().parents[1]
RUNTIME=Path('D:/传智杯/artifacts/portable-runtime/python-3.13.17-embed-amd64.zip')


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest().upper()


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=ROOT/'records/browser'/run_id;out.mkdir(parents=True)
    working=ROOT/'records/runtime'/run_id;working.mkdir(parents=True)
    server=AppServer(0,working/'course.sqlite',RUNTIME)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    base=f'http://127.0.0.1:{server.server_port}'
    checks=[];errors=[];external=[];internal=[];executions=[];completed=False
    def check(name):
        checks.append(name);print('PASS:',name,flush=True)
    def ps_command(page,name):
        page.locator('#make-command').click()
        command=page.locator('#command').inner_text();assert command
        script=out/(name+'.ps1');script.write_text(command,encoding='utf-8-sig')
        proc=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(script)],capture_output=True,timeout=70)
        (out/(name+'.stdout.txt')).write_bytes(proc.stdout)
        (out/(name+'.stderr.txt')).write_bytes(proc.stderr)
        executions.append(dict(name=name,returncode=proc.returncode,script=script.name))
        return proc
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(channel='msedge',headless=True)
            context=browser.new_context(viewport={'width':1440,'height':1000},accept_downloads=True)
            page=context.new_page()
            page.on('pageerror',lambda e:errors.append(str(e)))
            def record_request(request):
                if request.url.startswith(('http://','https://')) and not request.url.startswith(base+'/'):
                    external.append(request.url)
                elif request.url.startswith('edge:'):
                    internal.append(request.url)
            context.on('request',record_request)
            page.goto(base);page.wait_for_function('()=>state.config !== null')
            page.locator('#goal-form button').click();page.wait_for_selector('#guidance li')
            assert page.locator('#results .check').count()==0
            page.select_option('#prepared','missing');page.wait_for_function("()=>document.getElementById('prepared-hint').textContent.includes('自行安装')")
            assert page.locator('#results .check').count()==0
            check('Supported goal and preparation never imply environmental success')
            with page.expect_download() as dl:page.locator('#download-tool').click()
            archive=out/'downloaded-tool.zip';dl.value.save_as(archive)
            tool=working/"工具 O'Brien";tool.mkdir()
            with zipfile.ZipFile(archive) as z:
                assert z.testzip() is None;z.extractall(tool)
            page.locator('#command-panel').evaluate('(e)=>e.open=true')
            page.fill('#tool-dir',str(tool));page.fill('#target','D:\\ANACONDA\\python.exe')
            assert ps_command(page,'actual-A').returncode==0
            page.select_option('#report-stage','B')
            assert ps_command(page,'actual-B').returncode==0
            before=tool/'report-A.json';after=tool/'report-B.json'
            for name,source in [('actual-A.json',before),('actual-B.json',after)]: (out/name).write_bytes(source.read_bytes())
            page.set_input_files('#before-file',str(before));page.wait_for_selector('#results .check')
            page.set_input_files('#after-file',str(after));page.wait_for_function("()=>document.getElementById('comparison').textContent.includes('稳定复检通过')")
            assert page.locator('#results .state-pass').count()==4
            check('Downloaded embedded runtime and exact generated PS5.1 commands produce actual stable A/B')
            facts=page.locator('#results').inner_text()
            for mode in ['quick','standard','novice']:
                page.select_option('#mode',mode);page.wait_for_function('(m)=>document.querySelectorAll("#guidance li").length===(m==="quick"?2:m==="novice"?6:5)',arg=mode)
                assert page.locator('#results').inner_text()==facts
            check('Three guidance modes preserve identical report facts')
            page.fill('#user-error','Example only: sk-abcdefghijklmnop C:\\Users\\Example\\x')
            page.locator('#prepare-ai').click();page.wait_for_selector('#ai-preview-panel')
            preview=page.locator('#ai-preview').input_value()
            assert 'sk-abcdefghijklmnop' not in preview and 'Example\\x' not in preview
            assert page.locator('#send-ai').is_disabled()
            page.locator('#export').click()
            assert json.loads(page.locator('#export-preview').input_value())['share_only'] is True
            page.screenshot(path=str(out/'python-workflow.png'),full_page=True)
            check('Redacted editable preview and unconfigured AI preserve facts without sending')
            missing_tool=working/'missing-target';missing_tool.mkdir()
            with zipfile.ZipFile(archive) as z:z.extractall(missing_tool)
            page.fill('#tool-dir',str(missing_tool));page.fill('#target','C:\\CampusLab-Deliberately-Missing\\python.exe');page.select_option('#report-stage','A')
            assert ps_command(page,'missing-target').returncode==0
            missing=missing_tool/'report-A.json'
            page.set_input_files('#before-file',str(missing));page.wait_for_selector('#results .state-missing')
            assert page.locator('#results .state-pass').count()==1
            (out/'missing-target.json').write_bytes(missing.read_bytes())
            page.fill('#target',str(missing_tool/'runtime/python.exe'));page.select_option('#report-stage','B')
            assert ps_command(page,'reject-tool-runtime').returncode!=0
            assert not (missing_tool/'report-B.json').exists()
            check('Deliberately missing target remains missing/unknown; bundled interpreter rejected')
            page.locator('#teacher-form').evaluate('(e)=>e.closest("details").open=true')
            page.fill('#teacher-title','真实浏览器测试课程');page.fill('#python-min','3.14')
            page.locator('#teacher-form button').click();page.wait_for_function("()=>document.getElementById('task-title').textContent==='真实浏览器测试课程'")
            spec=page.evaluate('()=>state.task');code=page.evaluate('()=>state.course')
            (out/'published-course.json').write_text(json.dumps({'code':code,'task':spec},ensure_ascii=False,indent=2),encoding='utf-8')
            second=context.new_page();second.goto(base+'/?course='+code);second.wait_for_function('(id)=>state.task?.id===id',arg=spec['id']);second.close()
            page.set_input_files('#before-file',str(before));page.wait_for_function("()=>document.getElementById('notice').classList.contains('error')")
            assert page.locator('#results .check').count()==0
            check('Published immutable course opens through code and rejects another task report')
            page.select_option('#goal','local-qwen');page.locator('#goal-form button').click();page.wait_for_function("()=>state.task?.scenario==='local-qwen'")
            page.set_input_files('#before-file',str(ROOT/'records/iteration-3/before.json'));page.wait_for_selector('#results .state-unknown')
            page.set_input_files('#after-file',str(ROOT/'records/iteration-3/after.json'));page.wait_for_function("()=>document.getElementById('comparison').textContent.includes('补齐实际运行证据')")
            assert page.locator('#results .state-pass').count()==7
            page.screenshot(path=str(out/'local-model-workflow.png'),full_page=True)
            check('Actual fixed offline Qwen evidence is consumed by the same course/report workflow')
            page.select_option('#goal','other');assert page.locator('#task-panel').is_hidden()
            page.locator('#goal-form button').click();page.wait_for_function("()=>document.getElementById('notice').classList.contains('error')")
            assert page.locator('#results .check').count()==0
            check('Unsupported goal clears old successful evidence')
            page.select_option('#goal','python-basics');page.locator('#goal-form button').click();page.wait_for_selector('#guidance li')
            pending=[]
            page.route('**/api/analyze',lambda route:pending.append(route))
            page.set_input_files('#before-file',str(before));page.wait_for_timeout(150)
            assert pending
            page.select_option('#goal','other')
            report=json.loads(before.read_text(encoding='utf-8'))
            spec=json.loads((tool/'task.json').read_text(encoding='utf-8'))
            pending[0].fulfill(status=200,content_type='application/json',body=json.dumps(analyze(spec,report)))
            page.wait_for_timeout(150)
            assert page.locator('#task-panel').is_hidden() and page.locator('#results .check').count()==0
            page.unroute('**/api/analyze')
            check('Delayed old analysis cannot restore results after changing goal')
            page.set_viewport_size({'width':390,'height':844});page.goto(base)
            page.locator('#goal-form button').click();page.wait_for_selector('#guidance li')
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            page.screenshot(path=str(out/'mobile-390.png'),full_page=True)
            check('390px mobile layout has no horizontal overflow')
            assert not errors,errors
            assert not external,external
            browser.close()
            completed=True
    finally:
        server.shutdown();server.server_close();thread.join()
        source={p.relative_to(ROOT).as_posix():sha(p) for folder in ['campuslab','web'] for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts}
        result=dict(status='passed' if completed else 'failed',checks=checks,passed=len(checks),browser_errors=errors,external_requests=external,browser_internal_requests=len(internal),executions=executions,
                    source_sha256=source,python_installed_on_host=True,clean_device_test=False,physical_phone_test=False,
                    install_calls=0,paid_model_requests=0,ai_mock_tests_separate=True)
        (out/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print('Evidence:',out,flush=True)


if __name__=='__main__':main()
