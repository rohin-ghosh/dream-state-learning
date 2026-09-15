from pathlib import Path

import pytest

from gpu import orch_r118_f4_wait600 as wait


def test_only_future_F4_request_deadline_changes(monkeypatch):
    request = dict(id='P0021', payload={'unchanged': 'é'}, payload_sha256='a'*64, lane_deadline_unix=220)
    monkeypatch.setattr(wait.original.policy, 'queue_request', lambda *args: request)
    result = wait.queue_request('P0021', 'F4_FABLE', 6, 0, 'experience', {}, [], 'cohort', 100)
    assert result == dict(request, lane_deadline_unix=700)
    assert request['lane_deadline_unix'] == 220
    assert set(result) == {'id', 'payload', 'payload_sha256', 'lane_deadline_unix'}
    with pytest.raises(ValueError, match='F4_only'):
        wait.queue_request('P0021', 'F4_ASTRA', 6, 0, 'experience', {}, [], 'cohort', 100)


def test_original_hard_end_never_extended(monkeypatch):
    now = wait.original.END - 100
    monkeypatch.setattr(wait.original.policy, 'queue_request', lambda *args: dict(lane_deadline_unix=now+120))
    assert wait.queue_request('P0021', 'F4_FABLE', 6, 0, 'experience', {}, [], 'cohort', now)['lane_deadline_unix'] == wait.original.END - 5


def test_wait_uses_same_ask_and_reflection_generation():
    assert wait.WaitLife.ask.__code__ is wait.original.Life.ask.__code__
    assert wait.WaitLife.generate is wait.original.Life.generate
    assert wait.WaitLife.ask.__globals__['reflection_settings'] is wait.original.reflection_settings
    assert wait.WaitLife.ask.__globals__['policy'].queue_request is wait.queue_request
    assert wait.WaitLife.ask.__globals__['reserve'] is wait.original.reserve


def test_boundary_rejects_next_cycle_charge(monkeypatch, tmp_path):
    monkeypatch.setattr(wait, 'ROOT', tmp_path)
    complete = tmp_path/'cycles/0005/CYCLE_COMPLETE.json'
    complete.parent.mkdir(parents=True)
    wait.original.write(complete, dict(cycle=5, finished_unix=100))
    (tmp_path/'LEDGER.jsonl').write_text('{"cycle":6,"kind":"NATIVE","reserved_unix":101}\n')
    assert wait.boundary(tmp_path, complete) is None


def test_boundary_requires_published_claims_and_saved_carry(monkeypatch, tmp_path):
    monkeypatch.setattr(wait, 'ROOT', tmp_path)
    complete = tmp_path/'cycles/0005/CYCLE_COMPLETE.json'
    complete.parent.mkdir(parents=True)
    wait.original.write(complete, dict(cycle=5, finished_unix=100))
    (tmp_path/'LEDGER.jsonl').write_text('{"cycle":5,"kind":"PARENT","number":1,"reserved_unix":99}\n')
    assert wait.boundary(tmp_path, complete) is None
    wait.original.write(tmp_path/'parent_claude/P0001.claim/PUBLISHED.json', dict(status='MISSING'))
    with pytest.raises(ValueError, match='saved_context'):
        wait.boundary(tmp_path, complete)
    wait.original.write(tmp_path/'CARRY.json', [])
    checkpoint = wait.boundary(tmp_path, complete)
    assert checkpoint['next_cycle'] == 6 and checkpoint['parent_charged'] == 1
    assert checkpoint['old_calls_retried'] == 0
