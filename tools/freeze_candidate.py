"""Freeze the current review inputs. Excludes this manifest's own mutable bytes."""
from datetime import datetime,timezone
import argparse
import json
from pathlib import Path
import subprocess
from .catalog_legacy import ROOT,sha


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',default='candidate.json')
    args=parser.parse_args()
    if Path(args.output).name!=args.output:
        raise ValueError('Output must be a manifest filename')
    folder=ROOT/'records/review';folder.mkdir(exist_ok=True)
    target=folder/args.output
    if target.exists():raise ValueError('Do not overwrite a prior review manifest')
    names=subprocess.check_output(['git','ls-files','-z','--cached','--others','--exclude-standard'],cwd=ROOT).decode('utf-8').split('\0')
    files={n:sha(ROOT/n) for n in sorted(set(names)) if n and (ROOT/n).is_file() and n!=target.relative_to(ROOT).as_posix()}
    matching=[]
    for p in sorted((ROOT/'records/browser').glob('*/results.json')):
        data=json.loads(p.read_text(encoding='utf-8'))
        if data.get('status')=='passed' and all(sha(ROOT/n)==h for n,h in data['source_sha256'].items()):matching.append(p)
    if not matching:raise ValueError('No passing browser record matches current product source')
    result=dict(frozen_at=datetime.now(timezone.utc).isoformat(),parent_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                source_and_evidence_sha256=files,browser_record=matching[-1].relative_to(ROOT).as_posix(),browser_source_matches=True,official_compliance='not certified',independent_review='pending')
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(files=len(files),browser_source_matches=True)))


if __name__=='__main__':main()
