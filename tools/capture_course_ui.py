"""Capture readable viewports of actual evidence; no synthetic success states."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import threading
from playwright.sync_api import sync_playwright
from campuslab.web import AppServer


def main():
    root=Path(__file__).resolve().parents[1]
    evidence=root/'records/browser/20261108T101444960811Z-courses'
    out=root/'records/courses/ui';out.mkdir(exist_ok=False)
    server=AppServer(0,root/'records/runtime/ui-capture.sqlite')
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(channel='msedge',headless=True)
            page=browser.new_page(viewport={'width':1440,'height':1000})
            page.goto(f'http://127.0.0.1:{server.server_port}')
            page.screenshot(path=str(out/'entry-desktop.png'))
            page.select_option('#goal','pytorch-gpu');page.locator('#goal-form button').click()
            page.wait_for_function("()=>state.task?.scenario==='pytorch-gpu'")
            page.set_input_files('#before-file',str(evidence/'gpu-A.json'));page.wait_for_selector('#results .state-unknown')
            page.set_input_files('#after-file',str(evidence/'gpu-B.json'));page.wait_for_function('()=>state.analysis?.passed===true')
            page.select_option('#mode','quick');page.wait_for_function('()=>document.querySelectorAll("#guidance li").length===2')
            page.evaluate('window.scrollTo(0,0)');page.screenshot(path=str(out/'gpu-desktop.png'))
            page.locator('#results').evaluate('(e)=>e.scrollIntoView({block:"start"})');page.screenshot(path=str(out/'gpu-results-desktop.png'))
            page.set_viewport_size({'width':390,'height':844});page.locator('#task-panel').evaluate('(e)=>e.scrollIntoView({block:"start"})')
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            page.screenshot(path=str(out/'gpu-mobile.png'))
            page.locator('#results').evaluate('(e)=>e.scrollIntoView({block:"start"})');page.screenshot(path=str(out/'gpu-results-mobile.png'))
            page.set_viewport_size({'width':1440,'height':1000});page.select_option('#goal','vm-linux');page.locator('#goal-form button').click()
            page.wait_for_function("()=>state.task?.scenario==='vm-linux'")
            page.set_input_files('#before-file',str(evidence/'vm-A.json'));page.wait_for_selector('#results .state-unknown')
            page.evaluate('window.scrollTo(0,0)');page.screenshot(path=str(out/'vm-desktop.png'))
            page.locator('#results').evaluate('(e)=>e.scrollIntoView({block:"start"})');page.screenshot(path=str(out/'vm-unknown-results.png'))
            browser.close()
        (out/'evidence.json').write_text(json.dumps(dict(captured_at=datetime.now(timezone.utc).isoformat(),evidence=str(evidence.relative_to(root)),
            physical_phone=False,source_sha256={str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest().upper() for folder in ('web','campuslab') for f in (root/folder).glob('*') if f.is_file()}),ensure_ascii=False,indent=2),encoding='utf-8')
    finally:
        server.shutdown();server.server_close();thread.join()


if __name__=='__main__':main()
