"""Fixed read-only VirtualBox/VMware host and manually collected Linux guest evidence."""
from datetime import datetime, timezone
import hashlib
import json
import ntpath
from pathlib import Path
import platform
import re
import subprocess
import uuid

from .rules import absolute, seal, timestamp, version


def make_task(title=None):
    title=title or '虚拟机 / Linux 环境 · 演示任务'
    if not isinstance(title,str) or not 1<=len(title.strip())<=100:
        raise ValueError('任务名称须为1—100字')
    return seal(dict(schema=1,title=title,scenario='vm-linux',os='Windows',
        source='演示课程要求，参考高校虚拟机/Linux课程；不等于原校实验验收',
        software=dict(virtualbox=dict(min='7.0',max_exclusive='8.0'),vmware=dict(min='1.0',max_exclusive='2.0')),
        guest_os='Linux',verify='linux-uname-and-fixed-sum',guest_max_age_seconds=1800))


def validate_spec(spec):
    if not isinstance(spec,dict) or type(spec.get('schema')) is not int or spec!=make_task(spec.get('title')):
        raise ValueError('虚拟机任务快照缺失、摘要不匹配或含未支持要求')
    return spec


def _keys(value,expected):
    if not isinstance(value,dict) or set(value)!=set(expected.split()):
        raise ValueError('虚拟机报告缺少完整事实结构')


def _uuid(value):
    if not isinstance(value,str):raise ValueError('虚拟机UUID无效')
    try:return str(uuid.UUID(value))
    except (ValueError,AttributeError):raise ValueError('虚拟机UUID无效') from None


def _provider(target):
    name=ntpath.basename(absolute(target))
    if name=='vboxmanage.exe':return 'virtualbox'
    if name=='vmrun.exe':return 'vmware'
    raise ValueError('请选择VBoxManage.exe或vmrun.exe完整路径')


def _vm_id(value,provider):
    if provider=='virtualbox':return _uuid(value)
    result=absolute(value)
    if not result.endswith('.vmx'):raise ValueError('VMware实例须为明确选择的.vmx完整路径')
    return result


def analyze(spec,report):
    validate_spec(spec)
    if not isinstance(report,dict) or type(report.get('schema')) is not int or report.get('schema')!=1 or report.get('task_id')!=spec['id']:
        raise ValueError('报告与当前任务快照不一致')
    collected=timestamp(report.get('collected_at'))
    target,facts=report.get('target'),report.get('facts')
    _keys(target,'requested actual exists')
    provider=_provider(target['requested'])
    if target['exists'] is not None and type(target['exists']) is not bool:raise ValueError('目标存在状态无效')
    if target['actual'] is not None and (absolute(target['actual'])!=absolute(target['requested']) or target['exists'] is not True):
        raise ValueError('实际软件与所选目标不一致')
    _keys(facts,'os host software inventory instance guest')
    host,soft,inventory,instance,guest=(facts[k] for k in ('host','software','inventory','instance','guest'))
    _keys(host,'id virtualization source error')
    _keys(host['virtualization'],'firmware_enabled vm_monitor slat hypervisor_present')
    if host['id'] is not None and (not isinstance(host['id'],str) or not re.fullmatch('[a-f0-9]{64}',host['id'])):raise ValueError('宿主身份摘要无效')
    if any(v is not None and type(v) is not bool for v in host['virtualization'].values()):raise ValueError('虚拟化证据类型无效')
    _keys(soft,'provider version returncode error')
    _keys(inventory,'kind returncode items error')
    _keys(instance,'requested uuid name os_type state exists listed error')
    if soft['provider']!=provider or inventory['kind']!=('registered' if provider=='virtualbox' else 'running'):
        raise ValueError('虚拟化提供方与所选工具不一致')
    if any(v is not None and type(v) is not int for v in (soft['returncode'],inventory['returncode'])):raise ValueError('退出码无效')
    if any(v is not None and type(v) is not bool for v in (instance['exists'],instance['listed'])):raise ValueError('实例状态类型无效')
    if any(not isinstance(v,str) for v in (host['source'],host['error'],soft['error'],inventory['error'],instance['error'])):raise ValueError('错误说明类型无效')
    if any(v is not None and not isinstance(v,str) for v in (facts['os'],soft['version'],instance['name'],instance['os_type'],instance['state'])):raise ValueError('版本或实例字段无效')
    if not isinstance(inventory['items'],list):raise ValueError('实例列表无效')
    ids=[]
    for item in inventory['items']:
        _keys(item,'id name')
        if not isinstance(item['name'],str):raise ValueError('实例名称无效')
        ids.append(_vm_id(item['id'],provider))
    if len(ids)!=len(set(ids)):raise ValueError('实例列表有重复身份')
    selected=_vm_id(instance['requested'],provider) if instance['requested'] is not None else None
    if instance['uuid'] is not None:_uuid(instance['uuid'])
    if provider=='virtualbox' and instance['uuid'] is not None and _uuid(instance['uuid'])!=selected:raise ValueError('实例UUID与选择不一致')
    if instance['listed'] is True and (inventory['returncode']!=0 or selected not in ids):raise ValueError('实例列表不能证明所选实例')
    if instance['exists'] is True and (selected is None or instance['uuid'] is None):raise ValueError('实例存在须含明确身份')
    if instance['exists'] is not True and any(instance[k] is not None for k in ('uuid','name','os_type','state')):raise ValueError('实例未确认不得声称运行信息')
    if target['actual'] is None and (soft['version'] is not None or soft['returncode'] is not None or inventory['returncode'] is not None or instance['exists'] is not None or guest is not None):
        raise ValueError('所选虚拟化软件未确认，不能携带实例/来宾成功证据')
    checks=[]
    def check(key,status,observed,requirement):checks.append(dict(id=key,status=status,observed=observed,requirement=requirement))
    check('os','unknown' if facts['os'] is None else ('pass' if facts['os']=='Windows' else 'mismatch'),facts['os'],'Windows宿主')
    virt=host['virtualization'];required=[virt[k] for k in ('firmware_enabled','vm_monitor','slat')]
    state='mismatch' if False in required and virt['hypervisor_present'] is not True else ('pass' if all(v is True for v in required) and host['id'] is not None else 'unknown')
    check('host:virtualization',state,host,'同一宿主身份；固件虚拟化、VM扩展和SLAT均有证据。已有Hypervisor时False旗标可能受屏蔽，保留未知，不推断BIOS关闭')
    state='missing' if target['exists'] is False else 'unknown'
    if soft['version'] is not None:
        try:state='pass' if version(spec['software'][provider]['min'])<=version(soft['version'])<version(spec['software'][provider]['max_exclusive']) else 'mismatch'
        except ValueError:state='unknown'
        if soft['returncode'] is None:state='unknown'
        elif (soft['returncode'] not in ((0,-1,4294967295) if provider=='vmware' else (0,))) or soft['error']:state='mismatch'
    check('vm:software',state,soft,'VirtualBox CLI 7.x 或 vmrun CLI 1.x（非Workstation版本）；vmrun无参数帮助可退出-1')
    check('vm:instance','pass' if instance['exists'] is True else ('missing' if instance['exists'] is False else 'unknown'),instance,'显式选择的UUID或.vmx配置身份；不代表来宾已运行')
    check('vm:running','pass' if instance['exists'] is True and instance['state']=='running' and instance['listed'] is True else 'unknown',instance['state'],'所选实例当前运行证据；工具不会启动实例')
    identity_state=linux_state=run_state='unknown'
    if guest is not None:
        _keys(guest,'schema task_id vm_id hardware_uuid machine_id_sha256 collected_at os kernel verification source')
        if type(guest['schema']) is not int or guest['schema']!=1 or guest['task_id']!=spec['id'] or guest['source']!='manual-linux-guest-probe':raise ValueError('来宾报告与当前任务不一致')
        if selected is None or _vm_id(guest['vm_id'],provider)!=selected or instance['exists'] is not True:raise ValueError('来宾报告不属于所选实例')
        if guest['hardware_uuid'] is not None and _uuid(guest['hardware_uuid'])!=_uuid(instance['uuid']):raise ValueError('来宾DMI UUID不属于所选虚拟机')
        if guest['machine_id_sha256'] is not None and (not isinstance(guest['machine_id_sha256'],str) or not re.fullmatch('[a-f0-9]{64}',guest['machine_id_sha256'])):raise ValueError('来宾系统身份摘要无效')
        if not isinstance(guest['os'],str) or not isinstance(guest['kernel'],str):raise ValueError('来宾系统字段无效')
        verify=guest['verification'];_keys(verify,'returncode stdout error')
        if verify['returncode'] is not None and type(verify['returncode']) is not int:raise ValueError('来宾退出码无效')
        if not isinstance(verify['stdout'],str) or not isinstance(verify['error'],str):raise ValueError('来宾输出无效')
        age=(collected-timestamp(guest['collected_at'])).total_seconds()
        fresh=0<=age<=spec['guest_max_age_seconds']
        if fresh:
            identity_state='pass' if guest['hardware_uuid'] is not None and guest['machine_id_sha256'] is not None else 'unknown'
            linux_state='pass' if guest['os']=='Linux' and guest['kernel'] else 'mismatch'
            run_state='unknown' if verify['returncode'] is None else ('pass' if verify['returncode']==0 and verify['stdout'].strip()=='Linux:6' and not verify['error'] else 'mismatch')
    check('guest:identity',identity_state,guest,'手动来宾报告：同任务/实例、DMI UUID、machine-id摘要；30分钟内，不是密码学远程证明')
    check('guest:linux',linux_state,None if guest is None else dict(os=guest['os'],kernel=guest['kernel']),'来宾实际Linux与内核证据；配置文件OS类型不替代')
    check('guest:run',run_state,None if guest is None else guest['verification'],'来宾固定uname与Python求和输出Linux:6；非完整课程作业验收')
    return dict(task_id=spec['id'],target=target,collected_at=report['collected_at'],checks=checks,passed=all(c['status']=='pass' for c in checks))


def compare_identity(before,after):
    a,b=before['facts'],after['facts']
    if before['task_id']!=after['task_id'] or absolute(before['target']['requested'])!=absolute(after['target']['requested']):raise ValueError('复检须同任务、同虚拟化软件')
    if a['host']['id'] is None or a['host']['id']!=b['host']['id']:raise ValueError('复检须为同一宿主机')
    provider=a['software']['provider']
    if provider!=b['software']['provider']:raise ValueError('复检不能更换虚拟化提供方')
    for key in ('requested','uuid'):
        x,y=a['instance'][key],b['instance'][key]
        if key=='requested':
            x=_vm_id(x,provider) if x is not None else None;y=_vm_id(y,provider) if y is not None else None
        elif x is not None and y is not None:x,y=_uuid(x),_uuid(y)
        if (key=='requested' and x!=y) or (key=='uuid' and x is not None and y is not None and x!=y):raise ValueError('复检须为同一虚拟机实例；更换选择须重新初检')
    ga,gb=a['guest'],b['guest']
    if ga is not None and gb is not None:
        for key in ('machine_id_sha256','hardware_uuid'):
            if ga[key] is not None and gb[key] is not None and ga[key]!=gb[key]:raise ValueError('复检来宾系统身份已改变')
        if timestamp(gb['collected_at'])<=timestamp(ga['collected_at']):raise ValueError('请在同一来宾重新采集较晚证据，不复用旧来宾报告')


def _command(args):
    proc=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=20)
    return proc.returncode,proc.stdout,proc.stderr[:2000]


def host_evidence():
    result=dict(id=None,virtualization=dict(firmware_enabled=None,vm_monitor=None,slat=None,hypervisor_present=None),source='Windows CIM; HKLM MachineGuid SHA256',error='')
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,r'SOFTWARE\Microsoft\Cryptography',0,winreg.KEY_READ|winreg.KEY_WOW64_64KEY) as key:
            identity=winreg.QueryValueEx(key,'MachineGuid')[0]
        result['id']=hashlib.sha256(identity.casefold().encode()).hexdigest()
    except (OSError,ImportError,AttributeError):result['error']='无法取得宿主唯一身份；'
    script="$ErrorActionPreference='Stop'; $p=@(Get-CimInstance Win32_Processor); $c=Get-CimInstance Win32_ComputerSystem; if (!$p.Count) {throw 'No processor evidence'}; function KnownAll($items) { if ($items -contains $false) {return $false}; if ($items -contains $null) {return $null}; return $true }; @{firmware_enabled=(KnownAll @($p | ForEach-Object {$_.VirtualizationFirmwareEnabled})); vm_monitor=(KnownAll @($p | ForEach-Object {$_.VMMonitorModeExtensions})); slat=(KnownAll @($p | ForEach-Object {$_.SecondLevelAddressTranslationExtensions})); hypervisor_present=$c.HypervisorPresent} | ConvertTo-Json -Compress"
    try:
        code,out,error=_command(['powershell.exe','-NoProfile','-NonInteractive','-Command',script])
        if code:raise ValueError('CIM query failed')
        observed=json.loads(out)
        _keys(observed,'firmware_enabled vm_monitor slat hypervisor_present')
        if any(v is not None and type(v) is not bool for v in observed.values()):raise ValueError('CIM type')
        result['virtualization']=observed
    except (OSError,ValueError,subprocess.TimeoutExpired):result['error']+='CIM虚拟化查询未完成或权限不足，保留未知'
    return result


def collect(spec,target,vm_id=None,guest_report=None):
    validate_spec(spec);provider=_provider(target);path=Path(target)
    selected=_vm_id(vm_id,provider) if vm_id else None
    report=dict(schema=1,task_id=spec['id'],collected_at=datetime.now(timezone.utc).isoformat(),target=dict(requested=target,actual=None,exists=path.is_file()),
        facts=dict(os=platform.system(),host=host_evidence(),software=dict(provider=provider,version=None,returncode=None,error='所选软件不存在或未确认'),
            inventory=dict(kind='registered' if provider=='virtualbox' else 'running',returncode=None,items=[],error='未采集'),
            instance=dict(requested=selected,uuid=None,name=None,os_type=None,state=None,exists=None,listed=None,error='请选择具体实例'),guest=None),commands=[])
    facts=report['facts'];soft=facts['software'];inventory=facts['inventory'];instance=facts['instance']
    if path.is_file():
        try:
            report['target']['actual']=str(path.resolve())
            args=[str(path),'--version'] if provider=='virtualbox' else [str(path)]
            report['commands'].append(args);code,out,error=_command(args)
            match=re.search(r'^(\d+\.\d+\.\d+)',out) if provider=='virtualbox' else re.search(r'vmrun version (\d+\.\d+\.\d+)',out+error)
            # vmrun without a command returns its help/version; it performs no VM action.
            soft.update(version=match[1] if match else None,returncode=code,error='' if match and (code in (0,-1,4294967295) if provider=='vmware' else code==0) else error or '未取得软件版本')
            args=[str(path),'list','vms'] if provider=='virtualbox' else [str(path),'-T','ws','list']
            report['commands'].append(args);code,out,error=_command(args)
            inventory.update(returncode=code,error=error)
            if code==0:
                if provider=='virtualbox':
                    for line in out.splitlines():
                        match=re.fullmatch(r'"(.*)"\s+\{([0-9A-Fa-f-]{36})\}',line.strip())
                        if match:inventory['items'].append(dict(id=_uuid(match[2]),name=match[1]))
                else:
                    for line in out.splitlines()[1:]:
                        if line.strip():inventory['items'].append(dict(id=_vm_id(line.strip(),provider),name=ntpath.basename(line.strip())))
            if selected is not None:
                instance['listed']=selected in [_vm_id(x['id'],provider) for x in inventory['items']] if code==0 else None
                if provider=='virtualbox' and instance['listed'] is True:
                    args=[str(path),'showvminfo',selected,'--machinereadable'];report['commands'].append(args)
                    info_code,info_out,info_error=_command(args)
                    if info_code==0:
                        data=dict(re.findall(r'^(UUID|name|ostype|VMState)="([^"]*)"\s*$',info_out,re.M))
                        if set(data)=={'UUID','name','ostype','VMState'}:
                            instance.update(uuid=_uuid(data['UUID']),name=data['name'],os_type=data['ostype'],state=data['VMState'],exists=True,error='')
                        else:instance['error']='实例信息不完整'
                    else:instance['error']='showvminfo未完成：'+info_error
                elif provider=='virtualbox' and instance['listed'] is False:instance.update(exists=False,error='所选UUID未在注册列表中')
                elif provider=='vmware':
                    config=Path(vm_id)
                    if not config.is_file():instance.update(exists=False,error='所选.vmx不存在')
                    elif config.stat().st_size>1024*1024:instance['error']='所选.vmx过大，未解析'
                    else:
                        content=config.read_text(encoding='utf-8',errors='replace')
                        values=dict(re.findall(r'^(uuid\.bios|guestOS|displayName)\s*=\s*"([^"]*)"\s*$',content,re.M))
                        raw=values.get('uuid.bios','').replace(' ','').replace('-','')
                        if re.fullmatch('[A-Fa-f0-9]{32}',raw):
                            instance.update(uuid=str(uuid.UUID(bytes_le=bytes.fromhex(raw))),name=values.get('displayName',config.stem),os_type=values.get('guestOS','unknown'),state='running' if instance['listed'] else None,exists=True,error='')
                        else:instance['error']='所选.vmx缺少可绑定来宾的uuid.bios；保留未知'
        except (OSError,ValueError,subprocess.TimeoutExpired) as exc:
            soft['error']='只读采集未完成：'+type(exc).__name__
    if guest_report is not None:
        facts['guest']=json.loads(Path(guest_report).read_text(encoding='utf-8-sig')) if isinstance(guest_report,(str,Path)) else guest_report
    report['collected_at']=datetime.now(timezone.utc).isoformat()
    analyze(spec,report)
    return report
