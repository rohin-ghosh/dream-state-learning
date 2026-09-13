"""Bounded own-source REPLAY versus EXTRA_MEMORY; Main owns native execution."""
from __future__ import annotations

import argparse
import copy
from dataclasses import asdict
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
SCOPE = "astra_own_replay_repair_paired_20260913_v1"
RUNTIME_PIN = "7028fa9a9b277adc6edfec2398d1885d6c55ec33eb67a1bd51ac36b37e02215e"
LOWER_PIN = "80467204aa7ccb4a1cbf4f8d85c7be4e7347263f98f4f7b8fef5739980fcf413"
CAPTURE_PIN = "1142593afb544dec2344c77788f6dbb624f519897b0bb65e135a9e8eb1910107"
CORE_PIN = "9d8777ea3bfdcf92bace3b1a459644b9249dae108db9d5d6a3e35433e0bcff93"
PROTOCOL_PIN = "fb523ee6d96ef6186ae187c3c9b4482b25084fa49f292aae15a34affa87103c7"
TRAINER_PIN = "7bbf165fcb4b8ae3a1180328bcd19f57382c30516daddc95fd61e8a2c749fad7"
ARMS = ("REPLAY", "EXTRA_MEMORY")
STAGES = tuple(arm + suffix for arm in ARMS for suffix in ("_fit", "_readout"))
PANELS = ("exact", "paraphrase", "held", "canary")
SECONDS, COLLECTION_SECONDS, PREPARE_SECONDS = 7200, 180, 180
MEMORY_COUNTS, THRESHOLDS = (14, 8, 8), (8, 7, 5)
PASSES, LR = 8, 3e-5
CLAIM = ("Exploratory own-source observation-reading replay versus extra actual-memory rehearsal at equal steps, "
         "not equal memory exposure or tokens. Original perception parents; no teacher targets or new formation. "
         "Historical LOWER/HIGH/LR0 are noncontemporaneous, zero incremental cost. No fresh confirmation, H1/H2 or automatic promotion.")


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
    require(set(record) == {"path", "sha256"} and Path(record["path"]).is_absolute() and
            type(record["sha256"]) is str and len(record["sha256"]) == 64 and
            (expected is None or record["sha256"] == expected) and digest(record["path"]) == record["sha256"], "file/source pin differs")


def runtime():
    sys.dont_write_bytecode = True
    path = "/tmp/astra_real_record_memory_run_20260913.py"
    pinned(dict(path=path, sha256=RUNTIME_PIN), RUNTIME_PIN)
    spec = importlib.util.spec_from_file_location("own_replay_frozen_memory", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_spec(spec):
    require(set(spec) == {"runner_sha256", "runtime", "lower_runtime", "capture_runtime", "core", "protocol",
                          "memory_history", "lower_history", "capture", "seed", "fit_seed", "gpu_index", "gpu_uuid",
                          "expected_boot_id", "lease_end"}, "closed repair spec differs")
    require(spec["runner_sha256"] == digest(SELF), "runner pin differs")
    require(type(spec["seed"]) is int and spec["seed"] in (0, 1, 2) and type(spec["fit_seed"]) is int and
            spec["fit_seed"] == spec["seed"], "original learner seed required")
    for key, pin in (("runtime", RUNTIME_PIN), ("lower_runtime", LOWER_PIN), ("capture_runtime", CAPTURE_PIN),
                     ("protocol", PROTOCOL_PIN), ("core", CORE_PIN)):
        pinned(spec[key], pin)
    require(type(spec["gpu_index"]) is int and spec["gpu_index"] >= 0 and type(spec["gpu_uuid"]) is str and
            spec["gpu_uuid"].startswith("GPU-"), "explicit Main allocation required")
    require(type(spec["expected_boot_id"]) is str and len(spec["expected_boot_id"]) == 36 and
            type(spec["lease_end"]) in (int, float) and math.isfinite(spec["lease_end"]), "boot/lease binding required")
    for name in ("memory_history", "lower_history", "capture"):
        binding = spec[name]
        last = "report_sha256" if name == "capture" else "scores_sha256"
        require(set(binding) == {"root", "plan_sha256", "completion_sha256", "collection", last} and
                Path(binding["root"]).is_absolute(), "closed upstream binding differs: " + name)
        pinned(binding["collection"])


def allocation(plan):
    spec = plan["specification"]
    require(Path("/proc/sys/kernel/random/boot_id").read_text().strip() == spec["expected_boot_id"], "current boot differs")
    require(spec["lease_end"] > time.time() + SECONDS + COLLECTION_SECONDS + 21600, "six-hour lease finish margin required")


def collected(memory, binding, content_name, content_key):
    root, receipt = Path(binding["root"]), Path(binding["collection"]["path"])
    require(receipt.name == "collection.json" and not (receipt.parent / "collection_failure.json").exists(), "successful collection required")
    require(memory.read(receipt) == {content_key: binding[content_key], "completion_sha256": binding["completion_sha256"]}, "collection join differs")
    require(memory.read(root.with_name(root.name + ".collection_claim.json")) ==
            dict(plan_sha256=binding["plan_sha256"], out=str(receipt.parent), retry=False), "once-only collection claim differs")
    require(digest(receipt.parent / content_name) == binding[content_key], "collected content pin differs")
    return memory.read(receipt.parent / content_name)


def bind(spec, native=False):
    validate_spec(spec)
    memory = runtime()
    lower = memory.load(spec["lower_runtime"], "own_replay_lower", LOWER_PIN)
    capture = memory.load(spec["capture_runtime"], "own_replay_capture", CAPTURE_PIN)
    core = memory.load(spec["core"], "own_replay_mixture", CORE_PIN)
    lower_binding = spec["lower_history"]
    _, lower_plan, bound, historical = lower.verify(lower_binding["root"], lower_binding["plan_sha256"], native=native)
    require(lower_plan["specification"]["history"] == spec["memory_history"] and
            lower_plan["specification"]["seed"] == spec["seed"], "original seed/history differs")
    memory_plan = memory.read(Path(spec["memory_history"]["root"]) / "plan.json")
    require(lower_plan["parent"] == memory_plan["parent"] == bound["parent"], "original recipient differs")
    complete_path = Path(lower_binding["root"]) / "capture_complete.json"
    require(digest(complete_path) == lower_binding["completion_sha256"], "lower completion pin differs")
    complete = memory.read(complete_path)
    require(complete["scope"] == lower.SCOPE and complete["plan_sha256"] == lower_binding["plan_sha256"] and
            complete["scored"] is False and complete["stages"] == lower.validate_completed(memory, lower_plan, lower_binding["plan_sha256"], bound, historical) and
            complete["calls"] == lower_plan["calls_per_arm"] and complete["updates"] == lower_plan["updates_per_arm"] and
            type(complete["elapsed_seconds"]) in (int, float) and 0 <= complete["elapsed_seconds"] <= lower.SECONDS, "lower completion custody differs")
    lower_scores = collected(memory, lower_binding, "scores.json", "scores_sha256")
    require(lower_scores["seed"] == spec["seed"] and lower_scores["parent"] == bound["parent"] and
            lower_scores["plan_sha256"] == lower_binding["plan_sha256"] and lower_scores["completion_sha256"] == lower_binding["completion_sha256"] and
            lower_scores["native_capture_custody_checked"] is True and set(lower_scores["cells"]) == {"WRITE"}, "lower score identity differs")
    calls = memory.read(Path(memory_plan["root"]) / "calls.json")
    lower.validate_cells(lower_scores["cells"]["WRITE"], calls)
    require(lower_scores["cells"]["WRITE"] == memory.score_calls(lower_plan, bound, "WRITE") and
            lower_scores["historical_cells"] == {"HIGH": historical["cells"]["WRITE"], "LR0": historical["cells"]["LR0"]} and
            lower_scores["fits"]["WRITE"] == memory.read(Path(lower_plan["root"]) / "run/WRITE_fit/adapter/train_manifest.json"), "lower raw/manifest joins differ")
    capture_binding = spec["capture"]
    capture_plan, capture_bound = capture.verify(capture_binding["root"], capture_binding["plan_sha256"])
    complete_path = Path(capture_binding["root"]) / "capture_complete.json"
    require(digest(complete_path) == capture_binding["completion_sha256"], "capture completion pin differs")
    complete = memory.read(complete_path)
    require(complete["scope"] == capture.SCOPE and complete["plan_sha256"] == capture_binding["plan_sha256"] and
            complete["stages"] == capture.validate_completed(capture_plan, capture_binding["plan_sha256"], capture_bound) and
            complete["calls"] == 72 and complete["fits"] == complete["updates"] == complete["teacher_calls"] == 0 and
            complete["admitted"] is False and type(complete["elapsed_seconds"]) in (int, float) and
            0 <= complete["elapsed_seconds"] <= capture.CONTROLLER_SECONDS, "capture completion custody differs")
    report_binding = dict(capture_binding, replay_report_sha256=capture_binding["report_sha256"])
    report = collected(memory, report_binding, "replay_report.json", "replay_report_sha256")
    require(report["scope"] == capture.SCOPE and report["plan_sha256"] == capture_binding["plan_sha256"] and
            report["completion_sha256"] == capture_binding["completion_sha256"] and report["native_capture_receipts_checked"] is True,
            "capture report identity differs")
    seed = str(spec["seed"])
    entry = report["seed_reports"][seed]
    require(entry["path"] == f"seed{seed}_admission.json", "seed admission path differs")
    admission_path = Path(capture_binding["collection"]["path"]).parent / entry["path"]
    require(digest(admission_path) == entry["sha256"], "admission report pin differs")
    admission = memory.read(admission_path)
    require(report["counts"][seed] == capture.admission_counts(admission), "admission count join differs")
    raw_joins = []
    audits = {audit["response"]["request_id"]: audit for audit in admission["responses"]}
    prepared_calls = memory.read(Path(capture_plan["root"]) / f"calls_seed{seed}.json")
    require(len(audits) == len(admission["responses"]) == len(prepared_calls) == 24, "all24 response audits required")
    for call in prepared_calls:
        request = call["core_request"]
        directory = Path(capture_plan["root"]) / "run" / f"seed{seed}"
        response_path = directory / (call["call_id"] + ".response.json")
        response = memory.read(response_path)
        raw = dict(request_id=request["request_id"], input_sha256=request["input_sha256"], producer_sha256=request["producer_sha256"],
                   raw=response["text"], finish_reason=response["finish_reason"])
        raw_hash = capture_bound["core"].sha(capture_bound["core"].encoded(raw))
        require(audits[request["request_id"]]["response"] == raw and audits[request["request_id"]]["response_sha256"] == raw_hash,
                "raw child/admission join differs")
        raw_joins.append(dict(request_id=request["request_id"], call_id=call["call_id"],
                             native_request_sha256=digest(directory / (call["call_id"] + ".request.json")),
                             native_response_sha256=digest(response_path), core_response_sha256=raw_hash))
    require(raw_joins == report["native_source_joins"][seed], "native source joins differ")
    for key in ("model", "model_files", "chat_template", "engine", "params"):
        require(capture_plan[key] == memory_plan[key], "capture/recipient inference identity differs: " + key)
    mixture = core.build(memory_plan, bound, capture_plan, report, spec["seed"],
                         protocol_path=spec["protocol"]["path"], capture_runtime_path=spec["capture_runtime"]["path"])
    return dict(bound, lifecycle=memory, lower=lower, repair_core=core, memory_plan=memory_plan, lower_plan=lower_plan,
                capture_plan=capture_plan, capture_report=report, admission_report=admission, mixture=mixture, admission_path=str(admission_path),
                history={"LOWER": lower_scores["cells"]["WRITE"], "HIGH": historical["cells"]["WRITE"], "LR0": historical["cells"]["LR0"]},
                historical_manifests={"LOWER": lower_scores["fits"]["WRITE"], "HIGH": historical["fits"]["WRITE"], "LR0": historical["fits"]["LR0"]})


def dimensions(bound, seed):
    memory_count = len(bound["dataset"]["rows"])
    replay_count = bound["admission_report"]["admitted_count"]
    require(memory_count == MEMORY_COUNTS[seed] and type(replay_count) is int and 0 <= replay_count <= 24, "fixed source counts differ")
    return memory_count, replay_count


def encode(bound, arm, tokenizer, fit_seed):
    return bound["repair_core"].encode(bound["mixture"], arm, tokenizer, bound["trainer"], bound["helper"], bound["probe"], fit_seed)


def configs(bound, seed):
    base = copy.deepcopy(bound["lower_plan"]["configs"]["WRITE"])
    require(base["lr"] == LR and base["epochs"] == PASSES and base["batch_size"] == 1 and base["max_steps"] == 0 and
            base["seed"] == seed and base["rank"] == 8 and base["alpha"] == 16 and base["dropout"] == .05, "fixed fit config differs")
    base["note"] = SCOPE + "; unchanged raw target+EOS; original parent; fresh optimizer; fixed-step content contrast"
    return {arm: asdict(bound["trainer"].TrainConfig(**base)) for arm in ARMS}


def snapshots(spec, bound):
    paths = {f"memory/{name}": Path(bound["memory_plan"]["root"]) / name
             for name in ("dataset.json", "capture.json", "retention.json", "training.json", "calls.json")}
    for key in ("memory_history", "lower_history", "capture"):
        binding = spec[key]
        paths.update({f"{key}/plan.json": Path(binding["root"]) / "plan.json",
                      f"{key}/completion.json": Path(binding["root"]) / "capture_complete.json",
                      f"{key}/collection.json": Path(binding["collection"]["path"])})
        filename = "replay_report.json" if key == "capture" else "scores.json"
        paths[f"{key}/{filename}"] = Path(binding["collection"]["path"]).parent / filename
    paths["capture/admission.json"] = Path(bound["admission_path"])
    for key in ("core", "protocol", "runtime", "lower_runtime", "capture_runtime"):
        paths["sources/" + Path(spec[key]["path"]).name] = Path(spec[key]["path"])
    return paths


def protected(spec, bound):
    return [SELF, *(entry["path"] for key, entry in spec.items() if key in ("core", "protocol", "runtime", "lower_runtime", "capture_runtime")),
            *(spec[key]["root"] for key in ("memory_history", "lower_history", "capture")),
            *(Path(spec[key]["collection"]["path"]).parent for key in ("memory_history", "lower_history", "capture")),
            bound["memory_plan"]["source"], bound["memory_plan"]["model"], bound["parent"]["adapter"]]


def make_plan(root, spec, spec_sha256, bound, inputs, snapshot_hashes):
    memory_count, replay_count = dimensions(bound, spec["seed"])
    original = bound["memory_plan"]
    active = replay_count > 0
    return dict(scope=SCOPE, claim=CLAIM, root=str(Path(root).absolute()), specification=spec, spec_sha256=spec_sha256,
                self_sha256=digest(SELF), **{key: copy.deepcopy(original[key]) for key in
                    ("model", "model_files", "chat_template", "environment", "source", "parent", "engine", "params", "python", "python_sha256")},
                status="READY" if active else "REPLAY_UNAVAILABLE", stages=list(STAGES) if active else [], configs=configs(bound, spec["seed"]),
                input_hashes=inputs, snapshot_hashes=snapshot_hashes, gpu_index=spec["gpu_index"], gpu_uuid=spec["gpu_uuid"],
                counts=dict(memory=memory_count, replay=replay_count, rows_per_arm=memory_count + replay_count),
                updates_per_arm=8 * (memory_count + replay_count) if active else 0,
                calls_per_arm=2 * memory_count + 60 if active else 0,
                limits=dict(controller=SECONDS, collection=COLLECTION_SECONDS, fits=2 if active else 0,
                            updates=16 * (memory_count + replay_count) if active else 0, calls=2 * (2 * memory_count + 60) if active else 0,
                            global_fits=6, global_updates=1632, global_calls=480),
                reused_endpoints={name: dict(noncontemporaneous=True, incremental_calls=0, incremental_updates=0, incremental_fits=0)
                                  for name in ("LOWER", "HIGH", "LR0")})


def prepare(root, spec_path, spec_sha256, allow_native=False):
    require(allow_native is True and not os.environ.get("CUDA_VISIBLE_DEVICES"), "Main-only native CPU prepare with empty CVD required")
    memory = runtime()
    memory.offline()
    with memory.budget(PREPARE_SECONDS):
        require(digest(spec_path) == spec_sha256, "spec pin differs")
        spec = memory.read(spec_path)
        bound = bind(spec, native=True)
        root = memory.new_external(root, [spec_path, *protected(spec, bound)])
        allocation(dict(specification=spec))
        root.mkdir()
        memory.write(root / "prepare_started.json", dict(spec_sha256=spec_sha256, time=time.time()))
        try:
            tokenizer = bound["probe"].native_tokenizer(bound["memory_plan"]["model"])
            require(tokenizer.chat_template == bound["memory_plan"]["chat_template"], "original native template differs")
            calls = memory.build_calls(bound["dataset"], bound["retention"], bound["original_calls"], tokenizer, bound["probe"])
            require(calls == memory.read(Path(bound["memory_plan"]["root"]) / "calls.json"), "original readout prompt/token drift")
            payloads = {"mixture.json": bound["mixture"], "calls.json": calls}
            if dimensions(bound, spec["seed"])[1]:
                payloads.update({f"training_{arm}.json": encode(bound, arm, tokenizer, spec["fit_seed"]) for arm in ARMS})
            inputs = {}
            for name, payload in payloads.items():
                memory.write(root / name, payload)
                inputs[name] = digest(root / name)
            snapshot_hashes = {}
            for name, source in {**snapshots(spec, bound), "spec.json": Path(spec_path)}.items():
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                checksum = digest(source)
                with target.open("xb") as stream:
                    stream.write(source.read_bytes())
                require(digest(target) == checksum, "copied immutable input changed")
                snapshot_hashes[name] = checksum
            plan = make_plan(root, spec, spec_sha256, bound, inputs, snapshot_hashes)
            for arm in ARMS if plan["stages"] else ():
                prepared = payloads[f"training_{arm}.json"]
                require(prepared["rows"] == plan["counts"]["rows_per_arm"] and prepared["updates"] == plan["updates_per_arm"], "mixed encoding workload differs")
                bound["trainer"]._warm_parent(plan["parent"]["adapter"], root / "run" / (arm + "_fit") / "adapter",
                                               bound["trainer"].TrainConfig(**plan["configs"][arm]))
            memory.write(root / "plan.json", plan)
            return dict(status="NATIVE_CPU_PREPARED_NOT_LAUNCHED", plan_sha256=digest(root / "plan.json"),
                        availability=plan["status"], counts=plan["counts"], limits=plan["limits"])
        except BaseException as error:
            memory.failure(root / "prepare_failure.json", error)
            raise


def verify(root, plan_sha256, native=False):
    memory = runtime()
    root = Path(root).absolute()
    require(digest(root / "plan.json") == plan_sha256, "repair plan pin differs")
    plan = memory.read(root / "plan.json")
    spec = plan["specification"]
    bound = bind(spec, native=native)
    snapshot_hashes = {name: digest(path) for name, path in snapshots(spec, bound).items()}
    snapshot_hashes["spec.json"] = plan["spec_sha256"]
    require(plan == make_plan(root, spec, plan["spec_sha256"], bound, plan["input_hashes"], snapshot_hashes), "independent repair plan differs")
    expected_inputs = {"mixture.json", "calls.json"} | ({f"training_{arm}.json" for arm in ARMS} if plan["stages"] else set())
    require(set(plan["input_hashes"]) == expected_inputs and plan["python"] == os.path.abspath(sys.executable) and
            plan["python_sha256"] == digest(sys.executable), "prepared inventory/interpreter differs")
    require(not (root / "prepare_failure.json").exists() and memory.read(root / "prepare_started.json")["spec_sha256"] == plan["spec_sha256"] and
            memory.read(root / "spec.json") == spec, "preparation differs")
    for name, checksum in {**snapshot_hashes, **plan["input_hashes"]}.items():
        require(digest(root / name) == checksum, "prepared immutable input differs: " + name)
    require(memory.read(root / "mixture.json") == bound["mixture"] and memory.read(root / "calls.json") ==
            memory.read(Path(bound["memory_plan"]["root"]) / "calls.json"), "source/readout binding differs")
    return memory, plan, bound


def check_fit(manifest, prepared, config, parent, arm, counts):
    require(arm in ARMS, "fresh repair arm required")
    count, updates = prepared["rows"], prepared["updates"]
    require(type(count) is int and count == counts["memory"] + counts["replay"] and
            1 <= counts["replay"] <= 24 and counts["memory"] in MEMORY_COUNTS and
            type(updates) is int and updates == PASSES * count <= 304 and manifest["config"] == config and manifest["empty"] is False,
            "fit config/count differs")
    require(config["lr"] == LR and config["epochs"] == PASSES and config["batch_size"] == 1 and config["max_steps"] == 0 and
            config["rank"] == 8 and config["alpha"] == 16 and config["dropout"] == .05, "fixed fit recipe differs")
    require(all(type(manifest[key]) is int for key in ("steps", "micro_batches", "epochs_run", "nonfinite_batches")) and
            manifest["steps"] == manifest["micro_batches"] == updates and manifest["epochs_run"] == PASSES and
            manifest["nonfinite_batches"] == 0, "fit steps/nonfinite accounting differs")
    require(manifest["corpus"]["n_items"] == manifest["corpus"]["n_encoded"] == count and manifest["corpus"]["n_skipped_no_target"] == 0, "fit skipped records")
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
            warm["parent_unchanged"] is True and warm["initialized_loaded_state_check"] is True and warm["base_frozen"] is True and
            warm["adapter_count"] == 1 and warm["trainer_sha256"] == TRAINER_PIN and warm["phase_seed"] == config["seed"] and
            warm["phase_steps"] == updates and warm["parent_cumulative_steps"] == 320 and warm["cumulative_steps"] == 320 + updates,
            "warm-start custody differs")
    require(warm["initialized_state"] and set(warm["initialized_state"]) == set(warm["final_state"]) and
            warm["trainable_names"] and all("lora_A" in name or "lora_B" in name for name in warm["trainable_names"]), "LoRA tensor coverage differs")
    require(warm["initialized_state"] != warm["final_state"], "fresh arm made no actual parameter change")


def fit_arm(memory, plan, bound, arm):
    require(arm in ARMS and plan["stages"], "unavailable/unknown fit forbidden")
    started = time.monotonic()
    directory = Path(plan["root"]) / "run" / (arm + "_fit")
    tokenizer, base = bound["reflection"].load_native_model(plan["model"])
    require(not hasattr(base, "peft_config") and tokenizer.chat_template == plan["chat_template"], "fresh base/tokenizer required")
    prepared_path = Path(plan["root"]) / f"training_{arm}.json"
    prepared = memory.read(prepared_path)
    require(prepared == encode(bound, arm, tokenizer, plan["specification"]["fit_seed"]), "actual mixed encoding differs")
    adapter = directory / "adapter"
    require(not adapter.exists(), "fresh fit destination required")
    trainer = bound["trainer"]
    trainer.run_training(prepared["items"], tokenizer, base, trainer.TrainConfig(**plan["configs"][arm]), str(adapter),
                         corpus_sha=plan["input_hashes"][prepared_path.name], corpus_name=SCOPE + ":" + arm,
                         init_adapter=plan["parent"]["adapter"])
    manifest = memory.read(adapter / "train_manifest.json")
    require(manifest["corpus"]["sha256"] == plan["input_hashes"][prepared_path.name], "fit corpus pin differs")
    check_fit(manifest, prepared, plan["configs"][arm], plan["parent"], arm, plan["counts"])
    for historical in bound["historical_manifests"].values():
        require(all(manifest["warm_start"][key] == historical["warm_start"][key] for key in ("source_state", "initialized_state")), "original warm tensors differ")
    norms = memory.tensor_diagnostics(trainer, plan["parent"], adapter, manifest)
    require(norms["changed_elements"] > 0 and norms["l2"]["delta"] > 0, "fresh arm parameter delta absent")
    files = bound["helper"].check_adapter(adapter, plan["configs"][arm])
    require(bound["formation"].tree(plan["parent"]["adapter"]) == plan["parent"]["adapter_files"], "original parent changed")
    memory.write(directory / "fit.json", dict(arm=arm, adapter=str(adapter), adapter_files=files, updates=prepared["updates"], calls=0,
                 initialized_from=plan["parent"], training_sha256=plan["input_hashes"][prepared_path.name], norms=norms,
                 elapsed_seconds=time.monotonic() - started))


def worker(root, plan_sha256, stage, allow_gpu=False):
    require(allow_gpu is True and stage in STAGES, "explicit fresh arm worker required")
    memory = runtime()
    memory.offline()
    directory = Path(root) / "run" / stage
    try:
        memory, plan, bound = verify(root, plan_sha256, native=True)
        require(stage in plan["stages"] and os.environ.get("CUDA_VISIBLE_DEVICES") == plan["gpu_uuid"] and
                os.getpid() == os.getpgrp(), "worker stage/allocation/isolation differs")
        allocation(plan)
        memory.write(directory / "started.json", dict(pid=os.getpid(), pgid=os.getpgrp(), stage=stage, plan_sha256=plan_sha256, time=time.time()))
        arm, kind = stage.rsplit("_", 1)
        if kind == "fit":
            fit_arm(memory, plan, bound, arm)
        else:
            memory.capture_readout(plan, bound, arm)
    except BaseException as error:
        memory.failure(directory / "failure.json", error)
        raise


def run_stage(memory, plan, plan_sha256, stage, deadline, bound):
    require(stage in plan["stages"] and stage in STAGES, "unavailable/unknown stage forbidden")
    probe = bound["probe"]
    allocation(plan)
    require(deadline - time.monotonic() > memory.GPU_QUERY_SECONDS + memory.CLEANUP_SECONDS and probe.gpu_state(plan) is True,
            "fresh GPU vacancy/budget check failed")
    directory = Path(plan["root"]) / "run" / stage
    directory.mkdir()
    process, expected = None, None
    try:
        with (directory / "stdout.log").open("xb") as output, (directory / "stderr.log").open("xb") as errors:
            command = [plan["python"], "-B", str(SELF), "worker", "--root", plan["root"], "--plan-sha256", plan_sha256,
                       "--stage", stage, "--allow-gpu"]
            launched = time.time()
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=output, stderr=errors,
                                       env=dict(os.environ, CUDA_VISIBLE_DEVICES=plan["gpu_uuid"]), start_new_session=True)
            expected = memory.identity(process.pid)
            require(expected["pgid"] == process.pid, "worker process group differs")
            memory.write(directory / "launch.json", dict(identity=expected, stage=stage, plan_sha256=plan_sha256, command=command, time=launched))
            require(process.wait(timeout=max(.01, deadline - time.monotonic() - memory.CLEANUP_SECONDS)) == 0, "repair worker failed")
    except BaseException as error:
        memory.failure(directory / "stage_failure.json", error)
        raise
    finally:
        if process is not None:
            try:
                require(expected is not None, "missing owned process identity")
                memory.cleanup_owned(process, expected, probe)
                require(probe.gpu_state(plan) is True, "assigned GPU not empty after owned release")
                memory.write(directory / "released.json", dict(identity=expected, stage=stage, time=time.time()))
            except BaseException as error:
                memory.failure(directory / "cleanup_failure.json", error)
                raise


def validate_completed(memory, plan, plan_sha256, bound):
    root = Path(plan["root"])
    require(not (root / "controller_failure.json").exists(), "failed controller")
    require({path.name for path in (root / "run").iterdir()} == set(plan["stages"]), "fresh stage inventory differs")
    calls = memory.read(root / "calls.json")
    inventory, identities, manifests = {}, [], {}
    previous_release = 0
    for stage in plan["stages"]:
        directory = root / "run" / stage
        require(not any((directory / name).exists() for name in ("failure.json", "stage_failure.json", "cleanup_failure.json")), "failed fresh stage")
        launch, started, released = (memory.read(directory / name) for name in ("launch.json", "started.json", "released.json"))
        identity = launch["identity"]
        command = [plan["python"], "-B", str(SELF), "worker", "--root", plan["root"], "--plan-sha256", plan_sha256,
                   "--stage", stage, "--allow-gpu"]
        require(identity == released["identity"] and identity["pid"] == identity["pgid"] == started["pid"] == started["pgid"] and
                type(identity["start_ticks"]) is int and identity["start_ticks"] > 0 and launch["command"] == command and
                launch["stage"] == started["stage"] == released["stage"] == stage and
                launch["plan_sha256"] == started["plan_sha256"] == plan_sha256 and
                previous_release <= launch["time"] <= started["time"] <= released["time"], "fresh process custody/chronology differs")
        previous_release = released["time"]
        identities.append(identity["pid"])
        arm, kind = stage.rsplit("_", 1)
        route = memory.route_for(plan, bound, arm)
        if kind == "fit":
            prepared = memory.read(root / f"training_{arm}.json")
            fit = memory.read(directory / "fit.json")
            manifest = memory.read(directory / "adapter/train_manifest.json")
            check_fit(manifest, prepared, plan["configs"][arm], plan["parent"], arm, plan["counts"])
            require(fit["updates"] == prepared["updates"] == plan["updates_per_arm"] and fit["calls"] == 0 and
                    fit["training_sha256"] == manifest["corpus"]["sha256"] == plan["input_hashes"][f"training_{arm}.json"], "fit receipt differs")
            bound["helper"].check_adapter(directory / "adapter", plan["configs"][arm])
            for historical in bound["historical_manifests"].values():
                require(all(manifest["warm_start"][key] == historical["warm_start"][key] for key in ("source_state", "initialized_state")), "historical warm state differs")
            require(fit["norms"]["changed_elements"] > 0 and fit["norms"]["l2"]["delta"] > 0, "fresh tensor delta absent")
            manifests[arm] = manifest
        else:
            require(memory.read(directory / "identity.json") == dict(arm=arm, route=route, model_files=plan["model_files"],
                    parent=plan["parent"], params=plan["params"]), "cold readout identity differs")
            require(memory.read(directory / "readout.json") == dict(arm=arm, calls=len(calls), updates=0), "cold call count differs")
            for suffix in (".request.json", ".response.json"):
                require({path.name for path in directory.glob("*" + suffix)} == {call["call_id"] + suffix for call in calls}, "cold call inventory differs")
            for call in calls:
                request = memory.read(directory / (call["call_id"] + ".request.json"))
                response = memory.read(directory / (call["call_id"] + ".response.json"))
                require(request == dict(call, params=plan["params"], lora_request=route), "original readout prompt changed")
                bound["formation"].validate_response(request, response, route)
        inventory[stage] = bound["formation"].tree(directory)
    require(len(set(identities)) == len(plan["stages"]), "cold process reused")
    if manifests:
        require(len(calls) == plan["calls_per_arm"] <= 88 and plan["updates_per_arm"] <= 304 and
                all(manifests[ARMS[0]]["warm_start"][key] == manifests[ARMS[1]]["warm_start"][key]
                    for key in ("source_state", "initialized_state")), "paired warm state/workload differs")
    else:
        require(plan["status"] == "REPLAY_UNAVAILABLE" and plan["counts"]["replay"] == 0 and
                plan["calls_per_arm"] == plan["updates_per_arm"] == 0, "unavailable workload differs")
    return inventory


def controller(root, plan_sha256, allow_gpu=False):
    require(allow_gpu is True and not os.environ.get("CUDA_VISIBLE_DEVICES"), "Main-only controller with empty CVD required")
    memory = runtime()
    memory.offline()
    root = Path(root).absolute()
    try:
        with memory.budget(SECONDS):
            deadline = time.monotonic() + SECONDS
            memory, plan, bound = verify(root, plan_sha256, native=True)
            allocation(plan)
            memory.write(root / "controller_started.json", dict(plan_sha256=plan_sha256, pid=os.getpid(), time=time.time(), seconds=SECONDS))
            (root / "run").mkdir()
            for stage in plan["stages"]:
                run_stage(memory, plan, plan_sha256, stage, deadline, bound)
            inventory = validate_completed(memory, plan, plan_sha256, bound)
            require(time.monotonic() < deadline, "controller budget exceeded")
            memory.write(root / "capture_complete.json", dict(scope=SCOPE, status=plan["status"], plan_sha256=plan_sha256,
                         stages=inventory, fits=plan["limits"]["fits"], calls=plan["limits"]["calls"], updates=plan["limits"]["updates"],
                         scored=False, elapsed_seconds=SECONDS - (deadline - time.monotonic())))
            return dict(status=plan["status"] + "_COMPLETE_NOT_SCORED", completion_sha256=digest(root / "capture_complete.json"))
    except BaseException as error:
        memory.failure(root / "controller_failure.json", error)
        raise


def screen(seed, cells, historical):
    regressions = {}
    for panel in ("held", "canary"):
        old = {row["row_id"]: row["score"]["passed"] for row in historical[panel]}
        new = {row["row_id"]: row["score"]["passed"] for row in cells[panel]}
        require(set(old) == set(new) and all(type(value) is bool for value in [*old.values(), *new.values()]), "screen row/type join differs")
        regressions[panel] = sorted(key for key in old if old[key] and not new[key])
    exact = sum(row["score"]["score"]["production_eligible"] for row in cells["exact"])
    return dict(exact_eligible=exact, exact_denominator=MEMORY_COUNTS[seed], threshold=THRESHOLDS[seed],
                lr0_correct_regressions=regressions, passed=exact >= THRESHOLDS[seed] and not any(regressions.values()),
                exploratory=True, execution_gate=False, scientific_pass=None)


def constant_diagnostic(bound, cells):
    rows = bound["dataset"]["rows"]
    candidates = {row["target_sha256"]: row["raw_target"] for row in rows}
    variants = {}
    for variant, key in (("exact", "input_messages"), ("paraphrase", "paraphrase_input_messages")):
        alternatives = []
        for checksum, raw in sorted(candidates.items()):
            scores = [bound["memory"].score_readback(bound["capture"], row["row_id"], raw, "stop",
                       input_messages=row[key], variant=variant, **bound["kwargs"]) for row in rows]
            alternatives.append(dict(target_sha256=checksum, content_correct=sum(score["score"]["content_correct"] for score in scores),
                                     production_eligible=sum(score["score"]["production_eligible"] for score in scores)))
        best = max(item["content_correct"] for item in alternatives)
        variants[variant] = dict(denominator=len(rows), candidates=alternatives, oracle_best_content_correct=best,
                                tied_best_target_sha256=[item["target_sha256"] for item in alternatives if item["content_correct"] == best],
                                actual_content_correct={arm: sum(row["score"]["score"]["content_correct"] for row in panels[variant])
                                                        for arm, panels in cells.items()})
    return dict(variants=variants, candidate_set="each distinct exact raw target in original admitted memory rows",
                scope="Evaluator-only same-panel oracle constant, assumed stop; not native execution, causal proof or a new training source.")


def collect(root, plan_sha256, completion_sha256, out):
    memory = runtime()
    memory.offline()
    root = Path(root).absolute()
    with memory.budget(COLLECTION_SECONDS):
        memory, plan, bound = verify(root, plan_sha256)
        require(digest(root / "capture_complete.json") == completion_sha256, "completion pin differs")
        complete = memory.read(root / "capture_complete.json")
        require(complete["scope"] == SCOPE and complete["status"] == plan["status"] and complete["plan_sha256"] == plan_sha256 and
                complete["stages"] == validate_completed(memory, plan, plan_sha256, bound) and complete["scored"] is False and
                all(complete[key] == plan["limits"][key] for key in ("calls", "updates", "fits")) and
                type(complete["elapsed_seconds"]) in (int, float) and 0 <= complete["elapsed_seconds"] <= SECONDS, "completion custody differs")
        out = memory.new_external(out, [root, *protected(plan["specification"], bound)])
        memory.write(root.with_name(root.name + ".collection_claim.json"), dict(plan_sha256=plan_sha256, out=str(out), retry=False))
        out.mkdir()
        try:
            cells = {arm: memory.score_calls(plan, bound, arm) for arm in ARMS} if plan["stages"] else {}
            fits = {arm: memory.read(root / "run" / (arm + "_fit") / "adapter/train_manifest.json") for arm in cells}
            training = {arm: {key: value for key, value in memory.read(root / f"training_{arm}.json").items()
                             if key not in ("items", "encoding", "epoch_order")} for arm in cells}
            scores = dict(scope=SCOPE, claim=CLAIM, status=plan["status"], seed=plan["specification"]["seed"], parent=plan["parent"],
                          plan_sha256=plan_sha256, completion_sha256=completion_sha256, counts=plan["counts"], cells=cells,
                          source_bindings={key: plan["specification"][key] for key in ("core", "protocol", "capture")},
                          input_hashes=plan["input_hashes"],
                          historical_cells=bound["history"], historical_manifests=bound["historical_manifests"],
                          historical_bindings={key: plan["specification"][key] for key in ("memory_history", "lower_history")},
                          reused_endpoints=plan["reused_endpoints"], fits=fits, training_costs=training,
                          parameter_diagnostics={arm: memory.read(root / "run" / (arm + "_fit") / "fit.json")["norms"] for arm in cells},
                          screen={arm: screen(plan["specification"]["seed"], panel, bound["history"]["LR0"]) for arm, panel in cells.items()},
                          incremental_cost=dict(calls=complete["calls"], updates=complete["updates"], fits=complete["fits"],
                                                historical_calls=0, historical_updates=0, new_source_calls=0, teacher_calls=0,
                                                controller_seconds=complete["elapsed_seconds"]),
                          native_capture_custody_checked=True, automatic_pass=False, scientific_pass=None,
                          best_constant=constant_diagnostic(bound, cells) if cells else None,
                          evaluator_note="Independent reducer owns additional comparisons; best-constant uses original memory raw targets only after scoring. No winner selection.")
            memory.write(out / "scores.json", scores)
            memory.write(out / "collection.json", dict(scores_sha256=digest(out / "scores.json"), completion_sha256=completion_sha256))
            return dict(status="COLLECTED_" + plan["status"], out=str(out), scores_sha256=digest(out / "scores.json"))
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
    result = {"prepare": prepare, "worker": worker, "controller": controller, "collect": collect}[name](**options)
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
