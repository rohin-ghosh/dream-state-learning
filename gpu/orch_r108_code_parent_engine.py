"""Direct frozen BASE with a pinned reflection-only repetition stop."""

import hashlib
from pathlib import Path

from gpu.orch_rich_hot_node3_base107_engine import Engine as BaseEngine, assert_no_adapter
from gpu import orch_reflection_repetition_stop as stop
from organism_v6 import orch_r108_code_parent as policy


class Engine(BaseEngine):
    def generate(self, messages, *, max_new_tokens, reflection=False):
        self.check('generation')
        assert_no_adapter(self.model)
        tokens = self.tokenizer.apply_chat_template(messages, tokenize=True,
            add_generation_prompt=True, return_dict=False)
        policy.require(0 < max_new_tokens <= policy.token_budget(len(tokens)), 'bounded_full_prompt')
        inputs = self.torch.tensor([tokens], dtype=self.torch.long, device=self.device)
        config = self.transformers.GenerationConfig(do_sample=False, num_beams=1,
            use_cache=True, max_new_tokens=max_new_tokens, repetition_penalty=1.0,
            eos_token_id=self.tokenizer.eos_token_id, pad_token_id=self.tokenizer.pad_token_id)
        criterion, options = None, {}
        if reflection:
            policy.require(hashlib.sha256(Path(stop.__file__).read_bytes()).hexdigest() == policy.STOP_SHA,
                'pinned_reflection_guard')
            criterion = stop.ExactParagraphRepetitionStop(self.tokenizer, prompt_length=len(tokens),
                eos_token_ids=self.tokenizer.eos_token_id)
            options['stopping_criteria'] = self.transformers.StoppingCriteriaList([criterion])
        with self.torch.inference_mode():
            generated = self.model.generate(input_ids=inputs, attention_mask=self.torch.ones_like(inputs),
                generation_config=config, **options)
        policy.require(generated[0, :len(tokens)].tolist() == tokens, 'full_native_prefix_verified')
        tail = generated[0, len(tokens):].tolist()
        terminal = bool(tail) and tail[-1] == self.tokenizer.eos_token_id
        raw = self.tokenizer.decode(tail[:-1] if terminal else tail,
            skip_special_tokens=False, clean_up_tokenization_spaces=False)
        ending = criterion.finalize(generated, max_new_tokens=max_new_tokens) if criterion else None
        if ending is not None:
            policy.require(ending['terminal'] == terminal and (terminal or ending['raw_prefix'] == raw),
                'exact_guarded_prefix')
        return dict(messages=messages, raw=raw, token_ids=tail, prompt_tokens=len(tokens),
            terminal=terminal, truncated=ending['truncated'] if ending else not terminal and len(tail) == max_new_tokens,
            input_truncated=False, prompt_token_ids_sha256=policy.digest(tokens),
            effective_generation_cap=max_new_tokens, reflection_guard=ending,
            reflection_stop_source_sha256=policy.STOP_SHA if reflection else None,
            trainingAllowed=False, semantic_helpfulness=None)
