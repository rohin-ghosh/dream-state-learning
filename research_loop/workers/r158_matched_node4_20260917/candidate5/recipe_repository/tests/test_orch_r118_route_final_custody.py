import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from gpu import orch_r111_route_final as final
from gpu import orch_r118_route_final_custody as custody


@pytest.mark.parametrize('name', ['ATTEMPT.json', 'DISPATCH.json', 'FAILED.json', 'COMPLETED.json',
    'NOT_RUN_BOUND.json', 'SKIPPED_ALREADY_COMPLETE.json', 'FINAL_INVENTORY_BINDING.json'])
def test_rejects_every_old_attempt_without_reading_or_removing(tmp_path, name):
    target = tmp_path / name
    target.write_text('preserved')
    with pytest.raises(ValueError):
        custody.unused(tmp_path)
    assert target.read_text() == 'preserved'


def test_charged_ledger_never_reset(tmp_path):
    ledger = tmp_path / 'RESERVATIONS.jsonl'
    ledger.write_text('{"native":1}\n')
    with pytest.raises(ValueError, match='unused_original'):
        custody.unused(tmp_path)
    assert ledger.read_text() == '{"native":1}\n'


def test_prior_capture_rejected_without_reading(tmp_path):
    (tmp_path / 'sealed_final_readouts').mkdir()
    with pytest.raises(ValueError):
        custody.unused(tmp_path)


def test_actual_frozen_wait_preserves_old_started_and_same_lock(tmp_path, monkeypatch):
    root = tmp_path / 'evaluation'
    root.mkdir()
    old = root / 'SCHEDULER_STARTED.json'
    old.write_text('original history')
    directory = tmp_path / 'custody'
    directory.mkdir()
    selection = tmp_path / 'selection'
    selection.touch()
    (tmp_path / 'COMPLETED.json').touch()
    config = dict(root=str(root), end_unix=final.END, selection_path=str(selection), cutoff={})
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', '')
    monkeypatch.setattr(custody, 'verify', lambda *_: dict(original_root=str(root)))
    monkeypatch.setattr(final, 'validate_config', lambda _: config)
    monkeypatch.setattr(final, 'bound', lambda _: dict(directory=str(tmp_path)))
    monkeypatch.setattr(final.time, 'time', lambda: final.START)
    calls = []
    monkeypatch.setattr(final, 'dispatch', lambda value: calls.append(value))
    custody.resume(dict(directory=str(directory), config={}, source={}, old_started={}), final)
    assert calls == [config]
    assert old.read_text() == 'original history'
    assert (root / 'SCHEDULER.lock').exists()
    assert json.loads((directory / 'STARTED.json').read_text())['proof']['original_root'] == str(root)


def test_live_old_identity_is_not_exited():
    import os
    fields = (Path('/proc') / str(os.getpid()) / 'stat').read_text().split(') ', 1)[1].split()
    assert not custody.exited(dict(pid=os.getpid(), start_ticks=fields[19]))


def test_metadata_hash_mismatch_rejected(tmp_path):
    path = tmp_path / 'metadata'
    path.write_text('{}')
    with pytest.raises(ValueError, match='immutable_reference'):
        custody.bound(dict(path=str(path), sha256='incorrect'))
