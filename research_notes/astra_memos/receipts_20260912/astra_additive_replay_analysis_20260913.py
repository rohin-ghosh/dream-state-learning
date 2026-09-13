"""Prospective local additive cohort reduction; no native lifecycle or models."""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import json
import math
from pathlib import Path


SELF = Path(__file__).resolve()
SCHEMA = "astra_additive_replay_analysis_20260913_v1"
INPUT_SCHEMA = SCHEMA + "_inputs"
SCOPE = "astra_additive_replay_pair_20260913_v1"
ARMS = ("ADDITIVE", "MEMORY_ONLY")
STAGES = tuple(arm + suffix for arm in ARMS for suffix in ("_fit", "_readout"))
HISTORY = ("LOWER", "HIGH", "LR0", "REPLAY", "EXTRA_MEMORY")
PANELS = ("exact", "paraphrase", "held", "canary")
COUNTS, FLOORS = (14, 8, 8), (8, 7, 5)
PROTOCOL_PIN = "724d5a6e1aea7dca4b0ae42aec6e2fd0252b98646f7c903432927263f2c391e9"
FROZEN_TRAINER_PIN = "7bbf165fcb4b8ae3a1180328bcd19f57382c30516daddc95fd61e8a2c749fad7"
PINS = {
    "legacy": ("astra_own_replay_repair_analysis_20260913_orderfix.py", "4c06d8ded8ab58814a94f0aab40780a54fa2cf76ca0c7d858d1ab639483b03ab"),
    "runner": ("astra_additive_replay_run_20260913.py", "ca54e7e1971d89224bb8dec8f3518d0a6a73ec4d1abe6f29278bab335b1618a5"),
    "core": ("astra_additive_replay_core_20260913.py", "b58e4c90e2abdd26648475c9fb1fe92e3bc3fef2fa7664ecaaa69fc93591076a"),
    "trainer": ("astra_additive_replay_train_20260913.py", "3f2e73ef69b12c8db211e1d3043e4559713e036ffe09571ab8bc4c5199a426a0"),
    "launcher": ("astra_additive_replay_main_20260913.py", "1ed1b383f2a36855f53e7b165dc9d75fe99620e930a3ae89332fcbe22c7ce05c"),
}
TINY_PIN = "ff2346a72f7e4fed9f4cdb51c90bb701c736557add56f0462f2b1e7ef2bc0b7d"
LAUNCHER_FILES = {"precheck.json", "stdout.log", "launched.json", "holder_started.json", "controller.json",
                  "controller_exit.json", "collection_started.json", "collector.json", "collector_exit.json", "exit.json"}
DEFAULT_PROTOCOL = "/data/home/rohing/dream-state/research_notes/astra_memos/ASTRA_ADDITIVE_REPLAY_DEV_2026-09-13.md"
LEGACY_PROTOCOL = "/data/home/rohing/dream-state/research_notes/astra_memos/ASTRA_OWN_SOURCE_REPLAY_REPAIR_2026-09-13.md"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def equal(left, right, message):
    require(canonical(left) == canonical(right), message)


def digest(path):
    checksum = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            checksum.update(block)
    return checksum.hexdigest()


def decode(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "duplicate JSON key")
            result[key] = value
        return result
    def invalid(value):
        raise ValueError("nonfinite JSON: " + value)
    result = json.loads(raw, object_pairs_hook=unique, parse_constant=invalid)
    canonical(result)
    return result


def read(path):
    return decode(Path(path).read_bytes())


def count(value, expected=None):
    require(type(value) is int and value >= 0 and (expected is None or value == expected), "strict integer count differs (not bool)")
    return value


def number(value, ceiling=None):
    require(type(value) in (int, float) and math.isfinite(value) and value >= 0 and
            (ceiling is None or value <= ceiling), "finite nonnegative measurement/budget required")
    return value


def pin(path, checksum):
    path = Path(path)
    require(path.is_absolute() and path.is_file() and not any(item.is_symlink() for item in (path, *path.parents)), "regular absolute nonsymlink local input required")
    require(type(checksum) is str and len(checksum) == 64 and digest(path) == checksum, "file-byte pin differs: " + path.name)
    return path


def local(root, name):
    relative = Path(name)
    require(not relative.is_absolute() and ".." not in relative.parts and str(relative) not in (".", ""), "unsafe relative mirror path")
    result = Path(root) / relative
    require(result.resolve().is_relative_to(Path(root).resolve()), "mirror escape")
    return result


def load_apis(module_dir="/tmp", source_root="/tmp/astra_level1_real_record_source_20260913_attempt1",
              protocol_path=DEFAULT_PROTOCOL, legacy_protocol_path=LEGACY_PROTOCOL):
    from types import ModuleType
    pin(protocol_path, PROTOCOL_PIN)
    pin(Path(module_dir) / PINS["launcher"][0], PINS["launcher"][1])
    path = pin(Path(module_dir) / PINS["legacy"][0], PINS["legacy"][1])
    legacy = ModuleType("additive_frozen_local_reducer")
    legacy.__file__ = str(path)
    exec(compile(path.read_bytes(), str(path), "exec"), legacy.__dict__)
    apis = legacy.load_apis(module_dir, source_root, legacy_protocol_path)
    apis["legacy"] = legacy
    for name in ("core", "trainer"):
        apis["additive_" + name] = legacy.load_module(Path(module_dir) / PINS[name][0], PINS[name][1])
    apis["check"] = legacy.extract(Path(module_dir) / PINS["runner"][0], PINS["runner"][1], {"check_fit", "expected_costs"},
        dict(require=require, math=math, ARMS=ARMS, TRAINER_PIN=PINS["trainer"][1], FROZEN_TRAINER_PIN=FROZEN_TRAINER_PIN,
             PROTOCOL_PIN=PROTOCOL_PIN))["check_fit"]
    return apis


def load_bundle(entry):
    require(set(entry) == {"seed", "root", "plan_sha256", "completion_sha256", "scores", "collection", "collection_claim", "launcher"}, "closed seed entry differs")
    seed = count(entry["seed"])
    require(seed in (0, 1, 2) and Path(entry["root"]).is_absolute(), "original seed/local root required")
    root = Path(entry["root"])
    require(not any((root / name).exists() for name in ("prepare_failure.json", "controller_failure.json")), "failed native attempt")
    plan = read(pin(root / "plan.json", entry["plan_sha256"]))
    complete = read(pin(root / "capture_complete.json", entry["completion_sha256"]))
    reports = {}
    for name in ("scores", "collection", "collection_claim"):
        binding = entry[name]
        require(type(binding) is dict and set(binding) == {"path", "sha256"}, "closed local report binding required")
        reports[name] = read(pin(binding["path"], binding["sha256"]))
    out = Path(entry["scores"]["path"]).parent
    require(out == Path(entry["collection"]["path"]).parent and not (out / "collection_failure.json").exists(), "collection directory/failure differs")
    collection = reports["collection"]
    require(set(collection) == {"scores_sha256", "completion_sha256", "collection_seconds"}, "collection receipt schema differs")
    equal([collection["scores_sha256"], collection["completion_sha256"]], [entry["scores"]["sha256"], entry["completion_sha256"]], "collection hash join differs")
    number(collection["collection_seconds"], 180)
    claim = reports["collection_claim"]
    require(set(claim) == {"plan_sha256", "out", "retry"} and claim["plan_sha256"] == entry["plan_sha256"] and
            claim["retry"] is False and Path(claim["out"]).is_absolute(), "once-only claim differs")
    equal(sorted(complete["stages"]), sorted(STAGES), "complete four-stage inventory required")
    require({path.name for path in (root / "run").iterdir()} == set(STAGES), "extra/missing stage directory")
    files, hashes, journals = {}, {}, {}
    for mapping in (plan["input_hashes"], plan["snapshot_hashes"]):
        for name, checksum in mapping.items():
            require(name not in hashes, "overlapping input/snapshot namespace")
            path = pin(local(root, name), checksum)
            hashes[name] = checksum
            if name.endswith(".json"):
                files[name] = read(path)
    for stage, inventory in complete["stages"].items():
        directory = root / "run" / stage
        actual = {str(path.relative_to(directory)) for path in directory.rglob("*") if path.is_file()}
        equal(sorted(actual), sorted(inventory), "stage file inventory differs")
        require(not any("failure" in name.lower() for name in actual), "failed stage receipt")
        for name, checksum in inventory.items():
            relative = "run/" + stage + "/" + name
            path = pin(local(root, relative), checksum)
            hashes[relative] = checksum
            if name.endswith(".json"):
                files[relative] = read(path)
            elif name.endswith("steps.jsonl"):
                journals[stage] = [decode(line) for line in path.read_bytes().splitlines()]
            elif name == "adapter/DONE":
                require(path.read_bytes() == b"ok\n", "successful adapter marker differs")
    receipts = {name: read(root / (name + ".json")) for name in ("prepare_started", "prepare_done", "controller_started")}
    binding = entry["launcher"]
    require(type(binding) is dict and set(binding) == {"root", "files"} and Path(binding["root"]).is_absolute(), "closed local launcher binding required")
    launcher_root = Path(binding["root"])
    require(type(binding["files"]) is dict and set(binding["files"]) in (LAUNCHER_FILES, LAUNCHER_FILES | {"failure.json"}),
            "complete terminal launcher inventory required; holder failure is not transport failure")
    equal(sorted(path.name for path in launcher_root.iterdir()), sorted(binding["files"]), "extra/missing launcher receipts")
    launcher = {}
    for name, checksum in binding["files"].items():
        path = pin(local(launcher_root, name), checksum)
        if name.endswith(".json"):
            launcher[name] = read(path)
    return dict(entry=copy.deepcopy(entry), plan=plan, complete=complete, report=reports["scores"], collection=collection, claim=claim,
                files=files, hashes=hashes, journals=journals, receipts=receipts, launcher=launcher)


def validate_launcher(bundle):
    entry, plan, receipts = bundle["entry"], bundle["plan"], bundle["launcher"]
    equal(sorted(receipts), sorted(set(entry["launcher"]["files"]) - {"stdout.log"}), "launcher JSON inventory differs")
    launch, holder = receipts["launched.json"], receipts["holder_started.json"]
    precheck, controller, collector = (receipts[name] for name in ("precheck.json", "controller.json", "collector.json"))
    require(launch["status"] == "LAUNCHED_NOT_RESULT" and launch["automatic_once_collection"] is True, "single automatic collector required")
    equal([launch["seed"], launch["gpu_index"], precheck["gpu_index"]], [entry["seed"]] * 3, "launcher seed/allocation differs")
    equal([launch["root"], launch["gpu_uuid"], precheck["gpu_uuid"]], [plan["root"], plan["gpu_uuid"], plan["gpu_uuid"]], "launcher root/UUID differs")
    equal([precheck["reservations"], precheck["unresolved"]], [[], []], "prelaunch reservation check failed")
    for record in (launch, holder):
        equal([record["plan_sha256"], record["runner_sha256"], record["custodian_sha256"]],
              [entry["plan_sha256"], PINS["runner"][1], PINS["launcher"][1]], "launcher plan/code join differs")
    equal(launch["tiny_cpu_receipt"], holder["tiny_cpu_receipt"], "tiny CPU receipt identity differs")
    tiny = holder["tiny_cpu_receipt"]
    require(tiny["sha256"] == TINY_PIN and tiny["trainer_sha256"] == PINS["trainer"][1] and
            tiny["fixture_only"] is True and tiny["native_scientific_evidence"] is False and Path(tiny["path"]).is_absolute(), "tiny CPU gate differs")
    identity = launch["identity"]
    require(set(identity) == {"pid", "comm", "ppid", "start_ticks", "uid", "cmdline_sha256"}, "holder native identity schema differs")
    holder_pid = count(holder["pid"])
    require(holder_pid > 1 and count(identity["start_ticks"]) > 0, "holder identity required")
    count(launch["pid"], holder_pid)
    count(identity["pid"], holder_pid)
    count(identity["ppid"])
    count(identity["uid"])
    require(type(identity["cmdline_sha256"]) is str and len(identity["cmdline_sha256"]) == 64 and
            all(char in "0123456789abcdef" for char in identity["cmdline_sha256"]), "holder command byte digest required")
    runner_path, launcher_path = "/tmp/" + PINS["runner"][0], "/tmp/" + PINS["launcher"][0]
    equal(launch["command"], [plan["python"], "-B", launcher_path, "hold", "--seed", str(entry["seed"]),
          "--runner-sha256", PINS["runner"][1], "--tiny-cpu-receipt", tiny["path"]], "single holder command differs")
    equal(controller["command"], [plan["python"], "-B", runner_path, "controller", "--root", plan["root"],
          "--plan-sha256", entry["plan_sha256"], "--allow-gpu"], "single controller command differs")
    equal(collector["command"], [plan["python"], "-B", runner_path, "collect", "--root", plan["root"],
          "--plan-sha256", entry["plan_sha256"], "--completion-sha256", entry["completion_sha256"],
          "--out", plan["root"] + "_collected"], "single collector command differs")
    count(controller["pid"], bundle["receipts"]["controller_started"]["pid"])
    for record in (controller, collector):
        require(count(record["pid"]) > 1, "controller/collector PID required")
        count(record["pgid"], record["pid"])
    require(len({holder_pid, controller["pid"], collector["pid"]}) == 3, "conflicting holder/controller/collector identity")
    for name in ("controller_exit.json", "collector_exit.json", "exit.json"):
        count(receipts[name]["returncode"], 0)
    collection_start = receipts["collection_started.json"]
    equal([collection_start["completion_sha256"], collection_start["plan_sha256"], bundle["claim"]["out"]],
          [entry["completion_sha256"], entry["plan_sha256"], plan["root"] + "_collected"], "once collection/completion join differs")
    times = [number(precheck["time"]), number(holder["started_unix"]), number(controller["started_unix"]),
             number(receipts["controller_exit.json"]["completed_unix"]), number(collection_start["started_unix"]),
             number(collector["started_unix"]), number(receipts["collector_exit.json"]["completed_unix"]), number(receipts["exit.json"]["completed_unix"])]
    require(times == sorted(times), "holder/controller/collector chronology differs")
    launched_at = number(launch["started_unix"])
    require(times[0] <= launched_at <= times[-1], "launch receipt chronology differs")
    for stage in STAGES:
        for name in ("launch.json", "started.json", "released.json"):
            wall = number(bundle["files"]["run/" + stage + "/" + name]["time"])
            require(times[1] <= wall <= times[3], "stage outside holder/controller wall span")
    anomaly = receipts.get("failure.json")
    if anomaly is not None:
        require(set(anomaly) == {"error", "holder_may_be_running"} and type(anomaly["error"]) is str and
                anomaly["error"] and anomaly["holder_may_be_running"] is True, "unreconciled pre-spawn launcher failure")
    return dict(terminal_controller_rc=0, terminal_collector_rc=0, holder_written_terminal_rc=0,
        launcher_failure=copy.deepcopy(anomaly), launcher_failure_sha256=entry["launcher"]["files"].get("failure.json"),
        launcher_failure_classification="post_spawn_launcher_error_with_terminal_success" if anomaly is not None else "none_recorded",
        terminal_chain_consistent=True, single_launch_receipts_consistent=True, holder_identity=identity,
        controller_pid=controller["pid"], collector_pid=collector["pid"], receipt_hashes=entry["launcher"]["files"],
        holder_launch_through_collection_seconds=times[-1] - min(launched_at, times[1]),
        limitations="Pinned exclusive-write launcher and one local receipt chain support no retry within this root; not proof of no other root/launch. "
                    "CVD policy is source-validated (holder UUID, children empty), not independently sampled environment evidence. "
                    "Holder exit.json is written before return, not an OS wait/reap receipt; live process absence is not established. "
                    "Unrecorded SSH timeout is not recoverable from this chain; preserve Main's separate transport log.")


def validate_sources(bundle, apis):
    plan, files, hashes, report = (bundle[key] for key in ("plan", "files", "hashes", "report"))
    seed = plan["specification"]["seed"]
    core, trainer, legacy = apis["additive_core"], apis["additive_trainer"], apis["legacy"]
    material, paired, prior = files["material.json"], files["paired.json"], files["repair/plan.json"]
    core.validate_material(material)
    equal(material["repair_plan_sha256"], hashes["repair/plan.json"], "paired source plan pin differs")
    equal(material["parent"], plan["parent"], "original material recipient differs")
    equal(material["mixture"], files["repair/mixture.json"], "unchanged original source bank differs")
    require(material["seed"] == seed and material["counts"]["memory"] == COUNTS[seed] and material["counts"]["replay"] == 24, "fixed original source population differs")
    binding = plan["specification"]["repair_history"]
    for filename, key in (("plan.json", "plan_sha256"), ("capture_complete.json", "completion_sha256"), ("scores.json", "scores_sha256")):
        equal(hashes["repair/" + filename], binding[key], "historical repair snapshot binding differs")
    equal(hashes["repair/collection.json"], binding["collection"]["sha256"], "historical collection file pin differs")
    equal(files["repair/collection.json"], dict(scores_sha256=binding["scores_sha256"], completion_sha256=binding["completion_sha256"]), "historical once-collection join differs")
    equal(files["repair/spec.json"], prior["specification"], "original repair spec differs")
    require(prior["self_sha256"] == apis["legacy"].PINS["runner"][1] and prior["specification"]["seed"] == seed, "original repair code/seed differs")
    old_files = {name.removeprefix("upstream/"): value for name, value in files.items() if name.startswith("upstream/")}
    for name, checksum in prior["snapshot_hashes"].items():
        if name != "spec.json":
            equal(hashes["upstream/" + name], checksum, "frozen upstream snapshot changed")
    legacy.validate_snapshot_joins(prior, old_files, seed, apis["core"])
    legacy.validate_replay_sources(material["mixture"], old_files["capture/admission.json"], prior, apis)
    original = old_files["memory_history/plan.json"]
    equal([plan["parent"], prior["parent"]], [original["parent"]] * 2, "original recipient changed to descendant")
    parent = plan["parent"]
    equal(parent["plan_sha256"], apis["observation"].PLAN_PINS[seed], "original perception plan pin differs")
    equal(parent["adapter_files"]["adapter_model.safetensors"], apis["observation"].WEIGHT_PINS[seed], "original perception weights differ")
    require(parent["adapter"] == f"/localhome/local-rohing/astra_diagnostics/level1_perception_seed{seed}_20260913_attempt1/run/fit/adapter", "original perception adapter path differs")
    for key in ("model", "model_files", "environment", "chat_template", "engine", "params", "python", "python_sha256", "source"):
        equal(plan[key], original[key], "frozen model/source/config differs: " + key)
    old_training = {arm: files[f"repair/training_{arm}.json"] for arm in ("EXTRA_MEMORY", "REPLAY")}
    for arm, training in old_training.items():
        equal(hashes[f"repair/training_{arm}.json"], prior["input_hashes"][f"training_{arm}.json"], "actual original training byte pin differs")
        equal(training, material["saved_training"][arm], "original training object differs")
        legacy.validate_training(training, material["mixture"], arm, apis["core"])
    expected_pair = trainer.prepare_pair(old_training["EXTRA_MEMORY"], old_training["REPLAY"], seed=seed,
        source_pins=dict(extra_memory_sha256=hashes["repair/training_EXTRA_MEMORY.json"], replay_sha256=hashes["repair/training_REPLAY.json"]))
    equal(paired, expected_pair, "trainer pair differs from actual original file bytes")
    equal(paired["pairs"], material["pairs"], "fixed extra occurrence pairing differs")
    for arm in ARMS:
        equal(files[f"training_{arm}.json"], core.prepared_from_saved(material, arm), "full memory occurrence/order/accounting changed")
        equal(plan["configs"][arm], prior["configs"]["EXTRA_MEMORY"], "original complete fit config differs")
    dataset, capture, retention, calls = (old_files[name] for name in ("memory/dataset.json", "memory/capture.json", "memory/retention.json", "memory/calls.json"))
    equal(dataset["rows"], material["mixture"]["memory_rows"], "actual TRY record source changed")
    equal(files["calls.json"], calls, "original native readout prefixes changed")
    equal(files["repair/calls.json"], calls, "historical readout prefixes changed")
    legacy.validate_calls(calls, dataset, retention)
    prior_scores = files["repair/scores.json"]
    require(prior_scores["plan_sha256"] == binding["plan_sha256"] and prior_scores["completion_sha256"] == binding["completion_sha256"] and
            prior_scores["native_capture_custody_checked"] is True and prior_scores["parent"] == parent, "historical report identity differs")
    histories = dict(LOWER=old_files["lower_history/scores.json"]["cells"]["WRITE"], HIGH=old_files["memory_history/scores.json"]["cells"]["WRITE"],
                     LR0=old_files["memory_history/scores.json"]["cells"]["LR0"], **prior_scores["cells"])
    equal(sorted(histories), sorted(HISTORY), "historical endpoint inventory differs")
    equal(report["historical_cells"], histories, "imported historical cells changed")
    equal(prior_scores["historical_cells"], {key: histories[key] for key in ("LOWER", "HIGH", "LR0")}, "historical chain changed")
    manifests = dict(LOWER=old_files["lower_history/scores.json"]["fits"]["WRITE"], HIGH=old_files["memory_history/scores.json"]["fits"]["WRITE"],
                     LR0=old_files["memory_history/scores.json"]["fits"]["LR0"], **prior_scores["fits"])
    equal(report["historical_manifests"], manifests, "historical fit manifests changed")
    for arm in ("REPLAY", "EXTRA_MEMORY"):
        apis["pure"]["check_fit"](manifests[arm], old_training[arm], prior["configs"][arm], parent, arm, prior["counts"])
    return dict(dataset=dataset, capture=capture, retention=retention, calls=calls, histories=histories, historical_manifests=manifests, paired=paired)


def validate_custody(bundle, apis, source, scorer):
    entry, plan, report, complete, files, hashes = (bundle[key] for key in ("entry", "plan", "report", "complete", "files", "hashes"))
    receipts, seed = bundle["receipts"], entry["seed"]
    require(receipts["prepare_started"]["spec_sha256"] == plan["spec_sha256"] and receipts["prepare_done"]["plan_sha256"] == entry["plan_sha256"], "prepare receipt join differs")
    number(receipts["prepare_done"]["elapsed_seconds"], 180)
    controller = receipts["controller_started"]
    begin, deadline = number(controller["monotonic"]), number(controller["deadline"])
    require(controller["plan_sha256"] == entry["plan_sha256"] and controller["seconds"] == 7200 and deadline == begin + 7200, "controller entry/deadline differs")
    elapsed = number(complete["elapsed_seconds"], 7200)
    previous, identities, costs, manifests = begin, [], {}, {}
    calls, utilities = source["calls"], apis["utilities"]
    for stage in STAGES:
        prefix = "run/" + stage + "/"
        launch, started, done, exited, released = (files[prefix + name] for name in
            ("launch.json", "started.json", "worker_done.json", "exit.json", "released.json"))
        identity = launch["identity"]
        require(set(identity) == {"pid", "pgid", "start_ticks"}, "process identity schema differs")
        require(count(identity["pid"]) > 1 and count(identity["start_ticks"]) > 0, "owned process identity required")
        count(identity["pgid"], identity["pid"])
        equal(identity, exited["identity"], "exit identity differs")
        equal(identity, released["identity"], "release identity differs")
        count(started["pid"], identity["pid"])
        count(started["pgid"], identity["pgid"])
        count(exited["returncode"], 0)
        require(released["group_absent"] is True and released["gpu_vacant"] is True, "owned release receipt required")
        equal([item["stage"] for item in (launch, started, done, released)], [stage] * 4, "stage identity differs")
        equal([item["plan_sha256"] for item in (launch, started, done)], [entry["plan_sha256"]] * 3, "stage plan differs")
        command = launch["command"]
        require(len(command) == 11 and Path(command[2]).is_absolute() and Path(command[2]).name == PINS["runner"][0], "new runner process command differs")
        equal(command, [plan["python"], "-B", command[2], "worker", "--root", plan["root"], "--plan-sha256", entry["plan_sha256"], "--stage", stage, "--allow-gpu"], "fresh process route command differs")
        times = [previous] + [number(item["monotonic"]) for item in (launch, started, done, exited, released)] + [deadline]
        require(times == sorted(times) and released["monotonic"] - begin <= elapsed, "cold process/controller chronology differs")
        wall_times = [number(item["time"]) for item in (launch, started, released)]
        require(wall_times == sorted(wall_times), "wall chronology differs")
        previous = released["monotonic"]
        identities.append((identity["pid"], identity["start_ticks"]))
        arm, kind = stage.rsplit("_", 1)
        fit_prefix = "run/" + arm + "_fit/"
        fit = files[fit_prefix + "fit.json"]
        adapter = plan["root"] + "/run/" + arm + "_fit/adapter"
        equal([fit["arm"], fit["adapter"], fit["initialized_from"]], [arm, adapter, plan["parent"]], "new adapter route/original parent differs")
        inventory = complete["stages"][arm + "_fit"]
        equal(fit["adapter_files"], {name.removeprefix("adapter/"): checksum for name, checksum in inventory.items() if name.startswith("adapter/")}, "saved adapter inventory differs")
        if kind == "fit":
            prepared, manifest = files[f"training_{arm}.json"], files[prefix + "adapter/train_manifest.json"]
            apis["check"](manifest, prepared, plan["configs"][arm], plan["parent"], arm, plan["counts"], source["paired"])
            equal(bundle["journals"][stage], manifest["component_losses"], "per-step loss journal differs")
            equal(manifest, report["fits"][arm], "reported fit manifest differs")
            equal(fit["training_sha256"], manifest["corpus"]["sha256"], "fit training hash differs")
            equal(fit["training_sha256"], plan["input_hashes"][f"training_{arm}.json"], "fit source/encoding pin differs")
            count(fit["updates"], 8 * (COUNTS[seed] + 24))
            count(fit["calls"], 0)
            warm = manifest["warm_start"]
            for key in ("source_state", "initialized_state", "final_state"):
                utilities.inventory(warm[key])
            for old in source["historical_manifests"].values():
                for key in ("source_state", "initialized_state"):
                    equal(warm[key], old["warm_start"][key], "original warm tensors differ")
            equal(warm["optimizer_defaults"], source["historical_manifests"]["EXTRA_MEMORY"]["warm_start"]["optimizer_defaults"], "original optimizer defaults differ")
            config = files[prefix + "adapter/adapter_config.json"]
            require(config["r"] == 8 and config["lora_alpha"] == 16 and config["lora_dropout"] == .05 and config.get("bias") == "none" and
                    not config.get("use_dora") and not config.get("use_rslora") and not config.get("modules_to_save"), "one original LoRA structure required")
            equal(sorted(config["target_modules"]), sorted(plan["configs"][arm]["target_modules"]), "LoRA target modules differ")
            require("adapter/DONE" in inventory and sum(name in inventory for name in ("adapter/adapter_model.safetensors", "adapter/adapter_model.bin")) == 1, "final adapter missing")
            norms = fit["norms"]
            require(count(norms["changed_elements"]) > 0 and number(norms["l2"]["delta"]) > 0, "finite nonzero adapter update required")
            for value in norms["l2"].values():
                number(value)
            equal(norms, report["parameter_diagnostics"][arm], "norm receipt differs")
            times = {key: number(manifest[key]) for key in ("train_seconds", "wall_seconds")}
            times["fit_receipt_seconds"] = number(fit["elapsed_seconds"])
            times["process_seconds"] = done["monotonic"] - started["monotonic"]
            require(max(times["train_seconds"], times["wall_seconds"], times["fit_receipt_seconds"]) <= times["process_seconds"] + .01, "fit timing outside owned process")
            for value in manifest["component_seconds"].values():
                number(value)
            peak = manifest["peak_cuda_memory_allocated_bytes"]
            if peak is not None:
                count(peak)
            costs[arm] = dict(fits=1, updates=manifest["steps"], tokens=copy.deepcopy(manifest["costs"]), timings=times,
                component_seconds=manifest["component_seconds"], timing_scope=manifest["timing_scope"],
                peak_cuda_memory_allocated_bytes=peak, peak_memory_scope=manifest["peak_memory_scope"])
            manifests[arm] = manifest
        else:
            route = dict(name="real_record_memory_" + arm.lower(), id=1, path=adapter)
            equal(files[prefix + "identity.json"], dict(arm=arm, route=route, model_files=plan["model_files"], parent=plan["parent"], params=plan["params"]), "cold readout identity differs")
            equal(files[prefix + "readout.json"], dict(arm=arm, calls=len(calls), updates=0), "readout denominator differs")
            for suffix in (".request.json", ".response.json"):
                equal(sorted(name for name in complete["stages"][stage] if name.endswith(suffix)), sorted(call["call_id"] + suffix for call in calls), "readout raw inventory differs")
            by_id = {(panel, row["row_id"]): row for panel, rows in report["cells"][arm].items() for row in rows}
            prior_call, prompt_tokens, output_tokens, generation = started["monotonic"], 0, 0, 0.
            for call in calls:
                request_path, response_path = prefix + call["call_id"] + ".request.json", prefix + call["call_id"] + ".response.json"
                request, response = files[request_path], files[response_path]
                equal(request, dict(call, params=plan["params"], lora_request=route), "unchanged readout prompt/token/route differs")
                apis["response"](request, response, route)
                require(prior_call <= number(response["started"]) <= number(response["ended"]) <= done["monotonic"], "native call timing differs")
                prior_call = response["ended"]
                row = by_id[(call["panel"], call["row_id"])]
                equal([row["raw"], row["finish_reason"], row["response_sha256"]], [response["text"], response["finish_reason"], hashes[response_path]], "raw response/source hash join differs")
                cost = dict(prompt_tokens=len(response["actual_prompt_token_ids"]), output_tokens=len(response["output_token_ids"]), generation_seconds=response["ended"]-response["started"])
                equal(row["cost"], cost, "native call cost differs")
                prompt_tokens += cost["prompt_tokens"]
                output_tokens += cost["output_tokens"]
                generation += cost["generation_seconds"]
            costs[arm].update(calls=len(calls), readout=dict(prompt_tokens=prompt_tokens, output_tokens=output_tokens, generation_seconds=generation,
                              process_seconds=done["monotonic"]-started["monotonic"]))
    require(len(set(identities)) == 4, "cold process reused")
    return costs


def item_changes(first, second, panel, metric, utilities):
    paired = utilities.pair(first, second, panel, metric)
    paired["items"] = [dict(row_id=row_id, first=utilities.metric(first[row_id], panel, metric),
                             second=utilities.metric(second[row_id], panel, metric)) for row_id in sorted(first)]
    return paired


def reduce_seed(bundle, apis):
    entry, plan, report, complete, files = (bundle[key] for key in ("entry", "plan", "report", "complete", "files"))
    seed = count(entry["seed"])
    require(seed in (0, 1, 2), "original seed required")
    equal([plan["specification"]["seed"], plan["specification"]["fit_seed"], report["seed"]], [seed]*3, "cohort seed differs")
    require(plan["scope"] == report["scope"] == complete["scope"] == SCOPE, "additive scope differs")
    require(plan["self_sha256"] == plan["specification"]["runner_sha256"] == PINS["runner"][1], "frozen runner differs")
    for name in ("core", "trainer"):
        equal(plan["specification"][name]["sha256"], PINS[name][1], "frozen source differs")
    equal(plan["specification"]["protocol"]["sha256"], PROTOCOL_PIN, "protocol differs")
    equal(report["source_bindings"], plan["specification"], "source spec differs")
    equal(files["spec.json"], plan["specification"], "copied spec differs")
    equal(bundle["hashes"]["spec.json"], plan["spec_sha256"], "copied spec hash differs")
    for name in ("core", "trainer", "protocol", "repair_runtime"):
        binding = plan["specification"][name]
        equal(bundle["hashes"]["sources/" + Path(binding["path"]).name], binding["sha256"], "copied code/protocol pin differs")
    equal(sorted(plan["input_hashes"]), sorted(["material.json", "paired.json", "calls.json", *[f"training_{arm}.json" for arm in ARMS]]), "closed prepared input inventory differs")
    equal(report["input_hashes"], plan["input_hashes"], "source input pins differ")
    equal([report["plan_sha256"], complete["plan_sha256"], report["completion_sha256"]], [entry["plan_sha256"]]*2+[entry["completion_sha256"]], "report/completion join differs")
    equal(report["parent"], plan["parent"], "reported parent differs")
    require(report["native_capture_custody_checked"] is True and report["automatic_pass"] is False and report["scientific_pass"] is None and
            complete["scored"] is False, "custody/no-promotion flags differ")
    equal(sorted(report["cells"]), sorted(ARMS), "fresh pair missing/extra")
    equal(plan["stages"], list(STAGES), "fixed stage order differs")
    equal(sorted(complete["stages"]), sorted(STAGES), "complete stage inventory differs")
    equal(report["counts"], dict(memory=COUNTS[seed], replay=24, rows_per_arm=COUNTS[seed]+24), "source denominator differs")
    equal(plan["counts"], report["counts"], "plan denominator differs")
    updates, calls = 8*(COUNTS[seed]+24), 2*COUNTS[seed]+60
    count(plan["updates_per_arm"], updates)
    count(plan["calls_per_arm"], calls)
    for key, expected in (("fits", 2), ("updates", 2*updates), ("calls", 2*calls)):
        count(complete[key], expected)
        count(plan["limits"][key], expected)
    for key, expected in (("controller", 7200), ("prepare", 180), ("collection", 180), ("global_fits", 6), ("global_updates", 1632), ("global_calls", 480),
                          ("aggregate_allocation_hours", 8), ("new_source_calls", 0), ("teacher_calls", 0)):
        count(plan["limits"][key], expected)
    launcher = validate_launcher(bundle)
    source = validate_sources(bundle, apis)
    legacy, utilities = apis["legacy"], apis["utilities"]
    scorer = legacy.FrozenScorer(source["capture"], source["dataset"], source["retention"], apis)
    endpoints = dict(source["histories"], **report["cells"])
    indices = {name: legacy.rescore_cells(cells, source["calls"], scorer, seed, utilities) for name, cells in endpoints.items()}
    totals = {name: legacy.summarize_cells(cells, utilities) for name, cells in endpoints.items()}
    costs = validate_custody(bundle, apis, source, scorer)
    screens = {arm: legacy.screen(seed, indices[arm], indices["LR0"], utilities) for arm in ARMS}
    equal(report["screen"], screens, "unchanged noncompensatory screen differs")
    equal(report["best_constant"], legacy.constants(source["dataset"], source["calls"], scorer, report["cells"], utilities), "constant baseline recomputation differs")
    contrasts = {}
    for first, second in (("ADDITIVE", "MEMORY_ONLY"), ("ADDITIVE", "LR0"), ("MEMORY_ONLY", "LR0"), ("MEMORY_ONLY", "EXTRA_MEMORY"), ("ADDITIVE", "EXTRA_MEMORY")):
        panels = {}
        for panel in PANELS:
            metrics = utilities.MEMORY_METRICS if panel in ("exact", "paraphrase") else utilities.RETENTION_METRICS
            panels[panel] = {metric: item_changes(indices[first][panel], indices[second][panel], panel, metric, utilities) for metric in metrics}
        contrasts[first + "_vs_" + second] = dict(first=first, second=second, noncontemporaneous=second in HISTORY, panels=panels)
    restored = {}
    for arm in ARMS:
        restored[arm] = {}
        for panel in ("held", "canary"):
            rows = []
            for row_id in sorted(indices["LR0"][panel]):
                values = {name: utilities.metric(indices[name][panel][row_id], panel, "passed") for name in (arm, "LR0", "EXTRA_MEMORY")}
                rows.append(dict(row_id=row_id, lr0_correct=values["LR0"], old_extra_correct=values["EXTRA_MEMORY"], current_correct=values[arm],
                    restored_old_extra_loss=values["LR0"] and not values["EXTRA_MEMORY"] and values[arm],
                    missing_lr0_correct=values["LR0"] and not values[arm]))
            restored[arm][panel] = rows
    raw_drift = {panel: sorted(row_id for row_id in indices["MEMORY_ONLY"][panel] if
                 (indices["MEMORY_ONLY"][panel][row_id]["raw"], indices["MEMORY_ONLY"][panel][row_id]["finish_reason"]) !=
                 (indices["EXTRA_MEMORY"][panel][row_id]["raw"], indices["EXTRA_MEMORY"][panel][row_id]["finish_reason"])) for panel in PANELS}
    for name in HISTORY:
        equal(report["reused_endpoints"][name], dict(noncontemporaneous=True, incremental_fits=0, incremental_updates=0, incremental_calls=0), "historical reuse label/cost differs")
    equal(report["incremental_cost"], dict(calls=2*calls, fits=2, updates=2*updates, historical_calls=0, historical_updates=0, historical_fits=0,
          new_source_calls=0, teacher_calls=0, controller_seconds=complete["elapsed_seconds"]), "incremental costs differ")
    for arm in ARMS:
        training = files[f"training_{arm}.json"]
        equal(report["training_costs"][arm], {key: value for key, value in training.items() if key not in
              ("items", "encoding", "epoch_order", "replay_items", "replay_encoding")}, "reported token/dose accounting differs")
    return dict(seed=seed, parent=plan["parent"], evidence=entry, denominators=dict(exact=COUNTS[seed], paraphrase=COUNTS[seed], held=48, canary=12,
                original_possible_records=16), totals=totals, screens=screens, contrasts=contrasts, lr0_restoration=restored,
        historical_extra_memory_check=dict(noncontemporaneous=True, exact_memory_items_and_order=True, raw_changed_ids=raw_drift,
            any_raw_drift=any(raw_drift.values()), interpretation="Behavior differences require diagnosis before attribution; not an execution gate or automatic failure."),
        costs=costs, spans=dict(prepare_seconds=bundle["receipts"]["prepare_done"]["elapsed_seconds"], controller_seconds=complete["elapsed_seconds"],
            collection_seconds=bundle["collection"]["collection_seconds"], holder_launch_through_collection_seconds=launcher["holder_launch_through_collection_seconds"],
            limitation="Controller contains worker/model/fit/readout/cleanup spans; do not sum nested spans or call elapsed time GPU-active time."),
        launcher=launcher,
        losses={arm: {key: report["fits"][arm][key] for key in ("mean_loss_per_epoch", "final_loss", "component_losses", "executed_order")} for arm in ARMS},
        parameter_diagnostics=report["parameter_diagnostics"], historical_manifest_diagnostics={name: {key: source["historical_manifests"][name].get(key)
            for key in ("steps", "final_loss", "mean_loss_per_epoch", "train_tokens_seen", "train_seconds", "wall_seconds")} for name in HISTORY},
        memory_source_presentations=files["training_MEMORY_ONLY.json"]["memory_source_presentations"], constants=report["best_constant"],
        reused_endpoints=report["reused_endpoints"], custody=dict(new_stage_raw_and_hashes_audited=True, historical_raw_rescored=True,
            historical_native_generation_replayed=False, current_native_gpu_identity_verified=False, numerical_norms_recomputed=False),
        interpretation="Matched complete memory occurrence schedule, not compute/RNG/gradient parity. Historical controls reused. No automatic promotion.")


def reduce_cohort(bundles, apis):
    require(type(bundles) is list and len(bundles) == 3, "all three roots required")
    seeds = [count(bundle["entry"]["seed"]) for bundle in bundles]
    equal(sorted(seeds), [0, 1, 2], "unique original seeds0/1/2 required")
    results = [reduce_seed(bundle, apis) for bundle in sorted(bundles, key=lambda bundle: bundle["entry"]["seed"])]
    aggregate = dict(fits=sum(cost["fits"] for result in results for cost in result["costs"].values()),
        updates=sum(cost["updates"] for result in results for cost in result["costs"].values()),
        calls=sum(cost["calls"] for result in results for cost in result["costs"].values()),
        historical_incremental_calls=0, historical_incremental_updates=0, historical_incremental_fits=0, teacher_calls=0, new_source_calls=0)
    equal([aggregate["fits"], aggregate["updates"], aggregate["calls"]], [6, 1632, 480], "fixed full cohort cost differs")
    aggregate["executed_training"] = {arm: {key: sum(result["costs"][arm]["tokens"][key] for result in results) for key in
        ("updates", "memory_forwards", "replay_forwards", "total_forwards", "memory_total_tokens", "replay_total_tokens", "total_tokens", "supervised_tokens", "context_tokens")} for arm in ARMS}
    aggregate["holder_wall_hours"] = sum(result["spans"]["holder_launch_through_collection_seconds"] for result in results) / 3600
    aggregate["prepare_plus_holder_wall_hours"] = aggregate["holder_wall_hours"] + sum(result["spans"]["prepare_seconds"] for result in results) / 3600
    require(aggregate["prepare_plus_holder_wall_hours"] <= 8, "aggregate allocation ceiling exceeded")
    return dict(schema=SCHEMA, protocol_sha256=PROTOCOL_PIN, reducer_sha256=digest(SELF), code_pins=PINS, seeds=results,
        screen_by_seed={str(result["seed"]): result["screens"] for result in results}, costs=aggregate,
        all_seed_screen={arm: all(result["screens"][arm]["passed"] for result in results) for arm in ARMS},
        automatic_promotion=False, scientific_pass=None, fit_authorized=False,
        limitations=["Prospective reducer of a single-write development contrast; no parenting, repeated-cycle, H1/H2 or clean-lineage qualification.",
            "Complete memory occurrence parity does not establish equal compute, RNG consumption or gradients along different trajectories.",
            "Historical LOWER/HIGH/LR0/REPLAY/EXTRA_MEMORY are noncontemporaneous, with zero incremental cost.",
            "Per-item LR0-correct losses cannot be offset by gains; exact recall floors remain8/7/5.",
            "Scalar/serialized tensor receipts audited without Torch; current live GPU identity and kernel timings are not verified.",
            "Preparation plus holder spans are logged elapsed accounting, not independently metered GPU reservation time; inter-stage idle gaps before the holder are unmeasured."])


def markdown(report):
    lines = ["# Additive replay cohort — descriptive only", "", "| Seed | Arm | Exact eligible | Paraphrase content | Held | Canary | Screen |",
             "|---|---|---:|---:|---:|---:|---|"]
    for result in report["seeds"]:
        for arm in ARMS:
            total = result["totals"][arm]
            lines.append(f"| {result['seed']} | {arm} | {total['exact']['totals']['production_eligible']}/{result['denominators']['exact']} | "
                         f"{total['paraphrase']['totals']['content_correct']}/{result['denominators']['paraphrase']} | "
                         f"{total['held']['totals']['passed']}/48 | {total['canary']['totals']['passed']}/12 | {result['screens'][arm]['passed']} |")
    lines.extend(["", "6 fresh fits,1632optimizer steps,480readout calls. Historical controls incur zero incremental cost.",
                  "Full per-item contrasts, losses, costs, native receipts, constants and failures are in analysis.json.",
                  "No automatic promotion; full memory occurrence parity is not compute/RNG parity."])
    for result in report["seeds"]:
        anomaly = result["launcher"]["launcher_failure"]
        lines.append(f"Seed {result['seed']} launcher anomaly: {canonical(anomaly)}; terminal controller/collector and holder-written rc0 checked.")
    lines.append("Receipt chain supports one launch within each root, not independent live absence; preserve any separate SSH transport logs.")
    return "\n".join(lines) + "\n"


def run(manifest_path, manifest_sha256, out, *, module_dir="/tmp", source_root="/tmp/astra_level1_real_record_source_20260913_attempt1",
        protocol_path=DEFAULT_PROTOCOL, legacy_protocol_path=LEGACY_PROTOCOL):
    manifest = read(pin(manifest_path, manifest_sha256))
    require(set(manifest) == {"schema", "seeds"} and manifest["schema"] == INPUT_SCHEMA, "closed cohort manifest differs")
    out = Path(out).absolute()
    require(not out.exists() and not any(path.is_symlink() for path in (out, *out.parents)), "fresh nonsymlink analysis output required")
    protected = [Path(manifest_path).resolve(), Path(module_dir).resolve(), Path(source_root).resolve(), Path(protocol_path).resolve(), Path(legacy_protocol_path).resolve()]
    protected += [Path(entry["root"]).resolve() for entry in manifest["seeds"]]
    protected += [Path(entry["launcher"]["root"]).resolve() for entry in manifest["seeds"]]
    protected += [Path(entry[name]["path"]).resolve().parent for entry in manifest["seeds"] for name in ("scores", "collection", "collection_claim")]
    require(all(out != path and out not in path.parents for path in protected), "output would contain protected inputs")
    require(all(not out.is_relative_to(Path(entry["root"]).resolve()) for entry in manifest["seeds"]), "output nested in source mirror")
    require(all(not out.is_relative_to(Path(entry["launcher"]["root"]).resolve()) for entry in manifest["seeds"]), "output nested in launcher evidence")
    apis = load_apis(module_dir, source_root, protocol_path, legacy_protocol_path)
    report = reduce_cohort([load_bundle(entry) for entry in manifest["seeds"]], apis)
    report["manifest_sha256"] = manifest_sha256
    out.mkdir(parents=True, exist_ok=False)
    with (out / "analysis.json").open("xb") as output:
        output.write((canonical(report) + "\n").encode())
    with (out / "analysis.md").open("x") as output:
        output.write(markdown(report))
    return dict(out=str(out), analysis_sha256=digest(out / "analysis.json"), markdown_sha256=digest(out / "analysis.md"))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("manifest", "manifest-sha256", "out"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--module-dir", default="/tmp")
    parser.add_argument("--source-root", default="/tmp/astra_level1_real_record_source_20260913_attempt1")
    parser.add_argument("--protocol-path", default=DEFAULT_PROTOCOL)
    parser.add_argument("--legacy-protocol-path", default=LEGACY_PROTOCOL)
    args = vars(parser.parse_args(argv))
    args["manifest_path"] = args.pop("manifest")
    print(canonical(run(**args)))


if __name__ == "__main__":
    main()
