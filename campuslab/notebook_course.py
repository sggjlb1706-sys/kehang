"""Fixed data course using an explicitly selected, reviewed local IPython kernel."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess

from .rules import absolute, seal, timestamp, version

EXPECTED = dict(array_sum=42, group_totals={'A':30, 'B':12}, rows=3)
CSV = 'category,score\nA,10\nA,20\nB,12\n'


def make_task(title=None):
    title = title or 'Notebook 数据分析 · 固定内核演示任务'
    if not isinstance(title,str) or not 1 <= len(title.strip()) <= 100:
        raise ValueError('任务名称须为1—100字')
    return seal(dict(schema=1,title=title,scenario='notebook-data',
        source='本项目原创演示数据及固定程序；课程方向参考云南师范大学数据分析大纲，非学校指定版本',
        os='Windows',python=dict(min='3.10',max_exclusive='3.15'),
        packages={'numpy':'1.24','pandas':'2.0'},dependencies={'jupyter_client':'8.0','ipykernel':'6.0'},
        verify='ipykernel-fixed-data-v1',dataset_sha256=hashlib.sha256(CSV.encode()).hexdigest(),expected=EXPECTED))


def validate_spec(spec):
    if not isinstance(spec,dict) or type(spec.get('schema')) is not int or spec.get('schema') != 1 or spec != make_task(spec.get('title')):
        raise ValueError('Notebook任务摘要或固定要求不匹配')
    return spec


def inspect_kernel(path, target):
    """Read only the selected kernel.json; never evaluate its commands or environment."""
    absolute(path); absolute(target)
    file=Path(path)
    result=dict(spec_path=path,exists=file.is_file(),spec_sha256=None,argv=None,validated=False,
                started=None,actual=None,python=None,error='未取得所选kernel.json')
    if not file.is_file():return result
    try:
        raw=file.read_bytes()
        if len(raw)>32768:raise ValueError('kernel.json过大')
        result['spec_sha256']=hashlib.sha256(raw).hexdigest()
        spec=json.loads(raw.decode('utf-8-sig'))
        if not isinstance(spec,dict) or set(spec)-{'argv','display_name','language','metadata'}:
            raise ValueError('仅支持固定ipykernel元数据，不接受env或额外执行配置')
        argv=spec.get('argv'); metadata=spec.get('metadata',{})
        if spec.get('language')!='python' or not isinstance(argv,list) or not all(isinstance(x,str) for x in argv):
            raise ValueError('内核不是受支持的Python内核')
        if not isinstance(metadata,dict) or set(metadata)-{'debugger'} or ('debugger' in metadata and type(metadata['debugger']) is not bool):
            raise ValueError('不接受自定义kernel provisioner或启动配置')
        tail=argv[1:]
        if tail and tail[0]=='-Xfrozen_modules=off':tail=tail[1:]
        if not argv or absolute(argv[0])!=absolute(target) or tail!=['-m','ipykernel_launcher','-f','{connection_file}']:
            raise ValueError('内核argv与课程Python不一致，或启动命令未经审查')
        result.update(argv=argv,validated=True,error='')
    except (OSError,UnicodeError,ValueError,TypeError) as exc:
        result['error']=str(exc)[:500]
    return result


def _object(value,keys,label):
    if not isinstance(value,dict) or set(value)!=set(keys):raise ValueError(label+'证据不完整')


def _state(observed,minimum,installed):
    if observed is None:return 'missing' if installed is False else 'unknown'
    if not isinstance(observed,str):raise ValueError('版本类型无效')
    release=re.fullmatch(r'(\d+\.\d+(?:\.\d+)?)(?:\+[A-Za-z0-9.]+)?',observed)
    return ('pass' if version(release[1])>=version(minimum) else 'mismatch') if release else 'unknown'


def analyze(spec,report):
    validate_spec(spec)
    if not isinstance(report,dict) or type(report.get('schema')) is not int or report.get('schema')!=1 or report.get('task_id')!=spec['id']:
        raise ValueError('报告与Notebook任务不一致')
    timestamp(report.get('collected_at')); target=report.get('target'); facts=report.get('facts')
    _object(target,('requested','actual','exists'),'目标Python'); requested=absolute(target['requested'])
    if target['exists'] is not None and type(target['exists']) is not bool:raise ValueError('目标存在类型无效')
    if target['actual'] is not None and (absolute(target['actual'])!=requested or target['exists'] is not True):raise ValueError('探测Python与所选目标不一致')
    _object(facts,('os','python','dependencies','kernel','packages','run','cleanup'),'Notebook事实')
    for key in ('os','python'):
        if facts[key] is not None and not isinstance(facts[key],str):raise ValueError('系统或Python版本类型无效')
    _object(facts['dependencies'],spec['dependencies'],'Jupyter依赖')
    _object(facts['packages'],spec['packages'],'数据依赖')
    for name,item in facts['dependencies'].items():
        _object(item,('installed','version','error'),name)
        if item['installed'] is not True and item['version'] is not None:raise ValueError('未确认Jupyter依赖时不能携带版本')
    for name,item in facts['packages'].items():
        _object(item,('installed','version','imported','path','error'),name)
        if item['imported'] is not None and type(item['imported']) is not bool:raise ValueError('导入状态类型无效')
        if item['path'] is not None:absolute(item['path'])
        if item['installed'] is not True and (item['version'] is not None or item['imported'] is True or item['path'] is not None):raise ValueError('未确认依赖时不得携带导入事实')
    for item in [*facts['dependencies'].values(),*facts['packages'].values()]:
        if item['installed'] is not None and type(item['installed']) is not bool or not isinstance(item['error'],str):raise ValueError('依赖证据类型无效')
        if item['version'] is not None and not isinstance(item['version'],str):raise ValueError('依赖版本类型无效')
    kernel=facts['kernel'];run=facts['run'];cleanup=facts['cleanup']
    _object(kernel,('spec_path','exists','spec_sha256','argv','validated','started','actual','python','error'),'内核')
    if kernel['spec_path'] is not None:absolute(kernel['spec_path'])
    for key in ('exists','started'):
        if kernel[key] is not None and type(kernel[key]) is not bool:raise ValueError('内核状态类型无效')
    if type(kernel['validated']) is not bool or not isinstance(kernel['error'],str):raise ValueError('内核校验类型无效')
    if kernel['spec_sha256'] is not None and (not isinstance(kernel['spec_sha256'],str) or not re.fullmatch('[a-fA-F0-9]{64}',kernel['spec_sha256'])):raise ValueError('内核摘要无效')
    if kernel['actual'] is not None:absolute(kernel['actual'])
    if kernel['python'] is not None and not isinstance(kernel['python'],str):raise ValueError('内核Python版本无效')
    if kernel['argv'] is not None and (not isinstance(kernel['argv'],list) or not all(isinstance(x,str) for x in kernel['argv'])):raise ValueError('内核argv类型无效')
    if kernel['validated']:
        argv=kernel['argv'] or [];tail=argv[1:]
        if tail and tail[0]=='-Xfrozen_modules=off':tail=tail[1:]
        if not argv or absolute(argv[0])!=requested or tail!=['-m','ipykernel_launcher','-f','{connection_file}'] or kernel['exists'] is not True or not kernel['spec_sha256']:
            raise ValueError('已校验内核缺少固定启动身份')
    _object(run,('returncode','result','stdout','error','executed_at'),'固定内核运行')
    if run['returncode'] is not None and type(run['returncode']) is not int:raise ValueError('运行退出码类型无效')
    if any(not isinstance(run[k],str) for k in ('stdout','error')):raise ValueError('运行输出类型无效')
    if run['executed_at'] is not None:timestamp(run['executed_at'])
    result=run['result']
    if result is not None:
        _object(result,('array_sum','group_totals','rows'),'数据结果')
        if type(result['array_sum']) is not int or type(result['rows']) is not int or not isinstance(result['group_totals'],dict) or any(not isinstance(k,str) or type(v) is not int for k,v in result['group_totals'].items()):raise ValueError('固定数据结果类型无效')
    if run['returncode'] is None and result is not None:raise ValueError('未运行不能携带数据结果')
    _object(cleanup,('kernel_stopped','channels_stopped','error'),'内核清理')
    if any(cleanup[k] is not None and type(cleanup[k]) is not bool for k in ('kernel_stopped','channels_stopped')) or not isinstance(cleanup['error'],str):raise ValueError('内核清理类型无效')
    if target['actual'] is None and (facts['python'] is not None or any(x['installed'] is not None for x in facts['dependencies'].values()) or kernel['started'] is True or run['returncode'] is not None):raise ValueError('未确认课程Python时不能声称运行')
    checks=[]
    def check(key,status,observed,requirement):checks.append(dict(id=key,status=status,observed=observed,requirement=requirement))
    check('os','unknown' if facts['os'] is None else ('pass' if facts['os']=='Windows' else 'mismatch'),facts['os'],'Windows')
    py=facts['python'];check('python',('missing' if target['exists'] is False else 'unknown') if py is None else ('pass' if version('3.10')<=version(py)<version('3.15') else 'mismatch'),py,spec['python'])
    for name,minimum in spec['dependencies'].items():
        item=facts['dependencies'][name];status=_state(item['version'],minimum,item['installed'])
        if status=='pass' and item['error']:status='mismatch'
        check('package:'+name,status,item,'>='+minimum+'，来自所选课程Python')
    kernel_state='missing' if kernel['exists'] is False else 'unknown'
    if kernel['exists'] is True:kernel_state='pass' if kernel['validated'] and not kernel['error'] else 'mismatch'
    check('notebook:spec',kernel_state,kernel,'明确选择受支持ipykernel的kernel.json，argv绑定课程Python')
    identity='unknown' if kernel['started'] is not True or kernel['actual'] is None else ('pass' if absolute(kernel['actual'])==requested and kernel['python']==py else 'mismatch')
    check('notebook:identity',identity,dict(started=kernel['started'],actual=kernel['actual'],python=kernel['python']),'真实内核sys.executable及Python版本与课程Python一致')
    for name,minimum in spec['packages'].items():
        item=facts['packages'][name];status=_state(item['version'],minimum,item['installed'])
        if status=='pass' and (item['imported'] is not True or not item['path'] or item['error']):status='mismatch'
        check('package:'+name,status,item,'真实内核导入 '+name+'>='+minimum)
    check('notebook:run','unknown' if run['returncode'] is None else ('pass' if run['returncode']==0 and result==EXPECTED and not run['error'] and run['executed_at'] else 'mismatch'),run,'固定CSV分组A=30/B=12、数组和42、3行；真实内核执行')
    check('notebook:cleanup','pass' if cleanup['kernel_stopped'] is True and cleanup['channels_stopped'] is True and not cleanup['error'] else 'unknown',cleanup,'仅关闭本次创建的临时内核及通道')
    return dict(task_id=spec['id'],target=target,collected_at=report['collected_at'],checks=checks,passed=all(c['status']=='pass' for c in checks))


def compare_identity(before,after):
    if absolute(before['target']['requested'])!=absolute(after['target']['requested']):raise ValueError('复检须使用同一课程Python')
    a,b=before['facts']['kernel'],after['facts']['kernel']
    if (a['spec_path'] is None)!=(b['spec_path'] is None) or a['spec_path'] is not None and absolute(a['spec_path'])!=absolute(b['spec_path']):raise ValueError('复检须选择同一kernel.json')
    for key in ('spec_sha256','argv','actual'):
        if a[key] is not None and b[key] is not None and (absolute(a[key])!=absolute(b[key]) if key=='actual' else a[key]!=b[key]):raise ValueError('内核身份或配置已变更，请重新初检')


def collect(spec,target,kernel_spec=None):
    validate_spec(spec);absolute(target)
    path=Path(target)
    if (path.parent/'.campuslab-tool-runtime').exists():raise ValueError('工具runtime不能作为课程Python')
    kernel=inspect_kernel(kernel_spec,target) if kernel_spec else dict(spec_path=None,exists=None,spec_sha256=None,argv=None,validated=False,started=None,actual=None,python=None,error='请明确选择已有kernel.json')
    report=dict(schema=1,task_id=spec['id'],collected_at=datetime.now(timezone.utc).isoformat(),target=dict(requested=target,actual=None,exists=path.is_file()),
        facts=dict(os=platform.system(),python=None,dependencies={name:dict(installed=None,version=None,error='课程Python未运行') for name in spec['dependencies']},kernel=kernel,
        packages={name:dict(installed=None,version=None,imported=None,path=None,error='真实内核未运行') for name in spec['packages']},
        run=dict(returncode=None,result=None,stdout='',error='真实内核未运行',executed_at=None),cleanup=dict(kernel_stopped=None,channels_stopped=None,error='未启动内核')),commands=[])
    if path.is_file():
        command=[str(path),'-B','-I',str(Path(__file__).with_name('notebook_probe.py'))]
        if kernel['validated']:command+=['--kernel-spec',kernel_spec]
        report['commands'].append(command)
        try:
            flags=(subprocess.CREATE_NEW_PROCESS_GROUP|subprocess.CREATE_NO_WINDOW) if platform.system()=='Windows' else 0
            with subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',errors='replace',env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},creationflags=flags) as process:
                try:
                    stdout,stderr=process.communicate(timeout=110)
                except subprocess.TimeoutExpired:
                    if platform.system()=='Windows' and process.poll() is None:
                        # The PID is the new probe we created above, never an existing user session.
                        killer=Path(os.environ.get('SystemRoot',r'C:\Windows'))/'System32/taskkill.exe'
                        subprocess.run([str(killer),'/PID',str(process.pid),'/T','/F'],capture_output=True,timeout=10)
                    if process.poll() is None:process.kill()
                    process.communicate(timeout=10)
                    raise
                proc=subprocess.CompletedProcess(command,process.returncode,stdout,stderr)
            report['probe_exit']=proc.returncode
            if proc.returncode:raise ValueError('probe exit '+str(proc.returncode)+': '+proc.stderr[-500:])
            observed=json.loads(proc.stdout);report['target']['actual']=observed['actual']
            for key in ('python','dependencies','packages','run','cleanup'):report['facts'][key]=observed[key]
            if kernel['validated']:report['facts']['kernel'].update(observed['kernel'])
        except (OSError,ValueError,KeyError,TypeError,subprocess.TimeoutExpired) as exc:
            report['facts']['run']['error']='内核探测未完成：'+str(exc)[:500]
    report['collected_at']=datetime.now(timezone.utc).isoformat();analyze(spec,report)
    return report
