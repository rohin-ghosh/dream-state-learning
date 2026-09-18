"""Prepare assigned fixed-state clones without touching the current learners."""

import argparse
import json
from pathlib import Path
import time

import math_c
from stage_scale import DEVICES


ASSIGNMENTS = {
    0: ('KERNEL-VERIFY-A', 'A', 'CPU_STDLIB_ALGORITHM_CORRECTNESS',
        'Verify an algorithm with actual confined Python correctness checks. No GPU kernel execution is connected.'),
    1: ('MATH-SHORT-D', 'D', 'MATHEMATICAL_INVESTIGATION',
        'Prefer concise evidence-linked mathematical progress; ask light correction questions, not supplied answers.'),
    2: ('MATH-PROSE-B', 'B', 'MATHEMATICAL_INVESTIGATION',
        'Develop mathematical arguments in prose and check claims with actual calculation where useful.'),
    3: ('KERNEL-REFLECT-B', 'B', 'CPU_STDLIB_ALGORITHM_CORRECTNESS',
        'Reflect on predicted versus observed algorithm behavior using actual confined Python correctness checks; no GPU execution.'),
    5: ('REPO-TRACE-B', 'B', 'READ_ONLY_REPOSITORY_TRACE',
        'Trace claims through actual pinned repository reads and tests; do not invent tool results or shared-write access.'),
    7: ('CREATIVE-OPEN-C', 'C', 'CREATIVE_OWN_OBJECT',
        'Explore and revise the child\'s own creative object through questions; do not supply the original C2 story test.')}


def prepare(physical):
    math_c.host()
    target = math_c.HOME.parent / f'SCALE_physical{physical}'
    staged = math_c.read(target / 'STAGED.json')
    math_c.require(staged['candidate_physical'] == physical and staged['source_manifest_sha256'] == math_c.MANIFEST_SHA,
        'exact_prepared_receiver')
    arm, style, environment, brief = ASSIGNMENTS[physical]
    math_c.HOME, math_c.SOURCE, math_c.SNAPSHOT = target, target / 'source', target / 'snapshot'
    math_c.GPU = DEVICES[physical][0]
    math_c.clone_state(physical=physical, trial_id=f'R203_NODE4_{physical}_{arm.replace("-", "_")}', arm=arm)
    math_c.write(target / 'R203_ASSIGNMENT.json', dict(arm=arm, parent_style=style, physical=physical,
        gpu_uuid=DEVICES[physical][0], device_minor=DEVICES[physical][1], effective_environment=environment,
        parent_brief=brief, prepared_unix=time.time(), status='FIXED_STATE_PREPARED_PENDING_MAIN_R203_OVERLAY',
        source_cycle=51, optimizer_steps=4908, masked_context_cut=5846,
        first_input='R202_CLONE_PART_ONE_2026-09-17.txt', no_original_story_test=True,
        clean_reference_sha256='3d0d9dc7fbdefc7ccc24c2625b56b05a6a8c07baea41e3753038813f86da541d',
        guided_cycles=[52, 53, 54], withdrawn_cycles=[55, 56, 57],
        retire_current_at_fresh_COMPLETE=physical in (0, 1, 3, 5),
        retirement_reason='R203 useful-but-reallocated; no failure or degradation claim',
        kernel_route_claim=False, human_training_targets=False, historical_R194_retrotraining=False,
        new_GPU_actions=0, pending_parent_messages_to_be_reconciled_before_withdrawal=True))
    print(json.dumps(math_c.read(target / 'R203_ASSIGNMENT.json')))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--physical', type=int, choices=tuple(ASSIGNMENTS), required=True)
    prepare(parser.parse_args().physical)
