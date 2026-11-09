"""Create one new local release and private review ZIP without changing older versions."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
DEST=Path('D:/传智杯/versions/competition-courses-20261108')
ARCHIVE=Path('D:/传智杯/submission/课程能力版_20261108_待补本人视频.zip')
RECEIPT='records/review/courses-delivery-receipt.json'


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest().upper()


def command(args,cwd=ROOT):
    return subprocess.check_output(args,cwd=cwd,text=True,encoding='utf-8').strip()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--execute',action='store_true');args=parser.parse_args()
    if not args.execute:raise ValueError('Explicit --execute required for the new delivery')
    if DEST.exists() or ARCHIVE.exists():raise ValueError('New destination already exists; do not overwrite')
    if command(['git','status','--porcelain']):raise ValueError('Commit all final tracked and review files before delivery')
    for module in ('tools.course_baseline','tools.verify_baseline','tools.verify_legacy'):
        subprocess.run([sys.executable,'-B','-m',module],cwd=ROOT,check=True)
    head=command(['git','rev-parse','HEAD'])
    subprocess.run(['git','merge-base','--is-ancestor','42d86482fa1540b35fcdda6bbdf15d888f6b8cd1',head],cwd=ROOT,check=True)
    DEST.parent.mkdir(parents=True,exist_ok=True);ARCHIVE.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run(['git','-c','safe.directory='+ROOT.as_posix(),'clone','--no-local','--no-hardlinks',str(ROOT),str(DEST)],check=True)
    git=['git','-c','safe.directory='+DEST.as_posix(),'-C',str(DEST)]
    if command(git+['rev-parse','HEAD'])!=head:raise ValueError('Copied HEAD mismatch')
    names=command(['git','ls-files','-z']).split('\0')
    for name in names:
        if name and (ROOT/name).read_bytes()!=(DEST/name).read_bytes():raise ValueError('Tracked bytes mismatch: '+name)
    (DEST/'vendor').mkdir(exist_ok=True)
    runtime=ROOT/'vendor/python-3.13.17-embed-amd64.zip'
    shutil.copyfile(runtime,DEST/'vendor'/runtime.name)
    if sha(runtime)!=sha(DEST/'vendor'/runtime.name):raise ValueError('Runtime mismatch')
    smoke=json.loads(command([sys.executable,'-B','-m','tools.delivery_smoke'],cwd=DEST))
    if not smoke['passed'] or not smoke['service_stopped']:raise ValueError('Copied service smoke failed')
    files={p.relative_to(DEST).as_posix():sha(p) for p in DEST.rglob('*') if p.is_file() and '.git' not in p.relative_to(DEST).parts and p.relative_to(DEST).as_posix() not in ('SHA256SUMS-delivery.json','SHA256SUMS-delivery.json.sha256',RECEIPT)}
    manifest=DEST/'SHA256SUMS-delivery.json';manifest.write_text(json.dumps(files,ensure_ascii=False,indent=2),encoding='utf-8')
    (DEST/'SHA256SUMS-delivery.json.sha256').write_text(sha(manifest)+'  SHA256SUMS-delivery.json\n',encoding='ascii')
    # Include complete local Git history. No private maps, database, .env or duplicate test runtimes were cloned.
    archive_files=[p for p in DEST.rglob('*') if p.is_file()]
    with zipfile.ZipFile(ARCHIVE,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for p in archive_files:archive.write(p,'AI实验环境管家_课程能力版/'+p.relative_to(DEST).as_posix())
    with zipfile.ZipFile(ARCHIVE) as archive:
        if archive.testzip() is not None:raise ValueError('Archive CRC failure')
        for name,digest in files.items():
            if hashlib.sha256(archive.read('AI实验环境管家_课程能力版/'+name)).hexdigest().upper()!=digest:raise ValueError('ZIP content mismatch: '+name)
    if command(git+['status','--porcelain']):raise ValueError('Copied Git worktree dirty')
    for module in ('tools.course_baseline','tools.verify_baseline','tools.verify_legacy'):
        subprocess.run([sys.executable,'-B','-m',module],cwd=ROOT,check=True)
    receipt=dict(delivered_at=datetime.now(timezone.utc).isoformat(),source=str(ROOT),destination=str(DEST),head=head,
        branch=command(git+['branch','--show-current']),tracked_files_verified=len([n for n in names if n]),delivery_files=len(files),manifest_sha256=sha(manifest),
        archive=str(ARCHIVE),archive_sha256=sha(ARCHIVE),archive_entries=len(archive_files),archive_crc_verified=True,archive_content_sha_verified=True,
        full_git_history_preserved=True,baseline_ancestor=True,smoke=smoke,old_versions_written=False,published=False,uploaded=False,
        official_eligibility_certified=False,whole_competition_complete=False,private_local_review_package=True,
        omitted='private maps, .env, local course database, duplicate extracted tool runtimes and downloaded test ZIPs; formal MP4 missing')
    raw=json.dumps(receipt,ensure_ascii=False,indent=2)
    (ROOT/RECEIPT).write_text(raw,encoding='utf-8');(DEST/RECEIPT).write_text(raw,encoding='utf-8')
    print(raw)


if __name__=='__main__':main()
