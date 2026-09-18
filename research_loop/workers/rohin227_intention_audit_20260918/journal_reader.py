"""Local copy of existing immutable-reader primitives, without live locations."""

import hashlib
import json
import os
from pathlib import Path
import stat


MAX_BYTES = 128 * 1024 * 1024


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def read_bytes(path, limit=MAX_BYTES, tail=False):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(descriptor, 'rb') as incoming:
        before = os.fstat(incoming.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size > limit:
            raise ValueError('bounded_regular_file_required')
        if tail:
            incoming.seek(max(0, before.st_size - 4096))
        payload = incoming.read()
        after = os.fstat(incoming.fileno())
        if (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
            raise ValueError('immutable_file_changed_during_read')
    return payload, before


def metadata(path):
    ending, _ = read_bytes(path, tail=True)
    position = ending.rfind(b',"index":')
    if position < 0:
        position = ending.rfind(b'\n "index":')
    record = json.loads(b'{' + ending[position + 1:]) if position >= 0 else json.loads(read_bytes(path)[0])
    return {key: record[key] for key in ('index', 'kind', 'sha256', 'previous_sha256', 'journal_id')}


def verified(path, journal_id):
    payload, information = read_bytes(path)
    record = json.loads(payload)
    if record['sha256'] != digest({key: value for key, value in record.items() if key != 'sha256'}):
        raise ValueError('record_hash_mismatch')
    if record['journal_id'] != journal_id or record['index'] != int(path.stem):
        raise ValueError('record_identity_mismatch')
    return record, dict(record_index=record['index'], record_sha256=record['sha256'],
                        file_sha256=hashlib.sha256(payload).hexdigest(), file_mtime_unix=information.st_mtime)


def reduced(path, journal_id, life):
    record, receipt = verified(path, journal_id)
    kind, document = record['kind'], record['document']
    result = dict(receipt, kind=kind, envelope_verified=True)
    if kind != 'COMMITTED' or 'source_sha256' not in document:
        return None
    envelope = document['state']
    state = envelope['state']
    if digest(state) != envelope['sha256'] or state['pending'] is not None:
        raise ValueError('committed_state_mismatch')
    row = state['rows'][-1]
    if row['source_sha256'] != document['source_sha256'] or row['actor'] != 'child':
        raise ValueError('committed_child_source_mismatch')
    result.update(source_sha256=row['source_sha256'], segment=row['segment'],
                  target_sha256=hashlib.sha256(row['target'].encode()).hexdigest(),
                  state_sha256=envelope['sha256'], committed_row_verified=True)
    return result
