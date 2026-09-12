"""One sealed seed, two sequential compatible-habit arms; Main alone launches."""
from __future__ import annotations

import argparse
import copy
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


HELPER_SHA = "bc17821dc352757e7e18c74fddac451faee7b1ebae494b77ed61c4afceacb5e1"
SECONDS = 1200
CLEANUP = 140
ARMS = ("input_before", "input_after")
PINS = {
    0: ("d5a3d0297290184061b5cfcc3bf7fa5ba36a5995fbaedb021df464be7879ec5e",
        "bf67daeb5c7295c39b56259e44e7b619d5f99d99b34ba038f2a94f163e697467",
        "b58de5dde55c00762a4456727859c34f6caff3081c1bb068f7e960dbb284adc2"),
    1: ("f2aaa20ab53b7cd3221580f3098da68f0381bd6a120967b6cfa085eedb769252",
        "248fee8d701b435c334aafd2551b93ef6da25de137ac71510fa5bb5c49129335",
        "f5cc61263806bff26d7b77ca267b70b21507bf2e1feeea78dc4eb510675a7e7a"),
    2: ("54e44fc9e7193405b85b4a49b44c73ba50e3b075832b406a9538df77d0ad0fae",
        "fc5f2337f981ce71fe43a931bcff530019b843936f69104d6883cbb00001599c",
        "eea6c81b77aa745e440a68503a9984d52264b8b02932c512baa27dda368ba825"),
}
BASELINE_PINS = {
    0: ("56381a963c17c2a8d3337ba5aebbb8f884fa75e2881983dec2f0976ebd143549",
        "98a95c19ceb4fe305dc5282b49442ffc75fe9ccfc44298a11957adbe4b0cac82"),
    1: ("5a2881b2ba4151dd8335b10d4c90c0f9065922b6c43aa2e15b8eb3ef61cef8cc",
        "c216db3b54fa91777b56da99a5cca53b7226f90378a49a19111c8f4bf491e9a3"),
    2: ("25e32805bfb9119d14383b6bf290471b2d50e4d12ff014ea6efaeae277431a37",
        "a561fc2d3ae3bab6ad28b1223939e048fc4d5a6525ae59d28f1799b9ba2b1f2d"),
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def bind(source, helper="/tmp/astra_fading_replication_20260912.py",
         state_helper="/tmp/astra_fading_sentinel_20260912.py"):
    global prior, old, base, trainer, readout, material
    helper = Path(helper).resolve(strict=True)
    require(hashlib.sha256(helper.read_bytes()).hexdigest() == HELPER_SHA, "fading helper hash changed")
    spec = importlib.util.spec_from_file_location("two_habit_fading_helper", helper)
    prior = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prior)
    prior.bind(source, state_helper)
    old, base, trainer, readout = prior.old, prior.base, prior.trainer, prior.readout
    from organism_v6 import fundamental_two_habit_corpus as material
    require(Path(material.__file__).resolve().parent.parent == Path(source).resolve(), "wrong exporter import")


def sources():
    return dict(prior.sources(), **material.source_hashes(), two_habit_runner=base.digest(__file__))


def config(model, seed):
    require(type(seed) is int and seed in PINS, "exact original parent seed0/1/2 required")
    result = old.config(model, "1e-4")
    result.update(seed=seed, overflow="truncate")
    for key in ("lr", "rank", "alpha", "dropout", "epochs", "batch_size", "grad_accum", "target_modules",
                "layers", "optimizer", "max_steps", "max_len", "pack", "chat_template", "add_eos",
                "overflow", "shuffle_groups"):
        require(result[key] == material.RECIPE[key], "export/trainer recipe differs: " + key)
    return result


def bounds(started, deadline, lease_end):
    require(all(math.isfinite(value) for value in (started, deadline, lease_end)), "nonfinite time bounds")
    require(base.CLEANUP_RESERVE == CLEANUP and base.WORKER_SECONDS == 600, "native supervision bounds changed")
    effective = min(started + SECONDS, deadline, lease_end - 10)
    require(effective - time.time() > CLEANUP + 10, "insufficient full-controller cleanup window")
    return effective


def device_check(device):
    require(isinstance(device, str) and re.fullmatch(r"(?:0|[1-9][0-9]*|GPU-[0-9a-fA-F-]{36})", device),
            "one explicit Main-provided GPU required")


def score_orders(score):
    """Recognize both raw orders directly; never reorder or repair an output."""
    lines = [line for line in score["raw_text"].splitlines() if line.strip(" \t")]
    no_spill = score["strict_lines"] and len(lines) == 3 and all(
        score["field_counts"][label] == 1 for label in ("INPUT", "PREDICT", "ACT"))
    labels = tuple(re.match(r"[ \t]*(INPUT|PREDICT|ACT)\b", line)[1] for line in lines) if no_spill else ()
    before = bool(no_spill and score["input_correct"] and labels == ("INPUT", "PREDICT", "ACT"))
    after = bool(no_spill and score["input_correct"] and labels == ("PREDICT", "ACT", "INPUT"))
    correct = score["prediction_correct"] and score["act_success"] and score["form_a"]
    return dict(score, no_tag_spill=no_spill, input_before_order=before, input_after_order=after,
                input_before_success=bool(before and correct), input_after_success=bool(after and correct))


def score_panel(rows, arm=None):
    require(arm is None or arm in ARMS, "unknown scoring arm")
    require(isinstance(rows, list) and len(rows) == 48 and
            [row["case_id"] for row in rows] == list(readout.CASE_IDS), "complete original ordered48 required; no zeros/subsets")
    scored = [material.score_response(row["case_id"], row["raw_text"]) for row in rows]
    for row in scored:
        if row["kind"] == "addition":
            row["score"] = score_orders(row["score"])
        else:
            row["score"]["tag_spill"] = bool(re.search(r"\b(?:INPUT|PREDICT|ACT)\b", row["score"]["raw_text"], re.IGNORECASE))
    addition = [row["score"] for row in scored if row["kind"] == "addition"]
    memory = [row["score"] for row in scored if row["kind"] == "memory_recall"]
    require(len(addition) == 32 and len(memory) == 16, "panel kind/count mismatch")
    metrics = ("joint", "form_a", "form_b", "form_b_order", "input_correct", "prediction_correct", "act_success",
               "no_tag_spill", "input_before_order", "input_after_order", "input_before_success", "input_after_success")
    counts = dict(total=32, **{metric: sum(row[metric] for row in addition) for metric in metrics},
        original_adherence=sum(row["original_score"]["adherence"] for row in addition),
        invalid_for_both_orders=sum(not row["input_before_order"] and not row["input_after_order"] for row in addition))
    if arm is not None:
        opposite = next(other for other in ARMS if other != arm)
        counts.update(own_order_success=counts[arm + "_success"], opposite_order_count=counts[opposite + "_order"],
            opposite_order_rejected=sum(not row[opposite + "_order"] for row in addition),
            own_success_and_opposite_rejection=sum(row[arm + "_success"] and not row[opposite + "_order"] for row in addition))
    return dict(arm=arm, rows=scored, counts=dict(total=48, addition=counts,
        memory=dict(total=16, correct=sum(row["correct"] for row in memory),
                    invalid=sum(not row["valid"] for row in memory), tag_spill=sum(row["tag_spill"] for row in memory))),
        claim=material.CLAIM, selection="all original48; remaining64 unrequested; no subset rescue")


def baseline(readroot, plan, seed, tokenizer):
    require(tuple(base.digest(readroot / name) for name in ("run/data/manifest.json", "reduction.json")) ==
            BASELINE_PINS[seed], "not pinned original H capture/reduction")
    data = readroot / "run/data"
    require(base.read(data / "manifest.json")["files"] == base.tree_hashes(data, ("manifest.json",)),
            "original baseline capture changed")
    expected = {request["call_id"] + suffix for request in plan["requests"]
                for suffix in (".request.json", ".response.json")}
    require({path.name for path in (data / "calls").iterdir()} == expected and not (data / "failure.json").exists(),
            "extra/missing/failed baseline capture")
    require(base.read(data / "identity.json") == dict(backend=plan["identity"], model_files=plan["model_files"],
            adapter_files=plan["adapter_files"]), "baseline capture identity differs")
    prior.audit_inputs(readroot, plan, tokenizer)
    reduced = base.read(readroot / "reduction.json")
    rows = []
    for request, case in zip(plan["requests"], plan["cases"], strict=True):
        raw = base.read(data / "calls" / (request["call_id"] + ".response.json"))["response"]["text"]
        score = (readout.score_addition if case["kind"] == "addition" else readout.score_memory)(raw, case["expected"])
        rows.append(dict(call_id=request["call_id"], case_id=case["id"], kind=case["kind"], **score))
    require(reduced["complete"] is True and reduced["counts"]["total"] == 48 and reduced["rows"] == rows and
            reduced["plan_sha256"] == base.digest(readroot / "plan.json") and
            reduced["capture_sha256"] == base.digest(data / "manifest.json"), "baseline reduction/raw rows differ")
    return score_panel(rows)


def parent_record(root, seed, model, model_files, tokenizer, output):
    fit_name = "result.json" if seed == 0 else "verified.json"
    paths = [root / "plan.json", root / "fit_teach" / fit_name, root / "readouts/teach/plan.json"]
    require(tuple(base.digest(path) for path in paths) == PINS[seed], "not pinned original H parent")
    original, readplan = old.read_plan(root), old.read_plan(root / "readouts/teach")
    fit, parent = base.read(paths[1]), root / "fit_teach/adapter"
    expected = old.config(model, "0")
    expected.update(lr=3e-4, seed=seed)
    require(original["model"] == model and original["model_files"] == model_files and original["config"] == expected,
            "original parent base/recipe/seed differs")
    require(original["corpus_sha256"]["teach"] == material.SOURCE_SHA256, "parent did not fit original teaching material")
    require(original.get("replication", {}).get("seed", 0) == seed, "original parent seed differs")
    files = trainer._warm_inventory(parent)
    manifest = base.read(parent / "train_manifest.json")
    require((parent / "DONE").is_file() and manifest["config"] == expected and manifest["steps"] == 80 and
            manifest["nonfinite_batches"] == 0 and "warm_start" not in manifest and
            manifest["corpus"]["sha256"] == material.SOURCE_SHA256, "parent is not original completed fresh H")
    require(fit["adapter"] == str(parent) and fit["adapter_files"] == files and fit["arm"] == "teach" and
            fit["status"] == "FIT_COMPLETE_PENDING_PAIRED_READOUT", "parent fit identity differs")
    fit_receipt = base.read(root / "fit_teach/worker/supervision.json")
    if seed == 0:
        require(fit["manifest"] == manifest and fit["supervised"] == fit_receipt, "seed0 result/manifest/cost differs")
    else:
        require(fit["seed"] == seed and fit["steps"] == 80 and fit["plan_sha256"] == PINS[seed][0] and
                fit["supervision_sha256"] == base.digest(root / "fit_teach/worker/supervision.json"), "replication verified receipt differs")
    for receipt in (fit_receipt, base.read(root / "readouts/teach/run/worker/supervision.json")):
        require(all(receipt[key] is True for key in ("ok", "reservation_release_verified", "owned_group_empty", "gpu_processes_absent"))
                and receipt["returncode"] == 0, "original cleanup/worker success unverified")
    require(readplan["adapter"] == str(parent) and readplan["adapter_files"] == files and
            readplan["model"] == model and readplan["model_files"] == model_files and
            readplan["identity"] == base.expected_identity(readplan, str(parent)), "original H readout identity differs")
    scored = baseline(root / "readouts/teach", readplan, seed, tokenizer)
    trainer._warm_parent(parent, output / "unused-validation-output", trainer.TrainConfig(**config(model, seed)))
    return dict(parent=str(parent), parent_files=files, state=old.state_inventory(parent), readout=readplan,
        readout_root=str(root / "readouts/teach"), readout_files=base.tree_hashes(root / "readouts/teach"),
        provenance={str(path): base.digest(path) for path in paths + [root / "fit_teach/worker/supervision.json"]},
        baseline=scored)


def audit_material(root, model, model_files, tokenizer):
    manifest = base.read(root / "manifest.json")
    require(manifest["status"] == "NATIVE_TOKEN_MATCHED_NO_FIT_NO_LAUNCH" and manifest["model"] == model and
            manifest["pins"]["model_files"] == model_files and manifest["pins"]["source_code_sha256"] == material.source_hashes() and
            manifest["pins"]["source_sha256"] == material.SOURCE_SHA256 and manifest["recipe"] == material.RECIPE,
            "actual exported native material/recipe/pins required")
    names = {arm + ".json" for arm in ARMS} | {"inventory.json", "source_records.json", "panels.json", "token_audit.json"}
    require(set(manifest["sha256"]) == names and {path.name for path in root.iterdir()} == names | {"manifest.json"},
            "material membership differs")
    require(all(base.digest(root / name) == digest for name, digest in manifest["sha256"].items()), "material bytes changed")
    require(base.digest(manifest["source_path"]) == material.SOURCE_SHA256, "actual original source changed")
    rows = base.read(manifest["source_path"])["corpus"]
    expected = material.build_material(rows)
    require(all(base.read(root / (arm + ".json")) == dict(corpus=expected["corpora"][arm]) for arm in ARMS), "corpus differs")
    for key, filename in (("inventory", "inventory.json"), ("source_records", "source_records.json"), ("panels", "panels.json")):
        require(base.read(root / filename) == expected[key], "material provenance/panels differ")
    audit = material.audit_native(rows, expected, tokenizer)
    require(base.read(root / "token_audit.json") == audit, "actual native audit differs from exported audit")
    return dict(files=base.tree_hashes(root), source_path=manifest["source_path"],
                tokens={arm: audit["arms"][arm]["totals"] for arm in ARMS})


def prepare(runroot, materialroot, parentroot, seed, device, deadline, lease_end, budget_note, logging_note):
    started = time.time()
    device_check(device)
    require(type(seed) is int and seed in PINS, "only original seed0/1/2")
    require(all(isinstance(note, str) and note.strip() for note in (budget_note, logging_note)), "Main budget/logging declarations required")
    require(deadline > started + SECONDS and lease_end >= deadline + 10, "future full per-seed window required")
    bounds(started, deadline, lease_end)
    parentroot, materialroot = Path(parentroot).resolve(strict=True), Path(materialroot).resolve(strict=True)
    model = old.read_plan(parentroot)["model"]
    root = prior.fresh(runroot, (parentroot, materialroot, model, base.REPO))
    code, model_files = sources(), base.model_hashes(model)
    tokenizer = base.native_tokenizer(model)
    native = audit_material(materialroot, model, model_files, tokenizer)
    parent = parent_record(parentroot, seed, model, model_files, tokenizer, root)
    require(code == sources() and model_files == base.model_hashes(model), "source/model changed during CPU preparation")
    require(native["files"] == base.tree_hashes(materialroot) and parent["parent_files"] == trainer._warm_inventory(parent["parent"]) and
            parent["readout_files"] == base.tree_hashes(parent["readout_root"]), "material/parent/baseline changed during preparation")
    plan = dict(schema=1, source_root=str(base.REPO), source_label="d1e70002d12052f6b7357d42cf5997aa915e16f7; hashes authoritative",
        source_hashes=code, seed=seed, device=device, arms=list(ARMS), model=model, model_files=model_files,
        parent=parent, materialroot=str(materialroot), material=native, config=config(model, seed),
        deadline=float(deadline), real_lease_end=float(lease_end), controller_seconds=SECONDS, cleanup_seconds=CLEANUP,
        budget_note=budget_note, logging_note=logging_note, claim=material.CLAIM, counts_used_for_selection=False,
        counts=dict(fits=2, steps_per_fit=80, updates=160, row_presentations=640, new_readout_calls=96,
                    reused_H_calls=48, unrequested_cases=64, output_cap_tokens_not_usage=6144),
        preparation=dict(started=started, ended=time.time(), scope="offline CPU preflight, outside later GPU reservation"))
    root.mkdir(parents=True, exist_ok=False)
    old.seal(root, plan)
    return dict(root=str(root), status="PREPARED_NOT_LAUNCHED", seed=seed, device=device, plan_sha256=base.digest(root / "plan.json"))


def verify(root):
    plan = old.read_plan(root)
    device_check(plan["device"])
    require(plan["schema"] == 1 and plan["source_root"] == str(base.REPO) and plan["source_hashes"] == sources(), "source/plan contract changed")
    require(plan["arms"] == list(ARMS) and plan["config"] == config(plan["model"], plan["seed"]) and
            plan["controller_seconds"] == SECONDS and plan["cleanup_seconds"] == CLEANUP and
            plan["claim"] == material.CLAIM and plan["counts_used_for_selection"] is False, "recipe/seed/bounds changed")
    require(base.model_hashes(plan["model"]) == plan["model_files"], "model/tokenizer changed")
    require(base.tree_hashes(plan["materialroot"]) == plan["material"]["files"] and
            base.digest(plan["material"]["source_path"]) == material.SOURCE_SHA256, "material/source changed")
    parent = plan["parent"]
    require(trainer._warm_inventory(parent["parent"]) == parent["parent_files"] and
            base.tree_hashes(parent["readout_root"]) == parent["readout_files"] and
            all(base.digest(path) == digest for path, digest in parent["provenance"].items()), "original H parent/baseline changed")
    return plan


def arm_row(stage, plan, arm):
    require(arm in ARMS, "unknown arm")
    return dict(arm=arm, stage=str(stage / arm), adapter=str(stage / arm / "adapter"), parent=plan["parent"]["parent"])


def fit_command(plan, row):
    return [sys.executable, "-B", "-m", "organism_v6.train_adapter_v3", "--corpus",
        str(Path(plan["materialroot"]) / (row["arm"] + ".json")), "--out", row["adapter"], "--init-adapter", row["parent"],
        "--model", plan["model"], "--rank", "8", "--alpha", "16", "--dropout", "0.05", "--lr", "0.0001",
        "--epochs", "4", "--batch-size", "4", "--grad-accum", "1", "--seed", str(plan["seed"]),
        "--no-pack", "--max-len", "512", "--overflow", "truncate"]


def verify_fit(plan, row):
    parent = plan["parent"]
    require(row["parent"] == parent["parent"], "arms must start from the same original H, never chain")
    adapter = Path(row["adapter"])
    manifest = base.read(adapter / "train_manifest.json")
    require((adapter / "DONE").is_file() and manifest["config"] == plan["config"] and
            manifest["steps"] == manifest["micro_batches"] == 80 and manifest["epochs_run"] == 4 and
            manifest["nonfinite_batches"] == 0 and manifest["empty"] is False and math.isfinite(manifest["final_loss"]),
            "incomplete/nonfinite/wrong fit")
    actual = manifest["corpus"]
    require(actual["sha256"] == plan["material"]["files"][row["arm"] + ".json"] and
            actual["n_items"] == actual["n_encoded"] == 80 and actual["n_skipped_no_target"] == 0, "actual corpus differs")
    require(all(manifest["truncation"][key] == 0 for key in
                ("items_truncated", "context_tokens_dropped", "target_tokens_dropped", "items_split")), "ANY split/drop forbidden")
    tokens = plan["material"]["tokens"][row["arm"]]
    require(manifest["tokens"]["total"] == tokens["input_tokens"] and manifest["tokens"]["target"] == tokens["target_tokens"] and
            manifest["train_tokens_seen"] == 4 * tokens["input_tokens"], "actual native token dose differs")
    warm = manifest["warm_start"]
    require(warm["mode"] == "WEIGHT_WARM_START_FRESH_OPTIMIZER" and warm["parent_path"] == row["parent"] and
            warm["parent_files"] == warm["parent_files_after"] == parent["parent_files"] == trainer._warm_inventory(row["parent"]),
            "wrong/changed original parent")
    require(all(warm[key] is True for key in ("parent_unchanged", "base_frozen", "initialized_loaded_state_check")) and
            warm["adapter_count"] == 1 and warm["phase_seed"] == plan["seed"] and warm["optimizer_initial_state_entries"] == 0 and
            warm["optimizer_state_restored"] is False and warm["optimizer_state_saved"] is False and
            warm["optimizer_initialization"] == "fresh_per_write" and warm["phase_steps"] == 80 and
            warm["parent_cumulative_steps"] == 80 and warm["cumulative_steps"] == 160, "optimizer/seed/step lineage differs")
    unchanged = old.check_states("1e-4", parent["state"], warm, old.state_inventory(adapter))
    return dict(parent=row["parent"], parent_files=parent["parent_files"], adapter=str(adapter),
        adapter_files=trainer._warm_inventory(adapter), parameter_state_unchanged=unchanged, steps=80,
        train_tokens_seen=manifest["train_tokens_seen"], manifest_sha256=base.digest(adapter / "train_manifest.json"))


def execute_arm(root, stage, plan, arm, effective):
    verify(root)
    row = arm_row(stage, plan, arm)
    armroot = Path(row["stage"])
    armroot.mkdir()
    active = dict(plan, lease_end=effective)
    old.write(armroot / "arm.json", dict(row, seed=plan["seed"], config=plan["config"], effective_deadline=effective))
    fit_cost = base.supervise(stage, active, armroot / "fit-worker", fit_command(plan, row))
    fit = verify_fit(plan, row)
    old.write(armroot / "fit-result.json", fit)
    readroot = armroot / "readout"
    readroot.mkdir()
    readplan = copy.deepcopy(plan["parent"]["readout"])
    readplan.update(adapter=row["adapter"], adapter_files=fit["adapter_files"], device=plan["device"],
                    lease_end=float(effective), source_hashes=readout.sources())
    readplan["identity"] = base.expected_identity(readplan, row["adapter"])
    old.seal(readroot, readplan)
    readout.verify(readroot)
    (readroot / "run").mkdir()
    command = [sys.executable, "-B", "-m", "organism_v6.fundamental_teaching_readout", "_worker",
               "--root", str(readroot), "--allow-gpu"]
    read_cost = base.supervise(stage, readplan, readroot / "run/worker", command, readroot / "run/data/calls")
    reduced = readout.reduce(readroot)
    require(reduced["complete"] is True and reduced["counts"]["total"] == 48, "partial capture is not zero")
    scores = score_panel(reduced["rows"], arm=arm)
    require(trainer._warm_inventory(row["adapter"]) == fit["adapter_files"], "readout modified adapter")
    verify(root)
    old.write(armroot / "two-habit-scores.json", scores)
    result = dict(arm=arm, fit=fit, fit_cost=fit_cost, readout_cost=read_cost,
        reduction_sha256=base.digest(readroot / "reduction.json"), scores_sha256=base.digest(armroot / "two-habit-scores.json"),
        counts=scores["counts"])
    old.write(armroot / "result.json", result)
    return result


def release_summary(stage, device):
    receipts = [base.read(path) for path in sorted(stage.glob("**/supervision.json"))]
    require(all(math.isfinite(row["reserved_seconds"]) and row["reserved_seconds"] >= 0 and row["device"] == device
                for row in receipts), "invalid worker cost/device receipt")
    accounted = all((path.parent / "supervision.json").is_file() for path in stage.glob("**/process.json"))
    require(accounted, "worker missing supervision receipt; total worker time unknown")
    released = base.supervisor.gpu_processes_absent(device) is True and all(
        all(row.get(key) is True for key in ("reservation_release_verified", "owned_group_empty", "gpu_processes_absent"))
        for row in receipts)
    return receipts, released


def run(root, allow_gpu=False, clock=None):
    require(allow_gpu is True, "Main allocation and explicit --allow-gpu required")
    started, monotonic = clock if clock is not None else (time.time(), time.monotonic())
    root = Path(root).resolve(strict=True)
    plan = old.read_plan(root)
    device_check(plan["device"])
    require(os.environ.get("CUDA_VISIBLE_DEVICES") == plan["device"], "controller must inherit sealed single GPU")
    effective = bounds(started, plan["deadline"], plan["real_lease_end"])
    stage = prior.fresh(root / "run", (plan["model"], plan["materialroot"], plan["parent"]["parent"]))
    stage.mkdir()
    record = dict(seed=plan["seed"], device=plan["device"], controller_pid=os.getpid(), started=started,
        effective_deadline=effective, real_lease_end=plan["real_lease_end"], plan_sha256=base.digest(root / "plan.json"),
        reservation_scope="entire run controller including CPU/hash/audit/gaps/owned cleanup; offline prepare recorded separately",
        budget_note=plan["budget_note"], logging_note=plan["logging_note"],
        main_full_vacancy_check="Main required before spawn; not performed or certified by this controller")
    old.write(stage / "reservation.json", record)
    completed, error = [], None
    def interrupted(number, frame):
        raise RuntimeError(f"two-habit controller interrupted/cleanup boundary: {number}")
    handlers = {number: signal.signal(number, interrupted) for number in (signal.SIGALRM, signal.SIGTERM, signal.SIGINT)}
    signal.setitimer(signal.ITIMER_REAL, max(.001, effective - time.time() - CLEANUP))
    try:
        verify(root)
        for arm in ARMS:
            require(time.time() < effective - CLEANUP - 10, "per-seed controller window exhausted")
            completed.append(execute_arm(root, stage, plan, arm, effective))
    except BaseException as failure:
        error = dict(type=type(failure).__name__, message=str(failure))
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        try:
            receipts, released = release_summary(stage, plan["device"])
            accounted = True
        except Exception as failure:
            receipts, released, accounted = [], False, False
            error = error or dict(type=type(failure).__name__, message=str(failure))
        ended, elapsed = time.time(), time.monotonic() - monotonic
        worker_seconds = sum(row["reserved_seconds"] for row in receipts) if accounted else None
        success = (error is None and accounted and len(completed) == 2 and len(receipts) == 4 and released and
                   all(row.get("ok") is True and row.get("returncode") == 0 for row in receipts) and
                   ended <= effective and worker_seconds <= elapsed <= SECONDS)
        if not success and error is None:
            error = dict(type="TerminalValidationError",
                         message="arm/worker completeness, cleanup, deadline or worker/full-time accounting failed")
        terminal = dict(record, status="COMPLETE" if success else "FAILED_PARTIAL_NO_RETRY", arms=completed, error=error,
            ended=ended, reserved_seconds=elapsed, worker_reserved_seconds=worker_seconds,
            worker_accounting_complete=accounted, supervised_worker_count=len(receipts) if accounted else None,
            release_verified=released, deadline_met=ended <= effective and elapsed <= SECONDS,
            reused_H_counts=plan["parent"]["baseline"]["counts"], counts_used_for_selection=False,
            claim=material.CLAIM, monetary_cost=None)
        try:
            old.write(stage / "terminal.json", terminal)
        finally:
            for number, handler in handlers.items():
                signal.signal(number, handler)
    require(terminal["status"] == "COMPLETE", "partial seed; inspect terminal.json; no retry/resume")
    return terminal


def main():
    clock = time.time(), time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "run", "status"))
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--helper", default="/tmp/astra_fading_replication_20260912.py")
    parser.add_argument("--state-helper", default="/tmp/astra_fading_sentinel_20260912.py")
    parser.add_argument("--runroot", required=True)
    parser.add_argument("--materialroot")
    parser.add_argument("--parentroot")
    parser.add_argument("--seed", type=int, choices=(0, 1, 2))
    parser.add_argument("--device")
    parser.add_argument("--deadline", type=float)
    parser.add_argument("--lease-end", type=float)
    parser.add_argument("--budget-note")
    parser.add_argument("--logging-note")
    parser.add_argument("--allow-gpu", action="store_true")
    args = parser.parse_args()
    bind(args.source_root, args.helper, args.state_helper)
    if args.stage == "prepare":
        require(all(getattr(args, key) is not None for key in
            ("materialroot", "parentroot", "seed", "device", "deadline", "lease_end", "budget_note", "logging_note")), "missing Main prepare inputs")
        result = prepare(args.runroot, args.materialroot, args.parentroot, args.seed, args.device,
                         args.deadline, args.lease_end, args.budget_note, args.logging_note)
    elif args.stage == "run":
        require(all(getattr(args, key) is None for key in ("seed", "device", "deadline", "lease_end")), "run cannot override sealed allocation")
        result = run(args.runroot, args.allow_gpu, clock=clock)
    else:
        root = Path(args.runroot)
        old.read_plan(root)
        result = base.read(root / "run/terminal.json") if (root / "run/terminal.json").is_file() else dict(
            status="NONTERMINAL_OR_ABANDONED" if (root / "run").exists() else "NOT_STARTED")
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
