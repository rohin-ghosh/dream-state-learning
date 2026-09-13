"""Finite, source-withdrawn real-record memory write; Main owns native launch."""
from __future__ import annotations

import argparse
from collections import Counter
import contextlib
from dataclasses import asdict
import hashlib
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
SCOPE = "astra_real_record_memory_paired_write_lr0_20260913_v1"
MEMORY_PIN = "2c5538f5b63cbb4e592f40822561b4d62595ab3c9d7d193f084b91f9a064e8ef"
FORMATION_PIN = "3c03304ee5309517ce34f91b121594f0070b37bfb14f31f429f915d8310cc20e"
CORE_PIN = "b023a4321d0a20e465c96914316a730fbb2dd897c11369a9eb62d2d8f1248ef5"
TRAINER_PIN = "7bbf165fcb4b8ae3a1180328bcd19f57382c30516daddc95fd61e8a2c749fad7"
REFLECTION_PIN = "0f79efa1f4e4da6a9d1ec245c09e665f7c2b7d8bce31f7e01fe01b00f95a72fc"
FORMATION_PLAN = "039f8cc66ecae40ed9cbee649011b34e4e4654fec68f5e7d51a37f5a5a5374bd"
FORMATION_COMPLETE = "51b09f9a553cfe561ae8613e299a6d4926d8df3286265498927573b41dae1274"
FORMATION_COLLECTION = "77260fe6d540beb65cd4f9717a76fc827cb3e441a23663077f72dbdbd7a70a4c"
FORMATION_REPORT = "9d04155a0103377e41f80ad25b7b1b4ed9cd2ffd014503e74b27a0992b4c81f1"
PROTOCOL_PIN = "c056a0fb6c97d1ba93b4d2a0fa07cb70f806cfa64fef2df1769d78e80334a716"
ARMS = ("WRITE", "LR0")
STAGES = ("WRITE_fit", "WRITE_readout", "LR0_fit", "LR0_readout")
PASSES, BATCH_SIZE, MAX_LEN, OUTPUT_TOKENS = 8, 1, 1024, 192
MAX_UPDATES, MAX_CALLS = 256, 184
OUTER_SECONDS, COLLECTION_SECONDS, PREPARE_SECONDS = 3600, 180, 180
CLEANUP_SECONDS, GPU_QUERY_SECONDS, LEASE_MARGIN = 40, 30, 21600
CLAIM = ("Exploratory source-withdrawn real-record memory acquisition/persistence and separate paraphrase transfer. "
         "Same original perception adapter and admitted records in WRITE/LR0; fresh optimizer per arm. "
         "Retention is the original authored Level1 screen, not real-experience learning qualification. "
         "No teacher rewriting, new formation, closed-loop, H1/H2 or automatic promotion.")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def digest(path):
    checksum = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            checksum.update(block)
    return checksum.hexdigest()


def value_hash(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def read(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "duplicate JSON key")
            result[key] = value
        return result
    return json.loads(Path(path).read_bytes(), object_pairs_hook=unique,
                      parse_constant=lambda value: require(False, "nonfinite JSON"))


def write(path, value):
    path = Path(path)
    require(not path.is_symlink(), "output symlink")
    with path.open("xb") as stream:
        stream.write(encoded(value))


def failure(path, error):
    if not Path(path).exists():
        write(path, dict(error_type=type(error).__name__, error=str(error), retry=False, time=time.time()))


def load(record, name, expected=None):
    require(set(record) == {"path", "sha256"} and Path(record["path"]).is_absolute(), "explicit file binding required")
    require((expected is None or record["sha256"] == expected) and digest(record["path"]) == record["sha256"], "source pin differs: " + name)
    specification = importlib.util.spec_from_file_location("memory_run_" + name, record["path"])
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


def offline():
    sys.dont_write_bytecode = True
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_DATASETS_OFFLINE="1",
                      HF_HUB_DISABLE_TELEMETRY="1", VLLM_NO_USAGE_STATS="1", DO_NOT_TRACK="1",
                      VLLM_WORKER_MULTIPROC_METHOD="spawn", PYTHONDONTWRITEBYTECODE="1")


@contextlib.contextmanager
def budget(seconds):
    require(seconds > 0, "runtime budget exhausted")
    def expired(signum, frame):
        raise TimeoutError("memory runner deadline exceeded")
    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def new_external(path, protected):
    path = Path(path).absolute()
    require(".." not in path.parts and not any(item.is_symlink() for item in (path, *path.parents)) and not path.exists(), "fresh nonsymlink output required")
    for other in protected:
        other = Path(other).resolve()
        require(path != other and path not in other.parents and other not in path.parents, "output overlaps protected input")
    require(path.parent.is_dir(), "output parent must already exist")
    return path


def validate_spec(spec):
    require(set(spec) == {"runner_sha256", "memory", "formation_runtime", "formation", "protocol", "seed", "fit_seed",
                          "gpu_index", "gpu_uuid", "expected_boot_id", "lease_end"}, "closed specification fields differ")
    require(spec["runner_sha256"] == digest(SELF), "runner pin differs")
    require(type(spec["seed"]) is int and spec["seed"] in (0, 1, 2) and
            type(spec["fit_seed"]) is int and spec["fit_seed"] == spec["seed"], "same original learner fit seed0/1/2 required")
    require(type(spec["gpu_index"]) is int and spec["gpu_index"] >= 0 and
            type(spec["gpu_uuid"]) is str and spec["gpu_uuid"].startswith("GPU-"), "GPU identity binding required")
    require(type(spec["expected_boot_id"]) is str and len(spec["expected_boot_id"]) == 36 and
            type(spec["lease_end"]) in (int, float) and math.isfinite(spec["lease_end"]), "boot/lease binding required")
    protocol = spec["protocol"]
    require(set(protocol) == {"path", "sha256"} and Path(protocol["path"]).is_absolute() and
            protocol["sha256"] == PROTOCOL_PIN and digest(protocol["path"]) == protocol["sha256"], "protocol pin differs")
    upstream = spec["formation"]
    require(set(upstream) == {"root", "plan_sha256", "completion_sha256", "collection"} and
            upstream["plan_sha256"] == FORMATION_PLAN and upstream["completion_sha256"] == FORMATION_COMPLETE and
            upstream["collection"]["sha256"] == FORMATION_COLLECTION, "completed formation v2 binding differs")


def check_allocation(plan):
    spec = plan["specification"]
    require(Path("/proc/sys/kernel/random/boot_id").read_text().strip() == spec["expected_boot_id"], "current node boot mismatch")
    require(spec["lease_end"] > time.time() + OUTER_SECONDS + COLLECTION_SECONDS + LEASE_MARGIN, "six-hour lease finish margin required")


def bind_inputs(spec, native=False):
    validate_spec(spec)
    formation = load(spec["formation_runtime"], "formation", FORMATION_PIN)
    memory = load(spec["memory"], "projector", MEMORY_PIN)
    binding = spec["formation"]
    root = Path(binding["root"])
    require(root.is_absolute() and not (root / "controller_failure.json").exists(), "failed formation cannot write")
    plan, core, dependencies, probe = formation.verify(root, binding["plan_sha256"], native=native)
    require(plan["specification"]["core"]["sha256"] == CORE_PIN, "formation must use frozen v2 core")
    require(digest(root / "capture_complete.json") == binding["completion_sha256"], "formation completion differs")
    complete = read(root / "capture_complete.json")
    inventory, captures, costs = formation.validate_completed(plan, binding["plan_sha256"], core, dependencies)
    require(complete["plan_sha256"] == binding["plan_sha256"] and complete["formation_only"] is True and
            complete["stages"] == inventory and complete["calls"] == sum(cost["calls"] for cost in costs.values()), "formation completed custody differs")
    collection = binding["collection"]
    formation.pinned(collection)
    collection_path = Path(collection["path"])
    require(collection_path.name == "collection.json" and not (collection_path.parent / "collection_failure.json").exists(), "successful once-collected formation required")
    collected = read(collection_path)
    require(collected["completion_sha256"] == binding["completion_sha256"] and
            collected["formation_report_sha256"] == FORMATION_REPORT and
            digest(collection_path.parent / "formation_report.json") == FORMATION_REPORT, "formation collection/report differs")
    claim = read(root.with_name(root.name + ".collection_claim.json"))
    require(claim == dict(plan_sha256=binding["plan_sha256"], out=str(collection_path.parent), retry=False), "original once-only collection claim differs")
    state = "perception_seed" + str(spec["seed"])
    capture = next(capture for capture in captures if capture["state"] == state)
    kwargs = dict(core_path=plan["specification"]["core"]["path"], source_root=plan["source"])
    dataset = memory.project_capture(capture, **kwargs)
    parent = plan["upstream"][state]
    helper = formation.load_module(plan["specification"]["level1_runtime"], "level1")
    original = read(Path(parent["root"]) / "plan.json")
    require(original["skill"] == "perception" and original["learner_seed"] == spec["seed"], "original retention learner differs")
    require(digest(Path(parent["root"]) / "material.json") == original["input_hashes"]["material.json"] and
            digest(Path(parent["root"]) / "calls.json") == original["input_hashes"]["calls.json"], "original retention input pins differ")
    material_spec = dict(original["specification"], source=plan["source"])
    material = helper.load_material(material_spec)
    retention = read(Path(parent["root"]) / "material.json")
    require(encoded(retention) == encoded(material.build_dataset("perception", seed=original["material_seed"])), "retention material replay differs")
    helper.validate_dataset(retention)
    trainer_path = Path(plan["source"]) / "organism_v6/train_adapter_v3.py"
    trainer = load(dict(path=str(trainer_path), sha256=TRAINER_PIN), "trainer", TRAINER_PIN)
    reflection_record = original["specification"]["reflection"]
    reflection = load(reflection_record, "reflection", REFLECTION_PIN)
    return dict(formation=formation, memory=memory, helper=helper, trainer=trainer, probe=probe,
                reflection=reflection, material=material, plan=plan, parent=parent, capture=capture,
                dataset=dataset, retention=retention, original_calls=read(Path(parent["root"]) / "calls.json"), kwargs=kwargs)


def config_for(helper, trainer, model, seed, arm):
    require(arm in ARMS and type(seed) is int and seed in (0, 1, 2), "fit arm/seed differs")
    config = dict(helper.RECIPE, model=model, seed=seed, epochs=PASSES, batch_size=BATCH_SIZE,
                  lr=1e-4 if arm == "WRITE" else 0.0, max_steps=0,
                  note=SCOPE + "; exact raw child record plus EOS; original parent; fresh optimizer")
    require(config["rank"] == 8 and config["alpha"] == 16 and config["dropout"] == .05, "parent LoRA structure differs")
    return asdict(trainer.TrainConfig(**config))


def encode_training(rows, tokenizer, trainer, helper, probe, fit_seed):
    require(len(rows) <= 16 and len({row["row_id"] for row in rows}) == len(rows), "memory row limit/identity differs")
    require(tokenizer.pad_token_id is not None and tokenizer.pad_token_id != tokenizer.eos_token_id, "distinct PAD/EOS required")
    items, audits, segments = [], [], []
    for index, row in enumerate(rows):
        item, audit = helper.training_item(row, tokenizer, trainer, probe, index)
        item["view"] = "source_withdrawn_real_record"
        items.append(item)
        audits.append(audit)
        encoded_rows = trainer.encode_item_segments(item, tokenizer, MAX_LEN, False, False, index, overflow="truncate")
        require(len(encoded_rows) == 1, "one unsplit record required")
        segments.extend(encoded_rows)
    packs = trainer.pack_by_group(segments, MAX_LEN, False)
    require(len(packs) == len(rows) and all(len(pack) == 1 for pack in packs), "memory packing differs")
    orders = []
    for epoch in range(PASSES):
        ordered = trainer.epoch_order(packs, fit_seed, epoch, True)
        orders.append([pack[0].group for pack in ordered])
        for pack in ordered:
            batch = trainer.collate([pack], tokenizer.pad_token_id)
            require(batch["input_ids"] == [pack[0].ids] and batch["labels"] == [pack[0].labels], "single-row padding/mask drift")
    total = sum(len(audit["input_ids"]) for audit in audits)
    targets = sum(len(audit["supervised_ids"]) for audit in audits)
    return dict(items=items, encoding=audits, epoch_order=orders, fit_seed=fit_seed, rows=len(rows),
                updates=PASSES * len(rows), presentations=PASSES * len(rows), total_tokens=total,
                target_tokens=targets, context_tokens=total - targets, train_tokens_seen=PASSES * total,
                actual_supervised_tokens=PASSES * targets, actual_context_tokens=PASSES * (total - targets),
                actual_padded_tokens=PASSES * total, padding_tokens=0)


def build_calls(dataset, retention, original_calls, tokenizer, probe):
    calls = []
    for variant, key in (("exact", "input_messages"), ("paraphrase", "paraphrase_input_messages")):
        for row in dataset["rows"]:
            calls.append(dict(call_id=f"{variant}_{len(calls):02d}", panel=variant, row_id=row["row_id"], messages=row[key]))
    for panel, count in (("held", 48), ("canary", 12)):
        require(len(retention["evaluation"][panel]) == count, "original retention count differs")
        for index, row in enumerate(retention["evaluation"][panel]):
            old = next(call for call in original_calls if call["call_id"] == f"{panel}_{index:02d}")
            require(old["row_id"] == row["row_id"] and old["messages"] == row["input_messages"], "original retention cue differs")
            native = probe.render(tokenizer, old["messages"])
            require(native == old["native"], "original retention native prefix differs")
            calls.append(dict(call_id=old["call_id"], panel=panel, row_id=row["row_id"], messages=old["messages"]))
    for call in calls:
        call["native"] = probe.render(tokenizer, call["messages"])
        require(len(call["native"]["prompt_token_ids"]) + OUTPUT_TOKENS <= 16384, "readout context overflow")
    require(len(calls) == 2 * len(dataset["rows"]) + 60 and len(calls) <= 92, "readout ceiling differs")
    return calls


def protected_inputs(spec, bound):
    plan = bound["plan"]
    paths = [SELF, spec["protocol"]["path"], spec["memory"]["path"], spec["formation_runtime"]["path"],
             spec["formation"]["root"], Path(spec["formation"]["collection"]["path"]).parent,
             plan["source"], plan["model"]]
    paths.extend(plan["specification"][key]["path"] for key in ("core", "level1_runtime", "public", "protocol", "binding"))
    paths.extend(entry["root"] for entry in plan["upstream"].values())
    paths.extend(Path(entry["collection"]["path"]).parent for entry in plan["upstream"].values())
    return paths


def prepare(root, spec_path, spec_sha256, allow_native=False):
    require(allow_native is True, "Main-only native CPU prepare requires --allow-native")
    offline()
    require(not os.environ.get("CUDA_VISIBLE_DEVICES"), "native CPU prepare must not reserve CUDA")
    with budget(PREPARE_SECONDS):
        require(digest(spec_path) == spec_sha256, "spec hash differs")
        spec = read(spec_path)
        bound = bind_inputs(spec, native=True)
        root = new_external(root, [spec_path, *protected_inputs(spec, bound)])
        check_allocation(dict(specification=spec))
        root.mkdir()
        write(root / "prepare_started.json", dict(spec_sha256=spec_sha256, time=time.time()))
        try:
            plan = bound["plan"]
            tokenizer = bound["probe"].native_tokenizer(plan["model"])
            require(tokenizer.chat_template == plan["chat_template"], "formation tokenizer template differs")
            dataset = bound["dataset"]
            training = encode_training(dataset["rows"], tokenizer, bound["trainer"], bound["helper"], bound["probe"], spec["fit_seed"])
            calls = build_calls(dataset, bound["retention"], bound["original_calls"], tokenizer, bound["probe"]) if dataset["rows"] else []
            configs = {arm: config_for(bound["helper"], bound["trainer"], plan["model"], spec["fit_seed"], arm) for arm in ARMS}
            for arm in ARMS:
                bound["trainer"]._warm_parent(bound["parent"]["adapter"], root / "run" / (arm + "_fit") / "adapter", bound["trainer"].TrainConfig(**configs[arm]))
            files = {"dataset.json": dataset, "capture.json": bound["capture"], "retention.json": bound["retention"],
                     "training.json": training, "calls.json": calls}
            for name, value in files.items():
                write(root / name, value)
            result = dict(scope=SCOPE, claim=CLAIM, root=str(root), specification=spec, spec_sha256=spec_sha256,
                          self_sha256=digest(SELF), python=os.path.abspath(sys.executable), python_sha256=digest(sys.executable),
                          model=plan["model"], model_files=plan["model_files"], chat_template=plan["chat_template"],
                          environment=plan["environment"], source=plan["source"], parent=bound["parent"], configs=configs,
                          engine=bound["formation"].ENGINE, params=dict(bound["formation"].PARAMS, max_tokens=OUTPUT_TOKENS),
                          gpu_index=spec["gpu_index"], gpu_uuid=spec["gpu_uuid"], status=dataset["status"],
                          stages=list(STAGES) if dataset["rows"] else [], calls_per_arm=len(calls), updates_per_arm=training["updates"],
                          input_hashes={name: digest(root / name) for name in files},
                          limits=dict(controller=OUTER_SECONDS, collection=COLLECTION_SECONDS, updates=MAX_UPDATES, calls=MAX_CALLS))
            write(root / "plan.json", result)
            return dict(status="NATIVE_CPU_PREPARED_NOT_LAUNCHED", availability=dataset["status"], plan_sha256=digest(root / "plan.json"),
                        admitted=len(dataset["rows"]), calls=2 * len(calls), updates=2 * training["updates"])
        except BaseException as error:
            failure(root / "prepare_failure.json", error)
            raise


def verify(root, plan_sha256, native=False):
    root = Path(root).absolute()
    require(digest(root / "plan.json") == plan_sha256, "memory plan pin differs")
    plan = read(root / "plan.json")
    require(plan["root"] == str(root) and plan["scope"] == SCOPE and plan["claim"] == CLAIM and
            plan["self_sha256"] == digest(SELF) and plan["python"] == os.path.abspath(sys.executable) and
            plan["python_sha256"] == digest(sys.executable), "memory runtime identity differs")
    require(not (root / "prepare_failure.json").exists() and read(root / "prepare_started.json")["spec_sha256"] == plan["spec_sha256"], "preparation identity/failure")
    require(set(plan["input_hashes"]) == {"dataset.json", "capture.json", "retention.json", "training.json", "calls.json"}, "prepared input inventory differs")
    for name, checksum in plan["input_hashes"].items():
        require(digest(root / name) == checksum, "prepared input changed: " + name)
    bound = bind_inputs(plan["specification"], native=native)
    require(plan["parent"] == bound["parent"] and plan["model"] == bound["plan"]["model"] and
            plan["model_files"] == bound["plan"]["model_files"] and plan["source"] == bound["plan"]["source"] and
            plan["chat_template"] == bound["plan"]["chat_template"] and plan["environment"] == bound["plan"]["environment"], "upstream identity drift")
    require(encoded(read(root / "dataset.json")) == encoded(bound["dataset"]) and
            encoded(read(root / "capture.json")) == encoded(bound["capture"]) and
            encoded(read(root / "retention.json")) == encoded(bound["retention"]), "immutable projection/retention differs")
    for arm in ARMS:
        require(plan["configs"][arm] == config_for(bound["helper"], bound["trainer"], plan["model"], plan["specification"]["fit_seed"], arm), "fixed recipe drift")
    count = len(bound["dataset"]["rows"])
    require(plan["status"] == bound["dataset"]["status"] and plan["stages"] == (list(STAGES) if count else []) and
            plan["calls_per_arm"] == (2 * count + 60 if count else 0) and plan["updates_per_arm"] == PASSES * count and
            plan["engine"] == bound["formation"].ENGINE and plan["params"] == dict(bound["formation"].PARAMS, max_tokens=OUTPUT_TOKENS), "fixed workload/configuration drift")
    require(all(plan[key] == plan["specification"][key] for key in ("gpu_index", "gpu_uuid")), "new GPU binding differs")
    return plan, bound


def check_fit(manifest, prepared, config, parent, arm):
    count, updates = prepared["rows"], prepared["updates"]
    require(count > 0 and updates == PASSES * count <= 128 and manifest["config"] == config and manifest["empty"] is False,
            "fit config/count differs")
    require(all(type(manifest[key]) is int for key in ("steps", "micro_batches", "epochs_run", "nonfinite_batches")) and
            manifest["steps"] == manifest["micro_batches"] == updates and manifest["epochs_run"] == PASSES and
            manifest["nonfinite_batches"] == 0, "fit steps/nonfinite accounting differs")
    require(manifest["corpus"]["n_items"] == manifest["corpus"]["n_encoded"] == count and manifest["corpus"]["n_skipped_no_target"] == 0,
            "fit skipped records")
    require(all(manifest["truncation"][key] == 0 for key in ("items_truncated", "context_tokens_dropped", "target_tokens_dropped", "items_split")), "fit truncated/split records")
    require(manifest["packing"]["mode"] == "one_item_per_sequence" and manifest["packing"]["n_sequences"] == count and
            manifest["tokens"]["target"] == prepared["target_tokens"] and manifest["tokens"]["total"] == prepared["total_tokens"] and
            manifest["train_tokens_seen"] == prepared["train_tokens_seen"], "fit token exposure differs")
    losses = manifest["mean_loss_per_epoch"]
    require(len(losses) == PASSES and all(type(loss) in (int, float) and math.isfinite(loss) for loss in losses + [manifest["final_loss"]]), "nonfinite fit loss")
    warm = manifest["warm_start"]
    require(warm["mode"] == "WEIGHT_WARM_START_FRESH_OPTIMIZER" and warm["optimizer_initialization"] == "fresh_per_write" and
            warm["optimizer_state_restored"] is False and warm["optimizer_state_saved"] is False and
            warm["parent_path"] == parent["adapter"] and warm["parent_files"] == warm["parent_files_after"] == parent["adapter_files"] and
            warm["parent_unchanged"] is True and warm["initialized_loaded_state_check"] is True and
            warm["base_frozen"] is True and warm["adapter_count"] == 1 and warm["trainer_sha256"] == TRAINER_PIN and
            warm["phase_seed"] == config["seed"] and warm["phase_steps"] == updates and
            warm["cumulative_steps"] == warm["parent_cumulative_steps"] + updates, "warm-start custody differs")
    require(warm["initialized_state"] and set(warm["initialized_state"]) == set(warm["final_state"]) and
            warm["trainable_names"] and all("lora_A" in name or "lora_B" in name for name in warm["trainable_names"]), "LoRA tensor coverage differs")
    if arm == "LR0":
        require(warm["initialized_state"] == warm["final_state"], "LR0 changed initialized adapter tensors")
    else:
        require(warm["initialized_state"] != warm["final_state"], "WRITE made no actual parameter change")


def tensor_diagnostics(trainer, parent, adapter, manifest):
    import torch
    def tensors(path):
        path = Path(path)
        if (path / "adapter_model.safetensors").is_file():
            from safetensors.torch import load_file
            return load_file(str(path / "adapter_model.safetensors"), device="cpu")
        return torch.load(path / "adapter_model.bin", map_location="cpu", weights_only=True)
    source, final = tensors(parent["adapter"]), tensors(adapter)
    require(set(source) == set(final), "saved tensor keys differ")
    initial = {name: tensor.to(dtype=final[name].dtype, device="cpu") for name, tensor in source.items()}
    warm = manifest["warm_start"]
    require(trainer._warm_state_inventory(source) == warm["source_state"] and
            trainer._warm_state_inventory(initial) == warm["initialized_state"] and
            trainer._warm_state_inventory(final) == warm["final_state"], "serialized versus initialized/final tensor custody differs")
    sums = dict(initial=0.0, final=0.0, delta=0.0)
    changed = 0
    for name in source:
        before, after = initial[name].double(), final[name].double()
        sums["initial"] += before.square().sum().item()
        sums["final"] += after.square().sum().item()
        sums["delta"] += (after - before).square().sum().item()
        changed += int(torch.count_nonzero(after - before).item())
    require(all(math.isfinite(value) and value >= 0 for value in sums.values()), "nonfinite adapter norm")
    return dict(l2={name: math.sqrt(value) for name, value in sums.items()}, changed_elements=changed,
                comparison="source converted to actual saved/initialized dtype; not serialized file equality")


def fit_arm(plan, bound, arm):
    started = time.monotonic()
    directory = Path(plan["root"]) / "run" / (arm + "_fit")
    trainer, helper = bound["trainer"], bound["helper"]
    tokenizer, base = bound["reflection"].load_native_model(plan["model"])
    require(not hasattr(base, "peft_config") and tokenizer.chat_template == plan["chat_template"], "fresh base/tokenizer required")
    prepared = read(Path(plan["root"]) / "training.json")
    require(encoded(prepared) == encoded(encode_training(bound["dataset"]["rows"], tokenizer, trainer, helper, bound["probe"],
                                                       plan["specification"]["fit_seed"])), "actual training encoder differs")
    adapter = directory / "adapter"
    require(not adapter.exists(), "fresh writer output required")
    trainer.run_training(prepared["items"], tokenizer, base, trainer.TrainConfig(**plan["configs"][arm]), str(adapter),
                         corpus_sha=plan["input_hashes"]["training.json"], corpus_name="source_withdrawn_child_records",
                         init_adapter=plan["parent"]["adapter"])
    manifest = read(adapter / "train_manifest.json")
    require(manifest["corpus"]["sha256"] == plan["input_hashes"]["training.json"], "fit corpus pin differs")
    check_fit(manifest, prepared, plan["configs"][arm], plan["parent"], arm)
    norms = tensor_diagnostics(trainer, plan["parent"], adapter, manifest)
    require((norms["changed_elements"] > 0 and norms["l2"]["delta"] > 0) if arm == "WRITE" else
            (norms["changed_elements"] == 0 and norms["l2"]["delta"] == 0), "paired parameter-change invariant differs")
    files = helper.check_adapter(adapter, plan["configs"][arm])
    require(bound["formation"].tree(plan["parent"]["adapter"]) == plan["parent"]["adapter_files"], "immutable parent changed")
    write(directory / "fit.json", dict(arm=arm, adapter=str(adapter), adapter_files=files, updates=prepared["updates"],
          initialized_from=plan["parent"], training_sha256=plan["input_hashes"]["training.json"], calls=0, norms=norms,
          elapsed_seconds=time.monotonic() - started))


def route_for(plan, bound, arm):
    fit = read(Path(plan["root"]) / "run" / (arm + "_fit") / "fit.json")
    expected = str(Path(plan["root"]) / "run" / (arm + "_fit") / "adapter")
    require(fit["arm"] == arm and fit["adapter"] == expected and fit["initialized_from"] == plan["parent"] and
            bound["formation"].tree(expected) == fit["adapter_files"], "fitted route identity differs")
    return dict(name="real_record_memory_" + arm.lower(), id=1, path=expected)


def capture_readout(plan, bound, arm, backend_factory=None):
    directory = Path(plan["root"]) / "run" / (arm + "_readout")
    calls = read(Path(plan["root"]) / "calls.json")
    route = route_for(plan, bound, arm)
    native = (backend_factory or bound["formation"].Native)(plan, bound["probe"], route)
    require(native.tokenizer.chat_template == plan["chat_template"], "readout template drift")
    rebuilt = build_calls(bound["dataset"], bound["retention"], bound["original_calls"], native.tokenizer, bound["probe"])
    require(encoded(calls) == encoded(rebuilt), "cold readout prefix drift")
    write(directory / "identity.json", dict(arm=arm, route=route, model_files=plan["model_files"], parent=plan["parent"], params=plan["params"]))
    for call in calls:
        request = dict(call, params=plan["params"], lora_request=route)
        write(directory / (call["call_id"] + ".request.json"), request)
        response = native.generate(request)
        write(directory / (call["call_id"] + ".response.json"), response)
        bound["formation"].validate_response(request, response, route)
    write(directory / "readout.json", dict(calls=len(calls), updates=0, arm=arm))


def worker(root, plan_sha256, stage, allow_gpu=False):
    require(allow_gpu is True and stage in STAGES, "explicit GPU worker/stage required")
    offline()
    directory = Path(root) / "run" / stage
    try:
        plan, bound = verify(root, plan_sha256, native=True)
        require(stage in plan["stages"] and os.environ.get("CUDA_VISIBLE_DEVICES") == plan["gpu_uuid"] and
                os.getpid() == os.getpgrp(), "worker allocation/process isolation differs")
        write(directory / "started.json", dict(pid=os.getpid(), pgid=os.getpgrp(), stage=stage, plan_sha256=plan_sha256))
        arm, operation = stage.split("_")
        if operation == "fit":
            fit_arm(plan, bound, arm)
        else:
            capture_readout(plan, bound, arm)
    except BaseException as error:
        failure(directory / "failure.json", error)
        raise


def identity(pid):
    fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
    return dict(pid=pid, pgid=int(fields[2]), start_ticks=int(fields[19]))


def cleanup_owned(process, expected, probe):
    if process.poll() is None:
        require(identity(process.pid) == expected and expected["pgid"] == process.pid, "refuse unowned process cleanup")
    else:
        try:
            require(identity(process.pid) == expected, "PID reused before cleanup")
        except FileNotFoundError:
            pass
    require(probe.cleanup(process) and not probe.group_alive(process.pid), "owned group cleanup failed")


def run_stage(plan, plan_sha256, stage, deadline, bound):
    probe = bound["probe"]
    check_allocation(plan)
    require(deadline - time.monotonic() > GPU_QUERY_SECONDS + CLEANUP_SECONDS and probe.gpu_state(plan) is True,
            "fresh assigned GPU vacancy/budget check failed")
    directory = Path(plan["root"]) / "run" / stage
    directory.mkdir()
    process = None
    expected = None
    try:
        with (directory / "stdout.log").open("xb") as output, (directory / "stderr.log").open("xb") as errors:
            command = [plan["python"], "-B", str(SELF), "worker", "--root", plan["root"], "--plan-sha256", plan_sha256,
                       "--stage", stage, "--allow-gpu"]
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=output, stderr=errors,
                                       env=dict(os.environ, CUDA_VISIBLE_DEVICES=plan["gpu_uuid"]), start_new_session=True)
            expected = identity(process.pid)
            require(expected["pgid"] == process.pid, "worker process group differs")
            write(directory / "launch.json", dict(identity=expected, stage=stage, plan_sha256=plan_sha256, command=command))
            require(process.wait(timeout=max(.01, deadline - time.monotonic() - CLEANUP_SECONDS)) == 0, "native memory worker failed")
    finally:
        if process is not None:
            try:
                require(expected is not None, "missing owned process identity")
                cleanup_owned(process, expected, probe)
                require(probe.gpu_state(plan) is True, "all-process GPU release failed")
                write(directory / "released.json", dict(identity=expected, stage=stage))
            except BaseException as error:
                failure(directory / "cleanup_failure.json", error)
                raise


def validate_completed(plan, plan_sha256, bound):
    root = Path(plan["root"])
    require(not (root / "controller_failure.json").exists(), "failed memory controller")
    inventory, pids, manifests = {}, [], {}
    prepared = read(root / "training.json")
    calls = read(root / "calls.json")
    for stage in plan["stages"]:
        directory = root / "run" / stage
        require(not any((directory / name).exists() for name in ("failure.json", "cleanup_failure.json")), "failed native stage")
        launch, started, released = (read(directory / name) for name in ("launch.json", "started.json", "released.json"))
        expected = launch["identity"]
        require(expected == released["identity"] and expected["pid"] == expected["pgid"] == started["pid"] == started["pgid"] and
                type(expected["start_ticks"]) is int and expected["start_ticks"] > 0 and
                launch["stage"] == started["stage"] == released["stage"] == stage and
                launch["plan_sha256"] == started["plan_sha256"] == plan_sha256, "process custody differs")
        pids.append(expected["pid"])
        arm, operation = stage.split("_")
        if operation == "fit":
            fit = read(directory / "fit.json")
            route_for(plan, bound, arm)
            require(fit["updates"] == prepared["updates"] and fit["calls"] == 0 and fit["training_sha256"] == plan["input_hashes"]["training.json"], "fit receipt differs")
            manifest = read(directory / "adapter/train_manifest.json")
            check_fit(manifest, prepared, plan["configs"][arm], plan["parent"], arm)
            bound["helper"].check_adapter(directory / "adapter", plan["configs"][arm])
            manifests[arm] = manifest
        else:
            route = route_for(plan, bound, arm)
            require(read(directory / "identity.json") == dict(arm=arm, route=route, model_files=plan["model_files"], parent=plan["parent"], params=plan["params"]), "readout identity differs")
            require(read(directory / "readout.json") == dict(arm=arm, calls=len(calls), updates=0), "readout workload differs")
            for suffix in (".request.json", ".response.json"):
                require({path.name for path in directory.glob("*" + suffix)} == {call["call_id"] + suffix for call in calls}, "raw call inventory differs")
            for call in calls:
                request = read(directory / (call["call_id"] + ".request.json"))
                response = read(directory / (call["call_id"] + ".response.json"))
                require(request == dict(call, params=plan["params"], lora_request=route), "readout request changed")
                bound["formation"].validate_response(request, response, route)
        inventory[stage] = bound["formation"].tree(directory)
    require(len(set(pids)) == len(plan["stages"]), "separate cold processes required")
    if manifests:
        require(manifests["WRITE"]["warm_start"]["initialized_state"] == manifests["LR0"]["warm_start"]["initialized_state"] and
                manifests["WRITE"]["warm_start"]["source_state"] == manifests["LR0"]["warm_start"]["source_state"], "paired initialized tensors differ")
    require(2 * plan["calls_per_arm"] <= MAX_CALLS and 2 * plan["updates_per_arm"] <= MAX_UPDATES, "per-seed work cap exceeded")
    return inventory


def controller(root, plan_sha256, allow_gpu=False):
    require(allow_gpu is True, "Main-only --allow-gpu required")
    offline()
    require(not os.environ.get("CUDA_VISIBLE_DEVICES"), "controller must not reserve CUDA")
    root = Path(root).absolute()
    try:
        with budget(OUTER_SECONDS):
            deadline = time.monotonic() + OUTER_SECONDS
            plan, bound = verify(root, plan_sha256, native=True)
            check_allocation(plan)
            write(root / "controller_started.json", dict(plan_sha256=plan_sha256, pid=os.getpid(), started=time.time(), seconds=OUTER_SECONDS))
            (root / "run").mkdir()
            for stage in plan["stages"]:
                run_stage(plan, plan_sha256, stage, deadline, bound)
            inventory = validate_completed(plan, plan_sha256, bound)
            require(time.monotonic() < deadline, "total controller cap exceeded")
            write(root / "capture_complete.json", dict(plan_sha256=plan_sha256, stages=inventory, status=plan["status"],
                  calls=2 * plan["calls_per_arm"], updates=2 * plan["updates_per_arm"], scored=False,
                  elapsed_seconds=OUTER_SECONDS - (deadline - time.monotonic()), automatic_pass=False))
            return dict(status="MEMORY_CAPTURE_COMPLETE_NOT_SCORED", completion_sha256=digest(root / "capture_complete.json"))
    except BaseException as error:
        failure(root / "controller_failure.json", error)
        raise


def score_calls(plan, bound, arm):
    root = Path(plan["root"])
    panels = {name: [] for name in ("exact", "paraphrase", "held", "canary")}
    for call in read(root / "calls.json"):
        path = root / "run" / (arm + "_readout") / (call["call_id"] + ".response.json")
        response = read(path)
        if call["panel"] in ("exact", "paraphrase"):
            score = bound["memory"].score_readback(bound["capture"], call["row_id"], response["text"], response["finish_reason"],
                       input_messages=call["messages"], variant=call["panel"], **bound["kwargs"])
        else:
            row = next(row for row in bound["retention"]["evaluation"][call["panel"]] if row["row_id"] == call["row_id"])
            score = bound["material"].score_row(row, response["text"], response["finish_reason"])
            bound["helper"].validate_score(score, response["finish_reason"])
        panels[call["panel"]].append(dict(row_id=call["row_id"], raw=response["text"], finish_reason=response["finish_reason"],
                                         response_sha256=digest(path), score=score,
                                         cost=dict(prompt_tokens=len(response["actual_prompt_token_ids"]), output_tokens=len(response["output_token_ids"]),
                                                   generation_seconds=response["ended"] - response["started"])))
    return panels


def paired_counts(first, second):
    require(set(first) == set(second), "paired row join differs")
    require(all(type(value) is bool for value in [*first.values(), *second.values()]), "typed paired outcomes required")
    return dict(total=len(first), both=sum(first[key] and second[key] for key in first),
                neither=sum(not first[key] and not second[key] for key in first),
                first_only=sum(first[key] and not second[key] for key in first),
                second_only=sum(not first[key] and second[key] for key in first))


def summarize(results, bound):
    totals, contrasts, retained = {}, {}, {}
    metrics = ("production_eligible", "content_correct", "strict_canonical", "exact_target_bytes")
    def outcomes(rows, panel, metric):
        require(len({row["row_id"] for row in rows}) == len(rows), "duplicate scored row")
        return {row["row_id"]: (row["score"]["exact_target_bytes"] if metric == "exact_target_bytes" else
                row["score"]["score"][metric] if panel in ("exact", "paraphrase") else row["score"][metric]) for row in rows}
    if not results:
        return dict(totals={}, paired_WRITE_LR0={}, original_retention={}, reason="NO_WRITE; no fitted/readout endpoints")
    for arm, panels in results.items():
        totals[arm] = {}
        for panel, rows in panels.items():
            selected = metrics if panel in ("exact", "paraphrase") else ("passed", "content_correct", "strict")
            totals[arm][panel] = dict(denominator=len(rows), numerators={metric: sum(outcomes(rows, panel, metric).values()) for metric in selected},
                format_counts=dict(Counter((row["score"]["score"] if panel in ("exact", "paraphrase") else row["score"])["format"] for row in rows)),
                generation_costs={key: sum(row["cost"][key] for row in rows) for key in ("prompt_tokens", "output_tokens", "generation_seconds")})
            if panel in ("exact", "paraphrase"):
                totals[arm][panel]["possible_denominator"] = 16
                totals[arm][panel]["field_correct"] = {field: sum(row["score"]["score"]["field_correct"][field] for row in rows)
                                                         for field in ("try", "observed", "predicted", "relation")}
    for panel in results["WRITE"]:
        selected = metrics if panel in ("exact", "paraphrase") else ("passed", "content_correct", "strict")
        contrasts[panel] = {metric: paired_counts(outcomes(results["WRITE"][panel], panel, metric), outcomes(results["LR0"][panel], panel, metric)) for metric in selected}
    parent = bound["parent"]
    path = Path(parent["collection"]["path"]).parent / "scores.json"
    require(digest(path) == parent["scores_sha256"], "original retention score pin differs")
    original = read(path)
    for arm in ARMS:
        retained[arm] = {}
        for panel in ("held", "canary"):
            old_rows = original["cells"]["post"][panel]["rows"]
            for row in old_rows:
                reference = next(item for item in bound["retention"]["evaluation"][panel] if item["row_id"] == row["row_id"])
                require(bound["material"].score_row(reference, row["raw"], row["finish_reason"]) == row["score"], "original retention score replay differs")
            old = outcomes(old_rows, panel, "passed")
            new = outcomes(results[arm][panel], panel, "passed")
            counts = paired_counts(new, old)
            retained[arm][panel] = dict(counts=counts, retained=[key for key in old if old[key] and new[key]],
                regressed=[key for key in old if old[key] and not new[key]], gained=[key for key in old if not old[key] and new[key]],
                original_scores_sha256=parent["scores_sha256"])
    return dict(totals=totals, paired_WRITE_LR0=contrasts, original_retention=retained,
                pair_direction="first=WRITE/second=LR0; retention first=current/second=original post")


def collect(root, plan_sha256, completion_sha256, out):
    offline()
    root = Path(root).absolute()
    with budget(COLLECTION_SECONDS):
        plan, bound = verify(root, plan_sha256)
        out = new_external(out, [root, *protected_inputs(plan["specification"], bound)])
        require(digest(root / "capture_complete.json") == completion_sha256, "completed memory capture pin differs")
        complete = read(root / "capture_complete.json")
        require(complete["plan_sha256"] == plan_sha256 and complete["scored"] is False and
                type(complete["elapsed_seconds"]) in (int, float) and 0 <= complete["elapsed_seconds"] <= OUTER_SECONDS and
                complete["stages"] == validate_completed(plan, plan_sha256, bound) and
                complete["calls"] == 2 * plan["calls_per_arm"] and complete["updates"] == 2 * plan["updates_per_arm"], "memory completion custody differs")
        write(root.with_name(root.name + ".collection_claim.json"), dict(plan_sha256=plan_sha256, out=str(out), retry=False))
        out.mkdir()
        try:
            results = {arm: score_calls(plan, bound, arm) for arm in ARMS} if plan["stages"] else {}
            report = dict(scope=SCOPE, claim=CLAIM, plan_sha256=plan_sha256, completion_sha256=completion_sha256,
                          formation=plan["specification"]["formation"], seed=plan["specification"]["seed"], parent=plan["parent"],
                          status=plan["status"], counts=bound["dataset"]["counts"], refused=bound["dataset"]["refused"], cells=results,
                          memory_possible_denominator_per_variant=16, memory_scored_denominator=len(bound["dataset"]["rows"]),
                          retention_denominators=dict(held=48, canary=12), calls=complete["calls"], updates=complete["updates"],
                          fits={arm: read(root / "run" / (arm + "_fit") / "adapter/train_manifest.json") for arm in ARMS} if plan["stages"] else {},
                          parameter_diagnostics={arm: read(root / "run" / (arm + "_fit") / "fit.json")["norms"] for arm in ARMS} if plan["stages"] else {},
                          training_costs={key: value for key, value in read(root / "training.json").items() if key not in ("items", "encoding", "epoch_order")},
                          summary=summarize(results, bound),
                          native_capture_custody_checked=True, automatic_pass=False, scientific_pass=None,
                          interpretation="Separate exact-cue acquisition, paraphrase transfer, production grammar/content and authored retention; no pooled pass.")
            write(out / "scores.json", report)
            write(out / "collection.json", dict(scores_sha256=digest(out / "scores.json"), completion_sha256=completion_sha256))
            return dict(status="COLLECTED_EXPLORATORY_MEMORY", out=str(out), scores_sha256=digest(out / "scores.json"))
        except BaseException as error:
            failure(out / "collection_failure.json", error)
            raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    command = commands.add_parser("prepare")
    for name in ("root", "spec-path", "spec-sha256"):
        command.add_argument("--" + name, required=True)
    command.add_argument("--allow-native", action="store_true")
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
    options = vars(parser.parse_args(argv))
    name = options.pop("command")
    result = {"prepare": prepare, "controller": controller, "worker": worker, "collect": collect}[name](**options)
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
