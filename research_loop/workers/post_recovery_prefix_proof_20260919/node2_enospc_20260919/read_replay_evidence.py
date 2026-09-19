"""Read selected historical receipts and pinned source; never execute research code."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys


LIBRARY_SHA = 'be9564a48d35676538925e80ad0bc7c4511d2a5ef920c0fecdb6c1f492862a21'
EARLIER_SHA = '0981c0861c60a35b492ba0ff717e9a109f2d0cc2e4051b96dd59417b4fd5b2ea'
REMOTE = r'''
import collections, hashlib, json, time
from pathlib import Path
namespace = {'__name__': 'read_only_diagnostic_library'}
exec(compile(LIBRARY, '<pinned_diagnostic_library>', 'exec'), namespace)
load = namespace['load']
read_bytes = namespace['read_bytes']
def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
def record_at(records, index):
    record, raw_sha = load(records / f'{index:020d}.json', 128 * 1024 * 1024)
    if record['index'] != index or digest({key: value for key, value in record.items() if key != 'sha256'}) != record['sha256']:
        raise ValueError('canonical_record_mismatch')
    intent, intent_sha = load(records / f'{index:020d}.intent.json')
    expected = {key: record[key] for key in ('schema', 'journal_id', 'index', 'previous_sha256')}
    expected['record_sha256'] = record['sha256']
    if intent != expected:
        raise ValueError('intent_binding_mismatch')
    return record, dict(index=index, kind=record['kind'], sha256=record['sha256'],
        raw_file_sha256=raw_sha, intent_file_sha256=intent_sha,
        canonical_record_and_intent_verified=True, document_keys=sorted(record['document']))
result = dict(schema='NODE2_SELECTED_REPLAY_WITNESSES_V1', observed_unix=time.time(),
    node_writes=False, native_signals=[], research_source_executed=False,
    checkpoint_binaries_hashed=False, full_journal_verified=False, lives=[])
for earlier in EARLIER:
    guard, guard_sha = load(Path(earlier['guard_path']))
    if guard_sha != earlier['guard_sha256']:
        raise ValueError('guard_changed')
    plan, plan_sha = load(Path(guard['plan_path']))
    if plan_sha != guard['plan_sha256'] or plan_sha != earlier['plan_sha256']:
        raise ValueError('plan_changed')
    records = Path(guard['copy_raw']) / 'stream/records'
    head, head_summary = record_at(records, earlier['head']['index'])
    if head['sha256'] != earlier['head']['sha256']:
        raise ValueError('historical_cutoff_changed')
    headers = earlier['tail_headers']
    for expected in headers:
        current = namespace['header'](records / f"{expected['index']:020d}.json")
        if any(current[key] != expected[key] for key in ('index', 'journal_id', 'kind', 'previous_sha256', 'sha256')):
            raise ValueError('historical_tail_header_changed')
    summary = dict(life=earlier['life'], guard_sha256=guard_sha, plan_sha256=plan_sha,
        source_root=plan['source_root'], raw_root=guard['copy_raw'], head=head_summary,
        scope='selected_bodies_plus_previous_tail_headers_not_full_tail_audit',
        tail_kind_counts=dict(collections.Counter(item['kind'] for item in headers)),
        requests=[], responses=[], updates=[], other_selected=[], sources={})
    requests = {}
    selected_kinds = {'REQUEST', 'RESPONSE', 'GENERATION_PARTIAL', 'GENERATION_ABORTED',
        'SLEEP_RECIPE', 'TARGET_ELIGIBILITY', 'UPDATE'}
    for header in headers:
        if header['kind'] not in selected_kinds:
            continue
        record, item = record_at(records, header['index'])
        document = record['document']
        kind = record['kind']
        if kind == 'REQUEST':
            request = {key: value for key, value in document.items() if key != 'resume_state'}
            request_sha = digest(request)
            saved = document['resume_state']
            if saved['sha256'] != digest(saved['state']) or saved['state']['pending'] != request_sha:
                raise ValueError('request_saved_state_or_pending_mismatch')
            requests[request_sha] = item['index']
            item.update(request_sha256=request_sha, messages_sha256=digest(document['messages']),
                message_count=len(document['messages']), max_new_tokens=document['max_new_tokens'],
                prompt_tokens=document['prompt_tokens'], deadline_unix=document['deadline_unix'],
                model_state_sha256=document['model_state_sha256'], retry_allowed=document['retry_allowed'])
            summary['requests'].append(item)
        elif kind in ('RESPONSE', 'GENERATION_PARTIAL'):
            response = document['response']
            if document['request_sha256'] not in requests:
                raise ValueError('response_without_selected_request')
            item.update(request_index=requests[document['request_sha256']],
                response_keys=sorted(response), response_sha256=digest(response),
                token_count=len(response['token_ids']), token_ids_sha256=digest(response['token_ids']),
                raw_text_sha256=hashlib.sha256(response['raw'].encode()).hexdigest(),
                bindings={key: response[key] for key in ('adapter_state_sha256', 'base_sha256',
                    'decoder', 'prompt_token_ids_sha256', 'terminal', 'truncated') if key in response},
                randomness_fields=[key for key in response if 'rng' in key.lower() or 'random' in key.lower()])
            summary['responses'].append(item)
        elif kind == 'UPDATE':
            item.update(optimizer_step=document['optimizer_step'], source_sha256=document['source_sha256'],
                losses_sha256=digest(document['losses']), loss_entry_keys=sorted({key for loss in document['losses'] for key in loss}),
                loss_count=len(document['losses']), finished_unix=document['finished_unix'])
            summary['updates'].append(item)
        else:
            item['document_sha256'] = digest(document)
            summary['other_selected'].append(item)
    spans = {
        'gpu/orch_r125_continual_native.py': [(350, 391), (416, 464), (470, 501), (599, 647)],
        'organism_v6/orch_r125_continual_stream.py': [(214, 249)],
    }
    for relative, ranges in spans.items():
        raw = read_bytes(Path(plan['source_root']) / relative, 2 * 1024 * 1024)
        source_sha = hashlib.sha256(raw).hexdigest()
        if source_sha != guard['source_pins'][relative]:
            raise ValueError('source_pin_mismatch')
        lines = raw.decode().splitlines()
        summary['sources'][relative] = dict(sha256=source_sha, guard_pin_verified=True,
            excerpts=[dict(start_line=start, end_line=end, text='\n'.join(lines[start-1:end])) for start, end in ranges])
    steps = [item['optimizer_step'] for item in summary['updates']]
    if steps != list(range(steps[0], steps[-1] + 1)):
        raise ValueError('nonconsecutive_update_steps')
    summary['update_document_key_sets'] = sorted({tuple(item['document_keys']) for item in summary['updates']})
    result['lives'].append(summary)
print(json.dumps(result, sort_keys=True))
'''


if __name__ == '__main__':
    if len(sys.argv) != 3 or sys.argv[1] != '--receipt':
        raise SystemExit('use --receipt NEW_LOCAL_PATH')
    directory = Path(__file__).parent
    library = (directory / 'read_only_inspect.py').read_bytes()
    earlier = (directory / 'NODE2_READ_ONLY_20260919.json').read_bytes()
    if hashlib.sha256(library).hexdigest() != LIBRARY_SHA or hashlib.sha256(earlier).hexdigest() != EARLIER_SHA:
        raise ValueError('exact_preserved_evidence_required')
    payload = ('LIBRARY=' + repr(library.decode()) + '\nEARLIER='
        + repr(json.loads(earlier)['report']['lives']) + '\n' + REMOTE).encode()
    completed = subprocess.run(['bash', 'gpu/ovx_ssh.sh', 'python3 -B -'], input=payload,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    receipt = dict(returncode=completed.returncode, stderr=completed.stderr.decode(errors='replace'),
        inspector_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        prior_receipt_sha256=EARLIER_SHA, diagnostic_library_sha256=LIBRARY_SHA,
        remote_payload_sha256=hashlib.sha256(payload).hexdigest(),
        report=json.loads(completed.stdout) if completed.returncode == 0 else None)
    with Path(sys.argv[2]).open('x') as stream:
        json.dump(receipt, stream, sort_keys=True, indent=2)
        stream.write('\n')
    print(json.dumps(dict(path=sys.argv[2], returncode=completed.returncode)))
    raise SystemExit(completed.returncode)
