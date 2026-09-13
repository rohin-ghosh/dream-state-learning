"""Local pinned evidence reduction only; never invokes native lifecycle APIs."""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import copy
import hashlib
import json
import math
from pathlib import Path
import sys
from types import ModuleType


SCHEMA = "astra_own_replay_repair_analysis_20260913_v1"
INPUT_SCHEMA = SCHEMA + "_inputs"
SCOPE = "astra_own_replay_repair_paired_20260913_v1"
ARMS = ("REPLAY", "EXTRA_MEMORY")
HISTORY = ("LOWER", "HIGH", "LR0")
PANELS = ("exact", "paraphrase", "held", "canary")
COUNTS, FLOORS = (14, 8, 8), (8, 7, 5)
PINS = {
    "runner": ("astra_own_replay_repair_run_20260913.py", "f1e3782378959f0c2552eaf9646a6b8827b876652a535d3248e38fe28371c4fe"),
    "core": ("astra_own_replay_repair_core_20260913.py", "9d8777ea3bfdcf92bace3b1a459644b9249dae108db9d5d6a3e35433e0bcff93"),
    "memory": ("astra_real_record_memory_core_20260913.py", "2c5538f5b63cbb4e592f40822561b4d62595ab3c9d7d193f084b91f9a064e8ef"),
    "formation": ("astra_level1_real_record_core_20260913_v2.py", "b023a4321d0a20e465c96914316a730fbb2dd897c11369a9eb62d2d8f1248ef5"),
    "native_validator": ("astra_level1_real_record_run_20260913.py", "3c03304ee5309517ce34f91b121594f0070b37bfb14f31f429f915d8310cc20e"),
    "material": ("astra_level1_perception_reflection_material_20260913.py", "4648f8542b1babb10f6ffda4bf023024d71b8c9834a32e2242a7f064a94a8941"),
    "utilities": ("astra_actual_memory_analysis_20260913.py", "2d462f9dab797d72b397c33b0e823b65fda4ca8b7637babecf25b07cc144f994"),
    "observation": ("astra_own_source_replay_core_20260913.py", "f64e65a462afe7c2ed28d3dae16289d12bfc62b624b8d4900ff66a713f105f1a"),
}
PROTOCOL_PIN = "fb523ee6d96ef6186ae187c3c9b4482b25084fa49f292aae15a34affa87103c7"
TRAINER_PIN = "7bbf165fcb4b8ae3a1180328bcd19f57382c30516daddc95fd61e8a2c749fad7"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def equal(left, right, message):
    require(canonical(left) == canonical(right), message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "duplicate JSON key")
            result[key] = value
        return result
    def invalid(value):
        raise ValueError("nonfinite JSON: " + value)
    value = json.loads(Path(path).read_bytes(), object_pairs_hook=unique, parse_constant=invalid)
    canonical(value)
    return value


def count(value, expected=None):
    require(type(value) is int and value >= 0, "integer count required, not bool")
    require(expected is None or value == expected, "count disagreement")
    return value


def pin(path, checksum):
    path = Path(path)
    require(path.is_file() and not path.is_symlink(), "regular nonsymlink file required")
    require(type(checksum) is str and len(checksum) == 64 and digest(path) == checksum, "file pin differs: " + path.name)
    return path


def local(root, name):
    name = Path(name)
    require(not name.is_absolute() and ".." not in name.parts, "unsafe relative evidence path")
    path = Path(root) / name
    require(path.resolve().is_relative_to(Path(root).resolve()), "evidence path escapes mirror")
    return path


def load_module(path, checksum):
    source = pin(path, checksum).read_bytes()
    module = ModuleType("repair_analysis_" + Path(path).stem)
    module.__file__ = str(path)
    exec(compile(source, str(path), "exec"), module.__dict__)
    return module


def extract(path, checksum, names, namespace):
    source = pin(path, checksum).read_bytes()
    nodes = [node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef) and node.name in names]
    require({node.name for node in nodes} == set(names), "frozen pure functions missing")
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), namespace)
    return namespace


def load_apis(directory, source_root, protocol_path):
    pin(protocol_path, PROTOCOL_PIN)
    paths = {key: Path(directory) / value[0] for key, value in PINS.items()}
    for key, path in paths.items():
        pin(path, PINS[key][1])
    apis = {key: load_module(paths[key], PINS[key][1]) for key in ("core", "memory", "formation", "material", "utilities", "observation")}
    apis["material"].SOURCE_ROOT = Path(source_root).resolve()
    apis["dependencies"] = apis["formation"].load_dependencies(source_root)
    apis["retention"] = apis["material"].build_dataset("perception", seed=0)
    apis["corpus"], unused = apis["material"].load_sources()
    apis["pure"] = extract(paths["runner"], PINS["runner"][1], {"check_fit"},
        dict(require=require, ARMS=ARMS, MEMORY_COUNTS=COUNTS, PASSES=8, LR=3e-5, TRAINER_PIN=TRAINER_PIN, math=math))
    apis["response"] = extract(paths["native_validator"], PINS["native_validator"][1], {"validate_response"},
        dict(require=require, math=math))["validate_response"]
    return apis


class FrozenScorer:
    """Audit/project once, then apply the unchanged production row scorer."""
    def __init__(self, capture, dataset, retention, apis):
        self.apis = apis
        self.retention_cache = apis.setdefault("retention_score_cache", {})
        rebuilt, self.executions = apis["memory"]._project(capture, apis["formation"], apis["dependencies"])
        equal(rebuilt, dataset, "original memory projection differs")
        equal(retention, apis["retention"], "original perception sources differ")
        self.rows = {row["row_id"]: row for row in dataset["rows"]}
        self.retention = {panel: {row["row_id"]: row for row in retention["evaluation"][panel]} for panel in ("held", "canary")}

    def __call__(self, panel, row_id, raw, finish, messages):
        if panel in ("held", "canary"):
            row = self.retention[panel][row_id]
            equal(messages, row["input_messages"], "retention input messages differ")
            key = (row_id, raw, finish)
            if key not in self.retention_cache:
                self.retention_cache[key] = self.apis["material"].score_row(row, raw, finish)
            return copy.deepcopy(self.retention_cache[key])
        row = self.rows[row_id]
        key = "input_messages" if panel == "exact" else "paraphrase_input_messages"
        equal(messages, row[key], "source-withdrawn memory cue differs")
        score = self.apis["formation"].score_record(raw, finish, self.executions[row_id], self.apis["dependencies"])
        return dict(compiler=self.apis["memory"].COMPILER, row_id=row_id, variant=panel,
            endpoint="exact_cue_acquisition_persistence" if panel == "exact" else "paraphrase_transfer",
            target_sha256=row["target_sha256"], source=copy.deepcopy(row["source"]),
            exact_target_bytes=finish == "stop" and raw.encode("utf-8") == row["raw_target"].encode("utf-8"),
            score=score, native_identity_verified=False)


def load_bundle(entry):
    require(set(entry) == {"seed", "root", "plan_sha256", "completion_sha256", "scores", "collection"}, "seed manifest fields differ")
    count(entry["seed"])
    require(entry["seed"] in (0, 1, 2) and Path(entry["root"]).is_absolute(), "seed/local mirror required")
    root = Path(entry["root"])
    for name in ("controller_failure.json", "prepare_failure.json"):
        require(not (root / name).exists(), "failed native root")
    plan = read(pin(root / "plan.json", entry["plan_sha256"]))
    complete = read(pin(root / "capture_complete.json", entry["completion_sha256"]))
    loaded = {}
    for name in ("scores", "collection"):
        record = entry[name]
        require(set(record) == {"path", "sha256"} and Path(record["path"]).is_absolute(), "report path/pin required")
        loaded[name] = read(pin(record["path"], record["sha256"]))
    require(Path(entry["scores"]["path"]).parent == Path(entry["collection"]["path"]).parent, "collection/report directory differs")
    require(not (Path(entry["scores"]["path"]).parent / "collection_failure.json").exists(), "failed collection")
    equal(loaded["collection"], dict(scores_sha256=entry["scores"]["sha256"], completion_sha256=entry["completion_sha256"]), "collection pin join differs")
    files = {}
    for name, checksum in {**plan["input_hashes"], **plan["snapshot_hashes"]}.items():
        path = pin(local(root, name), checksum)
        if name.endswith(".json"):
            files[name] = read(path)
    for stage, inventory in complete["stages"].items():
        for name, checksum in inventory.items():
            require("failure" not in name, "failed stage receipt")
            if name.endswith(".json"):
                relative = "run/" + stage + "/" + name
                files[relative] = read(pin(local(root, relative), checksum))
    return dict(entry=entry, plan=plan, complete=complete, report=loaded["scores"], files=files)


def validate_calls(calls, dataset, retention):
    expected = []
    for panel, key in (("exact", "input_messages"), ("paraphrase", "paraphrase_input_messages")):
        expected.extend((panel, row["row_id"], row[key]) for row in dataset["rows"])
    for panel in ("held", "canary"):
        expected.extend((panel, row["row_id"], row["input_messages"]) for row in retention["evaluation"][panel])
    equal([(call["panel"], call["row_id"], call["messages"]) for call in calls], expected, "missing/substituted/reordered readout calls")
    require(len({call["call_id"] for call in calls}) == len(calls), "duplicate call identity")
    for call in calls:
        tokens = call["native"]["prompt_token_ids"]
        require(type(tokens) is list and tokens and all(type(token) is int and token >= 0 for token in tokens), "malformed prompt tokens")


def rescore_cells(cells, calls, scorer, seed, utilities):
    require(set(cells) == set(PANELS), "missing/extra panel")
    index = {}
    for panel in PANELS:
        denominator = COUNTS[seed] if panel in ("exact", "paraphrase") else 48 if panel == "held" else 12
        index[panel] = utilities.validate_rows(cells[panel], panel, denominator, seed)
        expected = [call for call in calls if call["panel"] == panel]
        equal([row["row_id"] for row in cells[panel]], [call["row_id"] for call in expected], "cell/call order differs")
        for call, row in zip(expected, cells[panel], strict=True):
            equal(row["score"], scorer(panel, row["row_id"], row["raw"], row["finish_reason"], call["messages"]), "frozen raw rescore disagreement")
    return index


def summarize_cells(cells, utilities):
    result = {}
    for panel in PANELS:
        metrics = utilities.MEMORY_METRICS if panel in ("exact", "paraphrase") else utilities.RETENTION_METRICS
        result[panel] = dict(denominator=len(cells[panel]),
            totals={metric: sum(utilities.metric(row, panel, metric) for row in cells[panel]) for metric in metrics},
            formats=dict(Counter((row["score"]["score"] if panel in ("exact", "paraphrase") else row["score"])["format"] for row in cells[panel])),
            errors=utilities.error_breakdown(cells[panel], panel))
    return result


def screen(seed, cells, baseline, utilities):
    losses = {}
    for panel in ("held", "canary"):
        losses[panel] = sorted(row_id for row_id in baseline[panel]
            if utilities.metric(baseline[panel][row_id], panel, "passed") and not utilities.metric(cells[panel][row_id], panel, "passed"))
    exact = sum(utilities.metric(row, "exact", "production_eligible") for row in cells["exact"].values())
    return dict(exact_eligible=exact, exact_denominator=COUNTS[seed], threshold=FLOORS[seed], lr0_correct_regressions=losses,
        passed=exact >= FLOORS[seed] and not any(losses.values()), exploratory=True, execution_gate=False, scientific_pass=None)


def constants(dataset, calls, scorer, cells, utilities):
    candidates = {row["target_sha256"]: row["raw_target"] for row in dataset["rows"]}
    variants = {}
    for panel in ("exact", "paraphrase"):
        results = []
        for checksum, raw in candidates.items():
            scores = [scorer(panel, call["row_id"], raw, "stop", call["messages"])["score"] for call in calls if call["panel"] == panel]
            results.append(dict(target_sha256=checksum, content_correct=sum(score["content_correct"] for score in scores),
                                production_eligible=sum(score["production_eligible"] for score in scores)))
        best = max(row["content_correct"] for row in results)
        variants[panel] = dict(denominator=len(dataset["rows"]), candidates=results, oracle_best_content_correct=best,
            tied_best_target_sha256=[row["target_sha256"] for row in results if row["content_correct"] == best],
            actual_content_correct={arm: sum(utilities.metric(row, panel, "content_correct") for row in panels[panel]) for arm, panels in cells.items()})
    return dict(variants=variants, candidate_set="each distinct exact raw target in original admitted memory rows",
        scope="Evaluator-only same-panel oracle constant, assumed stop; not native execution, causal proof or a new training source.")


def validate_training(prepared, mixture, arm, core):
    require(prepared["schema"] == core.ENCODING_SCHEMA and prepared["arm"] == arm, "encoding schema/arm differs")
    equal(prepared["encoding_sha256"], core.value_hash({key: value for key, value in prepared.items() if key != "encoding_sha256"}), "encoding hash differs")
    equal(prepared["material_sha256"], mixture["material_sha256"], "encoding/material join differs")
    rows = mixture["arms"][arm]["rows"]
    count(prepared["rows"], len(rows))
    count(prepared["updates"], 8 * len(rows))
    equal(prepared["presentation_counts"], {row["row_id"]: 8 for row in rows}, "presentation dose differs")
    equal(prepared["training_items_sha256"], core.value_hash(prepared["items"]), "training item hash differs")
    equal(prepared["epoch_order_sha256"], core.value_hash(prepared["epoch_order"]), "epoch hash differs")
    require(len(prepared["epoch_order"]) == 8, "eight passes required")
    for order in prepared["epoch_order"]:
        equal(sorted(order), sorted(row["row_id"] for row in rows), "incomplete epoch")
    require(len(prepared["items"]) == len(prepared["encoding"]) == len(rows), "missing encoded lineage")
    for index, (row, audit) in enumerate(zip(rows, prepared["encoding"], strict=True)):
        for key in ("row_id", "source_row_id", "item_kind"):
            equal(audit[key], row[key], "encoding source lineage differs")
        item = prepared["items"][index]
        equal(item["group"], row["row_id"], "training item group differs")
        equal(item["meta"]["target_sha256"], row["target_sha256"], "training raw target pin differs")
        for key in ("source_row_id", "item_kind", "presentation_index"):
            equal(item["meta"][key], row[key], "training item provenance differs")
        ids, labels = audit["input_ids"], audit["labels"]
        require(len(ids) == len(labels) <= 1024 and all(type(token) is int and token >= 0 for token in ids), "invalid training IDs/length")
        require(all(type(label) is int and label in (-100, ids[position]) for position, label in enumerate(labels)), "invalid target labels")
        equal([label for label in labels if label != -100], audit["supervised_ids"], "supervised token denominator differs")
        prefix = audit["native_prompt"]["prompt_token_ids"]
        equal(ids[:len(prefix)], prefix, "training prompt prefix differs")
        equal(labels[:len(prefix)], [-100]*len(prefix), "unmasked training context")
        require(audit["full_assistant_text"].startswith(audit["native_prompt"]["rendered_prompt"] + row["raw_target"]), "training raw target changed")
        spans = item["spans"]
        require(len(spans) in (3, 4) and spans[0] == [audit["native_prompt"]["rendered_prompt"], False, "context"] and
                spans[1] == [row["raw_target"], True, "skill_target"] and spans[2][1:] == [True, "assistant_end"] and
                type(spans[2][0]) is str and bool(spans[2][0]), "exact target/EOS spans differ")
        require(len(spans) == 3 or spans[3] == [audit["template_tail"], False, "template_tail"], "template tail span differs")
        equal("".join(span[0] for span in spans), audit["full_assistant_text"], "full training byte serialization differs")
        supervised = audit["supervised_ids"]
        require(len(supervised) >= 2 and ids[len(prefix):len(prefix)+len(supervised)] == supervised and
                labels[len(prefix):len(prefix)+len(supervised)] == supervised and
                all(label == -100 for label in labels[len(prefix)+len(supervised):]), "target/EOS mask is not one complete span")
    per_kind = {}
    for kind in ("memory", "observation_replay", "extra_memory"):
        selected = [audit for audit in prepared["encoding"] if audit["item_kind"] == kind]
        total = sum(len(audit["input_ids"]) for audit in selected)
        target = sum(len(audit["supervised_ids"]) for audit in selected)
        per_kind[kind] = dict(rows=len(selected), presentations=8*len(selected), total_tokens=total, target_tokens=target,
            context_tokens=total-target, train_tokens_seen=8*total, actual_supervised_tokens=8*target, actual_context_tokens=8*(total-target))
    equal(prepared["per_kind"], per_kind, "mixed lineage token/dose accounting differs")
    for key in ("total_tokens", "target_tokens", "context_tokens", "train_tokens_seen", "actual_supervised_tokens", "actual_context_tokens"):
        count(prepared[key], sum(value[key] for value in per_kind.values()))
    count(prepared["actual_padded_tokens"], prepared["train_tokens_seen"])
    count(prepared["padding_tokens"], 0)
    count(prepared["presentations"], prepared["updates"])
    return {key: value for key, value in prepared.items() if key not in ("items", "encoding", "epoch_order")}


def validate_replay_sources(mixture, admission, plan, apis):
    observation, corpus = apis["observation"], apis["corpus"]
    records, unused = observation.inventory(apis["retention"], apis["material"], corpus)
    selected = [row for row in records if row["selected"]]
    producer = dict(learner_seed=mixture["seed"], adapter=plan["parent"]["adapter"], adapter_files=plan["parent"]["adapter_files"],
        model=plan["model"], model_files=plan["model_files"], parent_plan_sha256=plan["parent"]["plan_sha256"])
    equal(admission["producer"], producer, "replay producer is not original recipient")
    producer_hash = observation.sha(observation.encoded(producer))
    require(admission["schema"] == observation.SCHEMA and admission["boundary"] == observation.BOUNDARY, "admission schema differs")
    require(admission["native_identity_verified"] is False and admission["training_export_ready"] is False and admission["fit_decision"] is None, "admission flags promoted")
    equal([admission[key] for key in ("source_population_denominator", "source_admissible_denominator", "requested_denominator", "submitted")], [96, 48, 24, 24], "source counts differ")
    require(len(admission["responses"]) == 24 and admission["missing_request_ids"] == [], "source response missing")
    accepted, audits = [], []
    for index, (row, saved) in enumerate(zip(selected, admission["responses"], strict=True)):
        request = dict(schema=observation.SCHEMA, row_id=row["row_id"], source_id=row["source_id"], input_messages=row["input_messages"],
            input_sha256=row["input_sha256"], producer_sha256=producer_hash, source_split="train")
        request_id = observation.sha(observation.encoded(request))
        response = saved["response"]
        require(set(response) == {"request_id", "input_sha256", "producer_sha256", "raw", "finish_reason"}, "closed source response differs")
        equal([response["request_id"], response["input_sha256"], response["producer_sha256"]],
            [request_id, row["input_sha256"], producer_hash], "source request/producer binding differs")
        require(type(response["raw"]) is str, "raw child response required")
        assessment = corpus.assess_source(row["source"])
        require(assessment["admissible"], "unsupported replay source")
        judge = corpus._interface().judge_record(response["raw"], assessment["execution"])
        errors = [] if response["finish_reason"] == "stop" else ["stop_completion_required"]
        if not judge["eligible"]:
            errors.extend(judge["failures"])
        raw_hash = hashlib.sha256(response["raw"].encode()).hexdigest()
        response_hash = observation.sha(observation.encoded(response))
        audit = dict(submission_index=index, response=response, response_sha256=response_hash, raw_sha256=raw_hash,
            eligible=not errors, errors=errors, source_judge=judge)
        equal(saved, audit, "source admission raw rescore disagreement")
        audits.append(audit)
        if not errors:
            accepted.append(dict(row_id=row["row_id"], request_id=request_id, input_messages=row["input_messages"], raw_target=response["raw"],
                target_sha256=raw_hash, source=row["source"], producer_sha256=producer_hash,
                source_proof=dict(original_train_row_id=row["row_id"], original_source_id=row["source_id"], input_sha256=row["input_sha256"],
                    supplied_response_sha256=response_hash, target_origin="SUPPLIED_RAW_CHILD_RESPONSE_ONLY")))
    equal(admission["admitted"], accepted, "admitted source/raw lineup differs")
    count(admission["admitted_count"], len(accepted))
    equal(mixture["replay_rows"], accepted, "replay material raw lineage differs")
    equal(admission["rejected"], [row for row in audits if not row["eligible"]], "rejected source evidence differs")
    equal(mixture["replay_rejected"], admission["rejected"], "rejected source material differs")


def validate_snapshot_joins(plan, files, seed, core):
    history = files["memory_history/plan.json"]
    require(plan["specification"]["memory_history"]["plan_sha256"] == core.MEMORY_PLAN_PINS[seed], "immutable original memory plan differs")
    for name in ("dataset.json", "capture.json", "retention.json", "calls.json"):
        require(plan["snapshot_hashes"]["memory/"+name] == history["input_hashes"][name], "original memory source/prefix pin differs")
    equal(plan["parent"], history["parent"], "original recipient plan differs")
    for key in ("model", "model_files", "params"):
        equal(plan[key], history[key], "original model/inference setting differs")
    binding = plan["specification"]["capture"]
    for name, field in (("plan.json", "plan_sha256"), ("completion.json", "completion_sha256"), ("replay_report.json", "report_sha256")):
        equal(plan["snapshot_hashes"]["capture/"+name], binding[field], "replay capture snapshot pin differs")
    report = files["capture/replay_report.json"]
    equal(report["plan_sha256"], binding["plan_sha256"], "replay capture plan differs")
    equal(report["completion_sha256"], binding["completion_sha256"], "replay capture completion differs")
    equal(report["seed_reports"][str(seed)]["sha256"], plan["snapshot_hashes"]["capture/admission.json"], "capture/admission pin differs")


def reduce_seed(bundle, apis, scorer_factory=FrozenScorer):
    entry, plan, report, complete, files = (bundle[key] for key in ("entry", "plan", "report", "complete", "files"))
    utilities = apis["utilities"]
    seed = count(entry["seed"])
    require(seed in (0, 1, 2), "seed differs")
    equal([plan["specification"]["seed"], plan["specification"]["fit_seed"], report["seed"]], [seed]*3, "learner seed differs")
    require(plan["scope"] == report["scope"] == complete["scope"] == SCOPE, "scope differs")
    require(plan["self_sha256"] == plan["specification"]["runner_sha256"] == PINS["runner"][1], "runner pin differs")
    require(plan["specification"]["core"]["sha256"] == PINS["core"][1] and plan["specification"]["protocol"]["sha256"] == PROTOCOL_PIN, "core/protocol pin differs")
    require(report["plan_sha256"] == complete["plan_sha256"] == entry["plan_sha256"] and
            report["completion_sha256"] == entry["completion_sha256"], "plan/completion join differs")
    equal(report["source_bindings"], {key: plan["specification"][key] for key in ("core", "protocol", "capture")}, "source binding differs")
    equal(report["input_hashes"], plan["input_hashes"], "input pins differ")
    equal(report["parent"], plan["parent"], "original parent differs")
    require(report["native_capture_custody_checked"] is True and complete["scored"] is False and
            report["automatic_pass"] is False and report["scientific_pass"] is None, "custody/promotion flags differ")
    mixture, dataset, capture, retention, calls = (files[name] for name in ("mixture.json", "memory/dataset.json", "memory/capture.json", "memory/retention.json", "calls.json"))
    apis["core"].validate_material(mixture)
    validate_replay_sources(mixture, files["capture/admission.json"], plan, apis)
    validate_snapshot_joins(plan, files, seed, apis["core"])
    equal(mixture["memory_rows"], dataset["rows"], "memory raw target lineage differs")
    equal(mixture["parent"], plan["parent"], "mixture parent differs")
    count(mixture["seed"], seed)
    memory_count, replay_count = len(dataset["rows"]), len(mixture["replay_rows"])
    count(memory_count, COUNTS[seed])
    equal(report["counts"], plan["counts"], "reported counts differ")
    equal(plan["counts"], dict(memory=memory_count, replay=replay_count, rows_per_arm=memory_count+replay_count), "mixed counts differ")
    expected_status = "READY" if replay_count else "REPLAY_UNAVAILABLE"
    require(plan["status"] == report["status"] == complete["status"] == expected_status, "unavailable/status mismatch")
    stages = [arm + suffix for arm in ARMS for suffix in ("_fit", "_readout")] if replay_count else []
    equal(plan["stages"], stages, "missing/extra planned stage")
    equal(sorted(complete["stages"]), sorted(stages), "missing/extra complete stage")
    equal(calls, files["memory/calls.json"], "original readout prefixes changed")
    validate_calls(calls, dataset, retention)
    scorer = scorer_factory(capture, dataset, retention, apis)
    history_sources = {"LOWER": files["lower_history/scores.json"], "HIGH": files["memory_history/scores.json"], "LR0": files["memory_history/scores.json"]}
    historical = {}
    equal(report["historical_bindings"], {key: plan["specification"][key] for key in ("memory_history", "lower_history")}, "historical bindings differ")
    for history in HISTORY:
        prefix = "lower_history" if history == "LOWER" else "memory_history"
        binding, source = plan["specification"][prefix], history_sources[history]
        require(plan["snapshot_hashes"][prefix + "/scores.json"] == binding["scores_sha256"] and
                plan["snapshot_hashes"][prefix + "/plan.json"] == binding["plan_sha256"] and
                plan["snapshot_hashes"][prefix + "/completion.json"] == binding["completion_sha256"], "historical snapshot custody differs")
        require(source["seed"] == seed and source["plan_sha256"] == binding["plan_sha256"] and
                source["completion_sha256"] == binding["completion_sha256"], "historical learner/plan differs")
        equal(source["parent"], plan["parent"], "historical original parent differs")
        source_arm = "LR0" if history == "LR0" else "WRITE"
        equal(report["historical_cells"][history], source["cells"][source_arm], "historical raw cell substitution")
        equal(report["historical_manifests"][history], source["fits"][source_arm], "historical fit substitution")
        historical[history] = rescore_cells(report["historical_cells"][history], calls, scorer, seed, utilities)
    equal(report["reused_endpoints"], {name: dict(noncontemporaneous=True, incremental_calls=0, incremental_updates=0, incremental_fits=0) for name in HISTORY}, "historical comparisons must be noncontemporaneous")
    active_arms = ARMS if replay_count else ()
    count(plan["calls_per_arm"], len(calls) if replay_count else 0)
    count(plan["updates_per_arm"], 8*(memory_count+replay_count) if replay_count else 0)
    for key in ("cells", "fits", "training_costs", "parameter_diagnostics", "screen"):
        equal(sorted(report[key]), sorted(active_arms), "missing/extra arm: " + key)
    results, indexed = {}, {}
    for arm in active_arms:
        indexed[arm] = rescore_cells(report["cells"][arm], calls, scorer, seed, utilities)
        route = dict(name="real_record_memory_" + arm.lower(), id=1, path=plan["root"] + "/run/" + arm + "_fit/adapter")
        readout = "run/" + arm + "_readout/"
        equal(files[readout + "identity.json"], dict(arm=arm, route=route, model_files=plan["model_files"], parent=plan["parent"], params=plan["params"]), "readout identity differs")
        equal(files[readout + "readout.json"], dict(arm=arm, calls=len(calls), updates=0), "readout count differs")
        for call in calls:
            request_name, response_name = call["call_id"] + ".request.json", call["call_id"] + ".response.json"
            request, response = files[readout + request_name], files[readout + response_name]
            equal(request, dict(call, params=plan["params"], lora_request=route), "native exact prompt/route differs")
            apis["response"](request, response, route)
            row = indexed[arm][call["panel"]][call["row_id"]]
            equal([row["raw"], row["finish_reason"], row["response_sha256"]],
                  [response["text"], response["finish_reason"], complete["stages"][arm+"_readout"][response_name]], "raw response/cell join differs")
            equal(row["cost"], dict(prompt_tokens=len(response["actual_prompt_token_ids"]), output_tokens=len(response["output_token_ids"]),
                generation_seconds=response["ended"]-response["started"]), "generation cost differs")
        prepared = files["training_" + arm + ".json"]
        training = validate_training(prepared, mixture, arm, apis["core"])
        equal(report["training_costs"][arm], training, "stored training costs differ")
        fit_path = "run/" + arm + "_fit/"
        fit, receipt = files[fit_path + "adapter/train_manifest.json"], files[fit_path + "fit.json"]
        equal(report["fits"][arm], fit, "fit manifest join differs")
        count(plan["configs"][arm]["seed"], seed)
        apis["pure"]["check_fit"](fit, prepared, plan["configs"][arm], plan["parent"], arm, plan["counts"])
        equal([receipt["arm"], receipt["updates"], receipt["calls"], receipt["training_sha256"], fit["corpus"]["sha256"]],
              [arm, prepared["updates"], 0, plan["input_hashes"]["training_"+arm+".json"], plan["input_hashes"]["training_"+arm+".json"]], "fit accounting differs")
        warm = fit["warm_start"]
        for field in ("source_state", "initialized_state", "final_state"):
            utilities.inventory(warm[field])
        for history in HISTORY:
            for field in ("source_state", "initialized_state"):
                equal(warm[field], report["historical_manifests"][history]["warm_start"][field], "same parent initialization differs")
        norms = report["parameter_diagnostics"][arm]
        equal(norms, receipt["norms"], "tensor diagnostic join differs")
        require(set(norms["l2"]) == {"initial", "final", "delta"}, "missing tensor norms")
        for value in norms["l2"].values():
            utilities.number(value)
        require(count(norms["changed_elements"]) > 0 and norms["l2"]["delta"] > 0, "arm tensor change absent")
        require(norms["changed_elements"] <= sum(math.prod(row["shape"]) for row in warm["initialized_state"].values()), "changed elements exceed tensor inventory")
        screening = screen(seed, indexed[arm], historical["LR0"], utilities)
        equal(report["screen"][arm], screening, "screen cannot offset itemwise loss with gains")
        costs = {key: sum(row["cost"][key] for rows in report["cells"][arm].values() for row in rows) for key in ("prompt_tokens", "output_tokens", "generation_seconds")}
        results[arm] = dict(panels=summarize_cells(report["cells"][arm], utilities), screen=screening, training=training,
            generation_cost=costs, parameter_diagnostics=norms, fit_seconds=utilities.number(receipt["elapsed_seconds"]),
            historical_comparisons={name: {panel: {metric: utilities.pair(indexed[arm][panel], historical[name][panel], panel, metric)
                for metric in (utilities.MEMORY_METRICS if panel in ("exact", "paraphrase") else utilities.RETENTION_METRICS)} for panel in PANELS} for name in HISTORY})
    expected_cost = dict(calls=2*len(calls) if replay_count else 0, updates=16*(memory_count+replay_count) if replay_count else 0,
        fits=2 if replay_count else 0, historical_calls=0, historical_updates=0, new_source_calls=0, teacher_calls=0,
        controller_seconds=utilities.number(complete["elapsed_seconds"]))
    require(expected_cost["controller_seconds"] <= 7200, "controller budget exceeded")
    for key in ("calls", "updates", "fits"):
        count(complete[key], expected_cost[key])
        count(plan["limits"][key], expected_cost[key])
    equal(report["incremental_cost"], expected_cost, "incremental cost differs")
    diagnostic = constants(dataset, calls, scorer, report["cells"], utilities) if replay_count else None
    equal(report["best_constant"], diagnostic, "constant-record diagnostic differs")
    pairs = {panel: {metric: utilities.pair(indexed[ARMS[0]][panel], indexed[ARMS[1]][panel], panel, metric)
        for metric in (utilities.MEMORY_METRICS if panel in ("exact", "paraphrase") else utilities.RETENTION_METRICS)} for panel in PANELS} if replay_count else None
    return dict(seed=seed, status=expected_status, counts=plan["counts"], arms=results, paired_replay_minus_extra=pairs,
        historical={name: dict(noncontemporaneous=True, panels=summarize_cells(report["historical_cells"][name], utilities)) for name in HISTORY},
        best_constant=diagnostic, incremental_cost=expected_cost, all_seed_screen_available=bool(replay_count), input_pins=entry)


def reduce_cohort(bundles, apis, scorer_factory=FrozenScorer):
    require(len(bundles) == 3, "exactly three original learner pairs required")
    seeds = [bundle["entry"]["seed"] for bundle in bundles]
    require(all(type(seed) is int for seed in seeds) and sorted(seeds) == [0, 1, 2], "missing/duplicate seed")
    results = [reduce_seed(bundle, apis, scorer_factory) for bundle in sorted(bundles, key=lambda item: item["entry"]["seed"])]
    totals = {key: sum(result["incremental_cost"][key] for result in results) for key in ("calls", "updates", "fits")}
    require(totals["calls"] <= 480 and totals["updates"] <= 1632 and totals["fits"] <= 6, "cohort budget exceeded")
    return dict(schema=SCHEMA, seeds=results, totals=totals, automatic_pass=False, scientific_pass=None,
        all_three_pairs_available=all(result["all_seed_screen_available"] for result in results),
        limitations=["Three learner pairs, not independent rows, presentations or episodes; no pooled causal claim.",
            "EXTRA_MEMORY matches steps, not memory exposure, context/target tokens or wall time.",
            "LOWER/HIGH/LR0 are historical noncontemporaneous references, not new executed controls.",
            "Constant-record comparison is evaluator-only same-panel oracle, not an executed control.",
            "Frozen CPU source scorer replay and archived native receipts, not native re-execution or tensor payload verification.",
            "Exposed exploratory DEV; no fresh confirmation, parenting, H1/H2, clean ancestry or automatic promotion."])


def markdown(report):
    lines = ["# Own-source replay repair: independent local reduction", "", "| Seed | Arm | Exact eligible | Paraphrase eligible | Held content | Canary content | LR0 losses held/canary | Exploratory screen |", "|---|---|---|---|---|---|---|---|"]
    for seed in report["seeds"]:
        if seed["status"] == "REPLAY_UNAVAILABLE":
            lines.append(f"| {seed['seed']} | REPLAY_UNAVAILABLE | — | — | — | — | — | NOT ASSESSABLE |")
        for arm, result in seed["arms"].items():
            panels, screen_result = result["panels"], result["screen"]
            values = [f"{panels[panel]['totals'][metric]}/{panels[panel]['denominator']}" for panel, metric in
                (("exact", "production_eligible"), ("paraphrase", "production_eligible"), ("held", "content_correct"), ("canary", "content_correct"))]
            losses = screen_result["lr0_correct_regressions"]
            lines.append(f"| {seed['seed']} | {arm} | " + " | ".join(values) + f" | {len(losses['held'])}/{len(losses['canary'])} | {screen_result['passed']} |")
    lines += ["", "## Dose and cost"]
    for seed in report["seeds"]:
        for arm, result in seed["arms"].items():
            lines.append(f"- Seed {seed['seed']} {arm}: {result['training']['updates']} updates; lineage/token costs and itemwise paired labels in JSON.")
    lines += ["", "Incremental totals: " + canonical(report["totals"]), "", *["- " + item for item in report["limitations"]]]
    return "\n".join(lines) + "\n"


def run(manifest_path, manifest_sha256, out, module_dir, source_root, protocol_path):
    manifest = read(pin(manifest_path, manifest_sha256))
    require(set(manifest) == {"schema", "seeds"} and manifest["schema"] == INPUT_SCHEMA, "manifest schema differs")
    out = Path(out).absolute()
    require(not out.exists(), "fresh write-once output required")
    protected = [Path(source_root), Path(module_dir), Path(protocol_path), Path(manifest_path)]
    protected += [Path(entry["root"]) for entry in manifest["seeds"]]
    protected += [Path(entry[key]["path"]).parent for entry in manifest["seeds"] for key in ("scores", "collection")]
    for path in protected:
        require(out.resolve() != path.resolve() and not path.resolve().is_relative_to(out.resolve()), "output would enclose an input")
    for entry in manifest["seeds"]:
        for path in (Path(entry["root"]), Path(entry["scores"]["path"]).parent):
            require(not out.resolve().is_relative_to(path.resolve()), "output inside evidence")
    apis = load_apis(module_dir, source_root, protocol_path)
    result = reduce_cohort([load_bundle(entry) for entry in manifest["seeds"]], apis)
    result["manifest_sha256"] = manifest_sha256
    result["analysis_sha256"] = digest(__file__)
    out.mkdir()
    with (out / "analysis.json").open("x") as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    with (out / "analysis.md").open("x") as stream:
        stream.write(markdown(result))
    return {name: digest(out / name) for name in ("analysis.json", "analysis.md")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("manifest", "manifest-sha256", "out", "source-root", "protocol-path"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--module-dir", default="/tmp")
    options = vars(parser.parse_args())
    options["manifest_path"] = options.pop("manifest")
    print(json.dumps(run(**options), sort_keys=True))


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    main()
