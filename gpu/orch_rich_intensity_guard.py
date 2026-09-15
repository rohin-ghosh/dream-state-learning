"""Reuse the established global/proc scanner; own only node3 physical0–5."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

from gpu import orch_oracle_repair_guard as existing
from gpu.orch_math_replication_guard import verify_sources
from gpu.orch_math_rich_screen import write
from organism_v6 import orch_rich_intensity as policy


DEVICES = dict(existing.DEVICES)
DEVICES.update({4: 'GPU-f484c608-a2d4-0c26-dee1-a06cc5ae69e4',
                5: 'GPU-bc211959-642d-664b-3581-42a0dbe434e9'})
existing.DEVICES = DEVICES


def scan(index, service):
    policy.allocation(index)
    if os.geteuid() == 0:
        return existing.scan(index, service)
    output = subprocess.check_output(['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=',
        'PYTHONDONTWRITEBYTECODE=1', 'PYTHONPATH=' + str(Path(__file__).resolve().parents[1]),
        'python3', str(Path(__file__).resolve()), '--snapshot-only', '--index', str(index),
        '--service', str(service)], text=True, timeout=60)
    snapshot = json.loads(output)
    assert snapshot['blocking_reasons'] == existing.evaluate(snapshot, index)
    return snapshot


def launch(root, service):
    assert os.geteuid() != 0
    verify_sources(root / 'source', root / 'SOURCE_SHA256.json')
    prepared = json.loads((root / 'prepare/RESULT.json').read_text())
    publication = json.loads((root / 'PUBLICATION.json').read_text())
    assert prepared['status'] == 'PREPARED_NO_MODEL' and prepared['model_calls'] == 0
    assert prepared['base_verification']['verified'] and prepared['tasks_sha256'] == policy.TASKS_SHA
    for relative, expected in publication['files'].items():
        assert hashlib.sha256((root / relative).read_bytes()).hexdigest() == expected
    assert publication['own_cpu_tests_passed'] and publication['dated_builder_publication']
    assert prepared['driver_sha256'] == hashlib.sha256((root / 'source/gpu/orch_rich_intensity_screen.py').read_bytes()).hexdigest()
    assert prepared['policy_sha256'] == hashlib.sha256(Path(policy.__file__).read_bytes()).hexdigest()
    output = root / 'run'
    output.mkdir(exist_ok=False)
    started = time.time()
    deadline = min(started + 7200, publication['original_batch_hard_deadline_unix'])
    assert deadline - started > 300
    assert deadline < existing.LEASE_CUTOFF
    write(output / 'START.json', dict(started_unix=started, hard_deadline_unix=deadline,
        native_deadline_unix=deadline - 240, assigned_gpus=DEVICES, max_calls=1536,
        assigned_gpu_hours_ceiling=12, fits=0, publication=publication,
        original_allocation_started_unix=publication['original_allocation_started_unix']))
    children, logs = [], []
    status = 'FAILED'
    try:
        for index in DEVICES:
            snapshot = scan(index, service)
            write(output / f'PRE_SCAN_{index}.json', snapshot)
            if not snapshot['clear']:
                raise RuntimeError('ownership_scan_blocked:' + str(index) + ':' + str(snapshot['blocking_reasons']))
        for index, uuid in DEVICES.items():
            environment = dict(os.environ, CUDA_VISIBLE_DEVICES=uuid,
                PYTHONPATH=str(root / 'source'), HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', TOKENIZERS_PARALLELISM='false', PYTHONDONTWRITEBYTECODE='1')
            log = (output / f'shard{index}.log').open('x')
            logs.append(log)
            child = subprocess.Popen([existing.PYTHON, '-B', '-m', 'gpu.orch_rich_intensity_screen',
                '--phase', 'screen', '--bundle', existing.BUNDLE, '--model-dir', existing.MODEL,
                '--tasks', str(root / 'TASKS.json'), '--output', str(output / f'shard{index}'),
                '--index', str(index), '--gpu-uuid', uuid, '--deadline', str(deadline - 240)],
                env=environment, cwd=root / 'source', stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            children.append(child)
            write(output / f'LAUNCH_{index}.json', dict(pid=child.pid, index=index, uuid=uuid,
                condition=policy.allocation(index)[0], started_unix=time.time()))
        while any(child.poll() is None for child in children):
            if time.time() >= deadline - 180:
                raise TimeoutError('common_120min_deadline')
            time.sleep(2)
        status = 'COMPLETE' if all(child.returncode == 0 for child in children) else 'SHARD_FAILURE'
    except BaseException as error:
        write(output / 'GUARD_FAILED.json', dict(error_type=type(error).__name__, error=str(error)))
        raise
    finally:
        for child in children:
            existing.stop_owned(child)
        for log in logs:
            log.close()
        write(output / 'RESULT.json', dict(status=status, exit_codes=[child.returncode for child in children],
            finished_unix=time.time(), assigned_gpu_hours=6 * (time.time() - started) / 3600))
        for index in DEVICES:
            write(output / f'RELEASE_{index}.json', scan(index, service))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path)
    parser.add_argument('--service', type=Path, required=True)
    parser.add_argument('--snapshot-only', action='store_true')
    parser.add_argument('--index', type=int, choices=range(6))
    options = parser.parse_args()
    if options.snapshot_only:
        assert os.geteuid() == 0
        print(json.dumps(scan(options.index, options.service)))
    else:
        launch(options.root, options.service)


if __name__ == '__main__':
    main()
