"""Prospective completed-shared-cycle route handoff; explicit Main authorization only."""

import argparse
from collections import Counter
import fcntl
import json
import os
from pathlib import Path
import signal
import time

from gpu import orch_r111_route_boundary as prior
from gpu import orch_r116_shared_learner as shared


SCHEMA = 'R118_ROUTE_PARALLEL_BOUNDARY_V1'
PURPOSE = 'POST_COMMITTED_SHARED_DEV_PARALLEL'
MODULE = 'gpu.orch_r111_route_pair_shared'
SUCCESSOR = 'gpu.orch_r118_route_parallel_run'
TRAIN_END = 1789491300
require, read, sha, ref = prior.require, prior.read, prior.sha, prior.reference
write = shared.write


def bound(reference):
    path = Path(reference['path'])
    require(path.is_absolute() and not path.is_symlink() and sha(path) == reference['sha256'],
            'exact_immutable_reference')
    return read(path)


def actor(pid, root, phase, uuid, module=MODULE):
    observed = prior.identity(pid)
    process = Path('/proc') / str(pid)
    arguments = (process / 'cmdline').read_bytes().split(b'\0')
    require(observed['uid'] == os.getuid(), 'owned_uid')
    require(arguments[-6:] == [b'-m', module.encode(), phase.encode(), b'--root', str(root).encode(), b''],
            'exact_route_module_phase_root')
    require(b'CUDA_VISIBLE_DEVICES=' + uuid.encode() in (process / 'environ').read_bytes().split(b'\0'),
            'exact_CVD')
    return observed


def committed(common):
    common = Path(common)
    state = read(common / 'STATE.json')
    require(state['generation'] >= 1, 'first_real_shared_commit_required')
    complete = common / f"generation_{state['generation'] - 1:06d}/sleep/COMPLETE.json"
    receipt = read(complete)
    require(receipt['state'] == state and receipt['same_optimizer'] is True, 'complete_state_optimizer_binding')
    require(not (common / f"generation_{state['generation']:06d}/sleep/START.json").exists(),
            'never_interrupt_next_shared_sleep')
    shared.checked_checkpoint(state['checkpoint'])
    return state, ref(complete)


def settled(root, common, cycle):
    root, common, cycle = Path(root), Path(common), Path(cycle)
    state, common_complete = committed(common)
    complete_path = cycle / 'COMPLETE.json'
    complete = read(complete_path)
    number, sleep = complete['cycle'], complete['sleeps']
    require(cycle == root / f'cycle_{number:04d}', 'exact_cycle_path')
    receipt = read(cycle / 'SHARED_SLEEP.json')
    require(receipt['status'] == 'COMPLETE' and receipt['state'] == state, 'actual_branch_shared_sleep')
    checkpoint = cycle / 'checkpoint/CHECKPOINT.json'
    document = read(checkpoint)
    require(document['complete'] is True and document['shared_checkpoint'] == state['checkpoint']
            and document['cycle'] == number and document['sleeps'] == sleep, 'shared_wrapper_not_local_optimizer')
    require(read(cycle / 'SLEEP.json')['checkpoint_sha256'] == sha(checkpoint)
            == read(root / 'OWN_CARRY.json')['checkpoint_sha256'], 'carry_checkpoint_binding')
    original = read(state['checkpoint']['path'])
    from organism_v6.orch_guided_bridge import AdapterIdentity
    AdapterIdentity.from_document(original['adapter'])
    require(original['optimizer_rng_sha256'] == state['checkpoint']['optimizer_path_sha256'],
            'actual_common_optimizer_rng_hash')
    require(document['adapter'] == original['adapter'], 'wrapper_exact_shared_adapter')
    dev = root / f'readout_{sleep:04d}'
    dev_complete, loaded = read(dev / 'COMPLETE.json'), read(dev / 'LOADED.json')
    require(dev_complete.get('fresh_process') is True and dev_complete.get('parent_calls') == 0
            and loaded.get('parent_free') is True and loaded.get('context_free') is True,
            'actual_fresh_parentfree_DEV_not_PROCESS_RESULT')
    require(loaded['checkpoint_sha256'] == sha(checkpoint) and loaded['adapter'] == document['adapter']
            and loaded['process'] != document['source_process'], 'DEV_loaded_exact_checkpoint')
    opened = root / 'open_readouts' / f'readout_{sleep:04d}'
    require((opened / 'COMPLETE.json').exists(), 'actual_OPEN_readout_complete')
    require(read(opened / 'COMPLETE.json')['parent_calls'] == 0, 'OPEN_parentfree')
    rows = prior.ledger(root)
    require(prior.no_later_reservations(rows, number, sleep), 'next_cycle_charged_preserve_no_replay')
    preserved = [complete_path, checkpoint, cycle / 'SHARED_SLEEP.json', cycle / 'SLEEP.json',
                 cycle / 'ROWS.json',
                 root / 'OWN_CARRY.json', root / 'RESERVATIONS.jsonl', root / 'PLAN.json',
                 dev / 'COMPLETE.json', dev / 'LOADED.json', opened / 'COMPLETE.json']
    for row in rows:
        if row.get('cycle') != number and row.get('sleep') != sleep:
            continue
        if row['kind'] == 'PARENT':
            path = root / 'parent_queue' / f'{row["number"]:06d}_F1_C{number:04d}.observed.json'
            require(path.exists() and read(path).get('observed_unix') is not None, 'every_parent_settled')
        else:
            matches = list(root.glob(f'**/CALL_{row["number"]:06d}.json'))
            require(len(matches) == 1 and read(matches[0]).get('finished_unix') is not None,
                    'every_native_settled_including_failure')
            path = matches[0]
        preserved.append(path)
    for name in ('PENDING_TRIPLE.json', 'PUBLICATION.json', 'ROHIN_GO.json'):
        if (root / name).exists():
            preserved.append(root / name)
    later = [path for path in sorted(root.glob('cycle_*/START.json')) if read(path)['cycle'] > number]
    require(len(later) <= 1, 'one_empty_successor_at_most')
    empty = None
    if later:
        require(read(later[0])['cycle'] == number + 1
                and {path.name for path in later[0].parent.iterdir()} == {'START.json'}, 'only_empty_START_can_resume')
        empty = ref(later[0])
        preserved.append(later[0])
    return dict(schema=SCHEMA, root=str(root), completed_cycle=number, next_cycle=number + 1,
                sleep=sleep, state=state, common_complete=common_complete, checkpoint=state['checkpoint'],
                charged=dict(Counter(row['kind'] for row in rows)), empty_successor_start=empty,
                preserved_files={str(path.relative_to(root)): sha(path) for path in preserved},
                no_pending_calls=True, no_quota_reset=True, observed_unix=time.time())


def candidate(root):
    root = Path(root)
    sleeps = sorted(root.glob('cycle_*/SLEEP.json'))
    if not sleeps:
        return None
    cycle = sleeps[-1].parent
    sleep = read(sleeps[-1])['sleeps']
    if not (cycle / 'SHARED_SLEEP.json').exists():
        return None
    if not (root / f'readout_{sleep:04d}/COMPLETE.json').exists():
        return None
    if not (root / f'open_readouts/readout_{sleep:04d}/COMPLETE.json').exists():
        return None
    return cycle


def prepare(root, directory, *, expires_unix, readiness):
    root, directory = Path(root).resolve(strict=True), Path(directory).resolve()
    plan = read(root / 'PLAN.json')
    physical = plan['physical']
    require(physical in prior.UUIDS and str(root) == prior.ROOT_TEMPLATE.format(physical)
            and plan['uuid'] == prior.UUIDS[physical], 'owned_route_only')
    require(time.time() < expires_unix <= min(TRAIN_END - 60, plan['bounds']['hard_end_unix']),
            'fixed_bounded_controller_expiry')
    ready = bound(readiness)
    require(ready['status'] == 'CPU_READY_NOT_ACTIVATED' and ready['branch'] == {0: 'F1', 4: 'A1'}[physical],
            'executable_successor_CPU_ready')
    for name, expected in ready['source_files'].items():
        require(sha(name) == expected, 'candidate_source_unchanged')
    native = actor(read(root / 'ACTOR_READY.json')['pid'], root, 'run', plan['uuid'])
    guard = actor(native['ppid'], root, 'supervise', plan['uuid'])
    source = next(Path(name) for name in plan['source_files'] if name.endswith('/gpu/orch_r111_route_pair_shared.py'))
    for process in (native, guard):
        prior.source_binding(process['pid'], source)
    require(plan['source_files'][str(source)] == sha(source), 'actual_shared_predecessor')
    request = dict(schema=SCHEMA, purpose=PURPOSE, root=str(root), directory=str(directory),
                   common=plan['shared_learner']['root'], plan=ref(root / 'PLAN.json'),
                   actor=native, supervisor=guard, source=ref(source), readiness=readiness,
                   mapping=prior.gpu_mapping(physical, plan['uuid']), bounds=plan['bounds'],
                   expires_unix=expires_unix, created_unix=time.time(), armed=False)
    write(directory / 'REQUEST.json', request)
    return ref(directory / 'REQUEST.json')


def authorize(request_path, authorization_path):
    request, permission = read(request_path), read(authorization_path)
    require(request['schema'] == SCHEMA and permission.get('purpose') == PURPOSE
            and permission.get('authorized') is True and permission.get('request_sha256') == sha(request_path)
            and permission.get('all_eight_ready') is True
            and permission.get('common_handoff_coordinated') is True, 'Main_all8_authorization_before_pidfds')
    ready = bound(request['readiness'])
    require(ready.get('status') == 'CPU_READY_NOT_ACTIVATED' and ready.get('source_files'),
            'CPU_ready_source_required_before_signals')
    for path, expected in ready['source_files'].items():
        require(sha(path) == expected, 'CPU_ready_source_unchanged_before_signals')
    require(permission.get('no_current_serial_interruption') is True, 'serial_preservation_authorization')
    require(time.time() < request['expires_unix'] <= TRAIN_END - 60, 'unexpired_request')
    return request


def execute(request_path, authorization_path):
    request = authorize(request_path, authorization_path)
    root, directory = Path(request['root']), Path(request['directory'])
    require(str(root.resolve()) == prior.ROOT_TEMPLATE.format(request['mapping']['physical'])
            and request['mapping']['uuid'] == prior.UUIDS[request['mapping']['physical']], 'exact_owned_root_UUID')
    require(sha(root / 'PLAN.json') == request['plan']['sha256'], 'predecessor_PLAN_unchanged')
    require(prior.gpu_mapping(request['mapping']['physical'], request['mapping']['uuid']) == request['mapping'],
            'fresh_physical_UUID_minor_binding')
    descriptors, stopped, irreversible = {}, set(), False
    with (directory / 'CONTROLLER.lock').open('a') as controller_lock:
        fcntl.flock(controller_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(not (directory / 'RELEASED.json').exists() and not (directory / 'ARMED.json').exists(),
                'one_shot_no_controller_replay')
        try:
            for role in ('actor', 'supervisor'):
                require(prior.identity(request[role]['pid']) == request[role], 'same_owned_process')
                descriptors[role] = os.pidfd_open(request[role]['pid'])
                require(prior.identity(request[role]['pid']) == request[role], 'pinned_same_process')
            write(directory / 'ARMED.json', dict(request=ref(request_path), authorization=ref(authorization_path),
                                                armed_unix=time.time()))
            while time.time() < request['expires_unix'] and not (directory / 'CANCEL').exists():
                cycle = candidate(root)
                try:
                    if cycle is None:
                        raise ValueError('no_completed_cycle')
                    state = read(Path(request['common']) / 'STATE.json')
                    require(state['generation'] >= 1 and read(cycle / 'SHARED_SLEEP.json')['state'] == state,
                            'actual_branch_commit_before_lock')
                except (ValueError, FileNotFoundError, KeyError) as error:
                    write(directory / 'STATUS.json', dict(phase='WAIT_ACTUAL_COMMIT_DEV_SETTLED_CURSOR',
                        reason=str(error), observed_unix=time.time(), signalled=False), replace=True)
                    time.sleep(.1)
                    continue
                with (root / 'RESERVATIONS.jsonl').open('r') as ledger:
                    try:
                        fcntl.flock(ledger, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    except BlockingIOError:
                        continue
                    try:
                        number = read(cycle / 'START.json')['cycle']
                        sleep = read(cycle / 'SLEEP.json')['sleeps']
                        require(prior.no_later_reservations(prior.ledger(root), number, sleep),
                                'do_not_pause_charged_next_cycle')
                        wait_end = min(request['expires_unix'], time.time() + 30)
                        while not (cycle / 'COMPLETE.json').exists() and time.time() < wait_end:
                            require(not (directory / 'CANCEL').exists(), 'cancelled_before_pause')
                            time.sleep(.02)
                        require((cycle / 'COMPLETE.json').exists(), 'wait_for_original_complete_without_calls')
                        for role in ('supervisor', 'actor'):
                            require(prior.identity(request[role]['pid']) == request[role], 'identity_before_pause')
                            stopped.add(role)
                            prior.stop(descriptors[role], request[role])
                        snapshot = settled(root, request['common'], cycle)
                        require(time.time() < request['expires_unix'] and not (directory / 'CANCEL').exists(),
                                'not_cancelled_before_release')
                        write(directory / 'BOUNDARY.json', snapshot)
                        irreversible = True
                        for role in ('supervisor', 'actor'):
                            signal.pidfd_send_signal(descriptors[role], signal.SIGTERM)
                            signal.pidfd_send_signal(descriptors[role], signal.SIGCONT)
                            stopped.discard(role)
                            require(prior.wait_exit(descriptors[role], 30), 'owned_exit_no_force_kill')
                        require(sha(root / 'RESERVATIONS.jsonl') == snapshot['preserved_files']['RESERVATIONS.jsonl'],
                                'no_charge_during_release')
                        receipt = dict(status='RELEASED', root=str(root), request=ref(request_path),
                            authorization=ref(authorization_path), boundary=ref(directory / 'BOUNDARY.json'),
                            actor=request['actor'], supervisor=request['supervisor'], released_unix=time.time(),
                            original_bounds=request['bounds'], no_quota_reset=True, no_replay=True)
                        write(directory / 'RELEASED.json', receipt)
                        return receipt
                    except (ValueError, FileNotFoundError, KeyError):
                        if irreversible:
                            raise
                        time.sleep(.05)
                    finally:
                        for role in tuple(stopped):
                            signal.pidfd_send_signal(descriptors[role], signal.SIGCONT)
                            stopped.discard(role)
            write(directory / 'EXPIRED_OR_CANCELLED.json', dict(finished_unix=time.time(), released=False))
        except BaseException as error:
            write(directory / 'ERROR.json', dict(error_type=type(error).__name__, error=str(error),
                                               irreversible=irreversible, automatic_retry=False))
            raise
        finally:
            for role in tuple(stopped):
                signal.pidfd_send_signal(descriptors[role], signal.SIGCONT)
            for descriptor in descriptors.values():
                os.close(descriptor)


def released(root, reference):
    receipt = bound(reference)
    if receipt.get('schema') == 'R118_ROUTE_CRASHED_POSTCOMMIT_V1':
        from gpu import orch_r118_route_crash_boundary as recovery
        return recovery.validate_release(root, reference)
    require(receipt['status'] == 'RELEASED' and receipt['root'] == str(root), 'actual_own_release')
    for role in ('actor', 'supervisor'):
        process = Path('/proc') / str(receipt[role]['pid'])
        require(not process.exists() or prior.identity(receipt[role]['pid']) != receipt[role]
                or prior.process_state(receipt[role]['pid']) == 'Z', 'predecessor_exited')
    snapshot = bound(receipt['boundary'])
    for name, expected in snapshot['preserved_files'].items():
        require(sha(Path(root) / name) == expected, 'preserved_boundary_bytes:' + name)
    state, unused = committed(read(Path(root) / 'PLAN.json')['shared_learner']['root'])
    require(state == snapshot['state'], 'no_changed_checkpoint_before_successor')
    return snapshot


def successor_cycle(root, reference):
    require(reference is not None, 'explicit_new_shared_release_required')
    return bound(bound(reference)['boundary'])['next_cycle']


def successor_start(root, output, reference):
    snapshot = bound(bound(reference)['boundary'])
    path = Path(output) / 'START.json'
    if path.exists():
        require(snapshot['empty_successor_start'] == ref(path)
                and {entry.name for entry in Path(output).iterdir()} == {'START.json'}, 'exact_uncharged_empty_cursor')
        return Path(output) / 'R118_PARALLEL_RESUMED_START.json'
    return path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('prepare', 'execute'))
    parser.add_argument('--root', type=Path)
    parser.add_argument('--directory', type=Path)
    parser.add_argument('--expires-unix', type=float)
    parser.add_argument('--readiness', type=Path)
    parser.add_argument('--request', type=Path)
    parser.add_argument('--authorization', type=Path)
    arguments = parser.parse_args()
    if arguments.phase == 'prepare':
        print(json.dumps(prepare(arguments.root, arguments.directory,
            expires_unix=arguments.expires_unix, readiness=ref(arguments.readiness))))
    else:
        print(json.dumps(execute(arguments.request, arguments.authorization)))
