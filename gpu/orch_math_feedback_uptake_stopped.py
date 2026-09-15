"""Explicit reflection-only integration of Pasteur's lexical stop criterion."""

import hashlib
from pathlib import Path

from gpu import orch_reflection_repetition_stop as safeguard


class TaggedMessages(list):
    def __init__(self, messages, purpose):
        super().__init__(messages)
        if purpose not in ('experience', 'check', 'revision', 'held'):
            raise ValueError('unknown_generation_purpose')
        self.purpose = purpose


def engine_class(original):
    class ReflectionGuardEngine(original):
        def generate(self, messages, *, max_new_tokens):
            if not isinstance(messages, TaggedMessages):
                raise AssertionError('explicit_purpose_required')
            if messages.purpose != 'revision':
                return super().generate(list(messages), max_new_tokens=max_new_tokens)
            self.check('generation')
            self.model.eval()
            tokens = self.tokenizer.apply_chat_template(list(messages), tokenize=True,
                add_generation_prompt=True, return_dict=False)
            if not 0 < max_new_tokens <= 8192 or not 0 < len(tokens) < 16384:
                raise AssertionError('bounded_uncropped_generation')
            actual_cap = min(max_new_tokens, 16384 - len(tokens))
            inputs = self.torch.tensor([tokens], dtype=self.torch.long, device=self.device)
            criterion = safeguard.ExactParagraphRepetitionStop(self.tokenizer, prompt_length=len(tokens),
                eos_token_ids=self.tokenizer.eos_token_id)
            config = self.transformers.GenerationConfig(do_sample=False, num_beams=1, use_cache=True,
                max_new_tokens=actual_cap, repetition_penalty=1.0, eos_token_id=self.tokenizer.eos_token_id,
                pad_token_id=self.tokenizer.pad_token_id)
            with self.torch.inference_mode():
                generated = self.model.generate(input_ids=inputs, attention_mask=self.torch.ones_like(inputs),
                    generation_config=config, stopping_criteria=self.transformers.StoppingCriteriaList([criterion]))
            if generated[0, :len(tokens)].tolist() != tokens:
                raise AssertionError('prompt_modified')
            tail = generated[0, len(tokens):].tolist()
            ending = criterion.finalize(generated, max_new_tokens=actual_cap)
            terminal = ending['terminal']
            raw = self.tokenizer.decode(tail[:-1] if terminal else tail,
                skip_special_tokens=False, clean_up_tokenization_spaces=False)
            if not terminal and raw != ending['raw_prefix']:
                raise AssertionError('stopped_prefix_not_preserved')
            ending['source_sha256'] = hashlib.sha256(Path(safeguard.__file__).read_bytes()).hexdigest()
            ending['application_scope'] = 'OWN_REFLECTION_ONLY'
            ending['fit_eligibility'] = 'NOT_APPLICABLE_BASE_NO_WEIGHT_WRITES_NOT_AUTO_ADMITTED'
            return dict(messages=list(messages), prompt_tokens=len(tokens), token_ids=tail, raw=raw,
                terminal=terminal, truncated=ending['truncated'], requested_generation_cap=max_new_tokens,
                effective_generation_cap=actual_cap, context_limit=16384, input_truncated=False,
                reflection_guard=ending)
    return ReflectionGuardEngine
