from pathlib import Path
from types import SimpleNamespace

import pytest

from gpu import orch_r119_code_runtime as runtime
from gpu import orch_r118_code_parallel_loop as original


def test_bootstrap_targets_new_wrapper_not_old_clock():
    config = dict(source_root='/old_source', wrapper_directory='/new_wrapper/gpu', interpreter='/python')
    args = runtime.command_from_runtime('/life/continuation/service', 'guard', config)
    assert args[:3] == ['/python', '-B', '-c']
    assert runtime.MODULE in args[-1] and '/new_wrapper/gpu' in args[-1]
    assert 'orch_r118_code_parallel_loop' not in args[-1]


def test_lifecycle_preserves_two_episode_pending_and_actual_shared_sleep():
    namespace = runtime.lifecycle_functions(original)
    for name in ('resume_pending', 'finish_committed_cycle', 'run_cycles', 'settle_readout'):
        assert namespace[name].__code__ is getattr(original, name).__code__
    assert namespace['settle_readout'].__kwdefaults__['launch'] is runtime.schedule_dev
    assert namespace['resume_pending'].__kwdefaults__['finish'] is namespace['finish_committed_cycle']
    assert namespace['run_cycles'].__globals__['finish_committed_cycle'] is namespace['finish_committed_cycle']


def test_completed_FINAL_not_scheduled(tmp_path):
    with pytest.raises(ValueError, match='completed_FINAL_never_rescheduled'):
        runtime.schedule_dev(tmp_path, None, 22, 'FINAL')
    assert not list(tmp_path.iterdir())


def test_native_never_constructs_independent_optimizer():
    import inspect
    text = inspect.getsource(runtime.native)
    assert 'local_optimizer=None' in text
    assert 'session.load_engine(effective, check)' in text
    assert "lifecycle['resume_pending']" in text
    assert 'AdamW' not in text


def test_readout_launch_has_binding_and_service_not_final_loop():
    config = dict(source_root='/old_source', wrapper_directory='/new_wrapper/gpu', interpreter='/python')
    args = runtime.command_from_runtime('/life/continuation/service', 'readout', config, '/life/shared/DEV.json')
    assert '--binding' in args[-1] and 'DEV.json' in args[-1]
    assert '--service' in args[-1]
