"""Bind completed author readings to the prospectively fixed eight-task panel."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil

from gpu.orch_rich_intensity_reduce import distribution, read, reduce
from organism_v6 import orch_math_rich as original
from organism_v6 import orch_rich_intensity as policy


POSITIONS = (0, 1, 64, 65, 128, 129, 192, 193)
AXES = ('first_person', 'grounded_operations', 'checkable_expectation',
        'reusable_content', 'no_padding', 'neutral_prefix_compatible')


def export(root, reading_path, first_packet, output):
    tasks = read(root / 'TASKS.json')['tasks']
    panel_tasks = [tasks[position] for position in POSITIONS]
    task_map = {task['id']: task for task in panel_tasks}
    readings = read(reading_path)
    reviews = read(first_packet / 'REVIEWS.json')
    gold = read(first_packet / 'GOLD.json')
    first_bytes = (first_packet / 'ADMITTED.json').read_bytes()
    assert hashlib.sha256(first_bytes).hexdigest() == '52197d8d0f73528af69b61e6f244e5b1570f2bcfafd5ebb79d4058c959946837'
    inventory = {}
    for path in sorted((root / 'run').glob('shard*/CALL_*.json')):
        row = read(path)
        if row['task_id'] in task_map:
            key = f"{row['condition']}:{row['task_id']}:{row['kind']}"
            assert key not in inventory
            inventory[key] = (path, row)
    reader = 'RICH-INTENSITY author, direct fulltext readings; not independent audit'
    for task_id, decision in readings['gold'].items():
        assert task_id not in gold
        gold[task_id] = dict(decision, question_sha256=task_map[task_id]['question_sha256'], reader=reader)
    for condition, task_id, kind, failures, reason, spans, branching in readings['reviews']:
        key = f'{condition}:{task_id}:{kind}'
        assert key not in reviews and set(failures) <= set(AXES)
        path, row = inventory[key]
        reviews[key] = dict(status='FAIL' if failures else 'PASS',
            target_sha256=row['target_sha256'], student_prefix_sha256=original.digest(row['student_prefix']),
            raw_call_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), full_text_read=True,
            reason=reason, evidence_spans=spans, descriptive_branching=branching, reader=reader,
            prefix_reason='Compared full target with complete question and exact prior assistant text in neutral history. '
                'Shown arithmetic supports self-checks, not external feedback. Defects are stated in reason.',
            **{axis: axis not in failures for axis in AXES})
    for condition in policy.CONDITIONS:
        for task_id in task_map:
            source_key = f'{condition}:{task_id}:rich'
            record_key = f'{condition}:{task_id}:new_record'
            assert source_key in inventory
            assert (record_key in inventory) == inventory[source_key][1]['outcome_pass']
    assert set(inventory) <= set(reviews)
    cohort_summary, cohort_rows = reduce(root, reviews, gold)
    rows = [row for row in cohort_rows if row['task_id'] in task_map]
    assert len(rows) == len(inventory)
    summary = dict(panel_complete=True, original_batch_complete=cohort_summary['complete'],
        positions=POSITIONS, task_ids=list(task_map), tasks_sha256=policy.TASKS_SHA,
        reviewed_rows=len(rows), initial_calls=24, total_calls=len(rows),
        family_tasks=dict(Counter(task['family'] for task in panel_tasks)),
        independent_verification=False, fits=0, claim='FIXED_PAIRED_DESCRIPTIVE_PANEL_NOT_WINNER_OR_LEARNING',
        first_packet_unchanged_sha256=hashlib.sha256(first_bytes).hexdigest(), conditions={})
    for condition in policy.CONDITIONS:
        selected = [row for row in rows if row['condition'] == condition]
        details = dict(denominator=8, calls=len(selected), admitted=sum(row['admitted'] for row in selected),
            admitted_tasks=len({row['task_id'] for row in selected if row['admitted']}), by_kind={})
        for kind in ('rich', 'new_record'):
            subset = [row for row in selected if row['kind'] == kind]
            details['by_kind'][kind] = dict(calls=len(subset), outcome_pass=sum(row['outcome_pass'] for row in subset),
                candidates=sum(row['candidate'] for row in subset), admitted=sum(row['admitted'] for row in subset),
                semantic_statuses=dict(Counter(row['semantic_status'] for row in subset)),
                generated_tokens=distribution([row['generated_tokens'] for row in subset]),
                unparseable_final=sum(original.final_value(row['target']) is None for row in subset),
                parsed_numeric_mismatch=sum(original.final_value(row['target']) is not None and not row['outcome_pass'] for row in subset),
                outside_target_range=sum(not row['token_contract_pass'] for row in subset),
                failed_axes=dict(Counter(axis for row in subset for axis in AXES if not row['review'][axis])),
                gold_excluded=sum(gold[row['task_id']]['status'] != 'VALID' for row in subset))
        details['family_admitted'] = dict(Counter(row['family'] for row in selected if row['admitted']))
        summary['conditions'][condition] = details
    output.mkdir(parents=True, exist_ok=False)
    for key, (path, row) in inventory.items():
        destination = output / 'RAW' / path.relative_to(root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)
    documents = {'SUMMARY.json': summary, 'ROWS.json': rows,
        'ADMITTED.json': [row for row in rows if row['admitted']],
        'REVIEWS.json': {key: reviews[key] for key in inventory},
        'GOLD.json': {task_id: gold[task_id] for task_id in task_map},
        'PANEL_TASKS.json': panel_tasks, 'COHORT_SNAPSHOT_SUMMARY.json': cohort_summary}
    for name, document in documents.items():
        (output / name).write_text(json.dumps(document, indent=2) + '\n')
    assert (first_packet / 'ADMITTED.json').read_bytes() == first_bytes
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--reading', type=Path, required=True)
    parser.add_argument('--first-packet', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    export(options.root, options.reading, options.first_packet, options.output)
