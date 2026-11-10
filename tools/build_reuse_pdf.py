"""Create the new technical document from the frozen, independently reviewed product."""
from datetime import datetime,timezone
from html import escape
import json
from pathlib import Path
import shutil
import subprocess
import fitz
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate,Paragraph,Table,TableStyle,Spacer,PageBreak,Image
from .build_technical_pdf import ROOT,WIDTH,INK,MUTED,ACCENT,PALE,LINE,font_setup,check_product,digest,Pipeline

def main():
    frozen=json.loads((ROOT/'records/review/reuse-ai-final-candidate.json').read_text(encoding='utf-8'))
    head=frozen['product_head'];check_product(head)
    for name,value in frozen['source_sha256'].items():assert digest(ROOT/name)==value
    review=ROOT/'records/review/reuse-ai-independent-product.md'
    if not review.is_file():raise ValueError('Independent fixed-product review required before final PDF')
    closure=json.loads((ROOT/'records/review/reuse-ai-review-closure.json').read_text(encoding='utf-8'))
    if closure['product_head']!=head or closure['blocking_findings']!=0:raise ValueError('Independent delta closure required')
    font=font_setup();qa=ROOT/'records/reuse-ai/pdf';qa.mkdir(parents=True,exist_ok=True)
    out=ROOT/'output/pdf/AI实验环境管家_开源AI_Agent版_技术文档.pdf';out.parent.mkdir(parents=True,exist_ok=True)
    styles={name:ParagraphStyle(name,fontName='CN',fontSize=size,leading=leading,textColor=color,spaceAfter=9,wordWrap='CJK')
            for name,size,leading,color in [('body',10.3,17,INK),('small',8.5,13,MUTED),('title',27,38,INK),('h1',20,29,INK),('h2',12.5,21,ACCENT),('cell',9.1,14,INK),('code',8.5,13,INK)]}
    story=[];images=[]
    def para(text,kind='body'):return Paragraph(escape(text).replace('\n','<br/>'),styles[kind])
    def p(text,kind='body'):story.append(para(text,kind))
    def h(text):p(text,'h2')
    def page(title):
        if story:story.append(PageBreak())
        p(title,'h1')
    def table(headers,rows,widths):
        t=Table([[para(str(c),'cell') for c in row] for row in [headers]+rows],colWidths=widths,repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),PALE),('LINEBELOW',(0,0),(-1,0),1,ACCENT),('LINEBELOW',(0,1),(-1,-1),.4,LINE),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8)]))
        story.extend([t,Spacer(1,10)])
    def link(title,url):story.append(Paragraph(escape(title)+'：<link href="'+escape(url,quote=True)+'" color="#884b31">'+escape(url)+'</link>',styles['small']))

    p('AI 实验环境管家','title');p('开源适配与 AI / Agent 课程能力版','h2')
    p('面向计算机与大数据专业实验课，把“应该准备什么”与“当前目标确实能运行什么”连接起来。学生从学习目标进入，教师发布固定任务；双方使用同一要求、证据、差异指导与复检。')
    story.append(Pipeline(['确定课程\n固定快照','选择目标\n实际采集','处理差异\n本人操作','同目标复检\n核对成果']))
    table(['本版新增','实际落实'],[
        ['Notebook数据分析','显式Python和已有内核，真实内核身份、NumPy/Pandas及固定数据计算。'],
        ['AI使用 / API','DeepSeek网页本人练习；独立API编程课，完整发送预览与终端单次同意。'],
        ['DeepSeek Harness','桌面与CLI分开；软件、运行时、工作区、模型、权限、工具与产物逐层核对。'],
        ['Java / SQLite','同源JDK固定编译运行；显式SQLite文件只读固定SELECT。'],
        ['教学动作二次开发','Educates两模板移植，固定报告检查衔接本人手动重采。'],
        ['原有六类课程','Python、Node、固定Qwen、PyTorch CPU/GPU、VM/Linux保留兼容。']],[104,WIDTH-104])
    p('产品 HEAD：'+head,'code')
    p('分支 codex/reuse-ai-courses-20261109；从 e0aca9ca04f350c5db0e3d6f197307260eee6276 完整克隆。材料/交付HEAD可较晚，产品与复用文件SHA须保持同一冻结版本。上游核对与首轮实测为2026-11-09，独立审查修复和集中复检为2026-11-10。','small')

    page('要求、目标与证据共用一条契约')
    p('每个任务只接受已审查的固定字段和程序，快照摘要绑定课程内容。采集由本人在目标电脑手动启动，网页只分析报告。工具自带运行时与课程环境各有身份。')
    table(['阶段','实现与验收'],[
        ['创建与传递','rules.task / validate_task 固定13类演示任务；CourseStore发布不可变快照；portable课程包携带相同摘要与离线指导。'],
        ['选择与采集','collect分派固定采集器，明确解释器/内核/JDK/数据库/DSH组件。不会导入任意SQL、Notebook或命令执行。'],
        ['四状态','pass / missing / mismatch / unknown分别为通过、缺失、不符合、未知。必须全部检查通过才得总体通过。'],
        ['指导与操作','新手、标准、快捷调整说明密度，保持要求和事实一致；按具体差异给本人操作与验证方法。'],
        ['复检','任务摘要、相关组件身份和时间顺序均核对。稳定通过、补齐证据、真实修复分别记录。'],
        ['清理与分享','任务/目标变更、无效新报告、异步旧响应不能恢复旧成功；分享先基础脱敏并允许本人编辑。']],[86,WIDTH-86])
    h('教师与学生如何使用')
    p('教师固定课程和版本后发布课程码，或导出任务包及离线指导。学生确认要求、解压下载工具、明确目标后生成可审查命令，运行得到A；按差异手动处理，再采集较晚B。课程包保证内容一致，不是教师数字签名；localhost入口只在本机可达。')
    h('AI在流程中的位置')
    p('原“AI解释报错”仍只解释已有证据。新增AI使用/API/DSH是独立课程，不借诊断接口冒充课程支持；教程确认、本人声明和模型自称完成都不能覆盖确定性规则。')

    page('Notebook：真正启动所选内核')
    p('选择课程Python与已有kernel.json，核对定义的argv及摘要，只接受同一解释器的固定ipykernel入口。采集器在专用临时配置中重建受控内核定义，启动真实内核，绑定本机连接并执行已审查的固定数据单元。')
    table(['事实','本轮本机真实结果'],[
        ['目标与内核','D:\\ANACONDA\\python.exe；已有base kernelspec；内核sys.executable与所选Python一致，Python3.13.9。'],
        ['依赖与运算','jupyter_client8.6.3、ipykernel6.30.1、NumPy2.3.4、Pandas3.0.3；数组和42，CSV分组A=30、B=12，共3行。'],
        ['报告与复检','10项检查通过，A/B stable-pass。分别保留所选/实际内核、解释器、依赖路径/版本、输出、时间与清理状态。'],
        ['失败证据','选错内核静态拒绝；明确缺失目标；已存在pytorch解释器的专用构造kernelspec真实启动后Pandas缺失。该负例不冒充已注册内核实测。'],
        ['退出边界','只关闭此次创建的内核/通道；超时仅终止本次probe进程树。不运行本人任意Notebook，不启动公网Notebook服务。']],[88,WIDTH-88])
    h('固定数据与可复现入口')
    p('原创演示CSV随下载工具提供：category,score / A,10 / A,20 / B,12。任务固化数据摘要与固定程序，不依赖外部数据集。下载工具经过实际命令执行、A/B网页导入、教师跨库传递和390px布局验证。')
    p('证据：records/reuse-ai/notebook/；最终网页与真实A/B见最终冻结清单列出的browser-data目录。各课程20261109T082430131236Z为首轮最终模块实测，修复后已重新下载工具执行。','small')

    page('Java 与 SQLite：课程成果能被核对')
    h('Java / JDK固定编译运行')
    p('用户选择JDK目录；只用该目录bin/java.exe和javac.exe，分别保存二进制摘要、版本及实际java.home，不借PATH中的其他工具。清理注入式Java环境选项，在专用临时目录以-proc:none编译原创固定源码，再用同一java运行产物。')
    p('本机Zulu JDK21.0.1，java/javac同源；固定数组10、20、12输出42及所选java.home。6项检查真实A/B稳定通过。版本/二进制/home变化须重新初检；临时源码和产物只属于本次验证。')
    h('SQLite单机SQL入门')
    p('本人显式创建一个尚不存在的演示文件，或选择明确文件。采集不会创建数据库；仅支持无WAL/SHM/journal侧文件的独立rollback-journal数据库。固定表结构和数据明确，连接mode=ro并设置query_only、trusted_schema关闭、固定函数与执行步数限制。')
    p('固定SELECT category, COUNT(*), SUM(score) FROM scores GROUP BY category ORDER BY category；期望A/2/30、B/1/12。本机SQLite3.50.2，5项检查真实A/B通过；采集前后文件SHA相同。复检绑定文件内容与工具SQLite运行时。')
    table(['课程边界','当前范围'],[
        ['服务器数据库','SQLite通过只证明单机任务。MySQL/PostgreSQL另需明确实例、只读身份、连接与固定查询；本轮未实现。'],
        ['Hadoop组合路线','来源固定Apache3.5.0指南，逐项要求Linux来宾、来宾Java、SSH、安装/配置、集群与固定作业身份。服务端要求JDK17；本机Windows JDK21课通过不能替代。'],
        ['现有外部缺口','无已验证Linux来宾、SSH及Hadoop集群；没有格式化、启动daemon或运行集群作业。']],[100,WIDTH-100])
    p('证据：records/reuse-ai/java/、sqlite/；组合来源见docs/Hadoop与框架组合路线-20261109.md。','small')

    page('AI网页使用与 DeepSeek API 编程')
    h('网页/客户端课程有可完成的练习')
    p('从官方DeepSeek入口，由本人登录并提问。固定上下文为score列10、14、18，要求JSON total=42、count=3、mean=14；本人独立复算并填写必要学习记录。成果数字可自动核对，完成记录明确标为本人提供，登录和远端连接始终保留未知。Qwen Chat、豆包仅提供官方指导路线。')
    h('独立API课与发送过程')
    p('显式选择Python3.10至3.15以下，验证urllib.request/ssl/json标准库。固定官方目的地 https://api.deepseek.com/chat/completions，模型deepseek-flash，非流式Chat Completions、thinking disabled、max_tokens128与JSON对象输出。模型名来自2026-11-09官方文档核对。')
    p('页面展示实际目的地、模型、系统说明及完整内容，允许编辑后保存预览；默认命令只预检。本人选择发送后，在终端再次看到完整请求，须键入SEND加该预览摘要，再getpass输入本次密钥。可能产生费用；本轮没有取得发送同意，因此实际API调用为0。')
    table(['处理','确定性行为'],[
        ['保密与资源','不读旧密钥/DSH凭据；密钥不进命令、报告或分享。已知密钥出现在预览则拒绝发送与保存报告；响应正文及元字段脱敏。无重试、无重定向，25秒和64KiB边界。'],
        ['失败分型','未配置、未调用、依赖缺失、认证/余额、模型/协议、限流、服务、超时、网络与运行异常。'],
        ['通过条件','核对内容类型、长度、唯一JSON字段、固定模型/assistant/stop及课程数字；HTTP200、配置存在或任意回答均不能单独通过。'],
        ['真实与测试','协议模拟和失败路径有测试；下载工具本机A/B仅预检通过环境项，调用/结果未知。固定Qwen离线路线保持独立。']],[82,WIDTH-82])

    page('DeepSeek Harness：具体工具的独立课程')
    p('固定官方上游 fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159，课程支持版本0.2.2-rc.1。已阅读CLI包/参数/启动分派、桌面README、安全说明与provider指南。采集采用静态元数据，不运行DSH版本入口、不运行npx、不扫描凭据。')
    table(['路线','独立判断'],[
        ['Windows桌面','明确选择exe，读PE ProductName/ProductVersion及摘要；桌面使用自带Electron运行时。外部Node缺失或PATH中无dsh不作桌面失败。'],
        ['npm/CLI/Web','明确选择Node、@deepseek-ai/dsh package.json及lib/bin.js，核对版本/包摘要/入口摘要和Node>=24.9.0关联身份。只执行所选Node的固定身份表达式。'],
        ['本机观察','所选Node24.21满足引擎；明确包路径缺失、一个桌面候选路径缺失。不是全机未安装结论。模型、权限与Agent任务均没有真实证据。']],[96,WIDTH-96])
    h('固定Agent练习可操作、可验证')
    p('显式准备一个新专用目录：task marker、固定input.csv和说明。本人启动并授权DSH，仅允许read input.csv、write summary.json，期望count=3、sum=42。产物在本机核对；必要摘要只包含公开目标/组件身份、权限、读写工具/时间与结果，不导出无关聊天或隐藏推理。')
    p('摘要模板初始未完成，不能直接通过；从本次预检可生成绑定身份模板。报告分软件、Node、工作区、模型、权限、工具与产物；普通聊天或版本号不能证明Agent任务完成。构造source=protocol-simulation不会被当作真实任务。本人摘要属于协作证据，不是密码学远程证明。')
    p('A/B复检要求同路线、程序/包/入口、运行时、模型、工作区标识和输入摘要，以及更晚的实际Agent任务。替换任一组件须重新初检。证据：records/reuse-ai/dsh/与browser-ai最终四路线。','small')

    page('开源适配：采用范围能追到具体文件')
    h('实际采用 Educates 两个教学动作模板')
    p('上游固定 d7e018f0cee382a595d2c9ecc6c938da099eb67e。采用examiner-execute-test.html（879字节）与clickable-action.html（1424字节）的字段和展示结构；不是仅加外链或复制原文件。')
    story.append(Pipeline(['原模板\n字段与结构','teaching.py\n固定检查映射','网页教学步骤\n标题/正文/状态','本人重采B\n新报告复检']))
    table(['保留与修改','具体落点'],[
        ['保留','name/title/description/cooldown默认3秒；clickable-action的header/title/body组织。页面实际渲染适配结构，绑定当前报告。'],
        ['替换','原Hugo/inline动作注册与后端脚本spawn被封闭检查ID和导入报告的确定性checks替代；本人按钮只切到B并聚焦命令准备。'],
        ['约束','不接受shell、args、autostart、无限重试或任意检查。外部JS事件、3秒冷却与键盘可操作；不会替本人运行命令。'],
        ['许可','Apache-2.0，Copyright The Educates Authors；原LICENSE/NOTICE、采用文件、manifest和修改说明随包保留，适配模块及页面注明来源。']],[82,WIDTH-82])
    h('其余候选据用途和条款取舍')
    p('Pinokio仅参考准备思路，任意脚本/下载执行模式不采用；Labtainers依赖Linux/Docker且分组件许可，TLJH为教师集中Notebook路线，本轮不部署。Open WebUI与Dify各有附加品牌/多租户条款，本轮无其产品代码。DSH是独立学习工具，本项目自行实现元数据与证据接缝，MIT原文和源码仅审查留档。')
    p('22项官方原件已核字节大小，其中9项另核Git blob，包括采用模板/LICENSE/NOTICE。来源和当前候选提交见docs/开源选型与二次开发-20261109.md、reuse.json与THIRD_PARTY_NOTICES；审查留档不计为可执行复用。','small')

    page('验证结果与能支持的结论')
    table(['层次','本轮证据与范围'],[
        ['单元/协议',str(frozen['unit_tests'])+'项通过；覆盖封闭快照、身份、固定结果、异常/失败、同意与脱敏、教学动作拒绝任意参数。'],
        ['浏览器','5套52组通过且产品源SHA匹配：原Python/Qwen网页10、Node9、Torch/VM9、新数据三课18、新AI/DSH6；另3项异步/身份构造回归。'],
        ['真实本机执行','下载工具/实际生成命令；Python、Node、Notebook、JDK、SQLite；PyTorch CPU与显式GPU；正确model-venv的固定Qwen离线推理。'],
        ['未取得的真实条件','DeepSeek API发送/鉴权/响应；真实DSH安装/模型/Agent任务；Linux来宾/SSH/Hadoop集群；第二设备与实体手机。'],
        ['构造与协作','错目标/无效报告/竞态/API假响应/DSH摘要是明确标注的构造或协议证据。网页本人记录与DSH最小摘要不会升级为独立远程真实性证明。'],
        ['独立审查','初审2项P2和1项P3已修复，固定新HEAD/SHA后独立delta复核闭合；初审与delta全文并存。结论范围不自动扩为赛事资格或实际提交。']],[86,WIDTH-86])
    h('首次失败保留并可解释')
    p('实现前ImportError、API针对断言、来源manifest首次关联错误、浏览器脚本未展开面板及集成旧预期均保留原记录，再保存修正后的结果。Qwen误选pytorch解释器真实缺transformers；后明确选择既有model-venv取得新推理证据，没有安装依赖或改写首次失败。')
    p('冻结清单 records/review/reuse-ai-final-candidate.json 记录当前源码、复用材料与证据摘要；初审清单保留。JDK退出证据、API缺依赖及Java运行超时归类的三项发现有red/green与独立delta，不覆盖原报告。','small')

    page('界面：把下一步与事实放在一起')
    p('沿用现有课程工作台：课程入口与教师任务并列，准备步骤、采集与报告依次展开。Notebook/API/DSH只显示适用字段；状态列表有中文名称和事实详情。变更内核、工作区、模型等即撤销旧报告与同意。')
    src=next(ROOT/name for name in frozen['browser_records'] if '/browser-data/' in name).parent
    from PIL import Image as PILImage
    desktop=src/'notebook-data-desktop.png';cropped=qa/'notebook-desktop-detail.png'
    with PILImage.open(desktop) as im:im.crop((460,0,1330,540)).save(cropped)
    mobile=src/'notebook-data-mobile-390.png'
    images.extend([dict(source=desktop.relative_to(ROOT).as_posix(),sha256=digest(desktop),crop=[460,0,1330,540]),dict(source=mobile.relative_to(ROOT).as_posix(),sha256=digest(mobile),crop=None)])
    t=Table([[Image(str(cropped),width=310,height=310*540/870),Image(str(mobile),width=145,height=145*844/390)]],colWidths=[WIDTH-155,155])
    t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0)]));story.append(t)
    p('图：同一Notebook真实A/B的桌面局部与390px模拟视口。原图保留在最终browser-data目录；390px来自桌面Edge模拟，不声称实体手机或另一设备验收。','small')
    h('操作与无障碍验证')
    p('使用原生表单/按钮，检查Tab、Enter触发及焦点。教学重试只引导手动生成较晚B；三种模式保持同一检查事实。所有浏览器记录页面错误与外部请求，当前回归未产生外部模型请求。')

    page('复现、来源与正式提交状态')
    h('已有Python时，直接启动新交付目录')
    p("Set-Location -LiteralPath 'D:\\传智杯\\versions\\competition-reuse-ai-20261109'\n& 'D:\\ANACONDA\\python.exe' -B -m campuslab.web `\n  --port 8781 --database '.\\data\\reuse-ai-courses.sqlite' `\n  --runtime-zip '.\\vendor\\python-3.13.17-embed-amd64.zip'",'code')
    p('访问http://127.0.0.1:8781/；Ctrl+C仅停止本人新启动的服务。使用新独立课程库，端口冲突时换空闲端口，不结束旧服务。无需.ps1或执行策略修改。已有官方嵌入ZIP随本机审阅包提供；课程软件与模型另由本人既有环境满足。')
    h('主要官方来源（固定核对记录另随包）')
    for title,url in [('Educates固定来源','https://github.com/educates/educates-training-platform/tree/d7e018f0cee382a595d2c9ecc6c938da099eb67e'),('DeepSeek API协议','https://api-docs.deepseek.com/api/create-chat-completion/'),('DSH固定来源','https://github.com/deepseek-ai/deepseek-harness/tree/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159'),('Hadoop3.5.0组合指南','https://hadoop.apache.org/docs/r3.5.0/hadoop-project-dist/hadoop-common/SingleCluster.html')]:link(title,url)
    h('交付与仍需本人完成的最少事项')
    p('新目录保留完整Git历史；最终HEAD、运行时、完整交付SHA、ZIP内容/CRC和启动烟测由新回执固定。原R1、Node、课程版及旧PDF/ZIP保持原字节。本包含原始设备路径/开发证据，供本人本机审阅；公开或上传前核对隐私。')
    p('正式5-8分钟1080p视频、至少2分钟真实AI协作录屏、至少三条完整Prompt核心链认证、评审仓库可访问方案与上传回执仍待本人完成。本轮提供新脚本和真实可见消息索引，不虚构用户Bug反馈或补造对话。')
    p('本人上传百度网盘目录/ZIP，核对链接、提取码与有效期，再在原入口提交保存回执。硬截止2026年11月18日15:00北京时间；尚未取得实际提交或资格确认。','small')

    def footer(c,doc):
        c.saveState();c.setStrokeColor(LINE);c.line(52,42,A4[0]-52,42);c.setFillColor(MUTED);c.setFont('CN',8)
        c.drawString(52,28,'AI实验环境管家 | 产品 '+head[:12]);c.drawRightString(A4[0]-52,28,str(doc.page));c.restoreState()
    SimpleDocTemplate(str(out),pagesize=A4,leftMargin=52,rightMargin=52,topMargin=47,bottomMargin=57,title='AI实验环境管家 - 开源AI Agent版技术文档',author='项目开发记录',subject='Product HEAD '+head).build(story,onFirstPage=footer,onLaterPages=footer)
    pdf=fitz.open(out);assert 1<=len(pdf)<=30;pages=[]
    poppler=shutil.which('pdftoppm')
    if poppler:subprocess.run([poppler,'-scale-to','1200','-png',str(out),str(qa/'page')],check=True,capture_output=True)
    for n,page_obj in enumerate(pdf,1):
        png=qa/('page-'+str(n).zfill(len(str(len(pdf))))+'.png')
        if not poppler:page_obj.get_pixmap(matrix=fitz.Matrix(1.4,1.4),alpha=False).save(png)
        pages.append(dict(page=n,png=png.relative_to(ROOT).as_posix(),sha256=digest(png),text_characters=len(page_obj.get_text())))
    data=dict(created_at=datetime.now(timezone.utc).isoformat(),product_head=head,source_sha256=frozen['source_sha256'],output=out.relative_to(ROOT).as_posix(),output_sha256=digest(out),pages=len(pdf),page_records=pages,screenshots=images,font=font,renderer='Existing Poppler' if poppler else 'Existing PyMuPDF; no installation',visual_review='pending all-page image inspection',independent_review_sha256=digest(review),delta_sha256=digest(ROOT/'records/review/reuse-ai-independent-delta.md'))
    (qa/'technical-pdf-build.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(dict(pages=len(pdf),output=str(out)),ensure_ascii=False))
if __name__=='__main__':main()
