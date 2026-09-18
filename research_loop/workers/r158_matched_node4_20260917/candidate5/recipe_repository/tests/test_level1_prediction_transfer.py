import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from organism_v6 import level1_prediction_transfer as transfer


class PredictionTransferTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.material = transfer.build_material()
        cls.frozen_api = transfer._load_frozen(transfer.ORIGINAL_MATERIAL_PATH)

    def test_balanced_cases_and_paired_rows(self):
        rows = self.material["rows"]
        self.assertEqual(len(rows), 48)
        self.assertEqual(len({row["row_id"] for row in rows}), 48)
        self.assertEqual(len({row["case_id"] for row in rows}), 24)
        for case in transfer.CASE_TYPES:
            for view in transfer.VIEWS:
                self.assertEqual(sum(row["case"] == case and row["view"] == view for row in rows), 6)
        for offset in range(0, 48, 2):
            full, minimal = rows[offset:offset + 2]
            self.assertEqual((full["view"], minimal["view"]), transfer.VIEWS)
            for key in ("source", "case_id", "expected", "raw_target", "source_sha256"):
                self.assertEqual(full[key], minimal[key])
            self.assertNotEqual(full["prompt"], minimal["prompt"])
            self.assertIsNot(full["source"], minimal["source"])
        self.assertEqual(len({row["source"]["source_group_id"] for row in rows}), 6)

    def test_case_semantics_and_no_observed_selected_result(self):
        for row in self.material["rows"]:
            facts = row["source"]["public_facts"]
            matching = [entry["outcome"] for entry in facts["belief_card"]
                        if entry["action"] == facts["selected_action"]]
            self.assertNotEqual(facts["selected_action"], facts["earlier_action"])
            if row["case"] == "supported_true":
                self.assertTrue(matching)
                self.assertEqual(set(matching), {True})
                self.assertIs(row["expected"]["prediction"], True)
            elif row["case"] == "supported_false":
                self.assertTrue(matching)
                self.assertEqual(set(matching), {False})
                self.assertIs(row["expected"]["prediction"], False)
            else:
                self.assertEqual(set(matching), set() if row["case"] == "missing" else {True, False})
                self.assertEqual(row["expected"], {"decision": "abstain", "prediction": None,
                                                   "reason": "insufficient_evidence"})
            self.assertNotIn("selected_outcome", facts)

    def test_every_action_is_disjoint_from_original_splits(self):
        old = self.frozen_api.build_dataset("prediction", seed=0)
        prior = old["training"] + old["evaluation"]["held"]
        self.assertEqual((len(old["training"]), len(old["evaluation"]["held"])), (96, 48))
        old_triples = set()
        for row in prior:
            facts = row["source"]["public_facts"]
            old_triples.update(tuple(entry["action"]) for entry in facts["belief_card"])
            old_triples.update((tuple(facts["selected_action"]), tuple(facts["earlier_action"])))
        new_triples = set()
        for row in self.material["rows"][::2]:
            facts = row["source"]["public_facts"]
            triples = {tuple(entry["action"]) for entry in facts["belief_card"]}
            triples.update((tuple(facts["selected_action"]), tuple(facts["earlier_action"])))
            self.assertFalse(triples & old_triples)
            self.assertFalse(triples & new_triples)
            new_triples.update(triples)
        audit = self.material["disjointness_audit"]
        self.assertTrue(audit["passed"])
        self.assertEqual(audit["new_unique_action_triples"], len(new_triples))
        for split, count in (("train", 96), ("held", 48)):
            self.assertEqual(audit["original"][split]["source_count"], count)
            self.assertEqual(audit["original"][split]["overlap"], [])
            self.assertEqual(len(audit["original"][split]["source_ids"]), count)

    def test_paired_prompts_have_identical_public_card_and_history(self):
        for full, minimal in zip(self.material["rows"][::2], self.material["rows"][1::2]):
            for row in (full, minimal):
                self.assertEqual(row["input_messages"], [{"role": "user", "content": row["prompt"]}])
            full_card = full["prompt"].split("Public belief card:\n", 1)[1].split("\nUse exactly", 1)[0]
            minimal_card = minimal["prompt"].split("Public belief card:\n", 1)[1].split("\nReturn one", 1)[0]
            self.assertEqual(full_card, minimal_card)
            for prefix in ("Earlier, different action:", "Earlier explicit prediction:", "Earlier public outcome:"):
                full_line = next(line for line in full["prompt"].splitlines() if line.startswith(prefix))
                self.assertIn(full_line, minimal["prompt"].splitlines())
            evidence, instruction = self.frozen_api._render(full["source"])
            self.assertIn(evidence + "\n" + instruction, full["prompt"])
            self.assertIn(transfer.MINIMAL_SEMANTICS, minimal["prompt"])
            self.assertIn("Report what follows from the supplied facts alone", minimal["prompt"])
            for removed in ("For uniquely supported output", "Otherwise use", "unresolved: abstain",
                            "classroom", "exercise", "predictions cannot fill gaps"):
                self.assertNotIn(removed.lower(), minimal["prompt"].lower())

    def test_no_evaluator_answer_leakage_or_reused_skin(self):
        for row in self.material["rows"]:
            prompt = row["prompt"]
            self.assertNotIn(row["raw_target"], prompt)
            for metadata in (row["row_id"], row["case_id"], row["case"], row["source_sha256"],
                             "raw_target", '"expected"', "source_group_id"):
                self.assertNotIn(metadata, prompt)
            for vocabulary in ('"decision"', '"prediction"', '"reason"', '"predict"',
                               '"abstain"', "true", "false", "null", '"public_evidence"',
                               '"insufficient_evidence"'):
                self.assertIn(vocabulary, prompt)
            for skin in self.frozen_api.SKINS:
                self.assertFalse(prompt.startswith(skin.split("{evidence}")[0]))

    def test_all_canonical_targets_use_unmocked_frozen_scorer(self):
        for row in self.material["rows"]:
            with self.subTest(row=row["row_id"]):
                observed = transfer.score_response(row, row["raw_target"], "stop")
                legacy = self.frozen_api._row(copy.deepcopy(row["source"]), 0)
                expected = self.frozen_api.score_row(legacy, row["raw_target"], "stop")
                self.assertEqual(observed, expected)
                self.assertTrue(observed["content_correct"])
                self.assertTrue(observed["strict"])

    def test_wrong_values_types_keys_and_length_fail(self):
        for row in self.material["rows"]:
            wrong = dict(row["expected"])
            wrong["prediction"] = False if wrong["prediction"] is True else True
            self.assertFalse(transfer.score_response(row, json.dumps(wrong), "stop")["passed"])
            self.assertFalse(transfer.score_response(row, row["raw_target"], "length")["passed"])
        row = next(row for row in self.material["rows"] if row["case"] == "supported_true")
        for response in ('{"decision":"predict","prediction":1,"reason":"public_evidence"}',
                         '{"decision":"predict","prediction":true,"reason":"wrong"}',
                         '{"decision":"predict","prediction":true,"reason":"public_evidence","extra":0}',
                         '{"decision":"predict","prediction":true,"prediction":true,"reason":"public_evidence"}',
                         "null", "NaN", None):
            self.assertFalse(transfer.score_response(row, response, "stop")["passed"])

    def test_content_and_format_policy_is_not_silently_tightened(self):
        row = self.material["rows"][0]
        for raw in (json.dumps(row["expected"], indent=2), "```json\n" + row["raw_target"] + "\n```"):
            result = transfer.score_response(row, raw, "stop")
            self.assertTrue(result["passed"])
            self.assertFalse(result["strict"])
            self.assertEqual(result["raw"], raw)

    def test_transfer_row_integrity_not_old_prompt_bypass(self):
        original = self.material["rows"][0]
        for field, value in (("prompt", "changed"), ("raw_target", "{}"), ("expected", {}),
                             ("max_new_tokens", 193), ("view", "MINIMAL"), ("source_sha256", "0" * 64),
                             ("input_messages", []), ("case", "missing"), ("row_id", [])):
            row = copy.deepcopy(original)
            row[field] = value
            with self.subTest(field=field), self.assertRaises(transfer.MaterialIntegrityError):
                transfer.score_response(row, original["raw_target"], "stop")
        row = copy.deepcopy(original)
        row["source"]["public_facts"]["selected_action"][0] += 1
        with self.assertRaises(transfer.MaterialIntegrityError):
            transfer.score_response(row, original["raw_target"], "stop")

    def test_dependency_pin_relocation_and_failure_before_execution(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "frozen.py"
            data = transfer.ORIGINAL_MATERIAL_PATH.read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), transfer.ORIGINAL_MATERIAL_SHA256)
            path.write_bytes(data)
            material = transfer.build_material(original_material_path=path)
            self.assertEqual(material["rows"], self.material["rows"])
            self.assertTrue(transfer.score_response(material["rows"][0], material["rows"][0]["raw_target"],
                                                    "stop", original_material_path=path)["strict"])
            path.write_text("raise RuntimeError('must not execute unpinned source')\n")
            with self.assertRaises(transfer.MaterialIntegrityError):
                transfer.build_material(original_material_path=path)
            with self.assertRaises(transfer.MaterialIntegrityError):
                transfer.score_response(self.material["rows"][0], "{}", "stop", original_material_path=path)

    def test_json_roundtrip_determinism_budget_and_no_training_export(self):
        material = transfer.build_material()
        self.assertEqual(material, self.material)
        self.assertEqual(json.loads(json.dumps(material)), material)
        digest = material.pop("material_sha256")
        self.assertEqual(digest, transfer._sha(material))
        self.assertEqual(material["max_new_tokens"], 192)
        self.assertTrue(all(row["max_new_tokens"] == 192 for row in material["rows"]))
        self.assertFalse(material["provenance"]["training_or_write_export"])
        self.assertFalse(material["provenance"]["model_outputs_used"])
        self.assertNotIn("training", material)
        material["rows"][0]["source"]["public_facts"]["selected_action"][0] = 0
        self.assertEqual(transfer.build_material(), self.material)


if __name__ == "__main__":
    unittest.main()
