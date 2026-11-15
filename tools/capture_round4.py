"""Compare runnable pages at matching viewports; never run an extension tool."""
import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
import json
from pathlib import Path
import threading
from playwright.sync_api import sync_playwright
import campuslab.web as web

ROOT = Path(__file__).resolve().parents[1]


def main(stage, source, result_only=False):
    out = ROOT / 'records/round4' / stage
    out.mkdir(parents=True, exist_ok=True)
    web.ROOT = Path(source) if source else ROOT
    result = dict(stage=stage, source=str(web.ROOT), time=datetime.now(timezone.utc).isoformat(), shots=[], errors=[])
    with ExitStack() as stack:
        server = web.AppServer(0, ROOT/'data/temp'/('round4-capture-'+stage+'.sqlite'))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        stack.callback(server.server_close)
        stack.callback(server.shutdown)
        with sync_playwright() as p:
            browser = p.chromium.launch(channel='msedge', headless=True)
            page = browser.new_page(reduced_motion='reduce')
            page.on('pageerror', lambda error: result['errors'].append(str(error)))
            page.goto('http://127.0.0.1:'+str(server.server_port))
            page.wait_for_function('()=>!!state.config&&!!practiceState.practice')

            def shots(name):
                for width, height in [(1912, 948), (1366, 768), (390, 844)]:
                    page.set_viewport_size(dict(width=width, height=height))
                    page.wait_for_timeout(150)
                    if name=='ai' and not page.locator('#learning-chat').is_visible():
                        page.click('#chat-toggle')
                    page.evaluate('window.scrollTo(0,0)')
                    file = name+'-'+str(width)+'.png'
                    page.screenshot(path=out/file)
                    result['shots'].append(dict(page=name, width=width, file=file, overflow=page.evaluate('document.documentElement.scrollWidth>innerWidth')))
                page.set_viewport_size(dict(width=1912, height=948))

            if result_only:
                page.click('#welcome-start');page.click('[data-scenario="python-basics"]')
                page.wait_for_function('()=>state.task?.scenario==="python-basics"&&guided.courseStep===1')
                page.click('#start-python');page.wait_for_function('()=>!!state.before&&!localState.running',timeout=90000)
                shots('python-result')
                (out/'capture.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
                print(json.dumps(dict(stage=stage,shots=len(result['shots']),errors=result['errors']),ensure_ascii=False))
                browser.close();return
            shots('welcome')
            page.click('#welcome-start')
            shots('selection')
            for scenario in ['dsh-desktop', 'dsh-cli', 'deepseek-api', 'ai-web-deepseek', 'local-qwen']:
                if stage=='before':
                    page.click('#home-nav')
                    page.click('[data-scenario="'+scenario+'"]')
                    page.wait_for_function('()=>guided.courseStep===1')
                else:
                    page.click('#extensions-nav')
                    page.locator('[data-extension="'+scenario+'"]').first.click()
                    page.wait_for_function('(s)=>guided.route==="extensions"&&KehangExtensions.current()===s', arg=scenario)
                shots(scenario)
            if stage!='before':
                page.click('#extensions-nav');page.wait_for_selector('#extension-list:visible');shots('extensions')
                page.locator('[data-extension="kehang-ai"]').click();page.wait_for_selector('#extension-guide:visible');shots('kehang-ai')
            page.click('#home-nav')
            page.click('[data-scenario="python-basics"]')
            page.wait_for_function('()=>guided.courseStep===1')
            shots('python-prepare')
            page.click('#home-nav')
            page.click('#start-practice')
            shots('practice')
            page.click('#teacher-nav')
            page.locator('#teacher-course-panel>summary').click()
            shots('teacher')
            page.click('#home-link')
            page.click('#chat-toggle')
            shots('ai')
            browser.close()
    (out/'capture.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps(dict(stage=stage, shots=len(result['shots']), errors=result['errors']), ensure_ascii=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('stage')
    parser.add_argument('--source')
    parser.add_argument('--result-only',action='store_true')
    args=parser.parse_args()
    main(args.stage, args.source, args.result_only)
