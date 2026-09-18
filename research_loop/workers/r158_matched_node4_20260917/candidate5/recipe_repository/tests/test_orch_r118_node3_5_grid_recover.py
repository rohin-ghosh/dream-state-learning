import json
from types import SimpleNamespace

import pytest

from gpu import orch_r118_node3_5_grid_recover as recovery
from gpu import orch_r118_node3_5_grid_broker as broker


def test_original_node3_budget_source_and_device():
    assert recovery.UUID == 'GPU-bc211959-642d-664b-3581-42a0dbe434e9'
    assert recovery.READY_SHA.startswith('1041b72f')
    assert recovery.ROOT == recovery.prior.ROOT
    assert recovery.TERMINAL != 'TERMINAL.json'
    assert 'node3' in recovery.RECEIPTS


def test_replay_exact_segment_one_no_new_charge(tmp_path):
    rows = [dict(kind='NATIVE', number=10, cadence='segment', cycle=1, phase='train')]
    (tmp_path / 'LEDGER.jsonl').write_text(json.dumps(rows[0]) + '\n')
    (tmp_path / 'calls').mkdir()
    call = dict(status='COMPLETE', messages=['original'], response=dict(requested_generation_cap=384, raw='unchanged'))
    (tmp_path / 'calls/N00010.json').write_text(json.dumps(call))
    old = SimpleNamespace(spend=lambda *args: pytest.fail('new charge'), write=lambda *args: pytest.fail('write'))
    replay = recovery.DryReplay(tmp_path, old)
    assert replay.spend(tmp_path, 'NATIVE', dict(cadence='segment', cycle=1, phase='train')) == 10
    assert replay.generate(None, ['original'], max_new_tokens=384) == call['response']
    with pytest.raises(recovery.DryComplete):
        replay.spend(tmp_path, 'NATIVE', {})
    assert replay.initial_native == 1 and replay.initial_parent == 0
    assert replay.output == tmp_path / recovery.RECEIPTS


def test_recovery_terminal_redirect_only(monkeypatch, tmp_path):
    seen = []
    monkeypatch.setattr(broker.prior.old.Store, 'exists', lambda self, path: seen.append(path) or True)
    store = object.__new__(broker.AtomicStore)
    store.exists(recovery.ROOT / 'TERMINAL.json')
    store.exists(recovery.ROOT / 'parent_queue/P0046.response.json')
    assert seen == [recovery.ROOT / recovery.TERMINAL, recovery.ROOT / 'parent_queue/P0046.response.json']


def test_terminal_redirect_remains_nonrecursive_after_store_binding(monkeypatch):
    seen = []
    monkeypatch.setattr(broker.ORIGINAL_STORE, 'exists', lambda self, path: seen.append(path) or True)
    monkeypatch.setattr(broker.prior.old, 'Store', broker.AtomicStore)
    assert object.__new__(broker.AtomicStore).exists(recovery.ROOT / 'TERMINAL.json')
    assert seen == [recovery.ROOT / recovery.TERMINAL]
