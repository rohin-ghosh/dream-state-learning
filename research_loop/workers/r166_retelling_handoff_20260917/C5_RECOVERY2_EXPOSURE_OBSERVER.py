import hashlib
import json
from pathlib import Path
import time

root = Path('/localhome/local-rohing/orch_r166_retelling_C5_20260917_recovery2')
records = Path('/localhome/local-rohing/orch_r153_community_C5_20260916_attempt1/life/stream/records')
deadline = time.monotonic() + 300
remaining = 32 * 1024 * 1024
cursor = 2900
pending = {}
committed = []
invocation = None
exposure = None
last_kind = None


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def read(path):
    global remaining
    size = path.stat().st_size
    if size > min(remaining, 16 * 1024 * 1024):
        raise RuntimeError('observer_read_budget_exhausted_no_extension')
    data = path.read_bytes()
    remaining -= len(data)
    return json.loads(data), dict(path=str(path), sha256=hashlib.sha256(data).hexdigest())


policy, policy_ref = read(root / 'control/EFFECTIVE_POLICY.json')
invitation = policy['invitation']
invitation_sha = hashlib.sha256(invitation.encode()).hexdigest()
assert invitation_sha == policy['invitation_sha256'] == 'c3d2e219e024baff2e2bde638d0caa303fb408d89afd8b305deaf4187839d56f'
prior, unused = read(records / '00000000000000002899.json')
previous = prior['sha256']
while True:
    failures = [name for name in ('RECOVERY_FAILED.json', 'attempt/FAILED.json', 'attempt/NATIVE_EXIT.json')
                if (root / name).exists()]
    while (records / ('%020d.json' % cursor)).exists():
        path = records / ('%020d.json' % cursor)
        record, reference = read(path)
        assert record['index'] == cursor and record['previous_sha256'] == previous
        assert record['sha256'] == digest({key: value for key, value in record.items() if key != 'sha256'})
        intent_path = path.with_name(path.stem + '.intent.json')
        intent, intent_ref = read(intent_path)
        assert intent['index'] == cursor and intent['record_sha256'] == record['sha256']
        assert intent['previous_sha256'] == previous
        previous = record['sha256']
        last_kind = record['kind']
        document = record['document']
        if last_kind == 'PRESLEEP_RETELLING_INVITATION':
            assert document['invitation_sha256'] == invitation_sha
            assert document['scope']['root'] == str(records.parent.parent)
            invocation = dict(record=reference, index=cursor, cycle=document['cycle'], invitation_sha256=invitation_sha)
        elif last_kind == 'REQUEST':
            request = {key: value for key, value in document.items() if key != 'resume_state'}
            request_sha = digest(request)
            assert document['split'] == 'TRAIN'
            assert document['resume_state']['state']['pending'] == request_sha
            pending = dict(request=request, request_sha=request_sha, request_ref=reference, request_index=cursor)
            if invocation:
                spans = []
                for index, message in enumerate(document['messages']):
                    content = message.get('content')
                    if isinstance(content, str) and invitation in content:
                        start = content.index(invitation)
                        spans.append(dict(message_index=index, role=message['role'], start=start,
                            end=start+len(invitation), content_sha256=hashlib.sha256(content.encode()).hexdigest()))
                if spans:
                    assert document['render_receipt']['all_history_tokens_masked'] is True
                    exposure = dict(request=reference, request_index=cursor, segment=document['segment'],
                        started_unix=document['started_unix'], request_sha256=request_sha,
                        invocation=invocation, exact_invitation_spans=spans,
                        all_history_tokens_masked=True, semantic_adoption='NOT_ADJUDICATED')
        elif last_kind == 'RESPONSE':
            assert pending and document['request_sha256'] == pending['request_sha']
            pending.update(response=document, response_ref=reference, response_index=cursor)
        elif last_kind == 'COMMITTED':
            assert pending and 'response' in pending
            response = pending['response']
            response_sha = digest(response)
            assert document['source_sha256'] == response_sha
            state = document['state']
            assert state['sha256'] == digest(state['state'])
            row = state['state']['rows'][-1]
            assert row['source_sha256'] == response_sha and row['actor'] == 'child' and row['split'] == 'TRAIN'
            assert row['prefix'] == pending['request']['messages'] and row['target'] == response['response']['raw']
            assert row['token_ids'] == response['response']['token_ids']
            assert row['prefix_loss'] is False and row['target_loss'] is True
            committed.append(dict(request=pending['request_ref'], response=pending['response_ref'],
                committed=reference, request_index=pending['request_index'], response_index=pending['response_index'],
                committed_index=cursor, segment=row['segment'], terminal=row['terminal'], truncated=row['truncated'],
                token_count=len(row['token_ids']), finished_unix=response['finished_unix'],
                response_source_sha256=response_sha, target_sha256=hashlib.sha256(row['target'].encode()).hexdigest(),
                rows=len(state['state']['rows']), sleep_frontier=state['state']['sleep_frontier'],
                sleep_due=document['sleep_due'], no_semantic_correctness_claim=True))
            pending = {}
        cursor += 1
        if exposure:
            break
    proc = Path('/proc/4018497/stat')
    stat = proc.read_text().rsplit(')', 1)[1].split() if proc.exists() else None
    if stat:
        assert stat[19] == '17068304'
    result = dict(observed_unix=time.time(),native_pid=4018497,native_state=stat[0] if stat else None,
        last_record_index=cursor-1,last_kind=last_kind,committed_own_segments=committed,
        pending_request_index=pending.get('request_index'),pending_response_index=pending.get('response_index'),
        policy_receipt=policy_ref,invocation=invocation,exposure=exposure,failures=failures,
        remaining_read_bytes=remaining,read_limit_bytes=32*1024*1024,max_seconds=300,
        no_signals=True,no_parent_action=True,no_restart=True)
    print(json.dumps(result,sort_keys=True),flush=True)
    if exposure or failures or stat is None or time.monotonic() >= deadline:
        break
    time.sleep(min(15,max(0,deadline-time.monotonic())))
