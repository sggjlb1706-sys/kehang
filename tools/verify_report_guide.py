"""Exercise visual report-finding guidance and the preserved report contract."""
from contextlib import ExitStack
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import threading

from playwright.sync_api import sync_playwright
from campuslab.collect import collect
from campuslab.rules import task
from campuslab.web import AppServer

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'records/report-guide' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')


def main():
    OUT.mkdir(parents=True)
    checks, shots, errors, remote = [], [], [], []
    result = dict(checks=checks, screenshots=shots, page_errors=errors, remote_requests=remote,
                  scope='Same-computer agent browser; real Node A/B when available, archived real Python reports for compatibility. Guidance drawings are labelled examples, not filesystem discovery. No model request or installation.')
    def save(name, data):
        path=OUT/name;path.parent.mkdir(exist_ok=True);path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8',newline='\n')
    try:
        with tempfile.TemporaryDirectory(prefix='kehang-report-guide-') as folder, ExitStack() as stack:
            server=AppServer(0,Path(folder)/'courses.sqlite',ROOT/'vendor/python-3.13.17-embed-amd64.zip')
            threading.Thread(target=server.serve_forever,daemon=True).start()
            stack.callback(server.server_close);stack.callback(server.shutdown)
            origin='http://127.0.0.1:'+str(server.server_port)
            with sync_playwright() as p, ExitStack() as browser_stack:
                browser=p.chromium.launch(channel='msedge',headless=True);browser_stack.callback(browser.close)
                context=browser.new_context(viewport=dict(width=1440,height=1000),permissions=['clipboard-read','clipboard-write'])
                page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
                page.on('request',lambda r:remote.append(r.url) if r.url.startswith(('http://','https://')) and not r.url.startswith(origin+'/') else None)
                def capture(name):
                    path=OUT/(name+'.png');page.screenshot(path=path,full_page=True)
                    shots.append(dict(path=path.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
                def choose(scenario):
                    page.click('#home-nav');page.click('#choose-course');page.select_option('#goal',scenario)
                    page.locator('#goal-form button').click();page.wait_for_function('(s)=>state.task?.scenario===s&&guided.courseStep===1',arg=scenario)
                    page.click('#guide-next')
                    if page.locator('#manual-collection > summary').is_visible() and not page.locator('#manual-collection').get_attribute('open'):
                        page.locator('#manual-collection > summary').click()
                page.goto(origin);page.wait_for_function('()=>!!state.config&&!!practiceState.practice')
                choose('node-basics')
                assert page.locator('#node-target-guide').is_visible()
                assert page.locator('.report-steps > li').count()==3
                assert page.locator('#report-example-file').inner_text()=='report-A.json'
                assert not page.locator('#copy-report-folder').is_visible()
                assert not server.local_check.jobs
                checks.append('Manual Node flow has a three-step labelled visual guide; unknown extraction directory is not fabricated and opens no local detection job')
                directory=r'D:\Kehang-tool (2)'
                page.fill('#tool-dir',directory)
                assert page.locator('#report-folder-address').input_value()==directory
                page.click('#copy-report-folder')
                page.wait_for_function('()=>document.getElementById("report-copy-status").textContent.includes("地址已复制")')
                assert page.evaluate('navigator.clipboard.readText()')==directory
                page.fill('#target',r'C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Node.js')
                page.click('#make-command')
                assert not page.locator('#command').inner_text()
                assert 'node.exe 程序文件' in page.locator('#notice').inner_text()
                checks.append('Actual clipboard copy preserves the entered directory; the reported Start Menu folder cannot generate a misleading Node collector command')
                node=shutil.which('node.exe');assert node,'Existing Node required for this same-computer acceptance'
                page.fill('#target','"'+node+'"');page.click('#make-command')
                command=page.locator('#command').inner_text()
                assert '--target $taskTarget' in command and 'report-A.json' in command and '报告已保存' in command
                assert command.index('if ($LASTEXITCODE')<command.index("Write-Host ('报告已保存")
                capture('01-node-report-A-desktop')
                checks.append('A quoted real node.exe is accepted; generated manual command names the same A output and prints its location only after successful collection')
                # Explicit test execution of existing fixed Node collector, not a browser execution endpoint.
                spec=task('node-basics');before=collect(spec,node);save('real-node/report-A.json',before)
                page.set_input_files('#report-files',OUT/'real-node/report-A.json')
                page.wait_for_function('()=>!!state.before&&!!state.analysis');page.click('#guide-next');page.click('#guide-next')
                assert page.locator('#report-stage').input_value()=='B'
                assert page.locator('#report-files').evaluate('e=>e.files.length')==0
                assert page.locator('#report-example-file').inner_text()=='report-B.json'
                assert page.locator('#report-earlier-file').is_visible()
                assert page.locator('#report-folder-address').input_value()==directory
                page.locator('#report-upload-title').scroll_into_view_if_needed();capture('02-node-report-B-desktop')
                path=OUT/'report-steps-B.png';page.locator('.report-steps').screenshot(path=path)
                shots.append(dict(path=path.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
                after=collect(spec,node);save('real-node/report-B.json',after)
                page.set_input_files('#report-files',OUT/'real-node/report-B.json');page.wait_for_function('()=>!!state.after')
                assert page.evaluate('state.before.collected_at')==before['collected_at']
                assert page.evaluate('state.after.target.requested===state.before.target.requested')
                save('real-node/browser-result.json',page.evaluate('({before:state.before,after:state.after,analysis:state.analysis})'))
                checks.append('Fresh actual Node A/B imports preserve original baseline and identity; B guide clears old file selection and highlights the new file while retaining the A example')
                choose('notebook-data')
                assert page.locator('#tool-dir').input_value()=='' and not page.locator('#copy-report-folder').is_visible()
                assert page.locator('#report-example-file').inner_text()=='report-A.json'
                assert not page.locator('#node-target-guide').is_visible()
                assert 'task.json' in page.locator('#report-folder-tip').inner_text()
                page.locator('#report-upload-title').scroll_into_view_if_needed();capture('03-notebook-no-directory')
                checks.append('Switching to Notebook removes stale directory/B guidance and Node hints; simple launcher users see the honest extraction-folder example')
                # Clipboard denied/unavailable: keyboard selection fallback is usable without unrelated navigation.
                choose('node-basics');page.fill('#tool-dir',directory)
                page.evaluate("Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async()=>{throw Error('controlled denial')}}})")
                page.click('#copy-report-folder')
                page.wait_for_function('()=>document.getElementById("report-copy-status").textContent.includes("Ctrl + C")')
                assert page.locator('#report-folder-address').evaluate('e=>e===document.activeElement&&e.selectionStart===0&&e.selectionEnd===e.value.length')
                checks.append('Clipboard denial leaves the current guide intact and selects the exact address for Ctrl+C')
                archived=ROOT/'records/practice/lab-run/python-basics-A.json'
                choose('python-basics')
                bad=Path(folder)/'bad.json';bad.write_text('{"share_only":true}',encoding='utf8')
                page.set_input_files('#report-files',bad);page.wait_for_function('()=>document.getElementById("notice").classList.contains("error")')
                assert not page.evaluate('state.before||state.analysis')
                page.set_input_files('#report-files',archived);page.wait_for_function('()=>!!state.before&&!!state.analysis')
                checks.append('The illustrated chooser retains real report validation: sharing-only input rejected, existing valid original accepted')
                choose('node-basics');page.fill('#tool-dir','D:\\课航 工具\\'+('较长文件夹名称'*5));page.select_option('#report-stage','B')
                for width,height in [(390,844),(768,900),(1440,1000)]:
                    page.set_viewport_size(dict(width=width,height=height));page.locator('#report-upload-title').scroll_into_view_if_needed()
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),width
                    assert page.locator('#report-example-file').inner_text()=='report-B.json'
                    if width==390:capture('04-node-report-B-mobile')
                checks.append('390/768/1440 layouts preserve all three steps, selected B filename and long-path copy without horizontal overflow')
                assert not errors and not remote
                result['passed']=True
    except Exception as exc:
        result.update(passed=False,error=repr(exc));raise
    finally:
        save('result.json',result)
        print(json.dumps(dict(passed=result.get('passed',False),path=str(OUT/'result.json'),groups=len(checks)),ensure_ascii=False))


if __name__=='__main__':main()
