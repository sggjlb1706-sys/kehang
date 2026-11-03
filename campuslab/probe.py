"""Runs inside the explicitly selected interpreter. Fixed read-only observations only."""
import importlib.metadata
import json
import platform
import subprocess
import sys


def main():
    packages = {}
    for name in ('requests',):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    try:
        run = subprocess.run([sys.executable, '-B', '-I', '-c', 'import requests; print("OK")'],
                             capture_output=True, timeout=20, text=True, encoding='utf-8', errors='replace')
        verification = dict(returncode=run.returncode, stdout=run.stdout[-3000:], error=run.stderr[-3000:])
    except (OSError, subprocess.TimeoutExpired) as exc:
        verification = dict(returncode=None, stdout='', error=type(exc).__name__)
    print(json.dumps(dict(actual=sys.executable, os=platform.system(), python=platform.python_version(),
                          packages=packages, verification=verification), ensure_ascii=True))


if __name__ == '__main__':
    main()
