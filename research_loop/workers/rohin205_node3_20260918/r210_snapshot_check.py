"""Replay an immutable physical archive using its hash-bound logical inbox."""

import hashlib
import json
from pathlib import Path
import sys

from gpu.r205_runtime import ControlJournal


class SnapshotJournal(ControlJournal):
    def __init__(self, root, logical_inbox):
        self.logical_inbox = Path(logical_inbox)
        super().__init__(root)

    def _reload_state(self, *arguments, **keywords):
        self.inbox = self.logical_inbox
        return super()._reload_state(*arguments, **keywords)


def main():
    archive, guard_path, expected_guard, complete_index = sys.argv[1:]
    guard_bytes = Path(guard_path).read_bytes()
    if hashlib.sha256(guard_bytes).hexdigest() != expected_guard:
        raise ValueError('original_guard_binding')
    guard = json.loads(guard_bytes)
    plan_bytes = Path(guard['plan_path']).read_bytes()
    if hashlib.sha256(plan_bytes).hexdigest() != guard['plan_sha256']:
        raise ValueError('original_plan_binding')
    plan = json.loads(plan_bytes)
    journal = SnapshotJournal(archive, Path(plan['root']) / 'stream/inbox')
    try:
        checkpoint = journal.latest_checkpoint()
        complete_path = Path(archive) / 'records' / f'{int(complete_index):020d}.json'
        complete = json.loads(complete_path.read_bytes())
        if complete['kind'] != 'SLEEP_COMPLETE' or checkpoint['document'] != complete['document']['resume_state']:
            raise ValueError('exact_saved_checkpoint_required')
        if checkpoint['document']['state']['pending'] is not None:
            raise ValueError('quiescent_saved_checkpoint_required')
        print(json.dumps(dict(status='VERIFIED', logical_inbox=str(journal.inbox),
            physical_archive=archive, complete_index=int(complete_index),
            checkpoint_sha256=checkpoint['expected_sha256'])))
    finally:
        journal.close()


if __name__ == '__main__':
    main()
