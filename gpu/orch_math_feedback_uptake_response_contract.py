"""Validate the uncropped direct-base engine response without altering generation."""

import hashlib
import inspect
from pathlib import Path


def canonical_response(response, messages, tokenizer, max_new_tokens, engine_sha256):
    tokens = tokenizer.apply_chat_template(list(messages), tokenize=True,
        add_generation_prompt=True, return_dict=False)
    if response.get('messages') != list(messages) or response.get('prompt_tokens') != len(tokens):
        raise ValueError('complete_prompt_tokenization_mismatch')
    if not 0 < len(tokens) < 16384 or not 0 < max_new_tokens <= 16384 - len(tokens):
        raise ValueError('uncropped_context_bounds')
    if 'input_truncated' in response and response['input_truncated'] is not False:
        raise ValueError('input_truncation_forbidden')
    if len(response['token_ids']) > max_new_tokens:
        raise ValueError('generation_cap_exceeded')
    return dict(response, input_truncated=False, context_limit=16384,
        requested_generation_cap=max_new_tokens, effective_generation_cap=max_new_tokens,
        response_contract=dict(engine_source_sha256=engine_sha256,
            full_prompt_tokens=len(tokens), uncropped_engine_prefix_assertion=True,
            metadata_only=True))


def engine_class(original):
    class ContractEngine(original):
        def generate(self, messages, *, max_new_tokens):
            response = super().generate(messages, max_new_tokens=max_new_tokens)
            source = Path(inspect.getfile(original))
            return canonical_response(response, messages, self.tokenizer, max_new_tokens,
                hashlib.sha256(source.read_bytes()).hexdigest())
    return ContractEngine
