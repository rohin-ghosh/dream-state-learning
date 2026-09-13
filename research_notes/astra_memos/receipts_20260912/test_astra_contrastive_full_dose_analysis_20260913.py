"""CPU fixtures only; no live roots, outcome discovery, native or model calls."""
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
PATH = Path("/tmp/astra_contrastive_full_dose_analysis_20260913.py")
spec = importlib.util.spec_from_file_location("full_dose_independent_analysis_test", PATH)
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)
FIXTURE = Path("/tmp/test_astra_contrastive_full_dose_run_20260913_v2.py")
assert analysis.digest(FIXTURE) == "b680d2123f496e405e203fe7a9859deb9b55a3ca177e3d5f766008695fd0333e"
fixture_spec = importlib.util.spec_from_file_location("frozen_full_dose_cpu_fixture", FIXTURE)
fixtures = importlib.util.module_from_spec(fixture_spec)
fixture_spec.loader.exec_module(fixtures)
runtime = fixtures.runtime


def record(path):
    return dict(path=str(path), sha256=analysis.digest(path))


class ScoringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixtures.FullDoseTests.setUpClass()
        cls.material = fixtures.FullDoseTests.material
        cls.corpus = fixtures.FullDoseTests.corpus
        cls.dataset = json.loads(cls.material.encoded(fixtures.FullDoseTests.dataset))

    def setUp(self):
        self.responses = {state: {panel+"/"+row["row_id"]: dict(raw=row["raw_target"], finish_reason="stop")
                                 for panel, rows in self.dataset["evaluation"].items() for row in rows} for state in analysis.STATES}

    def result(self):
        return analysis.summarize(self.dataset, self.responses, self.material, self.corpus)

    def test_frozen_material_identity_roundtrip(self):
        analysis.validate_dataset(self.dataset, self.material, self.corpus)
        analysis.validate_dataset(fixtures.FullDoseTests.dataset, self.material, self.corpus)

    def test_independent_summaries_equal_frozen_scorer(self):
        result = self.result()
        expected = self.material.score_dataset(self.corpus, self.dataset, self.responses)
        self.assertEqual(result["frozen_result"], expected)
        self.assertFalse(result["original_screen"]["met"])
        self.assertTrue(result["original_screen"]["ceiling_limited"])
        for state in analysis.STATES:
            self.assertEqual(result["states"][state]["held"], dict(content=24, strict=24))

    def test_missing_arm_or_off_rejected(self):
        for state in analysis.STATES:
            broken = copy.deepcopy(self.responses)
            del broken[state]
            with self.assertRaisesRegex(ValueError, "arm"):
                analysis.summarize(self.dataset, broken, self.material, self.corpus)

    def test_missing_extra_or_wrong_row_denominator(self):
        key = next(iter(self.responses["plain"]))
        for mode in ("missing", "extra"):
            broken = copy.deepcopy(self.responses)
            if mode == "missing":
                del broken["plain"][key]
            else:
                broken["plain"]["unknown-source"] = dict(raw="{}", finish_reason="stop")
            with self.assertRaisesRegex(ValueError, "response rows"):
                analysis.summarize(self.dataset, broken, self.material, self.corpus)
        dataset = copy.deepcopy(self.dataset)
        dataset["evaluation"]["D1"].pop()
        with self.assertRaises(ValueError):
            analysis.validate_dataset(dataset, self.material, self.corpus)

    def test_source_error_separate_from_syntax_and_fields(self):
        row = self.dataset["evaluation"]["D1"][0]
        key = "D1/"+row["row_id"]
        value = json.loads(row["raw_target"])
        value["observed"] = not value["observed"]
        self.responses["contrastive"][key]["raw"] = json.dumps(value, separators=(",", ":"))
        result = self.result()
        score = result["states"]["contrastive"]["rows"][key]
        self.assertFalse(score["content_correct"])
        self.assertIn("observed", score["source_errors"])
        self.assertFalse(score["syntax_errors"])
        self.assertFalse(score["schema_errors"])
        self.assertEqual(result["states"]["contrastive"]["panels"]["D1"]["fields"]["observed"]["incorrect"], 1)
        self.assertEqual(result["paired"]["contrastive_minus_plain"]["D1"]["content"]["difference"], -1)

    def test_bool_integer_schema_error_not_source_error(self):
        row = self.dataset["evaluation"]["D1"][0]
        key = "D1/"+row["row_id"]
        value = json.loads(row["raw_target"])
        value["try"][0] = True
        self.responses["plain"][key]["raw"] = json.dumps(value)
        score = self.result()["states"]["plain"]["rows"][key]
        self.assertFalse(score["content_correct"])
        self.assertIn("try:invalid_type_or_domain", score["schema_errors"])
        self.assertFalse(score["source_errors"])
        self.assertTrue(all(value is None for value in score["field_correct"].values()))

    def test_completion_failures_never_correct(self):
        key = "D1/"+self.dataset["evaluation"]["D1"][0]["row_id"]
        self.responses["contrastive"][key]["finish_reason"] = "length"
        result = self.result()
        score = result["states"]["contrastive"]["rows"][key]
        self.assertTrue(score["completion_errors"])
        self.assertFalse(score["strict_correct"])
        self.assertFalse(score["content_correct"])
        self.assertFalse(result["original_screen"]["complete"])

    def test_whitespace_content_vs_strict_not_new_parser(self):
        row = self.dataset["evaluation"]["D1"][0]
        key = "D1/"+row["row_id"]
        raw = json.dumps(json.loads(row["raw_target"]), indent=2)
        self.responses["contrastive"][key]["raw"] = raw
        result = self.result()
        self.assertEqual(result["frozen_result"], self.material.score_dataset(self.corpus, self.dataset, self.responses))
        score = result["states"]["contrastive"]["rows"][key]
        self.assertTrue(score["content_correct"])
        self.assertTrue(score["strict_correct"])
        self.assertFalse(score["exact_target_bytes"])

    def test_fence_does_not_import_level1_permissive_policy(self):
        row = self.dataset["evaluation"]["D1"][0]
        key = "D1/"+row["row_id"]
        self.responses["plain"][key]["raw"] = "```json\n"+row["raw_target"]+"\n```"
        score = self.result()["states"]["plain"]["rows"][key]
        self.assertFalse(score["content_correct"])
        self.assertTrue(score["syntax_errors"])

    def test_canaries_both_arms_individual_and_saved_order(self):
        for arm in analysis.ARMS:
            for panel in ("C-record", "C-general"):
                key = panel+"/"+self.dataset["evaluation"][panel][0]["row_id"]
                self.responses[arm][key]["raw"] = "wrong"
        result = self.result()
        self.assertEqual(result["frozen_result"], self.material.score_dataset(self.corpus, self.dataset, self.responses))
        for arm in analysis.ARMS:
            self.assertEqual(sum(row["lost"] for row in result["per_item_canaries"][arm].values()), 2)

    def test_actual_original_screen_thresholds_unchanged(self):
        for state in ("OFF", "plain"):
            for panel in ("D1", "D2"):
                for row in self.dataset["evaluation"][panel][:3]:
                    self.responses[state][panel+"/"+row["row_id"]]["raw"] = "wrong"
        result = self.result()
        self.assertTrue(result["original_screen"]["met"])
        self.assertEqual(result["frozen_result"], self.material.score_dataset(self.corpus, self.dataset, self.responses))
        self.assertEqual(result["paired"]["contrastive_minus_plain"]["held"]["strict"]["counts"]["wins"], 6)


class CustodyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not hasattr(fixtures.FullDoseTests, "trains"):
            fixtures.FullDoseTests.setUpClass()

    def setUp(self):
        self.fixture = fixtures.FullDoseTests(methodName="test_dose_only_and_seed_strict")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        completion = self.fixture.completed()
        self.root = self.fixture.root
        self.out = self.fixture.home / "collected"
        runtime.collect(str(self.root), self.fixture.pin, completion, str(self.out))
        self.entry = dict(seed=0, root=str(self.root), plan_sha256=self.fixture.pin, completion_sha256=completion,
                          collection=record(self.out / "collection.json"), scores=record(self.out / "scores.json"))
        self.manifest = dict(source_files=self.fixture.spec["source_files"], historical_archive=self.fixture.spec["historical_archive"])
        self.fixture.history_import.return_value = dict(self.fixture.history, archive=self.fixture.spec["historical_archive"])

    def reduce(self):
        return analysis.load_pair(self.entry, self.manifest, runtime, self.fixture.material, self.fixture.corpus,
                                  self.fixture.trainer, self.fixture.probe)

    def replace_scores(self, mutate):
        scores = analysis.read(self.out / "scores.json")
        mutate(scores)
        (self.out / "scores.json").write_bytes(analysis.encoded(scores))
        self.entry["scores"] = record(self.out / "scores.json")
        collection = analysis.read(self.out / "collection.json")
        collection["scores_sha256"] = self.entry["scores"]["sha256"]
        (self.out / "collection.json").write_bytes(analysis.encoded(collection))
        self.entry["collection"] = record(self.out / "collection.json")

    def test_completed_fixture_raw_replay_matches_collector(self):
        result = self.reduce()
        self.assertEqual(result["new_cost"], dict(fits=2, updates=672, presentations=2688, calls=96))
        self.assertTrue(result["historical_OFF"]["noncontemporaneous"])
        self.assertEqual(result["historical_OFF"]["incremental_calls"], 0)
        self.assertFalse(result["automatic_pass"])
        self.assertIsNone(result["scientific_pass"])

    def test_historical_off_never_incremental(self):
        self.replace_scores(lambda scores: scores["historical_OFF"].update(new_calls=48))
        with self.assertRaisesRegex(ValueError, "historical OFF label"):
            self.reduce()

    def test_missing_arm_failure(self):
        self.replace_scores(lambda scores: scores["material_scores"]["states"].pop("plain"))
        with self.assertRaisesRegex(ValueError, "aggregate differs"):
            self.reduce()

    def test_saved_field_error_tamper_detected(self):
        def alter(scores):
            key = next(key for key in scores["material_scores"]["states"]["plain"]["items"] if key.startswith("D1/"))
            scores["material_scores"]["states"]["plain"]["items"][key]["field_correct"]["observed"] = False
        self.replace_scores(alter)
        with self.assertRaisesRegex(ValueError, "aggregate differs"):
            self.reduce()

    def test_changed_raw_closed_receipt_rejected(self):
        (self.root / "run/readout_plain/D1__00.response.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "stage hashes"):
            self.reduce()

    def test_failed_controller_not_scored(self):
        runtime.write(self.root / "controller_failure.json", dict(error="CPU fixture"))
        with self.assertRaisesRegex(ValueError, "failed root"):
            self.reduce()

    def test_wrong_collection_or_seed_binding(self):
        self.entry["seed"] = 1
        with self.assertRaisesRegex(ValueError, "seed mismatch"):
            self.reduce()
        self.entry["seed"] = False
        with self.assertRaises(ValueError):
            self.reduce()

    def test_no_runtime_lifecycle_or_native_queries(self):
        with patch.object(runtime, "collect", side_effect=AssertionError("collector forbidden")), \
                patch.object(runtime, "verify", side_effect=AssertionError("native-path verify forbidden")), \
                patch.object(runtime, "validate_completed", side_effect=AssertionError("process querying forbidden")), \
                patch.object(runtime.old, "Native", side_effect=AssertionError("native forbidden")):
            self.reduce()
        self.fixture.probe.gpu_state.assert_not_called()

    def test_independent_padded_cost_recalculation(self):
        prepared = analysis.read(self.root / "train_plain.json")
        self.assertEqual(analysis.training_costs(prepared), prepared["costs"])
        changed = copy.deepcopy(prepared)
        changed["costs"]["padded_tokens"] += 1
        self.assertNotEqual(analysis.training_costs(changed), changed["costs"])

    def test_whole_roster_cost_and_historical_not_triplicated(self):
        result = self.reduce()
        spec = self.fixture.spec
        manifest = {key: spec[key] for key in ("protocol", "material", "public", "source", "source_files", "historical_archive")}
        manifest["runner"] = record(fixtures.PATH)
        manifest["pairs"] = [dict(self.entry, seed=seed, root=str(self.fixture.home / f"root{seed}"), plan_sha256=str(seed)*64) for seed in (0, 1, 2)]
        path = self.fixture.home / "manifest.json"
        path.write_bytes(analysis.encoded(manifest))
        def pair(entry, *args):
            return dict(copy.deepcopy(result), seed=entry["seed"], native_root=entry["root"], inputs=entry)
        with patch.object(analysis, "load_pair", side_effect=pair):
            reduced = analysis.reduce_manifest(str(path), analysis.digest(path))
        self.assertEqual(reduced["total_new_cost"], dict(fits=6, updates=2016, presentations=8064, calls=288))
        self.assertEqual(reduced["historical_OFF_unique_calls"], 48)
        self.assertEqual(reduced["historical_incremental_cost"], dict(calls=0, updates=0))
        self.assertEqual(reduced["roster"]["present"], [0, 1, 2])
        self.assertFalse(reduced["automatic_pass"])


class ManifestTests(unittest.TestCase):
    def test_incomplete_or_duplicate_seed_roster_rejected_before_loading(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as directory:
            path = Path(directory) / "manifest.json"
            manifest = dict(runner={}, protocol={}, material={}, public={}, source="/not-read", source_files={}, historical_archive={}, pairs=[])
            for pairs in ([], [dict(seed=0)], [dict(seed=0), dict(seed=0), dict(seed=2)], [dict(seed=False), dict(seed=1), dict(seed=2)]):
                manifest["pairs"] = pairs
                path.write_bytes(analysis.encoded(manifest))
                with patch.object(analysis, "load", side_effect=AssertionError("inputs must not load")):
                    with self.assertRaises(ValueError):
                        analysis.reduce_manifest(str(path), analysis.digest(path))

    def test_duplicate_json_and_nonfinite_rejected(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as directory:
            path = Path(directory) / "bad.json"
            for raw in ('{"a":1,"a":2}', '{"value":NaN}'):
                path.write_text(raw)
                with self.assertRaises(ValueError):
                    analysis.read(path)

    def test_output_cannot_overwrite(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as directory:
            path = Path(directory) / "existing.json"
            path.write_text("preserve")
            with self.assertRaises(ValueError):
                analysis.main(["--manifest", "/not-read", "--manifest-sha256", "bad", "--out", str(path)])
            self.assertEqual(path.read_text(), "preserve")

    def test_output_path_traversal_rejected(self):
        with self.assertRaises(ValueError):
            analysis.main(["--manifest", "/not-read", "--manifest-sha256", "bad", "--out", "/tmp/../var/contrastive_analysis.json"])


if __name__ == "__main__":
    unittest.main()
