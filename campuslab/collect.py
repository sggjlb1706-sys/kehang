"""Manual CLI: collect selected target; never install or change its packages."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import subprocess

from .rules import absolute, analyze, validate_task


def collect(spec, target, model_dir=None, infer=False, gpu_run=False, vm_id=None, guest_report=None,
            kernel_spec=None,package_json=None,workspace=None,provider=None,model=None,agent_evidence=None,
            learning_record=None,api_preview=None,api_send=False):
    validate_task(spec)
    absolute(target)
    scenario=spec['scenario']
    extras={'kernel_spec':kernel_spec,'package_json':package_json,'workspace':workspace,'provider':provider,
            'model':model,'agent_evidence':agent_evidence,'learning_record':learning_record,'api_preview':api_preview}
    allowed={'notebook-data':{'kernel_spec'},'dsh-desktop':{'workspace','provider','model','agent_evidence'},
             'dsh-cli':{'package_json','workspace','provider','model','agent_evidence'},
             'ai-web-deepseek':{'learning_record'},'deepseek-api':{'api_preview'}}
    if any(v is not None and k not in allowed.get(scenario,set()) for k,v in extras.items()) or (api_send and scenario!='deepseek-api'):
        raise ValueError('当前固定任务不接受这些采集参数')
    from .rules import NEW_COURSES, course_module
    if scenario in NEW_COURSES:
        if model_dir is not None or infer or gpu_run or vm_id is not None or guest_report is not None:
            raise ValueError('当前任务不接受其他课程参数')
        module=course_module(scenario)
        if scenario=='notebook-data': return module.collect(spec,target,kernel_spec=kernel_spec)
        if scenario.startswith('dsh-'): return module.collect(spec,target,package_json=package_json,workspace=workspace,provider=provider,model=model,evidence=agent_evidence)
        if scenario=='ai-web-deepseek': return module.collect_web(spec,target,learning_record)
        if scenario=='deepseek-api': return module.collect(spec,target,api_preview,api_send)
        return module.collect(spec,target)
    if gpu_run and scenario not in ('pytorch-cpu','pytorch-gpu'):
        raise ValueError('该任务不接受GPU验证参数')
    if (vm_id is not None or guest_report is not None) and scenario!='vm-linux':
        raise ValueError('该任务不接受虚拟机参数')
    if scenario in ('pytorch-cpu','pytorch-gpu','vm-linux'):
        if model_dir is not None or infer:
            raise ValueError('该任务不接受模型参数')
        if scenario=='vm-linux':
            from .vm_course import collect as collect_vm
            return collect_vm(spec,target,vm_id,guest_report)
        from .torch_course import collect as collect_torch
        return collect_torch(spec,target,gpu_run)
    if spec['scenario'] == 'node-basics':
        if model_dir is not None or infer:
            raise ValueError('Node任务不接受模型参数')
        from .node_collect import collect_node
        return collect_node(spec, target)
    if model_dir is not None:
        absolute(model_dir)
    path = Path(target)
    if (path.parent / '.campuslab-tool-runtime').exists():
        raise ValueError('工具自带运行时不能作为课程目标')
    report = dict(schema=1, task_id=spec['id'], collected_at=datetime.now(timezone.utc).isoformat(),
                  target=dict(requested=target, actual=None, exists=path.is_file()),
                  facts=dict(os=platform.system(), python=None, packages={name:None for name in spec['packages']},
                             verification=dict(returncode=None, stdout='', error='目标解释器不存在')))
    if spec['scenario'] == 'local-qwen':
        report['model']=dict(directory=model_dir,weights_sha256=None,inference=None)
        report['resources']=dict(ram_bytes=None,gpu=None,vram_bytes=None,collection='target probe not completed')
    if path.is_file():
        try:
            command=[str(path), '-B', '-I', str(Path(__file__).with_name('probe.py')), '--scenario', spec['scenario']]
            if model_dir is not None:
                command.extend(['--model-dir',model_dir])
            if infer:
                command.append('--infer')
            proc = subprocess.run(command,
                                  capture_output=True, timeout=180 if infer else 55, text=True, encoding='utf-8', errors='replace',
                                  env={**os.environ, 'PYTHONDONTWRITEBYTECODE':'1'})
            if proc.returncode:
                raise ValueError('probe exit ' + str(proc.returncode))
            observed = json.loads(proc.stdout)
            report['target']['actual'] = observed.pop('actual')
            for key in ('model','resources'):
                if key in observed:
                    report[key]=observed.pop(key)
            report['facts'] = observed
        except (OSError, ValueError, subprocess.TimeoutExpired):
            report['facts']['verification']['error'] = '无法完成目标探测；保留未知，不推定已安装'
    analyze(spec, report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task', type=Path, required=True)
    parser.add_argument('--target', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--model-dir')
    parser.add_argument('--infer',action='store_true',help='Explicitly run the fixed offline local model check')
    parser.add_argument('--gpu-run',action='store_true',help='Explicitly run the fixed GPU tensor check')
    parser.add_argument('--vm-id',help='Selected VirtualBox UUID or VMware absolute .vmx path')
    parser.add_argument('--guest-report',type=Path,help='Manually collected guest JSON bound to the same task and VM')
    parser.add_argument('--kernel-spec',help='Explicit existing kernel.json; only reviewed ipykernel launch syntax')
    parser.add_argument('--package-json',help='Explicit DSH CLI package.json')
    parser.add_argument('--workspace',help='Dedicated DSH exercise directory')
    parser.add_argument('--provider',help='Explicit DSH model provider, no credentials')
    parser.add_argument('--model',help='Explicit DSH model identifier')
    parser.add_argument('--agent-evidence',type=Path,help='Minimal user-exported DSH tool evidence, no private chats')
    parser.add_argument('--learning-record',type=Path,help='User-completed fixed web exercise record')
    parser.add_argument('--api-preview',type=Path,help='Editable exact request JSON; no key')
    parser.add_argument('--api-send',action='store_true',help='Interactive preview + single typed consent + getpass; may incur API fees')
    args = parser.parse_args()
    spec = json.loads(args.task.read_text(encoding='utf-8-sig'))
    guest=json.loads(args.guest_report.read_text(encoding='utf-8-sig')) if args.guest_report else None
    evidence=json.loads(args.agent_evidence.read_text(encoding='utf-8-sig')) if args.agent_evidence else None
    report = collect(spec, args.target, args.model_dir, args.infer,args.gpu_run,args.vm_id,guest,
                     args.kernel_spec,args.package_json,args.workspace,args.provider,args.model,evidence,
                     args.learning_record,args.api_preview,args.api_send)
    with args.output.open('x', encoding='utf-8') as output:
        json.dump(report, output, ensure_ascii=False, indent=2)
    print(json.dumps(analyze(spec, report), ensure_ascii=True))


if __name__ == '__main__':
    main()
