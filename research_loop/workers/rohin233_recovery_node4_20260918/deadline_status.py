"""Bounded read-only actual continuation status, never source-staged-as-live."""

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import time

from deadline_resume import TARGETS, digest, identity, read, require, sha


def utc(value):
    return datetime.fromtimestamp(value, timezone.utc).isoformat()


def status(name):
    target = Path(TARGETS[name]['target'])
    control = target / 'control'
    guard, plan = read(control / 'GUARD.json'), read(control / 'PLAN.json')
    launch, saved = read(control / 'LAUNCH.json'), read(control / 'PRESERVED.json')
    timeout = Path('/proc') / str(launch['pid'])
    children = (timeout / 'task' / str(launch['pid']) / 'children').read_text().split()
    natives = [identity(int(pid)) for pid in children]
    natives = [native for native in natives if native['argv'][-3:] == ['native', '--config', str(control / 'GUARD.json')]]
    require(len(natives) == 1, 'one_exact_continued_native')
    native = natives[0]
    require(native['cwd'] == plan['source_root'] and native['uid'] == 2524
        and sha(control / 'GUARD.json') == launch['guard_sha256']
        and sha(control / 'PLAN.json') == launch['plan_sha256'] == guard['plan_sha256'],
        'actual_process_new_guard_plan_source_binding')
    unit = native['cgroup'].split('/')[-1]
    systemd = subprocess.check_output(['systemctl', 'show', unit, '--property=ActiveState,SubState,RuntimeMaxUSec,ExecMainStartTimestamp'], text=True)
    before = read(Path(plan['root']) / 'stream/records' / f'{saved["complete_index"]:020d}.json')
    records = Path(plan['root']) / 'stream/records'
    events = {}
    for path in sorted(records.glob('[0-9]' * 20 + '.json')):
        if int(path.stem) <= saved['complete_index']:
            continue
        with path.open('rb') as stream:
            stream.seek(max(0, path.stat().st_size - 512))
            ending = stream.read()
        if b'"kind":"LOADED"' not in ending and b'"kind":"WALL_EXTENDED"' not in ending:
            continue
        row = read(path)
        require(row['journal_id'] == TARGETS[name]['journal']
            and row['sha256'] == digest({key:value for key,value in row.items() if key != 'sha256'}),
            'canonical_actual_journal_receipt')
        if row['kind'] == 'WALL_EXTENDED' and row['document']['plan_sha256'] == guard['plan_sha256']:
            events['wall_extended'] = row
        if row['kind'] == 'LOADED' and row['document']['pid'] == native['pid']:
            events['loaded'] = row
    old_exit = (read(Path(TARGETS[name]['guard']).parent / 'EXIT.json')['finished_unix'] if name == 'P7'
        else read(target / 'CONTINUATION_EXIT.json')['exited_observed_unix'])
    result = dict(component=name, observed_utc=utc(time.time()), status='NATIVE_REPLAY_NOT_LOADED',
        native=dict(pid=native['pid'], start_ticks=native['start_ticks']),
        hard_end_unix=plan['hard_end_unix'], hard_end_utc=utc(plan['hard_end_unix']),
        lease_end_utc=utc(plan['lease_end_unix']), lease_authority='USER_REPORTED_CONSERVATIVE_DATE_ONLY_SIX_HOUR_MARGIN',
        systemd=dict(line.split('=',1) for line in systemd.strip().splitlines()),
        timeout_argv=(timeout/'cmdline').read_bytes().decode().strip('\0').split('\0'),
        root=plan['root'], source_root=plan['source_root'], guard_path=str(control/'GUARD.json'),
        guard_sha256=launch['guard_sha256'], plan_sha256=launch['plan_sha256'],
        journal_id=TARGETS[name]['journal'], complete_index=saved['complete_index'],
        complete_sha256=saved['complete_sha256'], checkpoint_cycle=before['document']['cycle'],
        optimizer_steps=saved['checkpoint']['optimizer_steps'],
        old_exit_utc=utc(old_exit), old_exit_unix=old_exit, launch_utc=utc(launch['started_unix']),
        source_unchanged=True, training_policy_changed=False, all_exclusions_off_claim=False,
        model_LOAD_pending=True, wall_extended_pending=True,
        actual_native_signals=[] if name == 'P7' else ['EXACT_PIDFD_SIGTERM_AT_DURABLE_COMPLETE'],
        SIGSTOP=False, deliberate_hold=False, retirement=False)
    if 'wall_extended' in events:
        wall = events['wall_extended']
        extended = deepcopy(wall['document']['state'])
        require(extended['sha256'] == digest(extended['state']), 'actual_extended_state_digest')
        extended['state']['deadline_unix'] = before['document']['resume_state']['state']['deadline_unix']
        require(extended['state'] == before['document']['resume_state']['state'], 'whole_state_only_deadline_changed')
        result.update(wall_extended_pending=False, whole_state_only_deadline_changed=True,
            wall_extended=dict(index=wall['index'], sha256=wall['sha256'],
                written_utc=utc((records/f'{wall["index"]:020d}.json').stat().st_mtime),
                authorization=wall['document']['authorization']))
    if 'loaded' in events:
        loaded = events['loaded']
        require('wall_extended' in events and loaded['document']['optimizer_steps'] == saved['checkpoint']['optimizer_steps']
            and loaded['document']['resume'] is True, 'actual_LOAD_same_saved_optimizer_with_wall')
        result.update(status='LOADED', model_LOAD_pending=False,
            loaded=dict(index=loaded['index'], sha256=loaded['sha256'],
                loaded_utc=utc(loaded['document']['loaded_unix']), loaded_unix=loaded['document']['loaded_unix'],
                adapter_sha256=loaded['document']['adapter_sha256']),
            reload_gap_seconds=loaded['document']['loaded_unix'] - old_exit)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('life', choices=TARGETS)
    print(json.dumps(status(parser.parse_args().life), indent=2), flush=True)
