"""Constructed UI race/identity regressions from independent review."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import threading
from playwright.sync_api import sync_playwright
from campuslab.rules import task
from campuslab.web import AppServer


def main():
    root=Path(__file__).resolve().parents[1]
    out=root/'records/courses/review-ui'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ');out.mkdir(parents=True)
    server=AppServer(0,root/'records/runtime/review-ui.sqlite');thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    checks=[];errors=[]
    try:
        report=json.loads((root/'records/browser/20261108T103533580266Z/actual-A.json').read_text(encoding='utf-8'))
        report['facts']['packages']['requests']=None;report['facts']['verification'].update(returncode=1,stdout='',error='Constructed missing dependency')
        fixture=out/'constructed-missing-package.json';fixture.write_text(json.dumps(report),encoding='utf-8')
        with sync_playwright() as p:
            browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(f'http://127.0.0.1:{server.server_port}')
            page.locator('#goal-form button').click();page.wait_for_selector('#guidance li')
            page.set_input_files('#before-file',str(fixture));page.wait_for_selector('#remediation .remedy')
            old=page.locator('#remediation').inner_text();assert '-m pip' in old
            page.locator('#command-panel').evaluate('(e)=>e.open=true');page.fill('#target',r'C:\NewCourse\python.exe')
            checks.append(dict(name='Changing target clears old repair commands',passed=page.locator('#remediation').inner_text()=='',observed=page.locator('#remediation').inner_text()))
            page.locator('#teacher-form').evaluate('(e)=>e.closest("details").open=true');page.fill('#teacher-title','Delayed teacher')
            pending=[];page.route('**/api/course',lambda route:pending.append(route))
            page.locator('#teacher-form button').click();page.wait_for_timeout(150);assert pending
            page.select_option('#goal','node-basics');page.locator('#goal-form button').click();page.wait_for_function("()=>state.task?.scenario==='node-basics'")
            pending[0].fulfill(status=200,content_type='application/json',body=json.dumps(dict(code='123456789A',task=task(title='Delayed teacher'))))
            page.wait_for_function("()=>!document.querySelector('#teacher-form button').disabled")
            observed=page.evaluate('()=>({scenario:state.task?.scenario,selected:document.querySelector("#goal").value})')
            checks.append(dict(name='Late teacher publish cannot replace a newer task',passed=observed['scenario']=='node-basics',observed=observed))
            page.unroute('**/api/course')
            page.select_option('#goal','python-basics');page.locator('#goal-form button').click();page.wait_for_function("()=>state.task?.scenario==='python-basics'")
            page.set_input_files('#before-file',str(fixture));page.wait_for_selector('#remediation .remedy')
            invalid=out/'constructed-wrong-task.json';wrong=dict(report);wrong['task_id']='wrong';invalid.write_text(json.dumps(wrong),encoding='utf-8')
            page.set_input_files('#before-file',str(invalid));page.wait_for_function("()=>document.querySelector('#before-file').value===''")
            checks.append(dict(name='Invalid new initial report clears previous repair guidance',passed=page.locator('#remediation').inner_text()=='',observed=page.locator('#remediation').inner_text()))
            browser.close()
    finally:
        server.shutdown();server.server_close();thread.join()
        result=dict(status='passed' if checks and all(x['passed'] for x in checks) and not errors else 'failed',checks=checks,browser_errors=errors,
            constructed_only=True,real_environment_repair=False,source_sha256={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest().upper() for folder in ('campuslab','web') for p in (root/folder).glob('*') if p.is_file()})
        (out/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(dict(path=str(out),status=result['status'])))
    if result['status']!='passed':raise SystemExit(1)


if __name__=='__main__':main()
