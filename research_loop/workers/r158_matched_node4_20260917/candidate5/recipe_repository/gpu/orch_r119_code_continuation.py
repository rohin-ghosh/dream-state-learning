"""CODE continuation custody exports; original ledger and completed FINAL stay immutable."""

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import time


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def read(path):
    return json.loads(Path(path).read_bytes())


def ref(path):
    path = Path(path).resolve(strict=True)
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def checked(reference):
    require(ref(reference['path']) == reference, 'exact_immutable_reference')
    return read(reference['path'])


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')


def branch_snapshot(root):
    root = Path(root).resolve(strict=True)
    prepared_path = root / 'parallel_v4/proof_recovery_1629/OWNER_PREPARED.json'
    prepared = read(prepared_path)
    require(prepared['root'] == str(root) and prepared['branch'] in ('F3', 'A3'), 'own_CODE_branch')
    envelope = checked(prepared['owner']['handoff'])
    released = checked(envelope['release'])
    boundary = released['native']['boundary']
    plan = read(root / 'PLAN.json')
    require(plan['physical'] == {'F3': 2, 'A3': 6}[prepared['branch']], 'same_CODE_slot')
    preserved = boundary['preserved_files']
    require(all(ref(root / name)['sha256'] == expected for name, expected in preserved.items()),
        'all_original_pending_and_charges_preserved')
    reservations = {str(path.relative_to(root)): ref(path)['sha256']
        for path in (root / 'reservations').glob('*.json')}
    require(reservations == {name: expected for name, expected in preserved.items()
        if name.startswith('reservations/')}, 'exact_original_reservation_set')
    pending = checked(boundary['pending_reference'])
    cursor = checked(boundary['pending_cursor'])
    require(pending['cycle'] == boundary['cycle'] and cursor['next_cycle'] == boundary['next_cycle']
        and boundary['next_cycle'] == boundary['cycle'] + 1, 'unchanged_pending_cursor')
    submission = boundary['pending']['submission']
    require(ref(submission['path']) == submission, 'untrained_submission_preserved_not_resubmitted')
    common = Path(submission['path']).parents[1]
    selected = read(common / 'FINAL_SELECTION.json')
    state = checked(selected['state_reference'])
    require(read(common / 'STATE.json') == state == boundary['state'], 'same_actual_selected_committed_child')
    require(state['checkpoint'] == selected['checkpoint'] and state['generation'] == selected['generation'],
        'selected_generation_checkpoint_match')
    for field in ('path', 'optimizer_path'):
        require(ref(state['checkpoint'][field])['sha256'] == state['checkpoint'][field + '_sha256'],
            'same_saved_child_and_shared_optimizer')
    final_root = root / 'parallel_v4/final_failed_recovery'
    complete = read(final_root / 'COMPLETE.json')
    terminal = read(final_root / 'GUARD_TERMINAL.json')
    final_launch = read(final_root / 'LAUNCH.json')
    require(complete['native_calls'] == complete['completed_calls'] == 8
        and terminal['returncode'] == 0, 'original_FINAL_completed_not_repeated')
    require(not (Path('/proc') / str(final_launch['identity']['pid'])).exists(), 'FINAL_native_exited')
    charges = boundary['charges']
    return dict(schema='R119_CODE_CONTINUATION_POINTERS_V1', branch=prepared['branch'], root=str(root),
        original_plan=ref(root / 'PLAN.json'), original_activation=ref(root / 'SHARED_ACTIVATION.json'),
        original_broker_config=ref(root / 'BROKER_CONFIG.json'), prepared=ref(prepared_path),
        release=deepcopy(envelope['release']), owner_handoff=deepcopy(prepared['owner']['handoff']),
        common_root=str(common), common_pins={name:ref(common / name) for name in
            ('CONFIG.json', 'STATE.json', 'INITIALIZED.json', 'ADOPTION.json')},
        selection=ref(common / 'FINAL_SELECTION.json'), selected_state=selected['state_reference'],
        generation=state['generation'], checkpoint=state['checkpoint'],
        pending_cycle=boundary['cycle'], next_cycle=boundary['next_cycle'],
        pending_reference=boundary['pending_reference'], pending_cursor=boundary['pending_cursor'],
        existing_submission=submission, carry=boundary['carry'],
        cumulative_counts={key:charges[key] for key in ('native_used', 'parent_used')},
        original_bounds={key:plan[key] for key in
            ('started_unix','hard_deadline_unix','lease_end_unix','native_cap','parent_cap','cycles')},
        preserved_files=deepcopy(preserved), final_completed=ref(final_root / 'COMPLETE.json'),
        final_terminal=ref(final_root / 'GUARD_TERMINAL.json'), final_identity=final_launch['identity'],
        final_repeat_allowed=False, independent_optimizer_allowed=False, optimizer_owner='F1',
        status='EXACT_POINTERS_AWAIT_CANONICAL_LEASE_POLICY_AND_NEW_SESSION', observed_unix=time.time())


def effective_plan(original, policy):
    require(policy['train_end_unix'] < policy['hard_end_unix']
        and policy['hard_end_unix'] <= original['lease_end_unix'] - 21600,
        'same_actual_lease_margin')
    require(policy['hard_end_unix'] - policy['train_end_unix'] == 120, 'common_training_reserve120')
    result = deepcopy(original)
    result['hard_deadline_unix'] = policy['hard_end_unix']
    return result


def broker_config(original, policy):
    require(policy['train_end_unix'] < policy['hard_end_unix'], 'common_broker_wall')
    result = deepcopy(original)
    result['deadline_unix'] = policy['train_end_unix']
    return result


def prepare_owner(service, pointers_reference, clock_reference, backend, source_files,
        cpu_tests, wrapper_directory, interpreter, proof_directory):
    from gpu import orch_r119_lease_clock
    from gpu import orch_r119_code_runtime
    service = Path(service)
    require(not service.exists(), 'new_immutable_continuation_namespace')
    pointers = checked(pointers_reference)
    require(service.parents[1] == Path(pointers['root']), 'owned_CODE_service')
    bounds = orch_r119_lease_clock.validate(clock_reference, backend_path=backend['path'])
    original = checked(pointers['original_plan'])
    effective_plan(original, bounds)
    prepared = checked(pointers['prepared'])
    envelope = deepcopy(checked(prepared['owner']['handoff']))
    envelope['prior_envelope'] = prepared['owner']['handoff']
    envelope['lease_policy'] = clock_reference
    envelope['bounds'].update(train_end_unix=bounds['train_end_unix'], hard_end_unix=bounds['hard_end_unix'])
    for key in ('native_used', 'parent_used'):
        require(envelope['bounds'][key] == pointers['cumulative_counts'][key], 'no_counter_reset')
    final_identity = pointers['final_identity']
    envelope['predecessors'].append(dict(pid=final_identity['pid'], start_ticks=int(final_identity['start_ticks']),
        boot_id=final_identity['boot_id']))
    envelope['completed_final'] = dict(complete=pointers['final_completed'], terminal=pointers['final_terminal'])
    runtime = dict(schema='R119_CODE_LEASE_RUNTIME_V1', service=str(service), root=pointers['root'],
        pointers=pointers_reference, lease_policy=clock_reference, backend=backend, source_files=source_files,
        cpu_tests=cpu_tests, source_root=prepared['owner']['cwd'], wrapper_directory=str(wrapper_directory),
        interpreter=interpreter, common_root=pointers['common_root'], handoff=pointers['release'],
        next_cycle=pointers['next_cycle'], train_end_unix=bounds['train_end_unix'], hard_end_unix=bounds['hard_end_unix'],
        native_cap=original['native_cap'], parent_cap=original['parent_cap'], campaign=None, activation_directory=None)
    old_runtime = read(Path(pointers['root']) / 'parallel_v4/service_4/RUNTIME.json')
    for key in ('anchor_root', 'anchor_task_ids'):
        runtime[key] = old_runtime[key]
    script = ('import sys,runpy;sys.path.insert(0,' + repr(runtime['source_root']) +
        ');import gpu;gpu.__path__.insert(0,' + repr(str(Path(proof_directory) / 'gpu')) +
        ');sys.argv=["proof-scan","scan","--service",' + repr(str(service)) +
        '];runpy.run_module("gpu.orch_r118_code_parallel_proof_guard",run_name="__main__")')
    runtime['admission_command'] = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=',
        'PYTHONDONTWRITEBYTECODE=1', 'python3', '-B', '-c', script]
    write(service / 'RUNTIME_PREPARED.json', runtime)
    write(service / 'OWNER_RELEASE.json', envelope)
    owner = deepcopy(prepared['owner'])
    owner.update(handoff=ref(service / 'OWNER_RELEASE.json'), inherited_bounds=envelope['bounds'],
        source_files=source_files, bootstrap_path=str(service / 'FRESH_BOOTSTRAP.json'))
    owner['env'].update(ORCH_R119_LEASE_CLOCK=clock_reference['path'],
        ORCH_R119_LEASE_CLOCK_SHA256=clock_reference['sha256'])
    owner['command'] = orch_r119_code_runtime.command_from_runtime(service, 'guard', runtime)
    write(service / 'OWNER_PREPARED.json', owner)
    write(service / 'BROKER_CONFIG_PREPARED.json', broker_config(checked(pointers['original_broker_config']), bounds))
    return owner


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    write(args.output, branch_snapshot(args.root))
