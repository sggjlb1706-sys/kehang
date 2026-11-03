"""Verify local source prefixes and visible messages, including app-compressed originals."""
import hashlib
import json
from pathlib import Path
from .catalog_legacy import ROOT,sha


def main():
    source_map={}
    maps=list((ROOT/'private').glob('*source-map.json'))
    maps.append(Path('D:/传智杯/versions/goal-onboarding-20261101/private/exports-20261101-source-map.json'))
    for p in maps:
        if p.is_file():source_map.update(json.loads(p.read_text(encoding='utf-8')))
    count=0;authorization=False;compressed=[]
    indexes=list((ROOT/'docs/prompts').glob('*/index.json'))+[ROOT/'docs/legacy/prompt-exports-20261101/index.json']
    for index in indexes:
        for row in json.loads(index.read_text(encoding='utf-8')):
            export=index.parent/row['export']
            assert sha(export)==row['export_sha256']
            assert sha(export.with_suffix('.md'))==row['readable_sha256']
            source=Path(source_map[row['session_id']])
            if source.is_file():raw=source.read_bytes()
            else:
                import zstandard  # Existing developer utility only; never installed by this tool.
                with source.with_suffix(source.suffix+'.zst').open('rb') as f,zstandard.ZstdDecompressor().stream_reader(f) as reader:raw=reader.read()
                compressed.append(row['session_id'])
            prefix=raw[:row['source_prefix_bytes']]
            assert hashlib.sha256(prefix).hexdigest().upper()==row['source_prefix_sha256']
            rawlines=prefix.splitlines()
            for m in json.loads(export.read_text(encoding='utf-8'))['messages']:
                item=json.loads(rawlines[m['source_line']-1])['payload']
                text='\n'.join(b.get('text','') for b in item.get('content',[]) if b.get('type') in ('input_text','output_text'))
                assert hashlib.sha256(text.encode()).hexdigest().upper()==m['original_text_sha256']
                if m['role']=='user' and text.strip()=='2':authorization=True
            count+=1
    assert authorization
    result=dict(source_prefixes_and_exports_verified=count,losslessly_compressed_originals_verified=sorted(set(compressed)),
                actual_user_selection_2_preserved=authorization,originals_modified=False,official_three_complete_chains_certified=False)
    print(json.dumps(result))


if __name__=='__main__':main()
