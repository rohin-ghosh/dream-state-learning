"""Local scored-evidence reducer, never native collection, tensor loading or scoring."""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import copy
import hashlib
import json
import math
from pathlib import Path
import re


SCHEMA = "astra_actual_memory_analysis_20260913_v1"
INPUT_SCHEMA = "astra_actual_memory_analysis_inputs_20260913_v1"
SCOPE = "astra_real_record_memory_paired_write_lr0_20260913_v1"
COMPILER = "astra_real_record_source_withdrawn_memory_20260913_v1"
RUNNER_PATH = "/tmp/astra_real_record_memory_run_20260913.py"
RUNNER_PIN = "7028fa9a9b277adc6edfec2398d1885d6c55ec33eb67a1bd51ac36b37e02215e"
MEMORY_PIN = "2c5538f5b63cbb4e592f40822561b4d62595ab3c9d7d193f084b91f9a064e8ef"
FORMATION_RUNTIME_PIN = "3c03304ee5309517ce34f91b121594f0070b37bfb14f31f429f915d8310cc20e"
FORMATION_PLAN = "039f8cc66ecae40ed9cbee649011b34e4e4654fec68f5e7d51a37f5a5a5374bd"
FORMATION_COMPLETE = "51b09f9a553cfe561ae8613e299a6d4926d8df3286265498927573b41dae1274"
FORMATION_COLLECTION = "77260fe6d540beb65cd4f9717a76fc827cb3e441a23663077f72dbdbd7a70a4c"
PROTOCOL_PIN = "c056a0fb6c97d1ba93b4d2a0fa07cb70f806cfa64fef2df1769d78e80334a716"
TRAINER_PIN = "7bbf165fcb4b8ae3a1180328bcd19f57382c30516daddc95fd61e8a2c749fad7"
CAPTURE_PINS = {
    0: "46edd3aa57fb58d6e4f19c462db04d1b70d44f2bd5c2754c80423abe8680ba49",
    1: "6cddb954972b8953f0c1025e3aac5714a7a47e4fe01f22504c736ddbea2c62fb",
    2: "5ec4204e348531e7d47177e1a3db39c7a8980d2fc8350d66f84f5f9d51dad083",
}
ADMISSIONS = {0: 14, 1: 8, 2: 8}
ARMS = ("WRITE", "LR0")
MEMORY_PANELS = ("exact", "paraphrase")
RETENTION_PANELS = ("held", "canary")
PANELS = MEMORY_PANELS + RETENTION_PANELS
MEMORY_METRICS = ("production_eligible", "content_correct", "strict_canonical", "exact_target_bytes")
RETENTION_METRICS = ("passed", "content_correct", "strict")
FIELDS = ("try", "observed", "predicted", "relation")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def same(first, second, message):
    require(canonical(first) == canonical(second), message)


def validate_json(value):
    if type(value) is dict:
        require(all(type(key) is str for key in value), "JSON keys must be strings")
        for item in value.values():
            validate_json(item)
    elif type(value) is list:
        for item in value:
            validate_json(item)
    else:
        require(value is None or type(value) in (str, bool, int, float), "non-JSON value")
        require(type(value) is not float or math.isfinite(value), "nonfinite JSON number")


def read(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "duplicate JSON field")
            result[key] = value
        return result
    value = json.loads(Path(path).read_bytes(), object_pairs_hook=unique)
    validate_json(value)
    return value


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sha(value):
    require(type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None, "invalid SHA256")
    return value


def count(value, expected=None):
    require(type(value) is int and value >= 0, "nonnegative integer required, not bool")
    require(expected is None or value == expected, "count disagreement")
    return value


def number(value):
    require(type(value) in (int, float) and math.isfinite(value) and value >= 0, "nonnegative finite number required")
    return value


def boolean(value):
    require(type(value) is bool, "typed boolean required")
    return value


def pinned(record):
    require(type(record) is dict and set(record) == {"path", "sha256"}, "exact local path/SHA binding required")
    path = Path(record["path"])
    require(path.is_absolute() and path.is_file() and not path.is_symlink(), "local regular input file required")
    require(digest(path) == sha(record["sha256"]), "input file pin mismatch")
    return read(path)


def load_fit_validator(path=RUNNER_PATH):
    source = Path(path).read_bytes()
    require(hashlib.sha256(source).hexdigest() == RUNNER_PIN, "frozen memory runner pin mismatch")
    functions = [node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef) and node.name == "check_fit"]
    require(len(functions) == 1, "frozen fit validator missing")
    namespace = dict(require=require, PASSES=8, TRAINER_PIN=TRAINER_PIN, math=math)
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(path), "exec"), namespace)
    return namespace["check_fit"]


def metric(row, panel, name):
    if panel in MEMORY_PANELS:
        value = row["score"]["exact_target_bytes"] if name == "exact_target_bytes" else row["score"]["score"][name]
    else:
        value = row["score"][name]
    return boolean(value)


def join_rows(rows, denominator):
    require(type(rows) is list and len(rows) == denominator, "missing/extra scored row")
    result = {}
    for row in rows:
        require(type(row["row_id"]) is str and row["row_id"] and row["row_id"] not in result, "duplicate/invalid row ID")
        result[row["row_id"]] = row
    return result


def validate_rows(rows, panel, denominator, seed, *, original=False):
    indexed = join_rows(rows, denominator)
    metrics = MEMORY_METRICS if panel in MEMORY_PANELS else RETENTION_METRICS
    for row in rows:
        require(type(row["raw"]) is str and row["finish_reason"] in ("stop", "length"), "raw/finish differs")
        values = {name: metric(row, panel, name) for name in metrics}
        score = row["score"]["score"] if panel in MEMORY_PANELS else row["score"]
        require(type(score["format"]) is str and score["format"], "format missing")
        if row["finish_reason"] != "stop":
            require(not any(values.values()), "unfinished response counted successful")
        if panel in MEMORY_PANELS:
            outer, source = row["score"], row["score"]["source"]
            require(outer["compiler"] == COMPILER and outer["row_id"] == row["row_id"] and outer["variant"] == panel,
                    "memory compiler/row/variant mismatch")
            require(outer["endpoint"] == ("exact_cue_acquisition_persistence" if panel == "exact" else "paraphrase_transfer"),
                    "memory endpoint differs")
            require(source["state"] == "perception_seed" + str(seed) and source["capture_sha256"] == CAPTURE_PINS[seed],
                    "formation capture/seed differs")
            count(source["tick"])
            require(source["tick"] in (1, 2) and re.fullmatch(r"real-record-dev-[0-9a-f]{20}", source["task_id"]) is not None and
                    source["public_execution_id"] == f"{source['task_id']}#t{source['tick']}" and
                    source["execution_id"] == row["row_id"] == f"{source['state']}:{source['public_execution_id']}", "memory ID join differs")
            for name in ("execution_sha256", "wake_request_id", "record_request_id", "record_event_sha256", "capture_sha256"):
                sha(source[name])
            sha(outer["target_sha256"])
            require(outer["native_identity_verified"] is False and score["raw"] == row["raw"] and
                    score["finish_reason"] == row["finish_reason"], "nested raw/completion differs")
            exact = row["finish_reason"] == "stop" and hashlib.sha256(row["raw"].encode("utf-8")).hexdigest() == outer["target_sha256"]
            require(values["exact_target_bytes"] == exact, "raw exact-byte flag disagrees with target SHA")
            require(not values["strict_canonical"] or values["production_eligible"], "strict without production eligibility")
            require(not values["production_eligible"] or values["content_correct"], "production without content correctness")
            require(not exact or values["production_eligible"], "exact admitted target without production eligibility")
            require(set(score["field_correct"]) == set(FIELDS), "memory field inventory differs")
            for value in score["field_correct"].values():
                boolean(value)
        else:
            require(values["passed"] == values["content_correct"] and (not values["strict"] or values["content_correct"]),
                    "retention content/strict contract differs")
            require(score["raw"] == row["raw"] and score["finish_reason"] == row["finish_reason"] and
                    score["raw_sha256"] == hashlib.sha256(row["raw"].encode("utf-8")).hexdigest(), "retention raw/score digest differs")
        if not original:
            sha(row["response_sha256"])
            cost = row["cost"]
            require(set(cost) == {"prompt_tokens", "output_tokens", "generation_seconds"}, "call cost fields differ")
            require(count(cost["prompt_tokens"]) > 0 and count(cost["output_tokens"]) <= 192, "call token budget differs")
            number(cost["generation_seconds"])
    return indexed


def error_breakdown(rows, panel):
    scores = [row["score"]["score"] if panel in MEMORY_PANELS else row["score"] for row in rows]
    names = ("production_errors", "content_errors", "source_completion_errors") if panel in MEMORY_PANELS else (
        "source_errors", "schema_errors", "syntax_errors", "completion_errors")
    errors = {}
    for name in names:
        values = [score.get(name, []) for score in scores]
        require(all(type(value) is list and all(type(item) is str for item in value) for value in values), "malformed score errors")
        errors[name] = dict(Counter(item for value in values for item in value))
    strict = "strict_canonical" if panel in MEMORY_PANELS else "strict"
    return dict(content_failures=sum(not score["content_correct"] for score in scores),
                content_correct_non_strict=sum(score["content_correct"] and not score[strict] for score in scores),
                stopped=sum(row["finish_reason"] == "stop" for row in rows),
                length_terminated=sum(row["finish_reason"] == "length" for row in rows), errors=errors)


def pair(first, second, panel, name):
    require(set(first) == set(second), "paired row substitution/missing row")
    groups = {key: [] for key in ("both", "neither", "first_only", "second_only")}
    for row_id in first:
        left, right = metric(first[row_id], panel, name), metric(second[row_id], panel, name)
        key = "both" if left and right else "first_only" if left else "second_only" if right else "neither"
        groups[key].append(row_id)
    counts = dict(total=len(first), **{key: len(value) for key, value in groups.items()})
    return dict(counts=counts, row_ids=groups, delta=counts["first_only"] - counts["second_only"])


def reproduce_summary(cells, original, parent_score_pin):
    totals, contrasts, retained, pairs, retention = {}, {}, {}, {}, {}
    for arm in ARMS:
        totals[arm], retained[arm], retention[arm] = {}, {}, {}
        for panel in PANELS:
            rows = cells[arm][panel]
            metrics = MEMORY_METRICS if panel in MEMORY_PANELS else RETENTION_METRICS
            total = dict(denominator=len(rows), numerators={name: sum(metric(row, panel, name) for row in rows) for name in metrics},
                format_counts=dict(Counter((row["score"]["score"] if panel in MEMORY_PANELS else row["score"])["format"] for row in rows)),
                generation_costs={name: sum(row["cost"][name] for row in rows) for name in ("prompt_tokens", "output_tokens", "generation_seconds")})
            if panel in MEMORY_PANELS:
                total.update(possible_denominator=16, field_correct={name: sum(row["score"]["score"]["field_correct"][name] for row in rows) for name in FIELDS})
            totals[arm][panel] = total
            if panel in RETENTION_PANELS:
                old_rows = original["cells"]["post"][panel]["rows"]
                old, new = join_rows(old_rows, len(old_rows)), join_rows(rows, len(rows))
                same(list(new), list(old), "original retention row order/substitution differs")
                comparisons = {name: pair(new, old, panel, name) for name in RETENTION_METRICS}
                content = comparisons["passed"]
                retained[arm][panel] = dict(counts=content["counts"], retained=content["row_ids"]["both"],
                    regressed=content["row_ids"]["second_only"], gained=content["row_ids"]["first_only"],
                    original_scores_sha256=parent_score_pin)
                raw_changed = [row_id for row_id in old if old[row_id]["raw"].encode("utf-8") != new[row_id]["raw"].encode("utf-8")]
                finish_changed = [row_id for row_id in old if old[row_id]["finish_reason"] != new[row_id]["finish_reason"]]
                retention[arm][panel] = dict(metrics=comparisons, raw_changed=len(raw_changed), raw_changed_rows=raw_changed,
                    finish_changed=len(finish_changed), finish_changed_rows=finish_changed,
                    content_changed=content["counts"]["first_only"] + content["counts"]["second_only"],
                    content_regressed=content["counts"]["second_only"],
                    strict_changed=comparisons["strict"]["counts"]["first_only"] + comparisons["strict"]["counts"]["second_only"],
                    strict_regressed=comparisons["strict"]["counts"]["second_only"])
    for panel in PANELS:
        metrics = MEMORY_METRICS if panel in MEMORY_PANELS else RETENTION_METRICS
        first = join_rows(cells["WRITE"][panel], len(cells["WRITE"][panel]))
        second = join_rows(cells["LR0"][panel], len(cells["LR0"][panel]))
        pairs[panel] = {name: pair(first, second, panel, name) for name in metrics}
        contrasts[panel] = {name: result["counts"] for name, result in pairs[panel].items()}
    summary = dict(totals=totals, paired_WRITE_LR0=contrasts, original_retention=retained,
                   pair_direction="first=WRITE/second=LR0; retention first=current/second=original post")
    return summary, pairs, retention


def inventory(value):
    require(type(value) is dict and value, "missing tensor inventory")
    for name, record in value.items():
        require(name.endswith((".lora_A.weight", ".lora_B.weight")), "non-LoRA inventory key")
        require(set(record) == {"shape", "dtype", "sha256"} and type(record["shape"]) is list and record["shape"], "tensor inventory schema")
        require(all(type(size) is int and size > 0 for size in record["shape"]), "invalid tensor shape")
        require(type(record["dtype"]) is str and record["dtype"].startswith("torch."), "invalid tensor dtype")
        sha(record["sha256"])


def validate_fits(report, plan, denominator, check_fit):
    training = report["training_costs"]
    expected = dict(fit_seed=report["seed"], rows=denominator, updates=8 * denominator, presentations=8 * denominator,
                    padding_tokens=0)
    for name, value in expected.items():
        count(training[name], value)
    for name in ("total_tokens", "target_tokens", "context_tokens", "train_tokens_seen", "actual_supervised_tokens", "actual_context_tokens", "actual_padded_tokens"):
        count(training[name])
    require(training["target_tokens"] > 0 and training["context_tokens"] > 0 and
            training["total_tokens"] == training["target_tokens"] + training["context_tokens"], "per-pass token disagreement")
    for actual, source in (("train_tokens_seen", "total_tokens"), ("actual_supervised_tokens", "target_tokens"),
                           ("actual_context_tokens", "context_tokens"), ("actual_padded_tokens", "total_tokens")):
        count(training[actual], 8 * training[source])
    require(set(report["fits"]) == set(report["parameter_diagnostics"]) == set(plan["configs"]) == set(ARMS), "missing/extra fit arm")
    costs = {}
    for arm in ARMS:
        fit, config = report["fits"][arm], plan["configs"][arm]
        for name, value in dict(seed=report["seed"], rank=8, alpha=16, epochs=8, batch_size=1).items():
            count(config[name], value)
        require(config["model"] == plan["model"] and config["dropout"] == .05 and
                type(config["lr"]) in (int, float) and config["lr"] == (1e-4 if arm == "WRITE" else 0.0), "fit recipe differs")
        check_fit(fit, training, config, plan["parent"], arm)
        warm = fit["warm_start"]
        for name, value in (("adapter_count", 1), ("phase_seed", report["seed"]), ("phase_steps", 8 * denominator)):
            count(warm[name], value)
        count(warm["parent_cumulative_steps"])
        count(warm["cumulative_steps"], warm["parent_cumulative_steps"] + 8 * denominator)
        for name in ("n_items", "n_encoded", "n_skipped_no_target"):
            count(fit["corpus"][name])
        for name in ("items_truncated", "context_tokens_dropped", "target_tokens_dropped", "items_split"):
            count(fit["truncation"][name], 0)
        for name in ("source_state", "initialized_state", "final_state"):
            inventory(warm[name])
        require(set(warm["source_state"]) == set(warm["initialized_state"]) == set(warm["final_state"]), "tensor coverage differs")
        for name in warm["source_state"]:
            require(warm["source_state"][name]["shape"] == warm["initialized_state"][name]["shape"] == warm["final_state"][name]["shape"] and
                    warm["initialized_state"][name]["dtype"] == warm["final_state"][name]["dtype"], "tensor shape/dtype differs")
        norms = report["parameter_diagnostics"][arm]
        require(set(norms["l2"]) == {"initial", "final", "delta"}, "missing tensor norm")
        for value in norms["l2"].values():
            number(value)
        changed = count(norms["changed_elements"])
        total_elements = sum(math.prod(record["shape"]) for record in warm["initialized_state"].values())
        require(changed <= total_elements, "changed elements exceed tensor sizes")
        if arm == "WRITE":
            require(changed > 0 and norms["l2"]["delta"] > 0 and warm["initialized_state"] != warm["final_state"], "WRITE did not change parameters")
        else:
            require(changed == 0 and norms["l2"]["delta"] == 0 and norms["l2"]["initial"] == norms["l2"]["final"], "LR0 changed parameters")
        costs[arm] = dict(updates=fit["steps"], presentations=training["presentations"],
            train_seconds=number(fit["train_seconds"]), wall_seconds=number(fit["wall_seconds"]),
            final_loss=fit["final_loss"], mean_loss_per_epoch=fit["mean_loss_per_epoch"],
            supervised_tokens=training["actual_supervised_tokens"], context_tokens=training["actual_context_tokens"],
            padded_tokens=training["actual_padded_tokens"], parameter_diagnostics=copy.deepcopy(norms))
    same({key: value for key, value in plan["configs"]["WRITE"].items() if key != "lr"},
         {key: value for key, value in plan["configs"]["LR0"].items() if key != "lr"}, "arms differ beyond learning rate")
    for name in ("source_state", "initialized_state"):
        same(report["fits"]["WRITE"]["warm_start"][name], report["fits"]["LR0"]["warm_start"][name], "paired initial tensors differ")
    return costs


def reduce_seed(report, plan, original, entry, check_fit):
    for value in (report, plan, original):
        validate_json(value)
    seed = entry["seed"]
    require(type(seed) is int and seed in ADMISSIONS, "seed0/1/2 required")
    denominator = ADMISSIONS[seed]
    require(report["scope"] == plan["scope"] == SCOPE and report["status"] == plan["status"] == "WRITE_AVAILABLE", "wrong/incomplete report scope")
    count(report["seed"], seed)
    require(report["plan_sha256"] == entry["plan"]["sha256"] and plan["self_sha256"] == RUNNER_PIN, "source plan mismatch")
    sha(report["completion_sha256"])
    specification = plan["specification"]
    count(specification["seed"], seed)
    count(specification["fit_seed"], seed)
    require(specification["runner_sha256"] == RUNNER_PIN and specification["memory"]["sha256"] == MEMORY_PIN and
            specification["formation_runtime"]["sha256"] == FORMATION_RUNTIME_PIN and specification["protocol"]["sha256"] == PROTOCOL_PIN,
            "frozen source/protocol mismatch")
    same(specification["formation"], report["formation"], "formation plan binding differs")
    formation = report["formation"]
    require(formation["plan_sha256"] == FORMATION_PLAN and formation["completion_sha256"] == FORMATION_COMPLETE and
            formation["collection"]["sha256"] == FORMATION_COLLECTION, "wrong formation source")
    same(plan["parent"], report["parent"], "original learner parent differs")
    parent = report["parent"]
    require(parent["scores_sha256"] == entry["original_retention"]["sha256"] and original["plan_sha256"] == parent["plan_sha256"] and
            original["completion_sha256"] == parent["completion_sha256"] and original["skill"] == "perception" and
            original["scope"] == "authored_level1_skill_96train_320steps_120calls_v1", "original retention source differs")
    count(original["learner_seed"], seed)
    require(report["native_capture_custody_checked"] is True and report["automatic_pass"] is False and report["scientific_pass"] is None,
            "unverified/promoted input report")
    count(report["memory_scored_denominator"], denominator)
    count(report["memory_possible_denominator_per_variant"], 16)
    same(report["retention_denominators"], dict(held=48, canary=12), "retention denominator differs")
    count(report["counts"]["admitted_rows"], denominator)
    count(report["counts"]["possible_slots"], 16)
    count(report["counts"]["refused_slots"], 16 - denominator)
    require(len(report["refused"]) == 16 - denominator, "refusal inventory differs")
    count(report["calls"], 2 * (2 * denominator + 60))
    count(report["updates"], 16 * denominator)
    count(plan["calls_per_arm"], 2 * denominator + 60)
    count(plan["updates_per_arm"], 8 * denominator)
    require(set(report["cells"]) == set(ARMS), "missing/extra scored arm")
    first_ids, memory_sources = {}, {}
    for arm in ARMS:
        require(set(report["cells"][arm]) == set(PANELS), "missing/extra scored panel")
        for panel in PANELS:
            size = denominator if panel in MEMORY_PANELS else 48 if panel == "held" else 12
            rows = report["cells"][arm][panel]
            indexed = validate_rows(rows, panel, size, seed)
            if panel not in first_ids:
                first_ids[panel] = list(indexed)
            same(list(indexed), first_ids[panel], "arm row ordering differs")
            if panel in MEMORY_PANELS:
                same(list(indexed), first_ids["exact"], "exact/transfer source rows differ")
                for row in rows:
                    binding = dict(source=row["score"]["source"], target_sha256=row["score"]["target_sha256"])
                    if row["row_id"] not in memory_sources:
                        memory_sources[row["row_id"]] = binding
                    same(binding, memory_sources[row["row_id"]], "memory source/target substitution")
    for panel, size in (("held", 48), ("canary", 12)):
        old = original["cells"]["post"][panel]
        validate_rows(old["rows"], panel, size, seed, original=True)
        count(old["total"], size)
        for name in RETENTION_METRICS:
            count(old[name], sum(metric(row, panel, name) for row in old["rows"]))
    count(report["counts"]["distinct_raw_targets"], len({binding["target_sha256"] for binding in memory_sources.values()}))
    count(report["counts"]["episodes_with_admissions"], len({binding["source"]["task_id"] for binding in memory_sources.values()}))
    require(0 < count(report["counts"]["distinct_triples"]) <= report["counts"]["distinct_raw_targets"] <= denominator,
            "invalid admitted-record diversity counts")
    summary, pairs, retained = reproduce_summary(report["cells"], original, parent["scores_sha256"])
    same(report["summary"], summary, "reported totals/paired rows/original_retention disagree with cells")
    training = validate_fits(report, plan, denominator, check_fit)
    return dict(seed=seed, admitted_records=denominator, possible_record_slots=16, input_pins=copy.deepcopy(entry),
                plan_sha256=report["plan_sha256"], completion_sha256=report["completion_sha256"],
                totals=summary["totals"], paired_WRITE_LR0=pairs, original_retention=retained,
                error_breakdown={arm: {panel: error_breakdown(report["cells"][arm][panel], panel) for panel in PANELS} for arm in ARMS},
                reported_summary_reproduced=True, training=training, calls=report["calls"], updates=report["updates"],
                counts=copy.deepcopy(report["counts"]))


def analyze_manifest(manifest, *, runner_path=RUNNER_PATH):
    require(type(manifest) is dict and set(manifest) == {"schema", "seeds"} and manifest["schema"] == INPUT_SCHEMA, "input manifest schema")
    entries = manifest["seeds"]
    require(type(entries) is list and len(entries) == 3 and all(type(entry.get("seed")) is int for entry in entries) and
            sorted(entry["seed"] for entry in entries) == [0, 1, 2], "exactly one report for each seed0/1/2 required")
    check_fit = load_fit_validator(runner_path)
    results, seen_scores, seen_plans = [], set(), set()
    for entry in sorted(entries, key=lambda entry: entry["seed"]):
        require(set(entry) == {"seed", "scores", "plan", "collection", "original_retention"}, "input entry fields differ")
        report, plan, collection, original = (pinned(entry[name]) for name in ("scores", "plan", "collection", "original_retention"))
        require(entry["scores"]["sha256"] not in seen_scores and entry["plan"]["sha256"] not in seen_plans, "duplicate/substituted seed input")
        seen_scores.add(entry["scores"]["sha256"])
        seen_plans.add(entry["plan"]["sha256"])
        require(set(collection) == {"scores_sha256", "completion_sha256"} and collection["scores_sha256"] == entry["scores"]["sha256"] and
                collection["completion_sha256"] == report["completion_sha256"], "collected score/completion pin mismatch")
        results.append(reduce_seed(report, plan, original, entry, check_fit))
    return dict(schema=SCHEMA, seeds=results, independent_learners=3, automatic_pass=False, scientific_pass=None,
                accounting_only=dict(calls=sum(result["calls"] for result in results), updates=sum(result["updates"] for result in results)),
                interpretation="Local reduction of pinned native scored evidence, not raw native replay, recollection or tensor verification. Exact-cue acquisition/persistence and paraphrase transfer remain separate. Same-learner WRITE/LR0 pairs have 14/8/8 different admitted records; no pooled causal claim. Authored held/canary retention is not H1/H2 or recursive learning. Tensor checks validate finite recorded inventories/norms only.")


def markdown(report):
    lines = ["# Actual-record memory: local paired analysis", "", report["interpretation"], ""]
    for result in report["seeds"]:
        lines += [f"## Seed {result['seed']} — {result['admitted_records']} admitted / 16 possible", "",
                  "| Panel | Metric | WRITE | LR0 | WRITE-only | LR0-only |", "|---|---|---:|---:|---:|---:|"]
        for panel in PANELS:
            names = MEMORY_METRICS if panel in MEMORY_PANELS else ("content_correct", "strict")
            for name in names:
                first, second = (result["totals"][arm][panel] for arm in ARMS)
                counts = result["paired_WRITE_LR0"][panel][name]["counts"]
                lines.append(f"| {panel} | {name} | {first['numerators'][name]}/{first['denominator']} | {second['numerators'][name]}/{second['denominator']} | {counts['first_only']} | {counts['second_only']} |")
        lines += ["", "Retention changes versus the same original learner's post-fit receipt:", "",
                  "| Arm/panel | Raw changed | Content changed / regressed | Strict changed / regressed |", "|---|---:|---:|---:|"]
        for arm in ARMS:
            for panel in RETENTION_PANELS:
                cell = result["original_retention"][arm][panel]
                lines.append(f"| {arm}/{panel} | {cell['raw_changed']} | {cell['content_changed']} / {cell['content_regressed']} | {cell['strict_changed']} / {cell['strict_regressed']} |")
        lines += ["", f"Work: {result['calls']} generation calls; {result['updates']} optimizer updates across both arms (LR0 updates do not imply parameter change)."]
        for arm in ARMS:
            training = result["training"][arm]
            diagnostic = training["parameter_diagnostics"]
            costs = {name: sum(result["totals"][arm][panel]["generation_costs"][name] for panel in PANELS) for name in ("prompt_tokens", "output_tokens", "generation_seconds")}
            lines.append(f"- {arm}: {training['updates']} updates; train {training['train_seconds']:.3f}s / wall {training['wall_seconds']:.3f}s; supervised/context/padded tokens {training['supervised_tokens']}/{training['context_tokens']}/{training['padded_tokens']}; changed elements {diagnostic['changed_elements']}, delta L2 {diagnostic['l2']['delta']:.8g}; generation prompt/output tokens {costs['prompt_tokens']}/{costs['output_tokens']}, {costs['generation_seconds']:.3f}s.")
        lines += ["", "Per-metric paired row IDs and input hashes are preserved in analysis.json. Reported native summaries reproduced exactly.", ""]
        for arm in ARMS:
            exact = result["error_breakdown"][arm]["exact"]
            held = result["error_breakdown"][arm]["held"]
            lines.append(f"- {arm} format/content: exact-cue content failures {exact['content_failures']}, content-correct but non-strict {exact['content_correct_non_strict']}; held content failures {held['content_failures']}, content-correct but non-strict {held['content_correct_non_strict']}, length terminations {held['length_terminated']}.")
        lines.append("")
    lines += ["No automatic pass; no pooled success rate or causal promotion.", ""]
    return "\n".join(lines)


def run(manifest_path, manifest_sha256, out, *, runner_path=RUNNER_PATH):
    manifest = pinned(dict(path=str(Path(manifest_path).absolute()), sha256=manifest_sha256))
    output = Path(out).absolute()
    require(not output.exists() and not any(path.is_symlink() for path in (output, *output.parents)) and output.parent.is_dir(), "fresh output directory required")
    protected = [Path(manifest_path).resolve(), Path(runner_path).resolve(), Path(__file__).resolve()]
    protected.extend(Path(entry[name]["path"]).resolve() for entry in manifest["seeds"] for name in ("scores", "plan", "collection", "original_retention"))
    require(all(output != path and output not in path.parents and path not in output.parents for path in protected), "output overlaps inputs")
    report = analyze_manifest(manifest, runner_path=runner_path)
    report["manifest_sha256"] = manifest_sha256
    report["analyzer_sha256"] = digest(__file__)
    text = markdown(report)
    output.mkdir()
    with (output / "analysis.json").open("x") as stream:
        stream.write(canonical(report) + "\n")
    with (output / "analysis.md").open("x") as stream:
        stream.write(text)
    return dict(output=str(output), json_sha256=digest(output / "analysis.json"), markdown_sha256=digest(output / "analysis.md"),
                status="REDUCED_PINNED_SCORES_NOT_NEW_NATIVE_EVIDENCE")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--runner", default=RUNNER_PATH)
    args = parser.parse_args()
    print(canonical(run(args.manifest, args.manifest_sha256, args.out, runner_path=args.runner)))


if __name__ == "__main__":
    main()
