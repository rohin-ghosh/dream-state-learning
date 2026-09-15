"""Opt-in external cycle handoff for immutable route lives; never armed by import."""

import argparse
from collections import Counter
import fcntl
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import socket
import stat
import subprocess
import time


ROOT_TEMPLATE = '/localhome/local-rohing/orch_r111_f1_v4_20260915_node5_{}_attempt1'
UUIDS = {0: 'GPU-f237c5b5-c2a3-b377-92ee-46cf2658db9a',
         4: 'GPU-94c9a79c-8b13-5679-ad35-8dda3fe5c94d'}
MORNING_CUT = 1789491600


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def reference(path):
    return dict(path=str(path), sha256=sha(path))


def write_new(path, value):
    path = Path(path)
    partial = path.with_name(path.name + '.partial.' + str(os.getpid()))
    with partial.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        os.link(partial, path)
    finally:
        partial.unlink()


def identity(pid):
    directory = Path('/proc') / str(pid)
    fields = (directory / 'stat').read_text().rsplit(')', 1)[1].split()
    return dict(pid=pid, uid=directory.stat().st_uid, start_ticks=fields[19],
        ppid=int(fields[1]), command_sha256=sha(directory / 'cmdline'),
        boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
        cwd=str((directory / 'cwd').resolve(strict=True)))


def process_state(pid):
    return (Path('/proc') / str(pid) / 'stat').read_text().rsplit(')', 1)[1].split()[0]


def pinned_process(pid, root, phase, uuid):
    result = identity(pid)
    directory = Path('/proc') / str(pid)
    arguments = (directory / 'cmdline').read_bytes().split(b'\0')
    require(result['uid'] == os.getuid(), 'owned_uid_only')
    suffix = [b'-m', b'gpu.orch_r111_route_pair', phase.encode(), b'--root', str(root).encode(), b'']
    require(arguments[-6:] == suffix, 'exact_original_actor_or_supervisor')
    require(b'CUDA_VISIBLE_DEVICES=' + uuid.encode() in
            (directory / 'environ').read_bytes().split(b'\0'), 'exact_process_CVD')
    return result


def source_binding(pid, source):
    values = dict(part.split(b'=', 1) for part in
                  (Path('/proc') / str(pid) / 'environ').read_bytes().split(b'\0') if b'=' in part)
    paths = values.get(b'PYTHONPATH', b'').decode().split(':')
    require(paths and paths[0] == str(Path(source).parent.parent), 'original_first_PYTHONPATH_source')


def gpu_mapping(physical, uuid):
    output = subprocess.check_output(['nvidia-smi', '--query-gpu=index,uuid',
        '--format=csv,noheader,nounits'], text=True, timeout=20)
    rows = [tuple(part.strip() for part in line.split(',')) for line in output.splitlines()]
    matches = [row for row in rows if row[0] == str(physical)]
    require(len(matches) == 1 and matches[0][1] == uuid, 'physical_UUID_mapping')
    kernel = []
    for path in Path('/proc/driver/nvidia/gpus').glob('*/information'):
        fields = dict(line.split(':', 1) for line in path.read_text().splitlines() if ':' in line)
        fields = {key.strip(): value.strip() for key, value in fields.items()}
        if fields.get('GPU UUID') == uuid:
            kernel.append(int(fields['Device Minor']))
    require(len(kernel) == 1, 'kernel_minor_UUID_mapping')
    minor = kernel[0]
    device = Path('/dev') / f'nvidia{minor}'
    metadata = device.stat()
    require(stat.S_ISCHR(metadata.st_mode) and os.minor(metadata.st_rdev) == minor, 'kernel_device_minor_binding')
    return dict(physical=physical, uuid=uuid, kernel_minor=minor)


def prepare(root, destination, expires_unix, purpose):
    root = Path(root).resolve(strict=True)
    plan = read(root / 'PLAN.json')
    physical = plan['physical']
    require(physical in UUIDS and str(root) == ROOT_TEMPLATE.format(physical), 'owned_route_root')
    require(plan['uuid'] == UUIDS[physical], 'owned_route_UUID')
    require(time.time() < expires_unix <= plan['bounds']['hard_end_unix'], 'bounded_controller_wall')
    actor = pinned_process(read(root / 'ACTOR_READY.json')['pid'], root, 'run', plan['uuid'])
    supervisor = pinned_process(actor['ppid'], root, 'supervise', plan['uuid'])
    require(actor['cwd'] == supervisor['cwd'], 'same_owned_working_directory')
    sources = [Path(path) for path in plan['source_files'] if path.endswith('/gpu/orch_r111_route_pair.py')]
    require(len(sources) == 1, 'single_original_source')
    source = sources[0]
    require(plan['source_files'].get(str(source)) == sha(source), 'original_source_binding')
    for process in (actor, supervisor):
        source_binding(process['pid'], source)
    request = dict(schema='R118_ROUTE_BOUNDARY_REQUEST_V1', root=str(root), purpose=purpose,
        actor=actor, supervisor=supervisor, plan=reference(root / 'PLAN.json'),
        ready=reference(root / 'ACTOR_READY.json'), source=reference(source),
        host_sha256=hashlib.sha256(socket.gethostname().encode()).hexdigest(),
        mapping=gpu_mapping(physical, plan['uuid']), bounds=plan['bounds'],
        expires_unix=expires_unix, prepared_unix=time.time(), armed=False,
        mechanism='ORIGINAL_LEDGER_LOCK_THEN_ORIGINAL_COMPLETE_NO_NEW_RESERVATIONS')
    write_new(destination, request)
    return request


def ledger(root):
    return [json.loads(line) for line in (root / 'RESERVATIONS.jsonl').read_text().splitlines() if line.strip()]


def candidate(root, now):
    paths = sorted(root.glob('cycle_*/SLEEP.json'))
    if not paths:
        return None
    cycle = paths[-1].parent
    sleep = read(paths[-1])['sleeps']
    opened = root / 'open_readouts' / f'readout_{sleep:04d}'
    if not any((opened / name).exists() for name in ('COMPLETE.json', 'PROCESS_RESULT.json')):
        return None
    requested = root / 'FINAL_MORNING_REQUESTED.json'
    final_pending = now >= MORNING_CUT and (not requested.exists() or read(requested)['sleep'] == sleep)
    if final_pending:
        final = root / 'sealed_final_readouts' / f'readout_{sleep:04d}'
        if not any((final / name).exists() for name in ('COMPLETE.json', 'PROCESS_RESULT.json')):
            return None
    return cycle


def no_later_reservations(rows, cycle, sleep):
    return all(row.get('cycle', cycle) <= cycle and row.get('sleep', sleep) <= sleep for row in rows)


def completed_boundary(root, cycle):
    complete_path = cycle / 'COMPLETE.json'
    if not complete_path.exists():
        return None
    complete = read(complete_path)
    number, sleep = complete['cycle'], complete['sleeps']
    rows = ledger(root)
    if not no_later_reservations(rows, number, sleep):
        return None
    checkpoint_path = cycle / 'checkpoint/CHECKPOINT.json'
    checkpoint = read(checkpoint_path)
    require(checkpoint['complete'] is True and checkpoint['cycle'] == number
            and checkpoint['sleeps'] == sleep, 'latest_complete_checkpoint')
    require(read(cycle / 'SLEEP.json')['checkpoint_sha256'] == sha(checkpoint_path)
            == read(root / 'OWN_CARRY.json')['checkpoint_sha256'], 'checkpoint_sleep_carry_binding')
    optimizer = checkpoint_path.parent / 'optimizer_rng.pt'
    require(sha(optimizer) == checkpoint['optimizer_rng_sha256'], 'optimizer_bytes_preserved')
    adapter = checkpoint['adapter']
    for name, expected in adapter['files']:
        require(sha(Path(adapter['path']) / name) == expected, 'adapter_bytes_preserved')
    relevant = [row for row in rows if row.get('cycle') == number or row.get('sleep') == sleep]
    for row in relevant:
        if row['kind'] == 'PARENT':
            observed = root / 'parent_queue' / f'{row["number"]:06d}_F1_C{number:04d}.observed.json'
            require(observed.exists() and read(observed).get('observed_unix') is not None,
                    'every_current_parent_settled_including_MISSING')
        else:
            matches = list(root.glob(f'**/CALL_{row["number"]:06d}.json'))
            require(len(matches) == 1 and read(matches[0]).get('finished_unix') is not None,
                    'every_current_native_settled')
    starts = sorted(root.glob('cycle_*/START.json'))
    later = [path for path in starts if read(path)['cycle'] > number]
    require(len(later) <= 1, 'at_most_one_empty_successor')
    empty = None
    if later:
        require(read(later[0])['cycle'] == number + 1 and
                {path.name for path in later[0].parent.iterdir()} == {'START.json'},
                'empty_next_START_only_no_captures')
        empty = reference(later[0])
    return dict(complete=reference(complete_path), checkpoint=reference(checkpoint_path),
        optimizer=reference(optimizer), carry=reference(root / 'OWN_CARRY.json'),
        ledger=reference(root / 'RESERVATIONS.jsonl'), charged=dict(Counter(row['kind'] for row in rows)),
        empty_successor_start=empty, original_COMPLETE_written=True, no_pending_calls=True,
        pending_triple=reference(root / 'PENDING_TRIPLE.json') if (root / 'PENDING_TRIPLE.json').exists() else None)


def released_boundary(root, release_reference):
    release_path = Path(release_reference['path']).resolve(strict=True)
    require(sha(release_path) == release_reference['sha256'], 'exact_release_receipt')
    released = read(release_path)
    require(released['status'] == 'RELEASED' and
            Path(released['original_plan']['path']).parent.resolve() == root.resolve(), 'release_life_binding')
    saved_path = Path(released['boundary']['path'])
    require(sha(saved_path) == released['boundary']['sha256'], 'exact_boundary_receipt')
    return read(saved_path)


def successor_cycle(root, release_reference):
    starts = sorted(root.glob('cycle_*/START.json'))
    latest = max([read(path)['cycle'] for path in starts], default=0)
    if release_reference is None:
        return latest + 1
    saved = released_boundary(root, release_reference)
    empty = saved['empty_successor_start']
    expected = root / f'cycle_{latest:04d}' / 'START.json'
    if empty is not None and str(expected) == empty['path']:
        if {path.name for path in expected.parent.iterdir()} == {'START.json'}:
            require(sha(expected) == empty['sha256'], 'preserved_empty_START')
            require(sha(root / 'RESERVATIONS.jsonl') == saved['ledger']['sha256'], 'no_unrecorded_empty_cycle_charge')
            return latest
    return latest + 1


def successor_start(root, output, release_reference):
    if output.exists():
        require(release_reference is not None, 'existing_cycle_needs_exact_release')
        saved = released_boundary(root, release_reference)
        empty = saved['empty_successor_start']
        require(empty is not None and empty['path'] == str(output / 'START.json')
                and sha(empty['path']) == empty['sha256']
                and {path.name for path in output.iterdir()} == {'START.json'}, 'resume_only_empty_original_START')
        return output / ('RESUMED_START_' + str(time.time_ns()) + '.json')
    output.mkdir(exist_ok=False)
    return output / 'START.json'


def wait_exit(descriptor, timeout):
    poller = select.poll()
    poller.register(descriptor, select.POLLIN)
    return bool(poller.poll(int(timeout * 1000)))


def stop(descriptor, expected):
    require(identity(expected['pid']) == expected, 'identity_before_stop')
    signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        if process_state(expected['pid']) in ('T', 't'):
            return
        time.sleep(.01)
    raise RuntimeError('stop_not_observed')


def execute(request_path, authorization_path):
    request_path, authorization_path = Path(request_path), Path(authorization_path)
    request, authorization = read(request_path), read(authorization_path)
    require(authorization['request_sha256'] == sha(request_path)
            and authorization['purpose'] == request['purpose'] and authorization.get('authorized') is True,
            'explicit_exact_handoff_authorization')
    require(request['purpose'] in ('SHARED_ADOPTION', 'WAIT600_TRANSPORT'), 'supported_purpose')
    if request['purpose'] == 'SHARED_ADOPTION':
        require(authorization.get('all_eight_ready') is True and authorization.get('common_handoff_coordinated') is True,
                'no_premature_shared_stop')
    else:
        require(authorization.get('successor_ready') is True and authorization.get('prospective_only') is True
                and authorization.get('refusals_never_retried') is True, 'transport_successor_ready')
        require(authorization.get('transport_basis') in ('DEMONSTRATED_LATENCY', 'EXPLICIT_GENERAL_TRANSPORT_CHANGE')
                and bool(authorization.get('basis_reference')), 'refusal_is_not_transport_authorization')
    root = Path(request['root'])
    require(request['schema'] == 'R118_ROUTE_BOUNDARY_REQUEST_V1', 'known_boundary_request')
    physical = request['mapping']['physical']
    require(physical in UUIDS and str(root.resolve()) == ROOT_TEMPLATE.format(physical)
            and request['mapping']['uuid'] == UUIDS[physical], 'owned_root_UUID_only')
    require(sha(root / 'PLAN.json') == request['plan']['sha256'], 'original_plan_unchanged')
    plan = read(root / 'PLAN.json')
    require(plan['bounds'] == request['bounds'] and plan['physical'] == physical
            and plan['uuid'] == UUIDS[physical], 'bounds_and_slot_unchanged')
    require(time.time() < request['expires_unix'] <= plan['bounds']['hard_end_unix'], 'controller_wall')
    require(sha(request['source']['path']) == request['source']['sha256']
            == plan['source_files'][request['source']['path']], 'original_source_unchanged')
    require(sha(root / 'ACTOR_READY.json') == request['ready']['sha256'], 'original_actor_not_recovered')
    require(hashlib.sha256(socket.gethostname().encode()).hexdigest() == request['host_sha256'], 'hashed_host')
    require(gpu_mapping(request['mapping']['physical'], request['mapping']['uuid']) == request['mapping'],
            'fresh_physical_minor_mapping')
    descriptors = {}
    stopped = set()
    irreversible = False
    output = request_path.parent
    write_new(output / 'ARMED.json', dict(request=reference(request_path), authorization=reference(authorization_path),
        controller_pid=os.getpid(), armed_unix=time.time()))
    try:
        for role in ('supervisor', 'actor'):
            expected = request[role]
            descriptors[role] = os.pidfd_open(expected['pid'])
            require(identity(expected['pid']) == expected, 'pinned_original_process')
            require(pinned_process(expected['pid'], root, 'run' if role == 'actor' else 'supervise',
                                   UUIDS[physical]) == expected, 'original_process_role')
            source_binding(expected['pid'], request['source']['path'])
        require(request['actor']['ppid'] == request['supervisor']['pid'], 'actual_supervisor_parent')
        while time.time() < request['expires_unix']:
            if (output / 'CANCEL').exists():
                return dict(status='CANCELLED_NO_RELEASE')
            for role in descriptors:
                require(identity(request[role]['pid']) == request[role], 'identity_stayed_pinned')
            cycle = candidate(root, time.time())
            if cycle is None:
                time.sleep(.02)
                continue
            with (root / 'RESERVATIONS.jsonl').open('r') as stream:
                try:
                    fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    time.sleep(.02)
                    continue
                number = read(cycle / 'START.json')['cycle']
                sleep = read(cycle / 'SLEEP.json')['sleeps']
                if not no_later_reservations(ledger(root), number, sleep):
                    time.sleep(.02)
                    continue
                deadline = min(time.time() + 30, request['expires_unix'])
                while time.time() < deadline and not (cycle / 'COMPLETE.json').exists():
                    if (output / 'CANCEL').exists() or candidate(root, time.time()) != cycle:
                        break
                    time.sleep(.02)
                if not (cycle / 'COMPLETE.json').exists():
                    continue
                try:
                    for role in ('supervisor', 'actor'):
                        stopped.add(role)
                        stop(descriptors[role], request[role])
                    boundary = completed_boundary(root, cycle)
                    require(boundary is not None, 'boundary_not_raced')
                    require(not (output / 'CANCEL').exists(), 'cancelled_before_release')
                    require(time.time() < request['expires_unix'], 'handoff_wall')
                    write_new(output / 'BOUNDARY.json', dict(boundary, request=reference(request_path),
                        checked_unix=time.time(), bounds=request['bounds'], no_quota_reset=True))
                    signal.pidfd_send_signal(descriptors['supervisor'], signal.SIGTERM)
                    signal.pidfd_send_signal(descriptors['supervisor'], signal.SIGCONT)
                    stopped.discard('supervisor')
                    irreversible = True
                    require(wait_exit(descriptors['supervisor'], 10), 'supervisor_exit_before_actor')
                    signal.pidfd_send_signal(descriptors['actor'], signal.SIGTERM)
                    signal.pidfd_send_signal(descriptors['actor'], signal.SIGCONT)
                    stopped.discard('actor')
                    require(wait_exit(descriptors['actor'], 30), 'actor_exit_no_SIGKILL')
                    require(sha(root / 'RESERVATIONS.jsonl') == boundary['ledger']['sha256'], 'charges_unchanged')
                    result = dict(status='RELEASED', released_unix=time.time(), boundary=reference(output / 'BOUNDARY.json'),
                        actor=request['actor'], supervisor=request['supervisor'], no_restart=True,
                        no_quota_reset=True, raw_node_only=True, original_plan=reference(root / 'PLAN.json'))
                    write_new(output / 'RELEASED.json', result)
                    return result
                finally:
                    for role in tuple(stopped):
                        try:
                            signal.pidfd_send_signal(descriptors[role], signal.SIGCONT)
                        except ProcessLookupError:
                            pass
                        stopped.discard(role)
        return dict(status='EXPIRED_NO_RELEASE')
    except BaseException as error:
        write_new(output / 'ERROR.json', dict(error_type=type(error).__name__,
            after_supervisor_termination=irreversible, observed_unix=time.time(), automatic_retry=False))
        raise
    finally:
        for descriptor in descriptors.values():
            os.close(descriptor)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('prepare', 'execute'))
    parser.add_argument('--root', type=Path)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--authorization', type=Path)
    parser.add_argument('--expires-unix', type=float)
    parser.add_argument('--purpose', choices=('SHARED_ADOPTION', 'WAIT600_TRANSPORT'))
    arguments = parser.parse_args()
    def interrupt(signum, frame):
        raise InterruptedError('controller_interrupted_resume_owned_processes')

    signal.signal(signal.SIGTERM, interrupt)
    if arguments.phase == 'prepare':
        result = prepare(arguments.root, arguments.request, arguments.expires_unix, arguments.purpose)
    else:
        result = execute(arguments.request, arguments.authorization)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
