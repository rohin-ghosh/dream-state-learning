"""Hourly local observer/publisher. Never a learner or parent controller."""

import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import time

from collect import OWN, run_once, save
from publish import publish
from review_queue import OWNER


END = datetime(2026, 9, 18, 14, 0, tzinfo=timezone.utc).timestamp()


def serve(publishing=False):
    operator = OWN / 'operator'
    operator.mkdir(mode=0o700, exist_ok=True)
    with (operator / 'SINGLE_READER.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        started = time.time()
        start_ticks = int(Path(f'/proc/{os.getpid()}/stat').read_text().rsplit(')', 1)[1].split()[19])
        next_due = time.time()
        loops = 0
        loaded_source_hashes = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in OWN.glob('*.py')}
        while time.time() < END:
            if time.time() < next_due:
                time.sleep(min(5, next_due - time.time()))
                continue
            state = dict(pid=os.getpid(), start_ticks=start_ticks, started_unix=started,
                expires_utc=datetime.fromtimestamp(END, timezone.utc).isoformat(),
                interval_seconds=3600, publishing=publishing, remote_writes=0, learner_controls=0,
                source_sha256=loaded_source_hashes,
                mode='hourly_evidence_and_pending_review_queue_not_semantic_maintenance',
                automatic_semantic_review=False, semantic_review_owner=OWNER,
                successful_polls=loops, observed_unix=time.time())
            save(operator / 'PROCESS.json', state)
            try:
                result = run_once()
                for catchup in range(5):
                    if all(row.get('caught_up', True) for row in result['rows']):
                        break
                    result = run_once()
                loops += 1
                state.update(successful_polls=loops, last_success_utc=result['observed_utc'],
                    next_due_utc=datetime.fromtimestamp((int(time.time()) // 3600 + 1) * 3600, timezone.utc).isoformat(),
                    new_semantic_judgments_this_poll=0)
                save(OWN / 'public/SERVICE.json', state)
                if publishing:
                    save(operator / 'LAST_PUSH.json', publish())
            except Exception as error:
                save(operator / f'ERROR_{time.time_ns()}.json', dict(error_type=type(error).__name__, error=str(error), time_unix=time.time()))
            next_due = (int(time.time()) // 3600 + 1) * 3600
            state.update(next_due_utc=datetime.fromtimestamp(next_due, timezone.utc).isoformat())
            save(operator / 'PROCESS.json', state)
        save(operator / 'EXIT.json', dict(time_unix=time.time(), reason='finite_observer_horizon', learner_controls=0))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--publish', action='store_true')
    arguments = parser.parse_args()
    serve(arguments.publish)
