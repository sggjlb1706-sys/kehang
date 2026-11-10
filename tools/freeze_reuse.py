"""Freeze reviewed product and selected new evidence without mutating old releases."""
from datetime import datetime,timezone
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest().upper()
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--final',action='store_true');args=parser.parse_args()
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    files=[p for folder in ('campuslab','web','tests','docs/third-party') for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    product={p.relative_to(ROOT).as_posix():sha(p) for p in files}
    for name in product:
        if name.startswith(('campuslab/','web/','tests/')):
            if subprocess.check_output(['git','show',head+':'+name],cwd=ROOT)!=(ROOT/name).read_bytes():raise ValueError('Uncommitted product: '+name)
    records=['records/browser/20261109T082514365971Z/results.json','records/browser/20261109T082515110174Z-courses/results.json',
             'records/browser/20261109T082524188235Z-node/results.json','records/reuse-ai/browser-ai/20261109T082513596289Z/results.json',
             'records/reuse-ai/browser-data/20261109T082545764681Z/results.json']
    if args.final:
        records=[]
        for pattern in ('records/browser/*Z/results.json','records/browser/*Z-courses/results.json','records/browser/*Z-node/results.json','records/reuse-ai/browser-ai/*/results.json','records/reuse-ai/browser-data/*/results.json'):
            matching=[]
            for path in sorted(ROOT.glob(pattern)):
                data=json.loads(path.read_text(encoding='utf-8'))
                if data.get('status')=='passed' and all(sha(ROOT/n)==h.upper() for n,h in data['source_sha256'].items()):matching.append(path)
            if not matching:raise ValueError('No current passing evidence: '+pattern)
            records.append(matching[-1].relative_to(ROOT).as_posix())
    groups=0
    for name in records:
        data=json.loads((ROOT/name).read_text(encoding='utf-8'));assert data['status']=='passed'
        for source,digest in data['source_sha256'].items():assert sha(ROOT/source)==digest.upper(),source
        groups+=len(data['checks'])
    selected=records+['records/courses/model/20261109T082553Z/A.json','records/courses/model/20261109T082553Z/B.json',
        'records/courses/model/20261109T082553Z/comparison.json','records/reuse-ai/unit-final-pre-review-2.txt',
        'records/reuse-ai/baseline-independent.md','records/reuse-ai/baseline-supplement-independent.md']
    if args.final:
        selected.extend(['records/reuse-ai/review-fixes-green.txt','records/review/reuse-ai-independent-product.md'])
        model=sorted((ROOT/'records/courses/model').glob('*/B-analysis.json'))[-1]
        assert json.loads(model.read_text(encoding='utf-8'))['passed']
        selected.extend(p.relative_to(ROOT).as_posix() for p in model.parent.iterdir() if p.is_file())
    for folder in ('notebook','java','sqlite','dsh'):
        selected.extend(p.relative_to(ROOT).as_posix() for p in (ROOT/'records/reuse-ai'/folder).rglob('*') if p.is_file())
    result=dict(frozen_at=datetime.now(timezone.utc).isoformat(),product_head=head,source_sha256=product,
        evidence_sha256={n:sha(ROOT/n) for n in sorted(set(selected))},browser_records=records,browser_groups=groups,
        ui_race_record=sorted(ROOT.glob('records/courses/review-ui/*/results.json'))[-1].relative_to(ROOT).as_posix() if args.final else 'records/courses/review-ui/20261109T082531Z/results.json',unit_tests=115 if args.final else 112,
        actual_api_calls=0,actual_dsh_tasks=0,physical_phone=False,second_device=False,
        scope='Current product/tests/adopted and reviewed third-party bytes; selected actual and explicitly constructed evidence. Materials/delivery not yet reviewed.')
    path=ROOT/('records/review/reuse-ai-final-candidate.json' if args.final else 'records/review/reuse-ai-candidate.json')
    with path.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps(dict(product_head=head,source_files=len(product),browser_groups=groups,manifest_sha256=sha(path))))
if __name__=='__main__':main()
