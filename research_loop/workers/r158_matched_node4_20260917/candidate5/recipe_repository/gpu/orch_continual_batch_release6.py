"""Extra sixth-GPU release only on Laplace's actual-ready request; other lanes untouched."""

import json
import os
from pathlib import Path
import signal
import sys
import time


GENERATOR = Path('/localhome/local-rohing/orch_rich_hot_a100_20260915_attempt1')
ROOT = Path('/localhome/local-rohing/orch_continual_batch_20260915_sidecar')


def main():
    sys.path.insert(0, str(GENERATOR))
    import orch_rich_hot_a100_minor_scan as scanner
    from gpu import orch_rich_hot_a100_run as original

    original.validate(GENERATOR)
    lifetime = original.read(GENERATOR / 'LIFETIME.json')
    original.exclusive(ROOT / 'EXTRA6_WATCH_IDENTITY.json', dict(
        identity=original.identity(Path('/proc') / str(os.getpid())), source_sha256=original.sha(__file__),
        inherited_deadline=lifetime['hard_deadline_unix'], sole_target=6))
    request_path = ROOT / 'LAPLACE_EXTRA6_RELEASE_REQUEST.json'
    while time.time() < lifetime['hard_deadline_unix']:
        if request_path.exists():
            request = original.read(request_path)
            original.policy.require(request.get('requester') == 'Laplace' and request.get('launch_ready') is True,
                                    'actual_Laplace_ready_required')
            expected = original.read(GENERATOR / 'LAUNCH_6.json')['identity']
            directory = Path('/proc') / str(expected['pid'])
            if directory.exists():
                descriptor = os.pidfd_open(expected['pid'])
                try:
                    original.policy.require(original.identity(directory) == expected and expected['uid'] == os.getuid(),
                                            'exact_owned_GPU6_process_required')
                    signal.pidfd_send_signal(descriptor, signal.SIGTERM)
                finally:
                    os.close(descriptor)
            original.write(ROOT / 'EXTRA6_STOP_REQUESTED.json', dict(identity=expected,
                request_sha256=original.sha(request_path), requested_unix=time.time()))
            while directory.exists() and time.time() < lifetime['hard_deadline_unix']:
                time.sleep(2)
            report = scanner.scan(6, GENERATOR / 'SERVICE_IDENTITY.json')
            original.write(ROOT / 'EXTRA6_RELEASE.json', report)
            return
        time.sleep(2)


if __name__ == '__main__':
    main()
