"""Bounded, read-only TRAIN journal capture for the two existing siblings."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat


TARGETS = {
    'learner': dict(root='/localhome/local-rohing/orch_r231_curriculum_birth_20260918/raw',
        journal_id='038f85cbde5c4abfb749ea4d59da6897', pid=493500, start_ticks='10070880', loaded_index=2466),
    'frozen': dict(root='/localhome/local-rohing/orch_r232_curriculum_frozen_20260918/raw',
        journal_id='30fa18c869b34fd496a2758a4a28e197', pid=471737, start_ticks='9987073', loaded_index=1763),
}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def stable_read(path, maximum=128 * 1024 * 1024):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(descriptor, 'rb') as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size > maximum:
            raise ValueError('bounded_regular_file')
        raw = stream.read()
        after = os.fstat(stream.fileno())
    if (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
        raise ValueError('file_changed_during_read')
    return raw, before


def metadata(path):
    with path.open('rb') as stream:
        stream.seek(max(0, path.stat().st_size - 4096))
        ending = stream.read()
    offset = ending.rfind(b',"index":')
    document = json.loads(b'{' + ending[offset + 1:]) if offset >= 0 else json.loads(stable_read(path)[0])
    return {key: document[key] for key in ('index', 'kind', 'sha256', 'previous_sha256', 'journal_id')}


def verified(path, journal):
    raw, information = stable_read(path)
    record = json.loads(raw)
    if record['journal_id'] != journal or record['index'] != int(path.stem):
        raise ValueError('exact_journal_record_identity')
    if record['sha256'] != digest({key: value for key, value in record.items() if key != 'sha256'}):
        raise ValueError('canonical_record_hash')
    return record, len(raw), information.st_mtime


def message_match(event, message):
    if message.get('role') != 'user' or not isinstance(message.get('content'), str):
        return False
    content = message['content']
    if content == event['text']:
        return True
    parts = content.split('\n', 2)
    headers = {'parent': 'Parent advice (not an observed fact)', 'environment': 'Recorded environment observation'}
    if len(parts) != 3 or parts[0] != headers.get(event['actor']) or parts[2] != event['text']:
        return False
    try:
        attributes = json.loads(parts[1])
    except json.JSONDecodeError:
        return False
    return all(attributes.get(key) == event.get(key) for key in
        ('actor', 'event_id', 'source_id', 'source_sha256', 'split'))


def process(target):
    location = Path('/proc') / str(target['pid'])
    fields = (location / 'stat').read_text().rsplit(') ', 1)[1].split()
    argv = (location / 'cmdline').read_bytes().decode().strip('\0').split('\0')
    if fields[19] != target['start_ticks'] or 'gpu.r232_recovery' not in argv or '--config' not in argv:
        raise ValueError('exact_current_native_identity')
    guard_path = Path(argv[argv.index('--config') + 1])
    raw, unused = stable_read(guard_path)
    return dict(pid=target['pid'], start_ticks=fields[19], process_state=fields[0], argv=argv,
        cwd=str(location.joinpath('cwd').resolve()), guard_path=str(guard_path),
        guard_sha256=hashlib.sha256(raw).hexdigest())


def project(record, mtime):
    document = record['document']
    row = dict(index=record['index'], kind=record['kind'], sha256=record['sha256'],
        previous_sha256=record['previous_sha256'], document_sha256=digest(document), file_mtime_unix=mtime)
    kind = record['kind']
    if kind == 'REQUEST':
        if document.get('split') != 'TRAIN':
            raise ValueError('TRAIN_requests_only')
        envelope = document['resume_state']
        if digest(envelope['state']) != envelope['sha256']:
            raise ValueError('request_resume_state_hash')
        external = []
        for event in envelope['state']['history']['events']:
            if event['actor'] not in ('parent', 'environment'):
                continue
            matches = [position for position, message in enumerate(document['messages']) if message_match(event, message)]
            external.append(dict(event, rendered_message_indices=matches))
        sleeps = envelope['state'].get('sleep_receipts', [])
        row.update(request_digest=digest({key: value for key, value in document.items() if key != 'resume_state'}),
            started_unix=document['started_unix'], cycle=(sleeps[-1]['cycle'] if sleeps else 0) + 1,
            masked=document['render_receipt']['all_history_tokens_masked'] is True,
            external=external, messages=document['messages'], resume_state_sha256=envelope['sha256'])
    elif kind == 'RESPONSE':
        row.update(text=document['response']['raw'], request_digest=document['request_sha256'],
            finished_unix=document['finished_unix'])
    elif kind in ('COMMITTED', 'CONTEXT_COMMITTED', 'R184_STAGE'):
        row.update(source_sha256=document.get('source_sha256'), stage=document.get('stage'))
    elif kind == 'INBOX':
        message = document['message']
        row.update(event_id=message['actor'] + ':inbox:' + message['id'], actor=message['actor'],
            speaker=message['speaker'], text=message['text'], source_id=document['source_id'],
            source_sha256=document['source_sha256'])
    elif kind == 'SLEEP_COMPLETE':
        row.update(cycle=document['cycle'], status=document['status'], checkpoint=document['checkpoint'],
            checkpoint_sha256=document['checkpoint_sha256'], optimizer_steps=document['total_optimizer_steps'],
            resume_state_sha256=document['resume_state']['sha256'],
            adapter_state_sha256=document.get('after_adapter_sha256'))
    elif kind in ('R184_ACT', 'R189_OUTCOME_CYCLE', 'SLEEP_RECIPE', 'TARGET_ELIGIBILITY', 'LOADED', 'WALL_EXTENDED'):
        row['document'] = {key: value for key, value in document.items() if key not in ('state', 'resume_state')}
    return row


def collect(label, maximum_records=750, maximum_bytes=1024 * 1024 * 1024, cut_index=None, cut_sha256=None):
    target = TARGETS[label]
    actual = process(target)
    root = Path(target['root'])
    journal = json.loads(stable_read(root / 'stream/JOURNAL.json', 4096)[0])
    if journal['journal_id'] != target['journal_id']:
        raise ValueError('same_original_pair_journal')
    files = sorted((root / 'stream/records').glob('[0-9]' * 20 + '.json'))
    if (cut_index is None) != (cut_sha256 is None):
        raise ValueError('both_fixed_cut_index_and_hash_required')
    if cut_index is not None:
        files = [path for path in files if int(path.stem) <= cut_index]
    head = metadata(files[-1])
    if cut_index is not None and (head['index'] != cut_index or head['sha256'] != cut_sha256):
        raise ValueError('exact_reproduction_cut')
    complete_indices = []
    for path in reversed(files[-maximum_records:]):
        meta = metadata(path)
        if meta['kind'] == 'SLEEP_COMPLETE':
            complete_indices.append(meta['index'])
            if len(complete_indices) == 4:
                break
    if len(complete_indices) != 4:
        raise ValueError('four_anchors_required_for_three_complete_windows')
    anchor_index = complete_indices[-1]
    selected = [path for path in files if anchor_index <= int(path.stem) <= head['index']]
    previous, rows, total = None, [], 0
    for path in selected:
        if total + path.stat().st_size > maximum_bytes:
            raise ValueError('bounded_read_budget_incomplete_no_absence_claim')
        record, size, mtime = verified(path, target['journal_id'])
        total += size
        if previous and (record['index'] != previous['index'] + 1 or record['previous_sha256'] != previous['sha256']):
            raise ValueError('contiguous_verified_window')
        rows.append(project(record, mtime))
        previous = record
    loaded, unused, mtime = verified(root / 'stream/records' / f'{target["loaded_index"]:020d}.json', target['journal_id'])
    if loaded['kind'] != 'LOADED' or loaded['document']['pid'] != target['pid']:
        raise ValueError('actual_current_LOADED_binding')
    after = process(target)
    if (after['pid'], after['start_ticks'], after['guard_sha256']) != (actual['pid'], actual['start_ticks'], actual['guard_sha256']):
        raise ValueError('native_changed_during_capture')
    if metadata(files[-1]) != head:
        raise ValueError('pinned_cut_changed')
    parent_sources = {}
    for row in rows:
        for event in row.get('external', []):
            if event['actor'] != 'parent' or not event['rendered_message_indices']:
                continue
            source_path = Path(event['source_id'])
            if source_path.parent != root / 'stream/inbox' or source_path.suffix != '.json':
                raise ValueError('only_same_life_parent_backing_inbox')
            if event['source_sha256'] in parent_sources:
                continue
            raw, unused = stable_read(source_path, 1024 * 1024)
            message = json.loads(raw)
            if (hashlib.sha256(raw).hexdigest() != event['source_sha256'] or message['actor'] != 'parent'
                    or message['speaker'] + ': ' + message['text'] != event['text']):
                raise ValueError('parent_backing_source_hash_and_speaker')
            parent_sources[event['source_sha256']] = dict(inbox_id=message['id'], speaker=message['speaker'],
                source_sha256=event['source_sha256'], event_id=event['event_id'],
                backing_file_verified=True)
    return dict(schema='POST_RECOVERY_PAIR_TRAIN_CUT_V1', label=label,
        observed_utc=datetime.now(timezone.utc).isoformat(), target=target, native=actual,
        loaded=project(loaded, mtime), initial_head=head, anchor_index=anchor_index,
        complete_indices=sorted(complete_indices), window_complete=True, bytes_read=total,
        records=rows, parent_sources=parent_sources, native_at_end=after, remote_writes=0, process_signals=0, GPU_calls=0,
        model_calls=0, readout_files_read=0, private_judge_files_read=0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('label', choices=TARGETS)
    parser.add_argument('--cut-index', type=int)
    parser.add_argument('--cut-sha256')
    options = parser.parse_args()
    print(json.dumps(collect(options.label, cut_index=options.cut_index, cut_sha256=options.cut_sha256), sort_keys=True, ensure_ascii=False))
