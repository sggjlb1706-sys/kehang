"""User-clicked, fixed course checks on the loopback server's computer."""
from copy import deepcopy
import json
from pathlib import Path
import platform
import secrets
import subprocess
import sys
import tempfile
import threading
import time

from .launcher import discover_python
from .rules import absolute, analyze, compare, validate_task
from .owned_process import OwnedProcess
from .local_targets import FIELDS, TargetStore

ROOT = Path(__file__).resolve().parents[1]
MAX_CANDIDATES = 8
MAX_JOBS = 8
LEASE_SECONDS = 15


def run_check(spec, target, cancelled, options=None):
    """Use the existing collector contract in an owned, cancellable process tree."""
    temporary = ROOT / 'data/temp'
    temporary.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='kehang-local-', dir=temporary) as folder:
        folder = Path(folder)
        snapshot, output = folder / 'task.json', folder / 'report.json'
        snapshot.write_text(json.dumps(spec, ensure_ascii=False), encoding='utf8')
        command = [sys.executable, '-B', '-I', '-S', str(ROOT / 'campuslab/local_runner.py'),
                   '--task', str(snapshot), '--target', target, '--output', str(output)]
        for key, value in (options or {}).items():
            if type(value) is bool:
                if value: command.append('--' + key.replace('_', '-'))
            else: command.extend(['--' + key.replace('_', '-'), value])
        owned = OwnedProcess(command, cwd=ROOT)
        process = owned.process
        deadline = time.monotonic() + (195 if (options or {}).get('infer') else 150)
        try:
            while process.poll() is None:
                if cancelled.wait(.1):
                    return None
                if time.monotonic() >= deadline:
                    raise TimeoutError('固定检测超时')
            if cancelled.is_set():
                return None
            if process.returncode or not output.is_file() or output.stat().st_size > 200000:
                raise ValueError('固定检测未产生有效报告')
            report = json.loads(output.read_text(encoding='utf8'))
            analyze(spec, report)
            return report
        finally:
            owned.close()


class LocalCheckService:
    def __init__(self, discover=None, runner=None):
        self.token = secrets.token_hex(32)
        self.available = platform.system() == 'Windows'
        self.discover = discover or (lambda: discover_python(ROOT))
        self.runner = runner
        self.targets = TargetStore()
        self.lock = threading.RLock()
        self.jobs = {}
        self.active = None
        self.closed = False

    def configuration(self):
        return dict(available=self.available, token=self.token, scenarios=list(FIELDS),
                    max_candidates=MAX_CANDIDATES,
                    scope='检测运行课航服务的 Windows 电脑；仅运行当前课程固定检查，不安装软件')

    def authorize(self, token):
        if not isinstance(token, str) or not token.isascii() or not secrets.compare_digest(token, self.token):
            raise ValueError('请刷新本机页面后再检测')

    def start(self, body):
        if set(body) not in ({'task', 'consent'}, {'task', 'consent', 'selections', 'options'},
                             {'task', 'consent', 'previous_job', 'target_id'},
                             {'task', 'consent', 'previous_job', 'target_id', 'execution_consent'}):
            raise ValueError('本机检测只接受固定任务和本次点击同意')
        spec = deepcopy(validate_task(body['task']))
        if spec['scenario'] not in FIELDS or body['consent'] is not True or not self.available:
            raise ValueError('当前课程不支持本机检测或尚未主动同意')
        with self.lock:
            if self.closed:
                raise ValueError('服务已关闭')
            if self.active and self.jobs[self.active]['state'] in ('running', 'cancelling'):
                raise ValueError('已有本机检测，请等待或取消后重试')
            previous = None
            selected = None
            if 'previous_job' in body:
                old = self._job(body['previous_job'])
                if old['state'] != 'done' or old['task']['id'] != spec['id']:
                    raise ValueError('复检须使用同任务的已完成检测')
                previous = next((deepcopy(item) for item in old['results']
                                 if item['id'] == body['target_id'] and item.get('report')), None)
                if previous is None:
                    raise ValueError('未找到可复检的原环境，请重新初检')
                if any(previous.get('options', {}).get(k) for k in ('gpu_run', 'infer')) and body.get('execution_consent') is not True:
                    raise ValueError('本次复检需要重新同意实际 GPU 计算或模型推理')
            elif 'selections' in body:
                selected = self.targets.resolve(spec, body['selections'], body['options'])
            elif spec['scenario'] != 'python-basics':
                raise ValueError('请先选择当前课程的检测目标')
            while len(self.jobs) >= MAX_JOBS:
                del self.jobs[next(iter(self.jobs))]
            identity = secrets.token_hex(16)
            job = dict(id=identity, task=spec, state='running', results=[], total=0,
                       completed=0, limited=False, current='', error='', cancel=threading.Event(), seen=time.monotonic())
            self.jobs[identity] = job
            self.active = identity
            worker = threading.Thread(target=self._work, args=(job, previous, selected), daemon=True)
            job['worker'] = worker
            threading.Thread(target=self._watch, args=(job,), daemon=True).start()
            worker.start()
            return self.status(identity)

    def _job(self, identity):
        if not isinstance(identity, str) or identity not in self.jobs:
            raise ValueError('检测记录不存在或已过期，请重新检测')
        return self.jobs[identity]

    def status(self, identity, heartbeat=False):
        with self.lock:
            job = self._job(identity)
            if heartbeat:
                job['seen'] = time.monotonic()
            return deepcopy({k: v for k, v in job.items() if k not in ('cancel', 'worker', 'seen')})

    def _watch(self, job):
        # A closed page may disappear before receiving its POST response/job ID.
        while not job['cancel'].wait(.25):
            with self.lock:
                if job['state'] not in ('running', 'cancelling'):
                    return
                if time.monotonic() - job['seen'] > LEASE_SECONDS:
                    job['state'] = 'cancelling'
                    job['error'] = '页面已离开或连接中断，本次检测已取消。'
                    job['cancel'].set()

    def cancel(self, identity):
        with self.lock:
            job = self._job(identity)
            if job['state'] in ('running', 'cancelling'):
                job['state'] = 'cancelling'
                job['cancel'].set()
            return self.status(identity)

    def _work(self, job, previous, selected):
        try:
            if previous:
                choices = [(previous['target'], previous['source'], previous.get('options', {}))]
            elif selected:
                options = dict(selected)
                choices = [(options.pop('target'), '本人确认的课程目标', options)]
            else:
                choices, seen = [], set()
                for target, source in self.discover():
                    if job['cancel'].is_set():
                        break
                    try:
                        key = absolute(target)
                        path = Path(target).resolve()
                        # Never test another downloaded tool's embedded runtime either.
                        if path.name.lower() not in ('python.exe', 'python3.exe') or (path.parent / '.campuslab-tool-runtime').exists():
                            continue
                        if key in seen:
                            continue
                        seen.add(key)
                        choices.append((target, source, {}))
                    except (ValueError, OSError):
                        continue
                with self.lock:
                    job['limited'] = len(choices) > MAX_CANDIDATES
                choices = choices[:MAX_CANDIDATES]
            with self.lock:
                job['total'] = len(choices)
            for target, source, options in choices:
                if job['cancel'].is_set():
                    break
                with self.lock:
                    job['current'] = target
                item = dict(id=secrets.token_hex(12), target=target, source=source, options=options, error='')
                try:
                    report = self.runner(job['task'], target, job['cancel']) if self.runner else run_check(job['task'], target, job['cancel'], options)
                    if job['cancel'].is_set():
                        break
                    if not report or absolute(report['target']['requested']) != absolute(target):
                        raise ValueError('检测目标身份不一致')
                    item.update(report=report, analysis=analyze(job['task'], report))
                    if previous:
                        baseline = previous.get('before', previous['report'])
                        item.update(before=baseline, comparison=compare(job['task'], baseline, report))
                    # Raw originals stay on this computer across refreshes and failed rechecks.
                    archive = ROOT / 'data/local-check' / job['id'] / item['id']
                    archive.mkdir(parents=True)
                    for name, value in [('task', job['task']), ('report', report), ('selection', dict(target=target, options=options))]:
                        (archive / (name + '.json')).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf8')
                    if previous: (archive / 'before.json').write_text(json.dumps(baseline, ensure_ascii=False, indent=2), encoding='utf8')
                except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
                    item = dict(id=item['id'], target=target, source=source,
                                error='此环境未完成有效检测，状态未知。可重试或使用手动工具。')
                with self.lock:
                    job['results'].append(item)
                    job['completed'] += 1
            with self.lock:
                job['state'] = 'cancelled' if job['cancel'].is_set() else 'done'
        except Exception:
            with self.lock:
                job['error'] = '未完成本机检测，不能据此认定环境通过。请重试或使用手动工具。'
                job['state'] = 'cancelled' if job['cancel'].is_set() else 'failed'
        finally:
            with self.lock:
                job['current'] = ''

    def close(self):
        with self.lock:
            self.closed = True
            active = self.jobs.get(self.active)
            if active:
                active['cancel'].set()
        if active:
            active['worker'].join(timeout=12)
