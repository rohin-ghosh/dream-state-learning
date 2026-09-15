"""R115 executed bounded CODE environment and strict experience routing."""

import json

from organism_v6 import orch_r108_code_parent_r114_f3 as policy


AFFORDANCE = 'The environment can inspect a bounded expression on your chosen list: emit {"inspect":{"expression":"sum(values)","values":[1,2]}}. It returns the actual result. These are optional tools, not goals. The named input is values; at most 12 integers. No attributes, imports, arbitrary functions, files, or network access.'
require, digest = policy.require, policy.digest


def last_json(raw):
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    for line in lines[-1:]:
        try:
            value = json.loads(line)
        except (ValueError, TypeError):
            continue
        if isinstance(value, dict):
            return value
    return None


def inspect_environment(raw):
    value = last_json(raw)
    if not isinstance(value, dict) or set(value) != {'inspect'}:
        return dict(status='NO_ENVIRONMENT_ACTION', enacted=False)
    action = value['inspect']
    try:
        require(isinstance(action, dict) and set(action) == {'expression', 'values'}, 'inspect_schema')
        require(isinstance(action['expression'], str) and len(action['expression']) <= 2000, 'bounded_expression')
        require(isinstance(action['values'], list) and len(action['values']) <= 12
            and all(type(item) is int and abs(item) <= 1000000 for item in action['values']), 'bounded_values')
        observation = policy.previous.gym_policy.gym.evaluate(action['expression'], dict(values=action['values']))
        return dict(status='COMPLETE', enacted=True, operation='INSPECT', inputs=action,
            observation=observation, arbitrary_python_executed=False)
    except (ValueError, TypeError, ZeroDivisionError, OverflowError, IndexError) as error:
        return dict(status='REJECTED', enacted=False, operation='INSPECT', reason=type(error).__name__,
            arbitrary_python_executed=False)


def visible_checker(task, raw):
    value = last_json(raw)
    if not isinstance(value, dict) or set(value) != {'expression'} or not isinstance(value['expression'], str):
        return dict(status='NO_REGISTERED_EXPRESSION', child_received=True)
    values = [3, 0, -4, 12, 3, -4]
    try:
        observed = policy.previous.gym_policy.gym.evaluate(value['expression'], dict(values=values))
        expected = policy.previous.gym_policy.gym.evaluate(task['reference_expression'], dict(values=values))
        return dict(status='COMPLETE', child_received=True, public_input=values,
            observed=observed, passed=observed == expected)
    except (ValueError, TypeError, ZeroDivisionError, OverflowError, IndexError) as error:
        return dict(status='INVALID_EXPRESSION', child_received=True, error_type=type(error).__name__)


def score(task, raw):
    value = last_json(raw)
    if not isinstance(value, dict) or set(value) != {'expression'} or not isinstance(value['expression'], str):
        return dict(correct=False, format_valid=False, passed=0, total=len(task['tests']))
    passed = 0
    for case in task['tests']:
        try:
            observed = policy.previous.gym_policy.gym.evaluate(value['expression'], case['arguments'])
            passed += type(observed) is type(case['expected']) and observed == case['expected']
        except (ValueError, TypeError, ZeroDivisionError, OverflowError, IndexError):
            pass
    return dict(correct=passed == len(task['tests']), format_valid=True, passed=passed, total=len(task['tests']))


def capture_routes(split, phase, *, evaluation_origin=None):
    require(split in ('TRAIN', 'DEV', 'FINAL', 'LEGACY'), 'capture_split')
    return dict(parent=split == 'TRAIN' and evaluation_origin is None,
        head=split in ('TRAIN', 'DEV') and evaluation_origin != 'FINAL',
        sleep=False, optimizer=False, teacher_target=False, phase=phase,
        evaluation_origin=evaluation_origin, elicitation_only=True)


def event(task, actor, text, *, completed=False, event_type='text'):
    return dict(actor=actor, text=text, source_sha256=policy.text_sha(text), split=task['split'],
        task_id=task['task_id'], task_sha256=task['content_sha256'], visibility='CHILD_VISIBLE',
        completed_response=completed, child_received=True, event_type=event_type)
