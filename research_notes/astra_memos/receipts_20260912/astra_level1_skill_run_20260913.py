"""Bounded sourced authored Level1 skill fitting; Main alone launches native work.

Prepare uses the native tokenizer on CPU, never a model. One cold fit separates
OFF/post readouts, each sharing one engine across held/canary panels (120 calls).
Collection alone scores after all raw captures close.
Pinned original public/reflection helpers retain their existing native semantics.
"""
from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Mapping
import contextlib
from dataclasses import asdict
import hashlib
import importlib
import importlib.metadata
import importlib.util
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


SELF = Path(__file__).resolve()
SCOPE = "authored_level1_skill_96train_320steps_120calls_v1"
STATES = ("OFF", "post")
PANELS = ("held", "canary")
STAGES = ("OFF", "fit", "post")
TRAIN_ROWS, HELD_ROWS, CANARY_ROWS = 96, 48, 12
UPDATES, BATCH_SIZE, MAX_LEN = 320, 4, 1024
OUTER_SECONDS, COLLECTION_SECONDS = 5400, 180
GPU_QUERY_SECONDS, GROUP_CLEANUP_SECONDS = 30, 10
CLEANUP_SECONDS = GROUP_CLEANUP_SECONDS + GPU_QUERY_SECONDS
FIT_SECONDS, READOUT_SECONDS, LEASE_MARGIN = 3600, 600, 21600
SOURCE_NAMES = ("organism_v6/__init__.py", "organism_v6/birth_skill_corpus.py",
                "organism_v6/rulegame_parenting_diagnostic.py", "organism_v6/train_adapter_v3.py")
PARAMS = dict(temperature=0.0, seed=0, max_tokens=192, top_p=1.0, top_k=-1, n=1,
              presence_penalty=0.0, frequency_penalty=0.0, repetition_penalty=1.0, ignore_eos=False)
ENGINE = dict(max_model_len=16384, tensor_parallel_size=1, seed=0,
              gpu_memory_utilization=0.85, enforce_eager=True, enable_lora=True,
              max_lora_rank=32, enable_prefix_caching=False, dtype="bfloat16", trust_remote_code=False)
RECIPE = dict(rank=8, alpha=16, dropout=.05, lr=3e-4, epochs=14, max_len=MAX_LEN,
              seed=0, overflow="truncate", batch_size=BATCH_SIZE, grad_accum=1, pack=False,
              shuffle_groups=True, chat_template=False, add_eos=False, optimizer="adamw",
              grad_checkpoint=True, device="cuda", dtype="bf16", max_steps=UPDATES)
CLAIM = "Sourced authored Level1 only; cold base plus fresh LoRA, no live parent, child SLEEP, clean ancestry, mechanism freeze, P1/H1/H2 or automatic promotion."
RECIPE["note"] = (SCOPE + "; SEQ113-inspired, not replication: fresh320, no warm80 parent or unrelated arithmetic replay; "
                  "96 distinct authored sources, four distinct sources/batch, full target+EOS masks. "
                  "Upstream NO_FIT scope binds model files only; this branch explicitly fits one fresh adapter.")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode()


def digest(path):
    checksum = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            checksum.update(block)
    return checksum.hexdigest()


def value_hash(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def read(path):
    return json.loads(Path(path).read_text(), object_pairs_hook=unique_object,
                      parse_constant=lambda value: require(False, "nonfinite JSON"))


def write(path, value):
    path = Path(path)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.pending")
    with temporary.open("xb") as stream:
        stream.write(encoded(value))
        stream.flush()
        os.fsync(stream.fileno())
    try:
        os.link(temporary, path)
    finally:
        temporary.unlink()


def failure(path, error):
    if not Path(path).exists():
        write(path, dict(error_type=type(error).__name__, error=str(error), time=time.time(), retry=False))


def tree(root):
    result = {}
    for path in sorted(Path(root).rglob("*")):
        require(not path.is_symlink(), "symlink in artifact tree")
        if path.is_file():
            result[str(path.relative_to(root))] = digest(path)
        else:
            require(path.is_dir(), "special artifact file")
    return result


def offline():
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_DATASETS_OFFLINE="1",
                      HF_HUB_DISABLE_TELEMETRY="1", VLLM_NO_USAGE_STATS="1", DO_NOT_TRACK="1",
                      VLLM_WORKER_MULTIPROC_METHOD="spawn", PYTHONDONTWRITEBYTECODE="1")
    sys.dont_write_bytecode = True


def load_probe(path, expected):
    require(digest(path) == expected, "Boyle final driver hash differs")
    spec = importlib.util.spec_from_file_location("perception_final_public_probe", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    require(isinstance(module.ANCHOR, str) and module.ANCHOR.strip(), "missing Boyle anchor")
    require(getattr(module, "GPU_QUERY_SECONDS", None) == GPU_QUERY_SECONDS, "Boyle final driver must allow 30s NVML queries")
    return module


def source_api(source):
    source = Path(source).resolve()
    sys.path.insert(0, str(source))
    modules = [importlib.import_module("organism_v6." + name)
               for name in ("birth_skill_corpus", "train_adapter_v3")]
    for module in modules:
        require(Path(module.__file__).resolve().parent.parent == source, "wrong source import")
    return modules


def environment(probe):
    return dict(probe=probe.native_environment(), peft=importlib.metadata.version("peft"))


def token_ids(value):
    if isinstance(value, Mapping):
        value = value.get("input_ids")
    require(isinstance(value, (list, tuple)) and value and
            all(type(token) is int and token >= 0 for token in value), "invalid tokenizer token vector")
    return list(value)


def load_module(record, name):
    require(set(record) == {"path", "sha256"} and digest(record["path"]) == record["sha256"], name + " pin differs")
    specification = importlib.util.spec_from_file_location("level1_" + name, record["path"])
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


def load_material(specification):
    key = "ASTRA_LEVEL1_SOURCE_ROOT"
    previous = os.environ.get(key)
    os.environ[key] = specification["source"]
    try:
        return load_module(specification["material"], "material")
    finally:
        if previous is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = previous


def checked_apis(specification):
    require(specification["runner_sha256"] == digest(SELF), "runner pin differs")
    for key in ("material", "reflection", "public", "protocol", "binding"):
        record = specification[key]
        require(set(record) == {"path", "sha256"} and Path(record["path"]).is_absolute() and
                digest(record["path"]) == record["sha256"], key + " pin differs")
    source = Path(specification["source"])
    require(source.is_absolute() and not (source / ".git").exists() and
            set(SOURCE_NAMES).issubset(specification["source_files"]), "fresh pinned source snapshot required")
    require(tree(source) == specification["source_files"], "source snapshot differs")
    material = load_material(specification)
    reflection = load_module(specification["reflection"], "reflection")
    probe = load_probe(specification["public"]["path"], specification["public"]["sha256"])
    require(callable(material.build_dataset) and callable(material.score_row), "material API differs")
    require(reflection.GPU_QUERY_SECONDS == GPU_QUERY_SECONDS, "reflection query budget differs")
    return material, reflection, probe


def learner_seed(value):
    require(type(value) is int and value in (0, 1, 2), "learner seed must be integer 0/1/2")
    return value


def fit_config(trainer, model, seed, count=TRAIN_ROWS):
    require(type(count) is int and count >= BATCH_SIZE and count % BATCH_SIZE == 0, "full four-row batches required")
    return asdict(trainer.TrainConfig(**dict(RECIPE, seed=learner_seed(seed), epochs=math.ceil(UPDATES * BATCH_SIZE / count)), model=model))


def source_key(row):
    source = row["source"]
    require(type(source) is dict and source, "nonempty source object required")
    key = source.get("source_id", source.get("situation_id", value_hash(source)))
    require(type(key) is str and key, "source identity required")
    return key


def validate_score(score, finish_reason):
    require(type(score) is dict and all(type(score.get(key)) is bool for key in
            ("passed", "content_correct", "strict")) and score["passed"] == score["content_correct"] and
            type(score.get("format")) is str and score["format"], "material content/strict/format scoring API differs")
    require(finish_reason == "stop" or not score["passed"], "unfinished output cannot pass")
    require(not score["strict"] or score["content_correct"], "strict success must also have correct content")
    encoded(score)


def validate_dataset(dataset):
    require(type(dataset) is dict and set(dataset) == {"schema", "qualification", "provenance", "training", "evaluation"}, "dataset API fields differ")
    require(isinstance(dataset["schema"], str) and dataset["schema"] and dataset["qualification"] and dataset["provenance"], "dataset provenance/qualification missing")
    require(set(dataset["evaluation"]) == set(PANELS), "held/canary panels required")
    partitions = {"training": dataset["training"], **dataset["evaluation"]}
    identifiers = []
    for name, count in (("training", TRAIN_ROWS), ("held", HELD_ROWS), ("canary", CANARY_ROWS)):
        rows = partitions[name]
        require(type(rows) is list and len(rows) == count, "fixed partition size differs: " + name)
        for row in rows:
            require(type(row) is dict and {"row_id", "input_messages", "raw_target", "target_sha256", "source", "source_proof"}.issubset(row), "row API fields differ")
            require(type(row["row_id"]) is str and row["row_id"] and type(row["source_proof"]) is dict and row["source_proof"], "row identity/proof missing")
            source_key(row)
            require(type(row["raw_target"]) is str and row["raw_target"] and
                    hashlib.sha256(row["raw_target"].encode()).hexdigest() == row["target_sha256"], "exact target SHA256 differs")
            messages = row["input_messages"]
            require(type(messages) is list and messages and all(type(message) is dict and set(message) == {"role", "content"} and
                    message["role"] in ("system", "user", "assistant") and type(message["content"]) is str for message in messages), "prompt messages differ")
            identifiers.append(row["row_id"])
    require(len(set(identifiers)) == len(identifiers), "duplicate or cross-partition row IDs")
    sources = [source_key(row) for rows in partitions.values() for row in rows]
    require(len(set(sources)) == len(sources), "duplicate or cross-partition sources; skins are not independent sources")


def training_item(row, tokenizer, trainer, probe, index):
    """Full native assistant bytes, including EOS; template-only tail is masked."""
    require(type(row["raw_target"]) is str and row["raw_target"] and
            hashlib.sha256(row["raw_target"].encode()).hexdigest() == row["target_sha256"], "exact sourced target required")
    prompt = probe.render(tokenizer, row["input_messages"])
    messages = row["input_messages"] + [{"role": "assistant", "content": row["raw_target"]}]
    full_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
    full_ids = token_ids(tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=False))
    require(full_ids == token_ids(tokenizer.encode(full_text, add_special_tokens=False)), "full-assistant template/token mismatch")
    prefix = prompt["rendered_prompt"]
    require(full_text.startswith(prefix + row["raw_target"]), "assistant prefix/target bytes changed")
    require(full_ids[:len(prompt["prompt_token_ids"])] == prompt["prompt_token_ids"], "assistant prefix token boundary changed")
    end_text, end_id = tokenizer.eos_token, tokenizer.eos_token_id
    require(isinstance(end_text, str) and end_text and type(end_id) is int, "native EOS unavailable")
    suffix = full_text[len(prefix + row["raw_target"]):]
    require(suffix.startswith(end_text), "native assistant end is not tokenizer EOS")
    trailer = suffix[len(end_text):]
    require(not trailer.strip() and token_ids(tokenizer.encode(end_text, add_special_tokens=False)) == [end_id],
            "unexpected assistant trailer/EOS encoding")
    spans = [[prefix, False, "context"], [row["raw_target"], True, "skill_target"],
             [end_text, True, "assistant_end"]]
    if trailer:
        spans.append([trailer, False, "template_tail"])
    item = trainer.normalize_items([dict(spans=spans, group=row["row_id"], order=index,
                                        view="authored_level1", meta=dict(source_id=source_key(row),
                                        row_id=row["row_id"], target_sha256=row["target_sha256"]))])[0]
    segments = trainer.encode_item_segments(item, tokenizer, MAX_LEN, False, False, index, overflow="truncate")
    require(len(segments) == 1, "training row dropped or split")
    segment = segments[0]
    require(segment.context_dropped == segment.target_dropped == 0 and len(full_ids) <= MAX_LEN, "training truncation forbidden")
    target_ids = token_ids(tokenizer.encode(row["raw_target"], add_special_tokens=False))
    require(end_id not in target_ids, "target contains assistant end token")
    tail_ids = tokenizer.encode(trailer, add_special_tokens=False) if trailer else []
    labels = [-100] * len(prompt["prompt_token_ids"]) + target_ids + [end_id] + [-100] * len(tail_ids)
    require(segment.ids == full_ids and segment.labels == labels and len(labels) == len(full_ids),
            "actual v3 encoding/mask differs from full native assistant")
    batch = trainer.collate([[segment]], tokenizer.pad_token_id)
    require(batch["input_ids"] == [full_ids] and batch["labels"] == [labels], "actual collate changed target mask")
    audit = dict(row_id=row["row_id"], input_ids=full_ids, labels=labels,
                 supervised_ids=target_ids + [end_id], native_prompt=prompt,
                 full_assistant_text=full_text, template_tail=trailer)
    return item, audit


def encode_training(rows, tokenizer, trainer, probe, seed=0):
    count = len(rows)
    configuration = fit_config(trainer, "CPU_CONFIGURATION_ONLY", seed, count)
    require(len({row["row_id"] for row in rows}) == count, "unique training rows required")
    require(tokenizer.pad_token_id is not None and tokenizer.pad_token_id != tokenizer.eos_token_id, "distinct native PAD/EOS required")
    pairs = [training_item(row, tokenizer, trainer, probe, index) for index, row in enumerate(rows)]
    items, audits = map(list, zip(*pairs))
    segments = [trainer.encode_item_segments(item, tokenizer, MAX_LEN, False, False, index, overflow="truncate")[0]
                for index, item in enumerate(items)]
    packs = trainer.pack_by_group(segments, MAX_LEN, False)
    require(len(packs) == count, "one sequence per sourced row required")
    row_sources = {row["row_id"]: source_key(row) for row in rows}
    presentations = {row["row_id"]: 0 for row in rows}
    batch_order, epoch_order = [], []
    tokens, targets, padded = 0, 0, 0
    for epoch in range(configuration["epochs"]):
        ordered = trainer.epoch_order(packs, learner_seed(seed), epoch, True)
        epoch_order.append([pack[0].group for pack in ordered])
        for start in range(0, count, BATCH_SIZE):
            selected = ordered[start:start + BATCH_SIZE]
            names = [pack[0].group for pack in selected]
            require(len(names) == BATCH_SIZE and len({row_sources[name] for name in names}) == BATCH_SIZE, "batch must contain four distinct sources")
            batch = trainer.collate(selected, tokenizer.pad_token_id)
            for pack, ids, labels in zip(selected, batch["input_ids"], batch["labels"], strict=True):
                segment = pack[0]
                require(ids[:len(segment.ids)] == segment.ids and labels[:len(segment.labels)] == segment.labels and
                        all(label == -100 for label in labels[len(segment.labels):]), "actual collate/masked padding differs")
            tokens += batch["n_tokens"]
            targets += batch["n_target"]
            padded += sum(len(ids) for ids in batch["input_ids"])
            batch_order.append(names)
            for name in names:
                presentations[name] += 1
            if len(batch_order) == UPDATES:
                break
        if len(batch_order) == UPDATES:
            break
    require(len(batch_order) == UPDATES and sum(presentations.values()) == UPDATES * BATCH_SIZE, "exact 320-update exposure required")
    return dict(items=items, encoding=audits, epoch_order=epoch_order, actual_batch_order=batch_order,
                target_tokens=sum(len(row["supervised_ids"]) for row in audits),
                total_tokens=sum(len(row["input_ids"]) for row in audits),
                updates=UPDATES, epochs_run=len(epoch_order), presentations=presentations,
                actual_train_tokens=tokens, actual_supervised_tokens=targets, actual_padded_tokens=padded,
                per_row=[dict(row_id=row["row_id"], total_tokens=len(row["input_ids"]),
                              supervised_tokens=len(row["supervised_ids"])) for row in audits])


def prepare_inputs(specification, material, probe):
    seed = learner_seed(specification["learner_seed"])
    material_seed = learner_seed(specification.get("material_seed", 0))
    skill = specification["skill"]
    require(type(skill) is str and skill, "explicit skill required")
    dataset = material.build_dataset(skill, seed=material_seed)
    validate_dataset(dataset)
    require(encoded(dataset) == encoded(material.build_dataset(skill, seed=material_seed)), "material rebuild not deterministic")
    for panel in PANELS:
        row = dataset["evaluation"][panel][0]
        score = material.score_row(row, row["raw_target"], "stop")
        validate_score(score, "stop")
        require(score["passed"] and score["strict"], "authored reference target fails material scorer self-check")
    _, trainer = source_api(specification["source"])
    tokenizer = probe.native_tokenizer(specification["model"])
    prepared = encode_training(dataset["training"], tokenizer, trainer, probe, seed)
    calls = []
    for panel in PANELS:
        for index, row in enumerate(dataset["evaluation"][panel]):
            native = probe.render(tokenizer, row["input_messages"])
            require(len(native["prompt_token_ids"]) + PARAMS["max_tokens"] <= ENGINE["max_model_len"], "readout context overflow")
            calls.append(dict(call_id=f"{panel}_{index:02d}", row_id=row["row_id"], panel=panel,
                              messages=row["input_messages"], native=native))
    return dataset, prepared, calls, fit_config(trainer, specification["model"], seed), tokenizer.chat_template


def prepare(root, spec_path, spec_sha256, allow_native=False):
    require(allow_native is True, "explicit --allow-native CPU tokenizer preflight required")
    offline()
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    require(digest(spec_path) == spec_sha256, "spec pin differs")
    specification = read(spec_path)
    root = Path(root).resolve()
    require(not root.exists(), "fresh root required; no retry")
    require(type(specification["gpu_index"]) is int and specification["gpu_index"] >= 0 and
            isinstance(specification["gpu_uuid"], str) and specification["gpu_uuid"].startswith("GPU-"), "planned GPU binding")
    require(type(specification["lease_end"]) in (int, float) and math.isfinite(specification["lease_end"]) and
            specification["lease_end"] >= time.time() + OUTER_SECONDS + COLLECTION_SECONDS + LEASE_MARGIN, "six-hour finish margin required")
    protected = [specification["source"], specification["model"], spec_path, SELF] + [specification[key]["path"] for key in
                 ("material", "reflection", "public", "protocol", "binding")]
    require(all(Path(value).is_absolute() and root != Path(value).resolve() and root not in Path(value).resolve().parents and
                Path(value).resolve() not in root.parents for value in protected), "absolute disjoint inputs/root required")
    root.mkdir()
    write(root / "prepare_started.json", dict(spec_sha256=spec_sha256, time=time.time()))
    try:
        material, reflection, probe = checked_apis(specification)
        binding = probe.scope_binding(read(specification["binding"]["path"]), specification["source"], specification["model"],
                                      specification["source_files"]["organism_v6/birth_skill_corpus.py"])
        require(binding["source_files"] == {name: specification["source_files"][name] for name in probe.SOURCE_NAMES} and
                binding["model_files"] == probe.model_hashes(specification["model"]) and
                binding["native_environment"] == probe.native_environment(), "public base/source/environment differs")
        dataset, prepared, calls, config, template = prepare_inputs(specification, material, probe)
        costs = {key: value for key, value in prepared.items() if key not in ("items", "encoding", "epoch_order", "actual_batch_order")}
        for name, value in {"material.json": dataset, "train.json": prepared, "calls.json": calls, "costs.json": costs}.items():
            write(root / name, value)
        plan = dict(scope=SCOPE, claim=CLAIM, root=str(root), specification=specification, spec_sha256=spec_sha256,
                    skill=specification["skill"], learner_seed=specification["learner_seed"], material_seed=specification.get("material_seed", 0),
                    source=specification["source"], model=specification["model"], binding=binding, model_files=binding["model_files"],
                    config=config, chat_template=template, stages=list(STAGES), engine=ENGINE, params=PARAMS,
                    self_sha256=digest(SELF), python=os.path.abspath(sys.executable), python_sha256=digest(sys.executable),
                    environment=environment(probe), gpu_index=specification["gpu_index"], gpu_uuid=specification["gpu_uuid"],
                    lease_end=specification["lease_end"], input_hashes={name: digest(root / name) for name in ("material.json", "train.json", "calls.json", "costs.json")},
                    budget=dict(controller=OUTER_SECONDS, collection=COLLECTION_SECONDS, cleanup_in_controller=CLEANUP_SECONDS,
                                fit=FIT_SECONDS, readout=READOUT_SECONDS, fits=1, readouts=2, calls=120,
                                historical_basis="SEQ113 320 updates; 1308.919s old paired controller, not a new-skill timing guarantee"))
        checked_apis(specification)
        write(root / "plan.json", plan)
        return dict(status="CPU_NATIVE_TOKENIZER_PREFLIGHT_COMPLETE_NOT_GPU_APPROVAL", root=str(root),
                    plan_sha256=digest(root / "plan.json"), costs=costs, budget=plan["budget"])
    except BaseException as error:
        failure(root / "prepare_failure.json", error)
        raise


def verify(root, plan_sha256, native=False):
    root = Path(root).resolve()
    require(digest(root / "plan.json") == plan_sha256, "plan hash differs")
    plan = read(root / "plan.json")
    require(plan["root"] == str(root) and plan["scope"] == SCOPE and plan["claim"] == CLAIM and
            plan["self_sha256"] == digest(SELF) and plan["python"] == os.path.abspath(sys.executable) and
            plan["python_sha256"] == digest(sys.executable), "runtime/interpreter identity differs")
    require(plan["stages"] == list(STAGES) and plan["engine"] == ENGINE and plan["params"] == PARAMS, "closed stage/configuration differs")
    require(read(root / "prepare_started.json")["spec_sha256"] == plan["spec_sha256"] and
            not (root / "prepare_failure.json").exists(), "preparation failed or binding differs")
    material, reflection, probe = checked_apis(plan["specification"])
    for field in ("source", "model", "gpu_index", "gpu_uuid", "lease_end", "skill", "learner_seed"):
        require(plan[field] == plan["specification"][field], "spec/plan field differs: " + field)
    require(plan["material_seed"] == plan["specification"].get("material_seed", 0), "material seed differs")
    require(set(plan["input_hashes"]) == {"material.json", "train.json", "calls.json", "costs.json"}, "prepared inventory differs")
    for name, checksum in plan["input_hashes"].items():
        require(digest(root / name) == checksum, "prepared input differs")
    _, trainer = source_api(plan["source"])
    require(plan["config"] == fit_config(trainer, plan["model"], plan["learner_seed"]), "fit recipe differs")
    if native:
        require(environment(probe) == plan["environment"] and probe.model_hashes(plan["model"]) == plan["model_files"], "native base/environment drift")
    return plan, probe




def check_fit_manifest(manifest, prepared, config):
    for field in ("steps", "micro_batches", "epochs_run", "nonfinite_batches"):
        require(type(manifest[field]) is int, "integer fit accounting required")
    counts = ([manifest["corpus"][key] for key in ("n_items", "n_encoded", "n_skipped_no_target")] +
              [manifest["truncation"][key] for key in ("items_truncated", "context_tokens_dropped", "target_tokens_dropped", "items_split")] +
              [manifest["packing"]["n_sequences"], manifest["tokens"]["target"], manifest["tokens"]["total"], manifest["train_tokens_seen"]])
    require(all(type(value) is int and value >= 0 for value in counts), "nonnegative integer token/item accounting required")
    require(manifest["config"] == config and manifest["empty"] is False and manifest["steps"] == UPDATES and
            manifest["micro_batches"] == UPDATES and manifest["epochs_run"] == prepared["epochs_run"] and
            manifest["nonfinite_batches"] == 0, "fit completion/update mismatch")
    count = len(prepared["items"])
    require(manifest["corpus"]["n_items"] == manifest["corpus"]["n_encoded"] == count and
            manifest["corpus"]["n_skipped_no_target"] == 0, "fit dropped items")
    require(all(manifest["truncation"][key] == 0 for key in
                ("items_truncated", "context_tokens_dropped", "target_tokens_dropped", "items_split")), "fit truncated/split items")
    require(manifest["packing"]["mode"] == "one_item_per_sequence" and manifest["packing"]["n_sequences"] == count, "fit packing differs")
    require(manifest["tokens"]["target"] == prepared["target_tokens"] and
            manifest["tokens"]["total"] == prepared["total_tokens"] and
            manifest["train_tokens_seen"] == prepared["actual_train_tokens"], "fit token exposure mismatch")
    require(not manifest.get("warm_start"), "warm parent forbidden")
    losses = manifest["mean_loss_per_epoch"]
    require(len(losses) == prepared["epochs_run"] and all(type(value) in (int, float) and math.isfinite(value)
            for value in losses + [manifest["final_loss"]]), "nonfinite/incomplete fit losses")


def check_adapter(adapter, config):
    inventory = tree(adapter)
    weights = [name for name in ("adapter_model.safetensors", "adapter_model.bin") if name in inventory]
    require(len(weights) == 1 and "adapter_config.json" in inventory and "DONE" in inventory, "incomplete adapter")
    saved = read(Path(adapter) / "adapter_config.json")
    require(saved["r"] == 8 and saved["lora_alpha"] == 16 and saved["lora_dropout"] == .05 and
            set(saved["target_modules"]) == set(config["target_modules"]) and saved.get("bias") == "none" and
            not saved.get("modules_to_save") and not saved.get("use_dora") and not saved.get("use_rslora"), "adapter structure differs")
    return inventory


def fit_one(plan, stage, probe):
    require(stage == "fit", "one fit only")
    _, trainer = source_api(plan["source"])
    prepared = read(Path(plan["root"]) / "train.json")
    fit_started = time.monotonic()
    reflection = load_module(plan["specification"]["reflection"], "reflection")
    tokenizer, base = reflection.load_native_model(plan["model"])
    require(not hasattr(base, "peft_config"), "fit must start from a cold base without a parent adapter")
    require(tokenizer.chat_template == plan["chat_template"], "fit template drift")
    require(tokenizer.pad_token_id is not None and tokenizer.pad_token_id != tokenizer.eos_token_id, "fit PAD/EOS changed")
    for index, (item, expected) in enumerate(zip(prepared["items"], prepared["encoding"], strict=True)):
        segments = trainer.encode_item_segments(item, tokenizer, MAX_LEN, False, False, index, overflow="truncate")
        require(len(segments) == 1 and segments[0].ids == expected["input_ids"] and segments[0].labels == expected["labels"] and
                segments[0].context_dropped == segments[0].target_dropped == 0, "actual fit encoding/mask drift")
    directory = Path(plan["root"]) / "run" / stage
    adapter = directory / "adapter"
    require(not adapter.exists(), "fresh adapter required")
    trainer.run_training(prepared["items"], tokenizer, base, trainer.TrainConfig(**plan["config"]), str(adapter),
                         corpus_sha=plan["input_hashes"]["train.json"], corpus_name="train.json")
    trainable = [name for name, parameter in base.named_parameters() if parameter.requires_grad]
    require(trainable and all("lora_A" in name or "lora_B" in name for name in trainable), "non-LoRA trainability")
    check_fit_manifest(read(adapter / "train_manifest.json"), prepared, plan["config"])
    files = check_adapter(adapter, plan["config"])
    write(directory / "fit.json", dict(adapter=str(adapter), adapter_files=files, updates=UPDATES,
          presentations=UPDATES * BATCH_SIZE, elapsed_seconds=time.monotonic() - fit_started,
          trainable_names_sha256=value_hash(trainable), initialized_from="fresh frozen base; no parent"))


def adapter_for(plan, state):
    require(state in STATES, "unknown readout state")
    if state == "OFF":
        return None, {}
    directory = Path(plan["root"]) / "run" / "fit"
    receipt = read(directory / "fit.json")
    adapter = directory / "adapter"
    require(receipt["adapter"] == str(adapter) and receipt["updates"] == UPDATES and
            receipt["presentations"] == UPDATES * BATCH_SIZE and receipt["adapter_files"] == check_adapter(adapter, plan["config"]), "fitted adapter custody differs")
    check_fit_manifest(read(adapter / "train_manifest.json"), read(Path(plan["root"]) / "train.json"), plan["config"])
    return str(adapter), receipt["adapter_files"]


class Native:
    def __init__(self, plan, probe, adapter):
        from vllm import LLM
        from vllm.lora.request import LoRARequest
        self.probe = probe
        self.llm = LLM(model=plan["model"], tokenizer=plan["model"], **ENGINE)
        self.tokenizer = self.llm.get_tokenizer()
        require(self.tokenizer.chat_template == plan["chat_template"], "readout template drift")
        self.route = None if adapter is None else dict(name="level1_skill", id=1, path=adapter)
        self.lora = None if self.route is None else LoRARequest(self.route["name"], self.route["id"], self.route["path"])

    def generate(self, messages):
        import torch
        from vllm import SamplingParams
        native = self.probe.render(self.tokenizer, messages)
        started = time.monotonic()
        with torch.inference_mode():
            outputs = self.llm.generate([native["rendered_prompt"]], SamplingParams(**PARAMS), lora_request=self.lora, use_tqdm=False)
        require(len(outputs) == 1 and len(outputs[0].outputs) == 1, "readout cardinality differs")
        output = outputs[0].outputs[0]
        return dict(**native, text=output.text, output_token_ids=list(output.token_ids),
                    actual_prompt_token_ids=list(outputs[0].prompt_token_ids), finish_reason=output.finish_reason,
                    stop_reason=output.stop_reason, decoded_output=self.tokenizer.decode(list(output.token_ids), skip_special_tokens=True),
                    started=started, ended=time.monotonic(), lora_request=self.route)

    def close(self):
        shutdown = getattr(self.llm, "shutdown", None)
        if shutdown is not None:
            shutdown()


def capture_cell(plan, cell, probe):
    adapter, files = adapter_for(plan, cell)
    directory = Path(plan["root"]) / "run" / cell
    route = None if adapter is None else dict(name="level1_skill", id=1, path=adapter)
    identity = dict(cell=cell, model=plan["model"], revision=plan["binding"]["revision"], model_files=plan["model_files"],
                    adapter=adapter, adapter_files=files, lora_request=route, engine=ENGINE, params=PARAMS)
    write(directory / "identity.json", identity)
    calls = read(Path(plan["root"]) / "calls.json")
    backend = None
    try:
        backend = Native(plan, probe, adapter)
        for call in calls:
            write(directory / (call["call_id"] + ".request.json"), call)
            response = backend.generate(call["messages"])
            write(directory / (call["call_id"] + ".response.json"), response)
            require(response["lora_request"] == route, "actual LoRA route differs")
            probe.validate_response(call, response)
    finally:
        if backend is not None:
            backend.close()
    require(files == (tree(adapter) if adapter is not None else {}), "adapter changed during readout")
    names = ["identity.json"] + [call["call_id"] + suffix for call in calls for suffix in (".request.json", ".response.json")]
    write(directory / "closed.json", dict(calls=60, files={name: digest(directory / name) for name in names}))


def worker(root, plan_sha256, stage, allow_gpu=False):
    require(allow_gpu, "Main-only worker requires --allow-gpu")
    require(stage in STAGES and os.getpid() == os.getpgrp(), "worker must own a fresh process group")
    offline()
    plan, probe = verify(root, plan_sha256, native=True)
    require(os.environ.get("CUDA_VISIBLE_DEVICES") == plan["gpu_uuid"] and time.time() < plan["lease_end"] - COLLECTION_SECONDS - LEASE_MARGIN,
            "worker device/lease differs")
    directory = Path(root) / "run" / stage
    write(directory / "started.json", dict(pid=os.getpid(), pgid=os.getpgrp(), stage=stage, plan_sha256=plan_sha256, time=time.time()))
    try:
        if stage == "fit":
            fit_one(plan, stage, probe)
        else:
            capture_cell(plan, stage, probe)
    except BaseException as error:
        failure(directory / "failure.json", error)
        raise


@contextlib.contextmanager
def budget(seconds):
    require(seconds > 0, "no remaining budget")
    def expired(signum, frame):
        raise TimeoutError("Level1 bounded deadline exceeded")
    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def run_stage(plan, pin, stage, deadline, probe):
    require(deadline - time.monotonic() > GPU_QUERY_SECONDS + CLEANUP_SECONDS, "insufficient budget for vacancy and release checks")
    require(probe.gpu_state(plan) is True, "assigned GPU not vacant; no foreign process will be stopped")
    seconds = min(FIT_SECONDS if stage == "fit" else READOUT_SECONDS, deadline - time.monotonic() - CLEANUP_SECONDS)
    require(seconds > 0, "insufficient outer budget for next stage")
    directory = Path(plan["root"]) / "run" / stage
    directory.mkdir()
    command = [plan["python"], "-B", str(SELF), "worker", "--root", plan["root"], "--plan-sha256", pin,
               "--stage", stage, "--allow-gpu"]
    env = dict(os.environ, CUDA_VISIBLE_DEVICES=plan["gpu_uuid"])
    process = None
    try:
        with (directory / "stdout.log").open("xb") as output, (directory / "stderr.log").open("xb") as errors:
            process = subprocess.Popen(command, env=env, stdout=output, stderr=errors, start_new_session=True)
            write(directory / "launch.json", dict(pid=process.pid, pgid=process.pid, stage=stage, plan_sha256=pin))
            require(process.wait(timeout=seconds) == 0, "native worker failed: " + stage)
    finally:
        if process is not None:
            try:
                probe.cleanup(process)
                require(not probe.group_alive(process.pid), "owned process group survived cleanup")
                require(probe.gpu_state(plan) is True, "GPU release not confirmed")
                write(directory / "released.json", dict(pid=process.pid, pgid=process.pid, time=time.time()))
            except BaseException as error:
                failure(directory / "cleanup_failure.json", error)
                raise


def validate_completed(plan, pin, probe):
    root = Path(plan["root"])
    processes, inventory = [], {}
    for stage in STAGES:
        directory = root / "run" / stage
        require(not (directory / "failure.json").exists() and not (directory / "cleanup_failure.json").exists(), "failed stage cannot complete")
        started, launched, released = (read(directory / name) for name in ("started.json", "launch.json", "released.json"))
        require(type(started["pid"]) is int and started["pid"] > 1 and started["pid"] == started["pgid"] ==
                launched["pid"] == launched["pgid"] == released["pid"] == released["pgid"] and
                started["stage"] == launched["stage"] == stage and started["plan_sha256"] == launched["plan_sha256"] == pin,
                "fresh process receipt mismatch")
        processes.append(started["pid"])
        if stage == "fit":
            adapter_for(plan, "post")
        else:
            adapter, files = adapter_for(plan, stage)
            identity, closed = read(directory / "identity.json"), read(directory / "closed.json")
            route = None if adapter is None else dict(name="level1_skill", id=1, path=adapter)
            require(identity == dict(cell=stage, model=plan["model"], revision=plan["binding"]["revision"], model_files=plan["model_files"],
                                     adapter=adapter, adapter_files=files, lora_request=route, engine=ENGINE, params=PARAMS), "readout identity mismatch")
            calls = read(root / "calls.json")
            expected_names = {"identity.json"} | {call["call_id"] + suffix for call in calls for suffix in (".request.json", ".response.json")}
            require(closed["calls"] == 60 and set(closed["files"]) == expected_names, "incomplete raw capture inventory")
            require({path.name for path in directory.glob("*.response.json")} == {call["call_id"] + ".response.json" for call in calls},
                    "raw response count mismatch")
            for name, expected in closed["files"].items():
                require(digest(directory / name) == expected, "raw capture changed")
            for call in calls:
                require(read(directory / (call["call_id"] + ".request.json")) == call, "captured request differs")
                response = read(directory / (call["call_id"] + ".response.json"))
                require(response["lora_request"] == route, "captured adapter route differs")
                probe.validate_response(call, response)
        inventory[stage] = tree(directory)
    require(len(set(processes)) == 3, "OFF/fit/post must use three distinct fresh processes")
    return inventory


def controller(root, plan_sha256, allow_gpu=False):
    require(allow_gpu, "Main-only controller requires --allow-gpu")
    offline()
    root = Path(root).resolve()
    write(root / "controller_started.json", dict(time=time.time(), plan_sha256=plan_sha256))
    deadline = time.monotonic() + OUTER_SECONDS
    try:
        with budget(OUTER_SECONDS - CLEANUP_SECONDS):
            plan, probe = verify(root, plan_sha256, native=True)
            require(plan["lease_end"] > time.time() + OUTER_SECONDS + COLLECTION_SECONDS + LEASE_MARGIN,
                    "launch no longer fits lease")
            (root / "run").mkdir()
            for stage in STAGES:
                run_stage(plan, plan_sha256, stage, deadline, probe)
            inventory = validate_completed(plan, plan_sha256, probe)
            require(time.monotonic() < deadline, "outer deadline exceeded")
            write(root / "capture_complete.json", dict(plan_sha256=plan_sha256, stages=inventory, calls=120,
                                                       scored=False, time=time.time(), elapsed_seconds=OUTER_SECONDS - (deadline - time.monotonic())))
        return dict(status="ALL_CAPTURES_CLOSED_UNSCORED", completion_sha256=digest(root / "capture_complete.json"))
    except BaseException as error:
        failure(root / "controller_failure.json", error)
        raise


def collect(root, plan_sha256, completion_sha256, out):
    offline()
    root, out = Path(root).resolve(), Path(out).resolve()
    require(not out.exists() and root != out and root not in out.parents and out not in root.parents, "fresh external collection required")
    write(root.with_name(root.name + ".collection_claim.json"), dict(plan_sha256=plan_sha256, out=str(out), retry=False))
    out.mkdir()
    try:
        with budget(COLLECTION_SECONDS):
            plan, probe = verify(root, plan_sha256)
            require(not (root / "controller_failure.json").exists(), "failed controller not scorable; preserve partial artifacts")
            require(digest(root / "capture_complete.json") == completion_sha256, "completion pin differs")
            complete = read(root / "capture_complete.json")
            require(complete["plan_sha256"] == plan_sha256 and complete["calls"] == 120 and complete["scored"] is False,
                    "all captures must close before scoring")
            require(validate_completed(plan, plan_sha256, probe) == complete["stages"], "completed custody changed")
            material = load_material(plan["specification"])
            dataset = read(root / "material.json")
            require(encoded(dataset) == encoded(material.build_dataset(plan["skill"], seed=plan["material_seed"])), "material replay differs")
            results, costs = {}, {}
            for state in STATES:
                results[state], costs[state] = {}, {}
                for panel in PANELS:
                    scored, responses = [], []
                    for index, row in enumerate(dataset["evaluation"][panel]):
                        path = root / "run" / state / f"{panel}_{index:02d}.response.json"
                        response = read(path)
                        score = material.score_row(row, response["text"], response["finish_reason"])
                        validate_score(score, response["finish_reason"])
                        scored.append(dict(row_id=row["row_id"], raw=response["text"], finish_reason=response["finish_reason"],
                                           response_sha256=digest(path), score=score))
                        responses.append(response)
                    results[state][panel] = dict(total=len(scored), passed=sum(row["score"]["passed"] for row in scored),
                                                content_correct=sum(row["score"]["content_correct"] for row in scored),
                                                strict=sum(row["score"]["strict"] for row in scored),
                                                format_counts=dict(Counter(row["score"]["format"] for row in scored)), rows=scored)
                    costs[state][panel] = dict(calls=len(responses), prompt_tokens=sum(len(value["actual_prompt_token_ids"]) for value in responses),
                              output_tokens=sum(len(value["output_token_ids"]) for value in responses),
                              generation_seconds=sum(value["ended"] - value["started"] for value in responses))
            report = dict(scope=SCOPE, claim=CLAIM, skill=plan["skill"], learner_seed=plan["learner_seed"], material_seed=plan["material_seed"],
                          plan_sha256=plan_sha256, completion_sha256=completion_sha256, cells=results, calls=120,
                          primary_metric="content_correct (passed); finish=stop required; exact typed content per pinned material scorer",
                          secondary_metric="strict canonical raw format; format categories reported separately",
                          fit=read(root / "run/fit/fit.json"), fit_manifest=read(root / "run/fit/adapter/train_manifest.json"),
                          generation_costs=costs, training_costs=read(root / "costs.json"),
                          paired_post_minus_OFF={panel: dict(numerator=results["post"][panel]["passed"] - results["OFF"][panel]["passed"],
                                                            denominator=results["OFF"][panel]["total"]) for panel in PANELS},
                          material_provenance=dataset["provenance"], material_qualification=dataset["qualification"],
                          controller_elapsed_seconds=complete["elapsed_seconds"], automatic_pass=False, scientific_pass=None)
            write(out / "scores.json", report)
            write(out / "collection.json", dict(scores_sha256=digest(out / "scores.json"), completion_sha256=completion_sha256))
            return dict(status="COLLECTED_AUTHORED_LEVEL1_ONLY", out=str(out), scores_sha256=digest(out / "scores.json"))
    except BaseException as error:
        failure(out / "collection_failure.json", error)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prep = commands.add_parser("prepare")
    for name in ("root", "spec-path", "spec-sha256"):
        prep.add_argument("--" + name, required=True)
    prep.add_argument("--allow-native", action="store_true")
    for name in ("controller", "worker", "collect"):
        command = commands.add_parser(name)
        command.add_argument("--root", required=True)
        command.add_argument("--plan-sha256", required=True)
        if name != "collect":
            command.add_argument("--allow-gpu", action="store_true")
        if name == "worker":
            command.add_argument("--stage", choices=STAGES, required=True)
        if name == "collect":
            command.add_argument("--completion-sha256", required=True)
            command.add_argument("--out", required=True)
    arguments = vars(parser.parse_args(argv))
    name = arguments.pop("command")
    result = {"prepare": prepare, "controller": controller, "worker": worker, "collect": collect}[name](**arguments)
    if result is not None:
        print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
