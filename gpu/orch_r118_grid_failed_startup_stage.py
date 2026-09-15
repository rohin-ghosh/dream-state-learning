"""CPU-only, exclusive-write preparation of GRID failed-start recovery owners."""

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import time

_spec = importlib.util.spec_from_file_location('grid_failed_startup_stage_helper',
    Path(__file__).resolve().with_name('orch_r118_grid_failed_startup_run.py'))
recovery = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(recovery)


require, ref, read, write = recovery.require, recovery.ref, recovery.read, recovery.write


def validate_timer_identity(actual, original):
    require(all(str(actual[key]) == str(original[key]) for key in ('pid','start_ticks','boot_id')) and
            actual['uid'] == os.getuid() and actual['state'] not in ('Z','X'), 'actual_retained_live_timer')


def timer_identity(root, old_plan_reference, process):
    original = read(dict(path=str(root / 'parallel_exec_1513/TIMER_IDENTITY.json'),
                         sha256=ref(root / 'parallel_exec_1513/TIMER_IDENTITY.json')['sha256']))
    require(original['pid'] != recovery.SELECTOR_PID, 'never_selector')
    actual = process.identity(original['pid'])
    validate_timer_identity(actual, original)
    directory = Path('/proc') / str(actual['pid'])
    command = (directory / 'cmdline').read_bytes()
    actual['command_sha256'] = hashlib.sha256(command).hexdigest()
    recovery.timer_command(actual, old_plan_reference, command, (directory / 'environ').read_bytes())
    return actual


def prepare_branch(old_owner_reference, candidate_reference, observation_reference, authorization_reference):
    authorization = read(authorization_reference)
    require(authorization['schema'] == 'R118_GRID_FAILED_STARTUP_CPU_AUTH_V1' and
            authorization['GPU_start_authorized'] is False and
            time.time() < authorization['expires_unix'] <= 1789488600,
            'bounded_CPU_authorization_through_1610')
    owner = read(old_owner_reference)
    require(owner['branch'] in ('F4', 'A4'), 'owned_GRID_only')
    old_plan_reference = owner['runtime_plan']
    old_plan = read(old_plan_reference)
    candidate = read(candidate_reference)
    require(candidate['schema'] == 'R118_GRID_FAILED_STARTUP_SOURCE_V1', 'frozen_recovery_source')
    source = Path(__file__).resolve().parents[1]
    require(candidate['source_files'].get(str(source / 'gpu/orch_r118_grid_failed_startup_run.py')) ==
            ref(source / 'gpu/orch_r118_grid_failed_startup_run.py')['sha256'], 'actual_new_entrypoint_pin')
    root = Path(owner['root']).resolve(strict=True)
    directory = root / 'parallel_recovery_1548'
    require(not directory.exists(), 'single_new_preparation_directory')
    proof = read(observation_reference)
    own = proof['branches'][owner['branch']]
    require(own['root'] == str(root), 'observation_own_root')
    original_boundary = read(old_plan['boundary'])
    plan = deepcopy(old_plan)
    plan.update(directory=str(directory), candidate=candidate_reference, campaign=None,
                final_output=str(Path('/localhome/local-rohing/orch_r118_grid_final_recovery_20260915_v1') / owner['branch']),
                previous_final_plan=read(ref(root / 'parallel_exec_1513/FINAL_PLAN.ref.json')),
                old_final_identities=[])
    runner = recovery.configured_runner(plan)
    handoff, unused = runner.modules(plan)
    handoff.validate_snapshot(original_boundary)
    from gpu import orch_r118_grid_final_drain as process
    retained_timer = timer_identity(root, old_plan_reference, process)
    predecessors = [handoff.central_identity(own['identities'][role]['expected']) for role in ('native', 'guard')]
    for identity in predecessors:
        handoff.parallel.predecessor_released(identity)
    preserved = deepcopy(original_boundary['preserved_files'])
    for path in [root / recovery.ORIGINAL_TERMINAL, *sorted((root / 'parallel_exec_1513').rglob('*.json')),
                 root / 'parallel_exec_1513/NATIVE.log']:
        if path.is_file():
            preserved[str(path.relative_to(root))] = ref(path)['sha256']
    recovery_doc = dict(schema='R118_GRID_FAILED_STARTUP_RECOVERY_V1', root=str(root), branch=owner['branch'],
        observation=observation_reference, old_owner=old_owner_reference, old_plan=old_plan_reference,
        failed_session=proof['session'], failed_dispatch=proof['failure'], old_campaign=old_plan['campaign'],
        old_terminal=own['terminal'], predecessors=predecessors, preserved_files=preserved,
        timer_identity=retained_timer, original_failed_preserved=True, authorization=authorization_reference,
        same_checkpoint_sha256=recovery.CHECKPOINT_SHA, new_calls=0, optimizer_steps=0)
    recovery_reference = write(directory / 'RECOVERY.json', recovery_doc)
    plan['failed_startup_recovery'] = recovery_reference
    recovery.verify_failed_start(plan, handoff)
    released = dict(status='RELEASED', root=str(root), release=own['terminal'],
        predecessors=predecessors, bounds=owner['inherited_bounds'], preserved_files=preserved,
        next_cycle=9, original_FAILED_preserved=True, calls_replayed=0, parent_claims_discarded=0,
        boundary=old_plan['boundary'], recovery=recovery_reference,
        timer_release=False, no_successful_DEV_claim=True, observed_unix=time.time())
    release_reference = write(directory / 'RELEASE.json', released)
    envelope = {name:deepcopy(released[name]) for name in ('status','root','predecessors','bounds','preserved_files','next_cycle')}
    envelope['release'] = release_reference
    envelope_reference = write(directory / 'HANDOFF.json', envelope)
    new_owner = {key:deepcopy(value) for key, value in owner.items()
                 if key not in ('command','runtime_plan','runtime_staged','GPU_started')}
    new_owner.update(handoff=envelope_reference, source_files=candidate['source_files'],
                     bootstrap_path=str(directory / 'CANONICAL_BOOTSTRAP.json'))
    prepared = dict(schema='R118_GRID_FAILED_STARTUP_OWNER_PREPARED_V1',
        status='CPU_PREPARED_REQUIRES_NEW_MAIN_CAMPAIGN_BINDING', owner=new_owner, plan=plan,
        recovery=recovery_reference, python=owner['command'][0], GPU_started=False,
        timer_retired=False, new_calls=0, optimizer_steps=0,
        final_binding_action='MAIN_DISPATCHED_GUARD_RETIRES_EXACT_PREDECESSOR_TIMER_BEFORE_NEW_FINAL_DISPATCH',
        candidate=candidate_reference)
    prepared_reference = write(directory / 'OWNER_PREPARED.json', prepared)
    binding = dict(schema='R118_GRID_FAILED_STARTUP_BROKER_BINDING_V1', root=str(root),
        terminal_path=str(root / recovery.TERMINAL), previous_terminal=own['terminal'],
        handoff=envelope_reference, old_parent_numbers_preserved_through=40,
        wait_seconds=600 if owner['branch'] == 'F4' else 120, hard_end_unix=1789491720,
        activation='PROSPECTIVE_ONLY_AFTER_MAIN_RECOVERY_DISPATCH_BINDING', prepared=prepared_reference)
    broker_reference = write(directory / 'BROKER_BINDING.json', binding)
    return dict(prepared=prepared_reference, broker_binding=broker_reference, handoff=envelope_reference,
                runtime_source_files=candidate['source_files'], timer_identity=retained_timer,
                bind_command_prefix=[owner['command'][0], '-B', str(source / 'gpu/orch_r118_grid_failed_startup_run.py'),
                    'bind', '--prepared', prepared_reference['path'], '--prepared-sha256', prepared_reference['sha256']],
                bind_remaining_arguments=['--campaign', '--campaign-sha256'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('owner', 'candidate', 'observation', 'authorization'):
        parser.add_argument('--' + name, type=Path, required=True)
        parser.add_argument('--' + name + '-sha256', required=True)
    args = parser.parse_args()
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only_preparation')
    refs = [dict(path=str(getattr(args, name)), sha256=getattr(args, name + '_sha256'))
            for name in ('owner','candidate','observation','authorization')]
    print(json.dumps(prepare_branch(*refs), sort_keys=True))


if __name__ == '__main__':
    main()
