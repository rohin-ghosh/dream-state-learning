"""Receipt-bound parent I/O overlay; no native signals, launch, or checkpoint load."""

import hashlib
import json
import os
from pathlib import Path
import sys
import time
import types


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def sha(path):
    path = Path(path)
    require(path.is_absolute() and path.resolve() == path and path.is_file(), 'literal_pinned_file')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pins_match(pins):
    require(bool(pins), 'nonempty_pins')
    require(all(sha(path) == expected for path, expected in pins.items()), 'remote_pinned_bytes_changed')


def native_identity(expected):
    process = Path('/proc') / str(expected['pid'])
    fields = (process / 'stat').read_text().rsplit(')', 1)[1].split()
    observed = dict(pid=expected['pid'], start_ticks=fields[19], uid=process.stat().st_uid,
        boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
        argv=(process / 'cmdline').read_bytes().decode().rstrip('\0').split('\0'),
        cwd=str((process / 'cwd').resolve()), root=expected['root'], journal_id=expected['journal_id'])
    require(fields[0] not in ('Z', 'X', 'T', 't'), 'receiving_native_not_running')
    require(observed == expected, 'exact_native_pid_start_boot_uid_argv_cwd_required')
    require('gpu.r232_recovery' in observed['argv'] and 'native' in observed['argv'], 'native_not_dispatch_supervisor')
    require(read(Path(expected['root']) / 'raw/stream/JOURNAL.json')['journal_id'] == expected['journal_id'],
        'same_journal_required')
    return observed


def canonical(root, reference, kind=None):
    index = reference['index']
    require(type(index) is int and index >= 0, 'exact_record_index')
    directory = Path(root) / 'raw/stream/records'
    record = read(directory / f'{index:020d}.json')
    require(record['index'] == index and record['sha256'] == reference['sha256']
        and record['sha256'] == digest({key: value for key, value in record.items() if key != 'sha256'}),
        'canonical_record_hash')
    intent = read(directory / f'{index:020d}.intent.json')
    require(intent == dict(schema=record['schema'], journal_id=record['journal_id'], index=index,
        previous_sha256=record['previous_sha256'], record_sha256=record['sha256']), 'canonical_record_intent')
    require(kind is None or record['kind'] == kind, 'canonical_record_kind')
    return record


def reconcile(root, expected, cursor, deliveries):
    anchor = canonical(root, dict(index=cursor['next_index'] - 1, sha256=cursor['previous_sha256']))
    require(anchor['journal_id'] == expected['journal_id'], 'same_parent_cursor_journal')
    control = Path(root) / 'control'
    markers = list(control.glob('PARENT_*.dispatch'))
    require(len(markers) <= 10000, 'bounded_remote_dispatch_inventory')
    for marker in markers:
        require(marker.with_suffix('.json').is_file(), 'ambiguous_remote_dispatch_requires_operator')
    for delivery in deliveries:
        path = control / ('PARENT_' + delivery['delivery_id'] + '.json')
        receipt = read(path)
        require(receipt['journal_id'] == expected['journal_id']
            and receipt['publication'] == delivery['receipt']['publication']
            and receipt['text_sha256'] == delivery['text_sha256']
            and receipt['provider_response_sha256'] == delivery['provider_response_sha256'],
            'published_delivery_receipt_mismatch')
    return dict(cursor_verified=True, acknowledged_deliveries=len(deliveries), ambiguous_dispatches=0)


def verify_loaded(plan, approval, dependency_sha256):
    expected = approval['new_native']
    root = expected['root']
    require(root == plan['old_native']['root'] and expected['journal_id'] == plan['old_native']['journal_id'],
        'unchanged_root_and_journal')
    require(expected['boot_id'] == plan['old_native']['boot_id'] and expected['uid'] == plan['life_binding']['uid'],
        'same_host_boot_and_uid')
    require((expected['pid'], expected['start_ticks']) !=
        (plan['old_native']['pid'], plan['old_native']['start_ticks']), 'new_incarnation_required')
    old = Path('/proc') / str(plan['old_native']['pid'])
    if old.exists():
        old_fields = (old / 'stat').read_text().rsplit(')', 1)[1].split()
        require(old_fields[19] != plan['old_native']['start_ticks'], 'old_native_must_have_exited')
    native_identity(expected)
    pins_match(approval['receiver_pins'])
    token = read(approval['handoff_path'])
    require(approval['handoff_path'] in approval['receiver_pins'], 'pinned_handoff_required')
    require(token['sha256'] == digest({key: value for key, value in token.items() if key != 'sha256'})
        and token['old_native_exited'] is True and token['life_binding_sha256'] == digest(plan['life_binding'])
        and token['epoch_id'] == plan['source_epoch'] and token['deadline_unix'] == plan['until_unix'],
        'exact_exited_same_life_epoch_deadline_token')
    receiver = token['receiver']
    require(receiver['source_epoch'] == token['epoch_id'] and receiver['same_journal_root'] == root + '/raw/stream'
        and receiver['plan_sha256'] == digest(receiver['plan']), 'same_receiving_plan')
    parent_handoff = read(receiver['parent_handoff_path'])
    require(sha(receiver['parent_handoff_path']) == receiver['artifact_pins'][receiver['parent_handoff_path']]
        and parent_handoff['dependency_proof']['sha256'] == dependency_sha256, 'exact_receiver_parent_dependency')
    guard = read(receiver['guard_path'])
    require(receiver['guard_path'] == approval['guard_path'] and receiver['guard_path'] in approval['receiver_pins']
        and sha(guard['plan_path']) == guard['plan_sha256'] and read(guard['plan_path']) == receiver['plan']
        and guard['source_pins'] == token['new_source_pins'] and guard['hard_end_unix'] == plan['until_unix'],
        'exact_receiving_guard_source_and_plan')
    require('--config' in expected['argv'] and
        expected['argv'][expected['argv'].index('--config') + 1] == receiver['guard_path']
        and expected['cwd'] == receiver['plan']['source_root'], 'native_receiving_guard_and_source')
    source_root = Path(receiver['plan']['source_root'])
    source_files = {str(path): expected_hash for name, expected_hash in token['new_source_pins'].items()
        for path in [source_root / name] if not Path(name).is_absolute() and '..' not in Path(name).parts}
    require(len(source_files) == len(token['new_source_pins']), 'literal_source_closure_paths')
    pins_match(source_files)
    previous_guard = read(plan['life_binding']['guard_path'])
    require(sha(plan['life_binding']['guard_path']) == plan['life_binding']['guard_sha256'], 'old_guard_unchanged')
    movable = {'attempt_dir', 'plan_path', 'plan_sha256', 'lease_path', 'lease_sha256',
        'allocation_path', 'allocation_sha256', 'source_pins'}
    require({key: value for key, value in guard.items() if key not in movable} ==
        {key: value for key, value in previous_guard.items() if key not in movable}, 'same_allocation_and_confinement')
    boundary = token['exact_complete']
    complete = canonical(root, dict(index=boundary['complete_index'], sha256=boundary['complete_sha256']), 'SLEEP_COMPLETE')
    learned = canonical(root, dict(index=boundary['learn_index'], sha256=boundary['learn_sha256']), 'R184_LEARN_COMPLETE')
    adoption = canonical(root, approval['source_adoption'], 'RETENTION_SOURCE_ADOPTED')
    loaded = canonical(root, approval['loaded'], 'LOADED')
    require(complete['document']['status'] == 'COMPLETE' and complete['document']['checkpoint'] == boundary['checkpoint']
        and complete['document']['resume_state'] == boundary['resume_state']
        and learned['document']['checkpoint'] == boundary['checkpoint']
        and learned['document']['cycle'] == complete['document']['cycle'], 'same_exact_COMPLETE_checkpoint')
    saved = boundary['resume_state']
    require(saved['sha256'] == digest(saved['state']) and saved['state']['pending'] is None
        and saved['state']['sleep_frontier'] == len(saved['state']['rows'])
        and saved['state']['deadline_unix'] == plan['until_unix'], 'exact_saved_resolved_state')
    expected_adoption = dict(schema='RETENTION_SOURCE_ADOPTION_V1', epoch_id=token['epoch_id'],
        handoff_sha256=token['sha256'], source_pins_sha256=digest(token['new_source_pins']),
        complete_index=boundary['complete_index'], complete_sha256=boundary['complete_sha256'],
        state_sha256=boundary['resume_state']['sha256'], deadline_unix=plan['until_unix'],
        wall_extended=False, historical_rows_changed=False)
    require(adoption['document'] == expected_adoption, 'exact_source_adoption_evidence')
    require(complete['index'] < learned['index'] < adoption['index'] < loaded['index']
        and loaded['index'] - complete['index'] <= 512, 'bounded_COMPLETE_to_LOADED_chain')
    previous = complete
    singleton = {'R184_LEARN_COMPLETE': learned['index'], 'RETENTION_SOURCE_ADOPTED': adoption['index'], 'LOADED': loaded['index']}
    for index in range(complete['index'] + 1, loaded['index'] + 1):
        document = read(Path(root) / 'raw/stream/records' / f'{index:020d}.json')
        current = canonical(root, dict(index=index, sha256=document['sha256']))
        require(current['journal_id'] == expected['journal_id'] and current['previous_sha256'] == previous['sha256'],
            'contiguous_receiver_chain')
        allowed = {'INBOX', 'R184_LEARN_COMPLETE', 'RETENTION_SOURCE_ADOPTED', 'LOADED'}
        require(current['kind'] in allowed, 'no_intervening_work_before_LOADED')
        require(current['kind'] == 'INBOX' or singleton[current['kind']] == index, 'no_duplicate_receiver_events')
        previous = current
    require(loaded['document']['resume'] is True and loaded['document']['pid'] == expected['pid']
        and loaded['document']['adapter_sha256'] == boundary['checkpoint']['adapter_state_sha256']
        and loaded['document']['optimizer_steps'] == boundary['checkpoint']['optimizer_steps']
        and loaded['document']['base_sha256'] == boundary['checkpoint']['base_sha256'],
        'actual_LOADED_saved_adapter_optimizer_identity')
    native_identity(expected)
    return dict(loaded=approval['loaded'], source_adoption=approval['source_adoption'],
        handoff_sha256=token['sha256'], checkpoint_sha256=digest(boundary['checkpoint']), verified=True)


def execute(envelope):
    plan, request = envelope['plan'], envelope['request']
    require(time.time() < plan['until_unix'], 'original_deadline_expired')
    pins_match(plan['remote_transport_pins'])
    expected = envelope.get('approval', {}).get('new_native', plan['old_native'])
    root = expected['root']
    native_identity(expected)
    if request['action'] in ('fence_check', 'rebind_check'):
        result = reconcile(root, expected, envelope['cursor'], envelope['deliveries'])
        if request['action'] == 'rebind_check':
            result['receiving'] = verify_loaded(plan, envelope['approval'], envelope['dependency_sha256'])
    else:
        require('approval' in envelope and request['action'] in ('bind', 'poll', 'publish'), 'receipt_bound_IO_only')
        guard_path = envelope['approval']['guard_path']
        require(guard_path in envelope['approval']['receiver_pins'], 'guard_pin_required')
        pins_match({guard_path: envelope['approval']['receiver_pins'][guard_path]})
        require(expected['argv'][expected['argv'].index('--config') + 1] == guard_path, 'same_guard_each_IO')
        require(hashlib.sha256(envelope['transport_source'].encode()).hexdigest() ==
            plan['source_pins'][plan['transport_source_path']], 'same_original_parent_transport_source')
        legacy = types.ModuleType('receipt_bound_original_remote_io')
        exec(compile(envelope['transport_source'], plan['transport_source_path'], 'exec'), legacy.__dict__)
        legacy.identity = lambda arm: (Path(root), native_identity(expected))
        if request['action'] == 'publish':
            require(len(request['delivery_id']) == 64 and all(character in '0123456789abcdef' for character in request['delivery_id']),
                'RESULT_delivery_id_required')
            receipt = Path(root) / 'control' / ('PARENT_' + request['delivery_id'] + '.json')
            require(not receipt.with_suffix('.dispatch').exists() or receipt.exists(), 'ambiguous_dispatch_not_retried')
            if receipt.exists():
                existing = read(receipt)
                require(existing['journal_id'] == expected['journal_id']
                    and existing['provider_response_sha256'] == request['provider_response_sha256']
                    and existing['text_sha256'] == hashlib.sha256(request['text'].encode()).hexdigest(),
                    'existing_remote_ack_exact_request_required')
        result = legacy.execute(dict(request, arm=plan['arm'], native=expected))
    native_identity(expected)
    return dict(result, native=expected)


if __name__ == '__main__':
    try:
        print(json.dumps(execute(json.load(sys.stdin))))
    except Exception as error:
        print(json.dumps(dict(fatal=type(error).__name__, reason=str(error))))
        sys.exit(2)
