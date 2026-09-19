"""Opt-in pinned COMPLETE recovery; raw prefix verification, original tail rules."""

from copy import deepcopy
import hashlib
import os
from pathlib import Path
import re
import stat


POLICY = 'R233_PINNED_COMPLETE_TAIL_V1'
ANCHOR_SCHEMA = 'R233_DURABLE_COMPLETE_ANCHOR_V1'
HASH = re.compile(r'[0-9a-f]{64}')
TRAILER = re.compile(
    rb',"index":([0-9]+),"journal_id":"([0-9a-f]{32})","kind":"([A-Z][A-Z0-9_]{0,63})",'
    rb'"previous_sha256":"([0-9a-f]{64})","schema":"R125_STREAM_JOURNAL_V1",'
    rb'"sha256":"([0-9a-f]{64})"}\n\Z')
FIELDS = {'policy', 'root', 'journal_id', 'complete_index', 'complete_sha256',
    'life_id', 'max_tail_records', 'max_tail_bytes', 'sidecars', 'persist_complete_anchors'}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def validate_selection(selection, root, life_id=None):
    require(type(selection) is dict and set(selection) == FIELDS, 'checkpoint_tail_exact_selection')
    require(selection['policy'] == POLICY, 'checkpoint_tail_known_policy')
    requested = Path(selection['root'])
    require(requested.is_absolute() and '..' not in requested.parts
        and requested == Path(root).absolute(), 'checkpoint_tail_exact_root')
    require(type(selection['journal_id']) is str
        and re.fullmatch(r'[0-9a-f]{32}', selection['journal_id']), 'checkpoint_tail_journal_identity')
    require(type(selection['complete_index']) is int and selection['complete_index'] >= 0
        and type(selection['complete_sha256']) is str and HASH.fullmatch(selection['complete_sha256']),
        'checkpoint_tail_explicit_complete_pin')
    require(type(selection['life_id']) is str and bool(selection['life_id'])
        and (life_id is None or selection['life_id'] == life_id), 'checkpoint_tail_same_life')
    require(type(selection['max_tail_records']) is int and selection['max_tail_records'] > 0
        and type(selection['max_tail_bytes']) is int and selection['max_tail_bytes'] > 0,
        'checkpoint_tail_explicit_positive_bounds')
    require(type(selection['persist_complete_anchors']) is bool, 'checkpoint_tail_explicit_durability')
    require(type(selection['sidecars']) is list, 'checkpoint_tail_sidecars_list')
    names = set()
    for item in selection['sidecars']:
        require(type(item) is dict and set(item) == {'name', 'kind', 'required'},
            'checkpoint_tail_sidecar_fields')
        require(type(item['name']) is str and re.fullmatch(r'[a-z][a-z0-9_]*\.json', item['name'])
            and item['name'] not in names and item['name'] != 'JOURNAL.json',
            'checkpoint_tail_unique_relative_sidecar')
        require(item['kind'] == 'R197_CORRECTION_CYCLE' and type(item['required']) is bool,
            'checkpoint_tail_supported_sidecar_frontier')
        names.add(item['name'])
    return deepcopy(selection)


def _identity(value):
    return value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns


def hash_record(journal, index):
    name = f'{index:020d}.json'
    descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
        dir_fd=journal._records_fd)
    with os.fdopen(descriptor, 'rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode), 'checkpoint_tail_regular_record')
        stream.seek(max(0, before.st_size - 2048))
        ending = stream.read()
        matched = TRAILER.search(ending)
        require(matched is not None, 'checkpoint_tail_canonical_record_envelope')
        number, journal_id, kind, previous, expected = [part.decode() for part in matched.groups()]
        suffix = b',"sha256":"' + expected.encode() + b'"}\n'
        payload_bytes = before.st_size - len(suffix)
        require(payload_bytes > 0, 'checkpoint_tail_record_length')
        stream.seek(0)
        checksum = hashlib.sha256()
        raw_checksum = hashlib.sha256()
        offset = 0
        prefix = b''
        while True:
            block = stream.read(4 * 1024 * 1024)
            if not block:
                break
            if not prefix:
                prefix = block[:13]
            raw_checksum.update(block)
            remaining = max(0, payload_bytes - offset)
            checksum.update(block[:remaining])
            offset += len(block)
        checksum.update(b'}')
        after = os.fstat(stream.fileno())
        current = os.stat(name, dir_fd=journal._records_fd, follow_symlinks=False)
        require(_identity(before) == _identity(after) == _identity(current)
            and offset == before.st_size, 'checkpoint_tail_record_changed_during_hash')
        require(prefix.startswith(b'{"document":{') and checksum.hexdigest() == expected,
            'checkpoint_tail_raw_record_integrity')
        require(int(number) == index and str(index) == number
            and journal_id == journal._manifest['journal_id'], 'checkpoint_tail_record_identity')
    header = dict(schema='R125_STREAM_JOURNAL_V1', journal_id=journal_id, index=index,
        kind=kind, previous_sha256=previous, sha256=expected)
    intent = journal._read_json(journal._records_fd, f'{index:020d}.intent.json')
    require(intent == journal._intent(header), 'checkpoint_tail_intent_binding')
    return header, dict(bytes=offset, raw_sha256=raw_checksum.hexdigest())


def _decoded_record(journal, header):
    from gpu.orch_r125_stream_journal import _digest
    record = journal._read_json(journal._records_fd, f'{header["index"]:020d}.json')
    require(type(record) is dict and set(record) == set(header) | {'document'}
        and all(record[key] == value for key, value in header.items())
        and record['sha256'] == _digest({key: value for key, value in record.items() if key != 'sha256'}),
        'checkpoint_tail_decoded_record_binding')
    journal._validate_entry(record['kind'], record['document'])
    return record


def _sidecars(journal, state, headers, selection):
    checkpoints = state['latest']['document']['state']
    completed = len(checkpoints['sleep_receipts'])
    allowed_cycle = completed + int(len(checkpoints['rows']) > checkpoints['sleep_frontier'])
    results = []
    for definition in selection['sidecars']:
        name = definition['name']
        try:
            raw = journal._read_bytes(journal._root_fd, name, 1024 * 1024)
        except FileNotFoundError:
            require(not definition['required'], 'checkpoint_tail_required_sidecar_missing')
            results.append(dict(name=name, present=False))
            continue
        from gpu.orch_r125_stream_journal import _decode
        cached = _decode(raw)
        require(type(cached) is dict and set(cached) == {'record_index', 'record_sha256'}
            and type(cached['record_index']) is int and 0 <= cached['record_index'] < state['index'],
            'checkpoint_tail_sidecar_beyond_frontier')
        header = headers[cached['record_index']]
        require(header['sha256'] == cached['record_sha256'] and header['kind'] == definition['kind'],
            'checkpoint_tail_sidecar_source_binding')
        record = _decoded_record(journal, header)
        ledger = record['document']['ledger']
        require(ledger['schema'] == 'R197_CORRECTION_LEDGER_V1'
            and ledger['life_id'] == selection['life_id'], 'checkpoint_tail_sidecar_life')
        cycles = [entry['cycle'] for entry in ledger['cycles']]
        require(all(type(cycle) is int and 0 < cycle <= allowed_cycle for cycle in cycles)
            and cycles == sorted(set(cycles)), 'checkpoint_tail_sidecar_cycle_ahead_of_stream')
        for entry in ledger['cycles']:
            require(type(entry['completed_sleeps']) is int
                and 0 <= entry['completed_sleeps'] <= completed,
                'checkpoint_tail_sidecar_sleep_ahead_of_stream')
            reference = (entry['input'].get('source') or {}).get('response')
            if reference is not None:
                index = reference['record_index']
                require(type(index) is int and 0 <= index < header['index']
                    and headers[index]['kind'] == 'RESPONSE'
                    and headers[index]['sha256'] == reference['record_sha256'],
                    'checkpoint_tail_sidecar_response_provenance')
        require(raw == journal._read_bytes(journal._root_fd, name, 1024 * 1024),
            'checkpoint_tail_sidecar_changed_during_read')
        results.append(dict(name=name, present=True, file_sha256=hashlib.sha256(raw).hexdigest(),
            record_index=header['index'], record_sha256=header['sha256'],
            maximum_cycle=max(cycles) if cycles else None))
    return results


def scan(journal, selection, *, prefix_proof=None):
    from gpu.orch_r125_stream_journal import _digest
    selection = validate_selection(selection, journal.root)
    journal._ensure_open()
    require(selection['journal_id'] == journal._manifest['journal_id'], 'checkpoint_tail_same_journal')
    require(not any(name.endswith('.partial') for name in os.listdir(journal._root_fd)),
        'incomplete_journal_initialization')
    require(journal._read_json(journal._root_fd, 'JOURNAL.json') == journal._manifest,
        'journal_manifest_changed')
    names = set(os.listdir(journal._records_fd))
    indices = set()
    for name in names:
        matched = re.fullmatch(r'(\d{20})(?:\.intent)?\.json', name)
        require(matched is not None, 'incomplete_or_unexpected_journal_tail')
        indices.add(int(matched[1]))
    require(sorted(indices) == list(range(len(indices))), 'noncontiguous_journal')
    anchor_index = selection['complete_index']
    require(anchor_index < len(indices), 'checkpoint_tail_anchor_missing')
    tail_count = len(indices) - anchor_index - 1
    require(tail_count <= selection['max_tail_records'], 'checkpoint_tail_record_bound_exceeded')
    for index in indices:
        require(f'{index:020d}.json' in names and f'{index:020d}.intent.json' in names,
            'incomplete_journal_tail')
    tail_bytes = sum(os.stat(f'{index:020d}.json', dir_fd=journal._records_fd,
        follow_symlinks=False).st_size for index in range(anchor_index + 1, len(indices)))
    require(tail_bytes <= selection['max_tail_bytes'], 'checkpoint_tail_byte_bound_exceeded')
    verified_prefix = None
    if prefix_proof is not None:
        from gpu.immutable_prefix_proof import prepare
        verified_prefix = prepare(journal, selection, prefix_proof)
    headers = {}
    previous = _digest(journal._manifest)
    raw_bytes = 0
    inbox = {} if verified_prefix is None else deepcopy(verified_prefix.inbox)
    decoded_prefix = []
    for index in range(len(indices)):
        if verified_prefix is None:
            header, hashed = hash_record(journal, index)
        else:
            header, hashed = verified_prefix.record(index, hash_record)
        require(header['previous_sha256'] == previous, 'checkpoint_tail_chain_integrity')
        headers[index] = header
        raw_bytes += hashed['bytes']
        previous = header['sha256']
        if index <= anchor_index and header['kind'] == 'INBOX' and (
                verified_prefix is None or index >= verified_prefix.prefix_count):
            record = _decoded_record(journal, header)
            journal._advance(dict(inbox=inbox), 'INBOX', record['document'])
            decoded_prefix.append(index)
    anchor = headers[anchor_index]
    require(anchor['kind'] == 'SLEEP_COMPLETE' and anchor['sha256'] == selection['complete_sha256'],
        'checkpoint_tail_exact_complete_pin')
    complete = _decoded_record(journal, anchor)
    decoded_prefix.append(anchor_index)
    checkpoint = journal._checkpoint(complete['document']['resume_state'])
    saved = checkpoint['document']['state']
    receipt = {key: value for key, value in complete['document'].items() if key != 'resume_state'}
    require(saved['pending'] is None and saved['sleep_frontier'] == len(saved['rows'])
        and bool(saved['sleep_receipts']) and saved['sleep_receipts'][-1] == receipt
        and receipt['status'] == 'COMPLETE'
        and saved['model_state_sha256'] == _digest(receipt['checkpoint_sha256']),
        'checkpoint_tail_coherent_complete')
    state = dict(index=anchor_index + 1, previous=anchor['sha256'], latest=checkpoint,
        request=None, response=None, sleep_request=None, inbox=inbox)
    for index in range(anchor_index + 1, len(indices)):
        record = _decoded_record(journal, headers[index])
        journal._advance(state, record['kind'], record['document'])
        state['index'], state['previous'] = index + 1, record['sha256']
    sidecars = _sidecars(journal, state, headers, selection)
    require(set(os.listdir(journal._records_fd)) == names, 'journal_changed_during_scan')
    if verified_prefix is not None:
        verified_prefix.finish()
    journal.checkpoint_tail_receipt = dict(policy=POLICY, complete_index=anchor_index,
        complete_sha256=anchor['sha256'], restored_state_sha256=state['latest']['expected_sha256'],
        record_count=state['index'], head_sha256=state['previous'], raw_record_bytes_hashed=raw_bytes,
        prefix_records=anchor_index + 1, decoded_prefix_indices=decoded_prefix,
        tail_records=tail_count, tail_bytes=tail_bytes, sidecars=sidecars,
        prefix_semantic_authority='EXTERNAL_EXACT_COMPLETE_PIN_OR_CURRENT_VALIDATED_WRITER',
        prefix_work='ALL_RETAINED_BYTES_HASHED_NO_HISTORICAL_BODY_JSON_REPLAY',
        source_admission_unchanged=True, prefix_rewritten=False, pending_preserved=True)
    if verified_prefix is not None:
        journal.checkpoint_tail_receipt.update(verified_prefix.receipt())
    return state


def persist_complete(journal, reference):
    from gpu.orch_r125_stream_journal import _digest
    selection = journal._checkpoint_tail
    if selection is None or not selection['persist_complete_anchors']:
        return
    state = journal._state
    require(state['index'] == reference['index'] + 1 and state['previous'] == reference['sha256']
        and state['request'] is None and state['response'] is None and state['sleep_request'] is None
        and state['latest']['document']['state']['pending'] is None,
        'checkpoint_tail_durable_anchor_requires_resolved_complete')
    document = dict(schema=ANCHOR_SCHEMA, policy=POLICY, root=str(journal.root),
        journal_id=journal._manifest['journal_id'], complete_index=reference['index'],
        complete_sha256=reference['sha256'], state_sha256=state['latest']['expected_sha256'],
        previous_trusted_complete_index=selection['complete_index'],
        previous_trusted_complete_sha256=selection['complete_sha256'],
        authority='CURRENT_EXCLUSIVE_VALIDATED_WRITER', automatic_external_selection=False)
    directory_name = 'checkpoint_tail_anchors'
    try:
        os.mkdir(directory_name, mode=0o700, dir_fd=journal._root_fd)
        os.fsync(journal._root_fd)
    except FileExistsError:
        pass
    descriptor = os.open(directory_name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
        dir_fd=journal._root_fd)
    try:
        bound = os.fstat(descriptor)
        require(stat.S_ISDIR(bound.st_mode), 'checkpoint_tail_regular_anchor_directory')
        name = f'{reference["index"]:020d}.json'
        journal._publish(descriptor, name, document)
        require(_identity(os.fstat(descriptor)) == _identity(os.stat(directory_name,
            dir_fd=journal._root_fd, follow_symlinks=False)), 'checkpoint_tail_anchor_directory_replaced')
        written = journal._read_json(descriptor, name)
        require(written == document, 'checkpoint_tail_durable_anchor_exact_bytes')
    finally:
        os.close(descriptor)
    journal._checkpoint_tail = dict(selection, complete_index=reference['index'],
        complete_sha256=reference['sha256'])
    journal.checkpoint_tail_durable_anchor = dict(document=document, document_sha256=_digest(document),
        path=str(journal.root / directory_name / name))
