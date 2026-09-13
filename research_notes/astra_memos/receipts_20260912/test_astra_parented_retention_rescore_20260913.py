import copy
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest


SPEC = importlib.util.spec_from_file_location("retention_replay", "/tmp/astra_parented_retention_rescore_20260913.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class RetentionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        plan = MODULE.decode(Path("/tmp/astra_parented_record_native_20260913_attempt1/parented_record_seed0_20260913_attempt1/plan.json").read_bytes())
        cls.material = MODULE.load_material(plan["parent"]["material_pin"], plan["source"], plan["parent"]["source_files"])
        cls.dataset = cls.material.build_dataset("perception", seed=0)

    def fixture(self, raw=None, finish="stop", canary=False):
        row = copy.deepcopy(self.dataset["evaluation"]["canary" if canary else "held"][0])
        raw = row["raw_target"] if raw is None else raw
        call = dict(call_id="held_00", panel="held", row_id=row["row_id"], messages=row["input_messages"],
                    native=dict(prompt_token_ids=[1, 2], rendered_prompt="toy", actual_system_text="toy", actual_system_segment="toy"))
        route, params = {"path": "toy", "id": 1, "name": "toy"}, {"seed": 0}
        response = dict(call["native"], actual_prompt_token_ids=[1, 2], lora_request=route, text=raw, finish_reason=finish)
        pin = MODULE.sha(MODULE.encoded(response))
        score = self.material.score_row(row, raw, finish)
        saved = dict(row_id=row["row_id"], response_sha256=pin, raw=raw, finish_reason=finish, score=score)
        request = dict(call, lora_request=route, params=params)
        return dict(rows=[row], calls=[call], stored=[saved], responses=[(response, pin)], requests=[request],
                    scorer=self.material.score_row, route=route, params=params)

    def test_exact_replay(self):
        result = MODULE.rescore_panel(**self.fixture())
        self.assertEqual(result["discrepancies"], [])
        self.assertEqual(result["totals"]["content_correct"], 1)

    def test_wrong_stored_boolean_reports_exact_id(self):
        fixture = self.fixture()
        fixture["stored"][0]["score"]["content_correct"] = False
        result = MODULE.rescore_panel(**fixture)
        self.assertEqual(result["discrepancies"][0]["row_id"], fixture["rows"][0]["row_id"])
        self.assertEqual(result["discrepancies"][0]["differing_fields"], ["content_correct"])

    def test_bool_integer_score_discrepancy(self):
        fixture = self.fixture()
        fixture["stored"][0]["score"]["passed"] = 1
        self.assertEqual(MODULE.rescore_panel(**fixture)["discrepancies"][0]["differing_fields"], ["passed"])

    def test_nonboolean_error_field_discrepancy(self):
        fixture = self.fixture()
        fixture["stored"][0]["score"]["source_errors"] = ["invented"]
        self.assertEqual(MODULE.rescore_panel(**fixture)["discrepancies"][0]["differing_fields"], ["source_errors"])

    def test_missing_extra_score_fields_reported(self):
        fixture = self.fixture()
        del fixture["stored"][0]["score"]["format"]
        fixture["stored"][0]["score"]["unexpected"] = None
        self.assertEqual(MODULE.rescore_panel(**fixture)["discrepancies"][0]["differing_fields"], ["format", "unexpected"])

    def test_fence_content_not_strict(self):
        raw = self.dataset["evaluation"]["held"][0]["raw_target"]
        result = MODULE.rescore_panel(**self.fixture("```json\n" + raw + "\n```"))
        self.assertEqual(result["totals"]["content_correct"], 1)
        self.assertEqual(result["totals"]["strict"], 0)
        self.assertEqual(result["totals"]["format:fenced"], 1)

    def test_whitespace_keyorder(self):
        target = json.loads(self.dataset["evaluation"]["held"][0]["raw_target"])
        raw = json.dumps(dict(reversed(list(target.items()))), indent=2)
        result = MODULE.rescore_panel(**self.fixture(raw))
        self.assertEqual(result["totals"]["content_correct"], 1)
        self.assertEqual(result["totals"]["strict"], 0)

    def test_truncated_fails_both(self):
        result = MODULE.rescore_panel(**self.fixture(finish="length"))
        self.assertEqual(result["totals"]["content_correct"], 0)
        self.assertEqual(result["totals"]["strict"], 0)
        self.assertEqual(result["discrepancies"], [])

    def test_prose_rejected_not_repaired(self):
        result = MODULE.rescore_panel(**self.fixture("Here: " + self.dataset["evaluation"]["held"][0]["raw_target"]))
        self.assertEqual(result["totals"]["syntax_errors_rows"], 1)

    def test_canary_exact(self):
        self.assertEqual(MODULE.rescore_panel(**self.fixture(canary=True))["totals"]["strict"], 1)

    def test_target_tamper_rejected(self):
        fixture = self.fixture()
        fixture["rows"][0]["raw_target"] = "{}"
        with self.assertRaisesRegex(ValueError, "target/provenance"):
            MODULE.rescore_panel(**fixture)

    def test_source_proof_tamper_rejected(self):
        fixture = self.fixture()
        fixture["rows"][0]["source_proof"]["input_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "proof/input"):
            MODULE.rescore_panel(**fixture)

    def test_raw_join_mutations_rejected(self):
        for field in ("raw", "finish_reason", "response_sha256", "row_id"):
            with self.subTest(field=field):
                fixture = self.fixture()
                fixture["stored"][0][field] = "tampered"
                with self.assertRaises(ValueError):
                    MODULE.rescore_panel(**fixture)

    def test_request_join_mutations_rejected(self):
        for field in ("call_id", "messages", "native", "params", "lora_request", "panel", "row_id"):
            with self.subTest(field=field):
                fixture = self.fixture()
                fixture["requests"][0][field] = "tampered"
                with self.assertRaises(ValueError):
                    MODULE.rescore_panel(**fixture)

    def test_response_join_mutations_rejected(self):
        for field in ("rendered_prompt", "actual_system_text", "actual_system_segment", "prompt_token_ids", "actual_prompt_token_ids", "lora_request"):
            with self.subTest(field=field):
                fixture = self.fixture()
                fixture["responses"][0][0][field] = "tampered"
                with self.assertRaises(ValueError):
                    MODULE.rescore_panel(**fixture)

    def test_missing_duplicate_items_rejected(self):
        for field in ("stored", "calls", "responses", "requests"):
            for mode in ("missing", "duplicate"):
                with self.subTest(field=field, mode=mode):
                    fixture = self.fixture()
                    fixture[field] = [] if mode == "missing" else fixture[field] * 2
                    with self.assertRaises(ValueError):
                        MODULE.rescore_panel(**fixture)

    def test_duplicate_json_nonfinite_rejected(self):
        for raw in (b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":1e999}'):
            with self.assertRaises(ValueError):
                MODULE.decode(raw)

    def test_scorer_pin_rejected_before_import(self):
        with self.assertRaisesRegex(ValueError, "unexpected retention scorer"):
            MODULE.load_material({"path": "/tmp/not-a-file", "sha256": "wrong"}, "/tmp", {})

    def test_source_pin_rejected(self):
        with self.assertRaisesRegex(ValueError, "pin mismatch"):
            MODULE.load_material({"path": "/tmp/astra_level1_perception_reflection_material_20260913.py", "sha256": MODULE.MATERIAL_PIN},
                                 "/tmp/astra_level1_real_record_source_20260913_attempt1", {"organism_v6/birth_skill_corpus.py": "0" * 64})

    def test_archive_missing_duplicate_and_tampered(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "test.tar"
            with tarfile.open(path, "w") as archive:
                info = tarfile.TarInfo("one.json")
                info.size = 2
                archive.addfile(info, io.BytesIO(b"{}"))
            pin = MODULE.digest(path)
            self.assertEqual(MODULE.archive_records(path, pin, ["one.json"]), {"one.json": b"{}"})
            with self.assertRaisesRegex(ValueError, "missing"):
                MODULE.archive_records(path, pin, ["missing"])
            with self.assertRaisesRegex(ValueError, "archive pin"):
                MODULE.archive_records(path, "0" * 64, ["one.json"])
            with tarfile.open(path, "a") as archive:
                archive.addfile(info, io.BytesIO(b"{}"))
            with self.assertRaisesRegex(ValueError, "duplicate"):
                MODULE.archive_records(path, MODULE.digest(path), ["one.json"])

    def test_file_pin_and_symlink(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "data.json"
            path.write_bytes(b"{}")
            with self.assertRaisesRegex(ValueError, "pin mismatch"):
                MODULE.checked_bytes(path, "0" * 64)
            link = Path(temporary) / "link"
            link.symlink_to(path)
            with self.assertRaisesRegex(ValueError, "nonsymlink"):
                MODULE.checked_bytes(link)

    def test_fixed_manifest_pin(self):
        with self.assertRaisesRegex(ValueError, "fixed three-seed"):
            MODULE.replay("/tmp/not-read", "wrong", "/tmp/not-read")


if __name__ == "__main__":
    unittest.main()
