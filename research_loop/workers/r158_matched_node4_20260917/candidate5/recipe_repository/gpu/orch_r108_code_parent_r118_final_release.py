"""Future CODE-only completed-collection drain with exact pidfd custody."""

import os
from pathlib import Path
import select
import signal
import time

from gpu import orch_r108_code_parent_r118_activate as activation


io = activation.client.coordinator
require = io.require
CUT = 1789491600
RELEASE_START = CUT - 300


def identity(pid):
    return activation.original.scanner.pinned.identity(Path('/proc') / str(pid))


def ref(path):
    return dict(path=str(path), sha256=io.sha(path))


def prepare(root, original):
    root, original = Path(root), Path(original)
    launched = io.read(original / 'R118_SHARED_NATIVE_LAUNCH.json')
    dispatched = io.read(original / 'R118_SHARED_GUARD_DISPATCH.json')
    native = launched['identity']
    require(identity(native['pid']) == native, 'exact_live_CODE_native')
    guardian = identity(dispatched['guard_pid'])
    command = (Path('/proc') / str(guardian['pid']) / 'cmdline').read_bytes().split(b'\0')
    parent = (Path('/proc') / str(native['pid']) / 'stat').read_text().rsplit(') ', 1)[1].split()[1]
    require(guardian['uid'] == native['uid'] and int(parent) == guardian['pid']
        and str(original).encode() in command and b'gpu.orch_r108_code_parent_r118_activate' in command
        and b'guard' in command, 'exact_recorded_CODE_guardian_parent')
    plan = dict(schema='R118_CODE_FINAL_RELEASE_PLAN_V1', original_root=str(original),
        native_identity=native, guardian_identity=guardian,
        native_launch=ref(original / 'R118_SHARED_NATIVE_LAUNCH.json'),
        guard_dispatch=ref(original / 'R118_SHARED_GUARD_DISPATCH.json'),
        original_plan=ref(original / 'PLAN.json'), activation=ref(original / 'SHARED_ACTIVATION.json'),
        not_before_unix=RELEASE_START, stop_attempts_before_unix=CUT,
        prepared_unix=time.time(), optimizer_owner='F1', local_optimizer_steps=0)
    io.write(root / 'RELEASE_PLAN.json', plan)
    return plan


def collection_boundary(original, native_pid):
    original = Path(original)
    if (original / 'SHARED_TERMINAL.json').exists():
        return None
    children = Path('/proc') / str(native_pid) / 'task' / str(native_pid) / 'children'
    for child in children.read_text().split():
        try:
            state = (Path('/proc') / child / 'stat').read_text().rsplit(') ', 1)[1].split()[0]
        except FileNotFoundError:
            continue
        if state != 'Z':
            return None
    if any((original / 'readouts').glob('C*_FINAL')):
        return None
    calls = [(path, io.read(path)) for path in (original / 'reservations').glob('C*.json')]
    if not calls or any(row['status'] == 'STARTED' for path, row in calls):
        return None
    cycle = max(row['cycle'] for path, row in calls)
    submitted = original / 'shared_cycles' / f'C{cycle:03d}' / 'SHARED_SUBMISSION.json'
    if not submitted.exists():
        return None
    submission = io.read(submitted)
    if io.sha(submission['path']) != submission['sha256']:
        raise ValueError('actual_common_submission_changed')
    adopted = io.read(original / 'SHARED_ACTIVATION.json')['shared_learner']
    expected = Path(adopted['root']) / f"generation_{submission['generation']:06d}" / (adopted['branch'] + '.json')
    require(Path(submission['path']) == expected, 'own_actual_common_submission')
    common_receipt = io.read(expected)
    require(common_receipt['branch'] == adopted['branch'] and len(set(common_receipt['episode_ids'])) == 2,
        'two_completed_scheduled_episodes')
    for path, row in calls:
        if row['cycle'] == cycle and row['kind'] == 'PARENT':
            if not (original / 'parent_claude' / (row['id'] + '.claim') / 'PUBLISHED.json').exists():
                return None
    return dict(cycle=cycle, submission=ref(submitted), common_submission=submission,
        train_calls_inflight=0, parents_inflight=0, live_readout_children=0,
        preserved_reservations={path.name:io.sha(path) for path in (original / 'reservations').glob('*.json')})


def drained_process(expected, inspect, *, clock=time.time, pause=time.sleep):
    require(RELEASE_START <= clock() < CUT - 10, 'future_CODE_release_clock_gate')
    require(identity(expected['pid']) == expected, 'exact_owned_native_before_hold')
    descriptor = os.pidfd_open(expected['pid'])
    held = False
    terminated = False
    try:
        require(identity(expected['pid']) == expected, 'exact_owned_native_after_pidfd')
        signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
        held = True
        stopped = False
        for unused in range(100):
            state = (Path('/proc') / str(expected['pid']) / 'stat').read_text().rsplit(') ', 1)[1].split()[0]
            if state in ('T', 't'):
                stopped = True
                break
            pause(.01)
        require(stopped, 'owned_native_hold_observed')
        boundary = inspect()
        if boundary is None or clock() >= CUT - 10:
            return None
        require(identity(expected['pid']) == expected, 'exact_owned_native_at_clean_boundary')
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
        signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        held = False
        terminated = True
        readable, unused_write, unused_error = select.select([descriptor], [], [], 5)
        if not readable:
            signal.pidfd_send_signal(descriptor, signal.SIGKILL)
            readable, unused_write, unused_error = select.select([descriptor], [], [], 2)
        require(bool(readable), 'owned_boundary_process_exited')
        return dict(boundary=boundary, identity=expected, released_unix=clock(),
            reason='COMPLETED_COLLECTION_BOUNDARY_FINAL_DRAIN', not_natural_completion=True)
    finally:
        if held and not terminated:
            try:
                signal.pidfd_send_signal(descriptor, signal.SIGCONT)
            except ProcessLookupError:
                pass
        os.close(descriptor)


def validate_release(root):
    root = Path(root)
    plan = io.read(root / 'RELEASE_PLAN.json')
    receipt = io.read(root / 'PREDECESSOR_RELEASE.json')
    require(receipt['release_plan_sha256'] == io.sha(root / 'RELEASE_PLAN.json')
        and receipt['original_root'] == plan['original_root']
        and receipt['native']['identity'] == plan['native_identity'], 'exact_release_plan_binding')
    require(RELEASE_START <= receipt['native']['released_unix'] < CUT, 'actual_future_boundary_release')
    for expected in (plan['native_identity'], plan['guardian_identity']):
        path = Path('/proc') / str(expected['pid'])
        require(not path.exists() or identity(expected['pid']) != expected, 'original_predecessor_still_live')
    original = Path(plan['original_root'])
    for reference in (plan['original_plan'], plan['activation'], plan['native_launch'], plan['guard_dispatch']):
        require(io.sha(reference['path']) == reference['sha256'], 'original_provenance_preserved')
    for name, digest in receipt['native']['boundary']['preserved_reservations'].items():
        require(io.sha(original / 'reservations' / name) == digest, 'released_reservation_changed')
    require(set(receipt['native']['boundary']['preserved_reservations']) ==
        {path.name for path in (original / 'reservations').glob('*.json')}, 'no_post_release_original_calls')
    return receipt


def wait_release(root):
    root = Path(root)
    plan = io.read(root / 'RELEASE_PLAN.json')
    require(plan['not_before_unix'] == RELEASE_START and plan['stop_attempts_before_unix'] == CUT,
        'fixed_future_release_window')
    original = Path(plan['original_root'])
    while time.time() < RELEASE_START:
        time.sleep(max(0, min(30, RELEASE_START - time.time())))
    if (root / 'PREDECESSOR_RELEASE.json').exists():
        return validate_release(root)
    while time.time() < CUT - 10:
        if not (Path('/proc') / str(plan['native_identity']['pid'])).exists():
            break
        released = drained_process(plan['native_identity'],
            lambda: collection_boundary(original, plan['native_identity']['pid']))
        if released is None:
            time.sleep(max(0, min(10, CUT - 10 - time.time())))
            continue
        while time.time() < CUT and (Path('/proc') / str(plan['guardian_identity']['pid'])).exists():
            if identity(plan['guardian_identity']['pid']) != plan['guardian_identity']:
                break
            time.sleep(1)
        terminal = original / 'SHARED_TERMINAL.json'
        if not terminal.exists():
            io.write(terminal, dict(schema='R118_CODE_FINAL_BOUNDARY_TERMINAL_V1',
                writer='orch_r108_code_parent_r118_final_release', finished_unix=time.time(),
                reason=released['reason'], not_natural_completion=True,
                original_reservations_preserved=True, local_optimizer_steps=0))
        receipt = dict(schema='R118_CODE_FINAL_PREDECESSOR_RELEASE_V1', native=released,
            original_root=str(original), release_plan_sha256=io.sha(root / 'RELEASE_PLAN.json'),
            broker_terminal=ref(terminal), guardian_identity=plan['guardian_identity'],
            guardian_terminal=ref(original / 'R118_SHARED_GUARD_TERMINAL.json'))
        io.write(root / 'PREDECESSOR_RELEASE.json', receipt)
        return validate_release(root)
    io.write(root / 'RELEASE_NOT_COMPLETED.json', dict(observed_unix=time.time(),
        reason='NO_VERIFIED_COMPLETED_COLLECTION_RELEASE', native_eval_calls=0,
        no_forced_midcall_release=True))
    return None
