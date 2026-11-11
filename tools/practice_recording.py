"""Capture real product actions and a clearly labelled reader of archived visible messages.

No AI call, original session read, desktop capture, or historical response generation.
"""
from copy import deepcopy
from datetime import datetime,timezone
import hashlib
from html import escape
import json
from pathlib import Path
import subprocess
import tempfile
import threading

from playwright.sync_api import sync_playwright
from campuslab.web import AppServer


ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'records/practice/film-shots'
PROMPT=ROOT/'records/brand/prompts/01a1be86-7c96-7200-860a-ff272f5c3bb1.json'
GROUPS={'08':[17,29],'09':[338,470],'10':[565,810,815],'11':[890,970],'12':[1063],'13':[1402,1456,1463,1466]}


def make_reader():
    data=json.loads(PROMPT.read_text(encoding='utf-8'))
    messages={m['source_line']:m for m in data['messages']}
    diff=subprocess.check_output(['git','-c','safe.directory='+ROOT.as_posix(),'show','--format=commit %H%nDate %aI%nSubject %s','2c5ade2','--','campuslab/ai_probe.py','campuslab/java_course.py','tests/test_ai_course.py','tests/test_java_course.py'],cwd=ROOT,text=True,encoding='utf-8')
    pages={}
    for chapter,lines in GROUPS.items():
        articles=[]
        for line in lines:
            m=messages[line]
            role='用户原文' if m['role']=='user' else 'AI助手原文'
            articles.append('<details id="line-'+str(line)+'"><summary>'+role+' · 源行 '+str(line)+' · '+escape(m['timestamp'])+'</summary><p class="quote">'+escape(m['text'].split('<oai-mem-citation>')[0].rstrip())+'</p><p class="source">节选，原消息摘要 '+escape(m['original_text_sha256'])+'</p></details>')
        if chapter=='12':articles.append('<details id="git-diff"><summary>打开真实提交 2c5ade2 的代码与回归差异</summary><pre>'+escape(diff)+'</pre></details>')
        body=''.join(articles)
        html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>课航 · 历史AI协作回顾</title><style>
body{margin:0;padding:44px 88px;background:#fff;color:#1f2927;font:25px/1.7 "Microsoft YaHei",system-ui,sans-serif}header{font-size:22px;color:#76503f;border-bottom:1px solid #d9ddda;padding-bottom:20px}h1{font-size:38px;margin:18px 0 10px}p{max-width:1250px}details{padding:24px 0;border-top:1px solid #c9d1cd}summary{font-weight:bold;cursor:pointer;font-size:27px}.quote{white-space:pre-wrap;margin:22px 0}.source{font-size:17px;color:#465750;word-break:break-all}pre{font:19px/1.7 Consolas,monospace;white-space:pre-wrap;padding:22px;background:#f3f5f4}footer{font-size:20px;color:#465750;margin-top:30px}
</style><header>课航 · 历史AI协作回顾 · 已脱敏可见原文</header><h1>从用户意图，到实现与纠偏</h1><p>本页是本轮录制用的只读资料阅读页；回顾既有真实消息，不冒充现场生成，也不认证三条完整Prompt链。</p>'''+body+'''<footer>来源：records/brand/prompts/01a1be86-7c96-7200-860a-ff272f5c3bb1.json。源行号来自归档索引；未读取完整原会话、凭据或隐藏内容。独立审查发现保持审查者身份。</footer></html>'''
        target=OUT/'reader'/('chapter-'+chapter+'.html');target.parent.mkdir(parents=True,exist_ok=True);target.write_text(html,encoding='utf-8');pages[chapter]=target
    return pages


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    if (OUT/'index.json').exists():raise SystemExit('Existing recording index; choose a new output directory instead of overwriting evidence')
    started=datetime.now(timezone.utc).isoformat();shots=[];errors=[];external=[]
    pages=make_reader()
    def capture(page,chapter,action,source=None):
        folder=OUT/chapter;folder.mkdir(exist_ok=True)
        number=len([s for s in shots if s['chapter']==chapter])+1
        path=folder/f'{number:02d}.jpg';page.screenshot(path=str(path),type='jpeg',quality=94,mask=[page.locator('#results > p').filter(has_text='本次目标')],mask_color='#50645f')
        shots.append(dict(chapter=chapter,file=str(path.relative_to(ROOT)).replace('\\','/'),action=action,source=source,
                          captured_at=datetime.now(timezone.utc).isoformat(),width=1920,height=1080,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        print(chapter,number,action,flush=True)
    with tempfile.TemporaryDirectory(prefix='kehang-recording-') as name:
        temp=Path(name);servers=[];threads=[]
        for index in range(2):
            server=AppServer(0,temp/f'isolated-{index}.sqlite',ROOT/'vendor/python-3.13.17-embed-amd64.zip')
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();servers.append(server);threads.append(thread)
        urls=[f'http://127.0.0.1:{server.server_port}' for server in servers]
        try:
            with sync_playwright() as p:
                browser=p.chromium.launch(channel='msedge',headless=True)
                context=browser.new_context(viewport={'width':1920,'height':1080},accept_downloads=True)
                context.on('request',lambda r:external.append(r.url) if r.url.startswith(('http://','https://')) and not any(r.url.startswith(url+'/') for url in urls) else None)
                teacher=context.new_page();teacher.on('pageerror',lambda error:errors.append(str(error)));teacher.goto(urls[0]);teacher.wait_for_function('()=>practiceState.practice!==null')
                capture(teacher,'00','新启动的本机教师实例首页；固定实训概览')
                teacher.locator('#practice-instructions summary').click();capture(teacher,'00','展开真实学习目标与前置条件')
                teacher.locator('#practice-steps h3').nth(1).scroll_into_view_if_needed();capture(teacher,'00','滚动读取已有环境与明确内核要求')
                teacher.locator('#practice-instructions summary').click();teacher.evaluate('()=>scrollTo(0,0)');capture(teacher,'00','折叠步骤回到环境/阅读/成果三条状态')
                teacher.get_by_text('教师发布 / 学生导入实训资料包',exact=True).click();teacher.locator('#practice-publish').scroll_into_view_if_needed();capture(teacher,'01','展开本机教师发布入口')
                teacher.locator('#practice-publish').click();teacher.wait_for_function('()=>practiceState.courses!==null');capture(teacher,'01','教师实际发布，两组件分别取得本机课程码')
                with teacher.expect_download() as d:teacher.locator('#practice-materials').click()
                d.value.save_as(temp/'materials.zip');capture(teacher,'01','实际点击下载完整实训资料')
                with teacher.expect_download() as d:teacher.locator('#practice-export-package').click()
                package=temp/'practice-course.json';d.value.save_as(package);capture(teacher,'01','实际导出课堂资料包；供另一独立本机实例导入')
                learner=context.new_page();learner.on('pageerror',lambda error:errors.append(str(error)));learner.goto(urls[1]);learner.wait_for_function('()=>practiceState.practice!==null')
                capture(learner,'02','第二个独立本机服务与空课程库；仍为同一电脑')
                learner.get_by_text('教师发布 / 学生导入实训资料包',exact=True).click();learner.set_input_files('#practice-package',str(package));learner.wait_for_function('()=>practiceState.courses!==null');capture(learner,'02','实际导入教师资料包；分别发布同摘要组件任务')
                learner.locator('#practice-instructions summary').click();capture(learner,'02','展开完整跟做步骤与预期结果')
                learner.locator('#practice-steps li').filter(has_text='在Notebook中计算').scroll_into_view_if_needed();capture(learner,'02','读取Notebook填写与真实内核运行要求')
                learner.locator('#practice-read').scroll_into_view_if_needed();learner.locator('#practice-read').check();capture(learner,'02','本人阅读声明单独记录；不改变环境及成果结论')
                learner.locator('#practice-instructions summary').click()
                lab=ROOT/'records/practice/lab-run';good=json.loads((lab/'实训成果.json').read_text(encoding='utf-8'))
                wrong=deepcopy(good);wrong['notebook']['array_sum']=41;negative=temp/'代理构造负例_合计41.json';negative.write_text(json.dumps(wrong,ensure_ascii=False),encoding='utf-8')
                learner.locator('#practice-submission').scroll_into_view_if_needed();capture(learner,'05','成果提交入口；以下错误是代理构造验证负例')
                learner.set_input_files('#practice-submission',str(negative));capture(learner,'05','实际选择构造错误成果文件，尚未核验')
                learner.locator('#practice-check').click();learner.wait_for_function("()=>practiceState.attempts.at(-1)?.result.status==='mismatch'");capture(learner,'05','确定性核验实际拒绝41；提示重新计算')
                learner.locator('#practice-attempts-panel summary').click();learner.locator('#practice-attempts').scroll_into_view_if_needed();capture(learner,'05','保留错误提交实际记录，不冒充学生错误')
                learner.set_input_files('#practice-submission',str(lab/'实训成果.json'));learner.locator('#practice-check').click();learner.wait_for_function("()=>practiceState.attempts.at(-1)?.result.status==='pass'");learner.locator('#practice-result').scroll_into_view_if_needed();capture(learner,'06','核验本轮实际执行固定练习生成的正确成果',str((lab/'实训成果.json').relative_to(ROOT)))
                learner.locator('#practice-notebook').click();learner.wait_for_function("()=>state.task?.scenario==='notebook-data'");learner.set_input_files('#report-files',[str(lab/'notebook-data-B.json'),str(lab/'notebook-data-A.json')]);learner.wait_for_function('()=>state.after!==null&&state.analysis?.passed===true');learner.locator('#comparison').scroll_into_view_if_needed();capture(learner,'06','实际一次导入本轮Notebook原始A/B；此处为报告分析，非重新运行内核','records/practice/lab-run/notebook-data-{A,B}.json')
                learner.locator('#practice-sqlite').click();learner.wait_for_function("()=>state.task?.scenario==='sqlite-basics'");learner.set_input_files('#report-files',[str(lab/'sqlite-basics-B.json'),str(lab/'sqlite-basics-A.json')]);learner.wait_for_function('()=>state.after!==null&&state.analysis?.passed===true');learner.locator('#comparison').scroll_into_view_if_needed();capture(learner,'06','实际导入本轮SQLite原始A/B；与Notebook独立身份核对','records/practice/lab-run/sqlite-basics-{A,B}.json')
                learner.locator('#practice-environment').scroll_into_view_if_needed();capture(learner,'06','两个固定环境复检、阅读声明和成果结论分别显示')
                learner.locator('#practice-completion').scroll_into_view_if_needed();capture(learner,'07','回到成果与历史尝试记录，准备导出')
                with learner.expect_download() as d:learner.locator('#practice-completion').click()
                completion=OUT/'recorded-completion.json';d.value.save_as(completion);capture(learner,'07','实际导出完成物与错误→正确两次记录')
                teacher.get_by_text('教师核对学生完成物',exact=True).click();teacher.locator('#practice-completion-file').scroll_into_view_if_needed();capture(teacher,'07','教师展开重新核验入口，不信任文件中的通过字段')
                teacher.set_input_files('#practice-completion-file',str(completion));teacher.wait_for_function("()=>document.querySelectorAll('#practice-teacher-review li').length===2");teacher.locator('#practice-teacher-review').scroll_into_view_if_needed();capture(teacher,'07','教师实际重核两次成果：错误仍拒绝，正确通过')
                history=context.new_page()
                for chapter,lines in GROUPS.items():
                    history.goto(pages[chapter].as_uri());capture(history,chapter,'打开清楚标明历史回顾的只读原文阅读页',{'file':str(PROMPT.relative_to(ROOT)),'source_lines':lines})
                    for line in lines:
                        summary=history.locator(f'#line-{line} summary');summary.click();summary.scroll_into_view_if_needed();capture(history,chapter,'实际展开真实归档消息源行 '+str(line),{'source_line':line})
                    if chapter=='12':
                        history.locator('#git-diff summary').click();history.locator('#git-diff pre').scroll_into_view_if_needed();capture(history,chapter,'打开实际git show 2c5ade2代码及回归差异',{'commit':'2c5ade24c512a6b15c7111f808192f480627c4fb'})
                        history.mouse.wheel(0,570);history.wait_for_timeout(180);capture(history,chapter,'向下滚动核对真实修复代码差异')
                    else:
                        history.locator(f'#line-{lines[-1]} .quote').evaluate('(el)=>{const r=document.createRange();r.selectNodeContents(el);const s=getSelection();s.removeAllRanges();s.addRange(r)}')
                        capture(history,chapter,'在浏览器中选中最后一条真实消息原文',{'source_line':lines[-1]})
                        if len(lines)==2:
                            history.evaluate('()=>scrollTo(0,0)');capture(history,chapter,'回到本段真实消息并列阅读')
                browser.close()
        finally:
            for server in servers:server.shutdown();server.server_close()
            for thread in threads:thread.join()
    if errors or external:raise AssertionError((errors,external))
    index=dict(started_at=started,ended_at=datetime.now(timezone.utc).isoformat(),width=1920,height=1080,
               actor='代理实际操作同一电脑上新启动的两个独立本机实例；不是独立新手或第二设备。',
               history_scope='本轮录制的资料阅读动作；内容来自已脱敏真实可见消息与真实git diff，清楚标明历史回顾，不冒充历史聊天原屏幕或现场模型生成。',
               negative_scope='章节05的合计41为代理构造负例；章节06正确成果及环境A/B来自本轮实际执行归档。录制本身只导入/分析报告，不重新运行内核。',
               original_session_read=False,ai_requests=0,desktop_capture=False,page_errors=errors,external_requests=external,
               source_prompt_sha256=hashlib.sha256(PROMPT.read_bytes()).hexdigest(),shots=shots)
    (OUT/'index.json').write_text(json.dumps(index,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Recorded '+str(len(shots))+' true browser action screenshots: '+str(OUT),flush=True)


if __name__=='__main__':main()
