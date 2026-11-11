"""Build and render the practice edition from its frozen product and actual evidence."""
from pathlib import Path
import hashlib
import json
import subprocess
from html import escape
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from .build_technical_pdf import font_setup, ROOT
from PIL import Image
import fitz

def main():
    frozen=json.loads((ROOT/'records/practice/product.json').read_text(encoding='utf8'))
    for name, expected in frozen['files'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected,name
    run=json.loads((ROOT/'records/practice/e2e.json').read_text(encoding='utf8'))
    assert run['passed']
    font_setup()
    out=ROOT/'output/pdf/课航_实训闭环技术文档.pdf'
    pdf=Canvas(str(out),pagesize=A4,pageCompression=1)
    pdf.setTitle('课航 | 从一张成绩表到可核对的实训成果')
    width,height=A4
    y=0
    def text(x,top,value,size=12,color='#193933'):
        pdf.setFont('CN',size);pdf.setFillColor(HexColor(color));pdf.drawString(x,height-top,value)
    def paragraph(value,size=12,leading=20,color='#253D38',margin=10):
        nonlocal y
        p=Paragraph(escape(value),ParagraphStyle('p',fontName='CN',fontSize=size,leading=leading,wordWrap='CJK',textColor=HexColor(color)))
        _,h=p.wrap(width-96,1000);p.drawOn(pdf,48,height-y-h);y+=h+margin
        assert y<height-46, (value,y)
    def sec(label,body):
        paragraph(label,14,20,'#087661',5);paragraph(body)
    def start(n,label,title):
        nonlocal y
        if n>1:pdf.showPage()
        text(48,46,'课航   /   技术文档',11,'#19705C');text(width-140,46,'实训闭环版   /   '+f'{n:02}',10)
        pdf.setStrokeColor(HexColor('#C6D9D1'));pdf.line(48,height-58,width-48,height-58)
        y=86;paragraph(label,11,17,'#A75D32',5);paragraph(title,25,34,'#193933',17)
        text(48,height-28,'KEHANG     ·     本机评审版     /     2026.11',8,'#667B73')
    def shot(name,caption):
        nonlocal y
        path=ROOT/'records/practice/screens'/name
        with Image.open(path) as im:w,h=im.size
        sw=width-96;sh=sw*h/w
        pdf.drawImage(str(path),48,height-y-sh,sw,sh);y+=sh+6
        paragraph(caption,9,14,'#577068')
    start(1,'产品与代表任务','从一张成绩表到可核对的实训成果')
    paragraph('学生在 Notebook 算出分组统计，再用 SQLite 对同一份数据查询。教师收到限定格式的结果，可以按原任务重新核对两部分数值，也可以查看错误重交的过程。',15,24)
    sec('课堂问题','课程软件能运行，只解决了开课前的准备。教师还需要知道学生交了哪一版资料、哪组数字不符，以及第二次提交是否改对。课航把这三件事放在一次实训中。')
    shot('practice.png','图 1  本轮启动的课航工作台，课堂资料绑定两项独立环境任务。')
    paragraph('固定产品版本  '+frozen['head'],9,14)
    start(2,'教学设计','同源数据，两种方法')
    sec('01   教师发布','在课堂实训入口发布并导出课堂包。学生在另一独立课程库导入，核对任务标识和资料版本。下载并完整解压课堂资料，数据、模板、步骤和提交格式一起传递。')
    sec('02   学生动手','选择与课程 Python 对应的 Jupyter 内核，读入 scores.csv。计算行数、总分与按类别求和的结果。然后对 scores 表执行分组查询，比较两种方法的统计口径。')
    sec('03   教师核对','CSV 含 A/10、A/20、B/12。应有 3 行、总分 42；A 组 2 行合计 30，B 组 1 行合计 12。核验分别标出 Notebook 与 SQLite 的差异，保留首次错误和后来的正确提交。')
    sec('课堂使用边界','核验对象是该任务及同一数据版本的数字。相同的有效成果可以重复通过。本人阅读是声明，代码运行证据来自本机探针，作品原创性和学习掌握程度需要教师另行判断。')
    start(3,'工程设计','只分析证据的本机工作台')
    sec('本机网页','标准库 HTTP 服务绑定回环地址，SQLite 课程库存不可变任务快照。教师包在新实例导入时重新校验。浏览器请求只用于取材料、保存任务或核对数据。')
    sec('主动采集','Python 与 Notebook 工具包内的 Start-Collect.cmd 定位工具目录、内嵌运行时和 task.json。本人指定课程解释器，Notebook 还需指定对应 kernel.json。两份报告以实际时间排序并检查目标身份。')
    sec('确定性规则','成果限定为 JSON。先验证资料版本、数据摘要、任务身份及结构，再逐项比较行数、总和与分组。环境初复检仍使用原来各自的课程任务、组件身份与时间顺序。')
    sec('开源复用与意图控制','复用既有 Educates 教学动作适配，来源固定 d7e018f0，Apache-2.0 许可与 NOTICE 随仓库。代码只接收固定报告检查。用户授权新增课堂连续实训，既有 13 种课程任务继续沿用原快照。')
    sec('与其他工具配合','教程提供操作步骤，通用问答解释报错。课航额外携带固定数据、可移交的要求、各组件原始检查与可重算成果。AI 解释不能改变规则结论。')
    start(4,'验证与复现','怎样复核这次课堂操作')
    sec('在同一台 Windows 电脑上','本轮使用两个独立回环实例和两个新课程库，实际从教师端导出，再由学生端导入。完整步骤和本轮构造负例保存在 records/practice。')
    shot('result.png','图 2  学生端实际提交记录。错误成果是执行者构造的测试输入。')
    sec('复检与剩余条件','Notebook 真内核及 SQLite 只读查询各自取得同目标 A/B。覆盖范围为本机，390 像素为浏览器模拟。API 课程调用、产品 AI 诊断和本人授权的 DSH 工具任务各需自己的真实运行记录。')
    start(5,'评审入口','启动、检查与过程来源')
    sec('先备好环境','已有 Windows 和 Python 3.10 或以上即可运行网页。要复现 Notebook 计算，另需符合任务版本的 Python、Jupyter、ipykernel、NumPy 与 Pandas，以及与该解释器绑定的 kernel.json。解压包内运行时用于采集。')
    paragraph('从交付根目录运行  python -B -m campuslab.web --port 8783 --database ./data/practice.sqlite --runtime-zip ./vendor/python-3.13.17-embed-amd64.zip  ，访问 http://127.0.0.1:8783/。端口已占用时指定空闲端口。',10,17)
    sec('复核路径','先读 README 和评审入口，再取课堂资料和成果完成物。对照提交的数值或重新送入核验。对应单测、原始初复检、界面状态、固定产品清单和独立报告可按路径追查。')
    sec('如何追查 AI 协作','docs/实训版Prompt链逐项核查.md 区分用户具体引导、执行者发现和独立审查发现。原会话的脱敏可见导出、Git 差异与真实失败记录分别支撑相应步骤。完整三条核心链与赛事资格尚无确认。')
    sec('评分条目与外部交付','本版按 Vibe Coding 的过程可复现 25%、解题实用 25%、方法与意图控制 20%、工程 15%、体验 15% 整理。远程访问、上传与回执由本人办理。')
    pdf.save()
    qa=ROOT/'records/practice/pdf';qa.mkdir(parents=True,exist_ok=True)
    subprocess.run(['pdftoppm','-r','115','-png',str(out),str(qa/'page')],check=True)
    with fitz.open(out) as doc:
        assert len(doc)==5
        assert all(len(page.get_text().strip())>140 for page in doc)
    print(out)

if __name__=='__main__':main()
