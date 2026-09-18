"""One explicit clean-expiry rearm, preserving the prior immutable successor."""

import argparse
from copy import deepcopy
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import time
import uuid


HERE = Path(__file__).resolve().parent
PRIOR = Path('/localhome/local-rohing/orch_r179_node1_20260917_attempt2')
DESTINATION = Path('/localhome/local-rohing/orch_r179_node1_20260917_attempt3')
PRIOR_OPERATOR_SHA = 'fc960529e505d79e66ec92715535f770fc22a717210ec91c9dcfe0aea5775a87'
LANES = (2, 5, 6)


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def clean_expiry(physical, names, expired, operator_alive, remaining):
    require(physical in LANES, 'only_remaining_learning_lives')
    require(not operator_alive and remaining <= 0, 'prior_waiter_still_live_or_in_bound')
    require('NO_BOUNDARY.json' in names and expired.get('original_left_running') is True,
            'explicit_clean_timeout_receipt_required')
    forbidden = {'BOUNDARY.json', 'BOUNDARY_RECEIVING_CPU.json', 'RETIREMENT_STARTED.json',
                 'RETIRED.json', 'DISPATCHED.json', 'LOADED_RECEIPT.json', 'HANDOFF_COMPLETE.json'}
    require(not forbidden.intersection(names) and not any(name.startswith('FAILURE_') for name in names),
            'no_boundary_transaction_or_failure_replay')


def operator():
    require(HERE == DESTINATION / 'operator', 'immutable_new_operator_namespace')
    specification = importlib.util.spec_from_file_location('r179_rearm_operator', HERE / 'node1_operator.py')
    loaded = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(loaded)
    require(loaded.REMOTE == DESTINATION, 'new_epoch_without_replacing_prior_attempt')
    loaded.authorize()
    require(loaded.sha(PRIOR / 'operator/node1_operator.py') == PRIOR_OPERATOR_SHA, 'prior_operator_exact_bytes')
    return loaded


def old_lock(physical):
    path = PRIOR / ('lane' + str(physical) + '.lock')
    descriptor = os.open(path, os.O_RDWR | os.O_NOFOLLOW)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(os.fstat(descriptor).st_ino == path.stat().st_ino, 'same_prior_owner_lock_inode')
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def expired_request(loaded, physical):
    output = PRIOR / 'lanes' / ('lane' + str(physical))
    armed = loaded.read(output / 'ARMED.json')
    process = Path('/proc') / str(armed['operator_pid'])
    try:
        alive = (process / 'stat').read_text().rsplit(') ', 1)[1].split()[0] not in ('Z', 'X')
    except (FileNotFoundError, ProcessLookupError):
        alive = False
    clean_expiry(physical, {path.name for path in output.iterdir()},
                 loaded.read(output / 'NO_BOUNDARY.json') if (output / 'NO_BOUNDARY.json').exists() else {},
                 alive, armed['deadline_monotonic'] - time.monotonic())
    request = loaded.read(output / 'STAGED.json')
    require(request['operator_sha256'] == PRIOR_OPERATOR_SHA, 'original_preparation_operator')
    require(request['source_root'] == str(output / 'source'), 'reuse_exact_prepared_source')
    return output, request


def prepare(physical):
    require(physical in LANES, 'only_remaining_learning_lives')
    loaded = operator()
    descriptor = old_lock(physical)
    try:
        old_output, previous = expired_request(loaded, physical)
        base = loaded.legacy()
        life, config, plan, imported, pair, device = loaded.original_binding(base, physical)
        require(pair == previous['processes'] and device == previous['device'], 'exact_original_owner_and_device_revalidation')
        require(time.time() + 600 < plan['hard_end_unix'], 'unchanged_original_wall')
        require(loaded.sha(previous['new_config']) == previous['new_config_sha256'], 'prior_prepared_guard_pin')
        proof = loaded.read(old_output / 'SOURCE_PROOF.json')
        require(loaded.sha(old_output / 'SOURCE_PROOF.json') == previous['source_proof_sha256'], 'prior_source_closure_proof')
        require(loaded.source_inventory(proof['original_source']) == proof['before']
                and loaded.source_inventory(proof['successor_source']) == proof['after'], 'both_immutable_source_closures')
        require(loaded.sha(old_output / 'RECEIVING_CPU.json') == previous['receiving_cpu_sha256'], 'prior_actual_receiving_CPU_pin')
        source = Path(previous['source_root'])
        entry = base.verify_resume_entrypoint(source)
        require(entry == previous['entrypoint'], 'unchanged_normal_saved_resume')
        output = DESTINATION / 'lanes' / ('lane' + str(physical))
        require(not output.exists(), 'one_explicit_rearm_namespace_no_retry')
        output.mkdir(parents=True)
        loaded.write(output / 'SOURCE_PROOF.json', proof)
        control = output / 'control'
        control.mkdir()
        proposed = base.relocated_plan(plan, source)
        require(proposed == loaded.read(Path(previous['new_config']).parent / 'PLAN.json'), 'identical_plan_and_original_walls')
        loaded.write(control / 'PLAN.json', proposed)
        allocation = loaded.read(config['allocation_path'])
        require(allocation['plan_sha256'] == config['plan_sha256'], 'existing_allocation_binding')
        allocation.update(plan_sha256=loaded.sha(control / 'PLAN.json'), r179_scope_sha256=loaded.SCOPE_SHA,
                          r179_cpu_main_sha256=loaded.MAIN_CPU_SHA, r179_operator_cpu_sha256=loaded.sha(HERE / 'LOCAL_CPU.json'))
        loaded.write(control / 'ALLOCATION.json', allocation)
        updated = deepcopy(config)
        updated.update(attempt_dir=str(control), resume=True, plan_path=str(control / 'PLAN.json'),
                       plan_sha256=loaded.sha(control / 'PLAN.json'), allocation_path=str(control / 'ALLOCATION.json'),
                       allocation_sha256=loaded.sha(control / 'ALLOCATION.json'), source_pins=loaded.source_pins(proof['after']))
        updated['device_containment']['unit'] = 'orch-r136-native-' + uuid.uuid4().hex
        loaded.write(control / 'GUARD.json', updated)
        subprocess.run([loaded.PYTHON, '-B', '-c',
                        'from gpu.orch_r125_continual_guard import validate;import sys;validate(sys.argv[1])',
                        str(control / 'GUARD.json')], cwd=source, env=loaded.environment(source), check=True, timeout=120)
        receiving = subprocess.run([loaded.PYTHON, '-B', str(HERE / 'receiving_cpu.py'), str(source), str(output)],
                                   cwd=source, env=loaded.environment(source), text=True, capture_output=True, timeout=120)
        require(receiving.returncode == 0, 'fresh_receiving_CPU_required_before_any_signal')
        cpu = json.loads(receiving.stdout)
        require(cpu['passed'] >= 3 and cpu['cuda_initialized'] is False
                and cpu['native_sha256'] == proof['after'][loaded.NATIVE]['sha256']
                and cpu['policy_sha256'] == loaded.POLICY_SHA, 'fresh_receiving_CPU_exact_prepared_source')
        loaded.write(output / 'RECEIVING_CPU.json', cpu)
        require(loaded.original_binding(base, physical)[4:] == (pair, device), 'owner_revalidation_after_CPU')
        request = dict(status='STAGED_RECEIVING_CPU_PASS', physical=physical, node='a100',
                       original_guard=life['original_guard'], original_plan=life['original_plan'], processes=pair,
                       device=device, original_source=previous['original_source'], source_root=str(source),
                       new_config=str(control / 'GUARD.json'), new_config_sha256=loaded.sha(control / 'GUARD.json'),
                       source_proof_sha256=loaded.sha(output / 'SOURCE_PROOF.json'),
                       receiving_cpu_sha256=loaded.sha(output / 'RECEIVING_CPU.json'),
                       operator_sha256=loaded.sha(HERE / 'node1_operator.py'), scope_sha256=loaded.SCOPE_SHA,
                       entrypoint=entry, handler=base.launcher('a100', config), old_plan=plan, staged_unix=time.time())
        loaded.write(output / 'STAGED.json', request)
        receipt = dict(physical=physical, status='CLEAN_TIMEOUT_REARM_PREPARED_NO_SIGNALS',
                       prior_timeout_sha256=loaded.sha(old_output / 'NO_BOUNDARY.json'),
                       previous_source_root=str(source), source_reused_not_repatched=True,
                       receiving_cpu_sha256=request['receiving_cpu_sha256'], receiving_cpu_passed=cpu['passed'],
                       cuda_initialized=False, operator_sha256=request['operator_sha256'],
                       original_hard_end_unix=plan['hard_end_unix'], signals_sent=0, model_calls=0,
                       observed_unix=time.time(), prior_attempt_preserved=True)
        loaded.write(output / 'REARM_PREPARED.json', receipt)
        return receipt
    finally:
        os.close(descriptor)


def handoff(physical):
    require(physical in LANES, 'only_remaining_learning_lives')
    loaded = operator()
    descriptor = old_lock(physical)
    try:
        expired_request(loaded, physical)
        return loaded.handoff(physical, 5400)
    finally:
        os.close(descriptor)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'handoff'))
    parser.add_argument('--physical', type=int, choices=LANES, required=True)
    arguments = parser.parse_args()
    print(json.dumps(prepare(arguments.physical) if arguments.action == 'prepare' else handoff(arguments.physical)))


if __name__ == '__main__':
    main()
