"""Finite incremental continuation of the same sixteen immutable age ledgers."""

import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

from research_loop.workers.rohin233_kept_age_probe_20260918 import enroll


WORKER = Path(__file__).resolve().parent
PREVIOUS = WORKER.parent / 'rohin233_kept_age_probe_20260918'
REPO = WORKER.parents[2]
DEADLINE = 1789754250


def bounded_page(target, cursor, repo):
    if target['wrapper'] not in enroll.WRAPPERS:
        raise ValueError('registered_current_wrapper_only')
    source = Path(enroll.__file__).read_text().rsplit("if __name__ == '__main__':", 1)[0]
    code = source + '\nprint(json.dumps(page(' + repr(target) + ',' + repr(cursor) + ',limit=64)))\n'
    result = subprocess.run(['bash', str(repo / 'gpu' / target['wrapper']), 'python3 -B -'], input=code,
        text=True, capture_output=True, timeout=30)
    if result.returncode or len(result.stdout) > 1048576:
        raise ValueError('bounded_remote_metadata_failed')
    return json.loads(result.stdout)


def main():
    assert time.time() < DEADLINE and DEADLINE + 21600 <= 1789776000
    os.umask(0o077)
    bindings = [('enrollment', 'REGISTRATION.json'), ('extra_enrollment', 'EXTRA_REGISTRATION.json')]
    locks, registrations, before = [], [], []
    for directory, filename in bindings:
        output = PREVIOUS / directory
        lock = (output / 'ENROLL.lock').open('a')
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        locks.append(lock)
        raw = (PREVIOUS / 'private' / filename).read_bytes()
        registration = json.loads(raw)
        registration['deadline_unix'] = DEADLINE
        state_bytes = (output / 'private/STATE.json').read_bytes()
        state = json.loads(state_bytes)
        before.append(dict(ledger=directory, state_sha256=hashlib.sha256(state_bytes).hexdigest(),
            enrolled=len(state['entries']), registration_sha256=hashlib.sha256(raw).hexdigest(),
            cursors={name:value['last_index'] for name,value in state['cursors'].items()}))
        registrations.append((registration, output))
    assert sum(len(registration['targets']) for registration, _ in registrations) == 16
    assert len({target['journal_id'] for registration, _ in registrations for target in registration['targets']}) == 16
    enroll.put(WORKER / 'AGE_ENROLLMENT_STARTED.json', dict(unix=time.time(),pid=os.getpid(),
        deadline_unix=DEADLINE, prior_ledgers=before, native_roots=16, same_registered_sources=True,
        cursors_reset=False, enrollment_is_not_capture_or_evaluation=True, learner_signals=[],
        maximum_records_per_page=64, six_hour_margin=True))
    enroll.remote_page = bounded_page
    while time.time() < DEADLINE:
        statuses = []
        for registration, output in registrations:
            status = enroll.tick(registration, output, REPO)
            statuses.append(status)
        rows = [row for status in statuses for row in status['rows']]
        enroll.put(WORKER / 'AGE_ENROLLMENT_LATEST.json', dict(unix=time.time(),pid=os.getpid(),
            deadline_unix=DEADLINE, enrolled=sum(status['enrolled'] for status in statuses), rows=rows,
            roots=16, capture_and_evaluations='separate_receipts_not_implied_by_enrollment',
            GAME_UNPARENTED_N2='CONFIRMED_KEPT_SEPARATE_SIXTEENTH_ROOT', learner_signals=[]))
        time.sleep(min(15, max(0, DEADLINE-time.time())))


if __name__ == '__main__':
    main()
