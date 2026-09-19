"""Scoped proven native cold start on the single assigned A10G."""

from pathlib import Path
import time
from types import FunctionType

from gpu import r205_runtime as runtime
from gpu import orch_r125_stream_journal as journal_module


DEVICE = 'GPU-c57b2860-9ba6-74ee-876b-4fa22a10366e'
TRIAL = 'R231_BASE_CURRICULUM_FROM_BIRTH'
POLICY = 'R227_ALL_AUTHENTIC_CHILD_ROWS_V1'
OWNER = 1352


def receiving_command(arguments, mode, deadline, observed):
    result = list(arguments)
    for name in ('User', 'Group'):
        old = '--property=' + name + '=2524'
        runtime.require(result.count(old) == 1, 'one_exact_legacy_owner_binding')
        result[result.index(old)] = '--property=' + name + '=' + str(OWNER)
    if mode == 'child':
        from gpu.r226_caption_runtime import bounded_runtime
        result = bounded_runtime(result, deadline - 15, observed)
    return result


def main():
    runtime.DEVICES = {0: (DEVICE, '0000:4f:00.0')}
    runtime.TRIALS = runtime.TRIALS + (TRIAL,)
    runtime.MODULE = 'gpu.r231_runtime'
    original_install = runtime.install_runtime
    original_command = runtime.contained_command
    original_journal = journal_module.StreamJournal
    original_verifier = runtime.verify_devices
    constants = original_verifier.__code__.co_consts
    runtime.require(constants.count(2524) == 1, 'one_exact_nonroot_UID_check')
    runtime.verify_devices = FunctionType(original_verifier.__code__.replace(
        co_consts=tuple(OWNER if value == 2524 else value for value in constants)),
        original_verifier.__globals__)

    def install(plan):
        runtime.require(plan['think_act_learn']['trial_id'] == TRIAL, 'only_R231_new_base_birth')
        runtime.require(all(scope.get('learn_row_policy') == POLICY for scope in (plan, plan['think_act_learn'])), 'no_semantic_exclusions')
        runtime.receive_peer = lambda driver: None
        original_install(plan)
        journal_module.StreamJournal = original_journal

    def command(config_path, mode):
        from gpu.orch_r125_continual_guard import validate
        config, plan = validate(config_path)
        runtime.require(config['resume'] is False, 'cold_start_never_C2_or_saved_optimizer')
        runtime.require(Path(plan['root']).name == 'raw' and 'orch_r231_curriculum_birth_20260918' in plan['root'], 'new_private_R231_root')
        return receiving_command(original_command(config_path, mode), mode, plan['hard_end_unix'], time.time())

    runtime.install_runtime = install
    runtime.contained_command = command
    runtime.main()


if __name__ == '__main__':
    main()
