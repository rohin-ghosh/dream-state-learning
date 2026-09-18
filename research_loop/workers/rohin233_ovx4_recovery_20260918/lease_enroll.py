"""Continue all sixteen enrollment cursors under the reported existing lease."""

import fcntl
import hashlib
import json
import os
from pathlib import Path
import time

from research_loop.workers.rohin233_ovx4_recovery_20260918.resume_ages import bounded_page, PREVIOUS, REPO, WORKER
from research_loop.workers.rohin233_kept_age_probe_20260918 import enroll


DEADLINE = 1790791170


def main():
    assert time.time() < DEADLINE <= 1790812800-21600
    locks, registrations, before = [], [], []
    for directory, filename in [('enrollment','REGISTRATION.json'), ('extra_enrollment','EXTRA_REGISTRATION.json')]:
        output = PREVIOUS / directory
        lock = (output / 'ENROLL.lock').open('a')
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        locks.append(lock)
        raw = (output / 'private/STATE.json').read_bytes()
        state = json.loads(raw)
        before.append(dict(ledger=directory, state_sha256=hashlib.sha256(raw).hexdigest(), entries=len(state['entries']),
            cursors={name:value['last_index'] for name,value in state['cursors'].items()}))
        registration = json.loads((PREVIOUS / 'private' / filename).read_bytes())
        registration['deadline_unix'] = DEADLINE
        registrations.append((registration,output))
    assert sum(len(registration['targets']) for registration, unused in registrations) == 16
    enroll.put(WORKER / 'LEASE_ENROLLMENT_STARTED.json', dict(unix=time.time(),pid=os.getpid(),deadline_unix=DEADLINE,
        prior_ledgers=before,cursors_reset=False,learner_signals=[],enrollment_is_not_evaluation=True))
    enroll.remote_page = bounded_page
    while time.time() < DEADLINE:
        statuses = [enroll.tick(registration,output,REPO) for registration,output in registrations]
        enroll.put(WORKER / 'LEASE_ENROLLMENT_LATEST.json', dict(unix=time.time(),pid=os.getpid(),deadline_unix=DEADLINE,
            enrolled=sum(status['enrolled'] for status in statuses), rows=[row for status in statuses for row in status['rows']],
            roots=16, capture_and_evaluations='separate_actual_receipts'))
        time.sleep(min(15,max(0,DEADLINE-time.time())))


if __name__ == '__main__':
    main()
