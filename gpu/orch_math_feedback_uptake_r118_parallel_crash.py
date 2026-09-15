"""Explicit crashed-postcommit disposition; never replay submitted experience or DEV."""

from pathlib import Path
import time

from gpu import orch_math_feedback_uptake_r118_parallel_lifecycle as life
from gpu import orch_math_feedback_uptake_r118_parallel_recipe as recipe


shared, require, ref = life.shared, life.require, life.ref
KIND = 'CRASHED_POSTCOMMIT'


def inspect(plan):
    root = Path(plan['root'])
    old = life.checked(plan['old_drain_plan'])
    documents = life.boundary.fences(plan['protected_refs'])
    for role, label in (('native', 'native_launch'), ('guard', 'guard_receipt')):
        require(life.boundary.minimal_identity(documents[label]['identity']) ==
            life.boundary.minimal_identity(old[role]), 'actual_crashed_predecessor_binding')
        require(not life.alive(old[role]), 'crashed_predecessor_must_be_absent')
    require(not life.drain.live_readout_identities(root), 'no_live_crashed_readout')
    life.unused_old_FINAL(plan)
    failure = shared.read(root/'SHARED_FAILED.json')
    terminal = shared.read(root/'SHARED_RESIDENT_TERMINAL.json')
    guard_terminal = shared.read(root/'SHARED_TERMINAL.json')
    counters = shared.read(root/'COUNTERS.json')
    require(failure['type'] == 'ValueError' and failure['error'] == 'unchanged_adapter_recipe'
        and failure['counters'] == terminal['counters'] == counters
        and terminal['status'] == guard_terminal['status'] == 'FAILED'
        and terminal['local_optimizer_steps'] == guard_terminal['local_optimizer_steps'] == 0,
        'exact_nonmaterial_recipe_failure_only')
    cycles = sorted(path for path in root.glob('cycle[0-9][0-9][0-9]') if any(path.iterdir()))
    require(bool(cycles), 'actual_collected_cycle_required')
    output = cycles[-1]
    cycle = int(output.name[5:])
    require(cycle < life.previous.math.policy.CYCLES, 'no_extra_cycles')
    for name in ('TRAIN_FAILED.json', 'SHARED_SLEEP.json', 'COMPLETE.json'):
        require(not (output/name).exists(), 'do_not_relabel_other_phase_or_completed_work')
    trained = shared.read(output/'TRAIN_COMPLETE.json')
    generation = trained['shared_generation']
    common = Path(life.previous.ready.COMMON_ROOT)
    require(generation == 0 and trained['shared_branch'] == plan['branch'], 'authorized_first_commit_only')
    submission_path = common/f'generation_{generation:06d}'/(plan['branch']+'.json')
    accepted = life.checked(trained['submission'])
    require(trained['submission']['path'] == str(submission_path)
        and accepted['branch'] == plan['branch'] and accepted['generation'] == generation
        and accepted['checkpoint_sha256'] == trained['shared_checkpoint_sha256'], 'accepted_gen0_exact_once')
    ids = accepted['episode_ids']
    require(len(ids) == len(set(ids)) == 2, 'two_distinct_original_episodes')
    calls = sorted(path for path in output.glob('CALL_*.json') if not path.name.endswith('.request.json'))
    captures = [shared.read(path) for path in calls]
    require(len(captures) == 6 and all(call['status'] == 'COMPLETE' for call in captures)
        and tuple(call['phase'] for call in captures) == life.client.PHASES
        and [call['task_id'] for call in captures] == [ids[0]]*2+[ids[1]]*4, 'complete_six_call_source_order')
    require(len(accepted['rows']) == 6 and {row['source_call_sha256'] for row in accepted['rows']} ==
        {shared.sha(path) for path in calls}, 'all_captures_already_submitted')
    for path, call in zip(calls, captures):
        request = path.with_suffix('.request.json')
        require(shared.sha(request) == call['request_sha256'] and call['split'] == 'TRAIN'
            and call['shared_generation'] == generation
            and call['shared_checkpoint_sha256'] == trained['shared_checkpoint_sha256'], 'original_capture_provenance')
    carry = shared.read(output/'BOUNDARY.json')
    require(shared.digest(shared.read(output/'TRAIN_EXPERIENCE.json')) == carry['source_history_sha256']
        and carry['own_reflection']['actor'] == 'child', 'same_source_backed_carry')
    totals = dict(native=0, parent=0)
    parents = []
    reservations = sorted((root/'reservations').glob('*.json'))
    for kind in totals:
        for path in sorted((root/'reservations').glob(kind+'_*.json')):
            item = shared.read(path)
            require(item['kind'] == kind and item['first'] == totals[kind]+1, 'contiguous_original_reservations')
            totals[kind] += item['count']
            if kind == 'parent' and item['metadata']['id'].startswith(f'C{cycle:03d}_'):
                parents.append(item['metadata']['id'])
    require(totals == counters and len(parents) == 6, 'unchanged_all_charges_six_parents')
    parent_files = []
    for identifier in parents:
        paths = [root/'delivered'/(identifier+'.json'), root/'parent_queue'/(identifier+'.request.json'),
            root/'parent_queue'/(identifier+'.response.json')]
        delivered, request, response = [shared.read(path) for path in paths]
        require(delivered['id'] == identifier and delivered['request_sha256'] == shared.digest(request),
            'actual_closed_parent_delivery')
        receipt = response['transcript_receipt']
        archive = root/'parent_transcripts'/identifier
        require(receipt['remote_root'] == str(archive) and receipt['files'], 'closed_parent_archive')
        for name, digest in receipt['files'].items():
            require(Path(name).name == name and shared.sha(archive/name) == digest, 'parent_archive_hash')
        parent_files.extend(paths + [path for path in archive.rglob('*') if path.is_file()])
    require(not (root/'readouts'/f'cycle_{cycle:03d}').exists()
        and not list((root/'shared_readout_bindings').glob(f'cycle_{cycle:03d}*')), 'OLD_DEV_NOT_RUN_only_no_retry')
    session = life.client.prepare(common, plan['branch'])
    require(session['generation'] == generation+1, 'only_actual_first_committed_successor')
    publication = shared.read(common/f'generation_{generation:06d}'/'sleep/COMPLETE.json')
    require(publication['state'] == life.client.current(session) and publication['same_optimizer'] is True,
        'actual_shared_commit_not_replayed')
    require(not (common/f"generation_{session['generation']:06d}"/(plan['branch']+'.json')).exists()
        and not (common/f"generation_{session['generation']:06d}"/'sleep/START.json').exists(), 'no_next_submission_or_sleep')
    initial = shared.read(common/'INITIALIZED.json')['state']['checkpoint']
    shared.checked_checkpoint(initial)
    prior = shared.read(initial['path'])['adapter']
    comparison = recipe.require_same_recipe(shared.read(Path(prior['path'])/'adapter_config.json'),
        shared.read(Path(session['adapter']['path'])/'adapter_config.json'))
    require(initial['path_sha256'] == trained['shared_checkpoint_sha256'], 'unchanged_initial_source_checkpoint')
    kept = [root/name for name in ('COUNTERS.json', 'PROGRESS.json', 'CONFIG.json', 'ACTIVATION.json',
        'SHARED_ACTIVATION.json', 'SHARED_LAUNCH.json', 'SHARED_CLIENT_READY.json',
        'R118_SHARED_ADMISSION_REPAIR_LAUNCH.json', 'SHARED_FAILED.json',
        'SHARED_RESIDENT_TERMINAL.json', 'SHARED_TERMINAL.json')]
    kept += [path for path in output.rglob('*') if path.is_file()] + reservations + parent_files
    preserved = {str(path.relative_to(root)): shared.sha(path) for path in kept}
    return dict(kind=KIND, root=str(root), branch=plan['branch'], cycle=cycle, next_cycle=cycle+1,
        generation=session['generation'], checkpoint_sha256=session['checkpoint_sha256'],
        mounted_checkpoint_sha256=None, old_DEV_status='NOT_RUN', old_DEV_replayed=False,
        accepted_previous_submission=trained['submission'], carry=ref(output/'BOUNDARY.json'),
        counters=counters, inherited_bounds=plan['inherited_bounds'], preserved_files=preserved,
        recipe_comparison=comparison, actual_loaded_identity_required_at_fresh_bootstrap=True,
        old_failures_preserved=True, prior_generation_replayed=False, fresh_dev_complete=False,
        observed_unix=time.time())


def release(service, permission_reference):
    service = Path(service)
    plan = life.plan_for(service)
    permission = life.authorization(permission_reference, plan, 'RELEASE')
    require(permission.get('crashed_postcommit_recovery') is True, 'explicit_crash_recovery_scope')
    require(not (service/'RELEASED.json').exists(), 'single_actual_release')
    value = inspect(plan)
    require(permission['checkpoint_sha256'] == value['checkpoint_sha256'], 'canonical_authorized_checkpoint')
    root = Path(plan['root'])
    disposition = root/'R118_CRASH_POSTCOMMIT_DISPOSITION.json'
    cursor = root/'R118_CRASH_RECOVERY_CURSOR.json'
    require(not disposition.exists() and not cursor.exists(), 'single_new_disposition_no_overwrite')
    shared.write(disposition, dict(schema='R118_POSTCOMMIT_EVAL_DISPOSITION_V1',
        status='TERMINAL_POSTCOMMIT_EVALUATION', root=str(root), branch=plan['branch'],
        generation=value['generation'], checkpoint_sha256=value['checkpoint_sha256'],
        accepted_submission=value['accepted_previous_submission'],
        committed_sleep=ref(Path(life.previous.ready.COMMON_ROOT)/
            f"generation_{value['generation']-1:06d}"/'sleep/COMPLETE.json'),
        native_terminal=ref(root/'SHARED_RESIDENT_TERMINAL.json'),
        evaluations=dict(DEV='NOT_ATTEMPTED', OPEN='NOT_ATTEMPTED'),
        evaluation_evidence=[ref(root/name) for name in ('SHARED_FAILED.json',
            'SHARED_RESIDENT_TERMINAL.json','SHARED_TERMINAL.json')],
        replay_train=False, process_signals=0, authorization=permission_reference))
    shared.write(cursor, dict(schema='R118_POSTCOMMIT_RECOVERED_CURSOR_V1',
        root=str(root), branch=plan['branch'], accepted_generation=value['generation']-1,
        accepted_submission_sha256=value['accepted_previous_submission']['sha256'],
        checkpoint_sha256=value['checkpoint_sha256'], completed_train_cycle=value['cycle'],
        next_cycle=value['next_cycle'], native_used=value['counters']['native'],
        parent_used=value['counters']['parent'], pending_train_calls=[], pending_train_submissions=[],
        action='NEXT_NEW_CYCLE_AFTER_CANONICAL_BOOTSTRAP', disposition=ref(disposition)))
    value.update(disposition=ref(disposition), settled_cursor=ref(cursor))
    value['preserved_files'].update({str(path.relative_to(root)):shared.sha(path) for path in (disposition,cursor)})
    life.boundary.unchanged(root, value['preserved_files'])
    shared.write(service/'BOUNDARY.json',value)
    old = life.checked(plan['old_drain_plan'])
    require(all(not life.alive(old[role]) for role in ('native','guard')), 'actual_predecessors_absent_again')
    document = dict(status='RELEASED', kind=KIND, root=str(root), service=str(service),
        boundary=ref(service/'BOUNDARY.json'), authorization=permission_reference,
        predecessors=[old['native'],old['guard']], authentic_guard_terminal=ref(root/'SHARED_TERMINAL.json'),
        retired_FINAL_timers=[], final_custody_pending=True, released_unix=time.time(),
        process_signals=0, no_replay=True, old_peer_rng_saved=False,
        fresh_peer_rng_policy=plan['fresh_peer_rng_policy'])
    shared.write(service/'RELEASED.json',document)
    return ref(service/'RELEASED.json')
