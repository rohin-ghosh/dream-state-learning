"""Mock responses through the real pinned v2 core; no native/model imports."""
import copy
import hashlib
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

import astra_real_record_memory_core_20260913 as memory


class MemoryCoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.core, cls.dependencies = memory.load_core()

    def capture(self, mutate_record=None, invalid_wake=False, state="perception_seed0", wake_raw="PREDICT: T\nACT: TRY 2,5,9"):
        def backend(request):
            response = {"request_id": request["request_id"], "state": request["state"], "finish_reason": "stop"}
            if request["kind"] == "wake":
                response["raw"] = "TRY 2,5,9" if invalid_wake else wake_raw
            else:
                prompt = request["input_messages"][0]["content"]
                facts = json.loads(re.findall(r"^Observed fields: (.*)$", prompt, re.MULTILINE)[-1])
                response["raw"] = json.dumps({"try": facts["values"], "observed": facts["observed"],
                    "predicted": facts["predicted"],
                    "relation": "matched" if facts["predicted"] == facts["observed"] else "mismatched"})
                if mutate_record:
                    mutate_record(request, response)
            return response
        return self.core.run_state(state, backend, dependencies=self.dependencies)

    def test_all_admitted_in_original_order_and_input_unchanged(self):
        capture = self.capture()
        before = copy.deepcopy(capture)
        dataset = memory.project_capture(capture)
        self.assertEqual(capture, before)
        self.assertEqual(dataset["status"], "WRITE_AVAILABLE")
        self.assertEqual(len(dataset["rows"]), 16)
        self.assertEqual(dataset["refused"], [])
        expected = [f"perception_seed0:{task}#t{tick}" for task in self.core.episode_ids() for tick in (1, 2)]
        self.assertEqual([row["row_id"] for row in dataset["rows"]], expected)
        self.assertEqual(dataset["counts"]["distinct_triples"], 1)
        self.assertEqual(dataset["counts"]["episodes_with_admissions"], 8)
        self.assertFalse(dataset["qualification"]["native_identity_verified"])

    def test_calls_actual_frozen_audit(self):
        capture = self.capture()
        with patch.object(self.core, "audit_capture", wraps=self.core.audit_capture) as audit:
            with patch.object(memory, "load_core", return_value=(self.core, self.dependencies)):
                memory.project_capture(capture)
        audit.assert_called_once()

    def test_cue_is_only_public_ids_and_static_schema(self):
        capture = self.capture()
        dataset = memory.project_capture(capture)
        for row in dataset["rows"]:
            source = row["source"]
            self.assertEqual(source["public_execution_id"], f"{source['task_id']}#t{source['tick']}")
            for variant, key in (("exact", "input_messages"), ("paraphrase", "paraphrase_input_messages")):
                expected = memory.CUE_TEMPLATES[variant].format(task_id=source["task_id"],
                    public_execution_id=source["public_execution_id"]) + memory.SCHEMA_INSTRUCTION
                self.assertEqual(row[key], [{"role": "user", "content": expected}])
                for forbidden in ("ACT:", "PREDICT:", "Observed fields:", "the box says:", "2,5,9", row["raw_target"]):
                    self.assertNotIn(forbidden, expected)
                self.assertNotIn(source["state"], expected)
            self.assertEqual(row["encoding_contract"]["context_labels"], -100)

    def test_exact_utf8_target_bytes_not_reserialized(self):
        def whitespace(request, response):
            response["raw"] = " \r\n" + response["raw"].replace('"try"', '"\\u0074ry"') + "\t\r\n"
        capture = self.capture(whitespace)
        dataset = memory.project_capture(capture)
        originals = [turn["record"]["response"]["raw"] for episode in capture["episodes"] for turn in episode["turns"]]
        for row, original in zip(dataset["rows"], originals):
            self.assertEqual(row["raw_target"].encode("utf-8"), original.encode("utf-8"))
            self.assertEqual(row["target_sha256"], hashlib.sha256(original.encode("utf-8")).hexdigest())
            self.assertNotEqual(row["raw_target"], self.core.canonical(json.loads(original)))

    def test_changed_action_prior_outcome_do_not_change_cues(self):
        original = self.capture()
        changed = self.capture(wake_raw="PREDICT: F\nACT: TRY -7,11,19")
        original_rows = memory.project_capture(original)["rows"]
        changed_rows = memory.project_capture(changed)["rows"]
        for original_row, changed_row in zip(original_rows, changed_rows):
            self.assertEqual(original_row["input_messages"], changed_row["input_messages"])
            self.assertEqual(original_row["paraphrase_input_messages"], changed_row["paraphrase_input_messages"])
            self.assertNotEqual(original_row["raw_target"], changed_row["raw_target"])
        row = original_rows[0]
        result = memory.score_readback(changed, row["row_id"], row["raw_target"], "stop", input_messages=row["input_messages"])
        self.assertFalse(result["score"]["production_eligible"])

    def test_duplicate_or_reordered_episodes_refused(self):
        for duplicate in (True, False):
            capture = self.capture()
            if duplicate:
                capture["episodes"][1] = copy.deepcopy(capture["episodes"][0])
            else:
                capture["episodes"].reverse()
            capture["capture_sha256"] = self.core.digest({key: value for key, value in capture.items() if key != "capture_sha256"})
            with self.assertRaises(ValueError):
                memory.project_capture(capture)

    def test_no_records_is_explicit_no_write(self):
        dataset = memory.project_capture(self.capture(invalid_wake=True))
        self.assertEqual(dataset["status"], "NO_WRITE")
        self.assertEqual(dataset["rows"], [])
        self.assertEqual(len(dataset["refused"]), 16)
        self.assertEqual(dataset["counts"]["distinct_triples"], 0)

    def test_invalid_records_are_refused_not_repaired(self):
        def fenced(request, response):
            response["raw"] = "```json\n" + response["raw"] + "\n```"
        def malformed(request, response):
            response["raw"] = '{"try":'
        def wrong_fact(request, response):
            target = json.loads(response["raw"])
            target["try"] = [9, 9, 9]
            response["raw"] = json.dumps(target)
        def wrong_type(request, response):
            target = json.loads(response["raw"])
            target["try"][0] = True
            response["raw"] = json.dumps(target)
        def unfinished(request, response):
            response["finish_reason"] = "length"
        def wrong_source(request, response):
            response["request_id"] = "wrong-source"
        for mutation in (fenced, malformed, wrong_fact, wrong_type, unfinished, wrong_source):
            with self.subTest(mutation=mutation.__name__):
                dataset = memory.project_capture(self.capture(mutation))
                self.assertEqual(dataset["status"], "NO_WRITE")
                self.assertEqual(dataset["rows"], [])
                self.assertEqual(len(dataset["refused"]), 16)

    def test_mixed_admission_no_selection_or_deduplication(self):
        def reject_first(request, response):
            if request["tick"] == 1:
                response["raw"] = "not a record"
        dataset = memory.project_capture(self.capture(reject_first))
        self.assertEqual(len(dataset["rows"]), 8)
        self.assertEqual(len(dataset["refused"]), 8)
        self.assertTrue(all(row["source"]["tick"] == 2 for row in dataset["rows"]))

    def test_malformed_and_tampered_capture_refused(self):
        for capture in ({}, [], None):
            with self.subTest(capture=capture), self.assertRaises(ValueError):
                memory.project_capture(capture)
        capture = self.capture()
        capture["episodes"][0]["turns"][0]["execution"]["eid"] = "different-task"
        capture["capture_sha256"] = self.core.digest({key: value for key, value in capture.items() if key != "capture_sha256"})
        with self.assertRaises(ValueError):
            memory.project_capture(capture)

    def test_forged_admission_rejected_even_with_new_capture_hash(self):
        capture = self.capture(lambda request, response: response.update(raw="invalid"))
        capture["episodes"][0]["turns"][0]["score"]["production_eligible"] = True
        capture["capture_sha256"] = self.core.digest({key: value for key, value in capture.items() if key != "capture_sha256"})
        with self.assertRaises(ValueError):
            memory.project_capture(capture)

    def test_pinned_core_and_dependency_sources_required(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "core.py"
            path.write_text("raise AssertionError('must not execute')\n")
            with self.assertRaisesRegex(ValueError, "core pin"):
                memory.load_core(core_path=path)
            source = Path(directory) / "organism_v6"
            source.mkdir()
            (source / "rulegame.py").write_text("incorrect source")
            with self.assertRaisesRegex(ValueError, "source pin"):
                memory.load_core(source_root=directory)

    def test_primary_and_transfer_score_original_execution(self):
        capture = self.capture()
        row = memory.project_capture(capture)["rows"][0]
        for variant, key in (("exact", "input_messages"), ("paraphrase", "paraphrase_input_messages")):
            result = memory.score_readback(capture, row["row_id"], row["raw_target"], "stop",
                                           input_messages=row[key], variant=variant)
            self.assertTrue(result["score"]["production_eligible"])
            self.assertTrue(result["exact_target_bytes"])
            self.assertEqual(result["variant"], variant)
        target = json.loads(row["raw_target"])
        target["observed"] = not target["observed"]
        result = memory.score_readback(capture, row["row_id"], json.dumps(target), "stop", input_messages=row["input_messages"])
        self.assertFalse(result["score"]["production_eligible"])

    def test_variant_cue_source_and_nonadmitted_rows_rejected(self):
        capture = self.capture()
        row = memory.project_capture(capture)["rows"][0]
        for row_id, messages, variant in ((row["row_id"], row["paraphrase_input_messages"], "exact"),
                ("wrong-row", row["input_messages"], "exact"), (row["row_id"], row["input_messages"], "unknown"),
                (row["row_id"], [{"role": "user", "content": row["raw_target"]}], "exact")):
            with self.assertRaises(ValueError):
                memory.score_readback(capture, row_id, row["raw_target"], "stop", input_messages=messages, variant=variant)
        with self.assertRaises(ValueError):
            memory.score_readback(self.capture(invalid_wake=True), row["row_id"], row["raw_target"], "stop",
                                  input_messages=row["input_messages"])

    def test_readback_fences_and_length_not_primary_success(self):
        capture = self.capture()
        row = memory.project_capture(capture)["rows"][0]
        result = memory.score_readback(capture, row["row_id"], "```json\n" + row["raw_target"] + "\n```", "stop",
                                       input_messages=row["input_messages"])
        self.assertFalse(result["score"]["production_eligible"])
        self.assertTrue(result["score"]["content_correct"])
        self.assertFalse(result["exact_target_bytes"])
        result = memory.score_readback(capture, row["row_id"], row["raw_target"], "length", input_messages=row["input_messages"])
        self.assertFalse(result["score"]["production_eligible"])
        self.assertFalse(result["exact_target_bytes"])

    def test_all_states_supported_without_cross_state_row_substitution(self):
        for state in self.core.STATES:
            capture = self.capture(state=state)
            row = memory.project_capture(capture)["rows"][0]
            self.assertTrue(row["row_id"].startswith(state + ":"))
            other_id = ("OFF" if state != "OFF" else "perception_seed0") + ":" + row["source"]["public_execution_id"]
            with self.assertRaises(ValueError):
                memory.score_readback(capture, other_id, row["raw_target"], "stop", input_messages=row["input_messages"])


if __name__ == "__main__":
    unittest.main()
