"""Read-only verification of the delivered R1 baseline; never updates its manifest."""
import json
from pathlib import Path
from .catalog_legacy import ROOT, sha


def main():
    record = json.loads((ROOT/'records/node/baseline.json').read_text(encoding='utf-8'))
    source = Path(record['source'])
    failed = [name for name, digest in record['source_files'].items()
              if not (source/name).is_file() or sha(source/name) != digest]
    current = {p.relative_to(source).as_posix() for p in source.rglob('*')
               if p.is_file() and '.git' not in p.relative_to(source).parts}
    added = sorted(current - set(record['source_files']))
    result = dict(verified=len(record['source_files']), failed=failed, added=added,
                  original_R1_bytes_unchanged=not failed and not added)
    print(json.dumps(result))
    return bool(failed or added)


if __name__ == '__main__':
    raise SystemExit(main())
