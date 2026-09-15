"""Bounded, read-only reduction of prospective admissions and actual loss receipts."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import time


HARD_END = 1789491360


def read(path):
    return json.loads(Path(path).read_text())


def binding(path):
    return dict(path=str(path), sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest())


def admission_rate(decisions, now):
    accepted = [row for row in decisions if row.get('status') == 'ADMITTED']
    return dict(new_unique_total=len(accepted),
                newly_admitted_last3600=sum(now - 3600 <= row['admitted_unix'] <= now for row in accepted),
                last_admission_unix=max((row['admitted_unix'] for row in accepted), default=None))


def selected_new(loss, eligible, original_targets):
    if loss['eligible_supervised_tokens'] <= 0:
        return []
    return [dict(source_task_id=eligible[index]['source_task_id'],
                 target_sha256=eligible[index]['target_sha256'],
                 source_call_sha256=eligible[index]['source_call_sha256'],
                 update=loss['update'], finished_unix=loss['finished_unix'],
                 eligible_supervised_tokens=loss['eligible_supervised_tokens'])
            for source, index in loss['selections']
            if source == 'eligible' and eligible[index]['target_sha256'] not in original_targets]


def snapshot(root, now=None):
    now = time.time() if now is None else now
    root = Path(root)
    original = read(root.parent / 'experience_c1/ELIGIBLE.json')['rows']
    original_targets = {row['target_sha256'] for row in original}
    decisions = read(root / 'ADMISSION_DECISIONS.json')
    result = dict(observed_unix=now, root=str(root),
                  admissions=admission_rate(decisions['decisions'], now),
                  original_unique=len(original_targets), teacher_l2_admitted=0,
                  measured_persistence_claim=False, arms={},
                  source_bindings={name:binding(root/name) for name in
                                   ['RUNTIME.json','REVIEWS.json','ADMISSION_DECISIONS.json']})
    for arm in ('FULL','CONTROL'):
        heartbeat_path = root / ('HEARTBEAT_' + arm + '.json')
        arm_result = dict(heartbeat=read(heartbeat_path) if heartbeat_path.exists() else None,
                          trained_new_targets=[], checkpoints=[], loaded=[], latest_update=None)
        for folder in sorted((root / 'versions').iterdir()):
            eligible = read(folder / 'ELIGIBLE.json')['rows']
            for segment in sorted((folder / 'fit' / arm).glob('segment*')):
                loaded_path = segment / 'RANK0_LOADED.json'
                if loaded_path.exists():
                    arm_result['loaded'].append(dict(binding(loaded_path), **read(loaded_path)))
                loss_path = segment / 'RANK0_LOSSES.jsonl'
                if loss_path.exists():
                    with loss_path.open() as stream:
                        for line in stream:
                            if not line.endswith('\n'):
                                continue
                            loss = json.loads(line)
                            arm_result['latest_update'] = loss['update']
                            arm_result['trained_new_targets'].extend(selected_new(loss,eligible,original_targets))
                complete = segment / 'COMPLETE.json'
                if complete.exists():
                    commit = read(complete)
                    readouts = {condition:binding(segment/'readout'/condition/'COMPLETE.json')
                                for condition in ('ON','OFF')
                                if (segment/'readout'/condition/'COMPLETE.json').exists()}
                    arm_result['checkpoints'].append(dict(binding(complete), **commit, readouts=readouts))
        targets = arm_result['trained_new_targets']
        arm_result['trained_new_unique'] = len({row['target_sha256'] for row in targets})
        arm_result['new_target_exposures'] = len(targets)
        arm_result['new_target_tokens'] = sum(row['eligible_supervised_tokens'] for row in targets)
        arm_result['last_new_target_feed_unix'] = max((row['finished_unix'] for row in targets),default=None)
        arm_result['trained_new_targets'] = targets[-32:]
        result['arms'][arm] = arm_result
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--watch', action='store_true')
    arguments = parser.parse_args()
    while True:
        document = snapshot(arguments.root)
        if not arguments.watch:
            print(json.dumps(document, indent=2))
            break
        output = arguments.root / 'feed_status'
        output.mkdir(exist_ok=True)
        path = output / (str(time.time_ns()) + '.json')
        with path.open('x') as stream:
            json.dump(document,stream,indent=2)
        temporary = output / ('.latest.' + str(os.getpid()))
        temporary.write_text(json.dumps(dict(binding(path),observed_unix=document['observed_unix'])))
        os.replace(temporary,output/'LATEST.json')
        if time.time() >= HARD_END:
            break
        time.sleep(min(60,max(0,HARD_END-time.time())))
