"""Loopback application. No endpoint executes commands on behalf of students."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
import zipfile

from .courses import CourseStore
from .diagnosis import configuration, diagnose, redact_value
from .guidance import plan
from .rules import analyze, compare, task, validate_task
from .portable import export_package, import_package, guide_html

ROOT = Path(__file__).resolve().parents[1]


class AppServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, port=8772, database=None, runtime_zip=None):
        super().__init__(('127.0.0.1', port), Handler)
        self.store = CourseStore(database or ROOT / 'data/courses.sqlite')
        self.runtime_zip = Path(runtime_zip) if runtime_zip else None


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send(self, status, body, content_type='application/json; charset=utf-8', filename=None):
        if not isinstance(body, bytes):
            body = json.dumps(body, ensure_ascii=False, allow_nan=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        if filename:
            self.send_header('Content-Disposition', 'attachment; filename="' + filename + '"')
        self.end_headers()
        self.wfile.write(body)

    def check_origin(self):
        port = self.server.server_port
        hosts = {f'127.0.0.1:{port}', f'localhost:{port}'}
        if len(self.headers.get_all('Host', [])) != 1 or self.headers.get('Host') not in hosts:
            raise ValueError('Host不符合本机服务地址')
        origin = self.headers.get('Origin')
        if origin is not None and origin not in {'http://' + h for h in hosts}:
            raise ValueError('拒绝跨来源请求')

    def do_GET(self):
        try:
            self.check_origin()
            path = urlsplit(self.path)
            assets = {'/':'index.html', '/app.js':'app.js', '/style.css':'style.css'}
            if path.path in assets:
                name = assets[path.path]
                kind = {'html':'text/html', 'js':'text/javascript', 'css':'text/css'}[name.rsplit('.',1)[1]]
                self.send(200, (ROOT/'web'/name).read_bytes(), kind + '; charset=utf-8')
            elif path.path == '/api/practice':
                from .practice import make_practice, export_package as practice_package
                spec = make_practice()
                self.send(200, dict(practice=spec, package=practice_package(spec)))
            elif path.path == '/api/practice/materials':
                from .practice import make_practice, materials_zip
                self.send(200, materials_zip(make_practice()), 'application/zip', 'Kehang-practice-materials.zip')
            elif path.path == '/api/goal':
                goal = parse_qs(path.query).get('goal', ['python-basics'])[0]
                self.send(200, task(goal))
            elif path.path.startswith('/api/course/'):
                self.send(200, self.server.store.get(path.path.rsplit('/',1)[1]))
            elif path.path == '/api/tool':
                spec = self.server.store.get(parse_qs(path.query)['course'][0]) if 'course' in parse_qs(path.query) else task(parse_qs(path.query).get('goal',['python-basics'])[0])
                self.send(200, self.tool_zip(spec), 'application/zip', 'Kehang-tool.zip')
            elif path.path == '/api/config':
                self.send(200, dict(local_only=True, portable_available=bool(self.server.runtime_zip and self.server.runtime_zip.is_file()), ai=configuration()))
            elif path.path == '/api/catalog':
                from .preparation import CATALOG
                self.send(200,CATALOG)
            else:
                self.send(404, dict(error='未找到该地址'))
        except (ValueError, KeyError, TypeError, OSError) as exc:
            self.send(400, dict(error=str(exc) if isinstance(exc, ValueError) else '请求不完整或资源不可用'))

    def tool_zip(self, spec):
        output = BytesIO()
        with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as z:
            for name in ['__init__.py', 'rules.py', 'collect.py', 'probe.py']:
                z.writestr('campuslab/' + name, (ROOT/'campuslab'/name).read_bytes())
            if spec['scenario'] in ('python-basics', 'notebook-data') and self.server.runtime_zip and self.server.runtime_zip.is_file():
                z.writestr('campuslab/launcher.py', (ROOT/'campuslab/launcher.py').read_bytes())
                z.writestr('Start-Collect.cmd', '@echo off\r\nsetlocal DisableDelayedExpansion\r\ncd /d "%~dp0"\r\n"%~dp0runtime\\python.exe" -X utf8 -B -m campuslab.launcher\r\npause\r\n')
            if spec['scenario'] == 'node-basics':
                for name in ['node_collect.py', 'node_probe.js']:
                    z.writestr('campuslab/' + name, (ROOT/'campuslab'/name).read_bytes())
            if spec['scenario'] in ('pytorch-cpu','pytorch-gpu','vm-linux'):
                names=['torch_course.py','torch_probe.py'] if spec['scenario'].startswith('pytorch-') else ['vm_course.py','guest_probe.py']
                for name in names:
                    z.writestr('campuslab/'+name,(ROOT/'campuslab'/name).read_bytes())
                if spec['scenario']=='vm-linux':
                    z.writestr('guest_probe.py',(ROOT/'campuslab/guest_probe.py').read_bytes())
            z.writestr('campuslab/preparation.py',(ROOT/'campuslab/preparation.py').read_bytes())
            new_files={'notebook-data':['notebook_course.py','notebook_probe.py'],
                       'java-jdk':['java_course.py'],'sqlite-basics':['sqlite_course.py'],
                       'ai-web-deepseek':['ai_course.py','ai_probe.py','diagnosis.py'],
                       'deepseek-api':['ai_course.py','ai_probe.py','diagnosis.py'],
                       'dsh-desktop':['dsh_course.py'],'dsh-cli':['dsh_course.py']}
            for name in new_files.get(spec['scenario'],[]):
                z.writestr('campuslab/'+name,(ROOT/'campuslab'/name).read_bytes())
            if spec['scenario']=='notebook-data':
                z.writestr('campuslab/data/notebook_scores.csv',(ROOT/'campuslab/data/notebook_scores.csv').read_bytes())
            if spec['scenario']=='deepseek-api':
                from .ai_course import preview
                z.writestr('api-preview.json',json.dumps(preview(spec),ensure_ascii=False,indent=2))
            if spec['scenario']=='ai-web-deepseek':
                from .ai_course import web_record_template
                z.writestr('web-record.json',json.dumps(web_record_template(spec),ensure_ascii=False,indent=2))
            z.writestr('task.json', json.dumps(spec, ensure_ascii=False, indent=2))
            examples={'vm-linux':r'C:\Program Files\Oracle\VirtualBox\VBoxManage.exe','node-basics':r'C:\CourseNode\node.exe',
                      'java-jdk':r'C:\Program Files\Zulu\zulu-21','sqlite-basics':r'C:\Course\demo.sqlite',
                      'ai-web-deepseek':r'C:\Course\exercise','dsh-desktop':r'C:\DSH\DeepSeek Harness.exe','dsh-cli':r'C:\Node\node.exe'}
            target_example=examples.get(spec['scenario'],r'C:\Course\python.exe')
            extras={'notebook-data':' --kernel-spec "C:\\Users\\Student\\AppData\\Roaming\\jupyter\\kernels\\python3\\kernel.json"',
                    'ai-web-deepseek':' --learning-record web-record.json',
                    'deepseek-api':' --api-preview api-preview.json',
                    'dsh-cli':' --package-json "C:\\CourseDSH\\package.json" --workspace "C:\\Course\\dsh-practice"',
                    'dsh-desktop':' --workspace "C:\\Course\\dsh-practice"'}.get(spec['scenario'],'')
            if extras:
                z.writestr('COURSE.txt','Add these explicit fields to the manual collector command: '+extras+'\n'
                    'Notebook: select an existing reviewed kernel.json for the same Python; a real temporary kernel runs fixed CSV.\n'
                    'API: preview is editable. No request by default. Only --api-send asks for SEND <preview digest> and a hidden key in the terminal; possible fees. Never put keys in files or commands.\n'
                    'DSH: no DSH process is launched. Prepare a NEW workspace explicitly using python -B -m campuslab.dsh_course --task task.json --prepare-workspace NEW_ABSOLUTE_PATH; user runs and authorizes the real Agent. Evidence is a minimal user excerpt, never credentials/config dumps.\n')
            z.writestr('README.txt', f'Kehang / 课航——计算机课程学习与实训助手. Read-only collector. Extract all files; do not run inside ZIP.\nManual: runtime\\python.exe -B -m campuslab.collect --task task.json --target "{target_example}" --output report.json\nWithout bundled runtime use your existing tool Python. Tool runtime is not a course environment.\nFor PyTorch GPU explicitly add --gpu-run. For VM use --vm-id UUID-or-absolute-vmx-path and optionally --guest-report guest.json. Linux guest: python3 guest_probe.py --task-id TASK_SHA --vm-id SAME_VM_ID --output guest.json. Nothing starts a VM.\nHardware preparation: runtime\\python.exe -B -m campuslab.preparation --output hardware.json\n')
            if self.server.runtime_zip and self.server.runtime_zip.is_file():
                with zipfile.ZipFile(self.server.runtime_zip) as runtime:
                    for info in runtime.infolist():
                        if info.is_dir():
                            continue
                        if '/' in info.filename or '\\' in info.filename:
                            raise ValueError('运行时包结构不符合官方嵌入包')
                        data = runtime.read(info)
                        if info.filename.endswith('._pth'):
                            data += b'\n..\n'
                        z.writestr('runtime/' + info.filename, data)
                z.writestr('runtime/.campuslab-tool-runtime', 'Bundled tool only; never course target')
        return output.getvalue()

    def do_POST(self):
        try:
            if self.headers.get('Content-Type','').split(';')[0] != 'application/json':
                raise ValueError('请求须使用JSON')
            if self.headers.get('Transfer-Encoding') is not None or len(self.headers.get_all('Content-Length',[])) != 1:
                raise ValueError('请求长度缺失或冲突')
            length = int(self.headers['Content-Length'])
            if not 0 < length <= 262144:
                raise ValueError('请求过大或为空')
            def invalid_constant(value):
                raise ValueError('JSON中不允许NaN或Infinity')
            body = json.loads(self.rfile.read(length), parse_constant=invalid_constant)
            if not isinstance(body, dict):
                raise ValueError('请求须为对象')
            self.check_origin()
            if self.path in ('/api/practice/publish', '/api/practice/import'):
                from .practice import make_practice, import_package as practice_import, publish as practice_publish
                spec = practice_import(body['package']) if self.path.endswith('/import') else make_practice()
                self.send(200, practice_publish(self.server.store,spec))
            elif self.path == '/api/practice/check':
                from .practice import check as practice_check
                self.send(200, practice_check(body['practice'],body.get('submission')))
            elif self.path == '/api/course':
                spec = task(body.get('scenario','python-basics'), body.get('title'), body.get('python_min','3.10'), body.get('python_max','3.15'), body.get('requests_min','2.31'))
                self.send(200, self.server.store.publish(spec))
            elif self.path == '/api/analyze':
                self.send(200, analyze(body['task'], body['report']))
            elif self.path == '/api/compare':
                self.send(200, compare(body['task'], body['before'], body['after']))
            elif self.path == '/api/plan':
                self.send(200, plan(body['task'],body.get('mode','novice'),body.get('resources'),body.get('report')))
            elif self.path == '/api/lesson':
                from .teaching import lesson_checks
                self.send(200,lesson_checks(analyze(body['task'],body['report'])))
            elif self.path == '/api/learning-preview':
                from .ai_course import preview
                validate_task(body['task'])
                self.send(200,preview(body['task']))
            elif self.path == '/api/need':
                from .preparation import resolve_need
                self.send(200,resolve_need(body.get('text'),body.get('clarification')))
            elif self.path == '/api/recommend':
                from .preparation import recommend
                validate_task(body['task'])
                self.send(200,recommend(body['task'],body.get('hardware')))
            elif self.path == '/api/package':
                self.send(200,export_package(body['task']))
            elif self.path == '/api/import-course':
                spec=import_package(body['package'])
                self.send(200,self.server.store.publish(spec))
            elif self.path == '/api/guide':
                self.send(200,guide_html(body['task']).encode('utf-8'),'text/html; charset=utf-8','Kehang-guide.html')
            elif self.path == '/api/share':
                result=analyze(body['task'],body['report'])
                self.send(200,redact_value(dict(share_only=True,note='脱敏交流副本，不作为原始复检报告导入',task=body['task'],report=body['report'],result=result)))
            elif self.path == '/api/preview':
                spec=validate_task(body['task']) if body.get('task') else None
                result=analyze(spec,body['report']) if body.get('report') is not None and spec else None
                error=body.get('error','')
                if not isinstance(error,str) or len(error)>8000:
                    raise ValueError('报错过长')
                preview=redact_value(dict(task_title=spec['title'] if spec else '尚未确认课程',scenario=spec['scenario'] if spec else None,checks=result['checks'] if result else [],evidence_note='引用已有报告；建议不改变规则' if result else '没有检测证据，解释器、依赖、硬件与目标身份均未确认；请先澄清课程并手动采集',user_error=error))
                self.send(200, dict(preview=json.dumps(preview,ensure_ascii=False,indent=2),ai=configuration()))
            elif self.path == '/api/diagnose':
                if body.get('report') is not None:
                    analyze(body['task'],body['report'])
                self.send(200, diagnose(body.get('preview'),body.get('consent')))
            else:
                self.send(404, dict(error='未找到该接口'))
        except (ValueError, KeyError, TypeError, OSError):
            self.send(400, dict(error='请求无效：请核对固定任务、完整报告、目标路径及时间顺序'))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=8772)
    parser.add_argument('--database',type=Path)
    parser.add_argument('--runtime-zip',type=Path)
    args=parser.parse_args()
    with AppServer(args.port,args.database,args.runtime_zip) as server:
        print(f'课航: http://127.0.0.1:{server.server_port}/ (local only)', flush=True)
        server.serve_forever()


if __name__ == '__main__': main()
