"""Fixed isolated API learner probe. Input may hold a transient key; never echo it."""
import json
from pathlib import Path
import platform
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def main():
    args=json.loads(sys.stdin.read())
    result=dict(actual=sys.executable,os=platform.system(),python=platform.python_version(),stdlib=False,
        run=dict(attempted=False,category='dependency_missing',http_status=None,model=None,role=None,finish_reason=None,content='',latency_ms=None))
    try:
        import ssl
        import urllib.request
        from campuslab.ai_course import call_api, make_task
    except (ImportError,OSError):
        print(json.dumps(result,ensure_ascii=True));return
    result.update(stdlib=True,run=call_api(make_task(),args['request'],args['key'],args['consent']))
    print(json.dumps(result,ensure_ascii=True))


if __name__=='__main__': main()
