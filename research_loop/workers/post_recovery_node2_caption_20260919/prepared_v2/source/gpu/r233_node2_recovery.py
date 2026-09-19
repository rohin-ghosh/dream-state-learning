"""Authorized continuation of kept node2 lives; no new birth or peer wiring."""

import inspect
from pathlib import Path
import time

from gpu import r205_runtime as runtime
from gpu.r213_recovery_runtime import RecoveryJournal


MODULE = 'gpu.r233_node2_recovery'
TARGETS = {
    'orch_r216_C0_20260918_attempt2': (4, 'GPU-d304a15c-516a-16a0-a926-a560304077cc', '0000:ce:00.0'),
    'r213_r226_caption_unparented_fork': (2, 'GPU-d2db2a6a-a308-1782-bf41-e41411d8dc05', '0000:56:00.0'),
    'orch_r229_Astra7_20260918': (1, 'GPU-e7a322fc-fe84-919f-7534-cdfefb6ce1e4', '0000:52:00.0'),
}
POLICY = 'R227_ALL_AUTHENTIC_CHILD_ROWS_V1'


def binding(plan):
    target = TARGETS.get(Path(plan['source_root']).parent.name)
    if target is None or (plan['physical'], plan['gpu_uuid']) != target[:2]:
        raise ValueError('only_authorized_kept_original_node2_slots')
    from organism_v6.orch_r227_learning_policy import SEMANTIC_FILTER_FIELDS
    for scope in (plan, plan['think_act_learn']):
        if scope.get('learn_row_policy') != POLICY or any(key in scope for key in SEMANTIC_FILTER_FIELDS):
            raise ValueError('R227_both_scopes_without_semantic_exclusions')
    return target


def journal_type(plan):
    if binding(plan)[0] == 1:
        from gpu.r229_p7_inbox import journal_class
        return journal_class(RecoveryJournal)
    return RecoveryJournal


def bounded_command(command, plan, now):
    result = list(command)
    positions = [index for index, argument in enumerate(result)
        if argument.startswith('--property=RuntimeMaxSec=')]
    remaining = int(min(plan['hard_end_unix'], plan['lease_end_unix'] - 600) - now - 15)
    if len(positions) != 1 or not 30 < remaining <= plan['lease_end_unix'] - now - 600:
        raise ValueError('fresh_finite_operator_and_existing_lease_bound')
    result[positions[0]] = '--property=RuntimeMaxSec=' + str(remaining)
    return result


def preadmitted_report(config_path):
    from gpu.orch_r125_continual_guard import validate
    config, plan = validate(config_path)
    binding(plan)
    receipt = runtime.native.read(Path(config['attempt_dir']) / 'PRE_SERVICE_ADMISSION.json')
    if (receipt['guard_sha256'] != runtime.native.sha(config_path)
            or not 0 <= time.time() - receipt['verified_unix'] <= 120):
        raise ValueError('fresh_exact_privileged_admission_required')
    report = receipt['report']
    if report['scanner_euid'] != 0 or not report['clear'] or report['blocking_reasons']:
        raise ValueError('privileged_admission_not_clear')
    return report


def supervisor_source(source):
    seam = 'report = json.loads(subprocess.check_output(command, text=True, timeout=100))'
    prebound = """bound = child.read(attempt/'PRE_SERVICE_ADMISSION.json')
        child.require(bound['guard_sha256'] == child.sha(config_path)
            and 0 <= time.time()-bound['verified_unix'] <= 120, 'fresh_bound_privileged_preservice_scan')
        report = bound['report']"""
    if source.count(seam) + source.count(prebound) != 1 or source.count("'gpu.orch_r125_continual_guard'") != 2:
        raise ValueError('existing_tested_guard_seams_only')
    source = source.replace(seam, 'report = preadmitted_report(config_path)')
    return source.replace("'gpu.orch_r125_continual_guard'", repr(MODULE))


def supervise_owned(config_path):
    from gpu import orch_r125_continual_guard as guard
    source = supervisor_source(inspect.getsource(guard.supervise))
    namespace = dict(guard.supervise.__globals__, preadmitted_report=preadmitted_report)
    exec(compile(source, __file__ + ':existing_admission', 'exec'), namespace)
    return namespace['supervise'](config_path)


def main():
    original_install = runtime.install_runtime
    original_command = runtime.contained_command
    runtime.DEVICES = {target[0]: target[1:] for target in TARGETS.values()}

    def install(plan):
        from gpu import orch_r184_think_act_learn as driver
        target = binding(plan)
        original_loop = driver.run_loop
        runtime.ControlJournal = journal_type(plan)
        from gpu.caption_tail_runtime import bind_journal
        runtime.ControlJournal = bind_journal(runtime.ControlJournal, plan)
        runtime.TRIALS = (plan['think_act_learn']['trial_id'],)
        runtime.receive_peer = lambda driver: None
        original_install(plan)
        driver.run_loop = original_loop
        if target[0] == 2:
            from gpu.ny_caption_life import activate
            from gpu.r227_caption_runtime import caption_binding, make_sleep_hook
            _, socket_path = caption_binding(plan)
            runtime.native.NativeChild.sleep = make_sleep_hook(runtime.native.NativeChild.sleep)
            activate(socket_path, max_act_attempts=3)

    def command(config_path, mode):
        from gpu.orch_r125_continual_guard import validate
        _, plan = validate(config_path)
        binding(plan)
        result = original_command(config_path, mode)
        return bounded_command(result, plan, time.time()) if mode == 'child' else result

    runtime.MODULE = MODULE
    runtime.supervise_owned = supervise_owned
    runtime.install_runtime = install
    runtime.contained_command = command
    runtime.main()


if __name__ == '__main__':
    main()
