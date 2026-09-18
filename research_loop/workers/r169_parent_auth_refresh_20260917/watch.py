"""Bounded read-only follow-through for the consumed eighteen-parent refresh."""

import json
from pathlib import Path
import subprocess
import sys
import time


root = Path(__file__).resolve().parent
deadline = time.time()+900
with (root/'WATCH_STARTED.json').open('x') as output:
    json.dump(dict(started_unix=time.time(), deadline_unix=deadline, interval_seconds=60,
                   read_only=True, no_provider_calls=True, no_restarts=True), output)
status = 'DEADLINE'
observations = 0
while time.time() < deadline:
    result = subprocess.run([sys.executable, '-B', str(root/'observe.py')],
        stdin=subprocess.DEVNULL, capture_output=True, timeout=120)
    if result.returncode:
        status = 'OBSERVER_FAILED_NO_RETRY'
        break
    print(result.stdout.decode(), end='', flush=True)
    observations += 1
    time.sleep(min(60, max(0, deadline-time.time())))
with (root/'WATCH_FINISHED.json').open('x') as output:
    json.dump(dict(status=status, finished_unix=time.time(), observations=observations), output)
