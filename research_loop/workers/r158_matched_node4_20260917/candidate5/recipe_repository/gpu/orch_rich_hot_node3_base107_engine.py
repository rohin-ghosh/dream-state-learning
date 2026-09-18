"""Direct local Qwen base inference: no adapter loader, wrapper, or fitting."""

import importlib.metadata
import json
from pathlib import Path


BASE_SHA = 'a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992'


def assert_original_rope(config, original):
    assert original.get('rope_scaling') is None
    assert config.max_position_embeddings == original['max_position_embeddings'] >= 32768
    normalized = getattr(config, 'rope_scaling', None)
    assert normalized is None or normalized == dict(
        rope_theta=original['rope_theta'], rope_type='default')


def assert_no_adapter(model):
    names = [name for name, parameter in model.named_parameters()]
    adapter_names = [name for name in names if 'lora_' in name.lower() or 'adapter' in name.lower()]
    wrappers = [type(module).__module__ for module in model.modules()
                if type(module).__module__.startswith('peft')]
    trainable = sum(parameter.requires_grad for parameter in model.parameters())
    if adapter_names or wrappers or trainable or getattr(model, '_hf_peft_config_loaded', False):
        raise ValueError('genuine_frozen_base_no_adapter_required')
    if getattr(model, 'peft_config', None):
        raise ValueError('peft_configuration_forbidden')
    return dict(adapter_parameter_count=0, peft_wrapper_count=0,
                trainable_parameter_count=0, hf_peft_config_loaded=False,
                model_class=type(model).__name__)


class Engine:
    def __init__(self, model_dir, tokenizer, *, device, check):
        import torch
        import transformers
        from organism_v6.pcfl_vertical_train import _state_hash

        self.torch, self.transformers = torch, transformers
        self.tokenizer, self.device, self.check = tokenizer, device, check
        self.model_dir = Path(model_dir)
        if (self.model_dir / 'adapter_config.json').exists():
            raise ValueError('base_directory_contains_adapter_config')
        torch.set_num_threads(1)
        if torch.get_num_interop_threads() != 1:
            torch.set_num_interop_threads(1)
        check('direct_base_load')
        model = transformers.AutoModelForCausalLM.from_pretrained(str(self.model_dir),
            local_files_only=True, trust_remote_code=False, use_safetensors=True,
            torch_dtype=torch.bfloat16, attn_implementation='sdpa', device_map=None)
        assert model.config.model_type == 'qwen2'
        assert_original_rope(model.config, json.loads((self.model_dir / 'config.json').read_text()))
        model.requires_grad_(False)
        model.eval()
        self.model = model
        self.no_adapter = assert_no_adapter(model)
        self.base_references = dict(model.state_dict(keep_vars=True))
        self.loaded_base_sha256 = _state_hash(self.base_references)
        assert self.loaded_base_sha256 == BASE_SHA
        self.model = model.to(device)
        if str(device).startswith('cuda'):
            assert torch.cuda.device_count() == 1
        self.hook = model.register_forward_pre_hook(lambda module, inputs: check('forward'))
        self.runtime = {name: importlib.metadata.version(name) for name in ('torch', 'transformers', 'tokenizers')}

    def verify_base(self):
        from organism_v6.pcfl_vertical_train import _state_hash
        self.check('base_hash')
        assert_no_adapter(self.model)
        assert _state_hash(self.base_references) == BASE_SHA

    def generate(self, messages, *, max_new_tokens):
        from organism_v6.orch_rich_hot_node1_exhaustion import token_budget
        self.check('generation')
        assert_no_adapter(self.model)
        tokens = self.tokenizer.apply_chat_template(messages, tokenize=True,
            add_generation_prompt=True, return_dict=False)
        assert 0 < max_new_tokens <= token_budget(len(tokens))
        inputs = self.torch.tensor([tokens], dtype=self.torch.long, device=self.device)
        config = self.transformers.GenerationConfig(do_sample=False, num_beams=1,
            use_cache=True, max_new_tokens=max_new_tokens, repetition_penalty=1.0,
            eos_token_id=self.tokenizer.eos_token_id, pad_token_id=self.tokenizer.pad_token_id)
        with self.torch.inference_mode():
            generated = self.model.generate(input_ids=inputs, attention_mask=self.torch.ones_like(inputs),
                generation_config=config)
        assert generated[0, :len(tokens)].tolist() == tokens
        tail = generated[0, len(tokens):].tolist()
        terminal = bool(tail) and tail[-1] == self.tokenizer.eos_token_id
        text = self.tokenizer.decode(tail[:-1] if terminal else tail,
            skip_special_tokens=False, clean_up_tokenization_spaces=False)
        return dict(messages=messages, prompt_tokens=len(tokens), token_ids=tail,
                    raw=text, terminal=terminal, truncated=not terminal and len(tail) == max_new_tokens)
