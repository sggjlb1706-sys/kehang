"""Developer-triggered real offline regression, not AI error diagnosis."""
from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from campuslab.collect import collect
from campuslab.rules import analyze,compare,task


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target',required=True)
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    out=root/'records/courses/model'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out.mkdir(parents=True)
    spec=task('local-qwen');target=args.target
    model=r'D:\传智杯\artifacts\local-model\Qwen2.5-0.5B-Instruct'
    def save(name,value):
        (out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    save('task.json',spec)
    before=collect(spec,target,model_dir=model);save('A.json',before);save('A-analysis.json',analyze(spec,before))
    after=collect(spec,target,model_dir=model,infer=True);save('B.json',after);save('B-analysis.json',analyze(spec,after))
    result=compare(spec,before,after);save('comparison.json',result)
    save('execution.json',dict(command=['python','-B','-m','tools.course_model_retest','--target',target],purpose=__doc__,
        source_sha256={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest().upper() for p in (root/'campuslab').glob('*.py')},
        developer_triggered=True,download_calls=0,installation_calls=0,paid_requests=0,real_ai_diagnosis=False))
    print(json.dumps(dict(path=str(out),outcome=result['outcome'],passed=result['after']['passed'])))
    if not result['after']['passed']:raise SystemExit(1)


if __name__=='__main__':main()
