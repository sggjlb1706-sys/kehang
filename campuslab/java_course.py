"""Explicit JDK directory, same-source java/javac and one fixed temporary program."""
from datetime import datetime, timezone
import hashlib
import ntpath
import os
from pathlib import Path
import platform
import re
import subprocess
import tempfile

from .rules import absolute, seal, timestamp, version

SOURCE = '''public class CampusLabFixed {
    public static void main(String[] args) {
        int[] scores = {10, 20, 12};
        int total = 0;
        for (int score : scores) total += score;
        System.out.println(total);
        System.out.println(System.getProperty("java.home"));
    }
}
'''


def make_task(title=None):
    title=title or 'Java / JDK · 固定编译运行演示任务'
    if not isinstance(title,str) or not 1<=len(title.strip())<=100:raise ValueError('任务名称须为1—100字')
    return seal(dict(schema=1,title=title,scenario='java-jdk',source='本项目原创固定Java小程序；JDK21至25以下为演示配置，非学校统一要求',
        os='Windows',jdk=dict(min='21.0',max_exclusive='25.0'),verify='same-jdk-fixed-compile-v1',source_sha256=hashlib.sha256(SOURCE.encode()).hexdigest(),expected=42))


def validate_spec(spec):
    if not isinstance(spec,dict) or type(spec.get('schema')) is not int or spec.get('schema')!=1 or spec!=make_task(spec.get('title')):raise ValueError('JDK任务摘要或固定要求不匹配')
    return spec


def _object(value,keys,label):
    if not isinstance(value,dict) or set(value)!=set(keys):raise ValueError(label+'证据不完整')


def analyze(spec,report):
    validate_spec(spec)
    if not isinstance(report,dict) or type(report.get('schema')) is not int or report.get('schema')!=1 or report.get('task_id')!=spec['id']:raise ValueError('报告与JDK任务不一致')
    timestamp(report.get('collected_at'));target=report.get('target');facts=report.get('facts')
    _object(target,('requested','actual','exists'),'JDK目录');home=absolute(target['requested'])
    if target['exists'] is not None and type(target['exists']) is not bool:raise ValueError('JDK存在状态无效')
    if target['actual'] is not None and (absolute(target['actual'])!=home or target['exists'] is not True):raise ValueError('实际JDK目录不一致')
    _object(facts,('os','tools','compile','run'),'JDK事实');_object(facts['tools'],('java','javac'),'JDK工具')
    if facts['os'] is not None and not isinstance(facts['os'],str):raise ValueError('系统类型无效')
    for name,item in facts['tools'].items():
        _object(item,('path','sha256','exists','version','home','returncode','error'),name)
        if absolute(item['path'])!=absolute(ntpath.join(home,'bin',name+'.exe')):raise ValueError('java/javac必须属于明确选择的同一JDK目录')
        if item['exists'] is not None and type(item['exists']) is not bool or item['returncode'] is not None and type(item['returncode']) is not int or not isinstance(item['error'],str):raise ValueError('JDK工具证据类型无效')
        if item['version'] is not None and not isinstance(item['version'],str):raise ValueError('JDK版本类型无效')
        if item['home'] is not None:absolute(item['home'])
        if item['sha256'] is not None and (not isinstance(item['sha256'],str) or not re.fullmatch('[A-Fa-f0-9]{64}',item['sha256'])):raise ValueError('JDK工具摘要无效')
        if item['exists'] is not True and any(item[k] is not None for k in ('version','home','returncode','sha256')):raise ValueError('工具不存在时不能携带运行事实')
    for key in ('compile','run'):
        item=facts[key];_object(item,('returncode','stdout','error','home') if key=='run' else ('returncode','stdout','error'),key)
        if item['returncode'] is not None and type(item['returncode']) is not int or any(not isinstance(item[x],str) for x in ('stdout','error')):raise ValueError('编译运行证据类型无效')
    if facts['run']['home'] is not None:absolute(facts['run']['home'])
    if target['actual'] is None and (any(item['returncode'] is not None for item in facts['tools'].values()) or facts['compile']['returncode'] is not None or facts['run']['returncode'] is not None):raise ValueError('未确认JDK身份不得携带执行证据')
    if facts['run']['returncode'] is not None and facts['compile']['returncode']!=0:raise ValueError('未编译成功不得携带课程运行结果')
    checks=[]
    def check(key,status,observed,requirement):checks.append(dict(id=key,status=status,observed=observed,requirement=requirement))
    check('os','unknown' if facts['os'] is None else ('pass' if facts['os']=='Windows' else 'mismatch'),facts['os'],'Windows')
    for name,item in facts['tools'].items():
        state='missing' if item['exists'] is False else 'unknown';release=re.fullmatch(r'\d+\.\d+\.\d+',item['version'] or '')
        if release:state='pass' if version('21.0')<=version(item['version'])<version('25.0') else 'mismatch'
        if item['returncode'] is not None and (item['returncode']!=0 or item['error']):state='mismatch'
        check('java:'+name,state,item,'同一JDK中的 '+name+'，21.0至25.0以下')
    tools=list(facts['tools'].values())
    same='unknown' if any(x['home'] is None or x['sha256'] is None for x in tools) else ('pass' if all(absolute(x['home'])==home for x in tools) and tools[0]['version']==tools[1]['version'] else 'mismatch')
    check('java:identity',same,[dict(path=x['path'],home=x['home'],sha256=x['sha256']) for x in tools],'java/javac自身报告java.home等于所选JDK，版本一致，二进制摘要分别保存')
    compiled=facts['compile'];run=facts['run']
    check('java:compile','unknown' if compiled['returncode'] is None else ('pass' if compiled['returncode']==0 and not compiled['error'] else 'mismatch'),compiled,'固定源码在专用临时目录由所选javac编译，退出0')
    expected='42\n'+(run['home'] or '')+'\n'
    check('java:run','unknown' if run['returncode'] is None else ('pass' if run['returncode']==0 and run['home'] is not None and absolute(run['home'])==home and run['stdout'].replace('\r\n','\n')==expected and not run['error'] else 'mismatch'),run,'所选java运行本次编译产物，输出42及同一java.home')
    return dict(task_id=spec['id'],target=target,collected_at=report['collected_at'],checks=checks,passed=all(c['status']=='pass' for c in checks))


def compare_identity(before,after):
    if absolute(before['target']['requested'])!=absolute(after['target']['requested']):raise ValueError('复检必须使用同一JDK目录')
    for name in ('java','javac'):
        a,b=before['facts']['tools'][name],after['facts']['tools'][name]
        if absolute(a['path'])!=absolute(b['path']):raise ValueError('复检JDK工具位置不同')
        for key in ('sha256','home','version'):
            if a[key] is not None and b[key] is not None and (absolute(a[key])!=absolute(b[key]) if key=='home' else a[key]!=b[key]):raise ValueError('JDK工具身份已变更，请重新初检')


def collect(spec,target):
    validate_spec(spec);absolute(target);root=Path(target)
    report=dict(schema=1,task_id=spec['id'],collected_at=datetime.now(timezone.utc).isoformat(),target=dict(requested=target,actual=None,exists=root.is_dir()),
        facts=dict(os=platform.system(),tools={name:dict(path=str(root/'bin'/(name+'.exe')),sha256=None,exists=(root/'bin'/(name+'.exe')).is_file(),version=None,home=None,returncode=None,error='未运行') for name in ('java','javac')},
        compile=dict(returncode=None,stdout='',error='JDK身份未确认'),run=dict(returncode=None,stdout='',error='尚未编译运行',home=None)),commands=[])
    if root.is_dir():
        root=root.resolve();report['target']['actual']=str(root)
        env={k:v for k,v in os.environ.items() if k.upper() not in ('JAVA_TOOL_OPTIONS','_JAVA_OPTIONS','JDK_JAVA_OPTIONS','JDK_JAVAC_OPTIONS','CLASSPATH')}
        def execute(command,directory):
            report['commands'].append(command)
            return subprocess.run(command,cwd=directory,env=env,capture_output=True,timeout=25,text=True,encoding='utf-8',errors='replace')
        for name,item in report['facts']['tools'].items():
            path=Path(item['path'])
            if not path.is_file():continue
            if path.resolve().parent!=root/'bin':item['error']='工具链接指向所选JDK之外，未执行';continue
            try:
                item['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
                command=[str(path),'-XshowSettings:properties','-version'] if name=='java' else [str(path),'-J-XshowSettings:properties','-version']
                with tempfile.TemporaryDirectory(prefix='campuslab-jdk-version-') as temp:proc=execute(command,temp)
                item['returncode']=proc.returncode;text=proc.stdout+'\n'+proc.stderr
                home_match=re.search(r'^\s*java\.home\s*=\s*(.+)$',text,re.MULTILINE)
                release=re.search(r'(?:version\s+"|javac\s+)(\d+)(?:\.(\d+))?(?:\.(\d+))?',text)
                if home_match:item['home']=home_match[1].strip()
                if release:item['version']='.'.join(x or '0' for x in release.groups())
                item['error']='' if proc.returncode==0 and home_match and release else '无法取得JDK版本与java.home'
            except (OSError,ValueError,subprocess.TimeoutExpired) as exc:item['error']=type(exc).__name__+': '+str(exc)[:300]
        tools=report['facts']['tools']
        identities=all(x['home'] is not None and absolute(x['home'])==absolute(target) and x['returncode']==0 and not x['error'] for x in tools.values())
        if identities:
            with tempfile.TemporaryDirectory(prefix='campuslab-java-fixed-') as temporary:
                directory=Path(temporary);source=directory/'CampusLabFixed.java';source.write_text(SOURCE,encoding='utf-8')
                try:
                    compiled=execute([tools['javac']['path'],'-proc:none','-encoding','UTF-8','-d',temporary,str(source)],temporary)
                    report['facts']['compile']=dict(returncode=compiled.returncode,stdout=compiled.stdout,error=compiled.stderr[-1500:] if compiled.returncode else '')
                    if compiled.returncode==0:
                        run=execute([tools['java']['path'],'-cp',temporary,'CampusLabFixed'],temporary);lines=run.stdout.splitlines()
                        report['facts']['run']=dict(returncode=run.returncode,stdout=run.stdout,error=run.stderr[-1500:],home=lines[1] if len(lines)==2 else None)
                except (OSError,subprocess.TimeoutExpired) as exc:report['facts']['compile']['error']=type(exc).__name__+': '+str(exc)[:300]
    report['collected_at']=datetime.now(timezone.utc).isoformat();analyze(spec,report);return report
