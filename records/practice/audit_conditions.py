"""Minimal static conditions, official public rules and visible dialogue pointers."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
from urllib.request import urlopen

from campuslab.dsh_course import analyze, collect, make_task
from campuslab.rules import compare

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'records/practice'


def save(name,value):
    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def main():
    spec=make_task(route='desktop')
    target=r'D:\deep seekharness\DeepSeek Harness.exe'
    before=collect(spec,target);after=collect(spec,target)
    save('dsh-installed-fixed-task.json',spec);save('dsh-installed-fixed-A.json',before);save('dsh-installed-fixed-B.json',after)
    comparison=compare(spec,before,after);save('dsh-installed-fixed-comparison.json',comparison)
    conditions=dict(checked_at_utc=datetime.now(timezone.utc).isoformat(),
        dsh=dict(target=target,kind='Static installed PE resource/hash only; application not launched',
                 software=before['facts']['installation'],comparison_outcome=comparison['outcome'],
                 checks=[dict(id=c['id'],status=c['status']) for c in analyze(spec,before)['checks']],
                 runtime_launched=False,model_request=False,workspace_selected=False,
                 current_external_gap='本人在DSH明确选择合法模型、启动和固定文件读写工具授权；实际调用及产物仍未取得。'),
        libraries={m:(importlib.util.find_spec(m).origin if importlib.util.find_spec(m) else None) for m in ['playwright','reportlab','fitz']},
        executables={name:shutil.which(name) for name in ['ffmpeg','ffprobe','pdftoppm','pdftotext']},
        ignored_credentials_or_sessions_read=False,installed_software_modified=False)
    ffmpeg=ROOT.parent/'m4-post-submit-20261031/media-tools/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'
    conditions['known_ffmpeg']=dict(path=str(ffmpeg),exists=ffmpeg.is_file())
    if ffmpeg.is_file():
        result=subprocess.run([str(ffmpeg),'-version'],capture_output=True,text=True,encoding='utf-8',timeout=15)
        conditions['known_ffmpeg'].update(returncode=result.returncode,version=result.stdout.splitlines()[0],sha256=hashlib.sha256(ffmpeg.read_bytes()).hexdigest().upper())
    save('available-conditions.json',conditions)
    url='https://gateway.boxuegu.com/portal-marketing/competition/track/detail?id=10039&includeDetail=true'
    official=dict(checked_at_utc=datetime.now(timezone.utc).isoformat(),page_url='https://www.boxuegu.com/matchTrack/detail/?id=10039',public_api_url=url,method='GET public rules; no credentials')
    try:
        with urlopen(url,timeout=25) as response:
            raw=response.read(2000000);official['status']=response.status
        assert json.loads(raw)['data']['id']==10039
        (OUT/'official-track-current.json').write_bytes(raw)
        official.update(success=True,sha256=hashlib.sha256(raw).hexdigest().upper(),bytes=len(raw))
    except Exception as exc:
        official.update(success=False,error_type=type(exc).__name__,error=str(exc)[:300],
                        fallback='records/competition/official-track-detail.json, actually fetched 2026-11-08; current prompt and user supplied correct track screenshot remain authoritative user scope')
    save('official-current-fetch.json',official)
    # Exactly the two visible task-related messages requested by the new prompt.
    source=Path(r'C:\Users\DELL\.codex\sessions\2026\11\09\rollout-2026-11-09T12-17-27-01a1be86-7c96-7200-860a-ff272f5c3bb1.jsonl')
    from tools.export_prompt_history import redact
    selected=[]
    if source.is_file():
        with source.open(encoding='utf-8') as rows:
            for number,line in enumerate(rows,1):
                if number not in (1907,2009):continue
                row=json.loads(line);item=row.get('payload',{})
                assert row.get('type')=='response_item' and item.get('type')=='message'
                assert item.get('role') in ('user','assistant') and item.get('channel') in (None,'commentary','final')
                text='\n'.join(x.get('text','') for x in item.get('content',[]) if x.get('type') in ('input_text','output_text'))
                selected.append(dict(source_line=number,timestamp=row.get('timestamp'),role=item['role'],text=redact(text),original_text_sha256=hashlib.sha256(text.encode()).hexdigest().upper()))
    save('prior-visible-next-round.json',dict(session_id='01a1be86-7c96-7200-860a-ff272f5c3bb1',messages=selected,scope='Only two explicitly located visible user/assistant messages; no hidden reasoning, tool/system/developer content or raw original session exported.'))
    print(json.dumps(dict(dsh_metadata=conditions['dsh']['software'],ffmpeg=conditions['known_ffmpeg'],official=official,selected_visible_messages=len(selected)),ensure_ascii=False,indent=2))


if __name__=='__main__':main()
