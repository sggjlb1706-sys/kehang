"""Bounded discovery and user-native selections; never accept executable web paths."""
import base64
from copy import deepcopy
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import threading
import time
import uuid

from .launcher import discover_python
from .rules import absolute, validate_task

ROOT = Path(__file__).resolve().parents[1]
PYTHON = dict(label='课程 Python', kind='python', required=True)
FIELDS = {
    'python-basics': dict(target=PYTHON),
    'node-basics': dict(target=dict(label='课程 Node.js', kind='node', required=True)),
    'java-jdk': dict(target=dict(label='JDK 根目录', kind='jdk', required=True)),
    'notebook-data': dict(target=PYTHON, kernel_spec=dict(label='Notebook 内核 kernel.json', kind='kernel', required=True)),
    'sqlite-basics': dict(target=dict(label='课程 SQLite 数据库', kind='database', required=True)),
    'pytorch-cpu': dict(target=PYTHON),
    'pytorch-gpu': dict(target=PYTHON),
    'local-qwen': dict(target=PYTHON, model_dir=dict(label='固定 Qwen 模型目录', kind='folder', required=True)),
    'deepseek-api': dict(target=PYTHON),
    'dsh-desktop': dict(target=dict(label='DSH 桌面程序', kind='desktop', required=True), workspace=dict(label='DSH 专用练习目录（可选）', kind='folder', required=False)),
    'dsh-cli': dict(target=dict(label='课程 Node.js', kind='node', required=True), package_json=dict(label='DSH 包 package.json', kind='package', required=True), workspace=dict(label='DSH 专用练习目录（可选）', kind='folder', required=False)),
    'vm-linux': dict(target=dict(label='虚拟化程序 VBoxManage.exe / vmrun.exe', kind='vm', required=True), vm_id=dict(label='VMware 实例 .vmx（VirtualBox 可在下方填 UUID）', kind='vmx', required=False), guest_report=dict(label='同任务同实例的来宾报告（可选）', kind='json', required=False)),
}
NOTES = {
    'python-basics': '检查所选 Python 的版本、requests 与固定导入。也可直接检测已登记的 Python。',
    'node-basics': '使用所选 node.exe 和同目录 npm，运行已有固定检查。',
    'java-jdk': '核对同源 java / javac，在临时目录编译并运行固定 Java 程序。',
    'notebook-data': '实际启动你选定的内核，核对解释器并完成固定数据计算；随后关闭本次内核。',
    'sqlite-basics': '只读检查课程数据库，执行固定 SELECT 并复核文件摘要；不会修改数据库。',
    'pytorch-cpu': '导入 PyTorch 并运行固定 CPU 张量计算。',
    'pytorch-gpu': '默认检查准备状态；实际 GPU 张量计算需要勾选本次授权。',
    'local-qwen': '核对固定模型目录及权重；实际加载模型推理需要勾选本次授权。',
    'deepseek-api': '仅检查 Python 编程依赖与固定请求准备。不会发送 API 请求；实际调用继续使用手动预览与单次授权。',
    'dsh-desktop': '只读核对程序与公开包元数据，可核对专用练习目录。不启动 DSH、不读取会话凭据；真实 Agent 任务仍需本人完成。',
    'dsh-cli': '运行所选 Node 的固定身份检查，只读核对 DSH 包及可选练习目录。不执行包入口或 Agent 任务。',
    'vm-linux': '只读检查宿主、虚拟化程序和所选实例。不启动虚拟机、不登录来宾；无真实来宾报告保留未知。',
}


def validate_path(kind, value):
    absolute(value)
    path = Path(value).resolve()
    names = {'python': {'python.exe', 'python3.exe'}, 'node': {'node.exe'}, 'kernel': {'kernel.json'},
             'package': {'package.json'}, 'vm': {'vboxmanage.exe', 'vmrun.exe'}}
    if kind in names and path.name.casefold() not in names[kind]:
        raise ValueError('所选文件类型与当前字段不符')
    if kind in ('folder', 'jdk'):
        if not path.is_dir(): raise ValueError('请选择已有目录')
        if kind == 'jdk' and not (path / 'bin/java.exe').is_file(): raise ValueError('目录中没有 bin/java.exe')
    elif not path.is_file(): raise ValueError('所选文件不存在或已移走，请重新选择')
    if kind in ('python', 'node') and (path.parent / '.campuslab-tool-runtime').exists():
        raise ValueError('工具自带运行时不是课程目标')
    if kind == 'python' and path.parent.name.casefold() == 'windowsapps': raise ValueError('请选择实际 Python，不能使用应用别名')
    extensions = {'database': {'.sqlite', '.sqlite3', '.db'}, 'vmx': {'.vmx'}, 'json': {'.json'}, 'desktop': {'.exe'}}
    if kind in extensions and path.suffix.casefold() not in extensions[kind]: raise ValueError('所选文件后缀与当前字段不符')
    return str(path)


def python_choices():
    choices = discover_python(ROOT)
    # Only inspect known conda roots already discovered above, never scan drives.
    for path, _ in list(choices)[:8]:
        root = Path(path).parent
        if (root / 'conda-meta').is_dir() and (root / 'envs').is_dir():
            choices += [(str(p), '已知 Conda 环境目录候选') for p in sorted((root / 'envs').glob('*/python.exe'))[:8]]
    return choices


PICKER = r'''
$ErrorActionPreference = 'Stop'
[Console]::InputEncoding = [Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$settings = [Console]::In.ReadToEnd() | ConvertFrom-Json
Add-Type -AssemblyName System.Windows.Forms
if ($settings.folder) {
    $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
    $dialog.Description = $settings.label
    $dialog.ShowNewFolderButton = $false
} else {
    $dialog = New-Object System.Windows.Forms.OpenFileDialog
    $dialog.Title = $settings.label
    $dialog.Filter = $settings.filter
    $dialog.Multiselect = $false
    $dialog.CheckFileExists = $true
    $dialog.RestoreDirectory = $true
}
try {
    if ($dialog.ShowDialog() -eq [Windows.Forms.DialogResult]::OK) {
        $value = if ($settings.folder) { $dialog.SelectedPath } else { $dialog.FileName }
        @{ selected = $value } | ConvertTo-Json -Compress
    } else { @{ selected = $null } | ConvertTo-Json -Compress }
} finally { $dialog.Dispose() }
'''


def choose_native(field):
    filters = {'python': 'Python|python.exe;python3.exe', 'node': 'Node.js|node.exe', 'kernel': 'Notebook 内核|kernel.json',
               'database': 'SQLite|*.sqlite;*.sqlite3;*.db', 'package': 'DSH 包|package.json', 'desktop': 'DSH 程序|*.exe',
               'vm': '虚拟化程序|VBoxManage.exe;vmrun.exe', 'vmx': 'VMware 实例|*.vmx', 'json': '来宾报告|*.json'}
    settings = dict(label=field['label'], folder=field['kind'] in ('folder', 'jdk'), filter=filters.get(field['kind'], '文件|*.*'))
    shell = Path(os.environ.get('SystemRoot', r'C:\Windows')) / 'System32/WindowsPowerShell/v1.0/powershell.exe'
    result = subprocess.run([str(shell), '-NoLogo', '-NoProfile', '-STA', '-WindowStyle', 'Hidden', '-EncodedCommand', base64.b64encode(PICKER.encode('utf-16le')).decode()],
                            input=json.dumps(settings, ensure_ascii=False).encode('utf8'), capture_output=True, timeout=180,
                            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    if result.returncode: raise ValueError('文件选择窗口不可用，请重试或使用手动备用入口')
    return json.loads(result.stdout.decode('utf-8-sig'))['selected']


class TargetStore:
    def __init__(self):
        self.entries = {}
        self.lock = threading.RLock()
        self.picker_lock = threading.Lock()

    def register(self, spec, field, value, source):
        meta = FIELDS[spec['scenario']][field]
        path = validate_path(meta['kind'], value)
        with self.lock:
            now = time.monotonic()
            self.entries = {k: v for k, v in self.entries.items() if now - v['time'] < 1800}
            for key, entry in self.entries.items():
                if (entry['task'], entry['field'], entry['path']) == (spec['id'], field, path):
                    entry['time'] = now
                    return dict(id=key, path=path, source=source)
            while len(self.entries) >= 128: self.entries.pop(next(iter(self.entries)))
            key = secrets.token_hex(16)
            self.entries[key] = dict(task=spec['id'], field=field, path=path, kind=meta['kind'], time=now)
            return dict(id=key, path=path, source=source)

    def configuration(self, spec):
        validate_task(spec)
        fields = deepcopy(FIELDS.get(spec['scenario'], {}))
        for value in fields.values(): value['choices'] = []
        return dict(fields=fields, note=NOTES.get(spec['scenario'], '此课程是网页提问练习，没有适用的本机环境检测。请按学习步骤进入官方网页并完成练习。'))

    def discover(self, spec):
        value = self.configuration(spec)
        for field, meta in value['fields'].items():
            choices = []
            if meta['kind'] == 'python': choices = python_choices()
            elif meta['kind'] == 'node':
                found = shutil.which('node.exe')
                if found: choices = [(found, 'PATH 候选')]
            elif meta['kind'] == 'jdk':
                found = shutil.which('javac.exe') or shutil.which('java.exe')
                choices = [(str(Path(found).resolve().parent.parent), 'PATH 候选')] if found else []
                if os.environ.get('JAVA_HOME'): choices.append((os.environ['JAVA_HOME'], 'JAVA_HOME 候选'))
            elif meta['kind'] == 'kernel':
                folders = [Path(os.environ.get('APPDATA', str(Path.home()))) / 'jupyter/kernels', Path(os.environ.get('PROGRAMDATA', 'C:/ProgramData')) / 'jupyter/kernels']
                folders += [Path(p).parent / 'share/jupyter/kernels' for p, _ in python_choices()[:8]]
                for folder in folders:
                    if folder.is_dir(): choices += [(str(p), '已知 Jupyter 内核目录') for p in sorted(folder.glob('*/kernel.json'))[:8]]
            elif meta['kind'] == 'vm':
                for name, suffix in [('VBoxManage.exe', 'Oracle/VirtualBox/VBoxManage.exe'), ('vmrun.exe', 'VMware/VMware Workstation/vmrun.exe')]:
                    found = shutil.which(name)
                    if found: choices.append((found, 'PATH 候选'))
                    for base in (os.environ.get('ProgramFiles'), os.environ.get('ProgramFiles(x86)')):
                        if base: choices.append((str(Path(base) / suffix), '标准安装位置候选'))
            seen = set()
            for path, source in choices:
                try:
                    item = self.register(spec, field, path, source)
                    if item['id'] not in seen: meta['choices'].append(item); seen.add(item['id'])
                except (OSError, ValueError): pass
                if len(meta['choices']) >= 8: break
        return value

    def pick(self, spec, field):
        validate_task(spec)
        if field not in FIELDS.get(spec['scenario'], {}): raise ValueError('当前课程不接受此选择')
        if not self.picker_lock.acquire(blocking=False): raise ValueError('已有文件窗口，请先完成或取消选择')
        try:
            value = choose_native(FIELDS[spec['scenario']][field])
            return dict(selected=self.register(spec, field, value, '本人文件窗口选择') if value else None)
        finally: self.picker_lock.release()

    def resolve(self, spec, selections, options):
        scenario = spec['scenario']
        if not isinstance(selections, dict) or set(selections) - set(FIELDS[scenario]): raise ValueError('检测目标选择无效')
        if not isinstance(options, dict): raise ValueError('检测选项无效')
        allowed = {'pytorch-gpu': {'gpu_run'}, 'local-qwen': {'infer'}, 'vm-linux': {'vm_uuid', 'host_only'}}.get(scenario, set())
        if set(options) - allowed: raise ValueError('当前课程不接受此执行选项')
        result = {}
        with self.lock:
            for field, meta in FIELDS[scenario].items():
                key = selections.get(field)
                if not key:
                    if meta['required']: raise ValueError('请先选择' + meta['label'])
                    continue
                entry = self.entries.get(key) if isinstance(key, str) else None
                if not entry or (entry['task'], entry['field']) != (spec['id'], field) or time.monotonic() - entry['time'] >= 1800:
                    raise ValueError('目标选择已过期或不属于当前课程，请重新选择')
                result[field] = validate_path(meta['kind'], entry['path'])
        for key, value in options.items():
            if key in ('gpu_run', 'infer', 'host_only'):
                if type(value) is not bool: raise ValueError('实际运行须明确选择本次授权')
                if key != 'host_only': result[key] = value
            elif value:
                try: identity = str(uuid.UUID(value))
                except (ValueError, TypeError, AttributeError): raise ValueError('请输入有效的 VirtualBox UUID') from None
                if 'vm_id' in result: raise ValueError('请选择一种虚拟机实例标识')
                result['vm_id'] = identity
        if options.get('host_only') and 'vm_id' in result: raise ValueError('仅检测宿主时，请清空实例选择')
        if scenario == 'vm-linux' and 'vm_id' not in result and options.get('host_only') is not True: raise ValueError('请先选择具体实例，或明确选择仅检测宿主与软件')
        return result
