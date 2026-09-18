"""Read completed parent-free math readouts; never generate or rewrite outputs."""

import argparse
import hashlib
import json
from pathlib import Path
import time

from organism_v6 import orch_combined_l1_behavior as behavior
from organism_v6.orch_combined_l1_continual import atomic_json, digest


def read(path):
    return json.loads(path.read_text())


def analyze(readout, output, annotations=None):
    loaded_path = readout / 'LOADED.json'
    if not loaded_path.exists():
        return None
    loaded = read(loaded_path)
    assert loaded['parent_present'] is False, 'parent_free_readout_required'
    assert readout.name == 'readout', 'held_readout_directory_required'
    annotations = annotations or {}
    outcomes_path = readout / 'MATH_ROWS.json'
    outcomes = {row['task_id']: row for row in read(outcomes_path)} if outcomes_path.exists() else {}
    records = []
    for path in sorted(readout.glob('CALL_*.json')):
        raw = path.read_bytes()
        call = json.loads(raw)
        if call['metadata'].get('purpose') not in ('math_held', 'math'):
            continue
        if call['status'] == 'RESERVED':
            continue
        record = dict(call_path=str(path), call_sha256=hashlib.sha256(raw).hexdigest(),
            position=call['position'], task_id=call['metadata']['task_id'], status=call['status'])
        if call['status'] == 'COMPLETE':
            response = call['response']
            text = response['raw'] if isinstance(response, dict) else response
            record['description'] = behavior.describe(text, annotations.get(behavior.text_hash(text)))
            record['description']['tokens'] = behavior.token_metrics(response, call.get('max_new_tokens', 1536))
            record['prompt_condition'] = call.get('prompt_condition', 'HISTORICAL_PROMPTED_NOT_DEFAULT')
            record['original_outcome'] = outcomes.get(record['task_id'])
            record['outcome_rescored'] = False
        else:
            record['error'] = call.get('error')
        records.append(record)
    if not records:
        return None
    completed = [row for row in records if row['status'] == 'COMPLETE']
    assessed = [row for row in completed if row['description']['semantic']['status'] != 'UNASSESSED']
    report = dict(schema='COMBINED_L1_SEALED_DESCRIPTIVE_REPORT_V1', readout=str(readout),
        loaded_sha256=hashlib.sha256(loaded_path.read_bytes()).hexdigest(), records=records,
        completed=len(completed), failed=len(records) - len(completed), semantic_reviewed=len(assessed),
        semantic_unassessed=len(completed) - len(assessed), parent_access=False,
        native_calls=0, teacher_calls=0, improvement_claim=False, training_admission=False,
        visibility='SEALED_ANALYST_ONLY_NEVER_HANDOFF_OR_L1_INGEST',
        report_order=['richness', 'accuracy'],
        meaning='Richness first; accuracy retained from existing outcome records. Branches/rejections/coherence require full-output evidence-bound author review; lexical repetition is not semantic quality.')
    filename = digest(report) + '.json'
    output.mkdir(parents=True, exist_ok=True, mode=0o700)
    if not (output / filename).exists():
        atomic_json(output / filename, report)
        (output / filename).chmod(0o600)
    return output / filename


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--readout', type=Path, action='append', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--annotations', type=Path)
    parser.add_argument('--until', type=float)
    options = parser.parse_args()
    while True:
        annotations = read(options.annotations) if options.annotations else {}
        for readout in options.readout:
            key = hashlib.sha256(str(readout.resolve()).encode()).hexdigest()
            try:
                analyze(readout, options.output / key, annotations)
            except json.JSONDecodeError:
                if options.until is None:
                    raise
        if options.until is None or time.time() >= options.until:
            break
        time.sleep(20)


if __name__ == '__main__':
    main()
