"""Independent local reducer of pinned, completed fixed-coaching DEV receipts."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
from types import ModuleType

CORE_PATH = "/tmp/astra_parented_record_core_20260913.py"
CORE_PIN = "68ef29fcc162dbbf5fe1becf4c09b86ed5bc1f8a79e373276dd8ba3cda88e688"
RUNNER_PIN = "54cad8a6eeb5ae8af08213efe60f4c8047879991ca77f7a30d8be548659699f8"
PROTOCOL_PIN = "bae29cfc48d9ae0922531d306bef1434bcc7296f2ae71a4ad6493da2a5dfb964"
SCOPE = "astra_parented_record_dev_20260913_v1"
ARMS = ("P", "N")
METRICS = ("production_eligible", "content_correct", "strict_canonical")
CAPTURE_STAGES = ("P_formation", "N_formation", "ORIGINAL_held", "P_held", "N_held")
COST_STAGES = (*CAPTURE_STAGES, "P_retention", "N_retention")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def equal(left, right, message):
    require(canonical(left) == canonical(right), message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def integer(value, maximum=None):
    require(type(value) is int and value >= 0 and (maximum is None or value <= maximum), "invalid count")
    return value


def finite(value):
    require(type(value) in (int, float) and math.isfinite(value) and value >= 0, "invalid finite nonnegative cost")
    return value


def unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def reject(value):
    raise ValueError("nonfinite JSON constant: " + value)


def read(path, pin=None):
    path = Path(path)
    require(path.is_file() and not path.is_symlink() and path.stat().st_size < 64_000_000, "bounded regular JSON file required")
    raw = path.read_bytes()
    require(pin is None or sha(raw) == pin, "file pin mismatch: " + str(path))
    value = json.loads(raw, object_pairs_hook=unique, parse_constant=reject)
    canonical(value)
    return value


def load_core(source_root, protocol_path=None):
    raw = Path(CORE_PATH).read_bytes()
    require(sha(raw) == CORE_PIN, "frozen analysis core pin differs")
    module = ModuleType("parented_analysis_frozen_core")
    exec(compile(raw, CORE_PATH, "exec"), module.__dict__)
    return module, module.load_dependencies(source_root, protocol_path=protocol_path)


def stage_dir(stage):
    return f"arms/{stage[0]}/run/WRITE_fit" if stage.endswith("_fit") else "run/" + stage


def load_bundle(entry):
    root = Path(entry["root"]).resolve()
    def local(relative, pin=None):
        require(not PurePosixPath(relative).is_absolute() and ".." not in PurePosixPath(relative).parts, "unsafe receipt path")
        path = root / relative
        require(path.resolve().is_relative_to(root), "receipt escapes local root")
        return read(path, pin)
    scores = read(entry["scores"]["path"], entry["scores"]["sha256"])
    plan = local("plan.json", entry["plan_sha256"])
    complete = local("capture_complete.json", entry["completion_sha256"])
    collection = read(entry["collection"]["path"], entry["collection"]["sha256"])
    equal(collection["scores_sha256"], entry["scores"]["sha256"], "collection score pin differs")
    equal(collection["completion_sha256"], entry["completion_sha256"], "collection completion differs")
    equal(collection["automatic_pass"], False, "unexpected promotion")
    require(finite(collection["elapsed_whole_seconds"]) <= 7200, "whole-work cap exceeded")
    equal(scores["plan_sha256"], entry["plan_sha256"], "report plan differs")
    equal(scores["completion_sha256"], entry["completion_sha256"], "report completion differs")
    equal(plan["parent"]["scores_sha256"], entry["original_scores"]["sha256"], "historical baseline pin differs")
    history = read(entry["original_scores"]["path"], entry["original_scores"]["sha256"])
    for failure in ("controller_failure.json", "collection_failure.json"):
        require(not (root / failure).exists(), "failed root")
    stage_json = {}
    for stage, inventory in complete["inventory"].items():
        base = f"arms/{stage[0]}" if stage.endswith("_material") else stage_dir(stage)
        stage_json[stage] = {}
        for relative, pin in inventory.items():
            if relative.endswith(".json"):
                stage_json[stage][relative] = local(base + "/" + relative, pin)
        if not stage.endswith("_material"):
            equal(local(stage + ".stage.json"), inventory, "closed stage inventory differs")
    captures = {stage: stage_json[stage]["capture.json"] for stage in CAPTURE_STAGES}
    return dict(seed=entry["seed"], report=scores, plan=plan, complete=complete, history=history,
                stages=stage_json, captures=captures, collection=collection,
                pins={key: entry[key] for key in ("scores", "plan_sha256", "completion_sha256", "original_scores", "collection")})


def rows_for(capture, stage=None):
    return [dict(slot=f'{episode["episode_id"]}#t{turn["tick"]}', episode_id=episode["episode_id"], tick=turn["tick"],
                 stage=episode["stage"], execution=turn["execution"], score=turn["score"], errors=turn["errors"],
                 wake_raw=turn["wake"]["response"].get("raw"), wake_finish=turn["wake"]["response"].get("finish_reason"),
                 record_raw=turn["record"]["response"].get("raw") if turn["record"] else None,
                 record_called=turn["record"] is not None,
                 wake_prompt=turn["wake"]["request"]["input_messages"])
            for episode in capture["episodes"] if stage is None or episode["stage"] == stage for turn in episode["turns"]]


def counts(rows):
    result = dict(possible=len(rows), executions=sum(row["execution"] is not None for row in rows),
                  record_calls=sum(row["record_called"] for row in rows))
    for metric in METRICS:
        result[metric] = sum(row["score"] is not None and row["score"][metric] is True for row in rows)
        result[metric + "_over_possible"] = result[metric] / len(rows) if rows else None
        result[metric + "_over_records"] = result[metric] / result["record_calls"] if result["record_calls"] else None
    result["fields"] = {field: sum(row["score"] is not None and row["score"]["field_correct"][field] is True for row in rows)
                        for field in ("try", "observed", "predicted", "relation")}
    result["record_formats"] = dict(Counter(row["score"]["format"] for row in rows if row["score"]))
    result["invalid_wake_reasons"] = dict(Counter(error for row in rows if row["execution"] is None for error in row["errors"]))
    result["record_errors"] = dict(Counter(error for row in rows if row["score"] for error in row["score"]["production_errors"]))
    return result


def pair_rows(first, second):
    equal([row["slot"] for row in first], [row["slot"] for row in second], "paired schedule mismatch")
    result = {}
    for metric in METRICS:
        groups = {key: [] for key in ("first_only", "second_only", "both", "neither")}
        for left, right in zip(first, second):
            passed_left = left["score"] is not None and left["score"][metric] is True
            passed_right = right["score"] is not None and right["score"][metric] is True
            label = "both" if passed_left and passed_right else "first_only" if passed_left else "second_only" if passed_right else "neither"
            groups[label].append(left["slot"])
        result[metric] = groups
    result["same_executed_facts"] = [left["slot"] for left, right in zip(first, second)
        if left["execution"] is not None and right["execution"] is not None and
        all(left["execution"][key] == right["execution"][key] for key in ("values", "observed", "predicted"))]
    result["same_wake_prompt"] = [left["slot"] for left, right in zip(first, second) if left["wake_prompt"] == right["wake_prompt"]]
    return result


def validate_native(stage, documents, capture, cost):
    requests = sorted(name for name in documents if name.endswith(".request.json"))
    responses = sorted(name for name in documents if name.endswith(".response.json"))
    equal([name.replace(".request", "") for name in requests], [name.replace(".response", "") for name in responses], "native call pairs differ")
    events = [event for event in capture["events"] if event["kind"] == "call"] if capture else []
    equal(len(requests), len(events) if capture else 60, "native call denominator differs")
    prompt_tokens, output_tokens, seconds = 0, 0, 0.0
    for index, name in enumerate(requests):
        request = documents[name]
        response = documents[name.replace(".request", ".response")]
        if capture:
            equal(request["core_request"], events[index]["request"], "native/core request differs")
            equal(request["messages"], events[index]["request"]["input_messages"], "native prompt/source differs")
            equal(events[index]["response"]["native_response"], response, "native/core response differs")
            equal(events[index]["response"]["raw"], response["text"], "raw byte join differs")
        equal(request["lora_request"], documents["identity.json"]["route"], "request route differs")
        equal(response["lora_request"], request["lora_request"], "response route differs")
        equal(response["actual_prompt_token_ids"], request["native"]["prompt_token_ids"], "token-prefix receipt differs")
        for key, value in request["native"].items():
            equal(response[key], value, "native rendering receipt differs")
        require(type(response["text"]) is str and response["text"] == response["decoded_output"], "decoded bytes differ")
        for key in ("actual_prompt_token_ids", "output_token_ids"):
            require(type(response[key]) is list and all(type(token) is int and token >= 0 for token in response[key]), "invalid token IDs")
        cap = integer(request["params"]["max_tokens"])
        require(0 < len(response["output_token_ids"]) <= cap and response["finish_reason"] in ("stop", "length"), "output cap/completion differs")
        require(response["finish_reason"] != "length" or len(response["output_token_ids"]) == cap, "length count differs")
        elapsed = finite(response["ended"]) - finite(response["started"])
        require(elapsed >= 0, "negative span")
        prompt_tokens += len(response["actual_prompt_token_ids"])
        output_tokens += len(response["output_token_ids"])
        seconds += elapsed
    equal(cost["calls"], len(requests), "cost calls differ")
    equal(cost["updates"], 0, "generation stage has updates")
    equal(cost["prompt_tokens"], prompt_tokens, "prompt token cost differs")
    equal(cost["output_tokens"], output_tokens, "output token cost differs")
    require(abs(finite(cost["generation_seconds"]) - seconds) < 1e-7, "generation time differs")
    equal(documents["cost.json"], cost, "stage cost/report mismatch")
    literal = cost["contact_tokens_per_literal"]
    equal(sorted(literal), ["N", "P"] if stage.endswith("_formation") else [], "contact accounting fields differ")
    for value in literal.values():
        integer(value)


def retention(report, history, documents, inventory):
    result = {}
    equal(report["noncontemporaneous_original"], True, "historical control mislabeled")
    equal(report["exploratory"], True, "old retention is not confirmatory")
    for panel, denominator in (("held", 48), ("canary", 12)):
        rows = report["cells"][panel]
        old_rows = history["cells"]["post"][panel]["rows"]
        require(len(rows) == len(old_rows) == denominator, "retention denominator differs")
        old = {row["row_id"]: row for row in old_rows}
        require(len(old) == denominator and len({row["row_id"] for row in rows}) == denominator, "duplicate retention row")
        equal(sorted(old), sorted(row["row_id"] for row in rows), "retention identities differ")
        output = dict(denominator=denominator, raw_changed=[], metrics={})
        for index, row in enumerate(rows):
            name = f"{panel}_{index:02d}"
            response = documents[name + ".response.json"]
            equal(row["response_sha256"], inventory[name + ".response.json"], "retention response pin differs")
            equal(row["row_id"], documents[name + ".request.json"]["row_id"], "retention request row differs")
            equal(row["raw"], response["text"], "retention raw response differs")
            equal(row["finish_reason"], response["finish_reason"], "retention finish differs")
            require(not row["score"]["strict"] or row["score"]["content_correct"], "strict without content correctness")
            require(row["finish_reason"] == "stop" or not row["score"]["content_correct"], "unfinished retention scored correct")
            if row["raw"] != old[row["row_id"]]["raw"]:
                output["raw_changed"].append(row["row_id"])
        for metric in ("content_correct", "strict"):
            require(all(type(row["score"][metric]) is bool for row in [*rows, *old_rows]), "retention score must be Boolean")
            gains = [row["row_id"] for row in rows if row["score"][metric] and not old[row["row_id"]]["score"][metric]]
            losses = [row["row_id"] for row in rows if not row["score"][metric] and old[row["row_id"]]["score"][metric]]
            equal(report["versus_original"][panel][metric], dict(gains=gains, losses=losses), "reported retention contrast differs")
            output["metrics"][metric] = dict(current=sum(row["score"][metric] for row in rows),
                original=sum(row["score"][metric] for row in old_rows), gains=gains, losses=losses)
        output["failure_rows"] = [row for row in rows if not row["score"]["content_correct"]]
        output["format_counts"] = dict(Counter(row["score"].get("format", "not_reported") for row in rows))
        result[panel] = output
    return result


def reduce_bundle(bundle, core, dependencies):
    report, plan, complete = (bundle[key] for key in ("report", "plan", "complete"))
    seed = integer(bundle["seed"], 2)
    equal(report["scope"], SCOPE, "report scope differs")
    for item in (report, plan):
        equal(item["seed"], seed, "seed differs")
    equal(plan["self_sha256"], RUNNER_PIN, "runner version differs")
    equal(plan["specification"]["core"]["sha256"], CORE_PIN, "core pin differs")
    equal(plan["specification"]["protocol"]["sha256"], PROTOCOL_PIN, "protocol pin differs")
    equal(plan["manifest"]["contract"], core.contract(dependencies), "plan contract differs")
    equal(plan["manifest"]["disjointness"]["schedule_sha256"], core.SCHEDULE_SHA256, "source schedule pin differs")
    equal(plan["manifest"]["disjointness"]["disjoint"], True, "source overlap receipt")
    equal(plan["manifest"]["disjointness"]["distinct_ids"], 36, "source namespace count differs")
    equal(complete["plan_sha256"], report["plan_sha256"], "completion plan differs")
    equal(report["historical_original"], plan["historical_retention"], "original baseline binding differs")
    require(report["historical_original"]["noncontemporaneous"] is True, "historical control mislabeled")
    for key in ("scientific_pass", "outcome_gate"):
        require(report[key] is None, "unexpected outcome promotion")
    equal(report["automatic_pass"], False, "unexpected automatic pass")
    equal(complete["automatic_pass"], False, "unexpected completion pass")
    require(finite(complete["elapsed_seconds"]) <= 7200, "native duration cap differs")
    for key, expected in dict(lr=3e-5, epochs=8, batch_size=1, seed=seed, max_steps=0, rank=8, alpha=16, dropout=.05).items():
        equal(plan["config"][key], expected, "write policy differs: " + key)
    for field in ("material", "fits", "retention", "source_novelty", "held_vs_initial"):
        equal(sorted(report[field]), ["N", "P"], "missing/extra arm: " + field)
    equal(sorted(bundle["captures"]), sorted(CAPTURE_STAGES), "missing capture stage")
    equal(sorted(report["costs"]), sorted(COST_STAGES), "missing cost stage")
    stages = bundle["stages"]
    expected_stages = set(COST_STAGES) | {arm + "_material" for arm in ARMS}
    expected_stages |= {arm + "_fit" for arm in ARMS if report["material"][arm]["rows"]}
    equal(sorted(stages), sorted(expected_stages), "missing/unexpected stage; NO_WRITE is not a fit")
    equal(sorted(complete["inventory"]), sorted(expected_stages), "completion stage roster differs")
    summaries, ledgers = {}, {}
    identities = []
    for stage in expected_stages - {"P_material", "N_material"}:
        documents = stages[stage]
        require(not any(name in documents for name in ("failure.json", "cleanup_failure.json")), "failed stage")
        launch = documents["launch.json"]
        equal(launch["stage"], stage, "launch stage differs")
        equal(launch["plan_sha256"], report["plan_sha256"], "launch plan differs")
        owner = launch["identity"]
        identities.append((integer(owner["pid"]), integer(owner["start_ticks"])))
        equal(documents["started.json"], dict(identity=owner, stage=stage, plan_sha256=report["plan_sha256"]), "started receipt differs")
        equal(documents["worker_done.json"], dict(stage=stage, plan_sha256=report["plan_sha256"]), "worker incomplete")
        equal(documents["exit.json"], dict(identity=owner, returncode=0), "worker failed")
        equal(documents["released.json"], dict(identity=owner, stage=stage, group_absent=True, gpu_vacant=True), "release receipt differs")
    require(len(set(identities)) == len(identities), "cold worker identity reused")
    for stage in CAPTURE_STAGES:
        capture = bundle["captures"][stage]
        arm, phase = stage.split("_")
        state = f"perception_seed{seed}_{'INITIAL' if arm == 'ORIGINAL' else arm}"
        equal([capture["state"], capture["phase"], capture["split"]], [state, phase, "dev"], "wrong captured state/phase/split")
        core.audit_capture(capture, dependencies=dependencies)
        equal(capture["binding"], stages[stage]["identity.json"], "captured route identity differs")
        identity = capture["binding"]
        equal(identity["parent"], plan["parent"], "original parent differs")
        equal(identity["model_files"], plan["model_files"], "model binding differs")
        equal(identity["core"], plan["specification"]["core"], "capture core binding differs")
        equal(identity["stage"], stage, "stage identity differs")
        equal(identity["state"], state, "state identity differs")
        if phase == "held":
            equal(capture["contacts"], [], "held has contact context")
            require(all(event["request"]["contact_sha256"] is None and event["request"]["kind"] != "restate"
                        for event in capture["events"] if event["kind"] == "call"), "held has guidance/restatement requests")
        ledger = rows_for(capture, "apply" if phase == "formation" else "held")
        equal(len(ledger), 16, "record opportunity denominator differs")
        ledgers[stage] = ledger
        summaries[stage] = counts(ledger)
        summaries[stage]["turns"] = {str(tick): counts([row for row in ledger if row["tick"] == tick]) for tick in (1, 2)}
        validate_native(stage, stages[stage], capture, report["costs"][stage])
    for phase, subset in (("formation", [bundle["captures"][arm + "_formation"] for arm in ARMS]),
                          ("held", [bundle["captures"][arm + "_held"] for arm in ("ORIGINAL", *ARMS)])):
        equal(core.compare_states(subset, dependencies=dependencies), report[phase], "collector summary differs from replay")
    arms = {}
    for arm in ARMS:
        formation, held = (bundle["captures"][arm + suffix] for suffix in ("_formation", "_held"))
        dataset = core.project_capture(formation, dependencies=dependencies)
        equal(dataset, report["material"][arm], "collected material differs from source admission")
        material = stages[arm + "_material"]
        equal(material["dataset.json"], dataset, "material receipt differs")
        equal(material["capture.json"], formation, "material source differs")
        admitted = integer(dataset["counts"]["admitted_rows"], 16)
        fit = report["fits"][arm]
        original_route = bundle["captures"]["ORIGINAL_held"]["binding"]["route"]
        equal(original_route, dict(name="parented_original", id=1, path=plan["parent"]["adapter"]), "original checkpoint route differs")
        equal(formation["binding"]["route"], original_route, "formation did not use original checkpoint")
        held_route = held["binding"]["route"]
        if admitted == 0:
            equal(fit, dict(status="NO_WRITE", updates=0, fits=0), "empty arm forged fit")
            receipt = material["no_write.json"]
            equal({key: receipt[key] for key in ("status", "calls", "fits", "updates", "parent")},
                  dict(status="NO_WRITE", calls=0, fits=0, updates=0, parent=plan["parent"]), "NO_WRITE receipt differs")
            equal(receipt["dataset_sha256"], complete["inventory"][arm + "_material"]["dataset.json"], "NO_WRITE dataset pin differs")
            equal(held_route, original_route, "NO_WRITE route changed")
            dose = dict(rows=0, updates=0, presentations=0, target_tokens=0, context_tokens=0, actual_supervised_tokens=0, actual_context_tokens=0, actual_padded_tokens=0)
        else:
            equal([fit["status"], fit["fits"], fit["updates"]], ["WRITE", 1, 8 * admitted], "dose/fit count differs")
            prepared = material["training.json"]
            equal(material["prepared.json"], {name: complete["inventory"][arm + "_material"][name]
                                              for name in ("training.json", "dataset.json", "capture.json")}, "prepared material pins differ")
            equal(fit["dose"], prepared, "reported dose differs")
            for key, expected in dict(rows=admitted, updates=8 * admitted, presentations=8 * admitted, fit_seed=seed).items():
                equal(prepared[key], expected, "eight-pass dose differs")
            for key in ("target_tokens", "context_tokens", "total_tokens", "actual_supervised_tokens", "actual_context_tokens", "actual_padded_tokens", "padding_tokens", "train_tokens_seen"):
                integer(prepared[key])
            equal(prepared["total_tokens"], prepared["target_tokens"] + prepared["context_tokens"], "dose token totals disagree")
            for key, base in (("actual_supervised_tokens", "target_tokens"), ("actual_context_tokens", "context_tokens"), ("actual_padded_tokens", "total_tokens"), ("train_tokens_seen", "total_tokens")):
                equal(prepared[key], 8 * prepared[base], "eight-pass token total differs")
            equal(prepared["padding_tokens"], 0, "single-row padding differs")
            train_manifest = stages[arm + "_fit"]["adapter/train_manifest.json"]
            equal(train_manifest["warm_start"]["source_state"], fit["source_state"], "fit source tensors differ")
            equal(train_manifest["warm_start"]["initialized_state"], fit["initialized_state"], "fit initialization differs")
            require(train_manifest["warm_start"]["final_state"] != fit["initialized_state"], "WRITE unchanged per tensor inventory")
            require(held_route != original_route, "WRITE route unchanged")
            require(held_route["path"] == plan["root"] + f"/arms/{arm}/run/WRITE_fit/adapter", "wrong written adapter route")
            dose = {key: value for key, value in prepared.items() if key not in ("items", "encoding", "epoch_order")}
        source_values = {tuple(row["execution"]["values"]) for row in ledgers[arm + "_formation"] if row["execution"]}
        held_values = [tuple(row["execution"]["values"]) for row in ledgers[arm + "_held"] if row["execution"]]
        novelty = dict(held_executions=len(held_values), distinct_held_triples=len(set(held_values)),
                       held_executions_with_unseen_apply_triple=sum(values not in source_values for values in held_values),
                       same_initial_tasks_not_same_experience=True, new_ids_not_unseen_rules_or_base_knowledge=True)
        equal(novelty, report["source_novelty"][arm], "source novelty differs")
        equal(report["held_vs_initial"][arm], {metric: summaries[arm + "_held"][metric] - summaries["ORIGINAL_held"][metric] for metric in METRICS}, "initial contrast differs")
        retention_docs = stages[arm + "_retention"]
        equal(retention_docs["identity.json"]["route"], held_route, "retention checkpoint differs")
        validate_native(arm + "_retention", retention_docs, None, report["costs"][arm + "_retention"])
        arms[arm] = dict(status=fit["status"], source_counts=dataset["counts"], dose=dose,
                         novelty=novelty, retention=retention(report["retention"][arm], bundle["history"], retention_docs,
                                                            complete["inventory"][arm + "_retention"]))
    if all(report["fits"][arm]["fits"] for arm in ARMS):
        for key in ("source_state", "initialized_state"):
            equal(report["fits"]["P"][key], report["fits"]["N"][key], "unmatched initialized parent")
    totals = dict(calls=sum(integer(cost["calls"]) for cost in report["costs"].values()),
                  updates=sum(integer(fit["updates"]) for fit in report["fits"].values()),
                  fits=sum(integer(fit["fits"]) for fit in report["fits"].values()))
    for key, value in totals.items():
        equal(complete[key], value, "completion cost total differs")
        if key != "fits":
            equal(report[key], value, "report total differs")
    require(totals["calls"] <= 300 and totals["updates"] <= 256, "campaign dose cap exceeded")
    comparisons = {"P_vs_N": pair_rows(ledgers["P_held"], ledgers["N_held"]),
                   **{arm + "_vs_ORIGINAL": pair_rows(ledgers[arm + "_held"], ledgers["ORIGINAL_held"]) for arm in ARMS}}
    return dict(seed=seed, pins=bundle.get("pins", {}), arms=arms, summaries=summaries, rows=ledgers,
                paired=comparisons, costs=report["costs"], totals=totals,
                held_P_minus_N_over16=(summaries["P_held"]["production_eligible"] - summaries["N_held"]["production_eligible"]) / 16,
                parent_removal="core replay and exact archived native prompt joins; no independent model execution",
                historical_original=report["historical_original"], controller_elapsed_seconds=complete["elapsed_seconds"])


def reduce_cohort(bundles, core, dependencies):
    require(len(bundles) == 3 and all(type(bundle["seed"]) is int for bundle in bundles) and
            sorted(bundle["seed"] for bundle in bundles) == [0, 1, 2], "exact three learner seeds required")
    seeds = [reduce_bundle(bundle, core, dependencies) for bundle in sorted(bundles, key=lambda item: item["seed"])]
    values = [seed["held_P_minus_N_over16"] for seed in seeds]
    return dict(schema="astra_parented_record_local_analysis_20260913_v1", seeds=seeds,
        paired_learners=3, effect=dict(mean=sum(values) / 3, minimum=min(values), maximum=max(values)),
        automatic_pass=False, limitations=[
            "DEV, not adaptive parenting, strong H1/H2 or untouched confirmation; fixed comma scaffold remains.",
            "Three learner pairs, not independent episodes/turns; no pooled causal significance claim.",
            "Same starts and policy do not imply identical experiences, material, realized updates or total compute.",
            "Prior exposed retention panels use historical/noncontemporaneous original controls; losses remain substantive.",
            "CPU frozen-core replay and archived native attestations only; no tokenizer/model/hardware validation or tensor payload reads.",
            "Retention score Booleans are independently tallied and raw-linked, not freshly rescored with a model/material scorer.",
            "Source novelty is relative to own apply executions, not all training, unseen rules or base knowledge."])


def markdown(report):
    lines = ["# Fixed-coaching DEV: independent local reduction", ""]
    for seed in report["seeds"]:
        lines += [f'## Seed {seed["seed"]}', "", "|Seed|Arm|Admitted /16|Updates|Held eligible /16|Content|Strict|Old held content /48|Canary /12|", "|---|---|---|---|---|---|---|---|---|"]
        for arm in (*ARMS, "ORIGINAL"):
            summary = seed["summaries"][arm + "_held"]
            record = seed["arms"].get(arm)
            values = [str(seed["seed"]), arm, str(record["source_counts"]["admitted_rows"]) if record else "—",
                      str(record["dose"]["updates"]) if record else "0", str(summary["production_eligible"]),
                      str(summary["content_correct"]), str(summary["strict_canonical"]),
                      str(record["retention"]["held"]["metrics"]["content_correct"]["current"]) if record else "historical",
                      str(record["retention"]["canary"]["metrics"]["content_correct"]["current"]) if record else "historical"]
            lines.append("|" + "|".join(values) + "|")
        lines.append(f'\nSeed {seed["seed"]}: P−N/16={seed["held_P_minus_N_over16"]:+.4f}; calls/updates/fits {canonical(seed["totals"])}.')
        for arm in ARMS:
            value = seed["arms"][arm]
            lines.append(f'- {arm} {value["status"]}: held retention losses {len(value["retention"]["held"]["metrics"]["content_correct"]["losses"])}; '
                         f'novel apply-relative held executions {value["novelty"]["held_executions_with_unseen_apply_triple"]}; dose {canonical(value["dose"])}.')
        for stage, cost in seed["costs"].items():
            lines.append(f'- {stage}: {canonical(cost)}')
        lines.append("")
    lines += ["Paired mean/range over **three learners**: " + canonical(report["effect"]), "", "## Limits"]
    lines += ["- " + text for text in report["limitations"]]
    lines.append("\nFull paired slot IDs, turn strata, field/format errors, historical retention gains/losses and raw ledger are in analysis.json.")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--protocol-path")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    require(not Path(args.out).exists(), "output exists; no overwrite")
    manifest = read(args.manifest, args.manifest_sha256)
    equal(manifest["schema"], "astra_parented_record_analysis_inputs_v1", "input manifest schema differs")
    core, dependencies = load_core(args.source_root, args.protocol_path)
    report = reduce_cohort([load_bundle(entry) for entry in manifest["seeds"]], core, dependencies)
    report["input_manifest_sha256"] = args.manifest_sha256
    out = Path(args.out)
    out.mkdir()
    for name, text in (("analysis.json", json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n"),
                       ("analysis.md", markdown(report))):
        with (out / name).open("x") as stream:
            stream.write(text)
    print(canonical({name: sha((out / name).read_bytes()) for name in ("analysis.json", "analysis.md")}))


if __name__ == "__main__":
    main()
