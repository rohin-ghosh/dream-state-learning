"""Safe-boundary node2 rolling handoff, never touching another owner's process."""

import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import time

from gpu import orch_rich_hot_node2_exhaustion_v3 as run


base, ROOT = run.base, run.ROOT


def process_state(expected):
    directory = Path('/proc') / str(expected['pid'])
    if not directory.exists():
        return None
    try:
        base.hot.require(base.process_identity(directory) == expected and expected['uid'] == os.getuid(), 'exact_owned_identity_required')
        return (directory / 'stat').read_text().rsplit(')', 1)[1].split()[0]
    except FileNotFoundError:
        return None


def signal_exact(expected, signum):
    if process_state(expected) in (None, 'Z'):
        return False
    descriptor = os.pidfd_open(expected['pid'])
    try:
        base.hot.require(process_state(expected) not in (None, 'Z'), 'identity_changed_before_signal')
        signal.pidfd_send_signal(descriptor, signum)
    finally:
        os.close(descriptor)
    return True


def resolved(root, shard):
    for path in (root / 'reservations').glob(f'{shard}_*.json'):
        row = base.read(path)
        capture = root / f'shard{shard}' / f'{row["task_id"]}_{row["stage"]}.json'
        try:
            complete = capture.exists() and base.read(capture)['index'] == row['index']
        except (FileNotFoundError, json.JSONDecodeError):
            complete = False
        if not complete:
            return False
    return True


def closed(root, shard):
    launch = root / f'LAUNCH_{shard}.json'
    if not launch.exists():
        return True
    if process_state(base.read(launch)['identity']) not in (None, 'Z'):
        return False
    after = root / f'shard{shard}/AFTER.json'
    terminal = root / f'shard{shard}/TERMINAL.json'
    if not (after.exists() and terminal.exists() and base.read(after).get('unchanged') is True and resolved(root, shard)):
        return False
    status = base.read(terminal)['status']
    if status in ('COMPLETE', 'BOUNDED_STOP', 'FINITE_POOL_COMPLETE'):
        return True
    failure = root / f'shard{shard}/FAILED.json'
    return (root == base.ORIGINAL and (ROOT / f'ORIGINAL_CUTOFF_{shard}.json').exists()
            and failure.exists() and base.read(failure).get('type') == 'KeyboardInterrupt')


def marker(path):
    if not path.exists():
        base.write(path, dict(reason='Rohin100 safe-boundary V3 handoff, no replay or budget reset',
                             successor=str(ROOT), observed_unix=time.time()))


def watch():
    prepared = run.validate()
    ready = base.read(ROOT / 'READY.json')
    base.hot.require(ready['cpu_tests_passed'] and ready['prepare_sha256'] == base.sha(ROOT / 'PREPARE.json')
        and ready['builder_receipt_sha256'] == base.sha(ROOT / 'BUILDER_RECEIPT.md'), 'bound_preGPU_builder')
    lifetime = base.read(ROOT / 'LIFETIME.json')
    base.hot.require(lifetime['hard_deadline_unix'] < base.LEASE_END - 21600, 'lease_margin')
    original_owner = base.read(base.ORIGINAL / 'NODE2_ALL8_LEASE_CLAIM.json')
    base.hot.require(original_owner['identity']['uid'] == os.getuid(), 'original_allocation_owner')
    lock = (ROOT / 'ROLLING_ADMISSION.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    base.write(ROOT / 'GUARD_IDENTITY.json', dict(identity=base.process_identity(Path('/proc') / str(os.getpid())),
        original_owner=original_owner, original_lifetime_sha256=base.sha(base.ORIGINAL / 'LIFETIME.json')))
    for root in (run.OLD_CONTROL, run.DERIVED, run.FLOOR):
        marker(root / 'STOP_AFTER_CALL.json')
    children, logs, scans, cutoffs = {}, [], dict.fromkeys(range(8), 0), set()
    old_dispatch_stopped, reservation_lock = False, None
    status = 'FAILED'

    def interrupted(signum, frame):
        raise SystemExit(128 + signum)

    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        while time.time() < lifetime['hard_deadline_unix'] - 240:
            old_launches = list(run.OLD_CONTROL.glob('LAUNCH_[0-7].json'))
            if not old_dispatch_stopped and all(process_state(base.read(path)['identity']) in (None, 'Z') for path in old_launches):
                identity = base.read(run.OLD_CONTROL / 'LAUNCH.json')['identity']
                if not (ROOT / 'OLD_CONTROL_STOP.json').exists():
                    signalled = signal_exact(identity, signal.SIGTERM)
                    base.write(ROOT / 'OLD_CONTROL_STOP.json', dict(identity=identity, signalled=signalled,
                        children_already_terminal=True, observed_unix=time.time(), prior_status_sha256=base.sha(run.OLD_CONTROL / 'STATUS.json')))
                old_dispatch_stopped = process_state(identity) in (None, 'Z')
            if old_dispatch_stopped and reservation_lock is None:
                reservation_lock = (base.ORIGINAL / 'CALLS.jsonl').open('a+')
                fcntl.flock(reservation_lock, fcntl.LOCK_EX)
                base.write(ROOT / 'ORIGINAL_DISPATCH_QUIESCED.json', dict(observed_unix=time.time(),
                    source_sha256=base.sha(base.ORIGINAL / 'source.tar'), ledger_sha256=base.sha(base.ORIGINAL / 'CALLS.jsonl')))
            for shard in range(8):
                if reservation_lock is not None and shard not in cutoffs and resolved(base.ORIGINAL, shard):
                    identity = base.read(base.ORIGINAL / f'LAUNCH_{shard}.json')['identity']
                    state = process_state(identity)
                    base.write(ROOT / f'ORIGINAL_CUTOFF_{shard}.json', dict(identity=identity, prior_state=state,
                        all_reserved_calls_captured=True, next_reservation_blocked=True,
                        observed_unix=time.time(), reserved_calls=run.counts(base.ORIGINAL)[shard],
                        signal='SIGINT' if state not in (None, 'Z') else None,
                        preservation='Original source/raw/stdout and cutoff AFTER/TERMINAL remain at original native root; no replay.'))
                    signal_exact(identity, signal.SIGINT)
                    cutoffs.add(shard)
                if shard in children or time.time() >= lifetime['native_deadline_unix'] - 120:
                    continue
                if not all(closed(root, shard) for root in (base.ORIGINAL, run.FLOOR, run.DERIVED)):
                    continue
                report = base.scan(shard, ROOT / 'SERVICE_IDENTITY.json')
                base.write(ROOT / f'ADMISSION_{shard}_{scans[shard]:04d}.json', report)
                scans[shard] += 1
                if not (report['clear'] and report['scanner_euid'] == 0):
                    continue
                base.write(ROOT / f'LEASE_CLAIM_{shard}.json', dict(uuid=base.hot.UUIDS[shard], source_sha256=prepared['source_sha256'],
                    same_original_owner=True, prior_requests_resolved=True, after_unchanged=True,
                    inherited_deadline_unix=lifetime['hard_deadline_unix'], observed_unix=time.time()))
                log = (ROOT / f'shard{shard}.log').open('x')
                logs.append(log)
                child = subprocess.Popen([base.PYTHON, '-B', '-m', 'gpu.orch_rich_hot_node2_exhaustion_v3', '--shard', str(shard)],
                    cwd=ROOT / 'source', start_new_session=True, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                    env=dict(os.environ, CUDA_VISIBLE_DEVICES=base.hot.UUIDS[shard], PYTHONPATH=str(ROOT / 'source'),
                        HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
                        TOKENIZERS_PARALLELISM='false', PYTHONDONTWRITEBYTECODE='1'))
                identity = base.process_identity(Path('/proc') / str(child.pid))
                children[shard] = child, identity
                base.write(ROOT / f'LAUNCH_{shard}.json', dict(identity=identity, uuid=base.hot.UUIDS[shard], started_unix=time.time()))
            base.exporter.replace_json(ROOT / 'STATUS.json', dict(observed_unix=time.time(), launched_shards=sorted(children),
                pending_shards=sorted(set(range(8)) - set(children)), returncodes={str(shard): child.poll() for shard, (child, identity) in children.items()}))
            if len(children) == 8 and all(child.poll() is not None for child, identity in children.values()):
                status = 'COMPLETE' if all(child.returncode == 0 for child, identity in children.values()) else 'NATIVE_FAILURE'
                break
            time.sleep(5)
        else:
            status = 'INHERITED_HARD_GUARD'
    except BaseException as error:
        base.write(ROOT / 'GUARD_FAILED.json', dict(type=type(error).__name__, message=str(error)))
        raise
    finally:
        for child, identity in children.values():
            base.stop_owned(child, identity)
        for log in logs:
            log.close()
        if reservation_lock is not None:
            reservation_lock.close()
        base.write(ROOT / 'GUARD_TERMINAL.json', dict(status=status, finished_unix=time.time(), lifetime=lifetime))
        lock.close()


if __name__ == '__main__':
    watch()
