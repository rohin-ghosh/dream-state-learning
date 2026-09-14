"""Replay fixed math denominators and explicit full-text review decisions."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from organism_v6 import orch_math_rich as math


def read(path):
    return json.loads(Path(path).read_text())


def reduction(root, reviews=None):
    root = Path(root)
    tasks_document = read(root / 'TASKS.json')
    tasks = {task['id']: task for task in tasks_document['tasks']}
    task_hash = hashlib.sha256((root / 'TASKS.json').read_bytes()).hexdigest()
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
        else:
            statuses[str(shard)] = 'FAILED' if (directory / 'FAILED.json').exists() else 'PENDING'
        for path in sorted(directory.glob('CALL_*.json')):
            row = read(path)
            replay = math.capture(tasks[row['task_id']], row['kind'], row['call'], row['student_prefix'])
            assert replay == row, 'raw_capture_replay_mismatch'
            assert row['task_id'] in tasks
            assert row['call']['prompt_tokens'] <= 2048
            assert len(row['call']['token_ids']) <= (64 if row['kind'] == 'terse' else 512)
            inventory[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
            rows.append(row)
    result = math.reduce_screen(list(tasks.values()), rows)
    result['terminal_statuses'] = statuses
    result['complete'] = all(status == 'COMPLETE' for status in statuses.values())
    result['tasks_sha256'] = task_hash
    result['assigned_gpu_hours_completed'] = sum(seconds) / 3600
    result['call_file_sha256'] = inventory
    decisions = []
    for row in rows:
        key = row['task_id'] + ':' + row['kind']
        if reviews and key in reviews:
            row = math.admit(row, reviews[key], result['families'][row['family']]['eligible'])
        decisions.append(row)
    admitted = [row for row in decisions if row['admitted']]
    unique = Counter(row['target_sha256'] for row in admitted)
    if any(count > 1 for count in unique.values()):
        raise ValueError('duplicate_admitted_targets_not_distinct_rows')
    result['admitted'] = len(admitted)
    result['admitted_distinct_tasks'] = len({row['task_id'] for row in admitted})
    result['admitted_by_family'] = dict(Counter(row['family'] for row in admitted))
    result['admitted_token_distribution'] = sorted(row['generated_tokens'] for row in admitted)
    result['semantic_status_counts'] = dict(Counter(row['semantic_status'] for row in decisions if row['kind'] != 'terse'))
    result['class_metrics'] = {}
    for kind in ('terse', 'rich', 'correction', 'record'):
        group = [row for row in decisions if row['kind'] == kind]
        result['class_metrics'][kind] = dict(attempted=len(group), outcome_pass=sum(row['outcome_pass'] for row in group),
            token_contract_pass=sum(row['token_contract_pass'] for row in group),
            candidates=sum(row['candidate'] for row in group), admitted=sum(row['admitted'] for row in group),
            semantic=dict(Counter(row['semantic_status'] for row in group)))
    result['eligible_scale_families'] = [name for name in math.MINING
        if result['complete'] and result['families'][name]['eligible']
        and sum(row['family'] == name for row in admitted) >= 8
        and len({row['task_id'] for row in admitted if row['family'] == name}) >= 4]
    result['fit_ready'] = False
    return result, decisions


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--reviews')
    options = parser.parse_args()
    output = Path(options.output)
    output.mkdir(parents=True, exist_ok=False)
    result, decisions = reduction(options.root, read(options.reviews) if options.reviews else None)
    (output / 'REDUCTION.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    (output / 'ROWS.json').write_text(json.dumps(decisions, indent=2, sort_keys=True) + '\n')
    print(json.dumps({key: value for key, value in result.items() if key not in ('call_file_sha256', 'token_distribution')}, indent=2))


if __name__ == '__main__':
    main()
