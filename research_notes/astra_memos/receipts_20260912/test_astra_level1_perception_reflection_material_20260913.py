import copy
import importlib.util
import json
import os
from collections import Counter, defaultdict
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


PATH = Path(__file__).with_name("astra_level1_perception_reflection_material_20260913.py")
SPEC = importlib.util.spec_from_file_location("material", PATH)
material = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(material)


class MaterialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.datasets = {skill: material.build_dataset(skill) for skill in material.SKILLS}
        cls.helper, cls.reference = material.load_sources()

    def test_api_counts_sources_and_skins(self):
        for dataset in self.datasets.values():
            self.assertEqual(set(dataset), {"schema", "qualification", "provenance", "training", "evaluation"})
            self.assertEqual(set(dataset["evaluation"]), {"held", "canary"})
            all_rows = dataset["training"] + dataset["evaluation"]["held"] + dataset["evaluation"]["canary"]
            self.assertEqual(len(all_rows), 156)
            self.assertEqual(len({row["source"]["source_id"] for row in all_rows}), 156)
            self.assertEqual(len({row["row_id"] for row in all_rows}), 156)
            for row in all_rows:
                self.assertTrue({"row_id", "input_messages", "raw_target", "target_sha256", "source", "source_proof"} <= row.keys())
            for split, size, per_skin, per_case in (("train", 96, 24, 16), ("held", 48, 12, 8)):
                inventory = dataset["provenance"]["source_inventory"][split]
                self.assertEqual([inventory[key] for key in ("rows", "distinct_sources", "distinct_selected_triples")], [size] * 3)
                self.assertEqual(Counter(inventory["rows_per_skin"].values()), {per_skin: 4})
                self.assertEqual(inventory["diagnosis_counts"], {case: per_case for case in material.CASES})

    def test_determinism_and_order_only_seeds(self):
        for skill, dataset in self.datasets.items():
            self.assertEqual(material.encoded(dataset), material.encoded(material.build_dataset(skill)))
            seeded = material.build_dataset(skill, 2)
            self.assertNotEqual([row["row_id"] for row in dataset["training"]], [row["row_id"] for row in seeded["training"]])
            for original, other in ((dataset["training"], seeded["training"]), (dataset["evaluation"]["held"], seeded["evaluation"]["held"])):
                self.assertEqual({row["row_id"]: row for row in original}, {row["row_id"]: row for row in other})
            self.assertEqual(dataset["evaluation"]["canary"], seeded["evaluation"]["canary"])

    def test_invalid_skill_and_seed(self):
        for skill in ("reflection", "contradiction", "", None):
            with self.assertRaises(ValueError):
                material.build_dataset(skill)
        for seed in (True, False, "0", -1, 0.0, float("nan"), 2**32):
            with self.assertRaises(ValueError):
                material.build_dataset("perception", seed)

    def test_disjoint_all_event_triples_and_old_references(self):
        old = {tuple(triple) for triples in self.helper.SITUATIONS.values() for triple in triples} | {(20, 21, 22)}
        old.update(tuple(triple) for name in ("APPLICATION_TRIPLES", "DISTRACTOR_TRIPLES") for triple in self.reference[name])
        for dataset in self.datasets.values():
            triples = []
            prompts = []
            for row in dataset["training"] + dataset["evaluation"]["held"]:
                prompts.append(row["input_messages"][0]["content"])
                for event in row["source"]["events"]:
                    triples.append(tuple(self.helper._interface().parse_action(event["raw_response"], "interaction_v3")["values"]))
            self.assertEqual(len(triples), len(set(triples)))
            self.assertEqual(len(prompts), len(set(prompts)))
            self.assertFalse(set(triples) & old)
        self.assertFalse(set(material.TRAIN_SKINS) & set(material.HELD_SKINS))

    def test_earlier_and_observation_balance_per_case(self):
        for dataset in self.datasets.values():
            for rows in (dataset["training"], dataset["evaluation"]["held"]):
                counts = defaultdict(Counter)
                for row in rows:
                    fields, diagnosis = material.evidence(row["source"], self.helper)
                    if fields["observed"] is not None:
                        earlier = row["source"]["events"][0]["raw_outcome"].startswith("the box says: True ")
                        counts[diagnosis][(fields["observed"], earlier == fields["observed"])] += 1
                for count in counts.values():
                    self.assertEqual(len(count), 4)
                    self.assertEqual(len(set(count.values())), 1)

    def test_perception_records_exact_public_grammar(self):
        for rows, supported in ((self.datasets["perception"]["training"], 48), (self.datasets["perception"]["evaluation"]["held"], 24)):
            count = 0
            relations = Counter()
            for row in rows:
                target = json.loads(row["raw_target"])
                assessment = self.helper.assess_source(row["source"])
                if "abstain" in target:
                    self.assertEqual(set(target), {"abstain", "reason"})
                    self.assertIs(target["abstain"], True)
                    self.assertFalse(assessment["admissible"])
                else:
                    count += 1
                    self.assertEqual(set(target), {"try", "observed", "predicted", "relation"})
                    self.assertTrue(self.helper._interface().judge_record(row["raw_target"], assessment["execution"])["eligible"])
                    relations[target["relation"]] += 1
            self.assertEqual(count, supported)
            self.assertEqual(relations, {"matched": supported // 3, "mismatched": supported // 3, "unavailable": supported // 3})

    def test_missing_prior_is_not_conflicting_prior(self):
        rows = self.datasets["perception"]["training"]
        absent = next(row for row in rows if row["source_proof"]["diagnosis"] == "absent_prediction")
        ambiguous = next(row for row in rows if row["source_proof"]["diagnosis"] == "ambiguous_prediction")
        self.assertIsNone(json.loads(absent["raw_target"])["predicted"])
        self.assertEqual(json.loads(absent["raw_target"])["relation"], "unavailable")
        self.assertTrue(json.loads(ambiguous["raw_target"])["abstain"])

    def test_reflection_is_evidence_and_procedure_not_prose(self):
        for row in self.datasets["self_reflection"]["training"]:
            response = json.loads(row["raw_target"])
            self.assertEqual(set(response), {"diagnosis", "next_action", "evidence"})
            fields, diagnosis = material.evidence(row["source"], self.helper)
            self.assertEqual(response["evidence"], fields)
            self.assertEqual(response["diagnosis"], diagnosis)
            self.assertEqual(response["next_action"], material.POLICY[diagnosis])
        self.assertIn("NOT_FULL_SELF_REFLECTION", self.datasets["self_reflection"]["qualification"])
        self.assertEqual(self.datasets["self_reflection"]["provenance"]["reference_reflection_procedures"], self.reference["PROCEDURES"])

    def test_no_per_example_labels_in_held_transcript(self):
        for dataset in self.datasets.values():
            for row in dataset["evaluation"]["held"]:
                prompt = row["input_messages"][0]["content"]
                transcript = prompt.split("\n\n" + (material.PERCEPTION_TASK if row["skill"] == "perception" else material.REFLECTION_TASK))[0]
                self.assertNotIn(row["source"]["source_id"], prompt)
                self.assertNotIn(row["raw_target"], prompt)
                self.assertNotIn(row["source_proof"]["diagnosis"], transcript)

    def test_all_targets_pass(self):
        for dataset in self.datasets.values():
            for row in dataset["training"] + dataset["evaluation"]["held"] + dataset["evaluation"]["canary"]:
                score = material.score_row(row, row["raw_target"], "stop")
                self.assertTrue(score["passed"] and score["content_correct"] and score["strict"] and score["strict_pass"])
                self.assertEqual(score["format"], "exact")

    def test_primary_content_secondary_format_and_truncation(self):
        for dataset in self.datasets.values():
            row = dataset["training"][0]
            target = row["raw_target"]
            reordered = json.dumps(dict(reversed(list(json.loads(target).items()))))
            for raw, expected_format in ((" \n" + target, "json_noncanonical"), (reordered, "json_noncanonical"),
                                         ("```json\n" + target + "\n```", "fenced"), ("```\n" + target + "\n```", "fenced")):
                score = material.score_row(row, raw, "stop")
                self.assertTrue(score["passed"] and score["content_correct"])
                self.assertFalse(score["strict"])
                self.assertEqual(score["format"], expected_format)
                self.assertEqual(score["raw"], raw)
                for reason in ("length", "error", None):
                    score = material.score_row(row, raw, reason)
                    self.assertFalse(score["passed"] or score["content_correct"] or score["strict"])

    def test_prose_duplicate_keys_and_malformed_rejected(self):
        row = self.datasets["perception"]["training"][0]
        target = row["raw_target"]
        for raw in (None, "Here: " + target, target + " trailing", "```json\n" + target + "\n```\nmore",
                    '{"try":[],"try":[]}', "NaN", "```json\n{bad}\n```", "[]"):
            score = material.score_row(row, raw, "stop")
            self.assertFalse(score["passed"] or score["strict"])
            self.assertTrue(score["syntax_errors"] or score["schema_errors"])

    def test_typed_fields_no_bool_integer_alias(self):
        row = next(row for row in self.datasets["perception"]["training"] if "try" in json.loads(row["raw_target"]))
        for field, value in (("try", [True, 2, 3]), ("observed", 1), ("predicted", 0), ("relation", True)):
            response = json.loads(row["raw_target"])
            response[field] = value
            score = material.score_row(row, json.dumps(response), "stop")
            self.assertFalse(score["content_correct"])
            self.assertTrue(score["schema_errors"])
        reflection = self.datasets["self_reflection"]["training"][0]
        response = json.loads(reflection["raw_target"])
        response["evidence"]["observed"] = 1
        self.assertTrue(material.score_row(reflection, json.dumps(response), "stop")["schema_errors"])

    def test_field_errors_and_wrong_output_variant(self):
        row = next(row for row in self.datasets["perception"]["training"] if "try" in json.loads(row["raw_target"]))
        response = json.loads(row["raw_target"])
        response["observed"] = not response["observed"]
        score = material.score_row(row, material.canonical(response), "stop")
        self.assertEqual(score["source_errors"], ["observed"])
        self.assertFalse(score["field_correct"]["observed"])
        score = material.score_row(row, '{"abstain":true,"reason":"missing_outcome"}', "stop")
        self.assertEqual(score["source_errors"], ["output_variant"])
        self.assertFalse(score["schema_errors"])
        row = self.datasets["self_reflection"]["training"][0]
        response = json.loads(row["raw_target"])
        response["next_action"] = next(value for value in material.POLICY.values() if value != response["next_action"])
        score = material.score_row(row, material.canonical(response), "stop")
        self.assertEqual(score["source_errors"], ["next_action"])

    def test_counterfactual_evidence_not_earlier(self):
        for skill, dataset in self.datasets.items():
            row = next(row for row in dataset["training"] if row["source_proof"]["diagnosis"] == "agreement")
            for event_index in (0, 1):
                source = copy.deepcopy(row["source"])
                text = source["events"][event_index]["raw_outcome"]
                source["events"][event_index]["raw_outcome"] = text.replace("True", "OTHER").replace("False", "True").replace("OTHER", "False")
                self.helper._identify(source)
                new_target = material.canonical(material.expected(source, skill, self.helper))
                self.assertEqual(new_target == row["raw_target"], event_index == 0)

    def test_tampering_source_target_proof_and_prompt(self):
        original = self.datasets["perception"]["training"][0]
        for field in ("source", "target", "proof", "prompt"):
            row = copy.deepcopy(original)
            if field == "source":
                row["source"]["events"][0]["raw_response"] += " altered"
            elif field == "target":
                row["raw_target"] += " "
            elif field == "proof":
                row["source_proof"]["diagnosis"] = "bad"
            else:
                row["input_messages"][0]["content"] += " answer hint"
            with self.assertRaises(ValueError):
                material.score_row(row, row["raw_target"], "stop")

    def test_canaries_and_no_native_recipe(self):
        left, right = self.datasets.values()
        self.assertEqual(left["evaluation"]["canary"], right["evaluation"]["canary"])
        self.assertEqual(Counter(row["skill"] for row in left["evaluation"]["canary"]), {"addition": 6, "copy": 6})
        for row in left["evaluation"]["canary"]:
            score = material.score_row(row, " " + row["raw_target"], "stop")
            self.assertEqual(score["content_correct"], row["skill"] == "addition")
            self.assertFalse(score["strict"])
            if row["skill"] == "addition":
                for raw in ("true", "false", row["raw_target"] + ".0", json.dumps(row["raw_target"])):
                    self.assertFalse(material.score_row(row, raw, "stop")["content_correct"])
        self.assertIsNone(left["provenance"]["context_tokens"])
        self.assertNotIn("learning_rate", material.canonical(left))

    def test_cli_fresh_json_roundtrip_and_pin_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dataset.json"
            command = [sys.executable, "-B", str(PATH), "--skill", "perception", "--output", str(path)]
            completed = subprocess.run(command, capture_output=True, text=True, timeout=15, check=True)
            self.assertEqual(path.read_bytes(), material.encoded(self.datasets["perception"]))
            self.assertEqual(json.loads(completed.stdout)["sha256"], material.sha(path.read_bytes()))
            self.assertNotEqual(subprocess.run(command, capture_output=True, timeout=15).returncode, 0)
            alternate = Path(directory) / "absent"
            completed = subprocess.run(command, env={**os.environ, "ASTRA_LEVEL1_SOURCE_ROOT": str(alternate)}, capture_output=True, timeout=15)
            self.assertNotEqual(completed.returncode, 0)

    def test_relocated_three_source_tree_and_reference_pin(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "source"
            for relative in material.PINS:
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((material.SOURCE_ROOT / relative).read_bytes())
            output = Path(directory) / "dataset.json"
            command = [sys.executable, "-B", str(PATH), "--skill", "self_reflection", "--output", str(output)]
            environment = {**os.environ, "ASTRA_LEVEL1_SOURCE_ROOT": str(root)}
            subprocess.run(command, env=environment, capture_output=True, timeout=15, check=True)
            self.assertEqual(output.read_bytes(), material.encoded(self.datasets["self_reflection"]))
            reference = root / "organism_v6/birth_reflection_probe.py"
            reference.write_bytes(reference.read_bytes() + b"\n")
            command[-1] = str(Path(directory) / "rejected.json")
            result = subprocess.run(command, env=environment, capture_output=True, text=True, timeout=15)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("source pin mismatch: organism_v6/birth_reflection_probe.py", result.stderr)
            self.assertFalse(Path(command[-1]).exists())

    def test_false_abstention_and_nested_field_types(self):
        row = next(row for row in self.datasets["perception"]["training"] if "abstain" in json.loads(row["raw_target"]))
        for invalid in (1, "true", False):
            response = json.loads(row["raw_target"])
            response["abstain"] = invalid
            score = material.score_row(row, json.dumps(response), "stop")
            self.assertTrue(score["schema_errors"])
            self.assertFalse(score["content_correct"])
        row = self.datasets["self_reflection"]["training"][0]
        response = json.loads(row["raw_target"])
        response["evidence"]["try"][0] = True
        self.assertTrue(material.score_row(row, json.dumps(response), "stop")["schema_errors"])


if __name__ == "__main__":
    unittest.main()
