from types import SimpleNamespace

import pytest

from gpu import orch_guided_native as native
from gpu import orch_r111_route_pair as route
from gpu import orch_r111_route_shared as client


def test_actual_cpu_peft_reload_preserves_parameters_and_optimizer(tmp_path, monkeypatch):
    torch = pytest.importorskip('torch')
    transformers = pytest.importorskip('transformers')
    peft = pytest.importorskip('peft')
    assert not torch.cuda.is_initialized()
    config = transformers.Qwen2Config(vocab_size=32, hidden_size=32, intermediate_size=64,
        num_hidden_layers=1, num_attention_heads=4, num_key_value_heads=2, max_position_embeddings=128)
    model = peft.get_peft_model(transformers.Qwen2ForCausalLM(config),
        peft.LoraConfig(r=8, lora_alpha=16, target_modules=['q_proj', 'v_proj'], task_type='CAUSAL_LM'))
    base = {name: parameter for name, parameter in model.named_parameters() if not native.is_lora(name)}
    base_sha = native.state_hash(base)
    monkeypatch.setattr(route, 'BASE_SHA', base_sha)
    def verify_base():
        assert native.state_hash(base) == base_sha
    engine = SimpleNamespace(model=model, torch=torch, verify_base=verify_base)
    parameters = {name: parameter for name, parameter in model.named_parameters() if native.is_lora(name)}
    optimizer = torch.optim.AdamW(list(parameters.values()), lr=3e-5)
    tokens = torch.tensor([[1, 2, 3, 4]])
    model(input_ids=tokens, labels=tokens).loss.backward()
    optimizer.step()
    optimizer.zero_grad(set_to_none=True)
    route.checkpoint(engine, optimizer, tmp_path / 'checkpoint', sleeps=1, cycle=1)
    reference = client.checkpoint_reference(tmp_path / 'checkpoint' / 'CHECKPOINT.json')
    identities = {name: id(parameter) for name, parameter in parameters.items()}
    expected_sha = native.state_hash(parameters)
    with torch.no_grad():
        for parameter in parameters.values():
            parameter.add_(1)
    assert native.state_hash(parameters) != expected_sha
    client.reload_adapter(engine, reference)
    assert native.state_hash(parameters) == expected_sha
    assert {name: id(parameter) for name, parameter in parameters.items()} == identities
    replacement = torch.optim.AdamW(list(parameters.values()), lr=1)
    client.restore_optimizer(engine, replacement, reference, owner='F1')
    assert replacement.param_groups[0]['lr'] == 3e-5
    assert {int(state['step'].item()) for state in replacement.state.values()} == {1}
    assert not torch.cuda.is_initialized()
