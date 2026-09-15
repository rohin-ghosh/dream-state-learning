"""Prospective paired verdict-only repair policy; no fitting or target editing."""

import hashlib
import json

from organism_v6.orch_math_rich import RICH_GUIDANCE, digest, final_value, number
from organism_v6.orch_math_replication import MANIFEST_SHA256, sha256, write


BRANCHES = ('GUIDED', 'RETRY')
REJECTION = 'The exact-answer checker rejected your final value. '
CORRECTION = ('Recompute from the given problem, identify a meaningful correction '
              'to your prior answer, and explain a reusable lesson. ' + RICH_GUIDANCE)
RECORD = ('Write your own reusable record: explain the specific operations, when '
          'they apply, and a concrete check using this problem. Retain its final answer. '
          + RICH_GUIDANCE)
AXES = ('first_person', 'grounded_operations', 'checkable_expectation',
        'reusable_content', 'no_padding', 'no_false_premises', 'no_invented_guidance')


def text_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()


def prior_number(raw):
    parsed = final_value(raw)
    if parsed is not None:
        return parsed
    try:
        return number(raw.strip())
    except (ValueError, ZeroDivisionError):
        return None


def branch_order(position):
    return BRANCHES if position % 2 == 0 else tuple(reversed(BRANCHES))


def shard_for(position):
    return (position // 2) % 4


def validate_roster(document):
    tasks = document['tasks']
    if not 0 < len(tasks) <= 24 or document['denominator'] != len(tasks):
        raise ValueError('bounded_frozen_roster_required')
    hashes = [task['question_sha256'] for task in tasks]
    if hashes != sorted(set(hashes)):
        raise ValueError('unique_stable_task_hash_order_required')
    for position, task in enumerate(tasks):
        if (task['question_sha256'] != digest(' '.join(task['question'].lower().split()))
                or task['prior_sha256'] != text_hash(task['prior_raw'])
                or task['branch_order'] != list(branch_order(position))
                or task['shard'] != shard_for(position)
                or task['audit_status'] != 'PASS'
                or number(task['audited_value']) != number(task['gold'])
                or prior_number(task['prior_raw']) is None
                or prior_number(task['prior_raw']) == number(task['gold'])):
            raise ValueError('task_raw_gold_or_prospective_order_drift')
    return tasks


def prompt(task, branch, kind, repair_raw=None):
    if branch not in BRANCHES or kind not in ('repair', 'record'):
        raise ValueError('unknown_branch_or_kind')
    student = [{'role': 'user', 'content': task['question']},
               {'role': 'assistant', 'content': task['prior_raw']}]
    if kind == 'repair':
        request = (REJECTION if branch == 'GUIDED' else '') + CORRECTION
    else:
        if repair_raw is None:
            raise ValueError('actual_own_repair_required')
        student.append({'role': 'assistant', 'content': repair_raw})
        request = RECORD
    return student + [{'role': 'user', 'content': request}], student


def capture(task, branch, kind, result, student, prefix_ids):
    raw = result['raw']
    predicted = final_value(raw)
    outcome = result.get('error') is None and predicted is not None and predicted == number(task['gold'])
    tokens = len(result['token_ids']) - int(bool(result['token_ids']) and result['terminal'])
    bounded = (150 <= tokens <= 400 and not result['truncated']
               and result['prompt_tokens'] <= 2048 and result.get('error') is None)
    return dict(task_id=task['id'], cohort=task['cohort'], branch=branch, kind=kind,
                prior_sha256=task['prior_sha256'], outcome_pass=outcome,
                generated_tokens=tokens, token_contract_pass=bounded,
                candidate=outcome and bounded, target=raw, target_sha256=text_hash(raw),
                student_prefix=student, student_prefix_sha256=digest(student),
                prefix_token_ids=prefix_ids, target_token_ids=result['token_ids'],
                labels=[-100] * len(prefix_ids) + result['token_ids'],
                teacher_loss=False, semantic_status='UNREVIEWED', admitted=False, call=result)


def review_row(row, decision):
    if (decision.get('target_sha256') != row['target_sha256']
            or decision.get('student_prefix_sha256') != row['student_prefix_sha256']
            or decision.get('full_text_read') is not True
            or decision.get('prefix_read') is not True or not decision.get('reason')
            or decision.get('status') not in ('PASS', 'FAIL', 'UNRESOLVED')):
        raise ValueError('exact_fulltext_and_prefix_review_required')
    spans = decision.get('evidence_spans', [])
    if not spans or any(not span.strip() or span not in row['target'] for span in spans):
        raise ValueError('verbatim_target_evidence_required')
    if decision['status'] == 'PASS' and not all(decision.get(axis) is True for axis in AXES):
        raise ValueError('all_semantic_axes_required')
    if decision.get('prefix_supported') not in (True, False):
        raise ValueError('explicit_prefix_judgment_required')
    if row['kind'] == 'repair' and decision.get('meaningful_revision') not in (True, False):
        raise ValueError('explicit_mathematical_revision_required')
    qualified = bool(row['candidate'] and decision['status'] == 'PASS'
                     and decision['prefix_supported']
                     and (row['kind'] != 'repair' or decision['meaningful_revision']))
    return dict(row, review=decision, semantic_status=decision['status'], admitted=qualified)


def reduce_rows(document, rows, complete):
    tasks = validate_roster(document)
    by_key = {(row['task_id'], row['branch'], row['kind']): row for row in rows}
    if len(by_key) != len(rows) or len(rows) > 4 * len(tasks):
        raise ValueError('duplicate_or_excess_calls')
    expected = set()
    for task in tasks:
        for branch in BRANCHES:
            key = (task['id'], branch, 'repair')
            expected.add(key)
            if by_key.get(key, {}).get('outcome_pass'):
                expected.add((task['id'], branch, 'record'))
    if not set(by_key) <= expected or (complete and set(by_key) != expected):
        raise ValueError('missing_or_unconditional_record_calls')
    summary = dict(denominator=len(tasks), native_calls=len(rows), complete=complete,
                   fits=0, updates=0, branches={})
    for branch in BRANCHES:
        repairs = [row for row in rows if row['branch'] == branch and row['kind'] == 'repair']
        records = [row for row in rows if row['branch'] == branch and row['kind'] == 'record']
        qualified = {row['task_id'] for row in repairs if row['admitted']}
        summary['branches'][branch] = dict(
            repair_calls=len(repairs), correction_success=sum(row['outcome_pass'] for row in repairs),
            meaningful_revision=sum(row.get('review', {}).get('meaningful_revision', False) for row in repairs),
            semantic_rubric_pass=sum(row['semantic_status'] == 'PASS' for row in repairs),
            prefix_support=sum(row.get('review', {}).get('prefix_supported', False) for row in repairs),
            token_contract_pass=sum(row['token_contract_pass'] for row in repairs),
            outcome_and_rubric=sum(row['outcome_pass'] and row['semantic_status'] == 'PASS' for row in repairs),
            joint_repair_admissions=len(qualified), record_calls=len(records),
            record_outcome_pass=sum(row['outcome_pass'] for row in records),
            record_standalone_joint=sum(row['admitted'] for row in records),
            record_yield=sum(row['admitted'] and row['task_id'] in qualified for row in records),
            repair_tokens=sorted(row['generated_tokens'] for row in repairs),
            record_tokens=sorted(row['generated_tokens'] for row in records))
    advantage = (summary['branches']['GUIDED']['joint_repair_admissions']
                 - summary['branches']['RETRY']['joint_repair_admissions'])
    reviewed = all(row['semantic_status'] != 'UNREVIEWED' for row in rows)
    summary.update(joint_advantage=advantage, fulltext_review_complete=reviewed,
                   decision=('LOCAL_SIGNAL' if advantage >= 4 else 'DEALLOCATE_SCREEN')
                   if complete and reviewed else 'INCOMPLETE_NO_SCIENTIFIC_CONCLUSION')
    summary['paired'] = [dict(task_id=task['id'], **{
        branch: by_key.get((task['id'], branch, 'repair'), {}).get('admitted', False)
        for branch in BRANCHES}) for task in tasks]
    return summary
