"""Same-source, exact-sleep runtime extension for protected node5 lives 2 and 6."""

import argparse
from copy import deepcopy
import fcntl
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import signal
import socket
import stat
import subprocess
import sys
import time
import uuid


HOST = '[REDACTED_HOST]'
BASE = Path('/localhome/local-rohing')
PYTHON = BASE / 'v2/venv/bin/python'
AUTH_SHA = '05c50f8012559360221a889b26c00700a988878fbe4d32d30e3f786937dfc392'
NEW_WALL = 1789776000.0
RESOURCE_CEILING = 1789776600.0
LANES = {
    2: ('orch_r125_continual_20260916_attempt1', 'GPU-d62ba12e-ff08-9e5e-ba35-14c723f6e05b'),
    6: ('orch_r127_pilot_20260916_attempt1', 'GPU-67a989f7-2660-a76b-40e8-3619b9fa2987'),
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def read(path):
    path = Path(path)
    require(path.is_absolute() and path.resolve() == path and not path.is_symlink(), 'canonical_input')
    require(path.stat().st_size <= 64 * 1024 * 1024, 'bounded_JSON')
    return json.loads(path.read_bytes())


def sha(path):
    hasher = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            hasher.update(chunk)
    return hasher.hexdigest()


def write(path, value):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'wb') as stream:
        stream.write(encoded(value) + b'\n')
        stream.flush()
        os.fsync(stream.fileno())


def identity(process_id):
    process = Path('/proc') / str(process_id)
    fields = process.joinpath('stat').read_text().rsplit(') ', 1)[1].split()
    return dict(pid=process_id, state=fields[0], parent=int(fields[1]), group=int(fields[2]),
                start_ticks=fields[19], uid=process.stat().st_uid,
                argv=process.joinpath('cmdline').read_bytes().rstrip(b'\0').decode().split('\0'),
                cwd=str(process.joinpath('cwd').resolve()), cgroup=process.joinpath('cgroup').read_text().strip())


def modules(config_path):
    require(socket.gethostname() == HOST, 'node5_only')
    config = read(config_path)
    plan = read(config['plan_path'])
    require(plan['physical'] in LANES, 'protected_2_6_only')
    name, gpu_uuid = LANES[plan['physical']]
    require(plan['root'] == str(BASE / name / 'run1') and plan['gpu_uuid'] == gpu_uuid, 'same_life_same_device')
    source = Path(plan['source_root'])
    sys.path.insert(0, str(source))
    guard = importlib.import_module('gpu.orch_r125_continual_guard')
    require(Path(guard.__file__).resolve() == source / 'gpu/orch_r125_continual_guard.py', 'unchanged_source_import')
    require(guard.validate(str(config_path)) == (config, plan), 'original_guard_validation')
    return config, plan, guard


def extension_plan(plan, state):
    require(plan['physical'] in LANES and state['deadline_unix'] == plan['hard_end_unix'] < NEW_WALL,
            'exact_prior_wall_and_scope')
    name, gpu_uuid = LANES[plan['physical']]
    require(plan['root'] == str(BASE / name / 'run1') and plan['gpu_uuid'] == gpu_uuid, 'same_life_same_device')
    require(state['pending'] is None and state['sleep_frontier'] == len(state['rows'])
            and state['sleep_receipts'] and state['sleep_receipts'][-1]['status'] == 'COMPLETE',
            'completed_sleep_no_pending_work')
    successor = deepcopy(plan)
    successor['hard_end_unix'] = NEW_WALL
    successor['lease_end_unix'] = RESOURCE_CEILING
    successor['authorized_wall_extension'] = dict(schema='R131_SAVED_STATE_WALL_EXTENSION_V1',
        previous_deadline_unix=state['deadline_unix'], previous_stream_sha256=digest(state),
        new_deadline_unix=NEW_WALL, lease_end_unix=RESOURCE_CEILING, safety_margin_seconds=600)
    require('preupdate_recovery' not in successor, 'no_unsaved_replay_handoff')
    unchanged = deepcopy(successor)
    for key in ('hard_end_unix', 'lease_end_unix', 'authorized_wall_extension'):
        unchanged.pop(key, None)
    original = deepcopy(plan)
    for key in ('hard_end_unix', 'lease_end_unix', 'authorized_wall_extension'):
        original.pop(key, None)
    require(unchanged == original, 'only_runtime_budget_changes')
    return successor


def boundary(root):
    paths = sorted(path for path in (Path(root) / 'stream/records').glob('*.json')
                   if re.fullmatch(r'[0-9]{20}\.json', path.name))
    require(paths, 'existing_journal')
    record = read(paths[-1])
    if record['kind'] != 'SLEEP_COMPLETE':
        return None
    require(record['sha256'] == digest({key: value for key, value in record.items() if key != 'sha256'}), 'record_hash')
    document = record['document']
    envelope = document['resume_state']
    require(envelope['sha256'] == digest(envelope['state']) and document['status'] == 'COMPLETE', 'saved_state_hash')
    return dict(record=record, path=str(paths[-1]), state=envelope['state'], cycle=document['cycle'])


def stage(old_config, process_id, output, authority, cpu):
    config, plan, unused_guard = modules(old_config)
    require(sha(authority) == AUTH_SHA and read(authority)['must_abort_on_conflicting_real_reservation'] is True,
            'exact_explicit_user_authority')
    proof = read(cpu)
    require(proof['passed'] is True and proof['operator_sha256'] == sha(__file__), 'bound_CPU_provenance')
    actor = identity(process_id)
    timer = identity(actor['parent'])
    launch = read(Path(config['attempt_dir']) / 'LAUNCH.json')
    require(actor['argv'][-3:] == ['native', '--config', str(old_config)] and actor['cwd'] == plan['source_root'], 'owned_native')
    require(timer['pid'] == actor['group'] == timer['group'] and timer['pid'] == launch['pid']
            and timer['start_ticks'] == launch['parent_start_ticks'] and launch['guard_sha256'] == sha(old_config),
            'owned_timeout_group')
    require(actor['uid'] == timer['uid'] == os.getuid() and actor['cgroup'] == timer['cgroup'], 'owned_confined_identity')
    output.mkdir(mode=0o700)
    write(output / 'STAGED.json', dict(old_config=str(old_config), old_config_sha256=sha(old_config),
        actor=actor, timer=timer, authority=str(authority), authority_sha256=AUTH_SHA,
        cpu=str(cpu), cpu_sha256=sha(cpu), operator=str(Path(__file__).resolve()), operator_sha256=sha(__file__),
        source_pins_sha256=digest(config['source_pins']), staged_unix=time.time(), reset=False))
    return dict(output=str(output), staged=True, stopped=False)


def prepare_successor(output, config, plan, saved, guard):
    successor = extension_plan(plan, saved['state'])
    checkpoint_path = Path(plan['root']) / 'checkpoints' / f"sleep_{saved['cycle']:06d}" / 'COMMIT.json'
    checkpoint = read(checkpoint_path)
    guard.child.NativeChild.verify_checkpoint(checkpoint)
    from organism_v6.orch_r125_continual_stream import ContinualStream
    stream = ContinualStream.restore(dict(state=saved['state'], sha256=digest(saved['state'])),
                                    expected_sha256=digest(saved['state']))
    require(digest(checkpoint['checkpoint_sha256']) == stream.model_state_sha256, 'saved_adapter_optimizer_RNG_bundle')
    expected = guard.child.prepare_wall_extension(successor, stream, resume=True, plan_sha256=digest(successor))
    require(expected['state']['state'] == dict(saved['state'], deadline_unix=NEW_WALL), 'context_and_learning_state_identical')
    request = read(output / 'STAGED.json')
    write(output / 'BOUNDARY.json', dict(record_path=saved['path'], record_sha256=saved['record']['sha256'],
        state_sha256=digest(saved['state']), checkpoint_path=str(checkpoint_path), checkpoint_sha256=sha(checkpoint_path),
        cycle=saved['cycle'], optimizer_steps=checkpoint['optimizer_steps'], adapter_state_sha256=checkpoint['adapter_state_sha256'],
        preserved_state_fields=sorted(set(saved['state']) - {'deadline_unix'})))
    write(output / 'PLAN.json', successor)
    write(output / 'LEASE_BUDGET.json', dict(schema='R157_TEAM_NODE_AUTHORIZED_RUNTIME_BUDGET_V1',
        authority_path=request['authority'], authority_sha256=AUTH_SHA, previous_receipt_path=config['lease_path'],
        previous_receipt_sha256=config['lease_sha256'], hard_end_unix=NEW_WALL, lease_end_unix=RESOURCE_CEILING,
        legacy_lease_end_field_means='authorized_runtime_resource_ceiling_not_provider_booking',
        provider_reservation_expiry_verified=False, purchase_or_lease_transaction=False, safety_margin_seconds=600))
    allocation = read(config['allocation_path'])
    allocation.update(plan_sha256=sha(output / 'PLAN.json'), declared_unix=time.time(),
                      runtime_authority_sha256=AUTH_SHA, runtime_CPU_proof_sha256=request['cpu_sha256'])
    write(output / 'ALLOCATION.json', allocation)
    updated = deepcopy(config)
    updated.update(plan_path=str(output / 'PLAN.json'), plan_sha256=sha(output / 'PLAN.json'),
        lease_path=str(output / 'LEASE_BUDGET.json'), lease_sha256=sha(output / 'LEASE_BUDGET.json'),
        allocation_path=str(output / 'ALLOCATION.json'), allocation_sha256=sha(output / 'ALLOCATION.json'),
        attempt_dir=str(output), resume=True, hard_end_unix=NEW_WALL, next_reserved_unix=RESOURCE_CEILING)
    updated['device_containment'] = dict(updated['device_containment'], unit='orch-r136-native-' + uuid.uuid4().hex)
    require(updated['source_pins'] == config['source_pins'], 'all_frozen_source_bytes_preserved')
    write(output / 'GUARD.json', updated)
    guard.validate(str(output / 'GUARD.json'))


def readmit_stage(previous, output, authority, cpu):
    require(sha(authority) == AUTH_SHA, 'exact_readmission_authority')
    proof = read(cpu)
    require(proof['passed'] is True and proof['operator_sha256'] == sha(__file__), 'bound_readmission_CPU')
    require(not any((previous / name).exists() for name in
                    ('ADMISSION_TIME.json', 'CONTAINED_COMMAND.json', 'LAUNCH.json', 'CONTAINMENT_VERIFIED.json')),
            'failed_before_any_native_dispatch')
    admission = read(previous / 'ADMISSION.json')
    reasons = admission['blocking_reasons']
    stopped = read(previous / 'OLD_STOPPED.json')
    owned = {stopped['old_actor']['pid'], stopped['old_timer']['pid']}
    if stopped['old_timer'].get('parent') is not None:
        owned.add(stopped['old_timer']['parent'])
    cleanup = {f'{kind}:{process_id}' for kind in ('active_compute_pid', 'reserved_cvd_pid', 'uuid_reservation')
               for process_id in owned}
    allowed_cleanup = bool(set(reasons) & cleanup)
    require(not admission['clear'] and reasons and all(
        re.fullmatch(r'process_identity_drift:[0-9]+', reason) or reason in cleanup
        or (reason == 'unexplained_device_memory' and allowed_cleanup) for reason in reasons),
        'transient_identity_or_owned_cleanup_only')
    for reason in reasons:
        if ':' in reason:
            require(not Path('/proc', reason.split(':')[1]).exists(), 'reported_process_now_gone')
    for role in ('old_actor', 'old_timer'):
        require(not Path('/proc', str(stopped[role]['pid'])).exists(), 'old_process_gone')
    supervisor = read(previous / 'SUPERVISOR_STARTED.json')
    require(not Path('/proc', str(supervisor['pid'])).exists(), 'failed_supervisor_gone')
    config, plan, guard = modules(previous / 'GUARD.json')
    saved = boundary(plan['root'])
    original = read(previous / 'BOUNDARY.json')
    require(saved is not None and saved['record']['sha256'] == original['record_sha256']
            and digest(saved['state']) == original['state_sha256'], 'same_unconsumed_saved_boundary')
    checkpoint = read(Path(original['checkpoint_path']))
    guard.child.NativeChild.verify_checkpoint(checkpoint)
    output.mkdir(mode=0o700)
    for name in ('PLAN.json', 'LEASE_BUDGET.json', 'ALLOCATION.json', 'BOUNDARY.json'):
        write(output / name, read(previous / name))
    updated = deepcopy(config)
    updated.update(attempt_dir=str(output), plan_path=str(output / 'PLAN.json'),
        plan_sha256=sha(output / 'PLAN.json'), lease_path=str(output / 'LEASE_BUDGET.json'),
        lease_sha256=sha(output / 'LEASE_BUDGET.json'), allocation_path=str(output / 'ALLOCATION.json'),
        allocation_sha256=sha(output / 'ALLOCATION.json'))
    updated['device_containment'] = dict(updated['device_containment'], unit='orch-r136-native-' + uuid.uuid4().hex)
    write(output / 'GUARD.json', updated)
    guard.validate(str(output / 'GUARD.json'))
    write(output / 'READMISSION.json', dict(previous_attempt=str(previous), previous_admission_sha256=sha(previous / 'ADMISSION.json'),
        authority_sha256=AUTH_SHA, cpu_sha256=sha(cpu), operator_sha256=sha(__file__), prepared_unix=time.time(),
        source_pins_unchanged=updated['source_pins'] == config['source_pins'], no_reset=True,
        boundary_sha256=original['record_sha256'], previous_failure_preserved=True, scanner_checks_unchanged=True))


def watch(output):
    request = read(output / 'STAGED.json')
    require(request['operator_sha256'] == sha(__file__) and sha(request['authority']) == AUTH_SHA
            and sha(request['old_config']) == request['old_config_sha256'], 'stage_pins')
    config, plan, guard = modules(Path(request['old_config']))
    lock = os.open(output / 'OWNER.lock', os.O_CREAT | os.O_RDWR, 0o600)
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    paused = False
    stopped = False
    timer = request['timer']
    def stop_requested(signum, frame):
        raise RuntimeError('operator_stop_requested')
    signal.signal(signal.SIGTERM, stop_requested)
    signal.signal(signal.SIGINT, stop_requested)
    try:
        while time.time() < min(plan['hard_end_unix'] - 120, read(request['cpu'])['boundary_wait_until_unix']):
            saved = boundary(plan['root'])
            if saved is None:
                time.sleep(1)
                continue
            actor_now = identity(request['actor']['pid'])
            timer_now = identity(timer['pid'])
            require(actor_now['start_ticks'] == request['actor']['start_ticks'] and timer_now['start_ticks'] == timer['start_ticks'], 'no_PID_reuse')
            readout_name = guard.child.readout_name(plan, saved['cycle'])
            readout = Path(plan['root']) / 'readouts' / readout_name
            if not (readout / 'REQUEST.json').exists():
                time.sleep(0.2)
                continue
            os.killpg(timer['pid'], signal.SIGSTOP)
            paused = True
            checked = boundary(plan['root'])
            if checked is None or checked['record']['sha256'] != saved['record']['sha256']:
                os.killpg(timer['pid'], signal.SIGCONT)
                paused = False
                continue
            until = min(time.time() + 600, plan['hard_end_unix'] - 120)
            while time.time() < until:
                if (readout / 'COMPLETE.json').exists():
                    active = []
                    child_path = Path('/proc') / str(request['actor']['pid']) / 'task' / str(request['actor']['pid']) / 'children'
                    for value in child_path.read_text().split():
                        try:
                            child = identity(int(value))
                            if child['state'] != 'Z':
                                active.append(child)
                        except FileNotFoundError:
                            pass
                    if not active:
                        break
                time.sleep(0.2)
            else:
                raise RuntimeError('readout_not_finished_at_saved_boundary')
            require(boundary(plan['root'])['record']['sha256'] == saved['record']['sha256'], 'boundary_still_exact')
            prepare_successor(output, config, plan, saved, guard)
            os.killpg(timer['pid'], signal.SIGTERM)
            os.killpg(timer['pid'], signal.SIGCONT)
            paused = False
            stopped = True
            for unused in range(100):
                try:
                    if identity(request['actor']['pid'])['state'] == 'Z':
                        break
                except FileNotFoundError:
                    break
                time.sleep(0.1)
            else:
                raise RuntimeError('old_native_not_exited')
            write(output / 'OLD_STOPPED.json', dict(old_actor=request['actor'], old_timer=timer,
                stopped_unix=time.time(), cycle=saved['cycle'], planned_handoff=True, reset=False))
            command = [str(PYTHON), '-B', str(Path(__file__).resolve()), '--action', 'supervise', '--output', str(output)]
            with (output / 'SUPERVISOR.log').open('x') as log:
                process = subprocess.Popen(command, cwd=plan['source_root'], stdin=subprocess.DEVNULL,
                    stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
                    env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONPATH=plan['source_root'], PYTHONDONTWRITEBYTECODE='1'))
            write(output / 'SUPERVISOR_STARTED.json', dict(pid=process.pid, command=command, started_unix=time.time()))
            return
        raise RuntimeError('no_saved_boundary_before_watch_deadline')
    except BaseException as error:
        if paused and not stopped:
            os.killpg(timer['pid'], signal.SIGCONT)
        write(output / 'HANDOFF_FAILED.json', dict(error=str(error), old_stopped=stopped, no_implicit_retry=True))
        raise
    finally:
        os.close(lock)


def contained_command(config, plan, operator, output):
    policy = config['device_containment']
    properties = dict(User=str(policy['uid']), Group=str(policy['gid']), NoNewPrivileges='yes',
        DevicePolicy='strict', CapabilityBoundingSet='', AmbientCapabilities='', ProtectControlGroups='yes',
        RuntimeMaxSec=str(int(NEW_WALL - time.time())), TimeoutStopSec='5', KillMode='control-group', WorkingDirectory=plan['source_root'])
    devices = ['/dev/null rw', '/dev/zero rw', '/dev/random r', '/dev/urandom r',
               f"/dev/nvidia{policy['minor']} rw", '/dev/nvidiactl rw', '/dev/nvidia-uvm rw']
    return ['sudo', '-n', 'systemd-run', '--quiet', '--wait', '--pipe', '--unit=' + policy['unit'],
        *['--property=' + key + '=' + value for key, value in properties.items()], '--property=DeviceAllow=',
        *['--property=DeviceAllow=' + value for value in devices], '/usr/bin/env', '-i',
        'PATH=/usr/bin:/bin', 'HOME=' + str(BASE), 'CUDA_VISIBLE_DEVICES=' + plan['gpu_uuid'],
        'PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True', 'PYTHONDONTWRITEBYTECODE=1',
        'PYTHONPATH=' + plan['source_root'], 'HF_HUB_OFFLINE=1', 'TRANSFORMERS_OFFLINE=1',
        'OMP_NUM_THREADS=1', 'MKL_NUM_THREADS=1', 'TOKENIZERS_PARALLELISM=false',
        str(PYTHON), '-B', str(operator), '--action', 'contained', '--output', str(output)]


def supervise(output):
    config, plan, unused_guard = modules(output / 'GUARD.json')
    (output / 'DISPATCH_ONCE').mkdir()
    command = ['sudo', '-n', '/usr/bin/env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
        'PYTHONPATH=' + plan['source_root'], str(PYTHON), '-B', '-m', 'gpu.orch_r125_continual_guard',
        'scan', '--config', str(output / 'GUARD.json')]
    result = subprocess.run(command, capture_output=True, text=True, timeout=100, check=False)
    write(output / 'SCAN_PROCESS.json', dict(returncode=result.returncode, stderr=result.stderr[-4000:]))
    require(result.returncode == 0, 'privileged_scanner_process_success')
    report = json.loads(result.stdout)
    write(output / 'ADMISSION.json', report)
    require(report['scanner_euid'] == 0 and report['clear'] and not report['blocking_reasons']
            and report['gpu']['uuid'] == plan['gpu_uuid'], 'fresh_unchanged_admission')
    write(output / 'ADMISSION_TIME.json', dict(verified_unix=time.time()))
    command = contained_command(config, plan, Path(__file__).resolve(), output)
    write(output / 'CONTAINED_COMMAND.json', dict(command=command, started_unix=time.time()))
    result = subprocess.run(command, check=False)
    write(output / 'SERVICE_EXIT.json', dict(returncode=result.returncode, finished_unix=time.time()))
    require(result.returncode == 0, 'contained_native_failure_preserve_state')


def contained(output):
    config, plan, unused_guard = modules(output / 'GUARD.json')
    policy = config['device_containment']
    require(os.getuid() == policy['uid'] > 0 and os.getgid() == policy['gid'] > 0, 'nonroot_contained_identity')
    require(Path('/proc/self/cgroup').read_text().strip() == '0::/system.slice/' + policy['unit'] + '.service', 'actual_service_cgroup')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == plan['gpu_uuid']
            and os.environ.get('PYTORCH_CUDA_ALLOC_CONF') == 'expandable_segments:True', 'same_GPU_allocator')
    matches = []
    for information in Path('/proc/driver/nvidia/gpus').glob('*/information'):
        fields = dict(line.split(':', 1) for line in information.read_text().splitlines() if ':' in line)
        if fields.get('GPU UUID', '').strip() == plan['gpu_uuid']:
            matches.append(int(fields['Device Minor'].strip()))
    require(matches == [policy['minor']], 'actual_kernel_UUID_minor_mapping')
    denied = []
    for minor in range(8):
        if minor == policy['minor']:
            continue
        try:
            descriptor = os.open('/dev/nvidia' + str(minor), os.O_RDWR | os.O_CLOEXEC)
        except PermissionError:
            denied.append(minor)
        else:
            os.close(descriptor)
            raise ValueError('foreign_GPU_not_denied')
    for path in Path('/proc/self/fd').iterdir():
        try:
            item = path.stat()
            require(not (stat.S_ISCHR(item.st_mode) and os.major(item.st_rdev) == 195), 'no_inherited_GPU_FDs')
        except FileNotFoundError:
            pass
    write(output / 'CONTAINMENT_VERIFIED.json', dict(denied_foreign_minors=denied, policy=policy, pid=os.getpid()))
    admitted = read(output / 'ADMISSION_TIME.json')['verified_unix']
    require(0 <= time.time() - admitted < 100, 'fresh_scan_before_native_load')
    command = ['timeout', '--signal=TERM', '--kill-after=5s', str(int(NEW_WALL - time.time() - 10)) + 's',
               str(PYTHON), '-B', '-m', 'gpu.orch_r125_continual_guard', 'native', '--config', str(output / 'GUARD.json')]
    from gpu.orch_r133_code_feedback_guard import publish_launch
    with (output / 'NATIVE.log').open('x') as log:
        process = subprocess.Popen(command, cwd=plan['source_root'], stdin=subprocess.PIPE,
                                   stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        timer = identity(process.pid)
        publish_launch(output / 'LAUNCH.json', dict(pid=process.pid, parent_start_ticks=timer['start_ticks'],
            started_unix=time.time(), admission_verified_unix=admitted, admission_sha256=sha(output / 'ADMISSION.json'),
            guard_sha256=sha(output / 'GUARD.json'), command_sha256=digest(command), plan_sha256=config['plan_sha256'],
            gpu_uuid=plan['gpu_uuid'], hard_end_unix=NEW_WALL, no_retry=True,
            containment_sha256=sha(output / 'CONTAINMENT_VERIFIED.json')))
        process.stdin.write(b'LAUNCH_READY\n')
        process.stdin.close()
        result = process.wait()
    write(output / 'EXIT.json', dict(exit_code=result, finished_unix=time.time(), no_retry=True))
    require(result == 0, 'native_failure_preserve_state')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--action', required=True, choices=('stage', 'readmit-stage', 'watch', 'supervise', 'contained'))
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--old-config', type=Path)
    parser.add_argument('--pid', type=int)
    parser.add_argument('--authority', type=Path)
    parser.add_argument('--cpu', type=Path)
    parser.add_argument('--previous', type=Path)
    options = parser.parse_args()
    if options.action == 'stage':
        print(json.dumps(stage(options.old_config, options.pid, options.output, options.authority, options.cpu)))
    elif options.action == 'readmit-stage':
        readmit_stage(options.previous, options.output, options.authority, options.cpu)
    else:
        globals()[options.action](options.output)


if __name__ == '__main__':
    main()
