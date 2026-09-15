"""Per-lane natural-checkpoint succession; never interrupt the original workers."""

import argparse
import fcntl
import os
from pathlib import Path
import signal
import subprocess
import time

from gpu import orch_rich_hot_node2_continue as previous
from organism_v6 import orch_rich_hot_node2_floor98 as policy


ROOT = Path('/localhome/local-rohing/orch_rich_hot_node2_floor98_20260915_attempt1')


def ready_lane(original, shard):
    terminal = original / f'shard{shard}/TERMINAL.json'
    if not terminal.exists():
        return False
    previous.hot.require(previous.read(terminal)['status'] == 'COMPLETE', 'original_lane_failed_no_auto_replay')
    after = original / f'shard{shard}/AFTER.json'
    previous.hot.require(after.exists() and previous.read(after)['unchanged'] is True, 'original_lane_after_required')
    launch = previous.read(original / f'LAUNCH_{shard}.json')['identity']
    if (Path('/proc') / str(launch['pid'])).exists():
        return False
    for path in (original / 'reservations').glob(f'{shard}_*.json'):
        row = previous.read(path)
        capture = original / f'shard{shard}' / f'{row["task_id"]}_{row["stage"]}.json'
        previous.hot.require(capture.exists() and previous.read(capture)['index'] == row['index'], 'unresolved_original_lane_request')
    return True


def configure():
    previous.ROOT = ROOT
    previous.policy = policy


def watch(root):
    prepared = previous.validate(root)
    ready = previous.read(root / 'READY.json')
    previous.hot.require(ready['cpu_tests_passed'] and ready['prepare_sha256'] == previous.sha(root / 'PREPARE.json')
        and ready['builder_receipt_sha256'] == previous.sha(root / 'BUILDER_RECEIPT.md'), 'floor98_builder_gate')
    lifetime = previous.read(root / 'LIFETIME.json')
    previous.hot.require(lifetime['hard_deadline_unix'] < previous.LEASE_END - 21600, 'original_lease_margin')
    owner = previous.read(previous.ORIGINAL / 'NODE2_ALL8_LEASE_CLAIM.json')
    previous.hot.require(owner['identity']['uid'] == os.getuid() and owner['devices'] ==
                         {key: list(value) for key, value in previous.hot.DEVICES.items()}, 'same_original_allocation_owner')
    lock = (root / 'SUCCESSOR_SUBLEASE.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    previous.write(root / 'WATCH_IDENTITY.json', dict(identity=previous.process_identity(Path('/proc') / str(os.getpid())),
        ready_sha256=previous.sha(root / 'READY.json'), queued_unix=time.time(), original_owner=owner['identity']))
    (root / 'reservations').mkdir(exist_ok=False)
    children, logs, attempted, scan_attempts = {}, [], set(), dict.fromkeys(range(8), 0)
    status = 'FAILED'

    def interrupted(signum, frame):
        raise SystemExit(128 + signum)

    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        while time.time() < lifetime['hard_deadline_unix'] - 240:
            can_start = time.time() < lifetime['native_deadline_unix'] - 600 and not (root / 'STOP_AFTER_CALL.json').exists()
            for shard in range(8):
                if shard in attempted or not can_start:
                    continue
                try:
                    lane_ready = ready_lane(previous.ORIGINAL, shard)
                except ValueError as error:
                    previous.write(root / f'LANE_BLOCKED_{shard}.json', dict(error=str(error), observed_unix=time.time()))
                    attempted.add(shard)
                    continue
                if not lane_ready:
                    continue
                previous.validate(root)
                report = previous.scan(shard, root / 'SERVICE_IDENTITY.json')
                previous.write(root / f'ADMISSION_{shard}_{scan_attempts[shard]:04d}.json', report)
                scan_attempts[shard] += 1
                if not (report['clear'] and report['scanner_euid'] == 0):
                    continue
                previous.write(root / f'LEASE_CLAIM_{shard}.json', dict(shard=shard, uuid=previous.hot.UUIDS[shard],
                    original_lane=previous.read(previous.ORIGINAL / f'LAUNCH_{shard}.json'),
                    original_claim_sha256=previous.sha(previous.ORIGINAL / 'NODE2_ALL8_LEASE_CLAIM.json'),
                    original_lifetime_sha256=prepared['original_lifetime_sha256'],
                    source_sha256=prepared['source_sha256'], admitted_unix=time.time(),
                    authority='Rohin98 same-owner per-lane successor after natural completion; no original process stopped'))
                log = (root / f'shard{shard}.log').open('x')
                logs.append(log)
                child = subprocess.Popen([previous.PYTHON, '-B', '-m', 'gpu.orch_rich_hot_node2_floor98', 'run', '--shard', str(shard)],
                    cwd=root / 'source', start_new_session=True, env=dict(os.environ, CUDA_VISIBLE_DEVICES=previous.hot.UUIDS[shard],
                        PYTHONPATH=str(root / 'source'), HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1',
                        MKL_NUM_THREADS='1', TOKENIZERS_PARALLELISM='false', PYTHONDONTWRITEBYTECODE='1'),
                    stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
                identity = previous.process_identity(Path('/proc') / str(child.pid))
                children[shard] = child, identity
                attempted.add(shard)
                previous.write(root / f'LAUNCH_{shard}.json', dict(identity=identity, uuid=previous.hot.UUIDS[shard], started_unix=time.time()))
            previous.exporter.replace_json(root / 'WATCH_STATUS.json', dict(observed_unix=time.time(),
                launched_shards=sorted(children), pending_shards=sorted(set(range(8)) - attempted),
                returncodes={str(shard): child.poll() for shard, (child, identity) in children.items()},
                original_deadline_unix=lifetime['hard_deadline_unix']))
            if (len(attempted) == 8 or not can_start) and all(child.poll() is not None for child, identity in children.values()):
                status = 'BOUNDED_COMPLETE' if all(child.returncode == 0 for child, identity in children.values()) else 'NATIVE_FAILURE'
                break
            time.sleep(30)
        else:
            status = 'INHERITED_HARD_GUARD'
    except BaseException as error:
        previous.write(root / 'GUARD_FAILED.json', dict(type=type(error).__name__, message=str(error)))
        raise
    finally:
        for child, identity in children.values():
            previous.stop_owned(child, identity)
        for log in logs:
            log.close()
        releases = {}
        for shard in children:
            try:
                report = previous.scan(shard, root / 'SERVICE_IDENTITY.json', timeout_seconds=20)
                previous.write(root / f'RELEASE_{shard}.json', report)
                releases[str(shard)] = report['clear']
            except Exception as error:
                releases[str(shard)] = False
                previous.write(root / f'RELEASE_{shard}.json', dict(clear=False, error=str(error)))
        previous.write(root / 'TERMINAL.json', dict(status=status, releases=releases, finished_unix=time.time(), lifetime=lifetime))
        lock.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'run', 'watch'))
    parser.add_argument('--shard', type=int, choices=range(8))
    options = parser.parse_args()
    configure()
    if options.phase == 'prepare':
        previous.prepare(ROOT)
    elif options.phase == 'run':
        previous.run(ROOT, options.shard)
    else:
        watch(ROOT)
