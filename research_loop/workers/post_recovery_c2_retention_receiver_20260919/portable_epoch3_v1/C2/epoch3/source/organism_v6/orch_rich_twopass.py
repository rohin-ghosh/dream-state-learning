"""RAW85 paired generators over an externally frozen roster; no fitting."""

from collections import Counter
from copy import deepcopy
import hashlib

from organism_v6 import orch_math_record as record
from organism_v6 import orch_math_rich as original
from organism_v6 import orch_math_scale as admission


TASKS_SHA = '3e320ce8c06878a13da0400475977082cedd8379eab780ad82c5de8f1aa50c43'
CONDITIONS = ('BRANCH', 'CONTINUE')
CONTEXT = 4096
CAPS = dict(draft=512, final=1536, record=512)
MAX_CALLS = 1280
DENOMINATOR = 256
NEUTRAL_FINAL = 'Complete your solution to the problem. Finish with a separate line FINAL: followed by just the numeric answer.'
FINAL_SYSTEM = (
    'Solve the problem in your own first-person voice. Develop substantive reasoning '
    'from the given quantities and requested unknown. Spend your effort on useful '
    'calculations and evidence, not padding or invented facts. You have room for '
    'extended working when useful; you need not fill it. Finish with a separate '
    'line FINAL: followed by just the numeric answer.'
)
BRANCH_GUIDANCE = (
    'Evaluate the provisional conclusion in your preceding draft. Identify an '
    'uncertainty, alternative interpretation, or consequential step worth examining; '
    'select the one most useful to resolving this problem and follow it through. '
    'Concentrate the extra reasoning where it could change or substantively support '
    'your conclusion. Use what you find to retain or revise the final answer. '
    'Before the FINAL line, state the consequential alternative you considered '
    'and the evidence or calculation that made you reject it, when relevant. '
    'Do not manufacture disagreement or branches merely to produce more text.'
)
CONTINUE_GUIDANCE = (
    'Continue working from your preceding draft in your usual way and complete '
    'your solution. Use this additional response for whatever calculations or '
    'explanations you would ordinarily find useful. You may retain or correct '
    'the draft as needed. Keep the work relevant to this problem.'
)


def validate_roster(document):
    tasks = document['tasks']
    assert document['denominator'] == len(tasks) == DENOMINATOR
    assert document['per_family'] == 64 and document['no_l2_l3_access'] is True
    assert Counter(task['family'] for task in tasks) == dict.fromkeys(original.MINING, 64)
    assert len({task['id'] for task in tasks}) == len({task['question_sha256'] for task in tasks}) == DENOMINATOR
    assert len(set(document['excluded_ids'])) == len(set(document['excluded_question_hashes'])) == 1216
    assert not ({task['id'] for task in tasks} & set(document['excluded_ids']))
    assert not ({task['question_sha256'] for task in tasks} & set(document['excluded_question_hashes']))
    for task in tasks:
        assert set(task) == {'id', 'question', 'question_sha256', 'family', 'gold'}
        assert task['question_sha256'] == original.digest(' '.join(task['question'].lower().split()))
        original.number(task['gold'])


def prompt(task, stage, condition=None, draft=None, final=None):
    if stage == 'draft':
        return original.prompt(task, 'rich')
    if condition not in CONDITIONS or not isinstance(draft, str):
        raise ValueError('exact_condition_and_actual_child_draft_required')
    history = [dict(role='user', content=task['question']), dict(role='assistant', content=draft),
               dict(role='user', content=NEUTRAL_FINAL)]
    if stage == 'final':
        actual = [dict(role='system', content=FINAL_SYSTEM)] + deepcopy(history)
        actual[-1]['content'] += '\n\n' + (BRANCH_GUIDANCE if condition == 'BRANCH' else CONTINUE_GUIDANCE)
        return actual, history
    if stage != 'record' or not isinstance(final, str):
        raise ValueError('actual_child_final_required_for_NEW_record')
    history.append(dict(role='assistant', content=final))
    unused, neutral = record.prompt(task, 'new_record', final)
    return history + [dict(role='user', content=record.NEW_RECORD)], history + [deepcopy(neutral[-1])]


def capture(task, stage, condition, response, student, draft_sha256=None):
    kind = 'new_record' if stage == 'record' else 'rich'
    row = original.capture(task, kind, response, student)
    bounded = 150 <= row['generated_tokens'] <= 400 and not response['truncated'] and response['prompt_tokens'] <= CONTEXT
    row.update(stage=stage, condition=condition, context_contract=CONTEXT,
               token_contract_pass=bounded, candidate=bool(stage != 'draft' and row['outcome_pass'] and bounded),
               common_draft_sha256=draft_sha256, long_source=stage == 'final' and row['generated_tokens'] > 400,
               trainingAllowed=False, fit_ready=False)
    return row


def record_allowed(final_row):
    return final_row.get('status') == 'OK' and final_row.get('outcome_pass') is True


def admit(row, decision, gold_review):
    if row['stage'] == 'draft':
        raise ValueError('shared_draft_is_source_not_condition_target')
    return admission.admit(row, decision, gold_review)


def text_sha(text):
    return hashlib.sha256(text.encode()).hexdigest()
