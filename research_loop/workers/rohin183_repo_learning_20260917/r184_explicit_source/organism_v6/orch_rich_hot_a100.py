"""Prospective high-budget TRAIN generation; numeric outcomes are not admission."""

from organism_v6 import orch_math_rich as original
from organism_v6 import orch_math_record as record
from organism_v6 import orch_rich_intensity as intensity
from organism_v6.orch_rich_twopass import BRANCH_GUIDANCE


HOST_SHA = '6bcd6b8370cc2f2a15e1e488352b4cec96b1e137489d52c3324c199536a09ba8'
DEVICES = {
    2: 'GPU-8e15ce78-4e9c-4c48-724f-2b753c6c2296',
    3: 'GPU-631f3e6a-fbce-0ec5-b934-f08dd64634f8',
    7: 'GPU-f0405a96-813d-7ac7-d641-3ec31d103037',
    4: 'GPU-31583768-d90f-520c-51ed-5dac761526d0',
    5: 'GPU-c1650c7f-ac26-f1a0-2ab8-c7354a6f27c9',
    6: 'GPU-6de3930d-104a-f969-7d36-009271368dd1',
}
ALLOCATION = {2: ('ORIGINAL_RICH', 0), 3: ('LIGHT_BRANCH', 0), 7: ('SELF_EVALUATE', 0),
              4: ('ORIGINAL_RICH', 1), 5: ('LIGHT_BRANCH', 1), 6: ('SELF_EVALUATE', 1)}
CAP = 8192
CONTEXT = 16384
SECONDS = 12 * 3600
MAX_CALLS = 512
SOURCE_SHA = '17f347dc51477c50d4efb83959dbb7c56297aba886e5544ee2aaed3024813465'
RICH = original.RICH_GUIDANCE.replace(', using 150–400 tokens', '')
NEW = record.NEW_RECORD.replace('150–400 tokens', 'as much useful reasoning as needed')


def require(value, message):
    if not value:
        raise ValueError(message)


def allocation(index):
    require(index in ALLOCATION, 'unallocated_physical_gpu')
    return ALLOCATION[index]


def budget(prompt_tokens):
    require(type(prompt_tokens) is int and 0 < prompt_tokens < CONTEXT, 'context_no_crop')
    return min(CAP, CONTEXT - prompt_tokens)


def messages(task, strategy, previous=None):
    require(strategy in {value[0] for value in ALLOCATION.values()}, 'unknown_strategy')
    guidance = intensity.LIGHT if strategy == 'LIGHT_BRANCH' else RICH
    initial = [dict(role='system', content=guidance), dict(role='user', content=task['question'])]
    if previous is None:
        return initial
    require(isinstance(previous, str), 'actual_native_previous_required')
    followup = (BRANCH_GUIDANCE + '\nFinish with a separate line FINAL: followed by just the numeric answer.'
                if strategy == 'SELF_EVALUATE' else NEW)
    return initial + [dict(role='assistant', content=previous), dict(role='user', content=followup)]


def outcome(task, response):
    answer = original.final_value(response['raw'])
    correct = answer is not None and answer == original.number(task['gold'])
    return dict(parsed_answer=str(answer) if answer is not None else None, outcome_pass=bool(correct),
                terminal_correct=bool(correct and response['terminal'] and not response['truncated']),
                missing_final=answer is None, truncated=response['truncated'], terminal=response['terminal'],
                generated_tokens=len(response['token_ids']) - int(response['terminal']),
                semantic_status='UNREVIEWED', admitted=False, trainingAllowed=False)


def followup_allowed(strategy, result):
    return strategy == 'SELF_EVALUATE' or result['outcome_pass']


def lease_deadline(started, lease_end):
    require(started + SECONDS < lease_end - 21600, 'lease_end_minus6h')
    return dict(started_unix=started, native_deadline_unix=started + SECONDS - 300,
                hard_deadline_unix=started + SECONDS, max_calls_per_gpu=MAX_CALLS,
                max_total_calls=1536, assigned_gpu_hours_ceiling=36)
