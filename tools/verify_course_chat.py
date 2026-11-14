"""Same-computer browser checks; AI responses below are a local protocol fixture."""
from contextlib import ExitStack
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import tempfile
import threading
from unittest.mock import patch

from playwright.sync_api import sync_playwright
from campuslab.web import AppServer

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'records/course-chat' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
SCENARIOS = ['python-basics', 'node-basics', 'java-jdk', 'notebook-data', 'sqlite-basics', 'pytorch-cpu', 'pytorch-gpu', 'local-qwen', 'ai-web-deepseek', 'deepseek-api', 'dsh-desktop', 'dsh-cli', 'vm-linux']


class ProtocolFixture(BaseHTTPRequestHandler):
    calls = []
    fail = False

    def do_POST(self):
        type(self).calls.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
        value = {'text': 'invalid fixture'} if type(self).fail else {'choices': [{'message': {'content': '本地协议测试回复。先确认课程，再按当前步骤继续。<img src=x onerror=alert(1)>'}, 'finish_reason': 'stop'}]}
        raw = json.dumps(value).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *args):
        pass


def main():
    OUT.mkdir(parents=True)
    checks, errors, external = [], [], []
    result = dict(checks=checks, page_errors=errors, external_requests=external,
                  scope='Same-computer agent browser. Chat uses an explicitly local HTTP protocol fixture, not a real AI service. No installation, paid model call, external-device or official-submission claim.')
    try:
        with ExitStack() as stack:
            folder = Path(stack.enter_context(tempfile.TemporaryDirectory(prefix='course-chat-', dir=ROOT / 'data/temp')))
            server = AppServer(0, folder / 'courses.sqlite', ROOT / 'vendor/python-3.13.17-embed-amd64.zip')
            threading.Thread(target=server.serve_forever, daemon=True).start()
            stack.callback(server.server_close); stack.callback(server.shutdown)
            model = HTTPServer(('127.0.0.1', 0), ProtocolFixture)
            threading.Thread(target=model.serve_forever, daemon=True).start()
            stack.callback(model.server_close); stack.callback(model.shutdown)
            config = stack.enter_context(patch.dict(os.environ, {'CAMPUSLAB_AI_URL': f'http://127.0.0.1:{model.server_port}/chat', 'CAMPUSLAB_AI_MODEL': 'local-protocol-fixture', 'CAMPUSLAB_AI_KEY': ''}))
            origin = 'http://127.0.0.1:' + str(server.server_port)
            with sync_playwright() as p, ExitStack() as browser_stack:
                browser = p.chromium.launch(channel='msedge', headless=True)
                browser_stack.callback(browser.close)
                page = browser.new_page(viewport=dict(width=1440, height=1000))
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.on('request', lambda request: external.append(request.url) if not request.url.startswith(origin + '/') else None)
                page.goto(origin)
                page.wait_for_function('()=>!!state.config&&!!practiceState.practice&&typeof KehangChat!=="undefined"')
                assert page.locator('.course-card:visible').count() == 13
                assert not page.locator('#start-python').is_visible()
                assert not server.local_check.jobs and not ProtocolFixture.calls
                ids = page.locator('[id]').evaluate_all('(items)=>items.map(e=>e.id)')
                assert len(ids) == len(set(ids))
                page.screenshot(path=OUT / '01-home-desktop.png', full_page=True)
                for group, count in [('coding', 3), ('data', 2), ('ai', 7), ('system', 1), ('all', 13)]:
                    page.click(f'[data-filter="{group}"]')
                    assert page.locator('.course-card:visible').count() == count
                    assert page.locator(f'[data-filter="{group}"]').get_attribute('aria-pressed') == 'true'
                checks.append('All 13 courses visible on entry; five filters work; opening/filtering triggers no collection or model request.')

                for scenario in SCENARIOS:
                    page.click('#home-nav')
                    page.click(f'.course-card[data-scenario="{scenario}"]')
                    page.wait_for_function('(s)=>state.task?.scenario===s&&guided.courseStep===1', arg=scenario)
                    assert page.locator('#preparation').is_visible()
                    assert not page.locator('#collect-stage').is_visible()
                    assert not page.evaluate('state.before||state.after||state.analysis')
                    assert page.locator('#chat-input').input_value() == ''
                    page.click('#guide-next')
                    assert page.locator('#collect-stage').is_visible()
                assert not server.local_check.jobs and not ProtocolFixture.calls
                checks.append('Every home course button reaches its matching preparation and collector; navigation does not create report evidence.')

                page.click('#home-nav'); page.click('.course-card[data-scenario="java-jdk"]')
                page.wait_for_function('()=>state.task?.scenario==="java-jdk"&&guided.courseStep===1')
                def send(question, answer_count):
                    page.fill('#chat-input', question)
                    page.click('#chat-preview-button')
                    page.wait_for_selector('#chat-preview-panel:visible')
                    assert len(ProtocolFixture.calls) == answer_count - 1
                    if page.locator('#chat-preview-panel > details').get_attribute('open') is None:
                        page.locator('#chat-preview-panel > details > summary').click()
                    assert question in page.locator('#chat-preview').inner_text()
                    page.click('#chat-send')
                    page.wait_for_function('(n)=>document.querySelectorAll(".chat-assistant").length===n', arg=answer_count)
                send('JDK 是什么？', 1)
                page.click('#guide-next')
                assert page.locator('.chat-assistant').count() == 1
                send('那我应该选择哪个目录？', 2)
                messages = ProtocolFixture.calls[-1]['messages']
                assert [x['role'] for x in messages] == ['system', 'user', 'assistant', 'user']
                assert 'java-jdk' in messages[0]['content'] and '运行检测' in messages[0]['content']
                assert not page.locator('#chat-messages img').count()
                page.screenshot(path=OUT / '02-course-conversation.png', full_page=True)
                checks.append('Two real loopback HTTP requests preserve follow-up roles and fresh step context; generated HTML is displayed as plain text.')

                page.fill('#chat-input', '保留这个草稿'); page.click('#chat-preview-button')
                page.wait_for_selector('#chat-preview-panel:visible')
                page.fill('#chat-input', '编辑后应重新预览')
                assert not page.locator('#chat-preview-panel').is_visible()
                page.click('#chat-preview-button');page.wait_for_selector('#chat-preview-panel:visible')
                page.click('#guide-prev')
                assert not page.locator('#chat-preview-panel').is_visible()
                page.click('#home-nav');page.click('#choose-course')
                assert page.locator('.chat-message').count()==0 and not page.locator('#chat-input').input_value()
                assert 'Java' not in page.locator('#chat-context').inner_text()
                page.fill('#chat-input','我该选择什么课程？');page.click('#chat-preview-button')
                page.wait_for_selector('#chat-preview-panel:visible')
                selection_preview=list(server.chat.pending.values())[-1]['preview']
                assert selection_preview['context']['course'] is None
                assert len(selection_preview['context']['supported_courses'])==13
                page.click('#chat-cancel')
                page.click('#home-nav');page.click('.course-card[data-scenario="sqlite-basics"]')
                page.wait_for_function('()=>state.task?.scenario==="sqlite-basics"&&guided.courseStep===1')
                assert page.locator('.chat-message').count() == 0 and page.locator('#chat-input').input_value() == ''
                page.click('#home-nav');page.click('.course-card[data-scenario="java-jdk"]')
                page.wait_for_function('()=>state.task?.scenario==="java-jdk"&&guided.courseStep===1')
                assert page.locator('.chat-assistant').count() == 2 and page.locator('#chat-input').input_value() == '编辑后应重新预览'
                checks.append('Editing or changing step invalidates previews; course conversations and drafts are isolated and restored.')

                ProtocolFixture.fail = True
                page.click('#chat-preview-button');page.wait_for_selector('#chat-preview-panel:visible');page.click('#chat-send')
                page.wait_for_function('()=>document.querySelector("#chat-status").textContent.includes("未能回复")')
                assert page.locator('.chat-assistant').count() == 2 and page.locator('#chat-input').input_value()
                ProtocolFixture.fail = False
                page.click('#chat-clear')
                assert not page.locator('.chat-message').count() and not page.locator('#chat-input').input_value()
                checks.append('Invalid protocol response creates no fabricated answer; retry retains input; new conversation clears local history.')

                with patch.dict(os.environ, {'CAMPUSLAB_AI_URL': '', 'CAMPUSLAB_AI_MODEL': ''}):
                    page.reload();page.wait_for_function('()=>!!state.config&&typeof KehangChat!=="undefined"')
                    page.fill('#chat-input', '我想学 Python');page.click('#chat-preview-button')
                    page.wait_for_selector('#chat-preview-panel:visible')
                    assert page.locator('#chat-send').is_disabled()
                    assert '尚未连接' in page.locator('#chat-connection').inner_text()
                    assert page.locator('#chat-setup').is_visible()
                    assert not page.locator('.chat-assistant').count()
                    page.screenshot(path=OUT / '03-unconfigured.png', full_page=True)
                checks.append('Unconfigured model is clearly identified, with setup instructions, preview-only interaction and no simulated AI answer.')

                page.goto(origin);page.wait_for_function('()=>!!state.config&&typeof KehangChat!=="undefined"')
                page.click('#teacher-nav');page.locator('#teacher-course-panel > summary').click()
                page.select_option('#teacher-goal', 'node-basics');page.locator('#teacher-form button').click()
                page.wait_for_function('()=>guided.route==="teacher"&&state.task?.scenario==="node-basics"')
                page.locator('#course-sharing > summary').click()
                with page.expect_download() as download:
                    page.click('#export-course')
                download.value.save_as(folder / 'single-course.json')
                page.click('#home-nav');page.click('#import-entry')
                page.set_input_files('#course-package', folder / 'single-course.json')
                page.wait_for_function('()=>guided.route==="course"&&guided.courseStep===1&&state.task?.scenario==="node-basics"')
                page.click('#home-nav');page.click('#start-practice')
                assert page.locator('#practice-intro').is_visible()
                page.click('#guide-next');page.click('#practice-notebook')
                page.wait_for_function('()=>state.task?.scenario==="notebook-data"&&guided.courseStep===1')
                page.click('#back-practice');page.wait_for_function('()=>guided.route==="practice"&&guided.practiceStep===1')
                page.click('#guide-next')
                with page.expect_download() as download:
                    page.click('#practice-materials')
                download.value.save_as(folder / 'practice.zip')
                assert (folder / 'practice.zip').stat().st_size > 0
                page.click('#guide-next');assert page.locator('#practice-submission').is_visible()
                checks.append('Teacher publishes/exports and student imports the same course; practice material download and return from component guidance remain reachable.')

                # A late reply from another course must never appear in the active conversation.
                page.click('#home-nav');page.click('.course-card[data-scenario="java-jdk"]')
                page.wait_for_function('()=>state.task?.scenario==="java-jdk"&&guided.courseStep===1')
                delayed = []
                page.route('**/api/chat', lambda route: delayed.append(route))
                page.fill('#chat-input', '延迟响应测试');page.click('#chat-preview-button')
                page.wait_for_selector('#chat-preview-panel:visible');page.click('#chat-send')
                page.wait_for_timeout(80);assert delayed
                page.click('#home-nav');page.click('.course-card[data-scenario="sqlite-basics"]')
                page.wait_for_function('()=>state.task?.scenario==="sqlite-basics"&&guided.courseStep===1')
                with page.expect_response('**/api/chat'):
                    delayed.pop().continue_()
                page.wait_for_timeout(100)
                assert not page.locator('.chat-message').count()
                page.unroute('**/api/chat')
                checks.append('Delayed reply from another course is discarded rather than appearing in the current chat.')

                page.click('#home-nav')
                page.click('.course-card[data-scenario="python-basics"]')
                page.wait_for_function('()=>state.task?.scenario==="python-basics"&&guided.courseStep===1')
                assert page.locator('#start-python').is_visible()
                page.click('#start-python')
                page.wait_for_function('()=>!!localState.selected?.report', timeout=120000)
                assert page.evaluate('guided.courseStep') == 3
                assert page.locator('#local-ai').is_visible()
                assert not page.locator('#report-files').is_visible()
                original = page.evaluate('localState.selected.report')
                (OUT / 'real-report-A.json').write_text(json.dumps(original, ensure_ascii=False, indent=2), encoding='utf8')
                page.click('#local-ai')
                assert page.locator('#chat-input').input_value().startswith('这个检测结果')
                page.click('#chat-preview-button');page.wait_for_selector('#chat-preview-panel:visible')
                preview = list(server.chat.pending.values())[-1]['preview']
                assert isinstance(preview['context']['evidence'], dict)
                assert preview['context']['scenario'] == 'python-basics'
                page.click('#chat-cancel')
                page.screenshot(path=OUT / '04-real-python-result.png', full_page=True)
                page.click('#local-recheck')
                page.wait_for_function('()=>!!state.after&&!localState.running', timeout=120000)
                (OUT / 'real-report-B.json').write_text(json.dumps(page.evaluate('state.after'), ensure_ascii=False, indent=2), encoding='utf8')
                checks.append('Fresh real Python A/B collection works from the course flow; result chat preview uses the validated selected report.')

                page.click('#teacher-nav')
                if page.locator('#teacher-course-panel').get_attribute('open') is None:
                    page.locator('#teacher-course-panel > summary').click()
                page.select_option('#teacher-goal','python-basics');page.fill('#teacher-title','自定义 Python 3.14 课程')
                page.fill('#python-min','3.14');page.fill('#python-max','3.15');page.locator('#teacher-form button').click()
                page.wait_for_function('()=>guided.route==="teacher"&&state.task?.python?.min==="3.14"')
                if page.locator('#course-sharing').get_attribute('open') is None:
                    page.locator('#course-sharing > summary').click()
                with page.expect_download() as download:
                    page.click('#export-course')
                download.value.save_as(folder/'custom-python.json')
                page.click('#home-nav');page.click('#import-entry');page.set_input_files('#course-package',folder/'custom-python.json')
                page.wait_for_function('()=>guided.route==="course"&&guided.courseStep===1&&state.task?.python?.min==="3.14"')
                custom_id=page.evaluate('state.task.id');custom_code=page.evaluate('state.course')
                with page.expect_request('**/api/local-check') as request:
                    page.click('#start-python')
                assert request.value.post_data_json['task']['id']==custom_id
                assert request.value.post_data_json['task']['python']['min']=='3.14'
                page.wait_for_function('()=>!!localState.selected?.report&&!localState.running',timeout=120000)
                assert page.evaluate('state.task.id')==custom_id and page.evaluate('state.course')==custom_code
                assert page.evaluate('state.before.task_id')==custom_id
                checks.append('Imported custom Python requirements and course identity survive the preparation-page one-click check.')

                page.set_viewport_size(dict(width=768, height=900))
                page.wait_for_selector('#learning-chat', state='hidden')
                checks.append('Shrinking desktop to tablet automatically collapses the chat, leaving course controls reachable.')
                page.set_viewport_size(dict(width=390, height=700));page.click('#chat-toggle')
                page.fill('#chat-input', '小屏发送预览');page.click('#chat-preview-button')
                page.wait_for_selector('#chat-preview-panel:visible')
                if page.locator('#chat-preview-panel > details').get_attribute('open') is None:
                    page.locator('#chat-preview-panel > details > summary').click()
                page.locator('#chat-send').scroll_into_view_if_needed()
                panel=page.locator('#learning-chat').bounding_box();send_box=page.locator('#chat-send').bounding_box();close_box=page.locator('#chat-close').bounding_box()
                assert send_box['y']>=panel['y'] and send_box['y']+send_box['height']<=panel['y']+panel['height']
                assert close_box['y']>=panel['y'] and close_box['y']+close_box['height']<=panel['y']+panel['height']
                page.screenshot(path=OUT / '06-chat-mobile-preview.png')
                page.click('#chat-close');assert not page.locator('#learning-chat').is_visible()
                checks.append('390x700 chat preview can scroll to confirmation while keeping the close control visible.')
                for width in [320, 390, 768, 1120, 1280, 1440]:
                    page.set_viewport_size(dict(width=width, height=900))
                    page.click('#chat-close') if page.locator('#chat-close').is_visible() else None
                    page.click('#home-nav')
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), f'home overflow {width}'
                    page.click('#chat-toggle')
                    assert page.locator('#chat-input').is_visible()
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), f'chat overflow {width}'
                    page.keyboard.press('Escape')
                    assert not page.locator('#learning-chat').is_visible()
                    assert page.evaluate('document.activeElement.id') == 'chat-toggle'
                    page.click('.course-card[data-scenario="node-basics"]')
                    page.wait_for_function('()=>state.task?.scenario==="node-basics"&&guided.courseStep===1')
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), f'course overflow {width}'
                    if width == 390:
                        page.click('#home-nav');page.screenshot(path=OUT / '05-home-mobile.png', full_page=True)
                checks.append('320/390/768/1120/1280/1440 home, course and chat layouts reflow without horizontal overflow; Escape returns focus to launcher.')

                assert not errors, errors
                assert not external, external
                result['passed'] = True
    except Exception as error:
        result.update(passed=False, error=repr(error))
        raise
    finally:
        (OUT / 'acceptance.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
        print(json.dumps(dict(output=str(OUT), **result), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
