"""Prospective fresh-exec math custody; explicit Main release/launch authorizations."""

import argparse
from copy import deepcopy
import fcntl
import json
import os
from pathlib import Path
import select
import signal
import stat
import time

from gpu import orch_math_feedback_uptake_r118_parallel_boundary as boundary


previous, drain, hook = boundary.previous, boundary.drain, boundary.hook
shared, client, require = previous.shared, previous.client, previous.require
SOURCE = Path(__file__).resolve().parents[1]
SERVICES = Path('/localhome/local-rohing/orch_math_feedback_uptake_r118_parallel_20260915_attempt2')
FINAL_ROOT = Path('/localhome/local-rohing/orch_math_feedback_uptake_r118_parallel_final_20260915_attempt1')
MODULE = 'gpu.orch_math_feedback_uptake_r118_parallel_native'
TRAIN_END = drain.START
ref, checked, identity = previous.ready.reference, boundary.checked, drain.identity


def alive(expected):
    if not drain.io.same_process(expected):
        return False
    try:
        return drain.pinned.process_state(expected['pid']) not in ('Z', 'X')
    except (FileNotFoundError, ProcessLookupError):
        return False


def service_for(branch):
    require(branch in client.BRANCHES, 'only_F2_A2')
    return SERVICES/('lane'+str(hook.BRANCHES.index(branch)))


def authorization(reference, plan, action, clock=time.time):
    document = checked(reference)
    require(document.get('schema') == 'R118_MATH_PARALLEL_FRESH_EXEC_AUTH_V1'
            and document.get('authorized') is True and document.get('common_handoff_coordinated') is True
            and action in document.get('actions', []) and document.get('root') == plan['root']
            and document.get('plan_sha256') == plan['plan_sha256'], 'explicit_Main_scoped_authorization')
    require(document.get('fresh_peer_rng_policy') == 'DETERMINISTIC_NEW_STREAM_NOT_OLD_PEER_RNG'
            and document.get('lifecycle_rebinding_authorized') is True, 'explicit_fresh_exec_and_FINAL_custody')
    require(document['not_before_unix'] <= clock() < document['expires_unix'] <= TRAIN_END,
            'bounded_future_authorization_not_current_serial_swap')
    return document


def verify_source(manifest_reference, tests_reference):
    manifest, tests = checked(manifest_reference), checked(tests_reference)
    require(tests['passed'] is True and tests['cuda_initialized'] is False
            and tests['source_manifest_sha256'] == manifest_reference['sha256'], 'native_CPU_source_binding')
    for name, digest in manifest.items():
        relative = Path(name)
        require(not relative.is_absolute() and '..' not in relative.parts, 'source_path_escape')
        hook.checked_file(SOURCE/relative, digest)
    return manifest


def prepare(branch, old_drain_plan, old_eval_plan, source_manifest, tests_receipt):
    service = service_for(branch)
    require(not service.exists(), 'new_service_namespace_only')
    verify_source(source_manifest, tests_receipt)
    plan, evaluation = checked(old_drain_plan), checked(old_eval_plan)
    root = client.BRANCHES[branch]
    require(plan['root'] == evaluation['original_root'] == str(root) and plan['branch'] == branch,
            'same_original_life_and_FINAL')
    require(evaluation['drain_plan'] == old_drain_plan, 'actual_v2_FINAL_drain_binding')
    protected = dict(native_launch=ref(root/'SHARED_LAUNCH.json'),
        guard_receipt=ref(root/'R118_SHARED_ADMISSION_REPAIR_LAUNCH.json'),
        final_drain_plan=old_drain_plan, final_evaluation_plan=old_eval_plan,
        final_timer=ref(Path(evaluation['root'])/'SCHEDULED.json'),
        final_drain_timer=ref(Path(plan['output'])/'ARMED.json'), broker_config=ref(root/'BROKER_CONFIG.json'))
    boundary.fences(protected)
    original_timer = ref(Path(plan['timer_root'])/'SCHEDULED.json')
    document = dict(schema='R118_MATH_FRESH_EXEC_PLAN_V1', status='PREPARED_NOT_ACTIVE',
        branch=branch, root=str(root), service=str(service), source_root=str(SOURCE),
        old_drain_plan=old_drain_plan, old_evaluation_plan=old_eval_plan,
        old_timer_records=[protected['final_drain_timer'], protected['final_timer'], original_timer],
        protected_refs=protected, source_manifest=source_manifest, tests_receipt=tests_receipt,
        inherited_bounds=previous.ready.bounds(), train_end_unix=TRAIN_END,
        final_root=str(FINAL_ROOT/('lane'+str(hook.BRANCHES.index(branch)))),
        algorithm='FRESH_EXEC_CANONICAL_WEIGHTS_NEW_PEER_RNG_THEN_PARALLEL_AVERAGE_GRADIENT',
        fresh_peer_rng_policy='DETERMINISTIC_NEW_STREAM_NOT_OLD_PEER_RNG', prepared_unix=time.time())
    shared.write(service/'PLAN.json', document)
    return ref(service/'PLAN.json')


def plan_for(service):
    service = Path(service).resolve(strict=True)
    plan = shared.read(service/'PLAN.json')
    require(plan['schema'] == 'R118_MATH_FRESH_EXEC_PLAN_V1'
            and service == service_for(plan['branch']) and plan['root'] == str(client.BRANCHES[plan['branch']]),
            'exact_math_service_root')
    if plan['source_root'] != str(SOURCE):
        upgrade_path = service/('SOURCE_UPGRADE_'+shared.digest(str(SOURCE))[:16]+'.json')
        upgrade = shared.read(upgrade_path if upgrade_path.exists() else service/'SOURCE_UPGRADE.json')
        require(upgrade['schema'] == 'R118_MATH_UNLAUNCHED_SOURCE_UPGRADE_V1'
            and upgrade['original_plan'] == ref(service/'PLAN.json')
            and upgrade['previous_source_root'] == plan['source_root']
            and upgrade['source_root'] == str(SOURCE), 'exact_preserved_plan_source_upgrade')
        require(upgrade['previous_source_manifest'] == plan['source_manifest']
            and checked(upgrade['release'])['status'] == 'RELEASED'
            and upgrade['release'] == ref(service/'RELEASED.json'), 'released_unlaunched_source_upgrade')
        plan.update(source_root=upgrade['source_root'], source_manifest=upgrade['source_manifest'],
            tests_receipt=upgrade['tests_receipt'])
    require(plan['source_root'] == str(SOURCE) and plan['inherited_bounds'] == previous.ready.bounds()
            and plan['train_end_unix'] == TRAIN_END, 'frozen_source_and_original_caps')
    verify_source(plan['source_manifest'], plan['tests_receipt'])
    return dict(plan, plan_sha256=shared.sha(service/'PLAN.json'))


def exact_live(expected):
    require(expected['uid'] == os.getuid() and identity(expected['pid']) == expected,
            'exact_owned_boot_PID_start_exec_cwd_before_signal')


def terminate_owned(expected, *, held=False, clock=time.time, deadline=None, force=False):
    exact_live(expected)
    descriptor = os.pidfd_open(expected['pid'])
    try:
        exact_live(expected)
        require(deadline is None or clock() < deadline, 'signal_within_authorized_window')
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
        if held:
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        exited = bool(select.select([descriptor], [], [], 10)[0])
        if not exited and force:
            exact_live(expected)
            signal.pidfd_send_signal(descriptor, signal.SIGKILL)
            exited = bool(select.select([descriptor], [], [], 3)[0])
        require(exited, 'owned_process_must_exit_no_unbounded_wait')
    finally:
        os.close(descriptor)


def cpu_only(expected):
    exact_live(expected)
    directory = Path('/proc')/str(expected['pid'])
    environment = (directory/'environ').read_bytes().split(b'\0')
    require(b'CUDA_VISIBLE_DEVICES=' in environment, 'CPU_timer_empty_startup_CVD')
    devices = set()
    for pattern in ('/dev/nvidia*', '/dev/dri/renderD*'):
        import glob
        for name in glob.glob(pattern):
            info = Path(name).stat()
            if stat.S_ISCHR(info.st_mode):
                devices.add(info.st_rdev)
    for path in (directory/'fd').iterdir():
        try:
            info = path.stat()
        except FileNotFoundError:
            continue
        require(not stat.S_ISCHR(info.st_mode) or info.st_rdev not in devices, 'CPU_timer_no_GPU_FDs')


def unused_old_FINAL(plan):
    require(not drain.morning_attempts(Path(plan['root'])), 'no_old_FINAL_attempt_or_reservation')
    old = checked(plan['old_evaluation_plan'])
    earlier = checked(old['previous_evaluation_plan'])
    for evaluation in (old, earlier):
        root = Path(evaluation['root'])
        require(not any((root/name).exists() for name in ('LEDGER.json','NATIVE_CLAIM.json','LAUNCH.json'))
                and not list(root.glob('CALL_*.json')), 'no_old_separate_FINAL_charged_or_dispatched')


def release(service, permission_reference, *, clock=time.time, pause=time.sleep):
    service = Path(service)
    plan = plan_for(service)
    permission = authorization(permission_reference, plan, 'RELEASE', clock)
    root = Path(plan['root'])
    old = checked(plan['old_drain_plan'])
    require(not (service/'RELEASED.json').exists() and not (service/'RELEASE_STARTED.json').exists(),
            'single_owned_release_attempt')
    observed = boundary.inspect_completed(old, plan['protected_refs'])
    if observed is None:
        return dict(status='NOT_AT_SAFE_BOUNDARY', signalled=False)
    require(permission['checkpoint_sha256'] == observed['checkpoint_sha256'], 'Main_actual_commit_before_release')
    descriptors, held = {}, set()
    with (root/'COUNTERS.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            for role in ('guard', 'native'):
                expected = old[role]
                exact_live(expected)
                descriptors[role] = os.pidfd_open(expected['pid'])
                exact_live(expected)
            for role in ('guard', 'native'):
                authorization(permission_reference, plan, 'RELEASE', clock)
                exact_live(old[role])
                signal.pidfd_send_signal(descriptors[role], signal.SIGSTOP)
                held.add(role)
                for attempt in range(100):
                    if drain.pinned.process_state(old[role]['pid']) in ('T', 't'):
                        break
                    pause(.01)
                else:
                    raise ValueError('bounded_owned_hold_failed')
            observed = boundary.inspect_completed(old, plan['protected_refs'])
            if observed is None:
                return dict(status='RACED_NOT_RELEASED', signalled=True, resumed=True)
            require(observed['checkpoint_sha256'] == permission['checkpoint_sha256'], 'commit_unchanged_under_hold')
            unused_old_FINAL(plan)
            shared.write(service/'RELEASE_STARTED.json', dict(authorization=permission_reference,
                boundary_sha256=shared.digest(observed), observed_unix=clock()))
            shared.write(service/'BOUNDARY.json', observed)
            terminate_owned(old['native'], held=True, clock=clock, deadline=permission['expires_unix'])
            held.discard('native')
            exact_live(old['guard'])
            signal.pidfd_send_signal(descriptors['guard'], signal.SIGCONT)
            held.discard('guard')
            require(bool(select.select([descriptors['guard']], [], [], 12)[0]), 'authentic_old_guard_exit_required')
        finally:
            for role in held:
                try:
                    signal.pidfd_send_signal(descriptors[role], signal.SIGCONT)
                except ProcessLookupError:
                    pass
            for descriptor in descriptors.values():
                os.close(descriptor)
    boundary.unchanged(root, observed['preserved_files'])
    require(not alive(old['native']) and not alive(old['guard']) and not drain.live_readout_identities(root),
            'actual_old_native_guard_readouts_exited')
    terminal = ref(root/'SHARED_TERMINAL.json')
    retired = []
    for record in plan['old_timer_records']:
        expected_record = checked(record)['identity']
        expected = identity(expected_record['pid'])
        require(all(str(expected.get(key)) == str(value) for key, value in expected_record.items()),
                'authentic_old_timer_record')
        unused_old_FINAL(plan)
        cpu_only(expected)
        terminate_owned(expected, clock=clock, deadline=permission['expires_unix'])
        retired.append(dict(record=record, identity=expected, actual_eval_calls=0))
    unused_old_FINAL(plan)
    document = dict(status='RELEASED', root=str(root), service=str(service),
        boundary=ref(service/'BOUNDARY.json'), authorization=permission_reference,
        predecessors=[old['native'], old['guard']], authentic_guard_terminal=terminal,
        retired_FINAL_timers=retired, released_unix=clock(), old_peer_rng_saved=False,
        fresh_peer_rng_policy=plan['fresh_peer_rng_policy'], no_replay=True)
    shared.write(service/'RELEASED.json', document)
    return ref(service/'RELEASED.json')


def released(service, *, require_unchanged=True):
    service = Path(service)
    plan = plan_for(service)
    receipt = shared.read(service/'RELEASED.json')
    saved = checked(receipt['boundary'])
    require(receipt['status'] == 'RELEASED' and receipt['root'] == plan['root'], 'authentic_owned_release')
    require(all(not alive(item) for item in receipt['predecessors']), 'old_actors_still_live')
    checked(receipt['authentic_guard_terminal'])
    timers = receipt['retired_FINAL_timers']
    if receipt.get('final_custody_pending') and (service/'FINAL_TIMERS_RETIRED.json').exists():
        retirement = shared.read(service/'FINAL_TIMERS_RETIRED.json')
        require(retirement['release'] == ref(service/'RELEASED.json'), 'exact_pending_FINAL_custody')
        timers = retirement['timers']
    for timer in timers:
        checked(timer['record'])
        require(not alive(timer['identity']) and timer['actual_eval_calls'] == 0, 'old_FINAL_timer_still_live')
    unused_old_FINAL(plan)
    checked(saved['accepted_previous_submission'])
    if require_unchanged:
        boundary.unchanged(Path(plan['root']), saved['preserved_files'])
        require(shared.read(Path(plan['root'])/'COUNTERS.json') == saved['counters'], 'no_charge_reset_or_replay')
    return saved


def retire_final_timers(service, permission_reference):
    service = Path(service)
    plan = plan_for(service)
    permission = authorization(permission_reference, plan, 'LAUNCH')
    require(permission.get('all_eight_released') is True, 'coordinated_all8_released')
    released(service)
    receipt = shared.read(service/'RELEASED.json')
    if not receipt.get('final_custody_pending'):
        return None
    require(not (service/'FINAL_TIMERS_RETIRED.json').exists(), 'single_final_custody_retirement')
    retired = []
    for record in plan['old_timer_records']:
        expected_record = checked(record)['identity']
        expected = identity(expected_record['pid'])
        require(all(str(expected.get(key)) == str(value) for key,value in expected_record.items()),
            'authentic_old_timer_record')
        unused_old_FINAL(plan)
        cpu_only(expected)
        terminate_owned(expected, deadline=permission['expires_unix'])
        retired.append(dict(record=record, identity=expected, actual_eval_calls=0))
    shared.write(service/'FINAL_TIMERS_RETIRED.json', dict(release=ref(service/'RELEASED.json'),
        authorization=permission_reference, timers=retired, observed_unix=time.time()))
    return ref(service/'FINAL_TIMERS_RETIRED.json')


def stage(service, permission_reference, activation_directory, campaign_reference=None):
    service = Path(service)
    plan = plan_for(service)
    permission = authorization(permission_reference, plan, 'LAUNCH')
    require(permission.get('all_eight_released') is True, 'coordinated_all8_released')
    saved = released(service)
    session = client.prepare(previous.ready.COMMON_ROOT, plan['branch'])
    require(session['checkpoint_sha256'] == saved['checkpoint_sha256'] == permission['checkpoint_sha256'],
            'restore_exact_last_genuine_common_commit')
    directory = Path(activation_directory)
    require(directory.is_absolute() and not directory.is_relative_to(Path(session['shared_root']))
            and str(directory) == permission['activation_directory'], 'Main_activation_inbox_outside_COMMON')
    if campaign_reference is not None:
        campaign, unused_control = hook.campaign_document(campaign_reference['path'], campaign_reference['sha256'])
        require(campaign['root'] == session['shared_root']
            and campaign['activation_directory'] == str(directory)
            and campaign['deadline_unix'] <= TRAIN_END, 'same_Main_bounded_autoarm_campaign')
    retire_final_timers(service, permission_reference)
    runtime = dict(schema='R118_MATH_FRESH_EXEC_RUNTIME_V1', plan=ref(service/'PLAN.json'),
        release=ref(service/'RELEASED.json'), authorization=permission_reference, session=session,
        next_cycle=saved['next_cycle'], carry=saved['carry'], inherited_bounds=plan['inherited_bounds'],
        activation_directory=str(directory), campaign=campaign_reference, train_end_unix=TRAIN_END, local_optimizer_steps=0,
        bootstrap_path=str(Path(plan['root'])/'R118_PARALLEL_BOOTSTRAP.json'),
        seed_contract='Herschel bootstrap_fresh_actor: fixed SESSION hash/rank; once after canonical load',
        old_peer_rng_preserved=False, F1_optimizer_and_rng='OWNER_EXACT_RESTORE_REQUIRED')
    shared.write(service/'RUNTIME.json', runtime)
    return ref(service/'RUNTIME.json')


def owner_envelope(service):
    service = Path(service)
    plan = plan_for(service)
    saved = released(service)
    runtime = shared.read(service/'RUNTIME.json') if (service/'RUNTIME.json').exists() else None
    root = Path(plan['root'])
    old = checked(plan['old_drain_plan'])
    used = saved['counters']
    original = plan['inherited_bounds']
    bounds = dict(train_end_unix=TRAIN_END, hard_end_unix=original['hard_end_unix'],
        native_used=used['native'], native_cap=original['native_calls'],
        parent_used=used['parent'], parent_cap=original['parent_calls'])
    envelope = dict(root=str(root), bounds=bounds, release=ref(service/'RELEASED.json'),
        predecessors=[boundary.minimal_identity(old['native']), boundary.minimal_identity(old['guard'])],
        preserved_files=saved['preserved_files'], next_cycle=saved['next_cycle'])
    if (service/'OWNER_HANDOFF.json').exists():
        require(shared.read(service/'OWNER_HANDOFF.json') == envelope, 'no_changed_owner_envelope')
    else:
        shared.write(service/'OWNER_HANDOFF.json', envelope)
    manifest = checked(plan['source_manifest'])
    rank = hook.BRANCHES.index(plan['branch'])
    evidence = dict(committed_checkpoint_sha256=saved['checkpoint_sha256'], mounted_checkpoint_sha256=saved['checkpoint_sha256'],
            fresh_dev=ref(root/'readouts'/f"cycle_{saved['next_cycle']-1:03d}"/'COMPLETE.json'),
            settled_cursor=ref(root/'PROGRESS.json')) if saved.get('kind') != 'CRASHED_POSTCOMMIT' else dict(
                kind='CRASHED_POSTCOMMIT', committed_checkpoint_sha256=saved['checkpoint_sha256'],
                mounted_checkpoint_sha256=None, canonical_reload_required=True,
                postcommit_eval_disposition=saved['disposition'], settled_cursor=saved['settled_cursor'])
    owner = dict(root=str(root), handoff=ref(service/'OWNER_HANDOFF.json'), inherited_bounds=bounds,
        boundary=evidence,
        command=[previous.math.PYTHON,'-B','-m',MODULE,'guard','--service',str(service)], cwd=str(SOURCE),
        env=dict(CUDA_VISIBLE_DEVICES='', PYTHONPATH=str(SOURCE), PYTHONDONTWRITEBYTECODE='1',
            OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1'),
        source_files={str(SOURCE/name):digest for name,digest in manifest.items()},
        bootstrap_path=str(root/'R118_PARALLEL_BOOTSTRAP.json'), runtime_staged=runtime is not None,
        device=dict(kind='cuda', physical=rank, uuid=previous.math.policy.DEVICES[rank]))
    filename = 'FRESH_OWNER.json' if runtime is not None else 'FRESH_OWNER_PREPARED_'+plan['source_manifest']['sha256'][:16]+'.json'
    shared.write(service/filename, owner)
    return ref(service/filename)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('prepare','release','crash-release','stage','owner-envelope'))
    parser.add_argument('--branch', choices=('F2','A2'))
    parser.add_argument('--service', type=Path)
    parser.add_argument('--authorization', type=Path)
    parser.add_argument('--activation-directory', type=Path)
    parser.add_argument('--campaign', type=Path)
    parser.add_argument('--old-drain-plan', type=Path)
    parser.add_argument('--old-eval-plan', type=Path)
    parser.add_argument('--source-manifest', type=Path)
    parser.add_argument('--tests', type=Path)
    args = parser.parse_args()
    if args.phase == 'prepare':
        result = prepare(args.branch, ref(args.old_drain_plan), ref(args.old_eval_plan),
            ref(args.source_manifest), ref(args.tests))
    elif args.phase == 'release':
        result = release(args.service, ref(args.authorization))
    elif args.phase == 'crash-release':
        from gpu import orch_math_feedback_uptake_r118_parallel_crash as crash
        result = crash.release(args.service, ref(args.authorization))
    elif args.phase == 'stage':
        result = stage(args.service, ref(args.authorization), args.activation_directory,
            ref(args.campaign) if args.campaign else None)
    else:
        result = owner_envelope(args.service)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
