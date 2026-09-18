import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


HERE = Path(__file__).resolve().parent


@pytest.fixture
def ready():
    specification = importlib.util.spec_from_file_location('ready_under_test', HERE / 'LIFECYCLE_READY.py')
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def fixture_adapter(ready, *, changed=False, ticks=None, remaining=1200, cycle=None):
    processes = dict(actor=dict(pid=ready.EXPECTED_PID,
        start_ticks=ready.EXPECTED_TICKS if ticks is None else ticks),
        timer=dict(pid=12), supervisor=dict(pid=13))
    calls = []

    def owners(*arguments):
        calls.append(arguments)
        if changed and len(calls) > 1:
            return dict(processes, timer=dict(pid=14))
        return processes

    helper = SimpleNamespace(sha=lambda path: 'guard_sha')
    saved = SimpleNamespace(sleep_boundary=lambda root: None if cycle is None else dict(cycle=cycle))
    family = dict(api=lambda: helper,
        old_modules=lambda path: ({}, dict(root='/fixture/life', source_root='/fixture/source',
                                          hard_end_unix=1000 + remaining), SimpleNamespace(saved=saved)),
        old_processes=owners)
    return dict(family_namespace=lambda: family, OLD_GUARD=Path('/fixture/GUARD.json')), calls


def test_inventory_preserves_owner_and_reports_no_authority(ready):
    adapter, calls = fixture_adapter(ready)
    result = ready.observe(adapter, 1000)
    assert len(calls) == 2
    assert result['lanes'][0]['processes']['actor']['pid'] == ready.EXPECTED_PID
    assert result['head_completed_cycle'] is None
    assert result['signals_sent'] == result['model_calls'] == 0
    assert result['selection_created'] is result['main_go_created'] is False
    assert result['saved_state_handoff_authorized'] is False


@pytest.mark.parametrize('arguments,reason', [
    ({'changed': True}, 'stable_original_topology'),
    ({'ticks': 'replacement'}, 'exact_original_instance'),
    ({'remaining': 900}, 'original_wall_margin'),
])
def test_owner_and_wall_mismatch_fail_before_any_receipt(ready, arguments, reason):
    adapter, unused_calls = fixture_adapter(ready, **arguments)
    with pytest.raises(ValueError, match=reason):
        ready.observe(adapter, 1000)


def test_completed_head_is_observation_not_selection(ready):
    adapter, unused_calls = fixture_adapter(ready, cycle=43)
    result = ready.observe(adapter, 1000)
    assert result['head_completed_cycle'] == 43
    assert not result['selection_created']


def test_original_validation_failure_propagates(ready):
    adapter, unused_calls = fixture_adapter(ready)
    family = adapter['family_namespace']()

    def failed(path):
        raise ValueError('original_full_source_pin_failure')

    family['old_modules'] = failed
    with pytest.raises(ValueError, match='original_full_source_pin_failure'):
        ready.observe(adapter, 1000)


def test_loading_from_other_directory_refuses(ready):
    with pytest.raises(ValueError, match='exact_bootstrap_location'):
        ready.load_operator()


def test_dependency_pin_and_symlink_refuse(ready, tmp_path):
    original = tmp_path / 'source.py'
    original.write_bytes(b'bounded source')
    with pytest.raises(ValueError, match='pinned_dependency'):
        ready.checked_bytes(original, '0' * 64)
    link = tmp_path / 'link.py'
    link.symlink_to(original)
    with pytest.raises(ValueError, match='canonical_dependency'):
        ready.checked_bytes(link, '0' * 64)
