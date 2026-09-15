"""Fresh, parent-free held readouts of a durable continual checkpoint."""

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import time
from types import SimpleNamespace

from gpu import orch_combined_l1_continual_run as run
from gpu import orch_combined_l1_run as combined
from organism_v6 import orch_combined_l1_continual as policy


def readout(root, arm, update):
    prepared = run.validate(root)
    checkpoint = root / arm / 'checkpoints' / f'{update:09d}'
    metadata = policy.verify_checkpoint(checkpoint)['metadata']
    evaluation = root / 'EVALUATION'
    cell = 'COMBINED_' + arm
    binding = run.read(evaluation / cell / 'fit/COMPLETE.json')
    assert binding['output_adapter'] == metadata['adapter'] and binding['process'] == metadata['process']
    assert binding['checkpoint_commit_sha256'] == run.sha(checkpoint / 'COMMIT.json')
    combined.ROOT = evaluation
    combined.LAYOUT = SimpleNamespace(updates=update)
    combined.DEVICES = {'COMBINED_FULL': (2, run.DEVICES[2]), 'COMBINED_OFF': (3, run.DEVICES[3])}
    combined.validate_inputs = lambda unused: prepared
    combined.readout(evaluation, cell)


def launch_readouts(root, update, lifetime):
    evaluation = root / 'EVALUATION'
    evaluation.mkdir(exist_ok=False)
    for name in ('COHORT.json', 'ROUTE_COHORT.json', 'LEGACY_READOUT.json', 'PREPARE.json', 'LIFETIME.json'):
        shutil.copyfile(root / name, evaluation / name)
    children, logs = [], []
    try:
        for arm, index in (('FULL', 2), ('OFF', 3)):
            checkpoint = root / arm / 'checkpoints' / f'{update:09d}'
            metadata = policy.verify_checkpoint(checkpoint)['metadata']
            run.write(evaluation / ('COMBINED_' + arm) / 'fit/COMPLETE.json', dict(status='COMPLETE',
                fit_kind='DURABLE_CONTINUAL_CHECKPOINT_NOT_TERMINAL_CORPUS', updates=update,
                input_adapter=run.read(root / 'PREPARE.json')['initial'], output_adapter=metadata['adapter'],
                process=metadata['process'], checkpoint_commit_sha256=run.sha(checkpoint / 'COMMIT.json')))
            report = run.scan(index, root / 'SERVICE_IDENTITY.json')
            run.write(evaluation / f'ADMISSION_{arm}.json', report)
            assert report['clear']
            log = (evaluation / f'{arm}.log').open('x')
            logs.append(log)
            child = subprocess.Popen([run.PYTHON, '-B', '-m', 'gpu.orch_combined_l1_continual_readout',
                '--root', str(root), '--arm', arm, '--update', str(update)], cwd=root / 'source',
                env=dict(os.environ, CUDA_VISIBLE_DEVICES=run.DEVICES[index], PYTHONDONTWRITEBYTECODE='1'),
                stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            children.append((child, run.common.process_identity(child.pid)))
        while any(child.poll() is None for child, identity in children):
            assert time.time() < lifetime['native_deadline_unix'], 'readout_deadline'
            time.sleep(1)
        assert all(child.returncode == 0 for child, identity in children), 'readout_failure_preserved'
    finally:
        for child, identity in children:
            run.common.stop_owned(child, identity)
        for log in logs:
            log.close()
        for arm, index in (('FULL', 2), ('OFF', 3)):
            run.write(evaluation / f'RELEASE_{arm}.json', run.scan(index, root / 'SERVICE_IDENTITY.json'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--arm', choices=policy.ARMS, required=True)
    parser.add_argument('--update', type=int, required=True)
    options = parser.parse_args()
    readout(options.root, options.arm, options.update)
