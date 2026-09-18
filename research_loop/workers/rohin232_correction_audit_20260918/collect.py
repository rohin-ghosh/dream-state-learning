"""Collect bounded immutable TRAIN projections using existing read-only SSH."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import time

from audit import report


OWN = Path(__file__).resolve().parent
REPO = OWN.parents[2]


def save(path, value):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    temporary = path.with_suffix('.next')
    with temporary.open('w') as output:
        json.dump(value, output, ensure_ascii=False, sort_keys=True, indent=2)
        output.write('\n')
    os.replace(temporary, path)


def call(target, operation):
    if target['wrapper'] not in ('a40r_ssh.sh', 'ovx_ssh.sh', 'ovx2_ssh.sh', 'ovx3_ssh.sh', 'ovx4_ssh.sh'):
        raise ValueError('existing_allowlisted_transport')
    program = (OWN / 'reader.py').read_text() + '\n' + operation
    result = subprocess.run(['bash', str(REPO / 'gpu' / target['wrapper']),
        'CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -B -'],
        input=program, capture_output=True, text=True, timeout=150)
    if result.returncode:
        raise RuntimeError('read_only_remote_error:' + result.stderr[-1400:])
    return json.loads(result.stdout)


def one(target):
    label = target['label']
    if not target.get('root'):
        return dict(label=label, status=target['status'], highest_verified_level=None, learner_controls=0)
    private = OWN / 'private' / label
    evidence_path = private / 'EVIDENCE.json'
    old = json.loads(evidence_path.read_bytes()) if evidence_path.exists() else None
    if old and old.get('reader_revision') != 'R232_READ_ONLY_V2':
        save(private / 'BEFORE_RENDER_CONTRACT_REPAIR.json', old)
        old = None
    journal = old['journal_id'] if old else target.get('journal_id')
    after = old['through']['index'] if old else None
    operation = f'print(json.dumps(collect({target["root"]!r}, {journal!r}, maximum=1200, after={after!r}), ensure_ascii=False))\n'
    batch = call(target, operation)
    if old:
        if batch['journal_id'] != old['journal_id']:
            raise ValueError('life_incarnation_changed')
        if batch['continuity']:
            start = batch['continuity'][0]
            if start['index'] != old['through']['index'] + 1 or start['previous_sha256'] != old['through']['sha256']:
                raise ValueError('incremental_chain_gap')
            batch['records'] = old['records'] + batch['records']
            batch['continuity'] = old['continuity'] + batch['continuity']
        else:
            batch['records'], batch['continuity'], batch['through'] = old['records'], old['continuity'], old['through']
            batch['caught_up'] = batch['through'] == batch['head']
        batch['coverage_start'] = old['coverage_start']
    save(evidence_path, batch)
    annotations_path = private / 'ANNOTATIONS.json'
    annotations = json.loads(annotations_path.read_bytes()) if annotations_path.exists() else []
    result = report(batch, label, annotations)
    for trace in result['traces']:
        if trace['level'] != 3 or trace['checkpoint_pending']:
            continue
        destination = OWN / 'public' / 'first_full' / (label + '.json')
        if destination.exists():
            continue
        index = trace['first_following_complete']['index']
        manifest = call(target, f'print(json.dumps(checkpoint({target["root"]!r}, {batch["journal_id"]!r}, {index})))\n')
        trace['durable_checkpoint'] = manifest
        save(destination, dict(label=label, trace=trace, first_full_observed_unix=time.time()))
    return result


def run_once():
    os.umask(0o077)
    targets = json.loads((OWN / 'private/TARGETS.json').read_bytes())
    def checked(target):
        try:
            return one(target)
        except Exception as error:
            save(OWN / 'private' / target['label'] / 'ERROR.json', dict(error=str(error), observed_unix=time.time()))
            return dict(label=target['label'], status='READ_ERROR_PRIVATE_DIAGNOSTIC_RETAINED', highest_verified_level=None)
    with ThreadPoolExecutor(max_workers=3) as executor:
        rows = list(executor.map(checked, targets))
    result = dict(observed_utc=datetime.now(timezone.utc).isoformat(), rows=rows,
        interpretation='Bounded correction evidence; unknown is not failure, keyword candidates are not semantic proof.',
        no_subagents=True, remote_writes=0, inbox_changes=0, learner_signals=0, rescoring=0)
    save(OWN / 'public/CURRENT.json', result)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    save(OWN / 'public/cuts' / (stamp + '.json'), result)
    lines = ['# R232 correction-sequence audit', '', 'Cut: ' + result['observed_utc'], '',
        'Levels: feedback only0 → own correction identified1 → applied in the NEXT ACT2 → another relevant ACT without reminder3.',
        'Unknown is not level0 failure. Initial windows are bounded, not lifetime-negative claims. No lives modified.', '',
        '| Life | Covered records | Caught up | ACTs | Feedback candidates | Reviewed | Highest proved level | Status |',
        '| --- | --- | --- | ---: | ---: | ---: | --- | --- |']
    for row in rows:
        level = row.get('highest_verified_level')
        coverage = str(row.get('coverage_start', '?')) + '–' + str(row.get('coverage_end', '?'))
        lines.append(f'| {row["label"]} | {coverage} | {row.get("caught_up", "unknown")} | {row.get("actual_ACTs", "?")} | {row.get("external_feedback_candidates", "?")} | {row.get("reviewed_corrections", 0)} | {level if level is not None else "unknown"} | {row["status"]} |')
    path = OWN / 'public/STATUS.md'
    path.write_text('\n'.join(lines) + '\n')
    return result


if __name__ == '__main__':
    print(json.dumps(run_once(), sort_keys=True))
