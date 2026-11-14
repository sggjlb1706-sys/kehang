"""Controlled UI failures and races. No fixture is evidence of an installed course."""
from contextlib import ExitStack
from datetime import datetime, timezone
import json
from pathlib import Path
import threading
import time
from playwright.sync_api import sync_playwright
from campuslab.web import AppServer
from campuslab.rules import task

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'records/round2/edges'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')


def main():
    OUT.mkdir(parents=True)
    result=dict(checks=[],scope='Controlled failures/races, plus a real Python baseline to verify original retention. Not real GPU/model/Agent evidence.')
    try:
        with ExitStack() as stack:
            server=AppServer(0,OUT/'courses.sqlite');threading.Thread(target=server.serve_forever,daemon=True).start()
            stack.callback(server.server_close);stack.callback(server.shutdown)
            origin='http://127.0.0.1:'+str(server.server_port)
            with sync_playwright() as p:
                browser=p.chromium.launch(channel='msedge',headless=True)
                page=browser.new_page(viewport=dict(width=1440,height=1000))
                page.goto(origin);page.wait_for_function('()=>!!state.config');page.click('#welcome-start')
                page.click('[data-scenario="python-basics"]');page.wait_for_function('()=>guided.courseStep===1')
                page.click('#start-python');page.wait_for_function('()=>!localState.running&&!!state.before',timeout=90000)
                original=page.evaluate('state.before')
                (OUT/'real-python-baseline.json').write_text(json.dumps(original,ensure_ascii=False,indent=2),encoding='utf8')
                server.local_check.runner=lambda *args:(_ for _ in ()).throw(OSError('controlled failure'))
                page.click('#local-recheck');page.wait_for_function('()=>!localState.running&&guided.courseStep===3')
                assert page.evaluate('state.before')==original and page.evaluate('state.after') is None
                assert page.locator('#local-recheck').is_enabled()
                result['checks'].append('Controlled recheck failure retains real original report and allows retry.')

                entered=threading.Event()
                def wait(spec,target,cancel):entered.set();cancel.wait(5);return None
                server.local_check.runner=wait
                page.click('#local-recheck');page.wait_for_function('()=>localState.running');assert entered.wait(2)
                page.click('#local-cancel');page.wait_for_function('()=>!localState.running&&guided.courseStep===3')
                assert page.evaluate('state.before')==original
                result['checks'].append('Cancel same-target recheck preserves original report in result view.')

                page.click('#home-nav');page.click('[data-scenario="node-basics"]');page.wait_for_function('()=>guided.courseStep===1');page.click('#guide-next')
                page.wait_for_function('()=>!!document.querySelector("#local-field-target")')
                missing=OUT/'node.exe';missing.touch()
                identity=server.local_check.targets.register(task('node-basics'),'target',str(missing.resolve()),'controlled disappearing target')
                def discover(route):
                    value=server.local_check.targets.configuration(task('node-basics'));value['fields']['target']['choices']=[identity]
                    route.fulfill(status=200,content_type='application/json',body=json.dumps(value))
                page.route('**/api/local-check/discover',discover)
                page.click('#local-discover');page.wait_for_function('()=>document.querySelector("#local-field-target").options.length===2')
                page.select_option('#local-field-target',identity['id']);missing.unlink();count=len(server.local_check.jobs)
                page.click('#local-start');page.wait_for_function('()=>!localState.running&&!document.querySelector("#notice").hidden')
                assert len(server.local_check.jobs)==count and page.evaluate('state.before') is None
                page.unroute('**/api/local-check/discover')
                result['checks'].append('Target disappears after choice: server refuses execution; no report or job.')

                held=[];page.route('**/api/local-check/pick',lambda route:held.append(route))
                page.locator('#local-target-fields button').first.click();page.wait_for_timeout(100);assert held
                page.click('#back-home')
                held.pop().fulfill(status=200,content_type='application/json',body=json.dumps(dict(selected=identity)))
                page.wait_for_timeout(100)
                assert page.evaluate('guided.route')=='home' and not page.locator('#learning-chat').is_visible()
                page.unroute('**/api/local-check/pick')
                result['checks'].append('Late picker response after Home cannot replace current fields or reopen chat.')

                # The responsive change was previously delayed; a subsequent click must win.
                page.set_viewport_size(dict(width=1000,height=900));page.click('#welcome-start')
                page.set_viewport_size(dict(width=1280,height=900));page.click('#chat-toggle');page.wait_for_timeout(300)
                assert page.locator('#learning-chat').is_visible()
                page.click('#chat-close');page.click('[data-scenario="node-basics"]');page.wait_for_function('()=>guided.courseStep===1')
                page.click('#guide-next');page.locator('#manual-collection>summary').click()
                page.fill('#target',r'D:\课程 环境\node.exe')
                assert page.locator('#manual-collection').get_attribute('open') is not None
                result['checks'].append('Responsive policy cannot undo an explicit chat click; manual target editing leaves the fallback open.')

                from copy import deepcopy
                from tests.test_torch_course import evidence
                spec,fixture=evidence(True)
                fixture['facts']['gpu']['run'].update(requested=False,returncode=None,result=None,device=None,device_uuid=None)
                def controlled_gpu(spec,target,cancel):
                    value=deepcopy(fixture);value['target'].update(requested=target,actual=target)
                    value['collected_at']=datetime.now(timezone.utc).isoformat();return value
                server.local_check.runner=controlled_gpu
                page.click('#home-nav');page.click('[data-scenario="pytorch-gpu"]');page.wait_for_function('()=>guided.courseStep===1');page.click('#guide-next')
                page.wait_for_selector('#local-field-target');page.click('#local-discover');page.wait_for_function('()=>document.querySelector("#local-field-target").options.length>1')
                choice=page.locator('#local-field-target option').nth(1).get_attribute('value');page.select_option('#local-field-target',choice)
                page.click('#local-start');page.wait_for_function('()=>!!state.before&&!localState.running')
                preparation=page.evaluate('state.before');assert not preparation['facts']['gpu']['run']['requested']
                page.check('#local-recheck-execution')
                page.once('dialog',lambda dialog:dialog.dismiss());count=len(server.local_check.jobs);page.click('#local-recheck')
                assert len(server.local_check.jobs)==count and page.evaluate('state.before')==preparation
                fixture['facts']['gpu']['run']=evidence(True)[1]['facts']['gpu']['run']
                page.once('dialog',lambda dialog:dialog.accept())
                with page.expect_request('**/api/local-check') as request:page.click('#local-recheck')
                assert request.value.post_data_json['execution']=={'gpu_run':True} and request.value.post_data_json['execution_consent'] is True
                page.wait_for_function('()=>!!state.after&&!localState.running')
                assert page.evaluate('localState.selected.before')==preparation
                assert page.evaluate('localState.selected.comparison.outcome')=='verified'
                result['checks'].append('Controlled GPU preparation A upgrades to explicitly confirmed execution B; dismiss sends no job; target and original preserved. No GPU was actually executed.')
                browser.close();result['passed']=True
    except Exception as error:
        result.update(passed=False,error=repr(error));raise
    finally:
        (OUT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
