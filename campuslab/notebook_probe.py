"""Run only our reviewed data cell in a new loopback ipykernel, then close it."""
import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import tempfile
import time
import sys

CSV = 'category,score\nA,10\nA,20\nB,12\n'
CODE = '''import json, sys, platform, io, importlib.metadata
result = {"actual": sys.executable, "python": platform.python_version(), "packages": {}, "result": None, "error": ""}
for name in ("numpy", "pandas"):
    item = {"installed": False, "version": None, "imported": False, "path": None, "error": ""}
    result["packages"][name] = item
    try:
        item["version"] = importlib.metadata.version(name); item["installed"] = True
        module = __import__(name); item["imported"] = True; item["path"] = module.__file__
    except Exception as exc:
        item["error"] = type(exc).__name__ + ": " + str(exc)[:500]
try:
    import numpy as np, pandas as pd
    frame = pd.read_csv(io.StringIO("category,score\\nA,10\\nA,20\\nB,12\\n"))
    result["result"] = {"array_sum": int(np.array([10,20,12], dtype="int64").sum()), "group_totals": {str(k):int(v) for k,v in frame.groupby("category")["score"].sum().items()}, "rows": len(frame)}
except Exception as exc:
    result["error"] = type(exc).__name__ + ": " + str(exc)[:500]
print("CAMPUSLAB_DATA=" + json.dumps(result, ensure_ascii=True))
'''


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--kernel-spec');args=parser.parse_args()
    output=dict(actual=sys.executable,python=platform.python_version(),dependencies={},kernel=dict(started=None,actual=None,python=None,error=''),
        packages={name:dict(installed=None,version=None,imported=None,path=None,error='内核未运行') for name in ('numpy','pandas')},
        run=dict(returncode=None,result=None,stdout='',error='内核未运行',executed_at=None),cleanup=dict(kernel_stopped=None,channels_stopped=None,error='未启动内核'))
    for name in ('jupyter_client','ipykernel'):
        try:output['dependencies'][name]=dict(installed=True,version=importlib.metadata.version(name),error='')
        except importlib.metadata.PackageNotFoundError:output['dependencies'][name]=dict(installed=False,version=None,error='未安装')
    if not args.kernel_spec or not all(x['installed'] for x in output['dependencies'].values()):
        print(json.dumps(output,ensure_ascii=True));return
    from jupyter_client import KernelManager
    from jupyter_client.kernelspec import KernelSpecManager
    manager=None;client=None
    with tempfile.TemporaryDirectory(prefix='campuslab-notebook-') as temporary, ExitStack() as streams:
        root=Path(temporary); kernels=root/'kernels'; folder=kernels/'campuslab-fixed';folder.mkdir(parents=True)
        # Reconstruct the reviewed local kernel instead of passing metadata/env or provisioners from the selected file.
        approved=dict(argv=[sys.executable,'-I','-m','ipykernel_launcher','-f','{connection_file}'],language='python',display_name='CampusLab fixed local kernel')
        (folder/'kernel.json').write_text(json.dumps(approved),encoding='utf-8')
        env={k:v for k,v in os.environ.items() if not k.upper().startswith(('PYTHON','JUPYTER','IPYTHON'))}
        env.update(PYTHONDONTWRITEBYTECODE='1',IPYTHONDIR=str(root/'ipython'),JUPYTER_CONFIG_DIR=str(root/'config'),JUPYTER_DATA_DIR=str(root/'data'))
        try:
            manager=KernelManager(kernel_name='campuslab-fixed',kernel_spec_manager=KernelSpecManager(kernel_dirs=[str(kernels)]),connection_file=str(root/'connection.json'),ip='127.0.0.1')
            manager.start_kernel(cwd=str(root),env=env,stdout=streams.enter_context(open(os.devnull,'w')),stderr=streams.enter_context(open(os.devnull,'w')))
            output['kernel']['started']=True;client=manager.client();client.start_channels();client.wait_for_ready(timeout=30)
            message_id=client.execute(CODE,silent=False,store_history=False,allow_stdin=False,stop_on_error=True)
            output['run']['executed_at']=datetime.now(timezone.utc).isoformat();deadline=time.monotonic()+35;captured=[];observed=None;cell_error=''
            while time.monotonic()<deadline:
                message=client.get_iopub_msg(timeout=max(.1,deadline-time.monotonic()))
                if message.get('parent_header',{}).get('msg_id')!=message_id:continue
                kind=message['header']['msg_type'];content=message['content']
                if kind=='stream':
                    captured.append(content['text'])
                    for line in content['text'].splitlines():
                        if line.startswith('CAMPUSLAB_DATA='):observed=json.loads(line.split('=',1)[1])
                elif kind=='error':cell_error=content.get('ename','cell error')+': '+content.get('evalue','')
                elif kind=='status' and content['execution_state']=='idle':break
            else:raise TimeoutError('固定内核单元超时')
            if observed is None:raise ValueError('固定单元没有完整数据输出')
            output['kernel'].update(actual=observed['actual'],python=observed['python'])
            output['packages']=observed['packages'];error=cell_error or observed['error']
            output['run'].update(returncode=1 if error else 0,result=observed['result'],stdout=''.join(captured)[-12000:],error=error)
        except Exception as exc:
            output['kernel']['error']=type(exc).__name__+': '+str(exc)[:500]
            output['run']['error']=output['kernel']['error']
        finally:
            cleanup=[]
            if client is not None:
                try:client.stop_channels();output['cleanup']['channels_stopped']=True
                except Exception as exc:cleanup.append(type(exc).__name__)
            if manager is not None:
                try:
                    if manager.has_kernel:manager.shutdown_kernel(now=True)
                    output['cleanup']['kernel_stopped']=not manager.has_kernel
                    manager.cleanup_resources()
                except Exception as exc:cleanup.append(type(exc).__name__)
            output['cleanup']['error']='; '.join(cleanup)
    print(json.dumps(output,ensure_ascii=True))


if __name__=='__main__':main()
