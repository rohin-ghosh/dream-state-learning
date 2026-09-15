"""Compact richness-first reductions; raw held text never leaves native files."""

import argparse
from collections import Counter
from pathlib import Path
from statistics import mean, median

from gpu import orch_combined_l1_continual_run as run
from organism_v6 import orch_combined_l1_behavior as behavior


def reduce(readout, annotations=None):
    if not (readout / 'LOADED.json').exists():
        return dict(status='NOT_LOADED', readout=str(readout))
    assert run.read(readout / 'LOADED.json')['parent_present'] is False
    annotations = annotations or {}
    records = []
    reserved = failed = 0
    for path in sorted(readout.glob('CALL_*.json')):
        record = run.read(path)
        if record['metadata'].get('purpose') not in ('math', 'math_held'):
            continue
        reserved += 1
        if record['status'] == 'FAILED':
            failed += 1
        if record['status'] != 'COMPLETE':
            continue
        response = record['response']
        text = response['raw'] if isinstance(response, dict) else response
        description = behavior.describe(text, annotations.get(behavior.text_hash(text)))
        tokens = behavior.token_metrics(response, record.get('max_new_tokens', 1536))
        records.append(dict(position=record['position'], task_id=record['metadata']['task_id'],
            call_sha256=run.sha(path), prompt_condition=record.get('prompt_condition', 'HISTORICAL_PROMPTED_NOT_DEFAULT'),
            tokens=tokens, repetition=description['repetition'],
            semantics={key: value for key, value in description['semantic'].items() if key != 'annotation'},
            coherence={key: value for key, value in description['coherence'].items() if key not in ('evidence', 'reason')}))
    lengths = [record['tokens']['generated_tokens'] for record in records if record['tokens']['generated_tokens'] is not None]
    reviewed = [record for record in records if record['semantics']['status'] != 'UNASSESSED']
    outcomes = run.read(readout / 'MATH_ROWS.json') if (readout / 'MATH_ROWS.json').exists() else []
    return dict(schema='COMBINED_L1_RICHNESS_FIRST_COMPACT_V2', readout=str(readout),
        report_order=['richness', 'accuracy'], reserved=reserved, completed=len(records), failed=failed,
        generated_tokens=dict(measured=len(lengths), minimum=min(lengths) if lengths else None,
            median=median(lengths) if lengths else None, mean=mean(lengths) if lengths else None,
            maximum=max(lengths) if lengths else None),
        eos=sum(record['tokens'].get('eos') is True for record in records),
        ceiling=sum(record['tokens'].get('ceiling') is True for record in records),
        mean_lexical_repetition_rate=mean(record['repetition']['repeated_fourgram_rate'] for record in records) if records else None,
        semantic_reviewed=len(reviewed), semantic_unassessed=len(records)-len(reviewed),
        semantic_review_sample='first4 prospective positions per arm, author full-output review; not whole-cohort estimate',
        distinct_paths_considered=[record['semantics']['distinct_paths_considered'] for record in reviewed],
        grounded_rejections=[record['semantics']['paths_rejected_with_grounded_reason'] for record in reviewed],
        coherence_counts=dict(Counter(record['coherence']['judgment'] for record in reviewed)),
        accuracy_secondary=dict(correct=sum(row['outcome_pass'] for row in outcomes), completed_denominator=len(outcomes)),
        records=records, parent_access=False, improvement_claim=False, native_calls=0, raw_text_included=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--readout', type=Path, required=True)
    parser.add_argument('--annotations', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    report = reduce(arguments.readout, run.read(arguments.annotations) if arguments.annotations else None)
    assert not arguments.output.exists()
    run.write(arguments.output, report)
    print(__import__('json').dumps({key: value for key, value in report.items() if key != 'records'}, indent=2))
