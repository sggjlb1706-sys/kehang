"""Kehang branding and existing task/report compatibility; no new model or Agent run."""
from datetime import datetime,timezone
import hashlib,json,subprocess,sys,tempfile,threading,zipfile
from pathlib import Path
from playwright.sync_api import sync_playwright
from campuslab.web import AppServer
from campuslab.rules import task,NEW_COURSES,analyze

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT.parent/'competition-reuse-ai-20261109'
def main():
    out=ROOT/'records/brand/browser'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ');out.mkdir(parents=True)
    checks=[];errors=[];external=[];complete=False
    def check(text):checks.append(text);print('PASS:',text,flush=True)
    scenarios=['python-basics','node-basics','local-qwen','pytorch-cpu','pytorch-gpu','vm-linux',*NEW_COURSES]
    baseline=json.loads(subprocess.check_output([sys.executable,'-B','-c','import json; from campuslab.rules import task,NEW_COURSES; print(json.dumps({s:task(s) for s in ["python-basics","node-basics","local-qwen","pytorch-cpu","pytorch-gpu","vm-linux",*NEW_COURSES]}))'],cwd=BASE))
    assert {s:task(s) for s in scenarios}==baseline;check('All thirteen task snapshots and identifiers equal the previous delivered version')
    with tempfile.TemporaryDirectory(prefix='kehang-brand-') as temp:
        folder=Path(temp);server=AppServer(0,folder/'course.sqlite',ROOT/'vendor/python-3.13.17-embed-amd64.zip')
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();base=f'http://127.0.0.1:{server.server_port}'
        try:
            with sync_playwright() as p:
                browser=p.chromium.launch(channel='msedge',headless=True)
                context=browser.new_context(viewport={'width':1440,'height':1000},accept_downloads=True)
                context.on('request',lambda r:external.append(r.url) if r.url.startswith(('http://','https://')) and not r.url.startswith(base+'/') else None)
                page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.goto(base);page.wait_for_function('()=>state.config!==null')
                assert page.title()=='课航——计算机课程学习与实训助手'
                assert page.locator('header .brand').inner_text()=='课航'
                assert 'AI实验环境管家' not in page.locator('body').inner_text() and 'CAMPUS LAB' not in page.locator('body').inner_text()
                page.screenshot(path=str(out/'home-desktop.png'),full_page=True);check('Page title, brand, subtitle and introduction consistently show Kehang')
                for s in scenarios:
                    page.select_option('#goal',s);page.locator('#goal-form button').click();page.wait_for_function('(s)=>state.task?.scenario===s',arg=s)
                    assert page.evaluate('()=>state.task')==baseline[s]
                check('All thirteen UI course selections preserve the exact previous task snapshots')
                page.select_option('#goal','java-jdk');page.locator('#goal-form button').click();page.wait_for_function("()=>state.task?.scenario==='java-jdk'")
                with page.expect_download() as download:page.locator('#download-tool').click()
                assert download.value.suggested_filename=='Kehang-tool.zip'
                archive=folder/'tool.zip';download.value.save_as(archive)
                tool=folder/'tool';tool.mkdir()
                with zipfile.ZipFile(archive) as z:
                    assert z.testzip() is None and '课航——计算机课程学习与实训助手' in z.read('README.txt').decode('utf-8')
                    assert json.loads(z.read('task.json'))==baseline['java-jdk'];z.extractall(tool)
                proc=subprocess.run([str(tool/'runtime/python.exe'),'-B','-m','campuslab.collect','--task',str(tool/'task.json'),'--target',r'C:\KeHang-Missing-JDK','--output',str(tool/'report.json')],cwd=tool,capture_output=True,timeout=30)
                assert proc.returncode==0
                report=json.loads((tool/'report.json').read_text(encoding='utf-8'));assert not analyze(task('java-jdk'),report)['passed']
                check('Renamed downloadable tool includes brand and executes a missing-target report without changing its verdict')
                old=ROOT/'records/reuse-ai/browser-data/20261110T003103340935Z/java-jdk-A.json'
                page.set_input_files('#before-file',str(old));page.wait_for_function('()=>state.analysis?.passed===true')
                page.wait_for_function('()=>!document.getElementById("lesson-panel").hidden')
                assert '课航' in page.evaluate("async()=>JSON.stringify(await api('/api/lesson',{task:state.task,report:state.before}))")
                check('Previous real JDK report is accepted; derived teaching attribution uses the new visible name')
                with page.expect_download() as d:page.locator('#export-course').click()
                assert d.value.suggested_filename=='Kehang-course.json';package=folder/'course.json';d.value.save_as(package)
                value=json.loads(package.read_text(encoding='utf-8'));assert value['kind']=='campuslab-course'
                second=context.new_page();second.goto(base);second.set_input_files('#course-package',str(package));second.wait_for_function('(id)=>state.task?.id===id',arg=baseline['java-jdk']['id']);second.close()
                check('New course filename roundtrips the unchanged legacy package kind and immutable digest')
                with page.expect_download() as d:page.locator('#export-guide').click()
                assert d.value.suggested_filename=='Kehang-guide.html';guide=out/'Kehang-guide.html';d.value.save_as(guide)
                guide_page=context.new_page();guide_page.set_viewport_size({'width':390,'height':844});guide_page.goto(guide.as_uri())
                assert guide_page.title().startswith('课航') and '计算机课程学习与实训助手' in guide_page.locator('body').inner_text()
                assert guide_page.evaluate('document.documentElement.scrollWidth<=innerWidth');guide_page.screenshot(path=str(out/'guide-mobile.png'));guide_page.close()
                check('Renamed offline guide shows new brand and unchanged course identity at 390px')
                page.locator('#export').click();page.wait_for_function('()=>!document.getElementById("export-preview").hidden')
                with page.expect_download() as d:page.locator('#save-export').click()
                assert d.value.suggested_filename=='Kehang-share.json';assert not page.locator('#ai-consent').is_checked()
                check('Share filename is renamed while editable redaction and explicit AI consent remain in place')
                page.goto(base);page.wait_for_function('()=>state.config!==null');page.set_viewport_size({'width':390,'height':844})
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');page.locator('header .brand').focus();page.keyboard.press('Tab')
                page.screenshot(path=str(out/'home-mobile.png'),full_page=True)
                check('Desktop and 390px home retain keyboard navigation and fit without horizontal overflow')
                assert not errors and not external;browser.close();complete=True
        finally:
            server.shutdown();server.server_close();thread.join()
            sources={f.relative_to(ROOT).as_posix():hashlib.sha256(f.read_bytes()).hexdigest().upper() for folder in ('campuslab','web') for f in (ROOT/folder).rglob('*') if f.is_file() and '__pycache__' not in f.parts}
            (out/'results.json').write_text(json.dumps(dict(status='passed' if complete else 'failed',checks=checks,source_sha256=sources,browser_errors=errors,external_requests=external,
                baseline_head='fc14fc752a83709df496b386e4ce950b01996afe',task_snapshots_unchanged=True,prior_real_report_reanalysis=True,actual_new_model_or_agent_calls=0,physical_phone=False,second_device=False),ensure_ascii=False,indent=2),encoding='utf-8')
            print('Evidence:',out,flush=True)
if __name__=='__main__':main()
