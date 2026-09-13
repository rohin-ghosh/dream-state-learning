"""Local-only independent reduction of three completed full-dose pairs.

Consumes explicitly pinned local captures/collections; never discovers outcomes,
collects native work, loads a model/tokenizer, or changes a frozen score protocol.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys

SELF = Path(__file__).resolve()
RUNNER_PIN = "ddd36b16e188a2c2bfa11e61e8fbed66fed67d93f81b1d4fa6384c04dd43c025"
PROTOCOL_PIN = "e777b5be15e2a1cab447de3e72fb013bfac2a20a3d12d81574f95880ca60b0e6"
MATERIAL_PIN = "b3c7fa549fdade0866da51131f64fe067ad7cd3ce36187f67e4c56ac7fbe5c1d"
DATA_PIN = "7f9045242e98dc05b85f814574a1eb87cacebf463af88dcca60729c4aa5ebd66"
SCHEMA = "astra_contrastive_full_dose_independent_reduction_v1"
ARMS = ("plain", "contrastive")
STATES = ("OFF", *ARMS)
PANELS = ("D1", "D2", "C-record", "C-general")
FIELDS = ("try", "observed", "predicted", "relation")
ERRORS = ("completion_errors", "syntax_errors", "schema_errors", "source_errors")
LIMITS = [
    "All panels are exposed exploratory DEV, not fresh confirmation or independent learner replications.",
    "D1/D2 repeat twelve source situations in two wrappers; their24 rows are not24 independent situations.",
    "C-record is exposed; negate-earlier is a perfect fixture shortcut. No source-attention mechanism inference.",
    "Context grouping plus instructions differ; context/padded costs differ. Equal updates are not equal compute.",
    "OFF is one reused historical noncontemporaneous endpoint, not three replications or incremental calls.",
    "Frozen row scorer replay and receipt/hash consistency are not native hardware authentication or tokenizer/weight recomputation.",
    "No child SLEEP, parenting, freeze, clean-lineage, H1/H2/general G3 or automatic promotion.",
]
METRICS = dict(strict="Original frozen material.score_row strict_pass; perception JSON whitespace/key order are accepted, fences are not. NOT canonical-byte equality.",
               content="All source fields correct after the original decoder/type/domain checks and stop completion; addition/copy retain original exact targets.",
               exact_target_bytes="Stop completion and unchanged raw target text; descriptive only, not a replacement screen.")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    checksum = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b""):
            checksum.update(chunk)
    return checksum.hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)+"\n").encode()


def read(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "duplicate JSON key")
            result[key] = value
        return result
    return json.loads(Path(path).read_bytes(), object_pairs_hook=unique,
                      parse_constant=lambda value: require(False, "nonfinite JSON"))


def pinned(record, expected=None):
    require(type(record) is dict and set(record) == {"path", "sha256"}, "closed file binding required")
    require(type(record["path"]) is str and Path(record["path"]).is_absolute(), "absolute input required")
    require(expected is None or record["sha256"] == expected, "frozen source pin differs")
    require(digest(record["path"]) == record["sha256"], "file pin differs: "+record["path"])


def load(record, name, expected):
    pinned(record, expected)
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("contrastive_analysis_"+name, record["path"])
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def validate_dataset(dataset, material, corpus):
    require(hashlib.sha256(material.encoded(dataset)).hexdigest() == DATA_PIN and
            material.encoded(dataset) == material.encoded(material.build_dataset(corpus)), "exact frozen dataset differs")
    require(set(dataset["training"]) == set(ARMS) and set(dataset["evaluation"]) == set(PANELS), "arm/panel inventory differs")
    for panel, rows in dataset["evaluation"].items():
        require(len(rows) == 12 and len({row["row_id"] for row in rows}) == 12, "fixed12 panel denominator differs: "+panel)
    for left, right in zip(dataset["training"]["plain"], dataset["training"]["contrastive"], strict=True):
        require(left["raw_target"] == right["raw_target"] and left["source"] == right["source"] and
                left["material"]["fact_inventory"] == right["material"]["fact_inventory"], "paired source/target inventory differs")


def score_rows(dataset, responses, material, corpus):
    require(set(responses) == set(STATES), "missing/extra arm or historical OFF")
    cases = {panel+"/"+row["row_id"]: row for panel, rows in dataset["evaluation"].items() for row in rows}
    require(len(cases) == 48, "exact48 response denominator required")
    states, frozen = {}, {}
    for state in STATES:
        require(type(responses[state]) is dict and set(responses[state]) == set(cases), "missing/extra/unknown response rows")
        rows, originals = {}, {}
        for key, row in cases.items():
            response = responses[state][key]
            require(type(response) is dict and set(response) == {"raw", "finish_reason"} and
                    type(response["raw"]) is str and response["finish_reason"] in ("stop", "length", "error"), "raw envelope differs")
            original = material.score_row(corpus, row, response["raw"], response["finish_reason"])
            require(type(original["strict_pass"]) is bool, "typed strict score required")
            if row["skill"] == "perception":
                require(set(original["field_correct"]) == set(FIELDS) and
                        all(value is None or type(value) is bool for value in original["field_correct"].values()), "field score schema differs")
                content = not any(original[name] for name in ERRORS) and all(value is True for value in original["field_correct"].values())
            else:
                content = original["strict_pass"]
            require(not original["strict_pass"] or content, "strict correct without content")
            rows[key] = dict(original, content_correct=content, strict_correct=original["strict_pass"], skill=row["skill"],
                             exact_target_bytes=response["finish_reason"] == "stop" and response["raw"] == row["raw_target"])
            originals[key] = original
        panels = {}
        for panel in PANELS:
            selected = [row for key, row in rows.items() if key.startswith(panel+"/")]
            panels[panel] = dict(denominator=12, content=sum(row["content_correct"] for row in selected),
                                strict=sum(row["strict_correct"] for row in selected),
                                exact_target_bytes=sum(row["exact_target_bytes"] for row in selected),
                                content_without_strict=sum(row["content_correct"] and not row["strict_correct"] for row in selected),
                                finish_reasons=dict(Counter(row["finish_reason"] for row in selected)),
                                failures={name: dict(Counter(error for row in selected for error in row[name])) for name in ERRORS},
                                failure_rows={name: sum(bool(row[name]) for row in selected) for name in ERRORS},
                                strict_failures=dict(Counter(error for row in selected for error in row.get("strict_failures", []))),
                                fields={field: dict(correct=sum(row["field_correct"].get(field) is True for row in selected),
                                                    incorrect=sum(row["field_correct"].get(field) is False for row in selected),
                                                    unavailable=sum(row["field_correct"].get(field) is None for row in selected))
                                        for field in FIELDS} if panel != "C-general" else {})
        complete = all(row["finish_reason"] == "stop" for row in rows.values())
        states[state] = dict(rows=rows, panels=panels, complete=complete,
                             held={metric: sum(panels[panel][metric] for panel in ("D1", "D2")) for metric in ("content", "strict")})
        frozen[state] = dict(items=originals, totals={panel: panels[panel]["strict"] for panel in PANELS}, complete=complete)
    return states, frozen


def paired(first, second, keys, metric):
    result = {name: [] for name in ("wins", "losses", "both", "neither")}
    for key in keys:
        left, right = first[key][metric], second[key][metric]
        category = "both" if left and right else "wins" if left else "losses" if right else "neither"
        result[category].append(key)
    return dict(items=result, counts={name: len(values) for name, values in result.items()},
                difference=len(result["wins"])-len(result["losses"]), denominator=len(keys))


def summarize(dataset, responses, material, corpus):
    states, frozen = score_rows(dataset, responses, material, corpus)
    keys = list(states["OFF"]["rows"])
    groups = {panel: [key for key in keys if key.startswith(panel+"/")] for panel in PANELS}
    groups["held"] = groups["D1"]+groups["D2"]
    contrasts = {}
    for control in ("plain", "OFF"):
        contrasts["contrastive_minus_"+control] = {panel: {metric: paired(states["contrastive"]["rows"], states[control]["rows"], selected, metric+"_correct")
                                                                 for metric in ("content", "strict")} for panel, selected in groups.items()}
    canaries = {arm: {key: dict(historical_OFF_correct=states["OFF"]["rows"][key]["strict_correct"],
                               arm_correct=states[arm]["rows"][key]["strict_correct"],
                               lost=states["OFF"]["rows"][key]["strict_correct"] and not states[arm]["rows"][key]["strict_correct"])
                      for key in keys if key.startswith("C-")} for arm in ARMS}
    held = {state: states[state]["held"]["strict"] for state in STATES}
    screen = dataset["screen"]
    complete = all(states[state]["complete"] for state in STATES)
    regressions = [key for key, value in canaries["contrastive"].items() if value["lost"]]
    met = complete and held["OFF"] < screen["off_ceiling"] and held["contrastive"] >= screen["held_min"] and all(
        states["contrastive"]["panels"][panel]["strict"] >= screen["each_skin_min"] for panel in ("D1", "D2")) and all(
        held["contrastive"]-held[control] >= screen["advantage_over_each_control"] for control in ("OFF", "plain")) and not regressions
    frozen_result = dict(dataset_sha256=DATA_PIN, states=frozen, held_totals=held, complete=complete,
                         paired_held={control: {name: contrasts["contrastive_minus_"+control]["held"]["strict"]["items"][name]
                                               for name in ("wins", "losses")} for control in ("OFF", "plain")},
                         canary_regressions=regressions, ceiling_limited=held["OFF"] >= screen["off_ceiling"],
                         exploratory_screen_pass=met,
                         qualification="authored material screen only; syntax versus field errors must be interpreted separately")
    return dict(states=states, paired=contrasts, per_item_canaries=canaries, original_screen=dict(met=met, thresholds=screen,
                ceiling_limited=frozen_result["ceiling_limited"], complete=complete), frozen_result=frozen_result)


def stage_files(root, complete, stage, runtime):
    directory = root / "run" / stage
    require(directory.is_dir() and not directory.is_symlink(), "missing/nonlocal stage")
    require(not (directory / "failure.json").exists() and not (directory / "cleanup_failure.json").exists(), "failed stage never reduced")
    actual = runtime.tree(directory)
    require(actual == complete["stages"][stage], "completed stage hashes differ: "+stage)
    return directory


def training_costs(prepared):
    lengths = {row["row_id"]: len(row["input_ids"]) for row in prepared["encoding"]}
    require(len(lengths) == 12 and len(prepared["epoch_order"]) == 112, "fit cost denominator differs")
    padded = 0
    for order in prepared["epoch_order"]:
        require(len(order) == 12 and set(order) == set(lengths), "fit cost epoch inventory differs")
        for offset in range(0, 12, 4):
            padded += 4*max(lengths[key] for key in order[offset:offset+4])
    target = sum(len(row["supervised_ids"]) for row in prepared["encoding"])
    total = sum(lengths.values())
    return dict(rows=12, epochs=112, updates=336, presentations=1344,
                target_tokens_per_epoch=target, total_tokens_per_epoch=total,
                context_and_masked_tail_tokens_per_epoch=total-target,
                supervised_tokens=112*target, padded_tokens=padded)


def load_pair(entry, manifest, runtime, material, corpus, trainer, probe):
    require(type(entry) is dict and set(entry) == {"seed", "root", "plan_sha256", "completion_sha256", "collection", "scores"}, "closed pair binding required")
    seed = runtime.seed_value(entry["seed"])
    root = Path(entry["root"])
    require(root.is_absolute() and root.is_dir() and not root.is_symlink(), "explicit local capture root required")
    for name in ("collection", "scores"):
        pinned(entry[name])
    require(digest(root / "plan.json") == entry["plan_sha256"] and digest(root / "capture_complete.json") == entry["completion_sha256"], "plan/completion hash mismatch")
    plan, complete = read(root / "plan.json"), read(root / "capture_complete.json")
    collection, scores = read(entry["collection"]["path"]), read(entry["scores"]["path"])
    require(collection == dict(plan_sha256=entry["plan_sha256"], completion_sha256=entry["completion_sha256"], scores_sha256=entry["scores"]["sha256"]), "collection score join differs")
    require(plan["scope"] == runtime.SCOPE and plan["claim"] == runtime.CLAIM and plan["self_sha256"] == RUNNER_PIN and
            runtime.seed_value(plan["learner_seed"]) == seed and runtime.seed_value(plan["specification"]["learner_seed"]) == seed, "scope/runtime/seed mismatch")
    require(plan["model"] == plan["specification"]["model"] and plan["source"] == plan["specification"]["source"] and
            plan["model_files"] == plan["binding"]["model_files"], "base/source plan agreement differs")
    require(plan["specification"]["runner_sha256"] == RUNNER_PIN and plan["specification"]["protocol"]["sha256"] == PROTOCOL_PIN and
            plan["specification"]["material"]["sha256"] == MATERIAL_PIN and plan["specification"]["source_files"] == manifest["source_files"], "frozen input binding mismatch")
    for field, checksum in dict(original=runtime.ORIGINAL_SHA, encoder=runtime.old.ENCODER_SHA256,
                                reflection=runtime.old.REFLECTION_SHA256, public=runtime.old.PUBLIC_SHA256,
                                binding=runtime.BINDING_SHA, original_protocol=runtime.OLD_PROTOCOL_SHA,
                                historical_archive=runtime.ARCHIVE_SHA).items():
        require(plan["specification"][field]["sha256"] == checksum, "native helper/provenance pin differs: "+field)
    require(hashlib.sha256(encoded(plan["specification"])).hexdigest() == plan["spec_sha256"] and
            read(root / "prepare_started.json")["spec_sha256"] == plan["spec_sha256"], "prepared spec binding differs")
    require(plan["stages"] == list(runtime.STAGES) and plan["budget"] == runtime.BUDGET and
            plan["engine"] == runtime.old.ENGINE and plan["params"] == runtime.old.PARAMS, "closed stage/budget/native config mismatch")
    require(encoded(plan["config"]) == encoded(asdict(trainer.TrainConfig(**runtime.recipe(seed), model=plan["model"]))), "fit dose/config mismatch")
    require(not (root / "controller_failure.json").exists() and not (root / "prepare_failure.json").exists(), "failed root never reduced")
    require(complete["plan_sha256"] == entry["plan_sha256"] and complete["calls"] == 96 and complete["fits"] == 2 and complete["updates"] == 672 and complete["scored"] is False,
            "incomplete pair/budget")
    require(set(complete["stages"]) == set(runtime.STAGES) == {path.name for path in (root / "run").iterdir()}, "missing/extra arm or stage")
    expected = {"material.json", "calls.json", "costs.json", "historical_OFF.json", "train_plain.json", "train_contrastive.json"}
    require(set(plan["input_hashes"]) == expected and plan["input_hashes"]["material.json"] == DATA_PIN, "input inventory differs")
    for name, checksum in plan["input_hashes"].items():
        require(digest(root / name) == checksum, "prepared input changed: "+name)
    dataset, calls = read(root / "material.json"), read(root / "calls.json")
    validate_dataset(dataset, material, corpus)
    require(set(calls) == set(PANELS), "calls panel inventory differs")
    for panel in PANELS:
        require(len(calls[panel]) == 12, "call denominator differs")
        for index, (call, row) in enumerate(zip(calls[panel], dataset["evaluation"][panel], strict=True)):
            require(call["call_id"] == f"{index:02d}" and call["row_id"] == row["row_id"] and call["messages"] == row["input_messages"], "source/prompt/call row mismatch")
    history = runtime.import_off(manifest["historical_archive"], dataset, calls, plan["chat_template"], plan["binding"], probe)
    captured_history = read(root / "historical_OFF.json")
    require(captured_history["archive"]["sha256"] == manifest["historical_archive"]["sha256"], "historical archive differs")
    history["archive"] = captured_history["archive"]
    require(history == captured_history, "historical OFF import changed")
    historical_label = dict(archive=captured_history["archive"], plan_sha256=runtime.OLD_PLAN_SHA,
                            completion_sha256=runtime.OLD_COMPLETE_SHA, scores_sha256=runtime.OLD_SCORES_SHA, new_calls=0)
    require(scores["historical_OFF"] == historical_label, "historical OFF label/incremental cost differs")
    responses, costs, fits, pids = {"OFF": history["responses"]}, {}, {}, []
    controller = read(root / "controller_started.json")
    require(controller["plan_sha256"] == entry["plan_sha256"], "controller plan receipt differs")
    for stage in runtime.STAGES:
        directory = stage_files(root, complete, stage, runtime)
        started, launched, released = (read(directory / name) for name in ("started.json", "launch.json", "released.json"))
        require(type(started["pid"]) is int and started["pid"] > 1 and started["pid"] == started["pgid"] == launched["pid"] == launched["pgid"] == released["pid"] == released["pgid"] and
                started["stage"] == launched["stage"] == stage and started["plan_sha256"] == launched["plan_sha256"] == entry["plan_sha256"] and
                started["parent_pid"] == launched["parent_pid"] == controller["pid"], "process receipt custody differs")
        pids.append(started["pid"])
        kind, arm = stage.split("_", 1)
        native_adapter = str(Path(plan["root"]) / "run" / ("fit_"+arm) / "adapter")
        if kind == "fit":
            prepared = read(root / f"train_{arm}.json")
            runtime.validate_prepared(prepared, dataset["training"][arm], seed, trainer)
            computed_costs = training_costs(prepared)
            require(computed_costs == prepared["costs"], "independent training context/padding costs differ")
            receipt = read(directory / "fit.json")
            fit = read(directory / "adapter/train_manifest.json")
            runtime.check_fit_manifest(fit, prepared, plan, arm)
            files = runtime.old.check_adapter(directory / "adapter", plan["config"])
            require(receipt["arm"] == arm and receipt["learner_seed"] == seed and receipt["adapter"] == native_adapter and
                    receipt["adapter_files"] == files and receipt["updates"] == 336 and receipt["presentations"] == 1344 and
                    receipt["fresh_base"] is True and receipt["epoch_order_sha256"] == runtime.old.value_hash(prepared["epoch_order"]), "fresh fit receipt mismatch")
            require(scores["fits"][arm] == dict(receipt=receipt, manifest=fit), "collected fit differs")
            fits[arm] = dict(receipt=receipt, manifest=fit, costs=computed_costs)
        else:
            identity, closed = read(directory / "identity.json"), read(directory / "closed.json")
            require(identity == runtime.readout_identity(plan, arm, native_adapter, fits[arm]["receipt"]["adapter_files"]), "readout route/seed/model identity mismatch")
            expected_names = {"identity.json"} | {panel+"__"+call["call_id"]+suffix for panel in PANELS for call in calls[panel] for suffix in (".request.json", ".response.json")}
            require(closed["calls"] == 48 and set(closed["files"]) == expected_names, "closed response denominator differs")
            require({path.name for path in directory.glob("*.response.json")} == {name for name in expected_names if name.endswith(".response.json")}, "extra raw response")
            for name, checksum in closed["files"].items():
                require(complete["stages"][stage][name] == checksum, "closed/completed hash join differs")
            responses[arm] = {}
            for panel in PANELS:
                values = []
                for call in calls[panel]:
                    stem = panel+"__"+call["call_id"]
                    require(read(directory / (stem+".request.json")) == call, "captured request differs")
                    response = read(directory / (stem+".response.json"))
                    runtime.validate_response(probe, call, response, identity["lora_request"])
                    responses[arm][panel+"/"+call["row_id"]] = dict(raw=response["text"], finish_reason=response["finish_reason"])
                    values.append(response)
                costs[arm+"__"+panel] = dict(calls=12, prompt_tokens=sum(len(value["actual_prompt_token_ids"]) for value in values),
                                            output_tokens=sum(len(value["output_token_ids"]) for value in values),
                                            generation_seconds=sum(value["ended"]-value["started"] for value in values))
    require(len(set(pids)) == 4, "four distinct cold worker receipts required")
    trains = {arm: read(root / f"train_{arm}.json") for arm in ARMS}
    require(trains["plain"]["epoch_order"] == trains["contrastive"]["epoch_order"] and
            [row["supervised_ids"] for row in trains["plain"]["encoding"]] == [row["supervised_ids"] for row in trains["contrastive"]["encoding"]], "paired epoch/supervision mismatch")
    reduced = summarize(dataset, responses, material, corpus)
    require(reduced.pop("frozen_result") == scores["material_scores"], "raw scorer replay/independent aggregate differs from saved score")
    require(reduced["per_item_canaries"] == scores["per_item_canaries"] and costs == scores["generation_costs"], "saved canary/cost mismatch")
    require(scores["prepared_costs"] == read(root / "costs.json") == {arm: fits[arm]["costs"] for arm in ARMS}, "fit context cost mismatch")
    require(scores["plan_sha256"] == entry["plan_sha256"] and scores["completion_sha256"] == entry["completion_sha256"] and
            scores["learner_seed"] == seed and scores["calls"] == 96 and scores["budget"] == runtime.BUDGET and
            scores["scope"] == runtime.SCOPE and scores["claim"] == runtime.CLAIM and
            scores["automatic_pass"] is False and scores["scientific_pass"] is None, "collected identity/budget/claim mismatch")
    require(type(complete["elapsed_seconds"]) in (int, float) and math.isfinite(complete["elapsed_seconds"]) and
            0 <= complete["elapsed_seconds"] <= 7200 and scores["controller_elapsed_seconds"] == complete["elapsed_seconds"], "controller timing differs")
    for arm in ARMS:
        require(type(fits[arm]["receipt"]["elapsed_seconds"]) in (int, float) and math.isfinite(fits[arm]["receipt"]["elapsed_seconds"]) and
                fits[arm]["receipt"]["elapsed_seconds"] >= 0, "fit timing invalid")
    return dict(seed=seed, native_root=plan["root"], inputs=entry, **reduced, fit_costs={arm: dict(fits[arm]["costs"],
                elapsed_seconds=fits[arm]["receipt"]["elapsed_seconds"], final_loss=fits[arm]["manifest"]["final_loss"]) for arm in ARMS},
                generation_costs=costs, controller_elapsed_seconds=complete["elapsed_seconds"],
                new_cost=dict(fits=2, updates=672, presentations=2688, calls=96),
                historical_OFF=dict(historical_label, noncontemporaneous=True, reused=True, incremental_calls=0, incremental_updates=0),
                automatic_pass=False, scientific_pass=None)


def reduce_manifest(path, pin):
    binding = dict(path=str(Path(path).absolute()), sha256=pin)
    pinned(binding)
    manifest = read(path)
    require(set(manifest) == {"runner", "protocol", "material", "public", "source", "source_files", "historical_archive", "pairs"}, "closed manifest differs")
    require(type(manifest["pairs"]) is list and len(manifest["pairs"]) == 3, "all three completed pairs required; no selected subset")
    seeds = [entry["seed"] for entry in manifest["pairs"]]
    require(all(type(seed) is int for seed in seeds) and sorted(seeds) == [0, 1, 2], "exact independent seed0/1/2 roster required")
    require(len({entry["root"] for entry in manifest["pairs"]}) == 3 and len({entry["plan_sha256"] for entry in manifest["pairs"]}) == 3, "distinct roots/plans required")
    require(len({str(Path(entry["root"]).resolve()) for entry in manifest["pairs"]}) == 3, "aliased capture roots forbidden")
    runtime = load(manifest["runner"], "runtime", RUNNER_PIN)
    pinned(manifest["protocol"], PROTOCOL_PIN)
    material = load(manifest["material"], "material", MATERIAL_PIN)
    pinned(manifest["public"], runtime.old.PUBLIC_SHA256)
    pinned(manifest["historical_archive"], runtime.ARCHIVE_SHA)
    require(Path(manifest["source"]).is_absolute() and runtime.tree(manifest["source"]) == manifest["source_files"] and
            set(manifest["source_files"]) == set(runtime.old.SOURCE_NAMES), "explicit frozen four-file source required")
    require(manifest["source_files"]["organism_v6/__init__.py"] == hashlib.sha256(b"").hexdigest(), "frozen source init differs")
    for name, checksum in dict(material.PINS, **{"organism_v6/train_adapter_v3.py": material.REUSE["organism_v6/train_adapter_v3.py"]}).items():
        require(manifest["source_files"][name] == checksum, "frozen source mismatch")
    corpus = material.load_corpus(manifest["source"])
    _, trainer = runtime.old.source_api(manifest["source"])
    probe = runtime.old.load_probe(manifest["public"]["path"], runtime.old.PUBLIC_SHA256)
    results = [load_pair(entry, manifest, runtime, material, corpus, trainer, probe) for entry in sorted(manifest["pairs"], key=lambda entry: entry["seed"])]
    require(len({result["native_root"] for result in results}) == 3, "distinct original native roots required")
    require(all(result["states"]["OFF"] == results[0]["states"]["OFF"] for result in results), "different historical OFF across seeds")
    totals = {key: sum(result["new_cost"][key] for result in results) for key in ("fits", "updates", "presentations", "calls")}
    require(totals == dict(fits=6, updates=2016, presentations=8064, calls=288), "whole-roster budget mismatch")
    return dict(schema=SCHEMA, reducer_sha256=digest(SELF), manifest=binding, frozen_inputs={key: value for key, value in manifest.items() if key != "pairs"},
                seeds=results, roster=dict(present=[0, 1, 2], complete=True,
                original_screen_by_seed=[result["original_screen"]["met"] for result in results]),
                total_new_cost=totals, historical_OFF_unique_calls=48,
                historical_incremental_cost=dict(calls=0, updates=0),
                total_new_generation_cost={key: sum(cell[key] for result in results for cell in result["generation_costs"].values())
                                           for key in ("calls", "prompt_tokens", "output_tokens", "generation_seconds")},
                automatic_pass=False, scientific_pass=None, metric_definitions=METRICS, limitations=LIMITS)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("manifest", "manifest-sha256", "out"):
        parser.add_argument("--"+name, required=True)
    args = parser.parse_args(argv)
    output = Path(args.out)
    require(output.is_absolute() and output.resolve().is_relative_to(Path("/tmp").resolve()) and not output.exists() and not output.is_symlink(), "fresh /tmp analysis output required")
    require(output.resolve() != Path(args.manifest).resolve(), "cannot replace input")
    result = reduce_manifest(args.manifest, args.manifest_sha256)
    for entry in result["seeds"]:
        require(not output.resolve().is_relative_to(Path(entry["inputs"]["root"]).resolve()), "no capture-root writes")
    with output.open("xb") as stream:
        stream.write(encoded(result))
    print(json.dumps(dict(status="REDUCED_PINNED_RAW_COLLECTED_THREE_PAIRS", out=str(output), sha256=digest(output), native_executed=False)))


if __name__ == "__main__":
    main()
