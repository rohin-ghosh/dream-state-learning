"""Versioned seeds1/2 interleaved replication; explicit Main gate, no auto launch."""
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
import signal
import sys
import tarfile
import threading
import time
import xml.etree.ElementTree as ET


SOURCE_ID = "22b7e528f6f62358981ed2264d30ee7242926160"
DEPENDENCIES = {
    "root0_source": ("/tmp/astra_interleaved_memory_pair_20260912.py", "d100cb58296499c7cd6489d20e96528898f2e48b698147a97dae99fa38946bbe"),
    "replay_source": ("/tmp/astra_memory_replay_20260912.py", "1586ddf7d690ce8bc55d680bd926439fbd597236ea8e76394f88a3bdf023c8bc"),
    "paired_source": ("/tmp/astra_varied_memory_pair_20260912.py", "b58f65cd482bbd2d762edc030c7967a1ecd004829cf8271c74c15d3ca54bc8c7"),
    "memory": ("/tmp/astra_memory_only_20260912.py", "ac7a110bc74724fc592407ced854ad162da275d3de9d9eeeb40c19788416afdb"),
    "common": ("/tmp/astra_collect_memory_only_20260912.py", "d2152c179ca9a6b9801933a480ed62cd203018868a52034e13676963787579eb"),
}
ARMS = ("SINGLE_VIEW", "FOUR_VIEW")
PANELS = {"dev": 48, "exact": 16, "lexical": 48}
SECONDS, CLEANUP, CUSTODY = 1800, 140, 300
LEASE_MARGIN = 6 * 3600
SCHEMA = "INTERLEAVED_MEMORY_REPLICATION_V1"
GATE_SCHEMA = "INTERLEAVED_SEED0_MAIN_GATE_V1"
SEEDS = (1, 2)
COUNTS = {arm: dict(items=128, epochs=10, steps=320, cumulative_steps=400,
    input_per_epoch=inputs, context_per_epoch=inputs-1000, target_per_epoch=1000,
    input_presentations=inputs*10, context_presentations=(inputs-1000)*10, target_presentations=10000,
    presentations_per_source=40) for arm, inputs in (("SINGLE_VIEW", 6616), ("FOUR_VIEW", 6712))}
CLAIM = "AUTHORED_INTERLEAVED_DIAGNOSTIC_NOT_CHILD_EXPERIENCE_NOT_PARENTING_GATE"
PROGRESSION = dict(owner="Main", qualifying_arm="FOUR_VIEW", dev_memory_min=15, exact_memory_min=15,
    dev_habit_min=30, dev_act_min=31, each_lexical_family_min=15, eligible_next_seeds=[1, 2],
    single_scores_irrelevant=True, decide_only_after_both_technical_complete=True,
    automatic_progression=False, gate_evaluated_by_wrapper=False)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def load(name):
    path, checksum = DEPENDENCIES[name]
    payload = Path(path).read_bytes()
    require(hashlib.sha256(payload).hexdigest() == checksum, "helper pin changed: " + name)
    spec = importlib.util.spec_from_file_location("interleaved_" + name, path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(payload, path, "exec"), module.__dict__)
    return module


def python():
    return os.path.abspath(sys.executable)


def bind(source):
    global memory, common, old, base, trainer, dev, exact, material
    source = Path(source).resolve(strict=True)
    require(source.name == SOURCE_ID and Path.cwd().resolve() == source, "use immutable22b7e528 source CWD")
    memory, common = load("memory"), load("common")
    memory.bind(source, "/tmp/astra_fading_sentinel_20260912.py")
    old, base, trainer, dev, exact = memory.old, memory.base, memory.trainer, memory.dev, memory.exact
    from organism_v6 import interleaved_memory_replay_corpus as material
    require(Path(material.__file__).resolve().parent.parent == source == base.REPO.resolve(), "wrong imported source")


def sources():
    for path, checksum in DEPENDENCIES.values():
        require(base.digest(path) == checksum, "frozen dependency changed")
    return dict(memory.sources(), **material.source_hashes(), interleaved_replication=base.digest(__file__),
        dependencies={name: base.digest(path) for name, (path, _) in DEPENDENCIES.items()},
        vacancy_checker=base.digest(base.REPO / "gpu/astra_mini_sudoku_diagnostic.py"))


def bounds(started, deadline, lease_end):
    require(all(type(value) in (int, float) and math.isfinite(value) for value in (started, deadline, lease_end)), "invalid deadline")
    require(base.WORKER_SECONDS == 600 and base.CLEANUP_RESERVE == CLEANUP, "native bounds changed")
    effective = started + SECONDS
    require(effective <= deadline and effective + CUSTODY <= lease_end - LEASE_MARGIN, "full1800+300s window required before real lease minus6h")
    return effective


def budget(effective):
    require(time.time() < effective - CLEANUP - 10, "less than150s left; no next worker/reduction")


def cue_cases():
    candidate = material.build_candidate()
    material.validate_candidate(candidate)
    return [dict(row, kind="memory") for row in candidate["heldout_cues"]]


def cue_requests(cases):
    require(cases == cue_cases(), "fixed lexical cases changed")
    return [dict(call_id=f"{index:04d}", case_id=row["id"], role="lexical_memory", arm="readout",
        prompt=row["context"], temperature=0.0, seed=20260912, max_tokens=64) for index, row in enumerate(cases)]


def cue_template(model, model_files, tokenizer, device, lease_end):
    cases = cue_cases()
    requests = cue_requests(cases)
    plan = dict(schema=1, label="NEW_LEXICAL_CUES_SAME16_FACTS_NOT48_INDEPENDENT_FACTS", model=model,
        model_files=model_files, adapter=None, adapter_files={}, device=device, lease_end=float(lease_end),
        cases=cases, requests=requests, native_inputs=dev.native_inputs(tokenizer, requests), source_hashes=sources(),
        worker_seconds=600, output_token_ceiling=3072, claim_limits=CLAIM)
    plan["identity"] = base.expected_identity(plan, None)
    return plan


def parent_identity(root, seed):
    require(type(seed) is int and seed in SEEDS, "replication seeds1/2 only")
    root = Path(root)
    common.unaliased(root)
    receipt = "verified.json"
    paths = (root / "plan.json", root / "fit_teach" / receipt, root / "readouts/teach/plan.json")
    require(tuple(base.digest(path) for path in paths) == memory.PINS[str(seed)], "not original corresponding seed parent pins")
    original = old.read_plan(root)
    require(original["config"]["seed"] == seed, "original parent optimizer seed mismatch")


def gate_receipt(path, checksum, bound):
    path = Path(path).expanduser().absolute()
    common.unaliased(path)
    require(isinstance(checksum, str) and len(checksum) == 64 and base.digest(path) == checksum, "Main gate hash mismatch")
    gate = common.read(path)
    require(gate["schema"] == GATE_SCHEMA and gate["owner"] == "Main" and
        gate["decision"] == "ALLOW_SEEDS_1_2" and gate["eligible_seeds"] == [1, 2] and
        gate["criteria"] == PROGRESSION and gate["raw_review_verdict"] == "PASS", "explicit verified seed0 gate required")
    evidence = {str(path): checksum}
    for key in ("seed0_plan", "seed0_terminal", "seed0_validation", "raw_review"):
        item = gate[key]
        source = Path(item["path"])
        require(source.is_absolute(), "absolute gate evidence path required")
        common.unaliased(source)
        require(base.digest(source) == item["sha256"], "gate evidence changed: " + key)
        evidence[str(source)] = item["sha256"]
    original = common.read(gate["seed0_plan"]["path"])
    terminal = common.read(gate["seed0_terminal"]["path"])
    validation = common.read(gate["seed0_validation"]["path"])
    root0 = Path(original["root"])
    require(Path(gate["seed0_plan"]["path"]) == root0 / "plan.json" and
        Path(gate["seed0_terminal"]["path"]) == root0 / "run/terminal.json", "gate root/path mismatch")
    require(type(original["seed"]) is int and original["seed"] == 0 and original["source_commit"] == SOURCE_ID and
        original["source_hashes"]["interleaved_pair"] == DEPENDENCIES["root0_source"][1] and
        original["arm_order"] == list(ARMS) and original["panels"] == PANELS and original["total_calls"] == 224 and
        original["progression"] == PROGRESSION and original["parentroot"] == bound["material_parentroot"] and
        original["materialroot"] == bound["materialroot"] and original["material_files"] == bound["material_files"] and
        original["model"] == bound["model"] and original["model_files"] == bound["model_files"] and
        original["config"] == dict(memory.config(bound["model"], 0, 10), overflow="truncate"),
        "gate is not this frozen seed0 material/parent/panel")
    require(terminal["status"] == "COMPLETE" and terminal["seed"] == 0 and terminal["error"] is None and
        all(terminal[key] is True for key in ("release_verified", "deadline_met", "worker_accounting_complete")) and
        terminal["plan_sha256"] == gate["seed0_plan"]["sha256"] and validation["terminal_status"] == "COMPLETE" and
        validation["plan_sha256"] == gate["seed0_plan"]["sha256"] and
        validation["files"][root0.name + "/run/terminal.json"] == gate["seed0_terminal"]["sha256"], "seed0 technical custody incomplete")
    require(set(terminal["arms"]) == set(terminal["captured"]) == set(ARMS), "both seed0 arms required")
    for arm in ARMS:
        require(set(terminal["arms"][arm]["readouts"]) == set(terminal["captured"][arm]["captures"]) == set(PANELS), "seed0 panels incomplete")
        for panel, total in PANELS.items():
            reduced = terminal["arms"][arm]["readouts"][panel]["reduction"]
            require(reduced["complete"] is True and reduced["counts"]["total"] == total and
                terminal["captured"][arm]["captures"][panel]["pairs"] == total, "seed0 captures/reductions incomplete")
    four = terminal["arms"]["FOUR_VIEW"]["readouts"]
    devcounts = four["dev"]["reduction"]["counts"]
    lexical = four["lexical"]["reduction"]["counts"]["by_family"]
    require(set(lexical) == {"0", "1", "2"}, "all lexical families required")
    checks = [(devcounts["memory"]["correct"], 15, 16), (devcounts["addition"]["adherence"], 30, 32),
        (devcounts["addition"]["correct_action"], 31, 32), (four["exact"]["reduction"]["counts"]["correct"], 15, 16)]
    checks += [(lexical[str(family)]["correct"], 15, 16) for family in range(3)]
    require(all(type(value) is int and minimum <= value <= maximum for value, minimum, maximum in checks) and
        devcounts["memory"]["total"] == 16 and devcounts["addition"]["total"] == 32 and
        all(lexical[str(family)]["total"] == 16 for family in range(3)), "Main seed0 gate criteria not met")
    require(all(base.digest(source) == expected for source, expected in evidence.items()), "gate changed during read")
    return dict(path=str(path), sha256=checksum, seed0_root=str(root0), evidence_hashes=evidence,
        owner="Main", decision="ALLOW_SEEDS_1_2", raw_review_verdict="PASS", criteria=PROGRESSION)


def inspect_material(root, parentroot, seed):
    root = Path(root).resolve(strict=True)
    material.verify(root)
    manifest = base.read(root / "manifest.json")
    require(manifest["status"] == "CALLBACK_TOKENIZER_V3_AUDITED_NO_FIT" and manifest["seeds"] == [0, 1, 2], "native material audit required")
    require(manifest["recipe"] == material.RECIPE and manifest["protocol"] == material.PROTOCOL, "wrong material protocol")
    material_parentroot = Path(manifest["original_teach_path"]).parent
    require(base.digest(material_parentroot / "plan.json") == memory.PINS["0"][0], "not original material anchor")
    original = old.read_plan(material_parentroot)
    parentroot = Path(parentroot).resolve(strict=True)
    parent_identity(parentroot, seed)
    selected = old.read_plan(parentroot)
    require(selected["model"] == original["model"] and selected["model_files"] == original["model_files"], "parent/material model mismatch")
    audit = base.read(root / "token_audit.json")
    for arm in ARMS:
        expected = COUNTS[arm]
        totals = dict(input_tokens=expected["input_presentations"], context_tokens=expected["context_presentations"], target_tokens=10000)
        require(manifest["token_totals"][arm] == audit["arms"][arm]["ten_epochs"] == totals, "native token totals changed")
    require(set(audit["optimizer_update_schedule"]) == {"0", "1", "2"}, "all seed schedules required")
    for schedule in audit["optimizer_update_schedule"].values():
        require(len(schedule) == 320 and sum(row["target_tokens_by_kind"]["memory"] for row in schedule) == 1280 and
            sum(sum(row["target_tokens_by_kind"].values()) for row in schedule) == 10000, "memory target mass must be12.8%, not equal weighting")
    return dict(materialroot=str(root), material_files=base.tree_hashes(root), parentroot=str(parentroot),
        model=original["model"], model_files=original["model_files"], material_parentroot=str(material_parentroot))


def config(model, seed):
    require(type(seed) is int and seed in SEEDS, "replication seeds1/2 only")
    return dict(memory.config(model, seed, 10), overflow="truncate")


def fit_command(plan, arm, adapter):
    require(arm in ARMS and plan["config"] == config(plan["model"], plan["seed"]), "wrong arm/seed config")
    require(plan["parent"]["parent"] == str(Path(plan["parentroot"]) / "fit_teach/adapter"), "not selected original parent")
    require(Path(adapter) == Path(plan["root"]) / "run" / arm / "adapter", "wrong arm output slot")
    command = [plan["python"], "-B", "-m", "organism_v6.train_adapter_v3", "--corpus",
        str(Path(plan["materialroot"]) / (arm + ".json")), "--out", str(adapter),
        "--init-adapter", plan["parent"]["parent"], "--model", plan["model"], "--rank", "8",
        "--alpha", "16", "--dropout", "0.05", "--lr", "0.0003", "--epochs", "10",
        "--batch-size", "4", "--grad-accum", "1", "--seed", str(plan["seed"]), "--no-pack", "--max-len", "512", "--overflow", "truncate"]
    require(asdict(trainer.config_from_args(trainer.build_parser().parse_args(command[4:]))) == plan["config"], "CLI recipe mismatch")
    return command


def validate_manifest(plan, arm, manifest, before, saved):
    require(plan["config"] == config(plan["model"], plan["seed"]), "fit seed/config mismatch")
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
        type(warm["phase_seed"]) is int and warm["phase_seed"] == plan["seed"] and warm["adapter_count"] == 1 and warm["optimizer_initial_state_entries"] == 0 and
        warm["optimizer_state_restored"] is False and warm["optimizer_state_saved"] is False and warm["optimizer_initialization"] == "fresh_per_write" and
        warm["phase_steps"] == 320 and warm["parent_cumulative_steps"] == 80 and warm["cumulative_steps"] == 400,
        "original parent/fresh optimizer/history changed")
    old.check_states("varied_replay", before, warm, saved)
    require(before == plan["parent_state"] == warm["initialized_state"] and not warm["dtype_conversions"], "initialized original state differs")


def verify_fit(plan, stage, arm):
    require(arm in ARMS and Path(stage) == Path(plan["root"]) / "run" / arm, "wrong fit slot")
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



def worker_command(plan, root, name):
    if name == "lexical":
        return [plan["python"], "-B", str(Path(__file__).absolute()), "_cue-worker", "--source-root", plan["source_root"],
            "--runroot", str(root), "--allow-gpu"]
    module = dev if name == "dev" else exact
    require(name in PANELS, "unknown panel")
    return [plan["python"], "-B", "-m", module.__name__, "_worker", "--root", str(root), "--allow-gpu"]


def prepare(materialroot, runroot, device, deadline, lease_end, seed, parentroot, seed0_gate, seed0_gate_sha256):
    bounds(time.time(), deadline, lease_end)
    memory.branches([device] * 3)
    bound = inspect_material(materialroot, parentroot, seed)
    gate = gate_receipt(seed0_gate, seed0_gate_sha256, bound)
    root = memory.fresh(runroot, (bound["materialroot"], bound["parentroot"], bound["material_parentroot"], bound["model"], base.REPO, gate["seed0_root"]))
    require(root.parent == Path(bound["materialroot"]).parent, "fresh run beside material required")
    pins = sources()
    require(base.model_hashes(bound["model"]) == bound["model_files"], "base changed")
    parent = memory.parent_record(Path(bound["parentroot"]), seed, bound["model"], bound["model_files"])
    before = old.state_inventory(parent["parent"])
    tokenizer = base.native_tokenizer(bound["model"])
    candidate = base.read(Path(bound["materialroot"]) / "candidate.json")
    exported = material.export_native(candidate, base.read(Path(bound["parentroot"]) / "teach.json"), tokenizer)
    require(exported["audit"] == base.read(Path(bound["materialroot"]) / "token_audit.json") and all(
        exported["corpora"][arm] == base.read(Path(bound["materialroot"]) / (arm + ".json")) for arm in ARMS), "actual native CPU audit differs")
    templates = {name: memory.template(module, bound["model"], bound["model_files"], tokenizer, device, lease_end)
        for name, module in (("dev", dev), ("exact", exact))}
    templates["lexical"] = cue_template(bound["model"], bound["model_files"], tokenizer, device, lease_end)
    require(all(templates["dev"][key] == parent["readout"][key] for key in ("cases", "requests", "native_inputs")), "original dev interface changed")
    require([dict(id=case["id"], rendered_context=native["rendered_prompt"], prefix_token_ids=native["prompt_token_ids"])
        for case, native in zip(templates["lexical"]["cases"], templates["lexical"]["native_inputs"], strict=True)] ==
        exported["audit"]["heldout_prefixes"], "lexical material/readout prefixes differ")
    plan = dict(schema=SCHEMA, source_commit=SOURCE_ID, source_root=str(base.REPO), source_hashes=pins,
        root=str(root), **bound, python=python(), seed=seed, seed0_gate=gate, parent_pin=list(memory.PINS[str(seed)]), parent=parent, parent_state=before, device=device,
        config=config(bound["model"], seed), accounting=COUNTS, templates=templates,
        arm_order=list(ARMS), panels=PANELS, pair_seconds=SECONDS, cleanup_seconds=CLEANUP, external_custody_seconds=CUSTODY, lease_margin_seconds=LEASE_MARGIN,
        deadline=float(deadline), real_lease_end=float(lease_end), calls_per_arm=112, total_calls=224, confirmation_calls=0,
        progression=PROGRESSION, reduce_only_after_both_captures=True, outcome_selective_skips=False,
        claim=CLAIM, origin="UNRESOLVED_LOCAL_HASHES_ONLY", input_compute_matched=False,
        memory_target_mass_fraction=.128, native_cpu_audit=dict(status="ACTUAL_NATIVE_TOKENIZER_REAUDIT_PASS_NO_FIT",
            tokenizer_class=exported["audit"]["tokenizer_class"], source_hashes=material.source_hashes(),
            audit_sha256=base.digest(Path(bound["materialroot"]) / "token_audit.json"),
            padded_costs=exported["audit"]["scheduled_costs"][str(seed)], selected_seed=seed,
            schedule_sha256=base.value_hash(exported["audit"]["optimizer_update_schedule"][str(seed)]), native_origin_authenticated=False))
    for arm in ARMS:
        adapter = root / "run" / arm / "adapter"
        fit_command(plan, arm, adapter)
        trainer._warm_parent(parent["parent"], adapter, trainer.TrainConfig(**plan["config"]))
    require(sources() == pins and inspect_material(materialroot, parentroot, seed) == bound and
        gate_receipt(seed0_gate, seed0_gate_sha256, bound) == gate and
        base.model_hashes(bound["model"]) == bound["model_files"] and trainer._warm_inventory(parent["parent"]) == parent["parent_files"] and
        old.state_inventory(parent["parent"]) == before, "inputs changed during prepare")
    root.mkdir()
    old.seal(root, plan)
    return dict(status="PREPARED_REPLICATION_NOT_LAUNCHED", seed=seed, plan_sha256=base.digest(root / "plan.json"), root=str(root))


def verify(root, current=True):
    root = Path(root)
    plan = old.read_plan(root)
    require(plan["schema"] == SCHEMA and plan["source_commit"] == SOURCE_ID and plan["source_root"] == str(base.REPO) and
        plan["root"] == str(root) and plan["source_hashes"] == sources() and plan["python"] == python(), "source/root/interpreter changed")
    require(type(plan["seed"]) is int and plan["seed"] in SEEDS and plan["parent_pin"] == list(memory.PINS[str(plan["seed"])]) and plan["arm_order"] == list(ARMS) and plan["panels"] == PANELS and
        plan["config"] == config(plan["model"], plan["seed"]) and plan["accounting"] == COUNTS and
        plan["progression"] == PROGRESSION and plan["pair_seconds"] == SECONDS and plan["cleanup_seconds"] == CLEANUP and
        plan["external_custody_seconds"] == CUSTODY and plan["lease_margin_seconds"] == LEASE_MARGIN and plan["reduce_only_after_both_captures"] is True and
        plan["outcome_selective_skips"] is False and plan["calls_per_arm"] == 112 and plan["total_calls"] == 224 and
        plan["confirmation_calls"] == 0 and plan["claim"] == CLAIM and plan["origin"] == "UNRESOLVED_LOCAL_HASHES_ONLY" and
        plan["input_compute_matched"] is False and plan["memory_target_mass_fraction"] == .128, "fixed pair contract changed")
    memory.branches([plan["device"]] * 3)
    require(root.parent == Path(plan["materialroot"]).parent, "run/material parent changed")
    require(plan["parent"]["parent"] == str(Path(plan["parentroot"]) / "fit_teach/adapter"), "original parent path changed")
    if current:
        require(gate_receipt(plan["seed0_gate"]["path"], plan["seed0_gate"]["sha256"], plan) == plan["seed0_gate"], "Main gate changed")
        require(all(plan[key] == value for key, value in inspect_material(plan["materialroot"], plan["parentroot"], plan["seed"]).items()) and
            base.model_hashes(plan["model"]) == plan["model_files"], "material/base changed")
        parent = plan["parent"]
        require(memory.parent_record(Path(plan["parentroot"]), plan["seed"], plan["model"], plan["model_files"]) == parent, "original seed identity changed")
        require(parent["parent"] == str(Path(plan["parentroot"]) / "fit_teach/adapter") and
            trainer._warm_inventory(parent["parent"]) == parent["parent_files"] and old.state_inventory(parent["parent"]) == plan["parent_state"] and
            all(base.digest(path) == checksum for path, checksum in parent["provenance"].items()) and
            base.tree_hashes(Path(plan["parentroot"]) / "readouts/teach") == parent["readout_files"], "original parent changed")
        audit = base.read(Path(plan["materialroot"]) / "token_audit.json")
        require(plan["native_cpu_audit"] == dict(status="ACTUAL_NATIVE_TOKENIZER_REAUDIT_PASS_NO_FIT",
            tokenizer_class=audit["tokenizer_class"], source_hashes=material.source_hashes(),
            audit_sha256=base.digest(Path(plan["materialroot"]) / "token_audit.json"), padded_costs=audit["scheduled_costs"][str(plan["seed"])], selected_seed=plan["seed"],
            schedule_sha256=base.value_hash(audit["optimizer_update_schedule"][str(plan["seed"])]), native_origin_authenticated=False), "native CPU audit/padded cost changed")
    for name in PANELS:
        template = plan["templates"][name]
        cases = cue_cases() if name == "lexical" else (dev if name == "dev" else exact).selected_cases()
        requests = cue_requests(cases) if name == "lexical" else (dev if name == "dev" else exact).requests(cases)
        require(template["cases"] == cases and len(cases) == PANELS[name] and template["requests"] == requests and
            template["source_hashes"] == (sources() if name == "lexical" else (dev if name == "dev" else exact).sources()) and
            template["model"] == plan["model"] and template["model_files"] == plan["model_files"] and
            template["adapter"] is None and template["adapter_files"] == {} and template["worker_seconds"] == 600 and
            template["device"] == plan["device"] and template["lease_end"] == plan["real_lease_end"] and
            template["identity"] == base.expected_identity(template, None), "fixed template changed")
    require(all(plan["templates"]["dev"][key] == plan["parent"]["readout"][key] for key in ("cases", "requests", "native_inputs")), "inherited dev inputs changed")
    return plan


def readplan_for(plan, name, fit, effective):
    require(name in PANELS and Path(fit["adapter"]) in
        {Path(plan["root"]) / "run" / arm / "adapter" for arm in ARMS}, "foreign child readout")
    result = copy.deepcopy(plan["templates"][name])
    result.update(adapter=fit["adapter"], adapter_files=fit["adapter_files"], lease_end=float(effective))
    result["replication_binding"] = dict(seed=plan["seed"], original_parent=plan["parent"]["parent"],
        original_parent_plan_sha256=plan["parent_pin"][0], original_readout_plan_sha256=plan["parent_pin"][2],
        seed0_gate_sha256=plan["seed0_gate"]["sha256"])
    result["identity"] = base.expected_identity(result, fit["adapter"])
    return result


def execute_arm(root, plan, arm, effective):
    budget(effective)
    stage = memory.fresh(root / "run" / arm)
    stage.mkdir()
    receipt = base.supervise(root / "run", dict(plan, lease_end=effective), stage / "fit-worker", fit_command(plan, arm, stage / "adapter"))
    memory.successful(receipt)
    fit = dict(verify_fit(plan, stage, arm), supervision=receipt)
    old.write(stage / "fit-result.json", fit)
    captures = {}
    for name in PANELS:
        budget(effective)
        readroot = stage / name
        readroot.mkdir()
        readplan = readplan_for(plan, name, fit, effective)
        old.seal(readroot, readplan)
        (readroot / "run").mkdir()
        receipt = base.supervise(root / "run", readplan, readroot / "run/worker", worker_command(plan, readroot, name), readroot / "run/data/calls")
        memory.successful(receipt)
        captures[name] = capture_receipt(readroot, readplan)
        require(trainer._warm_inventory(fit["adapter"]) == fit["adapter_files"], "readout changed child")
    result = dict(fit=fit, captures=captures)
    old.write(stage / "capture-result.json", result)
    return result


def cue_verify(root):
    plan = old.read_plan(root)
    require(plan["cases"] == cue_cases() and plan["requests"] == cue_requests(plan["cases"]) and
        plan["source_hashes"] == sources() and plan["worker_seconds"] == 600 and plan["output_token_ceiling"] == 3072 and
        base.model_hashes(plan["model"]) == plan["model_files"] and base.tree_hashes(plan["adapter"]) == plan["adapter_files"] and
        plan["identity"] == base.expected_identity(plan, plan["adapter"]) and
        dev.native_inputs(base.native_tokenizer(plan["model"]), plan["requests"]) == plan["native_inputs"], "lexical plan/native identity changed")
    return plan


def cue_worker(root):
    parent_pid = os.getppid()
    require(parent_pid > 1, "supervisor parent required")
    plan = cue_verify(root)
    require(base.supervisor.selected_device() == plan["device"], "worker device differs")
    path = root / "run/worker/process.json"
    until = time.monotonic() + 5
    while not path.exists() and time.monotonic() < until:
        time.sleep(.05)
    process = base.read(path)
    parent_plan = old.read_plan(root.parents[2])
    require(process["pid"] == process["pgid"] == os.getpid() == os.getpgrp() and os.getppid() == parent_pid and
        process["argv"] == worker_command(parent_plan, root, "lexical"), "worker ownership differs")
    deadline = time.monotonic() + 600
    stop = threading.Event()
    def interrupted(number, frame):
        raise RuntimeError(f"worker interrupted: {number}")
    def watch():
        while not stop.wait(.2):
            if os.getppid() != parent_pid or time.monotonic() >= deadline or time.time() >= plan["lease_end"] - 10:
                os.killpg(os.getpgrp(), signal.SIGTERM)
                return
    handlers = {number: signal.signal(number, interrupted) for number in (signal.SIGTERM, signal.SIGINT)}
    watcher = threading.Thread(target=watch, daemon=True)
    watcher.start()
    try:
        dev.capture(plan, base.fresh_directory(root / "run/data", plan["model"]))
    finally:
        stop.set()
        watcher.join()
        for number, handler in handlers.items(): signal.signal(number, handler)


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


def cue_reduce(root, parent_plan):
    plan = cue_verify(root)
    responses, receipt = audit_panel(root, plan, worker_command(parent_plan, root, "lexical"))
    base.audit_native_calls(base.native_tokenizer(plan["model"]), root / "run/data")
    rows = [dict(case_id=case["id"], family=case["family"], source_event_ids=case["source_event_ids"],
        **dev.score_memory(response["text"], case["expected"])) for case, response in zip(plan["cases"], responses, strict=True)]
    require(len(rows) == 48 and Counter(row["family"] for row in rows) == {0: 16, 1: 16, 2: 16}, "incomplete lexical panel")
    counts = dict(total=48, correct=sum(row["correct"] for row in rows), invalid=sum(not row["valid"] for row in rows),
        by_family={str(family): dict(total=16, correct=sum(row["correct"] for row in rows if row["family"] == family),
            invalid=sum(not row["valid"] for row in rows if row["family"] == family)) for family in range(3)})
    result = dict(complete=True, counts=counts, rows=rows, cost=base.usage(root / "run/data"), identity=plan["identity"],
        model_files=plan["model_files"], adapter_files=plan["adapter_files"], source_hashes=plan["source_hashes"],
        plan_sha256=base.digest(root / "plan.json"), capture_sha256=base.digest(root / "run/data/manifest.json"),
        process_sha256=base.digest(root / "run/worker/process.json"), supervision_sha256=base.digest(root / "run/worker/supervision.json"),
        native_token_text_audit=True, reserved_seconds=receipt["reserved_seconds"], independent_facts=16, claim_limits=CLAIM)
    old.write(root / "reduction.json", result)
    return result


def reduce_pair(root, plan, captured, effective):
    require(set(captured) == set(ARMS), "both arms before any reduction")
    for arm in ARMS:
        require(set(captured[arm]["captures"]) == set(PANELS), "all panels before any reduction")
        for name in PANELS:
            require(capture_receipt(root / "run" / arm / name, plan["templates"][name]) == captured[arm]["captures"][name], "capture changed before reduction")
    results = {}
    for arm in ARMS:
        panels = {}
        for name, count in PANELS.items():
            budget(effective)
            readroot = root / "run" / arm / name
            reduced = cue_reduce(readroot, plan) if name == "lexical" else (dev if name == "dev" else exact).reduce(readroot)
            require(reduced["complete"] is True and reduced["counts"]["total"] == count, "partial panel not zero")
            panels[name] = dict(reduction=reduced, sha256=base.digest(readroot / "reduction.json"))
        results[arm] = dict(captured[arm], readouts=panels)
        old.write(root / "run" / arm / "arm-result.json", results[arm])
    return results


def run(root, allow_gpu=False, clock=None):
    require(allow_gpu, "Main allocation and --allow-gpu required")
    started, monotonic = clock or (time.time(), time.monotonic())
    plan = old.read_plan(root)
    effective = bounds(started, plan["deadline"], plan["real_lease_end"])
    require(base.supervisor.selected_device() == plan["device"], "Main must set initial CUDA_VISIBLE_DEVICES")
    pair = memory.fresh(root / "run")
    pair.mkdir()
    record = dict(controller_pid=os.getpid(), device=plan["device"], seed=plan["seed"], started=started, started_monotonic=monotonic, effective_deadline=effective,
        real_lease_end=plan["real_lease_end"], external_custody_deadline=effective + CUSTODY,
        plan_sha256=base.digest(root / "plan.json"), continuous_reservation=True)
    old.write(pair / "reservation.json", record)
    captured, completed, error = {}, {}, None
    def interrupted(number, frame): raise RuntimeError(f"controller interruption/cleanup boundary: {number}")
    require(signal.getitimer(signal.ITIMER_REAL) == (0., 0.), "nested timer forbidden")
    handlers = {number: signal.signal(number, interrupted) for number in (signal.SIGALRM, signal.SIGTERM, signal.SIGINT)}
    signal.setitimer(signal.ITIMER_REAL, max(.001, effective - time.time() - CLEANUP))
    try:
        verify(root)
        for arm in ARMS:
            budget(effective)
            captured[arm] = execute_arm(root, plan, arm, effective)
        completed = reduce_pair(root, plan, captured, effective)
        verify(root)
        for arm in ARMS:
            require(verify_fit(plan, pair / arm, arm) == {key: value for key, value in completed[arm]["fit"].items() if key != "supervision"}, "child changed")
    except BaseException as failure:
        error = dict(type=type(failure).__name__, message=str(failure))
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        receipts, released, accounted = [], False, False
        try:
            receipts = [base.read(path) for path in pair.glob("**/supervision.json")]
            require(all(math.isfinite(item["reserved_seconds"]) and item["reserved_seconds"] >= 0 for item in receipts), "invalid worker cost")
            accounted = all((path.parent / "supervision.json").is_file() for path in pair.glob("**/process.json"))
            released = accounted and base.supervisor.gpu_processes_absent(plan["device"]) is True and all(
                all(item.get(key) is True for key in ("reservation_release_verified", "owned_group_empty", "gpu_processes_absent")) for item in receipts)
        except Exception as failure:
            error = error or dict(type=type(failure).__name__, message=str(failure))
        ended = time.time()
        terminal = dict(record, status="COMPLETE" if error is None and set(completed) == set(ARMS) and len(receipts) == 8 and
            all(item.get("ok") is True and item.get("returncode") == 0 for item in receipts) and released and ended <= effective else "FAILED_PARTIAL_NO_RETRY",
            captured=captured, arms=completed, error=error, ended=ended, reserved_seconds=time.monotonic() - monotonic,
            worker_reserved_seconds=sum(item["reserved_seconds"] for item in receipts), worker_accounting_complete=accounted,
            release_verified=released, deadline_met=ended <= effective, gate_evaluated=False, automatic_progression=False,
            origin="UNRESOLVED_LOCAL_HASHES_ONLY", budget_extended=False)
        old.write(pair / "terminal.json", terminal)
        for number, handler in handlers.items(): signal.signal(number, handler)
    require(terminal["status"] == "COMPLETE", "partial pair; preserve; no retry/resume")
    return dict(status="COMPLETE_BOTH_ARMS_REDUCED_MAIN_GATE_PENDING", terminal=str(pair / "terminal.json"))


def launch_record(root, plan):
    launch = common.read(root / "launch/launch.json")
    require(launch["seed"] == plan["seed"] and launch["parent_plan_sha256"] == plan["parent_pin"][0] and
        launch["seed0_gate_sha256"] == plan["seed0_gate"]["sha256"] and launch["plan_sha256"] == base.digest(root / "plan.json") and launch["script_sha256"] == base.digest(__file__) and
        launch["root"] == str(root) and launch["source"] == str(base.REPO) and launch["device"] == plan["device"] and
        launch["controller_bound_seconds"] == SECONDS and launch["external_collection_margin_seconds"] == CUSTODY and
        type(launch["pid"]) is int and launch["pid"] > 1 and launch["generation_calls"] == 224 and
        launch["command"] == [plan["python"], "-B", str(Path(__file__).absolute()), "run", "--source-root", str(base.REPO), "--runroot", str(root), "--allow-gpu"], "launch receipt differs")
    check_uuid(launch["gpu"]["gpu_uuid"], launch["gpu"], common.read_bytes(root / "launch/gpu.xml"))
    return launch


def check_uuid(expected, gpu, xml):
    require(isinstance(expected, str) and expected.startswith("GPU-") and gpu["gpu_uuid"] == expected and
        [node.text for node in ET.fromstring(xml).findall("gpu/uuid")] == [expected], "GPU UUID changed")


def status(root):
    plan = old.read_plan(root)
    launch = launch_record(root, plan) if (root / "launch/launch.json").exists() else None
    markers = ["fit-worker/process.json", "fit-worker/supervision.json", "adapter/DONE", "fit-result.json", "capture-result.json"]
    markers += [name + suffix for name in PANELS for suffix in ("/run/data/manifest.json", "/run/worker/supervision.json", "/reduction.json")]
    return dict(controller_pid=launch["pid"] if launch else None,
        controller_present=Path(f"/proc/{launch['pid']}").exists() if launch else None,
        terminal_available=(root / "run/terminal.json").is_file(),
        arms={arm: {name: (root / "run" / arm / name).is_file() for name in markers} for arm in ARMS})


def observation(started, observed, effective):
    require(all(math.isfinite(value) for value in (started, observed, effective)) and observed >= started, "invalid custody clock")
    return dict(full_reservation_seconds=observed - started, declared_controller_deadline=effective,
        declared_custody_deadline=effective + CUSTODY, late_observation=observed > effective + CUSTODY,
        overrun_seconds=max(0., observed - effective - CUSTODY), budget_extended=False)


def input_stats(plan):
    roots = [Path(plan["model"]), Path(plan["parent"]["parent"]), Path(plan["materialroot"]), base.REPO]
    roots += [Path(path) for path in plan["parent"]["provenance"]]
    roots += [Path(path) for path, _ in DEPENDENCIES.values()]
    roots += [Path(__file__), Path(plan["parentroot"]) / "readouts/teach"]
    roots += [Path(path) for path in plan["seed0_gate"]["evidence_hashes"]]
    roots += [Path(plan["root"]) / "run" / arm / "adapter" for arm in ARMS if (Path(plan["root"]) / "run" / arm / "adapter").exists()]
    result = {}
    for root in roots:
        common.unaliased(root)
        for path in ([root, *root.rglob("*")] if root.is_dir() else [root]):
            if path.is_symlink():
                require(root == Path(plan["model"]) and path.is_file(), "only model leaf links allowed")
                result[str(path)] = (common.identity(path.lstat()), str(path.resolve(strict=True)), common.identity(path.stat()))
            else:
                common.unaliased(path)
                require(path.is_file() or path.is_dir(), "special input file")
                result[str(path)] = common.identity(path.stat())
    return result


def collect_body(root, archive):
    observed = status(root)
    require(observed["controller_present"] is False and observed["terminal_available"], "absent PID plus terminal required")
    archive = memory.fresh(archive)
    validation_path = Path(str(archive) + ".validation.json")
    release_json, release_xml = root / "run/main_release.json", root / "run/main_release.xml"
    require(not any(path.exists() or path.is_symlink() for path in (validation_path, release_json, release_xml)), "orphan/existing custody; no overwrite/retry")
    require(root not in archive.parents, "capsule must be outside run root")
    sealed = old.read_plan(root)
    stats = input_stats(sealed)
    plan = verify(root)
    launch = launch_record(root, plan)
    terminal = common.read(root / "run/terminal.json")
    reservation = common.read(root / "run/reservation.json")
    require(all(terminal[key] == value for key, value in reservation.items()) and
        terminal["controller_pid"] == launch["pid"] and terminal["device"] == plan["device"] and terminal["seed"] == plan["seed"] and
        terminal["plan_sha256"] == base.digest(root / "plan.json") and terminal["worker_accounting_complete"] is True and
        terminal["release_verified"] is True and terminal["effective_deadline"] == terminal["started"] + SECONDS and
        terminal["effective_deadline"] <= plan["deadline"] and terminal["real_lease_end"] == plan["real_lease_end"] and
        terminal["external_custody_deadline"] == terminal["effective_deadline"] + CUSTODY and
        terminal["external_custody_deadline"] <= plan["real_lease_end"] - LEASE_MARGIN and
        terminal["gate_evaluated"] is False and terminal["automatic_progression"] is False and terminal["budget_extended"] is False,
        "terminal bounds/custody/release changed")
    required = terminal["status"] == "COMPLETE"
    require(required or terminal["status"] == "FAILED_PARTIAL_NO_RETRY", "unknown terminal status")
    require(math.isfinite(terminal["reserved_seconds"]) and terminal["reserved_seconds"] >= 0 and
        terminal["deadline_met"] == (terminal["ended"] <= terminal["effective_deadline"]) and
        (not required or terminal["error"] is None and set(terminal["arms"]) == set(ARMS) and
            set(terminal["captured"]) == set(ARMS) and terminal["reserved_seconds"] <= SECONDS), "terminal completeness/cost differs")
    reports, workers, visited = {}, [], set()
    for arm in ARMS:
        stage = root / "run" / arm
        fit_path = stage / "fit-result.json"
        fit = common.read(fit_path) if fit_path.exists() else None
        worker = audit_worker(stage / "fit-worker", fit_command(plan, arm, stage / "adapter"), plan["device"], fit is not None or required)
        if worker: workers.append(worker); visited.add(stage / "fit-worker/process.json")
        if fit:
            require(verify_fit(plan, stage, arm) == {key: value for key, value in fit.items() if key != "supervision"} and fit["supervision"] == worker[1], "fit receipt changed")
        if required:
            require(common.read(stage / "arm-result.json") == terminal["arms"][arm] and
                common.read(stage / "capture-result.json") == terminal["captured"][arm] and
                terminal["arms"][arm]["fit"] == terminal["captured"][arm]["fit"] == fit, "terminal arm/fit receipt changed")
        reports[arm] = {}
        for name, count in PANELS.items():
            readroot = stage / name
            command = worker_command(plan, readroot, name)
            worker = audit_worker(readroot / "run/worker", command, plan["device"], required)
            if worker: workers.append(worker); visited.add(readroot / "run/worker/process.json")
            if not (readroot / "run/data/manifest.json").exists():
                require(not required and not (readroot / "reduction.json").exists(), "missing panel is not zero")
                reports[arm][name] = "PARTIAL_OR_NOT_STARTED_NOT_SCORED"
                continue
            require(fit is not None, "capture without fit")
            readplan = old.read_plan(readroot)
            require(readplan == readplan_for(plan, name, fit, terminal["effective_deadline"]), "readout parent/template changed")
            _, receipt = audit_panel(readroot, readplan, command)
            report = dict(raw_pairs=count, capture_sha256=base.digest(readroot / "run/data/manifest.json"))
            if (readroot / "reduction.json").exists():
                reduced = common.read(readroot / "reduction.json")
                require(reduced["complete"] is True and reduced["counts"]["total"] == len(reduced["rows"]) == count and
                    [row["case_id"] for row in reduced["rows"]] == [case["id"] for case in readplan["cases"]] and
                    reduced["plan_sha256"] == base.digest(readroot / "plan.json") and reduced["capture_sha256"] == report["capture_sha256"] and
                    reduced["source_hashes"] == readplan["source_hashes"] and reduced["model_files"] == plan["model_files"] and
                    reduced["adapter_files"] == fit["adapter_files"] and reduced["identity"] == readplan["identity"] and
                    reduced["native_token_text_audit"] is True and reduced["cost"] == base.usage(readroot / "run/data") and
                    reduced["reserved_seconds"] == receipt["reserved_seconds"], "existing reduction binding changed")
                report["reduction_sha256"] = base.digest(readroot / "reduction.json")
                if required:
                    require(terminal["arms"][arm]["readouts"][name] == dict(reduction=reduced, sha256=report["reduction_sha256"]) and
                        terminal["captured"][arm]["captures"][name] == capture_receipt(readroot, readplan), "terminal panel receipt changed")
            else:
                require(not required, "complete terminal missing reduction")
            reports[arm][name] = report
    require(visited == set((root / "run").glob("**/process.json")) and
        {path.parent / "supervision.json" for path in visited} == set((root / "run").glob("**/supervision.json")), "unaccounted workers")
    require(sum(receipt["reserved_seconds"] for _, receipt in workers) == terminal["worker_reserved_seconds"] and
        (not required or len(workers) == 8 and terminal["deadline_met"] is True and terminal["ended"] <= terminal["effective_deadline"]), "worker cost/completion changed")
    require(all(left[0]["started"] + left[1]["reserved_seconds"] <= right[0]["started"] for left, right in zip(workers, workers[1:])), "workers overlapped/reordered")
    require(all(terminal["started_monotonic"] <= process["started"] and
        process["started"] + receipt["reserved_seconds"] <= terminal["started_monotonic"] + terminal["reserved_seconds"]
        for process, receipt in workers), "workers outside controller accounting")
    before = common.metadata(root, root.parent)
    from gpu.astra_mini_sudoku_diagnostic import check_free
    gpu, xml = check_free(plan["device"])
    check_uuid(launch["gpu"]["gpu_uuid"], gpu, xml)
    require(not Path(f"/proc/{launch['pid']}").exists() and common.metadata(root, root.parent) == before and input_stats(plan) == stats,
        "evidence/controller changed")
    now = time.time()
    started = dt.datetime.fromisoformat(launch["started_utc"]).timestamp()
    common.write_new(release_xml, xml.encode())
    common.write_json(release_json, dict(full_release=True, controller_absent=True, gpu=gpu, device=plan["device"],
        controller_pid=launch["pid"], release_utc=dt.datetime.fromtimestamp(now, dt.timezone.utc).isoformat(),
        observation=observation(started, now, terminal["effective_deadline"]), plan_sha256=base.digest(root / "plan.json"),
        terminal_sha256=base.digest(root / "run/terminal.json"), launch_sha256=base.digest(root / "launch/launch.json"),
        xml_sha256=base.digest(release_xml), worker_reserved_seconds=terminal["worker_reserved_seconds"],
        controller_reserved_seconds=terminal["reserved_seconds"], accounting="overlapping windows; do not add"))
    manifest = common.metadata(root, root.parent)
    with archive.open("xb") as stream, tarfile.open(fileobj=stream, mode="w:gz", format=tarfile.USTAR_FORMAT) as bundle:
        for name, checksum in manifest.items():
            payload = common.read_bytes(root.parent / name)
            require(hashlib.sha256(payload).hexdigest() == checksum, "metadata changed during packaging")
            member = tarfile.TarInfo(name)
            member.size, member.mode = len(payload), 0o600
            bundle.addfile(member, io.BytesIO(payload))
    common.validate_archive(io.BytesIO(common.read_bytes(archive)), manifest, root.name + "/")
    require(common.metadata(root, root.parent) == manifest and input_stats(plan) == stats and not Path(f"/proc/{launch['pid']}").exists(),
        "evidence changed after packaging")
    common.write_json(validation_path, dict(archive=str(archive), sha256=base.digest(archive), files=manifest,
        plan_sha256=base.digest(root / "plan.json"), terminal_status=terminal["status"], audits=reports,
        observation=observation(started, time.time(), terminal["effective_deadline"]), excluded_suffixes=sorted(common.EXCLUDED),
        token_decode_audit="existing native audit receipts bound; no tokenizer/reducer rerun", weights="preserved native",
        seed=plan["seed"], original_parent_plan_sha256=plan["parent_pin"][0], seed0_gate_sha256=plan["seed0_gate"]["sha256"],
        authorship="replication driver author; custody verification not independent science"))
    return dict(status="COLLECTED_NO_SCORES", archive=str(archive), sha256=base.digest(archive), terminal_status=terminal["status"])


def collect(root, archive):
    require(signal.getitimer(signal.ITIMER_REAL) == (0., 0.), "nested timer forbidden")
    def expired(number, frame): raise TimeoutError("300s custody alarm; preserve partial files; no extension")
    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, CUSTODY)
    try:
        return collect_body(root, archive)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def main():
    clock = time.time(), time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "verify", "run", "status", "collect", "_cue-worker"))
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--runroot", required=True)
    parser.add_argument("--materialroot")
    parser.add_argument("--seed", type=int, choices=SEEDS)
    parser.add_argument("--parentroot")
    parser.add_argument("--seed0-gate")
    parser.add_argument("--seed0-gate-sha256")
    parser.add_argument("--device")
    parser.add_argument("--deadline", type=float)
    parser.add_argument("--lease-end", type=float)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--allow-gpu", action="store_true")
    args = parser.parse_args()
    bind(args.source_root)
    root = Path(args.runroot).expanduser().absolute()
    if args.stage == "prepare":
        require(all(getattr(args, key) is not None for key in ("materialroot", "device", "deadline", "lease_end", "seed", "parentroot", "seed0_gate", "seed0_gate_sha256")), "missing prepare arguments")
        result = prepare(args.materialroot, root, args.device, args.deadline, args.lease_end, args.seed, args.parentroot, args.seed0_gate, args.seed0_gate_sha256)
    elif args.stage == "run": result = run(root, args.allow_gpu, clock)
    elif args.stage == "status": result = status(root)
    elif args.stage == "collect":
        require(args.archive is not None, "exclusive --archive required")
        result = collect(root, args.archive)
    elif args.stage == "_cue-worker":
        require(args.allow_gpu, "supervised explicit worker only")
        cue_worker(root)
        result = dict(status="CAPTURED_NOT_REDUCED")
    else:
        verify(root)
        result = dict(status="VERIFIED_NOT_LAUNCH_AUTHORITY")
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
