"""Synthetic scored receipts only; no native/model/tokenizer execution."""
import ast
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

import astra_actual_memory_analysis_20260913 as analysis


def text_hash(value):
    return hashlib.sha256(value.encode()).hexdigest()


def retention_row(seed, panel, index, passed=True, strict=True):
    raw = '{"ok":true}' if passed else '{"ok":false}'
    if passed and not strict:
        raw = ' {"ok":true} '
    score = dict(passed=passed, content_correct=passed, strict=passed and strict, raw=raw,
                 finish_reason="stop", raw_sha256=text_hash(raw), format="exact" if strict else "json_noncanonical",
                 source_errors=[] if passed else ["content"], syntax_errors=[], schema_errors=[], completion_errors=[])
    return dict(row_id=f"synthetic:{seed}:{panel}:{index}", raw=raw, finish_reason="stop", score=score,
                response_sha256="1" * 64, cost=dict(prompt_tokens=10, output_tokens=5, generation_seconds=.25))


def memory_row(seed, panel, index, passed):
    task, tick = f"real-record-dev-{index // 2:020x}", index % 2 + 1
    public = f"{task}#t{tick}"
    row_id = f"perception_seed{seed}:{public}"
    target = '{"observed":true,"predicted":true,"relation":"matched","try":[1,2,3]}'
    raw = target if passed else "invalid"
    source = dict(state=f"perception_seed{seed}", task_id=task, tick=tick, public_execution_id=public,
                  execution_id=row_id, capture_sha256=analysis.CAPTURE_PINS[seed],
                  execution_sha256="2" * 64, wake_request_id="3" * 64,
                  record_request_id="4" * 64, record_event_sha256="5" * 64)
    score = dict(production_eligible=passed, content_correct=passed, strict_canonical=passed, raw=raw,
                 finish_reason="stop", field_correct={field: passed for field in analysis.FIELDS},
                 format="exact" if passed else "unparseable", production_errors=[] if passed else ["JSON"],
                 content_errors=[] if passed else ["JSON"], source_completion_errors=[])
    outer = dict(compiler=analysis.COMPILER, row_id=row_id, source=source, target_sha256=text_hash(target),
                 variant=panel, endpoint="exact_cue_acquisition_persistence" if panel == "exact" else "paraphrase_transfer",
                 score=score, exact_target_bytes=passed, native_identity_verified=False)
    return dict(row_id=row_id, raw=raw, finish_reason="stop", score=outer,
                response_sha256="6" * 64, cost=dict(prompt_tokens=20, output_tokens=10, generation_seconds=.5))


def native_summary(report, original):
    source = Path(analysis.RUNNER_PATH).read_bytes()
    assert hashlib.sha256(source).hexdigest() == analysis.RUNNER_PIN
    nodes = [node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef) and
             node.name in ("paired_counts", "summarize")]
    namespace = dict(require=analysis.require, ARMS=analysis.ARMS, Counter=Counter, Path=Path,
                     read=lambda path: original, digest=lambda path: report["parent"]["scores_sha256"])
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "frozen_summary_fixture", "exec"), namespace)
    bound = dict(parent=report["parent"], retention=dict(evaluation={panel: original["cells"]["post"][panel]["rows"]
                 for panel in analysis.RETENTION_PANELS}), material=SimpleNamespace(score_row=lambda row, raw, finish: row["score"]))
    return namespace["summarize"](report["cells"], bound)


def fixture(seed=0):
    size = analysis.ADMISSIONS[seed]
    parent = dict(adapter="/synthetic/parent", adapter_files={"adapter_model.safetensors": "a" * 64},
                  collection=dict(path="/synthetic/original/collection.json", sha256="b" * 64),
                  scores_sha256="c" * 64, plan_sha256="d" * 64, completion_sha256="e" * 64)
    formation = dict(root="/synthetic/formation", plan_sha256=analysis.FORMATION_PLAN,
                     completion_sha256=analysis.FORMATION_COMPLETE,
                     collection=dict(path="/synthetic/formation/collection.json", sha256=analysis.FORMATION_COLLECTION))
    specification = dict(seed=seed, fit_seed=seed, runner_sha256=analysis.RUNNER_PIN,
                         memory=dict(sha256=analysis.MEMORY_PIN), formation_runtime=dict(sha256=analysis.FORMATION_RUNTIME_PIN),
                         protocol=dict(sha256=analysis.PROTOCOL_PIN), formation=formation)
    configs = {arm: dict(seed=seed, rank=8, alpha=16, dropout=.05, epochs=8, batch_size=1,
                        lr=1e-4 if arm == "WRITE" else 0.0, model="/synthetic/model") for arm in analysis.ARMS}
    plan = dict(scope=analysis.SCOPE, status="WRITE_AVAILABLE", self_sha256=analysis.RUNNER_PIN,
                specification=specification, configs=configs, parent=parent, model="/synthetic/model",
                calls_per_arm=2 * size + 60, updates_per_arm=8 * size)
    original = dict(scope="authored_level1_skill_96train_320steps_120calls_v1", skill="perception", learner_seed=seed,
                    plan_sha256=parent["plan_sha256"], completion_sha256=parent["completion_sha256"], cells=dict(post={}))
    for panel, count in (("held", 48), ("canary", 12)):
        original["cells"]["post"][panel] = dict(rows=[retention_row(seed, panel, index) for index in range(count)],
                                               total=count, passed=count, content_correct=count, strict=count)
    training = dict(fit_seed=seed, rows=size, updates=8 * size, presentations=8 * size, padding_tokens=0,
                    total_tokens=30 * size, target_tokens=10 * size, context_tokens=20 * size,
                    train_tokens_seen=240 * size, actual_supervised_tokens=80 * size,
                    actual_context_tokens=160 * size, actual_padded_tokens=240 * size)
    report = dict(scope=analysis.SCOPE, status="WRITE_AVAILABLE", seed=seed, plan_sha256="f" * 64,
                  completion_sha256="7" * 64, parent=parent, formation=formation,
                  native_capture_custody_checked=True, automatic_pass=False, scientific_pass=None,
                  memory_scored_denominator=size, memory_possible_denominator_per_variant=16,
                  retention_denominators=dict(held=48, canary=12), counts=dict(admitted_rows=size, possible_slots=16,
                  refused_slots=16-size, distinct_raw_targets=1, distinct_triples=1, episodes_with_admissions=size // 2),
                  refused=[{} for index in range(16-size)], calls=2*(2*size+60), updates=16*size,
                  cells={}, fits={}, parameter_diagnostics={}, training_costs=training)
    for arm in analysis.ARMS:
        panels = {panel: [memory_row(seed, panel, index, arm == "WRITE" and index == 0) for index in range(size)]
                  for panel in analysis.MEMORY_PANELS}
        panels["held"] = [retention_row(seed, "held", index, passed=not (arm == "WRITE" and index == 0),
                                       strict=not (arm == "WRITE" and index == 1)) for index in range(48)]
        panels["canary"] = [retention_row(seed, "canary", index) for index in range(12)]
        report["cells"][arm] = panels
        state = {"base.model.layer.lora_A.weight": dict(shape=[2, 2], dtype="torch.float32", sha256="8" * 64)}
        final = copy.deepcopy(state)
        if arm == "WRITE":
            final["base.model.layer.lora_A.weight"]["sha256"] = "9" * 64
        warm = dict(mode="WEIGHT_WARM_START_FRESH_OPTIMIZER", optimizer_initialization="fresh_per_write",
                    optimizer_state_restored=False, optimizer_state_saved=False, parent_path=parent["adapter"],
                    parent_files=parent["adapter_files"], parent_files_after=parent["adapter_files"], parent_unchanged=True,
                    initialized_loaded_state_check=True, base_frozen=True, adapter_count=1, trainer_sha256=analysis.TRAINER_PIN,
                    phase_seed=seed, phase_steps=8*size, cumulative_steps=320+8*size, parent_cumulative_steps=320,
                    source_state=state, initialized_state=state, final_state=final,
                    trainable_names=["base.model.layer.lora_A.default.weight"])
        report["fits"][arm] = dict(config=configs[arm], empty=False, steps=8*size, micro_batches=8*size,
            epochs_run=8, nonfinite_batches=0, corpus=dict(n_items=size, n_encoded=size, n_skipped_no_target=0),
            truncation=dict(items_truncated=0, context_tokens_dropped=0, target_tokens_dropped=0, items_split=0),
            packing=dict(mode="one_item_per_sequence", n_sequences=size), tokens=dict(target=10*size, total=30*size),
            train_tokens_seen=240*size, mean_loss_per_epoch=[.2]*8, final_loss=.1, warm_start=warm, train_seconds=1., wall_seconds=2.)
        report["parameter_diagnostics"][arm] = dict(changed_elements=1 if arm == "WRITE" else 0,
            l2=dict(initial=1., final=1., delta=.1 if arm == "WRITE" else 0.))
    report["summary"] = native_summary(report, original)
    entry = dict(seed=seed, plan=dict(path="/synthetic/plan.json", sha256=report["plan_sha256"]),
                 scores=dict(path="/synthetic/scores.json", sha256="1" * 64),
                 collection=dict(path="/synthetic/collection.json", sha256="2" * 64),
                 original_retention=dict(path="/synthetic/original.json", sha256=parent["scores_sha256"]))
    return report, plan, original, entry


class AnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = staticmethod(analysis.load_fit_validator())

    def reduce(self, values):
        return analysis.reduce_seed(*values, self.validator)

    def test_all_three_denominators_and_native_summary_reproduction(self):
        for seed in range(3):
            result = self.reduce(fixture(seed))
            self.assertEqual(result["admitted_records"], (14, 8, 8)[seed])
            self.assertTrue(result["reported_summary_reproduced"])
            self.assertEqual(result["paired_WRITE_LR0"]["exact"]["production_eligible"]["counts"]["first_only"], 1)
            self.assertEqual(result["original_retention"]["WRITE"]["held"]["content_regressed"], 1)
            self.assertEqual(result["original_retention"]["WRITE"]["held"]["strict_regressed"], 2)
            self.assertEqual(result["original_retention"]["WRITE"]["held"]["raw_changed"], 2)

    def test_booleans_cannot_substitute_counts_or_scores(self):
        for location in ("score", "calls", "tensor", "warm"):
            values = fixture()
            report = values[0]
            if location == "score":
                report["cells"]["WRITE"]["exact"][0]["score"]["score"]["content_correct"] = 1
            elif location == "calls":
                report["calls"] = True
            elif location == "tensor":
                report["parameter_diagnostics"]["WRITE"]["changed_elements"] = True
            else:
                report["fits"]["WRITE"]["warm_start"]["adapter_count"] = True
            with self.subTest(location=location), self.assertRaises(ValueError):
                self.reduce(values)

    def test_finite_changed_vs_equal_tensor_checks(self):
        for arm, field, value in (("WRITE", "delta", 0.), ("LR0", "delta", .1), ("WRITE", "initial", float("nan"))):
            values = fixture()
            values[0]["parameter_diagnostics"][arm]["l2"][field] = value
            with self.subTest(arm=arm, field=field), self.assertRaises(ValueError):
                self.reduce(values)

    def test_missing_duplicate_cell_wrong_source_and_seed(self):
        for change in ("missing", "duplicate", "source", "seed", "pin"):
            values = fixture()
            report, plan, original, entry = values
            if change == "missing":
                report["cells"]["WRITE"]["exact"].pop()
            elif change == "duplicate":
                report["cells"]["LR0"]["held"][1] = copy.deepcopy(report["cells"]["LR0"]["held"][0])
            elif change == "source":
                report["cells"]["WRITE"]["exact"][0]["score"]["source"]["capture_sha256"] = "a" * 64
            elif change == "seed":
                report["seed"] = 1
            else:
                plan["specification"]["memory"]["sha256"] = "a" * 64
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.reduce(values)

    def test_summary_tamper_and_original_retention_mismatch_rejected(self):
        for section in ("totals", "paired", "retention", "original"):
            values = fixture()
            report, plan, original, entry = values
            if section == "totals":
                report["summary"]["totals"]["WRITE"]["exact"]["numerators"]["production_eligible"] += 1
            elif section == "paired":
                report["summary"]["paired_WRITE_LR0"]["held"]["passed"]["first_only"] += 1
            elif section == "retention":
                report["summary"]["original_retention"]["WRITE"]["held"]["regressed"] = []
            else:
                original["cells"]["post"]["held"]["strict"] -= 1
            with self.subTest(section=section), self.assertRaises(ValueError):
                self.reduce(values)

    def test_exact_byte_and_nested_raw_disagreements_rejected(self):
        values = fixture()
        values[0]["cells"]["WRITE"]["exact"][0]["score"]["exact_target_bytes"] = False
        with self.assertRaises(ValueError):
            self.reduce(values)
        values = fixture()
        values[0]["cells"]["WRITE"]["held"][0]["score"]["raw"] = "different"
        with self.assertRaises(ValueError):
            self.reduce(values)

    def test_training_token_and_cost_disagreements_rejected(self):
        values = fixture()
        values[0]["training_costs"]["actual_supervised_tokens"] += 1
        with self.assertRaises(ValueError):
            self.reduce(values)
        values = fixture()
        values[0]["cells"]["WRITE"]["held"][0]["cost"]["generation_seconds"] = -1
        with self.assertRaises(ValueError):
            self.reduce(values)

    def test_missing_or_duplicate_seed_manifest_rejected(self):
        for entries in ([], [{"seed": 0}, {"seed": 0}, {"seed": 2}], [{"seed": False}, {"seed": 1}, {"seed": 2}]):
            with self.assertRaises(ValueError):
                analysis.analyze_manifest(dict(schema=analysis.INPUT_SCHEMA, seeds=entries))

    def test_json_duplicate_nonfinite_and_pin_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            for text in ('{"key":1,"key":2}', '{"key":NaN}', '{"key":1e999}'):
                path.write_text(text)
                with self.assertRaises(ValueError):
                    analysis.read(path)
            path.write_text('{}')
            with self.assertRaises(ValueError):
                analysis.pinned(dict(path=str(path), sha256="0" * 64))

    def test_full_local_json_markdown_and_writeonce(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            entries = []
            def save(name, value):
                path = base / name
                path.write_text(analysis.canonical(value))
                return dict(path=str(path), sha256=analysis.digest(path))
            for seed in range(3):
                report, plan, original, entry = fixture(seed)
                entry["original_retention"] = save(f"old{seed}.json", original)
                plan["parent"]["scores_sha256"] = entry["original_retention"]["sha256"]
                entry["plan"] = save(f"plan{seed}.json", plan)
                report["plan_sha256"] = entry["plan"]["sha256"]
                report["summary"] = native_summary(report, original)
                entry["scores"] = save(f"scores{seed}.json", report)
                entry["collection"] = save(f"collection{seed}.json", dict(scores_sha256=entry["scores"]["sha256"], completion_sha256=report["completion_sha256"]))
                entries.append(entry)
            manifest = save("manifest.json", dict(schema=analysis.INPUT_SCHEMA, seeds=entries))
            result = analysis.run(manifest["path"], manifest["sha256"], base / "result")
            self.assertTrue((Path(result["output"]) / "analysis.md").is_file())
            report = analysis.read(Path(result["output"]) / "analysis.json")
            self.assertEqual(report["accounting_only"], dict(calls=480, updates=480))
            self.assertFalse(report["automatic_pass"])
            self.assertIsNone(report["scientific_pass"])
            self.assertEqual([row["seed"] for row in report["seeds"]], [0, 1, 2])
            with self.assertRaises(ValueError):
                analysis.run(manifest["path"], manifest["sha256"], base / "result")


if __name__ == "__main__":
    unittest.main()
