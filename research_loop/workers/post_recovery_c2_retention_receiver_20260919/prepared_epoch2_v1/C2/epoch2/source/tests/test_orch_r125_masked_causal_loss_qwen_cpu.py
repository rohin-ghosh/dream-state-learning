"""Installed Qwen2/PEFT CPU check for the opt-in native sleep loss, no downloads."""

import importlib.util
from types import SimpleNamespace
import unittest

from gpu import orch_r125_continual_native as native


@unittest.skipUnless(all(importlib.util.find_spec(name) is not None
    for name in ('torch', 'peft', 'transformers')), 'requires installed Qwen2/PEFT CPU runtime')
class QwenMaskedCausalLossTests(unittest.TestCase):
    def test_full_context_suffix_loss_lora_gradients_and_rng(self):
        import torch
        from peft import LoraConfig, get_peft_model
        from transformers import Qwen2Config, Qwen2ForCausalLM

        torch.set_num_threads(1)
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(541)
            model = get_peft_model(Qwen2ForCausalLM(Qwen2Config(vocab_size=128,
                hidden_size=32, intermediate_size=64, num_hidden_layers=2,
                num_attention_heads=4, num_key_value_heads=2, max_position_embeddings=256,
                attention_dropout=0.0, use_cache=False)), LoraConfig(r=8, lora_alpha=16,
                lora_dropout=0.05, target_modules=['q_proj', 'v_proj'], task_type='CAUSAL_LM'))
            model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
            model.enable_input_require_grads()
            model.train()
            with torch.no_grad():
                for name, parameter in model.named_parameters():
                    if 'lora_B' in name:
                        parameter.normal_(mean=0.0, std=0.03)
            parameters = {name: parameter for name, parameter in model.named_parameters() if parameter.requires_grad}
            self.assertTrue(parameters)
            self.assertTrue(all('lora_' in name for name in parameters))
            for prefix, count in ((1, 1), (28, 5), (100, 11)):
                with self.subTest(prefix=prefix, count=count):
                    inputs = torch.randint(3, 128, (1, prefix + count))
                    labels = inputs.clone()
                    labels[:, :prefix] = -100
                    mask = torch.ones_like(inputs)
                    sample = SimpleNamespace(input_ids=tuple(inputs[0].tolist()),
                        labels=tuple(labels[0].tolist()), target_ids=tuple(inputs[0, prefix:].tolist()))
                    initial_rng = torch.get_rng_state().clone()
                    model.zero_grad(set_to_none=True)
                    original = model(input_ids=inputs, labels=labels, attention_mask=mask, use_cache=False).loss
                    original.backward()
                    expected_rng = torch.get_rng_state().clone()
                    gradients = {name: parameter.grad.clone() for name, parameter in parameters.items()}
                    model.zero_grad(set_to_none=True)
                    torch.set_rng_state(initial_rng)
                    actual = native.sleep_causal_loss(model, inputs, labels, mask,
                        implementation=native.MASKED_CAUSAL_CE_V1, sample=sample)
                    actual.backward()
                    torch.testing.assert_close(actual, original, atol=1e-6, rtol=1e-6)
                    self.assertTrue(torch.equal(torch.get_rng_state(), expected_rng))
                    for name, parameter in parameters.items():
                        torch.testing.assert_close(parameter.grad, gradients[name], atol=1e-6, rtol=1e-5)
                    self.assertTrue(all(parameter.grad is None for name, parameter in model.named_parameters()
                        if name not in parameters))


if __name__ == '__main__':
    unittest.main()
