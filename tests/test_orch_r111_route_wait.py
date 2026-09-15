from copy import deepcopy
import json
from pathlib import Path

import pytest

from gpu import orch_r111_route_boundary as boundary
from gpu import orch_r111_route_wait as wait


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def test_actual_original_parent_function_uses_new_deadline_without_plan_change(tmp_path, monkeypatch):
    plan = dict(parent_wait_seconds=120, provider='claude-fable-5-1', bounds=dict(hard_end_unix=2000))
    before = deepcopy(plan)
    era = dict(parent_wait_seconds=600, handoff_request=dict(path=str(tmp_path / 'REQUEST.json')))
    era_path = tmp_path / 'ERA.json'
    put(era_path, era)
    monkeypatch.setattr(wait, 'verify_era', lambda *unused: era)
    monkeypatch.setattr(wait.original, 'reserve', lambda *unused: 1)
    monkeypatch.setattr(wait.original, 'public_payload', lambda *unused: dict(text='actual child'))
    monkeypatch.setattr(wait.original.time, 'time', lambda: 1000)
    captures = []

    def write(path, value):
        captures.append((path.name, value))
        put(path, value)
        if path.name.endswith('.request.json'):
            put(path.with_name(path.name.replace('.request.json', '.response.json')), dict(status='MISSING'))

    monkeypatch.setattr(wait.original, 'write', write)
    function = wait.runtime(tmp_path, era_path)
    result = function.__globals__['parent_call'](tmp_path, plan, {}, 4, 0, 'experience', [], 'hash')
    request = next(value for name, value in captures if name.endswith('.request.json'))
    assert request['lane_deadline_unix'] == 1600
    assert set(request) == {'id', 'payload', 'payload_sha256', 'lane_deadline_unix'}
    assert result['status'] == 'MISSING'
    assert plan == before
    assert len([name for name, unused in captures if name.endswith('.request.json')]) == 1


def test_deadline_clipped_to_original_lifetime(tmp_path, monkeypatch):
    plan = dict(parent_wait_seconds=120, provider='claude-fable-5-1', bounds=dict(hard_end_unix=1050))
    era = dict(parent_wait_seconds=600)
    era_path = tmp_path / 'ERA.json'
    put(era_path, era)
    monkeypatch.setattr(wait, 'verify_era', lambda *unused: era)
    monkeypatch.setattr(wait.original, 'reserve', lambda *unused: 1)
    monkeypatch.setattr(wait.original, 'public_payload', lambda *unused: {})
    monkeypatch.setattr(wait.original.time, 'time', lambda: 1000)
    requests = []

    def write(path, value):
        put(path, value)
        if path.name.endswith('.request.json'):
            requests.append(value)
            put(path.with_name(path.name.replace('.request.json', '.response.json')), dict(status='MISSING'))

    monkeypatch.setattr(wait.original, 'write', write)
    wait.runtime(tmp_path, era_path).__globals__['parent_call'](tmp_path, plan, {}, 4, 0, 'experience', [], 'hash')
    assert requests[0]['lane_deadline_unix'] == 1050


def test_native_capture_era_is_bound_before_generation(tmp_path, monkeypatch):
    era_path = tmp_path / 'ERA.json'
    put(era_path, dict(parent_wait_seconds=600))
    monkeypatch.setattr(wait, 'verify_era', lambda *unused: dict(parent_wait_seconds=600))
    generated = wait.runtime(tmp_path, era_path)
    assert generated.__globals__['transport_era'] == boundary.reference(era_path)
    assert generated.__code__.co_filename.endswith(':prospective_run')
    assert wait.original.run.__code__.co_filename != generated.__code__.co_filename


def test_empty_successor_resumes_same_task_cursor_and_preserves_START(tmp_path):
    current = tmp_path / 'cycle_0004'
    put(current / 'START.json', dict(cycle=4))
    before = (current / 'START.json').read_bytes()
    handoff = tmp_path / 'handoff'
    put(handoff / 'BOUNDARY.json', dict(empty_successor_start=boundary.reference(current / 'START.json')))
    era = dict(handoff_request=dict(path=str(handoff / 'REQUEST.json')))
    assert wait.resumed_cycle(tmp_path, [current / 'START.json'], era) == 4
    wait.prepare_cycle(current, era)
    wait.cycle_write(current / 'START.json', dict(cycle=4, resumed=True))
    assert (current / 'START.json').read_bytes() == before
    assert len(list(current.glob('RESUMED_START_*.json'))) == 1


def test_nonempty_successor_cannot_be_replayed(tmp_path):
    current = tmp_path / 'cycle_0004'
    put(current / 'START.json', dict(cycle=4))
    handoff = tmp_path / 'handoff'
    put(handoff / 'BOUNDARY.json', dict(empty_successor_start=boundary.reference(current / 'START.json')))
    put(current / 'CALL_001.json', dict(raw='preserve'))
    era = dict(handoff_request=dict(path=str(handoff / 'REQUEST.json')))
    assert wait.resumed_cycle(tmp_path, [current / 'START.json'], era) == 5
    with pytest.raises(ValueError, match='only_verified_empty'):
        wait.prepare_cycle(current, era)


def test_new_stop_marker_not_applied_to_original_live_source(tmp_path):
    assert 'STOP_AFTER_CYCLE' not in wait.original.run.__code__.co_consts
    assert wait.cooperative_boundary(tmp_path, 4, tmp_path / 'ERA.json') is False


def test_shared_stop_requires_all_eight_ready(tmp_path):
    era = tmp_path / 'ERA.json'
    put(era, {})
    put(tmp_path / 'STOP_AFTER_CYCLE.json', dict(era_sha256=boundary.sha(era), stop=True,
        purpose='SHARED_ADOPTION', all_eight_ready=False, common_handoff_coordinated=False))
    with pytest.raises(ValueError, match='shared_handoff_coordinated'):
        wait.cooperative_boundary(tmp_path, 4, era)
    assert not (tmp_path / 'WAIT600_CYCLE_STOPPED.json').exists()
