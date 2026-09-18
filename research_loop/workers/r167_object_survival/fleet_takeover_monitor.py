"""Bounded wrapper-only operational observations; no model/provider execution."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
DIRECTORY = HERE / 'fleet_generation2' / 'takeover_monitor1'
HARD_END = 1789659000


def write(path, document):
    with path.open('x') as stream:
        json.dump(document, stream, sort_keys=True)


def main():
    os.umask(0o077)
    DIRECTORY.mkdir(mode=0o700, exist_ok=False)
    observer = HERE / 'fleet_operational_observer.py'
    source = observer.read_bytes()
    checksum = hashlib.sha256(source).hexdigest()
    write(DIRECTORY / 'ONCE.json', dict(status='READ_ONLY_METADATA_MONITOR', started_unix=time.time(),
        hard_end_unix=HARD_END, observer_sha256=checksum, provider_launch=False, gpu_dispatch=False))
    sequence = 0
    while time.time() < HARD_END:
        if hashlib.sha256(observer.read_bytes()).hexdigest() != checksum:
            write(DIRECTORY / 'SOURCE_CHANGED_STOP.json', dict(status='OBSERVER_SOURCE_CHANGED_STOP', observed_unix=time.time()))
            return
        filename = f'{sequence:04d}.json'
        try:
            result = subprocess.run(['bash', str(REPO / 'gpu/ovx_ssh.sh'), 'python3 -B -'],
                input=source, capture_output=True, timeout=30, cwd=REPO,
                env=dict(PATH=os.environ.get('PATH', '/usr/bin:/bin'), HOME=os.environ['HOME']))
            if result.returncode:
                write(DIRECTORY / filename, dict(status='OBSERVATION_FAILED_NOT_JOB_RETRY',
                    returncode=result.returncode, observed_unix=time.time()))
                with (DIRECTORY / f'{sequence:04d}.stderr.private.txt').open('xb') as stream:
                    stream.write(result.stderr)
            else:
                report = json.loads(result.stdout)
                if report.get('status') != 'OPERATIONAL_METADATA_ONLY' or report.get('sealed_content_read') is not False:
                    raise ValueError('metadata_projection_required')
                write(DIRECTORY / filename, report)
        except (subprocess.TimeoutExpired, ValueError) as error:
            write(DIRECTORY / filename, dict(status='OBSERVATION_UNCERTAIN_NOT_JOB_RETRY',
                error_type=type(error).__name__, observed_unix=time.time()))
        sequence += 1
        time.sleep(max(0, min(60, HARD_END - time.time())))
    write(DIRECTORY / 'TERMINAL.json', dict(status='ORIGINAL_WINDOW_METADATA_MONITOR_ENDED',
        observed_unix=time.time(), observations=sequence, models_launched=0, retries_of_jobs=0))


if __name__ == '__main__':
    main()
