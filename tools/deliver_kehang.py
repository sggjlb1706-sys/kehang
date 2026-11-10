"""Deliver the authorized new private release; never overwrite any existing destination."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile
from .catalog_legacy import sha

ROOT=Path(__file__).resolve().parents[1]
DEST=Path('D:/传智杯/versions/kehang-20261110')
ARCHIVE=Path('D:/传智杯/submission/课航_课程学习与实训助手_20261110_待补本人视频.zip')
RECEIPT='records/review/kehang-delivery-receipt.json'
BASE=Path('D:/传智杯/versions/competition-courses-20261108')
BASE_HEAD='e0aca9ca04f350c5db0e3d6f197307260eee6276'

def git(*args,cwd=ROOT):
    return subprocess.check_output(['git','-c','safe.directory='+cwd.as_posix(),*args],cwd=cwd)
def protection():
    manifest=BASE/'SHA256SUMS-delivery.json'
    assert sha(manifest)=='93DC407BE48FFB4D2E8E79A852303B61AE4F578435DB3C06C81CF9BF900BAAC6'
    values=json.loads(manifest.read_text(encoding='utf-8'))
    assert all(sha(BASE/name)==value for name,value in values.items())
    assert git('rev-parse','HEAD',cwd=BASE).decode().strip()==BASE_HEAD
    oldzip=Path('D:/传智杯/submission/课程能力版_20261108_待补本人视频.zip')
    assert sha(oldzip)=='A8A62225EB2BC235FD7C259600F946F537FD6447AEA08C35A594D4BF752C23C6'
    # Hash only the previously protected files. Do not open new private/ignored runtime data.
    node=json.loads((ROOT/'records/courses/baseline.json').read_text(encoding='utf-8'))
    r1=json.loads((ROOT/'records/node/baseline.json').read_text(encoding='utf-8'))
    legacy=json.loads((ROOT/'docs/legacy/index.json').read_text(encoding='utf-8'))
    protected=dict(legacy['protected'])
    for item in legacy['copies']:
        protected[item['source']]=item['sha256'];protected[str(ROOT/item['copy'])]=item['sha256']
    for item in json.loads((ROOT/'docs/legacy/phases-catalog.json').read_text(encoding='utf-8'))['entries']:protected[item['source']]=item['sha256']
    groups=[('Node',{str(Path(node['baseline'])/n):h for n,h in node['all_non_git_files'].items()}),
            ('R1',{str(Path(r1['source'])/n):h for n,h in r1['source_files'].items()}),('legacy',protected)]
    original=[]
    for label,known in groups:
        assert all(sha(Path(n))==h for n,h in known.items()),label
        original.append(dict(scope=label,previously_protected_files=len(known),unchanged=True))
    return dict(course_manifest_files=len(values),old_zip_sha256=sha(oldzip),other_protected=original,private_course_database='excluded; not read/copied',old_versions_written=False)

def brand_baseline_protection():
    root=Path('D:/传智杯/versions/competition-reuse-ai-20261109')
    manifest=root/'SHA256SUMS-delivery.json'
    assert sha(manifest)=='41212ECC93DBC48C1CB5535AA34695E609003BCB15DD9A18D7AEE2CB83E22727'
    values=json.loads(manifest.read_text(encoding='utf-8'))
    assert all(sha(root/n)==h for n,h in values.items())
    assert git('rev-parse','HEAD',cwd=root).decode().strip()=='fc14fc752a83709df496b386e4ce950b01996afe'
    archive=Path('D:/传智杯/submission/开源AI_Agent课程版_20261109_待补本人视频.zip')
    assert sha(archive)=='4C929E654F99E36A768A5CBFF7332F487334CEF503381B32E800B7AB3E3208EB'
    return dict(files=len(values),unchanged=True,head='fc14fc752a83709df496b386e4ce950b01996afe',archive_sha256=sha(archive))

def main():
    if sys.argv[1:]!=['--execute']:raise ValueError('Explicit --execute required')
    if DEST.exists() or ARCHIVE.exists():raise ValueError('New destination exists; do not overwrite')
    if git('status','--porcelain').strip():raise ValueError('Commit final source, evidence and material before delivery')
    head=git('rev-parse','HEAD').decode().strip();branch=git('branch','--show-current').decode().strip()
    frozen=json.loads((ROOT/'records/review/kehang-candidate.json').read_text(encoding='utf-8'))
    closure=json.loads((ROOT/'records/review/kehang-review-closure.json').read_text(encoding='utf-8'))
    assert closure['product_head']==frozen['product_head'] and closure['blocking_findings']==0
    assert all(sha(ROOT/n)==h for n,h in frozen['source_sha256'].items())
    before=protection();brand_before=brand_baseline_protection()
    subprocess.run(['git','-c','safe.directory='+ROOT.as_posix(),'merge-base','--is-ancestor','fc14fc752a83709df496b386e4ce950b01996afe',head],cwd=ROOT,check=True)
    DEST.parent.mkdir(parents=True,exist_ok=True);ARCHIVE.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run(['git','-c','safe.directory='+ROOT.as_posix(),'-c','safe.directory='+ROOT.as_posix()+'/.git','clone','--no-local','--no-hardlinks',str(ROOT),str(DEST)],check=True)
    assert git('rev-parse','HEAD',cwd=DEST).decode().strip()==head
    history=git('rev-list','--all').decode().splitlines()
    assert set(history)==set(git('rev-list','--all',cwd=DEST).decode().splitlines())
    git('fsck','--full',cwd=DEST)
    names=[n for n in git('ls-files','-z').decode().split('\0') if n]
    tree={entry.split(b'\t',1)[1].decode():entry.split(b'\t',1)[0].split()[2].decode()
          for entry in git('ls-tree','-r','-z',head,cwd=DEST).split(b'\0') if entry}
    index={entry.split(b'\t',1)[1].decode():entry.split(b'\t',1)[0].split()[1].decode()
           for entry in git('ls-files','--stage','-z',cwd=DEST).split(b'\0') if entry}
    assert tree==index
    for name in names:
        data=(DEST/name).read_bytes()
        assert (ROOT/name).read_bytes()==data,name
        assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==tree[name],name
    (DEST/'vendor').mkdir(exist_ok=True)
    runtime=ROOT/'vendor/python-3.13.17-embed-amd64.zip';assert sha(runtime)=='9E35319BFFEDAB8B36AD44D8F377CB4F1733BCEC257A0B6D04D94F01486DDB38'
    shutil.copyfile(runtime,DEST/'vendor'/runtime.name);assert sha(DEST/'vendor'/runtime.name)==sha(runtime)
    smoke=json.loads(subprocess.check_output([sys.executable,'-B','-m','tools.kehang_smoke'],cwd=DEST,text=True))
    assert smoke['passed'] and smoke['service_stopped'] and not smoke['execution_policy_changed']
    files={n:sha(DEST/n) for n in names};files['vendor/'+runtime.name]=sha(runtime)
    manifest=DEST/'SHA256SUMS-delivery.json';manifest.write_text(json.dumps(files,ensure_ascii=False,indent=2),encoding='utf-8')
    (DEST/'SHA256SUMS-delivery.json.sha256').write_text(sha(manifest)+'  SHA256SUMS-delivery.json\n',encoding='ascii')
    archive_files=[p for p in DEST.rglob('*') if p.is_file()]
    prefix='课航_课程学习与实训助手/'
    with zipfile.ZipFile(ARCHIVE,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in archive_files:z.write(p,prefix+p.relative_to(DEST).as_posix())
    with zipfile.ZipFile(ARCHIVE) as z:
        assert z.testzip() is None
        for p in archive_files:assert hashlib.sha256(z.read(prefix+p.relative_to(DEST).as_posix())).hexdigest().upper()==sha(p)
    assert not git('status','--porcelain',cwd=DEST).strip()
    after=protection();assert before==after;assert brand_before==brand_baseline_protection()
    result=dict(delivered_at=datetime.now(timezone.utc).isoformat(),source=str(ROOT),destination=str(DEST),head=head,branch=branch,product_head=frozen['product_head'],
        reviewed_product_and_adopted_source_files=len(frozen['source_sha256']),tracked_files=len(names),delivery_files=len(files),manifest_sha256=sha(manifest),
        history_commits=len(history),full_history_preserved=True,git_index_and_all_blobs_verified=True,git_fsck=True,
        runtime_sha256=sha(runtime),archive=str(ARCHIVE),archive_sha256=sha(ARCHIVE),archive_entries=len(archive_files),archive_crc_verified=True,all_archive_content_sha_verified=True,
        smoke=smoke,old_version_protection=after,brand_baseline_protection=brand_before,source_git_clean=True,destination_git_clean=True,
        manifest_excludes=['.git internals (whole history is in ZIP and separately checked)','SHA256SUMS-delivery.json and its hash','post-build receipt and external independent delivery report','ignored private/env/course database/extracted test runtimes/test ZIPs'],
        zip_scope='Snapshot before post-build receipt; full history included. ZIP and receipt never include themselves.',private_local_review_only=True,
        published=False,uploaded=False,official_submission_receipt=False,formal_mp4_missing=True,three_prompt_chains_certified=False)
    raw=json.dumps(result,ensure_ascii=False,indent=2)
    (ROOT/RECEIPT).write_text(raw,encoding='utf-8');(DEST/RECEIPT).write_text(raw,encoding='utf-8')
    print(raw)
if __name__=='__main__':main()
