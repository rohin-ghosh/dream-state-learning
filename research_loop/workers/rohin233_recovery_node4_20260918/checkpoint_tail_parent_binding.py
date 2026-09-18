"""Read-only actual-LOAD binding for Main's C2 checkpoint-tail continuation."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time

from deadline_resume import digest, identity, read, require, sha
from receipt_window import header, read_record


CONTROL = Path('/localhome/local-rohing/orch_r233_C2_checkpoint_tail_20260918/control')
ROOT = '/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life'
JOURNAL = '260be8b8710a42559b291797c6e14983'
WALL = 1789927200
ORIGINAL_SOURCE = '/localhome/local-rohing/orch_r222_C2_20260918_discussion2/source'
ORIGINAL_GUARD = '/localhome/local-rohing/orch_r233_C2_deadline_20260918/control/GUARD.json'
ORIGINAL_GUARD_SHA = '5f8a471647972138f7429d6cafd962241a5363ca1c4f0fa447bfbadcb2de1ded'
COMPLETE_INDEX = 11502
COMPLETE_SHA = '9c59fe6c59a01948b6ffe894aaa681010346ccc671c2f774a10fe7399a49080f'
STATE_SHA = 'bdeb931b6cb171e6ed2a6b40d79827322e1f722bba432d69267d33de56121a19'
SUFFIX_SHA = '440b73e86eadcdc0a4feddee338fb9c7d823b55a1453373c324f92b273f5fa70'
OPTIMIZER_STEPS = 7756


def verify_process(plan, actual, pid, start_ticks, now):
    require(plan['root'] == ROOT and plan['hard_end_unix'] == WALL and now < WALL,
        'exact_C2_root_unexpired_lease_margin')
    require(actual['pid'] == pid and actual['start_ticks'] == start_ticks and actual['uid'] == 2524
        and actual['cwd'] == plan['source_root']
        and actual['argv'][-3:] == ['native', '--config', str(CONTROL / 'GUARD.json')],
        'exact_new_C2_native_not_old_replay')
    selection = plan['checkpoint_tail_recovery']
    require(selection['policy'] == 'R233_PINNED_COMPLETE_TAIL_V1'
        and selection['root'] == str(Path(ROOT) / 'stream') and selection['journal_id'] == JOURNAL
        and selection['complete_index'] == COMPLETE_INDEX and selection['complete_sha256'] == COMPLETE_SHA,
        'same_immutable_COMPLETE11502')


def verify_documents(binding, plan, actual, loaded, wall, now):
    verify_process(plan, actual, binding['native']['pid'], binding['native']['start_ticks'], now)
    require(binding['status'] == 'LOADED' and actual == binding['identity'], 'same_actual_loaded_incarnation')
    require(loaded['journal_id'] == wall['journal_id'] == JOURNAL and loaded['kind'] == 'LOADED'
        and loaded['index'] == binding['loaded']['index'] and loaded['sha256'] == binding['loaded']['sha256']
        and loaded['document']['pid'] == actual['pid'] and loaded['document']['resume'] is True
        and loaded['document']['optimizer_steps'] == OPTIMIZER_STEPS,
        'actual_same_boundary_C2_LOAD')
    require(wall['kind'] == 'WALL_EXTENDED' and COMPLETE_INDEX < wall['index'] < loaded['index']
        and wall['index'] == binding['wall_extended']['index']
        and wall['sha256'] == binding['wall_extended']['sha256']
        and wall['document']['plan_sha256'] == binding['plan_sha256']
        and wall['document']['authorization'] == plan['authorized_wall_extension']
        and wall['document']['authorization']['previous_stream_sha256'] == STATE_SHA
        and wall['document']['authorization']['new_deadline_unix'] == WALL,
        'actual_same_plan_WALL_before_LOAD')


def source_pins(root, pins):
    require(type(pins) is dict and bool(pins), 'nonempty_original_source_pins')
    for relative, expected in pins.items():
        path = Path(relative)
        require(not path.is_absolute() and '..' not in path.parts, 'relative_source_pin')
        require(sha(Path(root) / path) == expected, 'exact_bound_source_bytes:' + relative)


def control_documents(expected_guard_sha):
    require(sha(CONTROL / 'GUARD.json') == expected_guard_sha, 'exact_new_guard_bytes')
    guard = read(CONTROL / 'GUARD.json')
    require(guard['plan_path'] == str(CONTROL / 'PLAN.json')
        and sha(CONTROL / 'PLAN.json') == guard['plan_sha256'], 'exact_new_plan_bytes')
    plan = read(CONTROL / 'PLAN.json')
    source_pins(plan['source_root'], guard['source_pins'])
    require(sha(ORIGINAL_GUARD) == ORIGINAL_GUARD_SHA, 'preserved_original_view_guard')
    original = read(ORIGINAL_GUARD)
    source_pins(ORIGINAL_SOURCE, original['source_pins'])
    return guard, plan


def reference(record):
    return dict(index=record['index'], sha256=record['sha256'])


def observe(pid, start_ticks, expected_guard_sha, max_records=4096):
    require(type(max_records) is int and 1 <= max_records <= 4096, 'bounded_post_complete_observation')
    guard, plan = control_documents(expected_guard_sha)
    actual = identity(pid)
    verify_process(plan, actual, pid, start_ticks, time.time())
    records = Path(ROOT) / 'stream/records'
    anchor = read_record(records / f'{COMPLETE_INDEX:020d}.json', JOURNAL)
    require(anchor['sha256'] == COMPLETE_SHA and anchor['kind'] == 'SLEEP_COMPLETE'
        and anchor['document']['resume_state']['sha256'] == STATE_SHA, 'exact_saved_state_anchor')
    suffix = read_record(records / f'{COMPLETE_INDEX + 1:020d}.json', JOURNAL)
    require(suffix['sha256'] == SUFFIX_SHA and suffix['kind'] == 'R184_LEARN_COMPLETE'
        and suffix['previous_sha256'] == COMPLETE_SHA, 'preserved_complete_suffix')
    wall = None
    loaded = None
    for index in range(COMPLETE_INDEX + 2, COMPLETE_INDEX + 2 + max_records):
        path = records / f'{index:020d}.json'
        if not path.exists():
            break
        metadata = header(path)
        require(metadata['journal_id'] == JOURNAL and metadata['index'] == index,
            'same_journal_post_complete_metadata')
        if metadata['kind'] not in ('LOADED', 'WALL_EXTENDED'):
            continue
        record = read_record(path, JOURNAL)
        intent = read(path.with_name(f'{index:020d}.intent.json'))
        require(intent == dict(schema=record['schema'], journal_id=JOURNAL, index=index,
            previous_sha256=record['previous_sha256'], record_sha256=record['sha256']),
            'actual_receipt_intent_binding')
        if record['kind'] == 'WALL_EXTENDED' and record['document']['plan_sha256'] == guard['plan_sha256']:
            wall = record
        if record['kind'] == 'LOADED' and record['document']['pid'] == pid:
            loaded = record
            break
    require(identity(pid) == actual and sha(CONTROL / 'GUARD.json') == expected_guard_sha
        and sha(CONTROL / 'PLAN.json') == guard['plan_sha256'], 'unchanged_incarnation_during_observation')
    result = dict(schema='R233_CHECKPOINT_TAIL_C2_PARENT_BINDING_V1',
        status='PENDING_ACTUAL_LOAD', observed_utc=datetime.now(timezone.utc).isoformat(),
        native=dict(pid=pid, start_ticks=start_ticks), identity=actual,
        root=ROOT, journal_id=JOURNAL, source_root=plan['source_root'], source_unchanged=False,
        hard_end_unix=WALL, guard_path=str(CONTROL / 'GUARD.json'), guard_sha256=expected_guard_sha,
        plan_sha256=guard['plan_sha256'], complete_index=COMPLETE_INDEX, complete_sha256=COMPLETE_SHA,
        saved_state_sha256=STATE_SHA, original_view_source=ORIGINAL_SOURCE,
        original_view_guard=ORIGINAL_GUARD, original_view_guard_sha256=ORIGINAL_GUARD_SHA,
        original_view_source_pins_sha256=digest(read(ORIGINAL_GUARD)['source_pins']),
        copied_source_pins_sha256=digest(guard['source_pins']), native_signals=[], journal_writes=0,
        parent_started=False, parent_rendered=False, all_exclusions_off_claim=False)
    if loaded is not None:
        require(wall is not None, 'LOAD_without_bound_wall_receipt')
        extended = wall['document']['state']
        require(extended['sha256'] == digest(extended['state']), 'canonical_extended_state')
        expected = dict(anchor['document']['resume_state']['state'], deadline_unix=WALL)
        require(extended['state'] == expected, 'same_whole_state_only_wall_changed')
        result.update(status='LOADED', loaded=reference(loaded), wall_extended=reference(wall),
            loaded_unix=loaded['document']['loaded_unix'], optimizer_steps=OPTIMIZER_STEPS)
        verify_documents(result, plan, actual, loaded, wall, time.time())
    return result


def verify(binding_path, expected_sha256):
    require(sha(binding_path) == expected_sha256, 'exact_new_C2_parent_binding_bytes')
    binding = read(binding_path)
    require(binding['guard_path'] == str(CONTROL / 'GUARD.json'), 'exact_new_C2_control')
    guard, plan = control_documents(binding['guard_sha256'])
    require(guard['plan_sha256'] == binding['plan_sha256']
        and digest(guard['source_pins']) == binding['copied_source_pins_sha256'], 'same_bound_new_source')
    records = Path(ROOT) / 'stream/records'
    loaded = read_record(records / f'{binding["loaded"]["index"]:020d}.json', JOURNAL)
    wall = read_record(records / f'{binding["wall_extended"]["index"]:020d}.json', JOURNAL)
    verify_documents(binding, plan, identity(binding['native']['pid']), loaded, wall, time.time())
    return dict(pid=binding['native']['pid'], loaded_index=loaded['index'], hard_end_unix=WALL)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pid', type=int, required=True)
    parser.add_argument('--start-ticks', required=True)
    parser.add_argument('--guard-sha256', required=True)
    arguments = parser.parse_args()
    print(json.dumps(observe(arguments.pid, arguments.start_ticks, arguments.guard_sha256), sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
