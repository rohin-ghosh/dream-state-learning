"""Native 16K exhaustion generation without model or RoPE modifications."""

from gpu import astra_portable_actor_bundle as portable
from organism_v6 import orch_rich_hot_node1_exhaustion as policy


class Engine(portable.source.Engine):
    def generate(self, messages, *, max_new_tokens):
        self.check('generation')
        tokens = self.tokenizer.apply_chat_template(messages, tokenize=True,
            add_generation_prompt=True, return_dict=False)
        policy.require(0 < max_new_tokens <= policy.token_budget(len(tokens)), 'native_context_budget')
        inputs = self.torch.tensor([tokens], dtype=self.torch.long, device=self.device)
        config = self.transformers.GenerationConfig(do_sample=False, num_beams=1,
            use_cache=True, max_new_tokens=max_new_tokens, repetition_penalty=1.0,
            eos_token_id=self.tokenizer.eos_token_id, pad_token_id=self.tokenizer.pad_token_id)
        with self.torch.inference_mode():
            generated = self.model.generate(input_ids=inputs, attention_mask=self.torch.ones_like(inputs),
                generation_config=config)
        policy.require(generated[0, :len(tokens)].tolist() == tokens, 'native_prefix_changed')
        tail = generated[0, len(tokens):].tolist()
        terminal = bool(tail) and tail[-1] == self.tokenizer.eos_token_id
        text = self.tokenizer.decode(tail[:-1] if terminal else tail,
            skip_special_tokens=False, clean_up_tokenization_spaces=False)
        return dict(messages=messages, prompt_tokens=len(tokens), token_ids=tail,
            raw=text, terminal=terminal, truncated=not terminal and len(tail) == max_new_tokens)
