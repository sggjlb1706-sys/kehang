from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from campuslab.torch_course import make_task, collect, analyze, compare_identity
root = Path('records/courses/torch/float32-retest')
root.mkdir()
summary = {'started_at': datetime.now(timezone.utc).isoformat(), 'target': r'D:\ANACONDA\envs\pytorch\python.exe', 'evidence_kind': 'real_local_existing_environment', 'installs': 0, 'network_requests': 0, 'runs': []}
for gpu in (False, True):
    label = 'gpu' if gpu else 'cpu'
    spec = make_task(gpu_required=gpu)
    (root/(label+'-task.json')).write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding='utf-8')
    reports = []
    for stage in ('A', 'B'):
        started = time.monotonic()
        report = collect(spec, summary['target'], gpu_run=gpu and stage == 'B')
        result = analyze(spec, report)
        name = label+'-'+stage
        (root/(name+'.json')).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        (root/(name+'-analysis.json')).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        reports.append(report)
        summary['runs'].append({'name': name, 'seconds': time.monotonic()-started, 'passed': result['passed'], 'states': {c['id']:c['status'] for c in result['checks']}, 'commands': report['commands']})
        print(name, result['passed'], flush=True)
    compare_identity(*reports)
    a, b = [analyze(spec, report) for report in reports]
    summary[label+'_comparison'] = {'same_interpreter_and_gpu': True, 'outcome': 'stable-pass' if a['passed'] and b['passed'] else 'verified' if b['passed'] else 'incomplete'}
summary['finished_at'] = datetime.now(timezone.utc).isoformat()
summary['source_sha256'] = {str(p):hashlib.sha256(p.read_bytes()).hexdigest().upper() for p in (Path('campuslab/torch_course.py'), Path('campuslab/torch_probe.py'), Path('tests/test_torch_course.py'))}
(root/'real-summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(summary, ensure_ascii=True), flush=True)
