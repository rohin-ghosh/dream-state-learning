"""Finite read-only observation of one published correction; no publishing."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import time

from deadline_resume import write
from renew_c2_cpu import remote, PYTHON


OWN = Path(__file__).resolve().parent
REMOTE = '/localhome/local-rohing/orch_r233_C2_checkpoint_tail_20260918/parent_operator'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--wait-seconds', type=int, default=900)
    arguments = parser.parse_args()
    if not 1 <= arguments.wait_seconds <= 1800:
        raise ValueError('finite_read_only_observation_window')
    history = OWN / 'private/checkpoint_tail_v_delivery'
    history.mkdir(exist_ok=False)
    until = time.monotonic() + arguments.wait_seconds
    while time.monotonic() < until:
        try:
            text = remote(PYTHON + ' -B ' + REMOTE + '/checkpoint_tail_parent_delivery.py')
            result = json.loads(text)
        except (RuntimeError, subprocess.TimeoutExpired, json.JSONDecodeError) as error:
            with (history / 'READ_RETRIES.jsonl').open('a') as stream:
                stream.write(json.dumps(dict(observed_unix=time.time(), error_type=type(error).__name__,
                    native_signals=[], journal_writes=0)) + '\n')
            time.sleep(10)
            continue
        path = history / ('OBSERVED_' + str(time.time_ns()) + '.json')
        write(path, result)
        temporary = OWN / 'CHECKPOINT_TAIL_V_DELIVERY.next.json'
        temporary.write_text(text)
        os.replace(temporary, OWN / 'CHECKPOINT_TAIL_V_DELIVERY.json')
        print(json.dumps(dict(observed_utc=result['observed_utc'], latest_index=result['latest_index'],
            inbox=result['inbox_receipt'], render=result['first_render'], first_ACT=result['first_ACT'])), flush=True)
        if result['first_ACT'] is not None:
            return
        time.sleep(10)
    write(OWN / 'CHECKPOINT_TAIL_V_WATCH_ENDED.json', dict(status='READ_ONLY_WINDOW_ENDED',
        observed_unix=time.time(), native_signals=[], journal_writes=0, parent_stopped=False))


if __name__ == '__main__':
    main()
