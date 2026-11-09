"""Build the reviewed product's Chinese technical PDF; never install dependencies.

Run only after the PDF skill's one-time artifact-start command succeeds.
The product commit must have exactly the current campuslab/web/launcher bytes.
"""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import re
import shutil
import subprocess

import fitz
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Flowable, Image, KeepTogether, PageBreak, Paragraph,
                               SimpleDocTemplate, Spacer, Table, TableStyle)

ROOT = Path(__file__).resolve().parents[1]
INK = colors.HexColor('#26332f')
MUTED = colors.HexColor('#52615b')
ACCENT = colors.HexColor('#884b31')
PALE = colors.HexColor('#f3f5f1')
LINE = colors.HexColor('#d9dfd9')
WIDTH = A4[0]-104


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest().upper()


def check_product(head):
    if not re.fullmatch('[0-9a-f]{40}', head):
        raise ValueError('Product HEAD must be a full lowercase Git commit')
    names = subprocess.check_output(['git','ls-tree','-r','--name-only',head],cwd=ROOT,text=True,encoding='utf-8').splitlines()
    selected=[p for p in names if p.startswith(('campuslab/','web/')) or p=='Start-Web.ps1']
    if not selected:
        raise ValueError('Product commit contains no application files')
    checked={}
    for name in selected:
        original=subprocess.check_output(['git','show',head+':'+name],cwd=ROOT)
        current=(ROOT/name).read_bytes()
        if original!=current:
            raise ValueError('Current product differs from selected HEAD: '+name)
        checked[name]=sha256(current).hexdigest().upper()
    return checked


class Pipeline(Flowable):
    def __init__(self, labels, width=WIDTH, height=64):
        super().__init__(); self.labels=labels; self.width=width; self.height=height

    def draw(self):
        c=self.canv; count=len(self.labels); gap=14; box=(self.width-gap*(count-1))/count
        for i,label in enumerate(self.labels):
            x=i*(box+gap)
            c.setFillColor(PALE); c.setStrokeColor(LINE); c.roundRect(x,10,box,44,5,stroke=1,fill=1)
            c.setFillColor(ACCENT); c.setFont('CN',11)
            lines=label.split('\n')
            for j,line in enumerate(lines):c.drawCentredString(x+box/2,34+(len(lines)-1)*7-j*14,line)
            if i<count-1:
                c.setStrokeColor(MUTED); c.line(x+box+3,32,x+box+gap-3,32)
                c.line(x+box+gap-7,35,x+box+gap-3,32);c.line(x+box+gap-7,29,x+box+gap-3,32)


def font_setup():
    candidates=[Path('C:/Windows/Fonts/msyh.ttc'),Path('C:/Windows/Fonts/simsun.ttc')]
    for path in candidates:
        if path.is_file():
            try:
                pdfmetrics.registerFont(TTFont('CN',str(path),subfontIndex=0))
                return str(path)
            except Exception:
                continue
    raise ValueError('No existing embeddable Chinese font; do not install automatically')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--product-head',required=True)
    parser.add_argument('--unit-tests',required=True,type=int)
    parser.add_argument('--browser-summary',required=True)
    parser.add_argument('--review-status',required=True)
    parser.add_argument('--desktop',type=Path)
    parser.add_argument('--mobile',type=Path)
    parser.add_argument('--output',type=Path,default=ROOT/'output/pdf/AI实验环境管家_课程能力版_技术文档.pdf')
    args=parser.parse_args()
    if args.unit_tests<1:raise ValueError('Provide the actually verified test count')
    source_hashes=check_product(args.product_head)
    font=font_setup()
    out=args.output.resolve();out.parent.mkdir(parents=True,exist_ok=True)
    qa=ROOT/'records/courses/pdf';qa.mkdir(parents=True,exist_ok=True)
    styles={
        'body':ParagraphStyle('body',fontName='CN',fontSize=10.3,leading=17.2,textColor=INK,spaceAfter=9,wordWrap='CJK'),
        'small':ParagraphStyle('small',fontName='CN',fontSize=8.6,leading=13.2,textColor=MUTED,spaceAfter=7,wordWrap='CJK'),
        'title':ParagraphStyle('title',fontName='CN',fontSize=27,leading=38,textColor=INK,spaceAfter=14,wordWrap='CJK'),
        'h1':ParagraphStyle('h1',fontName='CN',fontSize=20,leading=29,textColor=INK,spaceAfter=15,wordWrap='CJK'),
        'h2':ParagraphStyle('h2',fontName='CN',fontSize=12.8,leading=21,textColor=ACCENT,spaceBefore=8,spaceAfter=7,wordWrap='CJK'),
        'cell':ParagraphStyle('cell',fontName='CN',fontSize=9.2,leading=14.3,textColor=INK,wordWrap='CJK'),
        'code':ParagraphStyle('code',fontName='CN',fontSize=8.2,leading=13,textColor=INK,backColor=PALE,borderPadding=10,spaceAfter=10,wordWrap='CJK'),
    }
    story=[];image_records=[]
    def p(text,kind='body'):
        story.append(Paragraph(escape(text).replace('\n','<br/>'),styles[kind]))
    def h(text):p(text,'h2')
    def page(title):
        if story:story.append(PageBreak())
        p(title,'h1')
    def table(headers,rows,widths):
        cells=[[Paragraph(escape(str(cell)),styles['cell']) for cell in row] for row in [headers]+rows]
        t=Table(cells,colWidths=widths,repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),PALE),('LINEBELOW',(0,0),(-1,0),1,ACCENT),
            ('LINEBELOW',(0,1),(-1,-1),.4,LINE),('VALIGN',(0,0),(-1,-1),'TOP'),
            ('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),
            ('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
        story.extend([t,Spacer(1,10)])
    def screenshot(path,max_w,max_h,caption,crop=None):
        if path is None:return
        path=path.resolve()
        if not path.is_file():raise ValueError('Missing supplied screenshot: '+str(path))
        from PIL import Image as PILImage
        original=path
        with PILImage.open(path) as im:
            if crop:
                cropped=im.crop(crop);path=qa/(original.stem+'-detail.png');cropped.save(path)
                w,h=cropped.size
            else:w,h=im.size
        image_records.append(dict(source=original.relative_to(ROOT).as_posix(),source_sha256=digest(original),
            used_image=path.relative_to(ROOT).as_posix(),used_image_sha256=digest(path),crop_pixels=crop))
        scale=min(max_w/w,max_h/h)
        story.append(Image(str(path),width=w*scale,height=h*scale,hAlign='LEFT'))
        p(caption,'small')

    # 1 - Product value and supported scope.
    p('AI 实验环境管家','title')
    p('课程要求驱动的环境准备、证据核对与同目标复检','h2')
    p('面向大数据及其他计算机专业的多种课程实验。学生从学习目标进入，教师从固定任务进入；两种入口共用要求、事实、指导和复检。系统帮助学生知道要准备什么、下一步怎样做，以及怎样证明当前环境确实能运行。')
    story.append(Pipeline(['确定课程\n固定要求','选择环境\n取得事实','处理差异\n本人操作','同目标复检\n运行证据']))
    h('课程任务是起点，真实运行是完成条件')
    table(['能力','本版落实'],[
        ['两条新纵切','独立PyTorch CPU/GPU课程；VirtualBox/VMware与Linux来宾分层课程。'],
        ['共同流程','需求澄清、独立硬件预检、分层操作指导、文字报错诊断、携带教师任务、脱敏分享与复检。'],
        ['原有能力','保留Python、Node.js/npm与固定Qwen本地模型的任务/报告兼容。'],
        ['课程目录','Notebook、Java/JDK、数据库、Hadoop、网络/云计算保留有来源的调研与扩展验收，不冒称已实现。'],
    ],[100,WIDTH-100])
    h('本技术文档的版本')
    p('产品HEAD：'+args.product_head,'code')
    p('基线：42d86482fa1540b35fcdda6bbdf15d888f6b8cd1；分支：codex/courses-20261108。技术PDF、演示与提交资料对应上述产品源码。后续仅文档/交付回执提交可形成更晚HEAD，产品字节一致性由构建记录核对。','small')
    p('2026年11月8日课程能力补全轮 | Windows本机产品 | 技术说明','small')

    # 2 - Architecture and deterministic ownership.
    page('统一流程：要求、事实与建议各有边界')
    story.append(Pipeline(['学生目标\n教师任务','固定任务\n摘要校验','显式目标\n手动采集','确定性分析\n四种状态']))
    p('网页负责组织步骤和生成可审查命令；独立采集器在目标电脑由本人启动。报告保存观察值，服务端重新判断状态，不相信报告自带的“通过”文字。AI位于事实解释之后，不参与改写任务与验收。')
    table(['层','责任与不变量'],[
        ['任务快照','规范化JSON生成SHA-256。支持固定检测类型；教师更名或要求变化形成不同快照，不能复用旧报告。'],
        ['目标与组件身份','显式绝对路径；解释器与GPU分别核对；宿主、软件、虚拟机实例与来宾分别表示。工具runtime不算课程Python。'],
        ['确定性判断','通过、缺失、不符合、未知完整保留。事实缺失、错误类型、失败运行和跨任务报告不会被显示为全部通过。'],
        ['指导与诊断','新手/标准/快捷只改变说明密度。建议已看、步骤已勾选、AI回复成功不改变事实与状态。'],
        ['同目标复检','相同任务摘要、目标与各已确认组件身份；B时间晚于A。区分稳定通过、补齐证据与真实改善。'],
    ],[100,WIDTH-100])
    h('同一套规则承载不同课程')
    p('rules.py保留已有任务与报告接缝，将固定PyTorch和VM场景分派到各自模块。collect.py统一手动CLI；CourseStore继续保存不可变教师快照。扩展只引入本轮验收需要的固定探测，不提供任意用户脚本执行接口。')
    h('轻量本机部署')
    p('网页和规则使用Python标准库，服务只监听127.0.0.1。不需要账号、班级、成绩后台或新Web依赖。既有官方嵌入Python仅服务检测工具；课程软件、权重和虚拟机由本人准备。')

    # 3 - Need and independent hardware evidence.
    page('从学习目标到有依据的准备路线')
    p('需求入口采用确定性识别与澄清：明确课程可以提出固定任务；CPU/GPU不清时提出选项；多课程、强制本地与仅云端等冲突先说明约束。学生确认后才建立任务。尚未实现的课程进入有来源目录，不退化成一个看似支持的替代任务。')
    screenshot(args.desktop,WIDTH,210,'本轮真实产品任务区域（从最终桌面视口截取）；原图及局部图摘要在构建记录中。',(450,260,1320,650))
    h('预检独立于课程是否已经装好')
    p('手动硬件CLI只读Windows、物理内存、目标盘容量与GPU/显存，记录采集时间、来源和未知原因。工具Python与课程解释器分开；不必先装PyTorch、下载权重或完成模型推理。')
    table(['本机事实','取得方式与解释'],[
        ['Windows 10.0.26200','CIM受限时使用只读platform/Windows API回退；不推测营销版本名称。'],
        ['物理内存16,849,256,448字节','GlobalMemoryStatusEx；是物理总量，不能等同当前空闲内存。'],
        ['D盘约71.4GB空闲','shutil.disk_usage；只代表报告时间的容量。'],
        ['RTX4060 Laptop / 约8GB显存','已有nvidia-smi驱动报告；显卡名称不证明框架构建或实际运算。'],
    ],[190,WIDTH-190])
    p('资源不足或信息未知时先补证据/向教师确认替代路线。固定本地任务仍要求本地运行，云端/API只解释为候选路线；4GiB提醒不是性能或兼容保证。','small')

    # 4 - PyTorch evidence.
    page('PyTorch：CPU验证与GPU验收分别成立')
    p('课程Python由学生明确选择；固定任务检查Python范围、torch版本及实际导入，运行明确float32矩阵乘法，期望结果为[[4,4],[10,8]]。课程方向参考高校深度学习大纲，版本和算式是本项目演示配置。')
    table(['课程层','本轮真实结果','不能替代的证据'],[
        ['CPU课程','同一Python A/B五项通过','GPU名称或包已安装不能代替固定CPU张量运行。'],
        ['GPU预检A','框架/设备已取证；GPU运算未知','CPU成功不能代替GPU成功。'],
        ['GPU显式运算B','九项通过；同一GPU UUID','须有CUDA构建、设备可用性、设备身份和实际GPU算式。'],
        ['另一基础Python','真实torch缺失，CPU运行未知','不得借用pytorch环境的版本补齐这个解释器。'],
    ],[92,155,WIDTH-247])
    h('本机实测环境')
    p('Python3.11.16、torch2.14.0+cu126、CUDA构建12.6、RTX4060 Laptop。GPU课程固定CUDA:0并记录独立UUID；未知UUID不推定同一设备，已知UUID变化拒绝按同目标复检。不同任务或解释器同样拒绝。')
    h('真实失败推动探测程序修正')
    p('首次int64矩阵在CPU成功，但CUDA返回“addmm_cuda not implemented for Long”。规则正确保留不符合。开发者随后把固定程序明确为float32，并将dtype写入新快照，另采CPU/GPU报告后通过；原int64报告原样保留。')
    p('这是探测程序修复，由开发实测发现；不是学生环境被修好，也不是用户针对Bug的反馈。证据：records/courses/torch/README.md、float32-retest/和首次报告。其他显卡、多GPU、CPU专用构建或任意版本组合没有因此得到兼容认证。','small')

    # 5 - VM evidence.
    page('VM/Linux：分层事实阻止错误完成')
    story.append(Pipeline(['宿主身份\n虚拟化条件','所选工具\n版本与路径','具体实例\nUUID或.vmx','Linux来宾\n身份与运行']))
    p('固定只读探测支持VirtualBox的版本、实例清单和showvminfo，以及VMware vmrun帮助/版本与运行实例清单。显式.vmx仅解析固定元数据，不执行配置内容；工具不会创建、导入、启动虚拟机或修改BIOS/系统/网络。')
    table(['证据层','本机实际情况','确定性结果'],[
        ['宿主虚拟化','HypervisorPresent=true；其他旗标不足以确认底层固件条件','未知；不把受屏蔽旗标说成BIOS关闭。'],
        ['软件','vmrun CLI1.17.0可读取；VirtualBox标准路径缺失','软件可单独通过，不代表来宾通过。'],
        ['具体实例','当前运行实例清单为0；未选定可读取实例','未知；不自动创建或启动。'],
        ['来宾系统/固定程序','本轮没有可取得的Linux来宾报告','未知；没有冒称完整来宾实测。'],
    ],[92,190,WIDTH-282])
    h('可执行的来宾证据路径')
    p('在本人已启动的所选Linux来宾中，复制单文件guest_probe.py并手动运行。报告绑定任务摘要和所选实例标识，读取DMI UUID、machine-id摘要，执行固定uname与Python求和。手动传回JSON，再由宿主采集器关联。')
    p("python3 guest_probe.py --task-id '<当前任务摘要>' --vm-id '<同一实例标识>' --output guest-A.json",'code')
    p('来宾证据有本演示的30分钟有效期；复检须取得较晚宿主/来宾证据。DMI和摘要是本机报告关联，不是不可伪造远程证明。固定Linux验证不代表完成XV6、Hadoop或其他课程作业。','small')

    # 6 - UI and portable delivery.
    page('让下一步操作清楚，也让任务可以传递')
    p('页面按“确定任务 - 准备课程环境 - 采集与复检”连续组织。任务要求与摘要可核对；缺失、不符合和未知同时使用文字状态，原始JSON细节默认收起。每个差异绑定当前任务和目标，给出本人可审查的步骤及复检方式。')
    if args.mobile:
        screenshot(args.mobile,165,230,'390px桌面浏览器宽度模拟局部，非实体手机。',(0,0,390,445))
    table(['使用方式','同一事实下的不同帮助'],[
        ['新手','分步解释术语、路径和操作位置；先区别工具Python、课程解释器与编辑器。'],
        ['标准','保留任务要求、依赖准备、采集、差异处理和复检关键步骤。'],
        ['快捷','直接核对差异及可审查命令；不降低证据或自动执行安装。'],
    ],[85,WIDTH-85])
    h('教师包与手机离线指导')
    p('教师导出固定课程包和无脚本的HTML指导，通过本人选择的文件渠道交给学生。另一实例导入时严格验证支持结构与摘要，保留相同验收条件；旧报告不能套到新快照。HTML指导可离线阅读，外部官方链接需联网。')
    p('摘要用于内容一致性检查，不是教师数字签名，须通过可信渠道确认来源。localhost课程码仅供原电脑访问；未生成指向不可达目标的二维码。','small')

    # 7 - Intent control and real iteration.
    page('AI协作：用可验证结果约束真实开发')
    p('本轮遵循用户明确的顺序：先能力、再UI、最后回归/独立审查与材料。先核对正式版HEAD、358项交付SHA和干净Git，再完整克隆到独立目录，保留旧版原字节。能力对照表把原方案、当前代码、缺口、实现和验收证据放在同一视图。')
    table(['实际阶段','真实产物与提交'],[
        ['核对与范围','33001e7：基线字节收据、来源、能力表和执行计划。'],
        ['PyTorch落地','941686f：独立CPU/GPU证据模块、固定探测、针对性测试及真实运行记录。'],
        ['VM/Linux落地','14244f1：宿主/软件/实例/来宾分层，固定只读命令和未知路径。'],
        ['准备与需求','aee993f：需求澄清、独立硬件预检、带来源课程目录。'],
        ['共用闭环','8e33aa1：课程包、离线指导、分层步骤与无报告文字报错入口。'],
        ['独立发现与修复','12d2a1b保留独立初审4项P2及1项P3；3dddd33实际修复，随后独立delta确认全部闭合。'],
    ],[105,WIDTH-105])
    h('失败保留，原因与证据分开')
    p('PyTorch首次CUDA dtype错误、vmrun -v参数调查失败、受限账户CIM取证失败，以及首次模块缺失/识别条件失败都按实际记录保留。Qwen首次错选缺transformers的PyTorch环境，改选已有模型环境后另采七项通过；没有安装修复。')
    p('独立审查另发现GPU硬要求被空格/CPU偏好降级、非CUDA文本误通过、JSON转义路径脱敏遗漏、旧目标修复命令残留及晚发布响应覆盖。主执行者保留反例并实际修复，由独立delta复核，不改写为用户Bug反馈。','small')
    h('真实Prompt的适用范围')
    p('可见消息留档保留来源行号和SHA，排除工具、系统/开发者和隐藏推理。用户的本轮范围指令是真实总授权，不伪装为具体Bug反馈。现有候选链尚不能确认达到至少三条完整核心链；旧阶段无Git与官方未答复仍明确保留。')

    # 8 - Verification and review.
    page('验证：对行为、证据和边界分别作证')
    table(['验证类型','本轮结果及适用范围'],[
        ['自动化单元/协议',str(args.unit_tests)+'项测试通过。覆盖固定任务、身份/时序、缺失未知、负例、携带课程、指导及AI同意；构造与本机协议测试不等于设备实测。'],
        ['浏览器回归',args.browser_summary],
        ['真实课程','CPU A/B稳定通过；GPU预检到主动运算后通过；固定Qwen七项通过、outcome=verified；VMware A/B仍incomplete。'],
        ['独立审查',args.review_status],
        ['原版本保护','基线358项交付文件匹配；原目录非Git文件保护与最终复核以交付回执为准。'],
    ],[105,WIDTH-105])
    h('AI诊断保持原规则')
    p('没有报告也能粘贴文字报错，但预览会明确解释器、依赖、硬件与目标身份尚未确认。有报告时引用既有检查；目的地与实际消息可预览编辑，必须明确单次同意。接口失败、超时、格式错误和未知建议不提升规则状态，建议命令由本人审查。')
    p('本轮没有取得可合法使用的免费/本地真实AI诊断条件，尚未发送真实诊断请求。固定Qwen课程离线推理是课程验证，不能当作AI报错诊断成功；本机假服务只能证明协议行为。')
    h('证据索引')
    p('records/courses/torch/、vm/、preparation/、model/保存真实与构造范围；records/browser/保存网页回归；最终UI三项以review-ui/20261108T105547Z为准。独立delta及evidence-note共同说明最终源码匹配范围，旧记录未覆盖。','small')

    # 9 - Reproduction, sources, delivery.
    page('复现与交付：同一个版本交给评审')
    h('已有工具Python时启动')
    p("进入新交付目录后运行：\n& .\\Start-Web.ps1 -Python 'D:\\ANACONDA\\python.exe' -Port 8772\n浏览器打开 http://127.0.0.1:8772/；Ctrl+C停止。",'code')
    p('服务需要已有Python≥3.10。网页与规则只用标准库；独立检测包使用既有官方嵌入运行时。上述启动不包含从零安装课程软件、下载模型或创建虚拟机。已有Qwen权重不随包复制，固定revision/SHA及来源见任务与reuse.json。')
    h('来源与扩展路线')
    p('高校公开资料提供课程方向依据，不代表用户学校统一要求。PyTorch参考重庆科技大学深度学习大纲；虚拟机分层参考哈工深实验指南；允许路线澄清参考科大Ubuntu实验；Notebook候选参考云南师范大纲。湖北、山东与北交部分原始PDF本轮访问失败/404，目录注明，未用搜索摘要冒充读正文。')
    for title,url in [
        ('重庆科技大学深度学习大纲','https://znxy.cqust.edu.cn/info/1155/5724.htm'),
        ('哈工深虚拟机实验指南','https://oslabs.hitsz.edu.cn/vm_env.html'),
        ('中国科大Ubuntu实验环境','https://soc.ustc.edu.cn/CECS/lab0/ubuntu/'),
        ('PyTorch官方文档','https://docs.pytorch.org/docs/2.14/'),
        ('VirtualBox官方命令参考','https://docs.oracle.com/en/virtualization/virtualbox/7.2/user/vboxmanage.html')]:
        story.append(Paragraph(escape(title)+'：<link href="'+escape(url,quote=True)+'" color="#884b31">'+escape(url)+'</link>',styles['small']))
    h('还需要本人完成的材料与访问')
    p('正式视频尚缺本人录屏/讲解与至少2分钟真实AI协作素材，已提供6分40秒镜头脚本；三条完整Prompt链仍未认证。评审可访问仓库未公开/推送；第二设备、实体手机和真实Linux来宾等缺口以最终HANDOFF为准。')
    p('沿用原预指导：本人上传百度网盘目录或ZIP，核对分享链接、提取码和有效期，再在原入口提交并保存回执。硬截止为2026年11月18日15:00北京时间。未取得回执不写已提交；本轮产品/审查结论不等于赛事资格或整套材料通过。','small')

    stamp=datetime.now(timezone.utc).isoformat()
    def footer(canvas,doc):
        canvas.saveState();canvas.setStrokeColor(LINE);canvas.line(52,42,A4[0]-52,42)
        canvas.setFillColor(MUTED);canvas.setFont('CN',8)
        canvas.drawString(52,28,'AI实验环境管家 | 产品 '+args.product_head[:12])
        canvas.drawRightString(A4[0]-52,28,str(doc.page));canvas.restoreState()
    doc=SimpleDocTemplate(str(out),pagesize=A4,rightMargin=52,leftMargin=52,topMargin=47,bottomMargin=57,
        title='AI实验环境管家 - 课程能力版技术文档',author='项目开发记录',subject='Product HEAD '+args.product_head)
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    pdf=fitz.open(out)
    if len(pdf)>30:raise ValueError('Technical PDF exceeds 30 pages')
    page_records=[];count=len(pdf)
    poppler=shutil.which('pdftoppm')
    if poppler:
        subprocess.run([poppler,'-scale-to','1200','-png',str(out),str(qa/'page')],check=True,capture_output=True)
    for number,page_obj in enumerate(pdf,1):
        png=qa/('page-'+str(number).zfill(len(str(count)))+'.png')
        if not poppler:page_obj.get_pixmap(matrix=fitz.Matrix(1.4,1.4),alpha=False).save(png)
        text=page_obj.get_text()
        page_records.append(dict(page=number,text_characters=len(text),png=png.relative_to(ROOT).as_posix()))
    pdf.close()
    screenshots={str(p.resolve()):digest(p) for p in [args.desktop,args.mobile] if p}
    receipt=dict(created_at=stamp,product_head=args.product_head,
        document_build_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        source_sha256=source_hashes,screenshots_sha256=screenshots,image_records=image_records,output=out.relative_to(ROOT).as_posix(),
        output_sha256=digest(out),pages=count,bytes=out.stat().st_size,font_source=font,
        unit_tests=args.unit_tests,browser_summary=args.browser_summary,review_status=args.review_status,
        renderer='Existing Poppler pdftoppm' if poppler else 'Existing PyMuPDF fallback; no installation',page_records=page_records,
        visual_review='pending PNG inspection; generation alone is not final QA')
    (qa/'technical-pdf-build.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(output=str(out),pages=count,bytes=out.stat().st_size,png_folder=str(qa)),ensure_ascii=False))


if __name__=='__main__':main()
