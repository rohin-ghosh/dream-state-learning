"""Frozen genuine BASE engine with bounded batch readouts, no adapter/sleep."""

from gpu.orch_rich_hot_node3_base107_engine import Engine as BaseEngine, assert_no_adapter


class Engine(BaseEngine):
    def generate_batch(self, messages, *, max_new_tokens):
        self.check('generation')
        assert_no_adapter(self.model)
        encoded = [self.tokenizer.apply_chat_template(value, tokenize=True,
            add_generation_prompt=True, return_dict=False) for value in messages]
        width = max(map(len, encoded))
        if not 0 < max_new_tokens <= 16384 - width:
            raise ValueError('uncropped_context_capacity')
        pad = self.tokenizer.pad_token_id
        inputs = self.torch.tensor([[pad] * (width - len(tokens)) + tokens for tokens in encoded],
            dtype=self.torch.long, device=self.device)
        mask = self.torch.tensor([[0] * (width - len(tokens)) + [1] * len(tokens) for tokens in encoded],
            dtype=self.torch.long, device=self.device)
        config = self.transformers.GenerationConfig(do_sample=False, num_beams=1, use_cache=True,
            max_new_tokens=max_new_tokens, no_repeat_ngram_size=4,
            eos_token_id=self.tokenizer.eos_token_id, pad_token_id=pad)
        with self.torch.inference_mode():
            generated = self.model.generate(input_ids=inputs, attention_mask=mask, generation_config=config)
        if not self.torch.equal(generated[:, :width], inputs):
            raise ValueError('native_prefix_mismatch')
        rows = []
        for index, tokens in enumerate(encoded):
            tail = generated[index, width:].tolist()
            terminal = self.tokenizer.eos_token_id in tail
            if terminal:
                tail = tail[:tail.index(self.tokenizer.eos_token_id) + 1]
            content = tail[:-1] if terminal else tail
            rows.append(dict(messages=messages[index], raw=self.tokenizer.decode(content,
                skip_special_tokens=False, clean_up_tokenization_spaces=False), token_ids=tail,
                prompt_tokens=len(tokens), terminal=terminal, truncated=not terminal and len(tail) == max_new_tokens,
                effective_generation_cap=max_new_tokens, input_truncated=False, trainingAllowed=False))
        return rows

    def generate(self, messages, *, max_new_tokens):
        return self.generate_batch([messages], max_new_tokens=max_new_tokens)[0]
