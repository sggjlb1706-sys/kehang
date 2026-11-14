"""Real browser/native picker/SQLite collector; only our owned dialog is automated."""
from contextlib import ExitStack
from datetime import datetime,timezone
import json
from pathlib import Path
import threading
from playwright.sync_api import sync_playwright
from campuslab.web import AppServer
from campuslab.sqlite_course import prepare_demo
from campuslab.rules import compare
from tools.verify_round2 import native_control

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'records/round2/native'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')


def main():
    OUT.mkdir(parents=True)
    database=OUT/'中文 教学数据库.sqlite';prepare_demo(database)
    result=dict(scope='Real owned native Windows file dialog, browser and fixed read-only SQLite collector. Agent automation of explicit test choices; not human acceptance.')
    try:
        with ExitStack() as stack:
            server=AppServer(0,OUT/'courses.sqlite');threading.Thread(target=server.serve_forever,daemon=True).start()
            stack.callback(server.server_close);stack.callback(server.shutdown)
            with sync_playwright() as p:
                browser=p.chromium.launch(channel='msedge',headless=True)
                page=browser.new_page(viewport=dict(width=1440,height=1000))
                page.goto('http://127.0.0.1:'+str(server.server_port));page.wait_for_function('()=>!!state.config')
                page.click('#welcome-start');page.click('[data-scenario="sqlite-basics"]');page.wait_for_function('()=>guided.courseStep===1');page.click('#guide-next')
                page.wait_for_selector('#local-field-target')
                button=page.locator('#local-target-fields button').first
                with native_control():
                    button.click();page.wait_for_function('()=>document.querySelector("#local-target-status").textContent.includes("已取消")',timeout=40000)
                assert not server.local_check.jobs and not page.locator('#local-field-target').input_value()
                with native_control(database):
                    button.click();page.wait_for_function('()=>document.querySelector("#local-target-status").textContent.includes("已选择")',timeout=40000)
                assert not server.local_check.jobs
                page.screenshot(path=OUT/'selected-native-target.png',full_page=True)
                page.click('#local-start');page.wait_for_function('()=>!!state.before&&!localState.running',timeout=30000)
                a=page.evaluate('state.before');page.click('#local-recheck');page.wait_for_function('()=>!!state.after&&!localState.running',timeout=30000)
                b=page.evaluate('state.after');comparison=compare(page.evaluate('state.task'),a,b)
                assert comparison['outcome']=='stable-pass'
                page.locator('#local-environment-details>summary').click()
                for selector,name in [('#local-save','B-download.json'),('#local-save-before','A-download.json')]:
                    with page.expect_download() as download:page.click(selector)
                    download.value.save_as(OUT/name)
                assert json.loads((OUT/'A-download.json').read_bytes())==a
                assert json.loads((OUT/'B-download.json').read_bytes())==b
                page.screenshot(path=OUT/'native-sqlite-result.png',full_page=True)
                for name,value in [('A.json',a),('B.json',b),('comparison.json',comparison)]:
                    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf8')
                result.update(passed=True,cancel_no_job=True,selection_no_job=True,unicode_space_path=True,comparison='stable-pass',download_originals_match=True)
                browser.close()
    except Exception as error:result.update(passed=False,error=repr(error));raise
    finally:
        (OUT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
