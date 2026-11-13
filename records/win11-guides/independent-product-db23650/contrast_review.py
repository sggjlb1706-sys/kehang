"""Measure computed sRGB contrast in the new illustration areas, excluding decorative icons and disabled controls."""
from contextlib import ExitStack
import json
from pathlib import Path
import sys
import tempfile
import threading

EVIDENCE=Path(__file__).resolve().parent
ROOT=EVIDENCE/'snapshot'
sys.path.insert(0,str(ROOT))
from campuslab.web import AppServer
from playwright.sync_api import sync_playwright

COURSES=['python-basics','node-basics','notebook-data','java-jdk','sqlite-basics','pytorch-cpu','pytorch-gpu','local-qwen','vm-linux','ai-web-deepseek','deepseek-api','dsh-desktop','dsh-cli']
MEASURE=r'''(host)=>{
  const canvas=document.createElement('canvas');canvas.width=canvas.height=1;
  const context=canvas.getContext('2d',{willReadFrequently:true});
  const color=css=>{context.clearRect(0,0,1,1);context.fillStyle=css;context.fillRect(0,0,1,1);return Array.from(context.getImageData(0,0,1,1).data).map((v,i)=>i===3?v/255:v);};
  const over=(fg,bg)=>[0,1,2].map(i=>fg[i]*fg[3]+bg[i]*(1-fg[3])).concat([1]);
  const luminance=rgba=>rgba.slice(0,3).map(v=>v/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4).reduce((a,v,i)=>a+v*[.2126,.7152,.0722][i],0);
  const values=[];
  for(const node of host.querySelectorAll('*')){
    if(!Array.from(node.childNodes).some(n=>n.nodeType===3&&n.textContent.trim()))continue;
    if(node.closest('[aria-hidden="true"],button:disabled,[hidden]'))continue;
    const style=getComputedStyle(node),rect=node.getBoundingClientRect();
    if(!rect.width||!rect.height||style.visibility!=='visible')continue;
    let bg=[255,255,255,1],ancestors=[];
    for(let current=node;current;current=current.parentElement)ancestors.unshift(current);
    for(const current of ancestors)bg=over(color(getComputedStyle(current).backgroundColor),bg);
    const fg=over(color(style.color),bg),a=luminance(fg),b=luminance(bg),ratio=(Math.max(a,b)+.05)/(Math.min(a,b)+.05);
    const large=parseFloat(style.fontSize)>=24||(parseFloat(style.fontSize)>=18.66&&parseInt(style.fontWeight)>=700),threshold=large?3:4.5;
    values.push({class:node.className,text:node.textContent.trim().slice(0,80),ratio:+ratio.toFixed(3),threshold,color:style.color,background:bg.slice(0,3)});
  }
  return values;
}'''
results=[]
with tempfile.TemporaryDirectory(prefix='kehang-independent-contrast-') as folder,ExitStack() as stack:
    server=AppServer(0,Path(folder)/'courses.sqlite',ROOT/'vendor/python-3.13.17-embed-amd64.zip')
    threading.Thread(target=server.serve_forever,daemon=True).start();stack.callback(server.server_close);stack.callback(server.shutdown)
    with sync_playwright() as p,ExitStack() as browsers:
        browser=p.chromium.launch(channel='msedge',headless=True);browsers.callback(browser.close)
        page=browser.new_page(viewport=dict(width=1440,height=1100))
        page.goto('http://127.0.0.1:'+str(server.server_port));page.wait_for_function('()=>!!state.config&&!!practiceState.practice')
        for scenario in COURSES:
            page.click('#home-nav');page.click('#choose-course');page.select_option('#goal',scenario);page.locator('#goal-form button').click()
            page.wait_for_function('(s)=>state.task?.scenario===s&&guided.courseStep===1',arg=scenario);page.click('#guide-next')
            if page.locator('#manual-collection > summary').is_visible() and page.locator('#manual-collection').get_attribute('open') is None:page.locator('#manual-collection > summary').click()
            for index,button in enumerate(page.locator('#course-visual-guide .visual-step-button').all()):
                button.click()
                values=page.locator('#course-visual-guide').evaluate(MEASURE)
                results.extend(dict(course=scenario,step=index+1,**v) for v in values)
        page.locator('#report-extension-help summary').click()
        for selector in ['#report-explorer-window','#report-extension-window']:
            results.extend(dict(area=selector,**v) for v in page.locator(selector).evaluate(MEASURE))
        page.click('#home-nav');page.click('#start-practice');page.click('#guide-next');page.click('#guide-next')
        for button in page.locator('#practice-visual-guide .visual-step-button').all():
            button.click();results.extend(dict(area='practice-work',**v) for v in page.locator('#practice-visual-guide').evaluate(MEASURE))
        page.click('#guide-next');results.extend(dict(area='practice-submit',**v) for v in page.locator('#practice-submit-guide').evaluate(MEASURE))
failures=[r for r in results if r['ratio']<r['threshold']]
result=dict(passed=not failures,text_samples=len(results),minimum_ratio=min(r['ratio'] for r in results),failures=failures,
            lowest_samples=sorted(results,key=lambda r:r['ratio'])[:20],
            scope='Computed Chromium CSS text/background contrast in new guides at default 1440 viewport; decorative aria-hidden icons and disabled controls excluded. This is not a full WCAG or assistive-technology certification.')
(EVIDENCE/'contrast-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(dict(passed=result['passed'],text_samples=len(results),minimum_ratio=result['minimum_ratio'],failures=len(failures)),ensure_ascii=False))
assert not failures,failures
