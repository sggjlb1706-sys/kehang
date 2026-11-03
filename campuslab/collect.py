"""Manual CLI: collect selected target; never install or change its packages."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import subprocess

from .rules import absolute, analyze, validate_task


def collect(spec, target):
    validate_task(spec)
    absolute(target)
    path = Path(target)
    if (path.parent / '.campuslab-tool-runtime').exists():
        raise ValueError('工具自带运行时不能作为课程目标')
    report = dict(schema=1, task_id=spec['id'], collected_at=datetime.now(timezone.utc).isoformat(),
                  target=dict(requested=target, actual=None, exists=path.is_file()),
                  facts=dict(os=platform.system(), python=None, packages={name:None for name in spec['packages']},
                             verification=dict(returncode=None, stdout='', error='目标解释器不存在')))
    if path.is_file():
        try:
            proc = subprocess.run([str(path), '-B', '-I', str(Path(__file__).with_name('probe.py'))],
                                  capture_output=True, timeout=35, text=True, encoding='utf-8', errors='replace',
                                  env={**os.environ, 'PYTHONDONTWRITEBYTECODE':'1'})
            if proc.returncode:
                raise ValueError('probe exit ' + str(proc.returncode))
            observed = json.loads(proc.stdout)
            report['target']['actual'] = observed.pop('actual')
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
    args = parser.parse_args()
    spec = json.loads(args.task.read_text(encoding='utf-8-sig'))
    report = collect(spec, args.target)
    with args.output.open('x', encoding='utf-8') as output:
        json.dump(report, output, ensure_ascii=False, indent=2)
    print(json.dumps(analyze(spec, report), ensure_ascii=True))


if __name__ == '__main__':
    main()
