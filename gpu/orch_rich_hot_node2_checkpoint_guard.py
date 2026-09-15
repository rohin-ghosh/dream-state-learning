"""Rohin99 one-checkpoint/seven37ec successor guardian, preserving original jobs."""

import fcntl
import os
from pathlib import Path
import signal
import subprocess
import time

from gpu import orch_rich_hot_node2_floor98 as floor
from gpu import orch_rich_hot_node2_continue as base
from gpu.orch_rich_hot_node2_checkpoint99 import ROOT as DERIVED


CONTROL = Path('/localhome/local-rohing/orch_rich_hot_node2_checkpoint99_control_20260915_attempt1')


def target(shard):
    if shard not in range(8):
        raise ValueError('only_node2')
    return (DERIVED, 'gpu.orch_rich_hot_node2_checkpoint99', []) if shard == 0 else (
        floor.ROOT, 'gpu.orch_rich_hot_node2_floor98', ['--shard', str(shard)])


def ready(root):
    prepared, receipt = base.read(root / 'PREPARE.json'), base.read(root / 'READY.json')
    base.hot.require(receipt['cpu_tests_passed'] and receipt['prepare_sha256'] == base.sha(root / 'PREPARE.json')
        and receipt['builder_receipt_sha256'] == base.sha(root / 'BUILDER_RECEIPT.md'), 'bound_CPU_builder')
    base.hot.require(base.sha(root / 'source.tar') == prepared['source_sha256'], 'source_archive_drift')
    base.verify_archive(root / 'source.tar', root / 'source')
    base.hot.require(all(base.sha(root / name) == digest for name, digest in prepared['files'].items()), 'frozen_input_drift')
    return prepared


def watch():
    configuration = base.read(CONTROL / 'READY.json')
    base.hot.require(configuration['cpu_tests_passed'] and configuration['source_sha256'] == base.sha(Path(__file__))
        and configuration['builder_receipt_sha256'] == base.sha(CONTROL / 'BUILDER_RECEIPT.md'), 'controller_preGPU_gate')
    lifetime = base.read(base.ORIGINAL / 'LIFETIME.json')
    base.hot.require(lifetime['hard_deadline_unix'] < base.LEASE_END - 21600, 'lease_margin')
    lock = (floor.ROOT / 'SUCCESSOR_SUBLEASE.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    base.write(CONTROL / 'IDENTITY.json', dict(identity=base.process_identity(Path('/proc') / str(os.getpid())),
        original_lifetime=lifetime, allocation={str(shard): str(target(shard)[0]) for shard in range(8)}))
    (DERIVED / 'reservations').mkdir(exist_ok=True)
    children, logs, attempted, scans = {}, [], set(), dict.fromkeys(range(8), 0)
    status = 'FAILED'

    def interrupted(signum, frame):
        raise SystemExit(128 + signum)

    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        while time.time() < lifetime['hard_deadline_unix'] - 240:
            for shard in range(8):
                root, module, arguments = target(shard)
                if shard in attempted or time.time() >= lifetime['native_deadline_unix'] - 600 or (CONTROL / 'STOP_AFTER_CALL.json').exists():
                    continue
                if not (root / 'READY.json').exists() or not floor.ready_lane(base.ORIGINAL, shard):
                    continue
                prepared = ready(root)
                report = base.scan(shard, root / 'SERVICE_IDENTITY.json')
                base.write(CONTROL / f'ADMISSION_{shard}_{scans[shard]:04d}.json', report)
                scans[shard] += 1
                if not report['clear'] or report['scanner_euid'] != 0:
                    continue
                base.write(CONTROL / f'LEASE_CLAIM_{shard}.json', dict(shard=shard, uuid=base.hot.UUIDS[shard],
                    original_lane=base.read(base.ORIGINAL / f'LAUNCH_{shard}.json'), source_sha256=prepared['source_sha256'],
                    original_lifetime_sha256=base.sha(base.ORIGINAL / 'LIFETIME.json'), admitted_unix=time.time()))
                log = (CONTROL / f'shard{shard}.log').open('x')
                logs.append(log)
                child = subprocess.Popen([base.PYTHON, '-B', '-m', module, 'run'] + arguments,
                    cwd=root / 'source', start_new_session=True, env=dict(os.environ, CUDA_VISIBLE_DEVICES=base.hot.UUIDS[shard],
                        PYTHONPATH=str(root / 'source'), HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1',
                        MKL_NUM_THREADS='1', TOKENIZERS_PARALLELISM='false', PYTHONDONTWRITEBYTECODE='1'),
                    stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
                identity = base.process_identity(Path('/proc') / str(child.pid))
                children[shard] = child, identity
                attempted.add(shard)
                launch = dict(identity=identity, uuid=base.hot.UUIDS[shard], started_unix=time.time(), controller=str(CONTROL))
                base.write(root / f'LAUNCH_{shard}.json', launch)
                base.write(CONTROL / f'LAUNCH_{shard}.json', launch)
            base.exporter.replace_json(CONTROL / 'STATUS.json', dict(observed_unix=time.time(), launched_shards=sorted(children),
                pending_shards=sorted(set(range(8)) - attempted), returncodes={str(shard): child.poll() for shard, (child, identity) in children.items()}))
            if len(attempted) == 8 and all(child.poll() is not None for child, identity in children.values()):
                status = 'COMPLETE' if all(child.returncode == 0 for child, identity in children.values()) else 'NATIVE_FAILURE'
                break
            time.sleep(10)
        else:
            status = 'INHERITED_HARD_GUARD'
    except BaseException as error:
        base.write(CONTROL / 'FAILED.json', dict(type=type(error).__name__, message=str(error)))
        raise
    finally:
        for child, identity in children.values():
            base.stop_owned(child, identity)
        for log in logs:
            log.close()
        for shard in children:
            root = target(shard)[0]
            try:
                base.write(CONTROL / f'RELEASE_{shard}.json', base.scan(shard, root / 'SERVICE_IDENTITY.json'))
            except Exception as error:
                base.write(CONTROL / f'RELEASE_{shard}.json', dict(clear=False, error=str(error)))
        base.write(CONTROL / 'TERMINAL.json', dict(status=status, finished_unix=time.time(), lifetime=lifetime))
        lock.close()


if __name__ == '__main__':
    watch()
