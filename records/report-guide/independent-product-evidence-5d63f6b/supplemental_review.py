"""Independent review harness, outside the fixed product snapshot."""
from contextlib import ExitStack
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import tempfile
import threading
import zipfile

REVIEW = Path(__file__).resolve().parent
ROOT = REVIEW / 'snapshot'
sys.path.insert(0, str(ROOT))
from playwright.sync_api import sync_playwright
from campuslab.web import AppServer
from campuslab.rules import task, compare

result = {'candidate': '5d63f6b265ca773bb62d0e4a228fc2b3520b438a', 'checks': [], 'scope': 'Independent same-computer agent review; constructed boundary cases are not installed environments or novice/device acceptance.'}
def check(name, detail):
    result['checks'].append({'name': name, 'passed': True, 'detail': detail})
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()

try:
    product = json.loads((ROOT / 'records/report-guide/product.json').read_text(encoding='utf8'))['files']
    mismatch = [p for p, sha in product.items() if digest(ROOT / p) != sha]
    assert len(product) == 50 and not mismatch, mismatch
    check('frozen_product_hashes', {'count': len(product), 'mismatch': mismatch})
    baseline = Path(r'D:\传智杯\versions\kehang-local-check-20261112')
    manifest = baseline / 'SHA256SUMS-delivery.json'
    old = json.loads(manifest.read_text(encoding='utf8'))
    mismatch = [p for p, sha in old.items() if not (baseline / p).is_file() or digest(baseline / p) != sha]
    assert len(old) == 2410 and not mismatch, mismatch
    assert digest(manifest) == '4E0E5E04CF0E261DD9FB452EAB3AB8FA268887848026EE121C5A07AA0FE62F44'
    check('old_D_delivery_unchanged', {'files': len(old), 'manifest_sha256': digest(manifest), 'mismatch': mismatch})
    real = ROOT / 'records/report-guide/20261112T090454322842Z/real-node'
    before = json.loads((real / 'report-A.json').read_text(encoding='utf8'))
    after = json.loads((real / 'report-B.json').read_text(encoding='utf8'))
    spec = task('node-basics')
    assert compare(spec, before, after)['outcome'] == 'stable-pass'
    negatives = []
    for label, a, b in [('same_time', before, deepcopy(before)), ('reversed_time', after, before)]:
        try:
            compare(spec, a, b)
        except ValueError as exc:
            negatives.append({'case': label, 'error': str(exc)})
        else:
            raise AssertionError(label)
    other = deepcopy(after)
    other['target']['requested'] = r'C:\Different\node.exe'
    other['target']['actual'] = r'C:\Different\node.exe'
    other['facts']['npm']['path'] = r'C:\Different\node_modules\npm\bin\npm-cli.js'
    other['facts']['npm']['node'] = r'C:\Different\node.exe'
    try:
        compare(spec, before, other)
    except ValueError as exc:
        assert str(exc) == '复检必须使用同一目标环境路径', str(exc)
        negatives.append({'case': 'different_target_constructed', 'error': str(exc)})
    else:
        raise AssertionError('different_target_constructed')
    check('real_A_B_and_constructed_time_identity_negatives', {'outcome': 'stable-pass', 'negative_cases': negatives})

    with tempfile.TemporaryDirectory(prefix='kehang-independent-report-') as temporary, ExitStack() as stack:
        server = AppServer(0, Path(temporary) / 'courses.sqlite', ROOT / 'vendor/python-3.13.17-embed-amd64.zip')
        threading.Thread(target=server.serve_forever, daemon=True).start()
        stack.callback(server.server_close)
        stack.callback(server.shutdown)
        origin = 'http://127.0.0.1:' + str(server.server_port)
        with sync_playwright() as pw, ExitStack() as browser_stack:
            browser = pw.chromium.launch(channel='msedge', headless=True)
            browser_stack.callback(browser.close)
            context = browser.new_context(viewport={'width': 1440, 'height': 1000}, accept_downloads=True, permissions=['clipboard-read','clipboard-write'])
            page = context.new_page()
            remote, errors = [], []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.on('request', lambda r: remote.append(r.url) if r.url.startswith(('http://','https://')) and not r.url.startswith(origin + '/') else None)
            page.goto(origin)
            page.wait_for_function('()=>!!state.config&&!!practiceState.practice')
            def choose(goal):
                page.click('#home-nav')
                page.click('#choose-course')
                page.select_option('#goal', goal)
                page.locator('#goal-form button').click()
                page.wait_for_function('(s)=>state.task?.scenario===s&&guided.courseStep===1', arg=goal)
                page.click('#guide-next')
                if page.locator('#manual-collection > summary').is_visible() and page.locator('#manual-collection').get_attribute('open') is None:
                    page.locator('#manual-collection > summary').click()
            choose('node-basics')
            long_path = 'D:\\课航 工具\\' + '较长文件夹名称' * 30
            page.fill('#tool-dir', long_path)
            assert page.locator('#report-folder-address').input_value() == long_path
            page.locator('#report-folder-address').focus()
            page.keyboard.press('Tab')
            assert page.locator('#copy-report-folder').evaluate('e=>e===document.activeElement')
            focus_style = page.locator('#copy-report-folder').evaluate('e=>({style:getComputedStyle(e).outlineStyle,width:getComputedStyle(e).outlineWidth})')
            assert focus_style['style'] != 'none' and focus_style['width'] != '0px'
            page.keyboard.press('Enter')
            page.wait_for_function('()=>document.getElementById("report-copy-status").textContent.includes("地址已复制")')
            assert page.evaluate('navigator.clipboard.readText()') == long_path
            page.keyboard.press('Tab')
            assert page.locator('#report-files').evaluate('e=>e===document.activeElement')
            a11y = page.locator('.report-steps').aria_snapshot()
            assert 'report-A.json' in a11y and '位置示意' in a11y and '报告所在的工具文件夹' in a11y
            (REVIEW / 'accessible-report-guide.txt').write_text(a11y, encoding='utf8')
            assert page.locator('#report-copy-status').get_attribute('role') == 'status'
            for width in [320,390,768,1440]:
                page.set_viewport_size({'width': width, 'height': 900})
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), width
            check('keyboard_accessible_names_long_path_and_reflow', {'widths': [320,390,768,1440], 'path_characters': len(long_path), 'focus': focus_style, 'clipboard': 'actual API success; full path preserved'})
            page.set_viewport_size({'width':1440,'height':1000})
            page.fill('#tool-dir', r'D:\Tool')
            for target in [r'C:\Start Menu\Programs\Node.js', r'C:\Start Menu\Node.js.lnk', r'node.exe']:
                page.fill('#target', target)
                page.click('#make-command')
                assert not page.locator('#command').inner_text(), target
            assert page.evaluate("()=>{try{requireNodeFile('C:\\\\node\\n.exe');return false}catch(e){return true}}")
            renamed = r'C:\Course Runtime\node-custom.exe'
            page.fill('#target', '"' + renamed + '"')
            page.click('#make-command')
            assert page.locator('#target').input_value() == renamed
            assert page.locator('#command').inner_text()
            check('node_path_form_validation', {'folder_lnk_relative_rejected': True, 'different_exe_name_allowed': True, 'surrounding_double_quotes_normalized': True, 'real_executable_acceptance': 'real Node A/B held separately'})

            # Evaluate only the two generated assignment lines, never collection or user command text.
            attack_root = 'D:\\课航 $($x) ` quote" folder'
            attack_target = 'C:\\Program Files\\node-$($x)-`-"-custom.exe'
            page.fill('#tool-dir', attack_root)
            page.fill('#target', attack_target)
            page.click('#make-command')
            lines = page.locator('#command').inner_text().splitlines()
            assignment = [line for line in lines if line.startswith(('$taskToolRoot = ', '$taskTarget = '))]
            assert len(assignment) == 2
            script = Path(temporary) / 'assignments.ps1'
            script.write_text('\n'.join(assignment + ['ConvertTo-Json -Compress -InputObject @($taskToolRoot, $taskTarget)']), encoding='utf8')
            parsed = subprocess.run(['pwsh','-NoProfile','-NonInteractive','-File',str(script)], capture_output=True, text=True, encoding='utf8', check=True)
            assert json.loads(parsed.stdout) == [attack_root, attack_target], parsed.stdout
            check('powershell_assignment_literals', {'constructed_metacharacters': 'dollar subexpression, backtick, double quote and spaces', 'evaluated_scope': 'only generated assignments; exact literal round trip; no collector execution'})

            page.fill('#tool-dir', r'D:\Old course')
            page.evaluate("Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:()=>new Promise((resolve,reject)=>{window.pendingClipboardReject=reject})}})")
            page.click('#copy-report-folder')
            page.wait_for_function('()=>!!window.pendingClipboardReject')
            choose('notebook-data')
            page.evaluate("window.pendingClipboardReject(Error('controlled delayed denial'))")
            page.wait_for_timeout(30)
            assert page.locator('#tool-dir').input_value() == ''
            assert page.locator('#report-folder-address').input_value() == '你解压的课航工具文件夹'
            assert not page.locator('#copy-report-folder').is_visible()
            assert page.locator('#report-copy-status').inner_text() == ''
            assert not page.locator('#report-folder-address').evaluate('e=>e===document.activeElement')
            check('delayed_clipboard_rejection_after_task_switch', {'constructed_denial': True, 'old_directory_status_and_focus_not_restored': True})
            with page.expect_download() as download:
                page.click('#download-tool')
            tool = REVIEW / 'downloaded-notebook-tool.zip'
            download.value.save_as(tool)
            with zipfile.ZipFile(tool) as z:
                assert z.testzip() is None
                readme = z.read('README.txt').decode('utf8')
                assert '--output report-A.json' in readme and '--output report-B.json; keep A.' in readme
                assert 'task.json' in readme
            check('downloaded_tool_readme', {'zip_sha256': digest(tool), 'default_A_and_keep_A_for_B': True})
            assert not errors and not remote, {'errors': errors, 'remote': remote}
            check('network_and_browser_error_scope', {'page_errors':errors,'remote_requests':remote,'model_requests':0,'installs':0})
    result['passed'] = True
except Exception as exc:
    result['passed'] = False
    result['error'] = repr(exc)
    raise
finally:
    result['finished_at_utc'] = datetime.now(timezone.utc).isoformat()
    (REVIEW / 'supplemental-result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
