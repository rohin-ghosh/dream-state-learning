"""Stage NODE4 parent-only inputs and custody metadata without publication."""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import time


WORKER = Path(__file__).resolve().parent
ADMISSION_SPEC = importlib.util.spec_from_file_location('node4_control_admission', WORKER / 'r175_control_admission.py')
admission = importlib.util.module_from_spec(ADMISSION_SPEC)
ADMISSION_SPEC.loader.exec_module(admission)
ROOTS = {
    0: '/localhome/local-rohing/orch_r132_kernel_child_20260916_attempt1/run1',
    1: '/localhome/local-rohing/orch_r136_raw_unparented_a40r1_20260916_attempt1/run1',
    3: '/localhome/local-rohing/orch_r136_raw_parented_seed1_a40r3_20260916_attempt1/run1',
    4: '/localhome/local-rohing/orch_r136_kernel_parented_a40r4_20260916_attempt1/run1',
}
EXPECTED = {0: ('B', 2), 1: ('BASELINE_THEN_HANDS_OFF', None), 3: ('D', 3), 4: ('A', 1)}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path, maximum=1048576):
    path = Path(path)
    require(path.is_file() and not path.is_symlink() and path.stat().st_size <= maximum, 'bounded_regular_metadata')
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with Path(path).open('x') as output:
        json.dump(value, output, indent=2, sort_keys=True, allow_nan=False)
        output.write('\n')


def validate_assignment(assignment):
    require(assignment['frozen'] is True and assignment['assignment_owner'] == 'Main', 'Main_frozen_assignment_required')
    require(set(assignment['assignments']) == {'0', '1', '3', '4'}, 'only_four_existing_NODE4_lives')
    for physical, expected in EXPECTED.items():
        row = assignment['assignments'][str(physical)]
        require((row['arm'], row['cadence_responses']) == expected, 'exact_Main_arm_and_cadence')
        require(row['baseline_only'] == (physical == 1), 'raw1_one_baseline_only')
        require(row['group'] == ('raw' if physical in (1, 3) else 'kernel'), 'preserve_pair_grouping')
    require(assignment['baseline_B0_maximum_words'] == 90, 'interim_B0_cap')
    require(assignment['unchanged_hard_end_unix'] == 1789754400, 'original_life_wall')
    return assignment


def custody(row):
    process = Path('/proc', str(row['parent_actor']['pid']))
    before = (process / 'stat').read_text().rsplit(')', 1)[1].split()
    argv = [part.decode() for part in (process / 'cmdline').read_bytes().split(b'\0') if part]
    after = (process / 'stat').read_text().rsplit(')', 1)[1].split()
    expected = row['parent_actor']
    require(before[19] == after[19] == expected['start_ticks'] and after[0] not in ('Z', 'X'), 'same_live_parent_PID_start')
    require(argv == expected['argv'] and process.stat().st_uid == expected['uid']
            and str((process / 'cwd').resolve()) == expected['cwd'], 'same_parent_argv_uid_cwd')
    config_path = Path(row['config_path'])
    config = read(config_path)
    require(sha(config_path) == row['config_sha256'], 'unchanged_predecessor_config')
    output = Path(row['output'])
    started_path = output / 'STARTED.json'
    started = read(started_path)
    require(started['pid'] == expected['pid'] and started['config_sha256'] == sha(config_path), 'actual_started_config_binding')
    clock = config.get('schedule_on', 'response') + '_count'
    cursor = config.get('start_after_' + clock, 0)
    attempts, pending = [], []
    directories = sorted(output.glob('parent_*'))
    require(len(directories) <= 10000, 'bounded_attempt_ledger')
    for directory in directories:
        source_path, result_path = directory / 'SOURCE.json', directory / 'RESULT.json'
        require(directory.is_dir() and not directory.is_symlink(), 'regular_attempt_directory')
        if not source_path.exists() or not result_path.exists():
            pending.append(str(directory))
            continue
        source, result = read(source_path, 16 * 1024 * 1024), read(result_path)
        require(source[clock] >= cursor, 'monotonic_reserved_parent_clock')
        require(result['source_head_sha256'] == source['head_sha256']
                and result['source_response_count'] == source['response_count']
                and result['branch'] == config['branch'], 'actual_result_source_binding')
        cursor = source[clock]
        attempts.append(dict(path=str(directory), source_sha256=sha(source_path), result_sha256=sha(result_path),
            clock_count=cursor, status=result['status'], publication=result.get('inbox_publication'),
            legacy_delivery_receipt_present=(directory / 'DELIVERED.json').exists()))
    return dict(parent_actor=expected, observed_unix=time.time(), config_path=str(config_path), config_sha256=sha(config_path),
        output=str(output), started_sha256=sha(started_path), reserved_clock=clock, reserved_cursor=cursor,
        attempts=attempts, unfinished_attempts=pending, settled_at_observation=not pending,
        final_parent_custody_must_be_revalidated=True, configs_changed=0, signals_sent=0)


def descriptor(physical, assignment, predecessor, caps):
    admission.target(physical, caps.get('root'))
    require(physical in ROOTS and caps['root'] == ROOTS[physical], 'exact_existing_root')
    selected = assignment['assignments'][str(physical)]
    require((physical == 1) == (predecessor is None), 'raw1_has_no_predecessor_parent')
    if predecessor:
        require(predecessor['child_root'] == ROOTS[physical], 'predecessor_same_child_root')
    return dict(schema='R175_NODE4_PREPARED_INPUT_NOT_EXECUTABLE_CONFIG_V1', physical=physical,
        root=ROOTS[physical], assignment=selected, programme=predecessor['declared_programme'] if predecessor else None,
        branch=predecessor['branch'] if predecessor else 'R175_RAW1_BASELINE_THEN_HANDS_OFF',
        predecessor_config=predecessor['config_path'] if predecessor else None,
        predecessor_config_sha256=predecessor['config_sha256'] if predecessor else None,
        predecessor_output=predecessor['output'] if predecessor else None,
        desired_parent_clock='response', desired_cadence_responses=selected['cadence_responses'],
        raw3_preserve_English_and_nonLatin_publication_guard=physical == 3,
        kernel_programme_extension_required=physical == 4,
        legacy_NODE4_cadence_style_wrapper_requires_scoped_replacement=physical in (3, 4),
        start_after_response_count=None, start_cursor_source='Refresh exact reserved predecessor clock at custody transfer; never reset.',
        parent_max_words=None, cap_source='Exact tested Main common helper; never invent a long cap.',
        common_helper_sha256=None, executable=False,
        native_runtime_caps_unchanged=caps['runtime_caps'], native_or_recipe_edits=0,
        baseline_only=physical == 1, ongoing_parent_process_permitted=physical != 1,
        first_published_receipt=None, first_rendered_REQUEST_receipt=None,
        first_exposure_sleep_baseline=None, completed_sleeps_after_exposure=[], required_completed_sleeps=3)


def following_sleeps(exposure, completions):
    require(exposure.get('actual_rendered_REQUEST') is True and exposure.get('publication_bound') is True,
            'actual_publication_bound_rendered_REQUEST_required')
    require(type(exposure.get('request_index')) is int and exposure['request_index'] >= 0, 'actual_exposure_request_index')
    seen = set()
    following = []
    for receipt in sorted(completions, key=lambda row: row['record_index']):
        require(receipt['journal_id'] == exposure['journal_id'], 'same_life_journal')
        require(receipt['kind'] == 'SLEEP_COMPLETE' and receipt['verified'] is True, 'verified_completed_sleeps_only')
        require(receipt['record_sha256'] not in seen, 'no_duplicate_sleep_credit')
        seen.add(receipt['record_sha256'])
        if receipt['record_index'] > exposure['request_index']:
            following.append(receipt)
    return dict(completed_after_actual_first_exposure=len(following), first_three=following[:3],
                three_completed_sleeps_reached=len(following) >= 3, generation_or_learning_claim=False)


def prepare(destination):
    current_authority = admission.authority()
    destination = Path(destination).resolve()
    require(destination.parent == WORKER and destination.name.startswith('prepared_'), 'new_own_worker_stage_only')
    assignment = validate_assignment(read(WORKER / 'R175_FROZEN_ASSIGNMENT.json'))
    parents = {row['physical']: row for row in read(WORKER / 'PARENT_CONFIG_INVENTORY.json')['rows']}
    caps = {row['physical']: row for row in read(WORKER / 'R175_TASK_CAPS_PREPARATION.json')['lives']}
    require(set(parents) == {0, 3, 4} and set(caps) == set(ROOTS), 'complete_exact_predecessor_inventory')
    custody_receipts = {physical: custody(row) for physical, row in parents.items()}
    destination.mkdir()
    for physical in (0, 3, 4):
        lane = destination / f'physical{physical}'
        lane.mkdir()
        write(lane / 'INPUTS.json', descriptor(physical, assignment, parents.get(physical), caps[physical]))
        if physical in parents:
            write(lane / 'PREDECESSOR_CONFIG.json', read(parents[physical]['config_path']))
            write(lane / 'CUSTODY_OBSERVATION.json', custody_receipts[physical])
    receipt = dict(schema='R175_NODE4_PARENT_INPUT_STAGE_V1', observed_unix=time.time(), stage=str(destination),
        assignment_sha256=sha(WORKER / 'R175_FROZEN_ASSIGNMENT.json'), stage_source_sha256=sha(__file__),
        files_sha256={str(path.relative_to(destination)): sha(path) for path in sorted(destination.glob('physical*/*.json'))},
        native_restarts=0, parent_signals=0, publications=0, provider_calls=0,
        control_exclusion=current_authority, excluded_physicals=[1],
        status='PREPARED_INPUTS_AWAIT_EXACT_COMMON_HELPER_API_AND_BYTES')
    write(destination / 'PREPARED.json', receipt)
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    print(json.dumps(prepare(options.output), sort_keys=True))
