"""Fixed PyTorch course: interpreter, CPU tensor and optional required CUDA proof."""
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import platform
import re
import subprocess

from .rules import absolute, seal, timestamp, version

EXPECTED = [[4, 4], [10, 8]]


def make_task(title=None, gpu_required=False):
    if type(gpu_required) is not bool:
        raise ValueError('GPU要求须明确为布尔值')
    title = title or ('PyTorch深度学习 · GPU演示任务' if gpu_required else 'PyTorch深度学习 · CPU演示任务')
    if not isinstance(title, str) or not 1 <= len(title.strip()) <= 100:
        raise ValueError('任务名称须为1—100字')
    return seal(dict(schema=1, title=title, scenario='pytorch-gpu' if gpu_required else 'pytorch-cpu',
                     source='演示配置；课程方向参考重庆科技大学深度学习大纲，版本与验证程序非学校指定',
                     os='Windows', python=dict(min='3.10', max_exclusive='3.15'), packages={'torch': '2.2'},
                     verify='torch-fixed-matmul', gpu_required=gpu_required,
                     gpu=dict(backend='cuda', index=0), tensor_dtype='float32', expected=EXPECTED))


def validate_spec(spec):
    if not isinstance(spec, dict) or type(spec.get('schema')) is not int or spec.get('schema') != 1:
        raise ValueError('PyTorch任务结构无效')
    if spec != make_task(spec.get('title'), spec.get('gpu_required')):
        raise ValueError('PyTorch任务摘要或固定要求不匹配')
    return spec


def _object(value, keys, label):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ValueError(label + '证据不完整')


def _nullable_bool(value):
    if value is not None and type(value) is not bool:
        raise ValueError('证据布尔类型无效')


def _run(value, gpu=False):
    _object(value, ('requested', 'returncode', 'result', 'device', 'device_uuid', 'error') if gpu else
            ('returncode', 'result', 'device', 'error'), '张量运行')
    if value['returncode'] is not None and type(value['returncode']) is not int:
        raise ValueError('张量运行退出码无效')
    if not isinstance(value['error'], str) or value['device'] is not None and not isinstance(value['device'], str):
        raise ValueError('张量运行输出类型无效')
    tensor = value['result']
    if tensor is not None and (not isinstance(tensor, list) or len(tensor) != 2 or
                              any(not isinstance(row, list) or len(row) != 2 or any(type(x) not in (int, float) or not math.isfinite(x) for x in row) for row in tensor)):
        raise ValueError('固定张量结果类型无效')
    if value['returncode'] is None and (tensor is not None or value['device'] is not None):
        raise ValueError('未完成运行时不得携带张量结果')
    if gpu:
        if type(value['requested']) is not bool or value['device_uuid'] is not None and not isinstance(value['device_uuid'], str):
            raise ValueError('GPU运行身份类型无效')
        if not value['requested'] and any(value[k] is not None for k in ('returncode', 'result', 'device', 'device_uuid')):
            raise ValueError('未主动触发GPU运算时不得携带运行证据')


def analyze(spec, report):
    validate_spec(spec)
    if not isinstance(report, dict) or type(report.get('schema')) is not int or report['schema'] != 1 or report.get('task_id') != spec['id']:
        raise ValueError('报告与PyTorch任务不一致')
    timestamp(report.get('collected_at'))
    target, facts = report.get('target'), report.get('facts')
    _object(target, ('requested', 'actual', 'exists'), '目标解释器')
    requested = absolute(target['requested']); _nullable_bool(target['exists'])
    if target['actual'] is not None and (absolute(target['actual']) != requested or target['exists'] is not True):
        raise ValueError('实际解释器与所选环境不同')
    _object(facts, ('os', 'python', 'torch', 'cpu', 'gpu'), 'PyTorch事实')
    for key in ('os', 'python'):
        if facts[key] is not None and not isinstance(facts[key], str):
            raise ValueError('系统或解释器版本类型无效')
    framework, cpu, gpu = facts['torch'], facts['cpu'], facts['gpu']
    _object(framework, ('installed', 'version', 'imported', 'error'), '框架')
    for key in ('installed', 'imported'):
        _nullable_bool(framework[key])
    if not isinstance(framework['error'], str) or framework['version'] is not None and not isinstance(framework['version'], str):
        raise ValueError('框架版本或错误类型无效')
    if framework['installed'] is not True and (framework['version'] is not None or framework['imported'] is True):
        raise ValueError('框架未确认安装时不得携带版本或导入成功')
    _run(cpu)
    _object(gpu, ('build', 'available', 'device', 'run', 'error'), 'GPU')
    _nullable_bool(gpu['available'])
    if gpu['build'] is not None and not isinstance(gpu['build'], str) or not isinstance(gpu['error'], str):
        raise ValueError('GPU构建证据类型无效')
    device = gpu['device']
    if device is not None:
        _object(device, ('index', 'uuid', 'name', 'total_memory'), 'GPU设备身份')
        if type(device['index']) is not int or device['index'] != 0 or not isinstance(device['name'], str):
            raise ValueError('GPU设备索引或名称无效')
        if device['uuid'] is not None and (not isinstance(device['uuid'], str) or not device['uuid'].strip()):
            raise ValueError('GPU UUID无效')
        if device['total_memory'] is not None and (type(device['total_memory']) is not int or device['total_memory'] <= 0):
            raise ValueError('GPU显存类型无效')
        if gpu['available'] is not True:
            raise ValueError('GPU未确认可用时不得携带设备身份')
    _run(gpu['run'], gpu=True)
    run = gpu['run']
    if run['device_uuid'] is not None and (device is None or run['device_uuid'] != device['uuid']):
        raise ValueError('GPU运行设备与所核对设备不同')
    if run['returncode'] == 0 and (gpu['available'] is not True or device is None):
        raise ValueError('GPU未可用时不得声称完成GPU运算')
    if framework['imported'] is not True and (cpu['returncode'] is not None or gpu['available'] is not None or gpu['build'] is not None):
        raise ValueError('未导入框架时不得携带运行或GPU证据')
    if target['actual'] is None and (facts['python'] is not None or framework['installed'] is not None or cpu['returncode'] is not None or gpu['available'] is not None):
        raise ValueError('未确认解释器时不得携带版本或运行证据')
    checks = []
    def check(name, state, observed, requirement):
        checks.append(dict(id=name, status=state, observed=observed, requirement=requirement))
    check('os', 'unknown' if facts['os'] is None else ('pass' if facts['os'] == 'Windows' else 'mismatch'), facts['os'], 'Windows')
    py = facts['python']
    check('python', ('missing' if target['exists'] is False else 'unknown') if py is None else
          ('pass' if version('3.10') <= version(py) < version('3.15') else 'mismatch'), py, spec['python'])
    release = re.fullmatch(r'(\d+\.\d+(?:\.\d+)?)(?:\+[A-Za-z0-9.]+)?', framework['version'] or '')
    package_state = 'missing' if framework['installed'] is False else 'unknown'
    if release:
        package_state = 'pass' if version(release[1]) >= version('2.2') else 'mismatch'
    check('package:torch', package_state, framework['version'], 'torch>=2.2；演示要求，组合兼容须实际运行')
    imported = framework['imported']
    check('torch:import', 'unknown' if imported is None else ('pass' if imported and not framework['error'] else
          ('missing' if framework['installed'] is False else 'mismatch')), framework, '所选解释器实际导入PyTorch')
    check('torch:cpu', 'unknown' if cpu['returncode'] is None else ('pass' if cpu['returncode'] == 0 and cpu['result'] == EXPECTED and cpu['device'] == 'cpu' and not cpu['error'] else 'mismatch'),
          cpu, 'CPU固定矩阵乘法得到[[4,4],[10,8]]')
    if spec['gpu_required']:
        build_state='unknown' if imported is not True else ('missing' if gpu['build'] is None else ('pass' if re.fullmatch(r'\d+\.\d+(?:\.\d+)?',gpu['build']) else 'unknown'))
        check('torch:cuda-build', build_state, gpu['build'], '框架包含有效CUDA版本构建')
        check('torch:gpu-available', 'unknown' if gpu['available'] is None or gpu['error'] else ('pass' if gpu['available'] else 'missing'), gpu['available'], '所选框架报告CUDA设备可用')
        check('torch:gpu-identity', 'pass' if device is not None and device['uuid'] else 'unknown', device, 'CUDA:0独立GPU UUID；名称不足以证明同一设备')
        check('torch:gpu-run', 'unknown' if run['returncode'] is None else ('pass' if run['returncode'] == 0 and run['result'] == EXPECTED and run['device'] == 'cuda:0' and run['device_uuid'] and not run['error'] else 'mismatch'),
              run, '本人触发CUDA:0固定矩阵乘法，实际设备UUID匹配；CPU结果不可替代')
    return dict(task_id=spec['id'], target=target, collected_at=report['collected_at'], checks=checks, passed=all(c['status'] == 'pass' for c in checks))


def compare_identity(before, after):
    if absolute(before['target']['requested']) != absolute(after['target']['requested']):
        raise ValueError('复检必须使用同一Python解释器')
    a, b = before['facts']['gpu']['device'], after['facts']['gpu']['device']
    if a is not None and a['uuid'] and b is not None and b['uuid'] and a['uuid'] != b['uuid']:
        raise ValueError('复检GPU UUID不同；请为新设备重新初检')


def collect(spec, target, gpu_run=False):
    validate_spec(spec); absolute(target)
    if type(gpu_run) is not bool:
        raise ValueError('GPU运行须明确触发')
    if gpu_run and not spec['gpu_required']:
        raise ValueError('请先选择GPU课程任务再触发GPU运算')
    path = Path(target)
    if (path.parent / '.campuslab-tool-runtime').exists():
        raise ValueError('工具运行时不能作为课程Python')
    report = dict(schema=1, task_id=spec['id'], collected_at=datetime.now(timezone.utc).isoformat(),
                  target=dict(requested=target, actual=None, exists=path.is_file()),
                  facts=dict(os=platform.system(), python=None,
                             torch=dict(installed=None, version=None, imported=None, error='目标解释器未确认'),
                             cpu=dict(returncode=None, result=None, device=None, error='目标解释器未确认'),
                             gpu=dict(build=None, available=None, device=None, error='目标解释器未确认',
                                      run=dict(requested=gpu_run, returncode=None, result=None, device=None, device_uuid=None, error='未运行GPU验证'))))
    command = [str(path), '-B', '-I', str(Path(__file__).with_name('torch_probe.py'))]
    if gpu_run:
        command.append('--gpu-run')
    report['commands'] = [command]
    if path.is_file():
        try:
            proc = subprocess.run(command, capture_output=True, timeout=120, text=True, encoding='utf-8', errors='replace',
                                  env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
            report['probe_exit'] = proc.returncode
            if proc.returncode:
                report['facts']['torch']['error'] = '探测退出' + str(proc.returncode) + ': ' + proc.stderr[-1500:]
            else:
                observed = json.loads(proc.stdout)
                report['target']['actual'] = observed['actual']
                report['facts'] = observed['facts']
        except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
            report['facts']['torch']['error'] = '探测未完成，保留未知: ' + type(exc).__name__
    analyze(spec, report)
    return report
