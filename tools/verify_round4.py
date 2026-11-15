"""Focused browser proof. Tools are only read; real execution is course Python A/B."""
from contextlib import ExitStack
from datetime import datetime, timezone
from http.server import HTTPServer
import json
import os
from pathlib import Path
import threading
from unittest.mock import patch
from playwright.sync_api import sync_playwright
from campuslab.web import AppServer
from campuslab.extensions import BY_ID, COURSES, LEGACY
from campuslab.portable import export_package
from campuslab.rules import task, compare
from verify_course_chat import ProtocolFixture

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'records/round4/verification'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    result = dict(time=datetime.now(timezone.utc).isoformat(), checks=[], errors=[], external=[], real=[], simulated=[])
    def save(name, value):
        (OUT/name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf8')
    def checked(text):
        result['checks'].append(text)
        print('PASS '+text, flush=True)
    try:
        with ExitStack() as stack:
            server = AppServer(0, ROOT/'data/temp/round4-verification.sqlite', ROOT/'vendor/python-3.13.17-embed-amd64.zip')
            threading.Thread(target=server.serve_forever, daemon=True).start()
            stack.callback(server.server_close); stack.callback(server.shutdown)
            origin = 'http://127.0.0.1:'+str(server.server_port)
            with sync_playwright() as p:
                browser = p.chromium.launch(channel='msedge', headless=True)
                page = browser.new_page(viewport=dict(width=1366, height=768), reduced_motion='reduce')
                requests=[]
                page.on('pageerror', lambda error: result['errors'].append(str(error)))
                page.on('request', lambda r: requests.append(r.url))
                page.on('request', lambda r: result['external'].append(r.url) if not r.url.startswith(origin+'/') else None)
                page.goto(origin); page.wait_for_function('()=>!!state.config&&!!practiceState.practice')
                page.click('#welcome-start')
                assert page.locator('#course-grid button').count()==8
                assert set(page.locator('#goal option').evaluate_all('(items)=>items.map(x=>x.value)'))==set(COURSES)|{'other'}
                assert set(page.locator('#teacher-goal option').evaluate_all('(items)=>items.map(x=>x.value)'))==set(COURSES)
                checked('8 course cards and both course selectors exclude all 5 legacy tool routes')

                page.click('#start-extensions');page.wait_for_selector('#extension-list:visible')
                assert page.locator('#extension-list [data-extension]').count()==6
                first=len(requests)
                for tool in BY_ID:
                    page.locator('[data-extension="'+tool+'"]').click()
                    page.wait_for_selector('#extension-guide:visible')
                    text=page.locator('#extension-guide').inner_text()
                    assert '2026-11-15' in text
                    for forbidden in ['初检','复检','sum=42','sum = 42','input.csv','report-A','选择目标并检测']:
                        assert forbidden not in text,(tool,forbidden)
                    assert not page.locator('#guide-shell').is_visible()
                    for width,height in [(1912,948),(1366,768),(390,844)]:
                        page.set_viewport_size(dict(width=width,height=height))
                        assert not page.evaluate('document.documentElement.scrollWidth>innerWidth'),tool
                        page.locator('.extension-content nav a').last.click()
                        assert page.locator('.extension-content section').last.is_visible()
                    page.set_viewport_size(dict(width=1366,height=768))
                    page.click('#extension-back')
                    page.wait_for_selector('#extension-list:visible')
                assert not any('/api/local-check/' in u or '/api/plan' in u or '/api/tool?' in u or '/api/analyze' in u for u in requests[first:])
                assert not server.local_check.jobs
                checked('All 6 guides, section anchors and 3 viewports work with zero collector/report/plan/tool-download requests')

                for tool in LEGACY:
                    package=OUT/(tool+'-HISTORICAL-course.json')
                    package.write_text(json.dumps(export_package(task(tool)),ensure_ascii=False),encoding='utf8')
                    page.click('#home-nav');page.click('#import-entry');page.set_input_files('#course-package',package)
                    page.wait_for_function('(id)=>guided.route==="extensions"&&KehangExtensions.current()===id',arg=tool)
                    page.wait_for_selector('#extension-guide:visible')
                    assert page.evaluate('state.task') is None
                checked('Each historical tool course package redirects to its matching guide without importing reports or collecting facts')

                page.goto(origin+'/?extension=deepseek-api');page.wait_for_selector('#extension-guide:visible')
                assert page.locator('#extensions-title').inner_text()=='DeepSeek API'
                page.click('#chat-toggle');page.fill('#chat-input','怎样查看 API 响应？');page.click('#chat-preview-button')
                page.wait_for_selector('#chat-preview-panel:visible')
                preview=list(server.chat.pending.values())[-1]['preview']['context']
                assert preview['extension']['id']=='deepseek-api' and 'evidence' not in preview and 'course' not in preview
                assert page.locator('#chat-send').is_disabled()
                page.click('#chat-cancel');page.click('#chat-close')
                page.click('#extension-back');page.locator('[data-extension="kehang-ai"]').click();page.wait_for_selector('#extension-guide:visible')
                page.click('#chat-toggle');assert page.locator('#chat-input').input_value()==''
                page.locator('#chat-setup').evaluate('(e)=>e.open=true');page.click('#chat-setup-guide')
                assert page.evaluate('KehangExtensions.current()')=='kehang-ai'
                checked('Direct guide URL, isolated tool-chat scopes, unconfigured preview-only consent and AI setup link work')

                page.click('#home-nav');page.click('#choose-course');page.locator('#need-form').evaluate('(e)=>e.closest("details").open=true')
                page.fill('#need-text','DeepSeek API');page.locator('#need-form button').click()
                page.wait_for_selector('#need-result button');assert '工具指南' in page.locator('#need-result button').inner_text()
                page.locator('#need-result button').click();page.wait_for_function('()=>guided.route==="extensions"&&KehangExtensions.current()==="deepseek-api"')
                checked('Learning-goal resolver opens the API guide instead of creating a course task')

                for scenario in COURSES:
                    page.click('#home-nav');page.click('[data-scenario="'+scenario+'"]')
                    page.wait_for_function('(s)=>state.task?.scenario===s&&guided.courseStep===1',arg=scenario)
                    assert page.locator('#guide-shell').is_visible()
                checked('All 8 real course preparation routes remain reachable')

                page.click('#home-nav');page.click('[data-scenario="python-basics"]')
                page.wait_for_function('()=>state.task?.scenario==="python-basics"&&guided.courseStep===1')
                page.click('#start-python');page.wait_for_function('()=>!!state.before&&!localState.running',timeout=90000)
                before=page.evaluate('state.before');spec=page.evaluate('state.task');save('REAL-python-A.json',before)
                page.click('#local-recheck');page.wait_for_function('()=>!!state.after&&!localState.running',timeout=90000)
                after=page.evaluate('state.after');save('REAL-python-B.json',after)
                assert page.evaluate('state.before')==before
                comparison=compare(spec,before,after);save('REAL-python-comparison.json',comparison)
                result['real'].append(dict(scenario=spec['scenario'],target=before['target']['requested'],outcome=comparison['outcome']))
                for width,height in [(1912,948),(1366,768),(390,844)]:
                    page.set_viewport_size(dict(width=width,height=height));page.screenshot(path=OUT/('REAL-python-result-'+str(width)+'.png'))
                    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
                checked('Fresh real Python A/B retains the original task, target and A report; result has no horizontal overflow')

                for width,height in [(1912,948),(1366,768),(390,844)]:
                    page.set_viewport_size(dict(width=width,height=height));page.click('#home-link');assert not page.locator('#learning-chat').is_visible()
                    page.click('#chat-toggle');assert page.locator('#chat-input').is_visible();page.keyboard.press('Escape')
                    assert page.evaluate('document.activeElement.id')=='chat-toggle'
                    page.click('#welcome-start');assert not page.locator('#learning-chat').is_visible()
                    page.click('[data-scenario="java-jdk"]');page.wait_for_function('()=>state.task?.scenario==="java-jdk"&&guided.courseStep===1')
                    assert page.locator('#learning-chat').is_visible()==(width>=1120)
                    page.click('#extensions-nav');page.wait_for_selector('#extension-list:visible');assert not page.locator('#learning-chat').is_visible()
                checked('Home/selection/tool AI stays collapsed; real-course desktop AI opens, mobile stays optional; Escape restores focus')

                page.click('#home-nav');page.click('#start-practice');page.click('#guide-next')
                assert page.locator('#practice-prepare').is_visible();page.click('#practice-notebook')
                page.wait_for_function('()=>state.task?.scenario==="notebook-data"&&guided.courseStep===1');page.click('#back-practice')
                assert page.locator('#practice-prepare').is_visible()
                page.click('#teacher-nav');page.click('#practice-publish');page.wait_for_function('()=>!document.querySelector("#practice-export-package").disabled')
                checked('Practice-to-Notebook and return plus teacher local practice publication remain functional')

                contrast=page.evaluate('''()=>{
                  const c=document.createElement('canvas').getContext('2d'),s=getComputedStyle(document.documentElement);
                  function color(v){c.fillStyle=v;c.fillRect(0,0,1,1);return [...c.getImageData(0,0,1,1).data].slice(0,3);}
                  function lum(v){return color(v).map(x=>{x/=255;return x<=.04045?x/12.92:((x+.055)/1.055)**2.4;}).reduce((a,x,i)=>a+x*[.2126,.7152,.0722][i],0);}
                  const token=n=>s.getPropertyValue('--'+n).trim();const out=[];
                  for(const fg of ['ink','muted','brand','success','error'])for(const bg of ['bg','surface','soft']){
                    let a=lum(token(fg)),b=lum(token(bg));out.push({fg,bg,ratio:(Math.max(a,b)+.05)/(Math.min(a,b)+.05),minimum:4.5});}
                  for(const [fg,bg] of [['focus','bg'],['focus','surface'],['control-line','surface']]){let a=lum(token(fg)),b=lum(token(bg));out.push({fg,bg,ratio:(Math.max(a,b)+.05)/(Math.min(a,b)+.05),minimum:3});}
                  let a=lum('white'),b=lum(token('brand'));out.push({fg:'white',bg:'brand',ratio:(Math.max(a,b)+.05)/(Math.min(a,b)+.05),minimum:4.5});return out;
                }''')
                save('contrast.json',contrast)
                assert all(x['ratio']>=x['minimum'] for x in contrast),contrast
                checked('19 computed palette text/button/focus/control contrast pairs meet their WCAG thresholds; status labels remain textual')
                assert not result['errors'] and not result['external'],result
                fixture=HTTPServer(('127.0.0.1',0),ProtocolFixture)
                threading.Thread(target=fixture.serve_forever,daemon=True).start()
                stack.callback(fixture.server_close);stack.callback(fixture.shutdown)
                ProtocolFixture.calls=[];ProtocolFixture.fail=False
                with patch.dict(os.environ,{'CAMPUSLAB_AI_URL':'http://127.0.0.1:'+str(fixture.server_port)+'/chat',
                                            'CAMPUSLAB_AI_MODEL':'ROUND4-LOCAL-PROTOCOL-FIXTURE','CAMPUSLAB_AI_KEY':''}):
                    page.set_viewport_size(dict(width=1366,height=768));page.goto(origin)
                    page.wait_for_function('()=>!!state.config');page.click('#welcome-start');page.click('[data-scenario="python-basics"]')
                    page.wait_for_function('()=>state.task?.scenario==="python-basics"&&guided.courseStep===1')
                    for i in range(2):
                        page.fill('#chat-input','本地协议测试问题 '+str(i));page.click('#chat-preview-button');page.wait_for_selector('#chat-preview-panel:visible')
                        assert len(ProtocolFixture.calls)==i
                        preview=list(server.chat.pending.values())[-1]['preview']
                        assert len(preview['messages'])==i*2+1 and preview['context']['scenario']=='python-basics'
                        page.click('#chat-send');page.wait_for_function('(n)=>document.querySelectorAll(".chat-assistant").length===n',arg=i+1)
                    assert len(ProtocolFixture.calls)==2 and page.locator('.chat-assistant img').count()==0
                    held=[];page.route('**/api/chat',lambda route:held.append(route))
                    page.fill('#chat-input','延迟回复隔离');page.click('#chat-preview-button');page.wait_for_selector('#chat-preview-panel:visible');page.click('#chat-send')
                    page.wait_for_timeout(100);assert held
                    page.click('#extensions-nav');page.wait_for_selector('#extension-list:visible')
                    held.pop().fulfill(status=200,content_type='application/json',body=json.dumps(dict(completed=True,explanation='SIMULATED LATE RESPONSE',evidence_verdict_changed=False)))
                    page.wait_for_timeout(100);assert not page.locator('#learning-chat').is_visible()
                    page.click('#chat-toggle');assert page.locator('.chat-assistant').count()==0
                    page.unroute('**/api/chat')
                    result['simulated'].append('Two user-consented turns reached a local HTTP fixture; held late response was explicitly simulated. No real model/API/Agent request.')
                    checked('Local protocol fixture verifies per-turn preview/consent, multi-turn context, text-only rendering and late-response isolation after opening tools')
                assert not result['errors'] and not result['external'],result
                result['passed']=True;browser.close()
    except Exception as error:
        result.update(passed=False,error=repr(error));raise
    finally:
        save('result.json',result)
        print(json.dumps(dict(passed=result.get('passed'),checks=len(result['checks']),path=str(OUT)),ensure_ascii=False))


if __name__=='__main__':main()
