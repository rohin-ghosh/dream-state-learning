"""Fixed original-parent memory-only continuations; Main owns GPU allocation."""
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
import re
import signal
import sys
import time

HELPER_SHA = "7b0686de7b66fcad27a665c0b30054a893af3ee33d053c26fae903fc1ed8af20"
CORPUS_SHA = "2d12bb35d44279c3412323472bb716581c9ed57a966bb829290a49c4d799de7c"
PINS = {
    "0": ("d5a3d0297290184061b5cfcc3bf7fa5ba36a5995fbaedb021df464be7879ec5e",
          "bf67daeb5c7295c39b56259e44e7b619d5f99d99b34ba038f2a94f163e697467",
          "b58de5dde55c00762a4456727859c34f6caff3081c1bb068f7e960dbb284adc2"),
    "1": ("f2aaa20ab53b7cd3221580f3098da68f0381bd6a120967b6cfa085eedb769252",
          "248fee8d701b435c334aafd2551b93ef6da25de137ac71510fa5bb5c49129335",
          "f5cc61263806bff26d7b77ca267b70b21507bf2e1feeea78dc4eb510675a7e7a"),
    "2": ("54e44fc9e7193405b85b4a49b44c73ba50e3b075832b406a9538df77d0ad0fae",
          "fc5f2337f981ce71fe43a931bcff530019b843936f69104d6883cbb00001599c",
          "eea6c81b77aa745e440a68503a9984d52264b8b02932c512baa27dda368ba825"),
}
SECONDS = 900
CLAIM = "MEMORY_ONLY_ACQUISITION_RETENTION_NOT_CAUSAL_INTERFERENCE_OR_DOSE"
ACCOUNTING = dict(items=16, epochs=20, steps=80, cumulative_steps=160,
                  input_per_epoch=704, target_per_epoch=32,
                  input_presentations=14080, target_presentations=640)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def bind(source, helper):
    global old, base, trainer, dev, exact
    helper = Path(helper).resolve(strict=True)
    require(hashlib.sha256(helper.read_bytes()).hexdigest() == HELPER_SHA, "helper changed")
    spec = importlib.util.spec_from_file_location("memory_only_fading_helper", helper)
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    old.bind(source)
    base, trainer, dev = old.base, old.trainer, old.readout
    from organism_v6 import fundamental_memory_diagnostic as exact
    require(Path(exact.__file__).resolve().parent.parent == Path(source).resolve(), "wrong exact module")


def sources():
    return dict(old.sources(), memory_diagnostic=base.digest(exact.__file__),
                memory_trainer=base.digest(trainer.__file__), sidecar=base.digest(__file__))


def config(model, seed, epochs=20):
    require(type(seed) is int and seed in (0, 1, 2), "original seeds only")
    return asdict(trainer.TrainConfig(model=model, rank=8, alpha=16, dropout=.05,
        lr=3e-4, epochs=epochs, batch_size=4, grad_accum=1, seed=seed, pack=False, max_len=512))


def branches(devices):
    require(len(devices) == 3 and all(isinstance(device, str) and
        re.fullmatch(r"(?:0|[1-9][0-9]*|GPU-[0-9a-fA-F-]{36})", device) for device in devices),
        "three explicit Main devices required")
    return {str(seed): dict(seed=seed, device=device) for seed, device in enumerate(devices)}


def bounds(started, deadline, lease_end):
    require(all(math.isfinite(value) for value in (started, deadline, lease_end)), "nonfinite bounds")
    require(base.CLEANUP_RESERVE == 140 and base.WORKER_SECONDS == 600, "native bounds changed")
    effective = min(started + SECONDS, deadline, lease_end - 10)
    require(effective == started + SECONDS, "full 900s controller window required; no shortened seed")
    require(effective - time.time() > 150, "startup exhausted cleanup window")
    return effective


def fresh(path, protected=()):
    path = Path(path).expanduser().absolute()
    require(not path.exists() and not path.is_symlink() and
        not any(parent.is_symlink() for parent in path.parents), "fresh unaliased output required; no retry")
    for source in protected:
        source = Path(source).resolve()
        require(path != source and path not in source.parents and source not in path.parents, "output overlaps input")
    return path


def successful(receipt):
    require(all(receipt.get(key) is True for key in
        ("ok", "reservation_release_verified", "owned_group_empty", "gpu_processes_absent")) and
        receipt.get("returncode") == 0 and receipt.get("error") is None and
        math.isfinite(receipt["reserved_seconds"]) and receipt["reserved_seconds"] >= 0, "worker/cleanup failed")


def subset(material, tokenizer):
    rows = [row for row in material["corpus"] if row.get("view") == "memory"]
    cases = exact.selected_cases()
    indexed = {row["group"]: row for row in rows}
    require(len(rows) == len(indexed) == 16 and set(indexed) == set(exact.CASE_IDS), "exact16 unique original rows required")
    native = exact.native_inputs(tokenizer, exact.requests(cases))
    audit = []
    for case, prefix in zip(cases, native, strict=True):
        row = indexed[case["id"]]
        require(row["spans"] == [[prefix["rendered_prompt"], False, "context"],
            [case["expected"], True, "authored_birth_target"]] and
            row["meta"]["source_event_ids"] == case["source_event_ids"], "original target/render/source changed")
        color = tokenizer.encode(case["expected"], add_special_tokens=False)
        require(len(color) == 1 and len(prefix["prompt_token_ids"]) == 42, "native color/prefix counts changed")
        target = color + [tokenizer.eos_token_id]
        encoded = trainer.encode_item_segments(trainer.normalize_items([row])[0], tokenizer, 512, False, True)
        require(len(encoded) == 1 and encoded[0].ids == prefix["prompt_token_ids"] + target and
            encoded[0].labels == [-100] * 42 + target, "native labels/causal indices changed")
        audit.append(dict(case_id=case["id"], input_ids=encoded[0].ids, labels=encoded[0].labels,
                          predictor_indices=[41, 42]))
    return dict(corpus=rows), audit


def parent_record(root, seed, model, model_files):
    receipt_name = "result.json" if seed == 0 else "verified.json"
    paths = [root / "plan.json", root / "fit_teach" / receipt_name, root / "readouts/teach/plan.json"]
    require(tuple(base.digest(path) for path in paths) == PINS[str(seed)], "not original pinned teach parent")
    original = old.read_plan(root)
    parent = root / "fit_teach/adapter"
    files = trainer._warm_inventory(parent)
    fit = base.read(paths[1])
    prior = base.read(parent / "train_manifest.json")
    expected = config(model, seed, 4)
    require(original["config"] == prior["config"] == expected and original["model"] == model and
        original["model_files"] == model_files and prior["base_model"] == model and
        prior["steps"] == 80 and "warm_start" not in prior and prior["nonfinite_batches"] == 0 and
        math.isfinite(prior["final_loss"]) and (parent / "DONE").is_file(), "parent recipe/history changed")
    require(fit["arm"] == "teach" and fit["adapter"] == str(parent) and fit["adapter_files"] == files,
        "parent fit identity differs")
    require(base.digest(root / "teach.json") == original["corpus_sha256"]["teach"] ==
        prior["corpus"]["sha256"] == CORPUS_SHA, "original corpus changed")
    readroot = root / "readouts/teach"
    readplan = old.read_plan(readroot)
    require(readplan["adapter"] == str(parent) and readplan["adapter_files"] == files and
        readplan["model_files"] == model_files and readplan["model"] == model and
        readplan["identity"] == base.expected_identity(readplan, str(parent)), "baseline identity changed")
    for worker in (root / "fit_teach/worker", readroot / "run/worker"):
        successful(base.read(worker / "supervision.json"))
        paths.append(worker / "supervision.json")
    data = readroot / "run/data"
    require(base.read(data / "manifest.json")["files"] == base.tree_hashes(data, ("manifest.json",)), "baseline capture changed")
    reduction = base.read(readroot / "reduction.json")
    require(reduction["complete"] is True and reduction["counts"]["total"] == 48 and
        reduction["plan_sha256"] == base.digest(readroot / "plan.json") and
        reduction["capture_sha256"] == base.digest(data / "manifest.json"), "baseline reduction unbound")
    paths.append(root / "teach.json")
    return dict(parent=str(parent), parent_files=files, provenance={str(path): base.digest(path) for path in paths},
        readout_files=base.tree_hashes(readroot), baseline_counts=reduction["counts"], readout=readplan)


def template(module, model, model_files, tokenizer, device, lease_end):
    cases = module.selected_cases()
    requests = module.requests(cases)
    result = dict(schema=1, model=model, model_files=model_files, adapter=None, adapter_files={},
        device=device, lease_end=float(lease_end), cases=cases, requests=requests,
        native_inputs=module.native_inputs(tokenizer, requests), source_hashes=module.sources(),
        worker_seconds=600, output_token_ceiling=64 * len(cases), claim_limits=module.CLAIM_LIMITS)
    if module is exact:
        result.update(label=exact.LABEL, corpus_sha256=base.value_hash(exact.corpus.build_candidate()))
    result["identity"] = base.expected_identity(result, None)
    return result


def inherited_baseline(readroot):
    prior = old.read_plan(readroot)
    data = readroot / "run/data"
    reduction = base.read(readroot / "reduction.json")
    require(base.read(data / "manifest.json")["files"] == base.tree_hashes(data, ("manifest.json",)) and
        reduction["complete"] is True and reduction["counts"]["total"] == 48 and
        reduction["plan_sha256"] == base.digest(readroot / "plan.json") and
        reduction["capture_sha256"] == base.digest(data / "manifest.json"), "inherited baseline unbound")
    successful(base.read(readroot / "run/worker/supervision.json"))
    return dict(root=str(readroot), files=base.tree_hashes(readroot), counts=reduction["counts"],
                model_files=prior["model_files"], inherited=True, new_calls=0)


def prepare(runroot, seed0_root, parentsroot, devices, deadline, lease_end):
    bounds(time.time(), deadline, lease_end)
    selected = branches(devices)
    roots = [Path(seed0_root).resolve(strict=True)] + [Path(parentsroot).resolve(strict=True) / f"seed{seed}" for seed in (1, 2)]
    original = old.read_plan(roots[0])
    model, model_files = original["model"], base.model_hashes(original["model"])
    root = fresh(runroot, (*roots, model, base.REPO))
    tokenizer = base.native_tokenizer(model)
    parents = {str(seed): parent_record(path, seed, model, model_files) for seed, path in enumerate(roots)}
    material, audit = subset(base.read(roots[0] / "teach.json"), tokenizer)
    for path in roots[1:]:
        require(subset(base.read(path / "teach.json"), tokenizer) == (material, audit), "seed subset changed")
    templates = {name: template(module, model, model_files, tokenizer, devices[0], lease_end)
                 for name, module in (("dev", dev), ("exact", exact))}
    references = {"OFF": inherited_baseline(roots[0] / "readouts/OFF")}
    references.update({f"control{seed}": inherited_baseline(path / "readouts/control") for seed, path in enumerate(roots)})
    require(all(reference["model_files"] == model_files for reference in references.values()), "baseline base differs")
    for parent in parents.values():
        require(all(parent["readout"][key] == templates["dev"][key] for key in
            ("cases", "requests", "native_inputs")), "inherited dev inputs differ")
    root.mkdir()
    old.write(root / "memory.json", material)
    plan = dict(schema=1, source_root=str(base.REPO), source_hashes=sources(), model=model, model_files=model_files,
        parents=parents, inherited_baselines=references, branches=selected, configs={str(seed): config(model, seed) for seed in range(3)},
        subset_sha256=base.digest(root / "memory.json"), native_audit=audit, accounting=ACCOUNTING,
        templates=templates, deadline=float(deadline), real_lease_end=float(lease_end), controller_seconds=900,
        cleanup_seconds=140, aggregate_a40_seconds=2700, claim=CLAIM, counts_used_for_selection=False,
        new_off_calls=0, new_hf_calls=0, confirmation_calls=0, calls_per_child=64)
    for seed in ("0", "1", "2"):
        adapter = root / f"seed{seed}/adapter"
        fit_command(root, plan, seed, adapter)
        trainer._warm_parent(parents[seed]["parent"], adapter, trainer.TrainConfig(**plan["configs"][seed]))
    old.seal(root, plan)
    return dict(root=str(root), status="ALL_THREE_PREPARED_NOT_LAUNCHED", branches=selected)


def verify(root):
    plan = old.read_plan(root)
    require(plan["schema"] == 1 and plan["source_root"] == str(base.REPO) and plan["source_hashes"] == sources(), "source changed")
    require(plan["branches"] == branches([plan["branches"][str(seed)]["device"] for seed in range(3)]) and
        plan["configs"] == {str(seed): config(plan["model"], seed) for seed in range(3)} and
        plan["accounting"] == ACCOUNTING and plan["controller_seconds"] == 900 and
        plan["cleanup_seconds"] == 140 and plan["aggregate_a40_seconds"] == 2700 and
        plan["claim"] == CLAIM and plan["counts_used_for_selection"] is False and
        all(plan[key] == 0 for key in ("new_off_calls", "new_hf_calls", "confirmation_calls")) and
        plan["calls_per_child"] == 64 and set(plan["parents"]) == {"0", "1", "2"}, "fixed contract changed")
    require(base.model_hashes(plan["model"]) == plan["model_files"], "base changed")
    require(base.digest(root / "memory.json") == plan["subset_sha256"], "subset changed")
    require(set(plan["inherited_baselines"]) == {"OFF", "control0", "control1", "control2"}, "baseline coverage changed")
    for reference in plan["inherited_baselines"].values():
        require(base.tree_hashes(reference["root"]) == reference["files"], "inherited baseline changed")
    for seed, parent in plan["parents"].items():
        require(trainer._warm_inventory(parent["parent"]) == parent["parent_files"] and
            all(base.digest(path) == digest for path, digest in parent["provenance"].items()), "parent changed")
        seedroot = Path(parent["parent"]).parent.parent
        require(base.digest(seedroot / "plan.json") == PINS[seed][0] and
            base.tree_hashes(seedroot / "readouts/teach") == parent["readout_files"], "baseline changed")
        require(base.read(root / "memory.json") == dict(corpus=[row for row in base.read(seedroot / "teach.json")["corpus"]
            if row.get("view") == "memory"]), "subset no longer equals original rows")
    return plan


def fit_command(root, plan, seed, adapter):
    command = [sys.executable, "-B", "-m", "organism_v6.train_adapter_v3", "--corpus", str(root / "memory.json"),
        "--out", str(adapter), "--init-adapter", plan["parents"][seed]["parent"], "--model", plan["model"],
        "--rank", "8", "--alpha", "16", "--dropout", "0.05", "--lr", "0.0003", "--epochs", "20",
        "--batch-size", "4", "--grad-accum", "1", "--seed", seed, "--no-pack", "--max-len", "512"]
    require(asdict(trainer.config_from_args(trainer.build_parser().parse_args(command[4:]))) == plan["configs"][seed],
        "effective CLI differs")
    return command


def validate_manifest(plan, seed, manifest, before, saved):
    parent = plan["parents"][seed]
    require(manifest["config"] == plan["configs"][seed] and manifest["base_model"] == plan["model"] and
        manifest["steps"] == manifest["micro_batches"] == 80 and manifest["epochs_run"] == 20 and
        manifest["nonfinite_batches"] == 0 and manifest["empty"] is False and
        math.isfinite(manifest["final_loss"]), "incomplete/wrong fit")
    corpus = manifest["corpus"]
    require(corpus["sha256"] == plan["subset_sha256"] and corpus["n_items"] == corpus["n_encoded"] == 16 and
        corpus["n_skipped_no_target"] == 0 and all(manifest["truncation"][key] == 0 for key in
        ("items_truncated", "context_tokens_dropped", "target_tokens_dropped", "items_split")), "corpus/truncation differs")
    require(manifest["tokens"]["total"] == 704 and manifest["tokens"]["target"] == 32 and
        manifest["train_tokens_seen"] == 14080 and manifest["epochs_run"] * manifest["tokens"]["target"] == 640,
        "token presentations differ")
    warm = manifest["warm_start"]
    require(warm["mode"] == "WEIGHT_WARM_START_FRESH_OPTIMIZER" and
        warm["parent_path"] == parent["parent"] and warm["parent_files"] == warm["parent_files_after"] == parent["parent_files"] and
        all(warm[key] is True for key in ("parent_unchanged", "base_frozen", "initialized_loaded_state_check")) and
        warm["adapter_count"] == 1 and warm["phase_seed"] == int(seed) and warm["optimizer_initial_state_entries"] == 0 and
        warm["optimizer_state_restored"] is False and warm["optimizer_state_saved"] is False and
        warm["optimizer_initialization"] == "fresh_per_write" and warm["phase_steps"] == 80 and
        warm["parent_cumulative_steps"] == 80 and warm["cumulative_steps"] == 160, "warm ownership/optimizer/history differs")
    old.check_states("memory", before, warm, saved)
    require(before == warm["initialized_state"] and not warm["dtype_conversions"], "original float32 loaded state changed")


def execute(root, stage, plan, seed, effective):
    parent = plan["parents"][seed]
    adapter = stage / "adapter"
    active = dict(plan, device=plan["branches"][seed]["device"], lease_end=effective)
    before = old.state_inventory(parent["parent"])
    fit_cost = base.supervise(stage, active, stage / "fit-worker", fit_command(root, plan, seed, adapter))
    successful(fit_cost)
    require((adapter / "DONE").is_file(), "missing fit DONE")
    manifest = base.read(adapter / "train_manifest.json")
    validate_manifest(plan, seed, manifest, before, old.state_inventory(adapter))
    files = trainer._warm_inventory(adapter)
    fit = dict(adapter=str(adapter), adapter_files=files, steps=80, cumulative_steps=160,
        input_presentations=14080, target_presentations=640, supervision=fit_cost)
    old.write(stage / "fit-result.json", fit)
    reductions = {}
    for name, module, count in (("dev", dev, 48), ("exact", exact, 16)):
        require(time.time() < effective - 150, "readout budget exhausted")
        readroot = stage / name
        readroot.mkdir()
        readplan = copy.deepcopy(plan["templates"][name])
        readplan.update(adapter=str(adapter), adapter_files=files, device=active["device"], lease_end=float(effective))
        readplan["identity"] = base.expected_identity(readplan, str(adapter))
        old.seal(readroot, readplan)
        module.verify(readroot)
        (readroot / "run").mkdir()
        command = [sys.executable, "-B", "-m", module.__name__, "_worker", "--root", str(readroot), "--allow-gpu"]
        successful(base.supervise(stage, readplan, readroot / "run/worker", command, readroot / "run/data/calls"))
        reduction = module.reduce(readroot)
        require(reduction["complete"] is True and reduction["counts"]["total"] == count, "incomplete readout is not zero")
        reductions[name] = dict(reduction=reduction, sha256=base.digest(readroot / "reduction.json"))
        require(trainer._warm_inventory(adapter) == files, "readout changed child")
    verify(root)
    return dict(fit=fit, readouts=reductions, baseline_counts=parent["baseline_counts"])


def run(root, seed, allow_gpu=False, clock=None):
    require(allow_gpu and seed in PINS, "Main allocation and explicit --allow-gpu required")
    started, monotonic = clock if clock is not None else (time.time(), time.monotonic())
    root = Path(root).resolve(strict=True)
    plan = old.read_plan(root)
    device = plan["branches"][seed]["device"]
    require(os.environ.get("CUDA_VISIBLE_DEVICES") == device, "wrong sealed device")
    effective = bounds(started, plan["deadline"], plan["real_lease_end"])
    stage = fresh(root / f"seed{seed}")
    stage.mkdir()
    record = dict(seed=int(seed), device=device, controller_pid=os.getpid(), started=started,
        effective_deadline=effective, plan_sha256=base.digest(root / "plan.json"),
        scope="whole controller including CPU/startup/gaps/cleanup; Main owns external reservation ledger")
    old.write(stage / "reservation.json", record)
    result, error = None, None
    def interrupted(number, frame):
        raise RuntimeError(f"controller interruption/cleanup boundary: {number}")
    handlers = {number: signal.signal(number, interrupted) for number in (signal.SIGALRM, signal.SIGINT, signal.SIGTERM)}
    signal.setitimer(signal.ITIMER_REAL, max(.001, effective - time.time() - 140))
    try:
        verify(root)
        result = execute(root, stage, plan, seed, effective)
    except BaseException as failure:
        error = dict(type=type(failure).__name__, message=str(failure))
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        try:
            receipts = [base.read(path) for path in stage.glob("**/supervision.json")]
            require(all(math.isfinite(receipt["reserved_seconds"]) and receipt["reserved_seconds"] >= 0 for receipt in receipts), "invalid cost")
            accounted = all((path.parent / "supervision.json").is_file() for path in stage.glob("**/process.json"))
            released = accounted and base.supervisor.gpu_processes_absent(device) is True and all(
                all(receipt.get(key) is True for key in ("reservation_release_verified", "owned_group_empty", "gpu_processes_absent"))
                for receipt in receipts)
        except Exception as failure:
            receipts, released = [], False
            error = error or dict(type=type(failure).__name__, message=str(failure))
        ended = time.time()
        terminal = dict(record, status="COMPLETE" if error is None and result is not None and len(receipts) == 3 and
            all(receipt.get("ok") is True for receipt in receipts) and released and ended <= effective else "FAILED_PARTIAL_NO_RETRY",
            result=result, error=error, ended=ended, reserved_seconds=time.monotonic()-monotonic,
            worker_reserved_seconds=sum(receipt["reserved_seconds"] for receipt in receipts), release_verified=released,
            deadline_met=ended <= effective, claim=CLAIM, counts_used_for_selection=False, monetary_cost=None)
        old.write(stage / "terminal.json", terminal)
        for number, handler in handlers.items():
            signal.signal(number, handler)
    require(terminal["status"] == "COMPLETE", "partial seed; inspect terminal.json; no retry/resume")
    return terminal


def main():
    clock = time.time(), time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "run", "status"))
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--helper", default="/tmp/astra_fading_sentinel_20260912.py")
    parser.add_argument("--runroot", required=True)
    parser.add_argument("--seed0-root")
    parser.add_argument("--parentsroot")
    parser.add_argument("--devices", nargs=3)
    parser.add_argument("--deadline", type=float)
    parser.add_argument("--lease-end", type=float)
    parser.add_argument("--seed", choices=tuple(PINS))
    parser.add_argument("--allow-gpu", action="store_true")
    args = parser.parse_args()
    bind(args.source_root, args.helper)
    if args.stage == "prepare":
        require(all(getattr(args, name) is not None for name in
            ("seed0_root", "parentsroot", "devices", "deadline", "lease_end")), "missing prepare inputs")
        result = prepare(args.runroot, args.seed0_root, args.parentsroot, args.devices, args.deadline, args.lease_end)
    elif args.stage == "run":
        result = run(args.runroot, args.seed, args.allow_gpu, clock)
    else:
        root = Path(args.runroot)
        old.read_plan(root)
        result = {seed: base.read(root / f"seed{seed}/terminal.json") if (root / f"seed{seed}/terminal.json").exists()
            else dict(status="NONTERMINAL_OR_ABANDONED" if (root / f"seed{seed}").exists() else "NOT_STARTED") for seed in PINS}
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
