"""Local additive reduction with an explicit collection-only recovery branch."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path


FROZEN_REDUCER = "/tmp/astra_additive_replay_analysis_20260913.py"
FROZEN_REDUCER_SHA256 = "df38efd210929ec21523d19daa8b65f98d50fef435b3fa23b719929bca6dc472"
RUNNER = "/tmp/astra_additive_replay_run_20260913.py"
RUNNER_SHA256 = "ca54e7e1971d89224bb8dec8f3518d0a6a73ec4d1abe6f29278bab335b1618a5"
LAUNCHER = "/tmp/astra_additive_replay_main_20260913.py"
LAUNCHER_SHA256 = "1ed1b383f2a36855f53e7b165dc9d75fe99620e930a3ae89332fcbe22c7ce05c"
TRAINER_SHA256 = "3f2e73ef69b12c8db211e1d3043e4559713e036ffe09571ab8bc4c5199a426a0"
TINY_SHA256 = "ff2346a72f7e4fed9f4cdb51c90bb701c736557add56f0462f2b1e7ef2bc0b7d"
EXPECTED_ERROR = "'dict' object has no attribute 'score_row'"
STAGES = tuple(arm + suffix for arm in ("ADDITIVE", "MEMORY_ONLY") for suffix in ("_fit", "_readout"))
LAUNCHER_JSON = {"precheck.json", "launched.json", "holder_started.json", "controller.json", "controller_exit.json",
                 "collection_started.json", "collector.json", "collector_exit.json", "exit.json"}
REPAIR = "/tmp/astra_additive_replay_collection_repair_20260913.py"
REPAIR_SHA256 = "9b67256c42b7f7c18e79a10f9bc6201140833e8d6c339a7e192ca18de67c854a"
RECOVERY_SCHEMA = "astra_additive_replay_collection_repair1_v1"
SCHEMA = "astra_additive_replay_recovered_analysis_20260913_v1"
INPUT_SCHEMA = SCHEMA + "_inputs"
BASE_ENTRY_KEYS = {"seed", "root", "plan_sha256", "completion_sha256", "scores", "collection", "collection_claim", "launcher"}
RECOVERY_KEYS = {"original_failure", "recovery", "recovery_claim"}
ARMS, PANELS = ("ADDITIVE", "MEMORY_ONLY"), ("exact", "paraphrase", "held", "canary")
HISTORY, COUNTS = ("LOWER", "HIGH", "LR0", "REPLAY", "EXTRA_MEMORY"), (14, 8, 8)
SOURCE_ROOT = "/tmp/astra_level1_real_record_source_20260913_attempt1"
PROTOCOL = "/data/home/rohing/dream-state/research_notes/astra_memos/ASTRA_ADDITIVE_REPLAY_DEV_2026-09-13.md"
LEGACY_PROTOCOL = "/data/home/rohing/dream-state/research_notes/astra_memos/ASTRA_OWN_SOURCE_REPLAY_REPAIR_2026-09-13.md"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def equal(left, right, message):
    require(json.dumps(left, sort_keys=True, allow_nan=False) == json.dumps(right, sort_keys=True, allow_nan=False), message)


def integer(value, expected=None):
    require(type(value) is int and value >= 0 and (expected is None or value == expected), "strict integer required; bool is not a returncode")
    return value


def seconds(value):
    require(type(value) in (int, float) and math.isfinite(value) and value >= 0, "finite nonnegative time required")
    return value


def digest(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def decode(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "duplicate JSON key")
            result[key] = value
        return result

    def invalid(value):
        raise ValueError("nonfinite JSON constant: " + value)

    return json.loads(raw, object_pairs_hook=unique, parse_constant=invalid)


def read_binding(binding):
    require(type(binding) is dict and set(binding) == {"path", "sha256"}, "explicit local file-byte binding required")
    path = Path(binding["path"])
    require(path.is_absolute() and path.is_file() and not any(part.is_symlink() for part in (path, *path.parents)), "regular absolute nonsymlink local file required")
    require(digest(path) == binding["sha256"], "file-byte pin differs")
    raw = path.read_bytes()
    return dict(binding=dict(binding), record=decode(raw), raw_utf8=raw.decode("utf-8"))


def verify_frozen_sources():
    pins = {FROZEN_REDUCER: FROZEN_REDUCER_SHA256, RUNNER: RUNNER_SHA256, LAUNCHER: LAUNCHER_SHA256, REPAIR: REPAIR_SHA256}
    for path, expected in pins.items():
        require(digest(path) == expected, "frozen source changed: " + path)
    return pins


def audit_original_attempt(bundle, failure_record):
    entry, plan, receipts = bundle["entry"], bundle["plan"], bundle["launcher"]
    require(set(receipts) in (LAUNCHER_JSON, LAUNCHER_JSON | {"failure.json"}), "complete original terminal chain required")
    equal(sorted(receipts), sorted(set(entry["launcher"]["files"]) - {"stdout.log"}), "original launcher inventory differs")
    require(set(failure_record) == {"error_type", "error", "retry", "time"} and failure_record["error_type"] == "AttributeError" and
            failure_record["error"] == EXPECTED_ERROR and failure_record["retry"] is False, "only declared scorer-binding failure is recoverable here")
    launch, holder = receipts["launched.json"], receipts["holder_started.json"]
    precheck, controller, collector = (receipts[name] for name in ("precheck.json", "controller.json", "collector.json"))
    require(launch["status"] == "LAUNCHED_NOT_RESULT" and launch["automatic_once_collection"] is True, "original automatic collection required")
    seed = integer(entry["seed"])
    require(seed in (0, 1, 2), "original seed required")
    equal([launch["seed"], launch["gpu_index"], precheck["gpu_index"]], [seed] * 3, "original allocation differs")
    equal([launch["root"], launch["gpu_uuid"], precheck["gpu_uuid"]], [plan["root"], plan["gpu_uuid"], plan["gpu_uuid"]], "original root/UUID differs")
    equal([precheck["reservations"], precheck["unresolved"]], [[], []], "prelaunch reservation failure")
    for record in (launch, holder):
        equal([record["plan_sha256"], record["runner_sha256"], record["custodian_sha256"]],
              [entry["plan_sha256"], RUNNER_SHA256, LAUNCHER_SHA256], "original source/plan pin differs")
    equal(launch["tiny_cpu_receipt"], holder["tiny_cpu_receipt"], "tiny fixture receipt differs")
    tiny = holder["tiny_cpu_receipt"]
    require(tiny["sha256"] == TINY_SHA256 and tiny["trainer_sha256"] == TRAINER_SHA256 and tiny["fixture_only"] is True and
            tiny["native_scientific_evidence"] is False and Path(tiny["path"]).is_absolute(), "original tiny CPU gate differs")
    identity = launch["identity"]
    require(set(identity) == {"pid", "comm", "ppid", "start_ticks", "uid", "cmdline_sha256"}, "holder identity schema differs")
    holder_pid = integer(holder["pid"])
    require(holder_pid > 1 and integer(identity["start_ticks"]) > 0, "holder process identity required")
    integer(launch["pid"], holder_pid)
    integer(identity["pid"], holder_pid)
    integer(identity["ppid"])
    integer(identity["uid"])
    require(type(identity["cmdline_sha256"]) is str and len(identity["cmdline_sha256"]) == 64 and
            all(char in "0123456789abcdef" for char in identity["cmdline_sha256"]), "holder command byte digest required")
    equal(launch["command"], [plan["python"], "-B", LAUNCHER, "hold", "--seed", str(seed), "--runner-sha256", RUNNER_SHA256,
                            "--tiny-cpu-receipt", tiny["path"]], "original single-holder command differs")
    prefix = [plan["python"], "-B", RUNNER]
    root_args = ["--root", plan["root"], "--plan-sha256", entry["plan_sha256"]]
    equal(controller["command"], prefix + ["controller"] + root_args + ["--allow-gpu"], "original controller command differs")
    equal(collector["command"], prefix + ["collect"] + root_args + ["--completion-sha256", entry["completion_sha256"],
                                                                "--out", plan["root"] + "_collected"], "original collector command differs")
    integer(controller["pid"], bundle["receipts"]["controller_started"]["pid"])
    for record in (controller, collector):
        require(integer(record["pid"]) > 1, "controller/collector PID required")
        integer(record["pgid"], record["pid"])
    require(len({holder_pid, controller["pid"], collector["pid"]}) == 3, "conflicting native identities")
    integer(receipts["controller_exit.json"]["returncode"], 0)
    integer(receipts["collector_exit.json"]["returncode"], 1)
    integer(receipts["exit.json"]["returncode"], 1)
    claim = bundle["claim"]
    require(set(claim) == {"plan_sha256", "out", "retry"} and claim["retry"] is False, "original once claim differs")
    collection_start = receipts["collection_started.json"]
    equal([collection_start["completion_sha256"], collection_start["plan_sha256"], claim["plan_sha256"], claim["out"]],
          [entry["completion_sha256"], entry["plan_sha256"], entry["plan_sha256"], plan["root"] + "_collected"], "original collection hash/claim join differs")
    times = [seconds(precheck["time"]), seconds(holder["started_unix"]), seconds(controller["started_unix"]),
             seconds(receipts["controller_exit.json"]["completed_unix"]), seconds(collection_start["started_unix"]),
             seconds(collector["started_unix"]), seconds(receipts["collector_exit.json"]["completed_unix"]), seconds(receipts["exit.json"]["completed_unix"])]
    require(times == sorted(times) and times[0] <= seconds(launch["started_unix"]) <= times[-1], "original launch chronology differs")
    require(times[5] <= seconds(failure_record["time"]) <= times[6], "collection failure outside original collector span")
    for stage in STAGES:
        for name in ("launch.json", "started.json", "released.json"):
            require(times[1] <= seconds(bundle["files"]["run/" + stage + "/" + name]["time"]) <= times[3], "native stage outside original controller")
    transport = receipts.get("failure.json")
    if transport is not None:
        require(set(transport) == {"error", "holder_may_be_running"} and type(transport["error"]) is str and transport["error"] and
                transport["holder_may_be_running"] is True, "unreconciled launcher failure")
    return dict(native_controller_rc=0, original_collector_rc=1, original_holder_written_rc=1,
                original_collection_failure=dict(failure_record), launcher_failure=None if transport is None else dict(transport),
                original_once_chain_consistent=True, recovery_validated=False, scientific_retries=None,
                limitation="Original failure audit only; recovery receipt/API and all scientific raw/source audits remain required. "
                           "Holder rc1 is retained, not repaired to rc0. No live absence or OS holder reaping claim.")


def load_apis(module_dir="/tmp", source_root=SOURCE_ROOT, protocol_path=PROTOCOL, legacy_protocol_path=LEGACY_PROTOCOL):
    verify_frozen_sources()
    specification = importlib.util.spec_from_file_location("additive_recovered_frozen_helpers", FROZEN_REDUCER)
    frozen = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(frozen)
    apis = frozen.load_apis(module_dir, source_root, protocol_path, legacy_protocol_path)
    apis["frozen_reducer"] = frozen
    return apis


def load_bundle(entry, apis):
    require(type(entry) is dict and set(entry) == BASE_ENTRY_KEYS | RECOVERY_KEYS, "closed recovered seed entry required")
    frozen = apis["frozen_reducer"]
    bundle = frozen.load_bundle({key: copy.deepcopy(entry[key]) for key in BASE_ENTRY_KEYS})
    bundle["entry"] = copy.deepcopy(entry)
    recovered = {name: read_binding(entry[name]) for name in RECOVERY_KEYS}
    original = Path(entry["original_failure"]["path"])
    require(original.name == "collection_failure.json" and sorted(path.name for path in original.parent.iterdir()) == ["collection_failure.json"],
            "original failed collection must remain exactly preserved")
    new_out = Path(entry["scores"]["path"]).parent
    require(new_out != original.parent and Path(entry["recovery"]["path"]).parent == new_out and
            sorted(path.name for path in new_out.iterdir()) == ["collection.json", "recovery.json", "scores.json"], "exact separate successful recovery directory required")
    require(Path(entry["recovery_claim"]["path"]) != Path(entry["collection_claim"]["path"]), "original claim must not be reused or overwritten")
    bundle["recovery_evidence"] = recovered
    return bundle


def validate_recovery(bundle):
    entry, plan = bundle["entry"], bundle["plan"]
    evidence = bundle["recovery_evidence"]
    failure = evidence["original_failure"]["record"]
    original = audit_original_attempt(bundle, failure)
    native_root = plan["root"]
    original_files = {
        native_root + ".collection_claim.json": entry["collection_claim"]["sha256"],
        native_root + "_collected/collection_failure.json": entry["original_failure"]["sha256"],
        **{native_root + ".launcher/" + name: entry["launcher"]["files"][name]
           for name in ("controller_exit.json", "collector_exit.json", "exit.json")}}
    expected_claim = dict(schema=RECOVERY_SCHEMA, root=native_root, out=native_root + "_collected_repair1", plan_sha256=entry["plan_sha256"],
        completion_sha256=entry["completion_sha256"], repair_sha256=REPAIR_SHA256, runner_sha256=RUNNER_SHA256,
        original_failure_files=original_files, collection_attempt=2, scientific_retry=False, generation_calls=0, fits=0, updates=0)
    equal(evidence["recovery_claim"]["record"], expected_claim, "new recovery claim/source/failure joins differ")
    receipt = evidence["recovery"]["record"]
    elapsed = seconds(receipt["elapsed_seconds"])
    require(elapsed <= 180 and elapsed == bundle["collection"]["collection_seconds"], "recovery budget/collection time differs")
    expected_receipt = dict(schema=RECOVERY_SCHEMA, status="COLLECTION_REPAIRED_NOT_SCIENTIFIC_RETRY", returncode=0,
        claim_sha256=entry["recovery_claim"]["sha256"], repair_sha256=REPAIR_SHA256, runner_sha256=RUNNER_SHA256,
        scores_sha256=entry["scores"]["sha256"], collection_sha256=entry["collection"]["sha256"], original_failure_files=original_files,
        collection_attempt=2, scientific_retry=False, fits=0, updates=0, generation_calls=0, elapsed_seconds=elapsed)
    equal(receipt, expected_receipt, "successful recovery receipt/byte joins or zero scientific cost differs")
    original["recovery_validated"] = True
    original["scientific_retries"] = 0
    original["original_failure_evidence"] = copy.deepcopy(evidence["original_failure"])
    original["original_claim"] = dict(binding=entry["collection_claim"], record=bundle["claim"])
    original["original_launcher_files"] = entry["launcher"]["files"]
    original["recovery_claim"] = copy.deepcopy(evidence["recovery_claim"])
    original["recovery_receipt"] = copy.deepcopy(evidence["recovery"])
    original["collection_attempt"] = 2
    original["recovery_recorded_rc"] = receipt["returncode"]
    original["recovery_cost"] = dict(fits=0, updates=0, generation_calls=0, elapsed_seconds=elapsed)
    original["limitation"] = ("Scoring-only second collection, not a new scientific attempt. Original controller/collector/holder rc0/1/1 preserved. "
        "Successful repair receipt is written before CLI return, not an independent OS wait/reap receipt. "
        "Raw/source files are independently rehashed/rescored by this reducer; before/after preservation is attested by the pinned repair. "
        "No current native identity/absence, cross-root retry exclusion, or independent holder/recovery process reaping is claimed.")
    return original


def reduce_seed(bundle, apis):
    frozen = apis["frozen_reducer"]
    entry, plan, report, complete, files = (bundle[key] for key in ("entry", "plan", "report", "complete", "files"))
    seed = integer(entry["seed"])
    require(seed in (0, 1, 2), "original seed required")
    equal([plan["specification"]["seed"], plan["specification"]["fit_seed"], report["seed"]], [seed]*3, "cohort seed differs")
    require(plan["scope"] == report["scope"] == complete["scope"] == frozen.SCOPE, "additive scope differs")
    require(plan["self_sha256"] == plan["specification"]["runner_sha256"] == RUNNER_SHA256, "frozen runner differs")
    for name in ("core", "trainer"):
        equal(plan["specification"][name]["sha256"], frozen.PINS[name][1], "frozen source differs")
    equal(plan["specification"]["protocol"]["sha256"], frozen.PROTOCOL_PIN, "protocol differs")
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
    require(report["native_capture_custody_checked"] is True and report["automatic_pass"] is False and report["scientific_pass"] is None and complete["scored"] is False,
            "custody/no-promotion flags differ")
    equal(sorted(report["cells"]), sorted(ARMS), "fresh pair missing/extra")
    equal(plan["stages"], list(STAGES), "fixed stage order differs")
    equal(sorted(complete["stages"]), sorted(STAGES), "complete stage inventory differs")
    equal(report["counts"], dict(memory=COUNTS[seed], replay=24, rows_per_arm=COUNTS[seed]+24), "source denominator differs")
    equal(plan["counts"], report["counts"], "plan denominator differs")
    updates, calls = 8*(COUNTS[seed]+24), 2*COUNTS[seed]+60
    integer(plan["updates_per_arm"], updates)
    integer(plan["calls_per_arm"], calls)
    for key, expected in (("fits", 2), ("updates", 2*updates), ("calls", 2*calls)):
        integer(complete[key], expected)
        integer(plan["limits"][key], expected)
    for key, expected in (("controller", 7200), ("prepare", 180), ("collection", 180), ("global_fits", 6), ("global_updates", 1632),
                          ("global_calls", 480), ("aggregate_allocation_hours", 8), ("new_source_calls", 0), ("teacher_calls", 0)):
        integer(plan["limits"][key], expected)
    recovery = validate_recovery(bundle)
    source = frozen.validate_sources(bundle, apis)
    legacy, utilities = apis["legacy"], apis["utilities"]
    scorer = legacy.FrozenScorer(source["capture"], source["dataset"], source["retention"], apis)
    endpoints = dict(source["histories"], **report["cells"])
    indices = {name: legacy.rescore_cells(cells, source["calls"], scorer, seed, utilities) for name, cells in endpoints.items()}
    totals = {name: legacy.summarize_cells(cells, utilities) for name, cells in endpoints.items()}
    costs = frozen.validate_custody(bundle, apis, source, scorer)
    screens = {arm: legacy.screen(seed, indices[arm], indices["LR0"], utilities) for arm in ARMS}
    equal(report["screen"], screens, "unchanged noncompensatory screen differs")
    equal(report["best_constant"], legacy.constants(source["dataset"], source["calls"], scorer, report["cells"], utilities), "constant baseline recomputation differs")
    contrasts = {}
    for first, second in (("ADDITIVE", "MEMORY_ONLY"), ("ADDITIVE", "LR0"), ("MEMORY_ONLY", "LR0"), ("MEMORY_ONLY", "EXTRA_MEMORY"), ("ADDITIVE", "EXTRA_MEMORY")):
        panels = {}
        for panel in PANELS:
            metrics = utilities.MEMORY_METRICS if panel in ("exact", "paraphrase") else utilities.RETENTION_METRICS
            panels[panel] = {metric: frozen.item_changes(indices[first][panel], indices[second][panel], panel, metric, utilities) for metric in metrics}
        contrasts[first + "_vs_" + second] = dict(first=first, second=second, noncontemporaneous=second in HISTORY, panels=panels)
    restored = {}
    for arm in ARMS:
        restored[arm] = {}
        for panel in ("held", "canary"):
            rows = []
            for row_id in sorted(indices["LR0"][panel]):
                values = {name: utilities.metric(indices[name][panel][row_id], panel, "passed") for name in (arm, "LR0", "EXTRA_MEMORY")}
                rows.append(dict(row_id=row_id, lr0_correct=values["LR0"], old_extra_correct=values["EXTRA_MEMORY"], current_correct=values[arm],
                    restored_old_extra_loss=values["LR0"] and not values["EXTRA_MEMORY"] and values[arm], missing_lr0_correct=values["LR0"] and not values[arm]))
            restored[arm][panel] = rows
    raw_drift = {panel: sorted(row_id for row_id in indices["MEMORY_ONLY"][panel] if
        (indices["MEMORY_ONLY"][panel][row_id]["raw"], indices["MEMORY_ONLY"][panel][row_id]["finish_reason"]) !=
        (indices["EXTRA_MEMORY"][panel][row_id]["raw"], indices["EXTRA_MEMORY"][panel][row_id]["finish_reason"])) for panel in PANELS}
    for name in HISTORY:
        equal(report["reused_endpoints"][name], dict(noncontemporaneous=True, incremental_fits=0, incremental_updates=0, incremental_calls=0), "historical reuse label/cost differs")
    equal(report["incremental_cost"], dict(calls=2*calls, fits=2, updates=2*updates, historical_calls=0, historical_updates=0, historical_fits=0,
          new_source_calls=0, teacher_calls=0, controller_seconds=complete["elapsed_seconds"]), "incremental costs differ")
    for arm in ARMS:
        equal(report["training_costs"][arm], {key: value for key, value in files[f"training_{arm}.json"].items() if key not in
              ("items", "encoding", "epoch_order", "replay_items", "replay_encoding")}, "reported token/dose accounting differs")
    launcher = bundle["launcher"]
    holder_start = min(launcher["holder_started.json"]["started_unix"], launcher["launched.json"]["started_unix"])
    return dict(seed=seed, parent=plan["parent"], evidence=entry, denominators=dict(exact=COUNTS[seed], paraphrase=COUNTS[seed], held=48, canary=12,
        original_possible_records=16), totals=totals, screens=screens, contrasts=contrasts, lr0_restoration=restored, recovery=recovery,
        historical_extra_memory_check=dict(noncontemporaneous=True, exact_memory_items_and_order=True, raw_changed_ids=raw_drift,
            any_raw_drift=any(raw_drift.values()), interpretation="Behavior differences require diagnosis before attribution; not an execution gate or automatic failure."),
        costs=costs, spans=dict(prepare_seconds=bundle["receipts"]["prepare_done"]["elapsed_seconds"], controller_seconds=complete["elapsed_seconds"],
            original_failed_collection_wall_seconds=launcher["collector_exit.json"]["completed_unix"] - launcher["collection_started.json"]["started_unix"],
            original_holder_wall_seconds=launcher["exit.json"]["completed_unix"] - holder_start,
            recovery_collection_seconds=bundle["collection"]["collection_seconds"],
            limitation="Original holder includes the failed collector; recovery is separate CPU time, not new GPU work. Do not sum nested spans; recovery idle gap is unmeasured."),
        losses={arm: {key: report["fits"][arm][key] for key in ("mean_loss_per_epoch", "final_loss", "component_losses", "executed_order")} for arm in ARMS},
        parameter_diagnostics=report["parameter_diagnostics"], historical_manifest_diagnostics={name: {key: source["historical_manifests"][name].get(key)
            for key in ("steps", "final_loss", "mean_loss_per_epoch", "train_tokens_seen", "train_seconds", "wall_seconds")} for name in HISTORY},
        memory_source_presentations=files["training_MEMORY_ONLY.json"]["memory_source_presentations"], constants=report["best_constant"],
        reused_endpoints=report["reused_endpoints"], custody=dict(new_stage_raw_and_hashes_audited=True, historical_raw_rescored=True,
            historical_native_generation_replayed=False, current_native_gpu_identity_verified=False, numerical_norms_recomputed=False),
        interpretation="Collection-only recovery after completed original scientific attempts. Full memory occurrence parity, not compute/RNG/gradient parity. No automatic promotion.")


def reduce_cohort(bundles, apis):
    require(type(bundles) is list and len(bundles) == 3, "all three original roots required; no exclusions")
    equal(sorted(integer(bundle["entry"]["seed"]) for bundle in bundles), [0, 1, 2], "unique original seeds0/1/2 required")
    results = [reduce_seed(bundle, apis) for bundle in sorted(bundles, key=lambda item: item["entry"]["seed"])]
    aggregate = {key: sum(result["costs"][arm][key] for result in results for arm in ARMS) for key in ("fits", "updates", "calls")}
    equal([aggregate["fits"], aggregate["updates"], aggregate["calls"]], [6, 1632, 480], "unchanged full cohort cost differs")
    aggregate.update(historical_incremental_calls=0, historical_incremental_updates=0, historical_incremental_fits=0,
                     teacher_calls=0, new_source_calls=0, recovery_fits=0, recovery_updates=0, recovery_generation_calls=0, scientific_retries=0)
    aggregate["executed_training"] = {arm: {key: sum(result["costs"][arm]["tokens"][key] for result in results) for key in
        ("updates", "memory_forwards", "replay_forwards", "total_forwards", "memory_total_tokens", "replay_total_tokens", "total_tokens", "supervised_tokens", "context_tokens")} for arm in ARMS}
    aggregate["prepare_plus_original_holder_wall_hours"] = sum(result["spans"]["prepare_seconds"] + result["spans"]["original_holder_wall_seconds"] for result in results) / 3600
    require(aggregate["prepare_plus_original_holder_wall_hours"] <= 8, "original aggregate allocation ceiling exceeded")
    aggregate["separate_recovery_cpu_seconds"] = sum(result["spans"]["recovery_collection_seconds"] for result in results)
    return dict(schema=SCHEMA, protocol_sha256=apis["frozen_reducer"].PROTOCOL_PIN, reducer_sha256=digest(__file__), frozen_sources=verify_frozen_sources(),
        seeds=results, screen_by_seed={str(result["seed"]): result["screens"] for result in results}, costs=aggregate,
        all_seed_screen={arm: all(result["screens"][arm]["passed"] for result in results) for arm in ARMS},
        automatic_promotion=False, scientific_pass=None, fit_authorized=False,
        limitations=["Scoring-only second collection preserves original rc0/1/1 and separate optional launcher BrokenPipe; no new scientific attempt.",
            "Per-item LR0-correct losses cannot be offset by gains; exact recall floors remain8/7/5. Full memory occurrence parity is not compute/RNG parity.",
            "Historical references are noncontemporaneous. No parenting, H1/H2, repeated-cycle or clean-lineage qualification.",
            "Scalar receipts are audited without tensor recomputation. No live native identity, independent process reaping, or unlogged reservation-gap measurement."])


def markdown(report):
    lines = ["# Additive replay — collection-only recovery", "", "| Seed | Arm | Exact eligible | Paraphrase content | Held | Canary | Screen |",
             "|---|---|---:|---:|---:|---:|---|"]
    for result in report["seeds"]:
        for arm in ARMS:
            totals = result["totals"][arm]
            lines.append(f"| {result['seed']} | {arm} | {totals['exact']['totals']['production_eligible']}/{result['denominators']['exact']} | "
                f"{totals['paraphrase']['totals']['content_correct']}/{result['denominators']['paraphrase']} | {totals['held']['totals']['passed']}/48 | "
                f"{totals['canary']['totals']['passed']}/12 | {result['screens'][arm]['passed']} |")
        recovery = result["recovery"]
        lines.append(f"Seed {result['seed']}: original controller/collector/holder rc0/1/1; recovery recorded rc0, collection attempt2, "
            f"scientific retries0. Original error: {json.dumps(recovery['original_collection_failure'])}. Launcher error (separate): {json.dumps(recovery['launcher_failure'])}.")
    lines.extend(["", "6 fits,1632 updates,480 cold calls unchanged; recovery adds zero fits/updates/generation. No automatic promotion.",
                  "Exact original errors/byte pins, component costs and per-item contrasts remain in analysis.json; all archived evidence remains untouched."])
    return "\n".join(lines) + "\n"


def run(manifest_path, manifest_sha256, out, *, module_dir="/tmp", source_root=SOURCE_ROOT, protocol_path=PROTOCOL, legacy_protocol_path=LEGACY_PROTOCOL):
    manifest = read_binding(dict(path=manifest_path, sha256=manifest_sha256))["record"]
    require(set(manifest) == {"schema", "seeds"} and manifest["schema"] == INPUT_SCHEMA and type(manifest["seeds"]) is list and len(manifest["seeds"]) == 3,
            "closed three-seed recovered manifest required")
    out = Path(out).absolute()
    require(not out.exists() and not any(part.is_symlink() for part in (out, *out.parents)), "fresh nonsymlink output required")
    protected = [Path(manifest_path).resolve(), Path(source_root).resolve(), Path(module_dir).resolve(), Path(protocol_path).resolve(), Path(legacy_protocol_path).resolve()]
    for entry in manifest["seeds"]:
        require(set(entry) == BASE_ENTRY_KEYS | RECOVERY_KEYS, "closed recovered entry required")
        roots = [Path(entry["root"]).resolve(), Path(entry["launcher"]["root"]).resolve()]
        roots += [Path(entry[name]["path"]).resolve().parent for name in ("scores", "collection", "original_failure", "recovery")]
        require(all(not out.is_relative_to(root) for root in roots), "output must not enter any evidence directory")
        protected += roots + [Path(entry[name]["path"]).resolve() for name in ("collection_claim", "recovery_claim")]
    require(all(out != path and out not in path.parents for path in protected), "output must not contain protected inputs")
    apis = load_apis(module_dir, source_root, protocol_path, legacy_protocol_path)
    report = reduce_cohort([load_bundle(entry, apis) for entry in manifest["seeds"]], apis)
    report["manifest_sha256"] = manifest_sha256
    out.mkdir(parents=True, exist_ok=False)
    with (out / "analysis.json").open("x") as stream:
        stream.write(json.dumps(report, sort_keys=True, allow_nan=False) + "\n")
    with (out / "analysis.md").open("x") as stream:
        stream.write(markdown(report))
    return dict(out=str(out), analysis_sha256=digest(out / "analysis.json"), markdown_sha256=digest(out / "analysis.md"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("manifest", "manifest-sha256", "out"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--module-dir", default="/tmp")
    parser.add_argument("--source-root", default=SOURCE_ROOT)
    parser.add_argument("--protocol-path", default=PROTOCOL)
    parser.add_argument("--legacy-protocol-path", default=LEGACY_PROTOCOL)
    arguments = vars(parser.parse_args())
    arguments["manifest_path"] = arguments.pop("manifest")
    print(json.dumps(run(**arguments), sort_keys=True))


if __name__ == "__main__":
    main()
