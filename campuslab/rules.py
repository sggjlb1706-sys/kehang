"""Shared deterministic contract. Reports contain observations, never trusted verdicts."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import ntpath
import re


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def version(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d+\.\d+(?:\.\d+)?', value):
        raise ValueError('版本须为两段或三段数字')
    return tuple(map(int, (value.split('.') + ['0'])[:3]))


def absolute(value):
    if not isinstance(value, str) or not ntpath.isabs(value) or not ntpath.splitdrive(value)[0] or '\x00' in value:
        raise ValueError('请填写完整的 Windows 绝对路径')
    return ntpath.normcase(ntpath.normpath(value))


def timestamp(value):
    try:
        result = datetime.fromisoformat(value)
        if result.tzinfo is None:
            raise ValueError()
        return result
    except (TypeError, ValueError):
        raise ValueError('报告时间必须包含时区') from None


def task(scenario='python-basics', title=None, python_min='3.10', python_max='3.15', requests_min='2.31'):
    if scenario != 'python-basics':
        raise ValueError('尚未支持该学习目标')
    if version(python_min) >= version(python_max):
        raise ValueError('Python版本范围无效')
    version(requests_min)
    spec = dict(schema=1, title=title or 'Python基础环境 · 演示任务', scenario=scenario,
                source='演示课程要求，非学校既定要求', os='Windows',
                python=dict(min=python_min, max_exclusive=python_max),
                packages={'requests': requests_min}, verify='import-requests')
    if not isinstance(spec['title'], str) or not 1 <= len(spec['title'].strip()) <= 100:
        raise ValueError('任务名称须为1—100字')
    return seal(spec)


def seal(spec):
    result = deepcopy(spec)
    result.pop('id', None)
    result['id'] = hashlib.sha256(canonical(result).encode('utf-8')).hexdigest()
    return result


def validate_task(spec):
    if not isinstance(spec, dict) or spec != seal(spec) or spec.get('schema') != 1:
        raise ValueError('任务快照缺失或摘要不匹配')
    expected = task(spec.get('scenario'), spec.get('title'), spec['python']['min'],
                    spec['python']['max_exclusive'], spec['packages']['requests'])
    if expected != spec:
        raise ValueError('任务中存在未支持或变更的要求')
    return spec


def analyze(spec, report):
    validate_task(spec)
    if not isinstance(report, dict) or report.get('schema') != 1 or report.get('task_id') != spec['id']:
        raise ValueError('报告与当前任务快照不一致')
    timestamp(report.get('collected_at'))
    target, facts = report.get('target', {}), report.get('facts', {})
    requested = absolute(target.get('requested'))
    actual, exists = target.get('actual'), target.get('exists')
    if exists is not None and type(exists) is not bool:
        raise ValueError('目标存在状态无效')
    if actual is not None and (absolute(actual) != requested or exists is not True):
        raise ValueError('实际解释器与所选目标不一致')
    if not isinstance(facts, dict) or set(facts) != {'os', 'python', 'packages', 'verification'}:
        raise ValueError('报告缺少完整事实集合')
    if not isinstance(facts['packages'], dict) or set(facts['packages']) != set(spec['packages']):
        raise ValueError('依赖证据不完整或含额外依赖')
    verify = facts['verification']
    if not isinstance(verify, dict) or set(verify) != {'returncode', 'stdout', 'error'}:
        raise ValueError('缺少运行验证证据')
    if verify['returncode'] is not None and type(verify['returncode']) is not int:
        raise ValueError('运行退出码无效')
    if any(not isinstance(verify[k], str) for k in ('stdout', 'error')):
        raise ValueError('运行输出无效')
    if actual is None and (facts['python'] is not None or any(v is not None for v in facts['packages'].values()) or verify['returncode'] is not None):
        raise ValueError('目标未确认时不得携带成功运行或软件版本')
    checks = []
    def check(name, state, observed, requirement):
        checks.append(dict(id=name, status=state, observed=observed, requirement=requirement))
    os_value = facts['os']
    if os_value is not None and not isinstance(os_value, str):
        raise ValueError('系统事实无效')
    check('os', 'unknown' if os_value is None else ('pass' if os_value == spec['os'] else 'mismatch'), os_value, spec['os'])
    py = facts['python']
    if py is not None:
        py_ver = version(py)
        py_state = 'pass' if version(spec['python']['min']) <= py_ver < version(spec['python']['max_exclusive']) else 'mismatch'
    else:
        py_state = 'missing' if exists is False else 'unknown'
    check('python', py_state, py, spec['python'])
    for name, minimum in spec['packages'].items():
        observed = facts['packages'][name]
        state = 'unknown' if actual is None else 'missing'
        if observed is not None:
            if not isinstance(observed, str):
                raise ValueError('依赖版本无效')
            release = re.match(r'^(\d+\.\d+(?:\.\d+)?)', observed)
            state = 'unknown' if not release else ('pass' if version(release[0]) >= version(minimum) else 'mismatch')
        check('package:' + name, state, observed, '>=' + minimum)
    runstate = 'unknown' if verify['returncode'] is None else ('pass' if verify['returncode'] == 0 and verify['stdout'].strip() == 'OK' else 'mismatch')
    check('run', runstate, verify, '固定导入程序退出0且输出OK')
    return dict(task_id=spec['id'], target=target, collected_at=report['collected_at'],
                checks=checks, passed=all(c['status'] == 'pass' for c in checks))


def compare(spec, before, after):
    a, b = analyze(spec, before), analyze(spec, after)
    if absolute(a['target']['requested']) != absolute(b['target']['requested']):
        raise ValueError('复检必须使用同一目标解释器')
    if timestamp(b['collected_at']) <= timestamp(a['collected_at']):
        raise ValueError('复检时间必须晚于初检')
    return dict(before=a, after=b, changes=[dict(id=x['id'], before=x['status'], after=y['status'])
                for x, y in zip(a['checks'], b['checks'])],
                outcome='stable-pass' if a['passed'] and b['passed'] else ('repaired' if b['passed'] else 'incomplete'))
