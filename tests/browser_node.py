"""Real local Edge/Node evidence; developer automation, not a physical-phone or novice test."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import threading
import zipfile

from playwright.sync_api import sync_playwright
from campuslab.web import AppServer

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = Path('D:/传智杯/artifacts/portable-runtime/python-3.13.17-embed-amd64.zip')
NODE = Path('D:/Program Files/nodejs/node.exe')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '-node'
    out = ROOT/'records/browser'/run_id
    working = ROOT/'records/runtime'/run_id
    out.mkdir(parents=True); working.mkdir(parents=True)
    server = AppServer(0, working/'course.sqlite', RUNTIME)
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    base = f'http://127.0.0.1:{server.server_port}'
    checks, errors, external, executions = [], [], [], []
    completed = False

    def check(name):
        checks.append(name); print('PASS:', name, flush=True)

    def execute(page, name):
        page.locator('#make-command').click()
        command = page.locator('#command').inner_text(); assert command
        script = out/(name+'.ps1'); script.write_text(command, encoding='utf-8-sig')
        proc = subprocess.run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(script)], capture_output=True, timeout=90)
        (out/(name+'.stdout.txt')).write_bytes(proc.stdout)
        (out/(name+'.stderr.txt')).write_bytes(proc.stderr)
        executions.append(dict(name=name, returncode=proc.returncode, script=script.name))
        assert proc.returncode == 0, proc.stderr

    def variant(name, report):
        path = out/(name+'.json')
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        return path

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel='msedge', headless=True)
            context = browser.new_context(viewport={'width':1440, 'height':1000}, accept_downloads=True)
            page = context.new_page()
            page.on('pageerror', lambda error:errors.append(str(error)))
            context.on('request', lambda request:external.append(request.url) if request.url.startswith(('http://','https://')) and not request.url.startswith(base+'/') else None)
            page.goto(base); page.wait_for_function('()=>state.config !== null')
            page.select_option('#goal','node-basics'); page.locator('#goal-form button').click()
            page.wait_for_selector('#guidance li')
            spec = page.evaluate('()=>state.task')
            variant('autonomous-task', spec)
            assert '演示课程要求' in page.locator('#task-source').inner_text()
            assert 'node.exe' in page.locator('#target-label').text_content()
            assert page.locator('#results .check').count() == 0
            check('Node autonomous goal displays fixed demonstration requirements without inferring a pass')

            with page.expect_download() as download:
                page.locator('#download-tool').click()
            archive = out/'downloaded-tool.zip'; download.value.save_as(archive)
            tool = working/"Node工具 O'Brien ‘左’ ‚低‛ “双” „低‟ $Literal `tick"
            tool.mkdir()
            with zipfile.ZipFile(archive) as z:
                assert z.testzip() is None
                assert json.loads(z.read('task.json')) == spec
                z.extractall(tool)
            page.locator('#command-panel').evaluate('(element)=>element.open=true')
            page.fill('#tool-dir', str(tool)); page.fill('#target', str(NODE))
            execute(page, 'actual-node-A')
            page.select_option('#report-stage', 'B'); execute(page, 'actual-node-B')
            before = variant('actual-node-A', json.loads((tool/'report-A.json').read_text(encoding='utf-8')))
            after = variant('actual-node-B', json.loads((tool/'report-B.json').read_text(encoding='utf-8')))
            page.set_input_files('#before-file', str(before)); page.wait_for_selector('#results .check')
            page.set_input_files('#after-file', str(after))
            page.wait_for_function("()=>document.getElementById('comparison').textContent.includes('稳定复检通过')")
            assert page.locator('#results .state-pass').count() == 4
            page.screenshot(path=str(out/'node-desktop.png'), full_page=True)
            check('Downloaded tool and exact generated PS5.1 commands collect real selected Node/npm stable A/B')

            facts = page.locator('#results').inner_text()
            for mode in ('quick', 'standard', 'novice'):
                page.select_option('#mode', mode)
                page.wait_for_function('(mode)=>document.querySelectorAll("#guidance li").length===(mode==="quick"?2:mode==="novice"?6:5)', arg=mode)
                assert page.locator('#results').inner_text() == facts
            check('Three Node guidance modes preserve the identical facts and verdicts')

            page.fill('#user-error', 'Example: sk-abcdefghijklmnop C:\\Users\\Example\\error.txt')
            page.locator('#prepare-ai').click(); page.wait_for_selector('#ai-preview-panel')
            assert 'sk-abcdefghijklmnop' not in page.locator('#ai-preview').input_value()
            assert page.locator('#send-ai').is_disabled()
            page.locator('#export').click()
            assert json.loads(page.locator('#export-preview').input_value())['share_only']
            check('Node evidence uses editable redaction and explicit AI consent without any model request')

            page.locator('#teacher-form').evaluate('(element)=>element.closest("details").open=true')
            page.select_option('#teacher-goal', 'node-basics')
            assert page.locator('#teacher-python-options').is_hidden()
            assert page.locator('#teacher-node-requirements').is_visible()
            page.locator('#teacher-form button').click()
            page.wait_for_function('()=>state.course !== null')
            assert page.evaluate('()=>state.task') == spec
            code = page.evaluate('()=>state.course')
            second = context.new_page(); second.goto(base+'/?course='+code)
            second.wait_for_function('(id)=>state.task?.id===id', arg=spec['id']); second.close()
            page.set_input_files('#before-file', str(before)); page.wait_for_selector('#results .check')
            page.set_input_files('#after-file', str(after))
            page.wait_for_function("()=>document.getElementById('comparison').textContent.includes('稳定复检通过')")
            variant('published-identical-course', dict(code=code, task=spec))
            check('Teacher code and autonomous Node entry consume the exact same immutable task and reports')

            different = deepcopy(json.loads(after.read_text(encoding='utf-8')))
            different['collected_at'] = (datetime.now(timezone.utc)+timedelta(seconds=1)).isoformat()
            different['target'].update(requested='C:\\DifferentNode\\node.exe', actual='C:\\DifferentNode\\node.exe')
            different['facts']['npm'].update(node='C:\\DifferentNode\\node.exe', path='C:\\DifferentNode\\node_modules\\npm\\bin\\npm-cli.js')
            page.set_input_files('#after-file', str(variant('constructed-other-target-B', different)))
            page.wait_for_function("()=>document.getElementById('notice').classList.contains('error')")
            page.wait_for_function("()=>document.getElementById('after-file').value === ''")
            assert page.locator('#comparison').inner_text() == ''
            assert page.evaluate('()=>state.after === null')
            incomplete = deepcopy(json.loads(before.read_text(encoding='utf-8')))
            incomplete['facts'].pop('npm')
            page.set_input_files('#before-file', str(variant('constructed-incomplete-A', incomplete)))
            page.wait_for_function("()=>document.getElementById('notice').classList.contains('error')")
            page.wait_for_function("()=>document.getElementById('before-file').value === ''")
            assert page.locator('#results .check').count() == 0
            check('Clearly labelled constructed reports with another target or incomplete facts cannot complete recheck')

            page.set_input_files('#before-file', str(before)); page.wait_for_selector('#results .check')
            page.fill('#target', 'C:\\DifferentNode\\node.exe')
            assert page.locator('#results .check').count() == 0
            assert page.locator('#ai-preview-panel').is_hidden()
            assert page.locator('#after-file').is_disabled()
            check('Editing the selected target clears old results, comparison and AI consent')

            page.select_option('#goal', 'python-basics'); page.locator('#goal-form button').click()
            page.wait_for_function("()=>state.task?.scenario==='python-basics'")
            page.set_input_files('#before-file', str(before))
            page.wait_for_function("()=>document.getElementById('notice').classList.contains('error')")
            page.wait_for_function("()=>document.getElementById('before-file').value === ''")
            assert page.locator('#results .check').count() == 0
            check('Node report is rejected under the Python task snapshot')

            page.select_option('#goal', 'node-basics'); page.locator('#goal-form button').click()
            page.wait_for_function("()=>state.task?.scenario==='node-basics'")
            page.fill('#target', str(NODE))
            page.set_input_files('#before-file', str(before)); page.wait_for_selector('#results .check')
            page.set_viewport_size({'width':390, 'height':844})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            page.screenshot(path=str(out/'node-mobile-390.png'), full_page=True)
            check('390px Node guidance, reports and teacher form have no horizontal overflow (desktop emulation)')
            assert not errors, errors
            assert not external, external
            browser.close(); completed = True
    finally:
        server.shutdown(); server.server_close(); thread.join()
        sources = {path.relative_to(ROOT).as_posix():sha(path) for folder in ('campuslab','web') for path in (ROOT/folder).rglob('*') if path.is_file() and '__pycache__' not in path.parts}
        result = dict(status='passed' if completed else 'failed', checks=checks, passed=len(checks), browser_errors=errors, external_requests=external,
                      executions=executions, source_sha256=sources, real_local_node=True, node_target=str(NODE), constructed_reports=['constructed-other-target-B.json','constructed-incomplete-A.json'],
                      developer_automation=True, novice_user_test=False, clean_device_test=False, physical_phone_test=False, install_calls=0, paid_model_requests=0)
        (out/'results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        print('Evidence:', out, flush=True)


if __name__ == '__main__':
    main()
