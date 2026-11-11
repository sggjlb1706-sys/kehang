"""Exercise the guided UI using isolated local services and archived real reports."""
from contextlib import ExitStack
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tempfile
import threading
import traceback
import zipfile

from playwright.sync_api import sync_playwright
from campuslab.web import AppServer

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'records/guided' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
LAB = ROOT / 'records/practice/lab-run'


def main():
    OUT.mkdir(parents=True)
    checks, errors, remote, shots = [], [], [], []
    result = dict(checks=checks, page_errors=errors, remote_requests=remote, screenshots=shots,
                  execution_scope='Agent-operated browser on one computer; archived real A/B reanalysed, not recollected; constructed 41 negative identified.')
    def capture(page, name):
        path = OUT / (name + '.png')
        page.screenshot(path=path, full_page=True,
                        mask=[page.locator('#results > p').filter(has_text='本次目标')])
        shots.append(dict(path=path.relative_to(ROOT).as_posix(), sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    def change_goal(page, goal):
        page.locator('#guide-progress button').nth(0).click()
        page.select_option('#goal', goal)
        page.locator('#goal-form button').click()
        page.wait_for_function('(s)=>state.task?.scenario===s && guided.courseStep===1', arg=goal)
    def see(page, selector):
        page.locator(selector).evaluate("e=>{for(let p=e;p;p=p.parentElement)if(p.tagName==='DETAILS')p.open=true}")
    def data(name):
        return json.loads((LAB / name).read_text(encoding='utf8'))
    def write(path, value):
        path.write_text(json.dumps(value, ensure_ascii=False), encoding='utf8')
        return path
    try:
        with tempfile.TemporaryDirectory(prefix='kehang-guided-ui-') as folder, ExitStack() as stack:
            folder = Path(folder)
            server = AppServer(0, folder / 'courses.sqlite', ROOT / 'vendor/python-3.13.17-embed-amd64.zip')
            threading.Thread(target=server.serve_forever, daemon=True).start()
            stack.callback(server.server_close)
            stack.callback(server.shutdown)
            origin = 'http://127.0.0.1:' + str(server.server_port)
            with sync_playwright() as p, ExitStack() as browser_stack:
                browser = p.chromium.launch(channel='msedge', headless=True)
                browser_stack.callback(browser.close)
                context = browser.new_context(viewport=dict(width=1360, height=900), accept_downloads=True)
                context.on('request', lambda r: remote.append(r.url) if r.url.startswith(('http://', 'https://')) and not r.url.startswith(origin + '/') else None)
                page = context.new_page()
                page.on('pageerror', lambda e: errors.append(str(e)))
                page.goto(origin)
                page.wait_for_function('()=>!!state.config && !!practiceState.practice')
                ids = page.locator('[id]').evaluate_all('(es)=>es.map(e=>e.id)')
                assert len(ids) == len(set(ids)), 'Duplicate element ids'
                assert page.locator('#start-python').is_visible()
                for selector in ['#download-tool', '#practice-submission', '#goal', '#practice-check', '#export-course', '#diagnosis']:
                    assert not page.locator(selector).is_visible(), selector
                assert page.locator('main input[type=file]:visible').count() == 0
                result['contrast_ratios'] = page.evaluate('''()=>{
                  const pixel=color=>{const c=document.createElement('canvas');c.width=c.height=1;const x=c.getContext('2d');x.fillStyle=color;x.fillRect(0,0,1,1);return [...x.getImageData(0,0,1,1).data].slice(0,3).map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4;}).reduce((s,v,i)=>s+v*[.2126,.7152,.0722][i],0);};
                  const vars=getComputedStyle(document.documentElement),bg=pixel(vars.getPropertyValue('--bg'));
                  return Object.fromEntries(['--ink','--muted','--brand'].map(k=>{const v=pixel(vars.getPropertyValue(k));return [k,(Math.max(v,bg)+.05)/(Math.min(v,bg)+.05)];}).concat([['primary_text',1.05/(pixel(vars.getPropertyValue('--brand'))+.05)]]));
                }''')
                assert all(ratio >= 4.5 for ratio in result['contrast_ratios'].values())
                capture(page, '01-home-desktop')
                checks.append('Home shows the recommended start and contextual alternatives, with no upload/download/technical workflow exposed')

                page.click('#start-python')
                page.wait_for_function("()=>state.task?.scenario==='python-basics' && guided.courseStep===1")
                assert page.locator('#preparation').is_visible() and not page.locator('#collect-stage').is_visible()
                assert not page.locator('#download-tool').is_visible()
                assert page.locator('#guide-progress button').nth(3).is_disabled()
                capture(page, '02-python-prepare')
                page.click('#guide-next')
                assert page.locator('#collect-stage').is_visible() and page.locator('#guide-next').is_disabled()
                assert page.locator('#guide-next').bounding_box()['y'] < page.viewport_size['height'], 'Next action must be visible without hunting at the bottom'
                assert page.locator('#simple-collector').is_visible() and not page.locator('#command-panel').get_attribute('open')
                assert page.locator('#download-tool').is_visible() and not page.locator('#export-course').is_visible()
                with page.expect_download() as download:
                    page.click('#download-tool')
                download.value.save_as(folder / 'tool.zip')
                with zipfile.ZipFile(folder / 'tool.zip') as z:
                    assert z.testzip() is None and 'Start-Collect.cmd' in z.namelist()
                    assert json.loads(z.read('task.json'))['id'] == page.evaluate('state.task.id')
                capture(page, '03-python-collect')
                checks.append('Python preparation and collection are separate; only current tool is offered; download ZIP contains selected task and launcher')

                bad = write(folder / 'invalid.json', dict(share_only=True))
                page.set_input_files('#report-files', bad)
                page.wait_for_function("()=>document.getElementById('notice').classList.contains('error')")
                assert page.locator('#guide-next').is_disabled() and not page.evaluate('state.before')
                page.set_input_files('#report-files', LAB / 'python-basics-A.json')
                page.wait_for_function('()=>!!state.before && !!state.analysis')
                page.click('#guide-next')
                assert page.locator('#review-stage').is_visible() and not page.evaluate('state.after')
                assert '初检' in page.locator('#review-hint').inner_text()
                page.click('#guide-next')
                assert page.evaluate("document.getElementById('report-stage').value") == 'B'
                assert page.evaluate('!!state.before')
                page.set_input_files('#report-files', LAB / 'python-basics-B.json')
                page.wait_for_function('()=>!!state.after && state.analysis?.passed')
                assert page.evaluate('state.before.collected_at') == data('python-basics-A.json')['collected_at']
                page.click('#guide-next')
                assert '同一目标稳定复检通过' in page.locator('#comparison').inner_text()
                capture(page, '04-python-reviewed')
                original = page.evaluate('JSON.stringify(state.analysis)')
                page.locator('#guide-progress button').nth(1).click()
                page.evaluate("document.getElementById('full-guidance').open=true")
                for mode in ['quick', 'standard', 'novice']:
                    page.select_option('#mode', mode)
                    assert page.evaluate('JSON.stringify(state.analysis)') == original
                checks.append('Invalid sharing report rejected; real A followed by single B preserves baseline and passes comparison; mode changes preserve facts')

                change_goal(page, 'pytorch-gpu')
                assert not page.evaluate('state.before || state.after || state.analysis')
                assert page.locator('#report-stage').input_value() == 'A', 'New course must start with A, not inherit previous B'
                assert page.locator('#guide-progress button').nth(3).is_disabled()
                page.click('#guide-next')
                assert page.locator('#command-panel').get_attribute('open') is not None
                assert page.locator('#target').is_visible() and page.locator('#guide-next').is_disabled()
                capture(page, '05-gpu-collect')
                checks.append('Changing goal clears reports and review access; GPU has one download and an open explicit-target collection form')

                for goal in ['node-basics','local-qwen','pytorch-cpu','vm-linux','notebook-data','java-jdk','sqlite-basics','deepseek-api','ai-web-deepseek','dsh-desktop','dsh-cli']:
                    change_goal(page, goal)
                    page.click('#guide-next')
                    assert page.locator('#download-tool').get_attribute('href').endswith('goal=' + goal)
                    assert page.locator('#collect-stage').is_visible() and page.locator('#guide-next').is_disabled()
                    if goal not in ['python-basics', 'notebook-data']:
                        assert page.locator('#command-panel').get_attribute('open') is not None
                checks.append('All 13 existing course selections reach compatible task-specific guidance and collection controls')

                page.click('#home-nav')
                page.click('#start-practice')
                page.click('#guide-next')
                page.click('#practice-notebook')
                page.wait_for_function("()=>state.task?.scenario==='notebook-data' && guided.courseStep===1")
                assert page.locator('#back-practice').is_visible()
                page.click('#back-practice')
                assert page.evaluate("guided.route==='practice' && guided.practiceStep===1")
                assert '无当前报告' in page.locator('#practice-environment').inner_text()
                page.click('#guide-next')
                with page.expect_download() as download:
                    page.click('#practice-materials')
                download.value.save_as(folder / 'materials.zip')
                with zipfile.ZipFile(folder / 'materials.zip') as z:
                    assert z.testzip() is None and {'scores.csv','01_Notebook练习.ipynb','02_SQLite练习.py','成果模板.json'} <= set(z.namelist())
                page.check('#practice-read')
                page.click('#guide-next')
                wrong = deepcopy(data('实训成果.json'))
                wrong['notebook']['array_sum'] = 41
                for file, status in [(write(folder / 'constructed-41.json', wrong), 'mismatch'), (LAB / '实训成果.json', 'pass')]:
                    page.set_input_files('#practice-submission', file)
                    page.click('#practice-check')
                    page.wait_for_function('(s)=>practiceState.attempts.at(-1)?.result.status===s', arg=status)
                assert page.evaluate('practiceState.attempts.length') == 2
                with page.expect_download() as download:
                    page.click('#practice-completion')
                download.value.save_as(folder / 'completion.json')
                completion = json.loads((folder / 'completion.json').read_bytes())
                assert [a['result']['status'] for a in completion['attempts']] == ['mismatch', 'pass']
                assert not completion['environment'] and completion['reading_self_declared']
                capture(page, '06-practice-result')
                checks.append('Practice supports returning from component environment; materials complete; constructed wrong and correct results retained; no invented environment pass')

                page.click('#teacher-nav')
                page.click('#practice-publish')
                page.wait_for_function('()=>!!practiceState.courses')
                with page.expect_download() as download:
                    page.click('#practice-export-package')
                download.value.save_as(folder / 'practice-course.json')
                see(page, '#practice-completion-file')
                page.set_input_files('#practice-completion-file', folder / 'completion.json')
                page.wait_for_function("()=>document.getElementById('practice-teacher-review').textContent.includes('已重新核验 2 条')")
                capture(page, '07-teacher')
                see(page, '#teacher-form')
                page.select_option('#teacher-goal', 'node-basics')
                page.locator('#teacher-form button').click()
                page.wait_for_function("()=>guided.route==='teacher' && state.task?.scenario==='node-basics'")
                assert not page.evaluate('state.before || state.after')
                see(page, '#export-course')
                with page.expect_download() as download:
                    page.click('#export-course')
                download.value.save_as(folder / 'single-course.json')
                page.click('#home-nav')
                page.click('#import-entry')
                page.set_input_files('#course-package', folder / 'single-course.json')
                page.wait_for_function("()=>guided.route==='course' && guided.courseStep===1 && state.task?.scenario==='node-basics'")
                checks.append('Teacher can publish and export single course without collecting a student report; original course package imports into guided flow')
                page.click('#home-nav')
                page.click('#import-entry')
                page.set_input_files('#practice-package', folder / 'practice-course.json')
                page.wait_for_function("()=>guided.route==='practice' && guided.practiceStep===0")
                assert not page.evaluate('Object.keys(practiceState.environment).length')
                page.click('#home-nav')
                page.click('#import-entry')
                page.set_input_files('#practice-package', bad)
                page.wait_for_function('()=>practiceState.practice===null')
                assert not page.locator('#practice-teacher-review').inner_text().strip()
                checks.append('Teacher tools separate from student start; publish/export/import and completion recheck work; invalid import clears stale success')

                # Delay a real request, leave its route, then release it: no late navigation.
                page.click('#home-nav')
                pending = []
                page.route('**/api/plan', lambda route: pending.append(route))
                page.click('#start-python')
                page.wait_for_timeout(100)
                assert pending
                page.click('#home-nav')
                pending.pop().continue_()
                page.unroute('**/api/plan')
                page.wait_for_timeout(300)
                assert page.evaluate("guided.route==='home'") and page.locator('#home-screen').is_visible()
                checks.append('Delayed task preparation does not navigate away from home after the user leaves')

                for width in [390,768,1360]:
                    page.set_viewport_size(dict(width=width, height=900))
                    page.click('#home-nav')
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), width
                    if width == 390:
                        capture(page, '08-home-mobile')
                    page.click('#choose-course')
                    page.select_option('#goal', 'pytorch-gpu')
                    page.locator('#goal-form button').click()
                    page.wait_for_function("()=>guided.courseStep===1")
                    page.click('#guide-next')
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), width
                    footer = page.locator('#guide-next').bounding_box()
                    assert footer['y'] >= 0 and footer['y']+footer['height'] <= page.viewport_size['height'], width
                    if width == 390:
                        capture(page, '09-gpu-mobile')
                page.emulate_media(reduced_motion='reduce')
                page.click('#home-nav')
                page.locator('#start-python').focus()
                page.keyboard.press('Enter')
                page.wait_for_function("()=>guided.courseStep===1")
                assert page.locator('#guide-title').evaluate('e=>e===document.activeElement')
                checks.append('390/768/1360 layouts have no horizontal overflow; reduced motion and keyboard activation/focus work')
                assert not errors and not remote, (errors, remote)
        result['passed'] = True
    except Exception:
        result['passed'] = False
        result['failure'] = traceback.format_exc()
        raise
    finally:
        (OUT / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
        print(json.dumps(dict(output=str(OUT), passed=result.get('passed'), checks=len(checks))))


if __name__ == '__main__':
    main()
