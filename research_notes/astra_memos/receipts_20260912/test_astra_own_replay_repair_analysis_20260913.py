"""Synthetic CPU evidence only; no outcome mirrors, models or native calls."""
import copy
import hashlib
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

import astra_own_replay_repair_analysis_20260913 as analysis


SOURCE = "/tmp/astra_level1_real_record_source_20260913_attempt1"
PROTOCOL = "/data/home/rohing/dream-state/research_notes/astra_memos/ASTRA_OWN_SOURCE_REPLAY_REPAIR_2026-09-13.md"


def checksum(value):
    return hashlib.sha256(analysis.canonical(value).encode()).hexdigest()


def capture_fixture(apis, seed):
    records = 0
    def backend(request):
        nonlocal records
        raw = "PREDICT: T\nACT: TRY 2,5,9"
        if request["kind"] == "record":
            facts = json.loads(re.findall(r"^Observed fields: (.*)$", request["input_messages"][0]["content"], re.MULTILINE)[-1])
            raw = json.dumps({"try": facts["values"], "observed": facts["observed"], "predicted": facts["predicted"],
                             "relation": "matched" if facts["observed"] == facts["predicted"] else "mismatched"})
            if records >= analysis.COUNTS[seed]:
                raw = "{}"
            records += 1
        return dict(request_id=request["request_id"], state=request["state"], raw=raw, finish_reason="stop")
    return apis["formation"].run_state("perception_seed"+str(seed), backend, dependencies=apis["dependencies"])


def admission_fixture(apis, seed, parent, replay_count):
    observation, corpus = apis["observation"], apis["corpus"]
    records, unused = observation.inventory(apis["retention"], apis["material"], corpus)
    producer = dict(learner_seed=seed, adapter=parent["adapter"], adapter_files=parent["adapter_files"],
        model="fixture-model-not-read", model_files={}, parent_plan_sha256=parent["plan_sha256"])
    producer_hash = observation.sha(observation.encoded(producer))
    audits, accepted = [], []
    for index, row in enumerate(row for row in records if row["selected"]):
        request = dict(schema=observation.SCHEMA, row_id=row["row_id"], source_id=row["source_id"], input_messages=row["input_messages"],
            input_sha256=row["input_sha256"], producer_sha256=producer_hash, source_split="train")
        request_id = observation.sha(observation.encoded(request))
        reference = next(item for item in apis["retention"]["training"] if item["row_id"] == row["row_id"])
        raw = reference["raw_target"] if index < replay_count else "{}"
        response = dict(request_id=request_id, input_sha256=row["input_sha256"], producer_sha256=producer_hash, raw=raw, finish_reason="stop")
        judge = corpus._interface().judge_record(raw, corpus.assess_source(row["source"])["execution"])
        response_hash = observation.sha(observation.encoded(response))
        raw_hash = hashlib.sha256(raw.encode()).hexdigest()
        audits.append(dict(submission_index=index, response=response, response_sha256=response_hash, raw_sha256=raw_hash,
            eligible=judge["eligible"], errors=[] if judge["eligible"] else judge["failures"], source_judge=judge))
        if judge["eligible"]:
            accepted.append(dict(row_id=row["row_id"], request_id=request_id, input_messages=row["input_messages"], raw_target=raw,
                target_sha256=raw_hash, source=row["source"], producer_sha256=producer_hash,
                source_proof=dict(original_train_row_id=row["row_id"], original_source_id=row["source_id"], input_sha256=row["input_sha256"],
                    supplied_response_sha256=response_hash, target_origin="SUPPLIED_RAW_CHILD_RESPONSE_ONLY")))
    return dict(schema=observation.SCHEMA, boundary=observation.BOUNDARY, producer=producer, source_population_denominator=96,
        source_admissible_denominator=48, requested_denominator=24, submitted=24, admitted_count=len(accepted), admitted=accepted,
        responses=audits, rejected=[row for row in audits if not row["eligible"]], missing_request_ids=[],
        native_identity_verified=False, training_export_ready=False, fit_decision=None)


def training_fixture(core, mixture, arm):
    rows = mixture["arms"][arm]["rows"]
    audits, items = [], []
    for index, row in enumerate(rows):
        audits.append(dict(row_id=row["row_id"], source_row_id=row["source_row_id"], item_kind=row["item_kind"], presentation_index=index,
            input_ids=[1, 2, 3], labels=[-100, 2, 3], supervised_ids=[2, 3], native_prompt=dict(prompt_token_ids=[1], rendered_prompt="prompt"),
            full_assistant_text="prompt" + row["raw_target"] + "<EOS>", template_tail=""))
        items.append(dict(group=row["row_id"], meta={key: row[key] for key in ("source_row_id", "item_kind", "presentation_index", "target_sha256")},
            spans=[["prompt", False, "context"], [row["raw_target"], True, "skill_target"], ["<EOS>", True, "assistant_end"]]))
    per_kind = {}
    for kind in ("memory", "observation_replay", "extra_memory"):
        size = sum(row["item_kind"] == kind for row in rows)
        per_kind[kind] = dict(rows=size, presentations=8*size, total_tokens=3*size, target_tokens=2*size, context_tokens=size,
            train_tokens_seen=24*size, actual_supervised_tokens=16*size, actual_context_tokens=8*size)
    size = len(rows)
    orders = [[row["row_id"] for row in rows] for unused in range(8)]
    result = dict(schema=core.ENCODING_SCHEMA, material_sha256=mixture["material_sha256"], status=mixture["status"], seed=mixture["seed"], arm=arm,
        items=items, encoding=audits, epoch_order=orders, fit_seed=mixture["seed"], rows=size, updates=8*size, presentations=8*size,
        total_tokens=3*size, target_tokens=2*size, context_tokens=size, train_tokens_seen=24*size, actual_supervised_tokens=16*size,
        actual_context_tokens=8*size, actual_padded_tokens=24*size, padding_tokens=0, per_kind=per_kind,
        presentation_counts={row["row_id"]: 8 for row in rows}, training_items_sha256=core.value_hash(items), epoch_order_sha256=core.value_hash(orders))
    result["encoding_sha256"] = core.value_hash(result)
    return result


def fit_fixture(prepared, config, parent):
    initial = {"layer.lora_A.weight": dict(shape=[2], dtype="torch.float32", sha256="1"*64)}
    final = {"layer.lora_A.weight": dict(shape=[2], dtype="torch.float32", sha256="2"*64)}
    size, updates = prepared["rows"], prepared["updates"]
    return dict(config=config, empty=False, steps=updates, micro_batches=updates, epochs_run=8, nonfinite_batches=0,
        corpus=dict(n_items=size, n_encoded=size, n_skipped_no_target=0, sha256=checksum(prepared)),
        truncation=dict(items_truncated=0, context_tokens_dropped=0, target_tokens_dropped=0, items_split=0),
        packing=dict(mode="one_item_per_sequence", n_sequences=size), tokens=dict(target=prepared["target_tokens"], total=prepared["total_tokens"]),
        train_tokens_seen=prepared["train_tokens_seen"], mean_loss_per_epoch=[.1]*8, final_loss=.1,
        warm_start=dict(mode="WEIGHT_WARM_START_FRESH_OPTIMIZER", optimizer_initialization="fresh_per_write", optimizer_state_restored=False,
            optimizer_state_saved=False, parent_path=parent["adapter"], parent_files=parent["adapter_files"], parent_files_after=parent["adapter_files"],
            parent_unchanged=True, initialized_loaded_state_check=True, base_frozen=True, adapter_count=1, trainer_sha256=analysis.TRAINER_PIN,
            phase_seed=config["seed"], phase_steps=updates, parent_cumulative_steps=320, cumulative_steps=320+updates,
            source_state=initial, initialized_state=initial, final_state=final, trainable_names=["layer.lora_A.weight"]))


def bundle_fixture(apis, seed, replay_count=24):
    core, utilities = apis["core"], apis["utilities"]
    capture = capture_fixture(apis, seed)
    dataset, unused = apis["memory"]._project(capture, apis["formation"], apis["dependencies"])
    utilities.CAPTURE_PINS[seed] = capture["capture_sha256"]
    retention = apis["retention"]
    scorer = analysis.FrozenScorer(capture, dataset, retention, apis)
    parent = dict(adapter="/fixture/original"+str(seed), adapter_files={"adapter.safetensors": "a"*64}, plan_sha256="b"*64)
    admission = admission_fixture(apis, seed, parent, replay_count)
    memory_rows, replay_rows = dataset["rows"], admission["admitted"]
    size = len(memory_rows)
    mixture = dict(schema=core.SCHEMA, seed=seed, parent=parent, status="READY" if replay_count else "REPLAY_UNAVAILABLE",
        memory_rows=memory_rows, replay_rows=replay_rows, replay_rejected=admission["rejected"],
        counts=dict(memory=size, replay=replay_count, rejected=24-replay_count, presentations_per_arm=size+replay_count if replay_count else 0,
            updates_per_arm=8*(size+replay_count) if replay_count else 0, source_population=96, source_supported=48, source_requested=24),
        arms={arm: dict(rows=core.arm_rows(memory_rows, replay_rows, seed, arm)) for arm in analysis.ARMS})
    mixture["material_sha256"] = core.value_hash(mixture)
    calls = []
    for panel in analysis.PANELS:
        rows = memory_rows if panel in ("exact", "paraphrase") else retention["evaluation"][panel]
        key = "paraphrase_input_messages" if panel == "paraphrase" else "input_messages"
        for row in rows:
            calls.append(dict(call_id=f"{panel}_{len(calls):02d}", panel=panel, row_id=row["row_id"], messages=row[key],
                native=dict(prompt_token_ids=[1], rendered_prompt="fixture")))
    config = dict(lr=3e-5, epochs=8, batch_size=1, max_steps=0, rank=8, alpha=16, dropout=.05, seed=seed)
    spec = dict(seed=seed, fit_seed=seed, runner_sha256=analysis.PINS["runner"][1], core=dict(path="/tmp/core.py", sha256=analysis.PINS["core"][1]),
        protocol=dict(path=PROTOCOL, sha256=analysis.PROTOCOL_PIN), capture={})
    stages = [arm+suffix for arm in analysis.ARMS for suffix in ("_fit", "_readout")] if replay_count else []
    plan = dict(scope=analysis.SCOPE, specification=spec, self_sha256=analysis.PINS["runner"][1], parent=parent, root="/fixture/seed"+str(seed),
        status=mixture["status"], stages=stages, configs={arm: copy.deepcopy(config) for arm in analysis.ARMS}, model="fixture-model-not-read", model_files={},
        params=dict(max_tokens=192), counts=dict(memory=size, replay=replay_count, rows_per_arm=size+replay_count),
        calls_per_arm=len(calls) if replay_count else 0, updates_per_arm=8*(size+replay_count) if replay_count else 0,
        input_hashes={}, snapshot_hashes={}, limits=dict(calls=2*len(calls) if replay_count else 0, updates=16*(size+replay_count) if replay_count else 0, fits=2 if replay_count else 0))
    files = {"mixture.json": mixture, "memory/dataset.json": dataset, "memory/capture.json": capture,
        "memory/retention.json": retention, "memory/calls.json": calls, "calls.json": calls, "capture/admission.json": admission}
    report = dict(scope=analysis.SCOPE, status=mixture["status"], seed=seed, parent=parent, plan_sha256="c"*64, completion_sha256="d"*64,
        counts=plan["counts"], source_bindings={key: spec[key] for key in ("core", "protocol", "capture")}, input_hashes=plan["input_hashes"],
        historical_bindings={}, historical_cells={}, historical_manifests={}, cells={}, fits={}, training_costs={}, parameter_diagnostics={}, screen={},
        reused_endpoints={name: dict(noncontemporaneous=True, incremental_calls=0, incremental_updates=0, incremental_fits=0) for name in analysis.HISTORY},
        native_capture_custody_checked=True, automatic_pass=False, scientific_pass=None,
        incremental_cost=dict(plan["limits"], historical_calls=0, historical_updates=0, new_source_calls=0, teacher_calls=0, controller_seconds=1.0))
    complete = dict(scope=analysis.SCOPE, status=mixture["status"], plan_sha256="c"*64, stages={stage: {} for stage in stages},
        scored=False, elapsed_seconds=1.0, **plan["limits"])
    def cell(call):
        rows = scorer.rows if call["panel"] in ("exact", "paraphrase") else scorer.retention[call["panel"]]
        raw = rows[call["row_id"]]["raw_target"]
        return dict(row_id=call["row_id"], raw=raw, finish_reason="stop", response_sha256="e"*64,
            score=scorer(call["panel"], call["row_id"], raw, "stop", call["messages"]),
            cost=dict(prompt_tokens=1, output_tokens=1, generation_seconds=.5))
    panels = {panel: [cell(call) for call in calls if call["panel"] == panel] for panel in analysis.PANELS}
    dummy_training = training_fixture(core, mixture, "REPLAY") if replay_count else dict(rows=size, updates=8*size, target_tokens=size, total_tokens=2*size, train_tokens_seen=16*size)
    for prefix in ("memory_history", "lower_history"):
        historical_plan_pin = core.MEMORY_PLAN_PINS[seed] if prefix == "memory_history" else "a"*64
        spec[prefix] = dict(scores_sha256="f"*64, plan_sha256=historical_plan_pin, completion_sha256="b"*64)
        for filename, field in (("scores.json", "scores_sha256"), ("plan.json", "plan_sha256"), ("completion.json", "completion_sha256")):
            plan["snapshot_hashes"][prefix+"/"+filename] = spec[prefix][field]
        files[prefix+"/scores.json"] = dict(seed=seed, plan_sha256=historical_plan_pin, completion_sha256="b"*64, parent=parent,
            cells={arm: copy.deepcopy(panels) for arm in ("WRITE", "LR0")}, fits={arm: fit_fixture(dummy_training, config, parent) for arm in ("WRITE", "LR0")})
        report["historical_bindings"][prefix] = spec[prefix]
    memory_inputs = {name: checksum(files["memory/"+name]) for name in ("dataset.json", "capture.json", "retention.json", "calls.json")}
    files["memory_history/plan.json"] = dict(input_hashes=memory_inputs, parent=parent, model=plan["model"], model_files=plan["model_files"], params=plan["params"])
    plan["snapshot_hashes"].update({"memory/"+name: value for name, value in memory_inputs.items()})
    spec["capture"].update(plan_sha256="1"*64, completion_sha256="2"*64, report_sha256="3"*64)
    plan["snapshot_hashes"].update({"capture/plan.json": "1"*64, "capture/completion.json": "2"*64, "capture/replay_report.json": "3"*64,
        "capture/admission.json": checksum(admission)})
    files["capture/replay_report.json"] = dict(plan_sha256="1"*64, completion_sha256="2"*64,
        seed_reports={str(seed): dict(sha256=checksum(admission))})
    for name in analysis.HISTORY:
        source = files[("lower_history" if name == "LOWER" else "memory_history")+"/scores.json"]
        source_arm = "LR0" if name == "LR0" else "WRITE"
        report["historical_cells"][name] = copy.deepcopy(source["cells"][source_arm])
        report["historical_manifests"][name] = copy.deepcopy(source["fits"][source_arm])
    for arm in analysis.ARMS if replay_count else ():
        prepared = training_fixture(core, mixture, arm)
        files["training_"+arm+".json"] = prepared
        plan["input_hashes"]["training_"+arm+".json"] = checksum(prepared)
        fit = fit_fixture(prepared, config, parent)
        report["fits"][arm] = fit
        report["parameter_diagnostics"][arm] = dict(changed_elements=1, l2=dict(initial=1., final=1.1, delta=.1))
        files["run/"+arm+"_fit/adapter/train_manifest.json"] = fit
        files["run/"+arm+"_fit/fit.json"] = dict(arm=arm, updates=prepared["updates"], calls=0, training_sha256=checksum(prepared),
            norms=report["parameter_diagnostics"][arm], elapsed_seconds=.8)
        report["training_costs"][arm] = {key: value for key, value in prepared.items() if key not in ("items", "encoding", "epoch_order")}
        report["cells"][arm] = copy.deepcopy(panels)
        route = dict(name="real_record_memory_"+arm.lower(), id=1, path=plan["root"]+"/run/"+arm+"_fit/adapter")
        directory = "run/"+arm+"_readout/"
        files[directory+"identity.json"] = dict(arm=arm, route=route, model_files={}, parent=parent, params=plan["params"])
        files[directory+"readout.json"] = dict(arm=arm, calls=len(calls), updates=0)
        for call in calls:
            raw = next(row["raw"] for row in panels[call["panel"]] if row["row_id"] == call["row_id"])
            files[directory+call["call_id"]+".request.json"] = dict(call, params=plan["params"], lora_request=route)
            files[directory+call["call_id"]+".response.json"] = dict(call["native"], actual_prompt_token_ids=[1], output_token_ids=[2], text=raw,
                decoded_output=raw, finish_reason="stop", stop_reason=None, lora_request=route, started=0., ended=.5)
            complete["stages"][arm+"_readout"][call["call_id"]+".response.json"] = "e"*64
        indices = {panel: {row["row_id"]: row for row in rows} for panel, rows in panels.items()}
        report["screen"][arm] = analysis.screen(seed, indices, indices, utilities)
    report["best_constant"] = analysis.constants(dataset, calls, scorer, report["cells"], utilities) if replay_count else None
    return dict(entry=dict(seed=seed, root="/fixture/local"+str(seed), plan_sha256="c"*64, completion_sha256="d"*64),
        plan=plan, report=report, complete=complete, files=files)


class ReducerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.apis = analysis.load_apis("/tmp", SOURCE, PROTOCOL)
        cls.bundles = [bundle_fixture(cls.apis, seed) for seed in range(3)]

    def fixture(self):
        return copy.deepcopy(self.bundles[0])

    def test_three_pairs_full_work_and_unequal_memory_exposure(self):
        result = analysis.reduce_cohort(self.bundles, self.apis)
        self.assertEqual(result["totals"], dict(calls=480, updates=1632, fits=6))
        self.assertEqual([seed["arms"]["REPLAY"]["training"]["updates"] for seed in result["seeds"]], [304, 256, 256])
        for seed in result["seeds"]:
            self.assertTrue(seed["arms"]["REPLAY"]["screen"]["passed"])
            self.assertEqual(seed["paired_replay_minus_extra"]["exact"]["production_eligible"]["delta"], 0)
            self.assertGreater(seed["arms"]["EXTRA_MEMORY"]["training"]["per_kind"]["extra_memory"]["presentations"], 0)
        self.assertFalse(result["automatic_pass"])

    def test_zero_replay_retained_not_passed(self):
        empty = bundle_fixture(self.apis, 1, 0)
        result = analysis.reduce_cohort([self.bundles[0], empty, self.bundles[2]], self.apis)
        self.assertFalse(result["all_three_pairs_available"])
        self.assertEqual(result["seeds"][1]["arms"], {})
        self.assertIsNone(result["seeds"][1]["paired_replay_minus_extra"])
        self.assertIn("NOT ASSESSABLE", analysis.markdown(result))

    def test_cached_audit_scorer_matches_original_api(self):
        bundle = self.bundles[0]
        files = bundle["files"]
        scorer = analysis.FrozenScorer(files["memory/capture.json"], files["memory/dataset.json"], files["memory/retention.json"], self.apis)
        for panel in ("exact", "paraphrase"):
            call = next(call for call in files["calls.json"] if call["panel"] == panel)
            for raw in (scorer.rows[call["row_id"]]["raw_target"], "{}", "```json\n{}\n```", "é"):
                expected = self.apis["memory"].score_readback(files["memory/capture.json"], call["row_id"], raw, "stop",
                    input_messages=call["messages"], variant=panel, core_path="/tmp/"+analysis.PINS["formation"][0], source_root=SOURCE)
                self.assertEqual(scorer(panel, call["row_id"], raw, "stop", call["messages"]), expected)

    def test_missing_duplicate_seed(self):
        for bundles in (self.bundles[:2], [self.bundles[0]]*3):
            with self.assertRaises(ValueError):
                analysis.reduce_cohort(bundles, self.apis)

    def test_missing_stage_or_panel(self):
        for kind in ("stage", "panel"):
            bundle = self.fixture()
            if kind == "stage":
                del bundle["complete"]["stages"]["REPLAY_fit"]
            else:
                del bundle["report"]["cells"]["REPLAY"]["held"]
            with self.assertRaises(ValueError):
                analysis.reduce_seed(bundle, self.apis)

    def test_raw_scorer_disagreement_rejected(self):
        bundle = self.fixture()
        bundle["report"]["cells"]["REPLAY"]["held"][0]["score"]["strict"] = False
        with self.assertRaises(ValueError):
            analysis.reduce_seed(bundle, self.apis)

    def test_native_prefix_route_and_raw_mismatch(self):
        for field, value in (("actual_prompt_token_ids", [99]), ("lora_request", {}), ("text", "changed")):
            bundle = self.fixture()
            call = bundle["files"]["calls.json"][0]
            bundle["files"]["run/REPLAY_readout/"+call["call_id"]+".response.json"][field] = value
            with self.assertRaises(ValueError):
                analysis.reduce_seed(bundle, self.apis)

    def test_bool_nan_and_unchanged_fit_rejected(self):
        for field, value in (("steps", True), ("final_loss", float("nan"))):
            bundle = self.fixture()
            bundle["report"]["fits"]["REPLAY"][field] = value
            with self.assertRaises(ValueError):
                analysis.reduce_seed(bundle, self.apis)
        bundle = self.fixture()
        bundle["report"]["parameter_diagnostics"]["REPLAY"]["changed_elements"] = 0
        with self.assertRaises(ValueError):
            analysis.reduce_seed(bundle, self.apis)

    def test_loss_not_offset_by_gain_and_floors(self):
        utilities = self.apis["utilities"]
        baseline = {panel: {row["row_id"]: copy.deepcopy(row) for row in rows} for panel, rows in self.bundles[0]["report"]["cells"]["REPLAY"].items()}
        current = copy.deepcopy(baseline)
        held_ids = list(baseline["held"])
        baseline["held"][held_ids[0]]["score"]["passed"] = False
        current["held"][held_ids[1]]["score"]["passed"] = False
        result = analysis.screen(0, current, baseline, utilities)
        self.assertFalse(result["passed"])
        self.assertEqual(result["lr0_correct_regressions"]["held"], [held_ids[1]])
        for seed in range(3):
            self.assertEqual(analysis.screen(seed, current, baseline, utilities)["threshold"], analysis.FLOORS[seed])

    def test_lineage_raw_rewrite_and_cost_disagreement(self):
        for field in ("raw_target", "cost"):
            bundle = self.fixture()
            if field == "raw_target":
                bundle["files"]["mixture.json"]["replay_rows"][0][field] += " "
            else:
                bundle["report"]["training_costs"]["REPLAY"]["total_tokens"] += 1
            with self.assertRaises(ValueError):
                analysis.reduce_seed(bundle, self.apis)

    def test_replay_source_wrong_producer_or_repaired_output(self):
        for field in ("producer", "raw"):
            bundle = self.fixture()
            admission = bundle["files"]["capture/admission.json"]
            if field == "producer":
                admission["producer"]["learner_seed"] = 2
            else:
                admission["responses"][0]["response"]["raw"] += " "
            with self.assertRaises(ValueError):
                analysis.reduce_seed(bundle, self.apis)

    def test_constant_is_evaluator_only_and_recomputed(self):
        result = analysis.reduce_seed(self.bundles[0], self.apis)
        self.assertIn("not native execution", result["best_constant"]["scope"])
        bundle = self.fixture()
        bundle["report"]["best_constant"]["variants"]["exact"]["oracle_best_content_correct"] += 1
        with self.assertRaises(ValueError):
            analysis.reduce_seed(bundle, self.apis)

    def test_missing_historical_lr0_rejected(self):
        bundle = self.fixture()
        del bundle["report"]["historical_cells"]["LR0"]
        with self.assertRaises((ValueError, KeyError)):
            analysis.reduce_seed(bundle, self.apis)

    def test_strict_json_pin_and_write_once(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)/"input.json"
            for raw in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":1e999}'):
                path.write_text(raw)
                with self.assertRaises(ValueError):
                    analysis.read(path)
            path.write_text('{"schema":"'+analysis.INPUT_SCHEMA+'","seeds":[]}')
            with self.assertRaises(ValueError):
                analysis.pin(path, "0"*64)
            with self.assertRaisesRegex(ValueError, "fresh write-once"):
                analysis.run(path, analysis.digest(path), temporary, "/tmp", SOURCE, PROTOCOL)


if __name__ == "__main__":
    unittest.main()
