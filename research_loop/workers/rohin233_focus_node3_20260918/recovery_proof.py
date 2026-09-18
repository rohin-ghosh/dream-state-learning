"""Bounded sanitized projection of actual same-journal recovery, never staging-as-live."""

import argparse
from pathlib import Path
import json
import os

from recovery import PHASE, current_control, read, utc
from retirement import PROTECTED, identity, metadata, public_identity, record, save, sha


def wall_projection(value, configured):
    document = value['document']
    authorization = document['authorization']
    actual = document['state']['state']['deadline_unix']
    if (document['schema'] != 'R131_WALL_EXTENDED_V1'
            or authorization['new_deadline_unix'] != configured or actual != configured):
        raise ValueError('actual_authorized_working_state_wall_must_match')
    return dict(index=value['index'], sha256=value['sha256'],
        previous_deadline_utc=utc(authorization['previous_deadline_unix']),
        new_deadline_utc=utc(actual), working_state_sha256=document['state']['sha256'],
        safety_margin_seconds=authorization['safety_margin_seconds'])


def project(root):
    rows = []
    for name, gpu in PROTECTED.items():
        arm = root / name
        control = current_control(arm)
        row = dict(life=name, gpu=gpu, status='PREPARING', actual_native=None, LOADED=None, REQUEST=None, ACT=None)
        if (control / 'PLAN.json').exists():
            plan = read(control / 'PLAN.json')
            row['configured_deadline_utc'] = utc(plan['hard_end_unix'])
            row['deadline_utc'] = row['configured_deadline_utc']
            row['resident_deadline_utc'] = None
            row['configured_learning_policy'] = plan.get('learn_row_policy')
            row['configured_think_learning_policy'] = plan['think_act_learn'].get('learn_row_policy')
            row['new_sleep_recipe_verified'] = False
        if (control / 'RECOVERY.json').exists():
            receipt = read(control / 'RECOVERY.json')
            row.update(recovery_receipt_sha256=sha(control / 'RECOVERY.json'),
                complete_cycle=receipt['complete_cycle'], optimizer_steps=receipt['optimizer_steps'],
                checkpoint_sha256=receipt['checkpoint_sha256'], lost_tail_updates=receipt['lost_tail_updates'],
                tail_response_count=len(receipt['tail_responses']), tail_inbox_count=len(receipt['tail_inbox_ids']),
                preservation_manifest_sha256=receipt['preservation_manifest_sha256'],
                initial_recovery_deadline_utc=utc(receipt['new_deadline_unix']), exact_resident_continuity_claimed=False)
            original = arm / PHASE / 'stream/JOURNAL.json'
            row['same_journal_manifest'] = sha(original) == sha(arm / 'raw/stream/JOURNAL.json')
        if (control / 'READY.json').exists():
            row.update(status='READY_NOT_RECONCILED', cpu_receipt_sha256=sha(control / 'RECEIVING_CPU.json'),
                replay_receipt_sha256=sha(control / 'ARCHIVE_REPLAY.json'))
        if (control / 'RECONCILED.json').exists():
            row['status'] = 'RECONCILED_NOT_LAUNCHED'
        if (control / 'DISPATCHED.json').exists():
            row['status'] = 'DISPATCHED_NOT_LOADED'
            recovery = read(control / 'RECOVERY_APPENDED.json')
            row['recovery_record'] = {key: recovery[key] for key in ('index', 'sha256')}
            floor = recovery['index']
            for path in sorted((arm / 'raw/stream/records').glob('[0-9]' * 20 + '.json')):
                if int(path.stem) <= floor:
                    continue
                kind = metadata(path)
                if kind == 'WALL_EXTENDED':
                    row['WALL_EXTENDED'] = wall_projection(record(path), plan['hard_end_unix'])
                if kind == 'SLEEP_RECIPE':
                    recipe = record(path)
                    row['SLEEP_RECIPE'] = dict(index=recipe['index'], sha256=recipe['sha256'],
                        learn_row_policy=recipe['document'].get('learn_row_policy'),
                        active_semantic_filters=recipe['document'].get('active_semantic_filters'),
                        semantic_row_exclusion=recipe['document'].get('semantic_row_exclusion'))
                    row['new_sleep_recipe_verified'] = recipe['document'].get('learn_row_policy') == 'R227_ALL_AUTHENTIC_CHILD_ROWS_V1'
                if kind not in ('LOADED', 'REQUEST', 'R184_ACT'):
                    continue
                value = record(path)
                target = 'ACT' if kind == 'R184_ACT' else kind
                if row[target] is not None:
                    continue
                document = value['document']
                row[target] = dict(index=value['index'], sha256=value['sha256'])
                if kind == 'LOADED':
                    row[target].update(pid=document['pid'], loaded_unix=document.get('loaded_unix'),
                        optimizer_steps=document.get('optimizer_steps'), resume=document.get('resume'))
                    try:
                        actual = identity(document['pid'])
                        if str(control / 'GUARD.json') in actual['args'] and actual['state'] not in ('Z', 'X'):
                            row['actual_native'] = public_identity(actual)
                            row['status'] = 'LOADED_ALIVE'
                            row['resident_deadline_utc'] = row['configured_deadline_utc']
                    except (FileNotFoundError, ProcessLookupError):
                        row['status'] = 'LOADED_BUT_EXITED'
                elif kind == 'REQUEST':
                    row[target].update(started_unix=document['started_unix'],
                        all_history_tokens_masked=document['render_receipt']['all_history_tokens_masked'])
                else:
                    origin = document['origin']
                    response = record(path.with_name(f"{origin['record_index']:020d}.json"))
                    if response['sha256'] != origin['record_sha256'] or response['kind'] != 'RESPONSE':
                        raise ValueError('actual_ACT_must_bind_own_response')
                    row[target]['origin'] = origin
        if (control / 'EXIT.json').exists():
            row.update(status='EXITED_AFTER_ATTEMPT', exit=read(control / 'EXIT.json'))
        rows.append(row)
    return dict(observed_utc=utc(), node='node3', lives=rows,
        live_count=sum(row['actual_native'] is not None and row['status'] == 'LOADED_ALIVE' for row in rows),
        native_signals=0, retired_roots_restarted=0, lease_extended=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--output', type=Path)
    arguments = parser.parse_args()
    value = project(arguments.root)
    if arguments.output:
        save(arguments.output, value)
    print(json.dumps(value, sort_keys=True, indent=2))
