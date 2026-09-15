"""Opt-in pinned math cycle release; preparing a request never signals a process."""

import argparse
import fcntl
import os
from pathlib import Path
import signal
import time

from gpu import orch_math_feedback_uptake_r118_shared_ready as ready
from gpu import orch_r111_route_boundary as pinned


shared, math, require = ready.shared, ready.math, ready.require


def process(pid, root, actor):
    identity = pinned.identity(pid)
    index = shared.read(root/'CONFIG.json')['index']
    directory = Path('/proc')/str(pid)
    arguments = (directory/'cmdline').read_bytes().split(b'\0')
    source = ready.ORIGINAL_SOURCE/'gpu'
    suffix = ([str(source/'orch_math_feedback_uptake_r115_native.py'), 'resident', '--root', str(root.parent),
        '--index', str(index), ''] if actor else [str(source/'orch_math_feedback_uptake_r116_launch.py'),
        '--index', str(index), ''])
    require(arguments[-len(suffix):] == [part.encode() for part in suffix], 'exact_original_process_command')
    require(identity['uid'] == os.getuid() and identity['cwd'] == str(ready.ORIGINAL_SOURCE), 'owned_original_process')
    cvd = math.policy.DEVICES[index] if actor else ''
    require(('CUDA_VISIBLE_DEVICES='+cvd).encode() in (directory/'environ').read_bytes().split(b'\0'), 'original_process_CVD')
    pinned.source_binding(pid, source/'orch_math_feedback_uptake_r115_native.py')
    return identity


def prepare(root, request_path, expires_unix):
    root = Path(root).resolve(strict=True)
    branch = ready.branch_for(root)
    previous = ready.predecessor(root)
    require(time.time() < expires_unix <= min(math.NATIVE-120, time.time()+3600), 'bounded_handoff_request')
    actor = process(shared.read(root/'LAUNCH.json')['identity']['pid'], root, True)
    supervisor = process(actor['ppid'], root, False)
    index = shared.read(root/'CONFIG.json')['index']
    math.bind()
    request = dict(schema='R118_MATH_BOUNDARY_V1', root=str(root), branch=branch, actor=actor,
        supervisor=supervisor, predecessor_bindings=previous, bounds=ready.bounds(),
        mapping=pinned.gpu_mapping(index, math.policy.DEVICES[index]), expires_unix=expires_unix,
        prepared_unix=time.time(), armed=False, ready=ready.reference(root/'SHARED_CLIENT_READY.json'))
    shared.write(request_path, request)
    return request


def candidate(root):
    for output in sorted(root.glob('cycle[0-9][0-9][0-9]'), reverse=True):
        cycle = int(output.name[5:])
        readout = root/'readouts'/f'cycle_{cycle:03d}'
        if not (output/'BOUNDARY.json').exists():
            continue
        batches = [shared.read(path) for path in readout.glob('BATCH_*.request.json')]
        if sum(len(batch['task_ids']) for batch in batches) == 20:
            return cycle
    return None


def snapshot(root, cycle):
    output = root/f'cycle{cycle:03d}'
    complete = shared.read(output/'COMPLETE.json')
    require(complete['status'] == 'COMPLETE' and complete['cycle'] == cycle, 'original_complete_cycle')
    readout = root/'readouts'/f'cycle_{cycle:03d}'
    require(shared.read(readout/'COMPLETE.json')['actual_native'] == 20 and (readout/'AFTER.json').exists()
        and (readout/'MOUNTED_FINAL.json').exists(), 'fresh_readout_fully_finished')
    require(not (Path('/proc')/str(shared.read(root/f'READOUT_cycle_{cycle:03d}_PROCESS.json')['pid'])).exists(),
        'readout_process_exited')
    counters = shared.read(root/'COUNTERS.json')
    require(counters == complete['counters'], 'no_next_cycle_charges')
    later = [path for path in root.glob('cycle[0-9][0-9][0-9]') if int(path.name[5:]) > cycle]
    require(len(later) <= 1 and all(path.name == f'cycle{cycle+1:03d}' and not list(path.iterdir()) for path in later),
        'only_empty_next_cycle_directory')
    reservations = {path.name: shared.sha(path) for path in sorted((root/'reservations').glob('*.json'))}
    charged = {'native': 0, 'parent': 0}
    for name in reservations:
        item = shared.read(root/'reservations'/name)
        require(item['first'] == charged[item['kind']]+1, 'contiguous_original_reservations')
        charged[item['kind']] += item['count']
    require(charged == counters, 'entire_charged_denominator')
    return dict(cycle=cycle, next_cycle=cycle+1, counters=counters, reservations=reservations,
        complete=ready.reference(output/'COMPLETE.json'), carry=ready.reference(output/'BOUNDARY.json'),
        readout=ready.reference(readout/'COMPLETE.json'), counters_file=ready.reference(root/'COUNTERS.json'),
        empty_successor=str(later[0]) if later else None, observed_unix=time.time())


def authorize(request_path, authorization_path):
    request, authorization = shared.read(request_path), shared.read(authorization_path)
    require(request['schema'] == 'R118_MATH_BOUNDARY_V1' and authorization.get('authorized') is True
        and authorization.get('all_eight_ready') is True and authorization.get('common_handoff_coordinated') is True
        and authorization.get('request_sha256') == shared.sha(request_path), 'agreed_exact_all_eight_boundary_only')
    require(request['bounds'] == ready.bounds() and time.time() < request['expires_unix'], 'original_unexpired_bounds')
    root = Path(request['root'])
    require(ready.branch_for(root) == request['branch'], 'exact_requested_branch')
    require(shared.sha(root/'SHARED_CLIENT_READY.json') == request['ready']['sha256'], 'bound_runnable_readiness')
    require(ready.predecessor(root) == request['predecessor_bindings'], 'unchanged_predecessor')
    math.bind()
    require(pinned.gpu_mapping(request['mapping']['physical'], request['mapping']['uuid']) == request['mapping'],
        'fresh_UUID_kernel_mapping')
    return request


def execute(request_path, authorization_path):
    request = authorize(request_path, authorization_path)
    root = Path(request['root'])
    output = Path(request_path).parent/'release'
    output.mkdir(exist_ok=False)
    descriptors, stopped = {}, set()
    irreversible = False
    try:
        for role in ('supervisor', 'actor'):
            expected = request[role]
            descriptors[role] = os.pidfd_open(expected['pid'])
            require(process(expected['pid'], root, role == 'actor') == expected, 'fresh_pinned_process')
        while time.time() < request['expires_unix']:
            if (Path(request_path).parent/'CANCEL').exists():
                return dict(status='CANCELLED_NO_RELEASE')
            for role in descriptors:
                require(pinned.identity(request[role]['pid']) == request[role], 'identity_still_pinned')
            cycle = candidate(root)
            if cycle is None:
                time.sleep(.05)
                continue
            with (root/'COUNTERS.lock').open('a') as lock:
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    time.sleep(.05)
                    continue
                deadline = min(request['expires_unix'], time.time()+60)
                while time.time() < deadline and not (root/f'cycle{cycle:03d}'/'COMPLETE.json').exists():
                    time.sleep(.05)
                if not (root/f'cycle{cycle:03d}'/'COMPLETE.json').exists():
                    continue
                complete = shared.read(root/f'cycle{cycle:03d}'/'COMPLETE.json')
                if shared.read(root/'COUNTERS.json') != complete['counters']:
                    continue
                try:
                    for role in ('supervisor', 'actor'):
                        stopped.add(role)
                        pinned.stop(descriptors[role], request[role])
                    try:
                        boundary = snapshot(root, cycle)
                    except (ValueError, FileNotFoundError):
                        continue
                    require(time.time() < request['expires_unix'] and not (Path(request_path).parent/'CANCEL').exists(),
                        'not_cancelled_before_release')
                    shared.write(output/'BOUNDARY.json', boundary)
                    irreversible = True
                    signal.pidfd_send_signal(descriptors['actor'], signal.SIGTERM)
                    signal.pidfd_send_signal(descriptors['actor'], signal.SIGCONT)
                    stopped.discard('actor')
                    require(pinned.wait_exit(descriptors['actor'], 30), 'actor_exit_no_SIGKILL')
                    signal.pidfd_send_signal(descriptors['supervisor'], signal.SIGTERM)
                    signal.pidfd_send_signal(descriptors['supervisor'], signal.SIGCONT)
                    stopped.discard('supervisor')
                    require(pinned.wait_exit(descriptors['supervisor'], 15), 'supervisor_exit_no_SIGKILL')
                    require(shared.sha(root/'COUNTERS.json') == boundary['counters_file']['sha256'], 'no_charge_during_release')
                    released = dict(status='RELEASED', root=str(root), branch=request['branch'],
                        boundary=ready.reference(output/'BOUNDARY.json'), actor=request['actor'], supervisor=request['supervisor'],
                        request=ready.reference(request_path), authorization=ready.reference(authorization_path),
                        released_unix=time.time(), no_quota_reset=True, optimizer_lost=False,
                        prior_life='FROZEN_BASE_CONTEXT_ONLY', termination='AUTHORIZED_COMPLETED_CYCLE_NOT_OUTCOME_STOP')
                    shared.write(output/'RELEASED.json', released)
                    return released
                finally:
                    for role in tuple(stopped):
                        try:
                            signal.pidfd_send_signal(descriptors[role], signal.SIGCONT)
                        except ProcessLookupError:
                            pass
                        stopped.discard(role)
        return dict(status='EXPIRED_NO_RELEASE')
    except BaseException as error:
        shared.write(output/'ERROR.json', dict(error=str(error), irreversible=irreversible, no_retry=True))
        raise
    finally:
        for descriptor in descriptors.values():
            os.close(descriptor)


def verify_release(root, reference):
    require(shared.sha(reference['path']) == reference['sha256'], 'exact_release_hash')
    release = shared.read(reference['path'])
    require(release['status'] == 'RELEASED' and release['root'] == str(root)
        and release['branch'] == ready.branch_for(root), 'same_released_life')
    for role in ('actor', 'supervisor'):
        directory = Path('/proc')/str(release[role]['pid'])
        require(not directory.exists(), 'original_process_exited')
    require(shared.sha(release['boundary']['path']) == release['boundary']['sha256'], 'bound_completed_boundary')
    boundary = shared.read(release['boundary']['path'])
    require(shared.read(root/'COUNTERS.json') == boundary['counters'], 'counters_preserved_at_adoption')
    actual = {path.name: shared.sha(path) for path in (root/'reservations').glob('*.json')}
    require(actual == boundary['reservations'], 'all_original_reservations_preserved')
    for key in ('complete', 'carry', 'readout', 'counters_file'):
        require(shared.sha(boundary[key]['path']) == boundary[key]['sha256'], 'original_boundary_bytes_preserved')
    return boundary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('prepare', 'execute'))
    parser.add_argument('--root', type=Path)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--expires-unix', type=float)
    parser.add_argument('--authorization', type=Path)
    args = parser.parse_args()
    result = (prepare(args.root, args.request, args.expires_unix) if args.phase == 'prepare'
        else execute(args.request, args.authorization))
    print(result.get('status', 'PREPARED_UNARMED'))
