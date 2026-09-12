"""Root0 only: original-parent SINGLE_VIEW then FOUR_VIEW. Main allocates/launches."""
from __future__ import annotations

import argparse
import copy
from dataclasses import asdict
import hashlib
import importlib.util
import math
import os
from pathlib import Path
import signal
import sys
import time
import json


SOURCE_ID = "dc2e9a3c11ccd9a3f10ea28513723bbfb8420247"
MEMORY_SHA = "ac7a110bc74724fc592407ced854ad162da275d3de9d9eeeb40c19788416afdb"
MATERIAL_SHA = "9c6c4bcf00f19e02a62b1939d8f669a16475483b4b74d8718f884830d3118a9c"
PREPARER_SHA = "d4df1ac1ef1a600d2d4e712b9522b50563e080a640dbe9fed176211e9941f6df"
ARMS = ("SINGLE_VIEW", "FOUR_VIEW")
SECONDS = 1500
CLAIM = "AUTHORED_VARIED_PHRASING_REPLAY_NOT_CHILD_EXPERIENCE_NOT_BRAIN_PROOF"
COUNTS = {arm: dict(items=128, epochs=10, steps=320, cumulative_steps=400,
    input_per_epoch=inputs, context_per_epoch=inputs-1000, target_per_epoch=1000,
    input_presentations=inputs*10, context_presentations=(inputs-1000)*10, target_presentations=10000,
    presentations_per_source=40) for arm, inputs in (("SINGLE_VIEW", 6616), ("FOUR_VIEW", 6712))}
PROGRESSION = dict(owner="Main", decide_only_after_both_technical_complete=True,
    qualifying_arm="FOUR_VIEW", dev_memory_min=15, exact_memory_min=15, dev_habit_min=30, dev_act_min=31,
    eligible_next_seeds=[1, 2], both_seeds_required_if_progressing=True, single_scores_irrelevant=True,
    automatic_progression=False, gate_evaluated_by_wrapper=False)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def bind(source, helper, fading_helper):
    global memory, old, base, trainer, dev, exact, varied
    source = Path(source).resolve(strict=True)
    require(source.name == SOURCE_ID, "use the immutable dc2e9a3c source root")
    helper = Path(helper).resolve(strict=True)
    payload = helper.read_bytes()
    require(hashlib.sha256(payload).hexdigest() == MEMORY_SHA, "accepted memory helper changed")
    spec = importlib.util.spec_from_file_location("varied_pair_memory_helper", helper)
    memory = importlib.util.module_from_spec(spec)
    exec(compile(payload, str(helper), "exec"), memory.__dict__)
    memory.bind(source, fading_helper)
    old, base, trainer, dev, exact = memory.old, memory.base, memory.trainer, memory.dev, memory.exact
    from organism_v6 import varied_memory_replay_corpus as varied
    require(Path(varied.__file__).resolve().parent.parent == source == base.REPO.resolve(), "wrong imported/CWD source")


def sources():
    return dict(memory.sources(), **varied.source_hashes(), varied_pair_sidecar=base.digest(__file__))


def config(model):
    return dict(memory.config(model, 0, 10), overflow="truncate")


def bounds(started, deadline, lease_end):
    require(all(type(value) in (int, float) and math.isfinite(value) for value in (started, deadline, lease_end)), "nonfinite bounds")
    require(base.WORKER_SECONDS == 600 and base.CLEANUP_RESERVE == 140, "native worker/cleanup bounds changed")
    effective = min(started + SECONDS, deadline, lease_end - 10)
    require(effective == started + SECONDS and effective - time.time() > 150, "full1500s pair window required")
    return effective


def budget(effective):
    require(time.time() < effective - 150, "less than150s left; no future phase")


def inspect_material(materialroot):
    materialroot = Path(materialroot).resolve(strict=True)
    require(base.digest(materialroot / "manifest.json") == MATERIAL_SHA, "not pinned actual native material")
    varied.verify(materialroot)
    manifest = base.read(materialroot / "manifest.json")
    receipt_path = materialroot.parent / "native_prepare.json"
    receipt = base.read(receipt_path)
    parentroot = Path(manifest["original_teach_path"]).parent
    original = old.read_plan(parentroot)
    require(receipt["status"] == "ACTUAL_NATIVE_TOKENIZER_AUDIT_PASS_NO_FIT" and
        receipt["source_commit"] == SOURCE_ID and receipt["source_root"] == str(base.REPO) and
        receipt["material"] == str(materialroot) and receipt["material_manifest_sha256"] == MATERIAL_SHA and
        receipt["preparation_script_sha256"] == PREPARER_SHA and receipt["source_hashes"] == manifest["source_hashes"] == varied.source_hashes() and
        receipt["original_plan_sha256"] == base.digest(parentroot / "plan.json") == memory.PINS["0"][0] and
        receipt["original_teach_sha256"] == manifest["original_teach_sha256"] == varied.ORIGINAL_TEACH_SHA256 and
        receipt["model"] == original["model"] and receipt["model_files"] == original["model_files"] and
        receipt["tokenizer_matches_original_model_files"] is True and receipt["no_model_forward_or_training"] is True and
        receipt["origin_authenticated"] is False and receipt["origin"] == "UNRESOLVED_LOCAL_HASHES_ONLY", "native preparation/parent/base/source receipt differs")
    require(manifest["seeds"] == [0, 1, 2] and manifest["recipe"] == varied.RECIPE and manifest["claim"] == CLAIM,
        "prepared recipe/seed schedule differs")
    audit = base.read(materialroot / "token_audit.json")
    require(audit["tokenizer_class"] == receipt["native_tokenizer_class"] and audit["compute_matched"] is False,
        "native tokenizer/cost claim differs")
    for arm in ARMS:
        expected = COUNTS[arm]
        totals = dict(input_tokens=expected["input_presentations"], context_tokens=expected["context_presentations"], target_tokens=10000)
        require(manifest["token_totals"][arm] == receipt["token_totals"][arm] == audit["arms"][arm]["ten_epochs"] == totals and
            audit["arms"][arm]["per_epoch"] == {key: value // 10 for key, value in totals.items()}, "native counts differ")
    return dict(materialroot=str(materialroot), material_files=base.tree_hashes(materialroot),
        native_prepare_path=str(receipt_path), native_prepare_sha256=base.digest(receipt_path),
        parentroot=str(parentroot), model=receipt["model"], model_files=receipt["model_files"])


def paths(root, parent):
    return {arm: dict(parent=parent, adapter=str(root / "run" / arm / "adapter")) for arm in ARMS}


def fit_command(plan, arm, adapter):
    require(arm in ARMS, "fixed arms only")
    command = [sys.executable, "-B", "-m", "organism_v6.train_adapter_v3", "--corpus",
        str(Path(plan["materialroot"]) / (arm + ".json")), "--out", str(adapter), "--init-adapter", plan["parent"]["parent"],
        "--model", plan["model"], "--rank", "8", "--alpha", "16", "--dropout", "0.05", "--lr", "0.0003",
        "--epochs", "10", "--batch-size", "4", "--grad-accum", "1", "--seed", "0", "--no-pack", "--max-len", "512", "--overflow", "truncate"]
    require(asdict(trainer.config_from_args(trainer.build_parser().parse_args(command[4:]))) == plan["config"], "effective V3 CLI config differs")
    return command


def prepare(materialroot, runroot, device, deadline, lease_end):
    bounds(time.time(), deadline, lease_end)
    memory.branches([device] * 3)
    bound = inspect_material(materialroot)
    root = memory.fresh(runroot, (bound["materialroot"], bound["parentroot"], bound["model"], base.REPO))
    require(root.parent == Path(bound["materialroot"]).parent, "fresh fits root must be beside immutable material")
    require(base.model_hashes(bound["model"]) == bound["model_files"], "actual base bytes changed")
    parent = memory.parent_record(Path(bound["parentroot"]), 0, bound["model"], bound["model_files"])
    before = old.state_inventory(parent["parent"])
    tokenizer = base.native_tokenizer(bound["model"])
    candidate = base.read(Path(bound["materialroot"]) / "candidate.json")
    exported = varied.export_native(candidate, base.read(Path(bound["parentroot"]) / "teach.json"), tokenizer, (0, 1, 2))
    require(exported["audit"] == base.read(Path(bound["materialroot"]) / "token_audit.json") and all(
        exported["corpora"][arm] == base.read(Path(bound["materialroot"]) / (arm + ".json")) for arm in ARMS),
        "actual native V3 material/order re-audit differs")
    memory.subset(base.read(Path(bound["parentroot"]) / "teach.json"), tokenizer)
    templates = {name: memory.template(module, bound["model"], bound["model_files"], tokenizer, device, lease_end)
        for name, module in (("dev", dev), ("exact", exact))}
    require(all(templates["dev"][key] == parent["readout"][key] for key in ("cases", "requests", "native_inputs")), "original dev48 interface differs")
    plan = dict(schema=1, root=str(root), **bound, source_root=str(base.REPO), source_hashes=sources(),
        parent=parent, parent_state=before, seed=0, device=device, config=config(bound["model"]),
        arm_order=list(ARMS), accounting=COUNTS, templates=templates, deadline=float(deadline), real_lease_end=float(lease_end),
        pair_seconds=SECONDS, cleanup_seconds=140, aggregate_a40_seconds=5400, campaign_pair_ceiling=3,
        progression=PROGRESSION, outcome_selective_skips=False, reduce_only_after_both_captures=True,
        calls_per_arm=64, total_calls=128, new_off_calls=0, new_hf_calls=0, confirmation_calls=0,
        claim=CLAIM, origin="UNRESOLVED_LOCAL_HASHES_ONLY", input_compute_matched=False,
        comparison="paired targets/exposure; different prefix costs; differs from SEQ107 batch layout, NOT dose-only")
    for arm, row in paths(root, parent["parent"]).items():
        fit_command(plan, arm, row["adapter"])
        trainer._warm_parent(row["parent"], row["adapter"], trainer.TrainConfig(**plan["config"]))
    require(inspect_material(materialroot) == bound and old.state_inventory(parent["parent"]) == before and
        trainer._warm_inventory(parent["parent"]) == parent["parent_files"] and plan["source_hashes"] == sources() and
        base.model_hashes(bound["model"]) == bound["model_files"], "inputs changed during CPU prepare")
    root.mkdir()
    old.seal(root, plan)
    return dict(status="PREPARED_ROOT0_NOT_LAUNCHED", root=str(root), plan_sha256=base.digest(root / "plan.json"))


def verify(root):
    root = Path(root)
    plan = old.read_plan(root)
    require(plan["schema"] == 1 and plan["root"] == str(root) and plan["source_root"] == str(base.REPO) and
        plan["source_hashes"] == sources() and type(plan["seed"]) is int and plan["seed"] == 0, "root0/source changed")
    require(plan["config"] == config(plan["model"]) and plan["accounting"] == COUNTS and plan["arm_order"] == list(ARMS) and
        plan["pair_seconds"] == SECONDS and plan["cleanup_seconds"] == 140 and plan["aggregate_a40_seconds"] == 5400 and
        plan["campaign_pair_ceiling"] == 3 and plan["progression"] == PROGRESSION and plan["outcome_selective_skips"] is False and
        plan["reduce_only_after_both_captures"] is True and plan["calls_per_arm"] == 64 and plan["total_calls"] == 128 and
        all(plan[key] == 0 for key in ("new_off_calls", "new_hf_calls", "confirmation_calls")) and plan["claim"] == CLAIM and
        plan["origin"] == "UNRESOLVED_LOCAL_HASHES_ONLY" and plan["input_compute_matched"] is False, "fixed pair contract changed")
    memory.branches([plan["device"]] * 3)
    require(all(plan[key] == value for key, value in inspect_material(plan["materialroot"]).items()) and
        root.parent == Path(plan["materialroot"]).parent and base.model_hashes(plan["model"]) == plan["model_files"], "material/base/native receipt changed")
    parent = plan["parent"]
    require(parent["parent"] == str(Path(plan["parentroot"]) / "fit_teach/adapter") and
        trainer._warm_inventory(parent["parent"]) == parent["parent_files"] and old.state_inventory(parent["parent"]) == plan["parent_state"] and
        all(base.digest(path) == checksum for path, checksum in parent["provenance"].items()) and
        base.tree_hashes(Path(plan["parentroot"]) / "readouts/teach") == parent["readout_files"], "original parent/provenance/state changed")
    for name, module, count in (("dev", dev, 48), ("exact", exact, 16)):
        template = plan["templates"][name]
        require(template["cases"] == module.selected_cases() and len(template["cases"]) == count and
            template["requests"] == module.requests(template["cases"]) and template["source_hashes"] == module.sources() and
            template["model"] == plan["model"] and template["model_files"] == plan["model_files"] and
            template["adapter"] is None and template["adapter_files"] == {} and template["worker_seconds"] == 600 and
            template["identity"] == base.expected_identity(template, None), "fixed readout template changed")
    require(all(plan["templates"]["dev"][key] == parent["readout"][key] for key in ("cases", "requests", "native_inputs")), "inherited dev inputs changed")
    return plan


def validate_manifest(plan, arm, manifest, before, saved):
    expected, parent = COUNTS[arm], plan["parent"]
    require(manifest["config"] == plan["config"] and manifest["base_model"] == plan["model"] and
        manifest["steps"] == manifest["micro_batches"] == 320 and manifest["epochs_run"] == 10 and manifest["nonfinite_batches"] == 0 and
        manifest["empty"] is False and math.isfinite(manifest["final_loss"]), "incomplete/nonfinite/wrong fit")
    actual = manifest["corpus"]
    require(actual["sha256"] == plan["material_files"][arm + ".json"] and actual["n_items"] == actual["n_encoded"] == 128 and
        actual["n_skipped_no_target"] == 0 and all(manifest["truncation"][key] == 0 for key in
        ("items_truncated", "context_tokens_dropped", "target_tokens_dropped", "items_split")), "material/drop/truncation changed")
    require(manifest["tokens"]["total"] == expected["input_per_epoch"] and manifest["tokens"]["context"] == expected["context_per_epoch"] and
        manifest["tokens"]["target"] == 1000 and manifest["train_tokens_seen"] == expected["input_presentations"] and
        manifest["tokens"]["target"] * manifest["epochs_run"] == 10000, "actual token accounting differs")
    warm = manifest["warm_start"]
    require(warm["mode"] == "WEIGHT_WARM_START_FRESH_OPTIMIZER" and warm["parent_path"] == parent["parent"] and
        warm["parent_files"] == warm["parent_files_after"] == parent["parent_files"] and
        all(warm[key] is True for key in ("parent_unchanged", "base_frozen", "initialized_loaded_state_check")) and
        warm["phase_seed"] == 0 and warm["adapter_count"] == 1 and warm["optimizer_initial_state_entries"] == 0 and
        warm["optimizer_state_restored"] is False and warm["optimizer_state_saved"] is False and warm["optimizer_initialization"] == "fresh_per_write" and
        warm["phase_steps"] == 320 and warm["parent_cumulative_steps"] == 80 and warm["cumulative_steps"] == 400,
        "original parent/fresh optimizer/history changed")
    old.check_states("varied_replay", before, warm, saved)
    require(before == plan["parent_state"] == warm["initialized_state"] and not warm["dtype_conversions"], "initialized original state differs")


def verify_fit(plan, stage, arm):
    adapter = stage / "adapter"
    require((adapter / "DONE").is_file(), "missing child DONE")
    validate_manifest(plan, arm, base.read(adapter / "train_manifest.json"), plan["parent_state"], old.state_inventory(adapter))
    require(trainer._warm_inventory(plan["parent"]["parent"]) == plan["parent"]["parent_files"] and
        old.state_inventory(plan["parent"]["parent"]) == plan["parent_state"], "parent changed during fit")
    return dict(parent=plan["parent"]["parent"], parent_files=plan["parent"]["parent_files"], adapter=str(adapter),
        adapter_files=trainer._warm_inventory(adapter), manifest_sha256=base.digest(adapter / "train_manifest.json"), accounting=COUNTS[arm])


def capture_receipt(readroot, template):
    data = readroot / "run/data"
    require(base.read(data / "manifest.json")["files"] == base.tree_hashes(data, ("manifest.json",)), "raw capture hash inventory changed")
    expected = {request["call_id"] + suffix for request in template["requests"] for suffix in (".request.json", ".response.json")}
    require({path.name for path in (data / "calls").iterdir()} == expected, "missing/extra raw response pairs, not a scientific zero")
    return dict(plan_sha256=base.digest(readroot / "plan.json"), capture_sha256=base.digest(data / "manifest.json"),
        pairs=len(template["requests"]), status="CAPTURED_NOT_REDUCED")


def execute_arm(root, pair, plan, arm, effective):
    budget(effective)
    stage = memory.fresh(pair / arm)
    stage.mkdir()
    adapter = stage / "adapter"
    receipt = base.supervise(pair, dict(plan, lease_end=effective), stage / "fit-worker", fit_command(plan, arm, adapter))
    memory.successful(receipt)
    fit = dict(verify_fit(plan, stage, arm), supervision=receipt)
    old.write(stage / "fit-result.json", fit)
    captures = {}
    for name, module in (("dev", dev), ("exact", exact)):
        budget(effective)
        readroot = stage / name
        readroot.mkdir()
        readplan = copy.deepcopy(plan["templates"][name])
        readplan.update(adapter=str(adapter), adapter_files=fit["adapter_files"], device=plan["device"], lease_end=float(effective))
        readplan["identity"] = base.expected_identity(readplan, str(adapter))
        old.seal(readroot, readplan)
        module.verify(readroot)
        (readroot / "run").mkdir()
        command = [sys.executable, "-B", "-m", module.__name__, "_worker", "--root", str(readroot), "--allow-gpu"]
        memory.successful(base.supervise(pair, readplan, readroot / "run/worker", command, readroot / "run/data/calls"))
        captures[name] = capture_receipt(readroot, readplan)
        require(trainer._warm_inventory(adapter) == fit["adapter_files"], "readout changed child")
    verify(root)
    result = dict(fit=fit, captures=captures)
    old.write(stage / "capture-result.json", result)
    return result


def reduce_pair(root, plan, captured, effective):
    require(set(captured) == set(ARMS), "both arms must capture before any reduction")
    for arm in ARMS:
        for name in ("dev", "exact"):
            require(capture_receipt(root / "run" / arm / name, plan["templates"][name]) == captured[arm]["captures"][name], "capture changed before pair reduction")
    results = {}
    for arm in ARMS:
        reductions = {}
        for name, module, count in (("dev", dev, 48), ("exact", exact, 16)):
            budget(effective)
            readroot = root / "run" / arm / name
            reduced = module.reduce(readroot)
            require(reduced["complete"] is True and reduced["counts"]["total"] == count, "incomplete panel is not zero")
            reductions[name] = dict(reduction=reduced, sha256=base.digest(readroot / "reduction.json"))
        results[arm] = dict(captured[arm], readouts=reductions)
        old.write(root / "run" / arm / "arm-result.json", results[arm])
    return results


def run(root, allow_gpu=False, clock=None):
    require(allow_gpu, "Main allocation and explicit --allow-gpu required")
    started, monotonic = clock if clock is not None else (time.time(), time.monotonic())
    root = Path(root).resolve(strict=True)
    plan = old.read_plan(root)
    require(type(plan["seed"]) is int and plan["seed"] == 0 and os.environ.get("CUDA_VISIBLE_DEVICES") == plan["device"], "root0/inherited Main device differs")
    effective = bounds(started, plan["deadline"], plan["real_lease_end"])
    pair = memory.fresh(root / "run")
    pair.mkdir()
    record = dict(seed=0, device=plan["device"], controller_pid=os.getpid(), started=started, effective_deadline=effective,
        real_lease_end=plan["real_lease_end"], plan_sha256=base.digest(root / "plan.json"),
        scope="one GPU continuously reserved across both arms, CPU/gaps/cleanup; Main full vacancy check before launch and ledger")
    old.write(pair / "reservation.json", record)
    captured, completed, error = {}, {}, None
    def interrupted(number, frame):
        raise RuntimeError(f"pair interruption/cleanup boundary: {number}")
    handlers = {number: signal.signal(number, interrupted) for number in (signal.SIGALRM, signal.SIGINT, signal.SIGTERM)}
    signal.setitimer(signal.ITIMER_REAL, max(.001, effective - time.time() - 140))
    try:
        verify(root)
        for arm in ARMS:
            budget(effective)
            captured[arm] = execute_arm(root, pair, plan, arm, effective)
        completed = reduce_pair(root, plan, captured, effective)
        verify(root)
        for arm in ARMS:
            require(verify_fit(plan, pair / arm, arm) == {key: value for key, value in completed[arm]["fit"].items() if key != "supervision"}, "completed child changed")
    except BaseException as failure:
        error = dict(type=type(failure).__name__, message=str(failure))
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        accounted = False
        try:
            receipts = [base.read(path) for path in pair.glob("**/supervision.json")]
            require(all(math.isfinite(item["reserved_seconds"]) and item["reserved_seconds"] >= 0 for item in receipts), "invalid worker cost")
            accounted = all((path.parent / "supervision.json").is_file() for path in pair.glob("**/process.json"))
            released = accounted and base.supervisor.gpu_processes_absent(plan["device"]) is True and all(
                all(item.get(key) is True for key in ("reservation_release_verified", "owned_group_empty", "gpu_processes_absent")) for item in receipts)
        except Exception as failure:
            receipts, released = [], False
            error = error or dict(type=type(failure).__name__, message=str(failure))
        ended = time.time()
        terminal = dict(record, status="COMPLETE" if error is None and set(completed) == set(ARMS) and len(receipts) == 6 and
            all(item.get("ok") is True and item.get("returncode") == 0 for item in receipts) and released and ended <= effective
            else "FAILED_PARTIAL_NO_RETRY", arms=completed, captured=captured, error=error, ended=ended,
            reserved_seconds=time.monotonic()-monotonic, worker_reserved_seconds=sum(item["reserved_seconds"] for item in receipts),
            release_verified=released, worker_accounting_complete=accounted, deadline_met=ended <= effective,
            progression_owner="Main", gate_evaluated=False, automatic_progression=False, outcome_selective_skips=False,
            claim=CLAIM, origin="UNRESOLVED_LOCAL_HASHES_ONLY", monetary_cost=None)
        old.write(pair / "terminal.json", terminal)
        for number, handler in handlers.items():
            signal.signal(number, handler)
    require(terminal["status"] == "COMPLETE", "partial pair; preserve artifacts; no retry/resume")
    return terminal


def main():
    clock = time.time(), time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "verify", "run", "status"))
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--helper", default="/tmp/astra_memory_only_20260912.py")
    parser.add_argument("--fading-helper", default="/tmp/astra_fading_sentinel_20260912.py")
    parser.add_argument("--runroot", required=True)
    parser.add_argument("--materialroot")
    parser.add_argument("--device")
    parser.add_argument("--deadline", type=float)
    parser.add_argument("--lease-end", type=float)
    parser.add_argument("--allow-gpu", action="store_true")
    args = parser.parse_args()
    bind(args.source_root, args.helper, args.fading_helper)
    root = Path(args.runroot).expanduser().absolute()
    if args.stage == "prepare":
        require(all(getattr(args, key) is not None for key in ("materialroot", "device", "deadline", "lease_end")), "missing prepare inputs")
        result = prepare(args.materialroot, root, args.device, args.deadline, args.lease_end)
    elif args.stage == "run":
        result = run(root, args.allow_gpu, clock)
    elif args.stage == "verify":
        verify(root)
        result = dict(status="VERIFIED_PLAN_NOT_LAUNCH_AUTHORITY", plan_sha256=base.digest(root / "plan.json"))
    else:
        old.read_plan(root)
        terminal = root / "run/terminal.json"
        result = base.read(terminal) if terminal.is_file() else dict(status="NONTERMINAL_OR_ABANDONED" if (root / "run").exists() else "NOT_STARTED")
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
