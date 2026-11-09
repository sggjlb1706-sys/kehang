"""Record final evidence consistency without rerunning hardware or changing old results."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess
import fitz
from campuslab.rules import task,analyze,compare


def main():
    root=Path(__file__).resolve().parents[1]
    def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest().upper()
    product='3dddd3314d63496965c2f23ca3a01a43b20167d1'
    product_names=subprocess.check_output(['git','ls-tree','-r','--name-only',product],cwd=root,text=True,encoding='utf-8').splitlines()
    sources={name:sha(root/name) for name in product_names if name.startswith(('campuslab/','web/')) or name=='Start-Web.ps1'}
    for name in sources:
        assert subprocess.check_output(['git','show',product+':'+name],cwd=root)==(root/name).read_bytes(),name
    browser={}
    for path in ['records/browser/20261108T104745025392Z/results.json','records/browser/20261108T104745480764Z-node/results.json',
                 'records/browser/20261108T104746040882Z-courses/results.json','records/courses/review-ui/20261108T105547Z/results.json']:
        data=json.loads((root/path).read_text(encoding='utf-8'));assert data['status']=='passed'
        assert all(sha(root/n)==h for n,h in data['source_sha256'].items()),path
        browser[path]=dict(checks=len(data['checks']),source_sha_matches=True,sha256=sha(root/path))
    results={}
    for scenario,directory,a,b in [('pytorch-cpu','records/courses/torch/float32-retest','cpu-A.json','cpu-B.json'),
                                  ('pytorch-gpu','records/courses/torch/float32-retest','gpu-A.json','gpu-B.json'),
                                  ('local-qwen','records/courses/model/20261108T103903Z','A.json','B.json')]:
        before=json.loads((root/directory/a).read_text(encoding='utf-8'));after=json.loads((root/directory/b).read_text(encoding='utf-8'))
        result=compare(task(scenario),before,after);assert result['after']['passed']
        results[scenario]=dict(outcome=result['outcome'],checks=len(result['after']['checks']),real_local=True,recomputed_only=True)
    vm=json.loads((root/'records/courses/vm/vmware-actual-elevated-host.json').read_text(encoding='utf-8'))
    analyzed=analyze(task('vm-linux'),vm);assert not analyzed['passed']
    results['vm-linux']=dict(passed=False,states={x['id']:x['status'] for x in analyzed['checks']},real_guest=False)
    pdf=root/'output/pdf/AI实验环境管家_课程能力版_技术文档.pdf'
    with fitz.open(pdf) as doc:
        assert len(doc)<=30
        pdf_result=dict(path=pdf.relative_to(root).as_posix(),pages=len(doc),sha256=sha(pdf))
    status=dict(recorded_at=datetime.now(timezone.utc).isoformat(),product_head=product,product_sources=sources,
        unit_tests=69,unit_record='records/courses/unit-review-final.txt',browser=browser,real_results=results,pdf=pdf_result,
        independent_review='4 P2 and 1 P3 closed; no new blockers',independent_delta_sha256=sha(root/'records/review/courses-independent-delta.md'),
        materials_review='9-page PDF and current handoff independently verified; no new material blockers',
        materials_review_sha256=sha(root/'records/review/courses-materials-delta.md'),
        formal_mp4=False,three_complete_prompt_chains_certified=False,reviewer_remote_repository=False,uploaded=False,official_eligibility_certified=False,
        physical_phone=False,second_computer=False,real_guest=False,real_ai_diagnosis=False,installs=0,vm_starts=0,paid_requests=0,published=False,
        remaining=['Formal MP4 and authentic AI collaboration footage','Three complete authentic Prompt chains not confirmed','Reviewer-accessible repository',
                   'Real Linux guest/VM instance, second computer, physical phone, clean Windows and independent novice',
                   'Real AI diagnosis, other GPU/CPU-only combinations and CPU Qwen inference','User upload and receipt'])
    out=root/'records/courses/final-status.json';out.write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(product_head=product,source_files=len(sources),browser_groups=sum(x['checks'] for x in browser.values()),unit_tests=69,pdf=pdf_result),ensure_ascii=False))


if __name__=='__main__':main()
