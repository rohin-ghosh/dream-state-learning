"""Fixed task-only interference sentinel; only Main may allocate and launch."""
from __future__ import annotations

import argparse
import copy
from dataclasses import asdict
import json
import math
import os
from pathlib import Path
import signal
import sys
import time


RATES = {"0": (0.0, "4"), "3e-5": (3e-5, "5"), "1e-4": (1e-4, "6")}
PHASES = tuple(f"continuation-phase-{index:02d}" for index in range(1, 5))
SECONDS = 1800
SEED0_SHA = "d5a3d0297290184061b5cfcc3bf7fa5ba36a5995fbaedb021df464be7879ec5e"
CLAIM = "TASK_ONLY_INTERFERENCE_NOT_PASSIVE_FADING_NOT_CHILD_SLEEP"


def bind(source):
    global base, trainer, material, readout
    source = Path(source).resolve(strict=True)
    sys.path.insert(0, str(source))
    from organism_v6 import rulegame_parenting_diagnostic as base
    from organism_v6 import train_adapter_v3 as trainer
    from organism_v6 import fundamental_continuation_corpus as material
    from organism_v6 import fundamental_teaching_readout as readout
    for module in (base, trainer, material, readout):
        require(Path(module.__file__).resolve().parent.parent == source, "wrong imported source root")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def write(path, value):
    with Path(path).open("x") as target:
        json.dump(value, target, sort_keys=True, indent=2, allow_nan=False)
        target.write("\n")


def seal(root, plan):
    write(root / "plan.json", plan)
    write(root / "plan.sha256.json", {"sha256": base.digest(root / "plan.json")})


def read_plan(root):
    require(base.digest(root / "plan.json") == base.read(root / "plan.sha256.json")["sha256"], "plan changed")
    return base.read(root / "plan.json")


def sources():
    return dict(readout.sources(), **material.source_hashes(), sentinel_script=base.digest(__file__))


def config(model, rate):
    require(rate in RATES, "only fixed sentinel rates")
    return asdict(trainer.TrainConfig(model=model, rank=8, alpha=16, dropout=.05,
        lr=RATES[rate][0], epochs=4, batch_size=4, grad_accum=1, seed=0, pack=False, max_len=512))


def phase_paths(root, starting_adapter):
    parent = Path(starting_adapter)
    rows = []
    for phase in PHASES:
        stage = root / phase
        adapter = stage / "adapter"
        rows.append(dict(phase=phase, stage=str(stage), parent=str(parent), adapter=str(adapter)))
        parent = adapter
    return rows


def fit_command(plan, rate, row):
    return [sys.executable, "-B", "-m", "organism_v6.train_adapter_v3",
        "--corpus", str(Path(plan["materialroot"]) / (row["phase"] + ".json")),
        "--out", row["adapter"], "--init-adapter", row["parent"], "--model", plan["model"],
        "--rank", "8", "--alpha", "16", "--dropout", "0.05", "--lr", str(RATES[rate][0]),
        "--epochs", "4", "--batch-size", "4", "--grad-accum", "1", "--seed", "0",
        "--no-pack", "--max-len", "512"]


def bounds(started, deadline, lease_end):
    require(all(math.isfinite(value) for value in (started, deadline, lease_end)), "nonfinite deadline")
    effective = min(started + SECONDS, deadline, lease_end - 10)
    require(effective - started > base.CLEANUP_RESERVE + 10, "insufficient cleanup time")
    require(base.WORKER_SECONDS == 600 and base.RESERVED_SECONDS == SECONDS, "native bounds changed")
    return effective


def prepare(materialroot, startingadapter, seed0_plan, source_root, deadline, lease_end, runroot):
    root = Path(runroot).expanduser().absolute()
    require(not root.exists() and not root.is_symlink(), "fresh runroot required")
    require(not any(path.is_symlink() for path in root.parents), "symlink output path")
    root = root.resolve()
    bounds(time.time(), deadline, lease_end)
    seed_path = Path(seed0_plan).resolve(strict=True)
    seed = read_plan(seed_path.parent)
    require(seed_path.name == "plan.json" and base.digest(seed_path) == SEED0_SHA, "not pinned actual seed0 attempt1 plan")
    parent = Path(startingadapter).resolve(strict=True)
    require(seed_path.parent.name == "astra_fundamental_teaching_20260912_attempt1" and
        parent == seed_path.parent / "fit_teach" / "adapter", "not actual seed0 teach adapter")
    require(Path(source_root).resolve() == base.REPO.resolve(), "source root differs")
    model = seed["model"]
    expected = config(model, "0")
    expected["lr"] = 3e-4
    require(seed["config"] == expected and seed["eval_dev_ids"] == list(readout.CASE_IDS), "seed0 recipe/cases differ")
    materialroot = Path(materialroot).resolve(strict=True)
    material.verify(materialroot)
    manifest = base.read(materialroot / "manifest.json")
    require(manifest["status"] == "NATIVE_V3_TOKEN_AUDIT_COMPLETE" and manifest["native_token_audit"] is True and
        manifest["tokenizer_injected"] is False, "actual native material required")
    require(manifest["model"] == model and manifest["model_files"] == seed["model_files"] ==
        base.model_hashes(model), "prepared material/seed0/base bytes differ")
    require(manifest["phase_corpora"] == {phase: phase + ".json" for phase in PHASES}, "phase membership differs")
    for protected in (parent, materialroot, seed_path.parent, Path(model).resolve(), base.REPO.resolve()):
        require(root != protected and protected not in root.parents and root not in protected.parents, "output overlaps inputs")
    parent_files = trainer._warm_inventory(parent)
    fit = base.read(parent.parent / "result.json")
    require(fit["arm"] == "teach" and fit["adapter"] == str(parent) and fit["adapter_files"] == parent_files,
        "seed0 completed fit inventory differs")
    require(fit["supervised"]["ok"] and fit["supervised"]["reservation_release_verified"], "seed0 cleanup unverified")
    require(base.read(parent / "train_manifest.json") == fit["manifest"] and fit["manifest"]["config"] == expected,
        "seed0 training manifest changed")
    trainer._warm_parent(parent, root / "unused-validation-output", trainer.TrainConfig(**config(model, "0")))
    require(deadline - time.time() > SECONDS and lease_end >= deadline, "prepare needs future full lineage window")
    plan = dict(schema=1, materialroot=str(materialroot), startingadapter=str(parent), model=model,
        model_files=seed["model_files"], parent_files=parent_files, seed0_plan=str(seed_path),
        seed0_plan_sha256=base.digest(seed_path), seed0_fit_sha256=base.digest(parent.parent / "result.json"),
        source_root=str(base.REPO), source_hashes=sources(), material_files=base.tree_hashes(materialroot),
        deadline=float(deadline), real_lease_end=float(lease_end), lineage_seconds=SECONDS, worker_seconds=600,
        rates={rate: config(model, rate) for rate in RATES}, devices={rate: value[1] for rate, value in RATES.items()},
        cases=readout.selected_cases(), claim=CLAIM, model_origin="UNRESOLVED_LOCAL_HASHES_ONLY",
        budget="Main must declare separate 90 A40-minute budget and retain each reservation across all gaps")
    base.fresh_directory(root, model)
    readout.prepare(root / "readout-template", model, str(parent), "4", float(deadline))
    plan["readout_template_files"] = base.tree_hashes(root / "readout-template")
    seal(root, plan)
    verify(root)
    return dict(root=str(root), status="PREPARED_NOT_LAUNCHED", devices=plan["devices"])


def verify(root):
    plan = read_plan(root)
    require(plan["schema"] == 1 and plan["claim"] == CLAIM and plan["lineage_seconds"] == SECONDS and
        plan["worker_seconds"] == 600 and plan["devices"] == {rate: value[1] for rate, value in RATES.items()}, "contract changed")
    require(plan["source_root"] == str(base.REPO) and plan["source_hashes"] == sources(), "sources changed")
    require(plan["cases"] == readout.selected_cases() and
        plan["rates"] == {rate: config(plan["model"], rate) for rate in RATES}, "cases/recipe changed")
    require(base.digest(plan["seed0_plan"]) == plan["seed0_plan_sha256"] == SEED0_SHA and
        base.digest(Path(plan["startingadapter"]).parent / "result.json") == plan["seed0_fit_sha256"], "seed0 provenance changed")
    require(base.model_hashes(plan["model"]) == plan["model_files"] and
        trainer._warm_inventory(plan["startingadapter"]) == plan["parent_files"], "base/initial parent changed")
    material.verify(plan["materialroot"])
    require(base.tree_hashes(plan["materialroot"]) == plan["material_files"] and
        base.tree_hashes(root / "readout-template") == plan["readout_template_files"], "material/template changed")
    return plan


def state_inventory(adapter):
    adapter = Path(adapter)
    files = [adapter / name for name in ("adapter_model.safetensors", "adapter_model.bin") if (adapter / name).is_file()]
    require(len(files) == 1, "missing/ambiguous saved parameter state")
    if files[0].suffix == ".safetensors":
        from safetensors.torch import load_file
        state = load_file(str(files[0]), device="cpu")
    else:
        import torch
        state = torch.load(files[0], map_location="cpu", weights_only=True)
    trainer._warm_validate_state(state, state)
    return trainer._warm_state_inventory(state)


def check_states(rate, before, warm, saved):
    require(before == warm["source_state"] and saved == warm["final_state"], "serialized parameter state differs")
    require(set(before) == set(saved) == set(warm["initialized_state"]), "partial initialized/saved state")
    for name in before:
        require(before[name]["shape"] == saved[name]["shape"], "parameter structure changed")
    unchanged = before == warm["initialized_state"] == saved
    require(rate != "0" or unchanged, "LR0 full parameter state changed (including dtype)")
    return unchanged


def verify_fit(plan, rate, row, parent_files, before):
    adapter = Path(row["adapter"])
    manifest = base.read(adapter / "train_manifest.json")
    require((adapter / "DONE").is_file() and manifest["config"] == plan["rates"][rate] and
        manifest["steps"] == manifest["micro_batches"] == 16 and manifest["epochs_run"] == 4 and
        manifest["nonfinite_batches"] == 0 and math.isfinite(manifest["final_loss"]), "incomplete/nonfinite/wrong fit")
    actual = manifest["corpus"]
    require(actual["sha256"] == plan["material_files"][row["phase"] + ".json"] and
        actual["n_items"] == actual["n_encoded"] == 16 and actual["n_skipped_no_target"] == 0, "actual corpus differs")
    require(all(manifest["truncation"][key] == 0 for key in
        ("items_truncated", "context_tokens_dropped", "target_tokens_dropped", "items_split")), "truncated/split corpus")
    tokens = base.read(Path(plan["materialroot"]) / "token_audit.json")["phases"][row["phase"]]["per_epoch"]
    require(manifest["tokens"]["total"] == tokens["input_tokens"] and manifest["tokens"]["target"] == tokens["target_tokens"]
        and manifest["train_tokens_seen"] == 4 * tokens["input_tokens"], "actual token counts differ")
    warm = manifest["warm_start"]
    require(warm["mode"] == "WEIGHT_WARM_START_FRESH_OPTIMIZER" and warm["parent_path"] == row["parent"] and
        warm["parent_files"] == warm["parent_files_after"] == parent_files == trainer._warm_inventory(row["parent"]), "parent changed")
    require(all(warm[key] is True for key in ("parent_unchanged", "base_frozen", "initialized_loaded_state_check")) and
        warm["adapter_count"] == 1 and warm["phase_seed"] == 0 and warm["optimizer_initial_state_entries"] == 0 and
        warm["optimizer_state_restored"] is False and warm["optimizer_state_saved"] is False and
        warm["optimizer_initialization"] == "fresh_per_write" and warm["phase_steps"] == 16,
        "warm-start ownership/optimizer differs")
    prior = base.read(Path(row["parent"]) / "train_manifest.json")
    cumulative = prior.get("warm_start", {}).get("cumulative_steps", prior["steps"])
    require(warm["parent_cumulative_steps"] == cumulative and warm["cumulative_steps"] == cumulative + 16,
        "cumulative parent chain differs")
    unchanged = check_states(rate, before, warm, state_inventory(adapter))
    return dict(parent=row["parent"], parent_files=parent_files, adapter=str(adapter),
        adapter_files=trainer._warm_inventory(adapter), parameter_state_unchanged=unchanged,
        base_parameter_scope="frozen trainer base plus unchanged bound base files; serialized LoRA tensors compared exactly",
        steps=16, train_tokens_seen=manifest["train_tokens_seen"], manifest_sha256=base.digest(adapter / "train_manifest.json"))


def execute_phase(root, lineage, plan, rate, row, effective):
    verify(root)
    stage = Path(row["stage"])
    stage.mkdir()
    parent_files, before = trainer._warm_inventory(row["parent"]), state_inventory(row["parent"])
    active = dict(plan, device=RATES[rate][1], lease_end=effective)
    write(stage / "phase.json", dict(row, config=plan["rates"][rate], parent_files=parent_files,
        effective_deadline=effective, real_lease_end=plan["real_lease_end"]))
    fit_cost = base.supervise(lineage, active, stage / "fit-worker", fit_command(plan, rate, row))
    fit = verify_fit(plan, rate, row, parent_files, before)
    write(stage / "fit-result.json", fit)
    readroot = stage / "readout"
    readroot.mkdir()
    readplan = copy.deepcopy(read_plan(root / "readout-template"))
    readplan.update(adapter=row["adapter"], adapter_files=fit["adapter_files"], device=active["device"], lease_end=effective)
    readplan["identity"] = base.expected_identity(readplan, row["adapter"])
    seal(readroot, readplan)
    readout.verify(readroot)
    (readroot / "run").mkdir()
    command = [sys.executable, "-B", "-m", "organism_v6.fundamental_teaching_readout", "_worker",
        "--root", str(readroot), "--allow-gpu"]
    read_cost = base.supervise(lineage, readplan, readroot / "run" / "worker", command, readroot / "run" / "data" / "calls")
    reduced = readout.reduce(readroot)
    require(reduced["complete"] is True and reduced["counts"]["total"] == 48, "incomplete readout is not zero")
    require(trainer._warm_inventory(row["adapter"]) == fit["adapter_files"], "readout modified adapter")
    require(trainer._warm_inventory(row["parent"]) == parent_files, "readout modified prior parent")
    verify(root)
    result = dict(phase=row["phase"], fit=fit, fit_cost=fit_cost, readout_cost=read_cost,
        reduction_sha256=base.digest(readroot / "reduction.json"))
    write(stage / "result.json", result)
    return result


def run_one_rate(root, rate, allow_gpu=False):
    require(allow_gpu and rate in RATES, "Main allocation and explicit --allow-gpu required")
    require(os.environ.get("CUDA_VISIBLE_DEVICES") == RATES[rate][1], "controller must inherit exact reserved device")
    root = Path(root).resolve(strict=True)
    plan = read_plan(root)
    started = time.time()
    started_monotonic = time.monotonic()
    effective = bounds(started, plan["deadline"], plan["real_lease_end"])
    lineage = root / ("rate-" + rate)
    lineage.mkdir()
    record = dict(rate=rate, device=RATES[rate][1], controller_pid=os.getpid(), started=started,
        effective_deadline=effective, real_lease_end=plan["real_lease_end"], plan_sha256=base.digest(root / "plan.json"),
        reservation_scope="entire controller including CPU/readout/preparation gaps; Main owns external ledger",
        release_between_workers=False, full_vacancy_check="Main BEFORE controller spawn; not repeated inside")
    write(lineage / "reservation.json", record)
    completed, error = [], None
    handlers = {}
    def interrupted(number, frame):
        raise RuntimeError(f"controller interrupted/deadline cleanup boundary: {number}")
    for number in (signal.SIGALRM, signal.SIGTERM, signal.SIGINT):
        handlers[number] = signal.signal(number, interrupted)
    signal.setitimer(signal.ITIMER_REAL, max(.001, effective - time.time() - base.CLEANUP_RESERVE))
    try:
        verify(root)
        for row in phase_paths(lineage, plan["startingadapter"]):
            require(time.time() < effective - base.CLEANUP_RESERVE - 10, "lineage budget exhausted")
            completed.append(execute_phase(root, lineage, plan, rate, row, effective))
    except BaseException as failure:
        error = dict(type=type(failure).__name__, message=str(failure))
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        try:
            clean = base.supervisor.gpu_processes_absent(RATES[rate][1]) is True
        except Exception:
            clean = False
        try:
            receipts = [base.read(path) for path in lineage.glob("**/supervision.json")]
            require(all(math.isfinite(receipt["reserved_seconds"]) and receipt["reserved_seconds"] >= 0
                for receipt in receipts), "invalid worker cost receipt")
            accounted = all((path.parent / "supervision.json").is_file() for path in lineage.glob("**/process.json"))
        except Exception as failure:
            receipts, accounted = [], False
            error = error or dict(type=type(failure).__name__, message=str(failure))
        released = clean and accounted and all(all(receipt.get(key) is True for key in
            ("ok", "reservation_release_verified", "owned_group_empty", "gpu_processes_absent")) for receipt in receipts)
        ended = time.time()
        result = dict(record, status="COMPLETE" if error is None and len(completed) == 4 and len(receipts) == 8 and released and ended <= effective
            else "FAILED_PARTIAL_NO_RETRY", ended=ended, reserved_seconds=time.monotonic()-started_monotonic,
            worker_reserved_seconds=sum(receipt["reserved_seconds"] for receipt in receipts),
            release_verified=released, deadline_met=ended <= effective, phases=completed, error=error,
            claim=CLAIM, counts_used_for_selection=False, monetary_cost=None)
        write(lineage / "terminal.json", result)
        for number, handler in handlers.items():
            signal.signal(number, handler)
    require(result["status"] == "COMPLETE", "partial lineage; inspect terminal.json; no replay/resume")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "run-one-rate", "status"))
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--runroot", required=True)
    for name in ("materialroot", "startingadapter", "seed0-plan"):
        parser.add_argument("--" + name)
    parser.add_argument("--deadline", type=float)
    parser.add_argument("--lease-end", type=float)
    parser.add_argument("--rate", choices=tuple(RATES))
    parser.add_argument("--allow-gpu", action="store_true")
    args = parser.parse_args()
    bind(args.source_root)
    if args.stage == "prepare":
        require(all(getattr(args, name) is not None for name in
            ("materialroot", "startingadapter", "seed0_plan", "deadline", "lease_end")), "missing prepare inputs")
        result = prepare(args.materialroot, args.startingadapter, args.seed0_plan, args.source_root,
            args.deadline, args.lease_end, args.runroot)
    elif args.stage == "run-one-rate":
        result = run_one_rate(args.runroot, args.rate, args.allow_gpu)
    else:
        root = Path(args.runroot)
        read_plan(root)
        result = {rate: base.read(root / ("rate-" + rate) / "terminal.json")
            if (root / ("rate-" + rate) / "terminal.json").exists() else
            {"status": "NONTERMINAL_OR_ABANDONED" if (root / ("rate-" + rate)).exists() else "NOT_STARTED"}
            for rate in RATES}
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
