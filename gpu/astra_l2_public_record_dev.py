"""Bounded PROMOTE/SHADOW DEV runtime; only Main authorizes native execution.

Preparation imports caller-pinned, final snapshot code, never the working core.
Worker processes own models/optimizers; collection alone scores report captures.
CPU fixtures exercise orchestration, not native certification or scientific proof.
"""
from __future__ import annotations

import argparse
from collections.abc import Mapping
import contextlib
from dataclasses import asdict
import hashlib
import importlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time


SCHEMA = "astra_l2_public_record_runtime_v1"
POLICIES = ("PROMOTE", "SHADOW")
STAGES = ("baseline", "wake1", "fit1", "report1_PROMOTE", "report1_SHADOW",
          "wake2_PROMOTE", "wake2_SHADOW", "fit2_PROMOTE", "fit2_SHADOW",
          "report2_PROMOTE", "report2_SHADOW")
SOURCE_NAMES = ("organism_v6/__init__.py", "organism_v6/l2_public_record_dev.py",
                "organism_v6/train_adapter_v3.py", "gpu/astra_l2_public_record_dev.py")
SELF = Path(__file__).resolve()
SEEDS = dict(vocabulary=2026091301, truth=2026091302, learner=0)
OUTER_SECONDS, CLEANUP_SECONDS, COLLECTION_SECONDS = 5400, 40, 180
FIT_SECONDS, INFERENCE_SECONDS, LEASE_MARGIN = 600, 300, 21600
CAPS = dict(calls=128, fits=3, updates=100)
GENERIC_SYSTEM = "You are a helpful assistant."
RECIPE = dict(rank=8, alpha=16, dropout=.05, lr=3e-5, epochs=20, max_len=1024,
              seed=0, overflow="truncate", batch_size=8, grad_accum=1, pack=False,
              shuffle_groups=True, chat_template=False, add_eos=False, optimizer="adamw",
              grad_checkpoint=True, device="cuda", dtype="bf16", max_steps=0,
              layers="all", svd_init=False, freeze_a=False, split_overlap_tokens=0,
              target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
              note=SCHEMA + "; exact child target plus EOS; no actual truncation")
ENGINE = dict(max_model_len=16384, tensor_parallel_size=1, seed=0,
              gpu_memory_utilization=.85, enforce_eager=True, enable_lora=True,
              max_lora_rank=32, enable_prefix_caching=False, dtype="bfloat16", trust_remote_code=False)
PARAMS = dict(temperature=0.0, seed=0, max_tokens=32, top_p=1.0, top_k=-1, n=1,
              presence_penalty=0.0, frequency_penalty=0.0, repetition_penalty=1.0, ignore_eos=False)
CLAIM = "Exploratory public-record DEV pair; no birth, parenting, H1/H2 or clean-ancestry qualification."
WITNESSES = {"SEAL.json", "FINALIZED.json", "FINALIZATION_ABORT.json"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False,
                       separators=(",", ":")) + "\n").encode("ascii")


def value_hash(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def digest(path):
    checksum = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            checksum.update(block)
    return checksum.hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON field")
        result[key] = value
    return result


def read(path):
    return json.loads(Path(path).read_text(), object_pairs_hook=unique_object,
                      parse_constant=lambda value: require(False, "nonfinite JSON"))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(encoded(value))
        stream.flush()
        os.fsync(stream.fileno())
    descriptor = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def pin(value):
    require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value), "invalid SHA256")
    return value


def plain_path(value):
    path = Path(value)
    require(path.is_absolute() and ".." not in path.parts, "absolute plain path required")
    require(not any(part.is_symlink() for part in (path, *path.parents)), "symlink path forbidden")
    return path


def tree(directory):
    directory = plain_path(str(directory))
    require(directory.is_dir(), "missing directory")
    files = {}
    for path in sorted(directory.rglob("*")):
        require(not path.is_symlink(), "linked artifact forbidden")
        require(path.is_dir() or path.is_file(), "special artifact forbidden")
        if path.is_file():
            require(path.stat().st_nlink == 1, "hardlinked artifact forbidden")
            files[path.relative_to(directory).as_posix()] = digest(path)
    return files


def checked_file(record):
    require(set(record) == {"path", "sha256"}, "file binding schema")
    path = plain_path(record["path"])
    require(path.is_file() and digest(path) == pin(record["sha256"]), "file pin differs: " + str(path))
    return path


def offline():
    sys.dont_write_bytecode = True
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_DATASETS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false", WANDB_DISABLED="true")


def launcher_output_outside(root):
    for descriptor in (1, 2):
        descriptor_path = Path(f"/proc/self/fd/{descriptor}")
        if descriptor_path.exists():
            target = os.readlink(descriptor_path)
            if target.startswith("/"):
                require(not Path(target).resolve().is_relative_to(Path(root).resolve()),
                        "launcher stdout/stderr must remain outside the sealed root")


@contextlib.contextmanager
def budget(seconds):
    require(seconds > 0, "deadline exhausted")
    def expired(signum, frame):
        raise TimeoutError("L2 bounded deadline exceeded")
    previous = signal.signal(signal.SIGALRM, expired)
    timer = signal.getitimer(signal.ITIMER_REAL)
    started = time.monotonic()
    signal.setitimer(signal.ITIMER_REAL, min(seconds, timer[0]) if timer[0] else seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
        if timer[0]:
            signal.setitimer(signal.ITIMER_REAL, max(.001, timer[0] - (time.monotonic() - started)), timer[1])


@contextlib.contextmanager
def release_budget(deadline):
    timer = signal.setitimer(signal.ITIMER_REAL, 0)
    started = time.monotonic()
    previous = {kind: signal.signal(kind, signal.SIG_IGN) for kind in (signal.SIGTERM, signal.SIGINT)}
    try:
        with budget(min(CLEANUP_SECONDS, max(.001, deadline - time.monotonic()))):
            yield
    finally:
        for kind, handler in previous.items():
            signal.signal(kind, handler)
        if timer[0]:
            signal.setitimer(signal.ITIMER_REAL, max(.001, timer[0] - (time.monotonic() - started)), timer[1])


def validate_spec(spec):
    require(set(spec) == {"schema", "source", "source_files", "core_schema", "helpers", "model",
                          "model_binding", "protocol", "gpu_uuid", "gpu_index", "lease_end"}, "spec fields")
    require(spec["schema"] == SCHEMA and isinstance(spec["core_schema"], str), "spec/core schema")
    source = plain_path(spec["source"])
    require(not (source / ".git").exists(), "fresh source snapshot, not a checkout")
    require(set(spec["source_files"]) == set(SOURCE_NAMES), "exact four-file final source inventory required")
    for checksum in spec["source_files"].values():
        pin(checksum)
    require(tree(source) == spec["source_files"], "fresh source snapshot inventory differs")
    require(digest(SELF) == spec["source_files"]["gpu/astra_l2_public_record_dev.py"], "running runtime differs")
    require(set(spec["helpers"]) == {"reflection", "public"}, "two final helper pins required")
    for record in spec["helpers"].values():
        checked_file(record)
    checked_file(spec["model_binding"])
    checked_file(spec["protocol"])
    plain_path(spec["model"])
    require(not source.is_relative_to(Path(spec["model"])) and not Path(spec["model"]).is_relative_to(source),
            "source/model must be disjoint")
    require(type(spec["gpu_index"]) is int and spec["gpu_index"] >= 0 and
            isinstance(spec["gpu_uuid"], str) and spec["gpu_uuid"].startswith("GPU-"), "GPU binding")
    require(type(spec["lease_end"]) in (int, float) and math.isfinite(spec["lease_end"]), "lease timestamp")


def load_apis(spec):
    validate_spec(spec)
    source = Path(spec["source"])
    for name, module in tuple(sys.modules.items()):
        if name == "organism_v6" or name.startswith("organism_v6."):
            require(getattr(module, "__file__", None) and
                    Path(module.__file__).resolve().is_relative_to(source), "cached non-snapshot core/trainer")
    sys.path.insert(0, str(source))
    core = importlib.import_module("organism_v6.l2_public_record_dev")
    trainer = importlib.import_module("organism_v6.train_adapter_v3")
    require(core.SCHEMA == spec["core_schema"], "final core schema differs")
    helpers = {}
    for name, record in spec["helpers"].items():
        module_spec = importlib.util.spec_from_file_location("_l2_pinned_" + name, record["path"])
        module = importlib.util.module_from_spec(module_spec)
        sys.modules[module_spec.name] = module
        module_spec.loader.exec_module(module)
        helpers[name] = module
    return core, trainer, helpers["public"], helpers["reflection"]


def messages(prompt):
    return [dict(role="system", content=GENERIC_SYSTEM), dict(role="user", content=prompt)]


def prepare(spec_path, spec_sha256, root, allow_native=False):
    require(allow_native, "prepare requires Main's --allow-native (local tokenizer only)")
    offline()
    spec_path = checked_file(dict(path=str(Path(spec_path).absolute()), sha256=spec_sha256))
    spec = read(spec_path)
    validate_spec(spec)
    root = plain_path(str(Path(root).absolute()))
    launcher_output_outside(root)
    for other in (spec["source"], spec["model"], *[entry["path"] for entry in spec["helpers"].values()], str(spec_path)):
        other = Path(other)
        require(not root.is_relative_to(other) and not other.is_relative_to(root), "root must be disjoint")
    require(time.time() + OUTER_SECONDS + COLLECTION_SECONDS + LEASE_MARGIN <= spec["lease_end"], "lease margin")
    root.mkdir()
    write(root / "prepare_started.json", dict(time=time.time(), spec_sha256=spec_sha256))
    try:
        core, trainer, probe, reflection = load_apis(spec)
        receipt = read(spec["model_binding"]["path"])
        model_files = probe.public_model_files(receipt, spec["model"])
        require(model_files == probe.model_hashes(spec["model"]), "local model differs from public binding")
        tokenizer = probe.native_tokenizer(spec["model"])
        world = core.build_world(SEEDS["vocabulary"], SEEDS["truth"])
        public = core.public_view(world)
        calls = {view: [dict(slot_id=slot.slot_id, messages=messages(core.action_prompt(public, slot.slot_id, view=view)),
                             native=probe.render(tokenizer, messages(core.action_prompt(public, slot.slot_id, view=view))))
                        for slot in public.slots] for view in ("wake", "readout", "train")}
        require(all(call["native"]["actual_system_text"] == GENERIC_SYSTEM
                    for entries in calls.values() for call in entries), "generic system drift")
        write(root / "calls.json", calls)
        write(root / "world.json", core.to_data(world))
        write(root / "model_binding.json", receipt)
        config = asdict(trainer.TrainConfig(**RECIPE, model=spec["model"]))
        plan = dict(schema=SCHEMA, spec=spec, spec_sha256=spec_sha256, root=str(root),
                    python=os.path.abspath(sys.executable), python_sha256=digest(sys.executable),
                    model_files=model_files, base_sha256=value_hash(model_files), seeds=SEEDS,
                    config=config, engine=ENGINE, params=PARAMS, stages=list(STAGES), caps=CAPS,
                    generic_system=GENERIC_SYSTEM, chat_template=tokenizer.chat_template,
                    environment=reflection.environment(probe), claim=CLAIM,
                    prepared_files={name: digest(root / name) for name in ("calls.json", "world.json", "model_binding.json")})
        write(root / "plan.json", plan)
        return dict(root=str(root), plan_sha256=digest(root / "plan.json"), schema=SCHEMA)
    except BaseException as error:
        write(root / "prepare_failure.json", failure(error))
        raise


def verify(root, plan_sha256, native=False):
    root = plain_path(str(Path(root).absolute()))
    require(digest(root / "plan.json") == pin(plan_sha256), "prepared manifest pin differs")
    plan = read(root / "plan.json")
    require(plan["schema"] == SCHEMA and plan["root"] == str(root), "prepared root/schema")
    require(plan["seeds"] == SEEDS and plan["engine"] == ENGINE and plan["params"] == PARAMS and
            plan["stages"] == list(STAGES) and plan["caps"] == CAPS and
            plan["generic_system"] == GENERIC_SYSTEM, "closed configuration differs")
    for name, checksum in plan["prepared_files"].items():
        require(name in ("calls.json", "world.json", "model_binding.json") and digest(root / name) == checksum,
                "prepared artifact drift")
    require(set(plan["prepared_files"]) == {"calls.json", "world.json", "model_binding.json"}, "prepared inventory")
    core, trainer, probe, reflection = load_apis(plan["spec"])
    require(plan["config"] == asdict(trainer.TrainConfig(**RECIPE, model=plan["spec"]["model"])), "fit recipe differs")
    require(plan["python"] == os.path.abspath(sys.executable) and plan["python_sha256"] == digest(sys.executable),
            "interpreter differs")
    require(plan["base_sha256"] == value_hash(plan["model_files"]), "base identity differs")
    world = core.from_data(read(root / "world.json"), expected_type=core.World)
    require(world == core.build_world(SEEDS["vocabulary"], SEEDS["truth"]), "world seeds differ")
    if native:
        require(probe.model_hashes(plan["spec"]["model"]) == plan["model_files"], "model drift")
        require(reflection.environment(probe) == plan["environment"], "native environment drift")
    return plan, core, trainer, probe, reflection, world


def failure(error):
    return dict(type=type(error).__name__, message=str(error), time=time.time())


def stage_dir(plan, stage):
    require(stage in STAGES, "unknown stage")
    return Path(plan["root"]) / "run" / stage


def read_stage(plan, stage):
    directory = stage_dir(plan, stage)
    closed = read(directory / "CLOSED.json")
    require(closed["stage"] == stage and closed["files"] == tree(directory / "data"), "stage custody differs")
    result = read(directory / "data/result.json")
    require(result["stage"] == stage and result["calls"] >= 0 and result["fits"] >= 0 and result["updates"] >= 0,
            "stage result identity/work")
    return result


def sequence(stage, ordinal):
    return (STAGES.index(stage) + 1) * 1000 + ordinal


def legal_action(public, raw):
    return next((action for action in public.actions if raw in (action.encode("ascii"), action.encode("ascii") + b"\n")), None)


def capture_from_data(core, public, payload):
    capture = core.from_data(payload, expected_type=core.CapturedBlock)
    rebuilt = core.capture_block(public, capture.block, capture.lineage, capture.episodes)
    require(capture == rebuilt, "capture reconstruction differs")
    return capture


def advance(core, public, states, stage, result):
    if stage.startswith("wake"):
        capture = capture_from_data(core, public, result["capture"])
        policies = POLICIES if stage == "wake1" else (stage.split("_")[1],)
        for policy in policies:
            states[policy] = core.close_block(public, states[policy], capture, expected_sha256=core.digest(capture))
    elif stage.startswith("fit"):
        policies = POLICIES if stage == "fit1" else (stage.split("_")[1],)
        for policy in policies:
            state = states[policy]
            require(result["corpus_sha256"] == core.digest(state.corpus), "fit corpus differs")
            require(result["initialized_from_sha256"] == state.base_sha256, "fit not base initialized")
            states[policy] = core.complete_sleep(public, state, corpus_sha256=result["corpus_sha256"],
                                                candidate_sha256=result["candidate_sha256"],
                                                initialized_from_sha256=result["initialized_from_sha256"])
    core.check_pair(public, states)


def dependency_states(plan, core, world, before_stage, reader=read_stage):
    public = core.public_view(world)
    states = core.start_pair(public, plan["base_sha256"])
    for prior in STAGES[:STAGES.index(before_stage)]:
        if prior.startswith(("wake", "fit")):
            advance(core, public, states, prior, reader(plan, prior))
    return states


def route_for(plan, core, states, stage, reader=read_stage):
    policy = stage.split("_")[1] if "_" in stage else "SHADOW"
    expected = core.routing(states[policy])["requested_artifact_sha256"]
    if policy == "SHADOW" or expected == plan["base_sha256"]:
        require(expected == plan["base_sha256"], "SHADOW attempted candidate mount")
        return None
    for fit in ("fit2_PROMOTE", "fit1"):
        if STAGES.index(fit) < STAGES.index(stage):
            result = reader(plan, fit)
            if result["candidate_sha256"] == expected:
                adapter = stage_dir(plan, fit) / "data/adapter"
                require(tree(adapter) == result["candidate_files"] and value_hash(result["candidate_files"]) == expected,
                        "mounted candidate drift")
                return dict(name="l2_public_record", id=1, path=str(adapter), sha256=expected)
    raise ValueError("mounted candidate unavailable")


def token_ids(value):
    if isinstance(value, Mapping):
        value = value.get("input_ids")
    require(isinstance(value, (list, tuple)) and all(type(token) is int and token >= 0 for token in value), "token vector")
    return list(value)


def encode_training(core, public, corpus, tokenizer, trainer, probe):
    require(corpus.kind == "AUTHENTIC" and 1 <= len(corpus.rows) <= 16, "authentic nonempty bounded corpus")
    exports = core.training_items(public, corpus, expected_sha256=core.digest(corpus))
    require(len(exports) == len(corpus.rows), "export row count")
    items, audits, encoded_rows = [], [], []
    for index, (row, export) in enumerate(zip(corpus.rows, exports)):
        target = row.target.decode("ascii")
        require(legal_action(public, row.target) is not None and row.source_slot_id == row.slot_id, "unsupported target")
        prompt_text = core.action_prompt(public, row.slot_id, view="train")
        require(row.prompt == prompt_text and export["spans"] == [[prompt_text, False, "context"],
                                                                   [target, True, "child_action"]], "export span drift")
        require(core.PROCESS_TAPE not in prompt_text, "teacher tape in sleep")
        prompt = probe.render(tokenizer, messages(prompt_text))
        require(prompt["actual_system_text"] == GENERIC_SYSTEM, "sleep system drift")
        full_messages = messages(prompt_text) + [dict(role="assistant", content=target)]
        full = tokenizer.apply_chat_template(full_messages, tokenize=False, add_generation_prompt=False)
        ids = token_ids(tokenizer.apply_chat_template(full_messages, tokenize=True, add_generation_prompt=False))
        prefix, prefix_ids = prompt["rendered_prompt"], prompt["prompt_token_ids"]
        require(full.startswith(prefix + target) and ids == token_ids(tokenizer.encode(full, add_special_tokens=False)),
                "native full-assistant bytes/tokens differ")
        require(ids[:len(prefix_ids)] == prefix_ids and len(ids) <= 1024, "prefix boundary/truncation")
        eos, eos_id = tokenizer.eos_token, tokenizer.eos_token_id
        require(isinstance(eos, str) and eos and type(eos_id) is int and eos_id >= 0, "missing EOS")
        suffix = full[len(prefix + target):]
        require(suffix.startswith(eos), "missing native assistant EOS")
        tail = suffix[len(eos):]
        target_ids = token_ids(tokenizer.encode(target, add_special_tokens=False))
        require(not tail.strip() and token_ids(tokenizer.encode(eos, add_special_tokens=False)) == [eos_id] and
                target_ids and eos_id not in target_ids, "EOS/trailer/target encoding")
        tail_ids = token_ids(tokenizer.encode(tail, add_special_tokens=False)) if tail else []
        labels = [-100] * len(prefix_ids) + target_ids + [eos_id] + [-100] * len(tail_ids)
        spans = [[prefix, False, "context"], [target, True, "child_action"], [eos, True, "assistant_end"]]
        if tail:
            spans.append([tail, False, "template_tail"])
        item_data = dict(spans=spans, group=row.slot_id, order=index, view="source_withdrawn_action")
        item = trainer.normalize_items([item_data])[0]
        segments = trainer.encode_item_segments(item, tokenizer, 1024, False, False, index, overflow="truncate")
        require(len(segments) == 1 and segments[0].context_dropped == segments[0].target_dropped == 0,
                "encoder dropped/split/truncated child target")
        require(segments[0].ids == ids and segments[0].labels == labels and len(ids) == len(labels), "full target/EOS mask")
        pad_id = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else eos_id
        batch = trainer.collate([[segments[0]]], pad_id)
        require(batch["labels"] == [labels] and batch["input_ids"] == [ids], "collation mask drift")
        items.append(item_data)
        encoded_rows.append(segments[0])
        audits.append(dict(slot_id=row.slot_id, target_hex=row.target.hex(), target_sha256=hashlib.sha256(row.target).hexdigest(),
                           input_ids=ids, labels=labels, child_tokens=len(target_ids),
                           supervised_tokens=len(target_ids) + 1, native_prompt=prompt))
    pad_id = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else tokenizer.eos_token_id
    packs = trainer.pack_by_group(encoded_rows, 1024, pack=False)
    require(len(packs) == len(items) and all(len(pack) == 1 for pack in packs), "packing forbidden")
    orders = []
    for epoch in range(20):
        ordered = trainer.epoch_order(packs, 0, epoch, True)
        orders.append([pack[0].item_index for pack in ordered])
        require(sorted(orders[-1]) == list(range(len(items))), "epoch row coverage differs")
        for offset in range(0, len(ordered), 8):
            subset = ordered[offset:offset + 8]
            batch = trainer.collate(subset, pad_id)
            for pack, ids, labels in zip(subset, batch["input_ids"], batch["labels"], strict=True):
                segment = pack[0]
                padding = len(ids) - len(segment.ids)
                require(ids == segment.ids + [pad_id] * padding and labels == segment.labels + [-100] * padding,
                        "batched target or padding mask differs")
    return dict(items=items, encoding=audits, source_exports=exports, rows=len(items), epoch_order=orders,
                steps=20 * math.ceil(len(items) / 8), corpus_sha256=core.digest(corpus),
                target_tokens=sum(row["supervised_tokens"] for row in audits),
                total_tokens=sum(len(row["input_ids"]) for row in audits))


def validate_manifest(manifest, config, prepared):
    count, steps = prepared["rows"], prepared["steps"]
    require(manifest["config"] == config and not manifest["empty"] and manifest["steps"] == steps and
            manifest["micro_batches"] == steps and manifest["epochs_run"] == 20 and
            manifest["nonfinite_batches"] == 0, "actual fit work/config differs")
    corpus = manifest["corpus"]
    require(corpus["n_items"] == corpus["n_encoded"] == count and corpus["n_skipped_no_target"] == 0 and
            corpus["sha256"] == prepared["corpus_sha256"], "fit corpus inventory")
    truncation = manifest["truncation"]
    require(all(truncation[key] == 0 for key in ("items_truncated", "context_tokens_dropped", "target_tokens_dropped",
                                                "items_split", "segments_from_splits")), "fit truncation/splitting")
    require(manifest["packing"]["mode"] == "one_item_per_sequence" and manifest["packing"]["n_sequences"] == count,
            "fit packing changed")
    tokens = manifest["tokens"]
    require(tokens["target"] == prepared["target_tokens"] and tokens["total"] == prepared["total_tokens"] and
            tokens["context"] == prepared["total_tokens"] - prepared["target_tokens"] and
            manifest["train_tokens_seen"] == 20 * prepared["total_tokens"], "actual exposure differs")
    require(tokens["target_by_category"] == {"child_action": prepared["target_tokens"] - count, "assistant_end": count} and
            tokens["target_by_view"] == {"source_withdrawn_action": prepared["target_tokens"]}, "target category exposure")
    losses = manifest["mean_loss_per_epoch"]
    require(len(losses) == 20 and all(type(value) in (int, float) and math.isfinite(value)
                                   for value in losses + [manifest["final_loss"]]), "nonfinite/incomplete fit losses")


def fit_stage(plan, core, trainer, probe, reflection, world, states, stage):
    policy = "PROMOTE" if stage == "fit1" else stage.split("_")[1]
    state = states[policy]
    corpus = state.corpus
    public = core.public_view(world)
    require(corpus is not None and corpus.kind == "AUTHENTIC", "missing authentic material")
    result = dict(stage=stage, calls=0, fits=0, updates=0, corpus_sha256=core.digest(corpus),
                  initialized_from_sha256=plan["base_sha256"], candidate_sha256=None, candidate_files={},
                  admitted=len(corpus.rows), rejected=len(corpus.rejected), status="FORMATION_SHORTAGE")
    directory = stage_dir(plan, stage) / "data"
    write(directory / "corpus.json", core.to_data(corpus))
    if not corpus.rows:
        return result
    tokenizer = probe.native_tokenizer(plan["spec"]["model"])
    require(tokenizer.chat_template == plan["chat_template"], "tokenizer template drift")
    prepared = encode_training(core, public, corpus, tokenizer, trainer, probe)
    write(directory / "training.json", prepared)
    write(directory / "fit_intent.json", dict(fresh_base=True, fresh_optimizer=True, initialized_from=plan["base_sha256"],
                                               steps=prepared["steps"], config=plan["config"]))
    loaded_tokenizer, model = reflection.load_native_model(plan["spec"]["model"])
    require(loaded_tokenizer.chat_template == tokenizer.chat_template and not getattr(model, "peft_config", None),
            "fit must cold-load base")
    adapter = directory / "adapter"
    manifest = trainer.run_training(trainer.normalize_items(prepared["items"]), tokenizer, model,
                                    trainer.TrainConfig(**plan["config"]), str(adapter),
                                    corpus_sha=prepared["corpus_sha256"], corpus_name="child_records:" + stage)
    trainable = []
    for name, parameter in model.named_parameters():
        if parameter.requires_grad:
            require("lora_A" in name or "lora_B" in name, "non-LoRA trainability")
            require(bool(parameter.detach().isfinite().all().item()), "nonfinite final LoRA state")
            trainable.append(name)
    require(trainable, "missing trainable LoRA parameters")
    require(read(adapter / "train_manifest.json") == manifest, "returned/durable trainer manifest differs")
    validate_manifest(manifest, plan["config"], prepared)
    reflection.check_adapter(str(adapter), plan["config"])
    files = tree(adapter)
    result.update(fits=1, updates=prepared["steps"], candidate_files=files,
                  candidate_sha256=value_hash(files), status="FIT_COMPLETE",
                  trainable_names_sha256=value_hash(trainable), final_trainable_finite=True)
    return result


class Native:
    def __init__(self, plan, probe, route):
        from vllm import LLM, SamplingParams
        from vllm.lora.request import LoRARequest
        self.probe, self.route = probe, route
        self.tokenizer = probe.native_tokenizer(plan["spec"]["model"])
        require(self.tokenizer.chat_template == plan["chat_template"], "native chat template differs")
        self.llm = LLM(model=plan["spec"]["model"], tokenizer=plan["spec"]["model"], **ENGINE)
        self.params = SamplingParams(**PARAMS)
        self.request = None if route is None else LoRARequest(route["name"], route["id"], route["path"])

    def generate(self, input_messages):
        native = self.probe.render(self.tokenizer, input_messages)
        started = time.monotonic()
        outputs = self.llm.generate([native["rendered_prompt"]], self.params, lora_request=self.request, use_tqdm=False)
        require(len(outputs) == 1 and len(outputs[0].outputs) == 1, "unexpected native output count")
        output = outputs[0].outputs[0]
        return dict(native=native, raw_hex=output.text.encode("utf-8").hex(), text=output.text,
                    output_token_ids=list(output.token_ids),
                    decoded=self.tokenizer.decode(list(output.token_ids), skip_special_tokens=True),
                    finish_reason=output.finish_reason, stop_reason=output.stop_reason,
                    started=started, ended=time.monotonic(), route=self.route,
                    returned_prompt_token_ids=list(outputs[0].prompt_token_ids))

    def close(self):
        shutdown = getattr(self.llm, "shutdown", None)
        if shutdown is not None:
            shutdown()


def validate_response(response, route):
    require(response["route"] == route and response["native"]["actual_system_text"] == GENERIC_SYSTEM, "actual route/system differs")
    require(bytes.fromhex(response["raw_hex"]) == response["text"].encode("utf-8") and
            response["decoded"] == response["text"], "raw native output/decoding differs")
    ids = token_ids(response["output_token_ids"])
    require(len(ids) <= 32 and response["finish_reason"] in ("stop", "length"), "generation work/finish differs")
    require(response["stop_reason"] is None or type(response["stop_reason"]) in (int, str), "native stop reason type")
    require(bool(ids) or not response["text"], "text without output tokens")
    require(response["returned_prompt_token_ids"] == response["native"]["prompt_token_ids"], "engine input tokens differ")
    require(all(type(response[key]) in (int, float) and math.isfinite(response[key]) for key in ("started", "ended")) and
            response["ended"] >= response["started"], "native timing differs")


def capture_stage(plan, core, world, states, stage, backend_factory, reader=read_stage):
    public = core.public_view(world)
    route = route_for(plan, core, states, stage, reader)
    directory = stage_dir(plan, stage) / "data"
    write(directory / "identity.json", dict(stage=stage, route=route, engine=ENGINE, params=PARAMS,
                                            base_sha256=plan["base_sha256"]))
    backend, calls, episodes, receipts = None, 0, [], []
    lineage = stage.split("_")[1] if "_" in stage else "SHARED"
    wake = stage.startswith("wake")
    block = 1 if stage == "wake1" else 2
    slots = [slot for slot in public.slots if not wake or slot.block == block]
    def generate(prompt, kind, slot):
        nonlocal calls
        call_id = f"{calls:02d}"
        request = dict(slot_id=slot.slot_id, kind=kind, messages=messages(prompt))
        write(directory / (call_id + ".request.json"), request)
        response = backend.generate(request["messages"])
        write(directory / (call_id + ".response.json"), response)
        calls += 1
        validate_response(response, route)
        return bytes.fromhex(response["raw_hex"])
    try:
        backend = backend_factory(route)
        for index, slot in enumerate(slots):
            kind = "action" if wake else "readout"
            raw = generate(core.action_prompt(public, slot.slot_id, view="wake" if wake else "readout"), kind, slot)
            action = core.make_receipt(public, slot.slot_id, kind, raw, sequence=sequence(stage, index * 3), lineage=lineage)
            write(directory / f"receipt_{index:02d}_action.json", core.to_data(action))
            if not wake:
                receipts.append(action)
            elif legal_action(public, raw) is None:
                episodes.append(core.Episode(action))
                write(directory / f"episode_{index:02d}.json", dict(status="INVALID_ACTION", action_sha256=action.sha256))
            else:
                outcome = core.feedback(world, action, sequence=sequence(stage, index * 3 + 1))
                write(directory / f"receipt_{index:02d}_outcome.json", core.to_data(outcome))
                record_raw = generate(core.process_prompt(public, action, outcome), "record", slot)
                record = core.make_receipt(public, slot.slot_id, "record", record_raw,
                                          sequence=sequence(stage, index * 3 + 2), lineage=lineage, previous=outcome)
                write(directory / f"receipt_{index:02d}_record.json", core.to_data(record))
                episodes.append(core.Episode(action, outcome, record))
    finally:
        if backend is not None:
            backend.close()
    if route is not None:
        require(value_hash(tree(route["path"])) == route["sha256"], "candidate mutated during inference")
    result = dict(stage=stage, calls=calls, fits=0, updates=0, route=route, status="CAPTURE_COMPLETE")
    if wake:
        result["capture"] = core.to_data(core.capture_block(public, block, lineage, tuple(episodes)))
    else:
        result["readouts"] = core.to_data(tuple(receipts))
    return result


def worker(root, plan_sha256, stage, deadline, allow_gpu=False):
    require(allow_gpu and os.getpid() == os.getpgrp(), "Main-only fresh process-group worker required")
    offline()
    with budget(deadline - time.time()):
        plan, core, trainer, probe, reflection, world = verify(root, plan_sha256, native=True)
        require(os.environ.get("CUDA_VISIBLE_DEVICES") == plan["spec"]["gpu_uuid"], "worker GPU binding differs")
        require(deadline <= plan["spec"]["lease_end"] - COLLECTION_SECONDS - LEASE_MARGIN, "worker lease margin")
        directory = stage_dir(plan, stage)
        require(directory.is_dir() and not (directory / "data").exists(), "fresh stage directory required")
        write(directory / "started.json", dict(pid=os.getpid(), pgid=os.getpgrp(), stage=stage,
                                               plan_sha256=plan_sha256, time=time.time()))
        try:
            states = dependency_states(plan, core, world, stage)
            if stage.startswith("fit"):
                result = fit_stage(plan, core, trainer, probe, reflection, world, states, stage)
            else:
                result = capture_stage(plan, core, world, states, stage, lambda route: Native(plan, probe, route))
            write(directory / "data/result.json", result)
            write(directory / "CLOSED.json", dict(stage=stage, pid=os.getpid(), files=tree(directory / "data")))
        except BaseException as error:
            write(directory / "failure.json", failure(error))
            raise


def stage_seconds(stage, deadline, now):
    seconds = min(FIT_SECONDS if stage.startswith("fit") else INFERENCE_SECONDS, deadline - now - CLEANUP_SECONDS)
    require(seconds > 0, "no compute time before cleanup reserve")
    return seconds


def run_stage(plan, plan_sha256, stage, deadline, probe):
    spec = plan["spec"]
    gpu = dict(gpu_uuid=spec["gpu_uuid"], gpu_index=spec["gpu_index"])
    require(probe.gpu_state(gpu), "assigned GPU occupied; no foreign process will be stopped")
    seconds = stage_seconds(stage, deadline, time.monotonic())
    directory = stage_dir(plan, stage)
    directory.mkdir(parents=True)
    command = [plan["python"], "-B", str(Path(spec["source"]) / "gpu/astra_l2_public_record_dev.py"),
               "worker", "--root", plan["root"], "--plan-sha256", plan_sha256, "--stage", stage,
               "--deadline", str(time.time() + seconds), "--allow-gpu"]
    process = None
    try:
        with (directory / "stdout.log").open("xb") as stdout, (directory / "stderr.log").open("xb") as stderr:
            process = subprocess.Popen(command, stdout=stdout, stderr=stderr, start_new_session=True,
                                       env=dict(os.environ, CUDA_VISIBLE_DEVICES=spec["gpu_uuid"], PYTHONDONTWRITEBYTECODE="1"))
            write(directory / "launch.json", dict(pid=process.pid, pgid=process.pid, command=command, seconds=seconds))
            require(process.wait(timeout=seconds) == 0, "native worker failed")
    finally:
        with release_budget(deadline):
            released = process is None or probe.cleanup(process)
            vacant = probe.gpu_state(gpu)
            write(directory / "release.json", dict(owned_group_released=released, gpu_vacant=vacant,
                                                   pid=process.pid if process else None, time=time.time()))
            require(released and vacant, "owned group/GPU release failed")
    result = read_stage(plan, stage)
    started, closed = read(directory / "started.json"), read(directory / "CLOSED.json")
    require(started["pid"] == started["pgid"] == closed["pid"] == process.pid and
            started["plan_sha256"] == plan_sha256, "fresh worker identity differs")
    return result


def check_work(stage, result):
    require(result["stage"] == stage, "work belongs to another stage")
    for field in CAPS:
        require(type(result[field]) is int and result[field] >= 0, "invalid work counter")
    if stage.startswith("fit"):
        admitted = result["admitted"]
        require(type(admitted) is int and 0 <= admitted <= (8 if stage == "fit1" else 16), "admitted count")
        require(result["calls"] == 0 and result["fits"] == int(admitted > 0) and
                result["updates"] == 20 * math.ceil(admitted / 8), "fit work differs")
        require((result["candidate_sha256"] is not None) == (admitted > 0), "candidate/shortage differs")
        if admitted:
            require(value_hash(result["candidate_files"]) == result["candidate_sha256"], "candidate identity differs")
        require(result["status"] == ("FIT_COMPLETE" if admitted else "FORMATION_SHORTAGE"), "fit status differs")
    else:
        require(result["fits"] == result["updates"] == 0 and
                (8 <= result["calls"] <= 16 if stage.startswith("wake") else result["calls"] == 16), "capture work differs")


def execute_loop(plan, core, world, runner):
    states = core.start_pair(core.public_view(world), plan["base_sha256"])
    completed, work = [], dict.fromkeys(CAPS, 0)
    status = "COMPLETE"
    for stage in STAGES:
        result = runner(stage)
        check_work(stage, result)
        for field in CAPS:
            work[field] += result[field]
            require(work[field] <= CAPS[field], "root work cap exceeded")
        advance(core, core.public_view(world), states, stage, result)
        completed.append(stage)
        if any(state.phase == "FORMATION_SHORTAGE" for state in states.values()):
            status = "FORMATION_SHORTAGE"
            break
    return dict(status=status, completed=completed, work=work, states=core.to_data(states),
                two_cycle_complete=status == "COMPLETE", scientific_pass=None, claim=CLAIM)


def finalize(root, terminal, plan_sha256, deadline, clock=time.monotonic):
    root = Path(root)
    write(root / "terminal.json", terminal)
    files = {name: checksum for name, checksum in tree(root).items() if name not in WITNESSES}
    write(root / "SEAL.json", dict(schema=SCHEMA, plan_sha256=plan_sha256, files=files))
    ended = clock()
    witness = dict(plan_sha256=plan_sha256, seal_sha256=digest(root / "SEAL.json"),
                   terminal_sha256=digest(root / "terminal.json"), ended=ended, deadline=deadline,
                   within_deadline=ended <= deadline)
    write(root / "FINALIZED.json", witness)
    if clock() > deadline:
        write(root / "FINALIZATION_ABORT.json", dict(reason="durable finalization exceeded controller deadline",
                                                     finalized_sha256=digest(root / "FINALIZED.json")))
    return "NONREPORTABLE_RUNTIME_ABORT" if not witness["within_deadline"] or (root / "FINALIZATION_ABORT.json").exists() else terminal["status"]


def controller(root, plan_sha256, allow_gpu=False):
    started = time.monotonic()
    deadline = started + OUTER_SECONDS
    require(allow_gpu, "Main-only controller requires --allow-gpu")
    offline()
    root = plain_path(str(Path(root).absolute()))
    launcher_output_outside(root)
    require(not any((root / name).exists() for name in ("controller_started.json", "run", "terminal.json", *WITNESSES)),
            "root cannot resume or relabel")
    write(root / "controller_started.json", dict(started=started, deadline=deadline, wall=time.time(), plan_sha256=plan_sha256))
    def terminated(signum, frame):
        raise InterruptedError("controller interrupted")
    previous = signal.signal(signal.SIGTERM, terminated)
    try:
        with budget(deadline - time.monotonic() - CLEANUP_SECONDS):
            plan, core, trainer, probe, reflection, world = verify(root, plan_sha256, native=True)
            require(time.time() + max(0, deadline - time.monotonic()) + COLLECTION_SECONDS + LEASE_MARGIN <= plan["spec"]["lease_end"],
                    "controller lease margin")
            terminal = execute_loop(plan, core, world, lambda stage: run_stage(plan, plan_sha256, stage, deadline, probe))
    except BaseException as error:
        terminal = dict(status="NONREPORTABLE_RUNTIME_ABORT", error=failure(error), two_cycle_complete=False,
                        completed=[stage for stage in STAGES if (root / "run" / stage / "CLOSED.json").exists()],
                        scientific_pass=None, claim=CLAIM)
    finally:
        signal.signal(signal.SIGTERM, previous)
    terminal.update(started=started, deadline=deadline, elapsed_before_finalization=time.monotonic() - started)
    return finalize(root, terminal, plan_sha256, deadline)


def custody(root, plan_sha256):
    root = Path(root)
    seal = read(root / "SEAL.json")
    require(seal["schema"] == SCHEMA and seal["plan_sha256"] == plan_sha256 and
            digest(root / "plan.json") == plan_sha256, "seal plan binding")
    files = {name: checksum for name, checksum in tree(root).items() if name not in WITNESSES}
    require(seal["files"] == files, "exact sealed inventory differs")
    terminal = read(root / "terminal.json")
    if not (root / "FINALIZED.json").exists():
        return dict(status="NONREPORTABLE_RUNTIME_ABORT", reason="missing final witness", scientific_replay=False), files
    witness = read(root / "FINALIZED.json")
    require(witness["seal_sha256"] == digest(root / "SEAL.json") and witness["terminal_sha256"] == digest(root / "terminal.json") and
            witness["plan_sha256"] == plan_sha256 and witness["deadline"] == terminal["deadline"], "final witness binding")
    require(all(type(witness[key]) in (int, float) and math.isfinite(witness[key]) for key in ("ended", "deadline")) and
            type(witness["within_deadline"]) is bool and witness["within_deadline"] == (witness["ended"] <= witness["deadline"]),
            "witness timing classification")
    if (root / "FINALIZATION_ABORT.json").exists():
        require(read(root / "FINALIZATION_ABORT.json")["finalized_sha256"] == digest(root / "FINALIZED.json"), "late-write binding")
    if not witness["within_deadline"] or (root / "FINALIZATION_ABORT.json").exists():
        return dict(status="NONREPORTABLE_RUNTIME_ABORT", reason="late finalization", scientific_replay=False), files
    return terminal, files


def replay_capture(plan, core, world, states, stage, result):
    public = core.public_view(world)
    directory = stage_dir(plan, stage) / "data"
    expected_route = route_for(plan, core, states, stage)
    require(result["route"] == expected_route, "capture requested route differs")
    require(read(directory / "identity.json") == dict(stage=stage, route=expected_route, engine=ENGINE, params=PARAMS,
                                                     base_sha256=plan["base_sha256"]), "capture identity differs")
    if stage.startswith("wake"):
        capture = capture_from_data(core, public, result["capture"])
        entries = [(episode.action, episode) for episode in capture.episodes]
    else:
        receipts = core.from_data(result["readouts"], expected_type=tuple)
        require(len(receipts) == 16 and [receipt.slot_id for receipt in receipts] == [slot.slot_id for slot in public.slots],
                "fixed report16 order")
        entries = [(receipt, None) for receipt in receipts]
    call_index = 0
    def check_call(receipt, prompt, kind):
        nonlocal call_index
        request = read(directory / f"{call_index:02d}.request.json")
        response = read(directory / f"{call_index:02d}.response.json")
        require(request == dict(slot_id=receipt.slot_id, kind=kind, messages=messages(prompt)), "capture visibility/request drift")
        validate_response(response, expected_route)
        require(bytes.fromhex(response["raw_hex"]) == receipt.raw, "raw capture/receipt differs")
        call_index += 1
    for index, (action, episode) in enumerate(entries):
        lineage = stage.split("_")[1] if "_" in stage else "SHARED"
        kind = "action" if episode is not None else "readout"
        rebuilt = core.make_receipt(public, action.slot_id, kind, action.raw, sequence=sequence(stage, index * 3), lineage=lineage)
        require(action == rebuilt, "action/readout identity differs")
        check_call(action, core.action_prompt(public, action.slot_id, view="wake" if episode is not None else "readout"), kind)
        if episode is not None:
            if legal_action(public, action.raw) is None:
                require(episode.outcome is None and episode.record is None, "invalid action fabricated feedback")
            else:
                expected = core.feedback(world, action, sequence=sequence(stage, index * 3 + 1))
                require(episode.outcome == expected and episode.record is not None, "public feedback differs")
                record = core.make_receipt(public, action.slot_id, "record", episode.record.raw,
                                           sequence=sequence(stage, index * 3 + 2), lineage=lineage, previous=expected)
                require(record == episode.record, "record receipt differs")
                check_call(record, core.process_prompt(public, action, expected), "record")
    require(call_index == result["calls"], "actual generation count differs")
    require(len(list(directory.glob("*.response.json"))) == call_index and
            len(list(directory.glob("*.request.json"))) == call_index, "extra/missing generation call")


def score_readouts(core, world, result):
    public = core.public_view(world)
    receipts = core.from_data(result["readouts"], expected_type=tuple)
    choices = [legal_action(public, receipt.raw) for receipt in receipts]
    correct = [choice == target for choice, target in zip(choices, world.success_actions)]
    return dict(total=16, old_total=8, new_total=8, old_correct=sum(correct[:8]), new_correct=sum(correct[8:]),
                legal=sum(choice is not None for choice in choices), malformed=sum(choice is None for choice in choices))


def collect(root, plan_sha256, output):
    offline()
    output = plain_path(str(Path(output).absolute()))
    require(not output.is_relative_to(Path(root).absolute()), "collection output must be outside sealed root")
    with budget(COLLECTION_SECONDS):
        terminal, files = custody(root, plan_sha256)
        summary = dict(schema=SCHEMA, status=terminal["status"], file_count=len(files),
                       bytes=sum((Path(root) / name).stat().st_size for name in files),
                       seal_sha256=digest(Path(root) / "SEAL.json"), plan_sha256=plan_sha256,
                       scientific_replay=False, scientific_pass=None, claim=CLAIM)
        if terminal["status"] != "NONREPORTABLE_RUNTIME_ABORT":
            plan, core, trainer, probe, reflection, world = verify(root, plan_sha256)
            states = core.start_pair(core.public_view(world), plan["base_sha256"])
            reports = {stage: None for stage in STAGES if stage == "baseline" or stage.startswith("report")}
            formation, exposure = {}, {}
            totals = dict.fromkeys(CAPS, 0)
            tokenizer = None
            require(terminal["completed"] == list(STAGES[:len(terminal["completed"])]), "nonprefix completed stages")
            for stage in terminal["completed"]:
                result = read_stage(plan, stage)
                check_work(stage, result)
                if stage.startswith("fit"):
                    policy = "PROMOTE" if stage == "fit1" else stage.split("_")[1]
                    formation[stage] = dict(status=result["status"], admitted=result["admitted"], rejected=result["rejected"],
                                            corpus_sha256=result["corpus_sha256"], candidate_sha256=result["candidate_sha256"],
                                            initialized_from_sha256=result["initialized_from_sha256"],
                                            shared_physical_fit=stage == "fit1")
                    exposure[stage] = dict(fits=result["fits"], updates=result["updates"],
                                           presentations=20 * result["admitted"] if result["fits"] else 0)
                    if result["fits"]:
                        adapter = stage_dir(plan, stage) / "data/adapter"
                        require(tree(adapter) == result["candidate_files"], "candidate custody differs")
                        reflection.check_adapter(str(adapter), plan["config"])
                        prepared = read(stage_dir(plan, stage) / "data/training.json")
                        if tokenizer is None:
                            tokenizer = probe.native_tokenizer(plan["spec"]["model"])
                            require(tokenizer.chat_template == plan["chat_template"], "collection tokenizer differs")
                        require(prepared == encode_training(core, core.public_view(world), states[policy].corpus,
                                                            tokenizer, trainer, probe), "replayed training/EOS exposure differs")
                        validate_manifest(read(adapter / "train_manifest.json"), plan["config"], prepared)
                        exposure[stage].update(target_tokens_per_epoch=prepared["target_tokens"],
                                               total_tokens_per_epoch=prepared["total_tokens"],
                                               train_tokens_seen=20 * prepared["total_tokens"])
                    require(result["admitted"] == len(states[policy].corpus.rows) and
                            result["rejected"] == len(states[policy].corpus.rejected), "formation counts differ")
                    require(core.from_data(read(stage_dir(plan, stage) / "data/corpus.json"), expected_type=core.Corpus) == states[policy].corpus,
                            "fit snapshot differs from replayed child material")
                else:
                    replay_capture(plan, core, world, states, stage, result)
                    responses = [read(path) for path in sorted((stage_dir(plan, stage) / "data").glob("*.response.json"))]
                    exposure[stage] = dict(calls=len(responses),
                                           prompt_tokens=sum(len(response["returned_prompt_token_ids"]) for response in responses),
                                           output_tokens=sum(len(response["output_token_ids"]) for response in responses),
                                           generation_seconds=sum(response["ended"] - response["started"] for response in responses),
                                           length_outputs=sum(response["finish_reason"] == "length" for response in responses))
                    if stage in reports:
                        reports[stage] = score_readouts(core, world, result)
                        reports[stage]["length_outputs"] = exposure[stage]["length_outputs"]
                advance(core, core.public_view(world), states, stage, result)
                for field in CAPS:
                    totals[field] += result[field]
                    require(totals[field] <= CAPS[field], "replay work cap exceeded")
            require(totals == terminal["work"] and core.to_data(states) == terminal["states"], "terminal state/work differs")
            complete = terminal["completed"] == list(STAGES) and all(state.phase == "COMPLETE" for state in states.values())
            require(terminal["two_cycle_complete"] == complete and (terminal["status"] == "COMPLETE") == complete,
                    "false two-cycle completion")
            require(complete or terminal["status"] == "FORMATION_SHORTAGE" and
                    any(state.phase == "FORMATION_SHORTAGE" for state in states.values()), "unexplained incomplete terminal")
            endpoint = None
            if complete:
                endpoint = core.reduce_pair(world, states, {policy: core.from_data(read_stage(plan, "report2_" + policy)["readouts"],
                                                                                  expected_type=tuple) for policy in POLICIES})
            contrasts = {}
            for cycle in (1, 2):
                promote, shadow = (reports[f"report{cycle}_{policy}"] for policy in POLICIES)
                contrasts[str(cycle)] = None if promote is None or shadow is None else {
                    key: promote[key] - shadow[key] for key in ("old_correct", "new_correct", "legal")}
            summary.update(scientific_replay=True, reports=reports, endpoint=endpoint, work=totals,
                           contrasts=contrasts, formation=formation, exposure=exposure,
                           two_cycle_complete=complete, completed=terminal["completed"],
                           incomplete=[stage for stage in STAGES if stage not in terminal["completed"]])
        else:
            summary.update(two_cycle_complete=False, reason=terminal.get("reason", terminal.get("error")),
                           completed=terminal.get("completed", []), failed_raw_stages_not_scored=True)
        write(output, summary)
        return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare_parser = commands.add_parser("prepare")
    prepare_parser.add_argument("--spec", required=True)
    prepare_parser.add_argument("--spec-sha256", required=True)
    prepare_parser.add_argument("--root", required=True)
    prepare_parser.add_argument("--allow-native", action="store_true")
    for name in ("controller", "worker", "collect"):
        command = commands.add_parser(name)
        command.add_argument("--root", required=True)
        command.add_argument("--plan-sha256", required=True)
        if name != "collect":
            command.add_argument("--allow-gpu", action="store_true")
        if name == "worker":
            command.add_argument("--stage", choices=STAGES, required=True)
            command.add_argument("--deadline", type=float, required=True)
        if name == "collect":
            command.add_argument("--output", required=True)
    args = vars(parser.parse_args())
    name = args.pop("command")
    if name == "prepare":
        args["spec_path"] = args.pop("spec")
    result = globals()[name](**args)
    if result is not None:
        print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
