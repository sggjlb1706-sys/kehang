"""Guidance varies detail; acceptance always belongs to rules.py."""
from .rules import validate_task


def plan(spec, mode='novice', resources=None, report=None, prepared='unsure'):
    validate_task(spec)
    if mode not in ('novice','standard','quick'):
        raise ValueError('指导模式无效')
    if prepared not in ('unsure', 'missing', 'installed'):
        raise ValueError('准备说明无效')
    from .rules import NEW_COURSES
    if spec['scenario'] in NEW_COURSES:
        result = learning_plan(spec,mode,report)
        if spec['scenario'] in ('deepseek-api','dsh-desktop','dsh-cli'):
            result['contextual'] = contextual_guidance(spec, report, prepared)
        return result
    if spec['scenario'] in ('pytorch-cpu','pytorch-gpu','vm-linux'):
        return course_plan(spec,mode,report)
    local = spec['scenario'] == 'local-qwen'
    if spec['scenario'] != 'node-basics':
        steps = [
            ('确认这次课程要求', f"目标是Windows与Python {spec['python']['min']}至{spec['python']['max_exclusive']}（不包含上限）。Python是运行程序的环境，编辑器不是解释器。"),
            ('准备目标电脑上的课程环境', '已安装时先找到所用python.exe；可在PowerShell手动运行 py -0p 查询。没有py启动器时，到安装目录或编辑器的解释器设置查看完整路径。未安装时从官方渠道选择课程允许的版本。'),
            ('完整解压工具，填写两个不同的路径', '工具目录是下载文件解压后的目录；目标解释器是课程要使用的python.exe。下载包内的runtime只负责检测，不能作为课程已经安装的证据。'),
            ('手动采集并导入初检报告', '复制下方命令到目标电脑的PowerShell，自行确认后运行。命令只读取环境并写出报告。导入report-A.json后查看缺失、不符合和未知。'),
            ('按差异自行处理，再采集复检报告', '如需安装或修复，由本人逐项决定。复检保持同一课程快照、同一个解释器路径。更换环境时重新开始初检。'),
            ('查看实际运行结果，脱敏后分享', '只有完整检查通过才显示通过。分享前在预览中删除个人目录或无关日志；脱敏报告用于交流，原始报告留在本人电脑。')
        ]
        links=[dict(title='Python 官方下载（选择符合本课程范围的版本）',url='https://www.python.org/downloads/windows/'),
               dict(title='Windows 安装操作参考（文档版本不代表课程要求）',url='https://docs.python.org/3/using/windows.html')]
    recommendation = None
    if spec['scenario'] == 'node-basics':
        steps = [
            ('确认这次示例课程要求', f"这是演示配置，非真实学校课程：Windows、Node.js {spec['node']['min']}至{spec['node']['max_exclusive']}、npm {spec['npm']['min']}至{spec['npm']['max_exclusive']}，均不包含上限。Node.js负责运行JavaScript，npm是包管理工具。"),
            ('明确选择课程使用的 Node.js', '已安装时从安装目录找到所选node.exe完整路径。可以手动运行 Get-Command node -All 查看候选，但PATH中的第一个结果不一定是本次课程环境。未安装时按固定范围从官方渠道自行准备；网页不会安装。'),
            ('完整解压检测工具，区分工具与课程环境', '工具包的runtime是用于采集的Python，不是课程Node.js。填写解压目录和明确选择的node.exe；npm固定取该目录的node_modules/npm/bin/npm-cli.js，由该node.exe执行，不借用PATH中其他npm。'),
            ('手动采集并导入初检报告', '检查下方生成的PowerShell命令，再由本人运行。只检测所选Node.js、关联npm和固定最小程序，记录实际路径、版本、时间及错误。导入report-A.json后查看四种状态；证据不完整不会全部通过。'),
            ('自行处理差异，同一任务和目标复检', '缺失或版本不符合时，由本人决定修复，不自动执行建议。复检使用同一任务快照和同一node.exe路径，保存较晚的report-B.json。若更换Node.js环境，重新开始初检。'),
            ('核对运行证据，脱敏后分享', '固定Node.js程序和关联npm均符合要求，完整证据才通过。先预览并编辑脱敏交流副本；原始A/B报告留在本人电脑，分享副本不能替代复检报告。')
        ]
        links=[dict(title='Node.js 官方下载（自行选择符合演示范围的版本）',url='https://nodejs.org/en/download'),
               dict(title='npm CLI 官方说明（工具不会运行安装命令）',url='https://docs.npmjs.com/cli/')]
    if local:
        steps.insert(2,('准备固定的本地模型实验', '本任务使用Qwen2.5-0.5B-Instruct的固定权重。先准备课程要求的torch、transformers和本地模型目录；页面不自动下载或安装。先采集预检查，再主动勾选执行固定离线推理。'))
        links.extend([dict(title='课程指定模型与文件来源',url='https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct'),dict(title='PyTorch 官方安装说明（按电脑和课程选择）',url='https://pytorch.org/get-started/locally/')])
        resources = resources if isinstance(resources,dict) else {}
        ram=resources.get('ram_bytes')
        if type(ram) is not int or ram<=0:
            recommendation='尚无有效内存证据，不能判断适合程度。先预检查，再决定是否尝试本地运行。'
        elif ram<4*1024**3:
            recommendation='检测内存小于4GiB，建议先向老师确认替代方案。当前任务要求本地运行，云端结果不能替代本课程验收。'
        else:
            recommendation='已取得内存证据，可尝试本任务固定0.5B模型；显卡未知时可走CPU，最终能否运行以实际推理为准。'
        recommendation+=' 本任务不以GPU缺失直接判失败；4GiB是本演示的操作提示，不能保证性能。'
    if spec['scenario']=='python-basics':
        steps[1]=('选择课程 Python，不必先记完整路径','若下载包带Start-Collect.cmd，双击后按回车列出已登记的Python，再输入编号；未找到可按F浏览python.exe或输入?查看开始菜单/Anaconda查找方法。候选尚未检测，选择后仍需确认START。未安装时先从官方准备课程允许的版本。')
        steps[2]=('完整解压检测工具','不要在ZIP中直接运行。带Start-Collect.cmd时可使用编号选择；不带该入口时，使用网页手动采集入口。包内runtime仅负责检测，不能作为课程Python。')
        steps[3]=('主动采集并带回初检报告','核对固定任务、所选Python和报告阶段A后，输入START才开始固定采集。使用手动入口时由本人检查并运行命令。导入report-A.json后查看缺失、不符合和未知。')
    if mode == 'standard':
        steps=[steps[0],steps[2],steps[-3],steps[-2],steps[-1]]
    elif mode == 'quick':
        steps=[('确认固定目标与要求',steps[0][1]),('采集、处理、同目标复检','使用下方手动命令，导入原始A/B。规则结果与其他模式相同。')]
    result=dict(mode=mode,steps=[dict(title=a,body=b) for a,b in steps],links=links,recommendation=recommendation)
    if local:
        result['preparation']=[
            '先手动运行硬件预检；内存、磁盘或显卡未知时先补证据。工具Python与课程Python分别选择。',
            '在明确选定的课程Python中按PyTorch官方安装选择器准备torch>=2.2及transformers>=4.45；不向其他环境安装。',
            '模型：'+spec['model']['name']+'；固定revision '+spec['model']['revision']+'；手动从官方文件页取得该revision，权重SHA256须为 '+spec['model']['weights_sha256']+'。',
            '选择真实模型目录，先采集预检查。权重/依赖齐备后主动勾选固定离线推理，再采集B；输出2和EOS必须来自当前本地目标。']
    result['remediation']=remediation(spec,report,mode)
    return result


def ps_literal(value):
    return '"'+''.join('`'+c if c in '`"$‘’‚‛“”„‟' else c for c in value)+'"'


def learning_plan(spec,mode,report):
    scenario=spec['scenario']
    from .ai_course import QUESTION, SOURCES
    if scenario=='notebook-data':
        steps=[('选择真正的课程内核','在Jupyter内核设置确认课程Python。带Start-Collect.cmd的检测包可按回车列Python候选、按编号选择，再按F选择kernel.json；找内核目录时，在课程Python终端手动运行python -m jupyter kernelspec list。不带入口时使用网页手动命令。工具只接受明确ipykernel启动格式，不运行内核配置中的任意命令或环境变量。'),
               ('核对数据与依赖','所选Python需要已有jupyter_client、ipykernel、NumPy、Pandas。内核真正启动后读取sys.executable与依赖版本，执行随固定任务审查的小数据计算；找到包不表示内核已经运行。'),
               ('运行与处理差异','生成并运行手动命令。缺解释器、缺依赖、内核错配、版本不符、启动/计算失败分别看原始证据。工具只清理自己创建的临时内核，不操作已有会话。')]
        links=[dict(title='Jupyter kernelspec 官方说明',url='https://jupyter-client.readthedocs.io/en/stable/kernels.html')]
    elif scenario=='java-jdk':
        steps=[('明确JDK目录','填写JDK根目录，例如 C:\\Program Files\\Zulu\\zulu-21，里面应同时有bin/java.exe和bin/javac.exe。JRE或编辑器不等于JDK。'),
               ('核对同一套工具','采集器只用这份JDK中的java/javac，核对版本与运行身份，不从PATH借另一编译器。固定源码在自己新建的临时目录编译运行，不写入本人项目。'),
               ('定位失败','工具缺失先确认目录；版本不符按任务范围手动准备；编译或运行错误先展开原始退出码和输出。处理后同一JDK复检。')]
        links=[dict(title='Oracle JDK 工具文档',url='https://docs.oracle.com/en/java/javase/21/docs/specs/man/index.html')]
    elif scenario=='sqlite-basics':
        steps=[('准备独立演示数据库','这是SQLite单机SQL入门。明确数据库文件路径；点击生成样例命令后本人执行，prepare-demo只创建新文件并拒绝覆盖。不要选择私人数据库或将其当作MySQL/PostgreSQL实例。'),
               ('只读执行固定查询','采集器使用SQLite URI mode=ro，固定SELECT核对随任务的演示表和结果；不接受导入的任意SQL，不写数据，不加载扩展。'),
               ('核对数据库身份','报告记录完整路径与文件摘要；更换文件或内容后重新初检，不将旧成功套到新数据库。缺表、错误数据和查询失败保留不符合或未知。')]
        links=[dict(title='SQLite 只读URI官方说明',url='https://www.sqlite.org/uri.html')]
    elif scenario=='ai-web-deepseek':
        steps=[('本人打开官方入口','从DeepSeek官方网页或客户端下载入口进入，由本人按页面条件注册/登录；不要在本工具填写密码。账号和可用条件以官方当前页面为准。Qwen、豆包提供代表性指导路线，未接入其自动验证。'),
               ('完成一次课程提问','新建对话，说明数据分析课程目标，粘贴这份非个人演示CSV；也可将相同内容保存为CSV后本人上传到工具支持的文件入口。问题：'+QUESTION),
               ('独立核对成果','手算10+14+18=42，行数3，均值14。检查模型解释和引用，避免把流畅回答当作事实。若登录失败按官网提示处理；若文件功能不可用直接粘贴演示文本。'),
               ('保存必要本人记录','下载包内web-record.json只填写本次是否完成、是否独立核对及JSON结果，不附无关聊天。本人记录和固定数字核对分别显示；本工具没有登录/远端连接证据，因此环境结论仍未知。')]
        links=SOURCES
    elif scenario=='deepseek-api':
        steps=[('确认API编程路线','本任务使用所选Python>=3.10且<3.15的urllib/ssl/json标准库，无需新SDK；提供方DeepSeek，接口 '+spec['api']['endpoint']+'，模型 '+spec['api']['model']+'。这与网页使用、本地Qwen和产品报错解释接口分别验收。'),
               ('先做未调用预检','下载工具中的api-preview.json展示系统说明及真实用户内容，可编辑并删除敏感信息；生成命令默认只预检Python，不读任何凭据，不发API请求。'),
               ('本人决定单次调用','仅当本人确认账号、调用条件和可能费用后，勾选“本次进入单次发送确认”生成命令；终端再次显示完整目的地/模型/内容，要求键入SEND及摘要，随后隐藏输入本次密钥。密钥不进网页、命令、报告或分享。此页面勾选本身不发送。'),
               ('核对响应和复检','HTTP200还须模型/协议、正常结束和固定JSON计算分别符合。未配置、认证/余额、模型/协议、限流、超时、异常分别报告；未调用保持未知。更改模型、目的地、解释器或发送内容后重新初检。')]
        links=SOURCES[:2]+[dict(title='DeepSeek 错误码',url='https://api-docs.deepseek.com/quick_start/error_codes/')]
    else:
        desktop=scenario=='dsh-desktop'
        steps=[('确认DSH路线','本任务是DeepSeek Harness。'+('选择明确的Windows桌面exe，读取文件身份/版本；官方桌面自带运行时，无外部Node或PATH无dsh不作为桌面失败依据。' if desktop else '选择明确node.exe及@deepseek-ai/dsh的package.json；固定0.2.2-rc.1包要求Node>=24.9.0，旧Node演示课通过不能替代。只查固定Node身份，不运行DSH/npx。')),
               ('准备专用练习工作区','生成准备命令，由本人新建专用目录。练习仅允许读取input.csv、写summary.json，目标sum=42。填写明确提供方和模型。路径/权限不明确先停止；不会读取DSH凭据或完整配置。'),
               ('本人在DSH启动并授权','打开所选桌面或使用该Node与固定包入口，按官方provider指南本人配置模型，在专用工作区审查任务和工具权限后运行。只看配置、版本或普通聊天不能证明Agent任务完成。'),
               ('带回必要运行证据','按工作区任务说明保存最少工具调用摘要、运行时间和固定产物；不收集隐藏推理或无关对话。采集器分别核对软件/运行时/模型/权限/实际工具与产物；无真实任务证据仍未知。'),
               ('同一路线与组件复检','保持安装/运行时、provider/model及工作区身份；更换后重新初检。未安装、未连接、权限未明、任务失败都给出不同检查项，不能用另一份Node或产物凑通过。')]
        links=[dict(title='DSH 官方下载与预览说明',url='https://www.deepseek.com/harness/'),dict(title='DSH 官方provider指南',url='https://deepseek-harness.github.io/deepseek-harness/en/guide/providers')]
    full=steps
    if mode=='standard': steps=[steps[0],steps[-2],steps[-1]] if len(steps)>3 else steps
    if mode=='quick': steps=[steps[0],('固定练习与同目标复检','核对页面的可审查手动命令、原始错误及任务摘要。'+steps[-1][1])]
    actions=[]
    if report is not None:
        from .rules import analyze
        for c in analyze(spec,report)['checks']:
            if c['status']=='pass': continue
            specific = check_guidance(spec, c['id']) if scenario in ('deepseek-api','dsh-desktop','dsh-cli') else None
            actions.append(dict(id=c['id'],status=c['status'],title=(specific[0] if specific else c['id'])+' · '+{'missing':'缺失','mismatch':'不符合','unknown':'未知'}[c['status']],
                body=specific[1] if specific else '所选目标：'+report['target']['requested']+'。'+({'missing':'先确认组件路径并按任务要求手动准备。','mismatch':'展开本项原始事实与错误，核对固定要求后手动处理。','unknown':'先补充本项证据；其他组件或本人勾选不能替代。'}[c['status']]),
                verify=full[-1][1]+' 保留原A，采集较晚B；不同目标重新初检。'))
    return dict(mode=mode,steps=[dict(title=a,body=b) for a,b in steps],links=links,recommendation=None,remediation=actions)


def check_guidance(spec, key):
    """Explanations of existing fixed checks, never an alternate acceptance rule."""
    if spec['scenario'] == 'deepseek-api':
        messages = {
            'os': ('运行电脑', '在运行课航服务的Windows电脑检查；另一台电脑使用手动工具，不能共用环境结论。'),
            'python': ('课程Python', '先确认本课实际使用的Python及任务版本范围，再检测同一目标；准备API不要求安装DSH或本地模型。'),
            'api:dependency': ('API编程依赖', '只需本任务Python的urllib.request、ssl、json标准库。先展开导入错误，不据此要求另装SDK。'),
            'api:request': ('发送内容', '核对任务固定目的地、模型与演示数据。改变提供方、模型或问题后不能沿用原任务的成功结论。'),
            'api:protocol': ('实际API响应', '网页检测只做未调用预检。若决定实际调用，在手动工具中预览完整请求、确认费用并进行终端单次授权，密钥仅在终端隐藏输入；没有响应证据时保留未知。'),
            'api:exercise': ('数据练习结果', '实际调用后再核对total=42、count=3、mean=14及完整JSON。HTTP200、普通聊天和课航AI解释均不能代替本项。'),
        }
    else:
        desktop = spec['scenario'] == 'dsh-desktop'
        messages = {
            'os': ('运行电脑', '这份DSH任务面向Windows；静态程序检查和真实Agent任务证据分别核对。'),
            'dsh:software': ('DSH桌面程序' if desktop else 'DSH CLI包',
                ('核对所选桌面exe及相邻公开包元数据。桌面自带运行时，不要求系统Python或PATH中的dsh。' if desktop else '核对所选@deepseek-ai/dsh的package.json及固定入口元数据；网页不会执行包入口。') + ' 本任务固定版本为'+spec['software_version']+'，不表示官方最新版；版本不符先与课程要求核对。'),
            'dsh:node': ('CLI运行时', '确认本课所选Node满足'+str(spec['node_min'])+'及包要求。另一份Node或普通Node课程通过不能代替；桌面路线不要求本项。'),
            'dsh:workspace': ('专用练习目录', '先选择已有的本任务专用目录；没有时，在手动备用入口生成准备命令，由本人新建目录，已有文件不覆盖。固定任务只读input.csv、只写summary.json。'),
            'dsh:model': ('DSH任务的模型接入', '按所选DSH版本的官方模型配置指南，在DSH中由本人配置并选择提供方和模型。课航不读取密钥；未取得真实任务摘要时无法验证连接，不等于部署失败。课航右侧AI是另一套可选连接。'),
            'dsh:permission': ('本次工具授权', '在DSH运行前审查本次固定read/write权限：只读input.csv、只写summary.json。不扩大到其他文件；课航中的勾选不代表DSH已实际授权。'),
            'dsh:tools': ('Agent工具步骤', '在本人已选DSH及专用目录完成固定CSV任务，保留必要的读/写工具摘要、实际时间和错误。普通聊天、安装版本和静态检查均不能证明Agent已执行。'),
            'dsh:artifact': ('固定任务产物', '核对同一专用目录的summary.json：整数count=3、sum=42。内容不符先查看实际产物；产物单独正确也不证明是本次Agent生成。'),
        }
    return messages.get(key, ('课程证据', '展开本项真实证据与错误，按原任务要求处理；不以指导文本替代检测。'))


def contextual_guidance(spec, report, prepared):
    """Choose the current route and next step from the validated task/report."""
    from .rules import analyze
    api = spec['scenario'] == 'deepseek-api'
    desktop = spec['scenario'] == 'dsh-desktop'
    checks = analyze(spec, report)['checks'] if report is not None else []
    states = {item['id']: item['status'] for item in checks}
    declaration = {'unsure':'本人尚不确定准备情况', 'missing':'本人说明尚未准备', 'installed':'本人说明已经准备'}[prepared]
    if api:
        title, intro = '准备API编程与一次固定练习', '先检查Python与请求准备，再由本人决定是否实际调用DeepSeek API'
        requirements = [f"Python {spec['python']['min']} 至 {spec['python']['max_exclusive']}（不含上限），使用urllib / ssl / json标准库",
                        '本任务模型：'+spec['api']['model']+'；目的地：'+spec['api']['endpoint'],
                        '固定结果：total=42、count=3、mean=14；无需安装DSH或加载本地权重']
        boundary = '网页本机检测不发送API、不读取密钥；课航AI聊天配置与本课API调用分别管理'
        first = 'python'
        order = ['os','python','api:dependency','api:request','api:protocol','api:exercise']
        links = [dict(title='DeepSeek API官方入门',url='https://api-docs.deepseek.com/'), dict(title='官方错误码',url='https://api-docs.deepseek.com/quick_start/error_codes/')]
        selection_hint = '选择本课Python；此项只调整准备指引，不表示API已连接'
    else:
        title = '准备DSH桌面任务' if desktop else '准备DSH CLI任务'
        intro = '先确认当前工具，再分别核对工作区、模型、工具授权与固定产物'
        requirements = [('Windows桌面程序，自带运行时；系统Python或Node不是本路线前置条件' if desktop else '本课Node ≥ '+str(spec['node_min'])+'，以及@deepseek-ai/dsh的package.json'),
                        '本任务固定DSH版本：'+spec['software_version']+'（不是官方最新版本声明）',
                        '专用目录中的input.csv → summary.json，固定结果count=3、sum=42']
        boundary = '网页只读核对所选工具与可选目录；不启动DSH、不配置模型、不授予工具权限，也不代做Agent任务'
        first = 'dsh:software'
        order = ['os','dsh:node','dsh:software','dsh:workspace','dsh:model','dsh:permission','dsh:tools','dsh:artifact']
        links = [dict(title='DSH官方下载与说明',url='https://www.deepseek.com/harness/'), dict(title='官方模型配置指南',url='https://deepseek-harness.github.io/deepseek-harness/en/guide/providers')]
        selection_hint = '选择当前DSH路线的准备情况；安装声明不代表模型或任务已完成'
    if report is None:
        status = '尚无检测报告；'+declaration+'，不是已验证事实'
        if prepared == 'missing':
            next_title = '先准备本课Python' if api else ('先准备DSH桌面程序' if desktop else '先准备本课Node与DSH CLI包')
            next_body = check_guidance(spec, first)[1]
            if api:
                next_body += ' 尚未安装时，按任务版本范围从Python官方渠道自行准备。'
                links.append(dict(title='Python官方下载',url='https://www.python.org/downloads/windows/'))
        else:
            next_title = '先完成API编程预检' if api else ('先核对桌面程序身份' if desktop else '先核对Node与CLI包身份')
            next_body = '点击“选择目标并检测”，确认'+('本课Python；结果只说明准备检查，不说明API调用成功。' if api else '本路线程序或包；静态软件证据与后续Agent任务分别显示。')
    else:
        first_missing = next((key for key in order if states.get(key) not in (None, 'pass')), None)
        passed = [check_guidance(spec, item['id'])[0] for item in checks if item['status'] == 'pass' and item['id'] != 'os']
        status = '已有检测报告；已核对：'+('、'.join(passed) if passed else '暂无通过项')
        if first_missing:
            next_title, next_body = check_guidance(spec, first_missing)
        else:
            next_title, next_body = '保留原始结果，同目标复检', '本固定任务现有检查均通过。保留原A与实际产物；复检使用同一任务、目标及已确认组件，变更组件后重新初检。'
        if api:
            run = report['facts']['run']
            if not run['attempted']:
                status += '；没有实际API响应证据，不判断账号、密钥或服务是否可用'
            elif first_missing == 'api:protocol':
                reasons = {'authentication':'认证', 'balance':'余额', 'rate_limit':'限流', 'timeout':'超时', 'network':'网络', 'model_or_protocol':'模型或协议', 'protocol':'协议', 'server':'服务端', 'runtime':'运行时'}
                next_title = '核对本次调用的'+reasons.get(run['category'], '响应')+'问题'
                next_body = '这来自本次报告，不能与“未调用”混同。先查看原始状态码与错误，再由本人决定是否重试；重试仍要预览并单次确认。'
        elif report['facts']['agent'] is None:
            status += '；尚无真实DSH任务摘要，模型连接与Agent执行保留未知'
    return dict(title=title,intro=intro,requirements=requirements,status=status,
                next_title=next_title,next_body=next_body,boundary=boundary,links=links,selection_hint=selection_hint)


def remediation(spec,report,mode):
    if report is None:
        return []
    from .rules import analyze
    result=analyze(spec,report)
    target=report['target']['requested']
    actions=[]
    for check in result['checks']:
        status=check['status']; key=check['id']
        if status=='pass':
            continue
        intro={'missing':'未取得所需组件，请按课程要求手动准备。','mismatch':'已取得证据但不符合要求；先核对版本或运行错误。','unknown':'现有证据不足；先补充事实，不要直接重装。'}[status]
        if key.startswith('package:'):
            package=key.split(':',1)[1]
            extra='仅在所选解释器中操作：'+ps_literal(target)+'。'
            if package=='requests':
                extra+=' 可审查的PowerShell建议：& '+ps_literal(target)+' -m pip install '+ps_literal('requests>='+spec['packages']['requests'])+'。由本人决定是否运行。'
            else:
                extra+=' PyTorch按官方安装选择器核对CPU/CUDA构建；先确认课程版本和驱动兼容，再手动安装。'
        elif key in ('python','node'):
            extra='找到课程实际程序完整路径，核对任务显示的允许版本。若换目标，清除原报告并重新初检A。'
        elif key=='npm':
            extra='使用所选node.exe同目录的node_modules/npm/bin/npm-cli.js；不要用PATH中另一份npm凑齐。缺失时按Node官方安装说明手动修复该目录。'
        elif 'gpu' in key or 'cuda' in key:
            extra='分别核对框架CUDA构建、设备可用性及所选GPU UUID；课程要求GPU时主动勾选固定GPU运算，CPU通过不能替代。'
        elif key.startswith('model:'):
            extra='按固定revision和权重SHA核对模型目录；依赖与权重齐备后主动执行本地离线推理。缺少权重不会自动下载。'
        elif any(part in key for part in ('guest','instance','vm','host','virtual')):
            extra='分别核对宿主、软件及实例身份；在本人已启动的所选Linux来宾中手动运行绑定采集器并导入来宾原始JSON。无法取得来宾时保持未知。'
        else:
            extra='展开本项原始证据查看错误。在同一目标重跑固定采集器；建议已阅读不会改变检查状态。'
        actions.append(dict(id=key,status=status,title=key+' · '+{'missing':'缺失','mismatch':'不符合','unknown':'未知'}[status],
            body=(intro+' '+extra if mode=='novice' else extra),verify='保持同一任务与所有已确认组件身份，采集较晚的B报告；更换环境则重新初检。'))
    return actions


def course_plan(spec,mode,report):
    vm=spec['scenario']=='vm-linux'
    if vm:
        steps=[('确认分层要求','宿主虚拟化、所选VirtualBox或VMware、具体实例和Linux来宾分别验证。软件已安装不代表实例或课程实验通过。'),
            ('选择软件和实例','填写VBoxManage.exe或vmrun.exe绝对路径；实例填VirtualBox UUID或VMware .vmx绝对路径。未知实例先查看虚拟化软件界面，工具不会创建或启动。'),
            ('准备来宾证据','在已由本人启动的Linux来宾复制guest_probe.py和同一task.json；手动运行 python3 guest_probe.py --help 查看绑定参数。将输出JSON带回宿主，采集时填写其路径；没有来宾证据保持未知。'),
            ('手动采集初检','完整解压工具并检查生成的PowerShell命令。固定只读命令核对软件与所选实例；没有证据的层不能由其他层代替。'),
            ('按差异复检','宿主、软件、实例及已知来宾身份须相同，B时间晚于A；换虚拟机重新开始。Linux基础固定验证不代表完成其他课程作业。'),
            ('传递与求助','下载课程包与离线指导，在另一实例导入同一摘要；诊断和分享先预览脱敏，步骤勾选不改变状态。')]
        links=[dict(title='VirtualBox 官方手册',url='https://www.virtualbox.org/manual/ch08.html'),dict(title='哈工深虚拟机实验参考（其版本仅适用于原课程）',url='https://oslabs.hitsz.edu.cn/vm_env.html')]
    else:
        gpu=spec['scenario']=='pytorch-gpu'
        steps=[('确认课程与运行设备','本演示明确选择Python与PyTorch环境；固定CPU张量必须运行。'+('本任务另外要求CUDA构建、GPU可用性与实际GPU张量运算。' if gpu else '本CPU任务不要求GPU通过。')),
            ('选择课程解释器','编辑器只是入口；在编辑器或Notebook手动查看 import sys; print(sys.executable)，把实际python.exe填入。Notebook内核关联未自动验证，请核对同一路径。'),
            ('按所选目标准备框架','从PyTorch官方安装选择器选择符合本任务版本的CPU/CUDA构建。安装建议只供本人审查，工具不安装。不能把另一个环境的torch当作当前目标。'),
            ('手动运行固定张量检查','完整解压工具，填写课程Python。CPU计算由固定探测器执行；GPU课程须主动勾选实际GPU运算，采集框架、可用性、设备UUID与运算结果。'),
            ('处理差异并复检','先看缺失、版本不符、执行失败和未知。保持相同任务、解释器及已确认GPU身份采集B；更换GPU或解释器重新开始。'),
            ('解释并分享','全部必需项有证据才通过；AI只解释已有事实。分享前编辑脱敏副本，原始报告留作复检。')]
        links=[dict(title='PyTorch 官方安装选择器',url='https://pytorch.org/get-started/locally/'),dict(title='PyTorch CUDA 语义',url='https://docs.pytorch.org/docs/stable/notes/cuda.html')]
    if mode=='standard':steps=[steps[i] for i in (0,2,3,4,5)]
    elif mode=='quick':steps=[steps[0],('采集与同目标复检',steps[3][1]+' '+steps[4][1])]
    return dict(mode=mode,steps=[dict(title=a,body=b) for a,b in steps],links=links,recommendation=None,remediation=remediation(spec,report,mode))
