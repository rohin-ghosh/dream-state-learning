"""Exact node3 saved-state receiving on node2; no source edits or parent launch."""

import argparse
from copy import deepcopy
import errno
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import socket
import stat
import subprocess
import sys
import tarfile
import time


BASE = Path('/localhome/local-rohing/orch_r188_node2_rehome_20260917t2344z')
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
LEASE = Path('/localhome/local-rohing/orch_r153_r184_node2_20260917/explicit1/LEASE.json')
FORKS = Path('/localhome/local-rohing/orch_r119_l1_generation_20260915_attempt2/FORKS.json')
FORKS_SHA = '621e1391285bcad9ee075106b4afab28970616b663876dc4ebeba7834e7b81e3'
HARD, CEILING = 1789776000, 1789776600
DEVICES = {0: 'GPU-c70cba10-6ab6-a287-e2db-51dccd617ab0',
    7: 'GPU-7c213554-a6c0-5c5a-1117-0422c8eee4ed',
    5: 'GPU-0cc84073-37a0-4f7a-e555-11671425bd03',
    6: 'GPU-a064bca2-bddc-73ad-faf1-a4fbcb49fecf'}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())


def assigned(original, physical):
    require(type(original) is int and type(physical) is int and
        (original, physical) in ((1, 0), (4, 7), (7, 5), (7, 6)), 'assigned_original_target_only')


def member_path(name, prefix):
    path = PurePosixPath(name)
    require(not path.is_absolute() and '..' not in path.parts and path.parts
        and path.parts[0] == prefix, 'archive_owned_relative_path')
    return path


def extract(archive_path, destination, prefix):
    destination.mkdir(parents=True, exist_ok=False)
    with tarfile.open(archive_path, 'r|gz') as archive:
        for member in archive:
            relative = member_path(member.name, prefix)
            target = destination / relative
            require(member.isdir() or member.isfile() or member.islnk(), 'archive_regular_files_and_directories_only')
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            elif member.islnk():
                link = destination / member_path(member.linkname, prefix)
                require(link.is_file() and not link.is_symlink(), 'prior_regular_archive_hardlink')
                target.parent.mkdir(parents=True, exist_ok=True)
                os.link(link, target)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.extractfile(member) as source, target.open('xb') as output:
                    shutil.copyfileobj(source, output, 1024 * 1024)
                require(target.stat().st_size == member.size, 'complete_archive_member')


def reconcile_inbox(original, final):
    prior = {path.name: sha(path) for path in original.iterdir() if path.is_file()}
    after = {path.name: sha(path) for path in final.iterdir() if path.is_file()}
    require(all(after.get(name) == value for name, value in prior.items()), 'final_inbox_preserves_prior_bytes')
    for name in after.keys() - prior.keys():
        shutil.copy2(final / name, original / name)
    require({path.name: sha(path) for path in original.iterdir() if path.is_file()} == after,
        'actual_final_inbox_complete')
    return dict(files=len(after), added=len(after.keys() - prior.keys()), files_digest=digest(after))


def make_plan(old, source, state, physical):
    plan = deepcopy(old)
    require(state['state']['deadline_unix'] == old['hard_end_unix'], 'source_wall_binding')
    require(state['sha256'] == digest(state['state']), 'saved_state_digest')
    plan.update(source_root=str(source), physical=physical, gpu_uuid=DEVICES[physical],
        hard_end_unix=HARD, lease_end_unix=CEILING,
        authorized_wall_extension=dict(schema='R131_SAVED_STATE_WALL_EXTENSION_V1',
            previous_deadline_unix=old['hard_end_unix'], previous_stream_sha256=state['sha256'],
            new_deadline_unix=HARD, lease_end_unix=CEILING, safety_margin_seconds=600))
    if plan.get('startup_context'):
        relative = Path(old['startup_context']['path']).relative_to(old['source_root'])
        plan['startup_context']['path'] = str(source / relative)
    restored = deepcopy(plan)
    restored.pop('authorized_wall_extension')
    for key in ('source_root', 'physical', 'gpu_uuid', 'hard_end_unix', 'lease_end_unix', 'startup_context'):
        if key in old:
            restored[key] = old[key]
    require(restored == old, 'only_receiving_paths_device_and_budget_change')
    return plan


def prepare(original, physical):
    assigned(original, physical)
    require(socket.gethostname() == '[REDACTED_HOST]', 'actual_node2')
    folder = BASE / ('receiving' + str(original))
    folder.mkdir(exist_ok=False)
    write(folder / 'PREPARE_STARTED.json', dict(started_unix=time.time(), original=original,
        physical=physical, helper_sha256=sha(__file__), no_retry=True))
    verified = read(BASE / 'final_transport' / f'physical{original}.VERIFIED.json')
    archive = BASE / 'final_transport' / f'physical{original}.tar.gz'
    require(verified['status'] == 'PERSISTENT_LOCAL_PACKET_VERIFIED' and
        verified['archive_paths_verified'] and verified['gzip_crc_verified'] and
        sha(archive) == verified['archive_sha256'], 'exact_final_packet_transport')
    require(verified['packet']['final_full_stream_included'] and not verified['packet']['current_learner_continues'],
        'final_not_initial_packet')
    require(shutil.disk_usage(BASE).free > 6 * 1024**3, 'receiving_disk_margin')
    extract(archive, folder / 'preserved', 'physical' + str(original))
    packet_root = folder / 'preserved' / ('physical' + str(original))
    packet = read(packet_root / 'PACKET.json')
    require(packet == verified['packet'], 'packet_metadata_binding')
    require(sha(packet_root / 'FILES.json') == packet['inventory_sha256'], 'packet_inventory_binding')
    stop = read(packet_root / 'FINAL_STOP.json')
    require(stop['original_actors_exited'], 'original_native_actors_stopped')
    source = packet_root / 'source'
    old_guard, old_plan = read(packet_root / 'control/GUARD.json'), read(packet_root / 'control/PLAN.json')
    pins = {str(path.relative_to(source)): sha(path) for path in source.rglob('*.py')}
    require(pins == old_guard['source_pins'], 'original_effective_python_closure')
    raw = folder / 'root'
    subprocess.run(['cp', '-a', '--reflink=auto', str(packet_root / 'root'), str(raw)], check=True)
    lock = raw / 'stream/WRITER.lock'
    if not lock.exists():
        lock.touch(exist_ok=False)
    overlay_receipt = read(BASE / 'final_transport/FINAL_INBOXES_VERIFIED.json')
    overlay_archive = BASE / 'final_transport/FINAL_INBOXES.tar.gz'
    require(overlay_receipt['status'] == 'ALL_OLD_PARENTS_SETTLED_AND_SOURCE_PUBLICATION_PATHS_FROZEN'
        and overlay_receipt['apply_after_final_state_packet'] and sha(overlay_archive) == overlay_receipt['archive_sha256'],
        'settled_parent_final_inbox_overlay')
    extract(overlay_archive, folder / 'overlay', 'final_inboxes_20260917t2350z')
    inbox = reconcile_inbox(raw / 'stream/inbox',
        folder / 'overlay/final_inboxes_20260917t2350z' / ('physical' + str(original)) / 'inbox')
    record_path = raw / 'stream/records' / f"{packet['saved_record_index']:020d}.json"
    record = read(record_path)
    require(record['kind'] == 'SLEEP_COMPLETE' and record['sha256'] == packet['saved_record_sha256']
        and record['sha256'] == digest({key: value for key, value in record.items() if key != 'sha256'}),
        'actual_saved_complete_record')
    state = record['document']['resume_state']
    require(state['state']['pending'] is None and state['state']['sleep_frontier'] == len(state['state']['rows']),
        'saved_frontier_no_unsaved_training')
    commit_path = raw / 'checkpoints' / f"sleep_{packet['captured_cycle']:06d}" / 'COMMIT.json'
    commit = read(commit_path)
    require(sha(commit_path) == packet['checkpoint_file_sha256'], 'exact_commit_file')
    mapped = lambda value: raw / Path(value).relative_to(old_plan['root'])
    require(sha(mapped(commit['optimizer_rng_path'])) == commit['checkpoint_sha256']['optimizer']
        == commit['checkpoint_sha256']['rng'], 'exact_optimizer_rng')
    adapter = {path.name: sha(path) for path in mapped(commit['adapter_path']).iterdir() if path.is_file()}
    require(adapter == commit['adapter_files'] and digest(adapter) == commit['checkpoint_sha256']['adapter']
        and digest(commit['checkpoint_sha256']) == state['state']['model_state_sha256'], 'exact_saved_adapter')
    require(sha(FORKS) == FORKS_SHA and HARD <= read(FORKS)['hard_deadline_unix'], 'existing_node2_machine_budget')
    lease = read(LEASE)
    require(lease['hard_end_unix'] == HARD and lease['lease_end_unix'] == CEILING, 'existing_receiving_deadline')
    plan = make_plan(old_plan, source, state, physical)
    for key in ('model_dir', 'anchors'):
        require(Path(plan[key]).is_dir(), 'existing_local_dependency_' + key)
    write(folder / 'PLAN.json', plan)
    sys.path.insert(0, str(source))
    from gpu import orch_r125_continual_guard as guard
    from organism_v6.orch_r125_continual_stream import ContinualStream
    guard.child.validate_plan(plan)
    restored = ContinualStream.restore(state, expected_sha256=state['sha256'])
    guard.child.prepare_wall_extension(plan, restored, resume=True, plan_sha256=sha(folder / 'PLAN.json'))
    write(folder / 'ALLOCATION.json', dict(plan_sha256=sha(folder / 'PLAN.json'), cpu_tests_passed=True,
        gpu_uuid=plan['gpu_uuid'], physical=physical, builder_entry_pushed=True, declared_unix=time.time(),
        authority='Main/Astra scheduling under standing user keep-alive directives', machine_lease_changed=False))
    config = dict(schema='R125_CONTINUAL_GUARD_V1', source_pins=pins, resume=True,
        plan_path=str(folder / 'PLAN.json'), plan_sha256=sha(folder / 'PLAN.json'), attempt_dir=str(folder),
        host_sha256=hashlib.sha256(socket.gethostname().encode()).hexdigest(), hard_end_unix=HARD,
        lease_path=str(LEASE), lease_sha256=sha(LEASE), next_reserved_unix=CEILING,
        allocation_path=str(folder / 'ALLOCATION.json'), allocation_sha256=sha(folder / 'ALLOCATION.json'))
    write(folder / 'GUARD.json', config)
    guard.validate(folder / 'GUARD.json')
    ready = dict(status='ACTUAL_RECEIVING_CPU_READY_NOT_LAUNCHED', original=original, physical=physical,
        raw_root=str(raw), logical_root=plan['root'], source_root=str(source), gpu_uuid=plan['gpu_uuid'],
        source_pins=pins, guard_sha256=sha(folder / 'GUARD.json'), plan_sha256=config['plan_sha256'],
        archive_sha256=verified['archive_sha256'], inbox_overlay_sha256=overlay_receipt['archive_sha256'],
        inbox=inbox, saved_cycle=packet['captured_cycle'], saved_index=packet['saved_record_index'],
        optimizer_steps=commit['optimizer_steps'], preserved_source_stop_accounting=stop['current_suffix_accounting'],
        helper_sha256=sha(__file__), lease_sha256=sha(LEASE), hard_end_unix=HARD, lease_end_unix=CEILING,
        parent_started=False, original_source_modified=False, observed_unix=time.time())
    write(folder / 'CPU_READY.json', ready)
    return {key: value for key, value in ready.items() if key != 'source_pins'}


def device_checks(physical, opener=os.open, closer=os.close):
    allowed, denied = [], []
    for minor in range(8):
        try:
            descriptor = opener('/dev/nvidia' + str(minor), os.O_RDWR | os.O_CLOEXEC)
        except OSError as error:
            require(minor != physical and error.errno in (errno.EACCES, errno.EPERM), 'foreign_device_denial')
            denied.append(minor)
        else:
            closer(descriptor)
            require(minor == physical, 'foreign_device_open_abort')
            allowed.append(minor)
    for path in ('/dev/nvidiactl', '/dev/nvidia-uvm'):
        closer(opener(path, os.O_RDWR | os.O_CLOEXEC))
    return dict(target_open_close=allowed == [physical], denied_foreign_minors=denied)


def command(folder, mode):
    ready = read(folder / 'CPU_READY.json')
    physical = ready['physical']
    unit = 'orch-r188-node2-' + str(ready['original']) + '-' + mode + '-' + ready['guard_sha256'][:16]
    properties = dict(User='2524', Group='2524', NoNewPrivileges='yes', DevicePolicy='strict',
        CapabilityBoundingSet='', AmbientCapabilities='', ProtectControlGroups='yes',
        RuntimeMaxSec=str(60 if mode == 'probe' else int(HARD - time.time() - 10)),
        TimeoutStopSec='5', KillMode='control-group', WorkingDirectory=ready['source_root'],
        MemoryMax=str(64 * 1024**3), TasksMax='256',
        BindPaths=ready['raw_root'] + ':' + ready['logical_root'], ReadOnlyPaths=ready['source_root'])
    devices = ['/dev/null rw', '/dev/zero rw', '/dev/random r', '/dev/urandom r',
        '/dev/nvidia' + str(physical) + ' rw', '/dev/nvidiactl rw', '/dev/nvidia-uvm rw']
    return ['sudo', '-n', '/usr/bin/systemd-run', '--quiet', '--wait', '--pipe', '--unit=' + unit,
        *['--property=' + key + '=' + value for key, value in properties.items()], '--property=DeviceAllow=',
        *['--property=DeviceAllow=' + value for value in devices], '/usr/bin/env', '-i',
        'PATH=/usr/bin:/bin', 'HOME=/localhome/local-rohing', 'TMPDIR=/tmp',
        'CUDA_VISIBLE_DEVICES=' + ready['gpu_uuid'], 'PYTHONDONTWRITEBYTECODE=1',
        'PYTHONPATH=' + ready['source_root'], 'HF_HUB_OFFLINE=1', 'TRANSFORMERS_OFFLINE=1',
        'OMP_NUM_THREADS=1', 'MKL_NUM_THREADS=1', 'TOKENIZERS_PARALLELISM=false',
        'PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True', PYTHON, '-B', str(Path(__file__).resolve()),
        mode, '--original', str(ready['original']), '--physical', str(physical)]


def confined(folder, mode):
    ready = read(folder / 'CPU_READY.json')
    require(sha(__file__) == ready['helper_sha256'], 'bound_external_launcher')
    unit = 'orch-r188-node2-' + str(ready['original']) + '-' + mode + '-' + ready['guard_sha256'][:16]
    require(os.getuid() == os.getgid() == 2524 and Path('/proc/self/cgroup').read_text().strip()
        == '0::/system.slice/' + unit + '.service', 'actual_nonroot_strict_unit')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == ready['gpu_uuid'], 'actual_UUID_environment')
    matching = []
    for path in Path('/proc/driver/nvidia/gpus').glob('*/information'):
        fields = dict(line.split(':', 1) for line in path.read_text().splitlines() if ':' in line)
        if fields.get('GPU UUID', '').strip() == ready['gpu_uuid']:
            matching.append(int(fields['Device Minor'].strip()))
    require(matching == [ready['physical']], 'kernel_UUID_minor_binding')
    for path in Path('/proc/self/fd').iterdir():
        try:
            require(not os.readlink(path).startswith('/dev/nvidia'), 'no_inherited_GPU_FD')
        except FileNotFoundError:
            pass
    proof = dict(device_checks(ready['physical']), observed_unix=time.time(), unit=unit,
        gpu_uuid=ready['gpu_uuid'], CUDA_context_created=False)
    write(folder / ('CONFINEMENT_' + mode.upper() + '.json'), proof)
    if mode == 'probe':
        return proof
    sys.path.insert(0, ready['source_root'])
    from gpu import orch_r125_continual_guard as guard
    from gpu.orch_r133_code_feedback_guard import publish_launch, reap_owned_child
    config, plan = guard.validate(folder / 'GUARD.json')
    admitted = read(folder / 'ADMISSION_TIME.json')['verified_unix']
    require(0 <= time.time() - admitted <= 100, 'fresh_admission_inside_strict_service')
    argv = ['timeout', '--signal=TERM', '--kill-after=5s', str(int(HARD - time.time() - 10)) + 's',
        PYTHON, '-B', '-m', 'gpu.orch_r125_continual_guard', 'native', '--config', str(folder / 'GUARD.json')]
    process = None
    try:
        with (folder / 'NATIVE.log').open('x') as log:
            process = subprocess.Popen(argv, cwd=ready['source_root'], stdin=subprocess.PIPE,
                stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            ticks = Path('/proc', str(process.pid), 'stat').read_text().rsplit(')', 1)[1].split()[19]
            publish_launch(folder / 'LAUNCH.json', dict(pid=process.pid, parent_start_ticks=ticks,
                started_unix=time.time(), admission_verified_unix=admitted,
                admission_sha256=sha(folder / 'ADMISSION.json'), guard_sha256=ready['guard_sha256'],
                command_sha256=digest(argv), plan_sha256=config['plan_sha256'], gpu_uuid=ready['gpu_uuid'],
                hard_end_unix=HARD, no_retry=True))
            process.stdin.write(b'LAUNCH_READY\n')
            process.stdin.close()
            result = process.wait()
        write(folder / 'EXIT.json', dict(exit_code=result, finished_unix=time.time()))
        return dict(exit_code=result)
    except BaseException:
        reap_owned_child(process)
        raise


def dispatch(folder):
    ready = read(folder / 'CPU_READY.json')
    require(sha(__file__) == ready['helper_sha256'], 'unchanged_launcher')
    builder = read(folder / 'BUILDER_ENTRY.json')
    require(builder['cpu_ready_sha256'] == sha(folder / 'CPU_READY.json') and builder['logged_in_coordination'],
        'actual_posted_CPU_provenance')
    (folder / 'DISPATCH_ONCE').mkdir()
    write(folder / 'DISPATCH_STARTED.json', dict(pid=os.getpid(), started_unix=time.time(), no_retry=True))
    subprocess.run(command(folder, 'probe'), check=True, timeout=90)
    scan = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
        'PYTHONPATH=' + ready['source_root'], PYTHON, '-B', '-m', 'gpu.orch_r125_continual_guard',
        'scan', '--config', str(folder / 'GUARD.json')]
    result = subprocess.run(scan, capture_output=True, text=True, timeout=100)
    require(result.returncode == 0, 'receiving_scanner_exit:' + result.stderr[-400:])
    admission = json.loads(result.stdout)
    write(folder / 'ADMISSION.json', admission)
    require(admission['scanner_euid'] == 0 and admission['clear'] and not admission['blocking_reasons']
        and admission['gpu']['uuid'] == ready['gpu_uuid'], 'fresh_privileged_exclusive_admission')
    write(folder / 'ADMISSION_TIME.json', dict(verified_unix=time.time()))
    result = subprocess.run(command(folder, 'contained'), check=False)
    write(folder / 'OUTER_EXIT.json', dict(exit_code=result.returncode, finished_unix=time.time()))
    return dict(exit_code=result.returncode)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('prepare', 'probe', 'contained', 'dispatch'))
    parser.add_argument('--original', required=True, type=int)
    parser.add_argument('--physical', required=True, type=int)
    args = parser.parse_args()
    assigned(args.original, args.physical)
    folder = BASE / ('receiving' + str(args.original))
    try:
        result = (prepare(args.original, args.physical) if args.mode == 'prepare' else
            dispatch(folder) if args.mode == 'dispatch' else confined(folder, args.mode))
        print(json.dumps(result, sort_keys=True), flush=True)
    except BaseException as error:
        if folder.exists():
            write(folder / (args.mode.upper() + '_FAILED.json'), dict(error_type=type(error).__name__,
                reason=str(error)[-1200:], observed_unix=time.time(), no_retry=True))
        raise
