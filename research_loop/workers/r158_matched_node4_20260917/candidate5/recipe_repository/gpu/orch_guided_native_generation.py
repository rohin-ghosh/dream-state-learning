"""Opt-in long generation over an already bound child, not a new model loader."""

from gpu import orch_guided_native as native


def generate(loaded, messages, *, max_prompt_tokens, max_new_tokens):
    require = native.require
    require(type(max_prompt_tokens) is int and max_prompt_tokens > 0
            and type(max_new_tokens) is int and max_new_tokens > 0,
            'explicit_positive_generation_budgets_required')
    require(native.process_identity() == loaded.process, 'stage_moved_to_another_process')
    require(loaded.binding.phase in ('collection', 'sealed_readout'), 'generation_requires_readonly_stage')
    loaded.context.validate(loaded.binding)
    engine = loaded.engine
    require(not engine.model.training, 'generation_requires_eval_mode')
    require(not any(parameter.requires_grad for unused, parameter in engine.model.named_parameters()),
            'generation_requires_frozen_parameters')
    model_limit = engine.model.config.max_position_embeddings
    require(type(model_limit) is int and model_limit > 0
            and max_prompt_tokens + max_new_tokens <= model_limit,
            'declared_total_budget_exceeds_model_positions')
    engine.check('generation')
    tokens = engine.tokenizer.apply_chat_template(messages, tokenize=True,
        add_generation_prompt=True, return_dict=False)
    require(type(tokens) is list and all(type(token) is int and token >= 0 for token in tokens),
            'native_template_integer_tokens_required')
    require(0 < len(tokens) <= max_prompt_tokens, 'context_bound_exceeded_no_truncation')
    inputs = engine.torch.tensor([tokens], dtype=engine.torch.long, device=engine.device)
    config = engine.transformers.GenerationConfig(do_sample=False, num_beams=1,
        use_cache=True, max_new_tokens=max_new_tokens, repetition_penalty=1.0,
        eos_token_id=engine.tokenizer.eos_token_id, pad_token_id=engine.tokenizer.pad_token_id)
    with engine.torch.inference_mode():
        generated = engine.model.generate(input_ids=inputs, attention_mask=engine.torch.ones_like(inputs),
                                          generation_config=config)
    require(generated[0, :len(tokens)].tolist() == tokens, 'generated_prefix_changed')
    tail = generated[0, len(tokens):].tolist()
    require(len(tail) <= max_new_tokens, 'generated_tail_exceeds_declared_budget')
    terminal = bool(tail) and tail[-1] == engine.tokenizer.eos_token_id
    text = engine.tokenizer.decode(tail[:-1] if terminal else tail,
        skip_special_tokens=False, clean_up_tokenization_spaces=False)
    return dict(messages=messages, prompt_tokens=len(tokens), token_ids=tail,
                raw=text, terminal=terminal, truncated=not terminal and len(tail) == max_new_tokens)
