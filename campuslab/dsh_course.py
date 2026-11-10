"""Fixed DSH course. Static installation facts and user-provided task excerpts stay distinct."""
from copy import deepcopy
import argparse
import ctypes
from datetime import datetime, timezone
import hashlib
import json
import ntpath
import os
from pathlib import Path
import platform
import re
import subprocess
import struct
import uuid

from .rules import absolute, canonical, seal, timestamp, version

UPSTREAM_COMMIT = 'fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159'
SUPPORTED_VERSION = '0.2.2-rc.1'
INPUT_BYTES = b'value\n10\n14\n18\n'
INPUT_SHA = hashlib.sha256(INPUT_BYTES).hexdigest()
PERMISSION = dict(confirmed=True, read=['input.csv'], write=['summary.json'], tools=['read', 'write'])
EVIDENCE_BASIS = '本人提供DSH最小工具摘要 + 本机固定产物核验；非远程真实性证明'


def make_task(title=None, route='desktop'):
    if route not in ('desktop', 'cli'):
        raise ValueError('请选择DSH桌面端或CLI/Web路线')
    title = title or ('DeepSeek Harness · 桌面课程' if route == 'desktop' else 'DeepSeek Harness · CLI/Web课程')
    if not isinstance(title, str) or not 1 <= len(title.strip()) <= 100:
        raise ValueError('任务名称须为1—100字')
    return seal(dict(schema=1, title=title, scenario='dsh-'+route, route=route, os='Windows',
                     source='本项目固定DSH演示；官方上游 '+UPSTREAM_COMMIT,
                     upstream_commit=UPSTREAM_COMMIT, software_version=SUPPORTED_VERSION,
                     node_min='24.9.0' if route == 'cli' else None,
                     verify='dsh-fixed-csv-summary', input_sha256=INPUT_SHA,
                     expected=dict(count=3, sum=42), permission=PERMISSION))


def validate_spec(spec):
    if not isinstance(spec, dict) or type(spec.get('schema')) is not int or spec.get('schema') != 1 or spec != make_task(spec.get('title'), spec.get('route')):
        raise ValueError('DSH任务摘要或固定要求不匹配')
    return spec


def _object(value, keys, label):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ValueError(label+'字段不完整或含未支持字段')


def _sha(value):
    if value is not None and (not isinstance(value, str) or not re.fullmatch('[a-fA-F0-9]{64}', value)):
        raise ValueError('文件摘要无效')


def _hash(path):
    value = hashlib.sha256()
    with path.open('rb') as source:
        for data in iter(lambda: source.read(1024*1024), b''):
            value.update(data)
    return value.hexdigest()


def _identifier(value):
    if value is not None and (not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/-]{0,99}', value) or value.lower().startswith('sk-')):
        raise ValueError('提供方和模型仅填写公开标识，不填密钥或配置全文')


def _desktop_metadata(path):
    """Read PE version resources without executing the selected desktop program."""
    result = dict(product=None, version=None, error='未取得Windows程序版本资源')
    if platform.system() != 'Windows':
        return result
    try:
        api = ctypes.WinDLL('version', use_last_error=True)
        api.GetFileVersionInfoSizeW.argtypes = [ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_uint)]
        api.GetFileVersionInfoSizeW.restype = ctypes.c_uint
        api.GetFileVersionInfoW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p]
        api.VerQueryValueW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_uint)]
        size = api.GetFileVersionInfoSizeW(str(path), None)
        if not size:
            return result
        data = ctypes.create_string_buffer(size)
        if not api.GetFileVersionInfoW(str(path), 0, size, data):
            return result
        pointer, length = ctypes.c_void_p(), ctypes.c_uint()
        translations = ['040904b0', '040904e4']
        if api.VerQueryValueW(data, '\\VarFileInfo\\Translation', ctypes.byref(pointer), ctypes.byref(length)) and length.value >= 4:
            language, codepage = (ctypes.c_ushort*2).from_address(pointer.value)
            translations.insert(0, f'{language:04x}{codepage:04x}')
        for field, name in [('product', 'ProductName'), ('version', 'ProductVersion')]:
            for translation in translations:
                if api.VerQueryValueW(data, '\\StringFileInfo\\'+translation+'\\'+name, ctypes.byref(pointer), ctypes.byref(length)) and length.value:
                    result[field] = ctypes.wstring_at(pointer.value, length.value).rstrip('\x00')
                    break
        result['error'] = '' if result['product'] and result['version'] else result['error']
    except (OSError, ValueError, AttributeError):
        pass
    return result


def _desktop_package(path):
    """Read only the selected desktop installation's root ASAR package metadata."""
    archive = path.parent/'resources'/'app.asar'
    if not archive.exists():
        return None
    result = dict(path=str(archive.absolute()), sha256=None, package_sha256=None,
                  name=None, version=None, main=None, error='未取得有效的相邻桌面包元数据')
    try:
        if archive.is_symlink() or archive.parent.is_symlink() or archive.resolve() != path.resolve().parent/'resources'/'app.asar':
            raise ValueError('桌面包必须位于所选程序的resources目录')
        before = _hash(archive)
        result['sha256'] = before
        with archive.open('rb') as source:
            raw = source.read(16)
            if len(raw) != 16:
                raise ValueError('ASAR头不完整')
            marker, header_size, payload_size, json_size = struct.unpack('<4I', raw)
            if marker != 4 or header_size != payload_size+4 or not 0 < json_size <= 8*1024*1024 or not 0 <= payload_size-4-json_size <= 3:
                raise ValueError('ASAR头大小无效')
            data_start = 8+header_size
            archive_size = archive.stat().st_size
            if data_start > archive_size:
                raise ValueError('ASAR头超出文件')
            def unique_pairs(items):
                value = {}
                for key, item in items:
                    if key in value:
                        raise ValueError('ASAR/JSON字段重复')
                    value[key] = item
                return value
            header = json.loads(source.read(json_size).decode('utf-8'), object_pairs_hook=unique_pairs)
            entry = header['files']['package.json']
            _object(entry, ('size', 'offset', 'integrity'), 'ASAR根package.json')
            size, offset = entry['size'], entry['offset']
            if type(size) is not int or not 1 <= size <= 65536 or not isinstance(offset, str) or not re.fullmatch(r'\d{1,20}', offset):
                raise ValueError('ASAR元数据长度或偏移无效')
            offset = int(offset)
            if offset+size > archive_size-data_start:
                raise ValueError('ASAR元数据超出文件')
            integrity = entry['integrity']
            _object(integrity, ('algorithm', 'hash', 'blockSize', 'blocks'), 'ASAR元数据完整性')
            if integrity['algorithm'] != 'SHA256' or integrity['blockSize'] != 4194304:
                raise ValueError('ASAR完整性算法不受支持')
            source.seek(data_start+offset)
            content = source.read(size)
            digest = hashlib.sha256(content).hexdigest()
            if len(content) != size or integrity['hash'] != digest or integrity['blocks'] != [digest]:
                raise ValueError('ASAR根package.json完整性不符')
            value = json.loads(content.decode('utf-8'), object_pairs_hook=unique_pairs)
            if not isinstance(value, dict) or any(not isinstance(value.get(key), str) or not 1 <= len(value[key]) <= 100 for key in ('name', 'version', 'main')):
                raise ValueError('桌面包公开身份字段无效')
        if before != _hash(archive):
            raise ValueError('读取期间桌面包发生变化')
        result.update(package_sha256=digest, name=value['name'], version=value['version'], main=value['main'], error='')
    except (OSError, ValueError, KeyError, TypeError, AttributeError, RecursionError) as exc:
        result['error'] = '桌面包元数据无效：'+str(exc)[:200]
    return result


def _node_identity(path):
    """Only the selected Node executes a fixed expression; the DSH entry never runs."""
    env = {key: value for key, value in os.environ.items() if key.upper() not in ('NODE_OPTIONS', 'NODE_PATH')}
    try:
        process = subprocess.run([str(path), '-p', 'JSON.stringify({actual:process.execPath,version:process.versions.node})'],
                                 capture_output=True, timeout=15, encoding='utf-8', errors='replace', env=env)
        if process.returncode:
            raise ValueError()
        value = json.loads(process.stdout)
        if set(value) != {'actual', 'version'}:
            raise ValueError()
        absolute(value['actual']); version(value['version'])
        return dict(**value, error='')
    except (OSError, ValueError, TypeError, subprocess.TimeoutExpired):
        return dict(actual=None, version=None, error='所选Node固定身份探测未完成；未执行DSH')


def prepare_workspace(spec, path):
    validate_spec(spec); absolute(path)
    folder = Path(path)
    if folder.exists():
        raise ValueError('DSH练习须使用尚不存在的专用目录，不能覆盖已有文件')
    folder.mkdir(parents=True)
    marker = dict(schema=1, kind='campuslab-dsh-workspace', id=str(uuid.uuid4()), task_id=spec['id'])
    (folder/'.campuslab-dsh-workspace.json').write_text(canonical(marker), encoding='utf-8')
    (folder/'input.csv').write_bytes(INPUT_BYTES)
    template = dict(schema=1, source='dsh-user-excerpt', task_id=spec['id'], route=spec['route'],
                    target=None, installation_sha256=None, package_json=None, runtime=None, runtime_version=None,
                    workspace=path, workspace_id=marker['id'], provider=None, model=None,
                    started_at=None, ended_at=None, permission=dict(confirmed=False, read=['input.csv'], write=['summary.json'], tools=['read', 'write']),
                    model_result='unknown', calls=[], artifact_sha256=None)
    (folder/'evidence-template.json').write_text(json.dumps(template, ensure_ascii=False, indent=2), encoding='utf-8')
    (folder/'COURSE-TASK.md').write_text(
        '# DSH固定课程练习\n\n只在本专用目录操作。仅允许读 input.csv、写 summary.json，允许工具为文件读取和文件写入；'
        '不运行终端、网络、安装或其他工具，不读取其他文件。\n\n'
        '让DSH统计value列，写入JSON：count为行数、sum为整数和。期望 {"count":3,"sum":42}。'
        '由本人在DSH选择此目录、明确提供方和模型，并审核本次工具权限后启动任务。\n\n'
        '将实际DSH工具记录中本次读写的工具名/相对路径/时间/状态转录为最小摘要；不导出隐藏推理、凭据、其他会话或配置。'
        '产品仅将摘要与当前软件、Node、模型、目录、固定输入和产物关联核验，不提供远程真实性证明。\n\n'
        'evidence-template.json为未完成模板，不能直接作为成功证据。先采集实际预检报告；可用 '
        'python -B -m campuslab.dsh_course --task task.json --template-from-report report-A.json --output evidence-bound.json '
        '生成绑定当前软件/模型/目录的模板。本人根据DSH本次工具记录填写真实 started_at/ended_at（含时区）、'
        'calls[{tool:read或write,path:固定相对路径,status:success或failed,at:含时区时间}]及实际model_result；'
        '只有确实授权才将permission.confirmed改为true。完成任务后先采一份不带摘要的临时报告以取得真实产物SHA，'
        '据此生成绑定模板，再带 --agent-evidence 导入摘要重新采集。不要伪造软件、调用、时间或产物。\n', encoding='utf-8')
    return marker


def _workspace(path, spec):
    result = dict(requested=path, actual=None, exists=None, id=None, task_id=None, input_sha256=None, error='尚未选择专用练习目录')
    artifact = dict(exists=None, sha256=None, value=None, error='尚无产物')
    if path is None:
        return result, artifact
    absolute(path); folder = Path(path); result['exists'] = folder.is_dir()
    try:
        if not folder.is_dir():
            raise ValueError()
        marker_path = folder/'.campuslab-dsh-workspace.json'
        if marker_path.is_symlink() or marker_path.stat().st_size > 2048:
            raise ValueError()
        marker = json.loads(marker_path.read_text(encoding='utf-8'))
        _object(marker, ('schema', 'kind', 'id', 'task_id'), '练习目录标识')
        if type(marker['schema']) is not int or marker['schema'] != 1 or marker['kind'] != 'campuslab-dsh-workspace' or marker['task_id'] != spec['id']:
            raise ValueError()
        uuid.UUID(marker['id'])
        input_file = folder/'input.csv'
        if input_file.is_symlink() or input_file.stat().st_size > 1024:
            raise ValueError()
        result.update(actual=str(folder.resolve()), id=marker['id'], task_id=marker['task_id'], input_sha256=_hash(input_file), error='')
        output = folder/'summary.json'; artifact['exists'] = output.is_file()
        if output.is_file():
            if output.is_symlink() or output.stat().st_size > 4096:
                raise ValueError()
            artifact.update(sha256=_hash(output), value=json.loads(output.read_text(encoding='utf-8-sig')), error='')
    except (OSError, ValueError, TypeError):
        result['error'] = '无法核对专用练习标识/固定文件；请核对路径和任务，勿用其他项目目录'
    return result, artifact


def _validate_excerpt(value, report):
    keys = ('schema', 'source', 'task_id', 'route', 'target', 'installation_sha256', 'package_json', 'runtime', 'runtime_version',
            'workspace', 'workspace_id', 'provider', 'model', 'started_at', 'ended_at', 'permission', 'model_result', 'calls', 'artifact_sha256')
    facts = report['facts']; installation = facts['installation']; runtime = facts['runtime']; work = facts['workspace']
    desktop_package = installation.get('desktop_package')
    desktop_sha = desktop_package['sha256'] if desktop_package else None
    if desktop_sha is not None:
        keys += ('desktop_package_sha256',)
    _object(value, keys, 'DSH最小工具摘要')
    expected = dict(schema=1, task_id=report['task_id'], route=installation['route'], target=report['target']['requested'],
                    installation_sha256=installation['sha256'], package_json=installation['package_json'], runtime=runtime['actual'],
                    runtime_version=runtime['version'], workspace=work['requested'], workspace_id=work['id'],
                    provider=facts['model']['provider'], model=facts['model']['model'], artifact_sha256=facts['artifact']['sha256'])
    if desktop_sha is not None:
        expected['desktop_package_sha256'] = desktop_sha
    if any(value[key] != item for key, item in expected.items()) or type(value['schema']) is not int:
        raise ValueError('DSH工具摘要与当前任务/安装/运行时/模型/练习目录或产物不一致')
    if value['source'] not in ('dsh-user-excerpt', 'protocol-simulation') or value['model_result'] not in ('completed', 'failed', 'unknown'):
        raise ValueError('DSH工具摘要来源或结果无效')
    start, end, now = map(timestamp, (value['started_at'], value['ended_at'], report['collected_at']))
    if not start <= end <= now or (now-start).total_seconds() > 1800:
        raise ValueError('DSH摘要须来自本次30分钟内的实际任务并早于采集')
    _object(value['permission'], ('confirmed', 'read', 'write', 'tools'), '权限声明')
    if type(value['permission']['confirmed']) is not bool or value['permission'] != PERMISSION:
        raise ValueError('DSH练习须明确仅允许固定文件读写权限')
    if not isinstance(value['calls'], list) or not 1 <= len(value['calls']) <= 20:
        raise ValueError('需要本次必要工具调用摘要')
    last = start
    for call in value['calls']:
        _object(call, ('tool', 'path', 'status', 'at'), '工具调用')
        if (call['tool'], call['path']) not in (('read', 'input.csv'), ('write', 'summary.json')) or call['status'] not in ('success', 'failed'):
            raise ValueError('摘要包含本练习未允许的工具/路径/状态')
        at = timestamp(call['at'])
        if not last <= at <= end:
            raise ValueError('工具摘要时间顺序不一致')
        last = at
    return value


def collect(spec, target, package_json=None, workspace=None, provider=None, model=None, evidence=None):
    validate_spec(spec); absolute(target); _identifier(provider); _identifier(model)
    if spec['route'] == 'desktop' and package_json is not None:
        raise ValueError('桌面路线不接受外部CLI包或Node要求')
    path = Path(target)
    installation = dict(route=spec['route'], exists=None, product=None, version=None, sha256=None, package_json=package_json,
                        bin=None, bin_sha256=None, node_requirement=None, error='尚未取得安装证据')
    runtime = dict(kind='bundled-electron' if spec['route'] == 'desktop' else 'selected-node', actual=None, version=None, sha256=None, error='尚未核对运行时')
    target_info = dict(requested=target, actual=None, exists=path.is_file())
    if spec['route'] == 'desktop':
        installation['exists'] = path.is_file()
        if path.is_file():
            installation.update(_desktop_metadata(path)); installation['sha256'] = _hash(path)
            target_info['actual'] = str(path.resolve())
            installation['desktop_package'] = _desktop_package(path)
        runtime['error'] = '桌面程序自带Electron运行时；本工具不执行或读取其凭据/会话'
    else:
        if path.is_file():
            runtime.update(_node_identity(path)); runtime['sha256'] = _hash(path)
            target_info['actual'] = runtime['actual']
        if package_json is not None:
            absolute(package_json); package = Path(package_json); installation['exists'] = package.is_file()
            try:
                if package.name != 'package.json' or package.is_symlink() or package.stat().st_size > 65536:
                    raise ValueError()
                value = json.loads(package.read_text(encoding='utf-8-sig'))
                installation.update(product=value.get('name'), version=value.get('version'), sha256=_hash(package), node_requirement=value.get('engines', {}).get('node'))
                if value.get('bin') != {'dsh': 'lib/bin.js'}:
                    raise ValueError()
                entry = package.parent/'lib'/'bin.js'
                if not entry.is_file() or entry.is_symlink() or entry.resolve().parent.parent != package.parent.resolve():
                    raise ValueError()
                installation.update(bin=str(entry.resolve()), bin_sha256=_hash(entry), error='')
            except (OSError, ValueError, TypeError, AttributeError):
                installation['error'] = '所选DSH包或固定入口元数据不完整；未执行包入口'
    work, artifact = _workspace(workspace, spec)
    report = dict(schema=1, task_id=spec['id'], collected_at=datetime.now(timezone.utc).isoformat(), target=target_info,
                  facts=dict(os=platform.system(), installation=installation, runtime=runtime, workspace=work,
                             model=dict(provider=provider, model=model, connection=None), permission=None, artifact=artifact, agent=None))
    if evidence is not None:
        _validate_excerpt(evidence, report)
        report['facts']['agent'] = deepcopy(evidence)
        report['facts']['permission'] = deepcopy(evidence['permission'])
        if evidence['source'] == 'dsh-user-excerpt':
            report['facts']['model']['connection'] = evidence['model_result'] == 'completed'
    analyze(spec, report)
    return report


def analyze(spec, report):
    validate_spec(spec)
    _object(report, ('schema', 'task_id', 'collected_at', 'target', 'facts'), 'DSH报告')
    if type(report['schema']) is not int or report['schema'] != 1 or report['task_id'] != spec['id']:
        raise ValueError('报告与DSH固定任务不一致')
    timestamp(report['collected_at']); target = report['target']; facts = report['facts']
    _object(target, ('requested', 'actual', 'exists'), '目标')
    absolute(target['requested'])
    if type(target['exists']) is not bool:
        raise ValueError('目标存在状态无效')
    if target['actual'] is not None and (not target['exists'] or absolute(target['actual']) != absolute(target['requested'])):
        raise ValueError('DSH实际程序或Node与所选目标不一致')
    _object(facts, ('os', 'installation', 'runtime', 'workspace', 'model', 'permission', 'artifact', 'agent'), 'DSH事实')
    installation, runtime, work, selected_model, artifact = [facts[key] for key in ('installation', 'runtime', 'workspace', 'model', 'artifact')]
    installation_keys = ('route', 'exists', 'product', 'version', 'sha256', 'package_json', 'bin', 'bin_sha256', 'node_requirement', 'error')
    _object(installation, installation_keys+(('desktop_package',) if 'desktop_package' in installation else ()), '软件安装')
    _object(runtime, ('kind', 'actual', 'version', 'sha256', 'error'), '运行时')
    _object(work, ('requested', 'actual', 'exists', 'id', 'task_id', 'input_sha256', 'error'), '练习目录')
    _object(selected_model, ('provider', 'model', 'connection'), '模型接入')
    _object(artifact, ('exists', 'sha256', 'value', 'error'), '固定产物')
    if installation['route'] != spec['route'] or runtime['kind'] != ('bundled-electron' if spec['route'] == 'desktop' else 'selected-node'):
        raise ValueError('DSH路线或运行时类型不一致')
    for value in (installation['exists'], work['exists'], artifact['exists'], selected_model['connection']):
        if value is not None and type(value) is not bool:
            raise ValueError('DSH事实布尔类型无效')
    for value in (installation['sha256'], installation['bin_sha256'], runtime['sha256'], work['input_sha256'], artifact['sha256']):
        _sha(value)
    for obj in (installation, runtime, work, artifact):
        if not isinstance(obj['error'], str):
            raise ValueError('DSH错误说明无效')
    for obj, keys in ((installation, ('product', 'version', 'node_requirement')), (runtime, ('version',))):
        if any(obj[key] is not None and not isinstance(obj[key], str) for key in keys):
            raise ValueError('DSH版本或程序标识类型无效')
    for value in (installation['package_json'], installation['bin'], runtime['actual'], work['requested'], work['actual']):
        if value is not None:
            absolute(value)
    for value in (selected_model['provider'], selected_model['model']):
        _identifier(value)
    if work['actual'] is not None and (absolute(work['actual']) != absolute(work['requested']) or work['exists'] is not True):
        raise ValueError('实际练习目录不一致')
    if work['id'] is not None:
        try:
            uuid.UUID(work['id'])
        except (ValueError, TypeError, AttributeError):
            raise ValueError('练习目录标识无效') from None
    if work['task_id'] is not None and work['task_id'] != spec['id']:
        raise ValueError('练习目录绑定其他任务')
    if spec['route'] == 'desktop':
        if any(installation[key] is not None for key in ('package_json', 'bin', 'bin_sha256', 'node_requirement')) or any(runtime[key] is not None for key in ('actual', 'version', 'sha256')):
            raise ValueError('桌面报告不能混入CLI运行时证据')
    elif runtime['actual'] is not None and (target['actual'] is None or absolute(runtime['actual']) != absolute(target['actual'])):
        raise ValueError('所选Node身份关联不一致')
    desktop_package = installation.get('desktop_package')
    if desktop_package is not None:
        if spec['route'] != 'desktop' or installation['exists'] is not True or target['actual'] is None:
            raise ValueError('桌面包元数据必须绑定所选实际桌面程序')
        _object(desktop_package, ('path', 'sha256', 'package_sha256', 'name', 'version', 'main', 'error'), '桌面包元数据')
        expected_path = ntpath.join(ntpath.dirname(target['requested']), 'resources', 'app.asar')
        if absolute(desktop_package['path']) != absolute(expected_path):
            raise ValueError('桌面包不是所选程序的相邻resources/app.asar')
        for key in ('sha256', 'package_sha256'):
            _sha(desktop_package[key])
        if not isinstance(desktop_package['error'], str) or any(desktop_package[key] is not None and (not isinstance(desktop_package[key], str) or not 1 <= len(desktop_package[key]) <= 100) for key in ('name', 'version', 'main')):
            raise ValueError('桌面包身份字段无效')
    agent = facts['agent']
    if agent is not None:
        _validate_excerpt(agent, report)
        if facts['permission'] != agent['permission'] or selected_model['connection'] != (agent['model_result'] == 'completed' if agent['source'] == 'dsh-user-excerpt' else None):
            raise ValueError('模型连接或权限证据未与本次摘要关联')
    elif facts['permission'] is not None or selected_model['connection'] is not None:
        raise ValueError('配置或勾选不能冒充连接/实际授权证据')
    checks = []
    def check(name, state, observed, required):
        checks.append(dict(id=name, status=state, observed=observed, requirement=required))
    check('os', 'unknown' if facts['os'] is None else ('pass' if facts['os'] == 'Windows' else 'mismatch'), facts['os'], 'Windows')
    software_state = 'missing' if installation['exists'] is False else 'unknown'
    product = 'DeepSeek Harness' if spec['route'] == 'desktop' else '@deepseek-ai/dsh'
    if installation['exists'] is True and installation['product'] is not None and installation['version'] is not None:
        version_valid = installation['version'] == SUPPORTED_VERSION
        if desktop_package is not None:
            version_valid = installation['version'] in (SUPPORTED_VERSION, '0.2.2.0') and desktop_package['name'] == '@deepseek-ai/dsh-desktop' and desktop_package['version'] == SUPPORTED_VERSION and desktop_package['main'] == 'lib/main.js' and bool(desktop_package['sha256']) and bool(desktop_package['package_sha256']) and not desktop_package['error']
        valid = installation['product'] == product and version_valid and bool(installation['sha256']) and not installation['error'] and target['actual'] is not None
        if spec['route'] == 'cli':
            valid = valid and installation['node_requirement'] == '>=24.9.0' and bool(installation['bin']) and bool(installation['bin_sha256'])
        software_state = 'pass' if valid else 'mismatch'
    check('dsh:software', software_state, installation, product+' '+SUPPORTED_VERSION+'；静态身份/版本不证明已登录或任务成功')
    if spec['route'] == 'cli':
        node_state = 'missing' if target['exists'] is False else 'unknown'
        if runtime['version'] is not None:
            try:
                node_state = 'pass' if version(runtime['version']) >= version('24.9.0') and runtime['actual'] and runtime['sha256'] and not runtime['error'] else 'mismatch'
            except ValueError:
                node_state = 'unknown'
        check('dsh:node', node_state, runtime, '本人所选Node>=24.9.0；其他Node课程通过不能代替')
    work_state = 'missing' if work['exists'] is False else ('pass' if work['id'] and work['input_sha256'] == INPUT_SHA and work['actual'] and not work['error'] else 'unknown')
    check('dsh:workspace', work_state, work, '同一专用目录、任务标识和固定CSV摘要')
    actual_evidence = agent is not None and agent['source'] == 'dsh-user-excerpt'
    check('dsh:model', 'unknown' if selected_model['connection'] is None else ('pass' if selected_model['connection'] and selected_model['provider'] and selected_model['model'] else 'mismatch'), selected_model, '实际本人任务模型结果；仅提供方/模型配置不证明连接可用')
    check('dsh:permission', 'pass' if actual_evidence and facts['permission'] == PERMISSION else 'unknown', facts['permission'], '本人实际授权：只读input.csv、只写summary.json、固定read/write工具')
    tools_state = 'unknown'
    if actual_evidence:
        calls = agent['calls']
        tools_state = 'pass' if agent['model_result'] == 'completed' and any(c['tool'] == 'read' and c['status'] == 'success' for c in calls) and any(c['tool'] == 'write' and c['status'] == 'success' for c in calls) and all(c['status'] == 'success' for c in calls) else 'mismatch'
    check('dsh:tools', tools_state, agent, '本人提供本次DSH读/写工具摘要；普通聊天、声明或模拟不代替')
    artifact_state = 'unknown' if artifact['exists'] is None else ('missing' if artifact['exists'] is False else 'mismatch')
    value = artifact['value']
    if artifact['exists'] is True and isinstance(value, dict) and set(value) == {'count', 'sum'} and all(type(value[k]) is int for k in value) and value == spec['expected'] and artifact['sha256'] and not artifact['error']:
        artifact_state = 'pass'
    check('dsh:artifact', artifact_state, artifact, '本机summary.json恰为整数count=3、sum=42；产物不单独证明Agent调用')
    return dict(task_id=spec['id'], target=target, collected_at=report['collected_at'], checks=checks,
                passed=all(c['status'] == 'pass' for c in checks), evidence_basis=EVIDENCE_BASIS if actual_evidence else '只读元数据/本机产物；无真实DSH任务摘要，相关项未知')


def compare_identity(before, after):
    if before['task_id'] != after['task_id'] or absolute(before['target']['requested']) != absolute(after['target']['requested']):
        raise ValueError('DSH复检须保持同一任务、路线及目标程序')
    for name, keys in [('installation', ('route', 'package_json', 'sha256', 'bin', 'bin_sha256')),
                       ('runtime', ('kind', 'actual', 'version', 'sha256')),
                       ('workspace', ('requested', 'id', 'input_sha256')),
                       ('model', ('provider', 'model'))]:
        a, b = before['facts'][name], after['facts'][name]
        for key in keys:
            if a[key] != b[key]:
                raise ValueError('DSH复检组件身份改变：'+name+'/'+key+'；请为新目标重新初检')
    if before['facts']['installation'].get('desktop_package') != after['facts']['installation'].get('desktop_package'):
        raise ValueError('DSH桌面包身份改变；请为新目标重新初检')
    a, b = before['facts']['agent'], after['facts']['agent']
    if a is not None and b is not None and timestamp(b['ended_at']) <= timestamp(a['ended_at']):
        raise ValueError('DSH复检须使用较晚的实际Agent任务摘要，不能重复旧成功')


def evidence_template(report):
    """Copy only public identity fields; every execution/permission field starts unconfirmed."""
    facts = report['facts']; installation = facts['installation']; runtime = facts['runtime']; work = facts['workspace']
    result = dict(schema=1, source='dsh-user-excerpt', task_id=report['task_id'], route=installation['route'],
                target=report['target']['requested'], installation_sha256=installation['sha256'],
                package_json=installation['package_json'], runtime=runtime['actual'], runtime_version=runtime['version'],
                workspace=work['requested'], workspace_id=work['id'], provider=facts['model']['provider'], model=facts['model']['model'],
                started_at=None, ended_at=None, permission=dict(confirmed=False, read=['input.csv'], write=['summary.json'], tools=['read', 'write']),
                model_result='unknown', calls=[], artifact_sha256=facts['artifact']['sha256'])
    desktop_package = installation.get('desktop_package')
    if desktop_package and desktop_package['sha256'] is not None:
        result['desktop_package_sha256'] = desktop_package['sha256']
    return result


def main():
    parser = argparse.ArgumentParser(description='只创建本项目固定DSH练习或未完成摘要模板；不启动DSH、不调用模型')
    parser.add_argument('--task', type=Path)
    parser.add_argument('--prepare-workspace', help='尚不存在的专用课程目录')
    parser.add_argument('--template-from-report', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.prepare_workspace and args.task and not args.template_from_report and not args.output:
        spec = json.loads(args.task.read_text(encoding='utf-8-sig'))
        prepare_workspace(spec, args.prepare_workspace)
        print('已创建固定DSH练习；本人在DSH启动和授权。尚无真实Agent运行证据。')
    elif args.template_from_report and args.output and not args.prepare_workspace:
        report = json.loads(args.template_from_report.read_text(encoding='utf-8-sig'))
        if args.task:
            spec = json.loads(args.task.read_text(encoding='utf-8-sig'))
        else:
            raise ValueError('生成摘要模板时同时提供 --task 以核验当前固定任务')
        analyze(spec, report)
        with args.output.open('x', encoding='utf-8') as output:
            json.dump(evidence_template(report), output, ensure_ascii=False, indent=2)
        print('已保存未完成的绑定模板；本人仅填写实际工具记录，不含密码/密钥或隐藏推理。')
    else:
        parser.error('使用 --task task.json --prepare-workspace PATH，或 --task task.json --template-from-report report.json --output new-template.json')


if __name__ == '__main__':
    main()
