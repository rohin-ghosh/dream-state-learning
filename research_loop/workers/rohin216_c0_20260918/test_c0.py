import importlib.util
from pathlib import Path
from unittest.mock import patch

import pytest


def load_parent():
    path = Path(__file__).resolve().parents[1] / 'gpu/r216_c0_parent.py'
    spec = importlib.util.spec_from_file_location('c0_parent', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_c0_new_identity_and_quitting_point():
    parent = load_parent()
    assert 'name is C0' in parent.prompt(0)
    assert 'not the continuing original C2' in parent.prompt(0)
    assert 'second turn' in parent.prompt(1)
    assert parent.PROBLEMS[0] in parent.prompt(1)
    assert parent.PROBLEMS[1] in parent.prompt(2)
    assert 'no code executor is connected' in parent.prompt(2)


def test_parent_never_claims_child_completion_or_gives_old_answer():
    parent = load_parent()
    for turn in range(12):
        text = parent.prompt(turn)
        assert 'V = 3' not in text
        assert 'You completed' not in text
        assert text.isascii()


def test_privileged_admission_is_reused_only_fresh_and_bound():
    from gpu import r216_c0_runtime as runtime
    report = dict(scanner_euid=0, clear=True, blocking_reasons=[])
    admission = dict(report=report, guard_sha256='a' * 64, verified_unix=100)
    with patch('gpu.orch_r125_continual_guard.validate', return_value=({'attempt_dir': '/tmp/C0'}, {})), \
            patch.object(runtime.runtime.native, 'read', return_value=admission), \
            patch.object(runtime.runtime.native, 'sha', return_value='a' * 64), \
            patch.object(runtime.time, 'time', return_value=110):
        assert runtime.preadmitted_report(Path('/tmp/C0/config')) == report
        admission['verified_unix'] = -100
        with pytest.raises(ValueError, match='fresh_source_bound'):
            runtime.preadmitted_report(Path('/tmp/C0/config'))
        admission['verified_unix'] = 100
        admission['guard_sha256'] = 'b' * 64
        with pytest.raises(ValueError, match='fresh_source_bound'):
            runtime.preadmitted_report(Path('/tmp/C0/config'))
        admission['guard_sha256'] = 'a' * 64
        admission['report']['clear'] = False
        with pytest.raises(ValueError, match='actual_privileged_clear'):
            runtime.preadmitted_report(Path('/tmp/C0/config'))


def test_service_budget_matches_bound_plan_not_legacy_two_hour_cap():
    from gpu import r216_c0_runtime as runtime
    command = ['--property=RuntimeMaxSec=7200', '--property=NoNewPrivileges=yes']
    with patch.object(runtime, 'ORIGINAL_CONTAINED_COMMAND', return_value=command), \
            patch('gpu.orch_r125_continual_guard.validate', return_value=({},
                dict(hard_end_unix=10900, lease_end_unix=22000))), \
            patch.object(runtime.time, 'time', return_value=100):
        assert runtime.contained_command(Path('/tmp/C0/config'), 'child') == [
            '--property=RuntimeMaxSec=10785', '--property=NoNewPrivileges=yes']
