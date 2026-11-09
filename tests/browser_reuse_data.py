"""Real downloaded Notebook/JDK/SQLite tools on this PC; no physical-device claim."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import threading
import traceback
import zipfile

from playwright.sync_api import sync_playwright
from campuslab.web import AppServer

ROOT=Path(__file__).resolve().parents[1]
RUNTIME=ROOT/'vendor/python-3.13.17-embed-amd64.zip'
PYTHON=r'D:\ANACONDA\python.exe'
KERNEL=r'D:\ANACONDA\share\jupyter\kernels\python3\kernel.json'
JDK=r'C:\Program Files\Zulu\zulu-21'


def sources():
    return {f.relative_to(ROOT).as_posix():hashlib.sha256(f.read_bytes()).hexdigest().upper()
        for folder in ('campuslab','web') for f in (ROOT/folder).rglob('*')
        if f.is_file() and '__pycache__' not in f.parts and f.suffix!='.pyc'}


def main():
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=ROOT/'records/reuse-ai/browser-data'/stamp;out.mkdir(parents=True)
    work=ROOT/'records/runtime'/('reuse-data-'+stamp);work.mkdir(parents=True)
    servers=[AppServer(0,work/(str(i)+'.sqlite'),RUNTIME) for i in range(2)]
    threads=[threading.Thread(target=s.serve_forever,daemon=True) for s in servers]
    for thread in threads:thread.start()
    bases=[f'http://127.0.0.1:{s.server_port}' for s in servers]
    checks=[];errors=[];external=[];executions=[];archives=[];completed=False;failure=None;start_sources=sources()
    def check(text):checks.append(text);print('PASS: '+text,flush=True)
    def save(name,value):
        path=out/name;path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8');return path
    def execute(command,name):
        assert command and '-ExecutionPolicy' not in command
        (out/(name+'-command.txt')).write_text(command,encoding='utf-8')
        # Pasted-command route works under the current policy. No .ps1 policy override is used.
        proc=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',command],capture_output=True,timeout=200)
        (out/(name+'-stdout.txt')).write_bytes(proc.stdout);(out/(name+'-stderr.txt')).write_bytes(proc.stderr)
        executions.append(dict(name=name,returncode=proc.returncode,policy_override=False))
        assert proc.returncode==0,(name,proc.stderr.decode(errors='replace'))
    def import_a(page,path):
        page.set_input_files('#before-file',str(path));page.wait_for_function('()=>state.before!==null&&state.analysis?.passed===true')
        page.wait_for_function('()=>!document.querySelector("#lesson-panel").hidden')
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(channel='msedge',headless=True)
            context=browser.new_context(viewport=dict(width=1440,height=1000),accept_downloads=True)
            context.on('page',lambda page:page.on('pageerror',lambda error:errors.append(str(error))))
            context.on('request',lambda request:external.append(request.url) if request.url.startswith(('http://','https://')) and not any(request.url.startswith(base+'/') for base in bases) else None)
            page=context.new_page();page.goto(bases[0]);page.wait_for_function('()=>state.config!==null')
            for scenario,target,count in [('notebook-data',PYTHON,10),('java-jdk',JDK,6),('sqlite-basics',None,5)]:
                page.set_viewport_size(dict(width=1440,height=1000))
                page.select_option('#goal',scenario);page.locator('#goal-form button').click()
                page.wait_for_function('(scenario)=>state.task?.scenario===scenario',arg=scenario)
                page.wait_for_selector('#guidance li');spec=page.evaluate('()=>state.task')
                assert not page.evaluate('()=>state.analysis!==null')
                save(scenario+'-task.json',spec)
                # Publish the same fixed task through the real teacher form before downloading it.
                page.locator('#teacher-form').evaluate('(e)=>e.closest("details").open=true')
                page.select_option('#teacher-goal',scenario);page.fill('#teacher-title',spec['title'])
                page.locator('#teacher-form button').click();page.wait_for_function('()=>state.course!==null')
                assert page.evaluate('()=>state.task.id')==spec['id']
                with page.expect_download() as download:page.locator('#download-tool').click()
                archive=work/(scenario+'-tool.zip');download.value.save_as(archive)
                tool=work/(scenario+" 工具 O'Brien ‘引’ $literal `tick");tool.mkdir()
                with zipfile.ZipFile(archive) as z:
                    assert z.testzip() is None;assert json.loads(z.read('task.json'))==spec
                    assert not any(name.startswith(('/', '\\')) or '..' in Path(name).parts for name in z.namelist())
                    z.extractall(tool);entries=z.namelist()
                archives.append(dict(scenario=scenario,sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),entries=entries,crc_passed=True))
                page.locator('#command-panel').evaluate('(e)=>e.open=true');page.fill('#tool-dir',str(tool));page.fill('#tool-python','')
                if scenario=='sqlite-basics':target=str(tool/'scores.sqlite')
                page.fill('#target',target)
                if scenario=='notebook-data':page.fill('#kernel-spec',KERNEL)
                if scenario=='sqlite-basics':
                    page.locator('#prepare-sqlite').click();execute(page.locator('#prepare-script').inner_text(),scenario+'-explicit-prepare')
                    assert Path(target).is_file()
                page.focus('#target');page.keyboard.press('Tab');assert page.evaluate('()=>document.activeElement.id')=='tool-python'
                for stage in ('A','B'):
                    page.select_option('#report-stage',stage);page.locator('#make-command').click()
                    execute(page.locator('#command').inner_text(),scenario+'-'+stage)
                    destination=out/(scenario+'-'+stage+'.json');destination.write_bytes((tool/('report-'+stage+'.json')).read_bytes())
                    if stage=='A':import_a(page,destination)
                    else:
                        page.set_input_files('#after-file',str(destination));page.wait_for_function('()=>state.after!==null&&state.analysis?.passed===true')
                        page.wait_for_function('()=>document.querySelector("#comparison").textContent.includes("稳定复检通过")')
                assert page.locator('#results .state-pass').count()==count
                page.wait_for_function('(count)=>document.querySelectorAll("#lesson-checks p").length===count',arg=count)
                check(scenario+': downloaded embedded tool and original generated commands obtain real A/B, same task and stable retest')
                original=page.evaluate('()=>JSON.stringify(state.analysis)')
                for mode in ('novice','standard','quick'):
                    page.select_option('#mode',mode);page.evaluate('()=>guidance()')
                    assert page.evaluate('()=>JSON.stringify(state.analysis)')==original
                page.locator('#lesson-panel').evaluate('(e)=>e.open=true');page.locator('#lesson-retry').click()
                assert page.input_value('#report-stage')=='B';assert page.locator('#lesson-retry').is_disabled()
                assert page.evaluate('()=>JSON.stringify(state.analysis)')==original
                check(scenario+': three guidance modes, keyboard tab and Educates-derived manual retry preserve deterministic facts')
                with page.expect_download() as download:page.locator('#export-course').click()
                package=out/(scenario+'-course.json');download.value.save_as(package)
                with page.expect_download() as download:page.locator('#export-guide').click()
                guide=out/(scenario+'-guide.html');download.value.save_as(guide)
                second=context.new_page();second.goto(bases[1]);second.wait_for_function('()=>state.config!==null')
                second.set_input_files('#course-package',str(package));second.wait_for_function('(id)=>state.task?.id===id',arg=spec['id'])
                import_a(second,out/(scenario+'-A.json'));second.set_input_files('#after-file',str(out/(scenario+'-B.json')))
                second.wait_for_function('()=>state.after!==null&&state.analysis?.passed===true')
                second.wait_for_function('()=>document.querySelector("#comparison").textContent.includes("稳定复检通过")')
                assert second.evaluate('()=>state.task.id')==spec['id']
                check(scenario+': real teacher package transfers to an independent local database with unchanged snapshot and A/B acceptance')
                page.locator('#command-panel').evaluate('(e)=>e.open=false');page.locator('#results').scroll_into_view_if_needed()
                page.screenshot(path=str(out/(scenario+'-desktop.png')));page.screenshot(path=str(out/(scenario+'-desktop-full.png')),full_page=True)
                second.set_viewport_size(dict(width=390,height=844));second.select_option('#mode','quick');second.evaluate('()=>guidance()')
                second.locator('#command-panel').evaluate('(e)=>e.open=false');second.locator('#results .check').first.scroll_into_view_if_needed()
                assert second.evaluate('()=>document.documentElement.scrollWidth<=innerWidth')
                second.screenshot(path=str(out/(scenario+'-mobile-390.png')))
                offline=context.new_page();offline.set_viewport_size(dict(width=390,height=844));offline.goto(guide.as_uri())
                assert spec['id'] in offline.locator('body').inner_text();assert offline.evaluate('()=>document.documentElement.scrollWidth<=innerWidth')
                offline.screenshot(path=str(out/(scenario+'-offline-390.png')));offline.close()
                check(scenario+': desktop and 390px workflow/offline guide fit; desktop emulation, no physical phone claim')
                second.locator('#export').click();second.wait_for_selector('#export-preview')
                assert json.loads(second.input_value('#export-preview'))['share_only'] is True
                malformed=save(scenario+'-constructed-invalid-A.json',{'schema':1,'task_id':'invalid'})
                second.set_input_files('#before-file',str(malformed));second.wait_for_function('()=>state.before===null&&state.analysis===null')
                assert second.locator('#results .check').count()==0
                assert second.locator('#lesson-panel').is_hidden() and second.locator('#export-preview').is_hidden()
                assert second.locator('#save-export').is_hidden() and second.locator('#after-file').is_disabled()
                check(scenario+': invalid new A clears prior facts, share and derived teaching steps')
                page.locator('#command-panel').evaluate('(e)=>e.open=true')
                if scenario=='notebook-data':
                    page.fill('#kernel-spec',KERNEL+'.different')
                else:page.fill('#target',target+'.different')
                assert page.evaluate('()=>state.before===null&&state.after===null&&state.analysis===null')
                assert page.locator('#results .check').count()==0;assert page.locator('#lesson-panel').is_hidden()
                check(scenario+': changing the selected environment component clears prior success and retry state')
                second.close()
            assert not errors,errors;assert not external,external
            browser.close();completed=True
    except Exception as exc:
        failure=type(exc).__name__+': '+str(exc)
        (out/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8')
        raise
    finally:
        for server in servers:server.shutdown();server.server_close()
        for thread in threads:thread.join(timeout=5)
        end_sources=sources()
        result=dict(status='passed' if completed else 'failed',checks=checks,commands=executions,archives=archives,
            browser_errors=errors,external_requests=external,failure=failure,source_sha256=end_sources,
            start_source_sha256=start_sources,source_stable=start_sources==end_sources,
            scope=['notebook-data','java-jdk','sqlite-basics'],services_stopped=all(not t.is_alive() for t in threads),
            physical_phone=False,second_computer=False,real_ai_request=False,paid_requests=0,installs=0,vm_starts=0,execution_policy_changed=False)
        (out/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print('Evidence: '+str(out),flush=True)


if __name__=='__main__':main()
