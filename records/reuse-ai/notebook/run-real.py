"""Current local developer verification; does not install or change course software."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from campuslab import notebook_course,java_course,sqlite_course
from campuslab.rules import timestamp


def save(path,value):
    with path.open('x',encoding='utf-8') as stream:json.dump(value,stream,ensure_ascii=False,indent=2)


def main():
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    summary={}
    for label,module,target,extra in [
        ('notebook',notebook_course,r'D:\ANACONDA\python.exe',dict(kernel_spec=r'D:\ANACONDA\share\jupyter\kernels\python3\kernel.json')),
        ('java',java_course,r'C:\Program Files\Zulu\zulu-21',{}),
        ('sqlite',sqlite_course,None,{})]:
        folder=ROOT/'records/reuse-ai'/label/stamp;folder.mkdir()
        spec=module.make_task();save(folder/'task.json',spec)
        if label=='sqlite':
            target=str(folder/'scores.sqlite');module.prepare_demo(target)
        a=module.collect(spec,target,**extra);save(folder/'A.json',a);save(folder/'A-analysis.json',module.analyze(spec,a))
        b=module.collect(spec,target,**extra);save(folder/'B.json',b);save(folder/'B-analysis.json',module.analyze(spec,b))
        module.compare_identity(a,b)
        if timestamp(b['collected_at'])<=timestamp(a['collected_at']):raise ValueError('non-increasing real timestamps')
        result=dict(real_local=True,device='same development computer',identity_checked=True,time_order_checked=True,
            both_passed=module.analyze(spec,a)['passed'] and module.analyze(spec,b)['passed'],
            shared_rules_retest_pending=True,physical_second_device=False)
        save(folder/'module-retest.json',result)
        missing=module.collect(spec,'C:\\CampusLab-Deliberately-Missing\\'+('python.exe' if label=='notebook' else 'target'),**extra)
        save(folder/'deliberately-missing-target.json',missing);save(folder/'deliberately-missing-analysis.json',module.analyze(spec,missing))
        if label=='notebook':
            with tempfile.TemporaryDirectory(prefix='campuslab-spec-mismatch-') as tmp:
                path=Path(tmp)/'kernel.json';path.write_text(json.dumps(dict(language='python',display_name='Deliberate mismatch',argv=[r'C:\OtherPython\python.exe','-m','ipykernel_launcher','-f','{connection_file}'])),encoding='utf-8')
                wrong=module.collect(spec,target,kernel_spec=str(path));save(folder/'deliberately-mismatched-kernel.json',wrong);save(folder/'deliberately-mismatched-analysis.json',module.analyze(spec,wrong))
        sources={str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for path in (ROOT/'campuslab').glob(label+'_*.py')}
        save(folder/'source-sha256.json',sources);summary[label]=dict(folder=str(folder),**result)
    out=ROOT/'records/reuse-ai/notebook'/('real-summary-'+stamp+'.json');save(out,summary)
    print(json.dumps(summary,ensure_ascii=True,indent=2))


if __name__=='__main__':main()
