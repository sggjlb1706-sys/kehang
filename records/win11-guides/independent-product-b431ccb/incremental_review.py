"""Close independent finding W11-01 on the final fixed candidate, with prior executed proofs retained."""
from contextlib import ExitStack
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading

EVIDENCE=Path(__file__).resolve().parent
ROOT=EVIDENCE/'snapshot'
SOURCE=Path(r'C:\Users\DELL\Documents\ChatGPT\传智杯\work\kehang-win11-guides-20261113')
INITIAL='db23650271ff580afc0960839cddf98bcf32e0dd'
FINAL='b431ccb1ca58750fdbc78d5ab2f69d272b793701'
sys.path.insert(0,str(ROOT))
from campuslab.web import AppServer
from playwright.sync_api import sync_playwright

def git(*args):return subprocess.check_output(['git','-C',str(SOURCE),*args])
def sha(value):return hashlib.sha256(value).hexdigest().upper()
result=dict(candidate=FINAL,initial_candidate=INITIAL,checks=[],page_errors=[],remote_requests=[],screenshots=[])
def check(name,**detail):result['checks'].append(dict(name=name,passed=True,**detail))

try:
    old_index=json.loads(git('show',INITIAL+':records/win11-guides/product.json'))['files']
    index=json.loads(git('show',FINAL+':records/win11-guides/product.json'))['files']
    assert set(index)==set(old_index) and len(index)==54
    changed=[name for name,digest in index.items() if old_index[name]!=digest]
    assert changed==['web/visual-guides.js'],changed
    for name,digest in index.items():
        assert sha(git('show',FINAL+':'+name))==digest,name
        assert sha((ROOT/name).read_bytes())==digest,name
        assert sha((SOURCE/name).read_bytes())==digest,name
    assert not git('diff','--name-only',INITIAL,FINAL,'--','campuslab','tests','tools')
    check('54 final frozen files match Git/archive/worktree; 53 unchanged; backend, tests and verification tools byte-identical', frozen_files=54,unchanged_frozen_files=53)
    before=git('show',INITIAL+':web/visual-guides.js').decode('utf8')
    after=git('show',FINAL+':web/visual-guides.js').decode('utf8')
    assert before.replace("path:'开始菜单中的程序快捷方式'","path:'通过“打开文件所在的位置”进入的快捷方式文件夹'").replace(
        '开始菜单右键程序快捷方式，打开“属性”，看“目标”里的完整程序路径。',
        '开始菜单右键程序 → 更多／打开文件所在的位置 → 在打开的文件夹里右键快捷方式 → 属性。复制“目标”中的程序路径。')==after
    check('The only product edits are the two accepted shortcut instructions; W11-01 source fix verified')
    with tempfile.TemporaryDirectory(prefix='kehang-independent-final-') as folder,ExitStack() as stack:
        server=AppServer(0,Path(folder)/'courses.sqlite',ROOT/'vendor/python-3.13.17-embed-amd64.zip')
        threading.Thread(target=server.serve_forever,daemon=True).start();stack.callback(server.server_close);stack.callback(server.shutdown)
        origin='http://127.0.0.1:'+str(server.server_port)
        with sync_playwright() as p,ExitStack() as browsers:
            browser=p.chromium.launch(channel='msedge',headless=True);browsers.callback(browser.close)
            page=browser.new_page(viewport=dict(width=1440,height=1100))
            requests=[];page.on('request',lambda r:requests.append(r.url));page.on('pageerror',lambda e:result['page_errors'].append(str(e)))
            page.goto(origin);page.wait_for_function('()=>!!state.config&&!!practiceState.practice')
            activations=0
            for scenario in ['python-basics','node-basics']:
                for width in [320,390,1440]:
                    page.set_viewport_size(dict(width=width,height=1100))
                    page.click('#home-nav');page.click('#choose-course');page.select_option('#goal',scenario);page.locator('#goal-form button').click()
                    page.wait_for_function('(s)=>state.task?.scenario===s&&guided.courseStep===1',arg=scenario);page.click('#guide-next')
                    if page.locator('#manual-collection > summary').is_visible() and page.locator('#manual-collection').get_attribute('open') is None:page.locator('#manual-collection > summary').click()
                    host=page.locator('#course-visual-guide');step=host.locator('.visual-step-button')
                    step.nth(1).focus();page.keyboard.press('Enter');step.first.focus();page.keyboard.press('Space')
                    assert host.locator('.visual-step-count').inner_text()=='1 / 2'
                    assert step.first.get_attribute('aria-current')=='step'
                    assert step.first.evaluate('e=>e.matches(":focus-visible")&&getComputedStyle(e).outlineWidth==="3px"')
                    text=host.locator('.visual-step-instruction').inner_text()
                    assert all(x in text for x in ['开始菜单','更多／打开文件所在的位置','在打开的文件夹里右键快捷方式','属性','复制“目标”'])
                    assert host.locator('.win11-address-text').inner_text()=='通过“打开文件所在的位置”进入的快捷方式文件夹'
                    assert '快捷方式' in host.locator('.win11-file-selected').inner_text()
                    assert not page.locator('#target').input_value()
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                    path=EVIDENCE/(scenario+'-'+str(width)+'.png');host.screenshot(path=path)
                    result['screenshots'].append(dict(path=str(path),sha256=sha(path.read_bytes())))
                    for key in ['Enter','Space']:
                        count=len(requests);host.locator('.visual-guide-controls .text-button').focus();page.keyboard.press(key)
                        assert page.evaluate('document.activeElement.id')=='target'
                        assert not any(page.is_checked('#'+x) for x in ['infer','gpu-run','api-send','ai-consent'])
                        assert not page.evaluate('state.before||state.after||state.analysis') and not server.local_check.jobs
                        assert len(requests)==count
                        activations+=1
            check('Final Python/Node first scene, current step and focus at 320/390/1440; Enter/Space jump remains focus-only',field_activations=activations)
            result['remote_requests']=[url for url in requests if not url.startswith(origin+'/')]
            assert not result['page_errors'] and not result['remote_requests']
            check('No browser error or remote request in the final incremental run')
    result.update(passed=True,finding_W11_01='closed',unresolved_count=0)
except Exception as exc:
    result.update(passed=False,error=repr(exc));raise
finally:
    (EVIDENCE/'incremental-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(dict(passed=result.get('passed',False),groups=len(result['checks'])),ensure_ascii=False))
