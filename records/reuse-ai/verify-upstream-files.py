"""Verify retrieved official text bytes and record source manifests. No upstream code executes."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
record = json.loads((ROOT/'records/reuse-ai/upstream-heads-20261109.json').read_text(encoding='utf-8'))
groups = {}
for item in record['sources']:
    path = ROOT/'docs/third-party'/item['local']
    data = path.read_bytes()
    # The patch transport appends a final LF to text lacking it. Restore only
    # that one transport byte when the official retrieval's byte count proves it.
    if len(data) == item['expected_bytes']+1 and data.endswith(b'\n'):
        data = data[:-1]
        path.write_bytes(data)
    if len(data) != item['expected_bytes']:
        raise ValueError('Official byte count mismatch: '+item['local'])
    blob = hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    if item.get('upstream_git_blob_sha1') and item['upstream_git_blob_sha1'] != blob:
        raise ValueError('Official Git blob mismatch: '+item['local'])
    value = dict(item, sha256=hashlib.sha256(data).hexdigest(), bytes=len(data), git_blob_sha1=blob)
    groups.setdefault(item['local'].split('/')[0], []).append(value)
for group, files in groups.items():
    result = dict(retrieved_on='2026-11-09', files=files, upstream_code_executed=False,
                  dependency_installations=0, product_adaptation='campuslab/teaching.py' if group == 'educates' else None)
    (ROOT/'docs/third-party'/group/'manifest.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(dict(verified_files=sum(map(len, groups.values())), groups={k:len(v) for k,v in groups.items()},
                     official_git_blob_comparisons=sum('upstream_git_blob_sha1' in v for values in groups.values() for v in values))))
