"""Start only restored CPU publishers in separate sessions and record identities."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time


OWN = Path(__file__).resolve().parent
REPO = OWN.parents[2]


def process(pid):
    root = Path('/proc') / str(pid)
    fields = (root / 'stat').read_text().rsplit(') ', 1)[1].split()
    return dict(pid=pid, start_ticks=fields[19], state=fields[0],
        argv=(root / 'cmdline').read_bytes().decode().rstrip('\0').split('\0'),
        boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('name', choices=('c2', 'p7', 'bridge'))
    options = parser.parse_args()
    commands = {
        'c2': [sys.executable, '-B', str(OWN / 'c2_restore.py'), 'run', '--session', str(OWN / 'c2_session1')],
        'p7': [sys.executable, '-B', str(OWN / 'p7_restore.py')],
        'bridge': [sys.executable, '-B', str(OWN.parent / 'rohin233_recovery_node4_20260918/bridge.py')],
    }
    command = commands[options.name]
    receipt = OWN / (options.name.upper() + '_SPAWNED.json')
    if receipt.exists():
        prior = json.loads(receipt.read_bytes())
        try:
            current = process(prior['pid'])
            if current['boot_id'] == prior['boot_id'] and current['start_ticks'] == prior['start_ticks']:
                print(json.dumps(dict(status='EXISTING_SAME_PROCESS', process=current)))
                return
        except FileNotFoundError:
            pass
        raise ValueError('prior_start_exists_requires_explicit_reconciliation')
    with (OWN / (options.name.upper() + '_RESTORE.log')).open('ab', buffering=0) as output:
        child = subprocess.Popen(command, cwd=REPO, stdin=subprocess.DEVNULL,
            stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
    time.sleep(2)
    if child.poll() is not None:
        raise RuntimeError(f'CPU_publisher_exited:{child.returncode}')
    identity = process(child.pid)
    with receipt.open('x') as handle:
        json.dump(dict(identity, started_unix=time.time(), native_signals=[]), handle, sort_keys=True, indent=2)
    print(json.dumps(dict(status='CPU_PROCESS_LIVE_DELIVERY_NOT_YET_PROVEN', process=identity)), flush=True)


if __name__ == '__main__':
    main()
