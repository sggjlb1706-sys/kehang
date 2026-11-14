"""All existing course illustrations; navigation never substitutes for evidence."""
from contextlib import ExitStack
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tempfile
import threading

from playwright.sync_api import sync_playwright
from campuslab.web import AppServer

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'records/round2/diagrams'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
COURSES=['python-basics','node-basics','notebook-data','java-jdk','sqlite-basics','pytorch-cpu','pytorch-gpu','local-qwen','vm-linux','ai-web-deepseek','deepseek-api','dsh-desktop','dsh-cli']


def main():
    OUT.mkdir(parents=True)
    checks,shots,errors,requests=[],[],[],[]
    result=dict(checks=checks,screenshots=shots,page_errors=errors,side_effect_requests=requests,
                scope='Same-computer agent browser, illustrated workflow/keyboard/reflow/contract verification only; no course collector, installation, real model request or external-device acceptance.')
    try:
        with tempfile.TemporaryDirectory(prefix='kehang-win11-') as folder,ExitStack() as stack:
            server=AppServer(0,Path(folder)/'courses.sqlite',ROOT/'vendor/python-3.13.17-embed-amd64.zip')
            threading.Thread(target=server.serve_forever,daemon=True).start();stack.callback(server.server_close);stack.callback(server.shutdown)
            origin='http://127.0.0.1:'+str(server.server_port)
            with sync_playwright() as p,ExitStack() as browsers:
                browser=p.chromium.launch(channel='msedge',headless=True);browsers.callback(browser.close)
                page=browser.new_page(viewport=dict(width=1440,height=1100))
                page.on('pageerror',lambda e:errors.append(str(e)))
                def watch(request):
                    if not request.url.startswith(origin+'/') or request.url.endswith(('/api/local-check','/api/diagnose')):requests.append(request.url)
                page.on('request',watch)
                page.goto(origin);page.wait_for_function('()=>!!state.config&&!!practiceState.practice')
                page.click('#welcome-start')
                assert set(page.evaluate('KehangVisuals.scenarios'))==set(COURSES)
                ids=page.locator('[id]').evaluate_all('(es)=>es.map(e=>e.id)');assert len(ids)==len(set(ids))
                def choose(scenario):
                    page.click('#home-nav');page.click('#choose-course');page.select_option('#goal',scenario);page.locator('#goal-form button').click()
                    page.wait_for_function('(s)=>state.task?.scenario===s&&guided.courseStep===1',arg=scenario);page.click('#guide-next')
                    if page.locator('#manual-collection > summary').is_visible() and not page.locator('#manual-collection').get_attribute('open'):page.locator('#manual-collection > summary').click()
                def capture(name,selector):
                    box=page.locator(selector);box.evaluate("e=>e.scrollIntoView({block:'center'})")
                    path=OUT/(name+'.png');box.screenshot(path=path)
                    shots.append(dict(path=path.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
                for scenario in COURSES:
                    choose(scenario);host=page.locator('#course-visual-guide')
                    assert host.is_visible() and host.get_attribute('data-course')==scenario
                    assert not page.locator('#target').input_value(),'New course must not inherit an old path'
                    task=page.evaluate('JSON.stringify(state.task)')
                    buttons=host.locator('.visual-step-button');count=buttons.count();assert count>=2
                    for index in range(count):
                        buttons.nth(index).click()
                        assert host.locator('.win11-window').is_visible()
                        assert host.locator('.visual-step-count').inner_text()==str(index+1)+' / '+str(count)
                        assert page.evaluate('JSON.stringify(state.task)')==task
                        assert not page.evaluate('state.before||state.after||state.analysis')
                        assert not any(page.is_checked('#'+name) for name in ['infer','gpu-run','api-send','ai-consent'])
                        jump=host.locator('.visual-guide-controls .text-button')
                        if jump.is_visible():
                            jump.click();assert page.evaluate('document.activeElement.id') not in ('','guide-title')
                    buttons.first.click();capture(scenario+'-desktop','#course-visual-guide')
                    checks.append(dict(course=scenario,steps=count,all_steps_visible=True,facts_unchanged=True))
                choose('node-basics')
                page.fill('#target',r'D:\课程 环境\node.exe');page.locator('#course-visual-guide .visual-step-button').nth(1).click()
                assert r'D:\课程 环境' in page.locator('#course-visual-guide .win11-address-text').inner_text()
                assert page.locator('#course-visual-guide .win11-file-selected').inner_text().startswith('EXE')
                page.fill('#tool-dir',r'D:\课航\<img src=x onerror=alert(1)>')
                assert not page.locator('#report-explorer-window img').count()
                assert '<img' in page.locator('#report-explorer-window .win11-address-text').inner_text()
                page.select_option('#report-stage','B')
                assert page.locator('#report-example-file').inner_text()=='report-B.json' and page.locator('#report-earlier-file').is_visible()
                page.locator('#report-extension-help summary').click()
                assert '文件扩展名' in page.locator('#report-extension-window .win11-view-submenu').inner_text()
                checks.append(dict(case='Live entered path, literal-safe text, B report and Windows11 extension help',passed=True))
                choose('notebook-data');page.locator('#course-visual-guide .visual-guide-controls .text-button').click();page.fill('#target',r'D:\课程 Python\python.exe');page.locator('#course-visual-guide .visual-step-button').nth(1).click()
                assert 'D:\\课程 Python\\python.exe' in page.locator('#course-visual-guide .win11-terminal-body').inner_text()
                choose('vm-linux');page.fill('#target',r'C:\VMware\vmrun.exe');page.locator('#course-visual-guide .visual-step-button').nth(1).click()
                assert 'VMware' in page.locator('#course-visual-guide .win11-terminal-body').inner_text()
                checks.append(dict(case='Notebook uses selected interpreter; VMware instructions follow selected software',passed=True))
                choose('node-basics')
                page.fill('#tool-dir',r'D:\Kehang-tool (2)');page.select_option('#report-stage','B');capture('report-B-desktop','#report-explorer-window')
                for width in [320,390,768,1440]:
                    page.set_viewport_size(dict(width=width,height=1000))
                    for scenario in ['notebook-data','java-jdk','local-qwen','vm-linux','dsh-cli']:
                        choose(scenario)
                        for button in page.locator('#course-visual-guide .visual-step-button').all():button.click();assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(width,scenario)
                    if width==390:capture('dsh-cli-mobile','#course-visual-guide')
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                checks.append(dict(case='320/390/768/1440 reflow across long multi-step courses',passed=True))
                page.set_viewport_size(dict(width=1440,height=1100));choose('notebook-data')
                page.emulate_media(reduced_motion='reduce')
                button=page.locator('#course-visual-guide .visual-step-button').nth(1);button.focus();page.keyboard.press('Enter')
                assert page.locator('#course-visual-guide .visual-step-count').inner_text().startswith('2')
                checks.append(dict(case='Keyboard guide activation, reduced motion and actual control focus',passed=True))
                page.click('#home-nav');page.click('#start-practice');page.click('#guide-next');page.click('#guide-next')
                host=page.locator('#practice-visual-guide');assert host.is_visible()
                for button in host.locator('.visual-step-button').all():button.click()
                assert not page.is_checked('#practice-read')
                capture('practice-files-desktop','#practice-visual-guide')
                page.click('#guide-next');assert page.locator('#practice-submit-guide').is_visible()
                assert '实训成果.json' in page.locator('#practice-submit-guide .win11-file-selected').inner_text()
                assert not page.locator('#practice-result').inner_text()
                capture('practice-submit-desktop','#practice-submit-guide')
                checks.append(dict(case='Continuous practice material and submission illustrations do not set declaration or completion',passed=True))
                assert not server.local_check.jobs and not errors and not requests,(errors,requests)
                result.update(passed=True,courses=13,total_groups=len(checks))
    except Exception as exc:
        result.update(passed=False,error=repr(exc));raise
    finally:
        (OUT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8',newline='\n')
        print(json.dumps(dict(passed=result.get('passed',False),path=str(OUT/'result.json'),groups=len(checks)),ensure_ascii=False))


if __name__=='__main__':main()
