"""Read-only bounded restore references for the eight live node5 learners."""

import datetime
import hashlib
import json
import os
from pathlib import Path
import socket
import time


BASE = Path('/localhome/local-rohing')
MAPPING = {
    0: ('C1', BASE / 'orch_r153_community_C1_20260916_attempt1/life'),
    1: ('C2', BASE / 'orch_r153_community_C2_20260916_attempt1/life'),
    2: ('run1', BASE / 'orch_r125_continual_20260916_attempt1/run1'),
    3: ('C3', BASE / 'orch_r153_community_C3_20260916_attempt1/life'),
    4: ('C4', BASE / 'orch_r153_community_C4_20260916_attempt1/life'),
    5: ('C5', BASE / 'orch_r153_community_C5_20260916_attempt1/life'),
    6: ('pilot', BASE / 'orch_r127_pilot_20260916_attempt1/run1'),
    7: ('repo_reader', BASE / 'orch_r136_repo_reader_20260916_attempt1/recovery_r154_saved30_20260916_attempt2/run1'),
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def reference(path):
    return dict(path=str(path), file_sha256=sha(path), bytes=Path(path).stat().st_size)


def metadata(path):
    with path.open('rb') as handle:
        handle.seek(max(0, path.stat().st_size - 4096))
        raw = handle.read()
    return json.loads(b'{' + raw[raw.rfind(b',"index":') + 1:])


def identity(process):
    fields = (process / 'stat').read_text().rsplit(') ', 1)[1].split()
    return dict(pid=int(process.name), start_ticks=fields[19], ppid=int(fields[1]), state=fields[0],
        uid=process.stat().st_uid, cwd=os.readlink(process / 'cwd'), argv_sha256=sha(process / 'cmdline'))


def record_reference(path):
    record = read(path)
    require(record['sha256'] == digest({key: value for key, value in record.items() if key != 'sha256'}),
        'canonical_record_sha256:' + str(path))
    return dict(**reference(path), index=record['index'], kind=record['kind'],
        record_sha256=record['sha256'], previous_sha256=record['previous_sha256']), record


def capture(process, guard_path, guard, plan):
    started = time.time()
    actor = identity(process)
    physical = plan['physical']
    label, storage = MAPPING[physical]
    logical = Path(plan['root'])
    view = process / 'root' / logical.relative_to('/')
    require(os.path.samefile(view, storage), 'live_process_view_matches_physical_storage:' + label)
    mount_lines = []
    for line in (process / 'mountinfo').read_text().splitlines():
        fields = line.split()
        target = fields[4].replace('\\040', ' ')
        if target != '/' and (str(logical) == target or str(logical).startswith(target.rstrip('/') + '/')):
            mount_lines.append(dict(mount_root=fields[3], target=target, device=fields[2]))
    paths = sorted((storage / 'stream/records').glob('[0-9]' * 20 + '.json'))
    require(paths, 'existing_live_stream')
    head, unused_record = record_reference(paths[-1])
    cut = head['index']
    require(len(paths) == cut + 1, 'bounded_contiguous_record_names')
    catalog = [metadata(path) for path in paths]
    complete_meta = next(item for item in reversed(catalog) if item['kind'] == 'SLEEP_COMPLETE')
    complete_ref, complete = record_reference(paths[complete_meta['index']])
    document = complete['document']
    state = document['resume_state']
    require(state['sha256'] == digest(state['state']) and state['state']['pending'] is None,
        'latest_complete_state_digest')
    checkpoint = document['checkpoint']
    logical_checkpoint = Path(checkpoint['optimizer_rng_path']).parent
    checkpoint_root = storage / logical_checkpoint.relative_to(logical)
    commit_path = checkpoint_root / 'COMMIT.json'
    commit = read(commit_path)
    require(commit == checkpoint, 'complete_record_matches_COMMIT')
    checkpoint_files = {str(path.relative_to(checkpoint_root)): reference(path)
        for path in sorted(checkpoint_root.rglob('*')) if path.is_file()}
    require(checkpoint_files['optimizer_rng.pt']['file_sha256'] == checkpoint['checkpoint_sha256']['optimizer']
        == checkpoint['checkpoint_sha256']['rng'], 'saved_optimizer_RNG_exact_file')
    for relative, expected in checkpoint['adapter_files'].items():
        require(checkpoint_files['adapter/' + relative]['file_sha256'] == expected, 'adapter_file:' + relative)
    state_cut = None
    for item in reversed(catalog):
        if item['kind'] not in ('COMMITTED', 'CONTEXT_COMMITTED', 'CONTEXT_INPUT', 'SLEEP_COMPLETE', 'COMPACTION', 'REQUEST'):
            continue
        candidate_ref, candidate = record_reference(paths[item['index']])
        candidate_document = candidate['document']
        envelope = candidate_document.get('resume_state') or candidate_document.get('state')
        if not isinstance(envelope, dict) or 'state' not in envelope or 'sha256' not in envelope:
            continue
        require(envelope['sha256'] == digest(envelope['state']), 'bounded_current_context_digest')
        state_cut = dict(record=candidate_ref, state_sha256=envelope['sha256'],
            history_events=len(envelope['state']['history']['events']),
            working_state=envelope['state']['history'].get('working_state'),
            pending=envelope['state'].get('pending') is not None,
            model_state_sha256=envelope['state'].get('model_state_sha256'),
            same_model_as_latest_COMPLETE=envelope['state'].get('model_state_sha256') == state['state']['model_state_sha256'],
            separately_preserved_context_not_automatic_resume_permission=True)
        break
    registered = {}
    for item in catalog:
        if item['kind'] == 'INBOX':
            inbox_document = read(paths[item['index']])['document']
            filename = Path(inbox_document['source_id']).name
            registered[filename] = dict(record_index=item['index'], source_sha256=inbox_document['source_sha256'])
    inbox = {}
    for path in sorted((storage / 'stream/inbox').glob('*.json')):
        data = read(path)
        item = reference(path)
        item.update(id=data['id'], actor=data['actor'], speaker=data.get('speaker'), registration=registered.get(path.name))
        if item['registration']:
            require(item['file_sha256'] == item['registration']['source_sha256'], 'registered_source_exact')
        inbox[path.name] = item
    source = Path(plan['source_root'])
    pins = guard.get('source_pins', {})
    mismatches = []
    for relative, expected in pins.items():
        require(not Path(relative).is_absolute() and '..' not in Path(relative).parts, 'relative_source_pin')
        if sha(source / relative) != expected:
            mismatches.append(relative)
    controls = dict(guard=reference(guard_path), plan=reference(Path(guard['plan_path'])))
    for name in ('lease', 'allocation'):
        if guard.get(name + '_path'):
            controls[name] = reference(Path(guard[name + '_path']))
    owner = identity(process)
    require(owner['pid'] == actor['pid'] and owner['start_ticks'] == actor['start_ticks'], 'same_native_after_manifest')
    require(sha(paths[-1]) == head['file_sha256'], 'frozen_prefix_head_unchanged_while_native_continues')
    return dict(label=label, physical=physical, gpu_uuid=plan['gpu_uuid'], native=actor,
        observed_start_unix=started, observed_end_unix=time.time(),
        logical_root=str(logical), host_storage_root=str(storage), process_view_root=str(view),
        logical_path_is_symlink=logical.is_symlink(), host_logical_path_is_live_storage=os.path.samefile(logical, storage),
        active_namespace_bindings=mount_lines, head=head,
        bounded_journal=dict(manifest=reference(storage / 'stream/JOURNAL.json'), records_root=str(storage / 'stream/records'),
            first_index=0, last_index_inclusive=cut, record_count=cut + 1,
            members='For each integer index from0 throughlast inclusive: %020d.json and %020d.intent.json',
            exclude_later_records_and_intents=True, source_WRITER_lock_not_portable=True),
        latest_complete=dict(record=complete_ref, cycle=document['cycle'], state_sha256=state['sha256'],
            checkpoint_root=str(checkpoint_root), logical_checkpoint_root=str(logical_checkpoint),
            COMMIT=reference(commit_path), optimizer_steps=checkpoint['optimizer_steps'],
            adapter_state_sha256=checkpoint['adapter_state_sha256'], files=checkpoint_files),
        latest_context=state_cut, inbox=inbox, registered_inbox_count=len(registered),
        restore_source=dict(source_root=str(source), source_pins=pins, source_pin_mismatches=mismatches,
            controls=controls, model_dir=plan['model_dir'], base_sha256=plan.get('base_sha256'),
            anchors=plan['anchors'], original_runtime_hard_end_unix=plan['hard_end_unix'],
            original_runtime_lease_end_unix=plan.get('lease_end_unix'),
            restore_requires_destination_device_namespace_gate_and_actual_lease_rebinding=True),
        live_memory_RNG_not_claimed_captured=True, no_source_writes=True, no_signals=True)


started = time.time()
require(socket.gethostname() == '[REDACTED_HOST]', 'actual_node5_host')
rows = []
for process in Path('/proc').glob('[0-9]*'):
    try:
        arguments = (process / 'cmdline').read_bytes().rstrip(b'\0').decode().split('\0')
    except (OSError, UnicodeDecodeError):
        continue
    if arguments[:4] != ['/localhome/local-rohing/v2/venv/bin/python', '-B', '-m', 'gpu.orch_r125_continual_guard']:
        continue
    if 'native' not in arguments:
        continue
    guard_path = Path(arguments[arguments.index('--config') + 1])
    guard = read(guard_path)
    plan = read(guard['plan_path'])
    rows.append(capture(process, guard_path, guard, plan))
require(len(rows) == 8 and {row['physical'] for row in rows} == set(range(8)), 'eight_current_live_slots')
result = dict(schema='NODE5_READ_ONLY_INSURANCE_MANIFEST_V1', host=socket.gethostname(),
    observed_start_unix=started, observed_end_unix=time.time(),
    user_confirmed_lease_end_utc='2026-09-22T04:04:00+00:00',
    provider_CLI_extension_receipt_independently_read=False,
    emergency_0400_stop_cancelled=True, offnode_copy_owner='Main',
    manifest_only_no_adapter_or_journal_transfer=True, live_actors_not_stopped=True,
    rows=sorted(rows, key=lambda item: item['physical']))
result['manifest_sha256'] = digest(result)
print(json.dumps(result, indent=2))
