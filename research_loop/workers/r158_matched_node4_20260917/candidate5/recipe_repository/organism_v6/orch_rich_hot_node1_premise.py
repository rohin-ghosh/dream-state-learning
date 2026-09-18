"""Separately labelled same-premise method exploration; no old relabelling."""

import re

from organism_v6 import orch_rich_hot_node1_exhaustion as previous


VERSION = 'PREMISE_PRESERVING_EXHAUSTION_V1'
ARM = 'PREMISE_PRESERVING_EXHAUSTION'
INDEX = 3
ROOT = '/localhome/local-rohing/orch_rich_hot_node1_20260915_premise_v1'
CONDITIONS = ('LIGHT_BRANCH',)
CAP, CONTEXT = previous.CAP, previous.CONTEXT
MAX_CALLS = previous.MAX_CALLS
UUIDS, MINORS = previous.UUIDS, previous.MINORS
HOST_SHA256, SOURCE_SHA = previous.HOST_SHA256, previous.SOURCE_SHA
INITIAL_STATE = previous.INITIAL_STATE
source, require = previous.source, previous.require
outcome, token_budget = previous.outcome, previous.token_budget
INSTRUCTION = (
    'Solve the original problem with its givens unchanged. Preserve every given '
    'quantity, rate, unit, condition, sharing rule and relationship. Do not invent '
    'a new quantity, change a rate, change who shares or receives an amount, or '
    'otherwise alter a premise to manufacture a second approach. Enumerate '
    'candidate solution methods for this SAME fixed problem. If genuinely '
    'available, work through at least two materially different solution methods '
    'under exactly the same givens. Two paraphrases or repeated calculations '
    'are not two methods; neither is a hypothetical problem with changed givens. '
    'Compare their worked reasoning and conclusions. Justify your choice and '
    'any rejection using the unchanged givens, valid calculations or logical '
    'checks. If valid methods agree, say so instead of falsely rejecting one. '
    'If a second materially different grounded method is not genuinely available, '
    'explicitly report that inability and give the valid method you do have; '
    'do not fabricate an alternative premise, method, fact or observation. '
    'Do not pad or count repetition as useful branching. Before FINAL, report '
    'WORKED_METHOD_COUNT: followed by an integer; PREMISES_PRESERVED: YES, NO '
    'or UNCERTAIN; REJECTED_METHOD: the method and specific justified reason '
    'for each rejection, or NONE; and INABILITY: the actual limitation, or NONE. '
    'These are unverified self-reports, not proof of method distinctness or '
    'premise preservation. Finish with a separate line FINAL: followed by '
    'just the numeric answer.'
)


def allocation(index):
    require(index == INDEX, 'only_board_requested_node1_physical3')
    return previous.allocation(index)


def arm(condition):
    require(condition in CONDITIONS, 'only_inherited_light_branch_cohort')
    return ARM


def messages(task, condition, previous_response=None):
    arm(condition)
    require(previous_response is None, 'single_source_method_arm_only')
    return [dict(role='system', content='ARM: ' + ARM + '\n' + INSTRUCTION),
            dict(role='user', content=task['question'])]


def assess(response):
    result = previous.assess(response)
    raw = response['raw']
    counts = re.findall(r'^WORKED_METHOD_COUNT:\s*(\d+)\s*$', raw, re.MULTILINE)
    preserved = re.findall(r'^PREMISES_PRESERVED:\s*(YES|NO|UNCERTAIN)\s*$', raw, re.MULTILINE)
    rejected = re.findall(r'^REJECTED_METHOD:\s*(.+)$', raw, re.MULTILINE)
    inability = re.findall(r'^INABILITY:\s*(.+)$', raw, re.MULTILINE)
    result.update(self_reported_worked_method_count=int(counts[0]) if len(counts) == 1 else None,
        self_reported_premises_preserved=preserved[0] if len(preserved) == 1 else None,
        self_reported_rejected_methods=[entry for entry in rejected if entry.strip() != 'NONE'],
        self_reported_inability=inability[0] if len(inability) == 1 else None,
        semantic_verified_worked_method_count=None, semantic_verified_premise_preservation=None,
        method_comparison_basis='UNCHANGED_GIVENS', premise_variants_count_as_methods=False,
        earlier_9_of_12_not_method_branch_evidence=True)
    return result


def protocol():
    return dict(phase_version=VERSION, arm=ARM, physical_index=INDEX, uuid=UUIDS[INDEX],
        prompt=messages(dict(question='TASK_PLACEHOLDER'),CONDITIONS[0]),
        inherited_condition=CONDITIONS[0], source_stage_only=True, cap=CAP, context=CONTEXT,
        global_call_cap=MAX_CALLS, quota_reset=False, original_deadline_unchanged=True,
        original_outputs_and_labels_unchanged=True, preserved_unhinted_slots=[0,1],
        variants_of_givens_are_not_methods=True, semantic_status='UNREVIEWED',
        raw_storage='GENERATION_NODE_ONLY', auto_admission=False,
        board_publication_required_before_boundary_and_launch=True)
