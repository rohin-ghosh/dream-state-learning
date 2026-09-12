"""One fixed sequential replay pair; Main owns allocation and seed progression."""
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
import signal
import sys
import time

MEMORY_SHA = "ac7a110bc74724fc592407ced854ad162da275d3de9d9eeeb40c19788416afdb"
ARMS = ("mixed", "all_memory")
ADDITION_IDS = tuple("train-addition-" + suffix for suffix in
    ("011", "039", "055", "029", "048", "000", "052", "017", "036", "046", "063", "019", "057", "030", "012", "015"))
COUNTS = {
    "mixed": dict(items=32, epochs=20, steps=160, cumulative_steps=240,
                  input_per_epoch=1654, target_per_epoch=250, input_presentations=33080, target_presentations=5000),
    "all_memory": dict(items=16, epochs=40, steps=160, cumulative_steps=240,
                       input_per_epoch=704, target_per_epoch=32, input_presentations=28160, target_presentations=1280),
}
CLAIM = "FIXED_UPDATE_REPLAY_ALLOCATION_NOT_EQUAL_MEMORY_DOSE_OR_COMPUTE"
PROGRESSION = dict(owner="Main", first_seed=0, decide_only_after_both_arms=True,
    mixed_dev_memory_min=15, mixed_exact_memory_min=15, mixed_adherence_min=30, mixed_act_min=31,
    technical_completion_required=True, next_seeds=[1, 2], automatic_progression=False)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def bind(source, helper, fading_helper):
    global memory, old, base, trainer, dev, exact
    helper = Path(helper).resolve(strict=True)
    require(hashlib.sha256(helper.read_bytes()).hexdigest() == MEMORY_SHA, "accepted memory helper changed")
    spec = importlib.util.spec_from_file_location("replay_memory_helper", helper)
    memory = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(memory)
    memory.bind(source, fading_helper)
    old, base, trainer, dev, exact = memory.old, memory.base, memory.trainer, memory.dev, memory.exact


def sources():
    return dict(memory.sources(), replay_sidecar=base.digest(__file__))


def configs(model, seed):
    return {arm: memory.config(model, seed, COUNTS[arm]["epochs"]) for arm in ARMS}


def bounds(started, deadline, lease_end):
    require(all(math.isfinite(value) for value in (started, deadline, lease_end)), "nonfinite bounds")
    require(base.WORKER_SECONDS == 600 and base.CLEANUP_RESERVE == 140, "native bounds changed")
    effective = min(started + 1200, deadline, lease_end - 10)
    require(effective == started + 1200 and effective - time.time() > 150, "full1200s pair/cleanup window required")
    return effective


def select_material(original):
    rows = original["corpus"]
    indexed = {row["group"]: row for row in rows}
    require(len(rows) == len(indexed) == 80 and
        {row["group"] for row in rows if row["view"] == "memory"} == set(exact.CASE_IDS) and
        {row["group"] for row in rows if row["view"] == "addition"} ==
        {f"train-addition-{index:03d}" for index in range(64)}, "original80-row membership differs")
    additions = [row["group"] for row in rows if row["view"] == "addition"][:16]
    require(tuple(additions) == ADDITION_IDS, "first16 arithmetic source order changed")
    selected = set(exact.CASE_IDS) | set(ADDITION_IDS)
    return dict(mixed=dict(corpus=[row for row in rows if row["group"] in selected]),
                all_memory=dict(corpus=[row for row in rows if row["view"] == "memory"]))


def audit_material(original, original_plan, tokenizer):
    material = select_material(original)
    memory_material, _ = memory.subset(original, tokenizer)
    require(material["all_memory"] == memory_material, "memory material differs")
    prior = {row["case_id"]: row for row in original_plan["row_audits"]["teach"]}
    audited = {}
    for arm in ARMS:
        rows = []
        for item in material[arm]["corpus"]:
            encoded = trainer.encode_item_segments(trainer.normalize_items([item])[0], tokenizer, 512, False, True)
            require(len(encoded) == 1 and encoded[0].context_dropped == encoded[0].target_dropped == 0 and
                encoded[0].n_splits == 1, "native split/truncation")
            selected = encoded[0]
            count = sum(label != -100 for label in selected.labels)
            check = dict(case_id=item["group"], input_tokens=len(selected.ids), target_tokens=count,
                         labels_sha256=base.value_hash([selected.labels]))
            require(check == prior[item["group"]], "original native token/mask receipt differs")
            rows.append(dict(check, input_ids=selected.ids, labels=selected.labels))
        expected = COUNTS[arm]
        require(len(rows) == expected["items"] and sum(row["input_tokens"] for row in rows) == expected["input_per_epoch"] and
            sum(row["target_tokens"] for row in rows) == expected["target_per_epoch"] and
            len(rows) * expected["epochs"] // 4 == 160, "fixed native counts differ")
        audited[arm] = rows
    return material, audited


def paths(stage, parent):
    return {arm: dict(parent=parent, adapter=str(stage / arm / "adapter")) for arm in ARMS}


def fit_command(root, plan, arm, adapter):
    command = [sys.executable, "-B", "-m", "organism_v6.train_adapter_v3", "--corpus", str(root / (arm + ".json")),
        "--out", str(adapter), "--init-adapter", plan["parent"]["parent"], "--model", plan["model"],
        "--rank", "8", "--alpha", "16", "--dropout", "0.05", "--lr", "0.0003",
        "--epochs", str(COUNTS[arm]["epochs"]), "--batch-size", "4", "--grad-accum", "1",
        "--seed", str(plan["seed"]), "--no-pack", "--max-len", "512"]
    require(asdict(trainer.config_from_args(trainer.build_parser().parse_args(command[4:]))) == plan["configs"][arm],
        "effective CLI recipe differs")
    return command


def prepare(parentroot, seed, device, deadline, lease_end, runroot):
    bounds(time.time(), deadline, lease_end)
    memory.branches([device, device, device])
    parentroot = Path(parentroot).resolve(strict=True)
    original = old.read_plan(parentroot)
    model = original["model"]
    root = memory.fresh(runroot, (parentroot, model, base.REPO))
    expected_configs = configs(model, seed)
    model_files = base.model_hashes(model)
    parent = memory.parent_record(parentroot, seed, model, model_files)
    tokenizer = base.native_tokenizer(model)
    material, audit = audit_material(base.read(parentroot / "teach.json"), original, tokenizer)
    templates = {name: memory.template(module, model, model_files, tokenizer, device, lease_end)
                 for name, module in (("dev", dev), ("exact", exact))}
    require(all(parent["readout"][key] == templates["dev"][key] for key in
        ("cases", "requests", "native_inputs")), "original dev endpoint differs")
    root.mkdir()
    for arm in ARMS:
        old.write(root / (arm + ".json"), material[arm])
    plan = dict(schema=1, parentroot=str(parentroot), parent=parent, seed=seed, device=device,
        model=model, model_files=model_files, source_root=str(base.REPO), source_hashes=sources(),
        configs=expected_configs, arm_order=list(ARMS), accounting=COUNTS, addition_ids=list(ADDITION_IDS),
        material_files={arm + ".json": base.digest(root / (arm + ".json")) for arm in ARMS},
        native_audit=audit, templates=templates, deadline=float(deadline), real_lease_end=float(lease_end),
        pair_seconds=1200, cleanup_seconds=140, aggregate_a40_seconds=5400,
        progression=PROGRESSION, outcome_selective_skips=False, calls_per_arm=64,
        new_off_calls=0, new_hf_calls=0, confirmation_calls=0, claim=CLAIM,
        inherited_anchor="SEQ105 memory-only80: equal memory exposure to mixed160, different update-budget estimand")
    for arm, row in paths(root / "run", parent["parent"]).items():
        fit_command(root, plan, arm, row["adapter"])
        trainer._warm_parent(row["parent"], row["adapter"], trainer.TrainConfig(**plan["configs"][arm]))
    old.seal(root, plan)
    return dict(status="PAIR_PREPARED_NOT_LAUNCHED", root=str(root), seed=seed, device=device, arm_order=list(ARMS))


def verify(root):
    plan = old.read_plan(root)
    require(plan["schema"] == 1 and plan["source_root"] == str(base.REPO) and plan["source_hashes"] == sources(), "source changed")
    require(plan["configs"] == configs(plan["model"], plan["seed"]) and plan["accounting"] == COUNTS and
        plan["arm_order"] == list(ARMS) and plan["addition_ids"] == list(ADDITION_IDS) and
        plan["pair_seconds"] == 1200 and plan["cleanup_seconds"] == 140 and plan["aggregate_a40_seconds"] == 5400 and
        plan["progression"] == PROGRESSION and plan["outcome_selective_skips"] is False and
        plan["calls_per_arm"] == 64 and all(plan[key] == 0 for key in ("new_off_calls", "new_hf_calls", "confirmation_calls")) and
        plan["claim"] == CLAIM, "fixed pair contract changed")
    memory.branches([plan["device"]] * 3)
    require(base.model_hashes(plan["model"]) == plan["model_files"], "base changed")
    parent = plan["parent"]
    require(trainer._warm_inventory(parent["parent"]) == parent["parent_files"] and
        all(base.digest(path) == checksum for path, checksum in parent["provenance"].items()), "original parent changed")
    parentroot = Path(plan["parentroot"])
    require(parent["parent"] == str(parentroot / "fit_teach/adapter") and
        base.digest(parentroot / "plan.json") == memory.PINS[str(plan["seed"])][0] and
        base.tree_hashes(parentroot / "readouts/teach") == parent["readout_files"], "original lineage changed")
    original = select_material(base.read(parentroot / "teach.json"))
    for arm in ARMS:
        require(base.digest(root / (arm + ".json")) == plan["material_files"][arm + ".json"] and
            base.read(root / (arm + ".json")) == original[arm], "selected material changed")
    return plan


def validate_manifest(plan, arm, manifest, before, saved):
    expected, parent = COUNTS[arm], plan["parent"]
    require(manifest["config"] == plan["configs"][arm] and manifest["base_model"] == plan["model"] and
        manifest["steps"] == manifest["micro_batches"] == 160 and manifest["epochs_run"] == expected["epochs"] and
        manifest["nonfinite_batches"] == 0 and manifest["empty"] is False and math.isfinite(manifest["final_loss"]), "incomplete/wrong fit")
    corpus = manifest["corpus"]
    require(corpus["sha256"] == plan["material_files"][arm + ".json"] and
        corpus["n_items"] == corpus["n_encoded"] == expected["items"] and corpus["n_skipped_no_target"] == 0 and
        all(manifest["truncation"][key] == 0 for key in
        ("items_truncated", "context_tokens_dropped", "target_tokens_dropped", "items_split")), "corpus/truncation differs")
    require(manifest["tokens"]["total"] == expected["input_per_epoch"] and
        manifest["tokens"]["target"] == expected["target_per_epoch"] and
        manifest["train_tokens_seen"] == expected["input_presentations"] and
        manifest["tokens"]["target"] * manifest["epochs_run"] == expected["target_presentations"], "token accounting differs")
    warm = manifest["warm_start"]
    require(warm["mode"] == "WEIGHT_WARM_START_FRESH_OPTIMIZER" and warm["parent_path"] == parent["parent"] and
        warm["parent_files"] == warm["parent_files_after"] == parent["parent_files"] and
        all(warm[key] is True for key in ("parent_unchanged", "base_frozen", "initialized_loaded_state_check")) and
        warm["phase_seed"] == plan["seed"] and warm["adapter_count"] == 1 and warm["optimizer_initial_state_entries"] == 0 and
        warm["optimizer_state_restored"] is False and warm["optimizer_state_saved"] is False and
        warm["optimizer_initialization"] == "fresh_per_write" and warm["phase_steps"] == 160 and
        warm["parent_cumulative_steps"] == 80 and warm["cumulative_steps"] == 240, "parent/fresh optimizer/history differs")
    old.check_states("replay", before, warm, saved)
    require(before == warm["initialized_state"] and not warm["dtype_conversions"], "original float32 load differs")


def execute_arm(root, pair, plan, arm, effective):
    stage = pair / arm
    stage.mkdir()
    row = paths(pair, plan["parent"]["parent"])[arm]
    before = old.state_inventory(row["parent"])
    active = dict(plan, lease_end=effective)
    receipt = base.supervise(pair, active, stage / "fit-worker", fit_command(root, plan, arm, row["adapter"]))
    memory.successful(receipt)
    adapter = Path(row["adapter"])
    require((adapter / "DONE").is_file(), "missing DONE")
    validate_manifest(plan, arm, base.read(adapter / "train_manifest.json"), before, old.state_inventory(adapter))
    files = trainer._warm_inventory(adapter)
    fit = dict(row, adapter_files=files, parent_files=plan["parent"]["parent_files"], accounting=COUNTS[arm], supervision=receipt)
    old.write(stage / "fit-result.json", fit)
    reductions = {}
    for name, module, count in (("dev", dev, 48), ("exact", exact, 16)):
        require(time.time() < effective - 150, "pair readout budget exhausted")
        readroot = stage / name
        readroot.mkdir()
        readplan = copy.deepcopy(plan["templates"][name])
        readplan.update(adapter=str(adapter), adapter_files=files, device=plan["device"], lease_end=float(effective))
        readplan["identity"] = base.expected_identity(readplan, str(adapter))
        old.seal(readroot, readplan)
        module.verify(readroot)
        (readroot / "run").mkdir()
        command = [sys.executable, "-B", "-m", module.__name__, "_worker", "--root", str(readroot), "--allow-gpu"]
        memory.successful(base.supervise(pair, readplan, readroot / "run/worker", command, readroot / "run/data/calls"))
        reduced = module.reduce(readroot)
        require(reduced["complete"] is True and reduced["counts"]["total"] == count, "incomplete panel is not zero")
        reductions[name] = dict(reduction=reduced, sha256=base.digest(readroot / "reduction.json"))
        require(trainer._warm_inventory(adapter) == files, "readout changed child")
    verify(root)
    result = dict(fit=fit, readouts=reductions)
    old.write(stage / "arm-result.json", result)
    return result


def run(root, allow_gpu=False, clock=None):
    require(allow_gpu, "Main allocation and explicit --allow-gpu required")
    started, monotonic = clock if clock is not None else (time.time(), time.monotonic())
    root = Path(root).resolve(strict=True)
    plan = old.read_plan(root)
    require(os.environ.get("CUDA_VISIBLE_DEVICES") == plan["device"], "wrong sealed device")
    effective = bounds(started, plan["deadline"], plan["real_lease_end"])
    pair = memory.fresh(root / "run")
    pair.mkdir()
    record = dict(seed=plan["seed"], device=plan["device"], controller_pid=os.getpid(), started=started,
        effective_deadline=effective, plan_sha256=base.digest(root / "plan.json"),
        scope="one GPU, sequential pair, whole controller including CPU/gaps/cleanup; Main owns external ledger")
    old.write(pair / "reservation.json", record)
    completed, error = {}, None
    def interrupted(number, frame):
        raise RuntimeError(f"pair interruption/cleanup boundary: {number}")
    handlers = {number: signal.signal(number, interrupted) for number in (signal.SIGALRM, signal.SIGINT, signal.SIGTERM)}
    signal.setitimer(signal.ITIMER_REAL, max(.001, effective - time.time() - 140))
    try:
        verify(root)
        for arm in ARMS:
            require(time.time() < effective - 150, "pair budget exhausted")
            completed[arm] = execute_arm(root, pair, plan, arm, effective)
    except BaseException as failure:
        error = dict(type=type(failure).__name__, message=str(failure))
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        try:
            receipts = [base.read(path) for path in pair.glob("**/supervision.json")]
            require(all(math.isfinite(item["reserved_seconds"]) and item["reserved_seconds"] >= 0 for item in receipts), "invalid cost")
            accounted = all((path.parent / "supervision.json").is_file() for path in pair.glob("**/process.json"))
            released = accounted and base.supervisor.gpu_processes_absent(plan["device"]) is True and all(
                all(item.get(key) is True for key in ("reservation_release_verified", "owned_group_empty", "gpu_processes_absent"))
                for item in receipts)
        except Exception as failure:
            receipts, released = [], False
            error = error or dict(type=type(failure).__name__, message=str(failure))
        ended = time.time()
        terminal = dict(record, status="COMPLETE" if error is None and list(completed) == list(ARMS) and
            len(receipts) == 6 and all(item.get("ok") is True for item in receipts) and released and ended <= effective
            else "FAILED_PARTIAL_NO_RETRY", arms=completed, error=error, ended=ended,
            reserved_seconds=time.monotonic()-monotonic, worker_reserved_seconds=sum(item["reserved_seconds"] for item in receipts),
            release_verified=released, deadline_met=ended <= effective, progression_owner="Main", outcome_selective_skips=False,
            claim=CLAIM, monetary_cost=None)
        old.write(pair / "terminal.json", terminal)
        for number, handler in handlers.items():
            signal.signal(number, handler)
    require(terminal["status"] == "COMPLETE", "partial pair; preserve artifacts; no retry/resume")
    return terminal


def main():
    clock = time.time(), time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "run", "status"))
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--helper", default="/tmp/astra_memory_only_20260912.py")
    parser.add_argument("--fading-helper", default="/tmp/astra_fading_sentinel_20260912.py")
    parser.add_argument("--runroot", required=True)
    parser.add_argument("--parentroot")
    parser.add_argument("--seed", type=int, choices=(0, 1, 2))
    parser.add_argument("--device")
    parser.add_argument("--deadline", type=float)
    parser.add_argument("--lease-end", type=float)
    parser.add_argument("--allow-gpu", action="store_true")
    args = parser.parse_args()
    bind(args.source_root, args.helper, args.fading_helper)
    if args.stage == "prepare":
        require(all(getattr(args, key) is not None for key in ("parentroot", "seed", "device", "deadline", "lease_end")), "missing prepare inputs")
        result = prepare(args.parentroot, args.seed, args.device, args.deadline, args.lease_end, args.runroot)
    elif args.stage == "run":
        result = run(args.runroot, args.allow_gpu, clock)
    else:
        root = Path(args.runroot)
        old.read_plan(root)
        result = base.read(root / "run/terminal.json") if (root / "run/terminal.json").is_file() else dict(
            status="NONTERMINAL_OR_ABANDONED" if (root / "run").exists() else "NOT_STARTED")
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
