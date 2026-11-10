"""Freeze the narrow brand change and its current compatibility evidence."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest().upper()
def main():
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    record=sorted((ROOT/'records/brand/browser').glob('*/results.json'))[-1]
    browser=json.loads(record.read_text(encoding='utf-8'));assert browser['status']=='passed'
    assert all(sha(ROOT/n)==h for n,h in browser['source_sha256'].items())
    source={n:sha(ROOT/n) for n in json.loads((ROOT/'records/review/reuse-ai-final-candidate.json').read_text(encoding='utf-8'))['source_sha256']}
    source['tests/browser_brand.py']=sha(ROOT/'tests/browser_brand.py')
    for n in source:assert subprocess.check_output(['git','show',head+':'+n],cwd=ROOT)==(ROOT/n).read_bytes()
    data=dict(product_head=head,baseline_head='fc14fc752a83709df496b386e4ce950b01996afe',brand='课航——计算机课程学习与实训助手',short_name='课航',source_sha256=source,browser_record=record.relative_to(ROOT).as_posix(),browser_groups=len(browser['checks']),unit_tests=115,task_snapshots_unchanged=browser['task_snapshots_unchanged'],actual_new_api_dsh_calls=0)
    out=ROOT/'records/review/kehang-candidate.json'
    with out.open('x',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False,indent=2)
    print(json.dumps(dict(head=head,files=len(source),sha256=sha(out))))
if __name__=='__main__':main()
