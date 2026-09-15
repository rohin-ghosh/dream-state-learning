"""Offline hash-bound full-text review joins; never admit unread rows."""

import argparse
import collections
import json
from pathlib import Path
import statistics

from organism_v6 import orch_code_channel as policy
from gpu.orch_code_channel_freeze import write


def key(row):
    return f"{row['arm']}:{row['position']:02d}:{row['kind']}"


def audit(freeze, raw, reviews):
    tasks = freeze['tasks']
    rows = []
    used = set()
    for arm in policy.ARMS:
        histories = {}
        for path in sorted((raw / arm).glob('CALL_*.json')):
            row = json.loads(path.read_text())
            task = tasks[row['position']]
            previous = histories.get(row['position']) if row['kind'] == 'NEW' else None
            if row['arm'] != arm or row['task_id'] != task['id']:
                raise ValueError('cohort_arm_join_failed')
            if row['kind'] == 'NEW' and previous is None:
                raise ValueError('NEW_without_source')
            messages, student = policy.prompt(task, arm, previous)
            if row['call']['messages'] != messages or row['student_prefix'] != student:
                raise ValueError('actor_or_neutral_prefix_changed')
            captured = policy.capture(task, arm, row['call'], previous)
            for field in ('target', 'target_sha256', 'question_sha256', 'feedback', 'outcome_pass',
                          'generated_tokens', 'token_contract', 'neutral_prefix_pass', 'source_target_sha256'):
                actual = json.loads(json.dumps(captured[field])) if field == 'feedback' else captured[field]
                if actual != row[field]:
                    raise ValueError('raw_replay_mismatch:' + field)
            review_key = key(row)
            review = reviews.get(review_key)
            if review is not None:
                row['admitted'] = policy.admission(row, review)
                row['semantic_status'] = review['status']
                row['review'] = review
                used.add(review_key)
            else:
                row['admitted'] = False
                row['semantic_status'] = 'UNREVIEWED'
            histories[row['position']] = row
            rows.append(row)
    if set(reviews) != used:
        raise ValueError('unused_or_unknown_review_keys')
    summary = policy.reduce(tasks, rows)
    for arm in policy.ARMS:
        selected = [row for row in rows if row['arm'] == arm]
        tokens = [row['generated_tokens'] for row in selected]
        summary['arms'][arm].update(
            semantic_statuses=dict(collections.Counter(row['semantic_status'] for row in selected)),
            semantic_axes={axis: dict(collections.Counter(str(row.get('review', {}).get(axis, 'UNREVIEWED'))
                            for row in selected)) for axis in policy.AXES},
            unique_targets=len({row['target_sha256'] for row in selected}),
            unique_admitted_targets=len({row['target_sha256'] for row in selected if row['admitted']}),
            token_min=min(tokens) if tokens else None, token_max=max(tokens) if tokens else None,
            token_median=statistics.median(tokens) if tokens else None,
            action_format_failures=sum(not row['action_valid'] for row in selected),
            failed_source_examples=[dict(task_id=row['task_id'], position=row['position'],
                feedback=row['feedback'], target_sha256=row['target_sha256']) for row in selected
                if row['kind'] == 'SOURCE' and not row['outcome_pass']])
        admitted = {row['task_id'] for row in selected if row['admitted']}
        unresolved_eligible = {row['task_id'] for row in selected
            if row['semantic_status'] in ('UNREVIEWED', 'UNRESOLVED')
            and row['outcome_pass'] and row['token_contract'] and row['neutral_prefix_pass']}
        sources = {row['task_id']: row for row in selected if row['kind'] == 'SOURCE'}
        records = {row['task_id'] for row in selected if row['kind'] == 'NEW'}
        pending = {task['id'] for task in tasks if task['id'] not in sources} | {
            task_id for task_id, row in sources.items() if row['outcome_pass'] and task_id not in records}
        summary['arms'][arm]['pending_task_calls'] = len(pending)
        summary['arms'][arm]['qualified_task_bounds'] = [len(admitted), len(admitted | unresolved_eligible | pending)]
        summary['arms'][arm]['mechanically_eligible_unreviewed'] = sum(
            row['semantic_status'] == 'UNREVIEWED' and row['outcome_pass'] and row['token_contract']
            for row in selected)
    summary['primary_gain_upper_bound'] = (summary['arms']['SEPARATED']['qualified_task_bounds'][1]
                                           - summary['arms']['LEGACY']['qualified_task_bounds'][0])
    summary['native_call_coverage_complete'] = all(summary['arms'][arm]['source_calls'] == 64
        and summary['arms'][arm]['pending_task_calls'] == 0 for arm in policy.ARMS)
    summary['full_review_complete'] &= summary['native_call_coverage_complete']
    summary['candidate'] &= summary['native_call_coverage_complete']
    summary['primary_refuted_by_necessary_gate'] = (summary['native_call_coverage_complete']
                                                   and summary['primary_gain_upper_bound'] < 8)
    summary['pairs'] = [dict(position=position, task_id=task['id'], family=task['family'], **{
        arm: dict(initial_success=next((row['outcome_pass'] for row in rows if row['arm'] == arm
                  and row['position'] == position and row['kind'] == 'SOURCE'), None),
                  qualified=any(row['admitted'] for row in rows if row['arm'] == arm and row['position'] == position),
                  unreviewed=sum(row['semantic_status'] == 'UNREVIEWED' for row in rows
                                 if row['arm'] == arm and row['position'] == position))
        for arm in policy.ARMS}) for position, task in enumerate(tasks)]
    return rows, summary


def main():
    parser = argparse.ArgumentParser()
    for name in ('freeze', 'raw', 'reviews', 'output'):
        parser.add_argument('--' + name, required=True)
    options = parser.parse_args()
    output = Path(options.output)
    output.mkdir(parents=True, exist_ok=False)
    rows, summary = audit(json.loads(Path(options.freeze).read_text()), Path(options.raw),
                          json.loads(Path(options.reviews).read_text()))
    write(output / 'ROWS.json', rows)
    write(output / 'SUMMARY.json', summary)
    print(json.dumps({arm: {field: summary['arms'][arm][field] for field in
          ('calls', 'initial_success', 'qualified_tasks', 'admitted_rows', 'unreviewed')}
          for arm in policy.ARMS}, indent=2))


if __name__ == '__main__':
    main()
