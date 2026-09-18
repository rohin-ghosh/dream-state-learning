"""Read current node4 clone incarnations and native consumption receipts."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time

from math_c import HOME, WALL, host, read, require


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def load(name, path):
    specification = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def audit(physical):
    root = HOME if physical == 6 else HOME.parent / f'SCALE_physical{physical}'
    paths = sorted((root / 'life/stream/records').glob('[0-9]' * 20 + '.json'))
    records = [read(path) for path in paths]
    times = {int(path.stem): path.stat().st_mtime for path in paths}
    loaded = [record for record in records if record['kind'] == 'LOADED']
    requests = [record for record in records if record['kind'] == 'REQUEST' and record['index'] >= 4]
    responses = [record for record in records if record['kind'] == 'RESPONSE' and record['index'] >= 4]
    row = dict(physical=physical, root=str(root / 'life'), current_native=None, first_loaded=None,
        latest_request=None, total_new_generated_tokens=sum(len(record['document']['response']['token_ids']) for record in responses),
        completed=[dict(cycle=record['document']['cycle'], index=record['index'], sha256=record['sha256'],
            unix=times[record['index']], total_optimizer_steps=record['document'].get('total_optimizer_steps'))
            for record in records if record['kind'] == 'SLEEP_COMPLETE'],
        latest_record=dict(index=records[-1]['index'], kind=records[-1]['kind'], unix=times[records[-1]['index']]),
        compactions=[dict(index=record['index'], sha256=record['sha256'], unix=times[record['index']],
            **{key: record['document'].get(key) for key in ('before_tokens', 'after_tokens', 'threshold_tokens',
            'carry_source_kind', 'raw_history_preserved', 'new_child_distillation', 'working_state_preserved')})
            for record in records if record['kind'] == 'COMPACTION'])
    if loaded:
        first, current = loaded[0], loaded[-1]
        row['first_loaded'] = dict(pid=first['document']['pid'], unix=first['document']['loaded_unix'],
            index=first['index'], sha256=first['sha256'])
        native = current['document']
        process = Path('/proc', str(native['pid']))
        item = dict(pid=native['pid'], unix=native['loaded_unix'], index=current['index'],
            sha256=current['sha256'], alive=process.exists(), optimizer_steps_at_load=native['optimizer_steps'],
            generated_tokens_since_load=sum(len(record['document']['response']['token_ids']) for record in responses
                if record['index'] > current['index']))
        if process.exists():
            try:
                arguments = (process / 'cmdline').read_bytes().rstrip(b'\0').decode().split('\0')
                guard_path = Path(arguments[-1])
                require(arguments[-3:-1] == ['native', '--config'] and process.stat().st_uid == 2524, 'actual_owned_native')
                guard = read(guard_path)
                plan = read(guard['plan_path'])
                require(plan['physical'] == physical and plan['root'] == str(root / 'life')
                    and plan['hard_end_unix'] == WALL and os.readlink(process / 'cwd') == plan['source_root'], 'actual_incarnation_binding')
                item.update(start_ticks=(process / 'stat').read_text().rsplit(')', 1)[1].split()[19],
                    guard=str(guard_path), source=plan['source_root'], max_sleeps=plan['max_sleeps'],
                    think_continuation_policy=plan['think_act_learn'].get('think_continuation_policy'),
                    structured_think_policy=plan['think_act_learn'].get('structured_think_policy'))
            except FileNotFoundError:
                item['alive'] = False
        row['current_native'] = item
    if requests:
        current = requests[-1]
        row['latest_request'] = dict(index=current['index'], sha256=current['sha256'], unix=times[current['index']],
            prompt_tokens=current['document']['prompt_tokens'], all_history_tokens_masked=current['document']['render_receipt']['all_history_tokens_masked'])
    row['think_receipts'] = [dict(kind=record['kind'], index=record['index'], sha256=record['sha256'],
        document={key: value for key, value in record['document'].items() if isinstance(value, (str, int, float, bool)) or value is None},
        explicit_continuation_requests=len(record['document'].get('continuation_requests', [])))
        for record in records if record['kind'] == 'R184_TRANSITION'
        and record['document'].get('from_stage') == 'THINK'][-6:]
    sys.path.insert(0, str(HOME.parent / 'SCALE_physical0/source'))
    load('gpu.orch_r127_pilot_transcript', root / 'read_transcript.py')
    snapshot = load('audit_snapshot_' + str(physical), root / 'read_snapshot.py')
    state = snapshot.genesis(root / 'life')
    try:
        for record in records:
            require(record['sha256'] == digest({key: value for key, value in record.items() if key != 'sha256'}), 'actual_record_digest')
            snapshot._reduce(state, record)
        parent_deliveries = []
        for identifier, delivery in state['delivered'].items():
            if delivery['speaker'] != 'Astra':
                continue
            request = records[delivery['record_index']]
            request_hash = digest({key: value for key, value in request['document'].items() if key != 'resume_state'})
            response = next((record for record in responses if record['document']['request_sha256'] == request_hash), None)
            commit = None if response is None else next((record for record in records
                if record['kind'] in ('COMMITTED', 'CONTEXT_COMMITTED')
                and record['document'].get('source_sha256') == digest(response['document'])), None)
            parent_deliveries.append(dict(inbox_id=identifier, **delivery,
                response_index=None if response is None else response['index'],
                response_sha256=None if response is None else response['sha256'],
                committed_index=None if commit is None else commit['index'],
                committed_sha256=None if commit is None else commit['sha256'],
                native_response_after_render=commit is not None, semantic_uptake_claimed=False))
        row['parent_deliveries'] = parent_deliveries
    except ValueError as error:
        row['parent_reader_error'] = str(error)
    row['parent_withdrawn'] = (root / 'PARENT_WITHDRAWAL_CLOSED.json').exists()
    for name in ('PARENT_WITHDRAWAL_RECONCILED.json', 'SCREEN_COMPLETE.json'):
        if (root / name).exists():
            value = read(root / name)
            row[name] = {key: value.get(key) for key in ('status', 'cycle', 'no_pending_parent_replay', 'completed_unix') if key in value}
    return row


if __name__ == '__main__':
    host()
    print(json.dumps(dict(observed_unix=time.time(), slots=[audit(physical) for physical in (0, 1, 2, 3, 5, 6, 7)]), indent=2))
