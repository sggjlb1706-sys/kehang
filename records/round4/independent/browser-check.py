import json, threading, subprocess, sys, hashlib
from pathlib import Path
from contextlib import ExitStack
from playwright.sync_api import sync_playwright
ROOT=Path.cwd();sys.path.insert(0,str(ROOT))
from campuslab.web import AppServer
from campuslab.rules import task
from campuslab.portable import export_package
from campuslab.extensions import BY_ID,COURSES,LEGACY
OUT=ROOT/'records/round4/independent'
result={'head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'checks':[],'errors':[],'external':[],'shots':[]}
def check(name):result['checks'].append(name);print('PASS',name,flush=True)
def save(name,value):(OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf8')
try:
 with ExitStack() as stack:
  server=AppServer(0,OUT/'review.sqlite')
  threading.Thread(target=server.serve_forever,daemon=True).start();stack.callback(server.server_close);stack.callback(server.shutdown)
  origin='http://127.0.0.1:'+str(server.server_port)
  with sync_playwright() as p:
   browser=p.chromium.launch(channel='msedge',headless=True)
   page=browser.new_page(viewport={'width':1366,'height':768},reduced_motion='reduce')
   page.on('pageerror',lambda e:result['errors'].append(str(e)))
   page.on('request',lambda r:result['external'].append(r.url) if not r.url.startswith(origin+'/') else None)
   requests=[];page.on('request',lambda r:requests.append(r.url))
   def wait():page.wait_for_function('()=>!!state.config&&!!practiceState.practice')
   page.goto(origin);wait();page.click('#welcome-start')
   assert page.locator('#course-grid button').count()==8
   assert set(page.locator('#teacher-goal option').evaluate_all('(xs)=>xs.map(x=>x.value)'))==set(COURSES)
   for value,count in [('coding',3),('data',2),('ai',2),('system',1),('all',8)]:
    page.click('[data-filter="'+value+'"]');assert page.locator('#course-grid button:visible').count()==count
   check('8 real course cards/teacher choices and 5 category filters correct')
   page.click('#extensions-nav');page.wait_for_selector('#extension-list:visible');first=len(requests)
   for tool in BY_ID:
    page.locator('[data-extension="'+tool+'"]').click();page.wait_for_selector('#extension-guide:visible')
    assert page.evaluate('KehangExtensions.current()')==tool
    text=page.locator('#extension-guide').inner_text()
    assert '2026-11-15' in text
    for word in ['初检','复检','sum=42','report-A.json','input.csv','选择目标并检测']:
     assert word not in text,(tool,word)
    for w,h in [(1912,948),(1366,768),(390,844)]:
     page.set_viewport_size({'width':w,'height':h});page.wait_for_timeout(40)
     assert not page.evaluate('document.documentElement.scrollWidth>innerWidth'),(tool,w)
     page.locator('.extension-content nav a').last.click();page.keyboard.press('Tab')
     assert page.locator('.extension-content section').last.is_visible()
     page.evaluate('scrollTo(0,0)');name=tool+'-'+str(w)+'.png';page.screenshot(path=OUT/name);result['shots'].append(name)
    page.click('#extension-back');page.wait_for_selector('#extension-list:visible')
   assert not any(any(q in u for q in ['/api/plan','/api/analyze','/api/local-check','/api/tool?','/api/compare']) for u in requests[first:])
   assert not server.local_check.jobs
   check('6 tool guides/anchors/3 viewports readable without course/check/report requests; 18 fresh screenshots')
   for tool in LEGACY:
    published=server.store.publish(task(tool))
    page.goto(origin+'/?course='+published['code']);page.wait_for_function('(x)=>guided.route==="extensions"&&KehangExtensions.current()===x',arg=tool)
    page.wait_for_selector('#extension-guide:visible');assert page.evaluate('state.task') is None
   check('All 5 legacy course-code URLs redirect to corresponding guide without a course task')
   page.goto(origin);wait()
   held=[]
   page.route('**/api/extensions',lambda r:held.append(r))
   page.click('#extensions-nav');page.wait_for_timeout(50);assert held
   page.click('#home-nav');held.pop().continue_();page.wait_for_timeout(100)
   assert page.locator('#selection-screen').is_visible() and not page.locator('#extensions-screen').is_visible()
   page.unroute('**/api/extensions')
   check('Late initial guide load cannot take navigation back from course selection')
   page.reload();wait();held=[];page.route('**/api/goal?goal=java-jdk',lambda r:held.append(r))
   page.click('#welcome-start');page.click('[data-scenario="java-jdk"]');page.wait_for_timeout(50);assert held
   page.click('#extensions-nav');page.wait_for_selector('#extension-list:visible');held.pop().continue_();page.wait_for_timeout(100)
   assert page.locator('#extensions-screen').is_visible() and page.evaluate('state.task') is None
   page.unroute('**/api/goal?goal=java-jdk')
   check('Late course load cannot overwrite the new tools route or create stale course task')
   for tool in ['deepseek-api','kehang-ai','deepseek-api']:
    if page.locator('#learning-chat').is_visible():page.keyboard.press('Escape')
    if page.locator('#extension-back').is_visible():page.click('#extension-back')
    page.locator('[data-extension="'+tool+'"]').click();page.wait_for_selector('#extension-guide:visible')
    if not page.locator('#learning-chat').is_visible():page.click('#chat-toggle')
    expected='' if tool=='kehang-ai' or not result.get('draft') else 'API scope draft'
    assert page.locator('#chat-input').input_value()==expected
    if tool=='deepseek-api' and not result.get('draft'):
     page.fill('#chat-input','API scope draft');result['draft']=True
    page.click('#chat-preview-button') if page.locator('#chat-input').input_value() else None
    if page.locator('#chat-input').input_value():
     page.wait_for_selector('#chat-preview-panel:visible')
     value=list(server.chat.pending.values())[-1]['preview']['context']
     assert value['extension']['id']==tool and 'course' not in value and 'evidence' not in value
     assert page.locator('#chat-send').is_disabled()
   check('Tool chat drafts are isolated/restored; unconfigured previews carry tool guide only and cannot send')
   if page.locator('#learning-chat').is_visible():page.keyboard.press('Escape')
   for scenario in COURSES:
    page.click('#home-nav');page.click('[data-scenario="'+scenario+'"]');page.wait_for_function('(s)=>state.task?.scenario===s&&guided.courseStep===1',arg=scenario)
    assert page.locator('#preparation').is_visible() and not page.locator('#extensions-screen').is_visible()
   check('All 8 real course preparation paths remain reachable independently')
   assert not result['errors'] and not result['external'],result
   result['passed']=True;browser.close()
except Exception as e:
 result.update(passed=False,error=repr(e));raise
finally:
 save('browser-result.json',result)
 print(json.dumps({'passed':result.get('passed'),'checks':len(result['checks']),'errors':result['errors'],'external':result['external']},ensure_ascii=False))
