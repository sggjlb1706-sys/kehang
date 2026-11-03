"""Loopback application. No endpoint executes commands on behalf of students."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
import zipfile

from .courses import CourseStore
from .diagnosis import configuration, diagnose, redact
from .guidance import plan
from .rules import analyze, compare, task, validate_task

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
            elif path.path == '/api/goal':
                goal = parse_qs(path.query).get('goal', ['python-basics'])[0]
                self.send(200, task(goal))
            elif path.path.startswith('/api/course/'):
                self.send(200, self.server.store.get(path.path.rsplit('/',1)[1]))
            elif path.path == '/api/tool':
                spec = self.server.store.get(parse_qs(path.query)['course'][0]) if 'course' in parse_qs(path.query) else task(parse_qs(path.query).get('goal',['python-basics'])[0])
                self.send(200, self.tool_zip(spec), 'application/zip', 'CampusLab-tool.zip')
            elif path.path == '/api/config':
                self.send(200, dict(local_only=True, portable_available=bool(self.server.runtime_zip and self.server.runtime_zip.is_file()), ai=configuration()))
            else:
                self.send(404, dict(error='未找到该地址'))
        except (ValueError, KeyError, TypeError, OSError) as exc:
            self.send(400, dict(error=str(exc) if isinstance(exc, ValueError) else '请求不完整或资源不可用'))

    def tool_zip(self, spec):
        output = BytesIO()
        with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as z:
            for name in ['__init__.py', 'rules.py', 'collect.py', 'probe.py']:
                z.writestr('campuslab/' + name, (ROOT/'campuslab'/name).read_bytes())
            z.writestr('task.json', json.dumps(spec, ensure_ascii=False, indent=2))
            z.writestr('README.txt', 'CampusLab read-only collector. Extract all files; do not run inside ZIP.\nManual: runtime\\python.exe -B -m campuslab.collect --task task.json --target C:\\Course\\python.exe --output report.json\nWithout bundled runtime use your existing tool Python. Tool runtime is not a course environment.\n')
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
            self.check_origin()
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
            if self.path == '/api/course':
                spec = task(body.get('scenario','python-basics'), body.get('title'), body.get('python_min','3.10'), body.get('python_max','3.15'), body.get('requests_min','2.31'))
                self.send(200, self.server.store.publish(spec))
            elif self.path == '/api/analyze':
                self.send(200, analyze(body['task'], body['report']))
            elif self.path == '/api/compare':
                self.send(200, compare(body['task'], body['before'], body['after']))
            elif self.path == '/api/plan':
                self.send(200, plan(body['task'],body.get('mode','novice'),body.get('resources')))
            elif self.path == '/api/preview':
                result=analyze(body['task'],body['report'])
                error=body.get('error','')
                if not isinstance(error,str) or len(error)>8000:
                    raise ValueError('报错过长')
                self.send(200, dict(preview=redact(json.dumps(dict(task_title=body['task']['title'],scenario=body['task']['scenario'],checks=result['checks'],user_error=error),ensure_ascii=False,indent=2)),ai=configuration()))
            elif self.path == '/api/diagnose':
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
        print(f'CampusLab: http://127.0.0.1:{server.server_port}/ (local only)', flush=True)
        server.serve_forever()


if __name__ == '__main__': main()
