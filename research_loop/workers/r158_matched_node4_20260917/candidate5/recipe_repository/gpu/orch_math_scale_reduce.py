"""Replay every native byte and keep oracle, rubric and fit gates separate."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from gpu.orch_math_rich_screen import write
from organism_v6 import orch_math_rich as original
from organism_v6 import orch_math_scale as policy


def read(path):
    return json.loads(Path(path).read_text())


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_raw(root):
    root = Path(root)
    document = read(root / 'TASKS.json')
    policy.validate(document)
    tasks = {task['id']: task for task in document['tasks']}
    task_hash = file_hash(root / 'TASKS.json')
    rows, statuses, seconds, inventory = [], {}, [], {}
    for shard in range(4):
        directory = root / f'shard{shard}'
        request = directory / 'REQUEST.json'
        if request.exists():
            assert read(request)['tasks_sha256'] == task_hash
        terminal = directory / 'RESULT.json'
        if terminal.exists():
            result = read(terminal)
            statuses[str(shard)] = result['status']
            seconds.append(result['finished_unix'] - result['started_unix'])
            assert result['adapter_state'] == '37ec37884e4b0b679edd1dba1be1dec3474589e992649f3a33e7e3b1ec78b8c0'
        else:
            statuses[str(shard)] = 'FAILED' if (directory / 'FAILED.json').exists() else 'PENDING'
        assigned = {task['id'] for position, task in enumerate(document['tasks']) if position % 4 == shard}
        calls = sorted(directory.glob('CALL_*.json'))
        assert len(calls) <= 512
        for path in calls:
            row = read(path)
            assert row['task_id'] in assigned
            assert row['kind'] in ('rich', 'new_record')
            assert row == original.capture(tasks[row['task_id']], row['kind'], row['call'], row['student_prefix'])
            assert row['call']['prompt_tokens'] <= 2048 and len(row['call']['token_ids']) <= 512
            rows.append(row)
            inventory[row['task_id'] + ':' + row['kind']] = dict(
                path=str(path.relative_to(root)), sha256=file_hash(path))
    by_key = {(row['task_id'], row['kind']): row for row in rows}
    assert len(by_key) == len(rows) <= policy.MAX_CALLS
    complete = all(status == 'COMPLETE' for status in statuses.values())
    for task_id, task in tasks.items():
        rich = by_key.get((task_id, 'rich'))
        record = by_key.get((task_id, 'new_record'))
        if rich:
            guided, student = policy.prompt(task, 'rich')
            assert rich['student_prefix'] == student and rich['call']['messages'] == guided
        if record:
            assert rich and rich['outcome_pass']
            guided, student = policy.prompt(task, 'new_record', rich['target'])
            assert record['student_prefix'] == student and record['call']['messages'] == guided
        if complete:
            assert rich is not None
            assert bool(record) == rich['outcome_pass']
    return document, rows, dict(complete=complete, statuses=statuses, task_sha256=task_hash,
                                native_gpu_hours_complete=sum(seconds)/3600, inventory=inventory)


def reduce(root, reviews=None, gold=None):
    document, rows, binding = load_raw(root)
    reviews, gold = reviews or {}, gold or {}
    tasks = {task['id']: task for task in document['tasks']}
    assert set(gold) <= set(tasks)
    for task_id, decision in gold.items():
        assert decision['question_sha256'] == tasks[task_id]['question_sha256']
        assert decision['status'] in ('VALID', 'INVALID', 'AMBIGUOUS')
        assert decision['reason'] and decision['independent_answer']
        if decision['status'] == 'VALID':
            assert original.number(decision['independent_answer']) == original.number(tasks[task_id]['gold'])
    assert set(reviews) <= set(binding['inventory'])
    decisions = []
    for row in rows:
        key = row['task_id'] + ':' + row['kind']
        if key in reviews:
            decision = reviews[key]
            assert decision['raw_call_sha256'] == binding['inventory'][key]['sha256']
            row = policy.admit(row, decision, gold.get(row['task_id'], {}))
        decisions.append(row)
    reading_complete = bool(binding['complete'] and len(reviews) == len(rows) and len(gold) == 1024)
    conditions = {}
    for kind in ('rich', 'new_record'):
        group = [row for row in decisions if row['kind'] == kind]
        conditions[kind] = metrics(group, 1024)
    families = {}
    for family in original.MINING:
        group = [row for row in decisions if row['family'] == family]
        families[family] = dict(denominator=256,
            conditions={kind: metrics([row for row in group if row['kind'] == kind], 256)
                        for kind in ('rich', 'new_record')},
            distinct_admitted_tasks=sorted({row['task_id'] for row in group if row['admitted']}))
    result = dict(denominator=1024, held_denominator=64, calls=len(rows),
        complete=binding['complete'], terminal_statuses=binding['statuses'],
        semantic_reading_complete=reading_complete, reviewed_rows=len(reviews), reviewed_questions=len(gold),
        tasks_sha256=binding['task_sha256'], raw_inventory=binding['inventory'],
        native_gpu_hours_complete=binding['native_gpu_hours_complete'],
        conditions=conditions, families=families,
        gold_review_counts=dict(Counter(decision['status'] for decision in gold.values())),
        unattempted_initial=1024-conditions['rich']['attempted'],
        skipped_or_unattempted_records=1024-conditions['new_record']['attempted'],
        fits=0, updates=0, independent_blind_audit_complete=False,
        claim='NEW_PIPELINE_MINING_YIELD_NOT_ACCURACY_GAIN_OR_LEARNING',
        **policy.corpus_gate(decisions, binding['complete'], reading_complete))
    return result, decisions


def metrics(rows, denominator):
    return dict(denominator=denominator, attempted=len(rows),
        outcome_pass=sum(row['outcome_pass'] for row in rows),
        token_contract_pass=sum(row['token_contract_pass'] for row in rows),
        candidate_count=sum(row['candidate'] for row in rows),
        admitted=sum(row['admitted'] for row in rows),
        semantic=dict(Counter(row['semantic_status'] for row in rows)),
        axes={axis: dict(Counter(str(row.get('review', {}).get(axis)) for row in rows)) for axis in policy.AXES},
        tokens=sorted(row['generated_tokens'] for row in rows),
        admitted_tokens=sorted(row['generated_tokens'] for row in rows if row['admitted']),
        admitted_distinct_tasks=sorted({row['task_id'] for row in rows if row['admitted']}),
        target_hash_unique_count=len({row['target_sha256'] for row in rows}),
        prefix_hash_unique_count=len({original.digest(row['student_prefix']) for row in rows}))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--review-directory')
    options = parser.parse_args()
    reviews, gold = {}, {}
    if options.review_directory:
        for path in sorted(Path(options.review_directory).glob('batch_*/ACCEPTED_REVIEW.json')):
            batch = read(path)
            for key, value in batch['reviews'].items():
                assert key not in reviews
                reviews[key] = value
            for key, value in batch['gold'].items():
                assert key not in gold
                gold[key] = value
    result, rows = reduce(options.root, reviews, gold)
    output = Path(options.output)
    output.mkdir(parents=True, exist_ok=False)
    write(output / 'REDUCTION.json', result)
    write(output / 'ROWS.json', rows)
    write(output / 'ADMITTED_ROWS.json', [row for row in rows if row['admitted']])
    print(json.dumps({key: result[key] for key in ('calls', 'complete', 'reviewed_rows',
          'admitted_distinct_targets', 'corpus_threshold_met', 'fit_ready')}, indent=2))


if __name__ == '__main__':
    main()
