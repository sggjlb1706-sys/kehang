"""Guidance varies detail; acceptance always belongs to rules.py."""
from .rules import validate_task


def plan(spec, mode='novice', resources=None):
    validate_task(spec)
    if mode not in ('novice','standard','quick'):
        raise ValueError('指导模式无效')
    local = spec['scenario'] == 'local-qwen'
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
    return dict(mode=mode,steps=[dict(title=a,body=b) for a,b in steps],links=links,recommendation=recommendation)
