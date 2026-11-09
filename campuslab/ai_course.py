"""Fixed DeepSeek learning tasks; the manual CLI owns any single API send."""
from datetime import datetime, timezone
import getpass
import hashlib
import json
import ntpath
import os
from pathlib import Path
import platform
import socket
import subprocess
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, HTTPRedirectHandler, build_opener

from .rules import absolute, canonical, seal, timestamp, version
from .diagnosis import redact

ENDPOINT='https://api.deepseek.com/chat/completions'
MODEL='deepseek-flash'
QUESTION='演示CSV数据 score\n10\n14\n18\n。计算 total、count、mean。只返回JSON对象，键恰为total、count、mean，不要代码围栏。'
SYSTEM='你是数据分析课程练习助手。依据给出的演示数据计算，只输出要求的JSON，不访问工具或外部数据。'
EXPECTED={'total':42,'count':3,'mean':14}
SOURCES=[dict(title='DeepSeek 官方网页与客户端下载',url='https://www.deepseek.com/'),
         dict(title='DeepSeek API 官方入门与当前模型',url='https://api-docs.deepseek.com/'),
         dict(title='Qwen Chat 官方入口（指导路线）',url='https://chat.qwen.ai/'),
         dict(title='豆包官方入口（指导路线）',url='https://www.doubao.com/chat/')]


def make_task(title=None):
    return _make('deepseek-api',title or 'DeepSeek API · 固定数据练习',
                 python={'min':'3.10','max_exclusive':'3.15'},
                 api={'provider':'DeepSeek','endpoint':ENDPOINT,'model':MODEL,'protocol':'chat-completions'},
                 exercise={'system':SYSTEM,'question':QUESTION,'expected':EXPECTED},verify='deepseek-fixed-json-v1')


def make_web_task(title=None):
    return _make('ai-web-deepseek',title or 'DeepSeek 网页/客户端 · 课程提问',
                 provider='DeepSeek',entry='https://chat.deepseek.com/',
                 exercise={'question':QUESTION,'expected':EXPECTED},verify='self-record-and-fixed-artifact-v1')


def _make(scenario,title,**fields):
    if not isinstance(title,str) or not 1<=len(title.strip())<=100:
        raise ValueError('任务名称须为1—100字')
    return seal(dict(schema=1,scenario=scenario,title=title,source='本项目演示课程；官方接口资料核对于2026-11-09',os='Windows',**fields))


def validate_spec(spec):
    if not isinstance(spec,dict) or type(spec.get('schema')) is not int or spec.get('schema')!=1:
        raise ValueError('AI课程快照类型无效')
    expected=make_web_task(spec.get('title')) if spec.get('scenario')=='ai-web-deepseek' else make_task(spec.get('title'))
    if spec!=expected: raise ValueError('AI课程仅接受已审查的固定任务')
    return spec


def preview(spec):
    validate_spec(spec)
    return dict(endpoint=spec['api']['endpoint'],payload=dict(model=spec['api']['model'],
        messages=[dict(role='system',content=SYSTEM),dict(role='user',content=QUESTION)],
        thinking={'type':'disabled'},stream=False,max_tokens=128,response_format={'type':'json_object'}))


def validate_preview(spec,value):
    if not isinstance(value,dict) or set(value)!={'endpoint','payload'} or value['endpoint']!=spec['api']['endpoint']:
        raise ValueError('仅允许任务固定的官方目的地')
    expected=preview(spec);payload=value['payload']
    if not isinstance(payload,dict) or set(payload)!=set(expected['payload']): raise ValueError('请求结构无效')
    for key in set(payload)-{'messages'}:
        if payload[key]!=expected['payload'][key] or type(payload[key]) is not type(expected['payload'][key]):
            raise ValueError('模型、协议与资源限制须保持任务要求')
    messages=payload['messages']
    if not isinstance(messages,list) or len(messages)!=2: raise ValueError('需要系统说明及实际用户内容')
    for message,role in zip(messages,('system','user')):
        if not isinstance(message,dict) or set(message)!={'role','content'} or message['role']!=role or not isinstance(message['content'],str) or not 1<=len(message['content'])<=4000:
            raise ValueError('消息无效或过长')
    return value


def empty_run(category='not_called'):
    return dict(attempted=False,category=category,http_status=None,model=None,role=None,finish_reason=None,content='',latency_ms=None)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): return None


def urlopen_once(request):
    """No retry or redirect; omit provider error bodies that could echo secrets."""
    try:
        with build_opener(NoRedirect).open(request,timeout=25) as response:
            if response.headers.get_content_type()!='application/json':raise ValueError('content_type')
            lengths=response.headers.get_all('Content-Length',[])
            if len(lengths)>1 or lengths and not lengths[0].isdigit():raise ValueError('content_length')
            raw=response.read(65537)
            if len(raw)>65536 or lengths and len(raw)!=int(lengths[0]): raise ValueError('response_length')
            return response.status,raw
    except HTTPError as exc:
        code=exc.code;exc.close();return code,b''


def call_api(spec,value,key,consent):
    validate_preview(spec,value)
    if consent is not True: return empty_run()
    if not key: return empty_run('unconfigured')
    run=empty_run();run['attempted']=True;start=time.monotonic()
    request=Request(value['endpoint'],data=canonical(value['payload']).encode('utf-8'),
        headers={'Content-Type':'application/json','Accept':'application/json','Authorization':'Bearer '+key})
    try:
        status,raw=urlopen_once(request);run['http_status']=status
        if status!=200:
            run['category']={400:'protocol',401:'authentication',402:'balance',403:'authentication',404:'model_or_protocol',422:'model_or_protocol',429:'rate_limit'}.get(status,'server' if status>=500 else 'protocol')
        else:
            def pairs(items):
                result={}
                for name,item in items:
                    if name in result:raise ValueError('duplicate_json')
                    result[name]=item
                return result
            def constant(value):raise ValueError('invalid_json_number')
            data=json.loads(raw,object_pairs_hook=pairs,parse_constant=constant)
            choices=data.get('choices')
            if not isinstance(choices,list) or len(choices)!=1: raise ValueError('protocol')
            choice=choices[0];message=choice.get('message',{})
            if message.get('tool_calls') or not isinstance(message.get('content'),str): raise ValueError('protocol')
            metadata=[data.get('model'),message.get('role'),choice.get('finish_reason')]
            if any(not isinstance(item,str) or len(item)>200 for item in metadata):raise ValueError('protocol')
            metadata=[redact(item.replace(key,'<密钥已删除>')) for item in metadata]
            run.update(category='ok',model=metadata[0],role=metadata[1],finish_reason=metadata[2],
                       content=redact(message['content'].replace(key,'<密钥已删除>'))[:4096])
    except (TimeoutError,socket.timeout): run['category']='timeout'
    except URLError as exc: run['category']='timeout' if isinstance(exc.reason,(TimeoutError,socket.timeout)) else 'network'
    except (ValueError,KeyError,TypeError,AttributeError): run['category']='protocol'
    except OSError: run['category']='runtime'
    run['latency_ms']=round((time.monotonic()-start)*1000)
    return run


def _base(spec,report,fact_keys):
    validate_spec(spec)
    if not isinstance(report,dict) or type(report.get('schema')) is not int or report['schema']!=1 or report.get('task_id')!=spec['id']:
        raise ValueError('报告与课程快照不一致')
    timestamp(report.get('collected_at'));target=report.get('target');facts=report.get('facts')
    if not isinstance(target,dict) or set(target)!={'requested','actual','exists'} or target['exists'] not in (True,False,None) or (target['exists'] is not None and type(target['exists']) is not bool):
        raise ValueError('目标身份不完整')
    absolute(target['requested'])
    if target['actual'] is not None and (absolute(target['actual'])!=absolute(target['requested']) or target['exists'] is not True):
        raise ValueError('实际目标与所选环境不一致')
    if not isinstance(facts,dict) or set(facts)!=set(fact_keys): raise ValueError('事实集合不完整')
    return target,facts


def _check(checks,key,state,observed,requirement):
    checks.append(dict(id=key,status=state,observed=observed,requirement=requirement))


def _grade(text):
    try:
        value=json.loads(text)
        return isinstance(value,dict) and set(value)==set(EXPECTED) and all(type(value[k]) in (int,float) and value[k]==v for k,v in EXPECTED.items())
    except (ValueError,TypeError): return False


def analyze(spec,report):
    target,facts=_base(spec,report,('os','python','stdlib','request','run'))
    validate_preview(spec,facts['request']);run=facts['run']
    if not isinstance(run,dict) or set(run)!=set(empty_run()) or type(run['attempted']) is not bool or not isinstance(run['category'],str) or not isinstance(run['content'],str):
        raise ValueError('API运行证据不完整')
    for key in ('http_status','latency_ms'):
        if run[key] is not None and (type(run[key]) is not int or run[key]<0): raise ValueError('API数值证据无效')
    for key in ('model','role','finish_reason'):
        if run[key] is not None and not isinstance(run[key],str): raise ValueError('API协议字段无效')
    if facts['stdlib'] is not None and type(facts['stdlib']) is not bool: raise ValueError('标准库状态无效')
    if facts['os'] is not None and not isinstance(facts['os'],str): raise ValueError('系统状态无效')
    if target['actual'] is None and (facts['python'] is not None or facts['stdlib'] is not None or run['attempted']): raise ValueError('未确认解释器不可声称运行')
    if not run['attempted'] and any(run[k] is not None for k in ('http_status','model','role','finish_reason','latency_ms')): raise ValueError('未调用不可带响应证据')
    checks=[]
    _check(checks,'os','unknown' if facts['os'] is None else ('pass' if facts['os']=='Windows' else 'mismatch'),facts['os'],'Windows')
    py=facts['python'];state='missing' if target['exists'] is False else 'unknown'
    if py is not None: state='pass' if version('3.10')<=version(py)<version('3.15') else 'mismatch'
    _check(checks,'python',state,py,spec['python'])
    _check(checks,'api:dependency','unknown' if facts['stdlib'] is None else ('pass' if facts['stdlib'] else 'missing'),facts['stdlib'],'所选Python可导入urllib.request/ssl/json，无新增SDK依赖')
    _check(checks,'api:request','pass' if facts['request']==preview(spec) else 'mismatch',facts['request'],'实际目的地、模型与本固定数据练习；编辑为其他问题不能完成原任务')
    state='unknown' if not run['attempted'] else ('pass' if run['category']=='ok' and run['http_status']==200 and run['role']=='assistant' and run['finish_reason']=='stop' and run['model']==MODEL else 'mismatch')
    _check(checks,'api:protocol',state,{k:v for k,v in run.items() if k!='content'},'实际非截断Chat Completions响应，固定模型、assistant与stop；HTTP200本身不足')
    _check(checks,'api:exercise','unknown' if not run['attempted'] else ('pass' if state=='pass' and _grade(run['content']) else 'mismatch'),run['content'],EXPECTED)
    return dict(task_id=spec['id'],target=target,collected_at=report['collected_at'],checks=checks,passed=all(c['status']=='pass' for c in checks))


def compare_identity(before,after):
    if 'request' not in before['facts']: return
    if before['facts']['request']!=after['facts']['request']:
        raise ValueError('复检须保持提供方、目的地、模型和实际发送内容；改变后重新初检')


def web_record_template(spec):
    validate_spec(spec)
    return dict(task_id=spec['id'],provider='DeepSeek',entry=spec['entry'],prompt=QUESTION,
                completed=False,checked_sources=False,response='')


def analyze_web(spec,report):
    target,facts=_base(spec,report,('record',));record=facts['record'];checks=[]
    if record is not None:
        expected=web_record_template(spec)
        if not isinstance(record,dict) or set(record)!=set(expected) or any(record[k]!=expected[k] for k in ('task_id','provider','entry','prompt')) or any(type(record[k]) is not bool for k in ('completed','checked_sources')) or not isinstance(record['response'],str) or len(record['response'])>8000:
            raise ValueError('本人学习记录无效；不导入无关聊天')
    _check(checks,'web:workspace','pass' if target['actual'] else ('missing' if target['exists'] is False else 'unknown'),target,'明确的练习目录')
    _check(checks,'web:self-record','pass' if record and record['completed'] and record['checked_sources'] else 'unknown',
           dict(completed=bool(record and record['completed']),checked_sources=bool(record and record['checked_sources']),source='本人填写，非自动登录验证'),'本人完成提问并独立核对结果/来源')
    _check(checks,'web:artifact','unknown' if not record or not record['response'] else ('pass' if _grade(record['response']) else 'mismatch'),record['response'] if record else None,EXPECTED)
    _check(checks,'web:login','unknown',None,'本工具不取得账号、登录或远端模型连接证据')
    return dict(task_id=spec['id'],target=target,collected_at=report['collected_at'],checks=checks,passed=False,
                learning_completed=all(c['status']=='pass' for c in checks if c['id']!='web:login'))


def collect_web(spec,target,record_path=None):
    validate_spec(spec);absolute(target);path=Path(target)
    record=None
    if record_path:
        candidate=Path(record_path)
        if candidate.stat().st_size>16000: raise ValueError('学习记录过大')
        record=json.loads(candidate.read_text(encoding='utf-8-sig'))
    report=dict(schema=1,task_id=spec['id'],collected_at=datetime.now(timezone.utc).isoformat(),
        target=dict(requested=target,actual=str(path.resolve()) if path.is_dir() else None,exists=path.is_dir()),facts=dict(record=record))
    analyze_web(spec,report);return report


def collect(spec,target,preview_path=None,send=False):
    validate_spec(spec);absolute(target);path=Path(target)
    if preview_path and Path(preview_path).stat().st_size>32768:raise ValueError('请求预览过大')
    value=json.loads(Path(preview_path).read_text(encoding='utf-8-sig')) if preview_path else preview(spec)
    validate_preview(spec,value)
    report=dict(schema=1,task_id=spec['id'],collected_at=datetime.now(timezone.utc).isoformat(),
        target=dict(requested=target,actual=None,exists=path.is_file()),
        facts=dict(os=platform.system(),python=None,stdlib=None,request=value,run=empty_run()))
    if (path.parent/'.campuslab-tool-runtime').exists(): raise ValueError('工具运行时不能作为课程Python')
    key='';consent=False
    if send and path.is_file():
        print('实际目的地及全部发送内容（密钥仅随后在终端输入）：\n'+json.dumps(value,ensure_ascii=False,indent=2))
        digest=hashlib.sha256(canonical(value).encode()).hexdigest()
        consent=input('确认可能产生费用；仅同意这一次请键入 SEND '+digest[:12]+' ：').strip()=='SEND '+digest[:12]
        if consent: key=getpass.getpass('本次API密钥（不保存，不读取其他工具凭据）：')
        if key and key in canonical(value):raise ValueError('请求预览含本次密钥，请删除敏感内容后重新确认；未发送、未保存报告')
    if path.is_file():
        try:
            proc=subprocess.run([str(path),'-B','-I',str(Path(__file__).with_name('ai_probe.py'))],
                input=json.dumps(dict(request=value,key=key,consent=consent),ensure_ascii=False),capture_output=True,
                timeout=35,encoding='utf-8',errors='replace',env={k:v for k,v in os.environ.items() if not k.startswith('PYTHON')})
            if proc.returncode: raise ValueError('probe_failed')
            data=json.loads(proc.stdout);report['target']['actual']=data.pop('actual');report['facts'].update(data)
        except subprocess.TimeoutExpired: report['facts']['run']=empty_run('runtime_timeout')
        except (OSError,ValueError,TypeError): report['facts']['run']=empty_run('runtime')
    key=''
    analyze(spec,report);return report
