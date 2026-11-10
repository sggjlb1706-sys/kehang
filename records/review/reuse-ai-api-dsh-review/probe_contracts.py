"""Independent review probes. All keys/Agent excerpts are constructed; no network API call."""
from contextlib import redirect_stdout
from copy import deepcopy
from datetime import datetime,timedelta,timezone
import hashlib
from io import StringIO
import json
from pathlib import Path
import tempfile
import sys
from unittest.mock import patch
import zipfile

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from campuslab import ai_course as ai
from campuslab import dsh_course as dsh
from campuslab.rules import canonical,compare
from tests.test_dsh_course import excerpt

OUT=Path(__file__).resolve().parent
results={'network_api_calls':0,'real_dsh_tasks':0,'constructed_key_used':True,'checks':[]}

# A partial selected Python is a real runtime failure fixture, never installed or registered.
with tempfile.TemporaryDirectory(prefix='ssl-missing-',dir=OUT) as temp:
    folder=Path(temp)
    with zipfile.ZipFile(ROOT/'vendor/python-3.13.17-embed-amd64.zip') as archive:
        for name in archive.namelist():
            if name!='_ssl.pyd':archive.extract(name,folder)
    report=ai.collect(ai.make_task(),str(folder/'python.exe'))
    analysis=ai.analyze(ai.make_task(),report)
    results['missing_ssl_actual_collector']={'fixture':'existing official embed ZIP extracted without _ssl.pyd; no .campuslab-tool-runtime marker, explicit selected target',
        'category':report['facts']['run']['category'],'stdlib':report['facts']['stdlib'],
        'dependency_status':next(c['status'] for c in analysis['checks'] if c['id']=='api:dependency'),
        'python_status':next(c['status'] for c in analysis['checks'] if c['id']=='python'),'passed':analysis['passed']}

value=ai.preview(ai.make_task());value['payload']['messages'][1]['content']+=' CONSTRUCTED_REVIEW_ONLY_KEY'
digest=hashlib.sha256(canonical(value).encode()).hexdigest()[:12]
with tempfile.TemporaryDirectory(prefix='preview-',dir=OUT) as temp:
    path=Path(temp)/'preview.json';path.write_text(json.dumps(value),encoding='utf-8')
    with patch('campuslab.ai_course.input',return_value='SEND '+digest),patch('campuslab.ai_course.getpass.getpass',return_value='CONSTRUCTED_REVIEW_ONLY_KEY'),patch('campuslab.ai_course.subprocess.run') as run,redirect_stdout(StringIO()):
        try:ai.collect(ai.make_task(),r'D:\ANACONDA\python.exe',path,True)
        except ValueError:results['checks'].append('Known key in edited preview rejected before probe; no report returned')
        else:raise AssertionError('Known key accepted')
        assert not run.called

with tempfile.TemporaryDirectory(prefix='dsh-',dir=OUT) as temp:
    root=Path(temp);exe=root/'DeepSeek Harness.exe';exe.write_bytes(b'CONSTRUCTED-FAKE-NOT-EXECUTED')
    work=root/'practice';spec=dsh.make_task();dsh.prepare_workspace(spec,str(work));(work/'summary.json').write_text('{"count":3,"sum":42}')
    with patch('campuslab.dsh_course._desktop_metadata',return_value=dict(product='DeepSeek Harness',version=dsh.SUPPORTED_VERSION,error='')):
        baseline=dsh.collect(spec,str(exe),workspace=str(work),provider='deepseek',model='deepseek-flash')
        value=excerpt(baseline)
        a=dsh.collect(spec,str(exe),workspace=str(work),provider='deepseek',model='deepseek-flash',evidence=value)
        b=deepcopy(a);b['collected_at']=(datetime.now(timezone.utc)+timedelta(seconds=1)).isoformat()
        try:compare(spec,a,b)
        except ValueError:results['checks'].append('Same successful constructed Agent task cannot be reused as a later retest')
        else:raise AssertionError('Replayed Agent task accepted')

(OUT/'probe-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(results,ensure_ascii=False))
