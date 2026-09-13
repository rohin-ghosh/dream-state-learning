"""Fresh ADDITIVE versus MEMORY_ONLY; Main owns all native operations."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time


SELF = Path(__file__).resolve()
SCOPE = "astra_additive_replay_pair_20260913_v1"
REPAIR_PIN = "f1e3782378959f0c2552eaf9646a6b8827b876652a535d3248e38fe28371c4fe"
FROZEN_TRAINER_PIN = "7bbf165fcb4b8ae3a1180328bcd19f57382c30516daddc95fd61e8a2c749fad7"
CORE_PIN = "b58e4c90e2abdd26648475c9fb1fe92e3bc3fef2fa7664ecaaa69fc93591076a"
TRAINER_PIN = "3f2e73ef69b12c8db211e1d3043e4559713e036ffe09571ab8bc4c5199a426a0"
PROTOCOL_PIN = "724d5a6e1aea7dca4b0ae42aec6e2fd0252b98646f7c903432927263f2c391e9"
ARMS = ("ADDITIVE", "MEMORY_ONLY")
STAGES = tuple(arm + suffix for arm in ARMS for suffix in ("_fit", "_readout"))
SECONDS, PREPARE_SECONDS, COLLECTION_SECONDS = 7200, 180, 180
MEMORY_COUNTS = (14, 8, 8)
HISTORY = ("LOWER", "HIGH", "LR0", "REPLAY", "EXTRA_MEMORY")
CLAIM = ("Exploratory additive observation CE with exact historical EXTRA_MEMORY occurrence/order dose; "
         "fresh MEMORY_ONLY comparator and original parents. Not matched tokens/FLOPs/RNG or trajectories. "
         "Historical endpoints noncontemporaneous; no new capture, teacher, parenting, H1/H2 or automatic promotion.")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    checksum = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            checksum.update(block)
    return checksum.hexdigest()


def pinned(record, expected=None):
    require(type(record) is dict and set(record) == {"path", "sha256"} and Path(record["path"]).is_absolute() and
            (expected is None or record["sha256"] == expected) and digest(record["path"]) == record["sha256"], "input/source pin differs")


def runtime():
    sys.dont_write_bytecode = True
    path = "/tmp/astra_own_replay_repair_run_20260913.py"
    pinned(dict(path=path, sha256=REPAIR_PIN), REPAIR_PIN)
    spec = importlib.util.spec_from_file_location("additive_frozen_repair_bootstrap", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.runtime()


def validate_spec(spec):
    require(set(spec) == {"runner_sha256", "repair_runtime", "core", "trainer", "protocol", "repair_history", "seed", "fit_seed",
                         "gpu_index", "gpu_uuid", "expected_boot_id", "lease_end"}, "closed additive spec differs")
    require(spec["runner_sha256"] == digest(SELF) and CORE_PIN is not None and TRAINER_PIN is not None, "final runner/core/trainer pins required")
    for key, pin in (("repair_runtime", REPAIR_PIN), ("core", CORE_PIN), ("trainer", TRAINER_PIN), ("protocol", PROTOCOL_PIN)):
        pinned(spec[key], pin)
    require(type(spec["seed"]) is int and spec["seed"] in (0, 1, 2) and type(spec["fit_seed"]) is int and
            spec["fit_seed"] == spec["seed"], "original seed/optimizer seed required")
    binding = spec["repair_history"]
    require(set(binding) == {"root", "plan_sha256", "completion_sha256", "collection", "scores_sha256"} and
            Path(binding["root"]).is_absolute(), "closed completed repair binding required")
    pinned(binding["collection"])
    require(type(spec["gpu_index"]) is int and spec["gpu_index"] >= 0 and type(spec["gpu_uuid"]) is str and
            spec["gpu_uuid"].startswith("GPU-") and type(spec["expected_boot_id"]) is str and len(spec["expected_boot_id"]) == 36 and
            type(spec["lease_end"]) in (int, float) and math.isfinite(spec["lease_end"]), "Main allocation/boot/lease required")


def allocation(plan):
    spec = plan["specification"]
    require(Path("/proc/sys/kernel/random/boot_id").read_text().strip() == spec["expected_boot_id"], "current boot differs")
    require(spec["lease_end"] > time.time() + SECONDS + COLLECTION_SECONDS + 21600, "six-hour lease-finish margin required")


def bind(spec, native=False):
    validate_spec(spec)
    memory = runtime()
    old = memory.load(spec["repair_runtime"], "additive_old_repair", REPAIR_PIN)
    core = memory.load(spec["core"], "additive_material", CORE_PIN)
    trainer = memory.load(spec["trainer"], "additive_trainer", TRAINER_PIN)
    history = spec["repair_history"]
    _, old_plan, old_bound = old.verify(history["root"], history["plan_sha256"], native=native)
    require(old_plan["specification"]["seed"] == spec["seed"] and old_plan["status"] == "READY" and
            old_plan["counts"]["replay"] == 24 and old_plan["parent"] == old_bound["memory_plan"]["parent"], "fixed completed source bank/parent differs")
    path = Path(history["root"]) / "capture_complete.json"
    require(digest(path) == history["completion_sha256"], "repair completion pin differs")
    complete = memory.read(path)
    require(complete["scope"] == old.SCOPE and complete["plan_sha256"] == history["plan_sha256"] and
            complete["status"] == "READY" and complete["scored"] is False and
            complete["stages"] == old.validate_completed(memory, old_plan, history["plan_sha256"], old_bound) and
            all(complete[key] == old_plan["limits"][key] for key in ("fits", "updates", "calls")) and
            type(complete["elapsed_seconds"]) in (int, float) and 0 <= complete["elapsed_seconds"] <= old.SECONDS, "completed repair custody differs")
    scores = old.collected(memory, history, "scores.json", "scores_sha256")
    require(scores["scope"] == old.SCOPE and scores["seed"] == spec["seed"] and scores["parent"] == old_plan["parent"] and
            scores["plan_sha256"] == history["plan_sha256"] and scores["completion_sha256"] == history["completion_sha256"] and
            scores["native_capture_custody_checked"] is True and set(scores["cells"]) == set(old.ARMS) and
            scores["historical_cells"] == old_bound["history"], "historical score identity differs")
    for arm in old.ARMS:
        require(scores["cells"][arm] == memory.score_calls(old_plan, old_bound, arm) and
                scores["fits"][arm] == memory.read(Path(old_plan["root"]) / "run" / (arm + "_fit") / "adapter/train_manifest.json"),
                "historical raw/fit join differs")
    saved = {arm: memory.read(Path(old_plan["root"]) / f"training_{arm}.json") for arm in old.ARMS}
    saved_hashes = {arm: digest(Path(old_plan["root"]) / f"training_{arm}.json") for arm in old.ARMS}
    require(all(saved_hashes[arm] == old_plan["input_hashes"][f"training_{arm}.json"] for arm in old.ARMS), "actual original training file bytes differ")
    material = core.build(old_plan, dict(old_bound, saved_training=saved, saved_training_sha256=saved_hashes), protocol_path=spec["protocol"]["path"])
    return dict(old_bound, old=old, old_plan=old_plan, old_bound=old_bound, core=core, additive_trainer=trainer,
                material=material, saved_training=saved, history=dict(old_bound["history"], **scores["cells"]),
                historical_manifests=dict(old_bound["historical_manifests"], **scores["fits"]))


def configs(bound, seed):
    config = bound["old_plan"]["configs"]["EXTRA_MEMORY"]
    require(config == bound["old_plan"]["configs"]["REPLAY"] and config["seed"] == seed and config["lr"] == 3e-5 and
            config["epochs"] == 8 and config["batch_size"] == config["grad_accum"] == 1 and config["max_steps"] == 0 and
            config["rank"] == 8 and config["alpha"] == 16 and config["dropout"] == .05 and config["max_len"] == 1024 and
            config["pack"] is False and config["add_eos"] is False, "unchanged recipe required")
    return {arm: copy.deepcopy(config) for arm in ARMS}


def paired(bound):
    source = {arm: digest(Path(bound["old_plan"]["root"]) / f"training_{arm}.json") for arm in ("EXTRA_MEMORY", "REPLAY")}
    require(all(source[arm] == bound["old_plan"]["input_hashes"][f"training_{arm}.json"] for arm in source), "original file-byte pins differ")
    result = bound["additive_trainer"].prepare_pair(bound["saved_training"]["EXTRA_MEMORY"], bound["saved_training"]["REPLAY"],
        seed=bound["material"]["seed"], source_pins=dict(extra_memory_sha256=source["EXTRA_MEMORY"], replay_sha256=source["REPLAY"]))
    require(result["primary"] == bound["saved_training"]["EXTRA_MEMORY"] and result["replay"] == bound["saved_training"]["REPLAY"] and
            result["pairs"] == bound["material"]["pairs"] and result["protocol_sha256"] == PROTOCOL_PIN and
            result["seed"] == result["fit_seed"] == bound["material"]["seed"], "core/trainer pairing or original schedule differs")
    for arm in ARMS:
        prepared = bound["core"].prepared_from_saved(bound["material"], arm)
        expected = expected_costs(prepared)
        require(all(result["costs"][arm][key] == value for key, value in expected.items()), "trainer/core executed token dose differs")
    return result


def expected_costs(prepared):
    account = prepared["token_accounting"]
    result = {key: account[key] for key in ("memory_total_tokens", "memory_supervised_tokens", "memory_context_tokens",
                                           "replay_total_tokens", "replay_supervised_tokens", "replay_context_tokens")}
    result.update(updates=prepared["updates"], memory_forwards=account["memory_presentations"], replay_forwards=account["replay_presentations"],
                  total_forwards=account["total_forward_sequences"], total_tokens=account["total_forward_tokens"],
                  supervised_tokens=account["total_supervised_tokens"], context_tokens=account["total_context_tokens"])
    return result


def encode(bound, arm, tokenizer, fit_seed):
    return bound["core"].encode(bound["material"], arm, tokenizer, bound["trainer"], bound["helper"], bound["probe"], fit_seed)


def snapshots(spec, bound):
    paths = bound["old"].snapshots(bound["old_plan"]["specification"], bound["old_bound"])
    paths = {"upstream/" + name: path for name, path in paths.items()}
    root = Path(spec["repair_history"]["root"])
    for name in ("plan.json", "spec.json", "capture_complete.json", "mixture.json", "training_EXTRA_MEMORY.json", "training_REPLAY.json", "calls.json"):
        paths["repair/" + name] = root / name
    receipt = Path(spec["repair_history"]["collection"]["path"])
    paths.update({"repair/collection.json": receipt, "repair/scores.json": receipt.parent / "scores.json"})
    for key in ("repair_runtime", "core", "trainer", "protocol"):
        paths["sources/" + Path(spec[key]["path"]).name] = Path(spec[key]["path"])
    paths["sources/frozen_train_adapter_v3.py"] = Path(bound["trainer"].__file__)
    return paths


def protected(spec, bound):
    return [SELF, *(spec[key]["path"] for key in ("repair_runtime", "core", "trainer", "protocol")),
            spec["repair_history"]["root"], Path(spec["repair_history"]["collection"]["path"]).parent,
            *bound["old"].protected(bound["old_plan"]["specification"], bound["old_bound"])]


def make_plan(root, spec, spec_sha256, bound, inputs, snapshot_hashes):
    original, count = bound["memory_plan"], MEMORY_COUNTS[spec["seed"]]
    require(bound["material"]["counts"]["memory"] == count and bound["material"]["counts"]["replay"] == 24, "exact fixed source counts required")
    return dict(scope=SCOPE, claim=CLAIM, root=str(Path(root).absolute()), specification=spec, spec_sha256=spec_sha256,
        self_sha256=digest(SELF), status="READY", stages=list(STAGES),
        **{key: copy.deepcopy(original[key]) for key in ("model", "model_files", "chat_template", "environment", "source", "parent", "engine", "params", "python", "python_sha256")},
        configs=configs(bound, spec["seed"]), input_hashes=inputs, snapshot_hashes=snapshot_hashes,
        counts=dict(memory=count, replay=24, rows_per_arm=count + 24), updates_per_arm=8 * (count + 24), calls_per_arm=2 * count + 60,
        gpu_index=spec["gpu_index"], gpu_uuid=spec["gpu_uuid"],
        limits=dict(controller=SECONDS, prepare=PREPARE_SECONDS, collection=COLLECTION_SECONDS, fits=2,
                    updates=16 * (count + 24), calls=2 * (2 * count + 60), global_fits=6, global_updates=1632, global_calls=480,
                    aggregate_allocation_hours=8, new_source_calls=0, teacher_calls=0),
        reused_endpoints={name: dict(noncontemporaneous=True, incremental_fits=0, incremental_updates=0, incremental_calls=0) for name in HISTORY})


def prepare(root, spec_path, spec_sha256, allow_native=False):
    entry = time.monotonic()
    require(allow_native is True and not os.environ.get("CUDA_VISIBLE_DEVICES"), "Main-only native CPU prepare with empty CVD required")
    memory = runtime()
    memory.offline()
    with memory.budget(entry + PREPARE_SECONDS - time.monotonic()):
        require(digest(spec_path) == spec_sha256, "spec pin differs")
        spec = memory.read(spec_path)
        bound = bind(spec, native=True)
        root = memory.new_external(root, [spec_path, *protected(spec, bound)])
        allocation(dict(specification=spec))
        root.mkdir()
        memory.write(root / "prepare_started.json", dict(spec_sha256=spec_sha256, monotonic=entry, time=time.time()))
        try:
            tokenizer = bound["probe"].native_tokenizer(bound["memory_plan"]["model"])
            require(tokenizer.chat_template == bound["memory_plan"]["chat_template"], "original native template differs")
            calls = memory.build_calls(bound["dataset"], bound["retention"], bound["original_calls"], tokenizer, bound["probe"])
            require(calls == memory.read(Path(bound["old_plan"]["root"]) / "calls.json"), "original readout prompt/token drift")
            payloads = dict({"material.json": bound["material"], "paired.json": paired(bound), "calls.json": calls},
                            **{f"training_{arm}.json": encode(bound, arm, tokenizer, spec["fit_seed"]) for arm in ARMS})
            inputs, hashes = {}, {}
            for name, payload in payloads.items():
                memory.write(root / name, payload)
                inputs[name] = digest(root / name)
            for name, path in {**snapshots(spec, bound), "spec.json": Path(spec_path)}.items():
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                checksum = digest(path)
                with target.open("xb") as output:
                    output.write(Path(path).read_bytes())
                require(digest(target) == checksum, "copied source changed")
                hashes[name] = checksum
            plan = make_plan(root, spec, spec_sha256, bound, inputs, hashes)
            for arm in ARMS:
                bound["trainer"]._warm_parent(plan["parent"]["adapter"], root / "run" / (arm + "_fit") / "adapter",
                                               bound["trainer"].TrainConfig(**plan["configs"][arm]))
            memory.write(root / "plan.json", plan)
            elapsed = time.monotonic() - entry
            require(elapsed <= PREPARE_SECONDS, "prepare entry budget exceeded")
            memory.write(root / "prepare_done.json", dict(plan_sha256=digest(root / "plan.json"), elapsed_seconds=elapsed))
            return dict(status="NATIVE_CPU_PREPARED_NOT_LAUNCHED", plan_sha256=digest(root / "plan.json"), counts=plan["counts"], limits=plan["limits"])
        except BaseException as error:
            memory.failure(root / "prepare_failure.json", error)
            raise


def verify(root, plan_sha256, native=False):
    memory, root = runtime(), Path(root).absolute()
    require(digest(root / "plan.json") == plan_sha256, "additive plan pin differs")
    plan = memory.read(root / "plan.json")
    bound = bind(plan["specification"], native=native)
    hashes = {name: digest(path) for name, path in snapshots(plan["specification"], bound).items()}
    hashes["spec.json"] = plan["spec_sha256"]
    require(plan == make_plan(root, plan["specification"], plan["spec_sha256"], bound, plan["input_hashes"], hashes), "independent additive plan differs")
    require(set(plan["input_hashes"]) == {"material.json", "paired.json", "calls.json", *{f"training_{arm}.json" for arm in ARMS}} and
            plan["python"] == os.path.abspath(sys.executable) and plan["python_sha256"] == digest(sys.executable), "prepared inventory/interpreter differs")
    require(not (root / "prepare_failure.json").exists() and memory.read(root / "prepare_started.json")["spec_sha256"] == plan["spec_sha256"] and
            memory.read(root / "spec.json") == plan["specification"], "successful preparation required")
    finished = memory.read(root / "prepare_done.json")
    require(finished["plan_sha256"] == plan_sha256 and type(finished["elapsed_seconds"]) in (int, float) and
            0 <= finished["elapsed_seconds"] <= PREPARE_SECONDS, "prepare completion/budget differs")
    for name, checksum in {**hashes, **plan["input_hashes"]}.items():
        require(digest(root / name) == checksum, "prepared immutable input differs: " + name)
    require(memory.read(root / "material.json") == bound["material"] and memory.read(root / "paired.json") == paired(bound) and
            memory.read(root / "calls.json") == memory.read(Path(bound["old_plan"]["root"]) / "calls.json"), "material/pair/readout source differs")
    for arm in ARMS:
        require(memory.read(root / f"training_{arm}.json") == bound["core"].prepared_from_saved(bound["material"], arm), "exact original schedule differs")
    return memory, plan, bound


def check_fit(manifest, prepared, config, parent, arm, counts, trainer_pair):
    require(arm in ARMS and prepared["arm"] == arm and prepared["rows"] == counts["memory"] + 24 and counts["replay"] == 24 and
            prepared["updates"] == 8 * prepared["rows"] <= 304, "fixed full memory dose required")
    require(manifest["config"] == config and config["lr"] == 3e-5 and config["epochs"] == 8 and
            config["batch_size"] == config["grad_accum"] == 1 and config["max_steps"] == 0 and config["rank"] == 8 and
            config["alpha"] == 16 and config["dropout"] == .05, "unchanged fit config required")
    require(manifest["empty"] is False and all(type(manifest[key]) is int for key in ("steps", "micro_batches", "epochs_run", "nonfinite_batches")) and
            manifest["steps"] == manifest["micro_batches"] == prepared["updates"] and manifest["epochs_run"] == 8 and
            manifest["nonfinite_batches"] == 0, "fit updates/nonfinite differs")
    require(manifest["corpus"]["n_items"] == manifest["corpus"]["n_encoded"] == prepared["rows"] and
            manifest["corpus"]["n_skipped_no_target"] == 0 and all(manifest["truncation"][key] == 0 for key in
                ("items_truncated", "context_tokens_dropped", "target_tokens_dropped", "items_split")), "fit skipped/truncated items")
    require(manifest["schema"] == "astra_additive_replay_train_20260913_v1" and manifest["arm"] == arm and
            manifest["objective"] == prepared["objective"] and manifest["trainer_sha256"] == TRAINER_PIN and
            manifest["frozen_trainer_sha256"] == FROZEN_TRAINER_PIN and manifest["protocol_sha256"] == PROTOCOL_PIN and
            manifest["paired_sha256"] == trainer_pair["paired_sha256"] and manifest["source_pins"] == trainer_pair["source_pins"] and
            manifest["primary_encoding_sha256"] == prepared["source_encoding_sha256"] and
            manifest["primary_training_items_sha256"] == prepared["training_items_sha256"] and
            manifest["primary_epoch_order_sha256"] == prepared["epoch_order_sha256"] and manifest["pairs_sha256"] == prepared["pair_sha256"],
            "explicit objective/schedule/source identity differs")
    costs = expected_costs(prepared)
    require(manifest["costs"] == trainer_pair["costs"][arm] and all(manifest["costs"][key] == value for key, value in costs.items()) and
            manifest["memory_forwards"] == costs["memory_forwards"] and manifest["replay_forwards"] == costs["replay_forwards"] and
            manifest["optimizer_steps"] == prepared["updates"] and
            manifest["train_tokens_seen"] == costs["total_tokens"] and manifest["tokens"]["target"] == prepared["target_tokens"] and
            manifest["tokens"]["total"] == prepared["total_tokens"] and manifest["packing"]["mode"] == "one_item_per_sequence" and
            manifest["packing"]["n_sequences"] == prepared["rows"], "actual additive/primary token accounting differs")
    pairs = {pair["memory_row_id"]: pair["replay_row_id"] for pair in prepared["pairs"]}
    order = [dict(epoch=epoch, position=position, memory_row_id=row_id, replay_row_id=pairs.get(row_id) if arm == "ADDITIVE" else None)
             for epoch, rows in enumerate(prepared["epoch_order"]) for position, row_id in enumerate(rows)]
    require(manifest["executed_order"] == order and len(manifest["component_losses"]) == len(order), "executed occurrence order differs")
    for expected, losses in zip(order, manifest["component_losses"]):
        require(all(losses[key] == value for key, value in expected.items()) and
                all(type(losses[key]) in (int, float) and math.isfinite(losses[key]) for key in ("memory", "total")), "component loss/order differs")
        replay_loss = losses["replay"]
        require((type(replay_loss) in (int, float) and math.isfinite(replay_loss)) if expected["replay_row_id"] else replay_loss is None,
                "applicable replay loss differs")
        require(math.isclose(losses["total"], losses["memory"] + (replay_loss if replay_loss is not None else 0), rel_tol=1e-7, abs_tol=1e-9),
                "sum of separately normalized losses required, not mean")
    losses = manifest["mean_loss_per_epoch"]
    require(len(losses) == 8 and all(type(value) in (int, float) and math.isfinite(value) for value in losses + [manifest["final_loss"]]), "nonfinite fit loss")
    warm = manifest["warm_start"]
    require(warm["mode"] == "WEIGHT_WARM_START_FRESH_OPTIMIZER" and warm["optimizer_initialization"] == "fresh_per_write" and
            warm["optimizer_state_restored"] is False and warm["optimizer_state_saved"] is False and
            type(warm["optimizer_initial_state_entries"]) is int and warm["optimizer_initial_state_entries"] == 0 and
            warm["optimizer_class"] == "torch.optim.adamw.AdamW" and warm["optimizer_defaults"]["lr"] == config["lr"] and
            warm["parent_path"] == parent["adapter"] and warm["parent_files"] == warm["parent_files_after"] == parent["adapter_files"] and
            warm["parent_unchanged"] is True and warm["initialized_loaded_state_check"] is True and warm["base_frozen"] is True and
            warm["adapter_count"] == 1 and warm["phase_seed"] == config["seed"] and warm["phase_steps"] == prepared["updates"] and
            warm["trainer_sha256"] == manifest["frozen_trainer_sha256"] and
            warm["parent_cumulative_steps"] == 320 and warm["cumulative_steps"] == 320 + prepared["updates"], "original warm-start custody differs")
    require(warm["initialized_state"] and set(warm["initialized_state"]) == set(warm["final_state"]) and
            warm["initialized_state"] != warm["final_state"] and warm["trainable_names"] and
            all("lora_A" in name or "lora_B" in name for name in warm["trainable_names"]), "LoRA state/change differs")


def fit_arm(memory, plan, bound, arm):
    directory = Path(plan["root"]) / "run" / (arm + "_fit")
    started = time.monotonic()
    tokenizer, base = bound["reflection"].load_native_model(plan["model"])
    require(not hasattr(base, "peft_config") and tokenizer.chat_template == plan["chat_template"], "fresh base/tokenizer required")
    prepared = memory.read(Path(plan["root"]) / f"training_{arm}.json")
    require(prepared == encode(bound, arm, tokenizer, plan["specification"]["fit_seed"]), "actual original encoding/order differs")
    trainer_pair = paired(bound)
    require(trainer_pair == memory.read(Path(plan["root"]) / "paired.json"), "trainer source pairing differs")
    adapter = directory / "adapter"
    require(not adapter.exists(), "fresh fit output required")
    bound["additive_trainer"].run_training(trainer_pair, tokenizer, base, bound["trainer"].TrainConfig(**plan["configs"][arm]), str(adapter),
        arm=arm, init_adapter=plan["parent"]["adapter"], expected_parent_files=plan["parent"]["adapter_files"], trainer=bound["trainer"],
        corpus_sha=plan["input_hashes"][f"training_{arm}.json"])
    manifest = memory.read(adapter / "train_manifest.json")
    require(manifest["corpus"]["sha256"] == plan["input_hashes"][f"training_{arm}.json"], "fit corpus pin differs")
    check_fit(manifest, prepared, plan["configs"][arm], plan["parent"], arm, plan["counts"], trainer_pair)
    for historical in bound["historical_manifests"].values():
        require(all(manifest["warm_start"][key] == historical["warm_start"][key] for key in ("source_state", "initialized_state")), "original warm tensors differ")
    require(manifest["warm_start"]["optimizer_defaults"] == bound["historical_manifests"]["EXTRA_MEMORY"]["warm_start"]["optimizer_defaults"],
            "original optimizer defaults differ")
    norms = memory.tensor_diagnostics(bound["trainer"], plan["parent"], adapter, manifest)
    require(norms["changed_elements"] > 0 and norms["l2"]["delta"] > 0, "fresh parameter delta absent")
    files = bound["helper"].check_adapter(adapter, plan["configs"][arm])
    require(bound["formation"].tree(plan["parent"]["adapter"]) == plan["parent"]["adapter_files"], "original parent changed")
    memory.write(directory / "fit.json", dict(arm=arm, adapter=str(adapter), adapter_files=files, updates=prepared["updates"],
        initialized_from=plan["parent"], training_sha256=plan["input_hashes"][f"training_{arm}.json"], calls=0, norms=norms,
        elapsed_seconds=time.monotonic() - started))


def worker(root, plan_sha256, stage, allow_gpu=False):
    require(allow_gpu is True and stage in STAGES, "explicit new worker stage required")
    memory = runtime()
    memory.offline()
    directory = Path(root) / "run" / stage
    try:
        memory, plan, bound = verify(root, plan_sha256, native=True)
        require(os.environ.get("CUDA_VISIBLE_DEVICES") == plan["gpu_uuid"] and os.getpid() == os.getpgrp(), "worker allocation/isolation differs")
        allocation(plan)
        memory.write(directory / "started.json", dict(stage=stage, plan_sha256=plan_sha256, pid=os.getpid(), pgid=os.getpgrp(), time=time.time(), monotonic=time.monotonic()))
        arm, kind = stage.rsplit("_", 1)
        if kind == "fit":
            fit_arm(memory, plan, bound, arm)
        else:
            memory.capture_readout(plan, bound, arm)
        memory.write(directory / "worker_done.json", dict(stage=stage, plan_sha256=plan_sha256, monotonic=time.monotonic()))
    except BaseException as error:
        memory.failure(directory / "failure.json", error)
        raise


def run_stage(memory, plan, plan_sha256, stage, deadline, bound):
    require(stage in STAGES, "unknown additive stage")
    probe = bound["probe"]
    allocation(plan)
    reserve = memory.GPU_QUERY_SECONDS + memory.CLEANUP_SECONDS
    require(deadline - time.monotonic() > reserve and probe.gpu_state(plan) is True, "fresh GPU vacancy/budget check failed")
    directory = Path(plan["root"]) / "run" / stage
    directory.mkdir()
    process, identity = None, None
    try:
        with (directory / "stdout.log").open("xb") as output, (directory / "stderr.log").open("xb") as errors:
            command = [plan["python"], "-B", str(SELF), "worker", "--root", plan["root"], "--plan-sha256", plan_sha256, "--stage", stage, "--allow-gpu"]
            launched, monotonic = time.time(), time.monotonic()
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=output, stderr=errors,
                                       env=dict(os.environ, CUDA_VISIBLE_DEVICES=plan["gpu_uuid"]), start_new_session=True)
            identity = memory.identity(process.pid)
            require(identity["pgid"] == process.pid, "fresh isolated group required")
            memory.write(directory / "launch.json", dict(identity=identity, stage=stage, plan_sha256=plan_sha256, command=command, time=launched, monotonic=monotonic))
            code = process.wait(timeout=max(.01, deadline - time.monotonic() - reserve))
            memory.write(directory / "exit.json", dict(identity=identity, returncode=code, monotonic=time.monotonic()))
            require(code == 0, "additive worker failed")
    except BaseException as error:
        memory.failure(directory / "stage_failure.json", error)
        raise
    finally:
        if process is not None:
            try:
                require(identity is not None, "missing owned process identity")
                memory.cleanup_owned(process, identity, probe)
                require(probe.gpu_state(plan) is True and time.monotonic() < deadline, "owned release/vacancy/budget failed")
                memory.write(directory / "released.json", dict(identity=identity, stage=stage, group_absent=True, gpu_vacant=True, time=time.time(), monotonic=time.monotonic()))
            except BaseException as error:
                memory.failure(directory / "cleanup_failure.json", error)
                raise


def validate_completed(memory, plan, plan_sha256, bound):
    root = Path(plan["root"])
    require(not (root / "controller_failure.json").exists() and {path.name for path in (root / "run").iterdir()} == set(STAGES), "complete four-stage inventory required")
    controller = memory.read(root / "controller_started.json")
    previous, deadline = controller["monotonic"], controller["deadline"]
    require(controller["plan_sha256"] == plan_sha256 and deadline == previous + SECONDS and controller["seconds"] == SECONDS, "controller entry/deadline differs")
    inventory, identities, manifests = {}, [], {}
    calls = memory.read(root / "calls.json")
    for stage in STAGES:
        directory = root / "run" / stage
        require(not any(directory.glob("*failure.json")), "failed additive stage cannot collect")
        launch, started, done, exited, released = (memory.read(directory / name) for name in
                                                 ("launch.json", "started.json", "worker_done.json", "exit.json", "released.json"))
        identity = launch["identity"]
        command = [plan["python"], "-B", str(SELF), "worker", "--root", plan["root"], "--plan-sha256", plan_sha256, "--stage", stage, "--allow-gpu"]
        require(identity == exited["identity"] == released["identity"] and identity["pid"] == identity["pgid"] == started["pid"] == started["pgid"] and
                type(identity["start_ticks"]) is int and identity["start_ticks"] > 0 and launch["command"] == command and
                launch["stage"] == started["stage"] == done["stage"] == released["stage"] == stage and
                launch["plan_sha256"] == started["plan_sha256"] == done["plan_sha256"] == plan_sha256 and
                type(exited["returncode"]) is int and exited["returncode"] == 0 and
                released["group_absent"] is True and released["gpu_vacant"] is True, "fresh exit/process/release custody differs")
        times = [previous, launch["monotonic"], started["monotonic"], done["monotonic"], exited["monotonic"], released["monotonic"], deadline]
        require(all(type(value) in (int, float) and math.isfinite(value) for value in times) and times == sorted(times), "stage entry/exit chronology differs")
        previous = released["monotonic"]
        identities.append((identity["pid"], identity["start_ticks"]))
        arm, kind = stage.rsplit("_", 1)
        route = memory.route_for(plan, bound, arm)
        if kind == "fit":
            prepared = memory.read(root / f"training_{arm}.json")
            fit, manifest = memory.read(directory / "fit.json"), memory.read(directory / "adapter/train_manifest.json")
            check_fit(manifest, prepared, plan["configs"][arm], plan["parent"], arm, plan["counts"], memory.read(root / "paired.json"))
            require(fit["updates"] == plan["updates_per_arm"] and fit["calls"] == 0 and
                    fit["training_sha256"] == manifest["corpus"]["sha256"] == plan["input_hashes"][f"training_{arm}.json"] and
                    fit["norms"]["changed_elements"] > 0 and fit["norms"]["l2"]["delta"] > 0, "fit source/delta receipt differs")
            bound["helper"].check_adapter(directory / "adapter", plan["configs"][arm])
            for historical in bound["historical_manifests"].values():
                require(all(manifest["warm_start"][key] == historical["warm_start"][key] for key in ("source_state", "initialized_state")), "historical original warm tensors differ")
            require(manifest["warm_start"]["optimizer_defaults"] == bound["historical_manifests"]["EXTRA_MEMORY"]["warm_start"]["optimizer_defaults"],
                    "original optimizer defaults differ")
            manifests[arm] = manifest
        else:
            require(memory.read(directory / "identity.json") == dict(arm=arm, route=route, model_files=plan["model_files"], parent=plan["parent"], params=plan["params"]) and
                    memory.read(directory / "readout.json") == dict(arm=arm, calls=len(calls), updates=0), "cold readout identity/count differs")
            for suffix in (".request.json", ".response.json"):
                require({path.name for path in directory.glob("*" + suffix)} == {call["call_id"] + suffix for call in calls}, "cold response inventory differs")
            previous_call = started["monotonic"]
            for call in calls:
                request = memory.read(directory / (call["call_id"] + ".request.json"))
                response = memory.read(directory / (call["call_id"] + ".response.json"))
                require(request == dict(call, params=plan["params"], lora_request=route), "original readout prompt/token changed")
                bound["formation"].validate_response(request, response, route)
                require(previous_call <= response["started"] <= response["ended"] <= done["monotonic"], "native readout timing differs")
                previous_call = response["ended"]
        inventory[stage] = bound["formation"].tree(directory)
    require(len(set(identities)) == 4 and len(calls) == plan["calls_per_arm"] <= 88 and
            all(manifests[ARMS[0]]["warm_start"][key] == manifests[ARMS[1]]["warm_start"][key] for key in ("source_state", "initialized_state")), "fresh paired identity/workload differs")
    return inventory


def controller(root, plan_sha256, allow_gpu=False):
    entry = time.monotonic()
    require(allow_gpu is True and not os.environ.get("CUDA_VISIBLE_DEVICES"), "Main-only controller with empty CVD required")
    memory = runtime()
    memory.offline()
    root = Path(root).absolute()
    try:
        with memory.budget(entry + SECONDS - time.monotonic()):
            memory, plan, bound = verify(root, plan_sha256, native=True)
            allocation(plan)
            deadline = entry + SECONDS
            memory.write(root / "controller_started.json", dict(plan_sha256=plan_sha256, pid=os.getpid(), monotonic=entry, deadline=deadline, seconds=SECONDS))
            (root / "run").mkdir()
            for stage in STAGES:
                run_stage(memory, plan, plan_sha256, stage, deadline, bound)
            inventory = validate_completed(memory, plan, plan_sha256, bound)
            require(time.monotonic() < deadline, "controller entry budget exceeded")
            memory.write(root / "capture_complete.json", dict(scope=SCOPE, plan_sha256=plan_sha256, stages=inventory, scored=False,
                         **{key: plan["limits"][key] for key in ("fits", "updates", "calls")}, elapsed_seconds=time.monotonic() - entry))
            return dict(status="ADDITIVE_PAIR_COMPLETE_NOT_COLLECTED", completion_sha256=digest(root / "capture_complete.json"))
    except BaseException as error:
        memory.failure(root / "controller_failure.json", error)
        raise


def collect(root, plan_sha256, completion_sha256, out):
    entry, memory = time.monotonic(), runtime()
    memory.offline()
    root = Path(root).absolute()
    with memory.budget(entry + COLLECTION_SECONDS - time.monotonic()):
        memory, plan, bound = verify(root, plan_sha256)
        require(digest(root / "capture_complete.json") == completion_sha256, "completion pin differs")
        complete = memory.read(root / "capture_complete.json")
        require(complete["scope"] == SCOPE and complete["plan_sha256"] == plan_sha256 and complete["scored"] is False and
                complete["stages"] == validate_completed(memory, plan, plan_sha256, bound) and
                all(complete[key] == plan["limits"][key] for key in ("fits", "updates", "calls")) and
                type(complete["elapsed_seconds"]) in (int, float) and 0 <= complete["elapsed_seconds"] <= SECONDS, "completed pair custody differs")
        out = memory.new_external(out, [root, *protected(plan["specification"], bound)])
        memory.write(root.with_name(root.name + ".collection_claim.json"), dict(plan_sha256=plan_sha256, out=str(out), retry=False))
        out.mkdir()
        try:
            cells = {arm: memory.score_calls(plan, bound, arm) for arm in ARMS}
            fits = {arm: memory.read(root / "run" / (arm + "_fit") / "adapter/train_manifest.json") for arm in ARMS}
            training = {arm: {key: value for key, value in memory.read(root / f"training_{arm}.json").items()
                              if key not in ("items", "encoding", "epoch_order", "replay_items", "replay_encoding")} for arm in ARMS}
            scores = dict(scope=SCOPE, claim=CLAIM, seed=plan["specification"]["seed"], parent=plan["parent"], plan_sha256=plan_sha256,
                completion_sha256=completion_sha256, counts=plan["counts"], cells=cells, fits=fits, historical_cells=bound["history"],
                historical_manifests=bound["historical_manifests"], reused_endpoints=plan["reused_endpoints"], source_bindings=plan["specification"],
                input_hashes=plan["input_hashes"], training_costs=training,
                parameter_diagnostics={arm: memory.read(root / "run" / (arm + "_fit") / "fit.json")["norms"] for arm in ARMS},
                screen={arm: bound["old"].screen(plan["specification"]["seed"], cells[arm], bound["history"]["LR0"]) for arm in ARMS},
                best_constant=bound["old"].constant_diagnostic(bound, cells),
                incremental_cost=dict(calls=complete["calls"], fits=complete["fits"], updates=complete["updates"], historical_calls=0,
                                      historical_updates=0, historical_fits=0, new_source_calls=0, teacher_calls=0, controller_seconds=complete["elapsed_seconds"]),
                native_capture_custody_checked=True, automatic_pass=False, scientific_pass=None,
                evaluator_note="Fresh MEMORY_ONLY drift versus old EXTRA_MEMORY needs diagnosis before attributing differences to replay; no automatic adoption.")
            memory.write(out / "scores.json", scores)
            elapsed = time.monotonic() - entry
            require(elapsed <= COLLECTION_SECONDS, "collector entry budget exceeded")
            memory.write(out / "collection.json", dict(scores_sha256=digest(out / "scores.json"), completion_sha256=completion_sha256, collection_seconds=elapsed))
            return dict(status="COLLECTED_ADDITIVE_PAIR", out=str(out), scores_sha256=digest(out / "scores.json"), collection_seconds=elapsed)
        except BaseException as error:
            memory.failure(out / "collection_failure.json", error)
            raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    command = commands.add_parser("prepare")
    for name in ("root", "spec-path", "spec-sha256"):
        command.add_argument("--" + name, required=True)
    command.add_argument("--allow-native", action="store_true")
    for name in ("worker", "controller", "collect"):
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
    command = options.pop("command")
    print(json.dumps({"prepare": prepare, "worker": worker, "controller": controller, "collect": collect}[command](**options), sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
