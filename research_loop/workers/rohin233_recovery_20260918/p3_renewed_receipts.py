"""Read a bounded post-LOAD window and prove P3 parent/Tool delivery."""

from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import shlex
import subprocess

import p3_receipts


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
AUDIT = HERE.parent / 'rohin232_correction_audit_20260918'
ROOT = '/localhome/local-rohing/orch_r201_node4_20260918/node4/R195_FLEET/SCALE_physical3/life'
TOOL = dict(id='04a8952f5a84794f257f24e1765489d7',
    sha256='f55867bbf14afe8bc01089abb6f1780f9128832daaf6c9ee0547392692938dd2')


def proof(publication, actor, evidence, frames, loaded):
    if evidence['journal_id'] != loaded['original_journal_id']:
        raise ValueError('same_restored_P3_journal_required')
    if any(row['index'] <= loaded['loaded']['index'] for row in evidence['records']):
        raise ValueError('post_LOAD_window_required')
    event_id = actor + ':inbox:' + publication['id']
    requests = [row for row in evidence['records'] if row['kind'] == 'REQUEST' and any(
        event['event_id'] == event_id and event['source_sha256'] == publication['sha256']
        for event in row['external'])]
    result = dict(inbox_id=publication['id'], inbox_sha256=publication['sha256'], actor=actor,
        status='PUBLISHED_NOT_YET_RENDERED_IN_WINDOW', uptake_or_quality_claim=False)
    if not requests:
        return result
    request = min(requests, key=lambda row: row['index'])
    if request['masked'] is not True:
        raise ValueError('external_history_must_remain_masked')
    result.update(status='RENDERED_ACT_PENDING', request_index=request['index'],
        request_sha256=request['sha256'], request_utc=p3_receipts.utc(request['time_unix']))
    acts = [frame for frame in frames if frame['stage'] == 'ACT'
        and frame['request']['index'] >= request['index']]
    if acts:
        frame = min(acts, key=lambda item: item['request']['index'])
        result.update(status='REQUEST_TO_COMMITTED_ACT_OBSERVED',
            act_request_index=frame['request']['index'], act_index=frame['response']['index'],
            act_sha256=frame['response']['sha256'], committed_index=frame['commit']['index'],
            stage_index=frame['stage_receipt']['index'],
            act_utc=p3_receipts.utc(frame['response']['time_unix']),
            act_text_sha256=hashlib.sha256(frame['response']['text'].encode()).hexdigest())
    return result


def main():
    loaded = json.loads((HERE / 'P3_CONTINUED_LOADED.json').read_bytes())
    reader_path = AUDIT / 'reader.py'
    code = reader_path.read_text() + '\nprint(json.dumps(collect(' + repr(ROOT) + ', ' + repr(
        loaded['original_journal_id']) + ', maximum=180, after=' + str(loaded['loaded']['index']) + ')))\n'
    result = subprocess.run(['bash', str(REPO / 'gpu/a40r_ssh.sh'), 'python3 -u -c ' + shlex.quote(code)],
        capture_output=True, text=True, check=True, timeout=120)
    evidence = json.loads(result.stdout)
    continuity = evidence['continuity']
    if continuity and (continuity[0]['index'] != loaded['loaded']['index'] + 1
            or continuity[0]['previous_sha256'] != loaded['loaded']['sha256']):
        raise ValueError('window_must_follow_exact_LOAD_anchor')
    specification = importlib.util.spec_from_file_location('p3_renewed_audit', AUDIT / 'audit.py')
    audit = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(audit)
    frames = audit.frames(evidence)
    parents = []
    for path in sorted(p3_receipts.PARENT.glob('parent_*/RESULT.json'), reverse=True):
        row = json.loads(path.read_bytes())
        if row.get('status') == 'PUBLISHED':
            parents.append(dict(attempt=path.parent.name,
                result_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                **proof(row['publication'], 'parent', evidence, frames, loaded)))
        if len(parents) == 3:
            break
    stamp = datetime.now(timezone.utc).strftime('%H%M%S')
    report = dict(observed_utc=datetime.now(timezone.utc).isoformat(),
        journal_id=evidence['journal_id'], loaded_index=loaded['loaded']['index'],
        loaded_sha256=loaded['loaded']['sha256'], through=evidence['through'], caught_up=evidence['caught_up'],
        reader_sha256=hashlib.sha256(reader_path.read_bytes()).hexdigest(),
        bounded_bytes_read=evidence['bytes_read'], parent_turns=parents,
        retrospective_tool=proof(TOOL, 'environment', evidence, frames, loaded),
        remote_writes=0, native_signals=[], raw_child_or_parent_text_exported_in_public_receipt=False)
    (HERE / f'P3_POST_LOAD_{stamp}.private.json').write_text(json.dumps(evidence, sort_keys=True) + '\n')
    path = HERE / f'P3_POST_LOAD_{stamp}.json'
    path.write_text(json.dumps(report, sort_keys=True, indent=2) + '\n')
    print(json.dumps(dict(receipt=str(path.relative_to(REPO)), **report), sort_keys=True))


if __name__ == '__main__':
    main()
