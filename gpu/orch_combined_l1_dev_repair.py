"""Retry only zero-call admission failure; preserve science and require clear scans."""

import argparse
import os
from pathlib import Path
import signal
import subprocess
import time

from gpu import orch_combined_l1_continual_run as run
from gpu import orch_combined_l1_continual_guard as guard
from gpu import orch_combined_l1_dev as dev


def settling_only(report):
    reasons = report['blocking_reasons']
    allowed = ('device_not_idle', 'process_identity_drift:', 'minor_scan_identity_changed:', 'minor_scan_process_drift:')
    return (bool(reasons) and report['gpu']['memory_used_mib'] == 0
        and all(reason == allowed[0] or reason.startswith(allowed[1:]) for reason in reasons)
        and not any(process['gpu_uuid'] == report['gpu']['uuid'] for process in report['compute_processes']))


def admit(root, indexes, label):
    for index in indexes:
        for attempt in range(60):
            report = run.scan(index, root / 'SERVICE_IDENTITY.json')
            run.write(root / 'DEV_REPAIR_ADMISSION' / f'{label}_{index}_{attempt:03d}.json', report)
            if report['clear']:
                assert not report['blocking_reasons']
                break
            assert settling_only(report), ('actual_gpu_ownership_or_memory_block', index, report['blocking_reasons'])
            assert attempt < 59, 'strict_clear_not_obtained'
            time.sleep(1)


def active(identity):
    try:
        return run.common.process_identity(identity['pid']) == identity
    except (FileNotFoundError, ProcessLookupError):
        return False


def repair(root, pid):
    ready = run.read(root / 'DEV_REPAIR_READY.json')
    assert ready['source_sha256'] == run.sha(__file__) and ready['status'] == 'PASS'
    assert run.read(root / 'DEV_REPAIR_PUBLICATION.json')['ready_sha256'] == run.sha(root / 'DEV_REPAIR_READY.json')
    prepared = run.validate(root)
    failed = dev.evaluation_root(root, 'INTERMEDIATE', 1636)
    result = run.read(failed / 'RESULT.json')
    assert result['actual_reserved_calls'] == 0 and result['jobs'] == []
    assert not list(failed.glob('*/*/readout/CALL_*.json'))
    assert not list(failed.glob('*_START.json'))
    descriptor = os.pidfd_open(pid)
    try:
        identity = run.common.process_identity(pid)
        command = Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')
        assert identity['uid'] == os.getuid() and str(root).encode() in command
        assert b'gpu.orch_combined_l1_continual_guard' in command
        run.write(root / 'DEV_REPAIR_REQUEST.json', dict(identity=identity, requested_unix=time.time(),
            action='GUARDIAN_ONLY_CHECKPOINT_THEN_READ_SAVED1636', workers_signalled=[],
            failed_zero_call_result_sha256=run.sha(failed / 'RESULT.json'), source_sha256=prepared['source_sha256']))
        assert run.common.process_identity(pid) == identity
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
    finally:
        os.close(descriptor)
    while active(identity):
        assert time.time() < run.read(root / 'LIFETIME.json')['native_deadline_unix']
        time.sleep(1)
    terminal = run.read(root / 'TERMINAL.json')
    assert terminal['status'] == 'TRAINING_CHECKPOINTED'
    latest = max((root / 'PAIRED_BOUNDARIES').glob('*.json'))
    update = run.read(latest)['update']
    metadata = [run.policy.verify_checkpoint(root / arm / 'checkpoints' / f'{update:09d}')['metadata'] for arm in run.policy.ARMS]
    assert run.policy.pair_boundary(*metadata) == update
    preserved = {arm: run.sha(root / arm / 'checkpoints' / f'{update:09d}/COMMIT.json') for arm in run.policy.ARMS}
    archive = root / 'PRECALL_FAILURES/INTERMEDIATE_000001636'
    archive.parent.mkdir(exist_ok=True)
    assert not archive.exists()
    os.rename(failed, archive)
    guard.admit_devices = admit
    evaluation = dev.evaluation_root(root, 'INTERMEDIATE', 1636)
    try:
        dev.launch(root, 'INTERMEDIATE', 1636, run.read(root / 'LIFETIME.json'))
    except BaseException as error:
        run.write(root / 'DEV_REPAIR_DISPATCH_EXCEPTION.json', dict(type=type(error).__name__,
            message=str(error), resume_preserved_training=True, time_unix=time.time()))
    assert preserved == {arm: run.sha(root / arm / 'checkpoints' / f'{update:09d}/COMMIT.json') for arm in run.policy.ARMS}
    run.write(root / 'DEV_REPAIR_COMPLETE.json', dict(readout_checkpoint=1636, retained_training_checkpoint=update,
        checkpoint_sha256=preserved, immutable_failed_attempt=str(archive), evaluation=str(evaluation),
        logical_updates_discarded=0, reset=False, finished_unix=time.time()))
    backup = root / 'DEV_REPAIR_PRIOR_CONTROLLER'
    backup.mkdir(exist_ok=False)
    for name in ('TERMINAL.json', 'ABORT.json', 'ADMISSION_ATTEMPTS'):
        if (root / name).exists():
            os.rename(root / name, backup / name)
    stream = (root / f'GUARDIAN_AFTER_DEV_REPAIR_{update:09d}.log').open('x')
    child = subprocess.Popen([run.PYTHON, '-B', '-m', 'gpu.orch_combined_l1_continual_guard',
        '--root', str(root), '--resume', str(update)], cwd=root / 'source', env=dict(os.environ,
        CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1'), stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
    stream.close()
    run.write(root / 'DEV_REPAIR_RESUMED.json', dict(pid=child.pid, identity=run.common.process_identity(child.pid),
        update=update, source_sha256=prepared['source_sha256'], started_unix=time.time()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--pid', type=int, required=True)
    options = parser.parse_args()
    repair(options.root, options.pid)
