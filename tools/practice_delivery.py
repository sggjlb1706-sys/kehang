"""Build the authorized new local release and an explicit reviewer copy.

--preflight and --verify-delivery are read-only. --execute never overwrites
destinations, changes an old version, publishes, or uploads either archive.
"""
import argparse
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
from pathlib import Path, PurePosixPath
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from urllib.error import URLError
from urllib.request import Request, urlopen
import zipfile

ROOT=Path(__file__).resolve().parents[1]
DEST=Path('D:/传智杯/versions/kehang-practice-20261110')
LOCAL_ZIP=Path('D:/传智杯/submission/课航_实训闭环_20261110_本机全历史.zip')
REVIEW_ZIP=Path('D:/传智杯/submission/课航_实训闭环_20261110_评审副本.zip')
EXTERNAL=ROOT.parents[1]/'交付/课航实训闭环-20261110'
BASE=Path('D:/传智杯/versions/kehang-20261110')
BASE_HEAD='a7dac52bfacf379dd13f1fe1a2d3120570e05532'
BASE_MANIFEST='328A7800C44BF89D4B835138491B1E9827CEEF8A42E8E9520E3F874A2981E428'
RUNTIME='vendor/python-3.13.17-embed-amd64.zip'
RUNTIME_SHA='9E35319BFFEDAB8B36AD44D8F377CB4F1733BCEC257A0B6D04D94F01486DDB38'
PDF='output/pdf/课航_实训闭环技术文档.pdf'
VIDEO='output/video/课航_实训闭环演示.mp4'
RECEIPT='records/review/practice-delivery-receipt.json'
MANIFEST='SHA256SUMS-delivery.json'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest().upper()


def digest(raw):return hashlib.sha256(raw).hexdigest().upper()


def git(*args,cwd=ROOT):
    return subprocess.check_output(['git','--no-optional-locks','-c','safe.directory='+cwd.as_posix(),*args],cwd=cwd)


def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))


def raw_json(value):return json.dumps(value,ensure_ascii=False,indent=2).encode('utf-8')


def relative(name):
    path=PurePosixPath(name.replace('\\','/'))
    if path.is_absolute() or '..' in path.parts or not path.parts or ':' in str(path):
        raise ValueError('Archive/manifest path is not a relative child: '+name)
    return path.as_posix()


def baseline_protection():
    assert sha(BASE/MANIFEST)==BASE_MANIFEST
    files=read(BASE/MANIFEST)
    assert all(sha(BASE/relative(name))==value.upper() for name,value in files.items())
    assert git('rev-parse','HEAD',cwd=BASE).decode().strip()==BASE_HEAD
    assert not git('status','--porcelain',cwd=BASE).strip()
    return dict(head=BASE_HEAD,manifest_sha256=BASE_MANIFEST,files=len(files),unchanged=True,old_versions_written=False)


def reviewed_product():
    product=read(ROOT/'records/practice/product.json')
    closure=read(ROOT/'records/practice/review-closure.json')
    assert closure['product_head']==product['head'] and closure['blocking_findings']==0
    for name,value in product['files'].items():
        assert sha(ROOT/relative(name))==value.upper(),name
    git('merge-base','--is-ancestor',product['head'],'HEAD')
    return product


def preflight():
    errors=[]
    def check(label,operation):
        try:operation()
        except (AssertionError,OSError,ValueError,KeyError,subprocess.CalledProcessError) as exc:
            errors.append(label+': '+(str(exc) or 'check failed'))
    check('clean source',lambda: require(not git('status','--porcelain').strip(),'Commit source/evidence/materials before delivery'))
    check('baseline ancestor',lambda:git('merge-base','--is-ancestor',BASE_HEAD,'HEAD'))
    check('reviewed product',reviewed_product)
    check('protected baseline',baseline_protection)
    check('official reused runtime',lambda:require(sha(ROOT/RUNTIME)==RUNTIME_SHA,'runtime SHA mismatch'))
    for name in (PDF,VIDEO,'README.md','.env.example','THIRD_PARTY_NOTICES.md'):
        check(name,lambda name=name:require((ROOT/name).is_file(),'required release file missing'))
    for path in (DEST,LOCAL_ZIP,REVIEW_ZIP,EXTERNAL/'delivery-receipt.json'):
        check(str(path),lambda path=path:require(not path.exists(),'existing destination: never overwrite'))
    return dict(read_only=True,ready=not errors,head=git('rev-parse','HEAD').decode().strip(),errors=errors,
                destination=str(DEST),local_archive=str(LOCAL_ZIP),reviewer_archive=str(REVIEW_ZIP))


def require(value,message):
    if not value:raise ValueError(message)


def smoke(root):
    from campuslab.practice import make_practice, submission_template
    from campuslab.rules import task, NEW_COURSES
    with socket.socket() as probe:
        probe.bind(('127.0.0.1',0));port=probe.getsockname()[1]
    checks=[]
    with tempfile.TemporaryDirectory(prefix='kehang-practice-delivery-') as temporary:
        argv=[sys.executable,'-B','-m','campuslab.web','--port',str(port),'--database',str(Path(temporary)/'new-library.sqlite'),
              '--runtime-zip',str(root/RUNTIME)]
        process=subprocess.Popen(argv,cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                                 creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=='win32' else 0)
        base=f'http://127.0.0.1:{port}'
        def request(path,body=None):
            data=raw_json(body) if body is not None else None
            return urlopen(Request(base+path,data=data,headers={'Content-Type':'application/json'} if data else {}),timeout=15)
        try:
            for _ in range(80):
                if process.poll() is not None:raise ValueError('New delivery CLI exited before ready')
                try:
                    with request('/api/config') as response:assert json.load(response)['portable_available']
                    break
                except (URLError,OSError):time.sleep(.1)
            else:raise ValueError('New delivery CLI did not become ready')
            with request('/') as response:assert '课航'.encode() in response.read()
            spec=json.load(request('/api/practice'))['practice'];assert spec==make_practice()
            teacher=json.load(request('/api/practice/publish',{}))
            imported=json.load(request('/api/practice/import',dict(package=teacher['package'])))
            assert imported['practice']==spec
            with request('/api/practice/materials') as response,zipfile.ZipFile(BytesIO(response.read())) as z:
                assert z.testzip() is None and json.loads(z.read('课堂资料包.json'))==teacher['package']
            checks.append('Fixed practice publish/import/materials complete ZIP/CRC')
            good=submission_template(spec);good.update(spec['expected'])
            wrong=json.loads(json.dumps(good));wrong['notebook']['array_sum']=43
            for submission,status in [(None,'missing'),(wrong,'mismatch'),(good,'pass')]:
                assert json.load(request('/api/practice/check',dict(practice=spec,submission=submission)))['status']==status
            checks.append('Missing result retained; constructed incorrect result rejected; correct fixed JSON accepted')
            for scenario in ['python-basics','node-basics','local-qwen','pytorch-cpu','pytorch-gpu','vm-linux',*NEW_COURSES]:
                assert json.load(request('/api/goal?goal='+scenario))==task(scenario)
                with request('/api/tool?goal='+scenario) as response,zipfile.ZipFile(BytesIO(response.read())) as z:
                    assert z.testzip() is None and json.loads(z.read('task.json'))==task(scenario)
                    assert 'runtime/python.exe' in z.namelist()
                    for name in z.namelist():
                        relative(name)
                        if name.startswith('campuslab/'):
                            assert z.read(name)==(root/name).read_bytes(),name
                checks.append(scenario+' snapshot/all downloaded product bytes/runtime/CRC')
            assert not git('status','--porcelain',cwd=root).strip()
        finally:
            process.terminate()
            try:process.communicate(timeout=10)
            except subprocess.TimeoutExpired:process.kill();process.communicate(timeout=5)
    return dict(passed=True,root=str(root),argv=argv,port=port,checks=checks,service_stopped=process.poll() is not None,
                database_scope='new temporary library only; removed after stopping own process',execution_policy_changed=False,
                actual_api_calls=0,actual_dsh_runs=0)


def reviewer_payload(root,names):
    from campuslab.diagnosis import redact_value
    from campuslab.practice import check, make_practice, materials_zip
    selected={}
    fixed={'README.md','.env.example','Start-Web.ps1','THIRD_PARTY_NOTICES.md','DEPENDENCIES.md','requirements.txt','docs/reuse.json',PDF,VIDEO}
    for name in names:
        if name in fixed or name.startswith(('campuslab/','web/','docs/third-party/')) or (name.startswith('docs/实训版') and name.endswith('.md')):
            raw=(root/name).read_bytes()
            # Reviewer documents are explicitly labelled sharing derivatives.
            if name.endswith(('.md','.json')) and not name.startswith(('campuslab/','docs/third-party/')):
                raw=redact_value(raw.decode('utf-8')).encode('utf-8')
            selected[name]=raw
    selected[RUNTIME]=(root/RUNTIME).read_bytes()
    selected['materials/课航固定实训资料.zip']=materials_zip(make_practice())
    result=read(root/'records/practice/lab-run/实训成果.json')
    assert check(make_practice(),result)['passed']
    selected['examples/同机代理实际成果.json']=raw_json(result)
    wrong=json.loads(json.dumps(result));wrong['notebook']['array_sum']=43
    selected['examples/代理构造错误负例.json']=raw_json(wrong)
    excerpts=read(root/'records/practice/prompt-candidate-excerpts.json')
    public=[]
    for group in excerpts:
        messages=[]
        for message in group['messages']:
            if message['role'] not in ('user','assistant') or message.get('channel') not in (None,'final','commentary'):continue
            text=redact_value(message['text'])
            messages.append(dict(role=message['role'],source_line=message['source_line'],timestamp=message.get('timestamp'),
                                 original_text_sha256=message.get('original_text_sha256'),text=text,shared_text_sha256=digest(text.encode())))
        public.append(dict(source=group['source'],messages=messages))
    selected['prompts/可见协作脱敏节选.json']=raw_json(dict(note='真实可见用户/助手文字节选；不是完整原始会话，未认证三条完整链。个人目录、邮箱和敏感值另作脱敏。',sources=public))
    selected['评审启动与来源说明.md']=('''# 课航实训闭环版：评审副本

本ZIP为尚未上传的评审运行/材料副本；不含.git、原始本机设备报告、私人库或密钥。完整真实Git历史只在本人本机全历史包保留，公开/推送仍需本人另行授权。此副本不代替官方提交回执或三条完整Prompt链认证。

需要已有Python≥3.10；服务端仅用标准库。解压后在目录中运行：

```powershell
& '你的已有Python绝对路径\\python.exe' -B -m campuslab.web --port 8794 --database '.\\data\\review.sqlite' --runtime-zip '.\\vendor\\python-3.13.17-embed-amd64.zip'
```

访问 http://127.0.0.1:8794/ 。端口冲突请选择空闲端口，保留已有服务。10分钟启动以已有Python及完整包为前提，不包含从零安装Jupyter/Pandas、模型或所有课程软件。检测包运行时不能充当课程Python。

教师发布实训并下载全部资料；学生在另一实例导入固定课堂资料包，按README主动完成Notebook和SQLite操作并提交JSON。materials内含完整固定资料，examples内正确成果来自代理在同一电脑真实固定练习；错误文件是代理构造负例，不能冒充学生犯错。公开预期数值无法鉴别复制或证明掌握。

Notebook、SQLite各自保留环境任务身份；环境探针、阅读声明、成果数值核验分别记录。真实API/产品诊断、DSH工具授权、来宾/集群和第二设备等以材料中的实际证据状态为准。

docs中的README/Markdown/元数据是脱敏分享衍生件，源文件和原始摘要留本机；product源码及第三方原作者LICENSE/NOTICE保持原字节。prompts只含真实可见文字脱敏节选，不含系统指令、隐藏推理或原始完整会话。Python官方运行时ZIP含原许可证，来源与固定SHA见docs/reuse.json。PDF、MP4为本版实际材料，请按其标明的真实操作/归档回顾/构造负例范围审阅。

SHARING-SHA256.json核对本副本全部负载文件。该清单排除自身；FINAL-STATE.json记录最终源HEAD及已审产品HEAD，不回写到Git历史。仓库远程访问、推送、公开和报名上传均尚未执行。
''').encode('utf-8')
    assert all(not name.startswith(('.git/','records/','private/','data/')) for name in selected)
    return selected


def build_zip(path,prefix,payload):
    with zipfile.ZipFile(path,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name,value in payload.items():
            target=prefix+relative(name)
            if isinstance(value,Path):z.write(value,target)
            else:z.writestr(target,value)
    verify_zip(path,prefix,payload)


def verify_zip(path,prefix,payload):
    with zipfile.ZipFile(path) as z:
        expected={prefix+relative(name) for name in payload}
        assert len(z.namelist())==len(expected) and set(z.namelist())==expected
        assert z.testzip() is None
        for name,value in payload.items():
            with z.open(prefix+relative(name)) as stream:
                observed=hashlib.file_digest(stream,'sha256').hexdigest().upper()
            assert observed==(sha(value) if isinstance(value,Path) else digest(value)),name
    return dict(entries=len(payload),crc=True,all_content_sha256=True,sha256=sha(path),bytes=path.stat().st_size)


def source_copy_check(head,names):
    assert git('rev-parse','HEAD',cwd=DEST).decode().strip()==head
    assert set(git('rev-list','--all').splitlines())==set(git('rev-list','--all',cwd=DEST).splitlines())
    assert git('ls-tree','-r','-z',head)==git('ls-tree','-r','-z',head,cwd=DEST)
    tree={item.split(b'\t',1)[1].decode():item.split(b'\t',1)[0].split()[2].decode()
          for item in git('ls-tree','-r','-z',head,cwd=DEST).split(b'\0') if item}
    index={item.split(b'\t',1)[1].decode():item.split(b'\t',1)[0].split()[1].decode()
           for item in git('ls-files','--stage','-z',cwd=DEST).split(b'\0') if item}
    assert tree==index and set(names)==set(tree)
    for name in names:
        raw=(DEST/name).read_bytes();assert raw==(ROOT/name).read_bytes(),name
        assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==tree[name],name
    git('fsck','--full',cwd=ROOT);git('fsck','--full',cwd=DEST)


def execute():
    ready=preflight();require(ready['ready'],json.dumps(ready['errors'],ensure_ascii=False))
    head=ready['head'];product=reviewed_product();before=baseline_protection()
    names=[relative(n) for n in git('ls-files','-z').decode().split('\0') if n]
    DEST.parent.mkdir(parents=True,exist_ok=True);LOCAL_ZIP.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run(['git','-c','safe.directory='+ROOT.as_posix(),'-c','safe.directory='+ROOT.as_posix()+'/.git',
                    'clone','--no-local','--no-hardlinks',str(ROOT),str(DEST)],check=True)
    source_copy_check(head,names)
    (DEST/'vendor').mkdir(exist_ok=True);shutil.copyfile(ROOT/RUNTIME,DEST/RUNTIME)
    assert sha(DEST/RUNTIME)==RUNTIME_SHA
    smoke_result=json.loads(subprocess.check_output([sys.executable,'-B','-m','tools.practice_delivery','--smoke-only'],cwd=DEST,text=True))
    assert smoke_result['passed'] and smoke_result['service_stopped']
    files={name:sha(DEST/name) for name in names};files[RUNTIME]=RUNTIME_SHA
    (DEST/MANIFEST).write_bytes(raw_json(files))
    (DEST/(MANIFEST+'.sha256')).write_text(sha(DEST/MANIFEST)+'  '+MANIFEST+'\n',encoding='ascii')
    local={p.relative_to(DEST).as_posix():p for p in DEST.rglob('*') if p.is_file()}
    build_zip(LOCAL_ZIP,'课航_实训闭环_本机全历史/',local)
    reviewer=reviewer_payload(DEST,names)
    reviewer['FINAL-STATE.json']=raw_json(dict(head=head,product_head=product['head'],source='本机完整历史保留，评审副本只含明确白名单及标明的脱敏衍生件',published=False,uploaded=False))
    reviewer['SHARING-SHA256.json']=raw_json({name:digest(value) for name,value in reviewer.items()})
    build_zip(REVIEW_ZIP,'课航_实训闭环_评审副本/',reviewer)
    assert baseline_protection()==before
    assert not git('status','--porcelain').strip() and not git('status','--porcelain',cwd=DEST).strip()
    receipt=dict(delivered_at=datetime.now(timezone.utc).isoformat(),head=head,product_head=product['head'],
        branch=git('branch','--show-current').decode().strip(),source=str(ROOT),destination=str(DEST),
        history_commits=len(git('rev-list','--all').splitlines()),full_history_preserved=True,all_worktree_blobs_and_index_verified=True,git_fsck=True,
        tracked_files=len(names),delivery_manifest_files=len(files),manifest_sha256=sha(DEST/MANIFEST),runtime_sha256=RUNTIME_SHA,
        local_archive=dict(path=str(LOCAL_ZIP),**verify_zip(LOCAL_ZIP,'课航_实训闭环_本机全历史/',local)),
        reviewer_archive=dict(path=str(REVIEW_ZIP),**verify_zip(REVIEW_ZIP,'课航_实训闭环_评审副本/',reviewer)),
        reviewer_scope='explicit product/material/legal whitelist; no .git, raw local reports, private libraries or credentials; documentation/Prompt sharing derivatives identified',
        smoke=smoke_result,baseline_protection=before,source_git_clean=True,destination_git_clean=True,
        pdf_sha256=sha(DEST/PDF),video_sha256=sha(DEST/VIDEO),published=False,uploaded=False,official_submission_receipt=False,
        exclusions='Manifests exclude themselves, .git internals, receipts and external independent reports. Local ZIP precedes receipts and includes all .git history. Reviewer SHA excludes itself. No archive includes itself.',
        independent_delivery_check='pending; independent read-only verifier must inspect final bytes separately')
    EXTERNAL.mkdir(parents=True,exist_ok=True)
    raw=raw_json(receipt)
    (EXTERNAL/'delivery-receipt.json').write_bytes(raw)
    (ROOT/RECEIPT).write_bytes(raw);(DEST/RECEIPT).write_bytes(raw)
    return receipt


def verify_delivery():
    receipt=read(EXTERNAL/'delivery-receipt.json');names=[n for n in git('ls-files','-z').decode().split('\0') if n]
    source_copy_check(receipt['head'],names)
    files=read(DEST/MANIFEST);assert sha(DEST/MANIFEST)==receipt['manifest_sha256']
    assert all(sha(DEST/relative(name))==value for name,value in files.items())
    local={p.relative_to(DEST).as_posix():p for p in DEST.rglob('*') if p.is_file() and p.relative_to(DEST).as_posix()!=RECEIPT}
    local_result=verify_zip(LOCAL_ZIP,'课航_实训闭环_本机全历史/',local)
    with zipfile.ZipFile(REVIEW_ZIP) as z:
        prefix='课航_实训闭环_评审副本/'
        reviewer={name[len(prefix):]:z.read(name) for name in z.namelist()}
    manifest=json.loads(reviewer.pop('SHARING-SHA256.json'))
    assert {name:digest(value) for name,value in reviewer.items()}==manifest
    reviewer['SHARING-SHA256.json']=raw_json(manifest)
    review_result=verify_zip(REVIEW_ZIP,'课航_实训闭环_评审副本/',reviewer)
    assert local_result=={k:v for k,v in receipt['local_archive'].items() if k!='path'}
    assert review_result=={k:v for k,v in receipt['reviewer_archive'].items() if k!='path'}
    assert (ROOT/RECEIPT).read_bytes()==(DEST/RECEIPT).read_bytes()==(EXTERNAL/'delivery-receipt.json').read_bytes()
    baseline_protection()
    return dict(read_only=True,verified=True,head=receipt['head'],local_archive=local_result,reviewer_archive=review_result)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    modes=parser.add_mutually_exclusive_group(required=True)
    for name in ('preflight','execute','verify-delivery','smoke-only'):modes.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    result=preflight() if args.preflight else execute() if args.execute else verify_delivery() if args.verify_delivery else smoke(ROOT)
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
