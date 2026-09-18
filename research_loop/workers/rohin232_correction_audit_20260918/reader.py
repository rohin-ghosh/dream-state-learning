"""Bounded stdlib-only journal projection; read-only on the receiving host."""

import hashlib
import json
import os
from pathlib import Path
import re
import stat
import time

REVISION = 'R232_READ_ONLY_V2'


def rendered(event, messages):
    for message in messages:
        if message.get('role') != 'user' or not isinstance(message.get('content'), str):
            continue
        content = message['content']
        if content == event['text']:
            return True
        parts = content.split('\n', 2)
        header = {'parent': 'Parent advice (not an observed fact)', 'environment': 'Recorded environment observation'}
        if len(parts) != 3 or parts[0] != header.get(event['actor']) or parts[2] != event['text']:
            continue
        try:
            metadata = json.loads(parts[1])
        except json.JSONDecodeError:
            continue
        if all(metadata.get(key) == event.get(key) for key in ('actor', 'event_id', 'source_id', 'source_sha256', 'split')):
            return True
    return False


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def read_stable(path, maximum=128 * 1024 * 1024):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(descriptor, 'rb') as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size > maximum:
            raise ValueError('bounded_regular_file_required')
        raw = stream.read()
        after = os.fstat(stream.fileno())
    if (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
        raise ValueError('source_changed_during_read')
    return raw, before


def metadata(path):
    with path.open('rb') as stream:
        stream.seek(max(0, path.stat().st_size - 4096))
        ending = stream.read()
    offset = ending.rfind(b',"index":')
    if offset < 0:
        row = json.loads(read_stable(path)[0])
    else:
        row = json.loads(b'{' + ending[offset + 1:])
    return {key: row[key] for key in ('index', 'kind', 'sha256', 'previous_sha256', 'journal_id')}


def verified(path, journal_id):
    raw, information = read_stable(path)
    row = json.loads(raw)
    if row['journal_id'] != journal_id or row['index'] != int(path.stem):
        raise ValueError('journal_identity_mismatch')
    if row['sha256'] != digest({key: value for key, value in row.items() if key != 'sha256'}):
        raise ValueError('canonical_record_hash_mismatch')
    return row, dict(index=row['index'], sha256=row['sha256'], kind=row['kind'],
        file_sha256=hashlib.sha256(raw).hexdigest(), time_unix=information.st_mtime)


def collect(root, expected_journal=None, maximum=900, after=None):
    root = Path(root)
    identity = json.loads(read_stable(root / 'stream/JOURNAL.json', 4096)[0])
    journal_id = identity['journal_id']
    if expected_journal and expected_journal != journal_id:
        raise ValueError('incarnation_changed_owner_binding_required')
    files = sorted((root / 'stream/records').glob('[0-9]' * 20 + '.json'))
    if not files:
        raise ValueError('no_actual_journal_records')
    head = metadata(files[-1])
    selected = files[-maximum:] if after is None else [path for path in files if int(path.stem) > after][:maximum]
    rows, continuity = [], []
    selected_kinds = {'REQUEST', 'RESPONSE', 'COMMITTED', 'CONTEXT_COMMITTED', 'R184_STAGE', 'INBOX', 'SLEEP_COMPLETE'}
    bytes_read = 0
    previous = None
    for path in selected:
        meta = metadata(path)
        if meta['journal_id'] != journal_id or (previous and (meta['index'] != previous['index'] + 1 or meta['previous_sha256'] != previous['sha256'])):
            raise ValueError('noncontiguous_journal_window')
        if bytes_read + path.stat().st_size > 512 * 1024 * 1024:
            break
        continuity.append(meta)
        previous = meta
        if meta['kind'] not in selected_kinds:
            continue
        record, receipt = verified(path, journal_id)
        bytes_read += path.stat().st_size
        document = record['document']
        receipt['document_sha256'] = digest(document)
        kind = record['kind']
        if kind == 'REQUEST':
            if document.get('split') != 'TRAIN':
                raise ValueError('TRAIN_only')
            envelope = document['resume_state']
            if digest(envelope['state']) != envelope['sha256']:
                raise ValueError('request_state_binding')
            external = []
            for event in envelope['state']['history']['events']:
                if event['actor'] not in ('parent', 'environment') or not rendered(event, document['messages']):
                    continue
                external.append({key: event[key] for key in ('event_id', 'actor', 'text', 'source_sha256', 'phase')})
            sleeps = envelope['state'].get('sleep_receipts', [])
            receipt.update(request_digest=digest({key: value for key, value in document.items() if key != 'resume_state'}),
                masked=document['render_receipt']['all_history_tokens_masked'] is True,
                cycle=(sleeps[-1]['cycle'] if sleeps else 0) + 1, external=external)
        elif kind == 'RESPONSE':
            receipt.update(text=document['response']['raw'], request_digest=document['request_sha256'])
        elif kind in ('COMMITTED', 'CONTEXT_COMMITTED', 'R184_STAGE'):
            receipt.update(source_sha256=document.get('source_sha256'), stage=document.get('stage'))
        elif kind == 'INBOX':
            message = document['message']
            receipt.update(event_id=message['actor'] + ':inbox:' + message['id'],
                actor=message['actor'], speaker=message['speaker'], source_sha256=document['source_sha256'])
        elif kind == 'SLEEP_COMPLETE':
            receipt.update(cycle=document['cycle'], status=document['status'],
                checkpoint_sha256=document['checkpoint_sha256'], optimizer_steps=document['total_optimizer_steps'])
        rows.append(receipt)
    return dict(reader_revision=REVISION, journal_id=journal_id, observed_unix=time.time(), head=head, records=rows,
        continuity=continuity, through=previous, caught_up=previous == head,
        coverage_start=continuity[0]['index'] if continuity else None, bytes_read=bytes_read,
        remote_writes=0, signals=0, model_calls=0, readout_or_private_score_files_read=0)


def checkpoint(root, journal_id, record_index):
    root = Path(root)
    record, receipt = verified(root / 'stream/records' / f'{record_index:020d}.json', journal_id)
    document = record['document']
    if record['kind'] != 'SLEEP_COMPLETE' or document['status'] != 'COMPLETE':
        raise ValueError('completed_sleep_only')
    directory = root / 'checkpoints' / f'sleep_{document["cycle"]:06d}'
    raw, _ = read_stable(directory / 'COMMIT.json')
    commit = json.loads(raw)
    if commit['checkpoint_sha256'] != document['checkpoint_sha256'] or commit['optimizer_steps'] != document['total_optimizer_steps']:
        raise ValueError('record_commit_binding')
    if digest(document['resume_state']['state']) != document['resume_state']['sha256']:
        raise ValueError('complete_state_hash')
    files = {}
    for name, expected in commit['adapter_files'].items():
        if Path(name).name != name:
            raise ValueError('adapter_filename_component')
        actual = hashlib.sha256(read_stable(directory / 'adapter' / name)[0]).hexdigest()
        if actual != expected:
            raise ValueError('durable_adapter_hash')
        files['adapter/' + name] = actual
    optimizer = hashlib.sha256(read_stable(directory / 'optimizer_rng.pt', 1024 * 1024 * 1024)[0]).hexdigest()
    if optimizer != commit['checkpoint_sha256']['optimizer'] or optimizer != commit['checkpoint_sha256']['rng']:
        raise ValueError('durable_optimizer_rng_hash')
    if read_stable(directory / 'COMMIT.json')[0] != raw:
        raise ValueError('checkpoint_commit_changed')
    return dict(record=receipt, cycle=document['cycle'], relative_checkpoint=f'checkpoints/sleep_{document["cycle"]:06d}',
        commit_file_sha256=hashlib.sha256(raw).hexdigest(), adapter_state_sha256=commit['adapter_state_sha256'],
        adapter_files=files, optimizer_rng_sha256=optimizer, resume_state_sha256=document['resume_state']['sha256'],
        preservation='Verified durable COMPLETE bytes in place; manifest only, no racing live-state copy.', copied_bytes=0)
