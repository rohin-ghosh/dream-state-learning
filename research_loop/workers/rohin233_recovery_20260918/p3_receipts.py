"""Attribute recovered parent publications to verified P3 REQUEST and ACT records."""

from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
WORKERS = HERE.parent
PARENT = WORKERS / 'rohin174_parenting_20260917/node4/R195_FLEET/r210_parent3/turns'
EVIDENCE = WORKERS / 'rohin233_focus_20260918/private/GAME1_P3/EVIDENCE.json'


def utc(timestamp):
    return datetime.fromtimestamp(timestamp, timezone.utc).isoformat()


def correlate(publication, evidence, frames):
    event_id = 'parent:inbox:' + publication['id']
    requests = [row for row in evidence['records'] if row['kind'] == 'REQUEST'
        and any(event['event_id'] == event_id for event in row['external'])]
    if not requests:
        return dict(status='PUBLISHED_RENDER_NOT_YET_IN_AUDIT')
    request = min(requests, key=lambda row: row['index'])
    candidates = [frame for frame in frames if frame['stage'] == 'ACT'
                  and frame['request']['index'] >= request['index']]
    result = dict(status='RENDERED_ACT_PENDING', request_index=request['index'],
                  request_sha256=request['sha256'], request_utc=utc(request['time_unix']),
                  all_history_tokens_masked=request['masked'])
    if candidates:
        act = min(candidates, key=lambda frame: frame['request']['index'])
        response = act['response']
        result.update(status='REQUEST_TO_ACT_OBSERVED', act_request_index=act['request']['index'],
                      act_index=response['index'], act_sha256=response['sha256'],
                      act_utc=utc(response['time_unix']),
                      act_text_sha256=hashlib.sha256(response['text'].encode()).hexdigest(),
                      act_excerpt=response['text'][:500],
                      success_claim='NONE_ARTIFACT_REQUIRES_REVIEW')
    return result


def main():
    specification = importlib.util.spec_from_file_location('correction_receipts',
        WORKERS / 'rohin232_correction_audit_20260918/audit.py')
    correction = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(correction)
    evidence = json.loads(EVIDENCE.read_text())
    frames = correction.frames(evidence)
    rows = []
    for path in sorted(PARENT.glob('parent_*/RESULT.json')):
        if int(path.parent.name.split('_')[-1]) < 292:
            continue
        result = json.loads(path.read_text())
        if result.get('status') != 'PUBLISHED':
            rows.append(dict(attempt=path.parent.name, status=result.get('status'),
                             publication=False))
            continue
        publication = result['publication']
        rows.append(dict(attempt=path.parent.name, inbox_id=publication['id'],
            inbox_sha256=publication['sha256'], parent_message=result['message'],
            result_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            **correlate(publication, evidence, frames)))
    output = dict(observed_utc=datetime.now(timezone.utc).isoformat(),
                  journal_id=evidence['journal_id'], audit_through=evidence['through'],
                  audit_caught_up=evidence['caught_up'], learner_signals=[],
                  rows=rows, scientific_retention_claim=False)
    temporary = HERE / 'P3_REQUEST_ACT.next'
    temporary.write_text(json.dumps(output, sort_keys=True, indent=2) + '\n')
    temporary.replace(HERE / 'P3_REQUEST_ACT.json')
    print(json.dumps(output, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
