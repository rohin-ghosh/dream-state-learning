"""Astra7-only authentic P7 parent admission; no human-speaker substitution."""

import hashlib
import json
from pathlib import Path
import re
import uuid

from organism_v6.orch_r124_train_history import TrainEvent


P7_JOURNAL_ID = 'e9d22d1e26234c4bbac761922929365f'
SCHEMA = 'R229_P7_PARENT_CAPSULE_V1'
LIMIT = 4 * 1024 * 1024


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def canonical(document):
    return json.dumps(document, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def check_record(record, kind):
    require(type(record) is dict and record.get('kind') == kind
        and record.get('journal_id') == P7_JOURNAL_ID, 'actual_P7_journal_and_record_kind')
    require(record.get('sha256') == hashlib.sha256(canonical(
        {key: value for key, value in record.items() if key != 'sha256'})).hexdigest(),
        'P7_canonical_record_sha256')


def validate_capsule(capsule, text):
    require(type(capsule) is dict and set(capsule) == {
        'schema', 'source_response', 'source_stage', 'projection_start', 'projection_end'}
        and capsule['schema'] == SCHEMA, 'exact_P7_capsule_schema')
    response, stage = capsule['source_response'], capsule['source_stage']
    check_record(response, 'RESPONSE')
    check_record(stage, 'R184_STAGE')
    require(stage['document'].get('stage') == 'ACT'
        and response['index'] < stage['index'] <= response['index'] + 32
        and stage['document'].get('source_sha256') == hashlib.sha256(canonical(response['document'])).hexdigest(),
        'P7_ACT_bound_to_actual_response')
    raw = response['document']['response']['raw']
    start, end = capsule['projection_start'], capsule['projection_end']
    require(type(raw) is str and type(start) is int and type(end) is int
        and 0 <= start < end <= len(raw) and type(text) is str and text == raw[start:end],
        'P7_exact_contiguous_own_output_projection')
    return response, stage


def p7_event(journal, message, path, source_sha256):
    require(type(message) is dict and set(message) == {
        'id', 'text', 'split', 'actor', 'schema', 'speaker', 'source_receipt'}
        and message['schema'] == 'R127_ATTRIBUTED_INBOX_V1'
        and message['actor'] == 'parent' and message['speaker'] == 'P7'
        and message['split'] == 'TRAIN', 'Astra7_only_authentic_P7_parent_route')
    require(type(message['id']) is str and bool(message['id'].strip())
        and type(message['text']) is str, 'inbox_id_and_text')
    require(type(path) is str and Path(path).parent == journal.inbox
        and Path(path).name.endswith('.json'), 'inbox_source_path')
    receipt = message['source_receipt']
    require(type(receipt) is dict and set(receipt) == {'path', 'sha256'}
        and type(receipt['path']) is str and type(receipt['sha256']) is str
        and re.fullmatch('[0-9a-f]{64}', receipt['sha256']), 'P7_source_receipt_shape')
    receipt_path = Path(receipt['path'])
    allowed = journal.inbox.parent / 'p7_receipts'
    require(receipt_path.is_absolute() and '..' not in receipt_path.parts
        and receipt_path.parent == allowed and not allowed.is_symlink()
        and not receipt_path.is_symlink() and receipt_path.is_file(), 'P7_confined_receipt_path')
    require(receipt_path.stat().st_size <= LIMIT, 'P7_receipt_size')
    raw = receipt_path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == receipt['sha256'], 'P7_receipt_file_sha256')
    validate_capsule(json.loads(raw), message['text'])
    return TrainEvent(event_id='parent:inbox:' + message['id'], actor='parent',
        text='P7: ' + message['text'], split='TRAIN', phase='experience',
        episode_id='continual_stream', source_id=path, source_sha256=source_sha256,
        origin='TRAIN_COLLECTION')


def journal_class(base):
    class Astra7Journal(base):
        def _inbox_event(self, message, path, source_sha256):
            if type(message) is dict and message.get('actor') == 'parent':
                return p7_event(self, message, path, source_sha256)
            return super()._inbox_event(message, path, source_sha256)

    return Astra7Journal


def publish_p7(root, capsule_path, text, *, logical_root=None):
    from gpu.orch_r127_pilot_console import _open_stream_directory, _publish
    root, capsule_path = Path(root), Path(capsule_path)
    require(capsule_path.parent == root / 'stream/p7_receipts', 'publisher_exact_receipt_directory')
    require(not capsule_path.is_symlink() and capsule_path.stat().st_size <= LIMIT, 'publisher_bounded_receipt')
    raw = capsule_path.read_bytes()
    validate_capsule(json.loads(raw), text)
    logical_root = root if logical_root is None else Path(logical_root)
    require(logical_root.is_absolute() and '..' not in logical_root.parts, 'logical_inbox_mount_root')
    admitted_path = logical_root / 'stream/p7_receipts' / capsule_path.name
    message = dict(schema='R127_ATTRIBUTED_INBOX_V1', id=uuid.uuid4().hex,
        actor='parent', speaker='P7', split='TRAIN', text=text,
        source_receipt=dict(path=str(admitted_path), sha256=hashlib.sha256(raw).hexdigest()))
    require(len(canonical(message)) <= 262144, 'P7_bounded_inbox')
    with _open_stream_directory(root, 'inbox') as (directory, path):
        return _publish(directory, path, message)
