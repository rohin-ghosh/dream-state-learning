import inspect
import json
from pathlib import Path

import pytest

from gpu import orch_r119_code_independent as independent


@pytest.fixture
def driver(tmp_path, monkeypatch):
    for name in ('reservations', 'parent_queue', 'cycles'):
        (tmp_path / name).mkdir()
    plan = dict(life_id='synthetic_CODE_fork', native_cap=100, parent_cap=50, hard_deadline_unix=9999999999)
    (tmp_path / 'PLAN.json').write_text(json.dumps(plan))
    document = dict(service=str(tmp_path / 'service'), train_end_unix=9999999999,
        hard_end_unix=9999999999, allowed_parent_models=['test-parent'])
    pointers = dict(carry=dict(reflection_settings=dict(effective_max_new_tokens=3072)),
        checkpoint=dict(path='actual_gen1', path_sha256='frozen'), generation=1)
    monkeypatch.setattr(independent.run, 'check', lambda root, phase: plan)
    actual = independent.Driver(tmp_path, object(), document, pointers)
    monkeypatch.setattr(independent.run.adapter, 'request', lambda task, events, **kw:
        dict(id=kw['identifier'], payload=dict(events=events), lane_deadline_unix=kw['lane_deadline_unix']))
    return actual


def test_parent_returns_immediately_and_preserves_pending(driver, monkeypatch):
    def forbidden_sleep(seconds):
        raise AssertionError('parent must not wait')
    monkeypatch.setattr(independent.time, 'sleep', forbidden_sleep)
    guidance = driver.parent('C023_PARENT', dict(split='TRAIN'), [], 23, 0, 'experience')
    assert guidance == '' and list(driver.pending) == ['C023_PARENT']
    record = independent.run.read(driver.root / 'reservations/C023_PARENT.json')
    assert record['status'] == 'PENDING' and record['wait_seconds'] == 0
    assert driver.settings['effective_max_new_tokens'] == 3072


def test_pending_timeout_is_operational_missing_without_new_request(driver):
    driver.parent('C023_PARENT', dict(split='TRAIN'), [], 23, 0, 'experience')
    entry = driver.pending['C023_PARENT']
    driver.poll_parent(now=entry['deadline'] + 1)
    record = independent.run.read(entry['path'])
    assert record['status'] == 'MISSING' and record['no_retry'] is True
    assert not driver.pending and len(list((driver.root / 'parent_queue').iterdir())) == 1


def test_diagnostics_never_submit_parent(driver):
    for split in ('DEV', 'FINAL'):
        with pytest.raises(ValueError, match='TRAIN_only_async_parent'):
            driver.parent('not-issued', dict(split=split), [], 23, 0, 'experience')
    assert not list((driver.root / 'reservations').iterdir())


def test_next_train_boundary_injects_but_DEV_cannot_consume(driver, monkeypatch):
    driver.guidance = [('parent1', 'Notice which evidence changed your view.')]
    captured = []
    def capture(self, identifier, task, phase, cycle, messages, cap, **kwargs):
        captured.append(messages)
        return dict(status='COMPLETE', response=dict(raw='full reasoning', token_ids=[1]))
    monkeypatch.setattr(independent.run.Driver, 'capture', capture)
    dev = driver.capture('DEV1', dict(split='DEV'), 'readout', 23, [], 2048, evaluation_origin='DEV')
    assert dev['injected_parent_ids'] == [] and driver.guidance
    train = driver.capture('TRAIN1', dict(split='TRAIN'), 'reflection', 23, [], 3072)
    assert train['injected_parent_ids'] == ['parent1'] and not driver.guidance
    assert 'Notice which evidence' in captured[-1][-1]['content']


def test_original_PARENT_identifier_cannot_be_reissued(driver):
    driver.parent('already', dict(split='TRAIN'), [], 23, 0, 'experience')
    with pytest.raises(ValueError, match='no_call_retry'):
        driver.parent('already', dict(split='TRAIN'), [], 23, 0, 'experience')


def test_no_shared_campaign_barrier_optimizer_or_sleep_in_native():
    source = inspect.getsource(independent.native)
    for forbidden in ('finish_cycle(', 'resume_pending(', 'bootstrap(', '.sleep(', 'AdamW(', 'SESSION.json'):
        assert forbidden not in source
    loader = inspect.getsource(independent.load_engine)
    assert 'SimpleNamespace' in loader and 'Session.load_engine' in loader
    assert 'Session(' not in loader


def test_new_FINAL_key_and_time_before_tasks_are_read(monkeypatch):
    monkeypatch.setattr(independent.time, 'time', lambda: independent.FINAL_TIME - 1)
    with pytest.raises(ValueError, match='no_early_or_old_FINAL_replay'):
        independent.diagnostic(None, 1, 'FINAL', 'R119_FINAL_20260916_0600')
    assert independent.FINAL_TIME == 1789538400
