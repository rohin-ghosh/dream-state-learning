"""Synthetic CODE cohort, bounded interpreter and TRAIN-only parent contract."""

from copy import deepcopy
import json

import pytest

from organism_v6 import orch_r108_code_parent as policy
from gpu import orch_r108_code_parent_registry as registry


def response(raw, **updates):
    return dict(dict(raw=raw, token_ids=[11, 12, 1], terminal=True, truncated=False), **updates)


@pytest.fixture
def task():
    return policy.tasks()[0]


def test_fixed60_tasks_and_exact100plus20_schedule():
    tasks = policy.tasks()
    assert tasks == policy.tasks()
    assert policy.validate_cohort(tasks, registry.collect([]))['status'] == 'PASS'
    schedule = policy.schedule(tasks)
    assert len(schedule) == len({row['cell_id'] for row in schedule}) == 120
    assert sum(row['kind']=='NATIVE' for row in schedule) == 100
    assert sum(row['kind']=='PARENT' for row in schedule) == 20
    for cycle in range(1, 11):
        rows = [row for row in schedule if row['cycle'] == cycle]
        assert [row['phase'] for row in rows] == ['original', 'parent', 'reflection', 'continuation']*2 + ['held']*4


def test_all_reference_expressions_verified_in_safe_interpreter():
    for task in policy.tasks():
        result = policy.outcome(task, response(json.dumps(dict(expression=task['reference_expression']))))
        assert result['passed'] and result['passed_cases'] == 6


@pytest.mark.parametrize('field', ['task_ids', 'prompt_hashes', 'question_hashes'])
def test_known_registry_collisions_fail(field, task):
    exclusions = registry.collect([])
    key = {'task_ids':'task_id','prompt_hashes':'prompt_sha256','question_hashes':'question_sha256'}[field]
    exclusions[field].append(task[key])
    with pytest.raises(ValueError, match='overlap'):
        policy.validate_cohort(policy.tasks(), exclusions)


@pytest.mark.parametrize('expression', ["__import__('os').system('false')", 'values.real',
    '(lambda values: values)(values)', 'sum(range(10000000))', '[1]*10000000', 'open(1)', '1/0'])
def test_generated_execution_never_allowed(task, expression):
    assert policy.outcome(task, response(json.dumps(dict(expression=expression))))['failure_class'] == 'unsafe_or_invalid_expression'


@pytest.mark.parametrize('raw,ending,category', [('',{},'missing_answer'), ('Reasoning only',{},'missing_exact_final_json'),
    ('{"expression":"0"}',{},'wrong_on_bounded_cases'), ('anything',{'truncated':True},'output_truncated'),
    ('anything',{'terminal':False},'nonterminal_output'),
    ('{"expression":"0","expression":"1"}',{},'missing_exact_final_json')])
def test_failure_classes_are_separate(task, raw, ending, category):
    assert policy.outcome(task, response(raw, **ending))['failure_class'] == category


def test_parent_sees_actual_train_failure_not_oracle(task):
    original = dict(response=response('Wrong format'), outcome=dict(failure_class='missing_exact_final_json'))
    payload = policy.parent_payload(task, original, 'Own observation')
    text = json.dumps(payload)
    assert task['reference_expression'] not in text
    assert 'expected' not in text and 'tests' not in text
    assert payload['episodes'][0]['public_experience']['child_raw'] == 'Wrong format'
    assert policy.validate_parent_payload(payload) == payload


@pytest.mark.parametrize('mutation', ['held', 'oracle', 'score', 'cycle', 'task', 'extra'])
def test_parent_visibility_allowlist(task, mutation):
    payload = policy.parent_payload(task, dict(response=response('actual'),outcome=dict(failure_class='passed_bounded_cases')), '')
    if mutation == 'held':
        payload['split'] = 'HELD'
    elif mutation in ('oracle','score'):
        payload['episodes'][0]['public_experience'][mutation] = 'secret'
    elif mutation == 'cycle':
        payload['cycle'] = 11
    elif mutation == 'task':
        payload['episodes'][0]['task_id'] = policy.tasks()[2]['task_id']
    else:
        payload['hidden'] = 'secret'
    with pytest.raises(ValueError):
        policy.validate_parent_payload(payload)


def test_held_payload_construction_rejected():
    with pytest.raises(ValueError, match='held'):
        policy.parent_payload(policy.tasks()[2], {}, '')


@pytest.mark.parametrize('text', ['```python\nanswer\n```', '`values`', '{"expression":"values"}',
    'def solve(values):', 'lambda values: values', 'return values'])
def test_parent_answer_provision_rejected(task, text):
    with pytest.raises(ValueError, match='answer_provision'):
        policy.parent_lesson(dict(guidance=text, episode_guidance={task['task_id']:''}, order=[task['task_id']]),task)


def test_ordinary_process_guidance_not_false_code(task):
    text = 'Return to the stated goal and distinguish what you observed from assumptions.'
    plan = dict(guidance=text, episode_guidance={task['task_id']:'Consider an alternative interpretation when relevant.'}, order=[task['task_id']])
    assert text in policy.parent_lesson(plan,task)


def test_triples_separate_byte_change_from_semantics(task):
    original=dict(response=response('old'),outcome=dict(passed=False))
    changed=dict(response=response('new'),outcome=dict(passed=True))
    triple=policy.triple(task,original,dict(actual='parent'),dict(actual='reflection'),changed)
    assert triple['continuation_changed'] is True
    assert triple['helpful'] is None and triple['semantic_changed'] is None
    assert triple['retained_weight_learning_claim'] is False and triple['weight_updates'] == 0


def test_registry_skips_raw_and_symlink_metadata(tmp_path):
    (tmp_path/'COHORT.json').write_text(json.dumps(dict(task_id='known',prompt='Public prompt',oracle={'secret':'do not export'})))
    (tmp_path/'raw').mkdir()
    (tmp_path/'raw/TASKS.json').write_text('{"task_id":"raw_forbidden"}')
    (tmp_path/'LINK_TASKS.json').symlink_to(tmp_path/'raw/TASKS.json')
    result=registry.collect([tmp_path])
    assert 'known' in result['task_ids'] and 'raw_forbidden' not in result['task_ids']
    assert 'Public prompt' not in json.dumps(result) and 'do not export' not in json.dumps(result)


@pytest.mark.parametrize('length', [0,32768,32769,-1])
def test_context_overflow_never_truncates(length):
    with pytest.raises(ValueError):
        policy.token_budget(length)
