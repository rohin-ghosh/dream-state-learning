"""Bounded, read-only parent INBOX to committed ACT evidence."""

import hashlib
import json
from pathlib import Path
import sys
import time


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def collect(root, publication, helper, native_pid, start_ticks):
    sys.path.insert(0, helper)
    from receipt_window import header, read_record
    process = Path('/proc') / str(native_pid)
    actual = (process / 'stat').read_text().rsplit(') ', 1)[1].split()
    if actual[19] != str(start_ticks) or actual[0] in ('Z', 'X'):
        raise ValueError('exact_live_native_required')
    stream = Path(root) / 'stream'
    manifest = json.loads((stream / 'JOURNAL.json').read_bytes())
    path = Path(publication['path'])
    raw = path.read_bytes()
    if path.parent != stream / 'inbox' or hashlib.sha256(raw).hexdigest() != publication['sha256']:
        raise ValueError('exact_parent_publication_bytes')
    message = json.loads(raw)
    paths = sorted((stream / 'records').glob('[0-9]' * 20 + '.json'))[-600:]
    metadata = [(path, header(path)) for path in paths]
    consumed = None
    requests, responses, commits, stages = {}, {}, {}, []
    for path, info in metadata:
        kind = info['kind']
        if kind not in ('INBOX', 'REQUEST', 'RESPONSE', 'COMMITTED', 'CONTEXT_COMMITTED', 'R184_STAGE'):
            continue
        if consumed is None and kind != 'INBOX':
            continue
        record = read_record(path, manifest['journal_id'])
        document = record['document']
        reference = dict(index=record['index'], sha256=record['sha256'])
        if kind == 'INBOX' and document['message']['id'] == message['id']:
            if document['source_sha256'] != publication['sha256'] or document['message'] != message:
                raise ValueError('exact_consumed_parent')
            consumed = reference
        elif kind == 'REQUEST':
            visible = any(message['text'] in item['content'] and item['role'] == 'user'
                for item in document['messages'])
            events = document['resume_state']['state']['history']['events']
            authored = [event for event in events if event['event_id'] == 'parent:inbox:' + message['id']]
            bound = bool(authored) and all(event['actor'] == 'parent'
                and event['source_id'] == publication['path']
                and event['source_sha256'] == publication['sha256'] for event in authored)
            request_sha = digest({key: value for key, value in document.items() if key != 'resume_state'})
            requests[request_sha] = dict(reference, visible=visible, source_bound=bound,
                started_unix=document['started_unix'], render_receipt=document.get('render_receipt'))
        elif kind == 'RESPONSE' and document['request_sha256'] in requests:
            responses[digest(document)] = dict(record=reference, request=requests[document['request_sha256']],
                finished_unix=document['finished_unix'], text_excerpt=document['response']['raw'][:1200])
        elif kind in ('COMMITTED', 'CONTEXT_COMMITTED'):
            commits[document.get('source_sha256')] = reference
        elif kind == 'R184_STAGE':
            source = document['source_sha256']
            if source in responses and source in commits:
                stages.append(dict(stage=document['stage'], stage_record=reference,
                    commit=commits[source], **responses[source]))
    first = next((request for request in requests.values() if request['visible'] and request['source_bound']), None)
    act = next((entry for entry in stages if first and entry['stage'] == 'ACT'
        and entry['request']['index'] >= first['index']), None)
    return dict(observed_unix=time.time(), native=dict(pid=native_pid, start_ticks=start_ticks),
        journal_id=manifest['journal_id'], publication=publication, inbox=consumed,
        first_REQUEST=first, first_committed_ACT=act, latest_index=metadata[-1][1]['index'],
        parent_verbatim_in_ACT=(act['request']['visible'] and act['request']['source_bound']) if act else None,
        native_signals=[], delivery_does_not_prove_uptake=True)
