"""Stage response-cadence alternatives; deliberately cannot activate a parent."""

import argparse
import json
from pathlib import Path
import time

from inventory_node1 import HERE, Reader, digest, identity, require, unchanged


PROPOSED = {
    'A': dict(cadence=1, framing='strict-dense every response; long child-facing prompt'),
    'B': dict(cadence=2, framing='transcript-grounded walkthrough'),
    'C': dict(cadence=3, framing='questions-only self-derivation'),
    'D': dict(cadence=3, framing='three-question light steer'),
}


def reserved_cursor(row):
    counts = [row['reserved_cursor_at_start']]
    for attempt in row['attempts']:
        for name in ('response_count', 'source_response_count'):
            value = attempt.get(name)
            if value is not None:
                require(type(value) is int and value >= 0, 'nonnegative_actual_reservation')
                counts.append(value)
        if attempt.get('status') in ('PUBLISHED', 'MISSING', 'SILENT'):
            require('SOURCE.json' in attempt and 'RESULT.json' in attempt
                    and attempt['head_sha256'] == attempt['source_head_sha256']
                    and attempt['response_count'] == attempt['source_response_count'],
                    'bound_terminal_attempt_no_replay')
    require(all(type(value) is int and value >= 0 for value in counts), 'actual_cursor_values')
    return max(counts)


def prepare_rows(inventory):
    parents = inventory['parents']
    require(len(parents) == 8 and {row['physical'] for row in parents} == set(range(8)),
            'exact_eight_node1_slots')
    rows = []
    for row in parents:
        require(row['unique_live_native'] and len(row['natives']) == 1, 'unique_live_child')
        native = row['natives'][0]
        require(native['plan_fields']['root'] == row['fields']['root']
                and native['plan_fields']['physical'] == row['physical'], 'actual_same_life_and_slot')
        control = row['physical'] in (0, 1)
        require(row['controls_frozen'] == control and native['control_native'] == control,
                'no_control_conversion')
        require(row['fields'].get('schedule_on', 'response') == 'response', 'actual_response_clock_only')
        cursor = reserved_cursor(row)
        pending = [attempt['attempt'] for attempt in row['attempts'] if not attempt['settled']]
        publications = [attempt['publication'] for attempt in row['attempts']
                        if attempt.get('status') == 'PUBLISHED']
        rows.append(dict(physical=row['physical'], label=row['label'],
                         current_parent=row['parent'], current_config=row['config'],
                         current_source=row['source'], current_cadence=row['fields']['cadence_responses'],
                         current_output=row['output'], existing_hard_end_unix=row['fields']['hard_end_unix'],
                         reserved_response_cursor=cursor, unsettled_attempts=pending,
                         publications_to_preserve_never_republish=publications,
                         required_action='PRESERVE_FROZEN_CONTROL' if control else 'AWAIT_MAIN_ASSIGNMENT',
                         required_baseline=None if control else 'C2_OBSERVATION_TO_ACTION',
                         wait_for_c2_success=False, unchanged_r166_learning_control=False,
                         initial_baseline_word_cap=None if control else 90,
                         dense_a_requires_main_longcap_pass=not control,
                         completed_sleep_check_after=None if control else 3,
                         incomplete_check_status='UNKNOWN', retirement_authorized=False,
                         proposed_alternatives={} if control else {
                             arm: dict(next_response_threshold=cursor + specification['cadence'], **specification)
                             for arm, specification in PROPOSED.items()},
                         selected_arm=None, config_written=False, first_turn_published=False,
                         request_exposure_verified=False))
    return rows


def revalidate_inputs(inventory, reader):
    for row in inventory['parents']:
        require(unchanged(row['parent'], identity(Path('/proc') / str(row['parent']['pid']))),
                'parent_owner_still_matches')
        for name in ('binding', 'config', 'source', 'operator', 'started'):
            reference = row[name]
            require(digest(reader.raw(reference['path'])) == reference['sha256'], 'unchanged_baseline_' + name)
        require(row['fields']['node'] == 'a100', 'node1_only')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inventory', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    arguments = parser.parse_args()
    require(arguments.inventory.resolve().parent == HERE.resolve(), 'own_inventory_only')
    reader = Reader()
    raw = reader.raw(arguments.inventory)
    require(digest(raw) == arguments.sha256, 'exact_inventory_hash')
    inventory = json.loads(raw)
    rows = prepare_rows(inventory)
    revalidate_inputs(inventory, reader)
    result = dict(schema='ROHIN175_NODE1_STAGING_ONLY_V1', observed_unix=time.time(),
                  inventory=dict(path=str(arguments.inventory), sha256=arguments.sha256), rows=rows,
                  assignment_sha256=None, common_policy_sha256=None,
                  unchanged_r166_learning_control_allowed=False,
                  status='BASELINE_STAGED_NO_ASSIGNMENT_OR_SWITCH', activation_supported=False,
                  reservation_thresholds_are_observations_not_admission=True,
                  requires_fresh_quiet_parent_boundary=True, no_child_changes=True,
                  messages_sent=0, signals=0, sealed_reads=0, key_reads=0,
                  staging_source_sha256=digest(Path(__file__).read_bytes()))
    path = HERE / ('STAGING_' + str(time.time_ns()) + '.json')
    with path.open('x') as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
    print(json.dumps(dict(path=str(path), sha256=digest(path.read_bytes()), status=result['status'])))


if __name__ == '__main__':
    main()
