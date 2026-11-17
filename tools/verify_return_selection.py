"""Real one-click navigation plus labelled historical report regressions; no model requests."""
from pathlib import Path
import hashlib, json, os, sys, threading
from contextlib import ExitStack
from playwright.sync_api import sync_playwright
from campuslab.web import AppServer

ROOT=Path(__file__).resolve().parents[1]
OUT=Path(sys.argv[1])
PREVIOUS=ROOT.parents[1]/'交付/课航提交收尾-20261116-01/证据/最终浏览器'
RUNTIME=ROOT.parent/'python-3.13.17-embed-amd64.zip'

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    for key in list(os.environ):
        if key.startswith('CAMPUSLAB_AI_'):del os.environ[key]
    os.environ.update(TEMP=str(OUT.parent.parent/'temp'),TMP=str(OUT.parent.parent/'temp'))
    result=dict(checks=[],errors=[],external=[],model_sends=0,real='Agent fresh one-click A only; no fresh B. User separately reported one-click success.',
                historical='Manual A/B cases import unchanged 2026-11-16 reports; not new collection or user trial.')
    def save(name,obj):(OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf8')
    try:
        with ExitStack() as stack:
            srv=AppServer(0,OUT/'fresh.sqlite',RUNTIME)
            threading.Thread(target=srv.serve_forever,daemon=True).start()
            stack.callback(srv.server_close);stack.callback(srv.shutdown)
            origin='http://127.0.0.1:'+str(srv.server_port)
            with sync_playwright() as p:
                browser=p.chromium.launch(channel='msedge',headless=True)
                page=browser.new_page(viewport=dict(width=1366,height=900))
                page.on('pageerror',lambda e:result['errors'].append(str(e)))
                page.on('request',lambda r:result['external'].append(r.url) if not r.url.startswith(origin+'/') else None)
                def start():
                    page.goto(origin);page.wait_for_function('()=>!!state.config&&!!practiceState.practice')
                    page.click('#welcome-start');page.click('[data-scenario="python-basics"]')
                    page.wait_for_function('()=>state.task?.scenario==="python-basics"&&guided.courseStep===1')
                def selection():
                    assert page.evaluate('guided.route')=='selection',page.evaluate('guided.route')
                    assert page.locator('#selection-screen').is_visible() and not page.locator('#home-screen').is_visible()
                    assert page.locator('#course-grid button').count()==8
                    assert not page.locator('#learning-chat').is_visible()
                start();page.click('#start-python')
                page.wait_for_function('()=>!!state.before&&!localState.running&&guided.courseStep===3',timeout=90000)
                before=page.evaluate('state.before');assert page.evaluate('state.analysis.passed') and not page.evaluate('state.after')
                save('agent-oneclick-A.json',before)
                page.screenshot(path=OUT/'oneclick-result.png',full_page=True)
                label=page.locator('#guide-next').inner_text();page.click('#guide-next')
                save('first-navigation.json',dict(button_label=label,actual_route=page.evaluate('guided.route'),expected_route='selection'))
                page.screenshot(path=OUT/'after-return.png',full_page=True)
                selection();assert label=='返回选课' and page.evaluate('state.before')==before
                result['checks'].append('Fresh real one-click A passes; result returns to eight-course selection, keeps report and collapses AI.')
                page.click('[data-scenario="node-basics"]');page.wait_for_function('()=>state.task?.scenario==="node-basics"&&guided.courseStep===1')
                assert not page.evaluate('state.before||state.after')
                result['checks'].append('Choosing a different course after return clears old reports.')
                a=PREVIOUS/'REAL-python-A.json';b=PREVIOUS/'REAL-python-B.json'
                result['historical_files']=[dict(path=str(q),sha256=hashlib.sha256(q.read_bytes()).hexdigest()) for q in [a,b]]
                start();page.click('#guide-next');page.set_input_files('#report-files',str(a));page.wait_for_function('()=>!!state.analysis')
                page.click('#guide-next');assert page.locator('#guide-next').inner_text()=='去采集复检报告 →'
                page.click('#guide-next');assert page.locator('#report-stage').input_value()=='B' and page.evaluate('state.before')
                result['checks'].append('Historical manual A alone still opens B collection and retains A.')
                page.set_input_files('#report-files',str(b));page.wait_for_function('()=>!!state.after&&state.analysis?.passed');page.click('#guide-next')
                assert page.locator('#guide-next').inner_text()=='返回选课'
                page.locator('#guide-next').focus();page.keyboard.press('Enter');selection()
                result['checks'].append('Historical manual A/B success returns to course selection by keyboard.')
                page.set_viewport_size(dict(width=390,height=844));start();page.click('#guide-next')
                page.set_input_files('#report-files',[str(a),str(b)]);page.wait_for_function('()=>!!state.after&&state.analysis?.passed')
                page.click('#guide-next');page.click('#guide-next');selection()
                assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
                result['checks'].append('Narrow viewport return reaches course selection without overflow.')
                page.set_viewport_size(dict(width=1366,height=900));page.click('#start-practice')
                for _ in range(3):page.click('#guide-next')
                assert page.locator('#guide-next').inner_text()=='返回学习首页'
                page.click('#guide-next');assert page.evaluate('guided.route')=='home'
                result['checks'].append('Continuous-practice final action still returns to welcome home.')
                assert not result['errors'] and not result['external'];result['passed']=True;browser.close()
    except Exception as error:
        result.update(passed=False,error=repr(error));raise
    finally:
        save('result.json',result);print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
