"""Guidance varies detail; acceptance always belongs to rules.py."""
from .rules import validate_task


def plan(spec, mode='novice', resources=None, report=None):
    validate_task(spec)
    if mode not in ('novice','standard','quick'):
        raise ValueError('指导模式无效')
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
