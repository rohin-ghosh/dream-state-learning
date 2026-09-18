"""Reconstruct only lost control updates from a durable optimizer/RNG checkpoint."""

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import time

from gpu import orch_combined_l1_continual_run as run
from gpu.orch_combined_l1_continual_guard import admit_devices, port
from organism_v6 import orch_combined_l1_continual as policy


def compare(previous, actual):
    assert all(previous[key] == actual[key] for key in ('update', 'rows', 'loss', 'reference',
        'supervised', 'local_active', 'corpus_version')), 'control_reconstruction_observable_mismatch'


def recover(root):
    import json
    assert root == run.ROOT and os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    run.validate(root)
    full = policy.verify_checkpoint(root / 'FULL/checkpoints/000001024')
    off = policy.verify_checkpoint(root / 'OFF/checkpoints/000000896')
    assert full['metadata']['update'] == 1024 and off['metadata']['update'] == 896
    assert not (root / 'OFF/checkpoints/000001024').exists()
    backup = root / 'STALE_ABORT_FAILURE'
    backup.mkdir(exist_ok=False)
    for name in ('ABORT.json', 'TERMINAL.json', 'OFF/RANK0_LOSSES_000000896.jsonl',
                 'OFF/RANK0_LOADED_000000896.json'):
        source = root / name
        if source.exists():
            destination = backup / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            os.rename(source, destination)
    old_log = backup / 'OFF/RANK0_LOSSES_000000896.jsonl'
    previous = {record['update']: record for record in map(json.loads, old_log.read_text().splitlines())}
    assert set(previous) == set(range(897, 1014))
    assert run.read(root / 'WINDOWS/000000896.json')['end_update'] == 1024
    run.write(root / 'WINDOWS/000001024.json', dict(stop=True, reason='paired_control_reconstruction'))
    admit_devices(root, (3,), 'CONTROL_RECONSTRUCT_ADMISSION')
    log = (root / 'CONTROL_RECONSTRUCT.log').open('x')
    command = [run.PYTHON, '-B', '-m', run.PROGRAM, 'train', '--root', str(root), '--arm', 'OFF',
        '--rank', '0', '--port', str(port()), '--world-size', '1', '--index', '3',
        '--resume', str(root / 'OFF/checkpoints/000000896')]
    child = subprocess.Popen(command, cwd=root / 'source', env=dict(os.environ,
        CUDA_VISIBLE_DEVICES=run.DEVICES[3], PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='2'),
        stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    identity = run.common.process_identity(child.pid)
    run.write(root / 'CONTROL_RECONSTRUCT_START.json', dict(pid=child.pid, identity=identity, command=command,
        logical_resume=896, expected_reconstructed_updates=117, new_updates=11, full_checkpoint_untouched=True,
        no_from_scratch_reset=True, started_unix=time.time()))
    checked = set()
    try:
        while child.poll() is None:
            path = root / 'OFF/RANK0_LOSSES_000000896.jsonl'
            if path.exists():
                for line in path.read_text().splitlines():
                    try:
                        actual = json.loads(line)
                    except json.JSONDecodeError:
                        break
                    if actual['update'] in previous:
                        compare(previous[actual['update']], actual)
                        checked.add(actual['update'])
            assert time.time() < run.read(root / 'LIFETIME.json')['native_deadline_unix']
            time.sleep(1)
        assert child.returncode == 0 and checked == set(previous)
        restored = policy.verify_checkpoint(root / 'OFF/checkpoints/000001024')
        assert policy.pair_boundary(full['metadata'], restored['metadata']) == 1024
        run.write(root / 'CONTROL_RECONSTRUCT_COMPLETE.json', dict(status='PASS', update=1024,
            observably_identical_replayed_updates=len(checked), additional_physical_updates=117,
            original_unsaved_tensor_identity_unavailable=True,
            full_sha256=run.sha(root / 'FULL/checkpoints/000001024/COMMIT.json'),
            off_sha256=run.sha(root / 'OFF/checkpoints/000001024/COMMIT.json'),
            native_generation=0, source_rows_unchanged=True, finished_unix=time.time()))
    except BaseException as error:
        run.write(root / 'CONTROL_RECONSTRUCT_FAILED.json', dict(type=type(error).__name__, message=str(error),
            checked=len(checked), finished_unix=time.time()))
        raise
    finally:
        run.common.stop_owned(child, identity)
        log.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    options = parser.parse_args()
    recover(options.root)
