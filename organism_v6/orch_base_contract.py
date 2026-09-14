"""Fixed diagnostic policies; no training and no generated Python execution."""

import hashlib
import json

from organism_v6 import orch_code_bounded as code
from organism_v6 import orch_math_rich as math


MANIFEST = '5e675c309b202625a6ddf1d36c1a58f51ef656985821cec1cd6123424d927469'
STATES = ('BASE', 'ORIGINAL')


def sha(value):
    return hashlib.sha256(value.encode()).hexdigest()


def select(tasks, per_family):
    counts = {}
    chosen = []
    for task in tasks:
        family = task['family']
        if counts.get(family, 0) < per_family:
            chosen.append(task)
            counts[family] = counts.get(family, 0) + 1
    if len(chosen) != 4:
        raise ValueError('fixed_four_per_domain_required')
    return chosen


def prompt(entry, previous=None):
    if entry['domain'] == 'CODE':
        return code.prompt(entry['task'], 'rich', [] if previous is None else [previous], previous is not None)
    return math.prompt(entry['task'], 'rich' if previous is None else 'record',
                       None if previous is None else previous['target'])


def capture(entry, result, student, previous=None):
    text = result['raw']
    rationale = text
    if entry['domain'] == 'CODE':
        try:
            action, rationale = code.parse_action(text, previous is not None)
            feedback = code.check(entry['task'], action) if previous is None else dict(success=True, record=True)
        except Exception as error:
            feedback = dict(success=False, error=str(error))
        outcome = feedback['success'] and (previous is None or previous['outcome_pass'])
    else:
        value = math.final_value(text)
        outcome = value is not None and value == math.number(entry['task']['gold'])
        feedback = dict(success=outcome)
    tokens = len(result['token_ids']) - int(result['terminal'])
    return dict(task_id=entry['task']['id'], domain=entry['domain'], family=entry['task']['family'],
                kind='solution' if previous is None else 'record', target=text,
                target_sha256=sha(text), feedback=feedback, outcome_pass=outcome,
                generated_tokens=tokens, rationale=rationale,
                token_contract=150 <= tokens <= 400 and result['terminal'] and not result['truncated'],
                student_prefix=student, call=result, semantic_status='UNREVIEWED', admitted=False)


def admission(row, review):
    if review['target_sha256'] != row['target_sha256'] or not review['reason']:
        raise ValueError('hash_bound_full_text_review_required')
    if review['status'] not in ('PASS', 'FAIL', 'UNRESOLVED'):
        raise ValueError('explicit_semantic_status_required')
    if not review['quotes'] or any(quote not in row['target'] for quote in review['quotes']):
        raise ValueError('literal_evidence_required')
    axes = ('ownership', 'grounding', 'checkable', 'truthful', 'no_padding', 'reusable')
    if review['status'] == 'PASS' and not all(review.get(axis) is True for axis in axes):
        raise ValueError('substantive_rubric_required')
    return review['status'] == 'PASS' and row['outcome_pass'] and row['token_contract']


def reduce(entries, rows):
    keys = [(row['task_id'], row['state'], row['kind']) for row in rows]
    if len(keys) != len(set(keys)):
        raise ValueError('duplicate_calls')
    summary = {}
    for state in STATES:
        selected = [row for row in rows if row['state'] == state]
        summary[state] = dict(denominator=8, calls=len(selected),
            initial_success=sum(row['outcome_pass'] for row in selected if row['kind'] == 'solution'),
            admitted_tasks=sum(any(row['task_id'] == entry['task']['id'] and row['admitted'] for row in selected) for entry in entries),
            admitted_rows=sum(row['admitted'] for row in selected),
            initial_admitted=sum(row['admitted'] for row in selected if row['kind'] == 'solution'),
            record_admitted=sum(row['admitted'] for row in selected if row['kind'] == 'record'),
            tokens=sorted(row['generated_tokens'] for row in selected))
    pairs = []
    for entry in entries:
        pairs.append(dict(task_id=entry['task']['id'], domain=entry['domain'], **{
            state: any(row['task_id'] == entry['task']['id'] and row['state'] == state and row['admitted'] for row in rows)
            for state in STATES}))
    difference = summary['BASE']['admitted_tasks'] - summary['ORIGINAL']['admitted_tasks']
    support = difference >= 3 and summary['BASE']['initial_success'] >= summary['ORIGINAL']['initial_success'] - 1
    return dict(states=summary, pairs=pairs, difference=difference, local_suppression_support=support,
                claim='EXPOSED_DIAGNOSTIC_REUSE_NOT_LEARNING_OR_GENERALIZATION', fits=0)
