"""Replay exact native receipts, then apply bound fulltext/prefix decisions."""

import argparse
import json
from pathlib import Path

from organism_v6 import orch_oracle_repair as policy


def collect(root, document):
    tasks = policy.validate_roster(document)
    by_id = {task['id']: task for task in tasks}
    rows = []
    complete = True
    for shard in range(4):
        directory = root / f'shard{shard}'
        paths = sorted(directory.glob('CALL_*.json'))
        expected_order = []
        actual_order = []
        shard_rows = {}
        for path in paths:
            row = json.loads(path.read_text())
            task = by_id[row['task_id']]
            if task['shard'] != shard:
                raise ValueError('task_device_assignment_drift')
            key = (row['task_id'], row['branch'], row['kind'])
            if key in shard_rows:
                raise ValueError('duplicate_native_key')
            own_repair = shard_rows.get((task['id'], row['branch'], 'repair'))
            repair_raw = own_repair['target'] if own_repair else None
            messages, student = policy.prompt(task, row['branch'], row['kind'], repair_raw)
            if row['kind'] == 'record' and not own_repair['outcome_pass']:
                raise ValueError('record_after_wrong_repair')
            if row['call']['messages'] != messages or row['student_prefix'] != student:
                raise ValueError('actor_or_neutral_prefix_bytes_changed')
            replay = policy.capture(task, row['branch'], row['kind'], row['call'], student, row['prefix_token_ids'])
            for field in ('target', 'target_sha256', 'student_prefix_sha256', 'outcome_pass',
                          'token_contract_pass', 'candidate', 'generated_tokens', 'prior_sha256',
                          'target_token_ids', 'labels', 'teacher_loss'):
                if replay[field] != row[field]:
                    raise ValueError('native_capture_replay_mismatch:' + field)
            shard_rows[key] = row
            actual_order.append(key)
            rows.append(dict(row, source_path=str(path), source_sha256=policy.sha256(path)))
        for task in tasks:
            if task['shard'] != shard:
                continue
            for branch in task['branch_order']:
                key = (task['id'], branch, 'repair')
                expected_order.append(key)
                if shard_rows.get(key, {}).get('outcome_pass'):
                    expected_order.append((task['id'], branch, 'record'))
        if actual_order != expected_order[:len(actual_order)]:
            raise ValueError('prospective_branch_or_task_order_changed')
        marker = directory / 'COMPLETE.json'
        if not marker.is_file():
            complete = False
            continue
        receipt = json.loads(marker.read_text())
        if (receipt['status'] != 'COMPLETE' or receipt['native_calls'] != len(paths)
                or receipt['adapter_state'] != '37ec37884e4b0b679edd1dba1be1dec3474589e992649f3a33e7e3b1ec78b8c0'
                or receipt['frozen_base_unchanged'] is not True
                or receipt['fits'] != 0 or receipt['updates'] != 0
                or actual_order != expected_order):
            raise ValueError('native_completion_integrity_failure')
    terminal = root / 'TERMINAL.json'
    if not terminal.exists() or json.loads(terminal.read_text())['status'] != 'COMPLETE':
        complete = False
    return rows, complete


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--roster', type=Path, required=True)
    parser.add_argument('--reviews', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    options.output.mkdir(exist_ok=False)
    document = json.loads(options.roster.read_text())
    rows, complete = collect(options.native, document)
    if options.reviews:
        decisions = json.loads(options.reviews.read_text())['decisions']
        expected = {f"{row['task_id']}:{row['branch']}:{row['kind']}" for row in rows}
        if set(decisions) != expected:
            raise ValueError('one_fulltext_decision_per_actual_call_required')
        rows = [policy.review_row(row, decisions[f"{row['task_id']}:{row['branch']}:{row['kind']}"])
                for row in rows]
    summary = policy.reduce_rows(document, rows, complete)
    summary.update(roster_sha256=policy.sha256(options.roster),
                   reviews_sha256=policy.sha256(options.reviews) if options.reviews else None)
    policy.write(options.output / 'ROWS.json', rows)
    policy.write(options.output / 'SUMMARY.json', summary)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
