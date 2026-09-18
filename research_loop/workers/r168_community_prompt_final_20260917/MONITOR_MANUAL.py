"""Read-only manual exposure watch; original operation deadline, no parent changes."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from gpu import orch_r153_community_parents as community


STAGE = Path(__file__).resolve().parent
ROOT = STAGE.parents[2]
DEADLINE = 1789634854


def main():
    output = STAGE/'MANUAL_OBSERVER'
    output.mkdir(mode=0o700)
    community.write(output/'STARTED.json', dict(pid=os.getpid(), started_unix=time.time(),
        deadline_unix=DEADLINE, interval_seconds=60, actual_read_budget=268435456,
        no_publications=True, no_signals=True, no_provider_calls=True,
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
    used = 0
    latest = None
    status = 'BOUND_ENDED_NO_RENDER_CLAIM'
    for index in range(16):
        if time.time() >= DEADLINE or used + 134217728 > 268435456:
            break
        result = subprocess.run([sys.executable, '-B', str(STAGE/'OBSERVE_MANUAL.py')],
            cwd=ROOT, env=dict(os.environ, PYTHONPATH=str(ROOT)), capture_output=True, text=True,
            timeout=min(50, max(1, DEADLINE-time.time())))
        if result.returncode:
            community.write(output/'OBSERVER_FAILED.json', dict(exit_code=result.returncode,
                stderr=result.stderr[-4000:], observed_unix=time.time(), not_parent_failure=True))
            status = 'OBSERVER_FAILED_NO_RENDER_INFERENCE'
            break
        report = json.loads(result.stdout)
        used += report['observation']['bytes_read_this_poll']
        latest = dict(path=report['path'], sha256=report['sha256'])
        print(json.dumps(dict(observed_unix=report['observation']['observed_unix'],
            status=report['observation']['status'], receipt=latest,
            actual_bytes_read_this_observer=used)), flush=True)
        if report['observation']['status'] == 'RENDERED':
            status = 'MANUAL_TURN_RENDERED'
            break
        time.sleep(max(0, min(60, DEADLINE-time.time())))
    community.write(output/'TERMINAL.json', dict(status=status, finished_unix=time.time(),
        actual_bytes_read_this_observer=used, latest=latest, no_parent_or_native_changes=True))


if __name__ == '__main__':
    main()
