"""Read a bounded, pinned TRAIN journal suffix without acquiring its writer lock."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat


MAX_RECORD = 16 * 1024 * 1024
MAX_TOTAL = 256 * 1024 * 1024


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(document):
    return hashlib.sha256(json.dumps(document, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def read_record(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_size <= MAX_RECORD, 'bounded_regular_record')
        raw = stream.read(MAX_RECORD + 1)
        after = os.fstat(stream.fileno())
    current = os.stat(path, follow_symlinks=False)
    require(len(raw) == before.st_size and len({(item.st_dev, item.st_ino, item.st_size, item.st_mtime_ns)
            for item in (before, after, current)}) == 1, 'record_changed')
    record = json.loads(raw)
    require(record.get('schema') == 'R125_STREAM_JOURNAL_V1' and
            record.get('sha256') == digest({key: value for key, value in record.items() if key != 'sha256'}),
            'record_hash')
    return record, len(raw), before.st_mtime


def trace(root, journal_id, anchor_index, anchor_sha256, inbox_id, maximum_records=4096):
    root = Path(root)
    require(not any(re.search(r'(^|[_ .-])(held|final|sealed|readout)([_ .-]|$)', part, re.I)
                    for part in root.parts), 'TRAIN_root_only')
    require(root.is_dir() and not root.is_symlink(), 'real_life_directory')
    require(type(maximum_records) is int and 1 <= maximum_records <= 4096, 'bounded_record_window')
    directory = root / 'stream' / 'records'
    require(directory.is_dir() and not directory.is_symlink(), 'real_record_directory')
    names = sorted(path for path in directory.iterdir() if re.fullmatch(r'[0-9]{20}\.json', path.name))
    require(len(names) <= 100000 and anchor_index < len(names), 'bounded_existing_anchor')
    require([int(path.stem) for path in names] == list(range(len(names))), 'contiguous_journal')
    rows = names[anchor_index:anchor_index + maximum_records]
    previous = None
    total_bytes = 0
    events = []
    inboxes = {}
    pending = None
    response = None
    exposure = None
    generated_tokens = 0
    guided_responses = 0
    selected_sleep = None
    for path in rows:
        record, size, modified = read_record(path)
        total_bytes += size
        require(total_bytes <= MAX_TOTAL, 'bounded_total_bytes')
        require(record['journal_id'] == journal_id and record['index'] == int(path.stem), 'same_journal_index')
        if previous is None:
            require(record['sha256'] == anchor_sha256, 'external_anchor_hash')
        else:
            require(record['previous_sha256'] == previous, 'linked_record_chain')
        previous = record['sha256']
        kind, document = record['kind'], record['document']
        event = dict(kind=kind, index=record['index'], sha256=previous,
                     file_mtime_observed_unix=modified)
        if kind == 'INBOX':
            message = document['message']
            require(message.get('split') == 'TRAIN', 'TRAIN_inbox')
            inboxes[message['id']] = message
            event.update(inbox_id=message['id'], speaker=message.get('speaker'), text=message['text'],
                         inbox_source_sha256=document['source_sha256'])
        elif kind == 'REQUEST':
            require(pending is None and document.get('split') == 'TRAIN', 'one_TRAIN_request')
            require(document.get('render_receipt', {}).get('all_history_tokens_masked') is True,
                    'rendered_external_text_masked')
            message = inboxes.get(inbox_id)
            visible = bool(message and any(item['role'] == 'user' and item['content'] ==
                           message['speaker'] + ': ' + message['text'] for item in document['messages'][2:]))
            if visible and exposure is None:
                exposure = dict(event, inbox_id=inbox_id, visibility='EXACT_ATTRIBUTED_PLAIN_MESSAGE')
            event.update(segment=document['segment'], bound_guidance_visible=visible,
                         prompt_messages=len(document['messages']))
            pending = dict(index=record['index'], segment=document['segment'],
                           sha256=digest({key: value for key, value in document.items() if key != 'resume_state'}))
        elif kind == 'RESPONSE':
            require(pending is not None and response is None and
                    document['request_sha256'] == pending['sha256'], 'response_request_binding')
            response = document
            event.update(raw=document['response']['raw'], token_count=len(document['response']['token_ids']),
                         finished_unix=document['finished_unix'], request_index=pending['index'])
        elif kind == 'COMMITTED' and document.get('kind') != 'BIRTH':
            require(pending is not None and response is not None and
                    document['source_sha256'] == digest(response) and document['segment'] == pending['segment'],
                    'commit_response_binding')
            if exposure is not None:
                guided_responses += 1
                generated_tokens += len(response['response']['token_ids'])
            event.update(segment=document['segment'], guided_responses=guided_responses,
                         guided_generated_tokens=generated_tokens)
            pending, response = None, None
        elif kind == 'SLEEP_COMPLETE':
            event.update(cycle=document['cycle'], adapter_sha256=document.get('after_adapter_sha256'),
                         total_optimizer_steps=document.get('total_optimizer_steps'),
                         checkpoint_path=document['checkpoint']['adapter_path'])
            if exposure is not None and guided_responses >= 4 and selected_sleep is None:
                selected_sleep = dict(event)
        elif kind in ('CHILD_COMPACTION', 'CONTEXT_RETAINED', 'SLEEP_REQUEST', 'TARGET_ELIGIBILITY'):
            event['document'] = document if kind != 'SLEEP_REQUEST' else {'cycle': document['cycle']}
        else:
            continue
        events.append(event)
    return dict(schema='R175_PINNED_LESSON_TRACE_V1', root=str(root), journal_id=journal_id,
                anchor_index=anchor_index, anchor_sha256=anchor_sha256, head_sha256=previous,
                end_index=int(rows[-1].stem), available_records=len(names), caught_up=len(names) <= anchor_index + maximum_records,
                source_bytes=total_bytes, observed_utc=datetime.now(timezone.utc).isoformat(), events=events,
                first_rendered_guidance=exposure, guided_committed_responses=guided_responses,
                guided_generated_tokens=generated_tokens, first_eligible_completed_sleep=selected_sleep,
                status='AWAITING_GUIDANCE_EXPOSURE' if exposure is None else
                       ('CHECKPOINT_SELECTED' if selected_sleep is not None else 'GUIDED_PHASE'),
                success_claim=False, no_writes_to_life=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    parser.add_argument('--journal-id', required=True)
    parser.add_argument('--anchor-index', type=int, required=True)
    parser.add_argument('--anchor-sha256', required=True)
    parser.add_argument('--inbox-id', required=True)
    arguments = parser.parse_args()
    print(json.dumps(trace(arguments.root, arguments.journal_id, arguments.anchor_index,
                           arguments.anchor_sha256, arguments.inbox_id), sort_keys=True))


if __name__ == '__main__':
    main()
