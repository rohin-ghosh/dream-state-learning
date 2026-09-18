"""One fresh admission after an exited transient process blocked before launch."""

from copy import deepcopy
import os
from pathlib import Path
import shutil
import subprocess
import time
import uuid

import r188_receive as receiving


def eligible(report, launched, pid_present):
    receiving.require(not launched, 'never_retry_a_launched_or_unknown_native')
    receiving.require(report['clear'] is False and report['scanner_euid'] == 0
        and report['gpu']['uuid'] == receiving.DEVICES[6][0]
        and report['gpu']['memory_used_mib'] == 0 and report['gpu']['utilization_percent'] == 0,
        'exact_empty_GPU6_prelaunch_failure')
    receiving.require(report['blocking_reasons'] == ['process_identity_drift:1980126']
        and not pid_present, 'exact_transient_process_is_gone_not_ignored')


def main():
    receiving.check_host()
    output = receiving.HOME / 'receiving3v2'
    old = output / 'control'
    ready = receiving.read(output / 'PREPARED.json')
    report = receiving.read(old / 'ADMISSION.json')
    eligible(report, (old / 'LAUNCH.json').exists() or (old / 'CONTAINMENT_VERIFIED.json').exists(),
        Path('/proc/1980126').exists())
    dispatch = receiving.read(output / 'DISPATCHED.json')
    receiving.require(not Path('/proc', str(dispatch['supervisor_pid'])).exists(), 'failed_supervisor_exited')
    control = output / 'control_admission2'
    control.mkdir(exist_ok=False)
    shutil.copyfile(old / 'PLAN.json', control / 'PLAN.json')
    allocation = receiving.read(old / 'ALLOCATION.json')
    allocation['declared_unix'] = time.time()
    receiving.write(control / 'ALLOCATION.json', allocation)
    guard = deepcopy(receiving.read(old / 'GUARD.json'))
    receiving.require({str(path.relative_to(ready['source_root'])): receiving.sha(path)
        for path in Path(ready['source_root']).rglob('*.py')} == guard['source_pins'],
        'unchanged_tested_runtime_source')
    guard.update(plan_path=str(control / 'PLAN.json'), attempt_dir=str(control),
        allocation_path=str(control / 'ALLOCATION.json'), allocation_sha256=receiving.sha(control / 'ALLOCATION.json'))
    guard['device_containment']['unit'] = 'orch-r136-native-' + uuid.uuid4().hex
    receiving.write(control / 'GUARD.json', guard)
    command = [str(receiving.PYTHON), '-B', '-m', receiving.MODULE, 'contained-supervise',
        '--config', str(control / 'GUARD.json')]
    receiving.write(control / 'FRESH_ADMISSION_REASON.json', dict(
        previous_admission_sha256=receiving.sha(old / 'ADMISSION.json'), transient_pid=1980126,
        transient_process_absent=True, previous_native_not_launched=True,
        original_clear_gate_unchanged=True, observed_unix=time.time(), command=command))
    with (control / 'SUPERVISOR.log').open('x') as log:
        process = subprocess.Popen(command, cwd=ready['source_root'], stdin=subprocess.DEVNULL,
            stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
            env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
                PYTHONPATH=ready['source_root'], OMP_NUM_THREADS='1', MKL_NUM_THREADS='1'))
    receiving.write(control / 'DISPATCHED.json', dict(supervisor_pid=process.pid, command=command,
        observed_unix=time.time(), no_retry=True, status='DISPATCHED_NOT_LOADED'))
    print(process.pid)


if __name__ == '__main__':
    main()
