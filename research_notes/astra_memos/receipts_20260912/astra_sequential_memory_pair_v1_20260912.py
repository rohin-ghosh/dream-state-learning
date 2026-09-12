"""Seed0 FOUR-source sequential memory allocation pair; Main alone launches."""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
import copy
import datetime as dt
import hashlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import re
import signal
import sys
import tarfile
import threading
import time
import xml.etree.ElementTree as ET


S0_SOURCE_ID = "22b7e528f6f62358981ed2264d30ee7242926160"
HELPER = "/tmp/astra_interleaved_memory_replication_20260912.py"
HELPER_SHA = "dc92b9d18f1fc7e8b9907f304e366de34a5e12340223f8dd17506e007093065f"
SCHEMA = "SEQUENTIAL_MEMORY_PAIR_V1"
STATES = ("S0", "R1", "NEW_ONLY1", "R2", "NEW_ONLY2")
FITS = STATES[1:]
PARENTS = dict(R1="S0", NEW_ONLY1="S0", R2="R1", NEW_ONLY2="NEW_ONLY1")
CUMULATIVE = dict(S0=400, R1=720, NEW_ONLY1=720, R2=1040, NEW_ONLY2=1040)
FIT_SEED = 0
SECONDS, CLEANUP, CUSTODY, LEASE_MARGIN = 5100, 140, 300, 21600
CALLS, WORKERS = 640, 9
CLAIM = "AUTHORED_SEQUENTIAL_FIXED_BUDGET_NOT_NEW_DOSE_MATCHED_NOT_PARENTING"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def valid_sha(value):
    return isinstance(value, str) and len(value) == 64 and all(letter in "0123456789abcdef" for letter in value)


def load_module(path, checksum, name):
    require(valid_sha(checksum), "explicit module SHA256 required")
    payload = Path(path).read_bytes()
    require(hashlib.sha256(payload).hexdigest() == checksum, "module bytes changed: " + str(path))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(payload, str(path), "exec"), module.__dict__)
    return module


def bind(source, source_id):
    global helper, memory, common, old, base, trainer, dev, material, SOURCE_ID
    source = Path(source).expanduser().absolute()
    require(isinstance(source_id, str) and re.fullmatch("[0-9a-f]{40}", source_id) and
        source.name == source_id and source == Path.cwd().resolve(), "use explicitly identified immutable source CWD")
    SOURCE_ID = source_id
    helper = load_module(HELPER, HELPER_SHA, "sequential_replication_helpers")
    memory, common = helper.load("memory"), helper.load("common")
    memory.bind(source, "/tmp/astra_fading_sentinel_20260912.py")
    old, base, trainer, dev = memory.old, memory.base, memory.trainer, memory.dev
    from organism_v6 import sequential_memory_corpus as material
    require(Path(material.__file__).resolve().parent.parent == source, "wrong corpus module source")


def python():
    return os.path.abspath(sys.executable)


def sources():
    require(digest(HELPER) == HELPER_SHA, "frozen helper changed")
    return dict(memory.sources(), **material.source_hashes(), sequential_pair=digest(__file__),
        replication_helpers=HELPER_SHA,
        vacancy_checker=digest(base.REPO / "gpu/astra_mini_sudoku_diagnostic.py"))


def config(model):
    return dict(memory.config(model, FIT_SEED, 10), overflow="truncate")


def bounds(started, deadline, lease_end):
    require(all(type(value) in (int, float) and math.isfinite(value) for value in (started, deadline, lease_end)),
        "finite explicit deadlines required")
    require(base.WORKER_SECONDS == 600 and base.CLEANUP_RESERVE == CLEANUP, "worker bounds changed")
    effective = started + SECONDS
    require(effective <= deadline and effective + CUSTODY <= lease_end - LEASE_MARGIN,
        "full5100+300s required before real lease expiry minus6h")
    return effective


def budget(effective):
    require(time.time() < effective - CLEANUP - 10, "cleanup reserve reached; no next stage")


def checked_root(root):
    root = Path(root).expanduser().absolute()
    require(".." not in root.parts, "parent traversal forbidden")
    return common.unaliased(root)


def model_snapshot(model, files):
    root = Path(model)
    require({str(path.relative_to(root)) for path in root.rglob("*") if path.is_file()} == set(files), "base file membership changed")
    result = {}
    for name in files:
        common.within(name)
        path = root / name
        result[name] = dict(link=os.readlink(path) if path.is_symlink() else None,
            entry=list(common.identity(path.lstat())), target=list(common.identity(path.stat())))
    return result


def parent_path(plan, state):
    require(state in FITS, "unknown fit state")
    parent = PARENTS[state]
    return plan["s0"]["parent"] if parent == "S0" else str(Path(plan["root"]) / "run" / parent / "adapter")


def adapter_path(plan, state):
    require(state in STATES, "unknown saved state")
    return plan["s0"]["parent"] if state == "S0" else str(Path(plan["root"]) / "run" / state / "adapter")


def select_s0(parentroot, plan_sha, native=True):
    parentroot = checked_root(parentroot)
    require(valid_sha(plan_sha) and common.digest(parentroot / "plan.json") == plan_sha, "S0 parent plan pin differs")
    original = old.read_plan(parentroot)
    require(type(original["seed"]) is int and original["seed"] == 0 and original["root"] == str(parentroot) and
        original["source_commit"] == S0_SOURCE_ID and original["source_hashes"]["interleaved_pair"] ==
        helper.DEPENDENCIES["root0_source"][1] and original["arm_order"] == ["SINGLE_VIEW", "FOUR_VIEW"],
        "S0 must be seed0 frozen interleaved FOUR source, never a per-seed winner")
    stage = parentroot / "run/FOUR_VIEW"
    terminal = common.read(parentroot / "run/terminal.json")
    fit = common.read(stage / "fit-result.json")
    parent = stage / "adapter"
    manifest = common.read(parent / "train_manifest.json")
    files = trainer._warm_inventory(parent)
    require(terminal["status"] == "COMPLETE" and terminal["plan_sha256"] == plan_sha and terminal["error"] is None and
        all(terminal[key] is True for key in ("release_verified", "deadline_met", "worker_accounting_complete")) and
        terminal["arms"]["FOUR_VIEW"]["fit"] == fit and fit["adapter"] == str(parent) and
        fit["adapter_files"] == files and (parent / "DONE").is_file(), "S0 technical completion/custody differs")
    require(manifest["config"] == dict(config(original["model"]), seed=0) and manifest["base_model"] == original["model"] and
        manifest["steps"] == 320 and manifest["nonfinite_batches"] == 0 and manifest["empty"] is False and
        math.isfinite(manifest["final_loss"]) and manifest["warm_start"]["parent_cumulative_steps"] == 80 and
        manifest["warm_start"]["cumulative_steps"] == 400 and manifest["warm_start"]["phase_seed"] == 0 and
        manifest["warm_start"]["adapter_count"] == 1, "S0 must be completed400-step seed0 FOUR weights")
    paths = [parentroot / "plan.json", parentroot / "run/terminal.json", stage / "fit-result.json"]
    result = dict(parentroot=str(parentroot), parent_plan_sha256=plan_sha, parent=str(parent), parent_files=files,
        model=original["model"], model_files=original["model_files"], cumulative_steps=400, seed=0, branch="FOUR_VIEW",
        original_teach=str(Path(original["parentroot"]) / "teach.json"),
        provenance={str(path): common.digest(path) for path in paths})
    if native:
        result["state"] = old.state_inventory(parent)
        require(result["state"] == manifest["warm_start"]["final_state"], "S0 saved tensors differ from write manifest")
    return result


def inspect_material(root, teach, tokenizer=None):
    root = checked_root(root)
    manifest = common.read(root / "manifest.json")
    corpus_files = {state: f"cycle{state[-1]}_{'R' if state.startswith('R') else 'NEW_ONLY'}.json" for state in FITS}
    expected = {"candidate.json", "token_audit.json", "readout_cases.json", "readout_requests.json", *corpus_files.values()}
    require(set(manifest["sha256"]) == expected and {path.name for path in root.iterdir()} == expected | {"manifest.json"},
        "exact eight-file material plus manifest required")
    require(all(common.digest(root / name) == checksum for name, checksum in manifest["sha256"].items()), "material hash changed")
    require(manifest["original_teach_path"] == str(teach) and
        manifest["original_teach_sha256"] == common.digest(teach) == material.prior.ORIGINAL_TEACH_SHA256 and
        manifest["source_hashes"] == material.source_hashes(), "original80/native export source differs")
    candidate = common.read(root / "candidate.json")
    material.validate_candidate(candidate)
    cases, requests = material.readout_cases(candidate), material.readout_requests()
    require(common.read(root / "readout_cases.json") == cases and common.read(root / "readout_requests.json") == requests and
        len(cases) == len(requests) == 128 and len({case["id"] for case in cases}) == 128 and
        Counter((case.get("bank"), case.get("surface")) for case in cases if case["kind"] == "memory_recall") ==
        Counter({(bank, surface): 16 for bank in ("M0", "B1", "B2") for surface in ("exact", "dev")}) and
        [case["id"] for case in cases if case["kind"] == "addition"] == [f"eval-addition-{index:03d}" for index in range(32)],
        "combined fixed128-case panel differs")
    require(all(request == dict(call_id=f"{index:04d}", case_id=case["id"], role="readout", arm="readout",
        prompt=case["context"], temperature=0.0, seed=20260912, max_tokens=64)
        for index, (case, request) in enumerate(zip(cases, requests, strict=True))), "fixed answer-free requests changed")
    audit = common.read(root / "token_audit.json")
    require(audit["source_hashes"] == material.source_hashes() and audit["recipe"]["seed"] == FIT_SEED and
        audit["total_planned_updates"] == 1280 and audit["total_target_exposure"] == sum(
            fit["ten_epochs"]["target_tokens"] for cycle in audit["fits"].values() for fit in cycle.values()),
        "fixed native schedule/target budget differs")
    counts = {}
    for state, filename in corpus_files.items():
        cycle, arm = state[-1], "R" if state.startswith("R") else "NEW_ONLY"
        fit = audit["fits"][cycle][arm]
        require(len(common.read(root / filename)["corpus"]) == len(fit["rows"]) == 128 and
            fit["corpus_sha256"] == manifest["sha256"][filename] and len(fit["schedule"]["updates"]) == 320 and
            fit["per_epoch"]["target_tokens"] >= 128 and
            fit["ten_epochs"] == {key: value * 10 for key, value in fit["per_epoch"].items()} and
            sum(update["target_tokens_by_kind"]["memory"] for update in fit["schedule"]["updates"]) == 1280,
            "per-fit native counts/corpus differ")
        counts[state] = fit["per_epoch"]
    if tokenizer is not None:
        exported = material.export_native(candidate, common.read(teach), tokenizer)
        require(exported["audit"] == audit and all(common.read(root / filename) ==
            exported["corpora"][state[-1]]["R" if state.startswith("R") else "NEW_ONLY"]
            for state, filename in corpus_files.items()), "actual native tokenizer/V3 re-audit differs")
    files = dict(manifest["sha256"], **{"manifest.json": common.digest(root / "manifest.json")})
    return dict(files=files, corpus_files=corpus_files, counts=counts, audit_sha256=files["token_audit.json"],
        paired=audit["paired"], source_hashes=audit["source_hashes"], candidate_sha256=files["candidate.json"],
        tokenizer_class=audit["tokenizer_class"], new_dose_matched=False)


def prepare(parentroot, parent_plan_sha, materialroot, root, device, deadline, lease_end):
    bounds(time.time(), deadline, lease_end)
    memory.branches([device] * 3)
    s0 = select_s0(parentroot, parent_plan_sha)
    model = s0["model"]
    root, materialroot = checked_root(root), checked_root(materialroot)
    memory.fresh(root, (parentroot, model, base.REPO, materialroot))
    require(root.parent == materialroot.parent, "fresh run must be beside material")
    model_stat = model_snapshot(model, s0["model_files"])
    require(base.model_hashes(model) == s0["model_files"] and model_snapshot(model, s0["model_files"]) == model_stat,
        "base model bytes differ from S0 or changed while hashing")
    pins = sources()
    tokenizer = base.native_tokenizer(model)
    if not materialroot.exists():
        memory.fresh(materialroot, (parentroot, model, base.REPO, root))
        material.prepare(materialroot, s0["original_teach"], tokenizer)
    exported = inspect_material(materialroot, s0["original_teach"], tokenizer)
    cases, requests = material.readout_cases(), material.readout_requests()
    template = dict(schema=SCHEMA, model=model, model_files=s0["model_files"], device=device,
        cases=cases, requests=requests, native_inputs=dev.native_inputs(tokenizer, requests),
        source_hashes=pins, worker_seconds=600, output_token_ceiling=8192, claim_limits=CLAIM)
    plan = dict(schema=SCHEMA, source_commit=SOURCE_ID, source_root=str(base.REPO), source_hashes=pins,
        root=str(root), materialroot=str(materialroot), material=exported, model=model, model_files=s0["model_files"], model_stat=model_stat,
        s0=s0, python=python(), seed=FIT_SEED, parent_seed=0, source_branch="FOUR_VIEW", config=config(model),
        device=device, states=list(STATES), parents=PARENTS, cumulative_steps=CUMULATIVE, template=template,
        pair_seconds=SECONDS, cleanup_seconds=CLEANUP, external_custody_seconds=CUSTODY, lease_margin_seconds=LEASE_MARGIN,
        deadline=deadline, real_lease_end=lease_end, total_calls=CALLS, total_workers=WORKERS, confirmation_calls=0,
        reduce_only_after_all_captures=True, outcome_selective_skips=False, automatic_progression=False,
        claim=CLAIM, origin="UNRESOLVED_LOCAL_HASHES_ONLY", native_reaudit=True)
    for state in FITS:
        fit_command(plan, state)
    trainer._warm_parent(s0["parent"], adapter_path(plan, "R1"), trainer.TrainConfig(**plan["config"]))
    require(sources() == pins and select_s0(parentroot, parent_plan_sha) == s0 and
        inspect_material(materialroot, s0["original_teach"]) == exported and model_snapshot(model, s0["model_files"]) == model_stat,
        "inputs changed during prepare")
    root.mkdir()
    old.seal(root, plan)
    return dict(status="PREPARED_NOT_LAUNCHED", root=str(root), plan_sha256=common.digest(root / "plan.json"),
        parent_seed=0, phase_seed=FIT_SEED, source_branch="FOUR_VIEW")


def verify(root, current=True):
    root = checked_root(root)
    plan = old.read_plan(root)
    require(plan["schema"] == SCHEMA and plan["root"] == str(root) and plan["source_root"] == str(base.REPO) and
        plan["source_commit"] == SOURCE_ID and plan["source_hashes"] == sources() and plan["python"] == python(),
        "source/root/interpreter changed")
    require(type(plan["seed"]) is int and plan["seed"] == FIT_SEED and type(plan["parent_seed"]) is int and
        plan["parent_seed"] == 0 and plan["source_branch"] == "FOUR_VIEW" and plan["config"] == config(plan["model"]) and
        plan["states"] == list(STATES) and plan["parents"] == PARENTS and plan["cumulative_steps"] == CUMULATIVE and
        plan["pair_seconds"] == SECONDS and plan["cleanup_seconds"] == CLEANUP and
        plan["external_custody_seconds"] == CUSTODY and plan["lease_margin_seconds"] == LEASE_MARGIN and
        plan["total_calls"] == CALLS and plan["total_workers"] == WORKERS and plan["confirmation_calls"] == 0 and
        plan["reduce_only_after_all_captures"] is True and plan["outcome_selective_skips"] is False and
        plan["automatic_progression"] is False and plan["claim"] == CLAIM and plan["native_reaudit"] is True,
        "fixed trajectory/budget/panel contract changed")
    memory.branches([plan["device"]] * 3)
    require(root.parent == Path(plan["materialroot"]).parent, "run/material layout changed")
    template = plan["template"]
    require(template["cases"] == material.readout_cases() and template["requests"] == material.readout_requests() and
        template["model"] == plan["model"] and template["model_files"] == plan["model_files"] and
        template["device"] == plan["device"] and template["source_hashes"] == plan["source_hashes"] and
        template["worker_seconds"] == 600 and template["output_token_ceiling"] == 8192 and
        len(template["native_inputs"]) == 128, "combined readout template changed")
    if current:
        require(select_s0(plan["s0"]["parentroot"], plan["s0"]["parent_plan_sha256"], native=False) ==
            {key: value for key, value in plan["s0"].items() if key != "state"} and
            model_snapshot(plan["model"], plan["model_files"]) == plan["model_stat"] and
            inspect_material(plan["materialroot"], plan["s0"]["original_teach"]) == plan["material"], "immutable inputs changed")
    return plan


def fit_command(plan, state):
    require(state in FITS and plan["config"] == config(plan["model"]), "fixed fit slot/config differs")
    command = [plan["python"], "-B", "-m", "organism_v6.train_adapter_v3", "--corpus",
        str(Path(plan["materialroot"]) / plan["material"]["corpus_files"][state]), "--out", adapter_path(plan, state),
        "--init-adapter", parent_path(plan, state), "--model", plan["model"], "--rank", "8", "--alpha", "16",
        "--dropout", "0.05", "--lr", "0.0003", "--epochs", "10", "--batch-size", "4", "--grad-accum", "1",
        "--seed", str(FIT_SEED), "--no-pack", "--max-len", "512", "--overflow", "truncate"]
    require(asdict(trainer.config_from_args(trainer.build_parser().parse_args(command[4:]))) == plan["config"],
        "native command/config mismatch")
    return command


def panel_root(plan, state):
    require(state in STATES, "unknown panel state")
    return Path(plan["root"]) / "run/panels" / state


def worker_command(plan, state):
    require(state in STATES, "unknown panel state")
    return [plan["python"], "-B", str(Path(__file__).absolute()), "_panel-worker", "--source-root", plan["source_root"],
        "--runroot", plan["root"], "--state", state, "--allow-gpu"]


def panel_plan(plan, state, files, effective):
    result = copy.deepcopy(plan["template"])
    result.update(adapter=adapter_path(plan, state), adapter_files=files, lease_end=effective,
        sequential_binding=dict(state=state, source_root=plan["root"], parent_plan_sha256=plan["s0"]["parent_plan_sha256"],
            source_branch="FOUR_VIEW", parent_seed=0, phase_seed=FIT_SEED, cumulative_steps=CUMULATIVE[state]))
    result["identity"] = base.expected_identity(result, result["adapter"])
    return result


def validate_manifest(plan, state, manifest, parent_files, before, saved):
    require(state in FITS, "unknown fit slot")
    expected = plan["material"]["counts"][state]
    require(manifest["config"] == plan["config"] and manifest["base_model"] == plan["model"] and
        manifest["steps"] == manifest["micro_batches"] == 320 and manifest["epochs_run"] == 10 and
        manifest["nonfinite_batches"] == 0 and manifest["empty"] is False and math.isfinite(manifest["final_loss"]),
        "incomplete/nonfinite/wrong fit")
    corpus = manifest["corpus"]
    require(corpus["sha256"] == plan["material"]["files"][plan["material"]["corpus_files"][state]] and
        corpus["n_items"] == corpus["n_encoded"] == 128 and corpus["n_skipped_no_target"] == 0 and
        all(manifest["truncation"][key] == 0 for key in
            ("items_truncated", "context_tokens_dropped", "target_tokens_dropped", "items_split")), "native corpus/drop/truncation differs")
    require(all(manifest["tokens"][key] == value for key, value in
        dict(total=expected["input_tokens"], context=expected["context_tokens"], target=expected["target_tokens"]).items()) and
        manifest["train_tokens_seen"] == expected["input_tokens"] * 10, "actual native token totals differ")
    warm = manifest["warm_start"]
    require(warm["mode"] == "WEIGHT_WARM_START_FRESH_OPTIMIZER" and warm["parent_path"] == parent_path(plan, state) and
        warm["parent_files"] == warm["parent_files_after"] == parent_files and
        all(warm[key] is True for key in ("parent_unchanged", "base_frozen", "initialized_loaded_state_check")) and
        type(warm["phase_seed"]) is int and warm["phase_seed"] == FIT_SEED and warm["adapter_count"] == 1 and
        warm["optimizer_initial_state_entries"] == 0 and warm["optimizer_state_restored"] is False and
        warm["optimizer_state_saved"] is False and warm["optimizer_initialization"] == "fresh_per_write" and
        warm["phase_steps"] == 320 and warm["parent_cumulative_steps"] == CUMULATIVE[PARENTS[state]] and
        warm["cumulative_steps"] == CUMULATIVE[state], "immediate parent/fresh optimizer/trajectory mismatch")
    old.check_states("sequential", before, warm, saved)
    require(before == warm["initialized_state"] and not warm["dtype_conversions"], "loaded source tensors/dtype changed")


def verify_fit(plan, state, native=True):
    stage = Path(plan["root"]) / "run" / state
    binding = common.read(stage / "input.json")
    require(binding["state"] == state and binding["parent"] == parent_path(plan, state) and
        binding["corpus_sha256"] == plan["material"]["files"][plan["material"]["corpus_files"][state]] and
        binding["parent_files"] == trainer._warm_inventory(binding["parent"]), "fit inputs/immutable parent changed")
    adapter = adapter_path(plan, state)
    files = trainer._warm_inventory(adapter)
    require((Path(adapter) / "DONE").is_file(), "fit checkpoint incomplete")
    manifest = common.read(Path(adapter) / "train_manifest.json")
    saved = old.state_inventory(adapter) if native else manifest["warm_start"]["final_state"]
    validate_manifest(plan, state, manifest, binding["parent_files"], binding["parent_state"], saved)
    return dict(state=state, adapter=adapter, adapter_files=files, saved_state=saved, parent=binding["parent"],
        parent_files=binding["parent_files"], steps=320, cumulative_steps=CUMULATIVE[state],
        input_sha256=common.digest(stage / "input.json"), manifest_sha256=common.digest(Path(adapter) / "train_manifest.json"))


def execute_fit(plan, state, effective):
    budget(effective)
    stage = memory.fresh(Path(plan["root"]) / "run" / state)
    parent = parent_path(plan, state)
    parent_files = trainer._warm_inventory(parent)
    before = old.state_inventory(parent)
    require(before == (plan["s0"]["state"] if PARENTS[state] == "S0" else
        common.read(Path(plan["root"]) / "run" / PARENTS[state] / "fit-result.json")["saved_state"]),
        "wrong immediate parent saved state")
    trainer._warm_parent(parent, adapter_path(plan, state), trainer.TrainConfig(**plan["config"]))
    stage.mkdir()
    old.write(stage / "input.json", dict(state=state, parent=parent, parent_files=parent_files, parent_state=before,
        corpus_sha256=plan["material"]["files"][plan["material"]["corpus_files"][state]]))
    receipt = base.supervise(stage, dict(plan, lease_end=effective), stage / "fit-worker", fit_command(plan, state))
    memory.successful(receipt)
    fit = dict(verify_fit(plan, state), supervision=receipt)
    old.write(stage / "fit-result.json", fit)
    return fit


def execute_panel(plan, state, effective):
    budget(effective)
    root = panel_root(plan, state)
    memory.fresh(root)
    files = trainer._warm_inventory(adapter_path(plan, state))
    require(files == (plan["s0"]["parent_files"] if state == "S0" else
        common.read(Path(plan["root"]) / "run" / state / "fit-result.json")["adapter_files"]), "panel saved adapter changed")
    readplan = panel_plan(plan, state, files, effective)
    root.mkdir()
    old.seal(root, readplan)
    (root / "run").mkdir()
    receipt = base.supervise(root, readplan, root / "run/worker", worker_command(plan, state), root / "run/data/calls")
    memory.successful(receipt)
    capture = capture_receipt(root, readplan)
    require(capture["pairs"] == 128 and trainer._warm_inventory(readplan["adapter"]) == files, "panel incomplete or adapter modified")
    old.write(root / "capture-result.json", capture)
    return capture


def capture_barrier(plan):
    captures = {}
    effective = common.read(Path(plan["root"]) / "run/reservation.json")["effective_deadline"]
    for state in STATES:
        root = panel_root(plan, state)
        readplan = old.read_plan(root)
        files = plan["s0"]["parent_files"] if state == "S0" else common.read(
            Path(plan["root"]) / "run" / state / "fit-result.json")["adapter_files"]
        require(readplan == panel_plan(plan, state, files, effective) and
            trainer._warm_inventory(readplan["adapter"]) == files, "saved panel/template/adapter changed")
        captures[state] = capture_receipt(root, readplan)
        require(captures[state] == common.read(root / "capture-result.json") and captures[state]["pairs"] == 128,
            "all640 captures required before any reducer")
    return captures


def reduce_all(plan, captures, effective, results=None):
    require(captures == capture_barrier(plan) and sum(item["pairs"] for item in captures.values()) == CALLS,
        "all640 captures required before any reducer")
    for state in STATES:
        require(not (panel_root(plan, state) / "reduction.json").exists(), "no resume/reduction before barrier")
    results = {} if results is None else results
    require(not results, "fresh reduction results required")
    for state in STATES:
        budget(effective)
        root = panel_root(plan, state)
        readplan = old.read_plan(root)
        responses, receipt = audit_panel(root, readplan, worker_command(plan, state))
        rows = []
        for case, response in zip(readplan["cases"], responses, strict=True):
            score = dev.score_addition(response["text"], case["expected"]) if case["kind"] == "addition" else dev.score_memory(response["text"], case["expected"])
            rows.append(dict(case_id=case["id"], kind=case["kind"], bank=case.get("bank"), surface=case.get("surface"), **score))
        memory_counts = {bank: {surface: dict(total=16,
            correct=sum(row["correct"] for row in rows if row["bank"] == bank and row["surface"] == surface),
            invalid=sum(not row["valid"] for row in rows if row["bank"] == bank and row["surface"] == surface))
            for surface in ("exact", "dev")} for bank in ("M0", "B1", "B2")}
        additions = [row for row in rows if row["kind"] == "addition"]
        result = dict(complete=True, state=state, rows=rows, counts=dict(total=128, memory=memory_counts,
            addition=dict(total=32, correct_action=sum(row["correct_action"] for row in additions),
                adherence=sum(row["adherence"] for row in additions))), plan_sha256=common.digest(root / "plan.json"),
            capture_sha256=captures[state]["capture_sha256"], barrier=captures, cost=base.usage(root / "run/data"),
            reserved_seconds=receipt["reserved_seconds"], claim=CLAIM, gate_evaluated=False)
        old.write(root / "reduction.json", result)
        results[state] = result
    return results


def capture_receipt(readroot, template):
    data = readroot / "run/data"
    require(base.read(data / "manifest.json")["files"] == base.tree_hashes(data, ("manifest.json",)), "raw capture hash inventory changed")
    expected = {request["call_id"] + suffix for request in template["requests"] for suffix in (".request.json", ".response.json")}
    require({path.name for path in (data / "calls").iterdir()} == expected, "missing/extra raw response pairs, not a scientific zero")
    return dict(plan_sha256=base.digest(readroot / "plan.json"), capture_sha256=base.digest(data / "manifest.json"),
        pairs=len(template["requests"]), status="CAPTURED_NOT_REDUCED")


def audit_worker(stage, command, device, required=False):
    process_path, receipt_path = stage / "process.json", stage / "supervision.json"
    require(process_path.exists() == receipt_path.exists(), "orphan worker custody; no retry")
    if not process_path.exists():
        require(not required, "required worker missing")
        return None
    process, receipt = base.read(process_path), base.read(receipt_path)
    require(process["argv"] == command and process["device"] == device and type(process["pid"]) is int and
        process["pid"] > 1 and process["pgid"] == process["pid"] and math.isfinite(process["started"]) and
        math.isfinite(process["timeout"]) and 0 < process["timeout"] <= 600 and receipt["device"] == device and
        math.isfinite(receipt["reserved_seconds"]) and receipt["reserved_seconds"] >= 0 and
        all(receipt[key] is True for key in ("reservation_release_verified", "owned_group_empty", "gpu_processes_absent")), "worker custody/release changed")
    if required: memory.successful(receipt)
    return process, receipt


def audit_panel(readroot, plan, command):
    process, receipt = audit_worker(readroot / "run/worker", command, plan["device"], True)
    data = readroot / "run/data"
    capture_receipt(readroot, plan)
    require(not (data / "failure.json").exists() and base.read(data / "backend.cleanup.json")["closed"] is True and
        base.read(data / "identity.json") == dict(backend=plan["identity"], model_files=plan["model_files"], adapter_files=plan["adapter_files"]), "backend capture/cleanup changed")
    ready = base.read(data / "backend.ready.json")
    require(ready["pid"] == process["pid"] and process["started"] <= ready["ready"] <= process["started"] + receipt["reserved_seconds"], "backend ownership changed")
    previous, responses = ready["ready"], []
    for request, native in zip(plan["requests"], plan["native_inputs"], strict=True):
        stem = data / "calls" / request["call_id"]
        sent, received = base.read(str(stem) + ".request.json"), base.read(str(stem) + ".response.json")
        response = received["response"]
        require(sent["request"] == request and sent["identity"] == plan["identity"] and
            sent["prompt_sha256"] == base.value_hash(request["prompt"]) and received["response_sha256"] == base.value_hash(response) and
            previous <= sent["started"] <= received["ended"] <= process["started"] + receipt["reserved_seconds"], "raw call binding/clock changed")
        base.validate_response(request, response)
        require(all(response[key] == native[key] for key in ("rendered_prompt", "prompt_token_ids")), "raw native prefix changed")
        previous = received["ended"]
        responses.append(response)
    require(base.usage(data) == base.read(data / "usage.json"), "usage changed")
    return responses, receipt


def check_uuid(expected, gpu, xml):
    require(isinstance(expected, str) and expected.startswith("GPU-") and gpu["gpu_uuid"] == expected and
        [node.text for node in ET.fromstring(xml).findall("gpu/uuid")] == [expected], "GPU UUID changed")


def panel_worker(root, state):
    parent_pid = os.getppid()
    require(parent_pid > 1, "supervised parent required")
    plan = verify(root, current=False)
    readroot = panel_root(plan, state)
    readplan = old.read_plan(readroot)
    reservation = common.read(Path(root) / "run/reservation.json")
    files = trainer._warm_inventory(adapter_path(plan, state))
    require(readplan == panel_plan(plan, state, files, reservation["effective_deadline"]) and
        model_snapshot(plan["model"], plan["model_files"]) == plan["model_stat"] and
        base.supervisor.selected_device() == plan["device"], "native panel/adapter/device identity changed")
    process_path = readroot / "run/worker/process.json"
    until = time.monotonic() + 5
    while not process_path.exists() and time.monotonic() < until:
        time.sleep(.05)
    process = common.read(process_path)
    require(process["pid"] == process["pgid"] == os.getpid() == os.getpgrp() and
        process["argv"] == worker_command(plan, state) and os.getppid() == parent_pid, "owned worker identity differs")
    stop = threading.Event()
    end = time.monotonic() + 600
    def interrupted(number, frame):
        raise RuntimeError(f"panel worker interrupted: {number}")
    def watch():
        while not stop.wait(.2):
            if os.getppid() != parent_pid or time.monotonic() >= end or time.time() >= readplan["lease_end"] - 10:
                os.killpg(os.getpgrp(), signal.SIGTERM)
                return
    handlers = {number: signal.signal(number, interrupted) for number in (signal.SIGTERM, signal.SIGINT)}
    watcher = threading.Thread(target=watch, daemon=True)
    watcher.start()
    try:
        dev.capture(readplan, base.fresh_directory(readroot / "run/data", plan["model"]))
    finally:
        stop.set()
        watcher.join()
        for number, handler in handlers.items():
            signal.signal(number, handler)


def worker_specs(plan):
    result = []
    for state in STATES:
        if state in FITS:
            result.append((Path(plan["root"]) / "run" / state / "fit-worker", fit_command(plan, state)))
        result.append((panel_root(plan, state) / "run/worker", worker_command(plan, state)))
    return result


def account_workers(plan, required=False):
    workers, visited = [], set()
    for stage, command in worker_specs(plan):
        worker = audit_worker(stage, command, plan["device"], required)
        if worker:
            workers.append(worker)
            visited.add(stage / "process.json")
    runroot = Path(plan["root"]) / "run"
    require(visited == set(runroot.glob("**/process.json")) and
        {path.parent / "supervision.json" for path in visited} == set(runroot.glob("**/supervision.json")), "unaccounted workers")
    require(all(left[0]["started"] + left[1]["reserved_seconds"] <= right[0]["started"]
        for left, right in zip(workers, workers[1:])), "workers overlap or are reordered")
    return workers


def run(root, allow_gpu=False, clock=None):
    require(allow_gpu, "Main allocation plus explicit --allow-gpu required")
    started, monotonic = clock or (time.time(), time.monotonic())
    plan = verify(root)
    effective = bounds(started, plan["deadline"], plan["real_lease_end"])
    require(base.supervisor.selected_device() == plan["device"], "Main initial device differs")
    runroot = memory.fresh(Path(root) / "run")
    runroot.mkdir()
    (runroot / "panels").mkdir()
    reservation = dict(controller_pid=os.getpid(), device=plan["device"], seed=FIT_SEED, parent_seed=0,
        started=started, started_monotonic=monotonic, effective_deadline=effective,
        real_lease_end=plan["real_lease_end"], external_custody_deadline=effective + CUSTODY,
        plan_sha256=common.digest(Path(root) / "plan.json"), continuous_reservation=True)
    old.write(runroot / "reservation.json", reservation)
    require(signal.getitimer(signal.ITIMER_REAL) == (0., 0.), "nested timer forbidden")
    def interrupted(number, frame):
        raise RuntimeError(f"controller cleanup boundary/interruption: {number}")
    handlers = {number: signal.signal(number, interrupted) for number in (signal.SIGALRM, signal.SIGTERM, signal.SIGINT)}
    signal.setitimer(signal.ITIMER_REAL, max(.001, effective - time.time() - CLEANUP))
    fits, captures, reductions, error = {}, {}, {}, None
    try:
        for state in STATES:
            budget(effective)
            if state in FITS:
                fits[state] = execute_fit(plan, state, effective)
            captures[state] = execute_panel(plan, state, effective)
        reduce_all(plan, captures, effective, reductions)
    except BaseException as failure:
        error = dict(type=type(failure).__name__, message=str(failure))
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        workers, released, accounted = [], False, False
        try:
            workers = account_workers(plan)
            accounted = True
            released = bool(workers) and all(all(receipt[key] is True for key in
                ("reservation_release_verified", "owned_group_empty", "gpu_processes_absent")) for _, receipt in workers)
        except Exception as failure:
            error = error or dict(type=type(failure).__name__, message=str(failure))
        ended, elapsed = time.time(), time.monotonic() - monotonic
        complete = (error is None and set(fits) == set(FITS) and set(captures) == set(reductions) == set(STATES) and
            len(workers) == WORKERS and released and accounted and ended <= effective and elapsed <= SECONDS and
            all(receipt["ok"] is True and receipt["returncode"] == 0 for _, receipt in workers))
        terminal = dict(reservation, status="COMPLETE" if complete else "FAILED_PARTIAL_NO_RETRY",
            fits=fits, captured=captures, reductions=reductions, error=error, ended=ended, reserved_seconds=elapsed,
            worker_reserved_seconds=sum(receipt["reserved_seconds"] for _, receipt in workers),
            worker_accounting_complete=accounted, release_verified=released, deadline_met=ended <= effective and elapsed <= SECONDS,
            automatic_progression=False, gate_evaluated=False, budget_extended=False, claim=CLAIM,
            origin="UNRESOLVED_LOCAL_HASHES_ONLY")
        old.write(runroot / "terminal.json", terminal)
        for number, handler in handlers.items():
            signal.signal(number, handler)
    require(terminal["status"] == "COMPLETE", "partial trajectory; preserve; no retry/resume/progression")
    return dict(status="COMPLETE_640_CAPTURED_THEN_REDUCED_MAIN_REVIEW_PENDING", terminal=str(runroot / "terminal.json"))


def launch_record(root, plan):
    launch = common.read(Path(root) / "launch/launch.json")
    expected = [plan["python"], "-B", str(Path(__file__).absolute()), "run", "--source-root", plan["source_root"],
        "--source-id", plan["source_commit"], "--runroot", plan["root"], "--allow-gpu"]
    require(launch["root"] == plan["root"] and launch["source"] == plan["source_root"] and
        launch["source_commit"] == plan["source_commit"] and launch["plan_sha256"] == common.digest(Path(root) / "plan.json") and
        launch["script_sha256"] == digest(__file__) and launch["device"] == plan["device"] and
        type(launch["seed"]) is int and launch["seed"] == FIT_SEED and launch["parent_seed"] == 0 and
        launch["source_branch"] == "FOUR_VIEW" and launch["parent_plan_sha256"] == plan["s0"]["parent_plan_sha256"] and
        launch["s0_adapter_files"] == plan["s0"]["parent_files"] and launch["controller_bound_seconds"] == SECONDS and
        launch["external_collection_margin_seconds"] == CUSTODY and launch["generation_calls"] == CALLS and
        launch["worker_count"] == WORKERS and type(launch["pid"]) is int and launch["pid"] > 1 and launch["command"] == expected,
        "launch plan/source/seed/S0/bounds/command mismatch")
    check_uuid(launch["gpu"]["gpu_uuid"], launch["gpu"], common.read_bytes(Path(root) / "launch/gpu.xml"))
    return launch


def status(root):
    plan = verify(root, current=False)
    launch = launch_record(root, plan) if (Path(root) / "launch/launch.json").exists() else None
    return dict(controller_pid=launch["pid"] if launch else None,
        controller_present=Path(f"/proc/{launch['pid']}").exists() if launch else None,
        terminal_available=(Path(root) / "run/terminal.json").is_file(),
        states={state: dict(fit_available=state == "S0" or (Path(root) / "run" / state / "fit-result.json").is_file(),
            capture_available=(panel_root(plan, state) / "capture-result.json").is_file(),
            reduction_available=(panel_root(plan, state) / "reduction.json").is_file()) for state in STATES})


def audit_terminal(root, plan, terminal, launch):
    reservation = common.read(Path(root) / "run/reservation.json")
    require(all(terminal[key] == value for key, value in reservation.items()) and
        terminal["controller_pid"] == launch["pid"] and terminal["device"] == plan["device"] and
        terminal["seed"] == FIT_SEED and terminal["parent_seed"] == 0 and
        terminal["plan_sha256"] == common.digest(Path(root) / "plan.json") and
        terminal["effective_deadline"] == bounds(terminal["started"], plan["deadline"], plan["real_lease_end"]) and
        terminal["external_custody_deadline"] == terminal["effective_deadline"] + CUSTODY and
        terminal["real_lease_end"] == plan["real_lease_end"] and terminal["worker_accounting_complete"] is True and
        terminal["gate_evaluated"] is False and terminal["automatic_progression"] is False and terminal["budget_extended"] is False,
        "terminal launch/reservation/bounds differ")
    require(terminal["status"] in ("COMPLETE", "FAILED_PARTIAL_NO_RETRY") and
        math.isfinite(terminal["reserved_seconds"]) and terminal["reserved_seconds"] >= 0 and
        terminal["deadline_met"] == (terminal["ended"] <= terminal["effective_deadline"] and terminal["reserved_seconds"] <= SECONDS),
        "terminal completion/clock differs")
    complete = terminal["status"] == "COMPLETE"
    workers = account_workers(plan, complete)
    require(sum(receipt["reserved_seconds"] for _, receipt in workers) == terminal["worker_reserved_seconds"] and
        all(terminal["started_monotonic"] <= process["started"] and
            process["started"] + receipt["reserved_seconds"] <= terminal["started_monotonic"] + terminal["reserved_seconds"]
            for process, receipt in workers), "worker accounting differs")
    if complete:
        require(terminal["error"] is None and terminal["deadline_met"] is True and terminal["release_verified"] is True and
            len(workers) == WORKERS and set(terminal["fits"]) == set(FITS) and
            set(terminal["captured"]) == set(terminal["reductions"]) == set(STATES), "complete terminal missing work")
    barrier = capture_barrier(plan) if complete or terminal["reductions"] else None
    reports = {}
    for state in STATES:
        if state in FITS:
            fit_path = Path(root) / "run" / state / "fit-result.json"
            if fit_path.exists():
                fit = common.read(fit_path)
                require(verify_fit(plan, state, native=False) == {key: value for key, value in fit.items() if key != "supervision"} and
                    fit == terminal["fits"][state] and fit["supervision"] ==
                    common.read(fit_path.parent / "fit-worker/supervision.json"), "saved fit/terminal differs")
            else:
                require(not complete and state not in terminal["fits"], "missing completed fit")
        readroot = panel_root(plan, state)
        if not (readroot / "run/data/manifest.json").exists():
            require(not complete and state not in terminal["captured"] and not (readroot / "reduction.json").exists(),
                "missing raw panel is not a zero")
            reports[state] = "PARTIAL_OR_NOT_STARTED_NOT_SCORED"
            continue
        files = plan["s0"]["parent_files"] if state == "S0" else common.read(Path(root) / "run" / state / "fit-result.json")["adapter_files"]
        readplan = old.read_plan(readroot)
        require(readplan == panel_plan(plan, state, files, terminal["effective_deadline"]), "panel binding changed")
        _, receipt = audit_panel(readroot, readplan, worker_command(plan, state))
        captured = capture_receipt(readroot, readplan)
        require(captured == common.read(readroot / "capture-result.json") and captured == terminal["captured"][state],
            "terminal raw capture changed")
        reports[state] = dict(captured)
        reduction_path = readroot / "reduction.json"
        if reduction_path.exists():
            reduced = common.read(reduction_path)
            require(barrier is not None and reduced["barrier"] == barrier and reduced == terminal["reductions"][state] and
                reduced["complete"] is True and reduced["counts"]["total"] == len(reduced["rows"]) == 128 and
                [row["case_id"] for row in reduced["rows"]] == [case["id"] for case in readplan["cases"]] and
                reduced["plan_sha256"] == common.digest(readroot / "plan.json") and
                reduced["capture_sha256"] == captured["capture_sha256"] and reduced["reserved_seconds"] == receipt["reserved_seconds"] and
                reduced["cost"] == base.usage(readroot / "run/data"), "stored reduction/capture barrier changed")
            reports[state]["reduction_sha256"] = common.digest(reduction_path)
        else:
            require(not complete and state not in terminal["reductions"], "complete terminal missing reduction")
    return reports


def collection_inputs(plan):
    paths = {"material/" + name: Path(plan["materialroot"]) / name for name in plan["material"]["files"]}
    paths["original_teach.json"] = Path(plan["s0"]["original_teach"])
    for index, path in enumerate(plan["s0"]["provenance"]):
        paths[f"s0_provenance/{index}-{Path(path).name}"] = Path(path)
    for name in common.metadata(Path(plan["s0"]["parent"]), Path(plan["s0"]["parent"]).parent):
        paths["s0/" + str(Path(name).relative_to(Path(plan["s0"]["parent"]).name))] = Path(plan["s0"]["parent"]).parent / name
    code = [Path(__file__), Path(HELPER), Path(material.__file__), Path(material.prior.__file__),
        Path(material.original.__file__), Path(trainer.__file__), Path(dev.__file__),
        Path(base.__file__), Path(memory.__file__), Path(common.__file__), Path(old.__file__)]
    code += [Path(path) for path, _ in helper.DEPENDENCIES.values()]
    for path in code:
        key = "code/" + path.name
        require(key not in paths or paths[key] == path, "code archive name collision")
        paths[key] = path
    return paths


def collect_body(root, archive):
    root = checked_root(root)
    observed = status(root)
    require(observed["controller_present"] is False and observed["terminal_available"], "absent controller plus terminal required")
    plan = verify(root)
    archive = memory.fresh(archive, (root, plan["materialroot"], plan["s0"]["parentroot"], plan["model"], base.REPO))
    validation = Path(str(archive) + ".validation.json")
    release_json, release_xml = root / "run/main_release.json", root / "run/main_release.xml"
    require(not any(path.exists() or path.is_symlink() for path in (validation, release_json, release_xml)), "fresh custody outputs required")
    launch = launch_record(root, plan)
    terminal = common.read(root / "run/terminal.json")
    reports = audit_terminal(root, plan, terminal, launch)
    before = common.metadata(root, root.parent)
    inputs = collection_inputs(plan)
    input_hashes = {name: common.digest(path) for name, path in inputs.items()}
    from gpu.astra_mini_sudoku_diagnostic import check_free
    gpu, xml = check_free(plan["device"])
    check_uuid(launch["gpu"]["gpu_uuid"], gpu, xml)
    require(not Path(f"/proc/{launch['pid']}").exists() and common.metadata(root, root.parent) == before and
        {name: common.digest(path) for name, path in inputs.items()} == input_hashes and verify(root) == plan,
        "evidence/input/controller changed during custody")
    now = time.time()
    started = dt.datetime.fromisoformat(launch["started_utc"]).timestamp()
    require(started <= terminal["started"] <= now <= min(terminal["external_custody_deadline"], started + SECONDS + CUSTODY),
        "global90min collection window exceeded; preserve for Main reconciliation")
    common.write_new(release_xml, xml.encode())
    common.write_json(release_json, dict(full_release=True, controller_absent=True, device=plan["device"], gpu=gpu,
        full_reservation_seconds=now-started, controller_reserved_seconds=terminal["reserved_seconds"],
        worker_reserved_seconds=terminal["worker_reserved_seconds"], budget_extended=False,
        terminal_sha256=common.digest(root / "run/terminal.json"), launch_sha256=common.digest(root / "launch/launch.json"),
        plan_sha256=common.digest(root / "plan.json"), xml_sha256=common.digest(release_xml),
        accounting="overlapping intervals; do not add worker/controller/full reservation"))
    manifest = common.metadata(root, root.parent)
    payload_paths = {name: root.parent / name for name in manifest}
    for name, path in inputs.items():
        member = root.name + "/inputs/" + name
        require(member not in manifest, "archive input collision")
        manifest[member], payload_paths[member] = input_hashes[name], path
    with archive.open("xb") as stream, tarfile.open(fileobj=stream, mode="w:gz", format=tarfile.USTAR_FORMAT) as bundle:
        for name, checksum in sorted(manifest.items()):
            payload = common.read_bytes(payload_paths[name])
            require(hashlib.sha256(payload).hexdigest() == checksum, "metadata changed during packaging")
            member = tarfile.TarInfo(name)
            member.size, member.mode = len(payload), 0o600
            bundle.addfile(member, io.BytesIO(payload))
    common.validate_archive(io.BytesIO(common.read_bytes(archive)), manifest, root.name + "/")
    require(all(common.digest(path) == manifest[name] for name, path in payload_paths.items()), "source changed after packaging")
    require(time.time() <= min(terminal["external_custody_deadline"], started + SECONDS + CUSTODY), "collection exceeded global ceiling")
    common.write_json(validation, dict(archive=str(archive), sha256=common.digest(archive), files=manifest,
        terminal_status=terminal["status"], reports=reports, plan_sha256=common.digest(root / "plan.json"),
        parent_seed=0, phase_seed=FIT_SEED, source_branch="FOUR_VIEW", total_expected_calls=640,
        native_model_or_tokenizer_rerun=False, reducers_rerun=False, weights="preserved native; not archived",
        source_commit=plan["source_commit"], new_dose_matched=False, budget_extended=False,
        authorship="driver author custody validation; not independent raw review"))
    return dict(status="COLLECTED_NO_NEW_SCORES", archive=str(archive), sha256=common.digest(archive), terminal_status=terminal["status"])


def collect(root, archive):
    require(signal.getitimer(signal.ITIMER_REAL) == (0., 0.), "nested timer forbidden")
    terminal = common.read(Path(root) / "run/terminal.json")
    remaining = min(CUSTODY, terminal["external_custody_deadline"] - time.time())
    require(remaining > 0, "custody deadline already expired; Main must reconcile")
    def expired(number, frame):
        raise TimeoutError("bounded collection expired; preserve partial outputs")
    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, remaining)
    try:
        return collect_body(root, archive)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def main():
    clock = time.time(), time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "verify", "run", "status", "collect", "_panel-worker"))
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--runroot", required=True)
    parser.add_argument("--parentroot")
    parser.add_argument("--parent-plan-sha256")
    parser.add_argument("--materialroot")
    parser.add_argument("--device")
    parser.add_argument("--deadline", type=float)
    parser.add_argument("--lease-end", type=float)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--state", choices=STATES)
    parser.add_argument("--allow-gpu", action="store_true")
    args = parser.parse_args()
    bind(args.source_root, args.source_id)
    root = checked_root(args.runroot)
    if args.stage == "prepare":
        require(all(getattr(args, key) is not None for key in
            ("parentroot", "parent_plan_sha256", "materialroot", "device", "deadline", "lease_end")), "missing prepare arguments")
        result = prepare(args.parentroot, args.parent_plan_sha256, args.materialroot, root, args.device, args.deadline, args.lease_end)
    elif args.stage == "run":
        result = run(root, args.allow_gpu, clock)
    elif args.stage == "status":
        result = status(root)
    elif args.stage == "collect":
        require(args.archive is not None, "exclusive --archive required")
        result = collect(root, args.archive)
    elif args.stage == "_panel-worker":
        require(args.allow_gpu and args.state in STATES, "explicit supervised state worker required")
        panel_worker(root, args.state)
        result = dict(status="CAPTURED_NOT_REDUCED")
    else:
        verify(root)
        result = dict(status="VERIFIED_NOT_LAUNCH_AUTHORITY")
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False), flush=True)


if __name__ == "__main__":
    main()
