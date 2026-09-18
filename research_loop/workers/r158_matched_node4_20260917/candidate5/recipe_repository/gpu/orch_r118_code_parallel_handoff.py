"""Future Main-authorized CODE release; never infers release from cycle COMPLETE."""

from copy import deepcopy
import argparse
import os
from pathlib import Path
import select
import signal
import time

from gpu import orch_r108_code_parent_r118_activate as previous
from gpu import orch_r108_code_parent_r118_final as final
from gpu import orch_r108_code_parent_r118_final_release as identities


io = previous.client.coordinator
require = io.require
TRAIN_END = 1789491600
HARD_END = 1789491720
SCHEMA = 'R118_CODE_PARALLEL_AUTHORIZATION_V1'


def ref(path):
    return dict(path=str(Path(path).resolve(strict=True)), sha256=io.sha(path))


def checked(reference):
    require(io.sha(reference['path']) == reference['sha256'], 'immutable_reference_changed')
    return io.read(reference['path'])


def alive(identity):
    path = Path('/proc') / str(identity['pid'])
    if not path.exists():
        return False
    if identities.identity(identity['pid']) != identity:
        return False
    return path.joinpath('stat').read_text().rsplit(') ', 1)[1].split()[0] != 'Z'


def collective_identity(identity):
    require(alive(identity), 'actual_live_collective_identity')
    fields = (Path('/proc') / str(identity['pid']) / 'stat').read_text().rsplit(') ', 1)[1].split()
    return dict(boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
        pid=identity['pid'], start_ticks=int(fields[19]))


def authorize(reference, root, action, clock=time.time):
    document = checked(reference)
    root = Path(root).resolve(strict=True)
    plan = io.read(root / 'PLAN.json')
    branch = {2: 'F3', 6: 'A3'}.get(plan['physical'])
    require(document['schema'] == SCHEMA and document['status'] == 'MAIN_ALL8_COORDINATED_GO'
        and document['action'] == action and set(document['branches']) == set(io.BRANCHES),
        'explicit_Main_all8_not_worker_readiness')
    own = document['branches'][branch]
    require(own['root'] == str(root) and own['plan_sha256'] == io.sha(root / 'PLAN.json'),
        'exact_owned_CODE_authorization')
    require(document['issued_unix'] <= clock() < document['expires_unix'] <= TRAIN_END,
        'finite_Main_authorization')
    return document, own, plan


def ledger(root):
    root = Path(root)
    files = sorted((root / 'reservations').glob('*.json'))
    train = []
    for path in files:
        if path.name.startswith('C'):
            row = io.read(path)
            require(row['split'] == 'TRAIN' and row['kind'] in ('NATIVE', 'PARENT'), 'known_TRAIN_ledger')
            train.append((path, row))
        else:
            require(path.name.startswith('R'), 'unknown_ledger_name_no_guess')
    parents = sum(row['kind'] == 'PARENT' for path, row in train)
    return dict(preserved={str(path.relative_to(root)): io.sha(path) for path in files},
        native_used=len(files) - parents, parent_used=parents), train


def parents_settled(root, train):
    root = Path(root)
    for path, row in train:
        if row['kind'] != 'PARENT':
            continue
        if row['status'] not in ('COMPLETE', 'SILENT', 'MISSING', 'FAILED'):
            return False
        request = root / 'parent_queue' / (row['id'] + '.request.json')
        if request.exists() and not (root / 'parent_claude' / (row['id'] + '.claim') / 'PUBLISHED.json').exists():
            return False
    return True


def readout_settled(root, cycle):
    root = Path(root)
    complete = root / 'readouts' / f'C{cycle:03d}_DEV' / 'COMPLETE.json'
    binding_path = root / 'shared_readout_bindings' / f'C{cycle:03d}_DEV.json'
    if not complete.exists() or not binding_path.exists():
        return None
    terminal = io.read(complete)
    require(terminal['cycle'] == cycle and terminal['scope'] == 'DEV' and terminal['fresh_process'] is True
        and terminal['optimizer_steps'] == 0 and terminal['sleep_buffer_rows'] == 0, 'actual_DEV_terminal')
    expected = [f'R{cycle:03d}_DEV_{scope}_{index}.json'
        for scope, count in (('DEV', 8), ('FOCUS', 2), ('OLD', 16), ('AUDIT', 2)) for index in range(count)]
    files = []
    for name in expected:
        path = root / 'reservations' / name
        if not path.exists():
            return None
        row = io.read(path)
        if row['status'] not in ('COMPLETE', 'FAILED'):
            return None
        require(row['kind'] == 'NATIVE' and row['split'] != 'TRAIN'
            and not row['routes']['parent'] and not row['routes']['sleep'], 'readout_never_experience')
        files.append(path)
    dev_first = io.read(root / 'reservations' / expected[0])
    if dev_first['status'] == 'COMPLETE':
        opened = root / 'reservations' / f'R{cycle:03d}_DEV_DEV_OPEN.json'
        if not opened.exists() or io.read(opened)['status'] not in ('COMPLETE', 'FAILED'):
            return None
        files.append(opened)
        if io.read(opened)['status'] == 'COMPLETE':
            environment = root / 'environment' / f'R{cycle:03d}_DEV_DEV_OPEN.json'
            if not environment.exists():
                return None
            if io.read(environment)['observation']['status'] != 'NO_ENVIRONMENT_ACTION':
                observed = root / 'reservations' / f'R{cycle:03d}_DEV_DEV_OPEN_OBSERVE.json'
                if not observed.exists() or io.read(observed)['status'] not in ('COMPLETE', 'FAILED'):
                    return None
                files.append(observed)
    return dict(complete=ref(complete), binding=ref(binding_path),
        preserved={str(path.relative_to(root)): io.sha(path) for path in files}, all_scheduled_cases_settled=True)


def live_children(native):
    directory = Path('/proc') / str(native['pid'])
    result = []
    for identifier in (directory / 'task' / str(native['pid']) / 'children').read_text().split():
        try:
            value = identities.identity(int(identifier))
            if alive(value):
                command = (Path('/proc') / identifier / 'cmdline').read_bytes().split(b'\0')
                result.append((value, command))
        except FileNotFoundError:
            continue
    return result


def exited_children(native):
    directory = Path('/proc') / str(native['pid'])
    result = []
    for identifier in (directory / 'task' / str(native['pid']) / 'children').read_text().split():
        try:
            fields = (Path('/proc') / identifier / 'stat').read_text().rsplit(') ', 1)[1].split()
            if fields[0] == 'Z':
                result.append(dict(identity=identities.identity(int(identifier)), wait_status=int(fields[49])))
        except FileNotFoundError:
            continue
    return result


def boundary(root, common, *, children=()):
    root, common = Path(root), Path(common)
    if children or final.prior_final_attempts(root):
        return None
    charged, train = ledger(root)
    if not train or any(row['status'] == 'STARTED' for path, row in train) or not parents_settled(root, train):
        return None
    for path in (root / 'reservations').glob('R*.json'):
        if '_FINAL_' not in path.name and io.read(path).get('status') not in ('COMPLETE', 'FAILED'):
            return None
    cycle = max(row['cycle'] for path, row in train)
    completed = root / 'cycles' / f'C{cycle:03d}_COMPLETE.json'
    slept = root / 'shared_cycles' / f'C{cycle:03d}' / 'SHARED_SLEEP.json'
    if not completed.exists() or not slept.exists():
        return None
    dev = readout_settled(root, cycle)
    if dev is None:
        return None
    state = io.read(common / 'STATE.json')
    require(state['generation'] > 0 and io.read(slept)['state'] == state
        and io.read(completed)['shared_generation'] == state['generation'], 'latest_committed_CODE_cycle')
    submitted_path = root / 'shared_cycles' / f'C{cycle:03d}' / 'SHARED_SUBMISSION.json'
    submitted = io.read(submitted_path)
    require(io.sha(submitted['path']) == submitted['sha256'], 'actual_CODE_submission_hash')
    submission = io.read(submitted['path'])
    branch = {2: 'F3', 6: 'A3'}[io.read(root / 'PLAN.json')['physical']]
    require(Path(submitted['path']) == common / f"generation_{state['generation'] - 1:06d}" / (branch + '.json')
        and submission['branch'] == branch and submission['generation'] == state['generation'] - 1
        and len(submission['episode_ids']) == len(set(submission['episode_ids'])) == 2,
        'two_actual_CODE_episodes_before_cursor')
    expected_ids = [task['task_id'] for task in previous.client.run.policy.tasks('TRAIN')[(cycle - 1) * 2:cycle * 2]]
    require(submission['episode_ids'] == expected_ids and len(expected_ids) == 2,
        'exact_original_scheduled_TRAIN_order')
    previous_sleep = common / f"generation_{state['generation'] - 1:06d}" / 'sleep' / 'COMPLETE.json'
    require(io.read(previous_sleep)['state'] == state and io.read(previous_sleep)['same_optimizer'] is True,
        'actual_common_commit')
    current = common / f"generation_{state['generation']:06d}" / 'sleep'
    require(not (current / 'START.json').exists(), 'no_running_or_failed_sleep_migration')
    dev_binding = checked(dev['binding'])
    require(dev_binding['state'] == state and dev_binding['checkpoint'] == state['checkpoint'],
        'DEV_matches_latest_committed_child')
    require(not any((root / 'reservations').glob(f'C{cycle + 1:03d}_*.json')), 'next_cursor_already_charged')
    parent_settings = [(row['finished_unix'], path, row) for path, row in train if row.get('reflection_settings')]
    require(parent_settings, 'actual_reflection_carry_required')
    unused, carry_path, carry_row = max(parent_settings, key=lambda item: item[0])
    preserved = dict(charged['preserved'])
    for path in (root / 'PLAN.json', root / 'SHARED_ACTIVATION.json', root / 'COHORT.json', completed, slept,
                 carry_path, submitted_path):
        preserved[str(path.relative_to(root))] = io.sha(path)
    for folder in ('parent_queue', 'parent_claude', 'triples', 'environment'):
        for path in (root / folder).rglob('*'):
            if path.is_file():
                preserved[str(path.relative_to(root))] = io.sha(path)
    preserved.update(dev['preserved'])
    for reference in (dev['complete'], dev['binding']):
        preserved[str(Path(reference['path']).relative_to(root))] = reference['sha256']
    return dict(cycle=cycle, next_cycle=cycle + 1, state=state, state_reference=ref(common / 'STATE.json'),
        dev=dev, preserved_files=preserved, charges={key: charged[key] for key in ('native_used', 'parent_used')},
        carry=dict(reflection_settings=deepcopy(carry_row['reflection_settings']), source=ref(carry_path)),
        train_registry_sha256=previous.client.run.policy.digest(previous.client.run.policy.tasks('TRAIN')),
        charged_replay=False, all_pending_DEV_settled=True)


def hold_release(expected, root, common, *, authorization, grace_seconds=120, clock=time.time, pause=time.sleep):
    unused, own, unused_plan = authorize(authorization, root, 'DRAIN', clock)
    mode = own.get('boundary_mode', 'COMMITTED_CYCLE')
    require(mode in ('COMMITTED_CYCLE', 'SETTLED_PENDING_CONSOLIDATION'), 'explicit_CODE_boundary_mode')
    require(type(grace_seconds) is int and 0 < grace_seconds <= 180, 'bounded_async_settlement')
    require(alive(expected), 'exact_owned_actor')
    descriptor = os.pidfd_open(expected['pid'])
    held, released = False, False
    try:
        require(alive(expected), 'exact_actor_after_pidfd')
        signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
        held = True
        end = min(clock() + grace_seconds, checked(authorization)['expires_unix'])
        for unused in range(100):
            state = (Path('/proc') / str(expected['pid']) / 'stat').read_text().rsplit(') ', 1)[1].split()[0]
            if state in ('T', 't'):
                break
            pause(.01)
        require(state in ('T', 't'), 'actor_hold_observed')
        while clock() < end:
            authorize(authorization, root, 'DRAIN', clock)
            children = live_children(expected)
            for identity, command in children:
                require(str(root).encode() in command and b'readout' in command
                    and b'gpu.orch_r108_code_parent_r116_shared_run' in command, 'only_own_existing_async_DEV_child')
            if mode == 'SETTLED_PENDING_CONSOLIDATION':
                from gpu import orch_r118_code_parallel_pending as pending
                candidate = None if children else pending.snapshot(root, common)
            else:
                candidate = boundary(root, common, children=children)
            if candidate is not None:
                exits = exited_children(expected)
                require(all(row['wait_status'] == 0 for row in exits), 'readout_child_nonzero_exit_preserved')
                candidate['readout_exit_custody'] = dict(observed_zombies=exits,
                    reaped_exit_status_available=False, terminal_cells_verified=True)
                require(alive(expected), 'exact_clean_actor')
                signal.pidfd_send_signal(descriptor, signal.SIGTERM)
                signal.pidfd_send_signal(descriptor, signal.SIGCONT)
                held = False
                released = True
                exited = select.select([descriptor], [], [], 5)[0]
                if not exited:
                    signal.pidfd_send_signal(descriptor, signal.SIGKILL)
                    exited = select.select([descriptor], [], [], 2)[0]
                require(exited, 'clean_actor_exit')
                return dict(identity=expected, boundary=candidate, released_unix=clock(),
                    authorization=authorization, not_natural_completion=True)
            if children:
                pause(.25)
            else:
                return None
        return None
    finally:
        if held and not released:
            try:
                signal.pidfd_send_signal(descriptor, signal.SIGCONT)
            except ProcessLookupError:
                pass
        os.close(descriptor)


def release(root, output, authorization, *, clock=time.time, pause=time.sleep):
    root, output = Path(root).resolve(strict=True), Path(output)
    document, own, plan = authorize(authorization, root, 'DRAIN', clock)
    require(not output.exists(), 'new_handoff_attempt_no_overwrite')
    require(output.resolve().is_relative_to(root), 'new_release_sidecar_under_owned_root')
    native = io.read(root / 'R118_SHARED_NATIVE_LAUNCH.json')['identity']
    guardian = identities.identity(io.read(root / 'R118_SHARED_GUARD_DISPATCH.json')['guard_pid'])
    require(native == own['native_identity'] and guardian == own['guardian_identity']
        and alive(native) and alive(guardian), 'Main_pinned_actual_predecessors')
    for identity, module, role in ((native, b'gpu.orch_r108_code_parent_r118_activate', b'native'),
            (guardian, b'gpu.orch_r108_code_parent_r118_activate', b'guard')):
        command = (Path('/proc') / str(identity['pid']) / 'cmdline').read_bytes().split(b'\0')
        require(str(root).encode() in command and module in command and role in command,
            'original_exact_CODE_role_and_root')
    parent_pid = (Path('/proc') / str(native['pid']) / 'stat').read_text().rsplit(') ', 1)[1].split()[1]
    require(int(parent_pid) == guardian['pid'] and guardian['uid'] == native['uid'], 'actual_guard_parent_UID')
    output.mkdir(parents=True)
    io.write(output / 'START.json', dict(authorization=authorization, native=native, guardian=guardian,
        started_unix=clock(), original_plan=ref(root / 'PLAN.json')))
    result = hold_release(native, root, own['common_root'], authorization=authorization, clock=clock, pause=pause)
    if result is None:
        io.write(output / 'NOT_RELEASED.json', dict(reason='NO_SETTLED_CURSOR', resume_unchanged=True, observed_unix=clock()))
        return None
    end = min(clock() + 30, document['expires_unix'])
    while alive(guardian) and clock() < end:
        pause(.25)
    require(not alive(guardian), 'original_guard_must_exit_naturally')
    for name, expected in result['boundary']['preserved_files'].items():
        require(io.sha(root / name) == expected, 'preserved_at_actual_exit')
    if result['boundary'].get('kind') == 'SETTLED_PENDING_CONSOLIDATION':
        from gpu import orch_r118_code_parallel_pending as pending
        verified = pending.snapshot(root, own['common_root'])
        require(verified['pending'] == result['boundary']['pending']
            and verified['state'] == result['boundary']['state'], 'pending_unchanged_after_exit')
        pending.publish(root, output, result['boundary'])
    receipt = dict(schema='R118_CODE_PARALLEL_RELEASE_V1', status='RELEASED', root=str(root), native=result,
        guardian=guardian, original_plan=ref(root / 'PLAN.json'), bounds={key: plan[key] for key in previous.client.BOUND_FIELDS},
        all_original_processes_exited=True, successor_started=False)
    io.write(output / 'HANDOFF.json', receipt)
    envelope = dict(result['boundary']['preserved_files'])
    envelope[str((output / 'HANDOFF.json').relative_to(root))] = io.sha(output / 'HANDOFF.json')
    bounds = dict(train_end_unix=min(TRAIN_END, plan['hard_deadline_unix']),
        hard_end_unix=min(HARD_END, plan['hard_deadline_unix'], plan['lease_end_unix'] - 21600),
        native_cap=plan['native_cap'], parent_cap=plan['parent_cap'], **result['boundary']['charges'])
    io.write(output / 'OWNER_RELEASE.json', dict(status='RELEASED', root=str(root), bounds=bounds,
        original_bounds=receipt['bounds'], release=ref(output / 'HANDOFF.json'),
        predecessors=[dict(value, start_ticks=int(value['start_ticks'])) for value in (native, guardian)],
        preserved_files=envelope, next_cycle=result['boundary']['next_cycle']))
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--authorization', required=True, type=Path)
    args = parser.parse_args()
    release(args.root, args.output, ref(args.authorization))
