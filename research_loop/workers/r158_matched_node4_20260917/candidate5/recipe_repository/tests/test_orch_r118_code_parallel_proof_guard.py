from pathlib import Path
from types import CodeType
import dis
import os

import pytest

from gpu import orch_r118_code_parallel_proof_guard as wrapper


def binding_path():
    return Path(os.environ.get('MATH_BINDING_SOURCE', str(Path(__file__).resolve().parents[1] /
        'gpu/orch_math_feedback_uptake_r118_preinfer.py')))


def test_reuses_exact_existing_binding_function_not_foreign_lifecycle(monkeypatch):
    path = binding_path()
    bound = wrapper.bind_function(path, wrapper.io.sha(path))
    compiled = compile(path.read_text(), str(path), 'exec')
    original = next(item for item in compiled.co_consts if isinstance(item, CodeType) and item.co_name == 'bind_scan')
    assert [(entry.opname, entry.argval) for entry in dis.get_instructions(bound)] == [
        (entry.opname, entry.argval) for entry in dis.get_instructions(original)]
    assert bound.__code__.co_names == original.co_names
    assert bound.__globals__['transient'] is wrapper.transient
    assert 'life' not in bound.__globals__ and 'native' not in bound.__globals__


def test_binding_source_change_rejected_before_compilation():
    with pytest.raises(ValueError, match='existing_Math'):
        wrapper.bind_function(binding_path(), '0' * 64)


def test_original_native_engine_and_safety_predicate_not_replaced():
    assert wrapper.core.MODULE == 'gpu.orch_r118_code_parallel_loop'
    assert wrapper.recording.handoff.previous.admitted is wrapper.handoff.previous.admitted


def test_privileged_same_process_required(monkeypatch):
    monkeypatch.setattr(wrapper.os, 'geteuid', lambda: 1000)
    with pytest.raises(ValueError, match='same_process'):
        wrapper.scan('/unused')


def test_both_failed_sessions_prohibited():
    assert len(wrapper.FAILED_SESSIONS) == 2
    assert '2987f2cba47868934fd6d465f0001c94e7d754d3b7972bb56c328ed6f081e641' in wrapper.FAILED_SESSIONS
