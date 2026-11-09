"""Fixed isolated API learner probe. Input may hold a transient key; never echo it."""
import json
from pathlib import Path
import platform
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from campuslab.ai_course import call_api, make_task


def main():
    args=json.loads(sys.stdin.read())
    # Only these standard-library modules are required in the selected interpreter.
    import ssl
    import urllib.request
    run=call_api(make_task(),args['request'],args['key'],args['consent'])
    print(json.dumps(dict(actual=sys.executable,os=platform.system(),python=platform.python_version(),stdlib=True,run=run),ensure_ascii=True))


if __name__=='__main__': main()
