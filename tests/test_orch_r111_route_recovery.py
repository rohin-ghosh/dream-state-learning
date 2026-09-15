import inspect
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from gpu import orch_r111_route_recovery as recovery


def test_exact_native_transform_preserves_reservation_function():
    native = recovery.native_function()
    assert native.__globals__['reserve'] is recovery.old.reserve
    assert native.__globals__['native_engine'].sleep is recovery.sleep
    assert native.__globals__['verify'] is recovery.verify


def test_transform_rejects_ambiguous_or_changed_bytes():
    for source in ('missing', 'twice twice'):
        with pytest.raises(ValueError):
            recovery.replace_once(source, 'twice', 'new')


def test_restore_preserves_all_charged_counters_and_memory():
    counters = {'native_completed': 0}
    state = {'memory': ''}
    recovered = dict(counters={'native_completed': 41, 'parent_completed': 4,
                              'sleeps': 1, 'optimizer_updates': 48},
                     own_memory='actual prior reflection', old_rows=[{'prior': True}])
    with patch.object(recovery, 'verify', return_value=recovered):
        recovery.state(Path('/owned'), 'a100_3', counters, state)
    assert counters['native_completed'] == 41
    assert counters['optimizer_updates'] == 48
    assert counters['parent_missing'] == 0
    assert state['memory'] == recovered['own_memory']
    assert state['old_rows'] == recovered['old_rows']


def test_broker_source_checks_use_frozen_root_not_transport_checkout():
    text = inspect.getsource(recovery.broker)
    assert "source.replace('repository/relative', 'frozen_repository/relative')" in text
    assert "Path(__file__).resolve().parents[1]" in text
    assert "namespace['serve'](repository, root, lane, buffer, receipts)" in text


def test_new_recovery_never_overwrites_original_campaign():
    root = Path('/owned/root')
    assert recovery.directory(root, 'a100_3') == root/'recovery_r113_v1/campaign_a100_3'
    text = inspect.getsource(recovery.prepare)
    assert 'exist_ok=False' in text
    assert 'original_partial_cycle_preserved_not_regenerated=True' in text
    assert "max(row.get('cycle', 0) for row in reservations)+1" in text
