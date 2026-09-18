"""Source-only HF readout over an explicitly supplied, already loaded model.

This non-material bridge implements v2 section 16 readout mechanics, not section
17 qualification. Public-message selection, authenticated model/tokenizer and
checkpoint identity, deadlines, aggregate budgets, device assignment/visibility,
and durable export of in-memory custody remain caller gates. No loaders run here.
The caller must prospectively bind OMP_NUM_THREADS, MKL_NUM_THREADS and torch
intra/inter-op thread counts for native replay; this bridge neither changes
global threads nor repairs old receipts or relaxes exact-equality requirements.

The supplied backend must be ordinary HF causal generation on CPU/CUDA, with
exclusive model/RNG access and a fixed caller-authorized visible CUDA inventory.
fork_rng saves CPU and ALL visible CUDA RNGs because manual_seed seeds all of
them, not just the input device. Other accelerator/custom RNGs are not qualified.
Neither this callback nor its synthetic tests authenticate public content or
confer native certification. Retain the actor's calls even when rollout fails.
"""

from copy import deepcopy
from types import MappingProxyType

from organism_v6 import composition_birth_stage2a as wire
from organism_v6 import composition_birth_stage2a_held as held
from organism_v6 import composition_birth_stage2a_rollout as rollout
from organism_v6 import composition_birth_stage2a_tokenization as tokenization


STATUS = "PARTIAL_SOURCE_ONLY"
SCIENCE_GATES = MappingProxyType(dict.fromkeys(rollout.SCIENCE_GATES, False))


def _render(tokenizer, prefix):
    if (type(prefix) is not tuple or not prefix
            or any(type(message) is not held.Message
                   or type(message.role) is not str
                   or message.role not in ("system", "user", "assistant")
                   or type(message.content) is not str for message in prefix)):
        raise ValueError("typed_public_message_prefix_required")
    messages = [{"role": message.role, "content": message.content} for message in prefix]
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    if type(prompt) is not str or not prompt:
        raise ValueError("chat_template_text_required")
    prompt_ids = tokenization._encode(tokenizer, prompt, name="readout_context")
    template_ids = tokenization._ids(tokenizer.apply_chat_template(
        messages, tokenize=True, add_generation_prompt=True, truncation=False, padding=False),
        name="readout_template")
    if prompt_ids != template_ids:
        raise ValueError("encode_template_disagreement")
    return prompt, prompt_ids


def _generation_config(max_new_tokens, eos, pad, factory):
    if factory is None:
        from transformers import GenerationConfig
        factory = GenerationConfig
    return factory(
        do_sample=False, temperature=0.0, top_p=1.0, top_k=0,
        num_beams=1, num_return_sequences=1, repetition_penalty=1.0,
        max_new_tokens=max_new_tokens, min_new_tokens=0, min_length=0,
        eos_token_id=eos, pad_token_id=pad, stop_strings=None,
        forced_bos_token_id=None, forced_eos_token_id=None,
        bad_words_ids=None, suppress_tokens=None, begin_suppress_tokens=None,
        no_repeat_ngram_size=0, max_time=None, token_healing=False,
        use_cache=True, return_dict_in_generate=False, output_scores=False,
        output_logits=False, output_attentions=False, output_hidden_states=False,
    )


class ReadoutActor:
    """Callable DecodeRequest -> Generation with failure-inclusive raw custody.

    count_basis is one of the existing tokenization source-only labels. device
    is supplied explicitly; no placement, discovery, loading, or thread tuning
    occurs at construction. generation_config_factory is an injection seam for
    synthetic tests, not a native-config authenticity assertion.

    calls contains one mutable in-memory receipt per invocation, reserved before
    validation. native_output retains the actual returned object before even
    tensor conversion; native_sequences additionally snapshots its list value.
    Exceptions themselves are retained (including backend-owned partial output).
    Nothing can recover tokens a backend never returned or attached to an error.
    Any call failure latches this actor closed; there is no retry or text repair.

    PEFT's public generation_config may forward through __getattr__ to a base
    module. Only real owners are rebound; original objects and forwarding-only
    attribute absence are restored, including after native wrapper mutations.
    """

    status = STATUS
    native_tokenizer_validated = False

    def __init__(self, *, tokenizer, model, torch, device, count_basis,
                 generation_config_factory=None):
        if type(count_basis) is not str or count_basis not in tokenization.COUNT_BASES:
            raise ValueError("explicit_non_native_count_basis_required")
        self.tokenizer = tokenizer
        self.model = model
        self.torch = torch
        self.device = device
        self.count_basis = count_basis
        self.generation_config_factory = generation_config_factory
        self.calls = []
        self._failed = False

    def count_context(self, prefix):
        return len(_render(self.tokenizer, prefix)[1])

    def __call__(self, request):
        receipt = dict(request=request, count_basis=self.count_basis, status=STATUS,
                       native_output=None, native_sequences=None, generated_ids=None,
                       raw=None, raw_bytes=None, generation=None, error=None)
        self.calls.append(receipt)
        try:
            if self._failed:
                raise ValueError("actor_failed_no_retry")
            if type(request) is not rollout.DecodeRequest:
                raise ValueError("decode_request_required")
            if type(request.seed) is not int or not 0 <= request.seed < 2**64:
                raise ValueError("exact_low64_seed_required")
            if (type(request.max_new_tokens) is not int or not 1 <= request.max_new_tokens <= 256
                    or type(request.context_tokens) is not int
                    or not 0 < request.context_tokens <= wire.CONTEXT_CAP
                    or request.context_tokens + request.max_new_tokens > wire.CONTEXT_CAP):
                raise ValueError("invalid_readout_caps")
            prompt, prompt_ids = _render(self.tokenizer, request.prefix)
            receipt.update(prompt=prompt, prompt_bytes=prompt.encode("utf-8"), prompt_ids=prompt_ids)
            if len(prompt_ids) != request.context_tokens:
                raise ValueError("context_count_disagreement")
            eos, pad, _, _ = tokenization._specials(self.tokenizer)
            config = _generation_config(request.max_new_tokens, eos, pad, self.generation_config_factory)
            receipt["generation_config"] = deepcopy(vars(config))
            torch, model = self.torch, self.model
            modes = tuple((module, module.training) for module in model.modules())
            absent = object()
            configs = tuple((module, vars(module).get("generation_config", absent))
                            for module, _ in modes)
            public_config = getattr(model, "generation_config", None)
            if (not callable(getattr(model, "generate", None)) or public_config is None
                    or not any(original is public_config for _, original in configs)):
                raise ValueError("hf_generate_with_resolved_config_owner_required")
            with torch.random.fork_rng(devices=None):
                try:
                    torch.manual_seed(request.seed)
                    model.eval()
                    for module, original in configs:
                        if original is not absent:
                            module.generation_config = config
                    with torch.inference_mode():
                        input_ids = torch.tensor([prompt_ids], dtype=torch.long, device=self.device)
                        output = model.generate(input_ids=input_ids, attention_mask=torch.ones_like(input_ids),
                                                generation_config=config)
                        receipt["native_output"] = output
                        sequences = output.tolist()
                        receipt["native_sequences"] = sequences
                finally:
                    for module, original in configs:
                        if original is not absent:
                            module.generation_config = original
                        elif "generation_config" in vars(module):
                            delattr(module, "generation_config")
                    for module, training in modes:
                        module.training = training
            if (type(sequences) is not list or len(sequences) != 1
                    or type(sequences[0]) is not list
                    or any(type(token) is not int or token < 0 for token in sequences[0])):
                raise ValueError("single_integer_token_sequence_required")
            sequence = sequences[0]
            continuation = tuple(sequence[len(prompt_ids):])
            receipt["generated_ids"] = continuation
            if tuple(sequence[:len(prompt_ids)]) != prompt_ids:
                raise ValueError("generated_prompt_ids_disagree")
            if not continuation or len(continuation) > request.max_new_tokens:
                raise ValueError("invalid_actual_generated_token_count")
            ended = continuation[-1] == eos
            content = continuation[:-1] if ended else continuation
            text = tokenization._decode(self.tokenizer, content)
            receipt["raw"] = text
            receipt["raw_bytes"] = text.encode("utf-8")
            receipt["decoded_with_terminal_eos"] = tokenization._decode(self.tokenizer, continuation)
            if not ended and len(continuation) != request.max_new_tokens:
                raise ValueError("unexplained_short_generation")
            generation = rollout.Generation(text, len(continuation), len(continuation), not ended,
                                            "stop" if ended else "length")
            receipt["generation"] = generation
            return generation
        except BaseException as error:
            self._failed = True
            receipt["error"] = error
            raise
