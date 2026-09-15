"""Finite exact-identity custody for the immutable no-replay continuation."""

import argparse
import fcntl
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from gpu import orch_r108_code_parent_r115_guard as original


def guard(root):
    run = original.run
    plan = original.verify(root)
    run.policy.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'cpu_custody_only')
    source = root / 'source_v2'
    for relative, expected in run.read(root / 'CONT_SOURCE_SHA256.json').items():
        run.policy.require(run.sha(source / relative) == expected, 'immutable_continuation_source')
    prior = run.read(root / 'LAUNCH.json')['identity']
    try:
        alive = original.scanner.pinned.identity(Path('/proc') / str(prior['pid'])) == prior
    except FileNotFoundError:
        alive = False
    run.policy.require(not alive, 'previous_owned_native_exited')
    (root / 'CONT_GUARD_ONCE').mkdir()
    with (Path('/tmp') / ('orch_r115_f3_' + plan['gpu_uuid'] + '.lock')).open('a') as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        for attempt in range(30):
            snapshot = original.scan(root)
            run.write_new(root / 'continuation_admission' / f'SCAN_{attempt:03d}.json', snapshot)
            if snapshot.get('clear') is True:
                break
            time.sleep(10)
        run.policy.require(snapshot['clear'] and snapshot['scanner_euid'] == 0
            and snapshot['gpu']['uuid'] == plan['gpu_uuid'], 'strict_continuation_admission')
        run.write_new(root / 'CONT_ADMISSION.json', snapshot)
        with (root / 'continuation.log').open('x') as stream:
            child = subprocess.Popen([sys.executable, '-B', '-m', 'gpu.orch_r108_code_parent_r115_continue',
                '--root', str(root)], cwd=source, stdin=subprocess.DEVNULL, stdout=stream,
                stderr=subprocess.STDOUT, start_new_session=True,
                env=dict(os.environ, CUDA_VISIBLE_DEVICES=plan['gpu_uuid'], PYTHONPATH=str(source),
                    HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1'))
            identity = original.scanner.pinned.identity(Path('/proc') / str(child.pid))
            run.write_new(root / 'CONT_LAUNCH.json', dict(identity=identity, started_unix=time.time(),
                original_plan_sha256=run.sha(root / 'PLAN.json'),
                source_manifest_sha256=run.sha(root / 'CONT_SOURCE_SHA256.json')))
            while child.poll() is None and time.time() < plan['hard_deadline_unix'] - 5:
                time.sleep(2)
            if child.poll() is None:
                run.policy.require(original.scanner.pinned.identity(Path('/proc') / str(child.pid)) == identity,
                    'exact_owned_continuation_identity')
                os.killpg(child.pid, signal.SIGTERM)
                child.wait(timeout=20)
            run.write_new(root / 'CONT_GUARD_TERMINAL.json', dict(returncode=child.returncode,
                finished_unix=time.time()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    guard(parser.parse_args().root)
