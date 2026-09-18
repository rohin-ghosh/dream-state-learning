import json
from copy import deepcopy
from types import SimpleNamespace

import pytest

from gpu import orch_r125_code_checker_recovery as recovery
from organism_v6 import orch_r108_code_parent_r115 as environment


def test_syntax_failure_is_visible_not_process_terminal():
    bound = recovery.checker_environment(environment)
    task = dict(reference_expression='sum(values)', tests=[dict(arguments=dict(values=[1, 2]), expected=3)])
    raw = json.dumps(dict(expression='[x ifx > 2 else 0 for x in values]'))
    with pytest.raises(SyntaxError):
        environment.visible_checker(task, raw)
    assert bound.visible_checker(task, raw) == dict(status='INVALID_EXPRESSION', child_received=True, error_type='SyntaxError')
    assert bound.score(task, raw) == dict(correct=False, format_valid=True, passed=0, total=1)
    inspected = bound.inspect_environment(json.dumps(dict(inspect=dict(expression='1 +', values=[1]))))
    assert inspected['status'] == 'REJECTED' and inspected['reason'] == 'SyntaxError'
    assert inspected['arbitrary_python_executed'] is False


def test_valid_and_unsafe_expressions_preserve_existing_semantics():
    bound = recovery.checker_environment(environment)
    task = dict(reference_expression='sum(values)', tests=[dict(arguments=dict(values=[1, 2]), expected=3)])
    for expression in ('sum(values)', '__import__("os")', 'values[99]'):
        raw = json.dumps(dict(expression=expression))
        assert bound.score(task, raw) == environment.score(task, raw)
        assert bound.visible_checker(task, raw) == environment.visible_checker(task, raw)


def test_unrelated_implementation_failure_is_not_swallowed():
    def broken(*args):
        raise RuntimeError('implementation bug')
    original = SimpleNamespace(**dict(vars(environment), visible_checker=broken))
    with pytest.raises(RuntimeError):
        recovery.checker_environment(original).visible_checker({}, '')


@pytest.fixture
def saved(tmp_path):
    messages = [dict(role='system', content='CODE'), dict(role='user', content='fixed TRAIN problem')]
    parent = dict(kind='PARENT', status='COMPLETE', split='TRAIN', guidance='Check your evidence.')
    recovery.io.write(tmp_path / 'reservations/C043_META_PARENT.json', parent)
    actual = messages + [dict(role='user', content='Parent guidance received since your previous turn:\n' + parent['guidance'])]
    row = dict(id=recovery.IDENTIFIER, status='COMPLETE', kind='NATIVE', split='TRAIN', cycle=44,
        phase='episode', evaluation_origin=None, requested_generation_cap=4096,
        injected_parent_ids=['C043_META_PARENT'], response=dict(messages=actual, raw='native only', token_ids=[1, 2]),
        model_binding=dict(checkpoint='same'))
    path = tmp_path / 'reservations' / (recovery.IDENTIFIER + '.json')
    recovery.io.write(path, row)
    return tmp_path, recovery.io.ref(path), messages, row


def test_saved_response_restore_never_dispatches_or_rewrites(saved, monkeypatch):
    root, reference, messages, row = saved
    driver = object.__new__(recovery.Driver)
    driver.root, driver.service = root, root / 'new_service'
    driver.recovery, driver.restored = dict(reference=reference), False
    driver.model_binding = dict(checkpoint='same')
    def forbidden(*args, **kwargs):
        raise AssertionError('no dispatch for already COMPLETE original')
    monkeypatch.setattr(recovery.previous.Driver, 'capture', forbidden)
    assert driver.capture(recovery.IDENTIFIER, dict(split='TRAIN'), 'episode', 44, messages, 4096) == row
    assert recovery.io.ref(reference['path']) == reference
    with pytest.raises(ValueError, match='one_logged_response_restore_only'):
        driver.capture(recovery.IDENTIFIER, dict(split='TRAIN'), 'episode', 44, messages, 4096)


@pytest.mark.parametrize('change', ('prompt', 'cap', 'split', 'raw'))
def test_recovery_rejects_changed_call_or_input(saved, change):
    root, reference, messages, row = saved
    messages = deepcopy(messages)
    if change == 'prompt':
        messages[-1]['content'] += ' changed'
    if change == 'raw':
        recovery.run.write(reference['path'], dict(row, status='FAILED'))
    with pytest.raises(ValueError):
        recovery.saved_call(root, reference, dict(split='DEV' if change == 'split' else 'TRAIN'),
            messages, 2048 if change == 'cap' else 4096)


def test_fresh_calls_keep_existing_nonblocking_driver(saved, monkeypatch):
    root, reference, messages, row = saved
    marker = object()
    monkeypatch.setattr(recovery.previous.Driver, 'capture', lambda *args, **kwargs: marker)
    driver = object.__new__(recovery.Driver)
    assert driver.capture('C044_E0_REFLECTION', dict(split='TRAIN'), 'reflection', 44, messages, 4096) is marker


def test_prepare_fails_before_writing_on_foreign_branch(tmp_path):
    prior = tmp_path / 'old/service'
    recovery.io.write(prior / 'INDEPENDENT.json', dict(branch='A3', root=str(tmp_path)))
    with pytest.raises(ValueError, match='F3_only_same_root'):
        recovery.prepare(prior, tmp_path / 'new/service')
    assert not (tmp_path / 'new').exists()
