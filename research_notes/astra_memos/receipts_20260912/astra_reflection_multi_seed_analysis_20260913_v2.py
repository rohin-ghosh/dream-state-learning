"""Offline post-COLLECTION reflection analysis; explicit relocated seeds 0/1/2 only.

API: analyze(manifest) -> JSON-compatible report, without writes.
CLI: --manifest PATH --output NEW_JSON (exclusive creation, outside inputs).
See astra_reflection_analysis_handoff_20260913.md for the manifest contract.
"""
from __future__ import annotations

import argparse
import ast
import builtins
from collections import Counter
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import statistics
import types


SCHEMA = "reflection_three_seed_collected_analysis_v2"
ARMS = ("withdrawn", "present")
STATES = ("OFF", "fitWithdrawn", "fitPresent")
CELLS = tuple(f"{state}__{arm}" for state in STATES for arm in ARMS)
STAGES = ("fit_withdrawn", "fit_present") + CELLS
PANELS = ("restatement", "application")
METRICS = {"restatement": "exact_authored_fixture_matches", "application": "strict_application_correct"}
SOURCE_PINS = {
    "organism_v6/__init__.py": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "organism_v6/birth_skill_corpus.py": "078ceba07141b5f6fb2159a12e21f1eccc0901ba9f51f52d1793d988927812f6",
    "organism_v6/rulegame_parenting_diagnostic.py": "e6055da48b2c6fa1bd294c9d991e07f32f05dc6630fe8973373977bdfe977526",
    "organism_v6/train_adapter_v3.py": "7bbf165fcb4b8ae3a1180328bcd19f57382c30516daddc95fd61e8a2c749fad7",
    "organism_v6/birth_reflection_probe.py": "b69dfe4ab39e60fab826e67758d21e708c87d538f3fcd2b8a579bb778b0ace80",
}
RUNTIME_PINS = {
    "seed0": "0f79efa1f4e4da6a9d1ec245c09e665f7c2b7d8bce31f7e01fe01b00f95a72fc",
    "replication": "d1f572d094507f85245af2edd95608daffa8322a2d5dbae01ae31957e40ac6c9",
}
INPUTS = {"train_withdrawn.json", "train_present.json", "dev.json", "calls.json",
          "exports.json", "binding_receipt.json", "source_pins.json"}
CLAIM = ("All three learner seeds were preselected before outcomes. Authored DEV only; "
         "exact restatement mismatch is not semantic prose failure. Strict A/B application is separate. "
         "Shared rows and deterministic OFF repeats are not independent observations. "
         "No composite, p-values, semantic prose scoring, causal promotion, persistence, L2 or H1/H2 inference.")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)


def same(left, right):
    return canonical(left) == canonical(right)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key: " + key)
        result[key] = value
    return result


def decode(raw):
    return json.loads(raw, object_pairs_hook=unique_object,
                      parse_constant=lambda value: require(False, "nonfinite JSON: " + value))


def digest(path):
    checksum = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            checksum.update(block)
    return checksum.hexdigest()


def local_path(value):
    require(type(value) is str and Path(value).is_absolute() and ".." not in Path(value).parts,
            "explicit absolute local path required")
    path = Path(value)
    require(not any(part.is_symlink() for part in (path, *path.parents)), "symlinked input path: " + value)
    return path


def member(root, name):
    relative = PurePosixPath(name)
    require(type(name) is str and relative.parts and not relative.is_absolute() and
            ".." not in relative.parts and str(relative) == name, "unsafe inventory member")
    return local_path(str(root / name))


def check_pin(path, expected):
    path = local_path(str(path))
    require(type(expected) is str and re.fullmatch(r"[0-9a-f]{64}", expected), "invalid SHA256 pin")
    require(path.is_file() and digest(path) == expected, "hash mismatch or missing file: " + str(path))


def bound_json(path, expected):
    path = local_path(str(path))
    require(type(expected) is str and re.fullmatch(r"[0-9a-f]{64}", expected), "invalid SHA256 pin")
    require(path.is_file(), "missing file: " + str(path))
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == expected, "hash mismatch: " + str(path))
    return decode(raw)


def checked_tree(root, pins):
    require(type(pins) is dict and pins, "empty custody inventory")
    actual = set()
    for path in root.rglob("*"):
        require(not path.is_symlink(), "symlink in custody tree")
        require(path.is_file() or path.is_dir(), "special custody file")
        if path.is_file():
            actual.add(str(path.relative_to(root)))
    require(actual == set(pins), "custody file inventory mismatch: " + str(root))
    require(not any("failure" in PurePosixPath(name).name for name in pins), "failed custody tree")
    for name, pin in pins.items():
        check_pin(member(root, name), pin)


def seed_field(value, seed, label):
    actual = value.get("learner_seed", 0 if seed == 0 else None)
    require(type(actual) is int and actual == seed, "learner seed mismatch: " + label)


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def tokens(value):
    return type(value) is list and bool(value) and all(type(token) is int and token >= 0 for token in value)


def load_sources(manifest):
    binding = manifest["source"]
    source = local_path(binding["root"])
    require(same(binding["sha256"], SOURCE_PINS), "frozen source pins differ")
    for name, pin in SOURCE_PINS.items():
        check_pin(member(source, name), pin)
    corpus_path = source / "organism_v6/birth_skill_corpus.py"
    corpus = types.ModuleType("pinned_reflection_historical_corpus")
    corpus.__file__ = str(corpus_path)
    exec(compile(corpus_path.read_bytes(), str(corpus_path), "exec"), corpus.__dict__)
    corpus._interface()
    package = types.SimpleNamespace(birth_skill_corpus=corpus)

    def source_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "organism_v6" and level == 0:
            return package
        return builtins.__import__(name, globals, locals, fromlist, level)

    reflection_path = source / "organism_v6/birth_reflection_probe.py"
    reflection = types.ModuleType("pinned_reflection_analysis_corpus")
    reflection.__file__ = str(reflection_path)
    reflection.__dict__["__builtins__"] = dict(vars(builtins), __import__=source_import)
    exec(compile(reflection_path.read_bytes(), str(reflection_path), "exec"), reflection.__dict__)
    reflection.build_panel = lru_cache(maxsize=6)(reflection.build_panel)
    runtimes = {}
    require(set(manifest["runtimes"]) == set(RUNTIME_PINS), "both source runtime bindings required")
    names = {"SCOPE", "PARAMS", "ENGINE", "RECIPE", "GENERIC_SYSTEM", "CLAIM", "SCOPE_EXPLANATION"}
    for name, pin in RUNTIME_PINS.items():
        runtime = manifest["runtimes"][name]
        path = local_path(runtime["path"])
        require(runtime["sha256"] == pin, "unsupported runtime source pin")
        check_pin(path, pin)
        selected = []
        for node in ast.parse(path.read_bytes()).body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                target = node.targets[0]
                if isinstance(target, ast.Name) and target.id in names:
                    selected.append(node)
                elif isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name) and target.value.id == "RECIPE":
                    selected.append(node)
            elif isinstance(node, ast.FunctionDef) and node.name == "check_fit_manifest":
                selected.append(node)
        namespace = {"require": require, "math": math,
                     "seed_matches": lambda value, expected: type(value) is int and value == expected}
        exec(compile(ast.Module(body=selected, type_ignores=[]), str(path), "exec"), namespace)
        require(names <= namespace.keys() and "check_fit_manifest" in namespace, "runtime CPU interface incomplete")
        runtimes[name] = namespace
    return reflection, runtimes


def build_expected(corpus):
    trains, dev, exports = {}, {}, {}
    for arm in ARMS:
        train = corpus.build_panel("restatement", split="train", parent_condition=arm)
        trains[arm] = train["rows"]
        dev[arm] = []
        exports[arm] = {"training_report": corpus.export_training(train)["report"], "development_reports": {}}
        for panel in PANELS:
            built = corpus.build_panel(panel, split="dev", parent_condition=arm)
            dev[arm].extend(built["rows"])
            exports[arm]["development_reports"][panel] = corpus.export_development(built)["report"]
    return trains, dev, exports


def training_exposure(prepared, rows, seed):
    seed_field(prepared, seed, "training audit")
    require(len(prepared["encoding"]) == len(prepared["items"]) == 12, "TRAIN12 encoding required")
    by_id = {}
    for expected, audit, item in zip(rows, prepared["encoding"], prepared["items"], strict=True):
        require(audit["row_id"] == expected["row_id"] and audit["response_target"] == expected["response_target"] and
                item["group"] == expected["row_id"], "TRAIN source/target/order drift")
        ids, labels = audit["input_ids"], audit["labels"]
        require(tokens(ids) and len(ids) <= 1024 and len(ids) == len(labels) and
                all(type(label) is int and (label == -100 or label == token) for label, token in zip(labels, ids)),
                "invalid training encoding/mask")
        supervised = [label for label in labels if label != -100]
        require(same(supervised, audit["supervised_ids"]) and len(supervised) == audit["target_tokens"] + 1,
                "target-plus-EOS exposure mismatch")
        prompt_count = len(audit["native_prompt"]["prompt_token_ids"])
        require(tokens(audit["native_prompt"]["prompt_token_ids"]) and
                labels == [-100] * prompt_count + supervised + [-100] * (len(ids) - prompt_count - len(supervised)) and
                ids[:prompt_count] == audit["native_prompt"]["prompt_token_ids"], "prompt supervision or prefix mismatch")
        require(audit["input_tokens"] == len(ids) and audit["prompt_tokens"] == prompt_count and
                audit["supervised_tokens"] == len(supervised), "training row token count mismatch")
        by_id[expected["row_id"]] = audit
    fields = {"prompt_tokens": "prompt_tokens", "authored_target_tokens": "target_tokens",
              "target_tokens": "supervised_tokens", "total_tokens": "input_tokens",
              "target_utf8_bytes": "target_utf8_bytes", "prompt_utf8_bytes": "prompt_utf8_bytes"}
    for field, audit_field in fields.items():
        require(type(prepared[field]) is int and prepared[field] == sum(audit[audit_field] for audit in by_id.values()),
                "training aggregate mismatch: " + field)
    orders, batches = prepared["epoch_order"], prepared["batch_exposure"]
    require(len(orders) == 4 and len(batches) == 12, "four epochs/twelve batches required")
    for epoch, order in enumerate(orders):
        require(len(order) == 12 and set(order) == set(by_id), "training epoch inventory mismatch")
        for offset in range(3):
            selected = order[4 * offset:4 * offset + 4]
            batch = batches[3 * epoch + offset]
            expected = dict(epoch=epoch, row_ids=selected,
                            input_tokens=sum(by_id[row_id]["input_tokens"] for row_id in selected),
                            padded_tokens=4 * max(by_id[row_id]["input_tokens"] for row_id in selected),
                            supervised_tokens=sum(by_id[row_id]["supervised_tokens"] for row_id in selected))
            require(same(batch, expected), "batch exposure/order mismatch")
    return dict(updates=12, presentations=48, epochs=4,
                per_epoch={field: prepared[field] for field in fields},
                full_fit={field: 4 * prepared[field] for field in fields},
                padded_tokens=sum(batch["padded_tokens"] for batch in batches),
                epoch_order=orders, batch_exposure=batches)


def validate_response(call, response, route):
    native = call["native"]
    require(tokens(native["prompt_token_ids"]) and type(native["rendered_prompt"]) is str,
            "invalid native prompt audit")
    require(all(same(response.get(key), value) for key, value in native.items()), "response/request audit mismatch")
    require(same(response["actual_prompt_token_ids"], native["prompt_token_ids"]) and same(response["lora_request"], route),
            "actual prompt/adapter route mismatch")
    require(tokens(response["output_token_ids"]) and len(response["output_token_ids"]) <= 192 and
            len(native["prompt_token_ids"]) + 192 <= 16384, "token budget/type mismatch")
    require(type(response["text"]) is str and response["text"] == response["decoded_output"], "raw text audit mismatch")
    require(response["finish_reason"] in ("stop", "length") and "stop_reason" in response, "invalid termination")
    require(response["finish_reason"] != "length" or len(response["output_token_ids"]) == 192, "weak length finish")
    require(finite(response["started"]) and finite(response["ended"]) and response["ended"] >= response["started"],
            "invalid generation timing")


def stage_timing(read, stage, plan_pin, seed):
    started, launched, released = (read(name) for name in ("started.json", "launch.json", "released.json"))
    for receipt in (started, launched, released):
        seed_field(receipt, seed, stage)
    pid = started["pid"]
    require(type(pid) is int and pid > 1 and all(type(receipt["pid"]) is int and
            receipt["pid"] == receipt["pgid"] == pid for receipt in (started, launched, released)), "worker PID/PGID mismatch")
    require(all(receipt["stage"] == stage and receipt["plan_sha256"] == plan_pin for receipt in (started, launched)),
            "stage plan binding mismatch")
    require(finite(started["time"]) and finite(released["time"]) and released["time"] >= started["time"], "invalid release time")
    return dict(pid=pid, started_wall_time=started["time"], released_wall_time=released["time"],
                started_receipt_to_release_seconds=released["time"] - started["time"])


def analyze_cell(cell, read, inventory, plan, calls, dev, fits, corpus, stored, seed):
    state, arm = cell.split("__")
    fit = None if state == "OFF" else fits["fit_withdrawn" if state == "fitWithdrawn" else "fit_present"]
    adapter = None if fit is None else fit["adapter"]
    route = None if fit is None else dict(name="reflection", id=1, path=adapter)
    identity, closed = read("identity.json"), read("closed.json")
    seed_field(identity, seed, "readout identity")
    seed_field(closed, seed, "readout closure")
    expected_identity = dict(cell=cell, model=plan["model"], revision=plan["binding"]["revision"], model_files=plan["model_files"],
                             adapter=adapter, adapter_files={} if fit is None else fit["adapter_files"],
                             lora_request=route, engine=plan["engine"], params=plan["params"])
    if "learner_seed" in identity:
        expected_identity["learner_seed"] = seed
    require(same(identity, expected_identity), "readout identity/route mismatch")
    names = {"identity.json"} | {f"{index:02d}{suffix}" for index in range(24) for suffix in (".request.json", ".response.json")}
    require(same(closed["calls"], 24) and set(closed["files"]) == names and
            all(closed["files"][name] == inventory[name] for name in names), "closed capture inventory mismatch")
    require({name for name in inventory if name.endswith((".request.json", ".response.json"))} == names - {"identity.json"},
            "extra raw capture")
    require(set(stored) == set(PANELS), "separate stored panels required")
    panels = {panel: [] for panel in PANELS}
    for index, (row, call) in enumerate(zip(dev[arm], calls[arm], strict=True)):
        require(same(read(call["call_id"] + ".request.json"), call), "captured request mismatch")
        response_name = call["call_id"] + ".response.json"
        response = read(response_name)
        validate_response(call, response, route)
        score = corpus.score_response(row, response["text"])
        panel = row["panel"]
        require(type(score["passed"]) is bool, "nonboolean corpus metric")
        if panel == "restatement":
            require(score["semantic_prose_score"] is None and score["score_kind"] == "exact_authored_restatement_only",
                    "semantic restatement scoring forbidden")
        else:
            require(score["score_kind"] == "strict_application_choice" and
                    score["syntax_valid"] == (response["text"] in ("A", "B")), "application scorer drift")
        original = dict(row_id=row["row_id"], source_id=row["source"]["source_id"], score=score,
                        finish_reason=response["finish_reason"], response_sha256=inventory[response_name])
        panels[panel].append(dict(original, call_id=f"{index:02d}", raw_response=response["text"],
                                  response_target=row["response_target"], input_messages=row["input_messages"],
                                  public_source=row["source"], source_proof=row["source_proof"],
                                  stop_reason=response["stop_reason"], prompt_tokens=len(call["native"]["prompt_token_ids"]),
                                  output_tokens=len(response["output_token_ids"]),
                                  generation_seconds=response["ended"] - response["started"]))
    result = {}
    for panel, rows in panels.items():
        original_rows = [{key: row[key] for key in ("row_id", "source_id", "score", "finish_reason", "response_sha256")} for row in rows]
        count = sum(row["score"]["passed"] for row in rows)
        length = sum(row["finish_reason"] == "length" for row in rows)
        expected = dict(rows=original_rows, metric=METRICS[panel], count=count, total=12,
                        semantic_prose_score=None, length_finishes=length)
        require(len(rows) == 12 and same(stored[panel], expected), "stored corpus decisions/counts differ: " + panel)
        result[panel] = dict(metric=METRICS[panel], count=count, total=12, semantic_prose_score=None,
                             syntax_valid_count=sum(row["score"]["syntax_valid"] for row in rows) if panel == "application" else None,
                             termination=dict(stop=12 - length, length=length,
                                              stop_reasons=dict(Counter(canonical(row["stop_reason"]) for row in rows))),
                             prompt_tokens=sum(row["prompt_tokens"] for row in rows),
                             output_tokens=sum(row["output_tokens"] for row in rows),
                             generation_seconds=sum(row["generation_seconds"] for row in rows), rows=rows)
    return result


def validate_receipts(manifest, plan, inputs):
    declarations = manifest.get("upstream_receipts", {})
    require(set(declarations) == {"source_pins", "binding"}, "explicit upstream receipt bindings required")
    originals, bindings = {}, {}
    for key, filename, plan_field in (("source_pins", "source_pins.json", "source_pins_sha256"),
                                      ("binding", "binding_receipt.json", "binding_receipt_sha256")):
        declaration = declarations[key]
        require(declaration["sha256"] == plan[plan_field], "upstream receipt pin differs from plan: " + key)
        original = bound_json(local_path(declaration["path"]), declaration["sha256"])
        require(same(original, inputs[filename]), "upstream/copied receipt content differs: " + key)
        originals[key] = original
        bindings[key] = dict(original_sha256=declaration["sha256"], copy_sha256=plan["input_hashes"][filename],
                             decoded_objects_equal=True)
    require(same(originals["source_pins"], SOURCE_PINS), "upstream source pins differ from frozen corpus")
    receipt = originals["binding"]
    require(receipt["status"] == "PUBLIC_REVISION_FILES_MATCHED_PROSPECTIVE_BINDING" and
            receipt["clean_lineage_certified"] is False and same(receipt["file_count"], 14) and
            len(receipt["files"]) == 14, "upstream public model receipt differs")
    require(receipt["repository"] == plan["binding"]["model_name"] == "Qwen/Qwen2.5-7B-Instruct" and
            receipt["revision"] == plan["binding"]["revision"] == "a09a35458c702b33eeacc393d103063234e8bc28" and
            receipt["model"] == plan["model"], "upstream model/revision/path binding differs")
    for name, item in receipt["files"].items():
        require("adapter" not in name.lower() and item["public_match"] in ("GIT_BLOB_SHA1", "LFS_SHA256") and
                re.fullmatch(r"[0-9a-f]{64}", item["sha256"]), "unmatched upstream model file")
    inventory = {name: item["sha256"] for name, item in receipt["files"].items()}
    require(same(inventory, plan["model_files"]) and same(inventory, plan["binding"]["model_files"]),
            "upstream model file inventory differs")
    return bindings


def analyze_seed(entry, manifest, corpus, runtimes, expected):
    seed = entry["learner_seed"]
    root, logs, scores_path = (local_path(entry[key]) for key in ("root", "logs", "scores"))
    require(entry.get("collected_snapshot") is True, "explicit completed collection required")
    plan = bound_json(root / "plan.json", entry["plan_sha256"])
    for relocated in (root, logs, scores_path):
        for name in ("root", "log_dir", "source", "model"):
            native = PurePosixPath(plan[name])
            require(native.is_absolute() and not PurePosixPath(str(relocated)).is_relative_to(native),
                    "original/native path is not a relocated snapshot")
    complete = bound_json(root / "capture_complete.json", entry["completion_sha256"])
    scores = bound_json(scores_path, entry["scores_sha256"])
    collection = bound_json(member(scores_path.parent, "collection.json"), entry["collection_sha256"])
    for path in (root / "controller_failure.json", root / "prepare_failure.json", scores_path.parent / "collection_failure.json"):
        require(not path.exists(), "failed collection/controller")
    for receipt in (plan, complete, scores, collection):
        seed_field(receipt, seed, "top-level receipt")
    runtime_name = "seed0" if seed == 0 else "replication"
    runtime = runtimes[runtime_name]
    require(plan["self_sha256"] == RUNTIME_PINS[runtime_name] and plan["scope"] == scores["scope"] == runtime["SCOPE"] and
            plan["claim"] == scores["claim"] == runtime["CLAIM"], "runtime identity mismatch")
    if seed:
        require(plan["parent_driver_sha256"] == scores["parent_driver_sha256"] == RUNTIME_PINS["seed0"], "replica parent runtime mismatch")
    require(complete["plan_sha256"] == scores["plan_sha256"] == entry["plan_sha256"] and
            scores["completion_sha256"] == collection["completion_sha256"] == entry["completion_sha256"] and
            collection["scores_sha256"] == entry["scores_sha256"], "collection hash chain mismatch")
    require(complete["scored"] is False and same(complete["calls"], 144) and same(scores["calls"], 144) and
            same(scores["fresh_workers"], 8) and scores["automatic_pass"] is False and scores["composite_metric"] is None and
            scores["clean_ancestry_certified"] is False, "closed/raw-only or claim boundary mismatch")
    require(same(plan["engine"], runtime["ENGINE"]) and same(plan["params"], runtime["PARAMS"]) and
            plan["generic_system"] == runtime["GENERIC_SYSTEM"] and same(plan["calls"], 144) and
            plan["truncation_allowed"] is False and plan["stages"] == list(STAGES), "readout contract drift")
    config = plan["config"]
    require(type(config["seed"]) is int and config["seed"] == seed and config["model"] == plan["model"], "fit seed/model mismatch")
    require(all(same(config[key], seed if key == "seed" else value) for key, value in runtime["RECIPE"].items()), "fit recipe drift")
    require(same(plan["source_hashes"], SOURCE_PINS) and set(plan["input_hashes"]) == INPUTS, "source/input inventory drift")
    inputs = {name: bound_json(member(root, name), pin) for name, pin in plan["input_hashes"].items()}
    receipt_bindings = validate_receipts(manifest, plan, inputs)
    require(same(plan["model_files"], plan["binding"]["model_files"]) and
            plan["binding"]["clean_ancestry_certified"] is False, "recorded model binding mismatch")
    trains, dev, exports = expected
    require(same(inputs["dev.json"], dev) and same(inputs["exports.json"], exports), "unchanged corpus/export mismatch")
    calls = inputs["calls.json"]
    require(set(calls) == set(ARMS), "call arm inventory mismatch")
    for arm in ARMS:
        require(len(calls[arm]) == 24, "DEV24 calls required")
        for index, (call, row) in enumerate(zip(calls[arm], dev[arm], strict=True)):
            require(set(call) == {"call_id", "row_id", "messages", "native"} and call["call_id"] == f"{index:02d}" and
                    call["row_id"] == row["row_id"] and same(call["messages"], row["input_messages"]), "call/source pairing mismatch")
            require(call["native"]["actual_system_text"] == runtime["GENERIC_SYSTEM"], "system replacement is not reflection withdrawal")
    exposure = {arm: training_exposure(inputs[f"train_{arm}.json"], trains[arm], seed) for arm in ARMS}
    require(same(exposure["withdrawn"]["epoch_order"], exposure["present"]["epoch_order"]) and
            same([row["supervised_ids"] for row in inputs["train_withdrawn.json"]["encoding"]],
                 [row["supervised_ids"] for row in inputs["train_present.json"]["encoding"]]), "matched target/order exposure mismatch")
    require(set(complete["stages"]) == set(STAGES) and {path.name for path in (root / "run").iterdir()} == set(STAGES) and
            {path.name for path in logs.iterdir()} == set(STAGES) and set(scores["cells"]) == set(CELLS), "stage/cell inventory mismatch")
    times, fits, cells = {}, {}, {}
    for stage in STAGES:
        inventory = complete["stages"][stage]
        require(set(inventory) == {"artifacts", "logs"} and set(inventory["logs"]) == {"stdout.log", "stderr.log"}, "stage custody schema mismatch")
        directory = member(root, "run/" + stage)
        checked_tree(directory, inventory["artifacts"])
        checked_tree(member(logs, stage), inventory["logs"])

        def read(name):
            require(name in inventory["artifacts"], "unbound stage artifact: " + name)
            return bound_json(member(directory, name), inventory["artifacts"][name])

        times[stage] = stage_timing(read, stage, entry["plan_sha256"], seed)
        if stage.startswith("fit_"):
            fit = read("fit.json")
            seed_field(fit, seed, "fit")
            arm = stage.removeprefix("fit_")
            adapter = str(PurePosixPath(plan["root"]) / "run" / stage / "adapter")
            require(fit["arm"] == arm and fit["adapter"] == adapter and same(fit["updates"], 12) and
                    same(fit["presentations"], 48), "fit route/exposure mismatch")
            require(fit["adapter_files"] and same(fit["adapter_files"],
                    {name.removeprefix("adapter/"): pin for name, pin in inventory["artifacts"].items() if name.startswith("adapter/")}),
                    "adapter custody mismatch")
            require(sum(name in fit["adapter_files"] for name in ("adapter_model.safetensors", "adapter_model.bin")) == 1 and
                    {"adapter_config.json", "DONE"} <= fit["adapter_files"].keys(), "incomplete adapter")
            saved = read("adapter/adapter_config.json")
            require(saved["r"] == 8 and saved["lora_alpha"] == 16 and saved["lora_dropout"] == .05 and
                    set(saved["target_modules"]) == set(config["target_modules"]) and saved.get("bias") == "none" and
                    not saved.get("modules_to_save") and not saved.get("use_dora") and not saved.get("use_rslora"), "adapter structure differs")
            runtime["check_fit_manifest"](read("adapter/train_manifest.json"), inputs[f"train_{arm}.json"], config)
            fits[stage] = fit
        else:
            cells[stage] = analyze_cell(stage, read, inventory["artifacts"], plan, calls, dev, fits, corpus, scores["cells"][stage], seed)
    require(len({value["pid"] for value in times.values()}) == 8, "workers are not eight fresh identities")
    require(finite(complete["time"]) and all(value["released_wall_time"] <= complete["time"] for value in times.values()),
            "completion precedes closed/released workers")
    for previous, following in zip(STAGES, STAGES[1:]):
        require(times[previous]["released_wall_time"] <= times[following]["started_wall_time"], "stage order/overlap mismatch")
    signature = {key: plan[key] for key in ("source_hashes", "engine", "params", "model_files", "chat_template", "probe_sha256")}
    signature.update(revision=plan["binding"]["revision"], calls=calls,
                     config={key: value for key, value in config.items() if key not in ("seed", "model", "note")},
                     training_encoding={arm: inputs[f"train_{arm}.json"]["encoding"] for arm in ARMS})
    return dict(learner_seed=seed, cells=cells, paired_flips=paired_flips(cells), training_exposure=exposure, receipt_bindings=receipt_bindings,
                timing=dict(stages=times, started_receipt_to_last_release_seconds=times[STAGES[-1]]["released_wall_time"] - times[STAGES[0]]["started_wall_time"],
                            summed_stage_seconds=sum(value["started_receipt_to_release_seconds"] for value in times.values()),
                            limitation="Stage wall intervals include release; generation monotonic intervals are nested, not additive. Collection/transfer/model verification excluded."),
                pins={key: entry[key] for key in ("root", "logs", "scores", "plan_sha256", "completion_sha256", "scores_sha256", "collection_sha256")}), signature


def pair(left, right):
    require([row["row_id"] for row in left] == [row["row_id"] for row in right], "paired row IDs/order differ")
    groups = {name: [] for name in ("gains", "losses", "both_correct", "both_wrong")}
    for after, before in zip(left, right, strict=True):
        after_pass, before_pass = after["score"]["passed"], before["score"]["passed"]
        require(type(after_pass) is bool and type(before_pass) is bool, "paired decisions must be boolean")
        group = "both_correct" if after_pass and before_pass else "gains" if after_pass else "losses" if before_pass else "both_wrong"
        groups[group].append(after["row_id"])
    return dict(total=len(left), counts={name: len(rows) for name, rows in groups.items()}, row_ids=groups,
                net_count=len(groups["gains"]) - len(groups["losses"]))


def paired_flips(cells):
    pairs = [("prompt_elicitation", "OFF__present", "OFF__withdrawn"),
             ("ordinary_transfer", "fitWithdrawn__withdrawn", "OFF__withdrawn")]
    pairs += [(f"training_parent_{arm}", f"fitPresent__{arm}", f"fitWithdrawn__{arm}") for arm in ARMS]
    pairs += [(f"matched_OFF_{state}_{arm}", f"{state}__{arm}", f"OFF__{arm}") for state in STATES[1:] for arm in ARMS]
    pairs += [(f"readout_parent_{state}", f"{state}__present", f"{state}__withdrawn") for state in STATES[1:]]
    return {panel: {name: dict(x_cell=left, y_cell=right, **pair(cells[left][panel]["rows"], cells[right][panel]["rows"]))
                    for name, left, right in pairs} for panel in PANELS}


def mean_range(values):
    return dict(mean=statistics.mean(values), minimum=min(values), maximum=max(values), learner_seeds=len(values))


def input_locations(manifest):
    paths = [local_path(manifest["source"]["root"])]
    paths += [local_path(binding["path"]) for binding in manifest["runtimes"].values()]
    paths += [local_path(binding["path"]) for binding in manifest["upstream_receipts"].values()]
    for entry in manifest["runs"]:
        paths += [local_path(entry["root"]), local_path(entry["logs"]), local_path(entry["scores"]).parent]
    return paths


def analyze(manifest):
    require(manifest["schema"] == SCHEMA and same(manifest.get("preselected_learner_seeds"), [0, 1, 2]) and
            manifest.get("selection_before_outcomes") is True, "preselected three-seed manifest required")
    entries = manifest["runs"]
    require(type(entries) is list and len(entries) == 3 and all(type(entry.get("learner_seed")) is int for entry in entries) and
            sorted(entry["learner_seed"] for entry in entries) == [0, 1, 2], "exact seeds 0,1,2 required")
    locations = [local_path(entry[key]) for entry in entries for key in ("root", "logs", "scores")]
    require(len(set(locations)) == 9, "distinct snapshot/log/score paths required")
    corpus, runtimes = load_sources(manifest)
    expected = build_expected(corpus)
    runs, signatures = [], []
    for entry in sorted(entries, key=lambda value: value["learner_seed"]):
        run, signature = analyze_seed(entry, manifest, corpus, runtimes, expected)
        runs.append(run)
        signatures.append(signature)
    require(all(same(signature, signatures[0]) for signature in signatures[1:]), "cross-seed data/readout/config drift")
    tables = {panel: [dict(cell=cell, metric=METRICS[panel], denominator_per_seed=12,
                           counts=[run["cells"][cell][panel]["count"] for run in runs],
                           descriptive_count=mean_range([run["cells"][cell][panel]["count"] for run in runs]),
                           syntax_valid=[run["cells"][cell][panel]["syntax_valid_count"] for run in runs],
                           length_finishes=[run["cells"][cell][panel]["termination"]["length"] for run in runs],
                           prompt_tokens=[run["cells"][cell][panel]["prompt_tokens"] for run in runs],
                           output_tokens=[run["cells"][cell][panel]["output_tokens"] for run in runs],
                           generation_seconds=[run["cells"][cell][panel]["generation_seconds"] for run in runs])
                      for cell in CELLS] for panel in PANELS}
    for name, pin in SOURCE_PINS.items():
        check_pin(member(local_path(manifest["source"]["root"]), name), pin)
    for name, pin in RUNTIME_PINS.items():
        check_pin(local_path(manifest["runtimes"][name]["path"]), pin)
    for binding in manifest["upstream_receipts"].values():
        check_pin(local_path(binding["path"]), binding["sha256"])
    return dict(schema=SCHEMA, claim=CLAIM, learner_seeds=[0, 1, 2], total_responses=432, source=manifest["source"],
                runtimes=manifest["runtimes"], upstream_receipts=manifest["upstream_receipts"],
                manifest_sha256=hashlib.sha256(canonical(manifest).encode()).hexdigest(),
                manifest_hash_kind="canonical JSON UTF-8, no trailing newline", tables=tables, per_seed=runs,
                semantic_prose_score=None, composite_metric=None, automatic_pass=False, clean_ancestry_certified=False,
                limitations=["Exact restatement has no prose-syntax or semantic failure judgment; raw prose and source context are retained for later manual review.",
                             "Byte custody and unchanged CPU metrics only; no native token reencoding, weight deserialization, model identity/ancestry recertification or process liveness check.",
                             "Preselection is an explicit supplied manifest declaration, not independently timestamp-certified here."])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    manifest_path, output = local_path(args.manifest), local_path(args.output)
    manifest = decode(manifest_path.read_bytes())
    require(output != manifest_path and not any(output == path or output.is_relative_to(path) for path in input_locations(manifest)),
            "output must be outside all inputs")
    require(not output.exists(), "output already exists")
    result = analyze(manifest)
    with output.open("x", encoding="utf-8") as stream:
        stream.write(canonical(result) + "\n")


if __name__ == "__main__":
    main()
