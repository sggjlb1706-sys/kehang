"""Edit the recorded isolated classroom tabs, lab outputs and attributed visible AI history into an MP4."""
from pathlib import Path
import argparse,hashlib,json,re,subprocess,tempfile
from PIL import Image,ImageDraw,ImageFont,ImageOps
ROOT=Path(__file__).resolve().parents[1]
REC=ROOT/'records/practice'
NAVY='#152E2C';GREEN='#00634F';MUTED='#526C66'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run():
    ap=argparse.ArgumentParser();ap.add_argument('--ffmpeg',type=Path,required=True);args=ap.parse_args()
    ff=str(args.ffmpeg.resolve())
    frozen=json.loads((REC/'product.json').read_text(encoding='utf8'))
    messages=json.loads(next((ROOT/'records/brand/prompts').glob('01a*.json')).read_text(encoding='utf8'))['messages']
    byline={m['source_line']:m for m in messages}
    out=ROOT/'output/video/课航_实训闭环演示.mp4';out.parent.mkdir(parents=True,exist_ok=True)
    base=REC/'film';base.mkdir(exist_ok=True)
    screens=REC/'screens'
    fonts={n:ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',n) for n in (20,25,28,32,36,42,54)}
    def wrap(d,x,y,s,px,maxw,col):
        line=''
        for ch in s+'\n':
            if ch=='\n' or (line and d.textlength(line+ch,font=fonts[px])>maxw):
                d.text((x,y),line,font=fonts[px],fill=col);y+=int(px*1.53);line='' if ch=='\n' else ch
            else: line+=ch
        return y
    def quote(lines):
        ans=[]
        for n in lines:
            m=byline[n];s=m['text'].strip().replace('**','').replace('`','')
            if n==17:s=s[s.index('不要依赖'):s.index('已授权')].strip()
            if n==1456:s=s.split('\n')[0]
            if len(s)>190:s=s[:188]+'…'
            ans.append(('用户' if m['role']=='user' else '助手',f'源行 {n}  ·  '+m['timestamp'][:10],s))
        return ans
    lab=REC/'lab-run'
    book=json.loads((lab/'学生已执行.ipynb').read_text(encoding='utf8'))
    code=next(''.join(c['source']) for c in book['cells'] if c['cell_type']=='code' and 'row_count = len' in ''.join(c['source']))
    nb=json.loads((lab/'实训成果.json').read_text(encoding='utf8'))
    field=lambda value:json.dumps(value,ensure_ascii=False)
    # Each cue identifies whether its source is a captured application, actual file or historical conversation.
    cues=[
      (19,'课程现场','一张表，两种算法','practice','教师希望核对学生交出的数据结果。打开课航，先看课堂实训的要求、两个环境任务和提交入口。'),
      (18,'课程现场','发布并携带要求','published','教师在本机发布课堂包，得到两个组件课程码。跨实例传递使用固定资料包，学生在另一份本机课程库导入。'),
      (19,'课程现场','跟着资料操作','steps','完整解压后，用已确认的课程内核打开 Notebook。三行数据保存在 scores.csv，先确认文件位置和每列含义。'),
      (19,'本轮实际执行文件','计算行数与分组',[('Notebook','学生已执行.ipynb · 已执行单元节选',code.split('group_totals =')[0].strip()[-290:]),('输出','实训成果.json · notebook',field(nb['notebook']))],'在已运行的 Notebook 中，按 category 汇总和直接求总和都来自读取的 CSV。内核探针另有自己的初检和复检。'),
      (19,'本轮实际执行文件','用 SQL 交叉核对',[('查询','02_SQLite练习.py · 本轮填写的固定语句','SELECT category, COUNT(*), SUM(score) FROM scores GROUP BY category ORDER BY category'),('查询结果','实训成果.json · sqlite',field(nb['sqlite']))],'在同一数据上按类别计算行数和分数合计。A 有两行，B 有一行，两组分数相加仍然是 42。'),
      (18,'课堂操作 · 代理构造负例','第一次核验总分为 41','wrong','这里特意把正确总分 42 改成 41，作为代理构造的反例。SQLite 行仍然正确，学生可以直接回到 Notebook 查总分。'),
      (19,'课程现场','再次提交真实计算结果','accepted','重新选取实际模板生成的成果。两部分都符合后，页面仍保留前一次错误。教师可以按同一份资料重新核对。'),
      (18,'课程现场','分别核对环境与成果','result','两份环境报告按时间和组件身份复检。阅读是本人声明，数字是否符合由规则判断。完成物保留提交次序。'),
      (23,'真实 AI 协作回顾','用户怎样规定范围',quote([17,29]),'回看上一轮的真实可见消息。用户要求从正式基线继续，助手把 Notebook、SQLite 等任务约束成可验证的具体工作。'),
      (23,'真实 AI 协作回顾','开源组件怎样落地',quote([338,470]),'助手把 Educates 教学动作接到已有检查上。随后报告固定内核运行和只读查询，今天的连续实训复用这两项任务。'),
      (22,'真实 AI 协作回顾','下载包缺什么',quote([565,810,815]),'执行者在整合时发现下载包缺少固定 CSV。保留原发现者身份，用户的“继续”只表示推进原任务。'),
      (23,'真实 AI 协作回顾','怎样把失败留作证据',quote([890,970]),'这次问题由独立审查者发现。版本命令退出状态缺失时，规则曾误判通过。助手报告修复内容并安排同版本复核。'),
      (23,'真实 AI 协作回顾','从消息追到代码',[('Git 差异','2c5ade2 · campuslab/java_course.py',subprocess.check_output(['git','show','--format=','-U0','2c5ade2','--','campuslab/java_course.py'],cwd=ROOT).decode().split('@@')[2].strip()[:315]),*quote([1063])],'可以把历史对话和提交放在一起审阅。独立者重跑 115 项测试，是当时版本的核对记录。'),
      (22,'真实 AI 协作回顾','用户如何纠正产品定位',quote([1402,1456,1463,1466]),'用户指出旧名称太窄，确认“课航”。对应的 Git 提交为 1eadacb。命名确认与围绕具体程序故障的用户纠偏分别记载。'),
      (17,'本轮交付','复现与证据入口',[('复现','README.md → 本机工作台','先准备课程 Python、Jupyter、NumPy、Pandas。导入课堂资料，完成模板并提交 JSON。'),('证据','records/practice','lab-run：实际完成的 Notebook 和初复检。completion-local.json：首次错误与后续正确。product.json：固定产品文件清单。')],'本片展示同一台电脑上的教师端和学生端。本轮没有取得本人真实 API 请求或 DSH 工具回合。评审访问与上传需本人办理。')]
    timeline=[];segments=[]
    with tempfile.TemporaryDirectory(prefix='kehang-film-') as tmp:
        folder=Path(tmp)
        def render(i,item,scene=None):
            sec,tag,title,source,caption=item
            im=Image.new('RGB',(1920,1080),'#F0F3EE');d=ImageDraw.Draw(im)
            d.rectangle((0,0,1920,13),fill=GREEN)
            d.text((70,46),'课航  /  计算机课程学习与实训助手',font=fonts[28],fill=GREEN)
            d.text((1480,46),tag,font=fonts[25],fill=MUTED);d.text((68,105),title,font=fonts[54],fill=NAVY)
            d.rectangle((66,206,1420,943),fill='white')
            if scene or isinstance(source,str):
                pic=Image.open(scene or screens/(source+'.png')).convert('RGB')
                pic.thumbnail((1344,727));im.paste(pic,(70+(1344-pic.width)//2,211))
            else:
                y=238
                for role,ref,body in source:
                    d.text((96,y),role+'   /   '+ref,font=fonts[25],fill=GREEN);y+=45
                    y=wrap(d,96,y,body,32,1270,NAVY)+21
                if y>964:raise ValueError(('cue overflow',i,y))
            wrap(d,1460,270,caption,32,390,NAVY)
            d.text((1460,815),'课航   /   本机实训',font=fonts[25],fill=GREEN)
            d.text((65,984),('脱敏会话原文节选及真实提交  ·  历史回顾' if tag.startswith('真实 AI') else tag+'  ·  开发者代理实际操作记录'),font=fonts[25],fill=MUTED)
            d.text((1530,986),f'{i+1:02d}  /  {len(cues):02d}     '+frozen['head'][:8],font=fonts[25],fill=MUTED)
            return im
        for i,item in enumerate(cues):
            sec,tag,title,src,caption=item
            frame=base/f'{i+1:02}.jpg';render(i,item).save(frame,quality=90)
            seq=[]
            chapter=sorted((REC/'film-shots'/f'{i:02}').glob('*.jpg'))
            if chapter:
                for k,path in enumerate(chapter):
                    f=folder/f'chapter-{i}-{k:03}.jpg';render(i,item,path).save(f,quality=91)
                    seq.append((f,(sec-4)/len(chapter)))
            # A real series of frames during teacher publish (no desktop or other tabs).
            if i==1 and not chapter:
                live=sorted((ROOT/'records/runtime/practice-recording/teacher').glob('*.jpg'))
                for k,path in enumerate(live[-32:]):
                    f=folder/f'live-{k:03}.jpg';render(i,item,path).save(f,quality=88);seq.append((f,.18))
            seq.append((frame,sec-sum(s for _,s in seq)))
            txt=folder/f'{i}.txt'
            txt.write_text(''.join("file '"+p.as_posix()+"'\nduration "+str(dur)+'\n' for p,dur in seq)+"file '"+frame.as_posix()+"'\n",encoding='utf8')
            seg=folder/f'{i:02}.mp4'
            subprocess.run([ff,'-hide_banner','-loglevel','error','-f','concat','-safe','0','-i',str(txt),'-t',str(sec),'-vf','fps=24','-c:v','libx264','-threads','4','-preset','veryfast','-crf','20','-pix_fmt','yuv420p',str(seg)],check=True)
            segments.append(seg);timeline.append(dict(start=sum(x['seconds'] for x in timeline),seconds=sec,title=title,category=tag,source=src if isinstance(src,str) else [x[1] for x in src],frame_sha256=sha(frame),caption=caption,live_frames=len(seq)-1))
        concat=folder/'parts.txt';concat.write_text(''.join("file '"+p.as_posix()+"'\n" for p in segments),encoding='utf8')
        subprocess.run([ff,'-y','-loglevel','error','-f','concat','-safe','0','-i',str(concat),'-c','copy','-movflags','+faststart',str(out)],check=True)
    inspect=subprocess.run([ff,'-hide_banner','-i',str(out),'-map','0:v','-f','null','-'],capture_output=True,check=True)
    details=inspect.stderr.decode(errors='replace');duration=re.search(r'Duration: (\d+):(\d+):([\d.]+)',details)
    h,m,s=duration.groups();length=int(h)*3600+int(m)*60+float(s)
    assert 300<=length<=480 and '1920x1080' in details
    verification=dict(seconds=length,size=[1920,1080],fps=24,ai_history_seconds=sum(v['seconds'] for v in timeline if v['category'].startswith('真实 AI')),head=frozen['head'],sha256=sha(out),full_decode=True,timeline=timeline,actual_course_footage='isolated browser tabs; developer-operated, plus actual lab outputs',audio='silent; burned-in Chinese explanations')
    assert verification['ai_history_seconds']>=120
    (base/'timeline.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2),encoding='utf8')
    print(length,verification['ai_history_seconds'],sha(out))

if __name__=='__main__':run()
