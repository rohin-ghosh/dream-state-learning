import inspect
import json
from pathlib import Path

import pytest

from gpu import orch_r119_code_old_fork as fork
from gpu import orch_r108_code_parent_r109_run as run


def plan():
    return dict(wrapper='ovx2', physical=3, adapter={'path': 'frozen'},
        lease_end_unix=100000, hard_end_unix=78400, train_end_unix=78280,
        first_cycle=27, cycle_limit=100, ancestry={'first_cycle': 27},
        parent_ttl_seconds=600, parent_wait_seconds=0, parent_effort='low',
        parent_cadence='EPISODE', optimizer_updates=0)


def test_explicit_fork_preserves_partial_ancestor_charges():
    result = fork.ancestry([dict(cycle=25, kind='NATIVE'), dict(cycle=26, kind='PARENT')], 25, 1500, 500)
    assert result['first_cycle'] == 27 and result['native_used'] == result['parent_used'] == 1
    assert not result['replay_allowed'] and result['interrupted_original_preserved']


def test_allocation_and_lease_and_nonblocking_are_bound():
    assert fork.validate_plan(plan(), now=1)['physical'] == 3
    for patch in ({'physical': 2}, {'parent_wait_seconds': 600}, {'parent_effort': 'high'},
                  {'hard_end_unix': 99999}, {'optimizer_updates': 1}):
        with pytest.raises(ValueError):
            fork.validate_plan(dict(plan(), **patch), now=1)


def test_BASE_only_on_a40r():
    actual = dict(plan(), wrapper='a40r', physical=6, adapter=None)
    fork.validate_plan(actual, now=1)
    with pytest.raises(ValueError):
        fork.validate_plan(dict(actual, adapter={'path': 'not_BASE'}), now=1)


def test_original_cycle_binding_compiles_without_model_or_prior_lessons():
    bound = fork.cycles_function(run, {'own_context': 'actual saved reflection'}, 27)
    assert bound.__globals__['first_cycle'] == 27
    assert bound.__globals__['restored_memory'] == 'actual saved reflection'
    assert bound.__globals__['restored_lessons'] == []
    assert 'assert_no_adapter' not in bound.__code__.co_names


def test_meta_turn_never_schedules_provider(tmp_path):
    (tmp_path / 'PLAN.json').write_text('{}')
    result = fork.parent_call(tmp_path, 'node3_episode', {'slot': 0}, 1, [], '', [], lambda phase: None)
    assert result['status'] == 'NOT_SCHEDULED' and not result['provider_dispatched']
    assert not (tmp_path / 'parent_queue').exists()


def test_pending_missing_does_not_wait_or_retry(tmp_path, monkeypatch):
    monkeypatch.setattr(fork.time, 'sleep', lambda seconds: pytest.fail('must not wait'))
    path = tmp_path / 'parent.json'
    record = dict(deadline_unix=20, started_unix=1, status='PENDING')
    fork.PENDING[str(tmp_path)] = {'slot': dict(path=path, record=record, request={})}
    assert fork.poll_parents(tmp_path, {}, now=10) == []
    assert 'slot' in fork.PENDING[str(tmp_path)]
    assert fork.poll_parents(tmp_path, {}, now=21) == []
    assert json.loads(path.read_text())['status'] == 'MISSING'
    assert not fork.PENDING[str(tmp_path)]


def test_unverified_response_not_injected(tmp_path):
    (tmp_path / 'parent_queue').mkdir()
    (tmp_path / 'parent_queue/slot.response.json').write_text(json.dumps({'status': 'COMPLETE', 'id': 'slot'}))
    record = dict(deadline_unix=20, started_unix=1, status='PENDING')
    fork.PENDING[str(tmp_path)] = {'slot': dict(path=tmp_path / 'parent.json', record=record, request={})}
    assert fork.poll_parents(tmp_path, {'allowed_parent_models': ['verified']}, now=10) == []
    assert json.loads((tmp_path / 'parent.json').read_text())['status'] == 'MISSING'


def test_parent_free_readouts_do_not_consume_pending_and_no_optimizer():
    source = inspect.getsource(fork.configured)
    assert "if task['split'] == 'TRAIN' else []" in source
    assert 'actual_parent_triple=False' in source
    assert 'is_trainable=False' in inspect.getsource(fork.load_engine)
    assert 'while time.time()' not in inspect.getsource(fork.parent_call)


def test_only_fresh_rescan_for_identity_churn_never_waives_blocker():
    report = dict(clear=False, blocking_reasons=['minor_scan_identity_changed:3082', 'process_identity_drift:3082'])
    assert fork.fresh_scan_retryable(report)
    assert report['clear'] is False and len(report['blocking_reasons']) == 2
    for reason in ('open_device_pid:1', 'unknown_visibility:1', 'kernel_uuid_minor_changed'):
        assert not fork.fresh_scan_retryable(dict(blocking_reasons=[reason]))


def test_expiry_preserves_existing_pending_file(tmp_path):
    path = tmp_path / 'parent.json'
    record = dict(deadline_unix=20, started_unix=1, status='PENDING')
    path.write_text(json.dumps(record))
    fork.PENDING[str(tmp_path)] = {'slot': dict(path=path, record=record, request={})}
    assert fork.poll_parents(tmp_path, {}, now=21) == []
    assert json.loads(path.read_text())['status'] == 'MISSING'
