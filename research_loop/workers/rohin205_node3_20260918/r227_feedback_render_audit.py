"""Read-only audit of actual caption REQUEST messages, never resume metadata."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import time


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
        allow_nan=False).encode()).hexdigest()


def objects(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from objects(child)


def inspect_messages(messages, receipt_ids, results):
    findings = []
    for index, message in enumerate(messages):
        content = message['content']
        if not isinstance(content, str):
            raise ValueError('actual_string_message_required')
        row = dict(message_index=index, role=message['role'],
            content_sha256=hashlib.sha256(content.encode()).hexdigest(),
            characters=len(content),
            rank_fields=re.findall(r'(?i)["\']?\brank["\']?\s*[:=]\s*\d+', content),
            numeric_rank_text=re.findall(r'(?i)\brank(?:ed|ing)?\s*(?:is|of|#|:|=)?\s*\d+', content),
            rank_fraction_text=re.findall(r'\b\d+\s*/\s*65\b', content),
            accepted_boolean_fields=re.findall(
                r'(?i)["\']?\baccepted["\']?\s*[:=]\s*(?:true|false)', content),
            new_pixel_marker='new_pixel' in content,
            receipt_ids_present=[value for value in receipt_ids if value in content],
            submission_ids_present=[result['submission_id'] for result in results
                if result.get('submission_id') and result['submission_id'] in content],
            pixel_ids_present=sorted({result['pixel_id'] for result in results
                if result.get('pixel_id') and result['pixel_id'] in content}),
            aggregate_observations=[], source_bound_result_objects=[])
        beginning = content.find('{')
        if beginning >= 0:
            try:
                decoded, _end = json.JSONDecoder().raw_decode(content[beginning:])
            except ValueError:
                decoded = None
            for item in objects(decoded):
                if item.get('schema') == 'R189_OUTCOME_ALLOCATION_V1' and 'observation' in item:
                    row['aggregate_observations'].append(item['observation'])
                for result in results:
                    if (item.get('submission_id') == result.get('submission_id')
                            and result.get('submission_id')
                            and all(item.get(key) == result.get(key)
                                for key in ('rank', 'accepted', 'status', 'pixel_id'))):
                        row['source_bound_result_objects'].append(result['submission_id'])
        findings.append(row)
    return dict(messages_sha256=digest(messages), message_count=len(messages), findings=findings)


def reference(record):
    return dict(index=record['index'], record_sha256=record['sha256'],
        journal_id=record['journal_id'], kind=record['kind'])


def collect(root):
    sys.path.insert(0, str(root))
    from r209_node3_audit import metadata, read_record

    cut = time.time()
    rows = []
    for physical, treatment in ((0, 'observation'), (3, 'perspective'), (5, 'revision'),
            (6, 'selfderive'), (7, 'unparented')):
        life = 'r213_r226_caption_' + treatment + '_fork'
        arm = root / life
        active = json.loads((arm / 'ACTIVE_RUNTIME.json').read_bytes())
        sys.path.insert(0, active['source'])
        from gpu.ny_caption_life import _child_stage

        paths = sorted(path for path in (arm / 'raw/stream/records').glob('[0-9]' * 20 + '.json')
            if path.stat().st_mtime <= cut)
        if len(paths) > 4096:
            raise ValueError('bounded_4096_records')
        kinds = {int(path.stem): metadata(path) for path in paths}
        load = read_record(next(path for path in paths if kinds[int(path.stem)] == 'LOADED'))
        acts = []
        for path in paths:
            if kinds[int(path.stem)] != 'R184_ACT':
                continue
            record = read_record(path)
            document = record['document']
            environment = document['outcome'].get('environment', {})
            receipt = environment.get('receipt_sha256')
            if not receipt:
                continue
            origin = document['origin']
            if environment.get('origin') != origin:
                raise ValueError('same_actual_origin_required')
            _child_stage(arm / 'raw', origin, 'ACT')
            transport = environment['source_transport']
            if (transport.get('journal_id') != record['journal_id']
                    or transport.get('authenticated_operator_transport') is not True
                    or transport.get('child_network_access') is not False):
                raise ValueError('authenticated_same_journal_transport_required')
            results = [{key: feedback['result'].get(key) for key in ('submission_id',
                'rank', 'accepted', 'status', 'pixel_id', 'ok', 'replayed')}
                for feedback in environment.get('report', {}).get('feedback', [])]
            acts.append(dict(ACT=reference(record), origin=origin,
                scorer_receipt_sha256=receipt, results=results,
                actual_RESPONSE_COMMITTED_ACT_chain_verified=True))
        requests = []
        for path in paths:
            if kinds[int(path.stem)] != 'REQUEST' or not acts or int(path.stem) <= acts[0]['ACT']['index']:
                continue
            record = read_record(path)
            prior = [act for act in acts if act['ACT']['index'] < record['index']]
            if record['journal_id'] != load['journal_id']:
                raise ValueError('same_life_request_required')
            document = record['document']
            inspection = inspect_messages(document['messages'],
                [act['scorer_receipt_sha256'] for act in prior],
                [result for act in prior for result in act['results']])
            requests.append(dict(REQUEST=reference(record),
                started_utc=datetime.fromtimestamp(document['started_unix'], timezone.utc).isoformat(),
                after_ACT_ids=[act['ACT']['index'] for act in prior],
                all_history_tokens_masked=document['render_receipt']['all_history_tokens_masked'],
                **inspection))
        if len(requests) > 128:
            raise ValueError('bounded_128_requests')
        for act in acts:
            act['next_REQUEST_index'] = next((request['REQUEST']['index'] for request in requests
                if request['REQUEST']['index'] > act['ACT']['index']), None)
        rows.append(dict(node_alias='node3', physical_gpu=physical, life=life, treatment=treatment,
            LOAD=reference(load), authentic_scorer_ACTs=acts, actual_REQUESTs=requests,
            scored_ACT_ids=[act['ACT']['index'] for act in acts if act['results']]))
    return dict(schema='R227_ACTUAL_REQUEST_FEEDBACK_AUDIT_V1',
        cut_utc=datetime.fromtimestamp(cut, timezone.utc).isoformat(), rows=rows,
        inspected_field='document.messages[].content', inspected_resume_metadata_as_feedback=False,
        learner_changed=False, scorer_called=False, messages_sent=False)


if __name__ == '__main__':
    print(json.dumps(collect(Path(sys.argv[1])), sort_keys=True, indent=2))
