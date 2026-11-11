"""Exercise the delivered classroom UI in two fresh databases and capture its actual views."""
from contextlib import ExitStack
from pathlib import Path
import base64,json,threading,tempfile,zipfile
from playwright.sync_api import sync_playwright
from campuslab.web import AppServer
from campuslab.rules import task,compare
from campuslab.practice import check
ROOT=Path(__file__).resolve().parents[1]
REC=ROOT/'records/practice'
LAB=REC/'lab-run'
SCREENS=REC/'screens'

def main():
    SCREENS.mkdir(exist_ok=True)
    assertions=[];errors=[];remote=[];sessions=[]
    def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
    def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf8')
    def screen(page,name,anchor=None):
        if anchor:page.locator(anchor).evaluate("e=>e.scrollIntoView({block:'start'})")
        page.screenshot(path=str(SCREENS/(name+'.png')),animations='disabled')
    def download(page,selector,path):
        with page.expect_download() as event:page.locator(selector).click()
        event.value.save_as(path)
    def show(page,selector):
        page.locator(selector).evaluate("e=>{for(let p=e;p;p=p.parentElement)if(p.tagName==='DETAILS')p.open=true}")
    with tempfile.TemporaryDirectory(prefix='kehang-lab-ui-') as folder, ExitStack() as stack:
        d=Path(folder)
        for i in range(2):
            srv=AppServer(0,d/str(i)/'courses.sqlite',ROOT/'vendor/python-3.13.17-embed-amd64.zip')
            threading.Thread(target=srv.serve_forever,daemon=True).start()
            stack.callback(srv.server_close);stack.callback(srv.shutdown)
            sessions.append('http://127.0.0.1:'+str(srv.server_port))
        with sync_playwright() as p:
            browser=p.chromium.launch(channel='msedge',headless=True,slow_mo=100)
            ctx=browser.new_context(viewport={'width':1360,'height':840},accept_downloads=True)
            ctx.on('request',lambda req:remote.append(req.url) if req.url.startswith(('http://','https://')) and not any(req.url.startswith(s+'/') for s in sessions) else None)
            teacher,student=ctx.new_page(),ctx.new_page()
            # Record only the two isolated application tabs. Keep raw frames in the
            # ignored run directory; the edit uses reviewed, identified frames.
            for label,pg in [('teacher',teacher),('student',student)]:
                capture=ROOT/'records/runtime/practice-recording'/label
                capture.mkdir(parents=True,exist_ok=True)
                cdp=ctx.new_cdp_session(pg)
                def frame(event,cdp=cdp,capture=capture):
                    ts=event['metadata'].get('timestamp',0)
                    (capture/f'{ts:.6f}.jpg').write_bytes(base64.b64decode(event['data']))
                    cdp.send('Page.screencastFrameAck',{'sessionId':event['sessionId']})
                cdp.on('Page.screencastFrame',frame)
                cdp.send('Page.startScreencast',{'format':'jpeg','quality':86,'everyNthFrame':1})
            for page,base in zip((teacher,student),sessions):
                page.on('pageerror',lambda e:errors.append(str(e)))
                page.goto(base);page.wait_for_function('()=>!!practiceState.practice && !!state.config')
            screen(teacher,'practice','#practice-panel')
            show(teacher,'#practice-publish');teacher.click('#practice-publish')
            teacher.wait_for_function('()=>!!practiceState.courses')
            screen(teacher,'published','#practice-publish')
            portable=d/'practice-course.json'
            download(teacher,'#practice-export-package',portable)
            download(teacher,'#practice-materials',d/'materials.zip')
            with zipfile.ZipFile(d/'materials.zip') as z:assert z.testzip() is None and json.loads(z.read('课堂资料包.json'))==read(portable)
            student.set_input_files('#practice-package',portable)
            student.wait_for_function('()=>!!practiceState.courses')
            assert teacher.evaluate('practiceState.practice.id')==student.evaluate('practiceState.practice.id')
            assertions.append('teacher exported fixed package + actual materials, student imported in distinct local DB')
            student.locator('#practice-package').evaluate("e=>e.closest('details').open=false")
            show(student,'#practice-read');student.check('#practice-read')
            screen(student,'steps','#practice-instructions')
            student.locator('#practice-read').evaluate("e=>e.closest('details').open=false")
            correct=read(LAB/'实训成果.json')
            wrong={**correct,'notebook':{**correct['notebook'],'array_sum':41}}
            write(d/'测试负例_总和41.json',wrong)
            for file,status in [(d/'测试负例_总和41.json','mismatch'),(LAB/'实训成果.json','pass')]:
                student.set_input_files('#practice-submission',file);student.click('#practice-check')
                student.wait_for_function('(s)=>practiceState.attempts.at(-1)?.result.status===s',arg=status)
                screen(student,'wrong' if status=='mismatch' else 'accepted','.practice-submission')
            assert len(student.evaluate('practiceState.attempts'))==2
            assertions.append('agent-constructed 41 rejected, actual completed notebook + SELECT accepted; both attempts retained')
            for key,scenario in [('notebook','notebook-data'),('sqlite','sqlite-basics')]:
                student.click('#practice-'+key)
                student.wait_for_function('(s)=>state.task?.scenario===s',arg=scenario)
                a,b=[LAB/(scenario+'-'+v+'.json') for v in ('A','B')]
                student.set_input_files('#report-files',[str(b),str(a)])
                student.wait_for_function('()=>!!state.after && state.analysis?.passed')
                assert student.evaluate('state.before.collected_at')==read(a)['collected_at']
                assert compare(task(scenario),read(a),read(b))['outcome']=='stable-pass'
                invariant=student.evaluate('JSON.stringify(state.analysis)')
                for mode in ('quick','novice','standard'):
                    student.select_option('#mode',mode)
                    assert student.evaluate('JSON.stringify(state.analysis)')==invariant
                assertions.append(scenario+' real A/B in reverse selection order, same identity/time, 3 modes agree')
            student.locator('#practice-attempts-panel').evaluate('e=>e.open=true')
            screen(student,'result','#practice-panel')
            download(student,'#practice-completion',REC/'completion-local.json')
            complete=read(REC/'completion-local.json')
            assert complete['reading_self_declared'] and set(complete['environment'])=={'notebook','sqlite'}
            assert [a['result']['status'] for a in complete['attempts']]==['mismatch','pass']
            assert all(check(complete['practice'],attempt['submission'])['status']==attempt['result']['status'] for attempt in complete['attempts'])
            assertions.append('exported completion independently recalculated for each attempt; both environments retained')
            student.set_viewport_size(dict(width=390,height=844))
            screen(student,'mobile','#practice-panel');assert student.evaluate('document.documentElement.scrollWidth<=innerWidth')
            assertions.append('390px reading, no horizontal overflow')
            student.select_option('#goal','python-basics');student.locator('#goal-form button').click()
            student.wait_for_function("()=>state.task?.scenario==='python-basics'")
            a,b=[LAB/('python-basics-'+s+'.json') for s in ('A','B')]
            student.set_input_files('#report-files',[str(b),str(a)])
            student.wait_for_function('()=>!!state.after && state.analysis?.passed')
            missing=d/'earlier-name.json';write(missing,read(b))
            student.set_input_files('#report-files',[str(b),str(missing)])
            student.wait_for_function('()=>!state.analysis && !state.after')
            share=d/'share.json';write(share,dict(share_only=True,report=read(a)))
            student.set_input_files('#report-files',[str(share),str(b)])
            student.wait_for_function('()=>!state.analysis && !state.before')
            assertions.append('Python real launcher pair; equal timestamps and share-only report rejected')
            assert not errors and not remote,(errors,remote)
            browser.close()
    write(REC/'e2e.json',dict(passed=True,assertions=assertions,origins=sessions,page_errors=errors,external_requests=remote,scope='Agent-operated, two local databases on the same Windows computer.'))
    print(json.dumps(assertions,ensure_ascii=False))

if __name__=='__main__':main()
