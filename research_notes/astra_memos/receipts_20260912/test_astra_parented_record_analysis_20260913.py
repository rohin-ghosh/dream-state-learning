import copy
import importlib.util
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
SPEC = importlib.util.spec_from_file_location("analysis", "/tmp/astra_parented_record_analysis_20260913.py")
analysis = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(analysis)
ROOT = "/data/home/rohing/dream-state"


def checksum(value):
    return analysis.sha(analysis.canonical(value).encode())


def native(messages, text, route):
    rendered = "SYSTEM\n" + "\n".join(message["content"] for message in messages)
    source = dict(rendered_prompt=rendered, prompt_token_ids=[1, 2, 3],
                  actual_system_text="SYSTEM", actual_system_segment="SYSTEM\n")
    response = dict(source, actual_prompt_token_ids=[1, 2, 3], text=text, decoded_output=text,
                    output_token_ids=[4, 5], finish_reason="stop", stop_reason=None,
                    started=1.0, ended=1.25, lora_request=route)
    return source, response


def fixture(core, dependencies, seed=0, admissions=None):
    admissions = admissions or dict(P=16, N=8)
    original = dict(name="parented_original", id=1, path="/synthetic/original")
    plan = dict(root=f"/synthetic/seed{seed}", seed=seed, self_sha256=analysis.RUNNER_PIN,
                specification=dict(core=dict(path=analysis.CORE_PATH, sha256=analysis.CORE_PIN),
                                   protocol=dict(path="/synthetic/protocol", sha256=analysis.PROTOCOL_PIN)),
                config=dict(lr=3e-5, epochs=8, batch_size=1, seed=seed, max_steps=0, rank=8, alpha=16, dropout=.05),
                parent=dict(adapter=original["path"], adapter_files={"adapter_model.safetensors": "a" * 64}, scores_sha256="b" * 64),
                manifest=core.build_manifest(dependencies), model_files={"model.safetensors": "c" * 64},
                historical_retention=dict(path="/synthetic/old/scores.json", sha256="b" * 64, noncontemporaneous=True))
    stages, captures, costs, materials, fits = {}, {}, {}, {}, {}
    plan_pin = checksum(plan)

    def initialize(stage, route, state):
        owner = dict(pid=100 + len(stages), start_ticks=1000 + len(stages))
        documents = {
            "launch.json": dict(identity=owner, stage=stage, plan_sha256=plan_pin),
            "started.json": dict(identity=owner, stage=stage, plan_sha256=plan_pin),
            "worker_done.json": dict(stage=stage, plan_sha256=plan_pin),
            "exit.json": dict(identity=owner, returncode=0),
            "released.json": dict(identity=owner, stage=stage, group_absent=True, gpu_vacant=True),
            "identity.json": dict(stage=stage, state=state, route=route, core=plan["specification"]["core"],
                                  parent=plan["parent"], model_files=plan["model_files"]),
        }
        stages[stage] = documents
        return documents

    for stage in analysis.CAPTURE_STAGES:
        arm, phase = stage.split("_")
        state = f"perception_seed{seed}_{'INITIAL' if arm == 'ORIGINAL' else arm}"
        route = original if phase == "formation" or arm == "ORIGINAL" or admissions[arm] == 0 else dict(
            name="real_record_memory_write", id=1, path=plan["root"] + f"/arms/{arm}/run/WRITE_fit/adapter")
        documents = initialize(stage, route, state)
        requests = []
        selected = [0]
        def backend(request):
            if request["split"] != "dev":
                raise AssertionError("confirmation fixture forbidden")
            if request["kind"] == "wake":
                raw = "PREDICT: F\nACT: TRY 3,7,11"
            elif request["kind"] == "restate":
                raw = "I acknowledge the session contact."
            else:
                facts = json.loads(re.findall(r"^Observed fields: (.+)$", request["input_messages"][0]["content"], re.M)[-1])
                passed = True
                if phase == "formation" and request["stage"] == "apply":
                    passed = selected[0] < admissions[arm]
                    selected[0] += 1
                prior = facts["predicted"] if passed else None
                raw = analysis.canonical(dict(observed=facts["observed"], predicted=prior,
                    relation="unavailable" if prior is None else "matched" if prior == facts["observed"] else "mismatched",
                    **{"try": facts["values"]}))
            source, response = native(request["input_messages"], raw, route)
            index = len(requests)
            full = dict(call_id=f"{index:02d}", core_request=request, messages=request["input_messages"], native=source,
                        params=dict(max_tokens=request["max_output_tokens"]), lora_request=route)
            requests.append(full)
            documents[f"{index:02d}.request.json"] = full
            documents[f"{index:02d}.response.json"] = response
            return dict(request_id=request["request_id"], state=request["state"], raw=raw, finish_reason="stop", native_response=response)
        capture = core.run_state(state, backend, phase=phase, dependencies=dependencies, binding=documents["identity.json"])
        captures[stage] = capture
        documents["capture.json"] = capture
        count = len(requests)
        cost = dict(calls=count, updates=0, prompt_tokens=3 * count, output_tokens=2 * count, generation_seconds=.25 * count,
                    contact_tokens_per_literal=dict(P=51, N=29) if phase == "formation" else {})
        documents["cost.json"] = cost
        costs[stage] = cost

    history = dict(cells=dict(post={}))
    retained = {}
    for panel, total in (("held", 48), ("canary", 12)):
        history["cells"]["post"][panel] = dict(rows=[dict(row_id=f"{panel}-{index}", raw="right", finish_reason="stop",
            score=dict(content_correct=True, strict=True, format="exact")) for index in range(total)])
    for arm in analysis.ARMS:
        dataset = core.project_capture(captures[arm + "_formation"], dependencies=dependencies)
        materials[arm] = dataset
        documents = dict(**{"dataset.json": dataset, "capture.json": captures[arm + "_formation"]})
        stages[arm + "_material"] = documents
        admitted = len(dataset["rows"])
        if admitted:
            dose = dict(rows=admitted, updates=8 * admitted, presentations=8 * admitted, fit_seed=seed,
                target_tokens=10 * admitted, context_tokens=20 * admitted, total_tokens=30 * admitted,
                actual_supervised_tokens=80 * admitted, actual_context_tokens=160 * admitted,
                actual_padded_tokens=240 * admitted, padding_tokens=0, train_tokens_seen=240 * admitted)
            documents["training.json"] = dose
            documents["prepared.json"] = {name: checksum(documents[name]) for name in ("training.json", "dataset.json", "capture.json")}
            fit = dict(status="WRITE", updates=8 * admitted, fits=1, dose=dose, source_state={"tensor": "original"}, initialized_state={"tensor": "initial"})
            fits[arm] = fit
            stage = arm + "_fit"
            target = initialize(stage, {}, "unused_fit_state")
            target["adapter/train_manifest.json"] = dict(warm_start=dict(source_state=fit["source_state"], initialized_state=fit["initialized_state"], final_state={"tensor": arm + "_written"}))
        else:
            fits[arm] = dict(status="NO_WRITE", updates=0, fits=0)
            documents["no_write.json"] = dict(status="NO_WRITE", calls=0, fits=0, updates=0, parent=plan["parent"], dataset_sha256=checksum(dataset))
        stage = arm + "_retention"
        route = captures[arm + "_held"]["binding"]["route"]
        documents = initialize(stage, route, f"perception_seed{seed}_{arm}")
        cells, contrasts = {}, {}
        for panel, total in (("held", 48), ("canary", 12)):
            cells[panel] = []
            for index in range(total):
                correct = not (arm == "P" and panel == "held" and index == 0)
                raw = "right" if correct else "wrong"
                messages = [dict(role="user", content=f"{panel}-{index}")]
                source, response = native(messages, raw, route)
                name = f"{panel}_{index:02d}"
                documents[name + ".request.json"] = dict(call_id=name, row_id=f"{panel}-{index}", messages=messages,
                    native=source, params=dict(max_tokens=192), lora_request=route)
                documents[name + ".response.json"] = response
                cells[panel].append(dict(row_id=f"{panel}-{index}", raw=raw, finish_reason="stop", response_sha256=checksum(response),
                    score=dict(content_correct=correct, strict=correct, format="exact")))
            contrasts[panel] = {metric: dict(gains=[], losses=[row["row_id"] for row in cells[panel] if not row["score"][metric]]) for metric in ("content_correct", "strict")}
        retained[arm] = dict(cells=cells, versus_original=contrasts, exploratory=True, noncontemporaneous_original=True)
        cost = dict(calls=60, updates=0, prompt_tokens=180, output_tokens=120, generation_seconds=15.0, contact_tokens_per_literal={})
        documents["cost.json"] = cost
        costs[stage] = cost
    novelty = {}
    for arm in analysis.ARMS:
        novelty[arm] = dict(held_executions=16, distinct_held_triples=1, held_executions_with_unseen_apply_triple=0,
                           same_initial_tasks_not_same_experience=True, new_ids_not_unseen_rules_or_base_knowledge=True)
    report = dict(scope=analysis.SCOPE, seed=seed, plan_sha256=plan_pin, completion_sha256="d" * 64,
        formation=core.compare_states([captures[arm + "_formation"] for arm in analysis.ARMS], dependencies=dependencies),
        held=core.compare_states([captures[arm + "_held"] for arm in ("ORIGINAL", *analysis.ARMS)], dependencies=dependencies),
        retention=retained, historical_original=plan["historical_retention"], material=materials,
        source_novelty=novelty, costs=costs, fits=fits, calls=sum(cost["calls"] for cost in costs.values()),
        updates=sum(fit["updates"] for fit in fits.values()), automatic_pass=False, scientific_pass=None, outcome_gate=None,
        held_vs_initial={arm: {metric: 0 for metric in analysis.METRICS} for arm in analysis.ARMS})
    complete = dict(plan_sha256=plan_pin, inventory={stage: {name: checksum(value) for name, value in documents.items()} for stage, documents in stages.items()},
                    calls=report["calls"], updates=report["updates"], fits=sum(fit["fits"] for fit in fits.values()), automatic_pass=False, elapsed_seconds=100.0)
    return dict(seed=seed, report=report, plan=plan, complete=complete, history=history, stages=stages, captures=captures)


class AnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.core, cls.dependencies = analysis.load_core(ROOT)
        cls.bundle = fixture(cls.core, cls.dependencies)

    def reduce(self, bundle):
        return analysis.reduce_bundle(bundle, self.core, self.dependencies)

    def test_unequal_admissions_and_doses_are_kept(self):
        report = self.reduce(copy.deepcopy(self.bundle))
        self.assertEqual(report["arms"]["P"]["dose"]["updates"], 128)
        self.assertEqual(report["arms"]["N"]["dose"]["updates"], 64)
        self.assertEqual(report["totals"]["calls"], 300)
        self.assertEqual(report["arms"]["P"]["retention"]["held"]["metrics"]["content_correct"]["losses"], ["held-0"])

    def test_empty_arms_require_no_write_not_missing_assessment(self):
        bundle = fixture(self.core, self.dependencies, admissions=dict(P=0, N=0))
        report = self.reduce(bundle)
        self.assertEqual(report["totals"]["fits"], 0)
        self.assertEqual(report["totals"]["updates"], 0)
        self.assertEqual(report["summaries"]["ORIGINAL_held"]["possible"], 16)
        self.assertEqual(report["arms"]["P"]["status"], "NO_WRITE")

    def test_missing_held_or_retention_stage_rejected(self):
        for stage in ("ORIGINAL_held", "P_retention"):
            bundle = copy.deepcopy(self.bundle)
            del bundle["stages"][stage]
            with self.subTest(stage=stage), self.assertRaises(ValueError):
                self.reduce(bundle)

    def test_missing_fit_not_silently_no_write(self):
        bundle = copy.deepcopy(self.bundle)
        del bundle["stages"]["P_fit"]
        with self.assertRaises(ValueError):
            self.reduce(bundle)

    def test_three_seeds_required_no_winner_selection(self):
        bundles = [fixture(self.core, self.dependencies, seed=seed) for seed in range(3)]
        report = analysis.reduce_cohort(bundles, self.core, self.dependencies)
        self.assertEqual(report["paired_learners"], 3)
        self.assertFalse(report["automatic_pass"])
        for bad in (bundles[:2], [bundles[0], bundles[0], bundles[2]]):
            with self.assertRaises(ValueError):
                analysis.reduce_cohort(bad, self.core, self.dependencies)

    def test_source_admission_mismatch_rejected(self):
        bundle = copy.deepcopy(self.bundle)
        bundle["report"]["material"]["P"]["rows"].pop()
        with self.assertRaises(ValueError):
            self.reduce(bundle)

    def test_protocol_pin_mismatch_rejected(self):
        bundle = copy.deepcopy(self.bundle)
        bundle["plan"]["specification"]["protocol"]["sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            self.reduce(bundle)

    def test_failed_release_and_reused_worker_rejected(self):
        bundle = copy.deepcopy(self.bundle)
        bundle["stages"]["P_held"]["released.json"]["gpu_vacant"] = False
        with self.assertRaises(ValueError):
            self.reduce(bundle)

    def test_native_parent_prompt_insertion_rejected(self):
        bundle = copy.deepcopy(self.bundle)
        bundle["stages"]["P_held"]["00.request.json"]["messages"] = [dict(role="user", content=self.core.CONTACTS["P"])]
        with self.assertRaises(ValueError):
            self.reduce(bundle)

    def test_retention_loss_and_row_denominator_mismatch(self):
        for mutation in ("loss", "row"):
            bundle = copy.deepcopy(self.bundle)
            if mutation == "loss":
                bundle["report"]["retention"]["P"]["versus_original"]["held"]["content_correct"]["losses"] = []
            else:
                bundle["report"]["retention"]["P"]["cells"]["held"].pop()
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                self.reduce(bundle)

    def test_nonfinite_bool_and_duplicate_json_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            for raw in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":1e999}'):
                path.write_text(raw)
                with self.assertRaises(ValueError):
                    analysis.read(path)
            path.write_text('{}')
            with self.assertRaises(ValueError):
                analysis.read(path, '0' * 64)
        bundle = copy.deepcopy(self.bundle)
        bundle["report"]["costs"]["P_formation"]["updates"] = False
        with self.assertRaises(ValueError):
            self.reduce(bundle)

    def test_wrong_eight_pass_dose_rejected(self):
        bundle = copy.deepcopy(self.bundle)
        bundle["report"]["fits"]["N"]["updates"] = 128
        with self.assertRaises(ValueError):
            self.reduce(bundle)

    def test_retention_response_pin_mismatch(self):
        bundle = copy.deepcopy(self.bundle)
        bundle["report"]["retention"]["P"]["cells"]["held"][0]["response_sha256"] = "f" * 64
        with self.assertRaises(ValueError):
            self.reduce(bundle)


if __name__ == "__main__":
    unittest.main()
