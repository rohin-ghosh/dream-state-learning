"""CPU-only fixed-budget provenance regression tests."""

import copy

import pytest

from research_loop.workers.r177_caption_game_stage1_20260917.data_judge import bt_budget as budget


def fixture():
    inventory = dict(root='/fixture/bt_qwen_v2', lease=dict(path='/fixture/lease', sha256='a'*64),
        allocation_end_unix=8200, lease_safe_end_unix=9000,
        files={'ranker.py': dict(sha256='b'*64), 'support/pytest.py': dict(sha256='c'*64)})
    config = dict(max_seconds=6600, calibration_reserve_seconds=1200)
    record = dict(schema='NY_R172_BT_EXPERIMENT_BUDGET_V1', machine_lease_extended=False,
        authority='Main/Astra Builder under user standing directives', root=inventory['root'], lease=inventory['lease'],
        device_uuid='GPU-35dcea35-12bc-f2f3-d5d2-d2eaa8bacdd8', start_unix=1000, deadline_unix=8200,
        max_gpu_seconds=6600, calibration_reserve_seconds=1200, source_sha256={'ranker.py': 'b'*64})
    return record, inventory, config


def test_fresh_budget_is_separate_from_retired_attempt():
    record, inventory, config = fixture()
    original = copy.deepcopy(inventory)
    budget.validate(record, inventory, config, 1100)
    assert inventory == original


@pytest.mark.parametrize('change', [dict(deadline_unix=8201), dict(start_unix=999),
    dict(start_unix=1200), dict(machine_lease_extended=True), dict(root='/old'),
    dict(authority='new human ratification'), dict(lease={}), dict(device_uuid='foreign'),
    dict(source_sha256={'ranker.py': 'd'*64}), dict(calibration_reserve_seconds=0),
    dict(max_gpu_seconds=7201), dict(start_unix=float('nan'))])
def test_budget_rejects_changed_authority_source_device_time_or_lease(change):
    record, inventory, config = fixture()
    with pytest.raises(ValueError):
        budget.validate(dict(record, **change), inventory, config, 1100)


def test_late_launch_and_machine_margin_rejected():
    record, inventory, config = fixture()
    with pytest.raises(ValueError):
        budget.validate(record, inventory, config, 1540)
    with pytest.raises(ValueError):
        budget.validate(record, dict(inventory, lease_safe_end_unix=8259), config, 1100)


def test_exact_new_runtime_and_calibration_budget():
    record, inventory, config = fixture()
    for changed in (dict(max_seconds=7200), dict(calibration_reserve_seconds=600)):
        with pytest.raises(ValueError):
            budget.validate(record, inventory, dict(config, **changed), 1100)


def test_v2_receiving_keeps_objective_and_exact_new_wall():
    from research_loop.workers.r177_caption_game_stage1_20260917.data_judge import bt_receiving_v2 as receiving
    from research_loop.workers.r177_caption_game_stage1_20260917.data_judge import bt_ranker as ranker
    config = dict(schema='NY_R171_BT_TRAIN_CONFIG_V1', objective='BRADLEY_TERRY_WEIGHTED_LOGISTIC',
        label_policy=ranker.LABEL_POLICY, pair_policy=ranker.PAIR_POLICY, reliability_policy=ranker.RELIABILITY_POLICY,
        max_updates=1000, batch_pairs=2, gradient_accumulation=4, max_seconds=6600, calibration_reserve_seconds=1200,
        max_length=512, heldout_per_contest=64, learning_rate=0.0001, humor_soft_CE_used=False,
        image_judge_training=False, development_reuse_provisional=True)
    receiving.validate_config(config)
    for change in (dict(max_seconds=7200), dict(calibration_reserve_seconds=600),
            dict(objective='MSE'), dict(humor_soft_CE_used=True), dict(image_judge_training=True)):
        with pytest.raises(ValueError):
            receiving.validate_config(dict(config, **change))
