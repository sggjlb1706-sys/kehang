"""Recompute protected prototype/evidence SHA values without changing the originals."""
import json
from pathlib import Path
from .catalog_legacy import sha,ROOT


def main():
    index=json.loads((ROOT/'docs/legacy/index.json').read_text(encoding='utf-8'))
    files=dict(index['protected'])
    for p in index['copies']:
        files[p['source']]=p['sha256']
        files[str(ROOT/p['copy'])]=p['sha256']
    catalog=json.loads((ROOT/'docs/legacy/phases-catalog.json').read_text(encoding='utf-8'))
    for p in catalog['entries']:files[p['source']]=p['sha256']
    failed=[p for p,h in files.items() if not Path(p).is_file() or sha(Path(p))!=h]
    print(json.dumps(dict(verified=len(files),failed=failed,originals_modified=False)))
    return bool(failed)


if __name__=='__main__':raise SystemExit(main())
