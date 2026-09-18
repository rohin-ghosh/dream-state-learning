"""Prospective DEV math screen; numeric success never implies semantic admission."""

from collections import Counter
from fractions import Fraction
import hashlib
import json
import re


MINING = ('percentages', 'work_rates', 'fractional_quantities', 'group_accounting')
VALIDATION = ('geometry_measurement', 'age_time_relations')
PER_FAMILY = 8
RICH_GUIDANCE = (
    'Solve in your own first-person voice, using 150–400 tokens. '
    'Identify the given quantities and requested unknown, explain the actual '
    'reusable operations connecting them, and check the result against the '
    'problem. Do not pad with generic advice or invent observations. '
    'Finish with a separate line FINAL: followed by just the numeric answer.'
)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def number(value):
    value = value.strip().replace(',', '')
    if not re.fullmatch(r'[+-]?(?:\d+(?:\.\d+)?|\.\d+)(?:/\d+)?', value):
        raise ValueError('unsupported_exact_numeric_value')
    return Fraction(value)


def final_value(text):
    lines = text.strip().splitlines()
    if not lines or not lines[-1].startswith('FINAL:'):
        return None
    try:
        return number(lines[-1][6:])
    except (ValueError, ZeroDivisionError):
        return None


def family(question):
    text = question.lower()
    if re.search(r'\b(area|perimeter|diameter|radius|rectangle|triangle|square feet|square meters)\b', text):
        return VALIDATION[0]
    if re.search(r'\b(years old|older than|younger than|years ago|o.clock|a\.m\.|p\.m\.)', text):
        return VALIDATION[1]
    if '%' in text or re.search(r'\b(percent|percentage)\b', text):
        return MINING[0]
    if re.search(r'\b(per hour|per minute|miles per|each hour|every hour|an hour|hours? to)\b', text):
        return MINING[1]
    if re.search(r'\b(half|third|quarter|fourth|fifth|sixth|one-third|two-thirds)\b|\b\d+/\d+\b', text):
        return MINING[2]
    if re.search(r'\b(each|every|per|groups?|boxes|packs|dozen)\b', text):
        return MINING[3]
    return None


def build_tasks(records):
    pools = {name: [] for name in MINING + VALIDATION}
    seen = set()
    for index, record in enumerate(records):
        question = record['question'].strip()
        identity = digest(' '.join(question.lower().split()))
        if identity in seen:
            continue
        seen.add(identity)
        name = family(question)
        if name is None:
            continue
        gold = str(number(record['answer'].rsplit('####', 1)[1]))
        pools[name].append(dict(id=f'gsm8k-train-{index}', question=question,
                                question_sha256=identity, gold=gold, family=name))
    tasks = []
    for name in MINING:
        ordered = sorted(pools[name], key=lambda task: digest('MATH_RICH_SCREEN_V1:' + task['id']))
        if len(ordered) < PER_FAMILY:
            raise ValueError('insufficient_prospective_family:' + name)
        tasks.extend(ordered[:PER_FAMILY])
    return dict(tasks=tasks, family_counts={name: len(pool) for name, pool in pools.items()},
                denominator=len(tasks), per_family=PER_FAMILY,
                held_validation_ids={name: [task['id'] for task in pools[name]] for name in VALIDATION},
                no_l2_l3_access=True, fit_ready=False)


def prompt(task, kind, previous=None):
    neutral = [{'role': 'user', 'content': task['question']}]
    if kind == 'terse':
        return neutral + [{'role': 'user', 'content': 'Answer directly without explanation. Last line FINAL: numeric answer.'}], neutral
    if kind == 'rich':
        return [{'role': 'system', 'content': RICH_GUIDANCE}] + neutral, neutral
    if previous is None:
        raise ValueError('previous_child_response_required')
    history = neutral + [{'role': 'assistant', 'content': previous}]
    if kind == 'correction':
        student = history + [{'role': 'user', 'content': 'Revisit your solution and explain any revision and reusable lesson.'}]
        guided = history + [{'role': 'user', 'content': 'The exact-answer checker rejected your final value. Recompute from the given problem, identify a meaningful correction, and explain a reusable lesson. ' + RICH_GUIDANCE}]
    elif kind == 'record':
        student = history + [{'role': 'user', 'content': 'Write your own reusable record of this solved task.'}]
        guided = history + [{'role': 'user', 'content': 'The final value passed the exact-answer checker. Write your own reusable record: explain the specific operations, when they apply, and a concrete check using this problem. Retain its final answer. ' + RICH_GUIDANCE}]
    else:
        raise ValueError('unknown_row_class')
    return guided, student


def capture(task, kind, result, student):
    predicted = final_value(result['raw'])
    correct = predicted is not None and predicted == number(task['gold'])
    tokens = len(result['token_ids']) - int(bool(result['token_ids']) and result['terminal'])
    bounded = 150 <= tokens <= 400 and not result['truncated'] and result['prompt_tokens'] <= 2048
    return dict(task_id=task['id'], family=task['family'], kind=kind, gold=task['gold'],
                outcome_pass=correct, token_contract_pass=bounded, generated_tokens=tokens,
                candidate=kind != 'terse' and correct and bounded,
                semantic_status='UNREVIEWED', admitted=False, student_prefix=student,
                target=result['raw'], target_sha256=hashlib.sha256(result['raw'].encode()).hexdigest(),
                call=result)


def reduce_screen(tasks, rows):
    by_key = {(row['task_id'], row['kind']): row for row in rows}
    if len(by_key) != len(rows):
        raise ValueError('duplicate_task_kind')
    counts = {}
    for name in MINING:
        fixed = [task for task in tasks if task['family'] == name]
        if len(fixed) != PER_FAMILY:
            raise ValueError('changed_prospective_denominator')
        successes = {kind: sum(by_key.get((task['id'], kind), {}).get('outcome_pass', False)
                               for task in fixed) for kind in ('rich', 'terse')}
        complete = all((task['id'], kind) in by_key for task in fixed for kind in ('rich', 'terse'))
        counts[name] = dict(denominator=len(fixed), **successes, complete=complete,
                           eligible=complete and successes['rich'] > successes['terse'])
    return dict(families=counts, denominator=len(tasks), calls=len(rows),
                row_classes=dict(Counter(row['kind'] for row in rows)),
                outcome_pass=sum(row['outcome_pass'] for row in rows),
                unreviewed_candidates=sum(row['candidate'] for row in rows),
                token_distribution=sorted(row['generated_tokens'] for row in rows if row['kind'] != 'terse'),
                admitted=0, fit_ready=False,
                claim='FIXED_DENOMINATOR_DEV_SCREEN_NOT_LEARNING_OR_TRANSFER')


def admit(row, decision, eligible):
    if decision.get('status') not in ('PASS', 'FAIL', 'UNRESOLVED'):
        raise ValueError('explicit_semantic_reading_required')
    if decision.get('target_sha256') != row['target_sha256'] or not decision.get('reason'):
        raise ValueError('review_must_bind_exact_target_and_reason')
    spans = decision.get('evidence_spans', [])
    if not spans or any(span not in row['target'] or not span.strip() for span in spans):
        raise ValueError('grounded_review_spans_required')
    if decision['status'] == 'PASS' and not all(decision.get(key) is True for key in
            ('first_person', 'grounded_operations', 'checkable_expectation', 'reusable_content', 'no_padding')):
        raise ValueError('all_substantive_rubric_axes_required')
    if row['kind'] == 'correction' and decision['status'] == 'PASS' and decision.get('meaningful_revision') is not True:
        raise ValueError('correction_requires_meaningful_revision')
    return dict(row, semantic_status=decision['status'], review=decision,
                admitted=bool(row['candidate'] and eligible and decision['status'] == 'PASS'))
