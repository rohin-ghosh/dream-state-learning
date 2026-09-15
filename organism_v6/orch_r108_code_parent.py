"""Predetermined bounded-expression CODE parenting; context changes, not weights."""

from copy import deepcopy
import hashlib
import json
import re

from organism_v6 import orch_code_bounded as gym
from organism_v6 import orch_r107_base_anchors as anchors
from organism_v6 import orch_r107_capability as capability


VERSION = 'R108_CODE_BASE_PARENT_DISCOVERY_V1'
PREFIX = 'R108_CODE_PARENT_20260915_A1'
BASE_SHA = anchors.BASE_SHA
HOST_SHA = '6bcd6b8370cc2f2a15e1e488352b4cec96b1e137489d52c3324c199536a09ba8'
GPU_UUID = 'GPU-ff5f84e9-c70e-272d-a8e0-eb20aad05ac6'
STOP_SHA = '1fe38d9fea6bed06f07c3a5eb0ccbb029635d7af148b38367d8cd51dddfc2ceb'
NATIVE_CAP, PARENT_CAP, CYCLES = 100, 20, 10
CONTEXT, OUTPUT = 32768, 2048
require, digest = anchors.require, anchors.digest
SYSTEM = ('Solve the stated bounded expression task. Reason where useful, then put exactly '
    'one JSON object {"expression":"..."} on the final nonempty line. No output follows it. '
    + gym.SPEC)
REFLECTION_SYSTEM = ('Reflect on your actual CODE attempt and the actual parent intervention. '
    'Consider relevant alternative interpretations, your reasoning process and limits, and what '
    'should change in your next attempt. Distinguish observations from guesses. Do not invent '
    'test results, echo advice mechanically, or pad repeated prose. No branch count, minimum '
    'length, checklist, or predetermined emotional response is required.')
PARENT_INSTRUCTIONS = ('You are the genuine supportive Astra parent for exploratory frozen-BASE '
    'CODE parenting. You see one actual TRAIN attempt and its machine failure class, not oracle '
    'cases or expected answers. Choose relevant intervention classes: perception, persistence, '
    'metacognition, curiosity, goal/meta-goal regulation, reflection, action steering, affective-value. '
    'Ground guidance in the actual child state and identify your chosen classes and rationale. '
    'If the attempt passed, discuss uncertainty and process rather than invent a failure. Never '
    'supply an answer, expression, implementation, code, pseudocode, worked example, expected '
    'test output, or invented observation. No tools, held data, hidden tests or scores are available. '
    'Coach how to notice, reason, judge and redirect; do not solve the task. Avoid branch-count, '
    'length and template demands. Return only the requested JSON plan; preserve episode order.')


def question_hash(text):
    return digest(' '.join(text.split()).casefold())


def token_budget(prompt_tokens):
    require(type(prompt_tokens) is int and 0 < prompt_tokens < CONTEXT, 'full_context_no_truncation')
    return min(OUTPUT, CONTEXT - prompt_tokens)


def specification(kind, parameter):
    specs = [
        (f'Sum each entry multiplied by its zero-based index, but include only entries strictly greater than {parameter}. Return zero if none qualify.',
         f'sum([values[index] * index for index in range(len(values)) if values[index] > {parameter}])'),
        (f'Return a list in original order: replace each negative entry by its absolute value plus {parameter}; leave nonnegative entries unchanged.',
         f'[abs(value) + {parameter} if value < 0 else value for value in values]'),
        (f'Count adjacent pairs whose second entry exceeds the first by strictly more than {parameter}. Lists shorter than two have count zero.',
         f'len([index for index in range(len(values)-1) if values[index+1] - values[index] > {parameter}])'),
        (f'Rotate the list left by {parameter} positions, wrapping around. The empty list stays empty.',
         f'values[{parameter} % len(values):] + values[:{parameter} % len(values)] if values else []'),
        (f'Return each distinct entry on its first occurrence, preserving order, but discard entries equal to {parameter}.',
         f'[values[index] for index in range(len(values)) if values[index] != {parameter} and values[index] not in values[:index]]'),
        (f'Sum entries at indices divisible by {parameter}, starting at index zero. Return zero on an empty list.',
         f'sum(values[::{parameter}])'),
        (f'Clamp each entry to the closed interval from {-parameter} to {parameter}, preserving order and length.',
         f'[max({-parameter}, min({parameter}, value)) for value in values]'),
        (f'Sum the entries at even indices minus the entries at odd indices, then add {parameter}. For an empty list return {parameter}.',
         f'sum(values[::2]) - sum(values[1::2]) + {parameter}'),
        (f'Return the zero-based indices of entries whose remainder on division by {parameter} is one, preserving index order.',
         f'[index for index in range(len(values)) if values[index] % {parameter} == 1]'),
        (f'Return adjacent forward differences (second minus first), discarding differences with absolute value greater than {parameter}. Lists shorter than two return an empty list.',
         f'[values[index+1] - values[index] for index in range(len(values)-1) if abs(values[index+1]-values[index]) <= {parameter}]'),
    ]
    return specs[kind]


def tasks():
    result = []
    for cycle in range(1, CYCLES + 1):
        for offset in range(6):
            split = 'TRAIN' if offset < 2 else 'HELD'
            parameter = 3 + cycle * 7 + offset
            question, reference = specification((cycle + offset) % 10, parameter)
            prompt = ('The only named argument is values, a list of integers with length at most 12. '
                + question + '\nReturn the requested bounded expression over values.')
            environments = [dict(values=values) for values in ([], [0], [-parameter-2, parameter+3],
                [parameter, -parameter, 1, 1, parameter+1, -1], [3, 0, -4, 12, 3, -4],
                [parameter+2, parameter+4, -parameter-5, 0, parameter+2, 2, 1])]
            row = dict(task_id=f'{PREFIX}_{split}_C{cycle:02d}_E{offset+1}', split=split,
                cycle=cycle, slot=offset+1, family='code', cohort=PREFIX, question=question, prompt=prompt,
                prompt_sha256=digest(prompt), question_sha256=question_hash(question),
                tests=[dict(arguments=environment, expected=gym.evaluate(reference, environment))
                    for environment in environments], reference_expression=reference)
            row['content_sha256'] = digest(row)
            result.append(row)
    return result


def validate_cohort(rows, exclusion):
    require(rows == tasks(), 'exact_frozen_code_cohort')
    prior = anchors.tasks() + capability.tasks()
    denied_ids = set(exclusion['task_ids']) | {row['id'] for row in prior}
    denied_prompts = set(exclusion['prompt_hashes']) | {row['prompt_sha256'] for row in prior}
    denied_questions = set(exclusion['question_hashes']) | {question_hash(row['prompt']) for row in prior}
    require(len(rows) == 60 and len({row['task_id'] for row in rows}) == 60, 'sixty_unique_tasks')
    require(not denied_ids.intersection(row['task_id'] for row in rows)
        and not denied_prompts.intersection(row['prompt_sha256'] for row in rows)
        and not denied_questions.intersection(row['question_sha256'] for row in rows), 'known_cohort_overlap')
    require(len({row['prompt_sha256'] for row in rows}) == 60, 'distinct_prompts')
    return dict(status='PASS', train_tasks=20, fresh_held_tasks=40,
        fixed32_and_all64anchors_excluded=True, known_registry_sha256=digest(exclusion),
        disclosure='Synthetic bounded-expression diagnostic; exact metadata exclusion, not semantic independence or full census.')


def schedule(rows):
    result = []
    for cycle in range(1, CYCLES + 1):
        for task in [row for row in rows if row['cycle'] == cycle]:
            phases = ('original', 'parent', 'reflection', 'continuation') if task['split'] == 'TRAIN' else ('held',)
            for phase in phases:
                result.append(dict(cell_id=task['task_id']+'_'+phase, task_id=task['task_id'],
                    cycle=cycle, slot=task['slot'], phase=phase, kind='PARENT' if phase == 'parent' else 'NATIVE'))
    require(sum(row['kind'] == 'NATIVE' for row in result) == NATIVE_CAP
        and sum(row['kind'] == 'PARENT' for row in result) == PARENT_CAP, 'exact100plus20')
    return result


def messages(task, memory=''):
    require(task in tasks(), 'frozen_task_required')
    system = SYSTEM + ('\n\nYour own latest TRAIN reflection, not a new observation:\n'+memory if memory else '')
    return [dict(role='system', content=system), dict(role='user', content=task['prompt'])]


def outcome(task, response):
    base = dict(terminal=response['terminal'], truncated=response['truncated'],
        generated_tokens=len(response['token_ids']), passed=False, case_count=len(task['tests']))
    if response['truncated']:
        return dict(base, failure_class='output_truncated')
    if not response['terminal']:
        return dict(base, failure_class='nonterminal_output')
    raw = response['raw'].strip()
    if not raw:
        return dict(base, failure_class='missing_answer')
    try:
        document = anchors.strict_json(raw.splitlines()[-1])
        require(isinstance(document, dict) and set(document) == {'expression'}
            and isinstance(document['expression'], str), 'expression_schema')
    except (ValueError, TypeError):
        return dict(base, failure_class='missing_exact_final_json')
    try:
        results = [gym.evaluate(document['expression'], row['arguments']) for row in task['tests']]
    except (ValueError, SyntaxError, TypeError, KeyError, IndexError, ZeroDivisionError, OverflowError):
        return dict(base, failure_class='unsafe_or_invalid_expression')
    passed = sum(anchors.same(actual, test['expected']) for actual, test in zip(results, task['tests']))
    return dict(base, passed=passed == len(results), passed_cases=passed,
        failure_class='passed_bounded_cases' if passed == len(results) else 'wrong_on_bounded_cases')


def parent_payload(task, original, memory):
    require(task['split'] == 'TRAIN', 'no_held_to_parent')
    payload = dict(split='TRAIN', cycle=task['cycle'], episode_index=task['slot'],
        episodes=[dict(task_id=task['task_id'], public_experience=dict(prompt=task['prompt'],
            child_raw=original['response']['raw'], failure_class=original['outcome']['failure_class'],
            terminal=original['response']['terminal'], truncated=original['response']['truncated']))],
        prior_own_reflection=memory)
    validate_parent_payload(payload)
    return payload


def validate_parent_payload(payload):
    require(set(payload) == {'split', 'cycle', 'episode_index', 'episodes', 'prior_own_reflection'}
        and payload['split'] == 'TRAIN' and type(payload['cycle']) is int
        and 1 <= payload['cycle'] <= 10 and payload['episode_index'] in (1, 2)
        and len(payload['episodes']) == 1, 'parent_strict_train_schema')
    episode = payload['episodes'][0]
    require(set(episode) == {'task_id', 'public_experience'}, 'parent_episode_allowlist')
    task = next((row for row in tasks() if row['task_id'] == episode['task_id']), None)
    require(task is not None and task['split'] == 'TRAIN' and task['cycle'] == payload['cycle']
        and task['slot'] == payload['episode_index'], 'exact_train_episode')
    public = episode['public_experience']
    require(set(public) == {'prompt', 'child_raw', 'failure_class', 'terminal', 'truncated'}
        and public['prompt'] == task['prompt'] and isinstance(public['child_raw'], str)
        and isinstance(public['failure_class'], str) and type(public['terminal']) is bool
        and type(public['truncated']) is bool and isinstance(payload['prior_own_reflection'], str),
        'no_oracle_or_held_parent_fields')
    return payload


def parent_lesson(plan, task):
    require(plan['order'] == [task['task_id']] and set(plan['episode_guidance']) == {task['task_id']},
        'unchanged_single_episode_order')
    text = plan['guidance'] + '\n' + plan['episode_guidance'][task['task_id']]
    require(text.strip() and len(text) <= 16000 and not re.search(
        r'```|`|"expression"|\bdef\s+\w+\(|\blambda\s+\w+\s*:|\breturn\s+(?:values\b|\[|\()', text)
        and task['reference_expression'] not in text, 'no_code_answer_provision')
    return text


def triple(task, original, parent, reflection, continuation):
    return dict(task_id=task['task_id'], cycle=task['cycle'], episode_index=task['slot'], split='TRAIN',
        child_state_sha256=digest(original), intervention_sha256=digest(parent),
        reflection_sha256=digest(reflection), continuation_sha256=digest(continuation),
        before=original['outcome'], after=continuation['outcome'],
        continuation_changed=original['response']['raw'] != continuation['response']['raw'],
        helpful=None, semantic_changed=None, audit_status='UNREVIEWED', weight_updates=0,
        retained_weight_learning_claim=False, automatic_fit=False)
