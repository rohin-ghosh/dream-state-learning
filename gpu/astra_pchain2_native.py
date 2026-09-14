"""Explicit DEV P-CHAIN-2 material, one-arm D1 training, and readout commands.

Importing loads no native libraries. Main selects the local official Qwen path,
salt/context/time limits, canaries, and execution order. Material construction
uses a tokenizer but never a model. Train receives one training file only;
readout is a different invocation after Main releases the selected checkpoint.
This is not an automatic campaign launcher or a D2 continuation implementation.
"""

import argparse
from collections import Counter
from dataclasses import asdict, dataclass, replace
from hashlib import sha256
import json
import math
from pathlib import Path
import signal
import time

from gpu import astra_pchain2_nulls as nulls
from gpu import astra_pchain2_prepare as source


SCHEMA = "ASTRA_PCHAIN2_NATIVE_D1_V1"
IDENTIFIER_COUNT = 192
IDENTIFIER_WIDTH = 16
IDENTIFIER_TOKENS = 8
TARGET_MODULES = ("q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj")
OPTIMIZER = dict(betas=(0.9, 0.999), eps=1e-8, weight_decay=0.01,
                 amsgrad=False, foreach=False, fused=False)
NUMERICAL_BINDING = dict(
    authority="Main prospective Stage2A numerical implementation binding",
    runtime=dict(torch="2.13.0+cu130", transformers="5.5.3", peft="0.20.0", tokenizers="0.22.2"),
    base_dtype="bfloat16", rotary_buffers="preserve_float32", adapter_dtype="float32",
    autocast_adapter_dtype=True, placement="device_only", intra_threads=1, inter_threads=1,
    checkpointing=dict(use_reentrant=False), optimizer="AdamW", gradient_clip=None,
    material_limits=dict(max_context=16384, salt_limit=4096, deadline_seconds=180, solver_seconds=60))


def base_state_hash(model):
    from organism_v6.pcfl_vertical_train import _state_hash

    return _state_hash(model.state_dict())


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _json_bytes(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False,
                       separators=(",", ":")) + "\n").encode("ascii")


def _write(path, value):
    with Path(path).open("xb") as stream:
        stream.write(_json_bytes(value))


def _read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _digest(value):
    return sha256(_json_bytes(value)).hexdigest()


def _encode(tokenizer, text):
    values = tokenizer.encode(text, add_special_tokens=False, truncation=False)
    _require(isinstance(values, (list, tuple)) and all(type(value) is int and value >= 0 for value in values),
             "integer_token_ids_required")
    return tuple(values)


def _decode(tokenizer, values):
    text = tokenizer.decode(list(values), skip_special_tokens=False, clean_up_tokenization_spaces=False)
    _require(type(text) is str, "decoded_text_required")
    return text


def tokenizer_signature(tokenizer):
    return dict(chat_template_sha256=sha256(tokenizer.chat_template.encode("utf-8")).hexdigest(),
                backend_sha256=sha256(tokenizer.backend_tokenizer.to_str().encode("utf-8")).hexdigest(),
                eos_token_id=tokenizer.eos_token_id, pad_token_id=tokenizer.pad_token_id,
                eos_token=tokenizer.eos_token, padding_side=tokenizer.padding_side)


def load_local_tokenizer(model_dir):
    """Restore the exact local tokenizer.json backend, as in the native Stage2A fix."""
    import tokenizers
    from transformers import AutoTokenizer

    directory = Path(model_dir).resolve(strict=True)
    tokenizer = AutoTokenizer.from_pretrained(str(directory), local_files_only=True,
                                              trust_remote_code=False, use_fast=True, padding_side="right")
    before = (tokenizer.chat_template, tokenizer.eos_token_id, tokenizer.pad_token_id, tuple(tokenizer.all_special_ids))
    tokenizer._tokenizer = tokenizers.Tokenizer.from_str((directory / "tokenizer.json").read_text(encoding="utf-8"))
    _require(before == (tokenizer.chat_template, tokenizer.eos_token_id, tokenizer.pad_token_id,
                        tuple(tokenizer.all_special_ids)), "backend_restoration_changed_wrapper")
    _require(tokenizer.is_fast and tokenizer.padding_side == "right", "fast_right_padding_required")
    return tokenizer


def identifier_candidate(serial, salt):
    """Role-blind SHA256 stream; rejection before mod 26 avoids alphabet bias."""
    _require(type(serial) is int and 0 <= serial < IDENTIFIER_COUNT
             and type(salt) is int and 0 <= salt < 2**32, "identifier_index_or_salt_out_of_range")
    prefix = source.MATERIAL_MASTER + b"\0identifier\0" + serial.to_bytes(4, "big") + salt.to_bytes(4, "big")
    letters, block = [], 0
    while len(letters) < IDENTIFIER_WIDTH:
        for value in sha256(prefix + block.to_bytes(4, "big")).digest():
            if value < 234:
                letters.append(chr(97 + value % 26))
                if len(letters) == IDENTIFIER_WIDTH:
                    break
        block += 1
    return "".join(letters)


def allocate_identifiers(tokenizer, *, salt_limit, check=lambda: None):
    _require(type(salt_limit) is int and 1 <= salt_limit <= 2**32, "explicit_positive_salt_limit_required")
    identifiers, salts = [], []
    specials = set(tokenizer.all_special_ids)
    for serial in range(IDENTIFIER_COUNT):
        for salt in range(salt_limit):
            check()
            candidate = identifier_candidate(serial, salt)
            encoded = _encode(tokenizer, candidate)
            if len(encoded) == IDENTIFIER_TOKENS and not specials.intersection(encoded):
                _require(_decode(tokenizer, encoded) == candidate, "identifier_roundtrip_mismatch")
                _require(candidate not in identifiers, "identifier_collision_no_redraw")
                identifiers.append(candidate)
                salts.append(salt)
                break
        else:
            raise ValueError(f"identifier_salt_exhausted:{serial}")
    return tuple(identifiers), tuple(salts)


def _ordered(values, label):
    prefix = source.MATERIAL_MASTER + b"\0" + label.encode("ascii") + b"\0"
    return tuple(sorted(values, key=lambda value: (sha256(prefix + value.encode("ascii")).digest(), value)))


def _domain_roles(identifiers):
    pool = _ordered(identifiers, "domain-order")
    return (_ordered(pool[:48], "role-order/EVAL-MEM"),
            _ordered(pool[48:96], "role-order/PROMPT-ONLY"),
            _ordered(pool[96:], "role-order/JUNCTION-TRAIN"))


def _fact_assignment(roles, *, emit, solve):
    sources, middles, endpoints = roles[:16], roles[16:32], roles[32:]
    orders = tuple(_ordered(endpoints[index // 8 * 8:index // 8 * 8 + 8], f"display/EVAL-MEM/{index}")
                   for index in range(16))
    registry = nulls.build_null_registry(sources=sources, candidate_orders=orders, token_lengths=((8,) * 8,) * 16)
    emit("null_registry.json", asdict(registry))
    attempt = solve(registry, endpoint_ids=endpoints, expected_registry_sha256=registry.registry_sha256)
    receipt = dict(terminal_reason=attempt.terminal_reason, backend=attempt.backend,
                   registry_sha256=attempt.registry_sha256, assignment=attempt.assignment,
                   solution_sha256=attempt.solution_sha256, stats=attempt.stats,
                   error=None if attempt.error is None else str(attempt.error))
    emit("null_assignment.json", receipt)
    _require(attempt.terminal_reason == "source_solution" and attempt.assignment is not None,
             "fixed_null_assignment_failed_no_redraw")
    chains = tuple(source.Chain(sources[index], middles[index], endpoints[attempt.assignment[index]])
                   for index in range(16))
    return chains, orders, receipt


def _prompt_material(roles):
    chains = tuple(source.Chain(roles[index], roles[16 + index], roles[32 + index]) for index in range(16))
    orders = []
    for block in range(2):
        positions = tuple(int(value) for value in _ordered(tuple(map(str, range(8))), f"positions/PROMPT-ONLY/{block}"))
        for offset, position in enumerate(positions):
            index = block * 8 + offset
            endpoint = chains[index].endpoint
            others = _ordered(tuple(chain.endpoint for chain in chains[block * 8:block * 8 + 8]
                                    if chain.endpoint != endpoint), f"display/PROMPT-ONLY/{index}")
            orders.append(others[:position] + (endpoint,) + others[position:])
    return chains, tuple(orders)


@dataclass(frozen=True)
class EncodedRow:
    input_ids: tuple
    labels: tuple
    target_ids: tuple


def encode_training_row(messages, tokenizer, *, max_context):
    _require(type(max_context) is int and max_context > 0, "positive_context_limit_required")
    _require(type(messages) is list and len(messages) == 3
             and [message.get("role") for message in messages] == ["system", "user", "assistant"]
             and messages[0]["content"] == source.SYSTEM, "exact_training_roles_required")
    _require(all(type(message.get("content")) is str for message in messages), "message_text_required")
    target = messages[-1]["content"]
    _require(target.endswith("\n") and not target.endswith("\n\n"), "canonical_target_LF_required")
    eos, pad = tokenizer.eos_token_id, tokenizer.pad_token_id
    _require(type(eos) is int and type(pad) is int and tokenizer.padding_side == "right", "declared_eos_pad_required")
    context = tokenizer.apply_chat_template(messages[:2], tokenize=False, add_generation_prompt=True, return_dict=False)
    full = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False, return_dict=False)
    _require(full == context + target + tokenizer.eos_token + "\n", "exact_Qwen_template_boundary_required")
    context_ids, content_ids, suffix_ids = _encode(tokenizer, context), _encode(tokenizer, target), _encode(tokenizer, "\n")
    _require(not set(tokenizer.all_special_ids).intersection(content_ids), "assistant_special_token_injection")
    _require(_encode(tokenizer, tokenizer.eos_token) == (eos,), "terminal_EOT_encoding_mismatch")
    target_ids = content_ids + (eos,)
    sequence = _encode(tokenizer, full)
    _require(sequence == context_ids + target_ids + suffix_ids, "token_boundary_mismatch")
    templated = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=False,
                                               return_dict=False, truncation=False, padding=False)
    _require(tuple(templated) == sequence and _decode(tokenizer, sequence) == full, "template_roundtrip_mismatch")
    _require(len(sequence) <= max_context, "training_context_overflow_no_truncation")
    return EncodedRow(sequence, (-100,) * len(context_ids) + target_ids + (-100,) * len(suffix_ids), target_ids)


def _bind_canaries(evaluation, canaries, identifiers):
    if canaries is None:
        return evaluation
    _require(type(canaries) is list and len(canaries) == 16, "sixteen_caller_canaries_required")
    for canary in canaries:
        _require(type(canary) is dict and set(canary) == {"user", "expected"}, "canary_user_expected_required")
        for text in canary.values():
            _require(type(text) is str and text.isascii() and text.endswith("\n")
                     and not text.endswith("\n\n") and "\r" not in text, "canonical_canary_text_required")
            _require(not any(identifier in text for identifier in identifiers), "canary_material_identifier_overlap")
    calls = tuple(replace(call, user=canaries[call.slot.index]["user"],
                          expected=canaries[call.slot.index]["expected"].encode("ascii"))
                  if call.slot.panel == "canary" else call for call in evaluation.calls)
    return replace(evaluation, calls=calls)


def tokenizer_canary(tokenizer, *, salt_limit, max_context, check=lambda: None,
                     emit=lambda name, value: None):
    """Qualify the native identifier/mask interface without EVAL labels or models.

    Atomic smoke rows use JUNCTION-TRAIN identifiers only. No scored fact is
    assigned, no null solver is invoked, and this output is not a training file.
    """
    signature = tokenizer_signature(tokenizer)
    identifiers, salts = allocate_identifiers(tokenizer, salt_limit=salt_limit, check=check)
    emit("identifiers.json", dict(master=source.MATERIAL_MASTER.decode(), identifiers=identifiers,
                                   accepted_salts=salts, salt_limit=salt_limit, native_length=8))
    _, _, skill_roles = _domain_roles(identifiers)
    skills = tuple(source.Chain(skill_roles[index], skill_roles[32 + index], skill_roles[64 + index]) for index in range(32))
    skills, local_examples = source.build_matched_skills(skills)
    junction = tuple(source._junction_row(32 + index, chain) for index, chain in enumerate(skills))
    local = tuple(source._local_row(32 + index, example) for index, example in enumerate(local_examples))
    atomic = (source._atomic_row(0, skills[0].source, skills[0].middle),
              source._atomic_row(1, skills[0].middle, skills[0].endpoint))
    encoded, samples = {}, []
    for kind, rows in (("atomic_smoke", atomic), ("junction", junction), ("local", local)):
        encoded[kind] = []
        for row in rows:
            check()
            result = encode_training_row(row.messages(), tokenizer, max_context=max_context)
            encoded[kind].append(result)
            samples.append(dict(kind=kind, row_id=row.row_id, messages=row.messages(), encoded=asdict(result)))
    for start in range(0, 32, 4):
        _require(sum(len(row.target_ids) for row in encoded["junction"][start:start + 4])
                 == sum(len(row.target_ids) for row in encoded["local"][start:start + 4]),
                 "LOCAL_JUNCTION_batch_target_token_count_mismatch")
    emit("encoded_canary_rows.json", samples)
    return dict(schema=SCHEMA, status="TOKENIZER_CANARY_PASS", material_kind="TOKENIZER_CANARY_ONLY",
                tokenizer=signature, identifiers=192, identifier_width=16, identifier_tokens=8,
                maximum_accepted_salt=max(salts), encoded_rows=len(samples), model_calls=0, fits=0,
                max_sequence_tokens=max(len(row.input_ids) for rows in encoded.values() for row in rows),
                EVAL_relations_assigned=0, null_solver_calls=0,
                blocked_bindings=[{"code": "EVAL_NULL_ASSIGNMENT", "owner": "Dewey/Main"},
                                  {"code": "GENERIC_CANARY_BYTES", "owner": "Main"},
                                  {"code": "D1_TRAINING_MATERIAL", "next_command": "material"}])


def generate_material(tokenizer, *, salt_limit, max_context, canaries=None, check=lambda: None,
                      emit=lambda name, value: None, solve=None):
    """Native tokenizer + deterministic source/solver work only, never model loading.

    PROMPT-ONLY target positions use independently hash-ordered 0..7 per block;
    remaining candidates are hash-ordered. EVAL uses Dewey's fixed null solver.
    An injected solve is a CPU test seam and marks the material diagnostic.
    """
    signature = tokenizer_signature(tokenizer)
    identifiers, salts = allocate_identifiers(tokenizer, salt_limit=salt_limit, check=check)
    emit("identifiers.json", dict(master=source.MATERIAL_MASTER.decode(), identifiers=identifiers,
                                   accepted_salts=salts, salt_limit=salt_limit, native_length=8))
    fact_roles, prompt_roles, skill_roles = _domain_roles(identifiers)
    facts, candidates, solver_receipt = _fact_assignment(fact_roles, emit=emit, solve=solve or nulls.solve_assignment)
    prompts, prompt_candidates = _prompt_material(prompt_roles)
    skills = tuple(source.Chain(skill_roles[index], skill_roles[32 + index], skill_roles[64 + index]) for index in range(32))
    prepared = source.prepare_training(fact_chains=facts, junction_examples=skills)
    evaluation = source.prepare_evaluation(fact_chains=facts, permutation=source.SECOND_HOP_PERMUTATION,
                                            prompt_chains=prompts, fact_candidates=candidates, prompt_candidates=prompt_candidates)
    source.check_cross_corpus(prepared, evaluation)
    evaluation = _bind_canaries(evaluation, canaries, identifiers)
    encoded = {}
    for state in prepared.states:
        encoded[state.name] = []
        for row in state.rows:
            check()
            encoded[state.name].append(encode_training_row(row.messages(), tokenizer, max_context=max_context))
    for batch in prepared.states[0].batches:
        authentic = [token for row in batch for token in encoded["ATOM-JUNCTION"][row].target_ids]
        deranged = [token for row in batch for token in encoded["DERANGED-JUNCTION"][row].target_ids]
        local = [token for row in batch for token in encoded["ATOM-LOCAL"][row].target_ids]
        _require(Counter(authentic) == Counter(deranged), "coupled_batch_target_token_multiset_mismatch")
        _require(len(local) == len(authentic), "LOCAL_JUNCTION_batch_target_token_count_mismatch")
    kind = "NATIVE_TOKENIZER_MATERIAL" if solve is None else "DIAGNOSTIC_INJECTED_SOLVER"
    training = {}
    for state in prepared.states:
        training[state.name] = {**state.trainer_manifest(), "schema": SCHEMA, "material_kind": kind,
                                "tokenizer": signature, "max_context": max_context,
                                "encoded_rows": [asdict(row) for row in encoded[state.name]]}
    readouts = {state: dict(schema=SCHEMA, material_kind=kind, state=state, tokenizer=signature,
                           calls=[dict(slot=asdict(call.slot), user=call.user,
                                       expected=None if call.expected is None else call.expected.decode("ascii"))
                                  for call in evaluation.calls if call.slot.state == state]) for state in source.STATES}
    return dict(training=training, evaluation=readouts,
                summary=dict(schema=SCHEMA, material_kind=kind, model_calls=0, fits=0,
                             budget=source.build_d1_plan()["budget"], tokenizer=signature,
                             missing_canary_calls=sum(call.user is None for call in evaluation.calls),
                             blocked_bindings=[] if canaries is not None else [
                                 {"code": "GENERIC_CANARY_BYTES", "owner": "Main", "blocks": "learned_arm_readout"}],
                             solver=solver_receipt, tape_sha256=source.presentation_tape_sha256(source.build_presentation_tape())))


def validate_training_manifest(manifest, tokenizer, *, state, max_context):
    _require(state in source.STATES[1:] and manifest["state"] == state
             and manifest["schema"] == SCHEMA and manifest["material_kind"] in (
                 "NATIVE_TOKENIZER_MATERIAL", "PCHAIN2_FREE_ENDPOINT_DEV_V1"),
             "bound_native_training_state_required")
    _require(manifest["recipe"] == source.fit_recipe(state) and manifest["dose"] == "D1"
             and manifest["learner_seed"] == 0, "fixed_D1_recipe_required")
    _require(manifest["tokenizer"] == tokenizer_signature(tokenizer), "material_tokenizer_mismatch")
    tape = source.build_presentation_tape()[:384]
    _require(manifest["batches"] == [list(batch.row_ids) for batch in tape]
             and manifest["dropout_seeds"] == [batch.dropout_seed for batch in tape], "bound_tape_required")
    _require(len(manifest["rows"]) == len(manifest["encoded_rows"]) == 64
             and [row["row_id"] for row in manifest["rows"]] == list(range(64)), "exact_64_rows_required")
    rows = tuple(encode_training_row(row["messages"], tokenizer, max_context=max_context) for row in manifest["rows"])
    _require(json.loads(_json_bytes([asdict(row) for row in rows])) == manifest["encoded_rows"], "material_encoding_changed")
    return rows, tape


def validate_readout_manifest(manifest, tokenizer, *, state, max_context):
    _require(state in source.STATES and manifest["state"] == state and manifest["schema"] == SCHEMA
             and manifest["material_kind"] in ("NATIVE_TOKENIZER_MATERIAL", "PCHAIN2_FREE_ENDPOINT_DEV_V1"),
             "bound_native_readout_state_required")
    _require(manifest["tokenizer"] == tokenizer_signature(tokenizer), "material_tokenizer_mismatch")
    slots = [asdict(slot) for slot in source.d1_readout_slots() if slot.state == state]
    _require([call["slot"] for call in manifest["calls"]] == slots, "exact_state_readout_roster_required")
    prompts = []
    for call in manifest["calls"]:
        _require(type(call["user"]) is str and type(call["expected"]) is str, "bind_canaries_before_model_load")
        messages = [{"role": "system", "content": source.SYSTEM}, {"role": "user", "content": call["user"]}]
        ids = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True,
                                             return_dict=False, truncation=False, padding=False)
        _require(isinstance(ids, (tuple, list)) and all(type(value) is int for value in ids), "prompt_token_ids_required")
        _require(len(ids) + call["slot"]["max_new_tokens"] <= max_context, "readout_context_overflow")
        prompts.append(tuple(ids))
    return tuple(prompts)


def collate(rows, *, pad_id):
    _require(len(rows) == 4, "batch_four_required")
    width = max(len(row.input_ids) for row in rows)
    return dict(input_ids=[list(row.input_ids) + [pad_id] * (width - len(row.input_ids)) for row in rows],
                labels=[list(row.labels) + [-100] * (width - len(row.labels)) for row in rows],
                attention_mask=[[1] * len(row.input_ids) + [0] * (width - len(row.input_ids)) for row in rows])


class HFState:
    """One fresh model and (training only) one fresh optimizer per invocation."""

    def __init__(self, model_dir, *, state, device, training, adapter_dir=None, expected_base_sha256=None):
        import torch
        import transformers
        import peft

        self.torch, self.transformers, self.peft = torch, transformers, peft
        self.device, self.state, self.training = device, state, training
        self.optimizer = None
        self.completed_updates = 0
        torch.set_num_threads(1)
        if torch.get_num_interop_threads() != 1:
            torch.set_num_interop_threads(1)
        model = transformers.AutoModelForCausalLM.from_pretrained(
            str(Path(model_dir).resolve(strict=True)), local_files_only=True, trust_remote_code=False,
            use_safetensors=True, torch_dtype=torch.bfloat16, attn_implementation="sdpa", device_map=None)
        _require(model.config.model_type == "qwen2", "local_Qwen2_base_required")
        model.requires_grad_(False)
        self.base_state_sha256 = base_state_hash(model)
        if expected_base_sha256 is not None:
            _require(self.base_state_sha256 == expected_base_sha256, "retained_base_hash_mismatch")
        if training:
            _require(state in source.STATES[1:] and adapter_dir is None, "fresh_D1_training_required")
            torch.manual_seed(source.LEARNER_SEED)
            config = peft.LoraConfig(r=8, lora_alpha=16, lora_dropout=0.05, target_modules=list(TARGET_MODULES),
                                     bias="none", task_type="CAUSAL_LM", init_lora_weights=True,
                                     use_rslora=False, use_dora=False)
            model = peft.get_peft_model(model, config, autocast_adapter_dtype=True)
        elif state != "BASE":
            _require(adapter_dir is not None, "readout_adapter_required")
            config = peft.LoraConfig.from_pretrained(str(adapter_dir), local_files_only=True)
            _require(config.r == 8 and config.lora_alpha == 16 and config.lora_dropout == 0.05
                     and set(config.target_modules) == set(TARGET_MODULES), "readout_adapter_recipe_mismatch")
            model = peft.PeftModel.from_pretrained(model, str(adapter_dir), is_trainable=False,
                                                   local_files_only=True, autocast_adapter_dtype=True)
        else:
            _require(adapter_dir is None, "BASE_must_not_mount_adapter")
        self.model = model.to(device)
        self.parameters = [(name, parameter) for name, parameter in self.model.named_parameters() if parameter.requires_grad]
        if training:
            _require(bool(self.parameters) and all(".lora_A." in name or ".lora_B." in name for name, _ in self.parameters),
                     "only_LoRA_parameters_trainable")
            self.initial_adapter_sha256 = self.adapter_hash()
            self.model.config.use_cache = False
            self.model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
            self.model.enable_input_require_grads()
            self.model.train()
            self.optimizer = torch.optim.AdamW([parameter for _, parameter in self.parameters],
                                               lr=0.0 if state == "LR0" else 3e-5, **OPTIMIZER)
            if state == "LR0":
                self.require_zero_delta()
        else:
            self.model.eval()

    def adapter_hash(self):
        digest = sha256()
        for name, tensor in sorted(self.model.named_parameters()):
            if ".lora_A." in name or ".lora_B." in name:
                digest.update(_json_bytes([name, list(tensor.shape), str(tensor.dtype)]))
                digest.update(tensor.detach().cpu().contiguous().view(self.torch.uint8).numpy().tobytes())
        return digest.hexdigest()

    def require_zero_delta(self):
        parameters = dict(self.model.named_parameters())
        selected = [(name, tensor) for name, tensor in parameters.items() if ".lora_A." in name or ".lora_B." in name]
        _require(bool(selected), "LR0_adapter_missing")
        for name, tensor in selected:
            _require(bool(self.torch.isfinite(tensor).all().item()), "LR0_nonfinite_adapter")
            if ".lora_B." in name:
                _require(self.torch.count_nonzero(tensor).item() == 0, "LR0_nonzero_B")

    def train_step(self, batch, *, seed):
        torch = self.torch
        torch.manual_seed(seed)
        self.optimizer.zero_grad(set_to_none=True)
        tensors = {name: torch.tensor(value, dtype=torch.long, device=self.device) for name, value in batch.items()}
        loss = self.model(**tensors).loss
        value = float(loss.detach().item())
        _require(math.isfinite(value), "nonfinite_training_loss")
        loss.backward()
        self.optimizer.step()
        self.completed_updates += 1
        return value

    def save_training(self, output):
        for _, tensor in self.parameters:
            _require(bool(self.torch.isfinite(tensor).all().item()), "nonfinite_final_adapter")
        final_hash = self.adapter_hash()
        if self.state == "LR0":
            self.require_zero_delta()
            _require(final_hash == self.initial_adapter_sha256, "LR0_adapter_changed")
        self.model.save_pretrained(str(output / "adapter"), safe_serialization=True, save_embedding_layers=False)
        rng = dict(cpu=self.torch.get_rng_state())
        if str(self.device).startswith("cuda"):
            rng["cuda"] = self.torch.cuda.get_rng_state(self.device)
        self.torch.save(dict(schema=SCHEMA, state=self.state, completed_updates=self.completed_updates,
                             cursor=self.completed_updates * 4, optimizer=self.optimizer.state_dict(), rng=rng,
                             tape_sha256=source.presentation_tape_sha256(source.build_presentation_tape()),
                             base_state_sha256=self.base_state_sha256, numerical_binding=NUMERICAL_BINDING,
                             initial_adapter_sha256=self.initial_adapter_sha256, final_adapter_sha256=final_hash),
                        output / "training_state.pt")
        return dict(initial_adapter_sha256=self.initial_adapter_sha256, final_adapter_sha256=final_hash,
                    base_state_sha256=self.base_state_sha256, numerical_binding=NUMERICAL_BINDING,
                    lr0_zero_B_finite_A_verified=self.state == "LR0", runtime=dict(torch=self.torch.__version__,
                    transformers=self.transformers.__version__, peft=self.peft.__version__))

    def generate(self, prompt_ids, *, max_new_tokens, eos_token_id, pad_token_id):
        config = self.transformers.GenerationConfig(do_sample=False, num_beams=1, use_cache=True,
                    max_new_tokens=max_new_tokens, eos_token_id=eos_token_id, pad_token_id=pad_token_id,
                    repetition_penalty=1.0, return_dict_in_generate=False)
        inputs = self.torch.tensor([list(prompt_ids)], dtype=self.torch.long, device=self.device)
        with self.torch.inference_mode():
            output = self.model.generate(input_ids=inputs, attention_mask=self.torch.ones_like(inputs), generation_config=config)
        _require(output[0, :len(prompt_ids)].tolist() == list(prompt_ids), "generation_prefix_changed")
        return output[0, len(prompt_ids):].tolist()


def execute_training(manifest, rows, tape, engine, output, *, pad_id, check=lambda: None):
    """Exactly one D1 tape; neither held data nor a second model is accepted."""
    _require(len(rows) == 64 and tape == source.build_presentation_tape()[:384], "exact_D1_execution_tape_required")
    completed, target_tokens = 0, 0
    with (output / "training.jsonl").open("xb") as stream:
        try:
            for batch in tape:
                check()
                selected = tuple(rows[index] for index in batch.row_ids)
                started = time.monotonic()
                loss = engine.train_step(collate(selected, pad_id=pad_id), seed=batch.dropout_seed)
                _require(math.isfinite(loss), "nonfinite_training_loss")
                completed += 1
                target_tokens += sum(len(row.target_ids) for row in selected)
                stream.write(_json_bytes(dict(update=batch.update_number, row_ids=batch.row_ids, loss=loss,
                                               target_tokens=sum(len(row.target_ids) for row in selected),
                                               seconds=time.monotonic() - started)))
                stream.flush()
            _require(completed == 384, "incomplete_D1_tape")
            check()
            saved = engine.save_training(output)
            result = dict(schema=SCHEMA, status="D1_TRAINING_COMPLETE", state=manifest["state"],
                          updates=completed, presentations=completed * 4, target_tokens=target_tokens,
                          held_calls=0, checkpoint=saved)
            _write(output / "RESULT.json", result)
            return result
        except BaseException as error:
            _write(output / "FAILED.json", dict(state=manifest["state"], completed_updates=completed,
                                                error=repr(error), retried=False))
            raise


def execute_readout(manifest, prompts, tokenizer, engine, output, *, check=lambda: None):
    _require(len(prompts) == len(manifest["calls"])
             and [call["slot"] for call in manifest["calls"]] == [asdict(slot) for slot in source.d1_readout_slots()
                                                                if slot.state == manifest["state"]],
             "exact_readout_execution_roster_required")
    completed = 0
    with (output / "raw_readouts.jsonl").open("xb") as stream:
        try:
            for call, prompt in zip(manifest["calls"], prompts):
                check()
                started = time.monotonic()
                cap = call["slot"]["max_new_tokens"]
                ids = engine.generate(prompt, max_new_tokens=cap, eos_token_id=tokenizer.eos_token_id,
                                       pad_token_id=tokenizer.pad_token_id)
                _require(type(ids) is list and len(ids) <= cap and all(type(value) is int for value in ids),
                         "bounded_generated_ids_required")
                terminal = bool(ids) and ids[-1] == tokenizer.eos_token_id
                raw = _decode(tokenizer, ids[:-1] if terminal else ids).encode("utf-8")
                record = dict(slot=call["slot"], status="RAW", token_ids=ids, raw_utf8_hex=raw.hex(),
                              terminal=terminal, truncated=len(ids) == cap and not terminal,
                              seconds=time.monotonic() - started)
                stream.write(_json_bytes(record))
                stream.flush()
                completed += 1
            _require(completed == len(manifest["calls"]), "incomplete_readout_roster")
            result = dict(schema=SCHEMA, status="RAW_READOUT_COMPLETE", state=manifest["state"],
                          calls=completed, fits=0, scored=False,
                          base_state_sha256=getattr(engine, "base_state_sha256", None),
                          numerical_binding=NUMERICAL_BINDING)
            _write(output / "RESULT.json", result)
            return result
        except BaseException as error:
            for offset, call in enumerate(manifest["calls"][completed:]):
                stream.write(_json_bytes(dict(slot=call["slot"], status="ERROR" if offset == 0 else "NOT_RUN",
                                               error=repr(error) if offset == 0 else None)))
            stream.flush()
            _write(output / "FAILED.json", dict(state=manifest["state"], completed_calls=completed,
                                                error=repr(error), retried=False))
            raise


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("tokenizer-canary", "material", "train", "readout"):
        command = commands.add_parser(name)
        command.add_argument("--model-dir", required=True)
        command.add_argument("--output", required=True)
        command.add_argument("--max-context", required=True, type=int)
        command.add_argument("--deadline-seconds", required=True, type=float)
        if name in ("tokenizer-canary", "material"):
            command.add_argument("--salt-limit", required=True, type=int)
            if name == "material":
                command.add_argument("--canaries", help="JSON list of 16 {user, expected} objects; no default corpus")
        else:
            command.add_argument("--state", required=True, choices=source.STATES[1:] if name == "train" else source.STATES)
            command.add_argument("--device", required=True)
            command.add_argument("--expected-base-sha256", help="Retained Stage2A base hash; checked once before PEFT")
            command.add_argument("--training-file" if name == "train" else "--evaluation-file", required=True)
            if name == "readout":
                command.add_argument("--adapter-dir")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    _require(math.isfinite(args.deadline_seconds) and args.deadline_seconds > 0 and args.max_context > 0,
             "positive_finite_limits_required")
    started = time.monotonic()

    def check():
        if time.monotonic() - started >= args.deadline_seconds:
            raise TimeoutError("caller_deadline_exceeded")

    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    previous_handler = None
    previous_timer = None
    try:
        if args.command in ("tokenizer-canary", "material"):
            def expire(signum, frame):
                raise TimeoutError("caller_deadline_exceeded")

            previous_handler = signal.signal(signal.SIGALRM, expire)
            previous_timer = signal.setitimer(signal.ITIMER_REAL, args.deadline_seconds)
        _write(output / "REQUEST.json", dict(schema=SCHEMA, command=args.command, arguments=vars(args),
                                              numerical_binding=NUMERICAL_BINDING,
                                              source_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
                                              prepare_sha256=sha256(Path(source.__file__).read_bytes()).hexdigest(),
                                              nulls_sha256=sha256(Path(nulls.__file__).read_bytes()).hexdigest()))
        tokenizer = load_local_tokenizer(args.model_dir)
        check()
        if args.command == "tokenizer-canary":
            result = tokenizer_canary(tokenizer, salt_limit=args.salt_limit, max_context=args.max_context,
                                      check=check, emit=lambda name, value: _write(output / name, value))
            _write(output / "RESULT.json", result)
        elif args.command == "material":
            material = generate_material(tokenizer, salt_limit=args.salt_limit, max_context=args.max_context,
                                         canaries=None if args.canaries is None else _read(args.canaries), check=check,
                                         emit=lambda name, value: _write(output / name, value))
            for namespace in ("training", "evaluation"):
                (output / namespace).mkdir()
                for state, manifest in material[namespace].items():
                    _write(output / namespace / (state + ".json"), manifest)
            _write(output / "RESULT.json", material["summary"])
        elif args.command == "train":
            manifest = _read(args.training_file)
            rows, tape = validate_training_manifest(manifest, tokenizer, state=args.state, max_context=args.max_context)
            check()
            engine = HFState(args.model_dir, state=args.state, device=args.device, training=True,
                             expected_base_sha256=args.expected_base_sha256)
            execute_training(manifest, rows, tape, engine, output, pad_id=tokenizer.pad_token_id, check=check)
        else:
            manifest = _read(args.evaluation_file)
            prompts = validate_readout_manifest(manifest, tokenizer, state=args.state, max_context=args.max_context)
            check()
            engine = HFState(args.model_dir, state=args.state, device=args.device, training=False,
                             adapter_dir=args.adapter_dir, expected_base_sha256=args.expected_base_sha256)
            execute_readout(manifest, prompts, tokenizer, engine, output, check=check)
    except BaseException as error:
        if not (output / "FAILED.json").exists():
            _write(output / "FAILED.json", dict(error=repr(error), retried=False))
        raise
    finally:
        if previous_handler is not None:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, previous_handler)
            if previous_timer is not None and previous_timer[0] > 0:
                signal.setitimer(signal.ITIMER_REAL, max(0.000001, previous_timer[0] - (time.monotonic() - started)),
                                 previous_timer[1])


if __name__ == "__main__":
    main()
