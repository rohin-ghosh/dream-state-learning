"""Incremental immutable-journal projections; existing reader functions injected."""

import json
from pathlib import Path
import time


WANTED = {'REQUEST', 'RESPONSE', 'COMMITTED', 'INBOX', 'R184_STAGE', 'R184_ACT',
          'R184_TRANSITION', 'SLEEP_REQUEST', 'SLEEP_COMPLETE', 'R205_CONSOLE_REPLY'}


def collect_tail(life, after_index, limit):
    if after_index < 0 or not 1 <= limit <= 256:
        raise ValueError('bounded_tail_required')
    identity = json.loads(read_bytes(life / 'stream/JOURNAL.json', limit=4096)[0])
    directory = life / 'stream/records'
    paths = sorted(directory.glob('[0-9]' * 20 + '.json'))
    anchor = metadata(directory / f'{after_index:020d}.json')
    if anchor['journal_id'] != identity['journal_id']:
        raise ValueError('tail_anchor_journal_mismatch')
    selected = [path for path in paths if int(path.stem) > after_index][:limit]
    previous, continuity, events = anchor, [], []
    for path in selected:
        meta = metadata(path)
        if (meta['index'] != previous['index'] + 1 or meta['previous_sha256'] != previous['sha256']
                or meta['journal_id'] != identity['journal_id']):
            raise ValueError('tail_chain_mismatch')
        previous = meta
        continuity.append(meta)
        if meta['kind'] not in WANTED:
            continue
        if meta['kind'] == 'COMMITTED':
            event = reduced(path, identity['journal_id'], life)
            if event is not None:
                events.append(event)
            continue
        record, receipt = verified(path, identity['journal_id'])
        document = record['document']
        omitted = {}
        for key in ('state', 'resume_state'):
            value = document.get(key)
            if isinstance(value, dict) and 'state' in value and 'sha256' in value:
                if digest(value['state']) != value['sha256']:
                    raise ValueError('tail_state_hash_mismatch')
                omitted[key] = value['sha256']
        projection = {key: value for key, value in document.items() if key not in ('state', 'resume_state')}
        event = dict(receipt, kind=record['kind'], document=projection,
                     envelope_verified=True, omitted_state_sha256=omitted)
        if record['kind'] == 'RESPONSE':
            event['source_sha256'] = digest(document)
        events.append(event)
    return dict(schema='R227_INCREMENTAL_TAIL_V1', observed_unix=time.time(),
                journal_id=identity['journal_id'], anchor=anchor, through=previous,
                remote_head=metadata(paths[-1]), continuity=continuity, events=events,
                remote_writes=False, signals=0, inbox_changes=False, parent_changes=False)


def collect_window(life, start_cycle, max_records):
    if not 2 <= start_cycle <= 10000 or not 1 <= max_records <= 1600:
        raise ValueError('bounded_window_required')
    identity = json.loads(read_bytes(life / 'stream/JOURNAL.json', limit=4096)[0])
    paths = sorted((life / 'stream/records').glob('[0-9]' * 20 + '.json'))
    head = metadata(paths[-1])
    anchor = None
    for path in reversed(paths):
        meta = metadata(path)
        if meta['kind'] != 'SLEEP_COMPLETE':
            continue
        record, receipt = verified(path, identity['journal_id'])
        if record['document']['cycle'] == start_cycle - 1:
            anchor = dict(meta, cycle=start_cycle - 1)
            break
    if anchor is None or head['index'] - anchor['index'] > max_records:
        raise ValueError('bounded_complete_anchor_unavailable')
    cursor = anchor['index']
    events, continuity = [], []
    observed = time.time()
    while cursor < head['index']:
        batch = collect_tail(life, cursor, min(256, head['index'] - cursor))
        if batch['through']['index'] <= cursor:
            raise ValueError('initial_window_did_not_advance')
        events.extend(batch['events'])
        continuity.extend(batch['continuity'])
        cursor = batch['through']['index']
        observed = batch['observed_unix']
    return dict(schema='R227_C2_WORK_EVIDENCE_V1', observed_unix=observed,
                journal_id=identity['journal_id'], start_cycle=start_cycle,
                anchor=anchor, head=head, continuity=continuity, events=events,
                remote_writes=False, signals=0, inbox_changes=False, parent_changes=False)
