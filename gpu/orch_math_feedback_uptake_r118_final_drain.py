"""Deadline-only math collection/readout boundary retirement; no import actions."""

import argparse
import fcntl
import os
from pathlib import Path
import select
import signal
import time

from gpu import orch_math_feedback_uptake_r118_final as io
from gpu import orch_r111_route_boundary as pinned


START = io.START - 300
LAST_ATTEMPT = io.START - 40
DIRECTORY = Path('/localhome/local-rohing/orch_math_feedback_uptake_r118_final_drain_20260915_attempt2')
PHASES = ('episode', 'open_turn', 'episode', 'open_turn', 'presleep', 'reflection')
require = io.require


def identity(pid):
    value = pinned.identity(pid)
    executable = (Path('/proc')/str(pid)/'exe').stat()
    return dict(value, exe_device=executable.st_dev, exe_inode=executable.st_ino)


def actual_process(expected, source, root, *, actor, uuid):
    actual = identity(expected['pid'])
    require(all(actual.get(name) == value for name, value in expected.items()), 'exact_recorded_process_identity')
    require(actual['uid'] == os.getuid() and actual['cwd'] == str(source), 'own_UID_and_frozen_cwd')
    directory = Path('/proc')/str(actual['pid'])
    command = (directory/'cmdline').read_bytes().split(b'\0')
    if actor:
        suffix = ['-m', 'gpu.orch_math_feedback_uptake_r118_shared_run', 'resident', '--root', str(root), '']
        require(command[-6:] == [part.encode() for part in suffix], 'exact_shared_actor_command')
    else:
        require(command[-3:] == [b'--root', str(root).encode(), b'']
                and Path(command[-4].decode()).name == 'orch_math_feedback_uptake_r118_shared_admit.py', 'exact_shared_guard_command')
    environment = (directory/'environ').read_bytes().split(b'\0')
    require(('CUDA_VISIBLE_DEVICES='+ (uuid if actor else '')).encode() in environment, 'exact_startup_CVD')
    require(('PYTHONPATH='+str(source)).encode() in environment, 'frozen_native_PYTHONPATH')
    return actual


def prepare(branch, previous_plan):
    require(time.time() < START and branch in io.MEMBERS, 'prospective_math_drain_only')
    prior = io.bound(previous_plan)
    physical, uuid = io.MEMBERS[branch]
    root = io.ORIGINAL/f'lane{physical}'
    require(prior['branch'] == branch and prior['original_root'] == str(root), 'unchanged_predecessor_root')
    for reference in prior['predecessor_refs'].values():
        io.bound(reference)
    repair = io.read(root/'R118_SHARED_ADMISSION_REPAIR_LAUNCH.json')
    source = Path(repair['native_source'])
    native = actual_process(io.read(root/'SHARED_LAUNCH.json')['identity'], source, root, actor=True, uuid=uuid)
    guard = actual_process(repair['identity'], source, root, actor=False, uuid=uuid)
    require(native['ppid'] == guard['pid'], 'actual_guard_native_parentage')
    timer_root = Path(prior['root'])
    timer_record = io.read(timer_root/'SCHEDULED.json')['identity']
    timer = identity(timer_record['pid'])
    require(all(timer[name] == value for name, value in timer_record.items())
            and timer['uid'] == os.getuid() and timer['cwd'] == prior['source_root'], 'actual_old_CPU_timer_identity')
    output = DIRECTORY/f'lane{physical}'
    output.mkdir(parents=True, exist_ok=False)
    plan = dict(schema='R118_MATH_FINAL_DRAIN_V1', branch=branch, root=str(root), output=str(output),
        previous_evaluation_plan=previous_plan, predecessor_refs=prior['predecessor_refs'],
        native=native, guard=guard, timer=timer, timer_root=str(timer_root), uuid=uuid, native_source=str(source),
        not_before_unix=START, last_attempt_unix=LAST_ATTEMPT, released_before_unix=io.START,
        original_bounds=prior['original_bounds'], local_optimizer_steps=0, owner='F1',
        authorization='Main 2026-09-15T13:41 deadline-only clean boundary drain; common TRAIN retirement16:55',
        source=io.ref(__file__), prepared_unix=time.time(), no_signals_during_prepare=True)
    io.write(output/'PLAN.json', plan)
    return io.ref(output/'PLAN.json')


def plan_check(reference):
    plan = io.bound(reference)
    require(plan['schema'] == 'R118_MATH_FINAL_DRAIN_V1' and plan['branch'] in io.MEMBERS, 'math_drain_scope')
    require(plan['source'] == io.ref(__file__), 'immutable_drain_source')
    require(plan['not_before_unix'] == START and plan['last_attempt_unix'] == LAST_ATTEMPT
            and plan['released_before_unix'] == io.START, 'fixed_deadline_only_drain_window')
    prior = io.bound(plan['previous_evaluation_plan'])
    require(plan['predecessor_refs'] == prior['predecessor_refs'] and plan['original_bounds'] == prior['original_bounds'],
            'preserved_original_and_evaluation_bounds')
    for item in plan['predecessor_refs'].values():
        io.bound(item)
    return plan


def live_children(pid):
    children = (Path('/proc')/str(pid)/'task'/str(pid)/'children').read_text().split()
    result = []
    for child in children:
        try:
            if pinned.process_state(int(child)) != 'Z':
                result.append(int(child))
        except (FileNotFoundError, ProcessLookupError):
            pass
    return result


def morning_attempts(root):
    paths = list((root/'sealed').glob('morning_final_*'))
    paths += list((root/'shared_readout_bindings').glob('morning_final_*'))
    for path in (root/'reservations').glob('native_*.json'):
        if io.read(path).get('metadata', {}).get('phase') == 'morning_final':
            paths.append(path)
    return paths


def snapshot(plan):
    root = Path(plan['root'])
    if live_children(plan['native']['pid']) or morning_attempts(root):
        return None
    cycles = sorted(root.glob('cycle[0-9][0-9][0-9]'))
    cycles = [path for path in cycles if list(path.iterdir())]
    if not cycles:
        return None
    output = cycles[-1]
    cycle = int(output.name[5:])
    trained = output/'TRAIN_COMPLETE.json'
    if not trained.exists() or (output/'TRAIN_FAILED.json').exists():
        return None
    trained_document = io.read(trained)
    submission = trained_document['submission']
    generation = trained_document['shared_generation']
    expected = io.COMMON/f'generation_{generation:06d}'/(plan['branch']+'.json')
    require(submission['path'] == str(expected) and io.sha(expected) == submission['sha256'], 'exact_accepted_common_submission')
    accepted = io.read(expected)
    ids = accepted['episode_ids']
    require(accepted['branch'] == plan['branch'] and accepted['generation'] == generation
            and len(ids) == len(set(ids)) == 2, 'two_actual_submitted_episodes')
    paths = sorted(path for path in output.glob('CALL_*.json') if not path.name.endswith('.request.json'))
    calls = [io.read(path) for path in paths]
    if len(calls) != 6 or any(call.get('status') != 'COMPLETE' for call in calls):
        return None
    require(tuple(call['phase'] for call in calls) == PHASES
            and [call['task_id'] for call in calls] == [ids[0]]*2+[ids[1]]*4, 'exact_two_episode_reflection_order')
    require(len(accepted['rows']) == 6
            and {row['source_call_sha256'] for row in accepted['rows']} == {io.sha(path) for path in paths},
            'all_actual_child_captures_in_submission')
    for path, call in zip(paths, calls):
        request = path.with_suffix('.request.json')
        require(io.sha(request) == call['request_sha256'] and call['split'] == 'TRAIN'
                and call['shared_generation'] == generation
                and call['shared_checkpoint_sha256'] == trained_document['shared_checkpoint_sha256'], 'actual_predispatch_source_binding')
    boundary = io.read(output/'BOUNDARY.json')
    require(io.digest(io.read(output/'TRAIN_EXPERIENCE.json')) == boundary['source_history_sha256']
            and boundary['own_reflection']['actor'] == 'child', 'source_backed_carry_preserved')
    reservations = sorted((root/'reservations').glob('*.json'))
    totals = dict(native=0, parent=0)
    parent_ids = []
    for kind in totals:
        for path in sorted((root/'reservations').glob(kind+'_*.json')):
            item = io.read(path)
            require(item['kind'] == kind and item['first'] == totals[kind]+1, 'all_original_charges_contiguous')
            totals[kind] += item['count']
            if kind == 'parent':
                parent_ids.append(item['metadata']['id'])
    counters = io.read(root/'COUNTERS.json')
    require(totals == counters, 'all_charged_reservations_accounted')
    current_parent_ids = [identifier for identifier in parent_ids if identifier.startswith(f'C{cycle:03d}_')]
    if len(current_parent_ids) != 6 or not parent_ids or not parent_ids[-1].startswith(f'C{cycle:03d}_'):
        return None
    parent_files = []
    for identifier in current_parent_ids:
        delivered = root/'delivered'/(identifier+'.json')
        request = root/'parent_queue'/(identifier+'.request.json')
        response = root/'parent_queue'/(identifier+'.response.json')
        if not delivered.exists() or not response.exists():
            return None
        document = io.read(delivered)
        require(document['id'] == identifier and document['request_sha256'] == io.digest(io.read(request)), 'completed_parent_delivery_join')
        provider = io.read(response)
        receipt = provider['transcript_receipt']
        require(Path(receipt['remote_root']) == root/'parent_transcripts'/identifier, 'closed_provider_archive_root')
        require(all(Path(name).name == name and io.sha(Path(receipt['remote_root'])/name) == expected
                    for name, expected in receipt['files'].items()), 'closed_provider_archive_hashes')
        parent_files.extend([delivered, request, response])
        archive = root/'parent_transcripts'/identifier
        if not archive.exists():
            return None
        parent_files.extend(path for path in archive.rglob('*') if path.is_file())
    state = io.read(io.COMMON/'STATE.json')
    require(state['config_sha256'] == io.COMMON_SHA, 'immutable_common_config')
    readout = root/'readouts'/f'cycle_{cycle:03d}'
    if not (output/'SHARED_SLEEP.json').exists():
        if state['generation'] != generation or state['checkpoint']['path_sha256'] != trained_document['shared_checkpoint_sha256']:
            return None
        if readout.exists() or (root/'shared_readout_bindings'/f'cycle_{cycle:03d}.json').exists():
            return None
        kind = 'COMPLETE_COLLECTION_ACCEPTED_WAITING_FOR_SHARED_CHECKPOINT'
    else:
        if not (output/'COMPLETE.json').exists() or not (readout/'COMPLETE.json').exists():
            return None
        complete = io.read(output/'COMPLETE.json')
        if complete['counters'] != counters:
            return None
        sleep = io.read(output/'SHARED_SLEEP.json')
        committed = io.COMMON/f'generation_{generation:06d}'/'sleep/COMPLETE.json'
        if not committed.exists():
            return None
        publication = io.read(committed)
        require(publication['state']['generation'] == generation+1 and publication['same_optimizer'] is True
                and sleep['publication'] == publication['state']['checkpoint']
                and complete['shared_generation'] == generation+1, 'actual_shared_committed_readout_checkpoint')
        require(io.read(readout/'COMPLETE.json')['actual_native'] == 20
                and io.read(readout/'COMPLETE.json')['shared_generation'] == generation+1
                and (readout/'AFTER.json').exists() and (readout/'MOUNTED_FINAL.json').exists(), 'actual_complete_fresh_DEV_boundary')
        readout_calls = sorted(path for path in readout.glob('CALL_*.json') if not path.name.endswith('.request.json'))
        require(len(readout_calls) == 20 and all(io.read(path)['status'] == 'COMPLETE' for path in readout_calls),
                'all_readout_attempts_complete_not_outcome_filter')
        paths += readout_calls
        kind = 'COMPLETE_SHARED_CHECKPOINT_AND_FRESH_DEV_CYCLE'
    if counters['native'] != max(int(path.stem.split('_')[1]) for path in paths):
        return None
    preserved = reservations + parent_files + [root/'COUNTERS.json', root/'LATEST_PARENT.json']
    preserved += [path for path in output.iterdir() if path.is_file()]
    if readout.exists():
        preserved += [path for path in readout.iterdir() if path.is_file()]
    files = {str(path.relative_to(root)): io.sha(path) for path in preserved}
    return dict(kind=kind, cycle=cycle, generation=generation, episode_ids=ids, counters=counters,
        common_submission=dict(path=str(expected), sha256=io.sha(expected)), carry=io.ref(output/'BOUNDARY.json'),
        preserved_files=files, reservation_names=[path.name for path in reservations],
        native_inflight=0, parent_wait_inflight=0, readout_children=0, local_optimizer_steps=0, observed_unix=time.time())


def release_window(now):
    require(START <= now < LAST_ATTEMPT, 'deadline_only_future_drain_clock_gate')


def safe_snapshot(plan):
    try:
        return snapshot(plan)
    except (FileNotFoundError, io.json.JSONDecodeError):
        return None


def held_release(plan, inspect, *, clock=time.time, pause=time.sleep):
    release_window(clock())
    descriptors, held = {}, set()
    try:
        for role in ('guard', 'native'):
            expected = plan[role]
            require(identity(expected['pid']) == expected and expected['uid'] == os.getuid(), 'exact_own_process_before_pidfd')
            descriptors[role] = os.pidfd_open(expected['pid'])
            require(identity(expected['pid']) == expected, 'exact_process_after_pidfd')
        for role in ('guard', 'native'):
            release_window(clock())
            require(identity(plan[role]['pid']) == plan[role], 'exact_process_before_hold')
            signal.pidfd_send_signal(descriptors[role], signal.SIGSTOP)
            held.add(role)
            for observation in range(100):
                if pinned.process_state(plan[role]['pid']) in ('T', 't'):
                    break
                pause(.01)
            else:
                raise ValueError('bounded_hold_not_observed')
        boundary = inspect()
        if boundary is None or clock() >= LAST_ATTEMPT:
            return None
        io.write(Path(plan['output'])/'BOUNDARY.json', boundary)
        for role in ('native', 'guard'):
            require(identity(plan[role]['pid']) == plan[role], 'exact_identity_before_release')
            signal.pidfd_send_signal(descriptors[role], signal.SIGTERM)
            signal.pidfd_send_signal(descriptors[role], signal.SIGCONT)
            held.discard(role)
            exited = bool(select.select([descriptors[role]], [], [], 8)[0])
            if not exited:
                signal.pidfd_send_signal(descriptors[role], signal.SIGKILL)
                exited = bool(select.select([descriptors[role]], [], [], 3)[0])
            require(exited, 'owned_deadline_boundary_exit_required')
        require(clock() < io.START, 'release_completed_before_legacy_FINAL')
        return boundary
    finally:
        for role in tuple(held):
            try:
                signal.pidfd_send_signal(descriptors[role], signal.SIGCONT)
            except ProcessLookupError:
                pass
        for descriptor in descriptors.values():
            os.close(descriptor)


def verify_snapshot(plan, boundary):
    root = Path(plan['root'])
    require(io.read(root/'COUNTERS.json') == boundary['counters'], 'no_post_release_charges')
    require(sorted(path.name for path in (root/'reservations').glob('*.json')) == boundary['reservation_names'], 'no_extra_original_reservations')
    for name, expected in boundary['preserved_files'].items():
        require(io.sha(root/name) == expected, 'preserved_source_or_carry_changed')
    require(io.sha(boundary['common_submission']['path']) == boundary['common_submission']['sha256'], 'accepted_submission_preserved')


def validate_release(reference):
    plan = plan_check(reference)
    output = Path(plan['output'])
    receipt = io.read(output/'RELEASED.json')
    require(receipt['plan'] == reference and receipt['status'] == 'RELEASED'
            and START <= receipt['released_unix'] < io.START, 'actual_deadline_release_receipt')
    require(all(not io.same_process(plan[role]) for role in ('native', 'guard')), 'old_native_guard_still_present')
    require(not live_readout_identities(Path(plan['root'])), 'old_readout_still_present')
    boundary = io.bound(receipt['boundary'])
    verify_snapshot(plan, boundary)
    require(not morning_attempts(Path(plan['root'])), 'no_legacy_FINAL_attempt')
    io.bound(receipt['authentic_guard_terminal'])
    timer = io.bound(receipt['previous_timer_retirement'])
    require(timer['identity'] == plan['timer'] and timer['actual_eval_calls'] == 0
            and not io.same_process(plan['timer']), 'old_eval_timer_retired_not_replayed')
    return dict(plan=reference, receipt=io.ref(output/'RELEASED.json'), boundary=receipt['boundary'],
                identities=[plan['native'], plan['guard']], observed_unix=time.time())


def live_readout_identities(root):
    return [io.read(path) for path in (root/'shared_readout_bindings').glob('*.process.json') if io.same_process(io.read(path))]


def retire_timer(plan, *, clock=time.time):
    release_window(clock())
    root = Path(plan['timer_root'])
    require(not (root/'LEDGER.json').exists() and not (root/'NATIVE_CLAIM.json').exists(), 'old_timer_zero_evaluation_calls')
    expected = plan['timer']
    signalled = False
    if io.same_process(expected):
        require(identity(expected['pid']) == expected and expected['uid'] == os.getuid(), 'exact_own_CPU_timer_before_retirement')
        directory = Path('/proc')/str(expected['pid'])
        require(b'CUDA_VISIBLE_DEVICES=' in (directory/'environ').read_bytes().split(b'\0'), 'CPU_timer_empty_startup_CVD')
        require(not any(os.readlink(path).startswith('/dev/nvidia') for path in (directory/'fd').iterdir()), 'CPU_timer_no_GPU_descriptors')
        arguments = (directory/'cmdline').read_bytes().split(b'\0')
        require(arguments[-6:] == [b'-m', io.MODULE.encode(), b'schedule', b'--root', str(root).encode(), b''], 'exact_old_eval_timer_command')
        descriptor = os.pidfd_open(expected['pid'])
        try:
            require(identity(expected['pid']) == expected, 'CPU_timer_identity_after_pidfd')
            release_window(clock())
            signal.pidfd_send_signal(descriptor, signal.SIGTERM)
            signalled = True
            exited = bool(select.select([descriptor], [], [], 8)[0])
            if not exited:
                signal.pidfd_send_signal(descriptor, signal.SIGKILL)
                exited = bool(select.select([descriptor], [], [], 3)[0])
            require(exited, 'old_CPU_timer_exit')
        finally:
            os.close(descriptor)
    require(not io.same_process(expected) and not (root/'LEDGER.json').exists()
            and not (root/'NATIVE_CLAIM.json').exists(), 'no_duplicate_old_eval_after_timer_retirement')
    receipt = dict(identity=expected, cpu_only=True, signalled=signalled, retired_unix=clock(),
                   previous_plan=plan['previous_evaluation_plan'], original_native_signals=0, actual_eval_calls=0)
    io.write(Path(plan['output'])/'PREVIOUS_TIMER_RETIRED.json', receipt)
    return receipt


def run(reference):
    plan = plan_check(reference)
    root, output = Path(plan['root']), Path(plan['output'])
    with (output/'CONTROLLER.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        io.write(output/'ARMED.json', dict(identity=identity(os.getpid()), plan=reference, armed_unix=time.time(),
            no_current_native_signals=True, not_before_unix=START))
        while time.time() < START:
            time.sleep(max(0, min(15, START-time.time())))
        try:
            retire_timer(plan)
            while time.time() < LAST_ATTEMPT:
                if not all(io.same_process(plan[role]) for role in ('guard', 'native')):
                    break
                if safe_snapshot(plan) is None:
                    time.sleep(5)
                    continue
                with (root/'COUNTERS.lock').open('a') as counters_lock:
                    try:
                        fcntl.flock(counters_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    except BlockingIOError:
                        continue
                    boundary = held_release(plan, lambda: safe_snapshot(plan))
                if boundary is None:
                    time.sleep(5)
                    continue
                verify_snapshot(plan, boundary)
                terminal = root/'SHARED_TERMINAL.json'
                require(terminal.exists(), 'authentic_guard_terminal_required_no_fabrication')
                io.write(output/'RELEASED.json', dict(status='RELEASED', plan=reference,
                    boundary=io.ref(output/'BOUNDARY.json'), authentic_guard_terminal=io.ref(terminal),
                    previous_timer_retirement=io.ref(output/'PREVIOUS_TIMER_RETIRED.json'),
                    released_unix=time.time(), deadline_not_outcome_stop=True, old_caps_unchanged=True,
                    lost_local_optimizer=False, no_replay=True, no_natural_completion_claim=True))
                return validate_release(reference)
            io.write(output/'NOT_RUN.json', dict(status='NOT_RUN', reason='NO_VERIFIED_CLEAN_BOUNDARY_BEFORE_LEGACY_FINAL',
                observed_unix=time.time(), original_evidence_preserved=True, no_new_eval_calls=True))
        except BaseException as error:
            io.write(output/'NOT_RUN.json', dict(status='NOT_RUN', reason=type(error).__name__+':'+str(error),
                observed_unix=time.time(), original_evidence_preserved=True, no_new_eval_calls=True))
            raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'run'))
    parser.add_argument('--branch', choices=tuple(io.MEMBERS))
    parser.add_argument('--plan', type=Path)
    parser.add_argument('--previous-evaluation', type=Path)
    args = parser.parse_args()
    if args.phase == 'prepare':
        print(io.json.dumps(prepare(args.branch, io.ref(args.previous_evaluation))))
    else:
        run(io.ref(args.plan))
