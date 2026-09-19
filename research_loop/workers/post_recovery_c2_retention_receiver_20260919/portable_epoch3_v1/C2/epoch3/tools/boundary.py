"""Fail-closed, read-only exact-COMPLETE selection for source-only adoption."""

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import stat


class Refusal(ValueError):
    pass


class ObservationRace(Refusal):
    pass


SCHEMA = 'R125_STREAM_JOURNAL_V1'


def require(condition, reason):
    if not condition:
        raise Refusal(reason)


def digest(document):
    return hashlib.sha256(json.dumps(document, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def file_bytes(path, limit=256 * 1024**2, *, durable=False):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    with os.fdopen(descriptor, 'rb') as handle:
        before = os.fstat(handle.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_size <= limit, 'bounded_regular_file')
        content = handle.read(limit + 1)
        require(len(content) <= limit, 'bounded_regular_file')
        if durable:
            os.fsync(handle.fileno())
        after = os.fstat(handle.fileno())
        current = os.stat(path, follow_symlinks=False)
    identity = lambda entry: (entry.st_dev, entry.st_ino, entry.st_size, entry.st_mtime_ns, entry.st_ctime_ns)
    if identity(before) != identity(after) or identity(after) != identity(current):
        raise ObservationRace('file_changed_during_read')
    return content


def sha(path):
    return hashlib.sha256(file_bytes(path)).hexdigest()


def read(path, *, durable=False):
    return json.loads(file_bytes(path, durable=durable))


def journal_identity(binding):
    root = Path(binding['journal_root'])
    require(root.is_absolute() and root.resolve() == root, 'literal_journal_root')
    manifest = read(root / 'JOURNAL.json')
    require(manifest == dict(schema=SCHEMA, journal_id=binding['journal_id']), 'bound_journal_manifest')
    result = dict(manifest_sha256=digest(manifest))
    for name in ('.', 'records', 'inbox', 'WRITER.lock'):
        entry = (root / name).stat(follow_symlinks=False)
        require((stat.S_ISREG if name == 'WRITER.lock' else stat.S_ISDIR)(entry.st_mode),
            'literal_journal_directories_and_writer_lock')
        result[name] = [entry.st_dev, entry.st_ino]
    return result


def validate_message(message):
    require(isinstance(message, dict) and message.get('split') == 'TRAIN'
        and message.get('actor') in ('parent', 'environment'), 'TRAIN_INBOX_only')
    require(isinstance(message.get('id'), str) and message['id'].strip()
        and isinstance(message.get('text'), str), 'INBOX_id_and_text')


def validate_records(records, binding, *, intents=None):
    if not records:
        return None
    require(intents is not None, 'durable_intents_required')
    for position, record in enumerate(records):
        require(isinstance(record, dict) and set(record) == {'schema', 'journal_id', 'index', 'kind',
            'previous_sha256', 'document', 'sha256'} and record['schema'] == SCHEMA
            and type(record['index']) is int and record['index'] >= 0, 'native_record_schema_and_index')
        require(record['journal_id'] == binding['journal_id'], 'exact_journal_identity')
        require(record['sha256'] == digest({key: value for key, value in record.items() if key != 'sha256'}), 'record_hash')
        if position:
            previous = records[position - 1]
            require(record['index'] == previous['index'] + 1 and record['previous_sha256'] == previous['sha256'],
                'contiguous_complete_tail_chain')
        if record['index'] == 0:
            require(record['previous_sha256'] == digest(dict(schema=SCHEMA, journal_id=binding['journal_id'])),
                'journal_genesis_binding')
        expected = dict(schema=record['schema'], journal_id=record['journal_id'], index=record['index'],
            previous_sha256=record['previous_sha256'], record_sha256=record['sha256'])
        require(intents.get(record['index']) == expected, 'durable_record_intent_pair')
    positions = [position for position, record in enumerate(records) if record['kind'] == 'SLEEP_COMPLETE']
    if not positions:
        return None
    position = positions[-1]
    complete = records[position]
    tail = records[position + 1:]
    if any(record['kind'] not in ('INBOX', 'R184_LEARN_COMPLETE') for record in tail):
        return None
    learned = [record for record in tail if record['kind'] == 'R184_LEARN_COMPLETE']
    if not learned:
        return None
    require(len(learned) == 1, 'one_matching_driver_LEARN_COMPLETE')
    document = complete['document']
    saved = document['resume_state']
    state = saved['state']
    require(saved['sha256'] == digest(state), 'saved_state_hash')
    require(document['status'] == 'COMPLETE' and state['pending'] is None
        and state['sleep_frontier'] == len(state['rows']) and state['sleep_receipts'], 'resolved_COMPLETE_no_pending_rows')
    checkpoint = document['checkpoint']
    last_sleep = state['sleep_receipts'][-1]
    require(last_sleep['status'] == 'COMPLETE' and last_sleep['cycle'] == document['cycle']
        and last_sleep['checkpoint'] == checkpoint and last_sleep['checkpoint_sha256'] == checkpoint['checkpoint_sha256'],
        'saved_sleep_checkpoint_exact')
    require(state['model_state_sha256'] == digest(checkpoint['checkpoint_sha256']), 'same_adapter_optimizer_RNG_binding')
    require(state['deadline_unix'] == binding['hard_end_unix'], 'same_deadline_no_wall_extension')
    learned_document = learned[0]['document']
    require(learned_document['cycle'] == document['cycle'] and learned_document['checkpoint'] == checkpoint,
        'driver_completion_same_cycle_checkpoint')
    inbox = [record for record in tail if record['kind'] == 'INBOX']
    identifiers = set()
    for record in inbox:
        receipt = record['document']
        require(set(receipt) == {'message', 'source_id', 'source_sha256'}, 'native_INBOX_receipt_fields')
        message = receipt['message']
        validate_message(message)
        require(message['id'] not in identifiers, 'unique_INBOX_registration')
        identifiers.add(message['id'])
    return dict(schema='RETENTION_EXACT_COMPLETE_V1', journal_id=binding['journal_id'],
        complete_index=complete['index'], complete_sha256=complete['sha256'], cycle=document['cycle'],
        learn_index=learned[0]['index'], learn_sha256=learned[0]['sha256'],
        head_index=records[-1]['index'], head_sha256=records[-1]['sha256'],
        checkpoint=deepcopy(checkpoint), resume_state=deepcopy(saved),
        preserved_INBOX_records=deepcopy(inbox), records=deepcopy(records[position:]),
        record_intents=deepcopy([intents[record['index']] for record in records[position:]]),
        authority='COMPLETE_PLUS_DRIVER_RECEIPT_NOT_REQUEST_OR_LATEST_UNRESOLVED_STATE')


def read_boundary(binding, *, max_records=128, durable=False):
    require(type(max_records) is int and max_records >= 2, 'bounded_tail_requires_two_records')
    root = Path(binding['journal_root'])
    identity = journal_identity(binding)
    directory = root / 'records'
    names = set(os.listdir(directory))
    if not all(re.fullmatch(r'\d{20}(?:\.intent)?\.json', name) for name in names):
        raise ObservationRace('no_partial_journal_publication')
    indices = sorted({int(name[:20]) for name in names})
    require(indices == list(range(len(indices))), 'no_missing_journal_indices')
    if not all(f'{index:020d}.json' in names and f'{index:020d}.intent.json' in names for index in indices):
        raise ObservationRace('no_unpaired_journal_intent')
    selected = indices[-max_records:]
    records = [read(directory / f'{index:020d}.json', durable=durable) for index in selected]
    require(all(record['index'] == index for index, record in zip(selected, records)), 'record_filename_index')
    intents = {index: read(directory / f'{index:020d}.intent.json', durable=durable) for index in selected}
    if set(os.listdir(directory)) != names:
        raise ObservationRace('journal_raced_while_observing')
    result = validate_records(records, binding, intents=intents)
    if result is None:
        return None
    inbox = {}
    for path in sorted((root / 'inbox').glob('*.json')):
        content = file_bytes(path, limit=1024 * 1024, durable=durable)
        message = json.loads(content)
        validate_message(message)
        duplicates = [item for item in inbox.values() if item['id'] == message['id']]
        require(all(item['sha256'] == hashlib.sha256(content).hexdigest() for item in duplicates),
            'no_conflicting_mailbox_id_bytes')
        inbox[str(path)] = dict(sha256=hashlib.sha256(content).hexdigest(), id=message['id'])
    for record in result['preserved_INBOX_records']:
        receipt = record['document']
        require(receipt['source_id'] in inbox and inbox[receipt['source_id']]['sha256'] == receipt['source_sha256']
            and read(receipt['source_id']) == receipt['message'],
            'registered_INBOX_source_file_preserved')
    if durable:
        read(root / 'JOURNAL.json', durable=True)
        for path in (directory, root / 'inbox', root):
            descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
    require(journal_identity(binding) == identity, 'journal_directories_replaced')
    if set(os.listdir(directory)) != names:
        raise ObservationRace('journal_raced_while_observing_mailbox')
    result['journal_identity'] = identity
    result['durable'] = durable
    result['mailbox'] = inbox
    result['mailbox_policy'] = 'PRESERVE_EXISTING_AND_ACCEPT_NEW_APPEND_ONLY_FILES; SUCCESSOR_RESCANS_SAME_INBOX'
    return result


def same_boundary(before, after):
    require(after is not None, 'raced_past_COMPLETE')
    for key in ('journal_id', 'journal_identity', 'complete_index', 'complete_sha256',
            'learn_index', 'learn_sha256', 'checkpoint', 'resume_state'):
        require(before[key] == after[key], 'boundary_changed:' + key)
    prior = {record['index']: record['sha256'] for record in before['records']}
    actual = {record['index']: record['sha256'] for record in after['records']}
    require(all(actual.get(index) == expected for index, expected in prior.items()), 'prior_tail_not_rewritten')
    require(all(record['kind'] == 'INBOX' for record in after['records'] if record['index'] > before['head_index']),
        'only_new_INBOX_tail_allowed')
    require(all(after['mailbox'].get(path) == entry for path, entry in before['mailbox'].items()),
        'never_delete_or_rewrite_existing_parent_mailbox')
    return after


def _source_only_plan_shape(old, new):
    normalized = deepcopy(new)
    require(old['source_root'] != new['source_root'], 'new_immutable_source_root_required')
    for plan in (old, new):
        source = Path(plan['source_root'])
        require(source.is_absolute() and '..' not in source.parts, 'absolute_source_root')
    normalized['source_root'] = old['source_root']
    if 'startup_context' in old:
        relative = Path(old['startup_context']['path']).relative_to(old['source_root'])
        require(Path(new['startup_context']['path']) == Path(new['source_root']) / relative, 'startup_path_only_relocated')
        normalized['startup_context']['path'] = old['startup_context']['path']
    required = []
    if old.get('authorized_wall_extension') is not None:
        require('authorized_wall_extension' not in new, 'consumed_wall_authorization_must_be_removed_not_reapplied')
        normalized['authorized_wall_extension'] = deepcopy(old['authorized_wall_extension'])
        required.append('consumed_wall_extension')
    if old.get('checkpoint_tail_recovery') is not None:
        previous = old['checkpoint_tail_recovery']
        selection = new.get('checkpoint_tail_recovery')
        require(isinstance(selection, dict) and isinstance(previous, dict), 'checkpoint_tail_reader_must_remain_enabled')
        require(type(selection.get('complete_index')) is int and selection['complete_index'] >= 0
            and isinstance(selection.get('complete_sha256'), str)
            and re.fullmatch(r'[0-9a-f]{64}', selection['complete_sha256']), 'checkpoint_tail_explicit_complete_pin')
        for key in ('complete_index', 'complete_sha256'):
            normalized['checkpoint_tail_recovery'][key] = previous[key]
        required.append('checkpoint_tail_recovery')
    require(normalized == old, 'source_only_plan_no_deadline_targets_recipe_or_row_policy_change')
    return normalized, required


def required_plan_metadata_receipts(old, new):
    """Structural preflight only: this never authorizes an adoption or a signal."""
    return tuple(_source_only_plan_shape(old, new)[1])


def plan_metadata_binding(binding, candidate, old, new):
    """Bind receipts to the exact pair, not a mutable head which INBOX may extend."""
    require(binding is not None and candidate is not None, 'exact_candidate_and_life_binding_required')
    records = candidate['records']
    intents = candidate.get('record_intents', [])
    require(len(records) == len(intents) and all(record['index'] == intent['index']
        for record, intent in zip(records, intents)), 'metadata_candidate_durable_intent_pairs')
    validated = validate_records(records, binding, intents={intent['index']: intent for intent in intents})
    require(validated is not None and all(candidate.get(key) == value for key, value in validated.items()),
        'metadata_candidate_exact_COMPLETE_LEARN_and_saved_state')
    require(old['hard_end_unix'] == new['hard_end_unix'] == binding['hard_end_unix']
        == candidate['resume_state']['state']['deadline_unix'], 'metadata_same_admitted_deadline')
    return dict(schema='RETENTION_PLAN_METADATA_BINDING_V1', life_binding_sha256=digest(binding),
        old_plan_sha256=digest(old), new_plan_sha256=digest(new), journal_root=binding['journal_root'],
        retained_plan_root=old['root'],
        journal_id=binding['journal_id'], journal_identity_sha256=digest(candidate['journal_identity']),
        complete_index=candidate['complete_index'], complete_sha256=candidate['complete_sha256'],
        learn_index=candidate['learn_index'], learn_sha256=candidate['learn_sha256'],
        resume_state_sha256=candidate['resume_state']['sha256'], checkpoint_sha256=digest(candidate['checkpoint']),
        deadline_unix=binding['hard_end_unix'])


def _verify_consumed_wall_extension(old, binding, candidate, receipt):
    record, intent = receipt['record'], receipt['intent']
    validate_records([record], binding, intents={record['index']: intent})
    require(record['kind'] == 'WALL_EXTENDED' and record['index'] < candidate['complete_index'],
        'consumed_extension_precedes_selected_COMPLETE')
    document = record['document']
    authorization = old['authorized_wall_extension']
    require(set(document) == {'schema', 'authorization', 'plan_sha256', 'state'}
        and document['schema'] == 'R131_WALL_EXTENDED_V1'
        and document['authorization'] == authorization, 'exact_consumed_wall_authorization_record')
    require(set(authorization) == {'schema', 'previous_deadline_unix', 'previous_stream_sha256',
        'new_deadline_unix', 'lease_end_unix', 'safety_margin_seconds'}
        and authorization['schema'] == 'R131_SAVED_STATE_WALL_EXTENSION_V1', 'consumed_wall_authorization_schema')
    require(all(type(authorization[key]) in (int, float) and 0 <= authorization[key] < float('inf')
        for key in ('previous_deadline_unix', 'new_deadline_unix', 'lease_end_unix', 'safety_margin_seconds')),
        'consumed_wall_finite_budget')
    require(authorization['safety_margin_seconds'] >= 120 and authorization['previous_deadline_unix']
        < authorization['new_deadline_unix'] == binding['hard_end_unix']
        and authorization['new_deadline_unix'] <= authorization['lease_end_unix'] - authorization['safety_margin_seconds'],
        'consumed_wall_already_at_admitted_deadline')
    require(all(isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value)
        for value in (authorization['previous_stream_sha256'], document['plan_sha256'])), 'consumed_wall_source_hashes')
    saved = document['state']
    require(saved['sha256'] == digest(saved['state']) and saved['state']['pending'] is None
        and saved['state']['sleep_frontier'] == len(saved['state']['rows'])
        and saved['state']['sleep_receipts'] and saved['state']['sleep_receipts'][-1]['status'] == 'COMPLETE'
        and saved['state']['deadline_unix'] == binding['hard_end_unix'], 'consumed_wall_saved_state')
    previous = deepcopy(saved['state'])
    previous['deadline_unix'] = authorization['previous_deadline_unix']
    require(digest(previous) == authorization['previous_stream_sha256'], 'consumed_wall_exact_prior_state_no_other_changes')


def _verify_checkpoint_tail(old, new, binding, candidate, receipt):
    selection = new['checkpoint_tail_recovery']
    require(selection['policy'] == 'R233_PINNED_COMPLETE_TAIL_V1'
        and selection['root'] == binding['journal_root'] and selection['journal_id'] == binding['journal_id']
        and selection['life_id'] == old['think_act_learn']['trial_id'], 'checkpoint_tail_same_root_journal_life_policy')
    require(selection['complete_index'] == candidate['complete_index']
        and selection['complete_sha256'] == candidate['complete_sha256'], 'checkpoint_tail_reanchored_to_selected_COMPLETE')
    previous = old['checkpoint_tail_recovery']
    require(selection['complete_index'] >= previous['complete_index'] and (selection['complete_index']
        != previous['complete_index'] or selection['complete_sha256'] == previous['complete_sha256']),
        'checkpoint_tail_no_rollback_or_rewritten_old_anchor')
    require(receipt['selection_sha256'] == digest(selection)
        and receipt['restored_state_sha256'] == candidate['resume_state']['sha256'], 'checkpoint_tail_exact_selection_and_state')
    head = next((record for record in candidate['records'] if record['index'] == receipt['head_index']), None)
    require(head is not None and head['sha256'] == receipt['head_sha256']
        and head['index'] >= candidate['learn_index'], 'checkpoint_tail_scan_head_on_selected_chain')
    require(receipt['pending'] is None and receipt['historical_body_replay'] is False
        and receipt['sidecars_verified'] is True and receipt['inbox_preserved'] is True,
        'checkpoint_tail_bounded_resume_no_prefix_replay_or_lost_inbox')
    require(all(isinstance(receipt.get(key), str) and re.fullmatch(r'[0-9a-f]{64}', receipt[key])
        for key in ('reader_source_pins_sha256', 'cpu_receipt_sha256')), 'checkpoint_tail_tested_reader_receipt')


def normalize_source_only_plan(old, new, *, binding=None, candidate=None, receipts=None):
    """Normalize only proven continuation metadata for comparison; never deploy this normalized plan."""
    normalized, required = _source_only_plan_shape(old, new)
    receipts = {} if receipts is None else receipts
    require(isinstance(receipts, dict) and set(receipts) == set(required), 'exact_required_plan_metadata_receipts')
    if required:
        expected = plan_metadata_binding(binding, candidate, old, new)
        for name in required:
            require(receipts[name]['binding'] == expected and receipts[name].get('durable') is True,
                'exact_durable_plan_metadata_receipt:' + name)
        if 'consumed_wall_extension' in required:
            _verify_consumed_wall_extension(old, binding, candidate, receipts['consumed_wall_extension'])
        if 'checkpoint_tail_recovery' in required:
            _verify_checkpoint_tail(old, new, binding, candidate, receipts['checkpoint_tail_recovery'])
    return normalized


def verify_source_only_plans(old, new, *, binding=None, candidate=None, receipts=None):
    require(normalize_source_only_plan(old, new, binding=binding, candidate=candidate, receipts=receipts) == old,
        'source_only_normalized_plan')
    return digest(old)


def recheck_consumed_wall_receipt(binding, receipts):
    """Point-read/fsync one historical record and intent, never replay the prefix."""
    receipt = receipts.get('consumed_wall_extension')
    if receipt is None:
        return
    record = receipt['record']
    require(type(record['index']) is int and record['index'] >= 0, 'consumed_wall_record_index')
    root = Path(binding['journal_root'])
    directory = root / 'records'
    require(digest(journal_identity(binding)) == receipt['binding']['journal_identity_sha256'],
        'consumed_wall_same_bound_journal')
    for suffix, expected in (('.json', record), ('.intent.json', receipt['intent'])):
        require(read(directory / f"{record['index']:020d}{suffix}", durable=True) == expected,
            'consumed_wall_original_record_and_intent_unchanged')
    descriptor = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
