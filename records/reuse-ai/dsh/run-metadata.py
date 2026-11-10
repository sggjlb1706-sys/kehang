"""Real local metadata probes only. Never launches DSH, reads credentials or calls a model."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from campuslab.dsh_course import make_task, collect, analyze, compare_identity

OUT = Path(__file__).resolve().parent/'real-metadata'
OUT.mkdir(exist_ok=False)
targets = dict(desktop=r'C:\Program Files\DeepSeek Harness\DeepSeek Harness.exe', cli=r'D:\Program Files\nodejs\node.exe')
summary = dict(collected_at=datetime.now(timezone.utc).isoformat(), real_dsh_execution=False, model_requests=0,
               credential_files_read=False, scope='Developer-selected known Node and one standard desktop candidate; not an exhaustive installation scan', routes={})
for route, target in targets.items():
    spec = make_task(route=route)
    (OUT/(route+'-task.json')).write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding='utf-8')
    kwargs = dict(package_json=r'D:\Program Files\nodejs\node_modules\@deepseek-ai\dsh\package.json') if route == 'cli' else {}
    reports = []
    for stage in ('A', 'B'):
        report = collect(spec, target, **kwargs)
        reports.append(report)
        (OUT/(route+'-'+stage+'.json')).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        (OUT/(route+'-'+stage+'-analysis.json')).write_text(json.dumps(analyze(spec, report), ensure_ascii=False, indent=2), encoding='utf-8')
    compare_identity(*reports)
    summary['routes'][route] = dict(passed=analyze(spec, reports[-1])['passed'], same_identity=True,
        states={c['id']: c['status'] for c in analyze(spec, reports[-1])['checks']})
summary['source_sha256'] = {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ('campuslab/dsh_course.py', 'campuslab/teaching.py')}
(OUT/'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(summary, ensure_ascii=True))
