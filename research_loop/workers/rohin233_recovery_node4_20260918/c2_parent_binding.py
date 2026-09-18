"""Read-only binding of the original C2 parent to its actual continued native."""

from pathlib import Path
import time

from deadline_resume import identity, read, require, sha
from receipt_window import read_record


CONTROL = Path('/localhome/local-rohing/orch_r233_C2_deadline_20260918/control')
ROOT = '/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life'
SOURCE = '/localhome/local-rohing/orch_r222_C2_20260918_discussion2/source'
JOURNAL = '260be8b8710a42559b291797c6e14983'
WALL = 1789927200


def verify_documents(binding, plan, actual, loaded, wall, now):
    require(plan['root'] == ROOT and plan['source_root'] == SOURCE
        and plan['hard_end_unix'] == binding['hard_end_unix'] == WALL and now < WALL,
        'same_C2_root_source_long_wall')
    require(actual == binding['identity'] and actual['pid'] == binding['native']['pid']
        and actual['start_ticks'] == binding['native']['start_ticks']
        and actual['uid'] == 2524 and actual['cwd'] == SOURCE
        and actual['argv'][-3:] == ['native', '--config', str(CONTROL / 'GUARD.json')],
        'exact_current_C2_native_identity')
    require(loaded['journal_id'] == wall['journal_id'] == JOURNAL
        and loaded['index'] == binding['loaded']['index']
        and loaded['sha256'] == binding['loaded']['sha256'] and loaded['kind'] == 'LOADED'
        and loaded['document']['pid'] == actual['pid'] and loaded['document']['resume'] is True
        and loaded['document']['optimizer_steps'] == binding['optimizer_steps'],
        'actual_C2_LOAD_same_optimizer')
    require(wall['index'] == binding['wall_extended']['index'] < loaded['index']
        and wall['sha256'] == binding['wall_extended']['sha256'] and wall['kind'] == 'WALL_EXTENDED'
        and wall['document']['plan_sha256'] == binding['plan_sha256']
        and wall['document']['authorization']['new_deadline_unix'] == WALL,
        'actual_C2_WALL_before_LOAD')


def verify(binding_path, expected_sha256):
    require(sha(binding_path) == expected_sha256, 'exact_C2_parent_binding_bytes')
    binding = read(binding_path)
    require(binding['guard_path'] == str(CONTROL / 'GUARD.json')
        and sha(CONTROL / 'GUARD.json') == binding['guard_sha256'], 'exact_C2_guard')
    guard = read(CONTROL / 'GUARD.json')
    require(guard['plan_path'] == str(CONTROL / 'PLAN.json')
        and sha(CONTROL / 'PLAN.json') == guard['plan_sha256'] == binding['plan_sha256'],
        'exact_C2_plan')
    plan = read(CONTROL / 'PLAN.json')
    records = Path(ROOT) / 'stream/records'
    loaded = read_record(records / f'{binding["loaded"]["index"]:020d}.json', JOURNAL)
    wall = read_record(records / f'{binding["wall_extended"]["index"]:020d}.json', JOURNAL)
    verify_documents(binding, plan, identity(binding['native']['pid']), loaded, wall, time.time())
    return dict(pid=binding['native']['pid'], loaded_index=loaded['index'], hard_end_unix=WALL)
