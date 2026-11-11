"""Read-only baseline and history preflight. Does not read ignored private data or keys."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BASE = Path(r'D:\传智杯\versions\kehang-20261110')
HEAD = 'a7dac52bfacf379dd13f1fe1a2d3120570e05532'
MANIFEST = '328A7800C44BF89D4B835138491B1E9827CEEF8A42E8E9520E3F874A2981E428'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def git(path, *args):
    return subprocess.check_output(['git', '--no-optional-locks', '-c', 'safe.directory='+str(path), '-C', str(path), *args])


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=Path, default=ROOT/'records/practice')
    output = parser.parse_args().output_dir
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = BASE/'SHA256SUMS-delivery.json'
    assert sha(manifest_path) == MANIFEST
    manifest = json.loads(manifest_path.read_text(encoding='utf-8-sig'))
    failures = [name for name, digest in manifest.items() if sha(BASE/name) != digest.upper()]
    assert not failures, failures
    tracked = git(BASE, 'ls-files', '-z').decode('utf-8').split('\x00')[:-1]
    assert set(manifest) == set(tracked) | {'vendor/python-3.13.17-embed-amd64.zip'}
    inherited = set(git(BASE, 'rev-list', '--all').decode().split())
    source_history = set(git(ROOT, 'rev-list', '--all').decode().split())
    assert inherited <= source_history
    assert git(BASE, 'rev-parse', 'HEAD').decode().strip() == HEAD
    assert git(BASE, 'status', '--porcelain').decode() == ''
    assert git(BASE, 'branch', '--show-current').decode().strip() == 'codex/kehang-brand-20261110'
    assert git(ROOT, 'branch', '--show-current').decode().strip() == 'codex/kehang-practice-20261110'
    subprocess.run(['git', '--no-optional-locks', '-c', 'safe.directory='+str(BASE), '-C', str(BASE), 'fsck', '--full'], check=True, capture_output=True)
    # Compare inherited HEAD blobs, not the actively edited new working files.
    assert git(BASE, 'rev-parse', 'HEAD^{tree}') == git(ROOT, 'rev-parse', HEAD+'^{tree}')
    receipt = json.loads((BASE/'records/review/kehang-delivery-receipt.json').read_text(encoding='utf-8-sig'))
    assert receipt['head'] == HEAD and receipt['manifest_sha256'] == MANIFEST
    record = dict(checked_at_utc=datetime.now(timezone.utc).isoformat(), baseline=str(BASE), new_working_copy=str(ROOT),
                  head=HEAD, branch='codex/kehang-brand-20261110', new_branch='codex/kehang-practice-20261110',
                  manifest_sha256=MANIFEST, manifest_files=len(manifest), tracked_files=len(tracked),
                  all_manifest_sha256_match=True, baseline_git_clean=True, git_fsck=True,
                  inherited_commits=len(inherited), full_history_preserved=True, inherited_tree_equal=True,
                  runtime_sha256=sha(BASE/'vendor/python-3.13.17-embed-amd64.zip'),
                  ignored_private_data_read=False, baseline_files_written=False,
                  scope='Current baseline owning files and exact manifest only; new copy may be under active implementation.')
    (output/'baseline.json').write_text(json.dumps(record, ensure_ascii=False, indent=2)+'\n',encoding='utf-8')

    # Static all-reachable-history scan: locations and categories only, never matching secret strings.
    # This is a publication preflight, not a guarantee that secrets cannot be present.
    objects = git(ROOT, 'rev-list', '--objects', '--all').decode('utf-8').splitlines()
    names = {}
    for line in objects:
        oid, _, name = line.partition(' ')
        if name:
            names.setdefault(oid, name)
    expressions = {
        'credential-shaped-token': re.compile(rb'\b(?:sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|AKIA[A-Z0-9]{16})\b'),
        'private-key-material': re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
        'personal-user-path': re.compile(rb'(?i)[A-Z]:[\\/]+Users[\\/]+DELL\b'),
        'email-address': re.compile(rb'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'),
        'device-identity-field': re.compile(rb'(?i)"(?:uuid|gpu_uuid|vm_id|computer_name|hostname)"\s*:'),
    }
    hits = {key: [] for key in expressions}
    process = subprocess.Popen(['git','-C',str(ROOT),'cat-file','--batch'], stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    scanned = 0
    try:
        for oid, name in names.items():
            process.stdin.write((oid+'\n').encode());process.stdin.flush()
            header = process.stdout.readline().decode().split()
            if len(header)!=3:
                raise ValueError('Invalid object batch response')
            size=int(header[2]); content=process.stdout.read(size); assert process.stdout.read(1)==b'\n'
            if header[1]!='blob':continue
            scanned+=1
            if b'\x00' in content[:8192]:continue
            for category, expression in expressions.items():
                count=sum(1 for _ in expression.finditer(content))
                if count:hits[category].append(dict(blob=oid,path=name,occurrences=count))
    finally:
        process.stdin.close();process.wait(timeout=15)
    dangerous_paths = sorted({name for name in names.values() if Path(name).name.casefold() in ('.env','id_rsa','id_ed25519') or name.startswith('private/')})
    scan=dict(checked_at_utc=datetime.now(timezone.utc).isoformat(), anchor_head=git(ROOT,'rev-parse','HEAD').decode().strip(),
              reachable_commits=len(source_history), unique_blobs_scanned=scanned, matching_values_output=False,
              dangerous_paths=dangerous_paths, patterns={key:len(value) for key,value in hits.items()},
              hits=hits, conclusion='Local review only. Personal paths/device evidence are present in complete history; do not publicly push this history without explicit review and authorization.',
              limitations='Pattern-based static scan cannot prove absence of every secret. Example tokens, upstream authors and synthetic identities need classification. Ignored .env/private/course databases were not opened.')
    (output/'history-publication-preflight.json').write_text(json.dumps(scan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(baseline=record,history_scan_summary={k:scan[k] for k in ('anchor_head','reachable_commits','unique_blobs_scanned','dangerous_paths','patterns')}),ensure_ascii=False,indent=2))


if __name__=='__main__':main()
