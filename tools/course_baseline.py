"""Read-only original-byte receipt; never rewrite the source delivery."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = Path('D:/传智杯/versions/competition-r1-node-20261108')
OUT = ROOT/'records/courses'


def hashes(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest().upper()
            for p in root.rglob('*') if p.is_file() and '.git' not in p.relative_to(root).parts}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    receipt = OUT/'baseline.json'
    if receipt.exists():
        saved = json.loads(receipt.read_text(encoding='utf-8'))
        current = hashes(BASE)
        if current != saved['all_non_git_files']:
            raise ValueError('Original baseline bytes changed')
        print(json.dumps(dict(original_files_verified=len(current), unchanged=True)))
        return
    manifest = json.loads((BASE/'SHA256SUMS-delivery.json').read_text(encoding='utf-8'))
    current = hashes(BASE)
    assert all(current.get(k) == v for k, v in manifest.items())
    git = ['git', '-c', 'safe.directory='+BASE.as_posix(), '-C', str(BASE)]
    assert not subprocess.check_output(git+['status','--porcelain'])
    head = subprocess.check_output(git+['rev-parse','HEAD'], text=True).strip()
    assert head == '42d86482fa1540b35fcdda6bbdf15d888f6b8cd1'
    receipt.write_text(json.dumps(dict(checked_at=datetime.now(timezone.utc).isoformat(), baseline=str(BASE),
        head=head, delivery_entries=len(manifest), all_non_git_files=current,
        source_clean=True, originals_written=False), ensure_ascii=False, indent=2), encoding='utf-8')
    (ROOT/'vendor').mkdir(exist_ok=True)
    runtime=BASE/'vendor/python-3.13.17-embed-amd64.zip'
    if runtime.is_file():
        shutil.copyfile(runtime, ROOT/'vendor'/runtime.name)
    print(json.dumps(dict(delivery_verified=len(manifest), protected_files=len(current), head=head)))


if __name__ == '__main__':
    main()
