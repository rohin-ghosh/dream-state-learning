from types import SimpleNamespace

import pytest

from gpu import orch_r118_node3_6_grid_recover as recovery
from gpu import orch_r118_node3_6_grid_recover_broker as broker


def engine():
    events = []
    model = SimpleNamespace(to=lambda device: events.append(device))
    value = SimpleNamespace(model=model, verify_base=lambda: events.append('verify'),
        torch=SimpleNamespace(cuda=SimpleNamespace(empty_cache=lambda: events.append('empty'))))
    return value, events


def test_same_model_offloaded_before_fresh_readout_then_restored():
    value, events = engine()
    original = value.model

    def readout():
        assert events == ['verify', 'cpu', 'collect', 'empty']
        events.append('fresh_readout')

    recovery.offloaded_readout(value, readout, collect=lambda: events.append('collect'))
    assert events == ['verify', 'cpu', 'collect', 'empty', 'fresh_readout', 'cuda:0', 'verify']
    assert value.model is original


def test_failed_readout_preserved_not_retried():
    value, events = engine()

    def fail():
        events.append('failed_once')
        raise RuntimeError('original failure')

    with pytest.raises(RuntimeError, match='original failure'):
        recovery.offloaded_readout(value, fail, collect=lambda: None)
    assert events.count('failed_once') == 1 and events[-2:] == ['cuda:0', 'verify']


def test_only_node3_6_and_original_caps():
    assert recovery.previous.UUID == 'GPU-1a83d900-1e95-c7b4-9b12-8117399697f8'
    assert recovery.grid.MAX_NATIVE == 1858 and recovery.grid.MAX_PARENT == 298
    assert recovery.grid.END == 1789491720 and recovery.grid.TRAIN_END == 1789491300
    with pytest.raises(ValueError):
        recovery.previous.allocation(5)


def test_no_parent_redispatch_before_recovery():
    assert all(broker.historical(f'P{number:04d}.request.json') for number in range(1, 41))
    assert not broker.historical('P0041.request.json')


def test_new_terminal_only_old_failure_never_suppressed():
    original = "if store.exists(root / 'TERMINAL.json'):\n    break\n"
    changed = broker.terminal_source(original)
    assert broker.TERMINAL in changed
    with pytest.raises(ValueError):
        broker.terminal_source(original + original)


def test_readout_attached_TRAIN_is_not_training_capture_or_replay():
    item = dict(kind='NATIVE', split='TRAIN', attached_readout=True)
    assert not recovery.train_charge(item)
    assert recovery.train_charge(dict(item, attached_readout=False))
    assert not recovery.train_charge(dict(item, split='FINAL', attached_readout=False))
