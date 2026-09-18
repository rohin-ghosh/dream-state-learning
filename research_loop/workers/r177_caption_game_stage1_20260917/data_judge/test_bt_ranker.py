import math
from pathlib import Path

import pytest

from research_loop.workers.r177_caption_game_stage1_20260917.data_judge import bt_ranker as bt


def row(name, counts, contest='fixture'):
    return dict(contest_id=contest, scene='Synthetic fixture scene.', caption=name,
        caption_family_sha256=name, counts=counts, votes=sum(counts))


def test_pair_order_is_positive_mass_not_mean_rating():
    high_mean = row('high mean', [80, 1, 19])
    high_q = row('high q', [70, 30, 0])
    assert bt.pair_target(high_mean, high_q)['winner'] == 0
    assert bt.positive_mass(high_mean) < bt.positive_mass(high_q)


def test_reliable_pairs_are_bounded_capped_and_ties_skipped():
    target = bt.pair_target(row('left', [1, 5, 4]), row('right', [9, 1, 0]))
    assert 0 < target['reliability'] <= 0.1 and target['winner'] == 1
    assert bt.pair_target(row('left', [1, 5, 4]), row('other', [1, 4, 5])) is None
    with pytest.raises(ValueError, match='within_contest'):
        bt.pair_target(row('one', [5, 4, 1]), row('two', [8, 2, 0], 'other'))


def test_actual_BT_logistic_gradient_not_q_difference_MSE():
    torch = pytest.importorskip('torch')
    left = torch.tensor([0.2], requires_grad=True)
    right = torch.tensor([-0.2], requires_grad=True)
    loss = bt.bt_loss(left, right, torch.tensor([1.0]), torch.tensor([0.5]), torch)
    assert loss.item() == pytest.approx(math.log1p(math.exp(-0.4)))
    loss.backward()
    assert left.grad.item() < 0 and right.grad.item() > 0
    assert not torch.cuda.is_initialized()


def test_isotonic_q_is_monotone_and_merges_wrong_order():
    calibration = bt.isotonic_calibration([0, 1, 2], [0.2, 0.1, 0.9])
    assert calibration['values'] == pytest.approx([0.15, 0.9])
    values = [bt.calibrated_q(calibration, score) for score in (-10, 0, 1, 2, 10)]
    assert values == sorted(values) and values[0] == pytest.approx(0.15) and values[-1] == 0.9
    assert bt.isotonic_calibration([1, 1], [0.1, 0.5])['values'] == [0.3]


@pytest.mark.parametrize('scores,targets', [([], []), ([float('nan')], [0.1]), ([0], [-1]), ([0], [2])])
def test_invalid_scalar_calibration_rejected(scores, targets):
    with pytest.raises(ValueError):
        bt.isotonic_calibration(scores, targets)


def test_rank_and_sample_topk_never_claim_full_top200():
    rows = [row(str(index), [10-index, index, 0]) for index in range(10)]
    metrics = bt.ranking_metrics(rows, list(range(10)), top_k=5)
    assert metrics['macro_contest_spearman'] == pytest.approx(1)
    assert metrics['pairwise_concordance'] == 1
    assert metrics['sampled_macro_top_k_positive_vote_mass'] == pytest.approx(0.7)
    assert metrics['maximum_sampled_rows_per_contest'] == 10
    assert not metrics['literal_full_contest_top200_measured']


def test_cpu_tiny_Qwen_scalar_LoRA_freezes_backbone_and_reloads_adapter(tmp_path):
    torch = pytest.importorskip('torch')
    from transformers import Qwen2Config, Qwen2ForSequenceClassification
    from peft import LoraConfig, TaskType, get_peft_model
    torch.manual_seed(171)
    config = Qwen2Config(vocab_size=32, hidden_size=16, intermediate_size=32, num_hidden_layers=1,
        num_attention_heads=2, num_key_value_heads=2, max_position_embeddings=64, num_labels=1, pad_token_id=0)
    model = get_peft_model(Qwen2ForSequenceClassification(config), LoraConfig(task_type=TaskType.SEQ_CLS,
        r=2, lora_alpha=4, target_modules=['q_proj', 'v_proj'], modules_to_save=['score'], bias='none'))
    names = [name for name, parameter in model.named_parameters() if parameter.requires_grad]
    assert names and all('lora_' in name or 'score.modules_to_save' in name for name in names)
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
    model.enable_input_require_grads()
    tokens = torch.tensor([[1, 2, 3, 0], [1, 4, 5, 0]])
    scores = model(input_ids=tokens, attention_mask=(tokens != 0)).logits[:, 0]
    assert scores.shape == (2,)
    loss = bt.bt_loss(scores[:1], scores[1:], torch.ones(1), torch.ones(1), torch)
    loss.backward()
    assert any(parameter.grad is not None and torch.count_nonzero(parameter.grad) for name, parameter in model.named_parameters() if 'score.modules_to_save' in name)
    before = {name: parameter.detach().clone() for name, parameter in model.named_parameters() if not parameter.requires_grad}
    optimizer = torch.optim.AdamW([parameter for parameter in model.parameters() if parameter.requires_grad], lr=1e-4)
    optimizer.step()
    assert all(torch.equal(before[name], parameter) for name, parameter in model.named_parameters() if name in before)
    model.save_pretrained(tmp_path/'adapter', safe_serialization=True)
    model.load_adapter(str(tmp_path/'adapter'), adapter_name='selected', is_trainable=False)
    model.set_adapter('selected')
    assert not torch.cuda.is_initialized()


def test_R171_config_explicitly_rejects_old_humor_objectives():
    from research_loop.workers.r177_caption_game_stage1_20260917.data_judge import bt_receiving
    config = dict(schema='NY_R171_BT_TRAIN_CONFIG_V1', objective='BRADLEY_TERRY_WEIGHTED_LOGISTIC',
        label_policy=bt.LABEL_POLICY, pair_policy=bt.PAIR_POLICY, reliability_policy=bt.RELIABILITY_POLICY,
        max_updates=1000, batch_pairs=2, gradient_accumulation=4, max_seconds=2400, calibration_reserve_seconds=600,
        max_length=512, heldout_per_contest=64, learning_rate=0.0001, humor_soft_CE_used=False,
        image_judge_training=False, development_reuse_provisional=True)
    bt_receiving.validate_config(config)
    for change in (dict(objective='SOFT_CE'), dict(objective='Q_DIFFERENCE_MSE'), dict(humor_soft_CE_used=True),
            dict(image_judge_training=True), dict(max_seconds=7200), dict(label_policy='MEAN_RATING')):
        with pytest.raises(ValueError):
            bt_receiving.validate_config(dict(config, **change))
