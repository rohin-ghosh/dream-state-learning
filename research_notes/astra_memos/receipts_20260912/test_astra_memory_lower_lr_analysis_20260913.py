"""Synthetic CPU result-reducer fixtures, not native observations."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("lower_lr_analysis_test", "/tmp/astra_memory_lower_lr_analysis_20260913.py")
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)
runner, memory = analysis.load_helpers()


def sha(value):
    return hashlib.sha256(value.encode()).hexdigest()


def row(panel, index, passed, seed):
    is_memory = panel in ("exact", "paraphrase")
    row_id = f"seed{seed}:{'record' if is_memory else panel}:{index:02d}"
    raw = f"CPU fixture {panel} {index} {passed}"
    body = dict(raw=raw, finish_reason="stop", format="exact" if passed else "unparseable",
                content_correct=passed, field_correct={field: passed for field in analysis.FIELDS} if is_memory else {})
    if is_memory:
        body.update(production_eligible=passed, strict_canonical=passed)
        score = dict(row_id=row_id, variant=panel, exact_target_bytes=passed, score=body,
                     source=dict(execution_id=row_id, capture_sha256=sha(str(seed))), target_sha256=sha(row_id))
    else:
        body.update(passed=passed, strict=passed)
        score = body
    return dict(row_id=row_id, raw=raw, finish_reason="stop", response_sha256=sha(raw), score=score,
                cost=dict(prompt_tokens=10, output_tokens=5, generation_seconds=.25))


def update_comparisons(candidate, historical):
    for endpoint, arm in (("LR0", "LR0"), ("HIGH", "WRITE")):
        first, second = candidate["cells"]["WRITE"], historical["cells"][arm]
        candidate["comparisons"]["candidate_vs_historical_" + endpoint] = dict(
            totals={name: {panel: analysis.panel_summary(cells[panel], panel) for panel in analysis.PANELS}
                    for name, cells in (("WRITE", first), ("LR0", second))},
            paired_WRITE_LR0={panel: {metric: memory.paired_counts(analysis.outcomes(first[panel], panel, metric),
                analysis.outcomes(second[panel], panel, metric)) for metric in analysis.metrics(panel)} for panel in analysis.PANELS})
    candidate["strict_exploratory_repair_screen"] = runner.repair_screen(candidate["seed"], candidate["comparisons"]["candidate_vs_historical_LR0"])


def fixture(seed=0):
    count, threshold = (14, 8, 8)[seed], (8, 7, 5)[seed]
    counts = dict(exact=count, paraphrase=count, held=48, canary=12)
    high = {panel: [row(panel, index, index < threshold if panel in ("exact", "paraphrase") else index != 0, seed)
                    for index in range(size)] for panel, size in counts.items()}
    lr0 = {panel: [row(panel, index, panel in ("held", "canary"), seed) for index in range(size)] for panel, size in counts.items()}
    lower = {panel: [row(panel, index, index < threshold if panel in ("exact", "paraphrase") else True, seed)
                     for index in range(size)] for panel, size in counts.items()}
    training = dict(fit_seed=seed, rows=count, updates=8 * count, presentations=8 * count,
                    actual_context_tokens=count * 80, actual_supervised_tokens=count * 40,
                    actual_padded_tokens=count * 120, train_tokens_seen=count * 120)
    config = dict(lr=1e-4, seed=seed, rank=8, alpha=16, dropout=.05, epochs=8, batch_size=1)
    fit = dict(config=config, steps=count * 8, train_seconds=2.5, wall_seconds=3.0, final_loss=.2, mean_loss_per_epoch=[.2] * 8,
               warm_start=dict(source_state={"tensor": "parent"}, initialized_state={"tensor": "original"}))
    common = dict(seed=seed, parent=dict(adapter=f"ORIGINAL_PARENT_{seed}"), native_capture_custody_checked=True,
                  automatic_pass=False, scientific_pass=None, memory_possible_denominator_per_variant=16,
                  memory_scored_denominator=count, retention_denominators=dict(held=48, canary=12), training_costs=training)
    historical = dict(copy.deepcopy(common), scope=memory.SCOPE, cells=dict(WRITE=high, LR0=lr0),
        fits=dict(WRITE=copy.deepcopy(fit), LR0=dict(copy.deepcopy(fit), config=dict(config, lr=0.0))),
        calls=2 * (2 * count + 60), updates=16 * count,
        parameter_diagnostics=dict(WRITE={"changed_elements": 2}, LR0={"changed_elements": 0}))
    candidate = dict(copy.deepcopy(common), scope=runner.SCOPE, cells=dict(WRITE=lower),
        historical_cells=dict(HIGH=copy.deepcopy(high), LR0=copy.deepcopy(lr0)), comparisons={},
        fits=dict(WRITE=dict(copy.deepcopy(fit), config=dict(config, lr=3e-5))),
        parameter_diagnostics=dict(WRITE={"changed_elements": 1}),
        incremental_cost=dict(calls=2 * count + 60, updates=count * 8, historical_calls=0, historical_updates=0),
        reused_endpoints={endpoint: dict(original_arm=arm, noncontemporaneous=True, incremental_calls=0, incremental_updates=0)
                          for endpoint, arm in (("HIGH", "WRITE"), ("LR0", "LR0"))})
    update_comparisons(candidate, historical)
    return candidate, historical


class ReducerTests(unittest.TestCase):
    def setUp(self):
        self.candidate, self.historical = fixture()
        temporary = tempfile.TemporaryDirectory(prefix="lower_lr_reducer_cpu_")
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name)

    def reduce(self):
        return analysis.reduce_seed(self.candidate, self.historical)

    def test_all_seed_denominators_thresholds_and_incremental_costs(self):
        for seed, count in enumerate((14, 8, 8)):
            with self.subTest(seed=seed):
                candidate, historical = fixture(seed)
                report = analysis.reduce_seed(candidate, historical)
                panels = report["panels"]["LOWER_LR"]
                self.assertEqual([panels[panel]["denominator"] for panel in analysis.PANELS], [count, count, 48, 12])
                self.assertEqual(panels["exact"]["possible_denominator"], 16)
                self.assertEqual(report["strict_exploratory_repair_screen"]["required_exact_source_faithful"], (8, 7, 5)[seed])
                self.assertTrue(report["strict_exploratory_repair_screen"]["met"])
                self.assertEqual(report["costs"]["new"]["updates"], count * 8)
                self.assertEqual(report["costs"]["new"]["calls"], 2 * count + 60)
                self.assertEqual(report["costs"]["new"]["prompt_tokens"], (2 * count + 60) * 10)
                self.assertEqual(report["costs"]["historical"]["LR0"]["incremental_cost"], dict(calls=0, updates=0))
                self.assertTrue(report["costs"]["historical"]["HIGH"]["noncontemporaneous"])
                self.assertFalse(report["native_identity_verified_by_reducer"])

    def test_per_item_restored_vs_still_missing_and_newly_lost(self):
        self.candidate["cells"]["WRITE"]["held"][1] = row("held", 1, False, 0)
        update_comparisons(self.candidate, self.historical)
        report = self.reduce()
        retention = report["retention"]["held"]
        self.assertEqual(retention["row_ids"]["restored_from_high_regression"], ["seed0:held:00"])
        self.assertEqual(retention["row_ids"]["still_missing_lr0_correct"], ["seed0:held:01"])
        self.assertEqual(retention["row_ids"]["newly_lost_vs_high"], ["seed0:held:01"])
        self.assertEqual(retention["counts"]["lr0_correct_retained"], 47)
        self.assertFalse(report["strict_exploratory_repair_screen"]["met"])

    def test_canary_regression_alone_fails_screen(self):
        self.candidate["cells"]["WRITE"]["canary"][5] = row("canary", 5, False, 0)
        update_comparisons(self.candidate, self.historical)
        report = self.reduce()
        self.assertEqual(report["strict_exploratory_repair_screen"]["lost_LR0_correct_items"], dict(held=0, canary=1))
        self.assertFalse(report["strict_exploratory_repair_screen"]["met"])

    def test_exact_floor_not_content_or_paraphrase(self):
        first = self.candidate["cells"]["WRITE"]["exact"][0]
        first["score"]["score"]["production_eligible"] = False
        first["score"]["score"]["strict_canonical"] = False
        first["score"]["score"]["format"] = "fenced"
        first["score"]["exact_target_bytes"] = False
        update_comparisons(self.candidate, self.historical)
        report = self.reduce()
        exact = report["panels"]["LOWER_LR"]["exact"]
        self.assertEqual(exact["numerators"]["content_correct"], 8)
        self.assertEqual(exact["numerators"]["production_eligible"], 7)
        self.assertEqual(exact["format_counts"]["fenced"], 1)
        self.assertFalse(report["strict_exploratory_repair_screen"]["met"])

    def test_higher_total_does_not_offset_lr0_correct_loss(self):
        for index in (1, 2):
            self.historical["cells"]["LR0"]["held"][index] = row("held", index, False, 0)
        self.candidate["historical_cells"]["LR0"] = copy.deepcopy(self.historical["cells"]["LR0"])
        self.candidate["cells"]["WRITE"]["held"][0] = row("held", 0, False, 0)
        update_comparisons(self.candidate, self.historical)
        report = self.reduce()
        self.assertEqual(report["panels"]["LOWER_LR"]["held"]["numerators"]["passed"], 47)
        self.assertEqual(report["panels"]["LR0"]["held"]["numerators"]["passed"], 46)
        self.assertFalse(report["strict_exploratory_repair_screen"]["met"])

    def test_bool_int_rejected(self):
        self.candidate["cells"]["WRITE"]["held"][0]["score"]["passed"] = 1
        with self.assertRaisesRegex(ValueError, "boolean metric"):
            self.reduce()

    def test_length_cannot_pass_no_repairs(self):
        first = self.candidate["cells"]["WRITE"]["exact"][0]
        first["finish_reason"] = first["score"]["score"]["finish_reason"] = "length"
        with self.assertRaisesRegex(ValueError, "non-stop"):
            self.reduce()

    def test_missing_duplicate_foreign_row_rejected(self):
        for case in ("missing", "duplicate", "foreign"):
            self.candidate, self.historical = fixture()
            rows = self.candidate["cells"]["WRITE"]["held"]
            if case == "missing":
                rows.pop()
            elif case == "duplicate":
                rows[1] = copy.deepcopy(rows[0])
            else:
                rows[0]["row_id"] = "foreign"
            with self.subTest(case=case), self.assertRaises(ValueError):
                self.reduce()

    def test_raw_source_target_and_prompt_join_failures(self):
        for case in ("raw", "source", "target", "prompt"):
            self.candidate, self.historical = fixture()
            first = self.candidate["cells"]["WRITE"]["exact"][0]
            if case == "raw":
                first["raw"] = "different"
            elif case == "source":
                first["score"]["source"]["execution_id"] = "foreign"
            elif case == "target":
                first["score"]["target_sha256"] = sha("foreign")
            else:
                first["cost"]["prompt_tokens"] = 11
            with self.subTest(case=case), self.assertRaises(ValueError):
                self.reduce()

    def test_original_parent_seed_or_lr_changes_rejected(self):
        for case in ("parent", "seed", "lr", "warm"):
            self.candidate, self.historical = fixture()
            if case == "parent":
                self.candidate["parent"]["adapter"] = "WRITE_DESCENDANT"
            elif case == "seed":
                self.candidate["seed"] = True
            elif case == "lr":
                self.candidate["fits"]["WRITE"]["config"]["lr"] = 1e-5
            else:
                self.candidate["fits"]["WRITE"]["warm_start"]["source_state"] = {}
            with self.subTest(case=case), self.assertRaises(ValueError):
                self.reduce()

    def test_forged_aggregate_or_screen_rejected(self):
        self.candidate["comparisons"]["candidate_vs_historical_LR0"]["totals"]["WRITE"]["exact"]["numerators"]["production_eligible"] = 14
        with self.assertRaisesRegex(ValueError, "aggregate"):
            self.reduce()
        update_comparisons(self.candidate, self.historical)
        self.candidate["strict_exploratory_repair_screen"]["met"] = False
        with self.assertRaisesRegex(ValueError, "strict screen"):
            self.reduce()

    def test_reused_controls_unchanged_and_no_rescore(self):
        before = copy.deepcopy((self.candidate, self.historical))
        with patch.object(memory, "score_calls", side_effect=AssertionError("must not score")):
            result = self.reduce()
        self.assertEqual((self.candidate, self.historical), before)
        self.assertFalse(result["raw_reparsed_or_rescored"])
        self.candidate["historical_cells"]["HIGH"]["held"][0]["raw"] = "changed"
        with self.assertRaisesRegex(ValueError, "historical cells"):
            self.reduce()

    def test_nan_negative_boolean_cost_rejected(self):
        for bad in (float("nan"), -1, True):
            self.candidate, self.historical = fixture()
            self.candidate["cells"]["WRITE"]["held"][0]["cost"]["generation_seconds"] = bad
            with self.subTest(bad=bad), self.assertRaisesRegex(ValueError, "typed cost"):
                self.reduce()

    def write(self, path, value):
        path.write_text(json.dumps(value, sort_keys=True) + "\n")
        return dict(path=str(path), sha256=analysis.digest(path))

    def test_collection_hash_and_completion_join(self):
        plan, complete = sha("plan"), sha("complete")
        report = dict(self.candidate, plan_sha256=plan, completion_sha256=complete)
        score_binding = self.write(self.home / "scores.json", report)
        binding = self.write(self.home / "collection.json", dict(scores_sha256=score_binding["sha256"], completion_sha256=complete))
        loaded, provenance = analysis.load_collected(binding, plan, complete)
        self.assertEqual(loaded, report)
        self.assertEqual(provenance["scores"], score_binding)
        with self.assertRaisesRegex(ValueError, "completion"):
            analysis.load_collected(binding, plan, sha("wrong"))
        (self.home / "scores.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "file pin"):
            analysis.load_collected(binding, plan, complete)

    def test_duplicate_json_and_nonfinite_rejected(self):
        path = self.home / "bad.json"
        for text in ('{"a":1,"a":2}', '{"a":NaN}'):
            path.write_text(text)
            with self.assertRaises(ValueError):
                analysis.read(path)

    def manifest_fixture(self, seeds):
        entries, lookup = [], {}
        for seed in seeds:
            old_plan, old_complete, old_collection, old_scores = runner.HISTORY_PINS[seed]
            candidate, historical = fixture(seed)
            history_binding = dict(path=str(self.home / f"historical{seed}/collection.json"), sha256=old_collection)
            candidate_binding = dict(path=str(self.home / f"candidate{seed}/collection.json"), sha256=sha(f"candidate{seed}"))
            candidate["historical_binding"] = dict(plan_sha256=old_plan, completion_sha256=old_complete,
                                                   collection=history_binding, scores_sha256=old_scores)
            entry = dict(seed=seed, candidate_collection=candidate_binding, candidate_plan_sha256=sha(f"plan{seed}"),
                         candidate_completion_sha256=sha(f"complete{seed}"), historical_collection=history_binding)
            entries.append(entry)
            lookup[history_binding["path"]] = (historical, dict(scores=dict(sha256=old_scores)))
            lookup[candidate_binding["path"]] = (candidate, dict(scores=dict(sha256=sha(f"scores{seed}"))))
        manifest = dict(protocol=dict(path="/data/home/rohing/dream-state/research_notes/astra_memos/ASTRA_ACTUAL_MEMORY_RETENTION_REPAIR_2026-09-13.md",
                                     sha256=analysis.PROTOCOL_PIN), runs=entries)
        binding = self.write(self.home / "manifest.json", manifest)
        return manifest, binding, lookup

    def test_partial_roster_unknown_not_pass_and_three_seed_costs(self):
        for seeds in ((2,), (2, 0, 1)):
            manifest, binding, lookup = self.manifest_fixture(seeds)
            with patch.object(analysis, "load_collected", side_effect=lambda binding, *args: lookup[binding["path"]]):
                result = analysis.reduce_manifest(binding["path"], binding["sha256"])
            self.assertEqual(result["roster"]["present"], sorted(seeds))
            if len(seeds) == 1:
                self.assertIsNone(result["roster"]["all_three_strict_screens_met"])
                self.assertEqual(result["roster"]["missing"], [0, 1])
            else:
                self.assertTrue(result["roster"]["all_three_strict_screens_met"])
                self.assertEqual(result["total_new_cost"]["updates"], 240)
                self.assertEqual(result["total_new_cost"]["calls"], 240)
            self.assertEqual(result["total_incremental_historical_cost"], dict(calls=0, updates=0))
            self.assertIsNone(result["scientific_pass"])

    def test_duplicate_seed_or_wrong_import_binding_rejected(self):
        manifest, binding, lookup = self.manifest_fixture((0,))
        manifest["runs"].append(copy.deepcopy(manifest["runs"][0]))
        binding = self.write(Path(binding["path"]), manifest)
        with patch.object(analysis, "load_collected", side_effect=lambda binding, *args: lookup[binding["path"]]), self.assertRaisesRegex(ValueError, "duplicate seed"):
            analysis.reduce_manifest(binding["path"], binding["sha256"])
        manifest["runs"].pop()
        binding = self.write(Path(binding["path"]), manifest)
        lookup[manifest["runs"][0]["candidate_collection"]["path"]][0]["historical_binding"]["scores_sha256"] = sha("wrong")
        with patch.object(analysis, "load_collected", side_effect=lambda binding, *args: lookup[binding["path"]]), self.assertRaisesRegex(ValueError, "imported history"):
            analysis.reduce_manifest(binding["path"], binding["sha256"])

    def test_output_exclusive_and_no_overwrite(self):
        output = self.home / "analysis.json"
        result = dict(roster=dict(complete=False), schema=analysis.SCHEMA)
        with patch.object(analysis, "reduce_manifest", return_value=result):
            analysis.main(["--manifest", "not-read", "--manifest-sha256", sha("manifest"), "--out", str(output)])
            before = output.read_bytes()
            with self.assertRaises(FileExistsError):
                analysis.main(["--manifest", "not-read", "--manifest-sha256", sha("manifest"), "--out", str(output)])
            self.assertEqual(output.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
