"""Same-computer browser acceptance; real collectors and controlled failures are separate."""
import base64
from contextlib import ExitStack
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import threading
import time
import traceback
from unittest.mock import patch

from playwright.sync_api import sync_playwright
from campuslab.local_targets import PICKER
from campuslab.rules import analyze, compare, task
from campuslab.sqlite_course import prepare_demo
from campuslab.web import AppServer

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'records/round2' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
SHELL = Path(os.environ.get('SystemRoot', 'C:/Windows')) / 'System32/WindowsPowerShell/v1.0/powershell.exe'
SCENARIOS = ['python-basics','node-basics','java-jdk','notebook-data','sqlite-basics','pytorch-cpu','pytorch-gpu','local-qwen','ai-web-deepseek','deepseek-api','dsh-desktop','dsh-cli','vm-linux']

# UI Automation addresses only controls owned by the new picker process.
AUTOMATE = r'''
$ErrorActionPreference='Stop'
[Console]::InputEncoding=[Text.UTF8Encoding]::new($false)
$settings=[Console]::In.ReadToEnd() | ConvertFrom-Json
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$owner=[Windows.Automation.PropertyCondition]::new([Windows.Automation.AutomationElement]::ProcessIdProperty,[int]$settings.process)
$title=[Windows.Automation.PropertyCondition]::new([Windows.Automation.AutomationElement]::NameProperty,[string]$settings.title)
$condition=[Windows.Automation.AndCondition]::new($owner,$title)
$window=$null
for($i=0;$i -lt 90;$i++) {
 $window=[Windows.Automation.AutomationElement]::RootElement.FindFirst([Windows.Automation.TreeScope]::Children,$condition)
 if($null -ne $window){break}; Start-Sleep -Milliseconds 100
}
if($null -eq $window){throw 'Owned picker not found'}
@{window=$window.Current.Name;handle=$window.Current.NativeWindowHandle;offscreen=$window.Current.IsOffscreen;framework=$window.Current.FrameworkId} | ConvertTo-Json -Compress
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class OwnedPicker {
 [DllImport("user32.dll")] public static extern IntPtr GetDlgItem(IntPtr h,int id);
 [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h,out uint p);
 [DllImport("user32.dll",CharSet=CharSet.Unicode)] public static extern IntPtr SendMessage(IntPtr h,uint m,IntPtr w,string text);
 [DllImport("user32.dll")] public static extern IntPtr SendMessage(IntPtr h,uint m,IntPtr w,IntPtr l);
}
'@
$root=[IntPtr]$window.Current.NativeWindowHandle
[uint32]$actualOwner=0
[void][OwnedPicker]::GetWindowThreadProcessId($root,[ref]$actualOwner)
if($root -eq [IntPtr]::Zero -or $actualOwner -ne [uint32]$settings.process){throw 'Root ownership mismatch'}
if(-not $settings.cancel){
 $edit=[OwnedPicker]::GetDlgItem($root,1148)
 if($edit -eq [IntPtr]::Zero){throw 'Owned filename control missing'}
 [void][OwnedPicker]::SendMessage($edit,0x000C,[IntPtr]::Zero,[string]$settings.path)
}
if($settings.cancel){[void][OwnedPicker]::SendMessage($root,0x0111,[IntPtr]2,[IntPtr]::Zero)}
else{[void][OwnedPicker]::SendMessage($root,0x0111,[IntPtr]1,[IntPtr]::Zero)}
'''


def native_control(path=None):
    original = subprocess.run
    encoded = base64.b64encode(PICKER.encode('utf-16le')).decode()
    def run(command, **kwargs):
        if not command or command[-1] != encoded: return original(command, **kwargs)
        settings = json.loads(kwargs['input'])
        assert not settings['folder'], 'This automated native proof covers file selection/cancel only'
        child = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
        result = []
        def control():
            value = original([str(SHELL), '-NoLogo', '-NoProfile', '-WindowStyle', 'Hidden', '-EncodedCommand', base64.b64encode(AUTOMATE.encode('utf-16le')).decode()],
                             input=json.dumps(dict(process=child.pid, title=settings['label'], path=str(path or ''), cancel=path is None), ensure_ascii=False).encode(),
                             capture_output=True, timeout=25, creationflags=subprocess.CREATE_NO_WINDOW)
            result.append(value)
            (OUT / 'native-controller.stderr.txt').write_bytes(value.stderr)
            (OUT / 'native-controller.stdout.txt').write_bytes(value.stdout)
        helper = threading.Thread(target=control); helper.start()
        try:
            stdout, stderr = child.communicate(kwargs['input'], timeout=35)
            helper.join(timeout=28)
            assert result and result[0].returncode == 0, result[0].stderr.decode(errors='replace') if result else 'No controller result'
            return subprocess.CompletedProcess(command, child.returncode, stdout, stderr)
        finally:
            if child.poll() is None: child.kill(); child.wait(timeout=5)
    return patch('campuslab.local_targets.subprocess.run', run)


def main():
    OUT.mkdir(parents=True)
    result = dict(started=datetime.now(timezone.utc).isoformat(), checks=[], real=[], controlled=[], page_errors=[], external_requests=[],
                  scope='Same-computer agent browser; real fixed collectors. Target candidate injection, native automation, controlled failures and protocol fixtures are explicitly identified. No user acceptance, paid API call, GPU computation consent, model inference consent, Agent task or guest execution claimed.')
    def check(value): result['checks'].append(value); print(value, flush=True)
    def save(name, value): (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf8')
    try:
        with ExitStack() as stack:
            server = AppServer(0, OUT / 'courses.sqlite', ROOT / 'vendor/python-3.13.17-embed-amd64.zip')
            threading.Thread(target=server.serve_forever, daemon=True).start()
            stack.callback(server.server_close); stack.callback(server.shutdown)
            origin = 'http://127.0.0.1:' + str(server.server_port)
            result['actual_model_configuration'] = dict(configured=False)
            database = OUT / '中文 教学数据库.sqlite'; prepare_demo(database)
            original_discover = server.local_check.targets.discover
            controlled_choices = {'sqlite-basics': {'target': database},
                                  'local-qwen': {'model_dir': Path('D:/传智杯/artifacts/local-model/Qwen2.5-0.5B-Instruct')},
                                  'dsh-desktop': {'target': Path('D:/deep seekharness/DeepSeek Harness.exe')}}
            def discover(spec):
                value = original_discover(spec)
                for field, path in controlled_choices.get(spec['scenario'], {}).items():
                    if path.exists(): value['fields'][field]['choices'].append(server.local_check.targets.register(spec, field, str(path), '验收控制候选；真实已有目标，非自动发现证明'))
                return value
            server.local_check.targets.discover = discover
            with sync_playwright() as p:
                browser = p.chromium.launch(channel='msedge', headless=True)
                page = browser.new_page(viewport=dict(width=1440, height=1000), reduced_motion='reduce')
                page.on('pageerror', lambda error: result['page_errors'].append(str(error)))
                page.on('request', lambda request: result['external_requests'].append(request.url) if not request.url.startswith(origin + '/') else None)
                page.goto(origin); page.wait_for_function('()=>!!state.config&&typeof KehangChat!=="undefined"')
                result['actual_model_configuration'] = page.evaluate('({configured:state.config.ai.configured,destination:state.config.ai.destination,model:state.config.ai.model})')
                assert page.locator('#welcome-start').is_visible() and not page.locator('#learning-chat').is_visible()
                assert page.locator('.course-card:visible').count() == 0 and not server.local_check.jobs
                page.screenshot(path=OUT / '01-welcome-desktop.png')
                page.click('#chat-toggle'); assert page.evaluate('document.activeElement.id') == 'chat-input'
                page.click('#chat-close'); assert page.evaluate('document.activeElement.id') == 'chat-toggle'
                page.click('#chat-toggle'); page.keyboard.press('Escape'); assert not page.locator('#learning-chat').is_visible()
                page.reload(); page.wait_for_function('()=>!!state.config'); assert not page.locator('#learning-chat').is_visible()
                page.focus('#welcome-start'); page.keyboard.press('Enter'); assert page.locator('.course-card:visible').count() == 13
                assert not page.locator('#learning-chat').is_visible()
                page.screenshot(path=OUT / '02-selection-desktop.png', full_page=True)
                check('Welcome, refresh, keyboard Start, optional chat and focus return; no collector or model request on navigation.')

                def choose(scenario):
                    page.click('#home-nav'); page.click(f'[data-scenario="{scenario}"]')
                    page.wait_for_function('(s)=>state.task?.scenario===s&&guided.courseStep===1', arg=scenario)
                    if scenario != 'ai-web-deepseek':
                        page.click('#guide-next'); page.wait_for_function('()=>!document.querySelector("#local-target-status").textContent.includes("正在读取")')

                def discover_select(scenario):
                    page.click('#local-discover'); page.wait_for_function('()=>!document.querySelector("#local-discover").disabled')
                    fields = page.locator('#local-target-fields select')
                    for i in range(fields.count()):
                        select = fields.nth(i); field = select.get_attribute('data-field')
                        options = select.locator('option').evaluate_all('(items)=>items.filter(x=>x.value).map(x=>({value:x.value,path:x.textContent}))')
                        if not options: continue
                        preferred = str(Path('D:/ANACONDA/envs/pytorch/python.exe')) if scenario in ('pytorch-cpu','pytorch-gpu','local-qwen') and field == 'target' else str(Path('D:/ANACONDA/python.exe')) if field == 'target' else ''
                        choice = next((o for o in options if o['path'].casefold() == preferred.casefold()), options[0])
                        select.select_option(choice['value'])

                def run_pair(scenario):
                    page.click('#local-start'); page.wait_for_function('()=>!localState.running&&(!!localState.selected||!document.querySelector("#notice").hidden)', timeout=200000)
                    item = page.evaluate('localState.selected'); assert item and item.get('report'), (item,page.locator('#notice').inner_text())
                    first = item['report']; save(scenario + '-A.json', first)
                    page.screenshot(path=OUT / (scenario + '-result.png'), full_page=True)
                    page.click('#local-recheck'); page.wait_for_function('()=>!localState.running&&!!state.after', timeout=200000)
                    second = page.evaluate('state.after'); save(scenario + '-B.json', second)
                    comparison = compare(page.evaluate('state.task'), first, second); save(scenario + '-comparison.json', comparison)
                    assert first == page.evaluate('localState.selected.before')
                    result['real'].append(dict(scenario=scenario, target=first['target']['requested'], checks=analyze(page.evaluate('state.task'), second), comparison=comparison['outcome'], original_retained=True, selection='真实候选/文件窗口；SQLite、模型目录、DSH额外候选由验收脚本登记，采集器未替换'))
                    check('Real web initial/recheck: ' + scenario + ' => ' + comparison['outcome'])

                for scenario in SCENARIOS:
                    choose(scenario)
                    assert page.evaluate('state.before') is None
                    if scenario == 'ai-web-deepseek':
                        assert page.locator('#web-course-note').is_visible()
                        result['real'].append(dict(scenario=scenario, applicable=False, reason='网页学习课程无适用本机环境检测；保留官方学习入口与本人记录核验'))
                        continue
                    assert page.locator('#local-check-panel').is_visible()
                    if scenario != 'python-basics':
                        before = len(server.local_check.jobs); page.click('#local-start'); page.wait_for_timeout(100)
                        assert len(server.local_check.jobs) == before
                    discover_select(scenario)
                    if scenario == 'sqlite-basics':
                        # Exercise the unmodified production picker through the web endpoint.
                        if os.environ.get('KEHANG_TEST_NATIVE')=='1':
                            with native_control():
                                page.locator('#local-field-target').locator('..').locator('button').click()
                                page.wait_for_function('()=>document.querySelector("#local-target-status").textContent.includes("已取消")', timeout=40000)
                            with native_control(database):
                                page.locator('#local-field-target').locator('..').locator('button').click()
                                page.wait_for_function('()=>document.querySelector("#local-target-status").textContent.includes("已选择")', timeout=40000)
                            result['controlled'].append('Native file dialog: real process-owned selection/cancel; Unicode + space SQLite path; real collector below.')
                        else: result['controlled'].append('SQLite target chosen from explicitly controlled candidate; native dialog proof runs separately.')
                    if scenario == 'dsh-cli':
                        # No DSH CLI package in the verified standard installation locations.
                        result['real'].append(dict(scenario=scenario, ran=False, reason='已发现Node，未找到/未提供DSH CLI包；不伪造包或Agent执行。字段与失败由受控测试验证。'))
                        continue
                    if scenario == 'vm-linux': page.check('#local-host-only')
                    run_pair(scenario)

                # Controlled failure paths never substitute fabricated success for evidence.
                choose('node-basics')
                with patch.object(server.local_check.targets, 'discover', return_value=server.local_check.targets.configuration(task('node-basics'))):
                    page.click('#local-discover');page.wait_for_function('()=>document.querySelector("#local-target-status").textContent.includes("未发现")')
                    assert not page.locator('#local-field-target').input_value()
                result['controlled'].append('No discovery candidates: honest empty state and native fallback, no report.')

                choose('python-basics'); discover_select('python-basics')
                entered = threading.Event()
                def wait_runner(spec, target, cancelled): entered.set(); cancelled.wait(10); return None
                with patch.object(server.local_check, 'runner', wait_runner):
                    page.click('#local-start');page.wait_for_function('()=>localState.running');assert entered.wait(3)
                    page.click('#local-cancel');page.wait_for_function('()=>!localState.running');assert page.evaluate('state.before') is None
                result['controlled'].append('Cancel running collector: no manufactured report; owned real process-tree cancellation is separately unit-tested.')

                # Late POST acknowledgement after navigating away is cancelled, never changes route.
                choose('python-basics'); held=[]
                page.route('**/api/local-check', lambda route: held.append(route))
                page.click('#local-start');page.wait_for_timeout(100);assert held
                page.click('#back-home'); held.pop().continue_();page.wait_for_timeout(500)
                assert page.evaluate('guided.route') == 'home' and not page.locator('#learning-chat').is_visible()
                page.unroute('**/api/local-check')
                result['controlled'].append('Late local-check acknowledgement after Home never changes page; returned job receives cancel.')

                for width in [320,390,768,1120,1280,1440]:
                    page.set_viewport_size(dict(width=width,height=900));page.click('#home-link')
                    page.wait_for_timeout(250)
                    assert not page.locator('#learning-chat').is_visible()
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), ('welcome overflow',width)
                    page.click('#chat-toggle');assert page.locator('#chat-close').is_visible();page.keyboard.press('Escape')
                    page.click('#welcome-start'); assert not page.locator('#learning-chat').is_visible()
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), ('selection overflow',width)
                    choose('notebook-data')
                    assert page.locator('#learning-chat').is_visible() == (width>=1120)
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), ('course overflow',width)
                    if width==390:
                        page.screenshot(path=OUT/'04-config-mobile.png',full_page=True)
                        page.click('#back-home');page.screenshot(path=OUT/'03-welcome-mobile.png')
                check('320/390/768/1120/1280/1440 welcome/selection/course reflow; per-page AI defaults; reduced-motion setting; no horizontal overflow.')
                assert not result['page_errors'],result['page_errors']
                assert not result['external_requests'],result['external_requests']
                result['passed']=True
                browser.close()
    except BaseException:
        result['passed']=False;result['failure']=traceback.format_exc();raise
    finally:
        result['finished']=datetime.now(timezone.utc).isoformat();save('acceptance.json',result)
        print(str(OUT),flush=True)


if __name__=='__main__':main()
