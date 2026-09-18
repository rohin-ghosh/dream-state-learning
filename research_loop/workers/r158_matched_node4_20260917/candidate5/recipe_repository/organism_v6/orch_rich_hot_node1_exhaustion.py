"""Rohin100 versioned exhaustion arms with unverified approach accounting."""

from collections import Counter
import re

from organism_v6 import orch_rich_hot_node1_v2 as previous


VERSION = 'ROHIN100_EXHAUSTION_V1'
CAP = 16384
CONTEXT = 32768
CONDITIONS = previous.CONDITIONS
MAX_CALLS = previous.MAX_CALLS
UUIDS = previous.UUIDS
MINORS = previous.MINORS
HOST_SHA256 = previous.HOST_SHA256
SOURCE_SHA = previous.SOURCE_SHA
INITIAL_STATE = previous.INITIAL_STATE
source = previous.source
require = previous.require
allocation = previous.allocation
outcome = previous.outcome
EXHAUSTION = (
    'Enumerate the plausible approaches to this task. Pursue at least two '
    'substantively different worked approaches, not two paraphrases of the same '
    'calculation. State their hypotheses or assumptions, work through their '
    'consequences using only the evidence actually available, and compare the '
    'results. Choose the supported conclusion and explain why competing '
    'approaches lose using specific evidence or checks. If valid approaches '
    'agree, acknowledge the agreement rather than falsely rejecting a correct '
    'method. If two grounded approaches cannot be worked, explicitly report '
    'that limitation instead of manufacturing facts or padding. Never invent '
    'facts, observations, uncertainty, or evidence. Repetition is a failure '
    'signal, not a distinct approach or useful branch. Before the final answer '
    'or action, report WORKED_APPROACH_COUNT: followed by an integer, and '
    'REJECTED_APPROACH: followed by the approach name and specific rejecting '
    'evidence for each rejection, or REJECTED_APPROACH: NONE. These are '
    'unverified self-reports, not semantic validation.'
)
STEERING = (
    'Use the task quantities, units and constraints explicitly. Check the '
    'selected result against the original question. In a later evaluation, '
    'compare your own actual prior response with the task, not with an '
    'external answer, and preserve correct work unless evidence justifies change.'
)


def arm(condition):
    require(condition in CONDITIONS, 'unknown_condition')
    return 'EXHAUSTION_ONLY' if condition == 'ORIGINAL_RICH' else 'EXHAUSTION_PLUS_STEERING'


def instruction(selected_arm):
    require(selected_arm in ('EXHAUSTION_ONLY', 'EXHAUSTION_PLUS_STEERING'), 'unknown_exhaustion_arm')
    return 'ARM: ' + selected_arm + '\n' + EXHAUSTION


def messages(task, condition, previous_response=None):
    selected_arm = arm(condition)
    guidance = instruction(selected_arm)
    if selected_arm == 'EXHAUSTION_PLUS_STEERING':
        guidance += '\n' + STEERING
    guidance += '\nFinish with a separate line FINAL: followed by just the numeric answer.'
    result = [dict(role='system', content=guidance), dict(role='user', content=task['question'])]
    if previous_response is not None:
        require(condition in ('TWO_PASS', 'META_EVALUATE'), 'second_pass_not_allocated')
        result.extend([dict(role='assistant', content=previous_response), dict(role='user', content=
            'The preceding response is your own actual first pass, not an external or verified answer. '
            'Now evaluate it against the task using the same exhaustion procedure. ' + EXHAUSTION +
            ' Finish with a separate line FINAL: followed by just the numeric answer.')])
    return result


def token_budget(prompt_tokens):
    require(isinstance(prompt_tokens, int) and 0 < prompt_tokens < CONTEXT, 'no_remaining_native_context')
    return min(CAP, CONTEXT - prompt_tokens)


def assess(response):
    raw = response['raw']
    counts = re.findall(r'^WORKED_APPROACH_COUNT:\s*(\d+)\s*$', raw, re.MULTILINE)
    rejected = re.findall(r'^REJECTED_APPROACH:\s*(.+)$', raw, re.MULTILINE)
    lines = [' '.join(line.split()) for line in raw.splitlines() if len(line.strip()) >= 20]
    repeats = sum(count - 1 for count in Counter(lines).values())
    return dict(self_reported_worked_approach_count=int(counts[0]) if len(counts) == 1 else None,
        self_reported_rejected_approaches=[entry for entry in rejected if entry.strip() != 'NONE'],
        self_reported_rejected_approach_count=sum(entry.strip() != 'NONE' for entry in rejected),
        semantic_verified_worked_approach_count=None, semantic_verified_rejected_approaches=None,
        semantic_status='UNREVIEWED', repeated_substantive_lines=repeats,
        substantive_line_count=len(lines), repetition_failure_signal=repeats > 0,
        repetition_counts_as_useful_branch=False, admission=False)


def protocol():
    return dict(phase_version=VERSION, arms={condition: arm(condition) for condition in CONDITIONS},
        prompts={condition: messages(dict(question='TASK_PLACEHOLDER'), condition) for condition in CONDITIONS},
        cap=CAP, context=CONTEXT, stage2_cap='min(16384,32768-actual_encoded_full_history)',
        no_model_or_rope_changes=True, global_call_cap=MAX_CALLS, original_deadline_unchanged=True,
        self_reports_are_semantic_verification=False, raw_storage='GENERATION_NODE_ONLY',
        auto_admission=False, forced_minimum_tokens=None)
