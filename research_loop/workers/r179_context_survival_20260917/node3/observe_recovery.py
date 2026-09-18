"""Read-only metadata/custody observation of the six already-started recoveries."""

import base64
import hashlib
import json
from pathlib import Path
import re
import time


ROOT = Path('/localhome/local-rohing/orch_r179_node3_recovery_20260917t1818z_2')


def history_progress(records):
    decisions, completed = {}, []
    for record in records:
        document = record['document']
        if record['kind'] == 'CONTEXT_RETAINED':
            decisions[document['cycle']] = dict(document, record_index=record['index'], record_sha256=record['sha256'])
        elif record['kind'] == 'COMPACTION' and 'context_policy' in document:
            policy = document['context_policy']
            decisions[policy['cycle']] = dict(policy, record_index=record['index'], record_sha256=record['sha256'])
        elif record['kind'] == 'SLEEP_COMPLETE':
            history = document['resume_state']['state']['history']
            decision = decisions.get(document['cycle'])
            completed.append(dict(cycle=document['cycle'], record_index=record['index'], record_sha256=record['sha256'],
                optimizer_steps=document['optimizer_steps'], saved_history_sha256=history['state_sha256'],
                context_policy_action=decision['action'] if decision else None,
                retained_history_through_completed_sleep=bool(decision
                    and decision['action'] == 'RETAIN_CONTEXT_ACROSS_SLEEP'
                    and decision['history_sha256_before'] == decision['history_sha256_after'] == history['state_sha256'])))
    return dict(first_context_policy=next(iter(decisions.values()), None), completed_sleeps=completed,
                new_completed_sleep_observed=bool(completed), no_scientific_claim=True)


ROWS = []
for physical in (0, 1, 2, 3, 4, 7):
    output = ROOT / ('control' + str(physical))
    row = dict(physical=physical, receiving_cpu=(output / 'BRANCH_CPU.json').exists(),
               dispatched=(output / 'DISPATCH_ONCE').exists())
    loaded = output / 'LOADED_RECEIPT.json'
    if loaded.exists():
        raw = loaded.read_bytes()
        receipt = json.loads(raw)
        actor = receipt['actor']
        row.update(loaded_receipt=dict(path=str(loaded), sha256=hashlib.sha256(raw).hexdigest(),
            base64=base64.b64encode(raw).decode()), native_pid=actor['pid'], native_start_ticks=actor['start_ticks'],
            saved_cycle=receipt['saved_cycle'], optimizer_steps=receipt['optimizer_steps'],
            unsaved_updates=receipt['unsaved_updates'], hard_end_unix=receipt['hard_end_unix'])
        stat = Path('/proc', str(actor['pid']), 'stat')
        if stat.exists():
            fields = stat.read_text().rsplit(') ', 1)[1].split()
            row.update(actor_state=fields[0], actor_exact_ticks=fields[19] == actor['start_ticks'])
        else:
            row['actor_absent'] = True
    for name in ('SUPERVISOR_FAILED.json', 'EXIT.json', 'SERVICE_EXIT.json', 'MONITOR_TIMEOUT.json'):
        path = output / name
        if path.exists():
            row[name] = json.loads(path.read_bytes())
    paths = sorted(path for path in (output / 'run1/stream/records').glob('*.json')
                   if re.fullmatch(r'\d{20}\.json', path.name))
    if paths:
        head = json.loads(paths[-1].read_bytes())
        row['head'] = dict(index=head['index'], kind=head['kind'],
                           optimizer_step=head['document'].get('optimizer_step'))
        cutoff = json.loads((output / 'RECOVERY_SEGMENT.json').read_bytes())['terminal']['saved']['index']
        fresh = []
        for path in paths:
            if int(path.stem) <= cutoff:
                continue
            record = json.loads(path.read_bytes())
            encoded = json.dumps({key: value for key, value in record.items() if key != 'sha256'},
                                 sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
            if hashlib.sha256(encoded).hexdigest() != record['sha256']:
                raise ValueError('new_operational_record_hash')
            fresh.append(record)
        row['history_progress'] = history_progress(fresh)
    monitor = ROOT / ('DISPATCH_MONITOR_' + str(physical) + '.log')
    if monitor.exists() and 'loaded_receipt' not in row:
        text = monitor.read_text()
        if 'Traceback' in text:
            row['monitor_failure'] = text[-2500:]
    ROWS.append(row)

print(json.dumps(dict(schema='R179_NODE3_RECOVERY_OBSERVATION_V1', rows=ROWS,
    observed_unix=time.time(), metadata_only=True, signals=0), sort_keys=True))
