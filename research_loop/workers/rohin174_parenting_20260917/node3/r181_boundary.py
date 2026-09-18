"""One saved-boundary handoff, retaining the actual R179 backing journal."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import select
import signal
import socket
import subprocess
import sys
import time
import uuid

HERE = Path(__file__).resolve().parent
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
HARD_END = 1789689000
NATIVE = 'gpu/orch_r125_continual_native.py'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            result.update(block)
    return result.hexdigest()


def digest(document):
    return hashlib.sha256(json.dumps(document, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def write(path, document):
    path = Path(path)
    require(path.resolve().is_relative_to(HERE), 'owned_node3_artifact')
    with path.open('x') as stream:
        json.dump(document, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())


def identity(pid):
    proc = Path('/proc') / str(pid)
    fields = (proc / 'stat').read_text().rsplit(') ', 1)[1].split()
    return dict(pid=pid, ticks=fields[19], parent=int(fields[1]), uid=proc.stat().st_uid,
        argv=(proc / 'cmdline').read_bytes().rstrip(b'\0').decode().split('\0'),
        cwd=os.readlink(proc / 'cwd'), cgroup=(proc / 'cgroup').read_text())


def exact(expected):
    actual = identity(expected['pid'])
    require(all(actual[field] == expected[field] for field in ('pid', 'ticks', 'uid', 'argv', 'cwd', 'cgroup')),
            'exact_owned_process_identity')
    require(actual['uid'] == os.getuid(), 'own_uid_only')
    return actual


def head(root):
    paths = sorted(path for path in (Path(root) / 'stream/records').iterdir()
                   if re.fullmatch(r'\d{20}\.json', path.name))
    return read(paths[-1])


def saved_state(record):
    if record['kind'] != 'SLEEP_COMPLETE':
        return None
    require(record['sha256'] == digest({key: value for key, value in record.items() if key != 'sha256'}),
            'published_boundary_record_hash')
    document = record['document']
    envelope = document['resume_state']
    state = envelope['state']
    require(envelope['sha256'] == digest(state) and document['status'] == 'COMPLETE'
            and state['pending'] is None and state['sleep_frontier'] == len(state['rows'])
            and state['sleep_receipts'][-1]['status'] == 'COMPLETE', 'exact_saved_frontier_no_unsaved_updates')
    require(state['deadline_unix'] == HARD_END, 'unchanged_1650_wall')
    return state


def command(folder, action, *, cpu=False):
    config = read(folder / 'GUARD.json')
    plan = read(folder / 'PLAN.json')
    policy = config['device_containment']
    unit = policy['unit'] + ('-cpu' if cpu else '')
    lifetime = min(60, int(HARD_END - time.time())) if cpu else int(HARD_END - time.time())
    require(lifetime > 10, 'time_inside_existing_wall')
    properties = dict(User=str(policy['uid']), Group=str(policy['gid']), NoNewPrivileges='yes',
        DevicePolicy='strict', CapabilityBoundingSet='', AmbientCapabilities='', ProtectControlGroups='yes',
        RuntimeMaxSec=str(lifetime), TimeoutStopSec='5', KillMode='control-group', WorkingDirectory=plan['source_root'])
    devices = ['/dev/null rw', '/dev/zero rw', '/dev/random r', '/dev/urandom r']
    if not cpu:
        devices += [f"/dev/nvidia{policy['minor']} rw", '/dev/nvidiactl rw', '/dev/nvidia-uvm rw']
    spec = read(folder / 'LIVE_HANDOFF.json')
    return ['sudo', '-n', 'systemd-run', '--quiet', '--wait', '--pipe', '--unit=' + unit,
        *['--property=' + key + '=' + value for key, value in properties.items()], '--property=DeviceAllow=',
        *['--property=DeviceAllow=' + device for device in devices],
        '--property=BindPaths=' + spec['backing_root'] + ':' + plan['root'],
        '--property=ReadOnlyPaths=' + plan['source_root'],
        '--property=BindReadOnlyPaths=' + str(folder / 'new_native.py') + ':' + str(Path(plan['source_root']) / NATIVE),
        '/usr/bin/env', '-i', 'PATH=/usr/bin:/bin', 'HOME=/localhome/local-rohing',
        'CUDA_VISIBLE_DEVICES=' + ('' if cpu else plan['gpu_uuid']), 'PYTHONDONTWRITEBYTECODE=1',
        'PYTHONPATH=' + plan['source_root'], 'HF_HUB_OFFLINE=1', 'TRANSFORMERS_OFFLINE=1',
        'OMP_NUM_THREADS=1', 'MKL_NUM_THREADS=1', 'TOKENIZERS_PARALLELISM=false',
        'PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True', PYTHON, '-B', str(Path(__file__).resolve()),
        action, '--physical', str(plan['physical'])]


def prepare(folder):
    spec = read(folder / 'LIVE_HANDOFF.json')
    exact(spec['identity'])
    require(read(spec['config_path']) == spec['config'], 'original_guard_unchanged')
    require(sha(Path(spec['plan']['source_root']) / NATIVE) == sha(folder / 'original_native.py'), 'actual_original_source')
    plan = dict(spec['plan'], rehearsal_presentations=0)
    consumed = plan.pop('authorized_wall_extension', None)
    require(plan['hard_end_unix'] == HARD_END and plan['lease_end_unix'] == 1789689600, 'existing_machine_ceiling')
    write(folder / 'PLAN.json', plan)
    allocation = dict(read(spec['config']['allocation_path']), plan_sha256=sha(folder / 'PLAN.json'),
        declared_unix=time.time(), cpu_tests_passed=True, builder_entry_pushed=True,
        r181_authority='ROHIN181 canonical four-delta directive; existing lives next saved boundary',
        r181_consumed_wall_authorization=consumed)
    write(folder / 'ALLOCATION.json', allocation)
    config = dict(spec['config'], plan_path=str(folder / 'PLAN.json'), plan_sha256=sha(folder / 'PLAN.json'),
        attempt_dir=str(folder), allocation_path=str(folder / 'ALLOCATION.json'), allocation_sha256=sha(folder / 'ALLOCATION.json'),
        resume=True, source_pins=dict(spec['config']['source_pins'], **{NATIVE: sha(folder / 'new_native.py')}),
        device_containment=dict(spec['config']['device_containment'], unit='orch-r181-node3-' + uuid.uuid4().hex))
    write(folder / 'GUARD.json', config)
    result = subprocess.run(command(folder, 'cpu', cpu=True), capture_output=True, text=True, timeout=90)
    require(result.returncode == 0, 'actual_private_overlay_guard_validation:' + result.stderr[-500:])
    write(folder / 'SOURCE_BOUND.json', dict(status='ACTUAL_PRIVATE_OVERLAY_GUARD_VALIDATED',
        canonical_delta=sha(folder / 'new_native.py'), original_source_unchanged=True,
        stdout=result.stdout, child_signals=0, observed_unix=time.time()))


def cpu(folder):
    sys.path.insert(0, read(folder / 'PLAN.json')['source_root'])
    from gpu import orch_r125_continual_guard as guard
    config, plan = guard.validate(folder / 'GUARD.json')
    require(sha(guard.child.__file__) == sha(folder / 'new_native.py'), 'actual_native_overlay')
    require(plan['rehearsal_presentations'] == 0, 'new_only_actual_plan')
    print(json.dumps(dict(status='PASS', actual_native=guard.child.__file__, source_sha256=sha(guard.child.__file__))))


def wait(folder):
    spec = read(folder / 'LIVE_HANDOFF.json')
    require((folder / 'SOURCE_BOUND.json').exists(), 'ready_private_source')
    actor = exact(spec['identity'])
    timer = identity(actor['parent'])
    supervisor = identity(timer['parent'])
    require(timer['argv'][:3] == ['timeout', '--signal=TERM', '--kill-after=5s'], 'actual_timeout_parent')
    require(actor['cgroup'] == timer['cgroup'] == supervisor['cgroup'], 'same_owned_service')
    require(spec['config_path'] in actor['argv'] and actor['cwd'] == spec['plan']['source_root'], 'exact_child_guard')
    actors = [actor, timer, supervisor]
    descriptors = []
    stopped = False
    retired = False
    try:
        for process in actors:
            exact(process)
            descriptors.append(os.pidfd_open(process['pid']))
        write(folder / 'WAIT_STARTED.json', dict(actors=actors, observed_unix=time.time(), next_saved_only=True,
            root=spec['backing_root'], no_state_reset=True, hard_end_unix=HARD_END))
        while time.time() < HARD_END - 180:
            exact(actor)
            record = head(spec['backing_root'])
            state = saved_state(record)
            if state is None:
                time.sleep(.1)
                continue
            signal.pidfd_send_signal(descriptors[0], signal.SIGSTOP)
            stopped = True
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                tasks = list((Path('/proc') / str(actor['pid']) / 'task').iterdir())
                if all((task / 'stat').read_text().rsplit(') ', 1)[1].split()[0] in ('T', 't') for task in tasks):
                    break
                time.sleep(.01)
            else:
                raise ValueError('all_native_threads_must_be_stopped')
            if head(spec['backing_root'])['sha256'] != record['sha256']:
                signal.pidfd_send_signal(descriptors[0], signal.SIGCONT)
                stopped = False
                time.sleep(.1)
                continue
            while time.time() < HARD_END - 180:
                children = (Path('/proc') / str(actor['pid']) / 'task' / str(actor['pid']) / 'children').read_text().split()
                active = []
                for child_pid in children:
                    try:
                        fields = (Path('/proc') / child_pid / 'stat').read_text().rsplit(') ', 1)[1].split()
                        if fields[0] not in ('Z', 'X'):
                            active.append(child_pid)
                    except FileNotFoundError:
                        pass
                if not active:
                    break
                time.sleep(.25)
            require(not active, 'existing_subprocesses_must_finish')
            checkpoint_path = Path(spec['backing_root']) / 'checkpoints' / ('sleep_%06d' % record['document']['cycle']) / 'COMMIT.json'
            checkpoint = read(checkpoint_path)
            mapped = lambda value: Path(spec['backing_root']) / Path(value).relative_to(spec['plan']['root'])
            require(sha(mapped(checkpoint['optimizer_rng_path'])) == checkpoint['checkpoint_sha256']['optimizer']
                == checkpoint['checkpoint_sha256']['rng'], 'exact_AdamW_and_RNG_file')
            adapter = {path.name: sha(path) for path in mapped(checkpoint['adapter_path']).iterdir() if path.is_file()}
            require(adapter == checkpoint['adapter_files'] and digest(adapter) == checkpoint['checkpoint_sha256']['adapter'], 'exact_adapter_files')
            require(digest(checkpoint['checkpoint_sha256']) == state['model_state_sha256'], 'stream_checkpoint_binding')
            require(head(spec['backing_root'])['sha256'] == record['sha256'], 'same_boundary_before_retirement')
            write(folder / 'BOUNDARY.json', dict(status='EXACT_SAVED_BOUNDARY', record=record, checkpoint=checkpoint,
                checkpoint_file_sha256=sha(checkpoint_path), actors=actors, observed_unix=time.time(),
                inbox_files={path.name: sha(path) for path in (Path(spec['backing_root']) / 'stream/inbox').glob('*.json')},
                same_backing_root=True, checkpoint_RNG_history_preserved=True, readout_contents_read=False))
            for process, descriptor in zip(actors, descriptors):
                if select.select([descriptor], [], [], 0)[0]:
                    continue
                exact(process)
                signal.pidfd_send_signal(descriptor, signal.SIGTERM)
                signal.pidfd_send_signal(descriptor, signal.SIGCONT)
                require(bool(select.select([descriptor], [], [], 20)[0]), 'exact_predecessor_exit')
            retired = True
            stopped = False
            write(folder / 'RETIRED.json', dict(actors=actors, observed_unix=time.time(), at_exact_saved_boundary=True))
            scan = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
                'PYTHONPATH=' + spec['plan']['source_root'], PYTHON, '-B', '-m', 'gpu.orch_r125_continual_guard',
                'scan', '--config', spec['config_path']]
            require((Path(spec['config']['attempt_dir']) / 'SERVICE_IDENTITY.json').exists(), 'scan_existing_identity_no_old_writes')
            scanned = subprocess.run(scan, capture_output=True, text=True, timeout=90, cwd=spec['plan']['source_root'])
            require(scanned.returncode == 0, 'fresh_existing_guard_admission_scan')
            report = json.loads(scanned.stdout)
            require(report['scanner_euid'] == 0 and report['clear'] and not report['blocking_reasons']
                    and report['gpu']['uuid'] == spec['plan']['gpu_uuid'], 'fresh_same_GPU_admission')
            write(folder / 'ADMISSION.json', report)
            write(folder / 'ADMISSION_TIME.json', dict(verified_unix=time.time()))
            (folder / 'DISPATCH_ONCE').mkdir()
            launch = command(folder, 'contained')
            write(folder / 'CONTAINED_COMMAND.json', dict(command=launch, observed_unix=time.time()))
            with (folder / 'SERVICE.log').open('x') as log:
                process = subprocess.Popen(launch, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            write(folder / 'DISPATCHED.json', dict(pid=process.pid, observed_unix=time.time(), resumed_same_saved_life=True))
            return
        write(folder / 'WAIT_EXPIRED.json', dict(status='NO_RETIREMENT', observed_unix=time.time()))
    finally:
        if stopped and not retired and descriptors:
            signal.pidfd_send_signal(descriptors[0], signal.SIGCONT)
        for descriptor in descriptors:
            os.close(descriptor)


def contained(folder):
    cpu(folder)
    config = read(folder / 'GUARD.json')
    plan = read(folder / 'PLAN.json')
    policy = config['device_containment']
    require(os.getuid() == policy['uid'] and os.getgid() == policy['gid'], 'same_nonroot_identity')
    require(Path('/proc/self/cgroup').read_text().strip() == '0::/system.slice/' + policy['unit'] + '.service', 'exact_strict_unit')
    for minor in range(8):
        if minor == policy['minor']:
            continue
        try:
            descriptor = os.open('/dev/nvidia' + str(minor), os.O_RDWR | os.O_CLOEXEC)
        except PermissionError:
            continue
        else:
            os.close(descriptor)
            raise ValueError('foreign_GPU_not_denied')
    from gpu.orch_r133_code_feedback_guard import publish_launch, reap_owned_child
    admitted = read(folder / 'ADMISSION_TIME.json')['verified_unix']
    require(0 <= time.time() - admitted <= 100, 'fresh_admission_inside_service')
    remaining = int(HARD_END - time.time() - 10)
    require(remaining > 10, 'unchanged_stop')
    launch = ['timeout', '--signal=TERM', '--kill-after=5s', str(remaining) + 's', PYTHON,
        '-B', '-m', 'gpu.orch_r125_continual_guard', 'native', '--config', str(folder / 'GUARD.json')]
    process = None
    try:
        with (folder / 'NATIVE.log').open('x') as log:
            process = subprocess.Popen(launch, cwd=plan['source_root'], stdin=subprocess.PIPE,
                stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            ticks = Path('/proc', str(process.pid), 'stat').read_text().rsplit(')', 1)[1].split()[19]
            publish_launch(folder / 'LAUNCH.json', dict(pid=process.pid, parent_start_ticks=ticks,
                started_unix=time.time(), admission_verified_unix=admitted, admission_sha256=sha(folder / 'ADMISSION.json'),
                guard_sha256=sha(folder / 'GUARD.json'), command_sha256=digest(launch), plan_sha256=config['plan_sha256'],
                gpu_uuid=plan['gpu_uuid'], hard_end_unix=HARD_END, no_retry=True))
            process.stdin.write(b'LAUNCH_READY\n')
            process.stdin.close()
            status = process.wait()
        write(folder / 'EXIT.json', dict(exit_code=status, finished_unix=time.time()))
    except BaseException:
        reap_owned_child(process)
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('prepare', 'wait', 'cpu', 'contained'))
    parser.add_argument('--physical', type=int, choices=(0, 1, 2, 3, 4, 7), required=True)
    args = parser.parse_args()
    require(socket.gethostname() == '[REDACTED_HOST]', 'node3_only')
    folder = HERE / 'r181' / ('physical' + str(args.physical))
    try:
        globals()[args.action](folder)
    except BaseException as error:
        write(folder / (args.action.upper() + '_FAILED.json'), dict(error_type=type(error).__name__, reason=str(error)[:500], observed_unix=time.time()))
        raise


if __name__ == '__main__':
    main()
