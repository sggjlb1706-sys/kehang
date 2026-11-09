"""Real downloaded collectors; API remains uncalled and DSH remains uninstalled at selected paths."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import threading
import zipfile
from playwright.sync_api import sync_playwright
from campuslab.web import AppServer

ROOT=Path(__file__).resolve().parents[1]
PYTHON=r'D:\ANACONDA\python.exe'
NODE=r'D:\Program Files\nodejs\node.exe'

def main():
    out=ROOT/'records/reuse-ai/browser-ai'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out.mkdir(parents=True)
    work=ROOT/'records/runtime'/out.name;work.mkdir(parents=True)
    servers=[AppServer(0,work/(str(i)+'.sqlite'),ROOT/'vendor/python-3.13.17-embed-amd64.zip') for i in range(2)]
    threads=[threading.Thread(target=s.serve_forever,daemon=True) for s in servers]
    for t in threads:t.start()
    bases=[f'http://127.0.0.1:{s.server_port}' for s in servers]
    checks=[];errors=[];external=[];executions=[];complete=False
    def check(name):checks.append(name);print('PASS:',name,flush=True)
    def save(name,value):
        path=out/name;path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8');return path
    def execute(command,name):
        (out/(name+'.ps1')).write_text(command,encoding='utf-8-sig')
        proc=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',command],capture_output=True,timeout=70)
        (out/(name+'.stdout.txt')).write_bytes(proc.stdout);(out/(name+'.stderr.txt')).write_bytes(proc.stderr)
        executions.append(dict(name=name,returncode=proc.returncode,execution_policy_changed=False));assert proc.returncode==0,proc.stderr
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(channel='msedge',headless=True)
            context=browser.new_context(viewport={'width':1440,'height':1000},accept_downloads=True)
            context.on('request',lambda r:external.append(r.url) if r.url.startswith(('http://','https://')) and not any(r.url.startswith(b+'/') for b in bases) else None)
            page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.goto(bases[0]);page.wait_for_function('()=>state.config!==null')
            for scenario in ('deepseek-api','ai-web-deepseek','dsh-desktop','dsh-cli'):
                page.select_option('#goal',scenario);page.locator('#goal-form button').click();page.wait_for_function('(s)=>state.task?.scenario===s',arg=scenario)
                spec=page.evaluate('()=>state.task');save(scenario+'-task.json',spec)
                with page.expect_download() as d:page.locator('#download-tool').click()
                archive=work/(scenario+'.zip');d.value.save_as(archive)
                folder=work/(scenario+" O'Brien ‘引’ $literal `tick");folder.mkdir()
                with zipfile.ZipFile(archive) as z:assert z.testzip() is None;z.extractall(folder)
                page.locator('#command-panel').evaluate('(e)=>e.open=true');page.fill('#tool-dir',str(folder))
                target=PYTHON if scenario=='deepseek-api' else str(folder) if scenario=='ai-web-deepseek' else NODE if scenario=='dsh-cli' else str(folder/'missing'/'DeepSeek Harness.exe')
                page.fill('#target',target)
                if scenario=='deepseek-api':
                    page.locator('#learning-preview').click();page.wait_for_function("()=>document.getElementById('learning-preview-text').value.includes('deepseek-flash')")
                    value=json.loads(page.locator('#learning-preview-text').input_value());assert value['endpoint']=='https://api.deepseek.com/chat/completions'
                    assert len(value['payload']['messages'])==2
                    page.locator('#api-send').check();page.fill('#learning-preview-text',json.dumps(value,ensure_ascii=False)+'\n')
                    assert not page.locator('#api-send').is_checked()
                    with page.expect_download() as d:page.locator('#save-learning-preview').click()
                    preview=folder/'edited-api-preview.json';d.value.save_as(preview);page.fill('#api-preview-path',str(preview))
                    check('API exact destination/model/system/content preview is editable; editing revokes send selection')
                if scenario.startswith('dsh-'):
                    page.fill('#dsh-workspace',str(folder/'practice'));page.fill('#dsh-provider','deepseek');page.fill('#dsh-model','deepseek-flash')
                    if scenario=='dsh-cli':page.fill('#dsh-package',str(folder/'missing-dsh'/'package.json'))
                    page.locator('#prepare-dsh').click();execute(page.locator('#prepare-script').inner_text(),scenario+'-prepare')
                    assert (folder/'practice/input.csv').is_file()
                reports=[]
                for stage in ('A','B'):
                    page.select_option('#report-stage',stage);page.locator('#make-command').click();command=page.locator('#command').inner_text()
                    assert '--api-send' not in command and 'Set-ExecutionPolicy' not in command
                    execute(command,scenario+'-'+stage)
                    report=json.loads((folder/('report-'+stage+'.json')).read_text(encoding='utf-8'));reports.append(report)
                    reportpath=save(scenario+'-'+stage+'.json',report);page.set_input_files('#before-file' if stage=='A' else '#after-file',str(reportpath))
                    page.wait_for_function('(n)=>state[n]!==null',arg='before' if stage=='A' else 'after')
                    page.wait_for_function('()=>!document.getElementById("lesson-panel").hidden')
                assert not page.evaluate('()=>state.analysis.passed')
                if scenario=='deepseek-api':
                    assert reports[-1]['facts']['run']['category']=='not_called'
                if scenario.startswith('dsh-'):
                    assert page.evaluate("()=>state.analysis.checks.find(c=>c.id==='dsh:software').status==='missing'")
                    if scenario=='dsh-desktop':assert not any(c['id']=='dsh:node' for c in page.evaluate('()=>state.analysis.checks'))
                    else:assert page.evaluate("()=>state.analysis.checks.find(c=>c.id==='dsh:node').status==='pass'")
                with page.expect_download() as d:page.locator('#export-course').click()
                package=out/(scenario+'-course.json');d.value.save_as(package)
                with page.expect_download() as d:page.locator('#export-guide').click()
                guide=out/(scenario+'-guide.html');d.value.save_as(guide)
                second=context.new_page();second.goto(bases[1]);second.set_input_files('#course-package',str(package));second.wait_for_function('(id)=>state.task?.id===id',arg=spec['id'])
                second.set_input_files('#before-file',str(out/(scenario+'-A.json')));second.wait_for_function('()=>state.before!==null')
                second.set_input_files('#after-file',str(out/(scenario+'-B.json')));second.wait_for_function('()=>state.after!==null');assert not second.evaluate('()=>state.analysis.passed');second.close()
                page.locator('#export').click();page.wait_for_function('()=>!document.getElementById("export-preview").hidden')
                assert 'share_only' in page.locator('#export-preview').input_value() and r'C:\Users\DELL' not in page.locator('#export-preview').input_value()
                page.locator('#lesson-panel').evaluate('(e)=>e.open=true');page.locator('#lesson-retry').focus();page.keyboard.press('Enter');assert page.locator('#report-stage').input_value()=='B'
                page.locator('#command-panel').evaluate('(e)=>e.open=false');page.screenshot(path=str(out/(scenario+'-desktop.png')),full_page=True)
                page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                page.screenshot(path=str(out/(scenario+'-mobile-390.png')),full_page=True);page.set_viewport_size({'width':1440,'height':1000})
                invalid=save(scenario+'-constructed-invalid.json',{'schema':1})
                page.set_input_files('#before-file',str(invalid));page.wait_for_function('()=>state.before===null&&state.analysis===null')
                assert page.locator('#lesson-panel').is_hidden() and not page.locator('#api-send').is_checked()
                check(scenario+': actual download/collector/A-B/import/package/offline/share/keyboard/mobile/invalid-state; no external call')
            # Constructed self record checks numerical work, never account authentication.
            page.select_option('#goal','ai-web-deepseek');page.locator('#goal-form button').click();page.wait_for_function("()=>state.task?.scenario==='ai-web-deepseek'")
            from campuslab.ai_course import collect_web,web_record_template
            spec=page.evaluate('()=>state.task');record=web_record_template(spec);record.update(completed=True,checked_sources=True,response='{"total":42,"count":3,"mean":14}')
            recordpath=save('constructed-self-record.json',record);report=collect_web(spec,str(work),recordpath);rp=save('constructed-web-report.json',report)
            page.set_input_files('#before-file',str(rp));page.wait_for_function('()=>state.analysis?.learning_completed===true');assert not page.evaluate('()=>state.analysis.passed')
            page.locator('#command-panel').evaluate('(e)=>e.open=true');page.fill('#target',str(work/'different'));assert page.evaluate('()=>state.analysis===null')
            page.set_input_files('#before-file',str(rp));page.wait_for_function("()=>document.getElementById('notice').textContent.includes('目标不同')");assert page.evaluate('()=>state.before===null')
            check('Constructed correct self record only completes learning; login unknown; selected target mismatch rejects import')
            assert not errors,errors;assert not external,external;browser.close();complete=True
    finally:
        for s in servers:s.shutdown();s.server_close()
        for t in threads:t.join()
        sources={f.relative_to(ROOT).as_posix():hashlib.sha256(f.read_bytes()).hexdigest().upper() for folder in ('campuslab','web') for f in (ROOT/folder).rglob('*') if f.is_file() and '__pycache__' not in f.parts}
        save('results.json',dict(status='passed' if complete else 'failed',checks=checks,executions=executions,browser_errors=errors,external_requests=external,source_sha256=sources,
            actual_api_calls=0,actual_dsh_runs=0,desktop_browser_emulation=True,physical_phone=False,second_device=False,constructed_reports=['constructed-self-record.json','constructed-web-report.json','*-constructed-invalid.json']))
        print('Evidence:',out,flush=True)

if __name__=='__main__':main()
