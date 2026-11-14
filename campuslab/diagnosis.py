"""Single opt-in HTTP interface. No retries, command execution or verdict mutation."""
import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

SYSTEM = '你是环境证据解释助手。只根据用户提供的检查事实与报错提出诊断假设、手动操作步骤和复检方法。不得声称检测通过、捏造硬件或执行命令。信息不足时明确指出。'


def redact(text):
    text=re.sub(r'(?i)\bsk-[A-Za-z0-9_-]{8,}','<密钥已删除>',text)
    text=re.sub(r'(?i)(Bearer\s+)[^\s"\'<>]+',r'\1<密钥已删除>',text)
    text=re.sub(r'(?i)((?:api[_-]?key|password|secret|access_token)["\' ]*\s*[:=]\s*["\']?)[^\s"\'<>;,}]+',r'\1<敏感值已删除>',text)
    text=re.sub(r'(?i)[A-Z]:[\\/]+Users[\\/]+[^\\/\s"\'<>]+','<个人用户目录>',text)
    text=re.sub(r'\b(?:192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3})\b','<私网地址>',text)
    text=re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b','<邮箱>',text)
    return text


def redact_value(value):
    if isinstance(value,str):return redact(value)
    if isinstance(value,list):return [redact_value(x) for x in value]
    if isinstance(value,dict):return {k:redact_value(v) for k,v in value.items()}
    return value


def configuration():
    url=os.environ.get('CAMPUSLAB_AI_URL','').strip()
    model=os.environ.get('CAMPUSLAB_AI_MODEL','').strip()
    parsed=urlsplit(url)
    valid=bool(url and model and parsed.hostname and not parsed.username and not parsed.password and not parsed.query and not parsed.fragment and
               (parsed.scheme=='https' or (parsed.scheme=='http' and parsed.hostname in ('127.0.0.1','localhost'))))
    return dict(configured=valid,destination=url if valid else None,model=model if valid else None,system=SYSTEM)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):
        return None


def diagnose(preview, consent):
    config=configuration()
    if consent is not True:
        raise ValueError('需要本人确认发送内容和目的地并同意')
    if not config['configured']:
        raise ValueError('AI未配置；规则结果仍然可用')
    if not isinstance(preview,str) or not 1<=len(preview)<=10000:
        raise ValueError('预览内容须为1—10000字')
    return model_request(config, [dict(role='system',content=SYSTEM),dict(role='user',content=preview)])


def model_request(config, messages):
    key=os.environ.get('CAMPUSLAB_AI_KEY','')
    payload=dict(model=config['model'],messages=messages,temperature=0,max_tokens=1024)
    headers={'Content-Type':'application/json','Accept':'application/json'}
    if key:
        headers['Authorization']='Bearer '+key
    request=Request(config['destination'],data=json.dumps(payload,ensure_ascii=False).encode('utf-8'),headers=headers)
    try:
        handlers=[NoRedirect]
        if urlsplit(config['destination']).hostname in ('127.0.0.1','localhost'):
            handlers.append(ProxyHandler({}))
        with build_opener(*handlers).open(request,timeout=25) as response:
            content_type=response.headers.get('Content-Type','').split(';')[0]
            length=response.headers.get('Content-Length')
            if content_type!='application/json' or length is None or not length.isdigit() or int(length)>131072:
                raise ValueError('diagnostic_protocol')
            raw=response.read(131073)
            if len(raw)!=int(length) or len(raw)>131072:
                raise ValueError('diagnostic_truncated')
            data=json.loads(raw)
            choices=data.get('choices')
            if not isinstance(choices,list) or len(choices)!=1:
                raise ValueError('diagnostic_json')
            choice=choices[0]; message=choice.get('message',{})
            content=message.get('content')
            if choice.get('finish_reason')!='stop' or message.get('tool_calls') or not isinstance(content,str) or not content.strip():
                raise ValueError('diagnostic_json')
            if key:
                content=content.replace(key,'<密钥已删除>')
            return dict(completed=True, explanation=redact(content), evidence_verdict_changed=False)
    except (HTTPError,URLError,TimeoutError,OSError,ValueError,KeyError,TypeError,AttributeError) as exc:
        category=str(exc) if isinstance(exc,ValueError) and str(exc).startswith('diagnostic_') else type(exc).__name__
        return dict(completed=False,error=category,explanation='AI诊断未完成；原始检查结果保持。',evidence_verdict_changed=False)
