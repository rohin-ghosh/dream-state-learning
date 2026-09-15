"""Replay fixed-cohort calls; keep unread source and records out of admission."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import statistics

from organism_v6 import orch_math_rich as original
from organism_v6 import orch_rich_intensity as policy


def read(path):
    return json.loads(Path(path).read_text())


def distribution(values):
    ordered = sorted(values)
    if not ordered:
        return dict(count=0, total=0)
    return dict(count=len(ordered), total=sum(ordered), minimum=ordered[0], maximum=ordered[-1],
        median=statistics.median(ordered), mean=statistics.mean(ordered),
        p10=ordered[int((len(ordered) - 1) * .1)], p90=ordered[int((len(ordered) - 1) * .9)])


def reduce(root, reviews=None, gold=None):
    root = Path(root)
    document = read(root / 'TASKS.json')
    policy.validate(document)
    assert hashlib.sha256((root / 'TASKS.json').read_bytes()).hexdigest() == policy.TASKS_SHA
    tasks = {task['id']: task for task in document['tasks']}
    rows, inventory, statuses = [], {}, {}
    reviews, gold = reviews or {}, gold or {}
    for task_id, decision in gold.items():
        assert decision['question_sha256'] == tasks[task_id]['question_sha256']
        assert decision['status'] in ('VALID', 'INVALID', 'AMBIGUOUS') and decision['reason']
        if decision['status'] == 'VALID':
            assert original.number(decision['independent_answer']) == original.number(tasks[task_id]['gold'])
    for index in range(6):
        condition, shard = policy.allocation(index)
        directory = root / 'run' / f'shard{index}'
        terminal = directory / 'RESULT.json'
        statuses[str(index)] = read(terminal)['status'] if terminal.exists() else (
            'FAILED' if (directory / 'FAILED.json').exists() else 'PENDING')
        paths = sorted(directory.glob('CALL_*.json'))
        assert len(paths) <= 256
        assigned = {task['id'] for position, task in enumerate(document['tasks']) if position % 2 == shard}
        previous = {}
        for path in paths:
            row = read(path)
            task_id, kind = row['task_id'], row['kind']
            assert task_id in assigned and row['condition'] == condition and row['physical_index'] == index
            assert kind in ('rich', 'new_record')
            key = f'{condition}:{task_id}:{kind}'
            assert key not in inventory
            if kind == 'new_record':
                assert task_id in previous and previous[task_id]['outcome_pass']
            guided, student = policy.prompt(tasks[task_id], condition, kind,
                previous[task_id]['target'] if kind == 'new_record' else None)
            assert row['generation_messages'] == row['call']['messages'] == guided
            assert row['student_prefix'] == student
            assert row['student_prefix_sha256'] == original.digest(student)
            assert row['max_new_tokens'] == policy.generation_cap(condition, kind)
            assert len(row['call']['token_ids']) <= row['max_new_tokens']
            assert row['call']['prompt_tokens'] <= policy.CONTEXT_LIMIT
            replay = policy.capture(tasks[task_id], kind, row['call'], student)
            assert all(row[field] == value for field, value in replay.items())
            inventory[key] = dict(path=str(path.relative_to(root)),
                sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            if kind == 'rich':
                previous[task_id] = row
            if key in reviews:
                assert reviews[key]['raw_call_sha256'] == inventory[key]['sha256']
                row = policy.admit(row, reviews[key], gold.get(task_id, {}))
            rows.append(row)
        if statuses[str(index)] == 'COMPLETE':
            assert len(previous) == 128
            assert len(paths) == 128 + sum(row['outcome_pass'] for row in previous.values())
    assert len(rows) <= 1536 and set(reviews) <= set(inventory)
    summary = dict(tasks_sha256=policy.TASKS_SHA, denominator_per_condition=256,
        statuses=statuses, complete=all(status == 'COMPLETE' for status in statuses.values()),
        total_calls=len(rows), fits=0, fit_ready=False, independent_verification=False,
        reviewed_rows=len(reviews), gold_reviewed_tasks=len(gold), conditions={}, inventory=inventory)
    for condition in policy.CONDITIONS:
        selected = [row for row in rows if row['condition'] == condition]
        values = dict(denominator=256, calls=len(selected),
            distinct_tasks=len({row['task_id'] for row in selected}),
            admitted_distinct_tasks=len({row['task_id'] for row in selected if row['admitted']}),
            admitted_rows=sum(row['admitted'] for row in selected), by_kind={}, by_family={})
        for name, subset in [(kind, [row for row in selected if row['kind'] == kind]) for kind in ('rich', 'new_record')]:
            values['by_kind'][name] = dict(calls=len(subset), outcome_pass=sum(row['outcome_pass'] for row in subset),
                candidates=sum(row['candidate'] for row in subset),
                semantic_statuses=dict(Counter(row['semantic_status'] for row in subset)),
                admitted=sum(row['admitted'] for row in subset),
                generated_tokens=distribution([row['generated_tokens'] for row in subset]),
                prompt_tokens=distribution([row['call']['prompt_tokens'] for row in subset]),
                truncated=sum(row['call']['truncated'] for row in subset),
                outside_target_range=sum(not 150 <= row['generated_tokens'] <= 400 for row in subset))
        for family in original.MINING:
            subset = [row for row in selected if row['family'] == family]
            values['by_family'][family] = dict(denominator=64, calls=len(subset),
                initial_outcome_pass=sum(row['kind'] == 'rich' and row['outcome_pass'] for row in subset),
                candidates=sum(row['candidate'] for row in subset), admitted=sum(row['admitted'] for row in subset))
        summary['conditions'][condition] = values
    return summary, rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--reviews', type=Path)
    parser.add_argument('--gold', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    summary, rows = reduce(options.root, read(options.reviews) if options.reviews else None,
        read(options.gold) if options.gold else None)
    options.output.mkdir(parents=True, exist_ok=False)
    (options.output / 'SUMMARY.json').write_text(json.dumps(summary, indent=2) + '\n')
    (options.output / 'ROWS.json').write_text(json.dumps(rows, indent=2) + '\n')
    print(json.dumps({key: value for key, value in summary.items() if key != 'inventory'}, indent=2))


if __name__ == '__main__':
    main()
