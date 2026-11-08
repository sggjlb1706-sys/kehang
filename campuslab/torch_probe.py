"""Fixed local tensor operations inside an explicitly selected course interpreter."""
import argparse
import importlib.metadata
import json
import platform
import sys


def tensor_run(torch, device):
    result = dict(returncode=None, result=None, device=None, error='')
    try:
        a = torch.tensor([[1, 2], [3, 4]], dtype=torch.float32, device=device)
        b = torch.tensor([[2, 0], [1, 2]], dtype=torch.float32, device=device)
        value = torch.matmul(a, b)
        if device.startswith('cuda'):
            torch.cuda.synchronize(0)
        result.update(returncode=0, result=value.cpu().tolist(), device=str(value.device))
    except Exception as exc:
        result.update(returncode=1, error=type(exc).__name__ + ': ' + str(exc)[:1500])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gpu-run', action='store_true')
    args = parser.parse_args()
    framework = dict(installed=None, version=None, imported=None, error='')
    cpu = dict(returncode=None, result=None, device=None, error='框架未导入')
    gpu = dict(build=None, available=None, device=None, error='',
               run=dict(requested=args.gpu_run, returncode=None, result=None, device=None, device_uuid=None, error='未触发GPU验证' if not args.gpu_run else 'GPU条件未确认'))
    try:
        framework.update(installed=True, version=importlib.metadata.version('torch'))
    except importlib.metadata.PackageNotFoundError:
        framework.update(installed=False, imported=False, error='所选环境未安装PyTorch')
    if framework['installed']:
        try:
            import torch
            framework.update(imported=True)
        except Exception as exc:
            framework.update(imported=False, error=type(exc).__name__ + ': ' + str(exc)[:1500])
        else:
            cpu = tensor_run(torch, 'cpu')
            gpu['build'] = torch.version.cuda
            try:
                gpu['available'] = bool(torch.cuda.is_available())
                if gpu['available']:
                    properties = torch.cuda.get_device_properties(0)
                    uuid = getattr(properties, 'uuid', None)
                    gpu['device'] = dict(index=0, uuid=str(uuid) if uuid else None, name=properties.name, total_memory=properties.total_memory)
                    if args.gpu_run:
                        gpu['run'].update(tensor_run(torch, 'cuda:0'))
                        if gpu['run']['returncode'] == 0:
                            gpu['run']['device_uuid'] = gpu['device']['uuid']
                elif args.gpu_run:
                    gpu['run']['error'] = 'CUDA设备不可用，未执行GPU运算'
            except Exception as exc:
                gpu['error'] = type(exc).__name__ + ': ' + str(exc)[:1500]
    print(json.dumps(dict(actual=sys.executable, facts=dict(os=platform.system(), python=platform.python_version(), torch=framework, cpu=cpu, gpu=gpu)), ensure_ascii=True))


if __name__ == '__main__':
    main()
