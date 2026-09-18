"""Prospective math boundary proofs; no signals, launches, or activation writes."""

from copy import deepcopy
import os
from pathlib import Path

from gpu import orch_math_feedback_uptake_r118_final_drain as drain
from gpu import orch_math_feedback_uptake_r118_shared_run as previous
from gpu import orch_r118_parallel_consolidation as hook


shared, client, require = previous.shared, previous.client, previous.require
SCHEMA = 'R118_MATH_PARALLEL_HANDOFF_V1'
FENCES = ('native_launch', 'guard_receipt', 'final_drain_plan',
          'final_evaluation_plan', 'final_timer', 'final_drain_timer', 'broker_config')


def minimal_identity(value):
    return dict(boot_id=value['boot_id'], pid=int(value['pid']), start_ticks=int(value['start_ticks']))


def launch_device(root, branch):
    mounted = previous.math.mounted(Path(root), 'prospective_parallel_existing_device')
    rank = hook.BRANCHES.index(branch)
    require(mounted['index'] == rank and mounted['uuid'] == previous.math.policy.DEVICES[rank],
            'actual_existing_rank_UUID_required')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == mounted['uuid'], 'actual_existing_CVD_required')
    return dict(kind='cuda', physical=rank, uuid=mounted['uuid'],
        cuda_visible_devices=os.environ['CUDA_VISIBLE_DEVICES'])


def checked(reference):
    path = hook.checked_file(reference['path'], reference['sha256'])
    return shared.read(path)


def fences(references):
    require(set(references) == set(FENCES), 'all_authentic_guard_and_FINAL_bindings_required')
    return {name: checked(reference) for name, reference in references.items()}


def unchanged(root, preserved):
    root = Path(root).resolve(strict=True)
    require(bool(preserved), 'preserved_ledger_required')
    for name, digest in preserved.items():
        relative = Path(name)
        require(not relative.is_absolute() and '..' not in relative.parts
                and (root/relative).resolve().is_relative_to(root), 'preserved_path_escape')
        hook.checked_file(root/relative, digest)


def inspect_completed(plan, protected_refs):
    """Observe only. A racing actor is not parked or authorized by this result."""
    root = Path(plan['root']).resolve(strict=True)
    require(plan['branch'] in client.BRANCHES
            and root == client.BRANCHES[plan['branch']], 'original_math_root_only')
    documents = fences(protected_refs)
    require(minimal_identity(documents['native_launch']['identity']) == minimal_identity(plan['native']),
            'authentic_native_launch')
    require(minimal_identity(documents['guard_receipt']['identity']) == minimal_identity(plan['guard']),
            'authentic_guard_launch')
    final_plan = documents['final_drain_plan']
    require(final_plan['root'] == str(root) and final_plan['native'] == plan['native']
            and final_plan['guard'] == plan['guard'], 'FINAL_drain_exact_predecessor_actors')
    for actor in ('native', 'guard'):
        drain.actual_process(plan[actor], plan['native_source'], root,
            actor=actor == 'native', uuid=plan['uuid'])
    value = drain.snapshot(plan)
    if value is None or value['kind'] != 'COMPLETE_SHARED_CHECKPOINT_AND_FRESH_DEV_CYCLE':
        return None
    cycle = value['cycle']
    common = drain.io.COMMON
    state = shared.read(common/'STATE.json')
    complete = shared.read(root/f'cycle{cycle:03d}'/'COMPLETE.json')
    progress = shared.read(root/'PROGRESS.json')
    require(state['generation'] == value['generation']+1 == complete['shared_generation'],
            'latest_committed_generation_no_skips')
    require(progress['cycle'] == cycle and progress['phase'] == 'CYCLE_COMPLETE'
            and progress['counters'] == value['counters']
            and progress['shared_generation'] == state['generation']
            and progress['shared_checkpoint_sha256'] == state['checkpoint']['path_sha256'],
            'actual_settled_cursor_after_DEV')
    shared.checked_checkpoint(state['checkpoint'])
    require(cycle < previous.math.policy.CYCLES, 'no_cycles_left_no_successor')
    readout_identity = None
    for name in ('BEFORE.json', 'AFTER.json', 'MOUNTED_FINAL.json'):
        mounted = shared.read(root/'readouts'/f'cycle_{cycle:03d}'/name)
        require(mounted['shared_generation'] == state['generation']
                and mounted['shared_checkpoint_sha256'] == state['checkpoint']['path_sha256'],
                'fresh_DEV_actual_mount_binding')
        require(mounted['process']['pid'] != plan['native']['pid'], 'DEV_not_resident_process')
        if readout_identity is None:
            readout_identity = mounted['process']
        require(mounted['process'] == readout_identity, 'same_fresh_DEV_process_before_after')
    require(not (common/f"generation_{state['generation']:06d}"/'sleep/START.json').exists(),
            'no_parallel_handoff_during_started_sleep')
    require(not (common/f"generation_{state['generation']:06d}"/(plan['branch']+'.json')).exists(),
            'no_unaccounted_next_submission')
    preserved = dict(value['preserved_files'])
    for name in ('PROGRESS.json', 'CONFIG.json', 'ACTIVATION.json', 'SHARED_ACTIVATION.json',
                 'SHARED_LAUNCH.json', 'SHARED_CLIENT_READY.json'):
        preserved[name] = shared.sha(root/name)
    unchanged(root, preserved)
    for name in ('BEFORE.json', 'AFTER.json', 'MOUNTED_FINAL.json'):
        path = root/'readouts'/f'cycle_{cycle:03d}'/name
        preserved[str(path.relative_to(root))] = shared.sha(path)
    fences(protected_refs)
    return dict(schema=SCHEMA, status='OBSERVED_NOT_RELEASED', branch=plan['branch'], root=str(root),
        identity=deepcopy(plan['native']), guard=deepcopy(plan['guard']), generation=state['generation'],
        checkpoint_sha256=state['checkpoint']['path_sha256'], next_cycle=cycle+1,
        inherited_bounds=previous.ready.bounds(), counters=value['counters'], carry=value['carry'],
        accepted_previous_submission=value['common_submission'], preserved_files=preserved,
        protected_refs=deepcopy(protected_refs), common_state=previous.ready.reference(common/'STATE.json'),
        process_signals=0, released=False, activated=False, RNG_policy='SAME_RESIDENT_ENGINE_ONLY')


def accept_in_process(handoff, engine):
    require(handoff['schema'] == SCHEMA and handoff['status'] == 'OBSERVED_NOT_RELEASED',
            'exact_observed_handoff_required')
    require(handoff['RNG_policy'] == 'SAME_RESIDENT_ENGINE_ONLY', 'no_reconstructed_rng_or_actor')
    identity = hook.process_identity()
    require(minimal_identity(handoff['identity']) == identity,
            'same_live_actor_no_replacement')
    require(handoff['inherited_bounds'] == previous.ready.bounds(), 'original_absolute_caps')
    root = Path(handoff['root'])
    require(engine.session['branch_root'] == str(root)
            and engine.session['branch'] == handoff['branch']
            and engine.session['generation'] == handoff['generation']
            and engine.session['checkpoint_sha256'] == handoff['checkpoint_sha256'],
            'handoff_actual_mounted_session')
    checked(handoff['common_state'])
    checked(handoff['accepted_previous_submission'])
    unchanged(root, handoff['preserved_files'])
    fences(handoff['protected_refs'])
    require(not drain.live_children(identity['pid']) and not drain.morning_attempts(root),
            'no_readout_child_or_previous_FINAL')
    require(shared.read(root/'COUNTERS.json') == handoff['counters'], 'no_new_charges_since_handoff')
    engine.verify_base()
    client.current(engine.session)
    carry = checked(handoff['carry'])['own_reflection']
    return handoff['next_cycle'], carry


def submission_certificate(root, engine, cycle, submission, protected_refs, supervision):
    """New generation's accepted collection, never the previous DEV certificate."""
    root = Path(root)
    session = engine.session
    client.current(session)
    require(str(root) == session['branch_root'] and session['branch'] in client.BRANCHES,
            'own_branch_certificate')
    expected = Path(session['shared_root'])/f"generation_{session['generation']:06d}"/(session['branch']+'.json')
    require(Path(submission['path']) == expected, 'current_generation_submission_only')
    accepted = checked(submission)
    tasks = shared.read(root.parent/'TRAIN.json')[cycle-1]
    require(accepted['branch'] == session['branch'] and accepted['generation'] == session['generation']
            and accepted['checkpoint_sha256'] == session['checkpoint_sha256']
            and accepted['episode_ids'] == [task['id'] for task in tasks] and len(tasks) == 2,
            'exact_two_new_episodes_no_old_resubmit')
    collection = root/f'cycle{cycle:03d}'
    require(shared.read(collection/'TRAIN_COMPLETE.json')['submission'] == submission,
            'actual_completed_source_collection')
    require(not (collection/'TRAIN_FAILED.json').exists()
            and not (collection/'SHARED_SLEEP.json').exists(), 'no_failed_or_completed_sleep_replay')
    require(not (expected.parent/'sleep/START.json').exists(), 'no_started_sleep_retry')
    actual = drain.snapshot(dict(root=str(root), branch=session['branch'], native=hook.process_identity()))
    require(actual is not None and actual['kind'] == 'COMPLETE_COLLECTION_ACCEPTED_WAITING_FOR_SHARED_CHECKPOINT'
            and actual['cycle'] == cycle and actual['common_submission'] == submission,
            'closed_source_parent_archive_and_all_reservations')
    documents = fences(protected_refs)
    require(supervision['native_identity'] == hook.process_identity()
            and supervision['guard_identity'] == minimal_identity(documents['guard_receipt']['identity'])
            and supervision['guard_binding'] == protected_refs['guard_receipt']
            and supervision['owner_verified_safe_for_parallel'] is True,
            'actual_retained_supervision_required')
    require(supervision['parallel_safe_snapshot_source_sha256'] == shared.sha(__file__)
            and documents['final_drain_timer'].get('parallel_safe_snapshot_source_sha256') == shared.sha(__file__),
            'future_parallel_aware_FINAL_controller_required')
    expected_finals = [dict(identity=minimal_identity(documents[name]['identity']), evidence=protected_refs[name])
        for name in ('final_timer', 'final_drain_timer')]
    require(supervision['final_identity_bindings'] == expected_finals, 'exact_live_FINAL_timers_required')
    for identity in [supervision['guard_identity'], *[item['identity'] for item in expected_finals]]:
        hook.live_identity(identity)
    counters = shared.read(root/'COUNTERS.json')
    original = previous.ready.bounds()
    for kind, cap in (('native', original['native_calls']), ('parent', original['parent_calls'])):
        require(type(counters[kind]) is int and 0 <= counters[kind] <= cap, 'original_charge_caps')
    files = [root/'COUNTERS.json', root/'PROGRESS.json']
    files += list((root/'reservations').glob('*.json'))
    files += [path for path in collection.iterdir() if path.is_file()]
    preserved = dict(actual['preserved_files'])
    preserved.update({str(path.relative_to(root)): shared.sha(path) for path in files})
    return dict(branch=session['branch'], root=str(root), generation=session['generation'],
        checkpoint_sha256=session['checkpoint_sha256'], identity=hook.process_identity(),
        status='SAFE_FOR_PARALLEL', bounds=dict(train_end_unix=original['native_end_unix']-120,
            hard_end_unix=original['hard_end_unix'], native_used=counters['native'],
            native_cap=original['native_calls'], parent_used=counters['parent'], parent_cap=original['parent_calls']),
        preserved_files=preserved, submission_sha256=submission['sha256'], cycle=cycle,
        protected_refs=deepcopy(protected_refs), optimizer_owner='F1', local_optimizer_steps=0,
        launch_device=launch_device(root, session['branch']),
        retained_supervision=deepcopy(supervision))


def parallel_safe_snapshot(plan):
    """Required future drain seam: an accepted collection is not an idle collective."""
    common = drain.io.COMMON
    for folder in common.glob('generation_*/sleep'):
        if (folder/'START.json').exists() and not (folder/'COMPLETE.json').exists():
            return None
        if (folder/'START.json').exists():
            started = shared.read(folder/'START.json')
            if started.get('schema') == hook.SCHEMA and not (folder/'ALL8_RELOAD.json').exists():
                return None
    return drain.snapshot(plan)
