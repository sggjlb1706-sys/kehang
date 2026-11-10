"""Portable fixed task and script-free, offline-readable guide."""
from html import escape
from .rules import canonical, validate_task
from .guidance import plan
import hashlib


def export_package(spec):
    validate_task(spec)
    return dict(schema=1, kind='campuslab-course', task=spec,
                sha256=hashlib.sha256(canonical(spec).encode('utf-8')).hexdigest())


def import_package(value):
    if not isinstance(value,dict) or set(value)!={'schema','kind','task','sha256'} or type(value['schema']) is not int or value['schema']!=1 or value['kind']!='campuslab-course':
        raise ValueError('课程包结构无效')
    expected=export_package(value['task'])
    if value!=expected:
        raise ValueError('课程包摘要不匹配，请向教师重新取得原件')
    return value['task']


def guide_html(spec):
    validate_task(spec)
    sections=[]
    for mode,label in [('novice','新手 · 分步操作'),('standard','标准 · 关键步骤'),('quick','快捷 · 核对与复检')]:
        data=plan(spec,mode)
        steps=''.join('<li><strong>'+escape(s['title'])+'</strong><p>'+escape(s['body'])+'</p></li>' for s in data['steps'])
        links=' · '.join('<a href="'+escape(link['url'],quote=True)+'">'+escape(link['title'])+'</a>' for link in data['links'])
        sections.append('<details'+(' open' if mode=='novice' else '')+'><summary>'+label+'</summary><ol>'+steps+'</ol><p>'+links+'</p></details>')
    return '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>课航 · '+escape(spec['title'])+'</title><style>body{font:16px/1.7 system-ui,sans-serif;max-width:780px;margin:auto;padding:24px;color:#203230;background:#f6f7f3}h1{font-size:28px}details{border-top:1px solid #bdcbc7;padding:20px 0}summary{font-weight:bold;cursor:pointer}code{overflow-wrap:anywhere}a{color:#185e52}li{padding:8px 0}</style><p><strong>课航</strong> · 计算机课程学习与实训助手</p><h1>'+escape(spec['title'])+'</h1><p>'+escape(spec['source'])+'</p><p>固定任务摘要：<code>'+spec['id']+'</code></p><p>通过文件传递把本页和课程包交给学生；手机用浏览器打开本HTML，电脑导入课程包并运行检测。外部文档链接需要联网。localhost课程码只在原电脑有效。</p><p>课程包摘要用于内容一致性校验，不是教师数字签名；请通过可信渠道核对上面的任务摘要。步骤已阅读不代表检测通过。</p>'+''.join(sections)+'<p>本人手动准备 → 初检A → 按差异处理 → 同一任务、同一组件身份的复检B。来宾或GPU证据缺失仍为未知；脱敏交流副本不能用作复检原件。</p></html>'
