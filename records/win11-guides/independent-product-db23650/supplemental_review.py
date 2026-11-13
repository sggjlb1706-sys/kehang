"""Independent read-only product checks against the externally archived candidate."""
from contextlib import ExitStack
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import threading

EVIDENCE = Path(__file__).resolve().parent
ROOT = EVIDENCE / 'snapshot'
SOURCE = Path(r'C:\Users\DELL\Documents\ChatGPT\传智杯\work\kehang-win11-guides-20261113')
OLD = Path(r'D:\传智杯\versions\kehang-report-guide-20261112')
HEAD = 'db23650271ff580afc0960839cddf98bcf32e0dd'
BASE = '11e52b4f7361dd4efd1453b3b47240650fb74225'
sys.path.insert(0, str(ROOT))
from playwright.sync_api import sync_playwright
from campuslab.web import AppServer

EXPECTED = {
    'python-basics': ['target', 'target'],
    'node-basics': ['target', 'target'],
    'notebook-data': ['target', 'kernel-spec', 'kernel-spec'],
    'java-jdk': ['target', 'target', 'make-command'],
    'sqlite-basics': ['prepare-sqlite', 'target'],
    'pytorch-cpu': ['target', 'make-command'],
    'pytorch-gpu': ['target', 'gpu-run'],
    'local-qwen': ['target', 'model-dir', 'model-dir', 'infer'],
    'vm-linux': ['target', 'vm-id', 'guest-path'],
    'ai-web-deepseek': ['target', 'learning-record'],
    'deepseek-api': ['target', 'api-preview-path', 'api-send'],
    'dsh-desktop': ['target', 'dsh-workspace', 'dsh-evidence'],
    'dsh-cli': ['target', 'dsh-package', 'dsh-workspace', 'dsh-evidence'],
}
PATHS = ['target', 'kernel-spec', 'model-dir', 'vm-id', 'guest-path', 'dsh-package',
         'dsh-workspace', 'dsh-evidence', 'api-preview-path', 'learning-record']
RESULT = dict(candidate=HEAD, baseline=BASE, started_at=datetime.now(timezone.utc).isoformat(),
              groups=[], screenshots=[], page_errors=[], remote_requests=[])
def sha(raw):
    return hashlib.sha256(raw).hexdigest().upper()
def git(*args):
    return subprocess.check_output(['git', '-C', str(SOURCE), *args])
def check(name, **detail):
    RESULT['groups'].append(dict(name=name, passed=True, **detail))

def main():
    manifest=json.loads((ROOT/'records/win11-guides/product.json').read_text(encoding='utf8'))['files']
    for name, digest in manifest.items():
        assert sha((ROOT/name).read_bytes()) == digest, name
        assert sha((SOURCE/name).read_bytes()) == digest, name
        assert sha(git('show', HEAD+':'+name)) == digest, name
    archive=tarfile.open(EVIDENCE/'fixed-source.tar')
    files={m.name:archive.extractfile(m).read() for m in archive.getmembers() if m.isfile()}
    entries=git('ls-tree','-rz','--full-tree',HEAD).split(b'\0')
    tree={entry.split(b'\t',1)[1].decode('utf8') for entry in entries if entry}
    assert set(files)==tree
    assert all((ROOT/name).read_bytes()==value for name,value in files.items())
    check('Fixed Git archive, UTF-8 extraction and frozen file index', frozen_files=len(manifest), tracked_files=len(files))
    changed=git('diff','--name-only',BASE,HEAD,'--','campuslab').decode().splitlines()
    assert changed==['campuslab/web.py'], changed
    old_manifest=OLD/'SHA256SUMS-delivery.json'
    assert sha(old_manifest.read_bytes())=='AFF351EEA7C94062B235420CE597F410B0E3344F00BDF34962F659DFDA67C8D6'
    old_files=json.loads(old_manifest.read_text(encoding='utf8'))
    assert len(old_files)==2529
    for name,digest in old_files.items():
        assert sha((OLD/name).read_bytes())==digest.upper(), name
    check('Old delivery 2529 manifest entries remain unchanged; backend changes limited to fixed assets', old_files=len(old_files))
    with tempfile.TemporaryDirectory(prefix='kehang-independent-win11-') as folder, ExitStack() as stack:
        server=AppServer(0,Path(folder)/'courses.sqlite',ROOT/'vendor/python-3.13.17-embed-amd64.zip')
        threading.Thread(target=server.serve_forever,daemon=True).start()
        stack.callback(server.server_close); stack.callback(server.shutdown)
        origin='http://127.0.0.1:'+str(server.server_port)
        with sync_playwright() as p, ExitStack() as browsers:
            browser=p.chromium.launch(channel='msedge',headless=True);browsers.callback(browser.close)
            page=browser.new_page(viewport=dict(width=1440,height=1100))
            requests=[]
            page.on('request',lambda r:requests.append((r.method,r.url)))
            page.on('pageerror',lambda e:RESULT['page_errors'].append(str(e)))
            def choose(scenario):
                page.click('#home-nav');page.click('#choose-course');page.select_option('#goal',scenario)
                page.locator('#goal-form button').click()
                page.wait_for_function('(s)=>state.task?.scenario===s&&guided.courseStep===1',arg=scenario)
                page.click('#guide-next')
                summary=page.locator('#manual-collection > summary')
                if summary.is_visible() and page.locator('#manual-collection').get_attribute('open') is None:summary.click()
            def invariants(task):
                assert page.evaluate('JSON.stringify(state.task)')==task
                assert not page.evaluate('state.before||state.after||state.analysis')
                assert not any(page.is_checked('#'+x) for x in ['infer','gpu-run','api-send','ai-consent'])
                assert not server.local_check.jobs
                assert not page.locator('#prepare-script').inner_text()
                assert not page.locator('#command').inner_text()
            def capture(name,selector):
                path=EVIDENCE/(name+'.png');page.locator(selector).screenshot(path=path)
                RESULT['screenshots'].append(dict(path=str(path),sha256=sha(path.read_bytes())))
            page.goto(origin);page.wait_for_function('()=>!!state.config&&!!practiceState.practice')
            total=0
            for scenario,fields in EXPECTED.items():
                choose(scenario)
                assert all(not page.locator('#'+x).input_value() for x in PATHS)
                task=page.evaluate('JSON.stringify(state.task)')
                for index,field in enumerate(fields):
                    page.locator('#course-visual-guide .visual-step-button').nth(index).click()
                    jump=page.locator('#course-visual-guide .visual-guide-controls .text-button')
                    for activation in ['mouse','Enter','Space']:
                        count=len(requests)
                        if activation=='mouse':jump.click()
                        else:
                            jump.focus();page.keyboard.press(activation)
                        assert page.evaluate('document.activeElement.id')==field,(scenario,index,activation,field)
                        invariants(task)
                        assert len(requests)==count,(scenario,index,activation,requests[count:])
                        total+=1
                page.evaluate('(ids)=>ids.forEach(id=>document.getElementById(id).value="D:\\OLD\\previous-path")',PATHS)
            check('Every step jump mouse/Enter/Space focuses exact real field without consent, commands or requests', activations=total, courses=len(EXPECTED))
            check('All ten old path inputs cleared on every new course selection', courses=len(EXPECTED))
            choose('java-jdk');jdk=r'D:\课程 JDK\jdk-21';page.fill('#target',jdk)
            page.locator('#course-visual-guide .visual-step-button').nth(1).click()
            assert page.locator('#course-visual-guide .win11-address-text').inner_text()==jdk+'\\bin'
            page.locator('#course-visual-guide .text-button').click()
            assert page.locator('#target').input_value()==jdk
            capture('extra-java-root-bin','#course-visual-guide')
            choose('local-qwen');model=r'D:\课程模型\Qwen2.5-0.5B-Instruct';page.fill('#model-dir',model)
            page.locator('#course-visual-guide .visual-step-button').nth(2).click()
            assert page.locator('#course-visual-guide .win11-address-text').inner_text()==model
            assert 'model.safetensors' in page.locator('#course-visual-guide .win11-file-selected').inner_text()
            page.locator('#course-visual-guide .text-button').click()
            assert page.locator('#model-dir').input_value()==model
            capture('extra-qwen-directory-weights','#course-visual-guide')
            choose('sqlite-basics')
            text=page.locator('#course-visual-guide').inner_text()
            assert all(x in text for x in ['单项课程','连续实训','scores.sqlite'])
            page.locator('#course-visual-guide .text-button').click()
            assert page.evaluate('document.activeElement.id')=='prepare-sqlite'
            assert not page.locator('#prepare-script').inner_text()
            check('JDK bin illustration retains root; Qwen weights illustration retains whole directory; SQLite prepare distinguishes standalone/practice')
            choose('notebook-data')
            literal=r"D:\课程 Python\a'b`$(Write-Output 1)\python.exe"
            page.locator('#course-visual-guide .text-button').click();page.fill('#target',literal)
            page.locator('#course-visual-guide .visual-step-button').nth(1).click()
            shown=page.locator('#course-visual-guide .win11-terminal-body').inner_text()
            expected=page.evaluate('ps(document.getElementById("target").value)')
            assert 'PS> & '+expected+' -m jupyter kernelspec list' in shown
            assert not page.locator('#course-visual-guide img, #course-visual-guide script').count()
            capture('extra-notebook-literal','#course-visual-guide')
            choose('node-basics');page.fill('#target',r'D:\<img src=x onerror=alert(1)>\node.exe')
            page.locator('#course-visual-guide .visual-step-button').nth(1).click()
            assert '<img' in page.locator('#course-visual-guide .win11-address-text').inner_text()
            assert not page.locator('#course-visual-guide img').count()
            check('Notebook command uses existing PowerShell literal encoder; arbitrary entered text remains literal DOM text')
            widths=[320,390,768,1440];steps=0
            for width in widths:
                page.set_viewport_size(dict(width=width,height=1000))
                for scenario,fields in EXPECTED.items():
                    choose(scenario)
                    for index in range(len(fields)):
                        page.locator('#course-visual-guide .visual-step-button').nth(index).click()
                        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(width,scenario,index)
                        steps+=1
                page.fill('#tool-dir','D:\\课航 工具\\'+('较长文件夹名称'*15));page.select_option('#report-stage','B')
                page.locator('#report-extension-help summary').click()
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(width,'report')
                assert page.locator('#report-example-file').inner_text()=='report-B.json'
                if width==320:capture('extra-report-320','#report-extension-window')
                page.click('#home-nav');page.click('#start-practice');page.click('#guide-next');page.click('#guide-next')
                for button in page.locator('#practice-visual-guide .visual-step-button').all():
                    button.click();assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                assert page.locator('#practice-read').is_visible() and not page.is_checked('#practice-read')
                if width==390:capture('extra-practice-390','#practice-visual-guide')
                page.click('#guide-next');jump=page.locator('#practice-submit-guide .text-button')
                for key in ['Enter','Space']:
                    jump.focus();page.keyboard.press(key)
                    assert page.evaluate('document.activeElement.id')=='practice-submission'
                    assert not page.locator('#practice-result').inner_text()
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            check('All 13 courses and every step at 320/390/768/1440; report extension menu and practice reflow', course_step_views=steps, widths=widths)
            page.set_viewport_size(dict(width=1440,height=1100));choose('python-basics')
            capture('extra-python-properties','#course-visual-guide')
            page.locator('#course-visual-guide .visual-step-button').nth(1).focus();page.keyboard.press('Enter')
            focus=page.locator('#course-visual-guide .visual-step-button').nth(1).evaluate('(e)=>({visible:e.matches(":focus-visible"),outline:getComputedStyle(e).outlineStyle,width:getComputedStyle(e).outlineWidth})')
            assert focus['visible'] and focus['outline']!='none' and focus['width']!='0px',focus
            assert page.locator('#course-visual-guide [aria-current="step"]').count()==1
            check('Keyboard focus outline and single current step', focus=focus)
            RESULT['remote_requests']=[url for method,url in requests if not url.startswith(origin+'/')]
            assert not RESULT['remote_requests'] and not RESULT['page_errors'] and not server.local_check.jobs
            check('No page error, remote request, local-check job, or evidence fabrication in supplemental illustration navigation')
    RESULT['passed']=True

try:
    main()
except Exception as exc:
    RESULT.update(passed=False,error=repr(exc))
    raise
finally:
    RESULT['finished_at']=datetime.now(timezone.utc).isoformat()
    (EVIDENCE/'supplemental-result.json').write_text(json.dumps(RESULT,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(dict(passed=RESULT.get('passed',False),groups=len(RESULT['groups'])),ensure_ascii=False))
