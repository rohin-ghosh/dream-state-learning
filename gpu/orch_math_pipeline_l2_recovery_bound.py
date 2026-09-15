"""End only the bound forensic processes at the user-assigned deadline."""

import argparse
import os
from pathlib import Path
import signal
import time

from gpu import orch_math_pipeline_l2_run as common


def run(root, deadline):
    identities = {}
    for arm in ('GUIDED_SLEEP', 'UNPARENTED_SLEEP'):
        identities[arm] = common.read(root / f'RECOVERY_LAUNCH_{arm}.json')['identity']
    while time.time() < deadline:
        if all((root / f'RECOVERY_{arm}' / 'FAILED.json').exists() or
               (root / f'RECOVERY_{arm}' / 'COMPLETE.json').exists() for arm in identities):
            break
        time.sleep(1)
    results = {}
    for arm, identity in identities.items():
        output = root / f'RECOVERY_{arm}'
        process = Path('/proc') / str(identity['pid'])
        if process.exists() and not (output / 'COMPLETE.json').exists():
            descriptor = os.pidfd_open(identity['pid'])
            try:
                assert common.process_identity(process) == identity and identity['uid'] == os.getuid()
                signal.pidfd_send_signal(descriptor, signal.SIGTERM)
            finally:
                os.close(descriptor)
        results[arm] = dict(complete=(output / 'COMPLETE.json').exists(),
            failed=(output / 'FAILED.json').exists(), original_saved_state_unavailable=True)
    common.write(root / 'RECOVERY_FIVE_MINUTE_BOUND.json', dict(deadline_unix=deadline,
        observed_unix=time.time(), results=results, peer_processes_signalled=0))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=common.ROOT)
    parser.add_argument('--deadline', type=float, required=True)
    options = parser.parse_args()
    run(options.root, options.deadline)
