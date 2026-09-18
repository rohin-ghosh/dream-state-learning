"""Hold only the exact ordinary parent quiet during its R188 root restoration."""

import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time

from inventory_node1 import HERE, identity, unchanged, require
from parent_custody import transport_children, write


def main(physical):
    require(physical in (2, 3), 'two_old_sleep_lives_only')
    candidates = sorted(path for path in HERE.glob('lane' + str(physical) + '_activation_r184_effort_*')
        if (path / 'PARENT_ACTIVATED.json').is_file() and not (path / 'SUPERSEDED.json').exists())
    require(len(candidates) == 1, 'one_current_R184_parent')
    directory = candidates[0]
    expected = json.loads((directory / 'PARENT_ACTIVATED.json').read_text())['actor']
    require(expected['uid'] == os.getuid() and str(HERE / 'r184_effort_parent.py') in expected['argv'], 'only_owned_parent')
    descriptor = os.pidfd_open(expected['pid'])
    paused = False
    output = HERE / ('R188_PARENT_QUIET_LANE' + str(physical))
    output.mkdir()
    try:
        deadline = time.monotonic() + 90
        while True:
            current = identity(Path('/proc') / str(expected['pid']))
            require(unchanged(expected, current) and current['state'] not in ('T', 't', 'Z', 'X'), 'exact_live_parent')
            signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
            paused = True
            for unused in range(100):
                if identity(Path('/proc') / str(expected['pid']))['state'] in ('T', 't'):
                    break
                time.sleep(.01)
            attempts = list((directory / 'parent').glob('parent_*'))
            if all((path / 'RESULT.json').is_file() for path in attempts if path.is_dir()) and not transport_children(expected['pid']):
                break
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
            paused = False
            require(time.monotonic() < deadline, 'parent_busy_no_child_action')
            time.sleep(.2)
        require(not list((directory / 'parent').glob('parent_*/PUBLICATION_UNKNOWN.json')), 'unknown_publication_preserved_no_child_action')
        write(output / 'PAUSED.json', dict(parent=expected, observed_unix=time.time(), attempts=[str(path) for path in attempts]))
        command = ('cd /localhome/local-rohing/orch_r181_node1_20260917/journal_overlay/support_identity_operator && '
            'CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 /localhome/local-rohing/v2/venv/bin/python -B r188_node1.py run ' + str(physical))
        result = subprocess.run(['bash', str(HERE.parents[3] / 'gpu/a100_ssh.sh'), command], text=True, capture_output=True, timeout=240)
        receipt = dict(returncode=result.returncode, stdout=result.stdout, stderr=result.stderr, observed_unix=time.time())
        write(output / 'REMOTE_RESULT.json', receipt)
        print(json.dumps(receipt), flush=True)
    finally:
        if paused and not select.select([descriptor], [], [], 0)[0]:
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        os.close(descriptor)


if __name__ == '__main__':
    main(int(sys.argv[1]))
