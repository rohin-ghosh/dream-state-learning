"""Separate zero-epoch frozen-base comparator, never an initial37ec adapter."""

from types import SimpleNamespace

BASE_SHA = 'a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992'


def options(model_dir, uuid):
    return SimpleNamespace(model_dir=model_dir, adapter_dir=None, phase='readout',
        device='cuda:0', gpu_uuid=uuid, expected_base_sha256=BASE_SHA)


def validate(plan):
    assert plan['schema'] == 'COMBINED_L1_NO_LORA_BASE_DEFAULT_V1'
    assert plan['base_sha256'] == BASE_SHA and plan['adapter'] is None
    assert plan['training_updates'] == 0 and plan['parent_access'] is False
    assert plan['old_ledger_cap'] == 1760 and plan['additional_base_calls'] == 64
    assert plan['new_total_cap'] == 1824 and plan['max_new_tokens'] == 1536
    assert plan['no_held_compilation'] is True
    return plan


def verify_no_adapter(named_parameters, peft_config=None):
    assert peft_config is None, 'peft_model_is_not_untrained_base'
    names = []
    for name, parameter in named_parameters:
        assert 'lora_' not in name.lower() and not parameter.requires_grad, 'no_lora_or_learning_allowed'
        names.append(name)
    assert names, 'nonempty_base_required'
    return len(names)
