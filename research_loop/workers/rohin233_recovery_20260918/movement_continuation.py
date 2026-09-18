"""Continue the read-only movement audit after its original CPU process exits."""

import json
import os
from pathlib import Path
import select
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
AUDITOR = HERE.parent / 'rohin233_focus_20260918/movement.py'
PREDECESSOR_PID = 2743158


def main():
    process = Path('/proc') / str(PREDECESSOR_PID)
    descriptor = os.pidfd_open(PREDECESSOR_PID)
    try:
        arguments = process.joinpath('cmdline').read_bytes().split(b'\0')
        if not any(argument.endswith(b'/rohin233_focus_20260918/movement.py') for argument in arguments):
            raise ValueError('exact_existing_movement_reader')
        ticks = process.joinpath('stat').read_text().rsplit(') ', 1)[1].split()[19]
        receipt = dict(mode='READ_ONLY_AUDITOR_CONTINUATION', observed_unix=time.time(),
            predecessor_pid=PREDECESSOR_PID, predecessor_start_ticks=ticks,
            waiter_pid=os.getpid(), learner_signals=[], parent_writes=0,
            end_unix=1789927200, state='WAITING_FOR_NATURAL_READER_EXIT')
        (HERE / 'MOVEMENT_CONTINUATION.json').write_text(json.dumps(receipt, indent=2) + '\n')
        while not select.select([descriptor], [], [], 10)[0]:
            if time.time() >= receipt['end_unix']:
                raise TimeoutError('earliest_reported_fleet_lease_bound')
    finally:
        os.close(descriptor)
    command = [sys.executable, '-B', str(AUDITOR), '--end-unix', str(receipt['end_unix'])]
    with (HERE / 'MOVEMENT_LEASE.log').open('a') as log:
        successor = subprocess.Popen(command, stdin=subprocess.DEVNULL,
            stdout=log, stderr=subprocess.STDOUT, start_new_session=True, close_fds=True)
    receipt.update(state='SUCCESSOR_DISPATCHED', successor_pid=successor.pid,
        dispatched_unix=time.time(), next_audit_not_yet_verified=True)
    (HERE / 'MOVEMENT_CONTINUATION.json').write_text(json.dumps(receipt, indent=2) + '\n')


if __name__ == '__main__':
    main()
