"""Actual local read-only recheck. Does not start VMs or collect a guest."""
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from campuslab.rules import compare
from campuslab.vm_course import collect,make_task

out=Path(__file__).parent
spec=make_task()
target=r'C:\Program Files (x86)\VMware\VMware Workstation\vmrun.exe'
before=json.loads((out/'vmware-actual-elevated-host.json').read_text(encoding='utf-8'))
after=collect(spec,target)
with (out/'vmware-actual-retest-B.json').open('x',encoding='utf-8') as output:
    json.dump(after,output,ensure_ascii=False,indent=2)
result=compare(spec,before,after)
with (out/'vmware-actual-retest-comparison.json').open('x',encoding='utf-8') as output:
    json.dump(result,output,ensure_ascii=False,indent=2)
sources={str(path.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(path.read_bytes()).hexdigest()
         for path in (ROOT/'campuslab/vm_course.py',ROOT/'campuslab/guest_probe.py',ROOT/'campuslab/rules.py')}
with (out/'real-collector-source-sha256.json').open('x',encoding='utf-8') as output:
    json.dump(sources,output,indent=2)
print(json.dumps(dict(outcome=result['outcome'],passed=result['after']['passed'],guest_collected=False)))
