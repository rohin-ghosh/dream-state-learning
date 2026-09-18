"""One guarded Astra7 birth; same confinement, no human parent publisher."""

import inspect
from pathlib import Path
import time

from gpu import r205_runtime as runtime
from gpu.r229_p7_inbox import journal_class


MODULE = 'gpu.r229_astra7_runtime'
TRIAL = 'R229_ASTRA7_P7_PARENT'
DEVICE = 'GPU-e7a322fc-fe84-919f-7534-cdfefb6ce1e4'
ORIGINAL_CONTAINED_COMMAND = runtime.contained_command


def contained_command(config_path, mode):
    from gpu import orch_r125_continual_guard as guard
    command = ORIGINAL_CONTAINED_COMMAND(config_path, mode)
    if mode == 'child':
        config, plan = guard.validate(config_path)
        remaining = int(min(plan['hard_end_unix'], plan['lease_end_unix'] - 600) - time.time() - 15)
        positions = [index for index, value in enumerate(command) if value.startswith('--property=RuntimeMaxSec=')]
        if len(positions) != 1 or not 30 < remaining <= 21600:
            raise ValueError('Astra7_bound_actual_operator_and_lease_deadline')
        command[positions[0]] = '--property=RuntimeMaxSec=' + str(remaining)
    return command


def preadmitted_report(config_path):
    from gpu import orch_r125_continual_guard as guard
    config, plan = guard.validate(config_path)
    admission = runtime.native.read(Path(config['attempt_dir']) / 'PRE_SERVICE_ADMISSION.json')
    if (admission['guard_sha256'] != runtime.native.sha(config_path)
            or not 0 <= time.time() - admission['verified_unix'] <= 120):
        raise ValueError('Astra7_fresh_source_bound_privileged_admission_required')
    report = admission['report']
    if report['scanner_euid'] != 0 or not report['clear'] or report['blocking_reasons']:
        raise ValueError('Astra7_actual_privileged_clear_admission_required')
    return report


def supervise_owned(config_path):
    from gpu import orch_r125_continual_guard as guard
    source = inspect.getsource(guard.supervise)
    original = 'report = json.loads(subprocess.check_output(command, text=True, timeout=100))'
    if source.count(original) != 1 or source.count("'gpu.orch_r125_continual_guard'") != 2:
        raise ValueError('Astra7_exact_tested_admission_and_entrypoint_seams')
    source = source.replace(original, 'report = preadmitted_report(config_path)')
    source = source.replace("'gpu.orch_r125_continual_guard'", repr(MODULE))
    namespace = dict(guard.supervise.__globals__, preadmitted_report=preadmitted_report)
    exec(compile(source, __file__ + ':preadmitted_entrypoint', 'exec'), namespace)
    return namespace['supervise'](config_path)


def main():
    runtime.MODULE = MODULE
    runtime.DEVICES = {1: (DEVICE, '0000:52:00.0')}
    runtime.TRIALS = (TRIAL,)
    runtime.ControlJournal = journal_class(runtime.ControlJournal)
    runtime.receive_peer = lambda driver: None
    runtime.supervise_owned = supervise_owned
    runtime.contained_command = contained_command
    runtime.main()


if __name__ == '__main__':
    main()
