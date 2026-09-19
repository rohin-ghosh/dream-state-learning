"""Explicit saved30 recovery segment; original interrupted artifacts stay intact."""

import argparse
from copy import deepcopy
from collections import Counter
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import time
from types import SimpleNamespace
import uuid


HOST = 'ipp2-ovx-p1-10'
BASE = Path('/localhome/local-rohing')
LIFE = BASE / 'orch_r136_repo_reader_20260916_attempt1'
ROOT = LIFE / 'run1'
GPU_UUID = 'GPU-9e6cdf73-7181-4405-2aec-787cc73a3e5b'
OLD_WALL = 1789596240.0
HARD_END = 1789617240.0
LEASE_END = 1789617840.0
GUARD_SHA = '4c14121560018ece983f24455c697274af8800dee8444c55e831a4596c8feb56'
LEASE = BASE / 'orch_r125_continual_20260916_attempt1/control6/LEASE_BUDGET.json'
LEASE_SHA = '12e187a3237d6c167d91c4abaae9e6ef671e096d827c9ed68a662aa465d51049'
NATIVE_SHA = '7626d13974a78c713b9e966093e285e1e8a4f194301dd8b69ec68cfcae656526'
ALLOWED_DOCUMENTS = {'access.md', 'continuity.md', 'overview.md'}
PYTHON = BASE / 'v2/venv/bin/python'
CAPSULE_SHA = '29e2d77dfe21a6c1b37861f52c00d2eeb858c67b60f054ab6e2d2238cc135c95'
AUTHORITY = 'Main_R154_EXACT_SAVED30_SEGMENT_125_UNSAVED_UPDATES_ARCHIVED'
SAVED_SHA = 'fd25b9ff33a44340a112c28844694d66a1135d5e50fa2f485d256a728b3824d3'
CHECKPOINT_SHA = '0080688e878cb18418a7afbba66085a8de972da4481bc494ad7e6dec47eb37d5'
HEAD_SHA = '932ab5ee4bbce469921edda15f0b543b92fd77482817bae8bf3ee5f8aa580f5e'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def regular(path):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts, 'absolute_path')
    require(not any(part.is_symlink() for part in (path, *path.parents)), 'no_symlinks')
    return path


def digest(document):
    return hashlib.sha256(json.dumps(document, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()


def sha(path):
    hasher = hashlib.sha256()
    with regular(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            hasher.update(chunk)
    return hasher.hexdigest()


def read(path):
    path = regular(path)
    require(path.stat().st_size <= 16 * 1024 * 1024, 'bounded_JSON')
    return json.loads(path.read_bytes())


def reference(path):
    return dict(path=str(path), sha256=sha(path))


def scope(plan, guard):
    require(type(plan['physical']) is int and plan['physical'] == 7
            and plan['gpu_uuid'] == GPU_UUID and plan['root'] == str(ROOT)
            and plan['source_root'] == str(LIFE / 'source1'), 'exact_repo_reader_only')
    require(plan['hard_end_unix'] == guard['hard_end_unix'] == OLD_WALL
            and plan['lease_end_unix'] == guard['next_reserved_unix'] == LEASE_END,
            'unchanged_original_wall_lease')


def wall_authorization(state, lease):
    require(lease['hard_end_unix'] == HARD_END and lease['lease_end_unix'] == LEASE_END,
            'existing_node5_receipt_wall_only')
    require(state['deadline_unix'] == OLD_WALL, 'exact_prior_stream_wall')
    require(state['pending'] is None and state['sleep_frontier'] == len(state['rows'])
            and state['sleep_receipts'] and state['sleep_receipts'][-1]['status'] == 'COMPLETE',
            'wall_extension_saved_sleep_boundary')
    return dict(schema='R131_SAVED_STATE_WALL_EXTENSION_V1', previous_deadline_unix=OLD_WALL,
                previous_stream_sha256=digest(state), new_deadline_unix=HARD_END,
                lease_end_unix=LEASE_END, safety_margin_seconds=600)


def chain(records, manifest):
    previous = digest(manifest)
    for index, record in enumerate(records):
        require(record['index'] == index and record['journal_id'] == manifest['journal_id']
                and record['previous_sha256'] == previous
                and record['sha256'] == digest({key: value for key, value in record.items() if key != 'sha256'}),
                'complete_original_journal_chain')
        previous = record['sha256']


def suffix_summary(records, saved_index, saved_steps):
    tail = records[saved_index + 1:]
    updates = [record for record in tail if record['kind'] == 'UPDATE']
    steps = [record['document']['optimizer_step'] for record in updates]
    require(steps == list(range(saved_steps + 1, saved_steps + 1 + len(steps))), 'consecutive_UPDATE_accounting')
    return dict(counts=dict(Counter(record['kind'] for record in tail)),
                unsaved_updates=len(updates), saved_optimizer_steps=saved_steps,
                last_optimizer_step=steps[-1] if steps else saved_steps,
                update_state_snapshots_available=bool(updates) and all(
                    all(key in record['document'] for key in ('adapter_state_sha256', 'optimizer_sha256', 'rng_sha256'))
                    for record in updates),
                tail_metadata=[dict(index=record['index'], kind=record['kind'], record_sha256=record['sha256'])
                               for record in tail])


def require_clean_recovery(summary, state):
    require(summary['unsaved_updates'] == 0, 'unsaved_UPDATE_requires_separate_verified_reconciliation')
    require(state['pending'] is None and state['sleep_frontier'] == len(state['rows']),
            'exact_saved_RNG_sleep_boundary_required')


def broker_preflight(config, directory):
    require(config['root'] == str(ROOT) and config['snapshot'] == str(LIFE / 'snapshot1'),
            'same_reader_snapshot_scope')
    manifest_path = LIFE / 'snapshot1/MANIFEST.json'
    require(sha(manifest_path) == config['manifest_sha256'], 'original_reviewed_snapshot_pin')
    manifest = read(manifest_path)
    require(set(manifest['files']) == ALLOWED_DOCUMENTS
            and {path.name for path in (LIFE / 'snapshot1').iterdir()} == ALLOWED_DOCUMENTS | {'MANIFEST.json'},
            'only_three_reviewed_documents')
    for name, metadata in manifest['files'].items():
        path = LIFE / 'snapshot1' / name
        require(sha(path) == metadata['sha256'] and path.stat().st_size == metadata['bytes'], 'same_snapshot_bytes')
    names = sorted(path.name for path in directory.iterdir())
    read_names = [name for name in names if re.fullmatch(r'READ_\d{20}\.json', name)]
    return dict(config_wall=config['hard_end_unix'], snapshot=reference(manifest_path),
                snapshot_files_verified=True, completed_historical_reads=len(read_names),
                historical_receipt_inventory_sha256=digest(names),
                restart_from_zero_permitted=False,
                blockers=['broker_original_wall_expired', 'durable_no_replay_cursor_required_before_restart'])


def inspect():
    require(socket.gethostname() == HOST, 'exact_ovx3_host')
    require(time.time() < HARD_END, 'remaining_authorized_wall_required')
    guard_path = LIFE / 'control1/GUARD.json'
    require(sha(guard_path) == GUARD_SHA and sha(LEASE) == LEASE_SHA, 'exact_original_guard_and_current_lease')
    guard = read(guard_path)
    plan = read(guard['plan_path'])
    scope(plan, guard)
    require(sha(guard['plan_path']) == guard['plan_sha256']
            and sha(guard['allocation_path']) == guard['allocation_sha256'], 'old_plan_allocation_hashes')
    for name, expected in guard['source_pins'].items():
        require(not Path(name).is_absolute() and '..' not in Path(name).parts, 'relative_source_pin')
        require(sha(Path(plan['source_root']) / name) == expected, 'original_source_closure:' + name)
    require(sha(LIFE / 'source1/gpu/orch_r125_continual_native.py') == NATIVE_SHA, 'exact_old_native')
    directory = ROOT / 'stream/records'
    paths = sorted(path for path in directory.iterdir() if re.fullmatch(r'\d{20}\.json', path.name))
    require(0 < len(paths) <= 12000, 'bounded_journal_record_count')
    require(sum(path.stat().st_size for path in paths) <= 512 * 1024 * 1024, 'bounded_journal_bytes')
    records = [read(path) for path in paths]
    chain(records, read(ROOT / 'stream/JOURNAL.json'))
    saved = next(record for record in reversed(records) if record['kind'] == 'SLEEP_COMPLETE')
    envelope = saved['document']['resume_state']
    require(digest(envelope['state']) == envelope['sha256'], 'saved_full_context_hash')
    checkpoint_path = ROOT / f"checkpoints/sleep_{saved['document']['cycle']:06d}/COMMIT.json"
    checkpoint = read(checkpoint_path)
    require(saved['document']['checkpoint'] == checkpoint, 'saved_record_checkpoint_binding')
    adapter = regular(checkpoint['adapter_path'])
    require(adapter == checkpoint_path.parent / 'adapter'
            and checkpoint['optimizer_rng_path'] == str(checkpoint_path.parent / 'optimizer_rng.pt'),
            'own_saved_checkpoint_paths')
    require({path.name for path in adapter.iterdir()} == set(checkpoint['adapter_files']), 'exact_adapter_inventory')
    for name, expected in checkpoint['adapter_files'].items():
        require(Path(name).name == name and sha(adapter / name) == expected, 'saved_adapter_file_hash')
    hashes = checkpoint['checkpoint_sha256']
    require(digest(checkpoint['adapter_files']) == hashes['adapter']
            and sha(checkpoint['optimizer_rng_path']) == hashes['optimizer'] == hashes['rng'], 'saved_AdamW_RNG_file_hash')
    latest = next(record for record in reversed(records) if record['kind'] in
                  ('SLEEP_COMPLETE', 'SLEEP_REQUEST', 'COMMITTED', 'COMPACTION', 'PRESENTATION', 'WALL_EXTENDED'))
    state_key = 'resume_state' if latest['kind'] in ('SLEEP_COMPLETE', 'SLEEP_REQUEST') else 'state'
    current = latest['document'][state_key]
    require(digest(current['state']) == current['sha256'], 'latest_context_carry_state_hash')
    suffix = suffix_summary(records, saved['index'], checkpoint['optimizer_steps'])
    blockers = []
    try:
        require_clean_recovery(suffix, current['state'])
    except ValueError as error:
        blockers.append(str(error))
    broker = broker_preflight(read(LIFE / 'BROKER_CONFIG_V2.json'), LIFE / 'broker2')
    blockers.extend(broker['blockers'])
    apps = subprocess.run(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid', '--format=csv,noheader,nounits'],
                          check=True, capture_output=True, text=True, timeout=15)
    own_pids = [int(line.split(',')[1]) for line in apps.stdout.splitlines() if line.split(',')[0].strip() == GPU_UUID]
    if own_pids:
        blockers.append('existing_physical7_compute_owner')
    candidate = BASE / 'orch_r143_node5_target_allocator_physical7_20260916t1536z_readyfirst1'
    return dict(schema='R154_REPO_READER_PREFLIGHT_V1', status='BLOCKED', blockers=blockers,
        root=str(ROOT), physical=7, gpu_uuid=GPU_UUID, observed_unix=time.time(),
        guard=reference(guard_path), lease=reference(LEASE), original_exit=reference(LIFE / 'control1/EXIT.json'),
        old_native_sha256=NATIVE_SHA, original_source_closure_verified=True,
        saved=dict(cycle=saved['document']['cycle'], index=saved['index'], record=reference(paths[saved['index']]),
                   state_sha256=envelope['sha256'], checkpoint=reference(checkpoint_path),
                   optimizer_steps=checkpoint['optimizer_steps'], bundle_sha256=hashes,
                   adapter_state_sha256=checkpoint['adapter_state_sha256']),
        head=dict(index=records[-1]['index'], kind=records[-1]['kind'], file=reference(paths[-1])),
        current_state_sha256=current['sha256'], suffix=suffix, broker=broker,
        historical_saved_boundary_wall_authorization=wall_authorization(envelope['state'], read(LEASE)),
        historical_wall_authorization_not_dispatchable_against_current_pending_state=True,
        original_readyfirst_wait_expired=reference(candidate / 'WAIT_EXPIRED.json'),
        target_compute_pids=own_pids, launch_authorized=False, no_remote_mutation=True,
        full_chain_verified=True, checkpoint_files_verified=True,
        strict_confinement_and_fresh_admission_still_required=True)


def write(path, document):
    with regular(path).open('x') as stream:
        json.dump(document, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def output_scope(output):
    output = regular(output)
    require(output.parent == LIFE and re.fullmatch(r'recovery_r154_saved30_20260916_attempt[1-9][0-9]*', output.name),
            'dedicated_saved30_segment_only')
    return output


def explicit_cutoff(evidence, authority):
    require(authority == AUTHORITY, 'explicit_saved_checkpoint_recovery_authority')
    require(evidence['saved']['cycle'] == 30 and evidence['saved']['optimizer_steps'] == 2745
            and evidence['saved']['index'] == 3179 and evidence['saved']['state_sha256'] == SAVED_SHA
            and evidence['saved']['checkpoint']['sha256'] == CHECKPOINT_SHA
            and evidence['head']['index'] == 3317 and evidence['head']['file']['sha256'] == HEAD_SHA,
            'exact_adjudicated_saved30_and_archived_head')
    require(evidence['suffix']['unsaved_updates'] == 125 and evidence['suffix']['last_optimizer_step'] == 2870,
            'explicit_125_unsaved_updates_not_restored')
    return dict(logical_life='repo_reader', recovery_type='EXACT_SAVED30_NOT_INTERRUPTED2870',
        restored_optimizer_steps=2745, archived_last_optimizer_step=2870, unsaved_updates_not_restored=125,
        discarded_compute_not_artifacts=True, original_full_journal_preserved=True,
        archived_suffix_replayed=False, archived_text_reinjected=False, fresh_base_or_adapter=False,
        authority=authority, saved_record_index=3179, archived_head_index=3317)


def plan_for_segment(old, destination, source, authorization):
    proposed = deepcopy(old)
    proposed.update(root=str(destination), source_root=str(source), hard_end_unix=HARD_END,
                    authorized_wall_extension=authorization)
    require(old.get('preupdate_recovery') is None and old.get('authorized_wall_extension') is None,
            'no_pending_recovery_directive_in_original_plan')
    if old.get('startup_context'):
        relative = Path(old['startup_context']['path']).relative_to(Path(old['source_root']))
        proposed['startup_context']['path'] = str(source / relative)
    restored = deepcopy(proposed)
    restored.pop('authorized_wall_extension')
    for key in ('root', 'source_root', 'hard_end_unix'):
        restored[key] = old[key]
    if old.get('startup_context'):
        restored['startup_context'] = old['startup_context']
    require(restored == old, 'recipe_unchanged_saved30_old_runtime_first')
    return proposed


def copy_prefix(original, destination, cutoff):
    original, destination = regular(original), regular(destination)
    require(not destination.exists() and not destination.is_relative_to(original), 'new_independent_stream')
    destination.mkdir(mode=0o700)
    (destination / 'records').mkdir(mode=0o700)
    (destination / 'inbox').mkdir(mode=0o700)
    (destination / 'WRITER.lock').touch(mode=0o600, exist_ok=False)
    shutil.copyfile(original / 'JOURNAL.json', destination / 'JOURNAL.json')
    pins = {'JOURNAL.json': sha(original / 'JOURNAL.json')}
    for index in range(cutoff + 1):
        for suffix in ('.json', '.intent.json'):
            name = f'{index:020d}' + suffix
            prior, copied = original / 'records' / name, destination / 'records' / name
            shutil.copyfile(regular(prior), copied)
            require(sha(prior) == sha(copied) and prior.stat().st_ino != copied.stat().st_ino,
                    'independent_exact_prefix_copy')
            pins['records/' + name] = sha(copied)
    return pins


def copy_saved_inbox(original, destination, cutoff):
    copied = {}
    for index in range(cutoff + 1):
        record = read(original / 'records' / f'{index:020d}.json')
        if record['kind'] != 'INBOX':
            continue
        document = record['document']
        source = regular(document['source_id'])
        require(source.parent == original / 'inbox' and sha(source) == document['source_sha256'],
                'only_already_registered_saved_inbox_files')
        target = destination / 'inbox' / source.name
        shutil.copyfile(source, target)
        require(sha(target) == document['source_sha256'], 'saved_inbox_exact_copy_not_new_publication')
        copied[source.name] = document['source_sha256']
    return copied


def reconcile_broker(cutoff):
    directory = LIFE / 'broker2'
    result = []
    names = sorted(directory.glob('READ_*.json'))
    require(len(names) == 13, 'exact_13_historical_reads')
    require({path.name.removeprefix('INTENT_') for path in directory.glob('INTENT_*.json')}
            == {path.name.removeprefix('READ_') for path in names}, 'no_unresolved_prior_read_intents')
    for path in names:
        delivered = read(path)
        consumed_path = directory / path.name.replace('READ_', 'CONSUMED_', 1)
        consumed = read(consumed_path)
        index = consumed['record_index']
        require(index <= cutoff and consumed['inbox_id'] == delivered['publication']['id'],
                'historical_publication_consumed_before_cutoff')
        record_path = ROOT / 'stream/records' / f'{index:020d}.json'
        record = read(record_path)
        require(record['kind'] == 'INBOX' and record['sha256'] == consumed['record_sha256']
                and record['document']['message']['id'] == consumed['inbox_id'], 'historical_INBOX_binding')
        require(record['document']['source_sha256'] == delivered['publication']['sha256'],
                'historical_publication_bytes_match_consumed_INBOX')
        result.append(dict(read=reference(path), consumed=reference(consumed_path), inbox_index=index,
                           publication_id=consumed['inbox_id']))
    first = read(directory / 'FIRST_READ_CONSUMED.json')
    require(first['record_index'] <= cutoff, 'initial_connection_already_in_saved_context')
    return dict(historical_reads=result, first_consumed=reference(directory / 'FIRST_READ_CONSUMED.json'),
                replay_past_reads=False, publish_initial_connection=False, future_cursor=cutoff + 1)


def verify_tool_source():
    path = LIFE / 'SIDECAR_SOURCE_PINS_V2.json'
    require(sha(path) == 'da18586f684c1fcacae0a6960083cadd6c927cc6af2a6d5c19583736e5a4169d', 'old_reader_tool_source_manifest')
    expected = read(path)
    source = LIFE / 'toolsource2'
    actual = {str(path.relative_to(source)): sha(path) for path in source.rglob('*.py')}
    require(actual == expected, 'entire_original_reader_tool_closure')
    return reference(path)


def confinement():
    path = Path(__file__).resolve().parent / 'CONFINEMENT_API.py'
    require(sha(path) == CAPSULE_SHA, 'tested_node5_confinement_capsule')
    spec = importlib.util.spec_from_file_location('r154_exact_node5_confinement', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.DEVICES = {7: GPU_UUID}
    return module


def cpu_gate(path):
    gate = read(path)
    require(gate['status'] == 'PASS' and gate['tests'] >= 20
            and gate['source_sha256'] == sha(Path(__file__).absolute())
            and gate['capsule_sha256'] == CAPSULE_SHA, 'receiving_CPU_for_exact_operator_and_capsule')
    return gate


def stage(output, gate_path, authority):
    output = output_scope(output)
    require(not output.exists(), 'never_reuse_attempt')
    cpu_gate(gate_path)
    evidence = inspect()
    cutoff = explicit_cutoff(evidence, authority)
    require(not evidence['target_compute_pids'], 'no_existing_reader_compute_owner')
    broker = reconcile_broker(3179)
    tool_source = verify_tool_source()
    old_guard = read(LIFE / 'control1/GUARD.json')
    old_plan = read(old_guard['plan_path'])
    output.mkdir(mode=0o700)
    write(output / 'ORIGINAL_INSPECTION.json', evidence)
    segment_id = 'repo_reader_saved30_' + uuid.uuid4().hex
    write(output / 'RECOVERY_SEGMENT.json', dict(cutoff, segment_id=segment_id, old_root=str(ROOT),
        new_root=str(output / 'run1'), original_head=evidence['head'], saved=evidence['saved'],
        runtime_logical_root=str(ROOT), private_mount_maps_logical_root_to_new_root=True,
        original_root_inode=ROOT.stat().st_ino, original_root_device=ROOT.stat().st_dev,
        old_journal_id=read(ROOT / 'stream/JOURNAL.json')['journal_id'],
        journal_prefix_identity_retained_external_segment_identity_new=True, created_unix=time.time()))
    source = output / 'source'
    shutil.copytree(LIFE / 'source1', source, ignore=shutil.ignore_patterns('__pycache__'))
    pins = {str(path.relative_to(source)): sha(path) for path in source.rglob('*.py')}
    require(pins == old_guard['source_pins'], 'entire_old_source_byte_identical_no_suffix_patch')
    destination = output / 'run1'
    destination.mkdir(mode=0o700)
    prefix = copy_prefix(ROOT / 'stream', destination / 'stream', 3179)
    saved_inbox = copy_saved_inbox(ROOT / 'stream', destination / 'stream', 3179)
    (destination / 'checkpoints').mkdir(mode=0o700)
    shutil.copytree(ROOT / 'checkpoints/sleep_000030', destination / 'checkpoints/sleep_000030')
    require(sha(destination / 'checkpoints/sleep_000030/COMMIT.json') == CHECKPOINT_SHA, 'copied_COMMIT_exact')
    for path in (ROOT / 'checkpoints/sleep_000030').rglob('*'):
        if path.is_file():
            require(sha(path) == sha(destination / 'checkpoints/sleep_000030' / path.relative_to(ROOT / 'checkpoints/sleep_000030')),
                    'independent_saved_checkpoint_copy')
    (destination / 'readouts').mkdir(mode=0o700)
    readout_markers = []
    revision = old_plan.get('readout_revision', 1)
    for cycle in range(31):
        name = f'sleep_{cycle:06d}' + (f'_r{revision}' if revision > 1 else '')
        marker = ROOT / 'readouts' / (name + '_DISPATCH.json')
        require(marker.is_file(), 'all_historical_readouts_already_dispatched')
        shutil.copyfile(marker, destination / 'readouts' / marker.name)
        readout_markers.append(reference(marker))
    write(output / 'PREFIX_COPY.json', dict(files=prefix, historical_readout_dispatch_markers=readout_markers,
        saved_registered_inbox_files=saved_inbox, unconsumed_original_inbox_not_copied=True,
        original_checkpoint_paths_retained_via_private_mount=True, original_inbox_not_republished=True))
    plan = plan_for_segment(old_plan, ROOT, source, evidence['historical_saved_boundary_wall_authorization'])
    write(output / 'PLAN.json', plan)
    allocation = deepcopy(read(old_guard['allocation_path']))
    allocation.update(plan_sha256=sha(output / 'PLAN.json'), declared_unix=time.time(),
        builder_entry='Rawls R154 explicit saved30 recovery segment; requires separate posted launch gate',
        builder_entry_pushed=True, cpu_tests_passed=True, checkpoint_resume=True)
    write(output / 'ALLOCATION.json', allocation)
    config = dict(old_guard, source_pins=pins, plan_path=str(output / 'PLAN.json'),
        plan_sha256=sha(output / 'PLAN.json'), allocation_path=str(output / 'ALLOCATION.json'),
        allocation_sha256=sha(output / 'ALLOCATION.json'), lease_path=str(LEASE), lease_sha256=LEASE_SHA,
        hard_end_unix=HARD_END, attempt_dir=str(output), resume=True,
        device_containment=dict(uid=os.getuid(), gid=os.getgid(), minor=confinement().device_minor(GPU_UUID),
                                unit='orch-r136-native-' + uuid.uuid4().hex))
    require(config['device_containment']['uid'] == config['device_containment']['gid'] == 2524
            and config['device_containment']['minor'] == 7, 'validated_node5_nonroot_minor7')
    write(output / 'GUARD.json', config)
    for name in ('broker', 'file_receipts'):
        (output / name).mkdir(mode=0o700)
    write(output / 'BROKER_CONFIG.json', dict(root=str(ROOT), host_root=str(destination), snapshot=str(LIFE / 'snapshot1'),
        manifest_sha256=evidence['broker']['snapshot']['sha256'], segment_id=segment_id, hard_end_unix=HARD_END,
        output=str(output / 'broker'), receipts=str(output / 'file_receipts'), start_index=3180,
        previous_sha256=read(ROOT / 'stream/records/00000000000000003179.json')['sha256'],
        journal_id=read(ROOT / 'stream/JOURNAL.json')['journal_id'], reconciliation=broker,
        tool_source=str(LIFE / 'toolsource2'), tool_source_manifest=tool_source))
    write(output / 'STAGED.json', dict(operator=reference(Path(__file__).absolute()), cpu=reference(gate_path),
        config=reference(output / 'GUARD.json'), segment=reference(output / 'RECOVERY_SEGMENT.json'),
        broker=reference(output / 'BROKER_CONFIG.json'), capsule_sha256=CAPSULE_SHA,
        original_head=evidence['head']['file'], stage_unix=time.time(), launch_authorized=False))
    return dict(status='STAGED_SAVED30_SEGMENT_NOT_LAUNCHED', output=str(output), segment_id=segment_id)


def modules(output):
    output = output_scope(output)
    request = read(output / 'STAGED.json')
    require(request['operator']['sha256'] == sha(Path(__file__).absolute()), 'same_staged_operator')
    for key in ('config', 'segment', 'broker', 'cpu'):
        require(sha(request[key]['path']) == request[key]['sha256'], 'unchanged_binding:' + key)
    cpu_gate(request['cpu']['path'])
    config = read(output / 'GUARD.json')
    plan = read(config['plan_path'])
    require(plan['root'] == str(ROOT) and plan['physical'] == 7
            and plan['gpu_uuid'] == GPU_UUID and config['resume'] is True, 'same_saved30_segment')
    sys.path.insert(0, plan['source_root'])
    guard = importlib.import_module('gpu.orch_r125_continual_guard')
    require(Path(guard.__file__).resolve() == Path(plan['source_root']) / 'gpu/orch_r125_continual_guard.py',
            'exact_frozen_guard_import')
    require(guard.validate(output / 'GUARD.json') == (config, plan), 'original_guard_validation')
    return request, config, plan, guard


def branch_cpu(output):
    request, config, plan, guard = modules(output)
    from gpu.orch_r125_stream_journal import StreamJournal
    from organism_v6.orch_r125_continual_stream import ContinualStream
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only_restore_validation')
    class SnapshotJournal(StreamJournal):
        def _inbox_event(self, message, path, source_sha256):
            return StreamJournal._inbox_event(SimpleNamespace(inbox=ROOT / 'stream/inbox'), message, path, source_sha256)
    with SnapshotJournal(output / 'run1/stream', create=False) as journal:
        saved = journal.latest_checkpoint()
        stream = ContinualStream.restore(saved['document'], expected_sha256=saved['expected_sha256'])
        require(saved['expected_sha256'] == SAVED_SHA and stream.pending is None
                and stream.sleep_frontier == len(stream.rows), 'exact_saved30_context_carry_restore')
        checkpoint = read(output / 'run1/checkpoints/sleep_000030/COMMIT.json')
        guard.child.NativeChild.verify_checkpoint(checkpoint)
        require(checkpoint['optimizer_steps'] == 2745
                and stream.model_state_sha256 == digest(checkpoint['checkpoint_sha256']), 'exact_saved2745_model_binding')
        before = stream.checkpoint()
        journal.inbox = ROOT / 'stream/inbox'
        journal.read_inbox()
        require(journal.latest_checkpoint()['expected_sha256'] == SAVED_SHA,
                'saved_inbox_registration_no_duplicate_messages')
        wall = guard.child.prepare_wall_extension(plan, stream, resume=True, plan_sha256=config['plan_sha256'])
        require(stream.checkpoint() == before, 'wall_preparation_does_not_mutate_saved_state')
    proof = dict(status='PASS', saved_state_sha256=SAVED_SHA, optimizer_steps=2745,
        original_source_sha256=sha(Path(plan['source_root']) / 'gpu/orch_r125_continual_native.py'),
        exact_old_native_unchanged=True, wall_extension_validated_without_writing=True,
        new_wall=HARD_END, config_sha256=sha(output / 'GUARD.json'), cpu= request['cpu'], verified_unix=time.time())
    write(output / 'BRANCH_CPU.json', proof)
    return proof


def contained_command(config, plan, payload, lifetime):
    policy = config['device_containment']
    require(plan['physical'] == policy['minor'] == 7 and policy['uid'] == policy['gid'] == 2524,
            'only_actual_reader_device')
    command = confinement().device_containment_command(7, 7, policy['uid'], policy['gid'],
        policy['unit'], plan['source_root'], payload, lifetime)
    position = command.index('/usr/bin/env')
    command[position:position] = ['--property=BindPaths=' + str(Path(config['attempt_dir']) / 'run1') + ':' + str(ROOT),
                                 '--property=ReadOnlyPaths=' + str(LIFE / 'source1')]
    position = command.index('/usr/bin/env')
    command.insert(position + 2, 'PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True')
    return command


def verify_segment_mount(output):
    segment = read(output / 'RECOVERY_SEGMENT.json')
    logical, physical = ROOT.stat(), (output / 'run1').stat()
    require((logical.st_dev, logical.st_ino) == (physical.st_dev, physical.st_ino)
            and (logical.st_dev, logical.st_ino) != (segment['original_root_device'], segment['original_root_inode']),
            'private_namespace_must_map_only_new_segment_not_original')
    return dict(logical_root=str(ROOT), host_segment_root=str(output / 'run1'), inode=logical.st_ino,
                device=logical.st_dev, original_host_root_hidden=True, verified_unix=time.time())


def launch_gate(output):
    proof = read(output / 'BRANCH_CPU.json')
    gate = read(output / 'BUILDER_GATE.json')
    require(gate['authority'] == AUTHORITY and gate['posted'] is True and gate['builder_entry'].strip()
            and gate['branch_cpu_sha256'] == sha(output / 'BRANCH_CPU.json')
            and gate['operator_sha256'] == sha(Path(__file__).absolute())
            and gate['segment_sha256'] == sha(output / 'RECOVERY_SEGMENT.json')
            and proof['status'] == 'PASS' and proof['config_sha256'] == sha(output / 'GUARD.json'),
            'posted_exact_CPU_and_segment_launch_gate')


def dispatch(output):
    modules(output)
    launch_gate(output)
    (output / 'DISPATCH_ONCE').mkdir()
    command = [str(PYTHON), '-B', str(Path(__file__).absolute()), '--action', 'supervise', '--output', str(output)]
    with (output / 'SUPERVISOR.log').open('x') as log:
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
            cwd=str(output / 'source'), env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1'),
            start_new_session=True)
    result = dict(supervisor_pid=process.pid, command=command, started_unix=time.time(), no_retry=True)
    write(output / 'DISPATCHED.json', result)
    return result


def supervise(output):
    request, config, plan, guard = modules(output)
    launch_gate(output)
    try:
        command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
                   'PYTHONPATH=' + plan['source_root'], str(PYTHON), '-B', '-m',
                   'gpu.orch_r125_continual_guard', 'scan', '--config', str(output / 'GUARD.json')]
        report = json.loads(subprocess.check_output(command, text=True, timeout=100))
        write(output / 'ADMISSION.json', report)
        require(report['scanner_euid'] == 0 and report['clear'] and not report['blocking_reasons']
                and report['gpu']['uuid'] == GPU_UUID, 'fresh_unchanged_privileged_admission')
        write(output / 'ADMISSION_TIME.json', dict(verified_unix=time.time()))
        payload = [str(PYTHON), '-B', str(Path(__file__).absolute()), '--action', 'contained', '--output', str(output)]
        command = contained_command(config, plan, payload, int(HARD_END - time.time()))
        write(output / 'CONTAINED_COMMAND.json', dict(command=command, started_unix=time.time()))
        result = subprocess.run(command, check=False)
        write(output / 'SERVICE_EXIT.json', dict(returncode=result.returncode, finished_unix=time.time()))
        require(result.returncode == 0, 'owned_contained_service_failed_no_retry')
    except BaseException as error:
        write(output / 'FAILED.json', dict(error=str(error), error_type=type(error).__name__, no_retry=True,
                                            finished_unix=time.time()))
        raise


def contained(output):
    request, config, plan, guard = modules(output)
    proof = confinement().verify_device_containment(config, plan)
    write(output / 'SEGMENT_MOUNT_VERIFIED.json', verify_segment_mount(output))
    require(os.environ.get('PYTORCH_CUDA_ALLOC_CONF') == 'expandable_segments:True', 'allocator_inside_clean_env')
    write(output / 'CONTAINMENT_VERIFIED.json', proof)
    report = read(output / 'ADMISSION.json')
    admitted = read(output / 'ADMISSION_TIME.json')['verified_unix']
    require(report['clear'] and report['scanner_euid'] == 0 and not report['blocking_reasons']
            and report['gpu']['uuid'] == GPU_UUID and 0 <= time.time() - admitted < 100, 'fresh_exact_admission')
    remaining = int(HARD_END - time.time() - 10)
    require(remaining > 60, 'remaining_old_lease_wall')
    command = ['timeout', '--signal=TERM', '--kill-after=5s', str(remaining) + 's', str(PYTHON), '-B',
               '-m', 'gpu.orch_r125_continual_guard', 'native', '--config', str(output / 'GUARD.json')]
    from gpu.orch_r133_code_feedback_guard import publish_launch
    with (output / 'NATIVE.log').open('x') as log:
        process = subprocess.Popen(command, cwd=plan['source_root'], stdin=subprocess.PIPE,
                                   stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        ticks = Path('/proc', str(process.pid), 'stat').read_text().rsplit(')', 1)[1].split()[19]
        publish_launch(output / 'LAUNCH.json', dict(pid=process.pid, parent_start_ticks=ticks, started_unix=time.time(),
            admission_verified_unix=admitted, admission_sha256=sha(output / 'ADMISSION.json'),
            guard_sha256=sha(output / 'GUARD.json'), command_sha256=digest(command), plan_sha256=config['plan_sha256'],
            gpu_uuid=GPU_UUID, hard_end_unix=HARD_END, no_retry=True,
            containment_sha256=sha(output / 'CONTAINMENT_VERIFIED.json')))
        process.stdin.write(b'LAUNCH_READY\n')
        process.stdin.close()
        status = process.wait()
    write(output / 'EXIT.json', dict(exit_code=status, no_retry=True, finished_unix=time.time()))
    require(status == 0, 'native_failed_preserve_no_retry')


def future_read(previous_request, response, committed, cutoff, response_index):
    require(response_index > cutoff, 'future_segment_response_only')
    request = {key: value for key, value in previous_request.items() if key != 'resume_state'}
    require(request['split'] == 'TRAIN' and response['request_sha256'] == digest(request)
            and committed['source_sha256'] == digest(response)
            and committed['segment'] == request['segment'], 'committed_TRAIN_request_response_binding')
    return response['response']['raw']


def broker_dispatch(output):
    request, config, plan, guard = modules(output)
    launch_gate(output)
    require((output / 'LAUNCH.json').exists() and (output / 'CONTAINMENT_VERIFIED.json').exists(),
            'native_dispatched_before_broker')
    (output / 'BROKER_DISPATCH_ONCE').mkdir()
    unit = 'orch-r154-reader-broker-' + uuid.uuid4().hex
    command = ['sudo', '-n', 'systemd-run', '--quiet', '--wait', '--pipe', '--unit=' + unit,
        '--property=User=2524', '--property=Group=2524', '--property=NoNewPrivileges=yes',
        '--property=CapabilityBoundingSet=', '--property=AmbientCapabilities=', '--property=DevicePolicy=strict',
        '--property=ProtectSystem=strict', '--property=ProtectControlGroups=yes', '--property=PrivateNetwork=yes',
        '--property=RuntimeMaxSec=' + str(int(HARD_END - time.time())),
        '--property=BindPaths=' + str(output / 'run1') + ':' + str(ROOT),
        '--property=ReadOnlyPaths=' + str(ROOT),
        '--property=ReadWritePaths=' + ' '.join(str(path) for path in
            (output / 'broker', output / 'file_receipts', ROOT / 'stream/inbox')),
        '--property=InaccessiblePaths=' + ' '.join(str(path) for path in
            (ROOT / 'readouts', output / 'run1/readouts')) + ' -/localhome/local-rohing/.ssh -/localhome/local-rohing/.aws',
        '/usr/bin/env', '-i', 'PATH=/usr/bin:/bin', 'HOME=' + str(BASE), 'CUDA_VISIBLE_DEVICES=',
        'PYTHONDONTWRITEBYTECODE=1', 'PYTHONPATH=' + str(LIFE / 'toolsource2'),
        str(PYTHON), '-B', str(Path(__file__).absolute()), '--action', 'broker', '--output', str(output)]
    with (output / 'BROKER.log').open('x') as log:
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                                   start_new_session=True)
    result = dict(pid=process.pid, unit=unit, command=command, no_gpu=True, started_unix=time.time())
    write(output / 'BROKER_DISPATCHED.json', result)
    return result


def broker(output):
    config = read(output / 'BROKER_CONFIG.json')
    require(config['root'] == str(ROOT) and config['host_root'] == str(output_scope(output) / 'run1')
            and config['hard_end_unix'] == HARD_END
            and config['start_index'] == 3180 and config['snapshot'] == str(LIFE / 'snapshot1')
            and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'future_cursor_same_snapshot_CPU_broker')
    from gpu.orch_r136_repo_reader import deliver, requests, verify
    from gpu.orch_r125_stream_console import _open_stream_directory, _read_record
    verify(config['snapshot'], config['manifest_sha256'])
    require(verify_tool_source() == config['tool_source_manifest'], 'unchanged_broker_library_closure')
    directory = output / 'broker'
    (directory / 'BROKER_ONCE').mkdir()
    write(directory / 'SEGMENT_MOUNT_VERIFIED.json', verify_segment_mount(output))
    denied = []
    for minor in range(8):
        try:
            descriptor = os.open('/dev/nvidia' + str(minor), os.O_RDWR | os.O_CLOEXEC)
        except PermissionError:
            denied.append(minor)
        else:
            os.close(descriptor)
            raise ValueError('broker_GPU_device_not_denied')
    try:
        descriptor = os.open(ROOT / 'stream/records/00000000000000003179.json', os.O_WRONLY | os.O_CLOEXEC)
    except (PermissionError, OSError) as error:
        require(error.errno in (13, 30), 'broker_expected_read_only_history')
    else:
        os.close(descriptor)
        raise ValueError('broker_history_not_read_only')
    write(directory / 'SANDBOX_VERIFIED.json', dict(denied_gpu_minors=denied, history_write_denied=True,
        only_reviewed_snapshot=True, no_credentials_or_held_reads=True, verified_unix=time.time()))
    index, previous = config['start_index'], config['previous_sha256']
    request = response = response_index = None
    pending = {}
    write(directory / 'STARTED.json', dict(pid=os.getpid(), start_index=index, previous_sha256=previous,
        historical_reads_reconciled=13, publish_initial_connection=False, historical_READs_replayed=False,
        snapshot_manifest_sha256=config['manifest_sha256'], segment_id=config['segment_id'], started_unix=time.time()))
    while time.time() < HARD_END:
        with _open_stream_directory(config['root'], 'records') as (descriptor, unused):
            record = _read_record(descriptor, index)
        if record is None:
            time.sleep(1)
            continue
        require(record['previous_sha256'] == previous and record['journal_id'] == config['journal_id'],
                'future_broker_chain')
        if record['kind'] == 'REQUEST':
            request = record['document']
        elif record['kind'] == 'RESPONSE':
            response, response_index = record['document'], index
        elif record['kind'] == 'COMMITTED' and response is not None:
            text = future_read(request, response, record['document'], 3179, response_index)
            try:
                names = requests(text)
            except ValueError:
                write(directory / f'REJECTED_{response_index:020d}.json', dict(response_index=response_index,
                    reason='invalid_read_request', record_sha256=record['sha256']))
                names = []
            for name in names:
                provenance = dict(actor='child', split='TRAIN', record_index=response_index,
                                  source_sha256=digest(response), segment_id=config['segment_id'])
                write(directory / f'INTENT_{response_index:020d}.json', dict(request=provenance, file=name))
                receipt = deliver(config['root'], config['snapshot'], config['manifest_sha256'], name,
                                  config['receipts'], provenance)
                write(directory / f'READ_{response_index:020d}.json', receipt)
                pending[receipt['publication']['id']] = response_index
            request = response = response_index = None
        elif record['kind'] == 'INBOX':
            identifier = record['document']['message']['id']
            if identifier in pending:
                target = pending.pop(identifier)
                write(directory / f'CONSUMED_{target:020d}.json', dict(inbox_id=identifier,
                    record_index=index, record_sha256=record['sha256']))
        write(directory / f'CURSOR_{index:020d}.json', dict(index=index, record_sha256=record['sha256'],
                                                        next_index=index + 1, observed_unix=time.time()))
        previous, index = record['sha256'], index + 1
    write(directory / 'EXIT.json', dict(reason='existing_lease_wall', finished_unix=time.time()))
    return dict(status='BROKER_EXITED')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--action', choices=('inspect', 'stage', 'branch-cpu', 'dispatch', 'supervise',
                                           'contained', 'broker-dispatch', 'broker'), required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--cpu', type=Path)
    parser.add_argument('--authority')
    args = parser.parse_args()
    if args.action == 'inspect':
        result = inspect()
    elif args.action == 'stage':
        result = stage(args.output, args.cpu, args.authority)
    else:
        result = globals()[args.action.replace('-', '_')](output_scope(args.output))
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
