"""Manually run in the selected Linux guest. No installation, credentials or network."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import re
import subprocess
import uuid


def read_value(path):
    try:
        return Path(path).read_text(encoding='utf-8').strip()
    except (OSError, UnicodeError):
        return None


def probe(task_id, vm_id):
    if not isinstance(task_id,str) or not re.fullmatch('[a-f0-9]{64}',task_id):
        raise ValueError('Use the fixed task SHA-256 shown by 课航')
    if not isinstance(vm_id,str) or not vm_id or len(vm_id)>1000 or '\x00' in vm_id:
        raise ValueError('Use the selected host VM UUID or full .vmx path')
    hardware = read_value('/sys/class/dmi/id/product_uuid') if platform.system()=='Linux' else None
    try:
        hardware=str(uuid.UUID(hardware)) if hardware else None
    except (ValueError,AttributeError):
        hardware=None
    machine=read_value('/etc/machine-id') if platform.system()=='Linux' else None
    result=dict(schema=1,task_id=task_id,vm_id=vm_id,hardware_uuid=hardware,
                machine_id_sha256=hashlib.sha256(machine.encode()).hexdigest() if machine else None,
                collected_at=datetime.now(timezone.utc).isoformat(),os=platform.system(),kernel=platform.release(),
                verification=dict(returncode=None,stdout='',error='Linux verification not available'),
                source='manual-linux-guest-probe')
    if platform.system()=='Linux':
        try:
            proc=subprocess.run(['/bin/uname','-s'],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=10)
            result['verification']=dict(returncode=proc.returncode,
                stdout=proc.stdout.strip()+':'+str(sum((1,2,3))),error=proc.stderr[:2000])
        except (OSError,subprocess.TimeoutExpired) as exc:
            result['verification']['error']=type(exc).__name__
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task-id',required=True)
    parser.add_argument('--vm-id',required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=probe(args.task_id,args.vm_id)
    with args.output.open('x',encoding='utf-8') as output:
        json.dump(result,output,ensure_ascii=False,indent=2)
    print('Guest evidence saved. Missing DMI/machine identity stays unknown; transfer this file manually.')


if __name__=='__main__':main()
