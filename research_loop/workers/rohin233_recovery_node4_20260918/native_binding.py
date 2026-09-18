"""Exact actual-incarnation binding for the existing P7 CPU endpoint."""

import hashlib
import json
import os
from pathlib import Path
import time

from receipt_window import read_record


JOURNAL = 'e9d22d1e26234c4bbac761922929365f'
CONTROL = Path('/localhome/local-rohing/orch_r233_p7_deadline_20260918/control')
WALL = 1790359200


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_loaded(binding, loaded, wall):
    require(binding['journal_id'] == JOURNAL and loaded['journal_id'] == JOURNAL
        and wall['journal_id'] == JOURNAL, 'same_P7_journal_no_alias')
    require(loaded['kind'] == 'LOADED' and loaded['index'] == binding['loaded_index']
        and loaded['sha256'] == binding['loaded_sha256'] and loaded['document']['resume'] is True
        and loaded['document']['pid'] == binding['pid'], 'actual_new_native_LOADED')
    require(wall['kind'] == 'WALL_EXTENDED' and wall['sha256'] == binding['wall_sha256']
        and wall['index'] == binding['wall_index'] < loaded['index']
        and wall['document']['plan_sha256'] == binding['plan_sha256']
        and wall['document']['authorization']['new_deadline_unix'] == WALL,
        'actual_supported_wall_before_LOAD')


def verify(path, root, source, now=None):
    binding = json.loads(Path(path).read_bytes())
    require(binding['guard_path'] == str(CONTROL / 'GUARD.json')
        and binding['previous_pid'] == 1100592 and binding['hard_end_unix'] == WALL,
        'scoped_P7_native_continuation_only')
    guard_path = Path(binding['guard_path'])
    require(sha(guard_path) == binding['guard_sha256'], 'exact_new_guard_bytes')
    guard = json.loads(guard_path.read_bytes())
    plan_path = Path(guard['plan_path'])
    require(plan_path == CONTROL / 'PLAN.json' and sha(plan_path) == binding['plan_sha256']
        == guard['plan_sha256'], 'same_new_plan_bytes')
    plan = json.loads(plan_path.read_bytes())
    require(plan['root'] == str(Path(root) / 'life') and plan['source_root'] == str(source)
        and plan['hard_end_unix'] == guard['hard_end_unix'] == WALL
        and (time.time() if now is None else now) < WALL, 'actual_new_native_wall_root_source')
    process = Path('/proc') / str(binding['pid'])
    fields = (process / 'stat').read_text().rsplit(') ', 1)[1].split()
    require(fields[19] == binding['start_ticks'] and fields[0] != 'Z'
        and process.stat().st_uid == 2524 and os.readlink(process / 'cwd') == str(source),
        'exact_new_live_native_identity')
    argv = (process / 'cmdline').read_bytes().decode().strip('\0').split('\0')
    require(argv == binding['argv'] and argv[-2:] == ['--config', str(guard_path)]
        and (process / 'cgroup').read_text().strip() == binding['cgroup']
        == '0::/system.slice/' + guard['device_containment']['unit'] + '.service',
        'exact_new_native_command_and_containment')
    records = Path(root) / 'life/stream/records'
    loaded = read_record(records / f'{binding["loaded_index"]:020d}.json', JOURNAL)
    wall = read_record(records / f'{binding["wall_index"]:020d}.json', JOURNAL)
    verify_loaded(binding, loaded, wall)
    return binding
