"""Real local A/B and controlled UI cases; never call an AI service."""
from contextlib import ExitStack
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tempfile
import threading
import time

from playwright.sync_api import sync_playwright
from campuslab.local_check import LocalCheckService
from campuslab.rules import task
from campuslab.web import AppServer

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'records/local-check' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')


def fixture(spec, target, cancel):
    from datetime import datetime, timezone
    return dict(schema=1, task_id=spec['id'], collected_at=datetime.now(timezone.utc).isoformat(),
                target=dict(requested=target, actual=target, exists=True),
                facts=dict(os='Windows', python='3.13.9' if 'Good' in target else '3.9.9',
                           packages=dict(requests='2.32.5'), verification=dict(returncode=0, stdout='OK\n', error='')))


def main():
    OUT.mkdir(parents=True)
    checks, shots, errors, remote = [], [], [], []
    result = dict(checks=checks, screenshots=shots, page_errors=errors, remote_requests=remote,
                  scope='Same-computer agent browser. real/ holds freshly collected original A/B. Controlled cases are fixtures, not installed environments; no AI request.')
    def save(name, value):
        path = OUT / name; path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf8')
    try:
        with tempfile.TemporaryDirectory(prefix='kehang-local-ui-') as folder, ExitStack() as stack:
            server = AppServer(0, Path(folder) / 'courses.sqlite', ROOT / 'vendor/python-3.13.17-embed-amd64.zip')
            threading.Thread(target=server.serve_forever, daemon=True).start()
            stack.callback(server.server_close); stack.callback(server.shutdown)
            origin = 'http://127.0.0.1:' + str(server.server_port)
            with sync_playwright() as p, ExitStack() as browser_stack:
                browser = p.chromium.launch(channel='msedge', headless=True)
                browser_stack.callback(browser.close)
                page = browser.new_page(viewport=dict(width=1360, height=900), accept_downloads=True)
                page.on('pageerror', lambda e: errors.append(str(e)))
                page.on('request', lambda r: remote.append(r.url) if r.url.startswith(('http://','https://')) and not r.url.startswith(origin + '/') else None)
                def ready():
                    page.goto(origin); page.wait_for_function('()=>!!state.config&&!!practiceState.practice')
                def capture(name):
                    path = OUT / (name + '.png'); page.screenshot(path=path, full_page=True)
                    shots.append(dict(path=path.relative_to(ROOT).as_posix(), sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
                def replace(choices, runner=fixture):
                    server.local_check.close()
                    server.local_check = LocalCheckService(lambda: choices, runner)
                    server.local_check.available = True
                    ready()
                ready(); page.wait_for_timeout(250)
                assert not server.local_check.jobs
                assert not page.locator('input[type=file]:visible').count()
                capture('01-home')
                page.click('#start-python')
                page.wait_for_function('()=>!!localState.selected?.report', timeout=120000)
                assert page.evaluate('guided.courseStep') == 3
                assert not page.locator('#report-files').is_visible()
                assert page.locator('#local-recheck').is_visible()
                original = page.evaluate('localState.selected.report')
                save('real/report-A.json', original)
                save('real/initial-job.json', page.evaluate('localState.job'))
                capture('02-real-result')
                page.click('#local-recheck')
                page.wait_for_function('()=>!!state.after&&!!localState.selected?.comparison', timeout=120000)
                save('real/report-B.json', page.evaluate('state.after'))
                save('real/comparison.json', page.evaluate('localState.selected.comparison'))
                assert page.evaluate('state.before.target.requested===state.after.target.requested')
                assert page.evaluate('state.before.collected_at') == original['collected_at']
                checks.append('Fresh real one-click A and same-target B returned directly to the page, without path entry, download, JSON import or AI request')
                capture('03-real-recheck')
                page.click('#local-ai'); page.wait_for_function('()=>!document.getElementById("ai-preview-panel").hidden')
                assert not page.is_checked('#ai-consent') and page.is_disabled('#send-ai')
                assert not remote
                checks.append('AI action generates an editable/redacted preview only; explicit single-send consent remains required')
                replace([(r'C:\Good\python.exe','controlled fixture'), (r'C:\Old\python.exe','controlled fixture')])
                page.click('#start-python'); page.wait_for_function('()=>localState.items.length===2&&!!state.analysis')
                assert page.evaluate('state.analysis.passed')
                page.locator('.local-environment button').nth(1).click()
                page.wait_for_function('()=>state.analysis&&!state.analysis.passed')
                assert page.evaluate('state.before.target.requested') == r'C:\Old\python.exe'
                page.click('#local-recheck'); page.wait_for_function('()=>!!state.after')
                page.locator('.local-environment button').nth(0).click()
                page.wait_for_function('()=>!!state.analysis?.passed')
                page.click('#local-recheck'); page.wait_for_function('()=>!!state.after&&state.after.target.requested.includes("Good")')
                assert page.evaluate('localState.items.length') == 2
                baseline = page.evaluate('JSON.stringify(state.analysis)')
                page.locator('#guide-progress button').nth(1).click()
                page.locator('#full-guidance').evaluate('e=>e.open=true')
                for mode in ['quick','standard','novice']:
                    page.select_option('#mode',mode)
                    assert page.evaluate('JSON.stringify(state.analysis)') == baseline
                checks.append('Controlled two-environment results stay separate, retest uses each owning job/target, and all explanation modes preserve facts')
                replace([]); page.click('#start-python')
                page.wait_for_function('()=>!localState.running&&!!localState.job')
                assert not page.evaluate('state.analysis||state.before')
                assert '不代表没有安装' in page.locator('#local-status').inner_text()
                assert page.locator('#local-prepare').is_visible()
                checks.append('No candidate keeps evidence unknown and offers preparation/manual guidance')
                capture('04-no-candidate')
                def waiting(spec, target, cancel):
                    cancel.wait(10); return fixture(spec, target, cancel)
                replace([(r'C:\Good\python.exe','controlled fixture')],waiting)
                page.click('#start-python'); page.wait_for_function('()=>localState.running&&!!localState.job')
                identity = page.evaluate('localState.job.id')
                page.click('#back-home'); page.wait_for_function('()=>guided.route==="home"')
                for _ in range(100):
                    if server.local_check.status(identity)['state']=='cancelled': break
                    time.sleep(.01)
                assert server.local_check.status(identity)['state']=='cancelled'
                page.wait_for_timeout(500)
                assert page.evaluate('guided.route')=='home' and not page.evaluate('state.before')
                checks.append('Leaving an active check cancels its owned job and late results cannot navigate back or populate reports')
                # Delay POST response to prove cancellation even before the browser knows the job ID.
                replace([(r'C:\Good\python.exe','controlled fixture')],waiting)
                def delayed(route):
                    response=route.fetch(); page.wait_for_timeout(350); route.fulfill(response=response)
                page.route('**/api/local-check',delayed)
                page.click('#start-python'); page.wait_for_function('()=>localState.running')
                page.click('#back-home'); page.wait_for_timeout(900)
                assert all(job['state']=='cancelled' for job in server.local_check.jobs.values())
                assert page.evaluate('guided.route')=='home' and not page.evaluate('state.before')
                page.unroute('**/api/local-check',delayed)
                checks.append('Delayed start response is cancelled after navigation; no stale report is attached')
                replace([(r'C:\Good\python.exe','controlled fixture')])
                page.set_viewport_size(dict(width=390,height=844))
                capture('05-home-mobile'); page.emulate_media(reduced_motion='reduce');page.locator('#start-python').focus();page.keyboard.press('Enter')
                page.wait_for_function('()=>!!state.analysis')
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                capture('06-result-mobile')
                assert page.locator('#local-recheck').is_visible()
                assert page.locator('#guide-title').evaluate('e=>e===document.activeElement')
                checks.append('390px home and results have no horizontal overflow and retain clear primary actions')
                assert not errors and not remote
                result['passed']=True
    except Exception as exc:
        result.update(passed=False, error=repr(exc))
        raise
    finally:
        save('result.json',result)
        print(json.dumps(dict(passed=result.get('passed',False),path=str(OUT/'result.json'),checks=len(checks)),ensure_ascii=False))


if __name__=='__main__': main()
