"""CPU-only retry1 evidence; never starts, signals or edits a native."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time


ROOT = Path('/localhome/local-rohing/orch_r201_node4_20260918/node4/R195_FLEET/SCALE_physical3')
TARGET = ROOT / 'r233_lease_continuation_retry1'
CONTROL = TARGET / 'control'
SOURCE = TARGET / 'source'
CPU = ROOT / 'r233_recovery'
BINDING = CPU / 'P3_RETRY_BINDING.json'
JOURNAL_ID = '0727d448bca644bfa64f1a1f65c1f21f'
END_UNIX = 1790359200


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def read(path):
    return json.loads(path.read_bytes())


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def content_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def immutable(path, value):
    if path.exists():
        require(read(path) == value, 'preserve_existing_immutable:' + path.name)
        return
    with path.open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def record(path):
    value = read(path)
    require(content_digest({key: item for key, item in value.items() if key != 'sha256'}) == value['sha256'],
        'journal_record_integrity')
    require(value['journal_id'] == JOURNAL_ID, 'same_original_P3_journal')
    return value


def process(pid):
    path = Path('/proc') / str(pid)
    try:
        fields = path.joinpath('stat').read_text().rsplit(') ', 1)[1].split()
        command = path.joinpath('cmdline').read_bytes()
        return dict(pid=pid, start_ticks=fields[19], state=fields[0],
            source=str(path.joinpath('cwd').resolve()), command_sha256=hashlib.sha256(command).hexdigest(),
            guard_argument_present=str(CONTROL / 'GUARD.json').encode() in command.split(b'\0'))
    except (FileNotFoundError, ProcessLookupError):
        return None


def same_process(actual, expected):
    return (actual is not None and actual.get('state') not in ('Z', 'X', None)
        and actual.get('guard_argument_present') is True
        and all(actual.get(key) == expected.get(key) and actual.get(key) is not None
            for key in ('pid', 'start_ticks', 'source', 'command_sha256')))


def verify_recovery_record(value, receipt, checksum):
    document = value['document']
    require(value['kind'] == 'R233_P3_RECOVERED_BOUNDARY' and value['journal_id'] == JOURNAL_ID
        and receipt['journal_id'] == JOURNAL_ID
        and value['index'] == receipt['old_head_index'] + 1
        and value['previous_sha256'] == receipt['old_head_sha256']
        and document['receipt_sha256'] == checksum
        and document['state']['sha256'] == receipt['saved_state_sha256']
        and content_digest(document['state']['state']) == receipt['saved_state_sha256'],
        'verified_original_or_retry_parent_cursor_recovery')


def verify_configuration(guard):
    require(guard['hard_end_unix'] == END_UNIX and time.time() < END_UNIX, 'current_authorized_retry_wall')
    for name in ('plan', 'lease'):
        path = Path(guard[name + '_path'])
        require(path == CONTROL / (name.upper() + '.json') and digest(path) == guard[name + '_sha256'],
            'exact_retry_' + name)
    plan, lease = read(CONTROL / 'PLAN.json'), read(CONTROL / 'LEASE.json')
    require(plan['source_root'] == str(SOURCE) and plan['hard_end_unix'] == lease['hard_end_unix'] == END_UNIX
        and lease['lease_end_unix'] >= END_UNIX + 21600, 'same_retry_source_inside_lease_margin')
    require(bool(guard['source_pins']), 'native_source_manifest_required')
    for relative, checksum in guard['source_pins'].items():
        path = SOURCE / relative
        require(path.resolve().is_relative_to(SOURCE.resolve()) and digest(path) == checksum,
            'unchanged_guard_bound_native_source')
    return content_digest(guard['source_pins'])


def observe():
    result = dict(observed_utc=datetime.now(timezone.utc).isoformat(), life='P3', node='node4', gpu=3,
        retry='r233_lease_continuation_retry1', status='WAITING_RETRY_CONTROL', binding=None,
        native=None, loaded=None, wall_extended=None, target_deadline_unix=END_UNIX,
        native_signals=[], gpu_launches=0)
    if not (CONTROL / 'RECOVERY.json').is_file():
        return result
    recovery = read(CONTROL / 'RECOVERY.json')
    require(recovery['journal_id'] == JOURNAL_ID and recovery['old_native_absent']
        and recovery['old_native_pid'] == 598987 and recovery['old_native_start_ticks'] == '32509102',
        'exact_failed_attempt1_recovery_receipt')
    complete_path = Path(recovery['complete_path'])
    require(complete_path == ROOT / 'life/stream/records/00000000000000005243.json', 'same_COMPLETE5243')
    complete = record(complete_path)
    require(complete['kind'] == 'SLEEP_COMPLETE' and complete['document']['cycle'] == 153
        and complete['document']['status'] == 'COMPLETE'
        and complete['sha256'] == recovery['complete_sha256'], 'same_coherent_sleep153')
    result.update(status='RETRY_CPU_REPLAY_OR_LOAD_PENDING', complete_index=5243, complete_cycle=153,
        recovery_sha256=digest(CONTROL / 'RECOVERY.json'), old_head_index=recovery['old_head_index'])
    if not (CONTROL / 'RECOVERY_APPENDED.json').is_file():
        return result
    appended = read(CONTROL / 'RECOVERY_APPENDED.json')
    require(appended['index'] == recovery['old_head_index'] + 1, 'retry_recovery_floor')
    recovery_record = record(ROOT / f"life/stream/records/{appended['index']:020d}.json")
    require(recovery_record['sha256'] == appended['sha256']
        and recovery_record['document']['receipt_path'] == str(CONTROL / 'RECOVERY.json'),
        'exact_appended_retry_recovery_record')
    verify_recovery_record(recovery_record, recovery, result['recovery_sha256'])
    paths = sorted((ROOT / 'life/stream/records').glob('[0-9]' * 20 + '.json'))
    for path in paths:
        if int(path.stem) <= appended['index']:
            continue
        value = read(path)
        if value['kind'] not in ('LOADED', 'WALL_EXTENDED'):
            continue
        value = record(path)
        selected = dict(index=value['index'], sha256=value['sha256'])
        if value['kind'] == 'LOADED':
            selected.update(pid=value['document']['pid'], loaded_unix=value['document']['loaded_unix'],
                optimizer_steps=value['document']['optimizer_steps'], resume=value['document']['resume'])
            result['loaded'] = selected
        else:
            document = value['document']
            state = document['state']
            require(document['authorization']['new_deadline_unix'] == END_UNIX
                and state['state']['deadline_unix'] == END_UNIX
                and content_digest(state['state']) == state['sha256'], 'actual_retry_wall_adopted')
            result['wall_extended'] = dict(selected, deadline_unix=END_UNIX, working_state_sha256=state['sha256'])
    if result['loaded'] is None:
        return result
    loaded = result['loaded']
    actual = process(loaded['pid'])
    result['native'] = actual
    if actual is None or actual['state'] in ('Z', 'X'):
        result['status'] = 'RETRY_LOADED_BUT_NATIVE_EXITED_NO_PARENT'
        return result
    require(actual['source'] == str(SOURCE) and actual['guard_argument_present'], 'actual_retry_native_source_and_guard')
    require(loaded['pid'] not in (237705, 598987) and loaded['resume'] is True,
        'new_retry_saved_boundary_incarnation')
    wall = result['wall_extended']
    require(wall is not None and appended['index'] < wall['index'] < loaded['index'], 'actual_retry_LOAD_after_WALL')
    guard = read(CONTROL / 'GUARD.json')
    source_manifest = verify_configuration(guard)
    require(same_process(process(loaded['pid']), actual), 'same_retry_process_after_source_verification')
    binding = dict(pid=actual['pid'], start_ticks=actual['start_ticks'], command_sha256=actual['command_sha256'],
        source=str(SOURCE), loaded_index=loaded['index'], loaded_sha256=loaded['sha256'],
        journal_id=JOURNAL_ID, hard_end_unix=END_UNIX, wall_index=wall['index'], wall_sha256=wall['sha256'],
        guard_sha256=digest(CONTROL / 'GUARD.json'), plan_sha256=guard['plan_sha256'],
        recovery_sha256=result['recovery_sha256'], source_manifest_sha256=source_manifest)
    result.update(status='RETRY_LOADED_ALIVE_WALL_VERIFIED', binding=binding)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bind', action='store_true')
    options = parser.parse_args()
    evidence = observe()
    if options.bind:
        require(evidence['binding'] is not None, 'actual_retry_LOAD_required_before_binding')
        immutable(BINDING, evidence['binding'])
        evidence['binding_persisted'] = True
    print(json.dumps(evidence, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
