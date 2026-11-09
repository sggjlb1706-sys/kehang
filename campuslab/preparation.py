"""Manual, read-only host preparation and deterministic learning-goal clarification."""
import argparse
import csv
import ctypes
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys

from .rules import absolute, timestamp


SOURCES = dict(
    hubu='https://cs.hubu.edu.cn/3_shujukexueyudashujujishuzhuanyebenkerencaipeiyangfangan-2024ban-.pdf',
    torch='https://znxy.cqust.edu.cn/info/1155/5724.htm',
    vm='https://oslabs.hitsz.edu.cn/vm_env.html',
    routes='https://soc.ustc.edu.cn/CECS/lab0/ubuntu/',
    hadoop='https://jwc.sandau.edu.cn/_upload/article/files/d3/6b/b686d2ad434fb3a8e28fc6a379ad/0ca304b3-6d23-42d7-9f3b-6ccf4006ed88.pdf',
    notebook='https://tgsf.ynnu.edu.cn/__local/B/40/36/352DC88EDEED3F9D523E925FCAC_82F10FDB_4133D.pdf',
    bjtu='https://cs.bjtu.edu.cn/docs/2026-05/bb29a34d13074d058ffa47e35b2cbd01.pdf')

CATALOG = [
    dict(scenario='python-basics', label='Python 基础环境', implemented=True, source=SOURCES['notebook'],
         status='已有固定演示检测；课程版本范围由任务快照决定', extension='现有解释器、requests与固定导入验证'),
    dict(scenario='node-basics', label='Node.js / npm', implemented=True, source='本项目固定演示配置',
         status='已有固定演示检测；不代表高校统一课程要求', extension='显式Node与同目录npm身份'),
    dict(scenario='local-qwen', label='固定 Qwen 本地模型', implemented=True, source='本项目固定演示配置',
         status='已有固定离线任务；仅指定模型及权重', extension='硬件预检、依赖、权重、离线推理闭环'),
    dict(scenario='pytorch-cpu', label='PyTorch 深度学习 · CPU', implemented=True, source=SOURCES['torch'],
         status='本轮实现固定张量课程；设备实测见验收证据', extension='指定解释器、框架、固定CPU运算'),
    dict(scenario='pytorch-gpu', label='PyTorch 深度学习 · GPU', implemented=True, source=SOURCES['torch'],
         status='本轮实现独立GPU要求；CPU成功不能替代', extension='框架构建、可用设备、显式GPU运算分别验证'),
    dict(scenario='vm-linux', label='虚拟机 / Linux', implemented=True, source=SOURCES['vm'],
         status='已实现VirtualBox/VMware固定只读任务；本机VMware可取证，实例/来宾未知', extension='宿主、软件、UUID或.vmx实例、来宾证据分别判断'),
    dict(scenario='notebook', label='数据分析 / Notebook', implemented=False, source=SOURCES['notebook'],
         status='课程调研与扩展路线；未实现Notebook采集', extension='固定内核ID与实际sys.executable绑定，再验证NumPy/Pandas固定运算'),
    dict(scenario='java', label='Java / JDK', implemented=False, source=SOURCES['hadoop'],
         status='候选目录；未实现JDK检测；原课程PDF本轮抓取超时', extension='显式JAVA_HOME、java/javac同源版本、固定编译运行'),
    dict(scenario='database', label='数据库 / SQL', implemented=False, source=SOURCES['hubu'],
         status='候选目录；未实现数据库检测；培养方案本轮抓取超时', extension='明确DBMS与实例身份、只读连接、固定SELECT；凭据不入分享'),
    dict(scenario='hadoop', label='Hadoop / 大数据', implemented=False, source='https://hadoop.apache.org/docs/r3.5.0/hadoop-project-dist/hadoop-common/SingleCluster.html',
         status='官方3.5.0组合准备路线；未取得Linux来宾、SSH或集群证据', extension='服务端JDK17、Linux来宾、SSH、明确Hadoop配置/集群身份逐项核对；现有Java课程JDK21通过不代表Hadoop服务端可用。详见docs/Hadoop与框架组合路线-20261109.md'),
    dict(scenario='network-cloud', label='网络 / 云计算', implemented=False, source=SOURCES['bjtu'],
         status='候选目录；未实现云资源或网络配置检测；原培养方案URL本轮404', extension='教师固定拓扑、资源/账户身份、只读证据；不自动创建云资源'),
]
for item in CATALOG:
    if item['scenario'] in ('notebook','java','database'):
        new_name={'notebook':'notebook-data','java':'java-jdk','database':'sqlite-basics'}[item['scenario']]
        item.update(scenario=new_name,implemented=True,
                    status='本轮新增固定任务；真实结果与外部条件见本轮证据',
                    extension={'notebook-data':'显式内核/解释器、NumPy/Pandas与固定数据运算',
                               'java-jdk':'显式JDK、同源java/javac、固定临时编译运行',
                               'sqlite-basics':'SQLite单机SQL入门，明确数据库文件，只读固定SELECT；不代表MySQL/PostgreSQL'}[new_name])
CATALOG.extend([
    dict(scenario='ai-web-deepseek',label='AI 网页/客户端 · DeepSeek',implemented=True,source='https://www.deepseek.com/',status='本人练习记录与固定成果核对；登录/连接不作自动认证',extension='网页使用、课程上下文、结果核对；另有Qwen/豆包官方指导路线'),
    dict(scenario='deepseek-api',label='DeepSeek API 编程准备',implemented=True,source='https://api-docs.deepseek.com/',status='固定官方目的地/模型/练习；真实发送须本人单次确认',extension='显式Python标准库、可编辑预览、终端密钥、协议/结果与复检'),
    dict(scenario='dsh-desktop',label='DeepSeek Harness · Windows 桌面',implemented=True,source='https://www.deepseek.com/harness/',status='静态安装身份与本人Agent证据分别验证',extension='自带运行时；系统Node/PATH无dsh不表示桌面失败'),
    dict(scenario='dsh-cli',label='DeepSeek Harness · npm/CLI/Web',implemented=True,source='https://github.com/deepseek-ai/deepseek-harness',status='固定包/Node身份、工作区、模型及Agent证据分层',extension='Node>=24.9.0；不会运行npx、启动DSH或读取其凭据'),
    dict(scenario='database-server',label='MySQL / PostgreSQL',implemented=False,source=SOURCES['hubu'],status='调研/指导；未实现实例连接验收',extension='需明确实例、只读账号和固定查询；SQLite不能替代'),
    dict(scenario='agent-framework-mcp',label='Agent 开发框架 / MCP',implemented=False,source='https://modelcontextprotocol.io/docs/learn/architecture',status='来源目录及后续路线；未实现真实模型工具调用验收',extension='未来固定工具参数/结果闭环，不能执行任意工具或命令')])
SUPPORTED = {x['scenario']: x['label'] for x in CATALOG if x['implemented']}


def resolve_need(text, clarification=None):
    """Return a proposal only. The UI must confirm before creating a task snapshot."""
    if not isinstance(text, str) or not 1 <= len(text.strip()) <= 4000:
        raise ValueError('请用1—4000字描述学习目标或文字报错')
    value = text.casefold()
    compact = ''.join(value.split())
    error = any(word in value for word in ('报错', '错误', '失败', 'error', 'exception', '找不到', 'failed'))
    result = dict(status='clarify', scenario=None, candidates=[], question='',
                  constraints=dict(local_required=False, gpu_required=False), error_help=error,
                  message='', requires_confirmation=True)
    if any(word in compact for word in ('课程要求本地', '必须本地', '老师要求本地')):
        result['constraints']['local_required'] = True
    if any(word in compact for word in ('要求gpu', '必须gpu', '需要gpu', '要求cuda')):
        result['constraints']['gpu_required'] = True
    if ((result['constraints']['local_required'] and any(word in compact for word in ('只用云', '只要云', '不能本地')))
            or (result['constraints']['gpu_required'] and any(word in compact for word in ('没有gpu', '无gpu', '只能cpu', '只用cpu', '先用cpu')))):
        result.update(status='conflict', message='个人条件与课程要求冲突。先向教师确认允许的路线，当前要求保持。',
                      question='课程是否允许替代路线？取得教师确认后再选择任务。')
        return result
    new=[]
    if any(word in value for word in ('deepseek harness','deepseek-harness','harness','dsh')):
        new=['dsh-cli'] if any(word in value for word in ('cli','npm','命令行','web端')) else (['dsh-desktop'] if any(word in value for word in ('桌面','desktop','客户端')) else ['dsh-desktop','dsh-cli'])
    elif any(word in value for word in ('deepseek','深度求索','主流ai','使用ai','ai工具')):
        new=['deepseek-api'] if 'api' in value else (['ai-web-deepseek'] if any(word in value for word in ('网页','客户端','聊天')) else ['ai-web-deepseek','deepseek-api','local-qwen'])
    elif any(word in value for word in ('hadoop','大数据','spark')):
        result.update(status='catalog_only',catalog=[x for x in CATALOG if x['scenario']=='hadoop'],message='组合课程须分别核对Linux、JDK、SSH和集群；单独Java或Linux通过不能替代。',question='先按官方组合路线确认教师要求与缺少组件。')
        if clarification is not None:raise ValueError('组合路线尚无集群检测任务')
        return result
    elif any(word in value for word in ('notebook','jupyter','数据分析','pandas')): new=['notebook-data']
    elif any(word in value for word in ('java','jdk')): new=['java-jdk']
    elif 'sqlite' in value or ('sql' in value and not any(word in value for word in ('mysql','postgres','sqlserver'))): new=['sqlite-basics']
    if new:
        if result['constraints']['local_required'] and any(x in new for x in ('deepseek-api','ai-web-deepseek')):
            result.update(status='conflict',message='课程明确要求本地，网页或远程API不可替代本地通过。',question='先确认教师允许的本地模型路线。')
            return result
        if result['constraints']['gpu_required']:
            result.update(status='conflict',message='当前固定任务不验证所要求的GPU运算，不能降低课程要求。',question='请先确认GPU课程及验收条件。')
            return result
        if clarification is not None:
            if clarification not in new: raise ValueError('澄清选项不属于当前学习目标')
            new=[clarification]
        result.update(candidates=[dict(scenario=x,label=SUPPORTED[x]) for x in new],
                      status='recognized' if len(new)==1 else 'clarify',scenario=new[0] if len(new)==1 else None,
                      message='确认具体路线后建立固定任务。网页使用、API和本地模型各有独立验收。',
                      question='' if len(new)==1 else '请选择要完成的路线；DSH桌面端与CLI依赖分别核对。')
        return result
    candidates = []
    deep = any(word in value for word in ('pytorch', '深度学习', 'torch'))
    if deep:
        if result['constraints']['gpu_required']:
            candidates.append('pytorch-gpu')
        elif 'cpu' in value or '无gpu' in compact or '没有gpu' in compact:
            candidates.append('pytorch-cpu')
        elif result['constraints']['gpu_required'] or 'gpu' in value or 'cuda' in value:
            candidates.append('pytorch-gpu')
        else:
            candidates.extend(('pytorch-cpu', 'pytorch-gpu'))
    if any(word in value for word in ('本地模型', '本地大模型', 'qwen', 'ollama', '运行大模型')):
        candidates.append('local-qwen')
    if any(word in value for word in ('虚拟机', 'virtualbox', 'vmware', 'linux', 'ubuntu')):
        candidates.append('vm-linux')
    if any(word in value for word in ('node', 'npm')):
        candidates.append('node-basics')
    if 'python' in value and not deep and not any(x in candidates for x in ('local-qwen',)):
        candidates.append('python-basics')
    research = []
    for scenario, words in [('database-server', ('数据库', 'mysql', 'sql', 'postgres')),
                            ('hadoop', ('hadoop', '大数据', 'spark')), ('network-cloud', ('网络', '云计算', '云端模型', 'api模型'))]:
        if any(word in value for word in words): research.append(scenario)
    if research:
        items = [item for item in CATALOG if item['scenario'] in research]
        result.update(status='catalog_only', catalog=items, message='已定位课程方向；当前只有调研与扩展路线，不能自动检测此课程。',
                      question='请先确认教师的软件、版本和验收要求。')
        result['candidates'] = [dict(scenario=x, label=SUPPORTED[x]) for x in candidates]
        if clarification is not None:
            raise ValueError('候选目录尚不能生成检测任务')
        return result
    candidates = list(dict.fromkeys(candidates))
    if 'local-qwen' in candidates and any(word in value for word in ('只用云', '只要云', '不能本地')):
        result.update(status='conflict', message='本地目标与仅云端约束冲突，当前固定本地任务不能替代为云端通过。',
                      question='先确认本地还是云端学习目标。云端目前仅提供路线说明。')
        return result
    if clarification is not None:
        allowed = candidates or list(SUPPORTED)
        if clarification not in allowed:
            raise ValueError('澄清选项须属于当前识别的受支持课程')
        candidates = [clarification]
    result['candidates'] = [dict(scenario=x, label=SUPPORTED[x]) for x in (candidates or SUPPORTED)]
    if len(candidates) == 1:
        result.update(status='recognized', scenario=candidates[0], message='已识别一个固定演示任务。核对课程要求并确认后建立快照。')
    elif len(candidates) > 1 and set(candidates) != {'pytorch-cpu', 'pytorch-gpu'}:
        result.update(status='conflict', message='检测到多个课程目标。一次任务只固定一组验收要求。', question='先处理哪一门课程？')
    else:
        result.update(question='课程是否要求GPU运算？' if deep else '请先选择报错所属课程或说明要完成的实验。',
                      message='尚缺足够信息；不会据此假定软件、硬件或课程已经配置。')
    if error:
        result['message'] += ' 文字报错可以进入诊断；未采集时需补充目标路径、版本、操作和原始错误，诊断不能代替检测。'
    return result


def _field(value, source, collected_at, reason=''):
    return dict(value=value, source=source, collected_at=collected_at, reason=reason)


def validate_hardware(report):
    if not isinstance(report, dict) or type(report.get('schema')) is not int or report.get('schema') != 1 or report.get('kind') != 'hardware':
        raise ValueError('需要硬件预检报告')
    timestamp(report.get('collected_at'))
    absolute(report.get('tool_runtime')); absolute(report.get('drive'))
    fields = report.get('fields')
    if not isinstance(fields, dict) or set(fields) != {'os', 'ram_bytes', 'storage_free_bytes', 'gpus'}:
        raise ValueError('硬件事实集合不完整')
    for name, field in fields.items():
        if not isinstance(field, dict) or set(field) != {'value', 'source', 'collected_at', 'reason'}:
            raise ValueError('硬件事实须含值、来源、时间和未知原因')
        timestamp(field['collected_at'])
        if not isinstance(field['source'], str) or not field['source'] or not isinstance(field['reason'], str):
            raise ValueError('硬件事实来源或原因无效')
        value = field['value']
        if value is None:
            if not field['reason']: raise ValueError('未知硬件事实须说明原因')
            continue
        if name == 'os' and (not isinstance(value, str) or not value): raise ValueError('系统事实无效')
        if name in ('ram_bytes', 'storage_free_bytes') and (type(value) is not int or value < 0): raise ValueError('资源值无效')
        if name == 'gpus':
            if not isinstance(value, list): raise ValueError('GPU事实无效')
            for gpu in value:
                if not isinstance(gpu, dict) or set(gpu) != {'id', 'name', 'vram_bytes'} or any(not isinstance(gpu[x], str) or not gpu[x] for x in ('id', 'name')):
                    raise ValueError('GPU身份无效')
                if gpu['vram_bytes'] is not None and (type(gpu['vram_bytes']) is not int or gpu['vram_bytes'] < 0): raise ValueError('显存值无效')
    return report


def collect_hardware(drive=None):
    """Only invoked by the manual CLI; importing this module performs no probes."""
    drive = drive or (Path.cwd().anchor or 'C:\\')
    absolute(drive)
    now = datetime.now(timezone.utc).isoformat()
    fields = {name: _field(None, 'not collected', now, '只支持Windows宿主手动预检')
              for name in ('os', 'ram_bytes', 'storage_free_bytes', 'gpus')}
    report = dict(schema=1, kind='hardware', collected_at=now, tool_runtime=sys.executable, drive=drive, fields=fields, commands=[])
    try:
        fields['storage_free_bytes'] = _field(shutil.disk_usage(drive).free, 'Python shutil.disk_usage: '+drive, now)
    except OSError as exc:
        fields['storage_free_bytes'] = _field(None, 'Python shutil.disk_usage: '+drive, now, type(exc).__name__)
    if platform.system() != 'Windows':
        raise ValueError('本轮硬件预检仅支持Windows宿主')
    script = ("$ErrorActionPreference='Stop'; [Console]::OutputEncoding=[System.Text.Encoding]::UTF8; "
              "$os=Get-CimInstance Win32_OperatingSystem; $cs=Get-CimInstance Win32_ComputerSystem; "
              "$video=@(Get-CimInstance Win32_VideoController | Select-Object PNPDeviceID,Name); "
              "@{os=($os.Caption+' '+$os.Version);ram_bytes=$cs.TotalPhysicalMemory;gpus=$video} | ConvertTo-Json -Depth 5 -Compress")
    command = ['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', script]
    try:
        proc = subprocess.run(command, capture_output=True, timeout=25, encoding='utf-8-sig', errors='replace')
        report['commands'].append(dict(command=command, returncode=proc.returncode, stdout=proc.stdout, stderr=proc.stderr))
        if proc.returncode: raise ValueError('CIM查询失败，退出码'+str(proc.returncode))
        data = json.loads(proc.stdout)
        fields['os'] = _field(data['os'], 'Get-CimInstance Win32_OperatingSystem', now)
        fields['ram_bytes'] = _field(int(data['ram_bytes']), 'Get-CimInstance Win32_ComputerSystem.TotalPhysicalMemory', now)
        cards = [dict(id=x['PNPDeviceID'], name=x['Name'], vram_bytes=None) for x in data['gpus']]
        fields['gpus'] = _field(cards, 'Get-CimInstance Win32_VideoController; 显存未确认', now,
                               'CIM显存字段可能截断，未用作真实显存证据' if cards else '')
    except (OSError, subprocess.TimeoutExpired, ValueError, KeyError, TypeError) as exc:
        for name in ('os', 'ram_bytes', 'gpus'):
            fields[name] = _field(None, 'Get-CimInstance只读查询', now, str(exc)[:300])
        # WMI may be unavailable to a restricted user. These read-only fallbacks
        # are independent of any course interpreter, framework or model.
        fields['os'] = _field('Windows '+platform.version(), 'Python platform.version (Windows宿主)', now,
                              'CIM不可用；未取得产品名称/版本营销名')
        class MemoryStatus(ctypes.Structure):
            _fields_ = [('length', ctypes.c_ulong), ('load', ctypes.c_ulong)] + [
                (key, ctypes.c_ulonglong) for key in ('total_phys', 'avail_phys', 'total_page', 'avail_page', 'total_virtual', 'avail_virtual', 'avail_extended')]
        memory = MemoryStatus(); memory.length = ctypes.sizeof(memory)
        try:
            if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)):
                raise OSError('GlobalMemoryStatusEx失败')
            fields['ram_bytes'] = _field(int(memory.total_phys), 'Windows GlobalMemoryStatusEx.ullTotalPhys', now,
                                         'CIM不可用；使用宿主系统API的可用物理内存总量')
        except (AttributeError, OSError) as fallback_error:
            fields['ram_bytes']['reason'] += '；'+str(fallback_error)
    smi = shutil.which('nvidia-smi.exe')
    if smi:
        command = [smi, '--query-gpu=uuid,name,memory.total', '--format=csv,noheader,nounits']
        try:
            proc = subprocess.run(command, capture_output=True, timeout=15, encoding='utf-8', errors='replace')
            report['commands'].append(dict(command=command, returncode=proc.returncode, stdout=proc.stdout, stderr=proc.stderr))
            if proc.returncode: raise ValueError('nvidia-smi退出码'+str(proc.returncode))
            cards = [dict(id=row[0].strip(), name=row[1].strip(), vram_bytes=int(row[2].strip())*1024**2)
                     for row in csv.reader(proc.stdout.splitlines()) if row]
            # Keep other adapters; only NVIDIA entries get VRAM measured by its driver.
            other = [x for x in (fields['gpus']['value'] or []) if 'nvidia' not in x['name'].casefold()]
            fields['gpus'] = _field(cards+other, 'nvidia-smi UUID/name/memory.total；非NVIDIA名称来自CIM', now,
                                   '非NVIDIA显存未知' if other else '')
        except (OSError, subprocess.TimeoutExpired, ValueError, IndexError) as exc:
            fields['gpus']['reason'] = 'nvidia-smi未完成：'+str(exc)[:200]
    validate_hardware(report)
    return report


def recommend(spec, hardware=None):
    if not isinstance(spec, dict) or spec.get('scenario') not in SUPPORTED:
        raise ValueError('仅为受支持的固定课程提供准备建议')
    scenario = spec['scenario']
    local_required = scenario == 'local-qwen' and spec.get('model', {}).get('local_required') is True
    result = dict(status='unknown', summary='先取得这台电脑的只读硬件预检，再确认课程路线。', evidence=[],
                  actions=['在目标电脑手动运行硬件预检，导入带时间与来源的hardware.json。'],
                  alternatives=[], requirement_unmodified=True, environment_passed=False)
    if scenario == 'local-qwen':
        result['actions'] += ['固定路线：确认Python环境 → 准备torch/transformers → 按任务revision准备权重并核对SHA → 指定模型目录预检 → 本人主动执行固定离线推理 → 同目标复检。']
        result['alternatives'] = ['本地：权重与计算在本机；云端：远程环境运行；API：请求外部服务，需另行确认隐私、费用与课程许可。',
                                  '课程强制本地时，云端/API不能替代该任务通过；资源不足须先向教师确认。' if local_required else '自主学习可先比较本地、云端和API；采用替代路线前重新确认目标，当前快照不自动改变。']
    if hardware is None: return result
    validate_hardware(hardware)
    fields = hardware['fields']
    result['evidence'] = [dict(id=k, **v) for k, v in fields.items()]
    result['hardware_collected_at'] = hardware['collected_at']
    result['actions'][0] = '这些是所导入报告时间的设备事实；硬件建议不代表课程环境已安装或运行成功。'
    needed = ['os', 'ram_bytes', 'storage_free_bytes'] + (['gpus'] if scenario in ('local-qwen', 'pytorch-gpu') else [])
    if any(fields[name]['value'] is None for name in needed):
        result['summary'] = '部分设备事实未知。补齐对应查询或保留未知后再选择准备路线。'
        result['actions'].append('未知项：'+ '、'.join(name for name in needed if fields[name]['value'] is None))
        return result
    ram, free, cards = (fields[name]['value'] for name in ('ram_bytes', 'storage_free_bytes', 'gpus'))
    if not fields['os']['value'].startswith('Windows') and 'Windows' not in fields['os']['value']:
        result.update(status='confirm_route', summary='此任务面向Windows宿主，当前系统证据不符合；先确认课程及运行电脑。')
    elif ram < 4*1024**3 or free < 4*1024**3:
        result.update(status='resource_pressure', summary='内存或目标盘空闲容量较紧张，先核对课程资源需求。')
        result['actions'].append('4GiB仅为本演示的资源规划提醒，不是最低要求、兼容性或性能保证；不要自动清理文件。')
    elif scenario in ('local-qwen', 'pytorch-gpu') and not cards:
        result.update(status='confirm_route', summary='预检未取得GPU设备；先确认课程的CPU/GPU要求。')
        result['actions'].append('固定Qwen允许尝试CPU但需实际推理确认速度；GPU课程仍须GPU证据，CPU成功不替代。')
    elif scenario == 'pytorch-gpu' and not any('nvidia' in x['name'].casefold() for x in cards):
        result.update(status='confirm_route', summary='当前固定GPU课程采用CUDA；未取得NVIDIA设备证据。')
        result['actions'].append('先核对课程是否允许CPU或其他平台；当前CUDA任务保留，不能用其他设备替代成功。')
    else:
        result.update(status='ready_to_check', summary='已取得基础设备事实，可以继续课程环境采集；仍需真实运行验收。')
        if scenario in ('local-qwen', 'pytorch-gpu') and all(x['vram_bytes'] is None for x in cards):
            result.update(status='unknown', summary='已发现显卡名称，但显存未知；补齐证据，不能推定资源充足。')
        result['actions'].append('使用当前任务固定要求和本人明确选择的目标环境采集，硬件名称不证明框架支持或运算成功。')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--drive', help='准备课程文件的现有盘符或目录；只读查询其可用容量')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = collect_hardware(args.drive)
    with args.output.open('x', encoding='utf-8') as output:
        json.dump(report, output, ensure_ascii=False, indent=2)
    print(json.dumps(dict(output=str(args.output), collected_at=report['collected_at']), ensure_ascii=True))


if __name__ == '__main__': main()
