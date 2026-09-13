"""Prospectively selected learner-seed 1/2 reflection replicas; Main alone launches.

Prepare uses the native tokenizer on CPU, never a model. Two cold fits precede
six isolated readouts. Collection alone scores after all 144 raw captures close.
Main supplies FINAL source/helper pins; no in-progress corpus hash is frozen.
"""
from __future__ import annotations

import argparse
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
SCOPE = "authored_reflection_12train_24dev_learner_seed_replication_v1"
LEARNER_SEEDS = (1, 2)
PARENT_DRIVER_SHA256 = "0f79efa1f4e4da6a9d1ec245c09e665f7c2b7d8bce31f7e01fe01b00f95a72fc"
ARMS = ("withdrawn", "present")
STATES = ("OFF", "fitWithdrawn", "fitPresent")
CELLS = tuple(f"{state}__{anchor}" for state in STATES for anchor in ARMS)
STAGES = ("fit_withdrawn", "fit_present") + CELLS
OUTER_SECONDS, COLLECTION_SECONDS = 3600, 180
GPU_QUERY_SECONDS, GROUP_CLEANUP_SECONDS = 30, 10
CLEANUP_SECONDS = GROUP_CLEANUP_SECONDS + GPU_QUERY_SECONDS
FIT_SECONDS, READOUT_SECONDS = 600, 300
SOURCE_NAMES = ("organism_v6/__init__.py", "organism_v6/birth_skill_corpus.py",
                "organism_v6/rulegame_parenting_diagnostic.py", "organism_v6/train_adapter_v3.py",
                "organism_v6/birth_reflection_probe.py")
PARAMS = dict(temperature=0.0, seed=0, max_tokens=192, top_p=1.0, top_k=-1, n=1,
              presence_penalty=0.0, frequency_penalty=0.0, repetition_penalty=1.0, ignore_eos=False)
ENGINE = dict(max_model_len=16384, tensor_parallel_size=1, seed=0,
              gpu_memory_utilization=0.85, enforce_eager=True, enable_lora=True,
              max_lora_rank=32, enable_prefix_caching=False, dtype="bfloat16", trust_remote_code=False)
RECIPE = dict(rank=8, alpha=16, dropout=.05, lr=1e-4, epochs=4, max_len=1024,
              seed=0, overflow="truncate", batch_size=4, grad_accum=1, pack=False,
              shuffle_groups=True, chat_template=False, add_eos=False, optimizer="adamw",
              grad_checkpoint=True, device="cuda", dtype="bf16", max_steps=0)
GENERIC_SYSTEM = "You are a helpful assistant."
PANELS = ("restatement", "application")
CLAIM = ("INDEPENDENTLY_PRESELECTED_AUTHORED_DEVELOPMENT_ONLY; exact authored restatement is not semantic prose "
         "failure; strict A/B near-transfer application is separate; not teacher distillation, clean ancestry, "
         "persistence, L2, H1/H2 qualification, or automatic promotion")
BINDING_SCOPE = "official_public_revision_files_only_v1"
SCOPE_EXPLANATION = ("Any upstream NO_FIT label describes the historical model-file receipt only, not this runtime. "
                     "This runtime explicitly performs two cold authored fits and six matched readouts. "
                     "Official file equality does not certify clean model ancestry.")
RECIPE["note"] = SCOPE + "; " + SCOPE_EXPLANATION


def require(condition, message):
    if not condition:
        raise ValueError(message)


def learner_recipe(learner_seed):
    require(type(learner_seed) is int and learner_seed in LEARNER_SEEDS, "learner_seed must be integer 1 or 2")
    return dict(RECIPE, seed=learner_seed)


def seed_matches(value, expected):
    return type(value) is int and type(expected) is int and value in LEARNER_SEEDS and value == expected


def bound_learner_seed(root, plan_sha256):
    path = Path(root) / "plan.json"
    require(digest(path) == plan_sha256, "plan hash differs")
    plan = read(path)
    learner_recipe(plan.get("learner_seed"))
    require(plan.get("parent_driver_sha256") == PARENT_DRIVER_SHA256, "replication parent source differs")
    return plan["learner_seed"]


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
    os.link(temporary, path)
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
    require(digest(path) == expected, "public helper final driver hash differs")
    spec = importlib.util.spec_from_file_location("reflection_final_public_probe", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    require(getattr(module, "GPU_QUERY_SECONDS", None) == GPU_QUERY_SECONDS, "public helper final driver must allow 30s NVML queries")
    return module


def source_api(source):
    source = Path(source).resolve()
    for name, module in list(sys.modules.items()):
        if name == "organism_v6" or name.startswith("organism_v6."):
            require(getattr(module, "__file__", None) and
                    Path(module.__file__).resolve().is_relative_to(source), "cached source import outside snapshot")
    sys.path.insert(0, str(source))
    modules = [importlib.import_module("organism_v6." + name)
               for name in ("birth_reflection_probe", "train_adapter_v3")]
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


def training_item(row, tokenizer, trainer, probe, index):
    """Full native assistant bytes, including EOS; template-only tail is masked."""
    require(row["panel"] == "restatement" and row["split"] == "train" and
            row["source"]["split"] == "train" and isinstance(row["response_target"], str)
            and row["response_target"], "restatement TRAIN target required")
    validate_messages(row["input_messages"])
    prompt = probe.render(tokenizer, row["input_messages"])
    messages = row["input_messages"] + [{"role": "assistant", "content": row["response_target"]}]
    full_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
    full_ids = token_ids(tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=False))
    require(full_ids == token_ids(tokenizer.encode(full_text, add_special_tokens=False)), "full-assistant template/token mismatch")
    prefix = prompt["rendered_prompt"]
    require(full_text.startswith(prefix + row["response_target"]), "assistant prefix/target bytes changed")
    require(full_ids[:len(prompt["prompt_token_ids"])] == prompt["prompt_token_ids"], "assistant prefix token boundary changed")
    end_text, end_id = tokenizer.eos_token, tokenizer.eos_token_id
    require(isinstance(end_text, str) and end_text and type(end_id) is int, "native EOS unavailable")
    suffix = full_text[len(prefix + row["response_target"]):]
    require(suffix.startswith(end_text), "native assistant end is not tokenizer EOS")
    trailer = suffix[len(end_text):]
    require(not trailer.strip() and token_ids(tokenizer.encode(end_text, add_special_tokens=False)) == [end_id],
            "unexpected assistant trailer/EOS encoding")
    require(len(full_ids) <= RECIPE["max_len"], "training truncation forbidden before native encoder")
    require(prompt["actual_system_text"] == GENERIC_SYSTEM, "native generic system drift")
    spans = [[prefix, False, "context"], [row["response_target"], True, "authored_restatement"],
             [end_text, True, "assistant_end"]]
    if trailer:
        spans.append([trailer, False, "template_tail"])
    item = trainer.normalize_items([dict(spans=spans, group=row["row_id"], order=index,
                                        view="restatement", meta=dict(source_id=row["source"]["source_id"],
                                        row_id=row["row_id"], target_sha256=row["target_sha256"]))])[0]
    segments = trainer.encode_item_segments(item, tokenizer, 1024, False, False, index, overflow="truncate")
    require(len(segments) == 1, "training row dropped or split")
    segment = segments[0]
    require(segment.context_dropped == segment.target_dropped == 0 and len(full_ids) <= 1024, "training truncation forbidden")
    target_ids = token_ids(tokenizer.encode(row["response_target"], add_special_tokens=False))
    require(end_id not in target_ids, "target contains assistant end token")
    tail_ids = tokenizer.encode(trailer, add_special_tokens=False) if trailer else []
    labels = [-100] * len(prompt["prompt_token_ids"]) + target_ids + [end_id] + [-100] * len(tail_ids)
    require(segment.ids == full_ids and segment.labels == labels and len(labels) == len(full_ids),
            "actual v3 encoding/mask differs from full native assistant")
    batch = trainer.collate([[segment]], tokenizer.pad_token_id)
    require(batch["input_ids"] == [full_ids] and batch["labels"] == [labels], "actual collate changed target mask")
    audit = dict(row_id=row["row_id"], input_ids=full_ids, labels=labels,
                 supervised_ids=target_ids + [end_id], native_prompt=prompt,
                 full_assistant_text=full_text, template_tail=trailer,
                 prompt_tokens=len(prompt["prompt_token_ids"]), target_tokens=len(target_ids),
                 supervised_tokens=len(target_ids) + 1, input_tokens=len(full_ids),
                 prompt_utf8_bytes=len(prefix.encode()), target_utf8_bytes=len(row["response_target"].encode()),
                 full_assistant_utf8_bytes=len(full_text.encode()), response_target=row["response_target"])
    return item, audit


def encode_training(rows, tokenizer, trainer, probe, learner_seed):
    learner_recipe(learner_seed)
    require(len(rows) == 12 and len({row["row_id"] for row in rows}) == 12, "TRAIN12 inventory required")
    require(tokenizer.pad_token_id is not None and tokenizer.pad_token_id != tokenizer.eos_token_id,
            "distinct native PAD/EOS required")
    pairs = [training_item(row, tokenizer, trainer, probe, index) for index, row in enumerate(rows)]
    items, audits = map(list, zip(*pairs))
    segments = [trainer.encode_item_segments(item, tokenizer, 1024, False, False, index, overflow="truncate")[0]
                for index, item in enumerate(items)]
    packs = trainer.pack_by_group(segments, 1024, False)
    orders, batches = [], []
    for epoch in range(4):
        order = trainer.epoch_order(packs, learner_seed, epoch, True)
        orders.append([pack[0].group for pack in order])
        for start in range(0, 12, 4):
            selected = order[start:start + 4]
            batch = trainer.collate(selected, tokenizer.pad_token_id)
            batches.append(dict(epoch=epoch, row_ids=[pack[0].group for pack in selected],
                                input_tokens=sum(len(pack[0].ids) for pack in selected),
                                padded_tokens=sum(len(ids) for ids in batch["input_ids"]),
                                supervised_tokens=sum(label != -100 for labels in batch["labels"] for label in labels)))
            for pack, ids, labels in zip(selected, batch["input_ids"], batch["labels"], strict=True):
                segment = pack[0]
                require(ids[:len(segment.ids)] == segment.ids and labels[:len(segment.labels)] == segment.labels,
                        "actual batch changed source labels")
                require(all(label == -100 for label in labels[len(segment.labels):]), "padding receives loss")
    return dict(learner_seed=learner_seed, items=items, encoding=audits, epoch_order=orders, batch_exposure=batches,
                prompt_tokens=sum(row["prompt_tokens"] for row in audits),
                authored_target_tokens=sum(row["target_tokens"] for row in audits),
                target_utf8_bytes=sum(row["target_utf8_bytes"] for row in audits),
                prompt_utf8_bytes=sum(row["prompt_utf8_bytes"] for row in audits),
                target_tokens=sum(len(row["supervised_ids"]) for row in audits),
                total_tokens=sum(len(row["input_ids"]) for row in audits))


def validate_messages(messages):
    require(isinstance(messages, list) and len(messages) == 2 and
            messages[0] == {"role": "system", "content": GENERIC_SYSTEM} and
            set(messages[1]) == {"role", "content"} and messages[1]["role"] == "user" and
            isinstance(messages[1]["content"], str) and messages[1]["content"],
            "explicit generic system and user only; metadata forbidden")


def public_binding(receipt, source, model, corpus_hash, probe):
    upstream = probe.scope_binding(receipt, source, model, corpus_hash)
    require(upstream["source_files"] == {name: digest(Path(source) / name) for name in probe.SOURCE_NAMES},
            "base/source binding drift")
    return dict(upstream, scope=BINDING_SCOPE, upstream_receipt_scope=upstream["scope"],
                scope_explanation=SCOPE_EXPLANATION, clean_ancestry_certified=False)


def source_snapshot(source, pins):
    source = Path(source).resolve()
    require(source.is_dir() and not (source / ".git").exists() and
            not any((parent / ".git").is_file() or (parent / ".git" / "HEAD").is_file() for parent in source.parents),
            "Main must provide a fresh non-checkout source snapshot")
    require(set(pins) == set(SOURCE_NAMES) and all(isinstance(value, str) and len(value) == 64 and
            all(character in "0123456789abcdef" for character in value) for value in pins.values()),
            "Main final source pin inventory required")
    require(tree(source) == pins, "fresh source snapshot differs from Main final pins")


def panel_inputs(corpus):
    trains, dev, exports = {}, {}, {}
    for arm in ARMS:
        built = corpus.build_panel("restatement", split="train", parent_condition=arm)
        exported = corpus.export_training(built)
        rows = built["rows"]
        require(len(rows) == 12 and len({row["row_id"] for row in rows}) == 12, "TRAIN12 inventory required")
        require(exported["records"] == [dict(input_messages=row["input_messages"],
                response_target=row["response_target"]) for row in rows], "TRAIN export visibility/schema drift")
        require(exported["report"]["application_rows"] == exported["report"]["dev_rows"] == 0,
                "application or DEV rows in loss")
        trains[arm], dev[arm] = rows, []
        exports[arm] = {"training_report": exported["report"], "development_reports": {}}
        for panel in PANELS:
            held = corpus.build_panel(panel, split="dev", parent_condition=arm)
            exported_dev = corpus.export_development(held)
            require(exported_dev["scoring_rows"] == held["rows"] and len(held["rows"]) == 12,
                    "DEV12 panel inventory required")
            require(exported_dev["requests"] == [dict(input_messages=row["input_messages"]) for row in held["rows"]],
                    "DEV target/metadata in model export")
            require(all(row["panel"] == panel and row["split"] == "dev" for row in held["rows"]), "DEV panel mismatch")
            dev[arm].extend(held["rows"])
            exports[arm]["development_reports"][panel] = exported_dev["report"]
        require(len({row["row_id"] for row in dev[arm]}) == 24, "duplicate DEV IDs")
        for row in trains[arm] + dev[arm]:
            validate_messages(row["input_messages"])
            require(row["parent_condition"] == arm, "parent condition drift")
        for field in ("source_id", "template_id"):
            require(not {row["source"][field] for row in trains[arm]} &
                    {row["source"][field] for row in dev[arm]}, "same-source/template TRAIN/DEV leakage")
        train_events = {(event["raw_response"], event["raw_outcome"]) for row in trains[arm]
                        for event in row["source"]["events"]}
        dev_events = {(event["raw_response"], event["raw_outcome"]) for row in dev[arm]
                      for event in row["source"]["events"]}
        require(not train_events & dev_events, "TRAIN/DEV event leakage")
        require(not {row["response_target"] for row in trains[arm]} &
                {row["response_target"] for row in dev[arm]}, "TRAIN/DEV target leakage")
    for sets in (trains, dev):
        for withdrawn, present in zip(sets["withdrawn"], sets["present"], strict=True):
            require({key: value for key, value in withdrawn.items() if key not in
                    ("parent_condition", "input_messages", "input_sha256")} ==
                    {key: value for key, value in present.items() if key not in
                    ("parent_condition", "input_messages", "input_sha256")}, "paired source/target/order drift")
            require(withdrawn["input_messages"] != present["input_messages"], "correction withdrawal absent")
    return trains, dev, exports


def prepare(root, source, model, probe_driver, probe_sha256, binding_path, binding_sha256,
            corpus_sha256, reflection_sha256, source_pins_path, source_pins_sha256,
            gpu_uuid, gpu_index, lease_end, log_dir, learner_seed):
    recipe = learner_recipe(learner_seed)
    offline()
    root, source, model, log_dir = map(lambda value: Path(value).resolve(), (root, source, model, log_dir))
    probe = load_probe(probe_driver, probe_sha256)
    inputs = (source, model, Path(probe_driver).resolve(), Path(binding_path).resolve(),
              Path(source_pins_path).resolve(), SELF)
    require(not root.exists() and not log_dir.exists() and probe.disjoint(root, log_dir) and
            all(probe.disjoint(output, path) for output in (root, log_dir) for path in inputs),
            "new disjoint root/log directories required")
    require(model.is_dir(), "existing locally verified official model directory required")
    require(type(gpu_index) is int and gpu_index >= 0 and isinstance(gpu_uuid, str) and gpu_uuid.startswith("GPU-"),
            "GPU binding required")
    require(math.isfinite(lease_end) and lease_end > time.time() + OUTER_SECONDS + COLLECTION_SECONDS + CLEANUP_SECONDS,
            "insufficient lease for outer plus collection")
    require(digest(source_pins_path) == source_pins_sha256, "Main final source pins receipt differs")
    hashes = read(source_pins_path)
    source_snapshot(source, hashes)
    require(hashes["organism_v6/birth_skill_corpus.py"] == corpus_sha256 and
            hashes["organism_v6/birth_reflection_probe.py"] == reflection_sha256, "Main final corpus/probe hash differs")
    root.mkdir()
    log_dir.mkdir()
    write(root / "prepare_started.json", dict(time=time.time(), scope=SCOPE, learner_seed=learner_seed))
    try:
        require(digest(binding_path) == binding_sha256, "Main base receipt hash differs")
        receipt = read(binding_path)
        binding = public_binding(receipt, source, model, corpus_sha256, probe)
        require(binding["model_files"] == probe.model_hashes(model) and
                binding["native_environment"] == probe.native_environment(), "model/environment drift")
        corpus, trainer = source_api(source)
        tokenizer = probe.native_tokenizer(str(model))
        train_rows, dev, exports = panel_inputs(corpus)
        trains, calls = {}, {}
        for arm in ARMS:
            trains[arm] = encode_training(train_rows[arm], tokenizer, trainer, probe, learner_seed)
            calls[arm] = [dict(call_id=f"{index:02d}", row_id=row["row_id"], messages=row["input_messages"],
                               native=probe.render(tokenizer, row["input_messages"])) for index, row in enumerate(dev[arm])]
            require(all(call["native"]["actual_system_text"] == GENERIC_SYSTEM for call in calls[arm]), "DEV system drift")
        require(trains["withdrawn"]["epoch_order"] == trains["present"]["epoch_order"], "fit row order differs")
        require([row["supervised_ids"] for row in trains["withdrawn"]["encoding"]] ==
                [row["supervised_ids"] for row in trains["present"]["encoding"]], "target/EOS exposure differs")
        artifacts = {"train_withdrawn.json": trains["withdrawn"], "train_present.json": trains["present"],
                     "dev.json": dev, "calls.json": calls, "exports.json": exports,
                     "binding_receipt.json": receipt, "source_pins.json": hashes}
        for name, content in artifacts.items():
            write(root / name, content)
        config = asdict(trainer.TrainConfig(**recipe, model=str(model)))
        plan = dict(scope=SCOPE, claim=CLAIM, learner_seed=learner_seed, parent_driver_sha256=PARENT_DRIVER_SHA256, root=str(root), source=str(source), source_hashes=hashes,
                    source_pins_sha256=source_pins_sha256, binding_receipt_sha256=binding_sha256,
                    log_dir=str(log_dir), model=str(model), binding=binding, model_files=binding["model_files"],
                    environment=environment(probe), probe_driver=str(Path(probe_driver).resolve()),
                    probe_sha256=probe_sha256, self_sha256=digest(SELF), python=os.path.abspath(sys.executable),
                    generic_system=GENERIC_SYSTEM, gpu_uuid=gpu_uuid, gpu_index=gpu_index, lease_end=lease_end,
                    engine=ENGINE, params=PARAMS, stages=list(STAGES), config=config, chat_template=tokenizer.chat_template,
                    outer_seconds=OUTER_SECONDS, collection_seconds=COLLECTION_SECONDS, gpu_query_seconds=GPU_QUERY_SECONDS,
                    fit_seconds=FIT_SECONDS, readout_seconds=READOUT_SECONDS, truncation_allowed=False,
                    calls=144, input_hashes={name: digest(root / name) for name in artifacts})
        source_snapshot(source, hashes)
        require(digest(probe_driver) == probe_sha256, "public helper changed during prepare")
        write(root / "plan.json", plan)
        return dict(status="PREPARED_NOT_LAUNCHED", learner_seed=learner_seed, root=str(root), plan_sha256=digest(root / "plan.json"))
    except BaseException as error:
        failure(root / "prepare_failure.json", error)
        raise


def verify(root, plan_sha256, native=False):
    root = Path(root).resolve()
    require(digest(root / "plan.json") == plan_sha256, "plan hash differs")
    plan = read(root / "plan.json")
    recipe = learner_recipe(plan.get("learner_seed"))
    require(plan.get("parent_driver_sha256") == PARENT_DRIVER_SHA256, "replication parent source differs")
    require(plan["root"] == str(root) and plan["scope"] == SCOPE and plan["claim"] == CLAIM and
            plan["self_sha256"] == digest(SELF) and plan["python"] == os.path.abspath(sys.executable), "runtime identity differs")
    require(plan["stages"] == list(STAGES) and plan["engine"] == ENGINE and plan["params"] == PARAMS and
            plan["outer_seconds"] == OUTER_SECONDS and plan["collection_seconds"] == COLLECTION_SECONDS and
            plan["gpu_query_seconds"] == GPU_QUERY_SECONDS and plan["fit_seconds"] == FIT_SECONDS and
            plan["readout_seconds"] == READOUT_SECONDS and plan["calls"] == 144 and
            plan["truncation_allowed"] is False and plan["generic_system"] == GENERIC_SYSTEM, "runtime scope differs")
    source_snapshot(plan["source"], plan["source_hashes"])
    require(set(plan["input_hashes"]) == {"train_withdrawn.json", "train_present.json", "dev.json", "calls.json",
            "exports.json", "binding_receipt.json", "source_pins.json"}, "prepared input inventory differs")
    for name, expected in plan["input_hashes"].items():
        require(digest(root / name) == expected, "prepared input differs")
    for arm in ARMS:
        require(seed_matches(read(root / f"train_{arm}.json").get("learner_seed"), plan["learner_seed"]),
                "prepared learner seed differs")
    require(read(root / "source_pins.json") == plan["source_hashes"], "source pins differ")
    probe = load_probe(plan["probe_driver"], plan["probe_sha256"])
    require(probe.disjoint(root, plan["log_dir"]) and Path(plan["log_dir"]).is_dir(), "external logs missing")
    if native:
        require(environment(probe) == plan["environment"] and probe.model_hashes(plan["model"]) == plan["model_files"],
                "native environment/base differs")
    require(public_binding(read(root / "binding_receipt.json"), plan["source"], plan["model"],
            plan["source_hashes"]["organism_v6/birth_skill_corpus.py"], probe) == plan["binding"], "public binding scope drift")
    _, trainer = source_api(plan["source"])
    require(seed_matches(plan["config"].get("seed"), plan["learner_seed"]) and
            plan["config"] == asdict(trainer.TrainConfig(**recipe, model=plan["model"])), "fit recipe differs")
    return plan, probe


def load_native_model(model):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(model, local_files_only=True, trust_remote_code=False)
    base = AutoModelForCausalLM.from_pretrained(model, torch_dtype=torch.bfloat16, device_map="cuda",
                                             local_files_only=True, trust_remote_code=False)
    require(not hasattr(base, "peft_config"), "fit must start from fresh base")
    return tokenizer, base


def check_fit_manifest(manifest, prepared, config):
    require(seed_matches(prepared.get("learner_seed"), config["seed"]), "fit/prepared learner seed differs")
    require(seed_matches(manifest["config"].get("seed"), config["seed"]) and manifest["config"] == config and manifest["empty"] is False and manifest["steps"] == 12 and
            manifest["micro_batches"] == 12 and manifest["epochs_run"] == 4 and manifest["nonfinite_batches"] == 0,
            "fit completion/update mismatch")
    require(manifest["corpus"]["n_items"] == manifest["corpus"]["n_encoded"] == 12 and
            manifest["corpus"]["n_skipped_no_target"] == 0, "fit dropped items")
    require(all(manifest["truncation"][key] == 0 for key in
                ("items_truncated", "context_tokens_dropped", "target_tokens_dropped", "items_split")), "fit truncated/split items")
    require(manifest["packing"]["mode"] == "one_item_per_sequence" and manifest["packing"]["n_sequences"] == 12,
            "fit packing differs")
    require(manifest["tokens"]["target"] == prepared["target_tokens"] and
            manifest["train_tokens_seen"] == 4 * prepared["total_tokens"], "fit exposure mismatch")
    require(manifest["tokens"]["context"] == prepared["total_tokens"] - prepared["target_tokens"] and
            manifest["tokens"]["total"] == prepared["total_tokens"] and
            manifest["tokens"]["target_by_category"] ==
            {"authored_restatement": prepared["authored_target_tokens"], "assistant_end": 12} and
            manifest["tokens"]["target_by_view"] == {"restatement": prepared["target_tokens"]},
            "actual fit token/category exposure differs")
    losses = manifest["mean_loss_per_epoch"]
    require(len(losses) == 4 and all(type(value) in (int, float) and math.isfinite(value)
                                  for value in losses + [manifest["final_loss"]]), "nonfinite fit loss")


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
    _, trainer = source_api(plan["source"])
    arm = stage.removeprefix("fit_")
    prepared = read(Path(plan["root"]) / f"train_{arm}.json")
    require(seed_matches(prepared.get("learner_seed"), plan["learner_seed"]) and
            seed_matches(plan["config"].get("seed"), plan["learner_seed"]), "worker learner seed differs")
    tokenizer, base = load_native_model(plan["model"])
    require(tokenizer.chat_template == plan["chat_template"], "fit chat template changed")
    require(tokenizer.pad_token_id is not None and tokenizer.pad_token_id != tokenizer.eos_token_id, "fit PAD/EOS changed")
    actual_segments = []
    for index, (item, expected) in enumerate(zip(prepared["items"], prepared["encoding"], strict=True)):
        segments = trainer.encode_item_segments(item, tokenizer, 1024, False, False, index, overflow="truncate")
        require(len(segments) == 1 and segments[0].ids == expected["input_ids"] and
                segments[0].labels == expected["labels"] and segments[0].context_dropped == segments[0].target_dropped == 0,
                "actual fit encoding/mask drift")
        actual_segments.append(segments[0])
    packs = trainer.pack_by_group(actual_segments, 1024, False)
    actual_order = [[pack[0].group for pack in trainer.epoch_order(packs, plan["learner_seed"], epoch, True)]
                    for epoch in range(4)]
    require(actual_order == prepared["epoch_order"], "prepared/native epoch-order seed mismatch")
    directory = Path(plan["root"]) / "run" / stage
    adapter = directory / "adapter"
    require(not adapter.exists(), "fresh fit adapter output required")
    trainer.run_training(prepared["items"], tokenizer, base, trainer.TrainConfig(**plan["config"]), str(adapter),
                         corpus_sha=plan["input_hashes"][f"train_{arm}.json"], corpus_name=f"train_{arm}.json")
    trainable = [name for name, parameter in base.named_parameters() if parameter.requires_grad]
    require(trainable and all("lora_A" in name or "lora_B" in name for name in trainable), "non-LoRA trainability")
    manifest = read(adapter / "train_manifest.json")
    check_fit_manifest(manifest, prepared, plan["config"])
    files = check_adapter(adapter, plan["config"])
    write(directory / "fit.json", dict(arm=arm, learner_seed=plan["learner_seed"], adapter=str(adapter), adapter_files=files,
                                       trainable_names_sha256=value_hash(trainable), updates=12, presentations=48))


def adapter_for(plan, cell):
    require(cell in CELLS, "unknown readout cell")
    state = cell.split("__")[0]
    if state == "OFF":
        return None, {}
    arm = "withdrawn" if state == "fitWithdrawn" else "present"
    directory = Path(plan["root"]) / "run" / f"fit_{arm}"
    receipt = read(directory / "fit.json")
    adapter = directory / "adapter"
    require(receipt["updates"] == 12 and receipt["presentations"] == 48 and
            receipt["arm"] == arm and seed_matches(receipt.get("learner_seed"), plan["learner_seed"]) and
            receipt["adapter"] == str(adapter) and
            receipt["adapter_files"] == check_adapter(adapter, plan["config"]), "fitted adapter custody differs")
    check_fit_manifest(read(adapter / "train_manifest.json"), read(Path(plan["root"]) / f"train_{arm}.json"), plan["config"])
    return str(adapter), receipt["adapter_files"]


class Native:
    def __init__(self, plan, probe, adapter):
        from vllm import LLM
        from vllm.lora.request import LoRARequest
        self.probe = probe
        self.llm = LLM(model=plan["model"], tokenizer=plan["model"], **ENGINE)
        self.tokenizer = self.llm.get_tokenizer()
        require(self.tokenizer.chat_template == plan["chat_template"], "readout template drift")
        self.route = None if adapter is None else dict(name="reflection", id=1, path=adapter)
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
    route = None if adapter is None else dict(name="reflection", id=1, path=adapter)
    identity = dict(cell=cell, learner_seed=plan["learner_seed"], model=plan["model"], revision=plan["binding"]["revision"], model_files=plan["model_files"],
                    adapter=adapter, adapter_files=files, lora_request=route, engine=ENGINE, params=PARAMS)
    write(directory / "identity.json", identity)
    calls = read(Path(plan["root"]) / "calls.json")[cell.split("__")[1]]
    require(len(calls) == 24 and [call["call_id"] for call in calls] == [f"{index:02d}" for index in range(24)],
            "exact ordered DEV24 capture inventory required")
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
    write(directory / "closed.json", dict(learner_seed=plan["learner_seed"], calls=24, files={name: digest(directory / name) for name in names}))


def worker(root, plan_sha256, stage, allow_gpu=False):
    require(allow_gpu, "Main-only worker requires --allow-gpu")
    require(stage in STAGES and os.getpid() == os.getpgrp(), "worker must own a fresh process group")
    offline()
    plan, probe = verify(root, plan_sha256, native=True)
    require(os.environ.get("CUDA_VISIBLE_DEVICES") == plan["gpu_uuid"] and time.time() < plan["lease_end"] - COLLECTION_SECONDS,
            "worker device/lease differs")
    directory = Path(root) / "run" / stage
    write(directory / "started.json", dict(pid=os.getpid(), pgid=os.getpgrp(), stage=stage, learner_seed=plan["learner_seed"], plan_sha256=plan_sha256, time=time.time()))
    try:
        if stage.startswith("fit_"):
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
        raise TimeoutError("reflection bounded deadline exceeded")
    previous = signal.signal(signal.SIGALRM, expired)
    previous_timer = signal.getitimer(signal.ITIMER_REAL)
    started = time.monotonic()
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
        if previous_timer[0] > 0:
            signal.setitimer(signal.ITIMER_REAL, max(.001, previous_timer[0] - (time.monotonic() - started)), previous_timer[1])


@contextlib.contextmanager
def controller_budget():
    def terminated(signum, frame):
        raise InterruptedError("controller terminated; release owned worker only")
    previous = signal.signal(signal.SIGTERM, terminated)
    try:
        with budget(OUTER_SECONDS - CLEANUP_SECONDS):
            yield
    finally:
        signal.signal(signal.SIGTERM, previous)


@contextlib.contextmanager
def release_budget(deadline):
    previous = {kind: signal.signal(kind, signal.SIG_IGN) for kind in (signal.SIGINT, signal.SIGTERM)}
    try:
        with budget(min(CLEANUP_SECONDS, max(.001, deadline - time.monotonic()))):
            yield
    finally:
        for kind, handler in previous.items():
            signal.signal(kind, handler)


def run_stage(plan, pin, stage, deadline, probe):
    require(deadline - time.monotonic() > GPU_QUERY_SECONDS + CLEANUP_SECONDS, "insufficient budget for vacancy and release checks")
    require(probe.gpu_state(plan), "assigned GPU not vacant; no foreign process will be stopped")
    seconds = min(FIT_SECONDS if stage.startswith("fit_") else READOUT_SECONDS, deadline - time.monotonic() - CLEANUP_SECONDS)
    require(seconds > 0, "insufficient outer budget for next stage")
    directory = Path(plan["root"]) / "run" / stage
    directory.mkdir()
    command = [plan["python"], "-B", str(SELF), "worker", "--root", plan["root"], "--plan-sha256", pin,
               "--stage", stage, "--allow-gpu"]
    env = dict(os.environ, CUDA_VISIBLE_DEVICES=plan["gpu_uuid"])
    process = None
    try:
        logs = Path(plan["log_dir"]) / stage
        logs.mkdir()
        with (logs / "stdout.log").open("xb") as output, (logs / "stderr.log").open("xb") as errors:
            process = subprocess.Popen(command, env=env, stdout=output, stderr=errors, start_new_session=True)
            write(directory / "launch.json", dict(pid=process.pid, pgid=process.pid, stage=stage, learner_seed=plan["learner_seed"], plan_sha256=pin))
            require(process.wait(timeout=seconds) == 0, "native worker failed: " + stage)
    finally:
        if process is not None:
            try:
                with release_budget(deadline):
                    probe.cleanup(process)
                    require(not probe.group_alive(process.pid), "owned process group survived cleanup")
                    require(probe.gpu_state(plan), "GPU release not confirmed")
                    write(directory / "released.json", dict(pid=process.pid, pgid=process.pid, learner_seed=plan["learner_seed"], time=time.time()))
            except BaseException as error:
                failure(directory / "cleanup_failure.json", error)
                raise


def validate_completed(plan, pin, probe):
    root = Path(plan["root"])
    require({path.name for path in (root / "run").iterdir()} == set(STAGES), "worker stage inventory differs")
    require({path.name for path in Path(plan["log_dir"]).iterdir()} == set(STAGES), "worker log inventory differs")
    processes, inventory = [], {}
    for stage in STAGES:
        directory = root / "run" / stage
        require(not (directory / "failure.json").exists() and not (directory / "cleanup_failure.json").exists(), "failed stage cannot complete")
        started, launched, released = (read(directory / name) for name in ("started.json", "launch.json", "released.json"))
        require(type(started["pid"]) is int and started["pid"] > 1 and started["pid"] == started["pgid"] ==
                launched["pid"] == launched["pgid"] == released["pid"] == released["pgid"] and
                started["stage"] == launched["stage"] == stage and started["plan_sha256"] == launched["plan_sha256"] == pin,
                "fresh process receipt mismatch")
        require(all(seed_matches(receipt.get("learner_seed"), plan["learner_seed"])
                    for receipt in (started, launched, released)), "worker receipt learner seed differs")
        processes.append(started["pid"])
        if stage.startswith("fit_"):
            adapter_for(plan, "fitWithdrawn__withdrawn" if stage == "fit_withdrawn" else "fitPresent__withdrawn")
        else:
            adapter, files = adapter_for(plan, stage)
            identity, closed = read(directory / "identity.json"), read(directory / "closed.json")
            route = None if adapter is None else dict(name="reflection", id=1, path=adapter)
            require(seed_matches(identity.get("learner_seed"), plan["learner_seed"]) and
                    identity == dict(cell=stage, learner_seed=plan["learner_seed"], model=plan["model"], revision=plan["binding"]["revision"], model_files=plan["model_files"],
                                     adapter=adapter, adapter_files=files, lora_request=route, engine=ENGINE, params=PARAMS), "readout identity mismatch")
            calls = read(root / "calls.json")[stage.split("__")[1]]
            require(len(calls) == 24 and [call["call_id"] for call in calls] == [f"{index:02d}" for index in range(24)],
                    "exact ordered DEV24 capture inventory required")
            expected_names = {"identity.json"} | {call["call_id"] + suffix for call in calls for suffix in (".request.json", ".response.json")}
            require(seed_matches(closed.get("learner_seed"), plan["learner_seed"]) and
                    closed["calls"] == 24 and set(closed["files"]) == expected_names, "incomplete raw capture inventory")
            require({path.name for path in directory.glob("*.response.json")} == {call["call_id"] + ".response.json" for call in calls},
                    "raw response count mismatch")
            for name, expected in closed["files"].items():
                require(digest(directory / name) == expected, "raw capture changed")
            for call in calls:
                require(read(directory / (call["call_id"] + ".request.json")) == call, "captured request differs")
                response = read(directory / (call["call_id"] + ".response.json"))
                require(response["lora_request"] == route, "captured adapter route differs")
                probe.validate_response(call, response)
        logs = Path(plan["log_dir"]) / stage
        require(set(tree(logs)) == {"stdout.log", "stderr.log"}, "fresh worker logs missing")
        inventory[stage] = dict(artifacts=tree(directory), logs=tree(logs))
    require(len(set(processes)) == 8, "fits/readouts must use eight distinct fresh processes")
    return inventory


def controller(root, plan_sha256, allow_gpu=False):
    require(allow_gpu, "Main-only controller requires --allow-gpu")
    offline()
    root = Path(root).resolve()
    write(root / "controller_started.json", dict(time=time.time(), plan_sha256=plan_sha256,
          learner_seed=bound_learner_seed(root, plan_sha256)))
    deadline = time.monotonic() + OUTER_SECONDS
    try:
        with controller_budget():
            plan, probe = verify(root, plan_sha256, native=True)
            require(plan["lease_end"] > time.time() + OUTER_SECONDS + COLLECTION_SECONDS + CLEANUP_SECONDS,
                    "launch no longer fits lease")
            (root / "run").mkdir()
            for stage in STAGES:
                run_stage(plan, plan_sha256, stage, deadline, probe)
            inventory = validate_completed(plan, plan_sha256, probe)
            require(time.monotonic() < deadline, "outer deadline exceeded")
            write(root / "capture_complete.json", dict(plan_sha256=plan_sha256, learner_seed=plan["learner_seed"], stages=inventory, calls=144,
                                                       scored=False, time=time.time()))
        return dict(status="ALL_CAPTURES_CLOSED_UNSCORED", learner_seed=plan["learner_seed"], completion_sha256=digest(root / "capture_complete.json"))
    except BaseException as error:
        failure(root / "controller_failure.json", error)
        raise


def collect(root, plan_sha256, completion_sha256, out):
    offline()
    out = Path(out).resolve()
    started = False
    try:
        with budget(COLLECTION_SECONDS):
            plan, probe = verify(root, plan_sha256)
            require(not out.exists() and all(probe.disjoint(out, path) for path in
                    (root, plan["source"], plan["model"], plan["log_dir"], plan["probe_driver"], SELF)),
                    "fresh external collection directory required")
            out.mkdir()
            started = True
            root = Path(root)
            require(not (root / "controller_failure.json").exists(), "failed controller cannot score")
            require(digest(root / "capture_complete.json") == completion_sha256, "completion pin differs")
            complete = read(root / "capture_complete.json")
            require(complete["plan_sha256"] == plan_sha256 and seed_matches(complete.get("learner_seed"), plan["learner_seed"]) and
                    complete["calls"] == 144 and complete["scored"] is False,
                    "all captures must precede scores")
            require(validate_completed(plan, plan_sha256, probe) == complete["stages"], "completion inventory changed")
            corpus, _ = source_api(plan["source"])
            dev = read(root / "dev.json")
            results = {}
            for cell in CELLS:
                panels = {}
                for panel in PANELS:
                    rows = []
                    for index, row in enumerate(dev[cell.split("__")[1]]):
                        if row["panel"] != panel:
                            continue
                        response_path = root / "run" / cell / f"{index:02d}.response.json"
                        response = read(response_path)
                        score = corpus.score_response(row, response["text"])
                        if panel == "restatement":
                            require(score["semantic_prose_score"] is None, "exact fixture is not semantic prose scoring")
                        else:
                            require(score["score_kind"] == "strict_application_choice" and
                                    score["syntax_valid"] == (response["text"] in ("A", "B")) and
                                    score["passed"] == (response["text"] == row["response_target"]), "strict A/B scoring drift")
                        rows.append(dict(row_id=row["row_id"], source_id=row["source"]["source_id"], score=score,
                                         finish_reason=response["finish_reason"], response_sha256=digest(response_path)))
                    require(len(rows) == 12, "both separate DEV12 metrics required")
                    count = sum(row["score"]["passed"] is True for row in rows)
                    metric = "exact_authored_fixture_matches" if panel == "restatement" else "strict_application_correct"
                    panels[panel] = dict(rows=rows, metric=metric, count=count, total=12, semantic_prose_score=None,
                                         length_finishes=sum(row["finish_reason"] == "length" for row in rows))
                results[cell] = panels
            report = dict(scope=SCOPE, claim=CLAIM, learner_seed=plan["learner_seed"], parent_driver_sha256=PARENT_DRIVER_SHA256, plan_sha256=plan_sha256, completion_sha256=completion_sha256,
                          cells=results, calls=144, fresh_workers=8, automatic_pass=False,
                          composite_metric=None, clean_ancestry_certified=False,
                          restatement_limitation="An exact authored fixture mismatch is NOT semantic prose failure.")
            write(out / "scores.json", report)
            write(out / "collection.json", dict(learner_seed=plan["learner_seed"], scores_sha256=digest(out / "scores.json"), completion_sha256=completion_sha256))
        return dict(status="COLLECTED_EXPLORATORY_ONLY", learner_seed=plan["learner_seed"], out=str(out), scores_sha256=digest(out / "scores.json"))
    except BaseException as error:
        if started:
            failure(out / "collection_failure.json", error)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prep = commands.add_parser("prepare")
    for name in ("root", "source", "model", "probe-driver", "probe-sha256", "binding-path", "binding-sha256",
                 "corpus-sha256", "reflection-sha256", "source-pins-path", "source-pins-sha256", "log-dir", "gpu-uuid"):
        prep.add_argument("--" + name, required=True)
    prep.add_argument("--learner-seed", type=int, choices=LEARNER_SEEDS, required=True)
    prep.add_argument("--gpu-index", type=int, required=True)
    prep.add_argument("--lease-end", type=float, required=True)
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
