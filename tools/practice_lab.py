"""Agent-run fixed lab proof, never an arbitrary uploaded Notebook runner.

Uses existing local Python/ipykernel only. All downloaded runtimes and course
libraries are new temporary files; only this run's reports/learning artifacts
are retained. Existing evidence is never overwritten.
"""
from contextlib import ExitStack
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
from urllib.request import Request, urlopen
import zipfile

from campuslab.practice import FILES, check, make_practice
from campuslab.rules import analyze, compare, task
from campuslab.web import AppServer

ROOT = Path(__file__).resolve().parents[1]
PYTHON = Path(r'D:\ANACONDA\python.exe')
KERNEL = Path(r'D:\ANACONDA\share\jupyter\kernels\python3\kernel.json')
QUERY = 'SELECT category, COUNT(*), SUM(score) FROM scores GROUP BY category ORDER BY category'


def save(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')


def main():
    output=ROOT/'records/practice/lab-run'
    resume = sys.argv[1:] == ['--resume-collectors']
    if sys.argv[1:] and not resume:
        raise ValueError('Only --resume-collectors is accepted; no arbitrary input paths')
    if not resume: output.mkdir(parents=True,exist_ok=False)
    summary=dict(started_at=datetime.now(timezone.utc).isoformat(),
        actor='代理在同一电脑的隔离目录执行固定练习；不是学生用户研究、独立新手或第二设备。',
        python=str(PYTHON),kernel_spec=str(KERNEL),commands=[],complete=False)
    if resume:
        summary=json.loads((output/'summary.json').read_text(encoding='utf-8'))
        assert not summary['complete']
        summary['resumed_at']=datetime.now(timezone.utc).isoformat()
    try:
        assert PYTHON.is_file() and KERNEL.is_file()
        with tempfile.TemporaryDirectory(prefix='课航 固定 实训 ') as temporary, ExitStack() as stack:
            folder=Path(temporary)
            servers=[]
            for i in range(2):
                server=AppServer(0,folder/f'library-{i}.sqlite',ROOT/'vendor/python-3.13.17-embed-amd64.zip')
                thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
                stack.callback(thread.join);stack.callback(server.server_close);stack.callback(server.shutdown)
                servers.append(server)
            def request(index,path,body=None):
                raw=json.dumps(body,ensure_ascii=False).encode('utf-8') if body is not None else None
                return urlopen(Request(f'http://127.0.0.1:{servers[index].server_port}'+path,data=raw,
                    headers={'Content-Type':'application/json'} if raw else {}),timeout=10)
            if not resume:
                teacher=json.load(request(0,'/api/practice/publish',{}))
                learner=json.load(request(1,'/api/practice/import',dict(package=teacher['package'])))
                assert teacher['practice']==learner['practice']==make_practice()
                summary['same_computer_libraries']=[dict(port=s.server_port,database=str(s.store.path)) for s in servers]
                save(output/'teacher-publish.json',teacher);save(output/'learner-import.json',learner)
                with zipfile.ZipFile(BytesIO(request(1,'/api/practice/materials').read())) as z:
                    assert z.testzip() is None
                    assert z.read('01_Notebook练习.ipynb')==(FILES/'01_Notebook练习.ipynb').read_bytes()
                    assert z.read('02_SQLite练习.py')==(FILES/'02_SQLite练习.py').read_bytes()
                    z.extractall(output)
                notebook=json.loads((output/'01_Notebook练习.ipynb').read_text(encoding='utf-8'))
                replacements={
                    'row_count = None  # TODO: 数据行数':'row_count = len(df)  # 代理按固定步骤填入计算表达式',
                    'score_total = None  # TODO: score列合计':"score_total = df['score'].sum()  # 实际计算",
                    'group_totals = None  # TODO: category分组score合计字典':"group_totals = df.groupby('category')['score'].sum().to_dict()  # 实际计算"}
                for cell in notebook['cells']:
                    if cell['cell_type']=='code':
                        source=''.join(cell['source'])
                        for before,after in replacements.items():source=source.replace(before,after)
                        cell['source']=source.splitlines(keepends=True)
                import nbformat
                from nbclient import NotebookClient
                from jupyter_client import KernelManager
                from jupyter_client.kernelspec import KernelSpecManager
                kernels=folder/'kernels';definition=kernels/'kehang-lab';definition.mkdir(parents=True)
                save(definition/'kernel.json',dict(argv=[str(PYTHON),'-I','-m','ipykernel_launcher','-f','{connection_file}'],
                    language='python',display_name='Kehang fixed lab existing Python'))
                manager=KernelManager(kernel_name='kehang-lab',kernel_spec_manager=KernelSpecManager(kernel_dirs=[str(kernels)]),
                                      connection_file=str(folder/'lab-connection.json'),ip='127.0.0.1')
                env={k:v for k,v in os.environ.items() if not k.upper().startswith(('PYTHON','JUPYTER','IPYTHON'))}
                env.update(PYTHONDONTWRITEBYTECODE='1',IPYTHONDIR=str(folder/'ipython'),JUPYTER_CONFIG_DIR=str(folder/'config'),JUPYTER_DATA_DIR=str(folder/'data'))
                try:
                    book=nbformat.reads(json.dumps(notebook),as_version=4)
                    client=NotebookClient(book,km=manager,timeout=45,allow_errors=False)
                    with open(os.devnull,'w') as quiet:
                        client.execute(cwd=str(output),env=env,stdout=quiet,stderr=quiet,cleanup_kc=True)
                    nbformat.write(book,output/'学生已执行.ipynb')
                finally:
                    if manager.has_kernel:manager.shutdown_kernel(now=True)
                    manager.cleanup_resources()
                script=output/'02_SQLite练习.py'
                script.write_text(script.read_text(encoding='utf-8').replace("QUERY = ''",'QUERY = '+repr(QUERY)),encoding='utf-8')
                command=[str(PYTHON),'-X','utf8','-B',str(script)]
                summary['commands'].append(command)
                completed=subprocess.run(command,cwd=folder,capture_output=True,text=True,encoding='utf-8',timeout=20)
                (output/'sqlite-learning-run.txt').write_text(completed.stdout+completed.stderr,encoding='utf-8')
                assert completed.returncode==0,(completed.returncode,completed.stderr)
                submission=json.loads((output/'实训成果.json').read_text(encoding='utf-8'))
                assert check(make_practice(),submission)['passed']
                save(output/'correct-result-check.json',check(make_practice(),submission))
                wrong=json.loads(json.dumps(submission));wrong['notebook']['array_sum']=43
                save(output/'constructed-wrong-result.json',wrong)
                rejected=check(make_practice(),wrong);assert rejected['status']=='mismatch'
                save(output/'constructed-wrong-check.json',dict(actor='代理构造的测试负例，不是学生犯错',result=rejected))
            for scenario in ('python-basics','notebook-data','sqlite-basics'):
                tool=folder/(scenario+' 中文 空格 工具');tool.mkdir()
                with zipfile.ZipFile(BytesIO(request(1,'/api/tool?goal='+scenario).read())) as z:
                    assert z.testzip() is None
                    z.extractall(tool)
                for stage in ('A','B'):
                    if scenario in ('python-basics','notebook-data'):
                        command=['cmd.exe','/d','/c','Start-Collect.cmd']
                        answers=[str(PYTHON)]
                        if scenario=='notebook-data':answers.append(str(KERNEL))
                        answers.extend([stage,'START',''])
                        completed=subprocess.run(command,input='\n'.join(answers)+'\n',cwd=tool,
                            capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=150)
                        report_path=tool/('report-'+stage+'.json')
                    else:
                        report_path=tool/('report-'+stage+'.json')
                        command=[str(tool/'runtime/python.exe'),'-X','utf8','-B','-m','campuslab.collect',
                            '--task',str(tool/'task.json'),'--target',str(output/'scores.sqlite'),'--output',str(report_path)]
                        completed=subprocess.run(command,cwd=tool,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=40)
                    summary['commands'].append(dict(scenario=scenario,stage=stage,argv=command,
                        input_note='明确课程Python/内核、A或B、START及pause回车；代理输入，仅验证主动入口' if scenario!='sqlite-basics' else '无交互；固定所选SQLite文件',returncode=completed.returncode))
                    (output/(scenario+'-'+stage+'-console.txt')).write_text(completed.stdout+completed.stderr,encoding='utf-8')
                    assert completed.returncode==0,(scenario,stage,completed.stdout,completed.stderr)
                    report=json.loads(report_path.read_text(encoding='utf-8'))
                    save(output/(scenario+'-'+stage+'.json'),report)
                    result=analyze(task(scenario),report);save(output/(scenario+'-'+stage+'-analysis.json'),result)
                    assert result['passed'],(scenario,stage,result)
                before=json.loads((output/(scenario+'-A.json')).read_text(encoding='utf-8'))
                after=json.loads((output/(scenario+'-B.json')).read_text(encoding='utf-8'))
                comparison=compare(task(scenario),before,after)
                assert comparison['outcome']=='stable-pass'
                save(output/(scenario+'-comparison.json'),comparison)
            summary.update(complete=True,scope='两本机实例传递；模板由代理填写固定表达式并真实执行，三课程A/B为同目标稳定复检；错误成果仅构造负例。没有安装、真实AI请求、DSH/VM或其他设备。',
                source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'campuslab/practice.py',ROOT/'campuslab/launcher.py',ROOT/'campuslab/web.py',*FILES.iterdir()]})
    finally:
        summary['ended_at']=datetime.now(timezone.utc).isoformat()
        save(output/'summary.json',summary)
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
