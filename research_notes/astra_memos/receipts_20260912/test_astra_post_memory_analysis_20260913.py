import importlib.util
import io
from pathlib import Path
import sys
import tarfile
import tempfile
from types import SimpleNamespace
import unittest

sys.dont_write_bytecode = True
SPEC = importlib.util.spec_from_file_location("reducer", "/tmp/astra_post_memory_analysis_20260913.py")
reducer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reducer)
SOURCE = "/tmp/astra_level1_real_record_source_20260913_attempt1"


class AnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.core = reducer.load_module("/tmp/astra_post_memory_formation_core_20260913.py", reducer.CORE_PIN)
        cls.dependencies = cls.core.load_dependencies(SOURCE)

    def fixture(self, *, invalid=False, constant=None, fence=False):
        def backend(request):
            values = [3, 7, 11]
            if request["kind"] == "wake":
                raw = "PREDICT: F\nACT: TRY " + ("3 7 11" if invalid else "3,7,11")
            else:
                unused, outcome = self.dependencies.game_class().evaluate(SimpleNamespace(eid=request["episode_id"]), "TRY 3,7,11")
                observed = "True" in outcome
                raw = constant
                if constant is None:
                    raw = reducer.canonical({"try": values, "observed": observed, "predicted": False,
                                             "relation": "mismatched" if observed else "matched"})
                if fence:
                    raw = "```json\n" + raw + "\n```"
            return dict(request_id=request["request_id"], state=request["state"], raw=raw, finish_reason="stop")
        return self.core.run_state("perception_seed0_WRITE", backend, dependencies=self.dependencies)

    def dataset(self, raw):
        return {"rows": [{"row_id": "original#t1", "raw_target": raw, "target_sha256": reducer.sha(raw.encode())}]}

    def test_complete_variable_outcomes_replay(self):
        capture = self.fixture()
        raw = capture["episodes"][0]["turns"][0]["record"]["response"]["raw"]
        result = reducer.reduce_capture(capture, self.dataset(raw), self.core, self.dependencies)
        self.assertEqual(result["audit"]["calls_replayed"], 32)
        self.assertEqual(result["groups"]["all"]["production_eligible"]["count"], 16)
        self.assertEqual(result["groups"]["example_absent"]["slots"], 8)

    def test_no_record_is_missing_not_accuracy_zero(self):
        capture = self.fixture(invalid=True)
        result = reducer.reduce_capture(capture, {"rows": []}, self.core, self.dependencies)
        self.assertEqual(result["groups"]["all"]["space_separated_invalid"], 16)
        self.assertIsNone(result["groups"]["all"]["production_eligible"]["over_records"])
        self.assertTrue(all(row["production_eligible"] is None for row in result["rows"]))

    def test_copied_target_can_be_wrong_source(self):
        raw = '{"observed":true,"predicted":false,"relation":"mismatched","try":[3,7,11]}'
        result = reducer.reduce_capture(self.fixture(constant=raw), self.dataset(raw), self.core, self.dependencies)
        cross = result["groups"]["all"]["target_match_by_eligibility"]
        self.assertGreater(cross["match/rejected"], 0)
        self.assertGreater(cross["match/eligible"], 0)

    def test_fences_not_production_success(self):
        result = reducer.reduce_capture(self.fixture(fence=True), {"rows": []}, self.core, self.dependencies)
        self.assertEqual(result["groups"]["all"]["content_correct"]["count"], 16)
        self.assertEqual(result["groups"]["all"]["production_eligible"]["count"], 0)

    def test_typed_match_is_not_byte_match(self):
        original = '{"observed":true,"predicted":false,"relation":"mismatched","try":[3,7,11]}'
        reformatted = '{ "try": [3,7,11], "relation": "mismatched", "predicted": false, "observed": true }'
        result = reducer.reduce_capture(self.fixture(constant=reformatted), self.dataset(original), self.core, self.dependencies)
        self.assertEqual(result["groups"]["all"]["target_byte_match"]["matches"], 0)
        self.assertEqual(result["groups"]["all"]["typed_target_match"]["matches"], 16)

    def test_resigned_source_join_tamper_fails(self):
        capture = self.fixture()
        capture["episodes"][0]["turns"][0]["execution"]["observed"] = "forged"
        capture["capture_sha256"] = self.core.digest({key: value for key, value in capture.items() if key != "capture_sha256"})
        with self.assertRaises(ValueError):
            reducer.reduce_capture(capture, {"rows": []}, self.core, self.dependencies)

    def test_strict_json_and_bool_count(self):
        for raw in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":1e999}'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                reducer.decode(raw)
        with self.assertRaises(ValueError):
            reducer.equal(True, 1, "bool is not count")
        self.assertIsNone(reducer.triple([True, 2, 3]))

    def test_pin_mismatch(self):
        with self.assertRaises(ValueError):
            reducer.load_module("/tmp/astra_post_memory_formation_core_20260913.py", "0" * 64)

    def test_target_pin_and_duplicate_rows(self):
        dataset = self.dataset('{"try":[1,2,3]}')
        dataset["rows"][0]["raw_target"] += " "
        with self.assertRaises(ValueError):
            reducer.bank(dataset)
        dataset = self.dataset('{"try":[1,2,3]}')
        dataset["rows"] *= 2
        with self.assertRaises(ValueError):
            reducer.bank(dataset)

    def test_paired_schedule_missing_or_swapped(self):
        result = reducer.reduce_capture(self.fixture(), {"rows": []}, self.core, self.dependencies)
        rows = result["rows"]
        for other in (rows[:-1], list(reversed(rows))):
            with self.assertRaises(ValueError):
                reducer.paired(rows, other)
        paired = reducer.paired(rows, rows)
        self.assertEqual(len(paired["production_eligible"]["both"]), 16)

    def test_archive_rejects_duplicate_and_does_not_extract(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "fixture.tar"
            with tarfile.open(path, "w") as handle:
                for unused in range(2):
                    info = tarfile.TarInfo("sample.json")
                    info.size = 2
                    handle.addfile(info, io.BytesIO(b"{}"))
            with self.assertRaises(ValueError):
                reducer.Archive(path)
            self.assertFalse((Path(folder) / "sample.json").exists())

    def test_actual_pinned_archive_and_all_seeds(self):
        root = Path("/data/home/rohing/dream-state/gpu_artifacts_local")
        post = reducer.Archive(root / "post_memory_formation_20260913_attempt1/evidence.tar", reducer.ARCHIVE_PIN)
        memory = reducer.Archive(root / "actual_record_memory_20260913_attempt1/evidence.tar")
        try:
            result = reducer.analyze(post, memory, "/tmp/astra_post_memory_collected_20260913_attempt1", SOURCE)
        finally:
            post.close()
            memory.close()
        self.assertEqual([seed["seed"] for seed in result["seeds"]], [0, 1, 2])
        for seed, expected in zip(result["seeds"], (7, 6, 4)):
            self.assertEqual(seed["arms"]["WRITE"]["groups"]["all"]["production_eligible"]["count"], 8)
            self.assertEqual(seed["arms"]["LR0"]["groups"]["all"]["production_eligible"]["count"], expected)
            for arm in reducer.ARMS:
                self.assertEqual(seed["arms"][arm]["groups"]["example_absent"]["space_separated_invalid"], 8)


if __name__ == "__main__":
    unittest.main()
