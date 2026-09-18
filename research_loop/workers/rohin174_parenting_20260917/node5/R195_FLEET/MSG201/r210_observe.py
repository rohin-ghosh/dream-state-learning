"""Finite read-only original-C2 homework receipts; no source changes."""

from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time


ROOT = Path('/localhome/local-rohing/orch_r210_C2_20260918_resume2')
LIFE = Path('/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life')
sys.path.insert(0, str(ROOT / 'source'))
from organism_v6.orch_r124_train_history import TrainEvent, TrainHistory
from organism_v6.orch_r125_plain_context import event_message


def main():
    receipts, visible, consumed, replies = [], [], set(), set()
    paths = sorted((LIFE / 'stream/records').glob('[0-9]' * 20 + '.json'))
    parents = {}
    for path in paths[6716:]:
        record = json.loads(path.read_bytes())
        document, kind = record['document'], record['kind']
        receipt = dict(index=record['index'], kind=kind,
            record_sha256=record['sha256'], file_mtime_unix=path.stat().st_mtime)
        for name in ('stage', 'segment', 'cycle', 'pid', 'loaded_unix', 'started_unix',
                'finished_unix', 'render_receipt', 'action_policy'):
            if name in document:
                receipt[name] = document[name]
        if kind == 'INBOX':
            message = document['message']
            receipt.update(inbox_id=message['id'], speaker=message.get('speaker'))
            consumed.add(message['id'])
            if message.get('speaker') in ('Astra', 'Rohin'):
                parents['parent:inbox:' + message['id']] = message.get('speaker')
        if kind == 'REQUEST':
            state = document['resume_state']['state']
            for raw in state['history']['events']:
                if raw['event_id'] not in parents:
                    continue
                event = TrainEvent(**raw)
                rendered = event_message(event) if state.get('presentation') else TrainHistory._message(event)
                if rendered in document['messages']:
                    visible.append(dict(request_index=record['index'], started_unix=document['started_unix'],
                        event_id=event.event_id, speaker=parents[event.event_id],
                        source_sha256=event.source_sha256, exact_rendered=True,
                        all_history_tokens_masked=document['render_receipt']['all_history_tokens_masked']))
        if kind == 'RESPONSE':
            receipt['raw_child_response'] = document['response']['raw']
        if kind.startswith('R210_') or kind in ('R205_CONSOLE_REPLY', 'R195_LEARN_REVIEW', 'TARGET_ELIGIBILITY'):
            receipt['document'] = document
            if kind == 'R205_CONSOLE_REPLY':
                replies.update(item['event_id'].removeprefix('parent:inbox:')
                    for item in document['source_inbox_events'])
        if kind not in ('UPDATE', 'COMMITTED', 'CONTEXT_INPUT', 'R197_CORRECTION_CYCLE'):
            receipts.append(receipt)
    source = LIFE / 'stream/inbox/e540198699ee4ddb9fbfd8b34b72ced3.json'
    now = time.time()
    result = dict(observed_unix=now, observed_at_utc=datetime.now(timezone.utc).isoformat(),
        source=dict(path=str(source), sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            published_file_unix=source.stat().st_mtime, age_seconds=now - source.stat().st_mtime,
            registered=source.stem in consumed, replied=source.stem in replies),
        head=int(paths[-1].stem), receiving_root=str(ROOT), receipts=receipts, visible=visible,
        preserved_boundary=json.loads((ROOT / 'PRESERVED_COMMITTED.json').read_bytes()),
        human_inbox_writes=0, homework_success_not_assumed=True,
        earlier_resident_post_console_sampling_RNG_not_separately_checkpointed=True)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
