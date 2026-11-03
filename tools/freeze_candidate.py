"""Freeze the current review inputs. Excludes this manifest's own mutable bytes."""
from datetime import datetime,timezone
import json
from pathlib import Path
import subprocess
from .catalog_legacy import ROOT,sha


def main():
    folder=ROOT/'records/review';folder.mkdir(exist_ok=True)
    names=subprocess.check_output(['git','ls-files','-z','--cached','--others','--exclude-standard'],cwd=ROOT).decode('utf-8').split('\0')
    files={n:sha(ROOT/n) for n in sorted(set(names)) if n and (ROOT/n).is_file() and n!='records/review/candidate.json'}
    browser=json.loads((ROOT/'records/browser/20261103T012753583646Z/results.json').read_text(encoding='utf-8'))
    assert all(sha(ROOT/n)==h for n,h in browser['source_sha256'].items())
    result=dict(frozen_at=datetime.now(timezone.utc).isoformat(),parent_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                source_and_evidence_sha256=files,browser_source_matches=True,official_compliance='not certified',independent_review='pending')
    (folder/'candidate.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(files=len(files),browser_source_matches=True)))


if __name__=='__main__':main()
