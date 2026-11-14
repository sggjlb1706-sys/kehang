"""Current UI/guidance regression. Real fixed checks and simulated states are separate."""
from contextlib import ExitStack
from copy import deepcopy
from datetime import datetime,timezone
import json
from pathlib import Path
import threading
from unittest.mock import patch
from playwright.sync_api import sync_playwright
from campuslab.web import AppServer
from campuslab.rules import task,analyze,compare
from campuslab.portable import export_package
from campuslab import dsh_course,ai_course

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'records/round3/verification'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')


def main():
    OUT.mkdir(parents=True)
    result=dict(scope='Same-computer browser. API/Node/DSH desktop fixed collectors are real; constructed report branches explicitly simulated. No API send, model, deployment, Agent or guest execution.',checks=[],real=[],simulated=[],errors=[],external_requests=[])
    def save(name,value):(OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf8')
    try:
        with ExitStack() as stack:
            server=AppServer(0,OUT/'courses.sqlite',ROOT/'vendor/python-3.13.17-embed-amd64.zip')
            threading.Thread(target=server.serve_forever,daemon=True).start();stack.callback(server.server_close);stack.callback(server.shutdown)
            origin='http://127.0.0.1:'+str(server.server_port)
            with sync_playwright() as p:
                browser=p.chromium.launch(channel='msedge',headless=True)
                page=browser.new_page(viewport=dict(width=1366,height=768),reduced_motion='reduce')
                page.on('pageerror',lambda error:result['errors'].append(str(error)))
                page.on('request',lambda request:result['external_requests'].append(request.url) if not request.url.startswith(origin+'/') else None)
                page.goto(origin);page.wait_for_function('()=>!!state.config&&!!practiceState.practice')
                assert not page.locator('#learning-chat').is_visible();page.click('#welcome-start')
                def choose(scenario):
                    page.click('#home-nav');page.click('[data-scenario="'+scenario+'"]')
                    page.wait_for_function('(s)=>state.task?.scenario===s&&guided.courseStep===1',arg=scenario)
                    assert page.locator('#prepared').input_value()=='unsure', 'Another course must not inherit a preparation declaration'
                for scenario in ['dsh-desktop','dsh-cli','deepseek-api']:
                    choose(scenario);identity=page.evaluate('JSON.stringify(state.task)')
                    page.select_option('#prepared','missing')
                    page.wait_for_function('()=>document.querySelector("#prepare-title").textContent.includes("先准备")')
                    assert '本人说明' in page.locator('#prepare-help').inner_text()
                    assert page.evaluate('state.before') is None and not server.local_check.jobs
                    page.select_option('#prepared','installed')
                    page.wait_for_function('()=>!document.querySelector("#prepare-title").textContent.includes("先准备")')
                    assert page.evaluate('JSON.stringify(state.task)')==identity
                    if scenario=='dsh-desktop':assert '系统Python或Node不是本路线前置条件' in page.locator('#prepare-summary').inner_text()
                    if scenario=='dsh-cli':assert '24.9.0' in page.locator('#prepare-summary').inner_text() and 'package.json' in page.locator('#prepare-summary').inner_text()
                    if scenario=='deepseek-api':assert '不发送API' in page.locator('#prepare-help').inner_text()
                result['checks'].append('Three course routes and all preparation declarations stay distinct from facts; correct tool/runtime and next step visible without expanding full guidance.')

                held=[]
                def delay(route):
                    if route.request.post_data_json.get('prepared')=='missing':held.append(route)
                    else:route.continue_()
                page.route('**/api/plan',delay);page.select_option('#prepared','missing');page.wait_for_timeout(100);assert held
                page.select_option('#prepared','installed');page.wait_for_function('()=>document.querySelector("#prepare-title").textContent.includes("预检")')
                held.pop().continue_();page.wait_for_timeout(150)
                assert '预检' in page.locator('#prepare-title').inner_text();page.unroute('**/api/plan')
                result['checks'].append('A late plan response for the previous preparation declaration cannot overwrite the current next step.')

                original=server.local_check.targets.discover
                def candidates(spec):
                    value=original(spec)
                    if spec['scenario']=='dsh-desktop':
                        path=Path('D:/deep seekharness/DeepSeek Harness.exe')
                        if path.is_file():value['fields']['target']['choices'].append(server.local_check.targets.register(spec,'target',str(path),'Controlled selection of real installed desktop target; not auto-discovery proof'))
                    return value
                server.local_check.targets.discover=candidates
                for scenario in ['node-basics','deepseek-api','dsh-desktop']:
                    choose(scenario);page.click('#guide-next');page.wait_for_selector('#local-field-target')
                    page.click('#local-discover');page.wait_for_function('()=>document.querySelector("#local-field-target").options.length>1')
                    page.select_option('#local-field-target',page.locator('#local-field-target option').nth(1).get_attribute('value'))
                    page.click('#local-start');page.wait_for_function('()=>!!state.before&&!localState.running',timeout=150000)
                    a=page.evaluate('state.before');save(scenario+'-real-A.json',a)
                    if scenario=='deepseek-api':assert '实际API响应' in page.locator('#course-next-guidance').inner_text() and not a['facts']['run']['attempted']
                    if scenario=='dsh-desktop':assert '专用练习目录' in page.locator('#course-next-guidance').inner_text() and a['facts']['agent'] is None
                    page.click('#local-recheck');page.wait_for_function('()=>!!state.after&&!localState.running',timeout=150000)
                    b=page.evaluate('state.after');save(scenario+'-real-B.json',b)
                    outcome=compare(page.evaluate('state.task'),a,b);save(scenario+'-comparison.json',outcome)
                    assert page.evaluate('localState.selected.before')==a
                    result['real'].append(dict(scenario=scenario,target=a['target']['requested'],comparison=outcome['outcome'],checks=analyze(page.evaluate('state.task'),b)))
                result['checks'].append('Fresh Node, API preparation and DSH desktop static web A/B preserve target, original, fixed facts and context-appropriate result guidance.')

                def import_state(spec,report,name):
                    package=OUT/(name+'-course.json');report_file=OUT/(name+'-SIMULATED-report.json')
                    package.write_text(json.dumps(export_package(spec),ensure_ascii=False),encoding='utf8');report_file.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
                    page.click('#home-nav');page.click('#import-entry');page.set_input_files('#course-package',package)
                    page.wait_for_function('(id)=>state.task?.id===id&&guided.courseStep===1',arg=spec['id'])
                    page.click('#guide-next');page.set_input_files('#before-file',report_file)
                    page.wait_for_function('()=>!!state.before&&!!state.analysis');page.click('#guide-next')
                    return page.locator('#course-next-guidance').inner_text()
                spec=task('deepseek-api',title='模拟展示状态 · API认证失败')
                report=dict(schema=1,task_id=spec['id'],collected_at=datetime.now(timezone.utc).isoformat(),target=dict(requested=r'C:\SIMULATED\python.exe',actual=r'C:\SIMULATED\python.exe',exists=True),
                            facts=dict(os='Windows',python='3.13.9',stdlib=True,request=ai_course.preview(spec),run=dict(attempted=True,category='authentication',http_status=401,model=None,role=None,finish_reason=None,content='',latency_ms=1)))
                text=import_state(spec,report,'api-auth');assert '认证问题' in text and '本次报告' in text
                result['simulated'].append('Constructed API401 report: authentication guidance, not an uncalled/deployment state; no network request.')

                spec=task('dsh-cli',title='模拟展示状态 · DSH CLI运行时不符合')
                node=OUT/'node.exe';node.touch()
                with patch('campuslab.dsh_course._node_identity',return_value=dict(actual=str(node),version='24.8.0',error='')):
                    report=dsh_course.collect(spec,str(node))
                text=import_state(spec,report,'dsh-cli-node');assert 'CLI运行时' in text and '24.9.0' in text
                result['simulated'].append('Constructed CLI runtime mismatch: Node-specific guidance, no Python/desktop substitution; dummy node never executed.')

                spec=task('dsh-desktop',title='模拟展示状态 · 桌面软件与工作区已核对')
                report=dsh_course.collect(spec,str(OUT/'missing-DSH.exe'))
                report['target'].update(exists=True,actual=report['target']['requested'])
                report['facts']['installation'].update(exists=True,product='DeepSeek Harness',version=spec['software_version'],sha256='a'*64,error='')
                report['facts']['workspace'].update(requested=str(OUT),actual=str(OUT),exists=True,id='12345678-1234-1234-1234-123456789012',task_id=spec['id'],input_sha256=dsh_course.INPUT_SHA,error='')
                text=import_state(spec,report,'dsh-model');assert 'DSH任务的模型接入' in text and '尚无真实DSH任务摘要' in text
                assert not page.evaluate('state.analysis.passed')
                result['simulated'].append('Constructed desktop installation/workspace checks: current next step is DSH model evidence, not reinstalling Python or claiming Agent completion.')

                for width,height in [(1912,948),(1366,768),(390,844)]:
                    page.set_viewport_size(dict(width=width,height=height));page.click('#home-link');page.wait_for_timeout(100)
                    assert not page.locator('#learning-chat').is_visible()
                    page.click('#chat-toggle');assert page.locator('#chat-input').is_visible();page.keyboard.press('Escape')
                    assert page.evaluate('document.activeElement.id')=='chat-toggle'
                    page.click('#welcome-start');assert not page.locator('#learning-chat').is_visible()
                    choose('deepseek-api');assert page.locator('#learning-chat').is_visible()==(width>=1120)
                    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
                result['checks'].append('1912x948, 1366x768 and390x844 route/AI policies, focus and input reachability preserved; no horizontal overflow.')
                assert not result['errors'] and not result['external_requests'],result
                result['passed']=True;browser.close()
    except Exception as error:result.update(passed=False,error=repr(error));raise
    finally:
        save('result.json',result);print(json.dumps(dict(passed=result.get('passed'),path=str(OUT),checks=len(result['checks']),real=len(result['real']),simulated=len(result['simulated'])),ensure_ascii=False))


if __name__=='__main__':main()
