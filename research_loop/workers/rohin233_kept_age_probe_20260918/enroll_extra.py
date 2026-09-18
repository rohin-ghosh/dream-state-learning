"""Confirmed sixteenth source, alongside rather than restarting the first fifteen."""

import argparse
import fcntl
import json
import os
from pathlib import Path
import time

from research_loop.workers.rohin233_kept_age_probe_20260918 import enroll


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--registration', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--repo', type=Path, required=True)
    args = parser.parse_args()
    os.umask(0o077)
    raw = args.registration.read_bytes()
    registration = json.loads(raw)
    assert len(registration['targets']) == 1 and registration['targets'][0]['label'] == 'GAME_UNPARENTED_N2'
    args.output.mkdir(mode=0o700, parents=True, exist_ok=True)
    lock = (args.output / 'ENROLL.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    while time.time() < registration['deadline_unix']:
        assert args.registration.read_bytes() == raw
        status = enroll.tick(registration, args.output, args.repo)
        status.update(extra_node2_player='CONFIRMED_KEPT_R233_PARENTED_EPOCH_OWNER_JASON',
            scope='sixteenth_distinct_native_journal_not_duplicate_fresh_alias', parent_rendering='owner_receipt_pending')
        enroll.put(args.output / 'STATUS.json', status)
        print(json.dumps(dict(unix=status['unix'], pid=os.getpid(), enrolled=status['enrolled'], rows=status['rows'])), flush=True)
        time.sleep(min(30, max(0, registration['deadline_unix'] - time.time())))


if __name__ == '__main__':
    main()
