"""Add priority-fill lanes without changing live sources or resetting lifetime."""

import fcntl
import os
from pathlib import Path
import signal
import subprocess
import time

from gpu import orch_rich_hot_a100_run as existing
import orch_rich_hot_a100_minor_scan as minor_scanner


INDICES = (2, 3, 7)


def inherited_lifetime(root, now):
    lifetime = existing.read(root / 'LIFETIME.json')
    existing.policy.require(now < lifetime['native_deadline_unix'], 'original_budget_expired')
    existing.policy.require(lifetime['hard_deadline_unix'] < existing.LEASE_END - 21600, 'lease_margin')
    return lifetime


def request_stop(child, pinned):
    if child.poll() is not None:
        return
    descriptor = os.pidfd_open(child.pid)
    try:
        existing.policy.require(existing.identity(Path('/proc') / str(child.pid)) == pinned and
                                pinned['uid'] == os.getuid(), 'exact_owned_pid_required')
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
    finally:
        os.close(descriptor)


def main():
    root = existing.ROOT
    existing.validate(root)
    ready = existing.read(root / 'FILL_READY.json')
    existing.policy.require(ready['driver_sha256'] == existing.sha(__file__) and
        ready['original_ready_sha256'] == existing.sha(root / 'READY.json') and
        ready['builder_receipt_sha256'] == existing.sha(root / 'FILL_BUILDER_RECEIPT.md') and
        ready['cpu_tests_passed'], 'fill_pregpu_required')
    lifetime = inherited_lifetime(root, time.time())
    lock = (root / 'FILL_GUARD.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    existing.exclusive(root / 'FILL_CLAIM.json', dict(identity=existing.identity(Path('/proc') / str(os.getpid())),
        indices=INDICES, lifetime=lifetime, own_additional_calls_ceiling=1536, aggregate_ceiling=3072,
        duplicate_cohort_repeat=True, counts_are_not_distinct_training_supply=True))
    children, logs, released, requested = {}, [], {}, set()
    signal.signal(signal.SIGTERM, lambda signum, frame: (_ for _ in ()).throw(SystemExit(128 + signum)))
    try:
        for index in INDICES:
            if (root / 'FILL_RELEASE_REQUEST.json').exists():
                break
            report = minor_scanner.scan(index, root / 'SERVICE_IDENTITY.json')
            existing.write(root / f'ADMISSION_{index}.json', report)
            existing.policy.require(report['clear'] and report['scanner_euid'] == 0, 'fill_admission_failed')
            log = (root / f'gpu{index}.log').open('x')
            logs.append(log)
            child = subprocess.Popen([existing.PYTHON, '-B', '-m', 'gpu.orch_rich_hot_a100_run', 'run',
                '--root', str(root), '--index', str(index)], cwd=root / 'source', start_new_session=True,
                env=dict(os.environ, CUDA_VISIBLE_DEVICES=existing.policy.DEVICES[index],
                         PYTHONPATH=str(root / 'source'), HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                         PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
                         TOKENIZERS_PARALLELISM='false'), stdout=log, stderr=subprocess.STDOUT)
            pinned = existing.identity(Path('/proc') / str(child.pid))
            children[index] = (child, pinned)
            existing.exclusive(root / f'LAUNCH_{index}.json', dict(identity=pinned,
                uuid=existing.policy.DEVICES[index], launched_unix=time.time(),
                fill_ready_sha256=existing.sha(root / 'FILL_READY.json'), inherited_lifetime=lifetime))
        while any(child.poll() is None for child, pinned in children.values()):
            existing.policy.require(time.time() < lifetime['hard_deadline_unix'] - 240, 'original12hour_guard')
            for index, (child, pinned) in children.items():
                if (root / 'FILL_RELEASE_REQUEST.json').exists() and index not in requested:
                    request_stop(child, pinned)
                    requested.add(index)
                if child.poll() is not None and index not in released:
                    report = minor_scanner.scan(index, root / 'SERVICE_IDENTITY.json')
                    existing.write(root / f'RELEASE_{index}.json', report)
                    released[index] = report['clear']
            time.sleep(2)
    except BaseException as error:
        existing.write(root / 'FILL_GUARD_FAILED.json', dict(type=type(error).__name__, message=str(error)))
        raise
    finally:
        for child, pinned in children.values():
            existing.stop_owned(child, pinned)
        for log in logs:
            log.close()
        for index in INDICES:
            if index not in released:
                report = minor_scanner.scan(index, root / 'SERVICE_IDENTITY.json')
                existing.write(root / f'RELEASE_{index}.json', report)
                released[index] = report['clear']
        existing.write(root / 'FILL_TERMINAL.json', dict(releases=released,
            returncodes={index: child.returncode for index, (child, _) in children.items()},
            finished_unix=time.time(), inherited_lifetime=lifetime))


if __name__ == '__main__':
    main()
