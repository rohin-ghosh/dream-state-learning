"""Read original C2's bounded post-release receipts without changing the life."""

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
import time

from organism_v6.orch_r124_train_history import TrainEvent, TrainHistory
from organism_v6.orch_r125_plain_context import event_message


root = Path('/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life')
paths = sorted((root / 'stream/records').glob('[0-9]' * 20 + '.json'))


def request_exposes(request, event):
    """Use the existing R137 exact visible-history and user-message predicate."""
    checkpoint = request['resume_state']['state']
    history = checkpoint['history']
    frontier = history['operations'][-1]['through']['event_count'] if history['operations'] else 0
    if event.actor != 'parent' or event.split != 'TRAIN' or asdict(event) not in history['events'][frontier:]:
        return False
    rendered = event_message(event) if checkpoint.get('presentation') else TrainHistory._message(event)
    return rendered is not None and rendered in request['messages']


def load(index):
    record = json.loads(paths[index].read_bytes())
    assert record['index'] == index
    unsigned = {key: value for key, value in record.items() if key != 'sha256'}
    raw = json.dumps(unsigned, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    assert record['sha256'] == hashlib.sha256(raw).hexdigest()
    return record


catalog = []
for path in paths:
    with path.open('rb') as handle:
        handle.seek(max(0, path.stat().st_size - 4096))
        raw = handle.read()
    catalog.append(json.loads(b'{' + raw[raw.rfind(b',"index":') + 1:]))

registrations = {}
for item in catalog:
    if item['kind'] == 'INBOX':
        record = load(item['index'])
        document = record['document']
        message = document['message']
        registrations[message['id']] = dict(index=record['index'], sha256=record['sha256'],
            speaker=message.get('speaker'), source_sha256=document['source_sha256'])

latest_request = load(max(item['index'] for item in catalog if item['kind'] == 'REQUEST'))
latest_history = latest_request['document']['resume_state']['state']['history']
boundary = load(5851)
old_history = boundary['document']['state']['state']['history']
old_ids = {event['event_id'] for event in old_history['events']}
latest_ids = {event['event_id'] for event in latest_history['events']}
inbox = []
for path in sorted((root / 'stream/inbox').glob('*.json')):
    raw = path.read_bytes()
    message = json.loads(raw)
    identifier = message['id']
    event_id = message['actor'] + ':inbox:' + identifier
    inbox.append(dict(id=identifier, path=str(path), source_sha256=hashlib.sha256(raw).hexdigest(),
        speaker=message.get('speaker'), actor=message['actor'], mtime_unix=path.stat().st_mtime,
        registration=registrations.get(identifier), in_preserved_context_5851=event_id in old_ids,
        in_latest_request_history=event_id in latest_ids,
        text=message['text'] if event_id not in latest_ids else None))

requests, responses, stages, sleeps, exposures = [], [], [], [], []
selected_ids = ('82ffcfbffd454500814e97d57f7c1e9c', 'aa816a964dec4638b00c84619ea97bec',
    '637e4fbb797349aa9b4e9b8d11ad85d8')
for item in catalog[5853:]:
    kind = item['kind']
    if kind not in ('REQUEST', 'RESPONSE', 'R184_STAGE', 'ACT', 'SLEEP_RECIPE', 'SLEEP_COMPLETE'):
        continue
    record = load(item['index'])
    document = record['document']
    reference = dict(index=record['index'], sha256=record['sha256'], kind=kind)
    if kind == 'REQUEST':
        requests.append(dict(**reference, started_unix=document['started_unix'],
            segment=document['segment'], render_receipt=document.get('render_receipt')))
        for event in document['resume_state']['state']['history']['events']:
            identifier = event['event_id'].removeprefix('parent:inbox:')
            if identifier in selected_ids and request_exposes(document, TrainEvent(**event)):
                exposures.append(dict(**reference, inbox_id=identifier,
                    started_unix=document['started_unix'], event_exactly_rendered=True,
                    all_history_tokens_masked=document['render_receipt']['all_history_tokens_masked'],
                    registration=registrations[identifier]))
    elif kind == 'RESPONSE':
        responses.append(dict(**reference, finished_unix=document['finished_unix'],
            request_sha256=document['request_sha256'], response=document['response']))
    elif kind in ('R184_STAGE', 'ACT'):
        stages.append(dict(**reference, document=document))
    else:
        sleeps.append(dict(**reference, document=document))

print(json.dumps(dict(observed_unix=time.time(), life_root=str(root), head=catalog[-1],
    source_context_index=5851, source_context_sha256=boundary['sha256'],
    source_history_events=len(old_history['events']), source_history_exact_prefix_preserved=
    latest_history['events'][:len(old_history['events'])] == old_history['events'],
    loaded=load(5856), requests=requests, responses=responses, stages=stages, sleeps=sleeps,
    parent_exposures=exposures, inbox=inbox,
    pending_inbox=[item for item in inbox if not item['in_latest_request_history']],
    preserved_working_state=old_history.get('working_state'),
    latest_working_state=latest_history.get('working_state'),
    saved_checkpoint_rng_preserved=True, live_console_sampling_RNG_not_separately_checkpointed=True,
    source_or_inbox_modifications=0), ensure_ascii=False, indent=2))
