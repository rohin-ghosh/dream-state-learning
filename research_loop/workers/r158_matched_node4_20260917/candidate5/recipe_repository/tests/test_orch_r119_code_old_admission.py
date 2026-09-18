import inspect
import pytest

from gpu import orch_r119_code_old_admission as admission


def test_actual_existing_math_kernel_proof_binds_without_importing_lifecycle():
    bound = admission.bind_proof()
    assert bound.__code__.co_name == 'bind_scan'
    assert bound.__globals__['transient'] is admission.transient
    assert 'gpu.orch_math_feedback_uptake_r118_preinfer' not in bound.__globals__


def test_proof_rejects_nonprivileged_execution(monkeypatch):
    monkeypatch.setattr(admission.os, 'geteuid', lambda: 2524)
    with pytest.raises(ValueError, match='fresh_same_process_root_scan_required'):
        admission.bind_proof()(lambda: pytest.fail('no unprivileged scan'))


def test_exact_target_original_argv_and_exit_checks_preserved():
    source = inspect.getsource(admission.scan)
    assert "index == plan['physical']" in source
    assert 'argv_admission.scan' in source
    assert 'bind_proof()' in source
    assert 'blocking_reasons' not in source
    assert 'True' not in source
