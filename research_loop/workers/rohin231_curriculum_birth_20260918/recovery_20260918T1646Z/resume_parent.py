"""Resume the same source-bound pair parenting with a refreshed finite wall."""

import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time


HERE = Path(__file__).resolve().parent
ORIGINAL = HERE.parent
PAIR = ORIGINAL / 'r232_pair'
REPO = ORIGINAL.parents[2]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--arm', choices=('learner', 'frozen'), required=True)
    parser.add_argument('--deadline', type=float, required=True)
    arguments = parser.parse_args()
    if not time.time() < arguments.deadline <= 1789754400:
        raise ValueError('finite_recovery_parent_wall')
    private = HERE / 'private'
    private.mkdir(mode=0o700, exist_ok=True)
    lock = (private / ('PUBLISHER_' + arguments.arm + '.lock')).open('a+')
    fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    sys.path.insert(0, str(ORIGINAL))
    spec = importlib.util.spec_from_file_location('r233_pair_parent_source', PAIR / 'PARENT_SOURCE.py')
    parent = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parent)
    parent.OWN, parent.REPO, parent.END = ORIGINAL, REPO, arguments.deadline
    if arguments.arm == 'frozen':
        parent.REMOTE = '/localhome/local-rohing/orch_r232_curriculum_frozen_20260918'
        parent.PRIVATE = PAIR / 'private/frozen_parent'
    else:
        parent.PRIVATE = ORIGINAL / 'private/parent'
    original_write, original_instruction = parent.write, parent.instruction

    def write(path, document):
        path = Path(path)
        if path.exists():
            if json.loads(path.read_bytes()) != document:
                raise ValueError('prior_exact_parent_receipt_changed')
            return
        original_write(path, document)

    def instruction():
        result = original_instruction()
        if (PAIR / 'EPOCH_RELEASE.json').exists():
            result = result.replace((ORIGINAL / 'BIRTH_SPEC_SOURCE.md').read_text(),
                (PAIR / 'BIRTH_SPEC_R232.md').read_text())
            result += ('\nR232 is an explicit later environment epoch, not a retroactive birth change. '
                'Teach exploration inside THINK from this child\'s actual results. Same help opportunity '
                'and90-word budget; do not copy a correction from the other child. No extra stage.')
        return result

    parent.write, parent.instruction = write, instruction
    parent.PRIVATE.mkdir(parents=True, exist_ok=True)
    receipt = dict(arm=arguments.arm, pid=os.getpid(),
        start_ticks=Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()[19],
        observed_unix=time.time(), expiry_unix=arguments.deadline,
        parent_source_sha256=hashlib.sha256((PAIR / 'PARENT_SOURCE.py').read_bytes()).hexdigest(),
        model='openai/openai/gpt-6-astra', message_max_words=90,
        help_spacing_by_stage=[1, 1, 1, 2, 3, 'on_request'], learner_signals=0,
        prior_deliveries_reused=True, learner_identity_changed=False)
    original_write(private / ('PARENT_' + arguments.arm + '_' + str(time.time_ns()) + '.json'), receipt)
    parent.serve()


if __name__ == '__main__':
    main()
