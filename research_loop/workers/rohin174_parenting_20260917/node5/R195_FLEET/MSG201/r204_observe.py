"""Bounded read-only C2 receipts; publication, rendering, and reply stay distinct."""

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, '/localhome/local-rohing/orch_r204_C2_20260918_resume1/source')
from organism_v6.orch_r124_train_history import TrainEvent, TrainHistory
from organism_v6.orch_r125_plain_context import event_message


ROOT = Path('/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life')
WALKTHROUGH = 'cbd12ed5973b4c0dba5004b31ac814cd'
paths = sorted((ROOT / 'stream/records').glob('[0-9]' * 20 + '.json'))
catalog, registrations = [], {}
receipts, exposures = [], []
latest_history_ids = set()
for path in paths:
    with path.open('rb') as handle:
        handle.seek(max(0, path.stat().st_size - 4096))
        raw = handle.read()
    item = json.loads(b'{' + raw[raw.rfind(b',"index":') + 1:])
    catalog.append(item)
    if item['kind'] == 'INBOX':
        record = json.loads(path.read_bytes())
        registrations[record['document']['message']['id']] = item
    if item['index'] < 5976:
        continue
    if item['kind'] not in ('LOADED', 'REQUEST', 'RESPONSE', 'SLEEP_REQUEST', 'SLEEP_RECIPE',
            'SLEEP_COMPLETE', 'INBOX', 'R184_STAGE') and 'COMPACT' not in item['kind']:
        continue
    record = json.loads(path.read_bytes())
    document = record['document']
    summary = dict(index=record['index'], kind=record['kind'], sha256=record['sha256'])
    for name in ('loaded_unix', 'started_unix', 'finished_unix', 'observed_unix', 'cycle',
            'segment', 'stage', 'optimizer_steps', 'render_receipt', 'request_sha256'):
        if name in document:
            summary[name] = document[name]
    if item['kind'] == 'RESPONSE':
        summary['raw_child_text'] = document['response']['raw']
    if item['kind'] == 'INBOX':
        summary['message'] = document['message']
    if item['kind'] == 'SLEEP_COMPLETE':
        summary['checkpoint_optimizer_steps'] = document['checkpoint']['optimizer_steps']
    if item['kind'] == 'REQUEST':
        state = document['resume_state']['state']
        history = state['history']
        latest_history_ids = {event['event_id'] for event in history['events']}
        frontier = history['operations'][-1]['through']['event_count'] if history['operations'] else 0
        for raw_event in history['events'][frontier:]:
            if raw_event['event_id'] != 'parent:inbox:' + WALKTHROUGH:
                continue
            event = TrainEvent(**raw_event)
            rendered = event_message(event) if state.get('presentation') else TrainHistory._message(event)
            if rendered in document['messages'] and asdict(event) in history['events'][frontier:]:
                exposures.append(dict(request_index=item['index'], request_sha256=record['sha256'],
                    started_unix=document['started_unix'], inbox_id=WALKTHROUGH,
                    exact_visible_event_and_message=True, render_receipt=document['render_receipt']))
    receipts.append(summary)
pending_registration, pending_history = [], []
for path in sorted((ROOT / 'stream/inbox').glob('*.json')):
    raw = path.read_bytes()
    message = json.loads(raw)
    entry = dict(id=message['id'], actor=message['actor'], speaker=message.get('speaker'),
        source_sha256=hashlib.sha256(raw).hexdigest(), mtime_unix=path.stat().st_mtime)
    if message['id'] not in registrations:
        pending_registration.append(entry)
    if message['actor'] + ':inbox:' + message['id'] not in latest_history_ids:
        pending_history.append(entry)
print(json.dumps(dict(observed_unix=time.time(), life_root=str(ROOT), head=catalog[-1],
    receipts=receipts, walkthrough_exposures=exposures,
    pending_unregistered=pending_registration, pending_latest_request_history=pending_history,
    original_inbox_writes=0, Fable_owns_Rohin_retry=True), indent=2))
