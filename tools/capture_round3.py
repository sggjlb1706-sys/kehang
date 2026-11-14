"""One screenshot batch across existing routes; record baseline/final source separately."""
import argparse
from contextlib import ExitStack
from datetime import datetime,timezone
import json
from pathlib import Path
import subprocess
import threading
from playwright.sync_api import sync_playwright
from campuslab.web import AppServer

ROOT=Path(__file__).resolve().parents[1]


def main(stage):
    out=ROOT/'records/round3'/stage;out.mkdir(parents=True,exist_ok=True)
    result=dict(stage=stage,time=datetime.now(timezone.utc).isoformat(),head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),shots=[],errors=[])
    try:
        with ExitStack() as stack:
            server=AppServer(0,ROOT/'data'/('round3-'+stage+'.sqlite'),ROOT/'vendor/python-3.13.17-embed-amd64.zip')
            threading.Thread(target=server.serve_forever,daemon=True).start();stack.callback(server.server_close);stack.callback(server.shutdown)
            with sync_playwright() as p:
                browser=p.chromium.launch(channel='msedge',headless=True)
                page=browser.new_page(viewport=dict(width=1912,height=948),reduced_motion='reduce')
                page.on('pageerror',lambda error:result['errors'].append(str(error)))
                page.goto('http://127.0.0.1:'+str(server.server_port));page.wait_for_function('()=>!!state.config&&!!practiceState.practice')
                def shots(name):
                    for width,height in [(1912,948),(1366,768),(390,844)]:
                        page.set_viewport_size(dict(width=width,height=height));page.wait_for_timeout(200)
                        page.evaluate('window.scrollTo(0,0)')
                        file=name+'-'+str(width)+'.png';page.screenshot(path=out/file)
                        result['shots'].append(dict(page=name,width=width,height=height,file=file,overflow=page.evaluate('document.documentElement.scrollWidth>innerWidth')))
                    page.set_viewport_size(dict(width=1912,height=948));page.wait_for_timeout(100)
                shots('welcome')
                page.click('#welcome-start');shots('selection')
                for scenario in ['deepseek-api','dsh-desktop','dsh-cli']:
                    page.click('#home-nav');page.click('[data-scenario="'+scenario+'"]');page.wait_for_function('()=>guided.courseStep===1')
                    shots(scenario+'-prepare');page.click('#guide-next');shots(scenario+'-check')
                page.click('#home-nav');page.click('[data-scenario="python-basics"]');page.wait_for_function('()=>guided.courseStep===1')
                page.click('#start-python');page.wait_for_function('()=>!!state.before&&!localState.running',timeout=90000)
                (out/'real-python-A.json').write_text(json.dumps(page.evaluate('state.before'),ensure_ascii=False,indent=2),encoding='utf8')
                shots('python-result')
                page.click('#home-nav');page.click('#start-practice');shots('practice')
                page.click('#guide-next');shots('practice-prepare')
                page.click('#teacher-nav');page.locator('#teacher-course-panel>summary').click();shots('teacher')
                page.click('#home-link');page.click('#chat-toggle');shots('welcome-ai')
                result['passed']=not result['errors'];browser.close()
    finally:
        (out/'capture.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
        print(json.dumps(dict(stage=stage,shots=len(result['shots']),errors=result['errors'],path=str(out)),ensure_ascii=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage');main(parser.parse_args().stage)
