"""Bounded incremental TRAIN reduction; never opens a journal as its writer."""

import copy
import hashlib
import os
from pathlib import Path
import re
import stat
import uuid

from gpu import orch_r127_pilot_transcript as transcript
from gpu.orch_r125_stream_journal import _decode, _digest, _encoded, require


SCHEMA = 'R166_VERIFIED_TRAIN_CURSOR_V1'
MAX_STATE_BYTES = 16 * 1024 * 1024
MAX_POLL_BYTES = 128 * 1024 * 1024


def genesis(root):
    return dict(schema=SCHEMA, root=str(Path(root).resolve()), next_index=0,
        journal_id=None, head_sha256=None, boundary_file_sha256=None, inbox={}, delivered={},
        events=[], pending=None, response=None, response_count=0, request_count=0, sleep_count=0)


def _read(directory, index, budget):
    name = f'{index:020d}.json'
    descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                         dir_fd=directory)
    with os.fdopen(descriptor, 'rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode), 'regular_record')
        require(before.st_size <= transcript.MAX_RECORD_BYTES, 'record_byte_limit')
        require(before.st_size <= budget, 'poll_byte_limit')
        raw = stream.read(before.st_size + 1)
        after = os.fstat(stream.fileno())
        current = os.stat(name, dir_fd=directory, follow_symlinks=False)
    require(len({(entry.st_dev, entry.st_ino, entry.st_mode, entry.st_size, entry.st_mtime_ns)
        for entry in (before, after, current)}) == 1 and len(raw) == before.st_size,
        'record_changed_during_read')
    record = _decode(raw)
    require(type(record) is dict and set(record) == {'schema', 'journal_id', 'index',
        'kind', 'previous_sha256', 'document', 'sha256'}, 'record_fields')
    require(record['schema'] == transcript.SCHEMA and type(record['index']) is int
        and record['index'] == index and type(record['journal_id']) is str
        and re.fullmatch('[0-9a-f]{32}', record['journal_id'])
        and type(record['document']) is dict and type(record['kind']) is str
        and re.fullmatch('[A-Z][A-Z0-9_]{0,63}', record['kind'])
        and transcript._hash(record['previous_sha256'])
        and record['sha256'] == _digest({key: value for key, value in record.items()
                                      if key != 'sha256'}), 'record_digest')
    return record, hashlib.sha256(raw).hexdigest(), len(raw)


def _reduce(state, record):
    kind, document = record['kind'], record['document']
    evidence = dict(record_index=record['index'], record_sha256=record['sha256'])
    if kind == 'INBOX':
        entry = transcript._inbox(document)
        require(entry['inbox_id'] not in state['inbox'], 'unique_inbox')
        state['inbox'][entry['inbox_id']] = entry
    elif kind == 'REQUEST':
        require(state['pending'] is None and document.get('split') == 'TRAIN', 'unique_TRAIN_request')
        require(document.get('render_receipt', {}).get('all_history_tokens_masked') is True,
                'external_context_masked')
        visible, ambiguous = transcript._visible(document['messages'], state['inbox'])
        if ambiguous:
            from organism_v6.orch_r124_train_history import TrainHistory
            envelope = document['resume_state']
            require(_digest(envelope['state']) == envelope['sha256'], 'delivery_resume_state_binding')
            history_document = envelope['state']['history']
            history = TrainHistory.restore(history_document)
            candidates = dict(state['inbox'])
            for identifier in ambiguous:
                entry = candidates[identifier]
                matches = [(position, event) for position, event in enumerate(history_document['events'])
                    if event['event_id'] == entry['actor'] + ':inbox:' + identifier]
                require(len(matches) == 1, 'one_exact_ambiguous_inbox_event')
                position, event = matches[0]
                require(event['actor'] == entry['actor'] and event['split'] == 'TRAIN'
                    and event['source_id'] == entry['inbox_source_id']
                    and event['source_sha256'] == entry['inbox_source_sha256']
                    and event['text'] == entry['visible_text'], 'exact_delivery_history_attribution')
                if position < history.visible_frontier.event_count:
                    del candidates[identifier]
            visible, ambiguous = transcript._visible(document['messages'], candidates)
        require(not ambiguous, 'ambiguous_delivery')
        state['request_count'] += 1
        for identifier in sorted(visible - state['delivered'].keys()):
            entry = state['inbox'][identifier]
            state['delivered'][identifier] = dict(speaker=entry['speaker'],
                inbox_sha256=entry['inbox_source_sha256'],
                text_sha256=hashlib.sha256(entry['text'].encode()).hexdigest(),
                request_count=state['request_count'], sleep_count=state['sleep_count'], **evidence)
            state['events'].append(dict(actor=entry['actor'], speaker=entry['speaker'],
                                        text=entry['text'], **evidence))
        state['pending'] = dict(segment=document['segment'], request_sha256=_digest(
            {key: value for key, value in document.items() if key != 'resume_state'}))
    elif kind == 'RESPONSE':
        require(state['pending'] is not None and state['response'] is None
            and document.get('request_sha256') == state['pending']['request_sha256'], 'response_binding')
        state['response'] = dict(document=document, evidence=evidence)
    elif kind == 'COMMITTED' and document.get('kind') == 'BIRTH':
        require(state['pending'] is None and state['response_count'] == 0
            and record['index'] == 0, 'genesis_birth_only')
    elif kind in ('COMMITTED', 'CONTEXT_COMMITTED'):
        require(state['pending'] is not None and state['response'] is not None
            and document.get('segment') == state['pending']['segment']
            and document.get('source_sha256') == _digest(state['response']['document']), 'commit_binding')
        state['response_count'] += 1
        state['events'].append(dict(actor='child', text=state['response']['document']['response']['raw'],
            commit_record_index=record['index'], commit_record_sha256=record['sha256'],
            **state['response']['evidence']))
        state['pending'], state['response'] = None, None
    elif kind == 'SLEEP_COMPLETE':
        state['sleep_count'] += 1
    state['events'] = state['events'][-12:]


def poll(root, cursor=None, *, cursor_sha256=None, max_records=128, max_bytes=MAX_POLL_BYTES):
    """Continue only caller-trusted cursor bytes; self-hashes are not authority.

    Filename census remains capped/contiguous; historical contents are trusted from
    the prior verified cursor, with an exact reread of the boundary record. This is
    append-only verification, not a fresh audit of every historical file each poll.
    """
    require(type(max_records) is int and 1 <= max_records <= transcript.MAX_RECORDS
        and type(max_bytes) is int and 1 <= max_bytes <= MAX_POLL_BYTES, 'bounded_poll')
    require(not any(re.search(r'(^|[_ .-])(held|final|readout|sealed)([_ .-]|$)', part, re.I)
        for part in Path(root).parts), 'TRAIN_root_only')
    if cursor is None:
        state = genesis(root)
    else:
        require(len(_encoded(cursor)) <= MAX_STATE_BYTES and _digest(cursor) == cursor_sha256,
                'trusted_cursor_pin')
        require(cursor['schema'] == SCHEMA and cursor['root'] == str(Path(root).resolve()), 'cursor_root')
        state = copy.deepcopy(cursor)
    used, processed = 0, 0
    with transcript._open_stream_directory(root, 'records') as (directory, unused):
        indices = []
        with os.scandir(directory) as entries:
            for count, entry in enumerate(entries, 1):
                require(count <= transcript.MAX_RECORDS * 4 + 1024, 'directory_entry_limit')
                if re.fullmatch(r'[0-9]{20}\.json', entry.name):
                    indices.append(int(entry.name[:20]))
                    require(len(indices) <= transcript.MAX_RECORDS, 'record_count_limit')
        indices.sort()
        require(indices == list(range(len(indices))), 'noncontiguous_records')
        require(state['next_index'] <= len(indices), 'journal_rewind')
        if state['next_index']:
            boundary, file_hash, size = _read(directory, state['next_index'] - 1, max_bytes)
            used += size
            require(file_hash == state['boundary_file_sha256']
                and boundary['sha256'] == state['head_sha256']
                and boundary['journal_id'] == state['journal_id'], 'boundary_changed')
        for index in indices[state['next_index']:state['next_index'] + max_records]:
            size = os.stat(f'{index:020d}.json', dir_fd=directory, follow_symlinks=False).st_size
            if used + size > max_bytes and processed:
                break
            record, file_hash, size = _read(directory, index, max_bytes - used)
            previous = state['head_sha256'] or _digest(dict(schema=transcript.SCHEMA,
                                                          journal_id=record['journal_id']))
            require(record['previous_sha256'] == previous and state['journal_id'] in
                (None, record['journal_id']), 'journal_chain')
            _reduce(state, record)
            state.update(next_index=index+1, head_sha256=record['sha256'],
                         journal_id=record['journal_id'], boundary_file_sha256=file_hash)
            used += size
            processed += 1
            require(len(_encoded(state)) <= MAX_STATE_BYTES, 'cursor_state_limit')
    snapshot = {key: state[key] for key in ('journal_id', 'head_sha256', 'events', 'delivered',
                                           'response_count', 'request_count', 'sleep_count')}
    snapshot.update(schema='R153_COMMITTED_TRAIN_SNAPSHOT_V1', split='TRAIN',
        caught_up=state['next_index'] == len(indices), source_bytes=used, new_records=processed)
    return dict(cursor=state, cursor_sha256=_digest(state), snapshot=snapshot)


def stored_poll(root, store, reference=None):
    """Remote seam: short path/hash arguments, parent-owned state outside child root.

    Caller serializes custody and persists each returned reference. A lost call is
    read-only with respect to the child; orphan cursor files do not publish advice.
    """
    root, store = Path(root).resolve(), Path(store)
    require(store.is_absolute() and store == store.resolve() and store != root
        and root not in store.parents and store not in root.parents, 'disjoint_cursor_store')
    store.mkdir(mode=0o700, parents=False, exist_ok=True)
    cursor = None
    if reference is not None:
        path = Path(reference['path'])
        require(path.parent == store and not path.is_symlink()
            and path.stat().st_size <= MAX_STATE_BYTES, 'bounded_cursor_file')
        raw = path.read_bytes()
        require(hashlib.sha256(raw).hexdigest() == reference['sha256'], 'cursor_file_pin')
        cursor = _decode(raw)
    result = poll(root, cursor, cursor_sha256=_digest(cursor) if cursor else None)
    path = store/(uuid.uuid4().hex + '.json')
    raw = _encoded(result['cursor'])
    with path.open('xb') as output:
        output.write(raw)
        output.flush()
        os.fsync(output.fileno())
    descriptor = os.open(store, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return dict(snapshot=result['snapshot'], reference=dict(path=str(path),
                sha256=hashlib.sha256(raw).hexdigest()))
