"""One bounded read of the first post-correction ACT and its actual context."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, '/localhome/local-rohing/orch_r233_C2_checkpoint_tail_20260918/parent_operator')
from checkpoint_tail_parent_binding import ROOT, JOURNAL, verify
from receipt_window import digest, read_record


OPERATOR = Path('/localhome/local-rohing/orch_r233_C2_checkpoint_tail_20260918/parent_operator')
PROVIDER_ID = 'ba0791dafdc7449d8e472b04565a65cb'
PROVIDER_SHA = 'c857694af7de5defdeb49f622b5c7b24ef2f670240fe0e0a9394ee27f0b8f125'
ORIGINAL_ID = 'a0ff9bd81cde4285ba7a7ef6fc7ea682'


def collect():
    native = verify(OPERATOR / 'C2_CHECKPOINT_TAIL_LOADED.json',
        'a7dc874936befcf29258597c8423dea2cd3be929d56bc00bb27f8c0d4220a757')
    records = Path(ROOT) / 'stream/records'
    request = read_record(records / f'{11633:020d}.json', JOURNAL)
    response = read_record(records / f'{11635:020d}.json', JOURNAL)
    compaction = read_record(records / f'{11632:020d}.json', JOURNAL)
    transition = read_record(records / f'{11629:020d}.json', JOURNAL)
    document = request['document']
    request_digest = digest({key: value for key, value in document.items() if key != 'resume_state'})
    if (request['kind'] != 'REQUEST' or response['kind'] != 'RESPONSE'
            or response['document']['request_sha256'] != request_digest
            or compaction['kind'] != 'COMPACTION' or transition['kind'] != 'R184_TRANSITION'):
        raise ValueError('exact_request_response_and_transition_compaction')
    provider_path = Path(ROOT) / 'stream/inbox' / (PROVIDER_ID + '.json')
    if hashlib.sha256(provider_path.read_bytes()).hexdigest() != PROVIDER_SHA:
        raise ValueError('actual_provider_publication_pin')
    provider = json.loads(provider_path.read_bytes())
    events = document['resume_state']['state']['history']['events']
    matching = [event for event in events if event['event_id'] == 'parent:inbox:' + PROVIDER_ID]
    if (len(matching) != 1 or matching[0]['actor'] != 'parent'
            or matching[0]['source_id'] != str(provider_path) or matching[0]['source_sha256'] != PROVIDER_SHA
            or matching[0]['text'] != 'Astra: ' + provider['text']):
        raise ValueError('actual_attributed_provider_event')
    matches = [dict(message_index=index, role=item['role'],
        content_sha256=hashlib.sha256(item['content'].encode()).hexdigest())
        for index, item in enumerate(document['messages']) if provider['text'] in item['content']]
    if not matches or any(item['role'] != 'user' for item in matches) or not document['render_receipt']['all_history_tokens_masked']:
        raise ValueError('exact_masked_provider_render')
    original = json.loads((Path(ROOT) / 'stream/inbox' / (ORIGINAL_ID + '.json')).read_bytes())
    response_digest = digest(response['document'])
    commit, stage = None, None
    latest = 11635
    for index in range(11636, 11650):
        path = records / f'{index:020d}.json'
        if not path.exists():
            break
        record = read_record(path, JOURNAL)
        latest = index
        if record['document'].get('source_sha256') != response_digest:
            continue
        if record['kind'] in ('COMMITTED', 'CONTEXT_COMMITTED'):
            commit = dict(index=index, sha256=record['sha256'])
        if record['kind'] == 'R184_STAGE' and record['document']['stage'] == 'ACT':
            stage = dict(index=index, sha256=record['sha256'])
    raw = response['document']['response']['raw']
    return dict(schema='R233_C2_FIRST_SUBSEQUENT_ACT_CUT_V1', observed_utc=datetime.now(timezone.utc).isoformat(),
        status='COMMITTED_ACT_VERIFIED' if commit and stage else 'RESPONSE_PRESENT_COMMIT_OR_STAGE_PENDING',
        latest_index=latest, native=native,
        compaction=dict(index=compaction['index'], sha256=compaction['sha256']),
        transition=dict(index=transition['index'], sha256=transition['sha256']),
        original_correction_verbatim_in_ACT_request=any(original['text'] in item['content'] for item in document['messages']),
        provider_correction_verbatim_in_ACT_request=True, provider_inbox_id=PROVIDER_ID,
        provider_inbox_sha256=PROVIDER_SHA,
        first_ACT=dict(stage='ACT' if stage else None, record=dict(index=response['index'], sha256=response['sha256']),
            commit=commit, stage_record=stage, finished_unix=response['document']['finished_unix'],
            characters=len(raw), text_sha256=hashlib.sha256(raw.encode()).hexdigest(), own_text_excerpt=raw,
            request=dict(index=request['index'], sha256=request['sha256'], request_digest=request_digest,
                started_unix=document['started_unix'], render_receipt=document['render_receipt'],
                provider_message_matches=matches)), native_signals=[], journal_writes=0,
        proof_basis='original correction rendered to THINK; first subsequent ACT rendered authenticated provider follow-up after compaction')


if __name__ == '__main__':
    print(json.dumps(collect(), sort_keys=True, indent=2, ensure_ascii=False))
