"""Fixed-denominator matched reduction, requiring explicit full-text decisions."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from gpu.orch_math_rich_screen import write
from organism_v6 import orch_math_record as policy
from organism_v6 import orch_math_rich as original


def read(path):
    return json.loads(Path(path).read_text())


def reduction(root, reviews=None, gold_review=None):
    root = Path(root)
    document = read(root / 'TASKS.json')
    policy.validate(document)
    tasks = {task['id']: task for task in document['tasks']}
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
            assert row == original.capture(tasks[row['task_id']], row['kind'], row['call'], row['student_prefix'])
            assert row['kind'] in ('rich', 'old_record', 'new_record')
            assert row['call']['prompt_tokens'] <= 2048 and len(row['call']['token_ids']) <= 512
            assert row['task_id'] in {task['id'] for position, task in enumerate(document['tasks']) if position % 4 == shard}
            rows.append(row)
            inventory[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    by_key = {(row['task_id'], row['kind']): row for row in rows}
    assert len(by_key) == len(rows)
    complete = all(status == 'COMPLETE' for status in statuses.values())
    for task_id, task in tasks.items():
        rich = by_key.get((task_id, 'rich'))
        if complete:
            assert rich is not None
            assert all(((task_id, kind) in by_key) == rich['outcome_pass'] for kind in ('old_record', 'new_record'))
        for kind in ('old_record', 'new_record'):
            row = by_key.get((task_id, kind))
            if row:
                assert rich and rich['outcome_pass']
                assert row['student_prefix'] == policy.prompt(task, kind, rich['target'])[1]
    decisions = []
    for row in rows:
        key = row['task_id'] + ':' + row['kind']
        if reviews and key in reviews:
            valid_gold = bool(gold_review and gold_review.get(row['task_id'], {}).get('status') == 'VALID')
            row = original.admit(row, reviews[key], valid_gold)
        decisions.append(row)
    complete_reading = bool(reviews and gold_review and len(reviews) == len(rows)
                            and set(gold_review) == set(tasks)
                            and all(row['semantic_status'] != 'UNREVIEWED' for row in decisions))
    if gold_review:
        for task_id, decision in gold_review.items():
            assert decision['question_sha256'] == tasks[task_id]['question_sha256']
            assert decision['status'] in ('VALID', 'AMBIGUOUS', 'SUSPECT') and decision['reason']
    groups = {kind: [row for row in decisions if row['kind'] == kind]
              for kind in ('rich', 'old_record', 'new_record')}
    by_key = {(row['task_id'], row['kind']): row for row in decisions}
    def flag(task_id, kind):
        return by_key.get((task_id, kind), {}).get('admitted', False)
    def grounded(kind, value):
        return sum(row.get('review', {}).get('grounded_operations') is value for row in groups[kind])
    primary = policy.paired_criterion(
        [flag(task_id, 'old_record') for task_id in tasks],
        [flag(task_id, 'new_record') for task_id in tasks],
        grounded('old_record', True), grounded('new_record', True),
        grounded('old_record', False), grounded('new_record', False), complete and complete_reading)
    metrics = {}
    for kind, group in groups.items():
        metrics[kind] = dict(denominator=64, attempted=len(group),
            outcome_pass=sum(row['outcome_pass'] for row in group),
            token_contract_pass=sum(row['token_contract_pass'] for row in group),
            candidates=sum(row['candidate'] for row in group), admitted=sum(row['admitted'] for row in group),
            semantic=dict(Counter(row['semantic_status'] for row in group)),
            axes={axis: dict(Counter(str(row.get('review', {}).get(axis)) for row in group)) for axis in policy.AXES},
            token_distribution=sorted(row['generated_tokens'] for row in group),
            admitted_token_distribution=sorted(row['generated_tokens'] for row in group if row['admitted']))
    families = {}
    for family in original.MINING:
        family_tasks = [task_id for task_id, task in tasks.items() if task['family'] == family]
        families[family] = dict(denominator=16, conditions={kind: dict(
            admitted=sum(flag(task_id, kind) for task_id in family_tasks),
            admitted_distinct_tasks=sorted(task_id for task_id in family_tasks if flag(task_id, kind)),
            token_distribution=sorted(row['generated_tokens'] for row in group if row['family'] == family),
            admitted_token_distribution=sorted(row['generated_tokens'] for row in group if row['family'] == family and row['admitted']),
            axes={axis: dict(Counter(str(row.get('review', {}).get(axis)) for row in group if row['family'] == family)) for axis in policy.AXES}
        ) for kind, group in groups.items()})
    result = dict(denominator=64, complete=complete, semantic_reading_complete=complete_reading,
                  terminal_statuses=statuses, calls=len(rows), tasks_sha256=task_hash,
                  primary=primary, conditions=metrics, families=families,
                  assigned_gpu_hours_completed=sum(seconds)/3600, call_file_sha256=inventory,
                  skipped_record_pairs=64-len(groups['old_record']), fit_ready=False, fits=0,
                  gold_review_counts=dict(Counter(decision['status'] for decision in (gold_review or {}).values())),
                  discordant_pairs=[dict(task_id=task_id, old=flag(task_id, 'old_record'), new=flag(task_id, 'new_record'))
                                    for task_id in tasks if flag(task_id, 'old_record') != flag(task_id, 'new_record')])
    return result, decisions


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--reviews')
    parser.add_argument('--gold-review')
    options = parser.parse_args()
    output = Path(options.output)
    output.mkdir(parents=True, exist_ok=False)
    result, rows = reduction(options.root, read(options.reviews) if options.reviews else None,
                             read(options.gold_review) if options.gold_review else None)
    write(output / 'REDUCTION.json', result)
    write(output / 'ROWS.json', rows)
    admitted = [{key: row[key] for key in ('task_id', 'family', 'kind', 'student_prefix', 'target', 'target_sha256')}
                for row in rows if row['admitted']]
    write(output / 'ADMITTED_ROWS.json', admitted)
    print(json.dumps(dict(calls=result['calls'], complete=result['complete'], primary=result['primary']), indent=2))


if __name__ == '__main__':
    main()
