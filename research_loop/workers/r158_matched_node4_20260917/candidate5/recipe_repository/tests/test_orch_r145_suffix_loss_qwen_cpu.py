"""CPU equivalence probe against installed Qwen2/PEFT, never downloads weights."""

import importlib.util
from types import SimpleNamespace
import unittest

from gpu.orch_r145_suffix_loss import loss_window


@unittest.skipUnless(all(importlib.util.find_spec(name) is not None
    for name in ('torch', 'peft', 'transformers')), 'requires installed Qwen2/PEFT CPU runtime')
class QwenSuffixEquivalence(unittest.TestCase):
    def test_same_loss_adapter_gradient_and_rng_with_full_context(self):
        import torch
        from peft import LoraConfig, get_peft_model
        from transformers import Qwen2Config, Qwen2ForCausalLM

        torch.set_num_threads(2)
        torch.manual_seed(145)
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
        trainable = {name: parameter for name, parameter in model.named_parameters() if parameter.requires_grad}
        self.assertTrue(trainable)
        self.assertTrue(all('lora_' in name for name in trainable))
        for prefix, target_count in ((1, 1), (28, 5), (100, 11)):
            with self.subTest(prefix=prefix, target_count=target_count):
                inputs = torch.randint(3, 128, (1, prefix + target_count))
                labels = inputs.clone()
                labels[:, :prefix] = -100
                sample = SimpleNamespace(input_ids=tuple(inputs[0].tolist()),
                    labels=tuple(labels[0].tolist()), target_ids=tuple(inputs[0, prefix:].tolist()))
                window = loss_window(sample)
                initial_rng = torch.get_rng_state()
                model.zero_grad(set_to_none=True)
                original_loss = model(input_ids=inputs, labels=labels,
                    attention_mask=torch.ones_like(inputs), use_cache=False).loss
                original_loss.backward()
                original_rng = torch.get_rng_state()
                original_gradients = {name: value.grad.clone() for name, value in trainable.items()}
                for name, gradient in original_gradients.items():
                    if prefix == target_count == 1 and 'q_proj' in name:
                        self.assertEqual(torch.count_nonzero(gradient).item(), 0, name)
                    else:
                        self.assertGreater(torch.count_nonzero(gradient).item(), 0, name)
                model.zero_grad(set_to_none=True)
                torch.set_rng_state(initial_rng)
                changed_loss = model(input_ids=inputs,
                    labels=torch.tensor([window['labels']], dtype=torch.long),
                    logits_to_keep=window['logits_to_keep'],
                    attention_mask=torch.ones_like(inputs), use_cache=False).loss
                changed_loss.backward()
                torch.testing.assert_close(changed_loss, original_loss, atol=1e-6, rtol=1e-6)
                self.assertTrue(torch.equal(torch.get_rng_state(), original_rng))
                for name, parameter in trainable.items():
                    torch.testing.assert_close(parameter.grad, original_gradients[name], atol=1e-6, rtol=1e-5)
                self.assertTrue(all(parameter.grad is None for name, parameter in model.named_parameters()
                    if name not in trainable))


if __name__ == '__main__':
    unittest.main()
