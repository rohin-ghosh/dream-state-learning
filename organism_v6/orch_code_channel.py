"""Fixed, read-only MBPP channel screen; the existing interpreter is the oracle."""

import hashlib
import json

from organism_v6 import orch_code_bounded as code


ARMS = ('LEGACY', 'SEPARATED', 'TERSE')
DEVICES = {'LEGACY': (0, 'GPU-ff5f84e9-c70e-272d-a8e0-eb20aad05ac6'),
           'SEPARATED': (2, 'GPU-8e15ce78-4e9c-4c48-724f-2b753c6c2296'),
           'TERSE': (3, 'GPU-631f3e6a-fbce-0ec5-b934-f08dd64634f8')}
MANIFEST = '5e675c309b202625a6ddf1d36c1a58f51ef656985821cec1cd6123424d927469'
MOUNTED = '37ec37884e4b0b679edd1dba1be1dec3474589e992649f3a33e7e3b1ec78b8c0'
BASE = 'a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992'
AXES = ('ownership', 'grounding', 'checkable', 'truthful', 'no_padding', 'reusable')
SEPARATION = ('The task wording describes the desired computation, not the response format. '
              'Use two separate channels in this single response. First write NARRATIVE: '
              'on its own line and your own 150–400-token grounded account below it. '
              'Then write ACTION: on its own line, followed by exactly one final JSON line. '
              'Only the string in that JSON action is interpreted, never the narrative. '
              'For a solution the JSON has exactly the key expression: its value must be '
              'one supported expression over the named arguments, not a function definition. '
              'For a requested record the JSON has exactly the key record: its value is '
              'your own reusable lesson, not executable code. '
              'Use first person, actual available evidence and a checkable expectation. '
              'Do not claim a test was run before feedback; do not pad or repeat the instructions.')


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def neutral_prefix(task, previous=None):
    user = task['text'] + '\nArguments: ' + ', '.join(task['arguments'])
    user += '\nPublic reference tests: ' + json.dumps([test['source'] for test in task['tests']])
    messages = [{'role': 'user', 'content': user}]
    if previous is not None:
        messages += [{'role': 'assistant', 'content': previous['target']},
                     {'role': 'user', 'content': 'My record.'}]
    return messages


def prompt(task, arm, previous=None):
    if arm not in ARMS:
        raise ValueError('unknown_arm')
    history = [] if previous is None else [previous]
    messages, unused = code.prompt(task, 'terse' if arm == 'TERSE' else 'rich', history,
                                   previous is not None)
    if arm == 'SEPARATED':
        messages[0] = {'role': 'system', 'content': SEPARATION}
    return messages, neutral_prefix(task, previous)


def project(text, arm, record=False):
    action, rationale = code.parse_action(text, record)
    if arm == 'SEPARATED':
        lines = text.strip().splitlines()
        if len(lines) < 4 or lines[0] != 'NARRATIVE:' or lines[-2] != 'ACTION:':
            raise ValueError('separated_channel_envelope_required')
        rationale = '\n'.join(lines[1:-2])
        if not rationale.strip():
            raise ValueError('empty_narrative')
    return action, rationale


def capture(task, arm, result, previous=None):
    text = result['raw']
    record = previous is not None
    if record and not previous['outcome_pass']:
        raise ValueError('record_requires_actual_success')
    rationale = text
    try:
        action, rationale = project(text, arm, record)
        feedback = dict(success=True, record=True) if record else code.check(task, action)
        action_valid = True
    except Exception as error:
        feedback = dict(success=False, error=str(error))
        action_valid = False
    tokens = len(result['token_ids']) - int(result['terminal'])
    return dict(task_id=task['id'], question_sha256=sha(task['text']), family=task['family'],
                arm=arm, kind='NEW' if record else 'SOURCE', target=text, target_sha256=sha(text),
                rationale=rationale, feedback=feedback, action_valid=action_valid,
                outcome_pass=feedback['success'], generated_tokens=tokens,
                token_contract=150 <= tokens <= 400 and result['terminal'] and not result['truncated'],
                student_prefix=neutral_prefix(task, previous), neutral_prefix_pass=True,
                source_target_sha256=previous['target_sha256'] if record else None,
                semantic_status='UNREVIEWED', admitted=False, call=result)


def admission(row, review):
    if review['target_sha256'] != row['target_sha256'] or not review['reason']:
        raise ValueError('hash_bound_full_text_review_required')
    if review['status'] not in ('PASS', 'FAIL', 'UNRESOLVED'):
        raise ValueError('explicit_semantic_status_required')
    if not review['quotes'] or any(quote not in row['target'] for quote in review['quotes']):
        raise ValueError('literal_evidence_required')
    if review['status'] == 'PASS' and not all(review.get(axis) is True for axis in AXES):
        raise ValueError('substantive_rubric_required')
    return (review['status'] == 'PASS' and row['outcome_pass'] and row['token_contract']
            and row['neutral_prefix_pass'])


def reduce(tasks, rows):
    if len(tasks) != 64 or len({task['id'] for task in tasks}) != 64:
        raise ValueError('fixed_64_denominator_required')
    keys = [(row['arm'], row['task_id'], row['kind']) for row in rows]
    if len(keys) != len(set(keys)) or len(rows) > 384:
        raise ValueError('duplicate_or_excess_calls')
    summary = {}
    for arm in ARMS:
        selected = [row for row in rows if row['arm'] == arm]
        sources = [row for row in selected if row['kind'] == 'SOURCE']
        summary[arm] = dict(denominator=64, calls=len(selected), source_calls=len(sources),
            initial_success=sum(row['outcome_pass'] for row in sources),
            qualified_tasks=len({row['task_id'] for row in selected if row['admitted']}),
            admitted_rows=sum(row['admitted'] for row in selected),
            unreviewed=sum(row['semantic_status'] == 'UNREVIEWED' for row in selected),
            kinds={kind: dict(calls=len([row for row in selected if row['kind'] == kind]),
                tokens=[row['generated_tokens'] for row in selected if row['kind'] == kind],
                token_pass=sum(row['token_contract'] for row in selected if row['kind'] == kind),
                admitted=sum(row['admitted'] for row in selected if row['kind'] == kind))
                for kind in ('SOURCE', 'NEW')},
            families={family: dict(denominator=sum(task['family'] == family for task in tasks),
                initial_success=sum(row['outcome_pass'] for row in sources if row['family'] == family),
                qualified_tasks=len({row['task_id'] for row in selected
                                     if row['admitted'] and row['family'] == family}))
                for family in sorted({task['family'] for task in tasks})})
    gain = summary['SEPARATED']['qualified_tasks'] - summary['LEGACY']['qualified_tasks']
    deficit = summary['LEGACY']['initial_success'] - summary['SEPARATED']['initial_success']
    complete = all(summary[arm]['source_calls'] == 64 and summary[arm]['unreviewed'] == 0 for arm in ARMS)
    return dict(arms=summary, qualified_task_gain=gain, initial_outcome_deficit=deficit,
                full_review_complete=complete, candidate=complete and gain >= 8 and deficit <= 4,
                fits=0, claim='FINITE_EXPOSED_PUBLIC_TEST_SCREEN_NOT_LEARNING_OR_GENERALIZATION')
