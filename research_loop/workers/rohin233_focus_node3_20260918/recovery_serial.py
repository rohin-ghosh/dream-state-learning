"""Dispatch once, then require actual LOADED before admitting the next life."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import time

from recovery import PHASE, current_control, utc
from recovery_proof import project


ORDER = ('r213_math_c', 'r213_math_a', 'r213_math_b_fork',
    'r213_r226_caption_unparented_fork', 'r213_r226_caption_observation_fork',
    'r213_r226_caption_perspective_fork', 'r213_r226_caption_revision_fork',
    'r213_r226_caption_selfderive_fork')


def require_policy(control):
    receipt = json.loads((control / 'POLICY_READY.json').read_bytes())
    plan = json.loads((control / 'PLAN.json').read_bytes())
    policy = 'R227_ALL_AUTHENTIC_CHILD_ROWS_V1'
    if not (receipt['policy'] == plan.get('learn_row_policy') ==
            plan.get('think_act_learn', {}).get('learn_row_policy') == policy):
        raise ValueError('R227_policy_required_for_every_new_dispatch')


def run(root, python):
    for name in ORDER:
        control = current_control(root / name)
        end = time.time() + 900
        while not (control / 'RECONCILED.json').exists():
            if time.time() >= end:
                raise ValueError('reconciliation_pending_no_launch:' + name)
            time.sleep(5)
        if (control / 'DISPATCHED.json').exists():
            row = next(item for item in project(root)['lives'] if item['life'] == name)
            if row['status'] == 'LOADED_ALIVE':
                continue
            print(json.dumps(dict(observed_utc=utc(), life=name,
                status='WAITING_EXISTING_DISPATCH_NO_NEW_START')), flush=True)
        else:
            require_policy(control)
            subprocess.run([python, '-B', str(Path(__file__).with_name('recovery.py')), 'launch',
                '--root', str(root), '--name', name, '--python', python], check=True)
            print(json.dumps(dict(observed_utc=utc(), life=name, status='DISPATCHED_WAITING_ACTUAL_LOADED')), flush=True)
        end = time.time() + 3600
        while time.time() < end:
            row = next(item for item in project(root)['lives'] if item['life'] == name)
            if row['status'] == 'LOADED_ALIVE':
                print(json.dumps(dict(observed_utc=utc(), life=name, LOADED=row['LOADED'],
                    actual_native=row['actual_native'])), flush=True)
                break
            if any((control / filename).exists() for filename in ('FAILED.json', 'EXIT.json', 'OUTER_FAILED.json')):
                raise ValueError('failed_attempt_preserved_no_retry:' + name)
            time.sleep(10)
        else:
            raise ValueError('LOADED_not_observed_no_signals_or_next_launch:' + name)
    print(json.dumps(dict(observed_utc=utc(), all_eight_loaded=True, pid=os.getpid())), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--python', required=True)
    options = parser.parse_args()
    run(options.root, options.python)
