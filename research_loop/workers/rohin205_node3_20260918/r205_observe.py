"""Bounded node3 receipt capture; no GPU-activity inference of LOADED."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import socket
import time

from r209_node3_audit import metadata, read_record


ROOT = Path(__file__).resolve().parent
ARMS = ('frozen_c2', 'fresh_math', 'peer_math', 'peer_repo', 'p4', 'p32', 'lr03', 'lr3',
    'conversational', 'r213_math_a', 'r213_math_c', 'r213_math_b_fork',
    'r213_siege_scout_fork', 'r213_siege_negotiator_fork',
    'r213_siege_quartermaster_fork', 'r213_siege_challenger_fork')


def main():
    observed = datetime.now(timezone.utc)
    result = dict(observed_utc=observed.isoformat(), hostname=socket.gethostname(), arms={},
        unique_loaded=0, current_native_count=0, completed_preserved_incarnations=0)
    for name in ARMS:
        root = ROOT / name
        if not root.exists():
            result['arms'][name] = dict(status='NOT_STAGED')
            continue
        row = dict(status='STAGED_NOT_DISPATCHED', root=str(root))
        active_path = root / 'ACTIVE_RUNTIME.json'
        active = json.loads(active_path.read_bytes()) if active_path.exists() else dict(control=str(root / 'control'))
        control = Path(active['control'])
        row['active_control'] = str(control)
        if (control / 'PLAN.json').exists():
            plan = json.loads((control / 'PLAN.json').read_bytes())
            row.update(physical=plan['physical'], trial_id=plan['think_act_learn']['trial_id'],
                plan_sha256=hashlib.sha256((control / 'PLAN.json').read_bytes()).hexdigest(),
                policy=plan['think_act_learn'].get('prose_target_filter'))
        if (root / 'DISPATCHED.json').exists():
            row.update(status='DISPATCHED_NOT_LOADED_PROOF', dispatch=json.loads((root / 'DISPATCHED.json').read_bytes()))
        for filename in ('OUTER_FAILED.json', 'FAILED.json', 'EXIT.json', 'OUTER_EXIT.json', 'CONFINEMENT_CHILD.json'):
            if (control / filename).exists():
                row[filename] = json.loads((control / filename).read_bytes())
        paths = sorted((root / 'raw/stream/records').glob('[0-9]' * 20 + '.json'))
        responses, stages = [], {}
        for path in paths:
            kind = metadata(path)
            if kind == 'RESPONSE':
                responses.append(path)
                continue
            if kind not in ('LOADED', 'R184_STAGE', 'R184_LEARN_COMPLETE', 'R205_PEER_THINK_INPUT', 'TERMINAL'):
                continue
            record = read_record(path)
            document = record['document']
            bound = dict(index=record['index'], sha256=record['sha256'], path=str(path))
            if record['kind'] == 'LOADED':
                responses = []
                row.update(status='LOADED', loaded=dict(bound, **{key: document.get(key) for key in
                    ('pid', 'loaded_unix', 'optimizer_steps', 'adapter_sha256', 'base_sha256', 'resume', 'plasticity')}))
                try:
                    command = Path('/proc', str(document['pid']), 'cmdline').read_bytes().split(b'\0')
                    process_state = Path('/proc', str(document['pid']), 'stat').read_text().rsplit(')', 1)[1].split()[0]
                    row['native_process_identity_present'] = str(control / 'GUARD.json').encode() in command and process_state not in ('Z', 'X')
                    row['process_state'] = process_state
                except FileNotFoundError:
                    row['native_process_identity_present'] = False
            elif record['kind'] == 'R184_STAGE':
                stages[document['source_sha256']] = document['stage']
                if document.get('stage') == 'ACT':
                    row.setdefault('first_ACT', dict(bound, stage='ACT', segment=document.get('segment')))
            elif record['kind'] == 'R184_LEARN_COMPLETE':
                row['latest_complete'] = dict(bound, cycle=document['cycle'], optimizer_steps=document['checkpoint']['optimizer_steps'])
            elif record['kind'] == 'TERMINAL':
                row['terminal'] = dict(bound, **document)
        if control == root / 'r210_enrichment/control' and responses:
            row['r210_child_outputs'] = {}
            for label, path in (('first', responses[0]), ('latest', responses[-1])):
                response = read_record(path)
                document = response['document']
                source = hashlib.sha256(json.dumps(document, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
                row['r210_child_outputs'][label] = dict(index=response['index'], sha256=response['sha256'],
                    path=str(path), raw=document['response']['raw'], stage=stages.get(source),
                    finished_unix=document.get('finished_unix'), source_sha256=source)
        result['unique_loaded'] += int('loaded' in row)
        result['current_native_count'] += int(row.get('native_process_identity_present', False))
        if 'loaded' in row and not row.get('native_process_identity_present'):
            row['status'] = 'HISTORICAL_LOADED_NOT_CURRENT'
            if control != root / 'control' and (control.parent / 'DISPATCHED.json').exists():
                row['status'] = 'R210_DISPATCHED_NOT_CURRENT_LOADED'
        if (row.get('terminal', {}).get('status') == 'R184_SCREEN_STOP'
                and row.get('terminal', {}).get('index', -1) > row.get('loaded', {}).get('index', -1)
                and row.get('EXIT.json', {}).get('exit_code') == 0):
            row['status'] = 'SCREEN_COMPLETE_PRESERVED'
            result['completed_preserved_incarnations'] += 1
        result['arms'][name] = row
    destination = ROOT / ('ACTUAL_' + observed.strftime('%Y%m%dT%H%M%SZ') + '.json')
    with destination.open('x') as output:
        json.dump(result, output, sort_keys=True, indent=2)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
