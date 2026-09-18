"""Same parent policy/help opportunity, independently responsive to each child."""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time


HERE = Path(__file__).resolve().parent
ORIGINAL = HERE.parent
REPO = ORIGINAL.parents[2]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--arm', choices=('learner', 'frozen'), required=True)
    arguments = parser.parse_args()
    sys.path.insert(0, str(ORIGINAL))
    spec = importlib.util.spec_from_file_location('r232_parent_source', HERE / 'PARENT_SOURCE.py')
    parent = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parent)
    parent.OWN, parent.REPO = ORIGINAL, REPO
    if arguments.arm == 'frozen':
        parent.REMOTE = '/localhome/local-rohing/orch_r232_curriculum_frozen_20260918'
        parent.PRIVATE = HERE / 'private/frozen_parent'
    else:
        parent.PRIVATE = ORIGINAL / 'private/parent'
    original_write, original_instruction = parent.write, parent.instruction

    def write(path, document):
        path = Path(path)
        if path.exists():
            assert json.loads(path.read_bytes()) == document, 'preserve_prior_exact_parent_receipt'
            return
        original_write(path, document)

    def instruction():
        result = original_instruction()
        release = HERE / 'EPOCH_RELEASE.json'
        if release.exists():
            result = result.replace((ORIGINAL / 'BIRTH_SPEC_SOURCE.md').read_text(),
                (HERE / 'BIRTH_SPEC_R232.md').read_text())
            result += ('\nR232 is an explicit later environment epoch, not a retroactive birth change. '
                'Teach exploration inside THINK from this child\'s actual results. Same help opportunity '
                'and90-word budget; do not copy a correction from the other child. No extra stage.')
        return result

    parent.write, parent.instruction = write, instruction
    parent.PRIVATE.mkdir(parents=True, exist_ok=True)
    receipt = dict(arm=arguments.arm, pid=os.getpid(), observed_unix=time.time(),
        policy_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        parent_source_sha256=hashlib.sha256((HERE / 'PARENT_SOURCE.py').read_bytes()).hexdigest(),
        model='openai/openai/gpt-6-astra', message_max_words=90, provider_max_output_tokens=4096,
        reasoning_effort='low', help_spacing_by_stage=[1, 1, 1, 2, 3, 'on_request'],
        expiry_unix=parent.END, learner_signals=0)
    write(parent.PRIVATE / ('PAIR_POLICY_' + str(time.time_ns()) + '.json'), receipt)
    parent.serve()


if __name__ == '__main__':
    main()
