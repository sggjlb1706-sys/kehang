"""Agent-operated browser proof; constructed submissions/reports are not student usage."""
from copy import deepcopy
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import tempfile
import threading

from playwright.sync_api import sync_playwright
from campuslab.practice import make_practice,submission_template
from campuslab.web import AppServer


ROOT=Path(__file__).resolve().parents[1]


def main():
    out=ROOT/'records/practice/ui'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ');out.mkdir(parents=True)
    checks=[];errors=[];external=[]
    def passed(name):checks.append(name);print('PASS '+name,flush=True)
    with tempfile.TemporaryDirectory(prefix='kehang-ui-proof-') as name:
        folder=Path(name);server=AppServer(0,folder/'courses.sqlite',ROOT/'vendor/python-3.13.17-embed-amd64.zip')
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();base=f'http://127.0.0.1:{server.server_port}'
        try:
            with sync_playwright() as p:
                browser=p.chromium.launch(channel='msedge',headless=True)
                context=browser.new_context(viewport={'width':1440,'height':1000},accept_downloads=True)
                context.on('request',lambda r:external.append(r.url) if r.url.startswith(('http://','https://')) and not r.url.startswith(base+'/') else None)
                page=context.new_page();page.on('pageerror',lambda error:errors.append(str(error)));page.goto(base)
                page.wait_for_function('()=>practiceState.practice!==null&&state.config!==null')
                page.locator('#practice-check').click();page.wait_for_function("()=>practiceState.attempts.at(-1)?.result.status==='missing'")
                spec=make_practice();good=submission_template(spec);good.update(notebook=spec['expected']['notebook'],sqlite=spec['expected']['sqlite'])
                invalid=deepcopy(good);invalid['private_extra']='PRIVATE-EXTRA-CONSTRUCTED-DO-NOT-EXPORT'
                wrong=deepcopy(good);wrong['notebook']['array_sum']=41
                for label,value,status in [('invalid',invalid,'invalid'),('wrong',wrong,'mismatch'),('correct',good,'pass')]:
                    file=folder/(label+'.json');file.write_text(json.dumps(value),encoding='utf-8')
                    page.set_input_files('#practice-submission',str(file));page.locator('#practice-check').click()
                    page.wait_for_function('(s)=>practiceState.attempts.at(-1)?.result.status===s',arg=status)
                assert page.locator('#practice-attempts li').count()==4
                assert '成果符合要求' in page.locator('#practice-artifact-status').inner_text()
                assert '本人尚未确认' in page.locator('#practice-reading-status').inner_text()
                assert '无当前报告' in page.locator('#practice-environment').inner_text()
                passed('missing/invalid/constructed-wrong/correct submissions retain four attempts and separate environment/reading states')
                with page.expect_download() as download:page.locator('#practice-completion').click()
                completion=out/'constructed-completion.json';download.value.save_as(completion)
                text=completion.read_text(encoding='utf-8');value=json.loads(text)
                assert 'PRIVATE-EXTRA-CONSTRUCTED' not in text and value['attempts'][1]['submission_omitted']
                assert [a['result']['status'] for a in value['attempts']]==['missing','invalid','mismatch','pass']
                passed('completion excludes arbitrary private extra fields and retains deterministic rejection plus source digest')
                value['attempts'][2]['result'].update(passed=True,status='pass')
                forged=folder/'forged-verdict.json';forged.write_text(json.dumps(value),encoding='utf-8')
                page.get_by_text('教师核对学生完成物',exact=True).click()
                page.set_input_files('#practice-completion-file',str(forged));page.wait_for_function("()=>document.querySelectorAll('#practice-teacher-review li').length===4")
                assert '结果不符合' in page.locator('#practice-teacher-review li').nth(2).inner_text()
                assert '成果符合要求' in page.locator('#practice-teacher-review li').nth(3).inner_text()
                passed('teacher rechecks retained historical submissions and rejects a forged stored pass verdict')
                page.locator('#practice-notebook').click();page.wait_for_function("()=>state.task?.scenario==='notebook-data'")
                assert page.locator('#simple-collector').is_visible()
                reports=ROOT/'records/reuse-ai/browser-data/20261110T003103340935Z'
                page.set_input_files('#report-files',[str(reports/'notebook-data-B.json'),str(reports/'notebook-data-A.json')])
                page.wait_for_function('()=>state.after!==null&&state.analysis?.passed===true')
                assert '按实际时间' in page.locator('#comparison').inner_text()
                assert 'Notebook：同目标复检通过' in page.locator('#practice-environment').inner_text()
                passed('one A/B selection orders archived Notebook reports by evidence time and preserves component identity')
                a=json.loads((reports/'notebook-data-A.json').read_text(encoding='utf-8'));b=deepcopy(a)
                for label,value in [('equal-a',a),('equal-b',b)]: (folder/(label+'.json')).write_text(json.dumps(value),encoding='utf-8')
                page.set_input_files('#report-files',[str(folder/'equal-b.json'),str(folder/'equal-a.json')]);page.wait_for_function("()=>document.querySelector('#notice').textContent.includes('无法确定先后')")
                assert page.evaluate('()=>state.before===null&&state.after===null&&state.analysis===null')
                assert 'Notebook：无当前报告' in page.locator('#practice-environment').inner_text()
                passed('ambiguous equal-time reports clear current evidence and cannot reuse old success')
                page.evaluate('()=>scrollTo(0,0)');page.screenshot(path=str(out/'desktop.png'))
                page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(out/'mobile.png'))
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                page.locator('header .brand').focus();page.keyboard.press('Tab');assert page.evaluate('document.activeElement!==document.body')
                passed('390px simulated mobile stays within viewport and keyboard focus remains available')
                browser.close()
        finally:
            server.shutdown();server.server_close();thread.join()
    assert not errors and not external,(errors,external)
    result=dict(passed=True,checks=checks,page_errors=errors,external_http_requests=external,
                scope='Agent browser operations; constructed result negatives and archive report re-analysis, not independent student or second-device evidence',
                source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ['web/app.js','web/index.html','web/style.css','campuslab/launcher.py']})
    (out/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(str(out),flush=True)


if __name__=='__main__':main()
