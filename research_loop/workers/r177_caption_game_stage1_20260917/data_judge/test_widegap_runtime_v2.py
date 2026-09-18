import copy

import pytest

from research_loop.workers.r177_caption_game_stage1_20260917.data_judge import bt_widegap_v2 as ranker
from research_loop.workers.r177_caption_game_stage1_20260917.data_judge import widegap_budget as budget
from research_loop.workers.r177_caption_game_stage1_20260917.data_judge import widegap_confinement as confinement
from research_loop.workers.r177_caption_game_stage1_20260917.data_judge import widegap_receiving_v2 as receiving


def fixture():
    config = dict(schema='NY_WIDEGAP100K_TRAIN_CONFIG_V2', objective='BRADLEY_TERRY_WEIGHTED_LOGISTIC',
        label_policy=ranker.LABEL_POLICY, pair_policy=ranker.PAIR_POLICY, reliability_policy=ranker.RELIABILITY_POLICY,
        max_updates=6250, batch_pairs=16, gradient_accumulation=1, max_seconds=20400,
        calibration_reserve_seconds=1800, max_length=512, heldout_per_contest=256,
        learning_rate=0.00003, inference_batch=16, seed=177, vote_cap=100,
        evaluation_steps=ranker.widegap.EVALUATION_STEPS, quality_contract=ranker.quality.CONTRACT,
        optimizer_state_reset=True, humor_soft_CE_used=False, image_judge_training=False,
        development_reuse_provisional=True)
    inventory = dict(root='/fixture/widegap', lease=dict(path='/fixture/lease', sha256='a'*64),
        allocation_end_unix=22600, lease_safe_end_unix=30000,
        files={'ranker.py': dict(sha256='b'*64), 'support/pytest.py': dict(sha256='c'*64)})
    record = dict(schema='NY_WIDEGAP100K_EXPERIMENT_BUDGET_V1', machine_lease_extended=False,
        authority='Main/Astra Builder under user standing directives', root=inventory['root'], lease=inventory['lease'],
        device_uuid=confinement.DEVICE, start_unix=1000, deadline_unix=22600,
        max_gpu_seconds=20400, calibration_reserve_seconds=1800, source_sha256={'ranker.py':'b'*64})
    return config, inventory, record


def test_fixed_recipe_and_separate_six_hour_budget():
    config, inventory, record = fixture()
    before = copy.deepcopy((config, inventory, record))
    receiving.validate_config(config)
    budget.validate(record, inventory, config, 1100)
    assert config['max_updates']*config['batch_pairs']*config['gradient_accumulation'] == 100000
    assert (config, inventory, record) == before


@pytest.mark.parametrize('change', [dict(max_updates=1000), dict(batch_pairs=2), dict(gradient_accumulation=4),
    dict(max_seconds=21601), dict(calibration_reserve_seconds=0), dict(learning_rate=0.0001),
    dict(objective='Q_DIFFERENCE_MSE'), dict(label_policy='POSITIVE_VOTE_MASS'),
    dict(optimizer_state_reset=False), dict(evaluation_steps=[6250]), dict(humor_soft_CE_used=True),
    dict(image_judge_training=True), dict(quality_contract={})])
def test_recipe_changes_rejected(change):
    config, unused_inventory, unused_record = fixture()
    with pytest.raises(ValueError):
        receiving.validate_config(dict(config, **change))


@pytest.mark.parametrize('change', [dict(machine_lease_extended=True), dict(authority='new user ratification'),
    dict(deadline_unix=22601), dict(start_unix=999), dict(source_sha256={}), dict(device_uuid='other'),
    dict(lease={}), dict(root='/old'), dict(max_gpu_seconds=21601), dict(start_unix=float('nan'))])
def test_budget_does_not_extend_or_mutate_machine_authority(change):
    config, inventory, record = fixture()
    with pytest.raises(ValueError):
        budget.validate(dict(record, **change), inventory, config, 1100)


def test_late_launch_and_machine_ceiling_fail_closed():
    config, inventory, record = fixture()
    with pytest.raises(ValueError):
        budget.validate(record, inventory, config, 2140)
    with pytest.raises(ValueError):
        budget.validate(record, dict(inventory, lease_safe_end_unix=22659), config, 1100)


def test_containment_only_changes_exact_runtime_property():
    original = confinement.original.command('/fixture', 'a'*64, 'train', 7200)
    actual = confinement.command('/fixture', 'a'*64, 'train', 20400)
    assert [(first,second) for first,second in zip(original,actual) if first!=second] == [
        ('--property=RuntimeMaxSec=7200','--property=RuntimeMaxSec=20400')]
    assert confinement.command('/fixture','a'*64,'probe',20400) == confinement.original.command('/fixture','a'*64,'probe',7200)
    for invalid in (7200,21601,20400.0,True):
        with pytest.raises(ValueError):
            confinement.command('/fixture','a'*64,'train',invalid)


def test_actual_tiny_Qwen_warmstart_update_reload_and_frozen_backbone(tmp_path):
    torch = pytest.importorskip('torch')
    from transformers import Qwen2Config, Qwen2ForSequenceClassification
    from peft import LoraConfig, TaskType, get_peft_model, PeftModel
    torch.set_num_threads(2)
    torch.manual_seed(177)
    config = Qwen2Config(vocab_size=32, hidden_size=16, intermediate_size=32, num_hidden_layers=1,
        num_attention_heads=2, num_key_value_heads=2, max_position_embeddings=64, num_labels=1, pad_token_id=0)
    base = Qwen2ForSequenceClassification(config)
    state = copy.deepcopy(base.state_dict())
    original = get_peft_model(base, LoraConfig(task_type=TaskType.SEQ_CLS, r=2, lora_alpha=4,
        target_modules=['q_proj','v_proj'], modules_to_save=['score'], bias='none'))
    original.save_pretrained(tmp_path/'original', safe_serialization=True)
    backbone = Qwen2ForSequenceClassification(config)
    backbone.load_state_dict(state)
    warm = PeftModel.from_pretrained(backbone, str(tmp_path/'original'), is_trainable=True, local_files_only=True)
    names = [name for name, parameter in warm.named_parameters() if parameter.requires_grad]
    assert names and all('lora_' in name or 'score.modules_to_save' in name for name in names)
    before = {name:parameter.detach().clone() for name,parameter in warm.named_parameters() if not parameter.requires_grad}
    tokens = torch.tensor([[1,2,3,0],[1,4,5,0]])
    scores = warm(input_ids=tokens, attention_mask=tokens!=0).logits[:,0]
    loss = ranker.bt_loss(scores[:1],scores[1:],torch.ones(1),torch.ones(1),torch)
    loss.backward()
    assert any(parameter.grad is not None and torch.count_nonzero(parameter.grad) for name,parameter in warm.named_parameters() if 'score.modules_to_save' in name)
    optimizer = torch.optim.AdamW([parameter for parameter in warm.parameters() if parameter.requires_grad], lr=0.00003)
    optimizer.step()
    assert all(torch.equal(value,dict(warm.named_parameters())[name]) for name,value in before.items())
    warm.eval()
    expected = warm(input_ids=tokens, attention_mask=tokens!=0).logits.detach()
    warm.save_pretrained(tmp_path/'updated', safe_serialization=True)
    warm.load_adapter(str(tmp_path/'updated'), adapter_name='selected', is_trainable=False)
    warm.set_adapter('selected')
    warm.eval()
    assert torch.allclose(expected,warm(input_ids=tokens,attention_mask=tokens!=0).logits)
    assert not torch.cuda.is_initialized()
