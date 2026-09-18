"""Restart exact owned parent processes without resetting their turn ledgers."""

import argparse
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time

import parent_c


def restart(physical):
    root = parent_c.OWN / f'parent_physical{physical}'
    previous = parent_c.read(root / 'PROCESS.json') if (root / 'PROCESS.json').exists() else None
    if previous and Path('/proc', str(previous['pid'])).exists():
        process = Path('/proc', str(previous['pid']))

        def identity():
            return ((process / 'stat').read_text().rsplit(')', 1)[1].split()[19],
                (process / 'cmdline').read_bytes().rstrip(b'\0').decode().split('\0'))

        expected = identity()
        assert expected[0] == str(previous.get('start_ticks', previous.get('ticks')))
        assert expected[1][-3:] == ['serve', '--physical', str(physical)]
        assert expected[1][-4] == str(parent_c.OWN / 'fleet_parent.py') and process.stat().st_uid == os.getuid()
        descriptor = os.pidfd_open(previous['pid'])
        paused = False
        try:
            deadline = time.monotonic() + 60
            while time.monotonic() < deadline:
                assert identity() == expected
                signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
                paused = True
                time.sleep(.03)
                children = (process / 'task' / str(previous['pid']) / 'children').read_text().split()
                active = [child for child in children if Path('/proc', child, 'stat').exists()
                    and Path('/proc', child, 'stat').read_text().rsplit(')', 1)[1].split()[0] not in ('Z', 'X')]
                if not active:
                    assert all((directory / 'RESULT.json').exists() for directory in (root / 'turns').glob('parent_*'))
                    signal.pidfd_send_signal(descriptor, signal.SIGTERM)
                    signal.pidfd_send_signal(descriptor, signal.SIGCONT)
                    paused = False
                    assert select.select([descriptor], [], [], 20)[0]
                    break
                signal.pidfd_send_signal(descriptor, signal.SIGCONT)
                paused = False
                time.sleep(.2)
            else:
                raise RuntimeError('inflight_parent_left_unchanged')
        finally:
            if paused:
                signal.pidfd_send_signal(descriptor, signal.SIGCONT)
            os.close(descriptor)
    suffix = str(time.time_ns())
    if previous:
        (root / 'PROCESS.json').rename(root / ('PROCESS_PRE_REPAIR_' + suffix + '.json'))
    command = [sys.executable, '-B', str(parent_c.OWN / 'fleet_parent.py'), 'serve', '--physical', str(physical)]
    with (root / ('PARENT_REPAIR_' + suffix + '.log')).open('x') as log:
        process = subprocess.Popen(command, cwd=parent_c.REPO, stdin=subprocess.DEVNULL,
            stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    ticks = Path('/proc', str(process.pid), 'stat').read_text().rsplit(')', 1)[1].split()[19]
    receipt = dict(pid=process.pid, start_ticks=ticks, command=command, started_unix=time.time(),
        seed_and_turn_ledger_preserved=True, validators_unchanged=True)
    parent_c.write(root / 'PROCESS.json', receipt)
    print(json.dumps(dict(physical=physical, **receipt)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--physical', type=int, choices=(0, 1, 2, 3, 5, 7), required=True)
    restart(parser.parse_args().physical)
