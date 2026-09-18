"""No-LoRA BASE is neither initial37ec nor a fresh trained adapter."""

from types import SimpleNamespace
import pytest
from organism_v6 import orch_combined_l1_base as base


def test_reused_native_engine_selects_actual_no_adapter_branch():
    options = base.options('/frozen', 'GPU-TEST')
    assert options.phase == 'readout' and options.adapter_dir is None
    assert options.expected_base_sha256 == base.BASE_SHA


def test_no_learning_and_no_peft_allowed():
    assert base.verify_no_adapter([('weight', SimpleNamespace(requires_grad=False))]) == 1
    with pytest.raises(AssertionError):
        base.verify_no_adapter([('lora_A.weight', SimpleNamespace(requires_grad=False))])
    with pytest.raises(AssertionError):
        base.verify_no_adapter([('weight', SimpleNamespace(requires_grad=True))])
    with pytest.raises(AssertionError):
        base.verify_no_adapter([('weight', SimpleNamespace(requires_grad=False))], {})


def test_cap_is_separate_addition_not_old_counter_rewrite():
    plan = dict(schema='COMBINED_L1_NO_LORA_BASE_DEFAULT_V1', base_sha256=base.BASE_SHA,
        adapter=None, training_updates=0, parent_access=False, old_ledger_cap=1760,
        additional_base_calls=64, new_total_cap=1824, max_new_tokens=1536, no_held_compilation=True)
    assert base.validate(plan) is plan
    with pytest.raises(AssertionError):
        base.validate(dict(plan, adapter='37ec'))
    with pytest.raises(AssertionError):
        base.validate(dict(plan, old_ledger_cap=1824))
