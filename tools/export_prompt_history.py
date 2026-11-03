"""Preserve visible local dialogue with provenance; never export reasoning or tools."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re


def digest(data):
    return hashlib.sha256(data).hexdigest().upper()


def redact(text):
    text = re.sub(r'(?i)\bsk-[A-Za-z0-9_-]{8,}', '<密钥已删除>', text)
    text = re.sub(r'(?i)(Bearer\s+)[^\s\"\'<>]+', r'\1<密钥已删除>', text)
    text = re.sub(r'(?i)((?:ENVCHECK_AI_KEY|api[_-]?key|password|secret|access_token)[\"\' ]*\s*[:=]\s*[\"\']?)[^\s\"\'<>;,}]+', r'\1<敏感值已删除>', text)
    text = re.sub(r'(?i)[A-Z]:[\\/]Users[\\/][^\\/\s\"\'<>]+', r'C:\\Users\\<用户>', text)
    text = re.sub(r'\b(?:192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3})\b', '<私网地址>', text)
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', '<邮箱>', text)
    return text


def extract(raw):
    messages, excluded = [], {}
    for number, line in enumerate(raw.splitlines(), 1):
        row = json.loads(line)
        if row.get('type') != 'response_item':
            continue
        item = row.get('payload', {})
        role = item.get('role')
        if item.get('type') != 'message' or role not in ('user', 'assistant'):
            continue
        if item.get('channel') not in (None, 'commentary', 'final'):
            excluded['non_visible_channel'] = excluded.get('non_visible_channel', 0) + 1
            continue
        blocks = item.get('content', [])
        text = '\n'.join(b.get('text', '') for b in blocks if b.get('type') in ('input_text', 'output_text'))
        if not text.strip():
            continue
        context_prefixes = ('# AGENTS.md instructions', '<environment_context>', '<external_codex_apps_open_page>', '<turn_aborted>')
        if role == 'user' and text.lstrip().startswith(context_prefixes):
            excluded['injected_context'] = excluded.get('injected_context', 0) + 1
            continue
        safe = redact(text)
        messages.append(dict(source_line=number, timestamp=row.get('timestamp'), role=role,
                             channel=item.get('channel'), original_text_sha256=digest(text.encode('utf-8')),
                             text=safe, redacted=safe != text,
                             omitted_image_blocks=sum(b.get('type') in ('input_image', 'image') for b in blocks)))
    return messages, excluded


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', action='append', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    private = Path(__file__).resolve().parents[1] / 'private'
    private.mkdir(exist_ok=True)
    sources, index = {}, []
    for source in args.source:
        raw = source.read_bytes()
        # The current chat is append-only; record an immutable complete-line prefix.
        raw = raw[:raw.rfind(b'\n') + 1]
        meta = json.loads(raw.splitlines()[0]).get('payload', {})
        session_id = meta['id']
        messages, excluded = extract(raw.decode('utf-8-sig'))
        result = dict(session_id=session_id, source_file=source.name,
                      source_prefix_bytes=len(raw), source_prefix_sha256=digest(raw),
                      preserved_at=datetime.now(timezone.utc).isoformat(), messages=messages,
                      excluded=excluded, scope='Visible user/assistant text only; images, system/developer, tools and reasoning excluded',
                      official_complete_chain_review='not yet certified; source availability and image omissions remain explicit')
        target = args.output / (session_id + '.json')
        target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        readable = ['# 可见对话留档：' + session_id, '', '整理说明：脱敏可见文本；非完整原始会话导出，未认证符合赛事完整Prompt链要求。', '']
        for m in messages:
            readable += ['## {} · {} · 原记录行{}'.format(m['timestamp'], m['role'], m['source_line']), '', m['text'], '']
        target.with_suffix('.md').write_text('\n'.join(readable), encoding='utf-8')
        index.append(dict(session_id=session_id, source_file=source.name,
                          source_prefix_bytes=len(raw), source_prefix_sha256=digest(raw),
                          export=target.name, export_sha256=digest(target.read_bytes()),
                          readable_sha256=digest(target.with_suffix('.md').read_bytes()),
                          visible_messages=len(messages), redacted_messages=sum(m['redacted'] for m in messages),
                          user_messages=sum(m['role'] == 'user' for m in messages),
                          assistant_messages=sum(m['role'] == 'assistant' for m in messages)))
        sources[session_id] = str(source)
    (args.output / 'index.json').write_text(json.dumps(index, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (private / (args.output.name + '-source-map.json')).write_text(json.dumps(sources, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(exports=len(index), visible_messages=sum(x['visible_messages'] for x in index),
                          original_sources_modified=False, official_history_compliance='pending external confirmation')))


if __name__ == '__main__':
    main()
