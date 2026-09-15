"""Rohin98 next-version prompts; never edit a running frozen source snapshot."""

from organism_v6 import orch_rich_hot_node1 as previous


VERSION = 'ORCH_RICH_HOT_NODE1_PROMPT_V2_ROHIN98'
CONDITIONS = previous.CONDITIONS
CAP = previous.CAP
CONTEXT = previous.CONTEXT
outcome = previous.outcome
BRANCH = (
    'When a consequential alternative is genuinely relevant, explain which '
    'alternative you considered and why the given evidence or a concrete check '
    'led you to reject it. If it remains unresolved, say so rather than claiming '
    'it was rejected. Do not fabricate alternatives, manufacture disagreement, '
    'or add padding merely to satisfy this instruction.'
)
FINAL = 'Finish with a separate line FINAL: followed by just the numeric answer.'
RICH = (
    'Solve the problem using the given quantities and requested unknown. '
    'Explain the task-specific operations and check the result against the '
    'problem. Distinguish given evidence from assumptions. Use useful reasoning '
    'rather than generic advice, repetition, or invented observations.'
)
LIGHT = (
    'Solve the problem clearly. Concentrate on the uncertainty or check that '
    'could most change the answer. Follow useful reasoning as far as the '
    'evidence warrants, without padding or repeating settled points.'
)
SECOND = {
    'TWO_PASS': (
        'The preceding assistant response is your own actual first pass on '
        'this task, not an external answer or a verified solution. Examine it '
        'against the given problem, perform a useful check, and retain or '
        'revise the conclusion with concrete reasons.'
    ),
    'META_EVALUATE': (
        'The preceding assistant response is your own actual first pass on '
        'this task, not an external answer or a verified solution. Evaluate '
        'the conclusion and its most consequential uncertainty. Identify the '
        'useful next question raised by that evaluation, work through its '
        'consequence, and retain or revise the answer with task-specific evidence.'
    ),
}


def messages(task, condition, previous_response=None):
    previous.require(condition in CONDITIONS, 'unknown_condition')
    guidance = LIGHT if condition == 'LIGHT_BRANCH' else RICH
    result = [dict(role='system', content=' '.join((guidance, BRANCH, FINAL))),
              dict(role='user', content=task['question'])]
    if previous_response is not None:
        previous.require(condition in SECOND, 'second_pass_not_allocated')
        result.extend([dict(role='assistant', content=previous_response),
                       dict(role='user', content=' '.join((SECOND[condition], BRANCH, FINAL)))])
    return result


def review_contract():
    return dict(owner='Hubble/Main sampled semantic review', raw_batch_size=64, sample_size=12,
        keyword_only_counting_allowed=False, auto_admission=False, review_blocks_generation=False,
        first_person_required=False, minimum_output_tokens=None, maximum_preferred_output_tokens=None,
        labels=['meaningful_supported_alternative', 'relevant_but_unresolved',
                'alternative_not_relevant', 'unsupported_or_fabricated_branch', 'UNREVIEWED'],
        meaningful_branch_requires=['sampled_full_text_semantic_read', 'task_relevant_consequence',
            'actual_alternative_identified', 'supported_reason_for_rejection', 'source_evidence_citation'],
        not_relevant_is_not_failure=True,
        reporting='sample denominator and unreviewed population separately; no population qualification from keywords',
        source_policy='cached TRAIN provenance and held exclusions required; no parenting experience into L1')
