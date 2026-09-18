"""Bounded read-only proof of the exact C2 correction's native rendering."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from checkpoint_tail_parent_binding import ROOT, JOURNAL, verify
from deadline_resume import sha, require
from receipt_window import digest, header, read_record


INBOX_ID = 'a0ff9bd81cde4285ba7a7ef6fc7ea682'
PUBLICATION_SHA = 'a27da1804b6e9cc91a4315194132b2ec555632b38b19e92eea519ceb7549cc96'


def rendered(request, message, path):
    document = request['document']
    matches = [dict(message_index=index, role=item['role'],
        content_sha256=hashlib.sha256(item['content'].encode()).hexdigest())
        for index, item in enumerate(document['messages']) if message['text'] in item['content']]
    if not matches:
        return None
    require(all(item['role'] == 'user' for item in matches)
        and document['render_receipt']['all_history_tokens_masked'] is True, 'actual_masked_parent_render')
    events = document['resume_state']['state']['history']['events']
    event = [item for item in events if item['event_id'] == 'parent:inbox:' + INBOX_ID]
    require(len(event) == 1 and event[0]['actor'] == 'parent' and event[0]['source_id'] == str(path)
        and event[0]['source_sha256'] == PUBLICATION_SHA
        and event[0]['text'] == 'Astra: ' + message['text'], 'same_actual_parent_event_not_quote_only')
    return dict(index=request['index'], sha256=request['sha256'], started_unix=document['started_unix'],
        render_receipt=document['render_receipt'], message_matches=matches,
        parent_event_id=event[0]['event_id'], request_digest=digest({key: value for key, value in document.items()
            if key != 'resume_state'}))


def collect():
    operator = Path(__file__).resolve().parent
    binding = operator / 'C2_CHECKPOINT_TAIL_LOADED.json'
    native = verify(binding, sha(binding))
    inbox_path = Path(ROOT) / 'stream/inbox' / (INBOX_ID + '.json')
    require(sha(inbox_path) == PUBLICATION_SHA, 'exact_authorized_parent_publication')
    message = json.loads(inbox_path.read_bytes())
    records = Path(ROOT) / 'stream/records'
    requests, responses, commits, stages = {}, {}, {}, []
    consumed = None
    latest = 11504
    for index in range(11505, 12005):
        path = records / f'{index:020d}.json'
        if not path.exists():
            break
        metadata = header(path)
        require(metadata['index'] == index and metadata['journal_id'] == JOURNAL, 'same_contiguous_post_LOAD_tail')
        latest = index
        if metadata['kind'] not in ('INBOX', 'REQUEST', 'RESPONSE', 'COMMITTED', 'CONTEXT_COMMITTED', 'R184_STAGE'):
            continue
        record = read_record(path, JOURNAL)
        document = record['document']
        reference = dict(index=index, sha256=record['sha256'])
        if record['kind'] == 'INBOX' and document['message']['id'] == INBOX_ID:
            require(document['source_sha256'] == PUBLICATION_SHA and document['message'] == message,
                'same_consumed_parent_bytes')
            consumed = reference
        elif record['kind'] == 'REQUEST':
            receipt = rendered(record, message, inbox_path)
            if receipt:
                requests[receipt['request_digest']] = receipt
        elif record['kind'] == 'RESPONSE' and document['request_sha256'] in requests:
            raw = document['response']['raw']
            responses[digest(document)] = dict(record=reference, request=requests[document['request_sha256']],
                finished_unix=document['finished_unix'], text_sha256=hashlib.sha256(raw.encode()).hexdigest(),
                characters=len(raw), own_text_excerpt=raw[:1800])
        elif record['kind'] in ('COMMITTED', 'CONTEXT_COMMITTED'):
            commits[document.get('source_sha256')] = reference
        elif record['kind'] == 'R184_STAGE':
            source = document['source_sha256']
            if source in responses and source in commits:
                stages.append(dict(stage=document['stage'], stage_record=reference,
                    commit=commits[source], **responses[source]))
    require(not requests or consumed is not None, 'registered_INBOX_precedes_actual_render')
    return dict(schema='R233_C2_SOURCE_GROUNDED_PARENT_RENDER_V1', observed_utc=datetime.now(timezone.utc).isoformat(),
        native=native, inbox_id=INBOX_ID, inbox_sha256=PUBLICATION_SHA, latest_index=latest,
        inbox_receipt=consumed, first_render=next(iter(requests.values()), None), stages=stages,
        first_ACT=next((stage for stage in stages if stage['stage'] == 'ACT'), None),
        native_signals=[], journal_writes=0, unaided_recall_claim=False)


if __name__ == '__main__':
    print(json.dumps(collect(), sort_keys=True, indent=2, ensure_ascii=False))
