"""Actual bundle/browser check, with optional automation of our own file dialog."""
import argparse
import base64
from contextlib import ExitStack
from datetime import datetime,timezone
from io import BytesIO
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import traceback
from urllib.request import urlopen
import zipfile

from playwright.sync_api import sync_playwright
from campuslab.launcher import FILE_DIALOG_SCRIPT
from campuslab.rules import analyze,compare,task
from campuslab.web import AppServer

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'records/path-help'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
POWERSHELL=Path(os.environ.get('SystemRoot',r'C:\Windows'))/'System32/WindowsPowerShell/v1.0/powershell.exe'

def ps(script):
    return [str(POWERSHELL),'-NoLogo','-NoProfile','-STA','-WindowStyle','Hidden','-EncodedCommand',base64.b64encode(script.encode('utf-16le')).decode()]

def dialog_check(folder):
    # Invoke only the window owned by this exact new PowerShell process. No global keys/clicks.
    automation=r'''
$ErrorActionPreference = 'Stop'
[Console]::InputEncoding = [Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$s = [Console]::In.ReadToEnd() | ConvertFrom-Json
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$pidCondition = [Windows.Automation.PropertyCondition]::new([Windows.Automation.AutomationElement]::ProcessIdProperty,[int]$s.process)
$titleCondition = [Windows.Automation.PropertyCondition]::new([Windows.Automation.AutomationElement]::NameProperty,'选择课程 Python：python.exe（不要选包内 runtime）')
$condition = [Windows.Automation.AndCondition]::new($pidCondition,$titleCondition)
$w = $null
for ($i=0; $i -lt 60; $i++) {
    $w = [Windows.Automation.AutomationElement]::RootElement.FindFirst([Windows.Automation.TreeScope]::Children,$condition)
    if ($null -ne $w) { break }
    Start-Sleep -Milliseconds 100
}
if ($null -eq $w) { throw 'Owned dialog not found' }
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class OwnedDialogNative {
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
    [DllImport("user32.dll",CharSet=CharSet.Unicode)] public static extern IntPtr SendMessage(IntPtr h,uint m,IntPtr w,string text);
    [DllImport("user32.dll")] public static extern IntPtr SendMessage(IntPtr h,uint m,IntPtr w,IntPtr l);
}
'@
function OwnHandle($element) {
    if ($null -eq $element) { throw 'Owned control missing' }
    $h=[IntPtr]$element.Current.NativeWindowHandle
    [uint32]$controlProcess=0
    [void][OwnedDialogNative]::GetWindowThreadProcessId($h,[ref]$controlProcess)
    if ($h -eq [IntPtr]::Zero -or $controlProcess -ne [uint32]$s.process) { throw 'Control ownership mismatch' }
    return $h
}
function ById($id,$type) {
    $c = [Windows.Automation.PropertyCondition]::new([Windows.Automation.AutomationElement]::AutomationIdProperty,$id)
    if ($null -ne $type) { $t=[Windows.Automation.PropertyCondition]::new([Windows.Automation.AutomationElement]::ControlTypeProperty,$type);$c=[Windows.Automation.AndCondition]::new($c,$t) }
    return $w.FindFirst([Windows.Automation.TreeScope]::Descendants,$c)
}
if ($s.cancel) { $b=ById '2' }
else {
    $e=ById '1148'
    if ($null -eq $e) {
        $w.FindAll([Windows.Automation.TreeScope]::Descendants,[Windows.Automation.Condition]::TrueCondition) | ForEach-Object { @{id=$_.Current.AutomationId;name=$_.Current.Name;type=$_.Current.ControlType.ProgrammaticName} } | ConvertTo-Json -Depth 3
        throw 'File-name control not found'
    }
    [void][OwnedDialogNative]::SendMessage((OwnHandle $e),0x000C,[IntPtr]::Zero,[string]$s.path)
    $b=ById '1'
}
if ($null -eq $b) { throw 'Owned dialog action not found' }
[void][OwnedDialogNative]::SendMessage((OwnHandle $b),0x00F5,[IntPtr]::Zero,[IntPtr]::Zero)
'''
    chosen=folder/'中文 课程 Python/python.exe';chosen.parent.mkdir();chosen.write_bytes(b'dialog-only fixture, never executed')
    results=[]
    for cancel in [False,True]:
        # Run choose_file itself, but record its one owned PS pid for targeted UI automation.
        child=subprocess.Popen(ps(FILE_DIALOG_SCRIPT),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                               text=True,encoding='utf8',creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            child.stdin.write(json.dumps(dict(kind='python',directory=str(chosen.parent)),ensure_ascii=False));child.stdin.close()
            control=subprocess.run(ps(automation),input=json.dumps(dict(process=child.pid,path=str(chosen),cancel=cancel),ensure_ascii=False).encode('utf8'),
                                   capture_output=True,timeout=18,creationflags=subprocess.CREATE_NO_WINDOW)
            if control.returncode:
                (OUT/'dialog-automation-error.txt').write_bytes(control.stderr)
                (OUT/'owned-dialog-controls.json').write_bytes(control.stdout)
                raise RuntimeError('Owned dialog automation failed; native stderr retained in external test evidence')
            child.wait(timeout=8)
            stdout=child.stdout.read();stderr=child.stderr.read()
            assert child.returncode==0,(stdout,stderr)
            value=json.loads(stdout.strip().lstrip('\ufeff'))['selected']
            assert value is None if cancel else Path(value)==chosen
            results.append(dict(cancelled=cancel,passed=True,unicode_space_path=not cancel))
        finally:
            if child.poll() is None:child.kill();child.wait(timeout=5)
            child.stdout.close();child.stderr.close()
    return results

def main(dialog=False):
    OUT.mkdir(parents=True)
    result=dict(checks=[],page_errors=[],remote_requests=[])
    try:
        with tempfile.TemporaryDirectory(prefix='课航 路径验收 ') as directory,ExitStack() as stack:
            folder=Path(directory)
            server=AppServer(0,folder/'new.sqlite',ROOT/'vendor/python-3.13.17-embed-amd64.zip')
            threading.Thread(target=server.serve_forever,daemon=True).start();stack.callback(server.server_close);stack.callback(server.shutdown)
            origin='http://127.0.0.1:'+str(server.server_port)
            for goal in ['python-basics','notebook-data']:
                with urlopen(origin+'/api/tool?goal='+goal) as response,zipfile.ZipFile(BytesIO(response.read())) as z:
                    assert z.testzip() is None
                    assert z.read('campuslab/launcher.py')==(ROOT/'campuslab/launcher.py').read_bytes()
                    assert 'Anaconda Prompt' in z.read('查找课程Python与内核.txt').decode('utf8')
                    if goal=='python-basics':z.extractall(folder/'解压后 工具')
            result['checks'].append('Python/Notebook downloads contain new selector and matching offline path help; ZIP CRC and source bytes verified')
            bundle=folder/'解压后 工具';command=[str(bundle/'runtime/python.exe'),'-X','utf8','-B','-m','campuslab.launcher']
            cancelled=subprocess.run(command,input='\nQ\n',capture_output=True,text=True,encoding='utf8',cwd=bundle,timeout=20)
            (OUT/'actual-list-and-cancel.txt').write_bytes(cancelled.stdout.encode('utf8'))
            assert cancelled.returncode==0 and '未检测' in cancelled.stdout and not (bundle/'report-A.json').exists()
            result['checks'].append('Actual embedded-runtime launcher lists local registered/PATH candidates without starting a course program; Q writes no report')
            for stage in ['A','B']:
                process=subprocess.run(command,input='"D:\\ANACONDA\\python.exe"\n'+stage+'\nSTART\n',capture_output=True,text=True,encoding='utf8',cwd=bundle,timeout=30)
                (OUT/('actual-'+stage+'.txt')).write_bytes(process.stdout.encode('utf8'))
                assert process.returncode==0,process.stderr
                report=json.loads((bundle/('report-'+stage+'.json')).read_bytes())
                assert analyze(task('python-basics'),report)['passed']
                (OUT/('report-'+stage+'.json')).write_bytes((bundle/('report-'+stage+'.json')).read_bytes())
            a,b=[json.loads((OUT/('report-'+s+'.json')).read_bytes()) for s in ['A','B']]
            assert compare(task('python-basics'),a,b)['outcome']=='stable-pass'
            result['checks'].append('Actual new downloaded runtime collects explicit existing course Python A/B only after START; both pass same-target comparison')
            if dialog:
                result['native_dialog']=dialog_check(folder)
                result['checks'].append('Actual Windows native dialog selects Unicode/space fixture path and cancels via process-owned UI Automation, without executing fixture')
            with sync_playwright() as p:
                browser=p.chromium.launch(channel='msedge',headless=True)
                try:
                    page=browser.new_page(viewport=dict(width=1360,height=900))
                    page.on('pageerror',lambda e:result['page_errors'].append(str(e)))
                    page.on('request',lambda r:result['remote_requests'].append(r.url) if r.url.startswith(('http://','https://')) and not r.url.startswith(origin+'/') else None)
                    page.goto(origin);page.wait_for_function('()=>!!state.config&&!!practiceState.practice')
                    page.click('#start-python');page.wait_for_function('()=>guided.courseStep===1');page.click('#guide-next')
                    assert page.locator('#python-path-help').is_visible() and not page.locator('#kernel-path-help').is_visible()
                    page.locator('#python-location-help summary').click()
                    assert page.locator('#python-location-help pre').inner_text()=='python -c "import sys; print(sys.executable)"'
                    page.screenshot(path=OUT/'python-path-help.png',full_page=True)
                    page.set_viewport_size(dict(width=390,height=844))
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                    page.screenshot(path=OUT/'python-path-help-mobile.png',full_page=True)
                    page.locator('#guide-progress button').nth(0).click();page.select_option('#goal','notebook-data');page.locator('#goal-form button').click()
                    page.wait_for_function('()=>guided.courseStep===1');page.click('#guide-next')
                    assert page.locator('#kernel-path-help').is_visible();page.locator('#kernel-path-help summary').click()
                    assert 'kernelspec list' in page.locator('#kernel-path-help').inner_text()
                    page.screenshot(path=OUT/'notebook-path-help-mobile.png',full_page=True)
                    assert not result['page_errors'] and not result['remote_requests']
                    result['checks'].append('Point-of-use Python finding steps, optional Anaconda manual command, Notebook kernel help and 390px layout work with no remote requests')
                finally:browser.close()
        result['passed']=True
    except Exception:
        result.update(passed=False,failure=traceback.format_exc());raise
    finally:
        result['scope']='Agent-owned temporary services; actual local fixed Python A/B; native dialog fixture is not executed; no install/model request.'
        (OUT/'result.json').write_bytes(json.dumps(result,ensure_ascii=False,indent=2).encode('utf8'))
        print(json.dumps(dict(output=str(OUT),passed=result.get('passed'),checks=len(result['checks']))))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--dialog',action='store_true');main(parser.parse_args().dialog)
