"""Explicit Node target only; npm is invoked by this target, never by PATH."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import subprocess

from .rules import analyze


def collect_node(spec, target):
    path = Path(target)
    report = dict(schema=1, task_id=spec['id'], collected_at=datetime.now(timezone.utc).isoformat(),
                  target=dict(requested=target, actual=None, exists=path.is_file()),
                  facts=dict(os=platform.system(), node=None,
                             npm=dict(path=None, node=None, exists=None, version=None, returncode=None, error='目标Node未确认'),
                             verification=dict(returncode=None, stdout='', error='目标Node文件不存在')))
    command = [str(path), str(Path(__file__).with_name('node_probe.js'))]
    report['commands'] = [command]
    if path.is_file():
        try:
            environment = {k:v for k,v in os.environ.items() if k.upper() not in ('NODE_OPTIONS', 'NODE_PATH')}
            proc = subprocess.run(command, capture_output=True, timeout=55, text=True,
                                  encoding='utf-8', errors='replace', env=environment)
            if proc.returncode:
                report['facts']['verification']['error'] = f'Node探测退出{proc.returncode}: {proc.stderr[:2000]}'
            else:
                observed = json.loads(proc.stdout)
                report['target']['actual'] = observed['actual']
                report['facts'] = observed['facts']
                report['commands'].extend(observed['commands'])
        except subprocess.TimeoutExpired:
            report['facts']['verification']['error'] = 'Node探测超过55秒，保留未知'
        except OSError as exc:
            report['facts']['verification']['error'] = f'无法启动所选Node: {type(exc).__name__}: {exc}'
        except (ValueError, KeyError, TypeError):
            report['facts']['verification']['error'] = 'Node探测未返回完整JSON，保留未知'
    analyze(spec, report)
    return report
