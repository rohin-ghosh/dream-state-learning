"""Six fixed one-phase parent-seed plasticity branches; Main alone launches."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import signal
import sys
import time


HELPER_SHA = "7b0686de7b66fcad27a665c0b30054a893af3ee33d053c26fae903fc1ed8af20"
PINS = {
    "1": ("f2aaa20ab53b7cd3221580f3098da68f0381bd6a120967b6cfa085eedb769252",
          "248fee8d701b435c334aafd2551b93ef6da25de137ac71510fa5bb5c49129335",
          "f5cc61263806bff26d7b77ca267b70b21507bf2e1feeea78dc4eb510675a7e7a"),
    "2": ("54e44fc9e7193405b85b4a49b44c73ba50e3b075832b406a9538df77d0ad0fae",
          "fc5f2337f981ce71fe43a931bcff530019b843936f69104d6883cbb00001599c",
          "eea6c81b77aa745e440a68503a9984d52264b8b02932c512baa27dda368ba825"),
}
RATES = ("0", "3e-5", "1e-4")
BRANCHES = {f"seed{seed}-rate-{rate}": dict(parent_seed=seed, rate=rate, device=str(index))
            for index, (seed, rate) in enumerate((seed, rate) for seed in (1, 2) for rate in RATES)}
SECONDS = 600
PHASE = "continuation-phase-01"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def bind(source, helper):
    global old, base, trainer, material, readout
    helper = Path(helper).resolve(strict=True)
    require(hashlib.sha256(helper.read_bytes()).hexdigest() == HELPER_SHA, "sentinel helper changed")
    spec = importlib.util.spec_from_file_location("fading_replication_helper", helper)
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    old.bind(source)
    base, trainer, material, readout = old.base, old.trainer, old.material, old.readout


def sources():
    return dict(old.sources(), replication_script=base.digest(__file__))


def bounds(started, deadline, lease_end):
    require(all(math.isfinite(value) for value in (started, deadline, lease_end)), "nonfinite bounds")
    require(base.CLEANUP_RESERVE == 140 and base.WORKER_SECONDS == 600, "native bounds changed")
    effective = min(started + SECONDS, deadline, lease_end - 10)
    require(effective - started > 150, "insufficient cleanup window")
    return effective


def fresh(root, protected):
    root = Path(root).expanduser().absolute()
    require(not root.exists() and not root.is_symlink(), "fresh runroot required; no retry/resume")
    require(not any(path.is_symlink() for path in root.parents), "symlink output path")
    for source in protected:
        source = Path(source).resolve()
        require(root != source and root not in source.parents and source not in root.parents, "output overlaps input")
    return root


def audit_inputs(readroot, plan, tokenizer):
    cases = readout.selected_cases()
    require(plan["cases"] == cases and plan["requests"] == readout.requests(cases), "original cases/requests differ")
    require(plan["native_inputs"] == readout.native_inputs(tokenizer, plan["requests"]), "original native inputs differ")
    calls = readroot / "run" / "data" / "calls"
    require(len(list(calls.glob("*.request.json"))) == len(list(calls.glob("*.response.json"))) == 48,
            "original native response completeness required")
    for request, native in zip(plan["requests"], plan["native_inputs"], strict=True):
        sent = base.read(calls / (request["call_id"] + ".request.json"))
        received = base.read(calls / (request["call_id"] + ".response.json"))
        require(sent["request"] == request and sent["identity"] == plan["identity"] and
                sent["prompt_sha256"] == base.value_hash(request["prompt"]), "original request changed")
        response = received["response"]
        require(received["response_sha256"] == base.value_hash(response), "original response hash differs")
        base.validate_response(request, response)
        require(all(response[key] == native[key] for key in ("rendered_prompt", "prompt_token_ids")),
                "original response input mismatch")
    base.audit_native_calls(tokenizer, readroot / "run" / "data")
    require(base.read(readroot / "run/data/backend.cleanup.json")["closed"] is True, "original backend cleanup missing")


def parent_record(root, seed, model, model_files, tokenizer):
    paths = [root / "plan.json", root / "fit_teach/verified.json", root / "readouts/teach/plan.json"]
    require(tuple(base.digest(path) for path in paths) == PINS[str(seed)], "not pinned original SEQ099 parent")
    original = old.read_plan(root)
    fit = base.read(paths[1])
    prior = old.read_plan(root / "readouts/teach")
    parent = root / "fit_teach/adapter"
    config = old.config(model, "0")
    config.update(lr=3e-4, seed=seed)
    require(original["config"] == config and original["replication"]["seed"] == seed and
            original["model"] == model and original["model_files"] == model_files, "parent recipe/base mismatch")
    files = trainer._warm_inventory(parent)
    require(fit["seed"] == seed and fit["arm"] == "teach" and fit["adapter"] == str(parent) and
            fit["plan_sha256"] == PINS[str(seed)][0] and fit["steps"] == 80 and
            fit["status"] == "FIT_COMPLETE_PENDING_PAIRED_READOUT" and fit["adapter_files"] == files,
            "parent fit unverified/changed")
    manifest = base.read(parent / "train_manifest.json")
    require((parent / "DONE").is_file() and manifest["config"] == config and manifest["steps"] == 80 and
            "warm_start" not in manifest, "not original freshly fitted parent")
    for worker in (root / "fit_teach/worker", root / "readouts/teach/run/worker"):
        receipt = base.read(worker / "supervision.json")
        require(all(receipt[key] is True for key in ("ok", "reservation_release_verified", "owned_group_empty", "gpu_processes_absent")),
                "original supervised cleanup unverified")
    require(base.digest(root / "fit_teach/worker/supervision.json") == fit["supervision_sha256"], "fit supervision changed")
    require(prior["adapter"] == str(parent) and prior["adapter_files"] == files and
            prior["model"] == model and prior["model_files"] == model_files and
            prior["identity"] == base.expected_identity(prior, str(parent)), "original readout identity mismatch")
    audit_inputs(root / "readouts/teach", prior, tokenizer)
    trainer._warm_parent(parent, root.parent / "unused-validation-only", trainer.TrainConfig(**old.config(model, "0")))
    provenance = {str(path): base.digest(path) for path in paths + [root / "fit_teach/worker/supervision.json"]}
    return dict(parent=str(parent), parent_files=files, provenance=provenance, readout=prior,
                readout_files=base.tree_hashes(root / "readouts/teach"))


def prepare(runroot, materialroot, parentsroot, deadline, lease_end):
    require(deadline > time.time() + SECONDS and lease_end >= deadline + 10, "future full branch window required")
    bounds(time.time(), deadline, lease_end)
    parentsroot, materialroot = Path(parentsroot).resolve(strict=True), Path(materialroot).resolve(strict=True)
    seed = old.read_plan(parentsroot / "seed1")
    model = seed["model"]
    root = fresh(runroot, (parentsroot, materialroot, model, base.REPO))
    material.verify(materialroot)
    manifest = base.read(materialroot / "manifest.json")
    require(manifest["status"] == "NATIVE_V3_TOKEN_AUDIT_COMPLETE" and manifest["native_token_audit"] is True and
            manifest["tokenizer_injected"] is False, "existing actual native material required")
    require(manifest["phase_corpora"] == {phase: phase + ".json" for phase in old.PHASES}, "material membership changed")
    model_files = base.model_hashes(model)
    require(manifest["model"] == model and manifest["model_files"] == model_files, "material/base mismatch")
    tokenizer = base.native_tokenizer(model)
    parents = {str(seed): parent_record(parentsroot / f"seed{seed}", seed, model, model_files, tokenizer) for seed in (1, 2)}
    require(all(parents["1"]["readout"][key] == parents["2"]["readout"][key]
                for key in ("cases", "requests", "native_inputs")), "parent readout inputs differ")
    plan = dict(schema=1, source_root=str(base.REPO), source_label="3a12807f; bound by source hashes, not Git lookup",
                source_hashes=sources(), model=model, model_files=model_files, materialroot=str(materialroot),
                material_files=base.tree_hashes(materialroot), parents=parents, branches=BRANCHES,
                rates={rate: old.config(model, rate) for rate in RATES}, phase=PHASE, optimizer_seed=0,
                deadline=float(deadline), real_lease_end=float(lease_end), branch_seconds=SECONDS,
                cleanup_seconds=140, claim=old.CLAIM, counts_used_for_selection=False,
                budget="Main declares 150 A40min total cap: prior57.68 + six10min branches + audit margin",
                interpretation="parent seed replication only; continuation optimizer seed fixed0; no independent-probe inference")
    base.fresh_directory(root, model)
    old.seal(root, plan)
    return dict(root=str(root), status="PREPARED_NOT_LAUNCHED", branches=BRANCHES)


def verify(root):
    plan = old.read_plan(root)
    require(plan["schema"] == 1 and plan["source_root"] == str(base.REPO) and plan["source_hashes"] == sources(), "source/contract changed")
    require(plan["branches"] == BRANCHES and plan["phase"] == PHASE and plan["optimizer_seed"] == 0 and
            plan["branch_seconds"] == 600 and plan["cleanup_seconds"] == 140 and plan["claim"] == old.CLAIM and
            plan["counts_used_for_selection"] is False and
            plan["rates"] == {rate: old.config(plan["model"], rate) for rate in RATES}, "fixed recipe changed")
    require(base.model_hashes(plan["model"]) == plan["model_files"], "base changed")
    material.verify(plan["materialroot"])
    require(base.tree_hashes(plan["materialroot"]) == plan["material_files"], "material changed")
    for seed, parent in plan["parents"].items():
        require(trainer._warm_inventory(parent["parent"]) == parent["parent_files"], "original parent changed")
        require(all(base.digest(path) == digest for path, digest in parent["provenance"].items()), "parent provenance changed")
        seedroot = Path(parent["parent"]).parent.parent
        require(base.digest(seedroot / "plan.json") == PINS[seed][0] and
                base.tree_hashes(seedroot / "readouts/teach") == parent["readout_files"], "original readout changed")
    return plan


def readplan_for(plan, branch, row, fit, effective):
    result = copy.deepcopy(plan["parents"][str(branch["parent_seed"])]["readout"])
    result.update(adapter=row["adapter"], adapter_files=fit["adapter_files"], device=branch["device"],
                  lease_end=float(effective), source_hashes=readout.sources())
    result["identity"] = base.expected_identity(result, row["adapter"])
    return result


def execute(root, stage, plan, branch, effective):
    parent = plan["parents"][str(branch["parent_seed"])]
    row = dict(phase=PHASE, parent=parent["parent"], adapter=str(stage / "adapter"), stage=str(stage))
    before = old.state_inventory(row["parent"])
    active = dict(plan, device=branch["device"], lease_end=effective)
    old.write(stage / "phase.json", dict(row, config=plan["rates"][branch["rate"]], effective_deadline=effective))
    fit_cost = base.supervise(stage, active, stage / "fit-worker", old.fit_command(plan, branch["rate"], row))
    fit = old.verify_fit(plan, branch["rate"], row, parent["parent_files"], before)
    old.write(stage / "fit-result.json", fit)
    readroot = stage / "readout"
    readroot.mkdir()
    readplan = readplan_for(plan, branch, row, fit, effective)
    old.seal(readroot, readplan)
    readout.verify(readroot)
    (readroot / "run").mkdir()
    command = [sys.executable, "-B", "-m", "organism_v6.fundamental_teaching_readout", "_worker",
               "--root", str(readroot), "--allow-gpu"]
    read_cost = base.supervise(stage, readplan, readroot / "run/worker", command, readroot / "run/data/calls")
    reduced = readout.reduce(readroot)
    require(reduced["complete"] is True and reduced["counts"]["total"] == 48, "incomplete readout is not zero")
    require(trainer._warm_inventory(row["adapter"]) == fit["adapter_files"], "readout changed adapter")
    verify(root)
    return dict(fit=fit, fit_cost=fit_cost, readout_cost=read_cost, reduction_sha256=base.digest(readroot / "reduction.json"))


def run(root, name, allow_gpu=False, clock=None):
    require(allow_gpu and name in BRANCHES, "explicit Main allocation and --allow-gpu required")
    branch = BRANCHES[name]
    require(os.environ.get("CUDA_VISIBLE_DEVICES") == branch["device"], "wrong reserved device")
    started, monotonic = clock if clock is not None else (time.time(), time.monotonic())
    root = Path(root).resolve(strict=True)
    plan = old.read_plan(root)
    effective = bounds(started, plan["deadline"], plan["real_lease_end"])
    stage = fresh(root / name, (plan["model"], plan["materialroot"]))
    stage.mkdir()
    record = dict(branch=branch, controller_pid=os.getpid(), started=started, effective_deadline=effective,
                  real_lease_end=plan["real_lease_end"], plan_sha256=base.digest(root / "plan.json"),
                  reservation="entire controller/CPU/gaps; Main full vacancy check before spawn; no inner full check_free")
    old.write(stage / "reservation.json", record)
    result, error = None, None
    def interrupted(number, frame):
        raise RuntimeError(f"branch interrupted/cleanup boundary: {number}")
    handlers = {number: signal.signal(number, interrupted) for number in (signal.SIGALRM, signal.SIGINT, signal.SIGTERM)}
    signal.setitimer(signal.ITIMER_REAL, max(.001, effective - time.time() - 140))
    try:
        verify(root)
        result = execute(root, stage, plan, branch, effective)
    except BaseException as failure:
        error = dict(type=type(failure).__name__, message=str(failure))
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        try:
            receipts = [base.read(path) for path in stage.glob("**/supervision.json")]
            require(all(math.isfinite(receipt["reserved_seconds"]) and receipt["reserved_seconds"] >= 0 for receipt in receipts), "invalid cost")
            accounted = all((path.parent / "supervision.json").is_file() for path in stage.glob("**/process.json"))
            released = accounted and base.supervisor.gpu_processes_absent(branch["device"]) is True and all(
                all(receipt.get(key) is True for key in ("reservation_release_verified", "owned_group_empty", "gpu_processes_absent"))
                for receipt in receipts)
        except Exception as failure:
            receipts, released = [], False
            error = error or dict(type=type(failure).__name__, message=str(failure))
        ended = time.time()
        terminal = dict(record, status="COMPLETE" if error is None and result is not None and len(receipts) == 2 and
                        all(receipt.get("ok") is True for receipt in receipts) and released and ended <= effective else "FAILED_PARTIAL_NO_RETRY",
                        result=result, error=error, ended=ended, reserved_seconds=time.monotonic()-monotonic,
                        worker_reserved_seconds=sum(receipt["reserved_seconds"] for receipt in receipts),
                        release_verified=released, deadline_met=ended <= effective, counts_used_for_selection=False,
                        claim=old.CLAIM, monetary_cost=None)
        old.write(stage / "terminal.json", terminal)
        for number, handler in handlers.items():
            signal.signal(number, handler)
    require(terminal["status"] == "COMPLETE", "partial branch; inspect terminal.json; never retry/resume")
    return terminal


def main():
    clock = time.time(), time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "run", "status"))
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--helper", default="/tmp/astra_fading_sentinel_20260912.py")
    parser.add_argument("--runroot", required=True)
    parser.add_argument("--parentsroot")
    parser.add_argument("--materialroot")
    parser.add_argument("--deadline", type=float)
    parser.add_argument("--lease-end", type=float)
    parser.add_argument("--branch", choices=tuple(BRANCHES))
    parser.add_argument("--allow-gpu", action="store_true")
    args = parser.parse_args()
    bind(args.source_root, args.helper)
    if args.stage == "prepare":
        require(all(getattr(args, key) is not None for key in ("parentsroot", "materialroot", "deadline", "lease_end")), "missing prepare inputs")
        result = prepare(args.runroot, args.materialroot, args.parentsroot, args.deadline, args.lease_end)
    elif args.stage == "run":
        result = run(args.runroot, args.branch, args.allow_gpu, clock=clock)
    else:
        root = Path(args.runroot)
        old.read_plan(root)
        result = {name: base.read(root / name / "terminal.json") if (root / name / "terminal.json").is_file()
                  else {"status": "NONTERMINAL_OR_ABANDONED" if (root / name).exists() else "NOT_STARTED"} for name in BRANCHES}
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
