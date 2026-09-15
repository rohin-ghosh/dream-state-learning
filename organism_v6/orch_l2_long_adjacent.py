"""Already-informed, fixed-cohort LONG checkpoint diagnostic; no training."""

import json
import math
from pathlib import Path

from organism_v6 import orch_l2_adjacent as adjacent


require = adjacent.require
read = adjacent.read
digest = adjacent.digest
SIDES = adjacent.SIDES
CLAIM = 'EXPLORATORY_LONG_C1_SAME_COHORT_CHECKPOINT_DIAGNOSTIC_NO_H1_H2_OR_TRAINING_REPLICATION'
DISCLOSURE = ('Main already knew LONG historical 11->8->9->9 on DIFFERENT stage cohorts '
              'before selection. Neither selection nor interpretation is blind or confirmatory. '
              'This compares immediate pre/post sleep states on the SAME stored C1 cohort; '
              'fresh processes are not independent training replications.')


def select_first(shared_root):
    shared_root = Path(shared_root)
    previous = adjacent.identity_fields(read(shared_root / 'INITIAL.json'))
    require(previous['state_sha256'] == adjacent.shared.INITIAL_STATE, 'initial_child_changed')
    cohort = read(shared_root / 'COHORT.json')
    checked = []
    for cycle in (1, 2, 3):
        folder = shared_root / 'LONG' / f'cycle{cycle}' / 'sleep'
        receipt_path = folder / 'COMPLETE.json'
        require(receipt_path.exists(), 'first_missing_LONG_sleep_cannot_skip')
        receipt = read(receipt_path)
        require(receipt['status'] == 'COMPLETE' and receipt['arm'] == 'LONG'
                and receipt['phase'] == 'sleep' and receipt['cycle'] == cycle, 'completed_LONG_sleep_required')
        require(receipt['input_adapter'] == previous, 'immediate_previous_child_drift')
        output = adjacent.identity_fields(receipt['output_adapter'])
        updates = receipt['updates']
        require(type(updates) is int and 0 <= updates <= adjacent.shared.CAPS['updates_per_sleep'],
                'actual_update_count')
        require(type(receipt['unchanged']) is bool and receipt['unchanged'] ==
                (output['state_sha256'] == previous['state_sha256']), 'unchanged_receipt_drift')
        checked.append(dict(cycle=cycle, updates=updates, complete_sha256=adjacent.bridge.file_sha256(receipt_path)))
        if updates == 0:
            require(output == previous and receipt['fits'] == 0, 'zero_update_must_preserve_child')
            previous = output
            continue
        require(receipt['fits'] == 1, 'actual_fit_required')
        loaded_path, losses_path = folder / 'LOADED.json', folder / 'LOSSES.jsonl'
        loaded = read(loaded_path)
        require(loaded['observed'] == previous and loaded['phase'] == 'sleep'
                and loaded['process'] == receipt['process'], 'actual_mounted_input_drift')
        losses = [json.loads(line) for line in losses_path.read_text().splitlines()]
        require([entry['update'] for entry in losses] == list(range(1, updates + 1))
                and all(math.isfinite(entry['loss']) for entry in losses), 'actual_optimizer_ledger_mismatch')
        require(cycle == 1 and updates == 28, 'this_assignment_only_LONG_C1_28_updates')
        return dict(status='SELECTED', policy='FIRST_COMPLETED_POSITIVE_LONG_SLEEP', cycle=cycle,
                    previous=previous, output=output, actual_updates=updates, checked=checked,
                    cohort_sha256=digest(cohort), held_sha256=digest(cohort['held'][cycle]),
                    complete_sha256=adjacent.bridge.file_sha256(receipt_path),
                    loaded_sha256=adjacent.bridge.file_sha256(loaded_path),
                    losses_sha256=adjacent.bridge.file_sha256(losses_path),
                    predecessor_process=receipt['process'], claim=CLAIM, disclosure=DISCLOSURE)
    raise ValueError('no_positive_LONG_sleep')


def paired_rows(previous, output):
    require(len(previous) == len(output) == 16, 'exact_paired_episode_denominator')
    rows = []
    for index, (before, after) in enumerate(zip(previous, output), 1):
        require(before['task'] == after['task'], 'paired_task_drift')
        rows.append(dict(episode=index, task=before['task'], previous=before['correct'],
                         output=after['correct'], previous_reads=before['reads'], output_reads=after['reads'],
                         previous_routes=before['routes'], output_routes=after['routes']))
    return dict(rows=rows, improved=sum(not row['previous'] and row['output'] for row in rows),
                regressed=sum(row['previous'] and not row['output'] for row in rows),
                both_correct=sum(row['previous'] and row['output'] for row in rows),
                both_incorrect=sum(not row['previous'] and not row['output'] for row in rows))
