"""Private fixed collector entry; launched only by LocalCheckService."""
from pathlib import Path
import os
import sys

# Wait until the parent has attached this process to its private Windows job.
if sys.stdin.buffer.read(1) != b'1':
    raise SystemExit(1)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
temporary = Path(__file__).resolve().parents[1] / 'data/temp'
temporary.mkdir(parents=True, exist_ok=True)
os.environ.update(TEMP=str(temporary), TMP=str(temporary))
from campuslab.collect import main

if __name__ == '__main__':
    main()
