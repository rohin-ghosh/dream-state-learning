"""Explicit single-DEV outcome SFT, never birth qualification or parenting.

Import is CPU/source-only. A complete, nonempty collector corpus must replay
exactly before native libraries load. Targets are only recorded successful model
outputs; neither witnesses nor teacher guidance enter student inputs. Successor
collections retain their own declared master/guidance and caller source label.
Main owns the training decision, GPU lease and external hard process timeout.
"""

import argparse
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import time

from gpu import astra_stage2a_native_models as models
from gpu import astra_stage2a_native_prepare as prepare
from gpu import astra_stage2a_native_tokenizer_receipt as tokens
from gpu import astra_stage2a_outcome_collect as collector
from organism_v6 import composition_birth_stage2a as wire
from organism_v6 import composition_birth_stage2a_actor as actor_api
from organism_v6 import composition_birth_stage2a_held as held_api
from organism_v6 import composition_birth_stage2a_rollout as rollout
from organism_v6 import composition_birth_stage2a_scoring as scoring
from organism_v6 import composition_birth_stage2a_screen_custody as custody
from organism_v6 import composition_birth_stage2a_screen_reduce as reducer
from organism_v6 import composition_birth_stage2a_screen_runtime as runtime
from organism_v6 import composition_birth_stage2a_tokenization as tokenization
from organism_v6 import composition_birth_stage2a_training as training
from organism_v6.pcfl_vertical_train import _state_hash


EVAL_MASTER = b"ASTRA-OUTCOME-EVAL-20260914-A1"
BASE_ID = "OUTCOME-BASE-20260914-A1"
FITTED_ID = "OUTCOME-SFT-20260914-A1"
CLAIM = "SINGLE_DEV_OUTCOME_SFT_NOT_BIRTH_QUALIFICATION_OR_AUTONOMOUS_PARENTING"
SEED, UPDATES, BATCH_SIZE, MAX_SECONDS = 0, 256, 4, 5400
MAX_FILE_BYTES = 256 * 1024 * 1024
MAX_CALLS = 32 * wire.CALL_CAP
require = collector.require


def _json_bytes(value):
    return json.dumps(collector.plain(value), sort_keys=True, ensure_ascii=True,
                      allow_nan=False, separators=(",", ":")).encode("ascii")


def _same(actual, expected, reason):
    require(_json_bytes(actual) == _json_bytes(expected), reason)


def _request(value):
    require(type(value) is dict and set(value) == {"prefix", "max_new_tokens", "seed", "context_tokens"},
            "recorded_request_required")
    require(type(value["prefix"]) is list and all(type(message) is dict
            and set(message) == {"role", "content"} and type(message["role"]) is str
            and type(message["content"]) is str for message in value["prefix"]), "recorded_messages_required")
    require(all(type(value[name]) is int for name in ("max_new_tokens", "seed", "context_tokens")),
            "integer_request_fields_required")
    return rollout.DecodeRequest(tuple(held_api.Message(**message) for message in value["prefix"]),
        value["max_new_tokens"], value["seed"], value["context_tokens"])


def _generation(value):
    require(type(value) is dict and set(value) == {
        "raw", "declared_tokens", "actual_tokens", "truncated", "finish_reason"}, "recorded_generation_required")
    require(type(value["raw"]) is str and type(value["finish_reason"]) is str
            and type(value["truncated"]) is bool
            and type(value["declared_tokens"]) is int and type(value["actual_tokens"]) is int,
            "typed_generation_fields_required")
    return rollout.Generation(**value)


def _student_prefix(prefix, guidance):
    require(type(prefix) is list and len(prefix) >= 2
            and prefix[0] == {"role": "system", "content": wire.SYSTEM_MESSAGE}
            and all(type(message) is dict and set(message) == {"role", "content"}
                    and type(message["content"]) is str for message in prefix)
            and all(message["role"] in ("user", "assistant") for message in prefix[1:]),
            "unassisted_student_prefix_required")
    require(all(not guidance or guidance not in message["content"] for message in prefix),
            "teacher_guidance_forbidden_in_student_prefix")


def collection_to_student_rows(*, result, episodes, calls, drafts, worlds, source_master, check=lambda phase: None):
    """Replay fixed collector schema with retained source master, never a model.

    All 32 episodes and calls are checked, including unsuccessful episodes.
    Return only byte-identical recorded DRAFT rows from re-scored successes.
    A source label is metadata, not evidence of authenticity; no substitute rows.
    """
    require(result.get("status") == "COLLECTION_COMPLETE_DRAFT_ONLY"
            and result.get("completed_episodes") == 32 and len(episodes) == 32,
            "complete_32_episode_collection_required")
    require(bool(drafts) and result.get("whole_chain_successes", 0) > 0, "nonempty_success_rows_required_no_fit")
    require(result.get("physical_calls") == len(calls) <= MAX_CALLS
            and result.get("draft_rows") == len(drafts) <= MAX_CALLS, "collection_counts_mismatch")
    guidance = result.get("guidance")
    require(type(guidance) is str and bool(guidance)
            and sha256(guidance.encode("utf-8")).hexdigest() == result.get("guidance_sha256"),
            "recorded_guidance_binding_required")
    require(result.get("master") == source_master.decode("ascii") and source_master != EVAL_MASTER,
            "source_master_must_differ_from_predeclared_eval")
    require(len(worlds) == 16 and tuple(world.world for world in worlds) == tuple(f"h{index:02d}" for index in range(16)),
            "all_16_source_worlds_required")
    selected, cursor, successes = [], 0, 0
    for episode, (world, member) in zip(episodes, ((world, member) for world in worlds for member in world.members)):
        check("collection_replay")
        require(episode.get("status") == "COMPLETED" and episode.get("error") is None
                and episode.get("split") == "TRAIN_ONLY" and episode.get("world") == world.world
                and episode.get("member") == member.member and episode.get("call_start") == cursor,
                "ordered_complete_source_episode_required")
        end = episode.get("call_end")
        require(type(end) is int and cursor < end <= len(calls) and end - cursor <= wire.CALL_CAP,
                "bounded_source_episode_calls_required")
        episode_calls = calls[cursor:end]
        prepared = []
        for index, call in enumerate(episode_calls, cursor):
            require(type(call.get("call_index")) is int and call["call_index"] == index
                    and call.get("error") is None and call.get("context_count_basis") == "ACTUAL_GUIDED_PREFIX",
                    "ordered_successful_source_call_required")
            request = _request(call["public_request"])
            guided = _request(call["guided_request"])
            generation = _generation(call["generation"])
            _student_prefix(collector.plain(request.prefix), guidance)
            expected_guided = rollout.DecodeRequest(
                (held_api.Message("system", wire.SYSTEM_MESSAGE + guidance),) + request.prefix[1:],
                request.max_new_tokens, request.seed, request.context_tokens)
            require(guided == expected_guided, "guided_public_request_mismatch")
            native = call.get("native")
            require(type(native) is dict and native.get("error") is None, "native_source_call_required")
            _same(native.get("request"), guided, "native_request_mismatch")
            _same(native.get("generation"), generation, "native_generation_mismatch")
            require(native.get("raw") == generation.raw
                    and native.get("raw_bytes") == {"bytes_hex": generation.raw.encode("utf-8").hex()},
                    "native_raw_source_mismatch")
            prepared.append((request, generation))
        position = 0

        def count_context(prefix):
            require(position < len(prepared) and prefix == prepared[position][0].prefix,
                    "source_public_prefix_replay_mismatch")
            return prepared[position][0].context_tokens

        def captured_actor(request):
            nonlocal position
            require(position < len(prepared) and request == prepared[position][0], "source_request_replay_mismatch")
            generation = prepared[position][1]
            position += 1
            return generation

        replayed = rollout.run_chain(world, member.member, actor=captured_actor,
            count_context=count_context, counter_provenance="ACTUAL_GUIDED_NATIVE_PREFIX", master=source_master, stage="D1")
        require(position == len(prepared), "source_calls_not_fully_replayed")
        _same(replayed, episode.get("run"), "source_driver_replay_mismatch")
        score = scoring.score_chain(replayed.attempts, member)
        _same(score, episode.get("score"), "recorded_success_score_mismatch")
        require(type(episode.get("selected")) is bool and episode["selected"] == score.whole_chain_success,
                "selected_success_mismatch")
        if score.whole_chain_success:
            successes += 1
            executed = [call for call in replayed.calls if call.disposition == "EXECUTED"]
            require(len(executed) == len(prepared) and all(call.attempt.accepted for call in executed),
                    "accepted_successful_calls_required")
            for call, (request, generation), source in zip(executed, prepared, episode_calls):
                require(call.raw_bytes == generation.raw.encode("utf-8") == call.attempt.capture.raw_bytes,
                        "actual_successful_source_action_required")
                selected.append(dict(status="DRAFT_NOT_RELEASED", episode_id=episode["episode_id"],
                    source_call_index=source["call_index"], prefix=collector.plain(request.prefix),
                    assistant=generation.raw, target_eot="<|im_end|>",
                    loss_policy=dict(prefix="MASK_ALL", assistant="TRAIN", eot="TRAIN")))
        cursor = end
    require(cursor == len(calls) and successes == result["whole_chain_successes"], "source_success_totals_mismatch")
    _same(selected, drafts, "draft_rows_must_equal_actual_successful_source_calls")
    require(bool(selected), "nonempty_success_rows_required_no_fit")
    return tuple(selected)


def load_collection(directory, *, source_label, check=lambda phase: None):
    require(type(source_label) is str and bool(source_label.strip()), "explicit_source_label_required")
    root, pins = Path(directory), {}

    def read(name, lines=False):
        check("read_collection:" + name)
        with (root / name).open("rb") as stream:
            raw = stream.read(MAX_FILE_BYTES + 1)
        require(len(raw) <= MAX_FILE_BYTES, "collection_file_bound_exceeded")
        pins[name] = sha256(raw).hexdigest()
        if lines:
            records = raw.splitlines()
            require(len(records) <= MAX_CALLS, "collection_row_bound_exceeded")
            return [json.loads(line) for line in records]
        return json.loads(raw)

    result = read("RESULT.json")
    require(result.get("status") == "COLLECTION_COMPLETE_DRAFT_ONLY"
            and result.get("whole_chain_successes", 0) > 0 and result.get("draft_rows", 0) > 0,
            "complete_nonempty_success_collection_required_no_fit")
    require(type(result.get("master")) is str and 0 < len(result["master"]) <= 4096,
            "bounded_recorded_source_master_required")
    source_master = result["master"].encode("ascii")
    require(source_master != EVAL_MASTER, "source_master_must_differ_from_predeclared_eval")
    request = read("REQUEST.json")
    episodes, calls, drafts = (read(name, lines=True) for name in
        ("EPISODES.jsonl", "CALLS.jsonl", "DRAFT_TRAINING_ROWS.jsonl"))
    allocation = prepare.allocate_source(master=source_master)
    require(result.get("allocation_sha256") == allocation.custody_sha256, "source_allocation_mismatch")
    worlds = held_api.build_chain_panel(role_tokens_by_world=allocation.role_tokens_by_world("dose_chain"))
    rows = collection_to_student_rows(result=result, episodes=episodes, calls=calls, drafts=drafts,
                                     worlds=worlds, source_master=source_master, check=check)
    return rows, dict(source_label=source_label, source_directory=str(root.absolute()), source_master=result["master"],
        source_claim=result.get("claim"), source_request=request, source_result=result, input_sha256=pins,
        rows_sha256=sha256(_json_bytes(rows)).hexdigest(), successful_rows=len(rows))


@dataclass(frozen=True)
class StudentRow:
    source_call_index: int
    input_ids: tuple
    labels: tuple
    attention_mask: tuple
    prefix_tokens: int
    target_tokens: int


def tokenize_rows(rows, tokenizer, *, guidance=None):
    """Unpaired rows; source-declared guidance excluded, assistant/EOT-only labels."""
    require(bool(rows), "nonempty_student_rows_required")
    eos, pad, eos_text, specials = tokenization._specials(tokenizer)
    require(eos_text == "<|im_end|>", "recorded_eot_must_match_tokenizer")
    tokenized = []
    for row in rows:
        _student_prefix(row["prefix"], guidance)
        require(row["target_eot"] == eos_text and row["loss_policy"] == {
            "prefix": "MASK_ALL", "assistant": "TRAIN", "eot": "TRAIN"}, "assistant_eot_only_policy_required")
        wire.parse_action(row["assistant"])
        prefix = tokenizer.apply_chat_template(row["prefix"], tokenize=False, add_generation_prompt=True)
        full = tokenizer.apply_chat_template(row["prefix"] + [{"role": "assistant", "content": row["assistant"]}],
                                             tokenize=False, add_generation_prompt=False)
        require(full == prefix + row["assistant"] + eos_text + "\n", "exact_unassisted_template_required")
        context = tokenization._encode(tokenizer, prefix, name="student_prefix")
        target = tokenization._encode(tokenizer, row["assistant"], name="student_assistant")
        suffix = tokenization._encode(tokenizer, "\n", name="student_suffix")
        require(not specials.intersection(target), "assistant_special_token_forbidden")
        sequence = context + target + (eos,) + suffix
        require(sequence == tokenization._encode(tokenizer, full, name="student_sequence")
                and len(sequence) <= tokenization.MAX_CONTEXT_TOKENS, "untruncated_exact_sequence_required")
        require(tuple(tokenizer.apply_chat_template(row["prefix"], tokenize=True,
                    add_generation_prompt=True, return_dict=False))
                == context, "student_template_token_ids_mismatch")
        labels = (-100,) * len(context) + target + (eos,) + (-100,) * len(suffix)
        tokenized.append(StudentRow(row["source_call_index"], sequence, labels, (1,) * len(sequence),
                                    len(context), len(target) + 1))
    return tuple(tokenized), pad


def cyclic_batch(rows, update_number, pad_token_id, *, outcome_row_count=None):
    require(bool(rows) and type(update_number) is int and 1 <= update_number <= UPDATES, "bounded_cyclic_update_required")
    indexes = tuple(((update_number - 1) * BATCH_SIZE + offset) % len(rows) for offset in range(BATCH_SIZE))
    if outcome_row_count is not None:
        from organism_v6.outcome_action_replay import scheduled_indexes

        indexes = scheduled_indexes(outcome_row_count, len(rows) - outcome_row_count, update_number)
    selected = tuple(rows[index] for index in indexes)
    width = max(len(row.input_ids) for row in selected)
    batch = {name: tuple(getattr(row, name) + (padding,) * (width - len(row.input_ids)) for row in selected)
             for name, padding in (("input_ids", pad_token_id), ("labels", -100), ("attention_mask", 0))}
    return indexes, selected, batch


def train_updates(model, rows, *, pad_token_id, torch, device, emit, check, outcome_row_count=None):
    """Exactly 256 actual batch-four AdamW updates, no paired-batch validator."""
    trainable = [parameter for parameter in model.parameters() if parameter.requires_grad]
    require(bool(trainable) and all(parameter.dtype == torch.float32 for parameter in trainable),
            "fp32_trainable_adapters_required")
    optimizer = torch.optim.AdamW(trainable, **dict(training.OPTIMIZER_RECIPE))
    torch.manual_seed(SEED)
    if torch.device(device).type == "cuda":
        torch.cuda.manual_seed_all(SEED)
    model.train()
    for update in range(1, UPDATES + 1):
        check("train_update")
        indexes, selected, batch = cyclic_batch(rows, update, pad_token_id, outcome_row_count=outcome_row_count)
        inputs = {name: torch.tensor(values, dtype=torch.long, device=device) for name, values in batch.items()}
        optimizer.zero_grad(set_to_none=True)
        with torch.autocast(device_type=torch.device(device).type, dtype=torch.bfloat16):
            output = model(**inputs, use_cache=False)
            loss = output.loss
        require(loss.ndim == 0 and loss.requires_grad and bool(torch.isfinite(loss)), "finite_scalar_training_loss_required")
        loss.backward()
        require(all(parameter.grad is not None and bool(torch.isfinite(parameter.grad).all()) for parameter in trainable),
                "finite_adapter_gradients_required")
        check("optimizer_step")
        optimizer.step()
        require(all(bool(torch.isfinite(parameter).all()) for parameter in trainable), "finite_adapter_weights_required")
        receipt = dict(update_number=update, loss=float(loss.detach().item()), row_indexes=indexes,
                  source_call_indexes=[row.source_call_index for row in selected],
                  supervised_tokens=sum(row.target_tokens for row in selected), batch_size=BATCH_SIZE, seed=SEED)
        if outcome_row_count is not None:
            receipt["source_kinds"] = ["OUTCOME" if index < outcome_row_count else "SOURCE_ACTION_COPY"
                                       for index in indexes]
            receipt["supervised_tokens_by_kind"] = {
                kind: sum(row.target_tokens for row, actual in zip(selected, receipt["source_kinds"]) if actual == kind)
                for kind in ("OUTCOME", "SOURCE_ACTION_COPY")}
        emit(receipt)
        del output, loss, inputs
    optimizer.zero_grad(set_to_none=True)


def initialize_student(base, *, torch, peft, directory, expected_base_sha256):
    """Stage2A rank-eight recipe with explicit seed zero, no dtype-wide cast."""
    require(not torch.cuda.is_initialized() and not hasattr(base, "peft_config"), "fresh_cpu_base_required")
    references = dict(base.state_dict(keep_vars=True))
    auxiliary = {name: value for name, value in base.named_buffers() if name not in references}
    require(base.config.model_type == "qwen2" and all(value.device.type == "cpu" for value in (references | auxiliary).values()),
            "cpu_qwen_base_required")
    require(_state_hash(references) == expected_base_sha256, "expected_frozen_base_hash_required")
    auxiliary_hash = _state_hash(auxiliary)
    base.requires_grad_(False)
    base.config.use_cache = False
    torch.manual_seed(SEED)
    config = peft.LoraConfig(r=8, lora_alpha=16, lora_dropout=0.05,
        target_modules=list(training.TARGET_MODULES), bias="none", task_type="CAUSAL_LM",
        init_lora_weights=True, use_rslora=False, use_dora=False)
    model = peft.get_peft_model(base, config, adapter_name="default", autocast_adapter_dtype=True)
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    observation = models.initial.inspect_initial_adapter(model, torch=torch,
        layer_count=model.config.num_hidden_layers, adapter_name="default")
    require(all(spec.dtype == "torch.float32" for spec in observation.trainable_roster), "fp32_adapter_storage_required")
    current = dict(model.named_parameters()) | dict(model.named_buffers())
    by_identity = {id(value): name for name, value in current.items()}
    require(all(id(value) in by_identity for value in (references | auxiliary).values()), "base_replaced_during_initialization")
    paths = {name: by_identity[id(value)] for name, value in references.items()}
    receipt = dict(expected_base_sha256=expected_base_sha256, auxiliary_base_sha256=auxiliary_hash,
        auxiliary_base_paths={name: by_identity[id(value)] for name, value in auxiliary.items()},
        seed=SEED, method="DEV_OUTCOME_SFT", observation=asdict(observation),
        auxiliary_dtypes={name: str(value.dtype) for name, value in auxiliary.items()})
    initialized = models.InitializedAtom(model, observation, references, paths, receipt, Path(directory))
    models.verify_retained_base(initialized, base_state_hash=_state_hash)
    require(not Path(directory).exists(), "fresh_initial_adapter_directory_required")
    model.save_pretrained(directory, safe_serialization=True)
    collector.write_json(Path(directory) / "INITIALIZATION.json", receipt)
    return initialized


def _evaluate(initialized, tokenizer, held, *, torch, directory, state_id, check):
    model = initialized.model
    model.eval()

    class BoundedActor(actor_api.ReadoutActor):
        def count_context(self, prefix):
            check("evaluation_context")
            return super().count_context(prefix)

        def __call__(self, request):
            check("evaluation_call")
            return super().__call__(request)

    actor = BoundedActor(model=model, tokenizer=tokenizer, torch=torch, device="cuda:0", count_basis=prepare.COUNT_BASIS)
    with custody.ScreenCustodySink(directory, torch=torch) as sink:
        run = runtime.run_reduced_state(state_id=state_id, stage="D1", master=EVAL_MASTER,
            chains=held.chains, interventions=held.interventions, canaries=held.canaries, actor=actor,
            actor_calls=actor.calls, count_context=actor.count_context, counter_provenance=prepare.COUNT_BASIS,
            custody_sink=sink)
    require(not run.failures and run.terminal_reason == "completed_unscored" and len(run.reservations) == 280,
            "complete_280_slot_evaluation_required")
    verified = custody.verify_receipt(directory)
    require((verified.state_id, verified.stage, verified.terminal_reason) == (state_id, "D1", run.terminal_reason),
            "evaluation_custody_binding_mismatch")
    return run


def run(options, *, libraries=None, clock=time.time):
    started = clock()

    def check(phase):
        require(type(options.deadline_unix) in (int, float) and math.isfinite(options.deadline_unix)
                and clock() < options.deadline_unix <= started + MAX_SECONDS, "finite_max_5400s_deadline:" + phase)

    check("request")
    root = Path(options.output)
    require(not root.resolve().is_relative_to(Path(options.collection).resolve()), "output_outside_collection_required")
    root.mkdir(exist_ok=False)
    summary = dict(status="INCOMPLETE", claim=CLAIM, source_label=options.source_label,
        started_unix=started, seed=SEED, planned_updates=UPDATES, completed_updates=0, batch_size=BATCH_SIZE,
        master_hex=EVAL_MASTER.hex(), base_state_id=BASE_ID, fitted_state_id=FITTED_ID, frozen_base_hashes={})
    hooks = []
    try:
        collector.write_json(root / "REQUEST.json", dict(vars(options), master_hex=EVAL_MASTER.hex(),
            base_state_id=BASE_ID, atom_state_id=FITTED_ID, method=CLAIM))
        rows, provenance = load_collection(options.collection, source_label=options.source_label, check=check)
        summary["collection"] = provenance
        collector.write_json(root / "COLLECTION_RECHECK.json", provenance)
        outcome_row_count = None
        if getattr(options, "source_action_copy_replay", False):
            from organism_v6.outcome_action_replay import compile_copy_rows

            outcome_row_count = len(rows)
            copy_rows, replay = compile_copy_rows(rows)
            rows = tuple(rows) + tuple(copy_rows)
            summary["source_action_copy_replay"] = replay
            collector.write_json(root / "SOURCE_ACTION_COPY_REPLAY.json", replay)
        summary["training_rows_sha256"] = sha256(_json_bytes(rows)).hexdigest()
        with (root / "STUDENT_ROWS.jsonl").open("x") as stream:
            for row in rows:
                collector.append_json(stream, row)
        require(training._sha(options.expected_base_sha256)
                and provenance["source_result"].get("base_pre") == options.expected_base_sha256
                and provenance["source_result"].get("base_post") == options.expected_base_sha256,
                "collector_and_student_frozen_base_binding_required")
        require(type(options.gpu_uuid) is str and options.gpu_uuid.startswith("GPU-") and "," not in options.gpu_uuid
                and os.environ.get("CUDA_VISIBLE_DEVICES") == options.gpu_uuid, "one_explicit_gpu_required")
        check("native_imports")
        if libraries is None:
            import torch
            import peft
            import transformers
        else:
            torch, peft, transformers = libraries
        require(all(str(library.__version__) == tokens.RUNTIME_VERSIONS[name]
                    for name, library in (("torch", torch), ("peft", peft), ("transformers", transformers))),
                "native_runtime_changed")
        require(not torch.cuda.is_initialized(), "fresh_exclusive_process_required")
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
        eval_held = prepare.prepare_reduced_held(bound_allocation=prepare.allocate_source(master=EVAL_MASTER))
        summary["eval_held_sha256"] = eval_held.receipt_sha256
        official_path = Path(tokens.__file__).resolve().parents[1] / (
            "research_notes/astra_memos/receipts_20260912/astra_qwen_public_binding_receipt_20260913_attempt1.json")
        official_raw = official_path.read_bytes()
        require(sha256(official_raw).hexdigest() == tokens.OFFICIAL_RECEIPT_SHA256, "official_tokenizer_receipt_changed")
        check("tokenizer")
        tokenizer = transformers.AutoTokenizer.from_pretrained(options.model_dir,
            local_files_only=True, trust_remote_code=False, use_fast=True, padding_side="right")
        summary["tokenizer"] = tokens.restore_official_backend(tokenizer, options.model_dir,
            json.loads(official_raw)["files"], root / "backend")
        tokenized, pad = tokenize_rows(rows, tokenizer, guidance=provenance["source_result"]["guidance"])
        collector.write_json(root / "MASK_RECEIPT.json", [dict(source_call_index=row.source_call_index,
            prefix_tokens=row.prefix_tokens, supervised_tokens=row.target_tokens,
            input_sha256=sha256(_json_bytes(row.input_ids)).hexdigest(),
            labels_sha256=sha256(_json_bytes(row.labels)).hexdigest()) for row in tokenized])
        check("base_load")
        base = transformers.AutoModelForCausalLM.from_pretrained(options.model_dir,
            local_files_only=True, trust_remote_code=False, torch_dtype=torch.bfloat16,
            device_map=None, attn_implementation="sdpa", use_safetensors=True)
        initialized = initialize_student(base, torch=torch, peft=peft, directory=root / "initial",
                                         expected_base_sha256=options.expected_base_sha256)
        model, roster = initialized.model, initialized.observation.trainable_roster
        check("placement")
        torch.cuda.init()
        require(torch.cuda.device_count() == 1, "exactly_one_visible_gpu_required")
        properties = torch.cuda.get_device_properties(0)
        require("A100" in properties.name and properties.total_memory >= 75 * 1024 ** 3, "A100_80GB_expected")
        summary["device"] = dict(name=properties.name, total_memory=properties.total_memory, uuid=options.gpu_uuid)
        model.to("cuda:0")
        hooks.append(model.register_forward_pre_hook(lambda module, inputs: check("forward")))

        def hash_base(label):
            check("frozen_base_hash:" + label)
            summary["frozen_base_hashes"][label] = models.verify_retained_base(initialized, base_state_hash=_state_hash)
            collector.write_json(root / ("BASE_HASH_" + label + ".json"), summary["frozen_base_hashes"])

        hash_base("before_training")
        training._validate_model(model, roster, initialized.observation.layer_count, "default")
        with (root / "LOSSES.jsonl").open("x") as stream:
            def emit(receipt):
                collector.append_json(stream, receipt)
                summary["completed_updates"] = receipt["update_number"]

            train_updates(model, tokenized, pad_token_id=pad, torch=torch, device="cuda:0", emit=emit, check=check,
                          outcome_row_count=outcome_row_count)
        require(summary["completed_updates"] == UPDATES, "exact_256_completed_updates_required")
        hash_base("after_training")
        check("adapter_checkpoint_before_evaluation")
        adapter_hash = training.adapter_sha256(model, roster)
        adapter_dir = root / "adapter"
        model.save_pretrained(adapter_dir, safe_serialization=True)
        summary["adapter_sha256"] = adapter_hash
        summary["adapter_files_sha256"] = {path.name: models._file_hash(path) for path in adapter_dir.iterdir() if path.is_file()}
        require({"adapter_model.safetensors", "adapter_config.json"} <= set(summary["adapter_files_sha256"])
                and (adapter_dir / "adapter_model.safetensors").stat().st_size > 0, "saved_peft_adapter_required")
        collector.write_json(adapter_dir / "TRAINING.json", dict(claim=CLAIM, completed_updates=UPDATES,
            seed=SEED, batch_size=BATCH_SIZE, optimizer=dict(training.OPTIMIZER_RECIPE),
            rows_sha256=summary["training_rows_sha256"], source_label=options.source_label,
            adapter_sha256=adapter_hash, files_sha256=summary["adapter_files_sha256"],
            checkpoint_kind="PEFT_ADAPTER_ONLY_NOT_FULL_RESUME_STATE"))
        model.eval()
        check("base_evaluation")
        with model.disable_adapter():
            baseline = _evaluate(initialized, tokenizer, eval_held, torch=torch,
                directory=root / "BASE", state_id=BASE_ID, check=check)
        hash_base("after_base_evaluation")
        require(training.adapter_sha256(model, roster) == adapter_hash, "base_readout_changed_adapter")
        fitted = _evaluate(initialized, tokenizer, eval_held, torch=torch,
            directory=root / "FITTED", state_id=FITTED_ID, check=check)
        hash_base("after_fitted_evaluation")
        require(training.adapter_sha256(model, roster) == adapter_hash, "fitted_readout_changed_adapter")
        reduced = reducer.reduce_base_d1(base=baseline, atom_local=fitted, base_state_id=BASE_ID,
            atom_local_state_id=FITTED_ID, master=EVAL_MASTER, chains=eval_held.chains,
            interventions=eval_held.interventions, canaries=eval_held.canaries)
        summary.update(reportable=reduced.reportable, criteria_passed=reduced.criteria_passed,
            criteria=[dict(asdict(item), passed=item.passed) for item in reduced.criteria],
            screens={label: dict(accounting=asdict(state.accounting), issues=state.issues,
                metrics=None if state.metrics is None else {name: getattr(state.metrics, name) for name in (
                    "skill_pairs", "typed_interventions", "whole_chains", "useful_reads", "typed_steps", "canaries")})
                for label, state in (("BASE", reduced.base), ("FITTED", reduced.atom_local))})
        require(reduced.reportable, "outcome_screen_reduction_not_reportable")
        check("result")
        summary.update(status="DEV_OUTCOME_SFT_COMPLETE", finished_unix=clock())
        collector.write_json(root / "RESULT.json", summary)
        return summary
    except BaseException as error:
        summary.update(status="FAILED_NO_COMPLETION", error_type=type(error).__name__, error=str(error), finished_unix=clock())
        collector.write_json(root / "FAILED.json", summary)
        raise
    finally:
        for hook in hooks:
            hook.remove()


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("collection", "source-label", "model-dir", "output", "gpu-uuid", "expected-base-sha256"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--deadline-unix", required=True, type=float)
    parser.add_argument("--source-action-copy-replay", action="store_true")
    return parser.parse_args(argv)


if __name__ == "__main__":
    run(parse_args())
