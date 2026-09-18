from copy import deepcopy

import pytest

from gpu import orch_r119_code_continuation as continuation


def test_plan_changes_only_explicit_wall_preserves_caps_and_identity():
    original = dict(hard_deadline_unix=100, lease_end_unix=100000, native_cap=8192,
        parent_cap=1000, started_unix=1, cycles=100, model_dir='frozen_base', gpu_uuid='fixed')
    before = deepcopy(original)
    actual = continuation.effective_plan(original, dict(train_end_unix=70000, hard_end_unix=70120))
    assert original == before
    assert actual == dict(original, hard_deadline_unix=70120)


@pytest.mark.parametrize('policy', [dict(train_end_unix=80000, hard_end_unix=80120),
    dict(train_end_unix=70000, hard_end_unix=70001), dict(train_end_unix=71000, hard_end_unix=70000)])
def test_plan_rejects_lease_violation_or_personal_reserve(policy):
    with pytest.raises(ValueError):
        continuation.effective_plan(dict(lease_end_unix=100000), policy)


def test_broker_change_preserves_provider_quotas_and_queue():
    original = dict(deadline_unix=100, model='same_parent', max_calls=1000, remote_root='same_queue')
    before = deepcopy(original)
    result = continuation.broker_config(original, dict(train_end_unix=900, hard_end_unix=1020))
    assert result == dict(original, deadline_unix=900)
    assert original == before


def test_reference_changes_rejected_and_output_immutable(tmp_path):
    path = tmp_path / 'receipt.json'
    continuation.write(path, {'pending_cycle':22})
    reference = continuation.ref(path)
    assert continuation.checked(reference) == {'pending_cycle':22}
    with pytest.raises(FileExistsError):
        continuation.write(path, {})
    path.write_text('{}')
    with pytest.raises(ValueError, match='exact_immutable_reference'):
        continuation.checked(reference)
