"""Receive stopped NODE3 originals on NODE4 using the unchanged native guard."""

import argparse
import ast
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tarfile
import time
import uuid


HOME = Path('/localhome/local-rohing/orch_r188_node4_relocated_20260917t2349z')
BASE = Path('/localhome/local-rohing')
PYTHON = BASE / 'v2/venv/bin/python'
HOST_SHA = 'e376292376f9f56a83e1255021f5b1a4249f1afdff42b5aed3cad36a9635834b'
LEASE = BASE / 'orch_r132_kernel_child_20260916_attempt1/control1/LEASE_BUDGET.json'
LEASE_SHA = 'ca4ead20b2b772c09e4d30e271c24988f0bbcc5f625665e6b63a441fe0e112a2'
R137_SHA = '74cca3f1061f848da049b19e98797c5925e7646002c82147399b0c1131c4dcd2'
DEPENDENCY_SHA = '0a9e370683bebeccdc96d0b344baf154513a37957674c0935c196e614c4920df'
WALL = 1789754400
TARGETS = {0: 7, 2: 5, 3: 6}
DEVICES = {
    5: ('GPU-2e7eb3b8-9b0b-3729-f5ff-2bbdad6a4a30', 6),
    6: ('GPU-06b31c8f-7a96-d812-23f3-df3444d95397', 5),
    7: ('GPU-6eac3b9d-551a-d786-f598-04ef6d701c98', 4),
}
MODULE = 'gpu.orch_r188_node4_rehome_containment'
ATTEMPT = 'v2'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def read(path):
    return json.loads(Path(path).read_bytes())


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, document):
    with Path(path).open('x') as stream:
        json.dump(document, stream, sort_keys=True, indent=2)
        stream.flush()
        os.fsync(stream.fileno())


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def check_host():
    require(hashlib.sha256(socket.gethostname().encode()).hexdigest() == HOST_SHA,
        'exact_NODE4_host')
    require(os.getuid() == os.getgid() == 2524 and sha(LEASE) == LEASE_SHA,
        'nonroot_receiving_identity_and_existing_lease')
    require(read(LEASE)['hard_end_unix'] == WALL and time.time() + 120 < WALL,
        'unchanged_NODE4_wall')


def safe_members(archive, prefix):
    members = archive.getmembers()
    for member in members:
        require((member.name.startswith(prefix) or (member.isdir() and member.name == prefix.rstrip('/')))
            and not Path(member.name).is_absolute()
            and '..' not in Path(member.name).parts, 'owned_archive_path')
        require(member.isfile() or member.isdir() or member.islnk(), 'no_symbolic_or_device_entries')
        if member.islnk():
            require(member.linkname.startswith(prefix) and not Path(member.linkname).is_absolute()
                and '..' not in Path(member.linkname).parts, 'internal_hardlink_only')
    return members


def containment(reference):
    require(hashlib.sha256(reference.encode()).hexdigest() == R137_SHA, 'reviewed_R137_bytes')
    tree = ast.parse(reference)
    devices = next(node for node in tree.body if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == 'DEVICES' for target in node.targets))
    lines = reference.splitlines(keepends=True)
    result = ''.join(lines[:devices.lineno - 1]) + 'DEVICES = ' + repr({
        physical: value[0] for physical, value in DEVICES.items()}) + '\n' + ''.join(lines[devices.end_lineno:])
    return result.replace("'gpu.orch_r137_node4_containment'", repr(MODULE))


def bind_plan(original, source, saved, lease, physical):
    require(physical in TARGETS, 'assigned_original_only')
    require(saved['state']['pending'] is None
        and saved['state']['sleep_frontier'] == len(saved['state']['rows']), 'saved_COMPLETE_not_inflight')
    plan = deepcopy(original)
    plan.update(source_root=str(source), physical=TARGETS[physical],
        gpu_uuid=DEVICES[TARGETS[physical]][0], hard_end_unix=lease['hard_end_unix'],
        lease_end_unix=lease['lease_end_unix'])
    if plan.get('startup_context'):
        relative = Path(plan['startup_context']['path']).relative_to(original['source_root'])
        plan['startup_context']['path'] = str(source / relative)
    plan['authorized_wall_extension'] = dict(schema='R131_SAVED_STATE_WALL_EXTENSION_V1',
        previous_deadline_unix=saved['state']['deadline_unix'], previous_stream_sha256=saved['sha256'],
        new_deadline_unix=lease['hard_end_unix'], lease_end_unix=lease['lease_end_unix'],
        safety_margin_seconds=lease['safety_margin_seconds'])
    return plan


def prepare(physical):
    check_host()
    require(physical in TARGETS, 'assigned_original_only')
    verified = read(HOME / f'metadata/physical{physical}.VERIFIED.json')
    audit = next(row for row in read(HOME / 'metadata/FINAL_SOURCE_STOP_AUDIT.json')['rows']
        if row['physical'] == physical)
    archive_path = HOME / f'transport/physical{physical}.tar.gz'
    require(sha(archive_path) == verified['archive_sha256']
        and archive_path.stat().st_size == verified['archive_bytes'], 'exact_final_packet_bytes')
    require(verified['packet']['final_full_stream_included'] and audit['actors_absent']
        and audit['final']['original_actors_exited'], 'final_stopped_source_required')
    output = HOME / f'receiving{physical}{ATTEMPT}'
    output.mkdir(exist_ok=False)
    with tarfile.open(archive_path) as archive:
        archive.extractall(output, members=safe_members(archive, f'physical{physical}/'))
    packet = output / f'physical{physical}'
    require(read(packet / 'FINAL_STOP.json') == audit['final'], 'exact_source_exit_evidence')
    require(sha(packet / 'FILES.json') == verified['packet']['inventory_sha256'], 'packet_inventory_bound')
    for relative, expected in read(packet / 'FILES.json').items():
        path = packet / relative
        require(path.is_relative_to(packet) and '..' not in Path(relative).parts,
            'safe_manifest_path')
        require(path.stat().st_size == expected['bytes'] and sha(path) == expected['sha256'],
            'packet_file_provenance:' + relative)
    source, control, live = output / 'source', output / 'control', output / 'run1'
    shutil.copytree(packet / 'source', source)
    shutil.copytree(packet / 'root', live)
    for directory in [live, *(path for path in live.rglob('*') if path.is_dir())]:
        directory.chmod(directory.stat().st_mode | 0o700)
    control.mkdir()
    original, old_guard = read(packet / 'control/PLAN.json'), read(packet / 'control/GUARD.json')
    require({str(path.relative_to(source)): sha(path) for path in source.rglob('*.py')}
        == old_guard['source_pins'], 'exact_deployed_source_closure')
    module_path = source / (MODULE.replace('.', '/') + '.py')
    require(not module_path.exists(), 'new_receiving_module_only')
    module_path.write_text(containment((HOME / 'reference_r137.py').read_text()))
    dependency = source / 'gpu/orch_r133_retire_old_lanes.py'
    require(not dependency.exists(), 'add_missing_reviewed_operator_dependency_only')
    require(sha(HOME / dependency.name) == DEPENDENCY_SHA, 'exact_reviewed_dependency')
    shutil.copyfile(HOME / 'orch_r133_retire_old_lanes.py', dependency)
    overlay_meta = read(HOME / 'metadata/FINAL_INBOXES_VERIFIED.json')
    overlay_path = HOME / 'transport/FINAL_INBOXES.tar.gz'
    require(overlay_meta['status'] == 'ALL_OLD_PARENTS_SETTLED_AND_SOURCE_PUBLICATION_PATHS_FROZEN'
        and overlay_meta['apply_after_final_state_packet']
        and sha(overlay_path) == overlay_meta['archive_sha256'], 'frozen_final_inbox_overlay')
    overlay = output / 'overlay'
    overlay.mkdir()
    with tarfile.open(overlay_path) as archive:
        archive.extractall(overlay, members=safe_members(archive, 'final_inboxes_20260917t2350z/'))
    final_inbox = overlay / f'final_inboxes_20260917t2350z/physical{physical}/inbox'
    require(final_inbox.is_dir(), 'own_final_inbox_present')
    (live / 'stream/inbox').rename(output / 'pre_overlay_inbox')
    shutil.copytree(final_inbox, live / 'stream/inbox')
    (live / 'stream/inbox').chmod((live / 'stream/inbox').stat().st_mode | 0o700)
    inbox_pins = {path.name: sha(path) for path in final_inbox.iterdir() if path.is_file()}
    require({path.name: sha(path) for path in (live / 'stream/inbox').iterdir() if path.is_file()}
        == inbox_pins, 'exact_final_inbox_bytes_no_republication')
    root = Path(original['root'])
    require(root.is_relative_to(BASE) and not root.exists() and not root.is_symlink(),
        'unused_original_logical_root')
    root.parent.mkdir(parents=True, exist_ok=True)
    root.symlink_to(live, target_is_directory=True)
    saved_index = verified['packet']['saved_record_index']
    record = read(live / f'stream/records/{saved_index:020d}.json')
    require(record['kind'] == 'SLEEP_COMPLETE' and record['sha256'] == verified['packet']['saved_record_sha256'],
        'exact_saved_COMPLETE_record')
    saved = record['document']['resume_state']
    plan = bind_plan(original, source, saved, read(LEASE), physical)
    write(control / 'PLAN.json', plan)
    pins = {str(path.relative_to(source)): sha(path) for path in source.rglob('*.py')}
    delta = sorted(key for key in set(pins) | set(old_guard['source_pins'])
        if pins.get(key) != old_guard['source_pins'].get(key))
    require(delta == sorted([str(module_path.relative_to(source)), str(dependency.relative_to(source))]),
        'native_journal_guard_unchanged')
    return finish(physical)


def finish(physical):
    check_host()
    require(physical in TARGETS, 'assigned_original_only')
    output = HOME / f'receiving{physical}{ATTEMPT}'
    source, control, live = output / 'source', output / 'control', output / 'run1'
    packet = output / f'physical{physical}'
    require(not (control / 'DISPATCH_ONCE').exists(), 'prelaunch_receiving_only')
    archived_lock = packet / 'final_live_stream/WRITER.lock'
    require(archived_lock.is_file() and archived_lock.stat().st_size == 0, 'actual_archived_writer_lock')
    live_lock = live / 'stream/WRITER.lock'
    if not live_lock.exists():
        shutil.copyfile(archived_lock, live_lock)
    require(sha(live_lock) == sha(archived_lock), 'exact_writer_lock_restored')
    plan = read(control / 'PLAN.json')
    old_guard = read(packet / 'control/GUARD.json')
    verified = read(HOME / f'metadata/physical{physical}.VERIFIED.json')
    audit = next(row for row in read(HOME / 'metadata/FINAL_SOURCE_STOP_AUDIT.json')['rows']
        if row['physical'] == physical)
    overlay_meta = read(HOME / 'metadata/FINAL_INBOXES_VERIFIED.json')
    frozen = read(output / f'overlay/final_inboxes_20260917t2350z/physical{physical}/FROZEN.json')
    inbox_pins = {path.name: sha(path) for path in (live / 'stream/inbox').iterdir() if path.is_file()}
    require(inbox_pins == frozen['inbox_files'], 'frozen_final_inbox_manifest')
    (live / 'stream/inbox').chmod(frozen['receiving_inbox_mode'])
    pins = {str(path.relative_to(source)): sha(path) for path in source.rglob('*.py')}
    delta = sorted(key for key in set(pins) | set(old_guard['source_pins'])
        if pins.get(key) != old_guard['source_pins'].get(key))
    require(delta == ['gpu/orch_r133_retire_old_lanes.py', MODULE.replace('.', '/') + '.py']
        and sha(source / 'gpu/orch_r133_retire_old_lanes.py') == DEPENDENCY_SHA,
        'native_journal_guard_unchanged_exact_dependency')
    saved_index = verified['packet']['saved_record_index']
    saved = read(live / f'stream/records/{saved_index:020d}.json')['document']['resume_state']
    root = Path(plan['root'])
    cpu_code = '''import json,sys
from pathlib import Path
from gpu import orch_r125_continual_native as native
from gpu.orch_r125_stream_journal import StreamJournal
from organism_v6.orch_r125_continual_stream import ContinualStream
from gpu import orch_r188_node4_rehome_containment as containment
plan_path=Path(sys.argv[1]); plan=native.validate_plan(native.read(plan_path))
with StreamJournal(Path(plan['root'])/'stream') as journal:
 state=journal.latest_checkpoint()
 stream=ContinualStream.restore(state['document'],expected_sha256=state['expected_sha256'])
 proof=native.prepare_wall_extension(plan,stream,resume=True,plan_sha256=native.sha(plan_path))
 checkpoints=[native.read(path) for path in (Path(plan['root'])/'checkpoints').glob('*/COMMIT.json')]
 matching=[value for value in checkpoints if native.digest(value['checkpoint_sha256'])==stream.model_state_sha256]
 native.require(len(matching)==1,'exact_model_state')
 checkpoint=matching[0]
 native.require(native.sha(checkpoint['optimizer_rng_path'])==checkpoint['checkpoint_sha256']['optimizer']==checkpoint['checkpoint_sha256']['rng'],'exact_optimizer_rng')
 native.require({path.name:native.sha(path) for path in Path(checkpoint['adapter_path']).iterdir() if path.is_file()}==checkpoint['adapter_files'],'exact_adapter_files')
 native.require(checkpoint.get('experiment')==getattr(stream,'experiment',None),'same_experiment')
 print(json.dumps(dict(passed=True,state_sha256=state['expected_sha256'],model_state_sha256=stream.model_state_sha256,optimizer_steps=checkpoint['optimizer_steps'],history_preserved=True,deadline_only_transition=True,model_calls=0)))
'''
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONPATH=str(source),
        PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
    result = subprocess.run([str(PYTHON), '-B', '-c', cpu_code, str(control / 'PLAN.json')],
        cwd=source, env=environment, capture_output=True, text=True, timeout=180)
    write(control / 'RECEIVING_CPU_COMPAT.json', dict(returncode=result.returncode,
        stdout=result.stdout, stderr=result.stderr, observed_unix=time.time(), source_pins_sha256=digest(pins)))
    require(result.returncode == 0, 'actual_source_receiving_CPU_failed')
    allocation = dict(physical=plan['physical'], gpu_uuid=plan['gpu_uuid'],
        plan_sha256=sha(control / 'PLAN.json'), cpu_tests_passed=True, builder_entry_pushed=True,
        declared_unix=time.time(), builder_entry='Main original-life rehome allocation; NODE4 dated owned Builder receipt',
        authorization='REHOME_ALLOCATIONS_V1_CORRECTED_METADATA.json; existing standing scope',
        cpu_receipt_sha256=sha(control / 'RECEIVING_CPU_COMPAT.json'), lease_extended=False)
    write(control / 'ALLOCATION.json', allocation)
    guard = dict(old_guard, plan_path=str(control / 'PLAN.json'), plan_sha256=sha(control / 'PLAN.json'),
        allocation_path=str(control / 'ALLOCATION.json'), allocation_sha256=sha(control / 'ALLOCATION.json'),
        attempt_dir=str(control), resume=True, source_pins=pins, host_sha256=HOST_SHA,
        hard_end_unix=WALL, next_reserved_unix=read(LEASE)['lease_end_unix'],
        lease_path=str(LEASE), lease_sha256=LEASE_SHA, device_containment=dict(
            uid=2524, gid=2524, minor=DEVICES[plan['physical']][1], unit='orch-r136-native-' + uuid.uuid4().hex))
    write(control / 'GUARD.json', guard)
    write(output / 'PREPARED.json', dict(status='RECEIVING_CPU_PROVEN_NOT_LOADED', physical=physical,
        target_physical=plan['physical'], root=str(root), backing_root=str(live), source_root=str(source),
        guard=str(control / 'GUARD.json'), packet_sha256=verified['archive_sha256'],
        saved_cycle=verified['packet']['captured_cycle'], saved_index=saved_index,
        saved_state_sha256=saved['sha256'], model_state_sha256=verified['packet']['model_state_sha256'],
        final_inbox_sha256=digest(inbox_pins), final_overlay_sha256=overlay_meta['archive_sha256'],
        preserved_suffix_accounting=audit['final']['current_suffix_accounting'],
        exact_inflight_continuation=False, changed_source_files=delta, native_sha256=sha(source / 'gpu/orch_r125_continual_native.py'),
        journal_sha256=sha(source / 'gpu/orch_r125_stream_journal.py'), observed_unix=time.time()))
    return read(output / 'PREPARED.json')


def launch(physical):
    check_host()
    require(physical in TARGETS, 'assigned_original_only')
    output = HOME / f'receiving{physical}{ATTEMPT}'
    ready = read(output / 'PREPARED.json')
    control = output / 'control'
    require(not (control / 'DISPATCH_ONCE').exists(), 'no_dispatch_replay')
    command = [str(PYTHON), '-B', '-m', MODULE, 'contained-supervise', '--config', ready['guard']]
    write(output / 'DISPATCH_INTENT.json', dict(command=command, observed_unix=time.time(),
        prepared_sha256=sha(output / 'PREPARED.json'), no_retry=True))
    with (control / 'SUPERVISOR.log').open('x') as log:
        process = subprocess.Popen(command, cwd=ready['source_root'], stdin=subprocess.DEVNULL,
            stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
            env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
                PYTHONPATH=ready['source_root'], OMP_NUM_THREADS='1', MKL_NUM_THREADS='1'))
    write(output / 'DISPATCHED.json', dict(supervisor_pid=process.pid, observed_unix=time.time(),
        command=command, no_retry=True, status='DISPATCHED_NOT_LOADED'))
    return dict(supervisor_pid=process.pid, original_physical=physical, target_physical=TARGETS[physical])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'finish', 'launch'))
    parser.add_argument('--physical', type=int, choices=tuple(TARGETS), required=True)
    arguments = parser.parse_args()
    print(json.dumps({'prepare': prepare, 'finish': finish, 'launch': launch}[arguments.action](arguments.physical), sort_keys=True))
