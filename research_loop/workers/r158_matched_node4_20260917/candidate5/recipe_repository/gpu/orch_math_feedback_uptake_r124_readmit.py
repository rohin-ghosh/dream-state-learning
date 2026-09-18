"""One administrative readmission after a proven input-free failed scan."""

import errno
import fcntl
import os
from pathlib import Path
from types import FunctionType

from gpu import orch_math_feedback_uptake_r124_readout as run


ATTEMPT = 'admission_attempt2'
EXPECTED_ADMISSION = '0839d755c573997ef06b77cb78dc81bc657744d5a217fc2a38db216b54cfbddb'
EXPECTED_PLAN = '3d387dd15e2424871163773b6d7e97441cb51a60278487ef64e25486cb56d80e'
EXPECTED_RELEASE = '05ea4c1c6d5a232c45c889c0bcc5de4dcc3a3ab7329144116b2128e7c59a0d8a'


def prove_absent(pid):
    try:
        descriptor = os.pidfd_open(pid)
    except OSError as error:
        run.require(error.errno == errno.ESRCH and not Path(f'/proc/{pid}').exists(), 'exact_process_exit_required')
        return dict(pid=pid, pidfd_errno=error.errno, proc_absent=True)
    else:
        os.close(descriptor)
        raise ValueError('live_or_reused_PID_no_readmission')


def no_input(root, counters):
    run.require(run.read(root / 'COUNTERS.json') == counters, 'unchanged_original_counters')
    for name in ('LAUNCH.json', 'native.log', 'LIFE.lock', 'LOADED.json', 'MOUNTED_BEFORE.json',
                 'PAIRED_PROBE_FINISHED.json', 'TERMINAL.json'):
        run.require(not (root / name).exists(), 'pre_model_only:' + name)
    for pattern in ('reservations/*.json', 'paired_DEV/**/*', 'cycle*', 'sealed/**/*'):
        run.require(not any(root.glob(pattern)), 'no_input_or_reserved_task:' + pattern)


def receipt_path(root, path):
    path = Path(path)
    if path in (root / 'ADMISSION.json', root / 'GUARD_STARTED.json'):
        return root / ATTEMPT / path.name
    return path


def execute():
    run.configure()
    root = run.ROOT / 'A2'
    run.require(run.sha(root / 'PLAN.json') == EXPECTED_PLAN, 'same_plan')
    run.require(run.sha(root / 'RELEASED.json') == EXPECTED_RELEASE, 'same_release')
    run.require(run.sha(root / 'ADMISSION.json') == EXPECTED_ADMISSION, 'preserved_failed_admission')
    plan = run.validate(root)
    report = run.read(root / 'ADMISSION.json')
    run.require(report['clear'] is False and report['blocking_reasons'] ==
        ['process_identity_drift:3950956', 'process_identity_drift:3950958'], 'only_exact_prior_drift_failure')
    with (root / 'READMISSION.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        no_input(root, plan['contract']['inherited_counters'])
        evidence = [prove_absent(pid) for pid in (3950703, 3950956, 3950958)]
        target = root / ATTEMPT
        target.mkdir(exist_ok=False)
        run.write(target / 'PREMODEL_PROOF.json', dict(exited=evidence,
            failed_admission=run.ref(root / 'ADMISSION.json'), original_guard=run.ref(root / 'GUARD_STARTED.json'),
            plan=run.ref(root / 'PLAN.json'), release=run.ref(root / 'RELEASED.json'),
            counters=run.read(root / 'COUNTERS.json'), source=run.ref(Path(__file__)),
            no_model_dispatch=True, no_task_reservations=True, scanner_unchanged=True,
            policy='ONE_FRESH_ADMINISTRATIVE_ADMISSION_NOT_MODEL_INPUT_RETRY'))
        def write(path, data):
            run.write(receipt_path(root, path), data)
        namespace = dict(run.old.guard.__globals__, write=write)
        guard = FunctionType(run.old.guard.__code__, namespace, 'guard', run.old.guard.__defaults__)
        guard(root)


if __name__ == '__main__':
    execute()
