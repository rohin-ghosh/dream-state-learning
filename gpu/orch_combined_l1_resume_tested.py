"""Resume the last tested immutable source immediately after control recovery."""

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import time

from gpu import orch_combined_l1_continual_run as run
from organism_v6 import orch_combined_l1_continual as policy


def resume(root):
    assert root == run.ROOT and os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    prepared = run.validate(root)
    assert prepared['source_sha256'] == '80176fbe9effcaccf77c62d77706ba1ff33f5baaea591e554ebd86ea34709f5a'
    assert run.sha(root / 'READY.json') == run.read(root / 'PUBLICATION.json')['ready_sha256']
    run.write(root / 'TESTED_RESUME_QUEUED.json', dict(pid=os.getpid(), update=1024,
        source_sha256=prepared['source_sha256'], wait_reason='CONTROL1024_MATCHED_DURABLE_STATE_ONLY',
        decoder_or_readout_gate=False, queued_unix=time.time()))
    while not (root / 'CONTROL_RECONSTRUCT_COMPLETE.json').exists():
        assert not (root / 'CONTROL_RECONSTRUCT_FAILED.json').exists(), 'reconstruction_failed_no_retry'
        assert time.time() < run.read(root / 'LIFETIME.json')['native_deadline_unix']
        time.sleep(1)
    receipt = run.read(root / 'CONTROL_RECONSTRUCT_COMPLETE.json')
    assert receipt['status'] == 'PASS'
    metadata = [policy.verify_checkpoint(root / arm / 'checkpoints/000001024')['metadata'] for arm in policy.ARMS]
    assert policy.pair_boundary(*metadata) == 1024
    for attempt in range(90):
        workers = []
        for folder in Path('/proc').glob('[0-9]*'):
            try:
                arguments = (folder / 'cmdline').read_bytes().split(b'\0')
            except (FileNotFoundError, PermissionError, ProcessLookupError):
                continue
            if str(root).encode() in arguments and b'gpu.orch_combined_l1_continual_run' in arguments:
                workers.append(folder.name)
        if not workers:
            break
        time.sleep(1)
    assert not workers, 'own_previous_native_not_exited'
    backup = root / 'TESTED_RESUME_1024_PRIOR_CONTROLLER'
    backup.mkdir(exist_ok=False)
    for name in ('ABORT.json', 'TERMINAL.json', 'ADMISSION_ATTEMPTS'):
        if (root / name).exists():
            os.rename(root / name, backup / name)
    for path in root.glob('INITIAL_ADMISSION_*.json'):
        shutil.copyfile(path, backup / path.name)
    log = (root / 'GUARDIAN_TESTED_RESUME_1024.log').open('x')
    command = [run.PYTHON, '-B', '-m', 'gpu.orch_combined_l1_continual_guard',
               '--root', str(root), '--resume', '1024']
    child = subprocess.Popen(command, cwd=root / 'source', env=dict(os.environ,
        CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1'), stdout=log, stderr=subprocess.STDOUT,
        start_new_session=True)
    run.write(root / 'TESTED_RESUME_STARTED.json', dict(pid=child.pid,
        identity=run.common.process_identity(child.pid), command=command,
        source_sha256=prepared['source_sha256'], update=1024, started_unix=time.time(),
        native_updates_not_yet_asserted=True, no_new_source_deployment=True))
    log.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    options = parser.parse_args()
    resume(options.root)
