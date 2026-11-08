"""Downloaded collectors on this device; no physical phone or guest success claim."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import socket
import subprocess
import threading
import zipfile
from playwright.sync_api import sync_playwright
from campuslab.web import AppServer

ROOT=Path(__file__).resolve().parents[1]
RUNTIME=ROOT/'vendor/python-3.13.17-embed-amd64.zip'
PYTORCH='D:\\ANACONDA\\envs\\pytorch\\python.exe'
VMRUN='C:\\Program Files (x86)\\VMware\\VMware Workstation\\vmrun.exe'


def main():
    run=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-courses'
    out=ROOT/'records/browser'/run;out.mkdir(parents=True)
    work=ROOT/'records/runtime'/run;work.mkdir(parents=True)
    servers=[AppServer(0,work/(str(i)+'.sqlite'),RUNTIME) for i in range(2)]
    threads=[threading.Thread(target=s.serve_forever,daemon=True) for s in servers]
    for t in threads:t.start()
    bases=[f'http://127.0.0.1:{s.server_port}' for s in servers]
    checks=[];errors=[];external=[];commands=[];completed=False
    def check(text):checks.append(text);print('PASS:',text,flush=True)
    def execute(page,name,limit=120):
        page.locator('#make-command').click();command=page.locator('#command').inner_text();assert command
        script=out/(name+'.ps1');script.write_text(command,encoding='utf-8-sig')
        proc=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(script)],capture_output=True,timeout=limit)
        (out/(name+'.stdout.txt')).write_bytes(proc.stdout);(out/(name+'.stderr.txt')).write_bytes(proc.stderr)
        commands.append(dict(script=script.name,returncode=proc.returncode));assert proc.returncode==0,proc.stderr
    def download_tool(page,name):
        with page.expect_download() as d:page.locator('#download-tool').click()
        archive=out/(name+'-tool.zip');d.value.save_as(archive)
        folder=work/(name+" O'Brien ‘引’ $literal `tick");folder.mkdir()
        with zipfile.ZipFile(archive) as z:
            assert z.testzip() is None;z.extractall(folder)
        page.locator('#command-panel').evaluate('(e)=>e.open=true');page.fill('#tool-dir',str(folder))
        return folder
    def copy_report(folder,name,stage):
        dest=out/(name+'-'+stage+'.json');dest.write_bytes((folder/('report-'+stage+'.json')).read_bytes());return dest
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(channel='msedge',headless=True)
            context=browser.new_context(viewport={'width':1440,'height':1000},accept_downloads=True)
            page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
            context.on('request',lambda r:external.append(r.url) if r.url.startswith(('http://','https://')) and not any(r.url.startswith(b+'/') for b in bases) else None)
            page.goto(bases[0]);page.wait_for_function('()=>state.config!==null')
            page.fill('#user-error','ModuleNotFoundError sk-abcdefghijklmnop');page.locator('#prepare-ai').click()
            page.wait_for_selector('#ai-preview-panel');assert '没有检测证据' in page.locator('#ai-preview').input_value()
            assert 'sk-abcdefghijklmnop' not in page.locator('#ai-preview').input_value();assert page.locator('#send-ai').is_disabled()
            check('Text-only error preview declares missing facts, redacts and requires explicit consent')
            page.fill('#need-text','深度学习课要求GPU运行PyTorch');page.locator('#need-form button').click()
            page.wait_for_selector('#need-result button');assert page.evaluate('()=>state.task===null')
            page.locator('#need-result button').first.click();page.wait_for_function("()=>state.task?.scenario==='pytorch-gpu'")
            spec=page.evaluate('()=>state.task');(out/'gpu-task.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding='utf-8')
            check('Natural language proposal creates a fixed GPU task only after confirmation')
            tool=download_tool(page,'gpu');page.fill('#target',PYTORCH)
            execute(page,'gpu-precheck-A');a=copy_report(tool,'gpu','A')
            page.set_input_files('#before-file',str(a));page.wait_for_selector('#results .state-unknown')
            assert not page.evaluate('()=>state.analysis.passed')
            page.locator('#gpu-run').check();page.select_option('#report-stage','B');execute(page,'gpu-run-B');b=copy_report(tool,'gpu','B')
            page.set_input_files('#after-file',str(b));page.wait_for_function("()=>document.querySelector('#comparison').textContent.includes('补齐实际运行证据')")
            assert page.locator('#results .state-pass').count()==9
            page.select_option('#mode','quick');page.wait_for_function('()=>document.querySelectorAll("#guidance li").length===2')
            page.locator('#command-panel').evaluate('(e)=>e.open=false');page.screenshot(path=str(out/'gpu-desktop-1440.png'))
            page.screenshot(path=str(out/'gpu-desktop-full.png'),full_page=True)
            check('Downloaded tool and generated PS5.1 command obtain real CPU and explicit GPU evidence with matching UUID')
            page.locator('#command-panel').evaluate('(e)=>e.open=true');page.locator('#hardware-panel').evaluate('(e)=>e.open=true')
            page.locator('#hardware-command').click();script=out/'actual-hardware.ps1';script.write_text(page.locator('#hardware-script').inner_text(),encoding='utf-8-sig')
            proc=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(script)],capture_output=True,timeout=80)
            commands.append(dict(script=script.name,returncode=proc.returncode));assert proc.returncode==0
            hw=out/'actual-hardware.json';hw.write_bytes((tool/'hardware.json').read_bytes())
            page.set_input_files('#hardware-file',str(hw));page.wait_for_selector('#hardware-results p')
            assert page.evaluate('()=>state.analysis.passed')
            check('Independent hardware command works from the downloaded tool without changing the environment verdict')
            with page.expect_download() as d:page.locator('#export-course').click()
            package=out/'teacher-course.json';d.value.save_as(package)
            with page.expect_download() as d:page.locator('#export-guide').click()
            guide=out/'offline-guide.html';d.value.save_as(guide)
            second=context.new_page();second.goto(bases[1]);second.set_input_files('#course-package',str(package))
            second.wait_for_function('(id)=>state.task?.id===id',arg=spec['id'])
            assert second.evaluate('()=>state.course!==null')
            second.set_input_files('#before-file',str(a));second.wait_for_selector('#results .state-unknown')
            second.set_input_files('#after-file',str(b));second.wait_for_function('()=>state.analysis?.passed===true')
            check('Portable teacher task transfers to an independent database with the same digest and original A/B acceptance')
            second.set_viewport_size({'width':390,'height':844});second.locator('#task-panel').scroll_into_view_if_needed();second.screenshot(path=str(out/'gpu-mobile-390.png'))
            assert second.evaluate('document.documentElement.scrollWidth<=innerWidth')
            guidepage=context.new_page();guidepage.set_viewport_size({'width':390,'height':844});guidepage.goto(guide.as_uri())
            assert spec['id'] in guidepage.locator('body').inner_text();assert guidepage.evaluate('document.documentElement.scrollWidth<=innerWidth')
            guidepage.screenshot(path=str(out/'offline-guide-mobile-390.png'));guidepage.close()
            check('Offline guide and course workflow are readable at 390px; desktop emulation only')
            tampered=json.loads(package.read_text(encoding='utf-8'));tampered['task']['title']='tampered'
            bad=out/'constructed-tampered-package.json';bad.write_text(json.dumps(tampered),encoding='utf-8')
            second.set_input_files('#course-package',str(bad));second.wait_for_function("()=>document.querySelector('#notice').classList.contains('error')")
            assert second.evaluate('()=>state.task===null&&state.analysis===null')
            check('Tampered package rejection clears prior task and success state')
            page.select_option('#goal','vm-linux');page.locator('#goal-form button').click();page.wait_for_function("()=>state.task?.scenario==='vm-linux'")
            vmtool=download_tool(page,'vm');page.fill('#target',VMRUN);page.select_option('#report-stage','A');execute(page,'vm-A')
            va=copy_report(vmtool,'vm','A');page.select_option('#report-stage','B');execute(page,'vm-B');vb=copy_report(vmtool,'vm','B')
            page.set_input_files('#before-file',str(va));page.wait_for_selector('#results .state-unknown')
            page.set_input_files('#after-file',str(vb));page.wait_for_function("()=>document.querySelector('#comparison').textContent.includes('仍未全部通过')")
            assert not page.evaluate('()=>state.analysis.passed');assert page.evaluate("()=>state.analysis.checks.find(x=>x.id==='vm:software').status==='pass'")
            page.select_option('#mode','quick');page.locator('#command-panel').evaluate('(e)=>e.open=false')
            page.screenshot(path=str(out/'vm-desktop-1440.png'));page.screenshot(path=str(out/'vm-desktop-full.png'),full_page=True)
            page.locator('#command-panel').evaluate('(e)=>e.open=true')
            page.fill('#vm-id','D:\\Different\\machine.vmx');assert page.evaluate('()=>state.before===null&&state.analysis===null')
            check('Real installed VMware is verified while absent instance and guest stay unknown; changing instance clears evidence')
            page.select_option('#goal','pytorch-cpu');page.locator('#goal-form button').click();page.wait_for_function("()=>state.task?.scenario==='pytorch-cpu'")
            assert page.locator('#torch-options').is_hidden()
            page.set_input_files('#before-file',str(ROOT/'records/courses/torch/float32-retest/cpu-A.json'));page.wait_for_function('()=>state.analysis?.passed===true')
            check('CPU task consumes its real fixed tensor report and does not offer the GPU-only trigger')
            assert not errors,errors;assert not external,external
            browser.close();completed=True
    finally:
        for s in servers:s.shutdown();s.server_close()
        for t in threads:t.join()
        sources={f.relative_to(ROOT).as_posix():hashlib.sha256(f.read_bytes()).hexdigest().upper() for folder in ('campuslab','web') for f in (ROOT/folder).glob('*') if f.is_file()}
        availability={}
        for port in (11434,1234):
            try:
                with socket.create_connection(('127.0.0.1',port),timeout=.5):availability[str(port)]='listening; no model request sent'
            except OSError:availability[str(port)]='not listening'
        result=dict(status='passed' if completed else 'failed',checks=checks,commands=commands,browser_errors=errors,external_requests=external,source_sha256=sources,
            physical_phone=False,second_device=False,guest_real_validation=False,real_ai_diagnosis=False,local_ai_ports=availability,paid_requests=0,installs=0,vm_start_calls=0)
        (out/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print('Evidence:',out,flush=True)


if __name__=='__main__':main()
