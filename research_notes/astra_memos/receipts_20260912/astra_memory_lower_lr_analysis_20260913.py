"""CPU-only reduction of frozen lower-LR collections; no native verification or scoring."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys


SELF = Path(__file__).resolve()
SCHEMA = "astra_memory_lower_lr_analysis_20260913_v1"
RUNNER_PIN = "80467204aa7ccb4a1cbf4f8d85c7be4e7347263f98f4f7b8fef5739980fcf413"
MEMORY_PIN = "7028fa9a9b277adc6edfec2398d1885d6c55ec33eb67a1bd51ac36b37e02215e"
PROTOCOL_PIN = "122965224f6a72d1fb852a40dd24c02b78c733751337f37513712f0f3b45bbce"
PANELS = ("exact", "paraphrase", "held", "canary")
MEMORY_METRICS = ("production_eligible", "content_correct", "strict_canonical", "exact_target_bytes")
RETENTION_METRICS = ("passed", "content_correct", "strict")
FIELDS = ("try", "observed", "predicted", "relation")
GENERATION_COSTS = ("prompt_tokens", "output_tokens", "generation_seconds")
MAX_FILE_BYTES = 64 * 1024 * 1024


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    checksum = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            checksum.update(block)
    return checksum.hexdigest()


def checksum(value):
    require(type(value) is str and len(value) == 64 and all(char in "0123456789abcdef" for char in value), "SHA256 required")
    return value


def read(path):
    require(Path(path).stat().st_size <= MAX_FILE_BYTES, "bounded input file size exceeded")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "duplicate JSON key")
            result[key] = value
        return result
    return json.loads(Path(path).read_bytes(), object_pairs_hook=unique,
                      parse_constant=lambda value: require(False, "nonfinite JSON"))


def pinned(binding, expected=None):
    require(set(binding) == {"path", "sha256"} and Path(binding["path"]).is_absolute(), "explicit absolute file binding required")
    checksum(binding["sha256"])
    require((expected is None or binding["sha256"] == expected) and digest(binding["path"]) == binding["sha256"], "file pin differs")


def load_helpers():
    sys.dont_write_bytecode = True
    modules = []
    for name, path, pin in (("candidate", "/tmp/astra_memory_lower_lr_run_20260913.py", RUNNER_PIN),
                            ("memory", "/tmp/astra_real_record_memory_run_20260913.py", MEMORY_PIN)):
        pinned(dict(path=path, sha256=pin), pin)
        spec = importlib.util.spec_from_file_location("lower_lr_analysis_" + name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        modules.append(module)
    return tuple(modules)


def number(value, integer=False):
    require((type(value) is int if integer else type(value) in (int, float)) and math.isfinite(value) and value >= 0,
            "finite nonnegative typed cost/count required")
    return value


def metrics(panel):
    return MEMORY_METRICS if panel in ("exact", "paraphrase") else RETENTION_METRICS


def score_body(row, panel):
    return row["score"]["score"] if panel in ("exact", "paraphrase") else row["score"]


def outcomes(rows, panel, metric):
    return {row["row_id"]: row["score"]["exact_target_bytes"] if metric == "exact_target_bytes"
            else score_body(row, panel)[metric] for row in rows}


def validate_panel(rows, panel, count):
    require(type(rows) is list and len(rows) == count, "fixed panel denominator differs")
    identities = [row["row_id"] for row in rows]
    require(all(type(value) is str and value for value in identities) and len(set(identities)) == count, "duplicate/invalid row ID")
    for row in rows:
        require(type(row["raw"]) is str and type(row["finish_reason"]) is str, "raw/finish type differs")
        checksum(row["response_sha256"])
        body = score_body(row, panel)
        require(body["raw"] == row["raw"] and body["finish_reason"] == row["finish_reason"] and type(body["format"]) is str,
                "stored score raw/finish join differs")
        for metric in metrics(panel):
            value = outcomes([row], panel, metric)[row["row_id"]]
            require(type(value) is bool, "typed boolean metric required")
            require(row["finish_reason"] == "stop" or not value, "non-stop completion cannot pass")
        if panel in ("exact", "paraphrase"):
            wrapper = row["score"]
            require(wrapper["row_id"] == row["row_id"] and wrapper["variant"] == panel, "memory row/variant join differs")
            checksum(wrapper["target_sha256"])
            require(set(body["field_correct"]) == set(FIELDS) and all(type(value) is bool for value in body["field_correct"].values()),
                    "typed field agreement required")
            require(row["finish_reason"] == "stop" or not any(body["field_correct"].values()), "non-stop field cannot pass")
        require(set(row["cost"]) == set(GENERATION_COSTS), "generation cost fields differ")
        for key in GENERATION_COSTS:
            number(row["cost"][key], integer=key != "generation_seconds")


def panel_summary(rows, panel):
    result = dict(denominator=len(rows), numerators={metric: sum(outcomes(rows, panel, metric).values()) for metric in metrics(panel)},
                  format_counts=dict(Counter(score_body(row, panel)["format"] for row in rows)),
                  generation_costs={key: sum(row["cost"][key] for row in rows) for key in GENERATION_COSTS})
    if panel in ("exact", "paraphrase"):
        result.update(possible_denominator=16, field_correct={field: sum(score_body(row, panel)["field_correct"][field] for row in rows) for field in FIELDS})
    return result


def same_sources(first, second, panel):
    first = {row["row_id"]: row for row in first}
    second = {row["row_id"]: row for row in second}
    require(set(first) == set(second), "paired source row IDs differ")
    for row_id, row in first.items():
        other = second[row_id]
        require(row["cost"]["prompt_tokens"] == other["cost"]["prompt_tokens"], "stored prompt token counts differ")
        if panel in ("exact", "paraphrase"):
            require(row["score"]["source"] == other["score"]["source"] and
                    row["score"]["target_sha256"] == other["score"]["target_sha256"], "memory source/target join differs")


def retention_items(candidate, high, lr0, panel):
    low_flags = outcomes(candidate, panel, "passed")
    high_flags = outcomes(high, panel, "passed")
    zero_flags = outcomes(lr0, panel, "passed")
    rows = [dict(row_id=row_id, lr0_correct=zero_flags[row_id], high_correct=high_flags[row_id], lower_lr_correct=low_flags[row_id],
                 restored_from_high_regression=zero_flags[row_id] and not high_flags[row_id] and low_flags[row_id],
                 still_missing_lr0_correct=zero_flags[row_id] and not low_flags[row_id],
                 newly_lost_vs_high=zero_flags[row_id] and high_flags[row_id] and not low_flags[row_id]) for row_id in sorted(zero_flags)]
    groups = dict(lr0_correct=[row["row_id"] for row in rows if row["lr0_correct"]],
                  lr0_correct_retained=[row["row_id"] for row in rows if row["lr0_correct"] and row["lower_lr_correct"]])
    for key in ("restored_from_high_regression", "still_missing_lr0_correct", "newly_lost_vs_high"):
        groups[key] = [row["row_id"] for row in rows if row[key]]
    return dict(items=rows, row_ids=groups, counts={key: len(value) for key, value in groups.items()})


def endpoint_cost(cells, manifest, training):
    require(type(manifest["steps"]) is int and manifest["steps"] == training["updates"], "fit update count differs")
    cost = dict(calls=sum(len(rows) for rows in cells.values()), updates=manifest["steps"],
                fit_train_seconds=number(manifest["train_seconds"]), fit_wall_seconds=number(manifest["wall_seconds"]))
    cost.update({key: sum(row["cost"][key] for rows in cells.values() for row in rows) for key in GENERATION_COSTS})
    cost["training_tokens"] = {key: number(training[key], integer=True) for key in
                               ("actual_context_tokens", "actual_supervised_tokens", "actual_padded_tokens", "train_tokens_seen")}
    return cost


def reduce_seed(candidate, historical):
    """Pure stored-score arithmetic. In-memory callers must authenticate inputs separately."""
    runner, memory = load_helpers()
    seed = candidate["seed"]
    require(type(seed) is int and seed in (0, 1, 2) and type(historical["seed"]) is int and historical["seed"] == seed, "seed mismatch")
    count = (14, 8, 8)[seed]
    require(candidate["scope"] == runner.SCOPE and historical["scope"] == memory.SCOPE, "frozen score scope differs")
    require(candidate["parent"] == historical["parent"], "original parent differs")
    require(candidate["native_capture_custody_checked"] is True and historical["native_capture_custody_checked"] is True,
            "successful collector custody declaration required")
    require(candidate["automatic_pass"] is False and candidate["scientific_pass"] is None, "no promotion in source report")
    require(set(candidate["cells"]) == {"WRITE"} and set(historical["cells"]) == {"WRITE", "LR0"} and
            set(candidate["historical_cells"]) == {"HIGH", "LR0"}, "endpoint inventory differs")
    cells = dict(LOWER_LR=candidate["cells"]["WRITE"], HIGH=historical["cells"]["WRITE"], LR0=historical["cells"]["LR0"])
    for endpoint in ("HIGH", "LR0"):
        require(candidate["historical_cells"][endpoint] == cells[endpoint], "imported historical cells changed")
        require(candidate["reused_endpoints"][endpoint] == dict(original_arm="WRITE" if endpoint == "HIGH" else "LR0",
                noncontemporaneous=True, incremental_calls=0, incremental_updates=0), "historical reuse/cost label differs")
    for report in (candidate, historical):
        require(type(report["memory_possible_denominator_per_variant"]) is int and report["memory_possible_denominator_per_variant"] == 16 and
                type(report["memory_scored_denominator"]) is int and report["memory_scored_denominator"] == count and
                report["retention_denominators"] == dict(held=48, canary=12), "report denominator differs")
    training = candidate["training_costs"]
    require(training == historical["training_costs"] and type(training["fit_seed"]) is int and training["fit_seed"] == seed and
            training["rows"] == count and training["updates"] == training["presentations"] == 8 * count, "original training accounting differs")
    low_fit = candidate["fits"]["WRITE"]
    high_fit, zero_fit = (historical["fits"][arm] for arm in ("WRITE", "LR0"))
    require(high_fit["config"]["lr"] == 1e-4 and zero_fit["config"]["lr"] == 0.0 and
            low_fit["config"] == dict(high_fit["config"], lr=3e-5) and low_fit["config"]["seed"] == seed, "LR-only fit config differs")
    for old_fit in (high_fit, zero_fit):
        require(all(low_fit["warm_start"][key] == old_fit["warm_start"][key] for key in ("source_state", "initialized_state")),
                "warm source/init inventories differ")
    totals = {}
    for endpoint, panels in cells.items():
        require(set(panels) == set(PANELS), "panel inventory differs")
        for panel in PANELS:
            validate_panel(panels[panel], panel, count if panel in ("exact", "paraphrase") else 48 if panel == "held" else 12)
            same_sources(panels[panel], cells["LR0"][panel], panel)
        exact = {row["row_id"]: row["score"] for row in panels["exact"]}
        paraphrase = {row["row_id"]: row["score"] for row in panels["paraphrase"]}
        require(set(exact) == set(paraphrase) and all(exact[row_id]["source"] == paraphrase[row_id]["source"] and
                exact[row_id]["target_sha256"] == paraphrase[row_id]["target_sha256"] for row_id in exact), "exact/paraphrase source join differs")
        totals[endpoint] = {panel: panel_summary(panels[panel], panel) for panel in PANELS}
    pairwise = {endpoint: {panel: {metric: memory.paired_counts(outcomes(cells["LOWER_LR"][panel], panel, metric),
                  outcomes(cells[endpoint][panel], panel, metric)) for metric in metrics(panel)} for panel in PANELS} for endpoint in ("LR0", "HIGH")}
    for endpoint in ("LR0", "HIGH"):
        stored = candidate["comparisons"]["candidate_vs_historical_" + endpoint]
        require(stored["totals"] == dict(WRITE=totals["LOWER_LR"], LR0=totals[endpoint]) and
                stored["paired_WRITE_LR0"] == pairwise[endpoint], "stored aggregate differs from row reduction")
    screen = runner.repair_screen(seed, dict(totals=dict(WRITE=totals["LOWER_LR"]), paired_WRITE_LR0=pairwise["LR0"]))
    require(candidate["strict_exploratory_repair_screen"] == screen, "stored strict screen differs")
    expected_cost = dict(calls=2 * count + 60, updates=8 * count, historical_calls=0, historical_updates=0)
    require(candidate["incremental_cost"] == expected_cost and historical["calls"] == 2 * expected_cost["calls"] and
            historical["updates"] == 2 * expected_cost["updates"], "new/historical expenditure differs")
    new_cost = endpoint_cost(cells["LOWER_LR"], low_fit, training)
    historical_costs = {endpoint: dict(observed_cost=endpoint_cost(cells[endpoint], manifest, training),
                                      incremental_cost=dict(calls=0, updates=0), reused=True, noncontemporaneous=True)
                        for endpoint, manifest in (("HIGH", high_fit), ("LR0", zero_fit))}
    return dict(seed=seed, panels=totals, paired_lower_lr_vs=pairwise,
        retention={panel: retention_items(cells["LOWER_LR"][panel], cells["HIGH"][panel], cells["LR0"][panel], panel) for panel in ("held", "canary")},
        strict_exploratory_repair_screen=screen, costs=dict(new=new_cost, historical=historical_costs),
        fit_diagnostics={endpoint: dict(final_loss=manifest["final_loss"], mean_loss_per_epoch=manifest["mean_loss_per_epoch"],
                          parameter_diagnostics=(candidate if endpoint == "LOWER_LR" else historical)["parameter_diagnostics"]["LR0" if endpoint == "LR0" else "WRITE"])
                         for endpoint, manifest in (("LOWER_LR", low_fit), ("HIGH", high_fit), ("LR0", zero_fit))},
        native_identity_verified_by_reducer=False, raw_reparsed_or_rescored=False, automatic_pass=False, scientific_pass=None)


def load_collected(binding, plan_sha256, completion_sha256):
    pinned(binding)
    checksum(plan_sha256)
    checksum(completion_sha256)
    path = Path(binding["path"])
    require(path.name == "collection.json" and not (path.parent / "collection_failure.json").exists(), "successful collection required")
    collection = read(path)
    require(set(collection) == {"scores_sha256", "completion_sha256"} and collection["completion_sha256"] == completion_sha256, "collection completion differs")
    scores_binding = dict(path=str(path.parent / "scores.json"), sha256=checksum(collection["scores_sha256"]))
    pinned(scores_binding)
    scores = read(scores_binding["path"])
    require(scores["plan_sha256"] == plan_sha256 and scores["completion_sha256"] == completion_sha256, "collected plan/completion join differs")
    return scores, dict(collection=binding, scores=scores_binding, plan_sha256=plan_sha256, completion_sha256=completion_sha256)


def reduce_manifest(manifest_path, manifest_sha256):
    runner, _ = load_helpers()
    manifest_binding = dict(path=str(Path(manifest_path).absolute()), sha256=manifest_sha256)
    pinned(manifest_binding)
    manifest = read(manifest_path)
    require(set(manifest) == {"protocol", "runs"}, "closed manifest fields differ")
    pinned(manifest["protocol"], PROTOCOL_PIN)
    require(type(manifest["runs"]) is list and 1 <= len(manifest["runs"]) <= 3, "one to three completed seeds required")
    results, inputs, seen = [], [], set()
    for entry in manifest["runs"]:
        require(set(entry) == {"seed", "candidate_collection", "candidate_plan_sha256", "candidate_completion_sha256", "historical_collection"}, "closed run binding differs")
        seed = entry["seed"]
        require(type(seed) is int and seed in (0, 1, 2) and seed not in seen, "invalid/duplicate seed")
        seen.add(seed)
        old_plan, old_complete, old_collection, old_scores = runner.HISTORY_PINS[seed]
        require(entry["historical_collection"]["sha256"] == old_collection, "historical collection pin differs")
        historical, historical_binding = load_collected(entry["historical_collection"], old_plan, old_complete)
        require(historical_binding["scores"]["sha256"] == old_scores, "historical scores pin differs")
        candidate, candidate_binding = load_collected(entry["candidate_collection"], entry["candidate_plan_sha256"], entry["candidate_completion_sha256"])
        history = candidate["historical_binding"]
        require(candidate["seed"] == seed and (history["plan_sha256"], history["completion_sha256"], history["collection"]["sha256"],
                history["scores_sha256"]) == runner.HISTORY_PINS[seed], "candidate imported history differs")
        results.append(reduce_seed(candidate, historical))
        inputs.append(dict(seed=seed, candidate=candidate_binding, historical=historical_binding))
    results.sort(key=lambda value: value["seed"])
    inputs.sort(key=lambda value: value["seed"])
    new_totals = {key: sum(result["costs"]["new"][key] for result in results) for key in
                  ("calls", "updates", *GENERATION_COSTS, "fit_train_seconds", "fit_wall_seconds")}
    return dict(schema=SCHEMA, reducer_sha256=digest(SELF), protocol=manifest["protocol"], manifest=manifest_binding,
        frozen_sources=dict(candidate_runner=RUNNER_PIN, memory_runner=MEMORY_PIN), inputs=inputs, seeds=results,
        roster=dict(complete=seen == {0, 1, 2}, present=sorted(seen), missing=sorted({0, 1, 2} - seen),
                    all_three_strict_screens_met=all(result["strict_exploratory_repair_screen"]["met"] for result in results) if seen == {0, 1, 2} else None),
        total_new_cost=new_totals, total_incremental_historical_cost=dict(calls=0, updates=0),
        automatic_pass=False, scientific_pass=None,
        limitations=["Stored score arithmetic, not independent semantic scoring, prompt-token verification or native custody verification.",
                     "Historical HIGH and LR0 are reused and noncontemporaneous, not new controls or replications.",
                     "Strict screen uses production_eligible exact recall8/7/5 and zero lost LR0-correct held/canary items; gains cannot offset losses.",
                     "Partial tradeoffs are not full repair. This inspected held panel is exploratory, not fresh confirmation or H1/H2 promotion.",
                     "Costs sum observed call/fit durations, not concurrent makespan or controller/collection wall time."])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--out", required=True)
    options = parser.parse_args(argv)
    result = reduce_manifest(options.manifest, options.manifest_sha256)
    out = Path(options.out)
    require(not out.is_symlink(), "output symlink rejected")
    with out.open("x") as stream:
        json.dump(result, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps(dict(status="REDUCED_STORED_SCORES", out=str(out.absolute()), sha256=digest(out), roster=result["roster"]), sort_keys=True))


if __name__ == "__main__":
    main()
