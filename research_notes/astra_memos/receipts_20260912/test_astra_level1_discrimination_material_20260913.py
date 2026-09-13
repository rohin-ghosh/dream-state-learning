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


PATH = Path(__file__).with_name("astra_level1_discrimination_material_20260913.py")
SPEC = importlib.util.spec_from_file_location("material", PATH)
material = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(material)


class MaterialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.datasets = {skill: material.build_dataset(skill) for skill in material.SKILLS}
        cls.helper = material.corpus()

    def test_exact_sizes_and_required_fields(self):
        required = {"row_id", "input_messages", "raw_target", "target_sha256", "source", "source_proof"}
        for dataset in self.datasets.values():
            self.assertEqual(len(dataset["training"]), 96)
            self.assertEqual({key: len(rows) for key, rows in dataset["evaluation"].items()}, {"held": 48, "canary": 12})
            for split, size, per_skin in (("train", 96, 24), ("held", 48, 12)):
                inventory = dataset["provenance"]["source_inventory"][split]
                self.assertEqual([inventory[key] for key in ("rows", "distinct_sources", "distinct_selected_triples")], [size] * 3)
                self.assertEqual(set(inventory["rows_per_skin"].values()), {per_skin})
            for row in dataset["training"] + dataset["evaluation"]["held"] + dataset["evaluation"]["canary"]:
                self.assertTrue(required <= row.keys())
                self.assertIsInstance(row["raw_target"], str)
                self.assertEqual(row["target_sha256"], material.sha(row["raw_target"].encode()))

    def test_label_and_skin_balance(self):
        for skill, dataset in self.datasets.items():
            label = "verdict" if skill == "contradiction" else "decision"
            for rows, count in ((dataset["training"], 8), (dataset["evaluation"]["held"], 4)):
                by_skin = defaultdict(Counter)
                for row in rows:
                    by_skin[row["source"]["template_id"]][json.loads(row["raw_target"])[label]] += 1
                self.assertEqual(len(by_skin), 4)
                for counts in by_skin.values():
                    self.assertEqual(len(counts), 3)
                    self.assertEqual(set(counts.values()), {count})

    def test_deterministic_and_seed_only_order(self):
        for skill, dataset in self.datasets.items():
            self.assertEqual(material.encoded(dataset), material.encoded(material.build_dataset(skill)))
            other = material.build_dataset(skill, seed=1)
            self.assertNotEqual([row["row_id"] for row in dataset["training"]], [row["row_id"] for row in other["training"]])
            self.assertEqual({row["row_id"]: row for row in dataset["training"]}, {row["row_id"]: row for row in other["training"]})
            self.assertEqual({row["row_id"]: row for row in dataset["evaluation"]["held"]}, {row["row_id"]: row for row in other["evaluation"]["held"]})
            self.assertEqual(dataset["evaluation"]["canary"], other["evaluation"]["canary"])

    def test_invalid_arguments(self):
        for seed in (True, False, "0", -1, 1.0, float("nan"), 2**32):
            with self.assertRaises(ValueError):
                material.build_dataset("contradiction", seed)
        for skill in ("judgement", "reflection", "", None):
            with self.assertRaises(ValueError):
                material.build_dataset(skill)

    def test_disjoint_sources_triples_and_prompts(self):
        for dataset in self.datasets.values():
            train = dataset["training"]
            held = dataset["evaluation"]["held"]
            self.assertFalse({row["row_id"] for row in train} & {row["row_id"] for row in held})
            triple_sets = []
            for rows in (train, held):
                triples = [tuple(self.helper._interface().parse_action(event["raw_response"], "interaction_v3")["values"])
                           for row in rows for event in row["source"]["events"]]
                self.assertEqual(len(triples), len(set(triples)))
                triple_sets.append(set(triples))
            self.assertFalse(triple_sets[0] & triple_sets[1])
            self.assertFalse({row["input_messages"][0]["content"] for row in train} & {row["input_messages"][0]["content"] for row in held})
            self.assertFalse(set(material.TRAIN_SKINS) & set(material.HELD_SKINS))

    def test_earlier_shortcut_balanced(self):
        for skill, dataset in self.datasets.items():
            for rows in (dataset["training"], dataset["evaluation"]["held"]):
                groups = defaultdict(Counter)
                label_field = "verdict" if skill == "contradiction" else "decision"
                for row in rows:
                    state = material.assess(row["source"], self.helper)
                    if state["observed"] is not None:
                        earlier_observed = row["source"]["events"][0]["raw_outcome"].startswith("the box says: True ")
                        label = json.loads(row["raw_target"])[label_field]
                        groups[label][earlier_observed == state["observed"]] += 1
                for counts in groups.values():
                    self.assertEqual(counts[True], counts[False])

    def test_polarity_and_four_negative_subtypes(self):
        for skill, dataset in self.datasets.items():
            for rows in (dataset["training"], dataset["evaluation"]["held"]):
                reasons = Counter()
                observations = Counter()
                for row in rows:
                    target = json.loads(row["raw_target"])
                    reasons[target["reason"]] += 1
                    state = material.assess(row["source"], self.helper)
                    if state["observed"] is not None:
                        observations[state["observed"]] += 1
                self.assertEqual(observations[True], observations[False])
                negative_reasons = {"ambiguous_prediction", "missing_outcome", "outcome_action_mismatch",
                                    "missing_prediction" if skill == "contradiction" else "invalid_outcome"}
                self.assertTrue(negative_reasons <= reasons.keys())

    def test_missing_prediction_different_task_meaning(self):
        contradiction = [row for row in self.datasets["contradiction"]["training"] if json.loads(row["raw_target"])["reason"] == "missing_prediction"]
        self.assertTrue(contradiction)
        self.assertTrue(all(json.loads(row["raw_target"])["verdict"] == "insufficient" for row in contradiction))
        admitted_null = [row for row in self.datasets["update_judgement"]["training"]
                         if json.loads(row["raw_target"])["decision"] == "admit" and row["source"]["candidate_record"]["predicted"] is None]
        self.assertTrue(admitted_null)
        self.assertTrue(all(row["source"]["candidate_record"]["relation"] == "unavailable" for row in admitted_null))

    def test_rejections_require_source_not_internal_consistency(self):
        rows = self.datasets["update_judgement"]["training"]
        for row in rows:
            if json.loads(row["raw_target"])["decision"] == "reject":
                candidate = row["source"]["candidate_record"]
                self.assertEqual(candidate["relation"], material.relation(candidate["predicted"], candidate["observed"]))
                assessment = self.helper.assess_source(row["source"])
                self.assertTrue(assessment["admissible"])
                self.assertFalse(self.helper._interface().judge_record(material.canonical(candidate), assessment["execution"])["eligible"])

    def test_no_derived_labels_in_eval_transcript(self):
        for skill, dataset in self.datasets.items():
            for row in dataset["evaluation"]["held"]:
                prompt = row["input_messages"][0]["content"]
                transcript = prompt.split("\n\n" + material.INSTRUCTIONS[skill])[0]
                self.assertNotIn(row["source"]["source_id"], prompt)
                self.assertNotIn(row["raw_target"], prompt)
                self.assertNotIn('"verdict"', transcript)
                self.assertNotIn('"decision"', transcript)
                self.assertNotIn('"reason"', transcript)

    def test_all_targets_pass(self):
        for dataset in self.datasets.values():
            for row in dataset["training"] + dataset["evaluation"]["held"] + dataset["evaluation"]["canary"]:
                self.assertTrue(material.score_row(row, row["raw_target"], "stop")["passed"])

    def test_schema_syntax_and_source_errors_separate(self):
        for dataset in self.datasets.values():
            row = dataset["training"][0]
            for raw in (None, "Prose before\n```json\n" + row["raw_target"] + "\n```", '{"event_id":"e1","event_id":"e1"}', "NaN"):
                score = material.score_row(row, raw, "stop")
                self.assertFalse(score["passed"])
                self.assertTrue(score["syntax_errors"] or score["schema_errors"])
                self.assertFalse(score["source_errors"])
            response = json.loads(row["raw_target"])
            response["event_id"] = True
            self.assertTrue(material.score_row(row, json.dumps(response), "stop")["schema_errors"])
            response["event_id"] = "e0"
            score = material.score_row(row, json.dumps(response), "stop")
            self.assertEqual(score["source_errors"], ["event_id"])
            self.assertFalse(score["schema_errors"])

    def test_truncation_and_missing_never_pass(self):
        row = self.datasets["contradiction"]["training"][0]
        for reason in ("length", "error", None, "missing"):
            score = material.score_row(row, row["raw_target"], reason)
            self.assertFalse(score["passed"])
            self.assertFalse(score["content_correct"])
            self.assertFalse(score["strict"])
            self.assertTrue(score["completion_errors"])

    def test_source_target_and_proof_tampering_reject(self):
        original = self.datasets["contradiction"]["training"][0]
        for field in ("source", "target", "proof", "prompt"):
            row = copy.deepcopy(original)
            if field == "source":
                row["source"]["events"][-1]["raw_outcome"] = None
            elif field == "target":
                row["raw_target"] += " "
            elif field == "proof":
                row["source_proof"]["parsed_evidence"]["event_id"] = "e0"
            else:
                row["input_messages"][0]["content"] += " fabricated hint"
            with self.assertRaises(ValueError):
                material.score_row(row, row["raw_target"], "stop")

    def test_canary_shared_exact_and_no_recipe(self):
        left, right = self.datasets.values()
        self.assertEqual(left["evaluation"]["canary"], right["evaluation"]["canary"])
        rows = left["evaluation"]["canary"]
        self.assertEqual(Counter(row["skill"] for row in rows), {"addition": 6, "copy": 6})
        for row in rows:
            score = material.score_row(row, " " + row["raw_target"], "stop")
            self.assertEqual(score["passed"], row["skill"] == "addition")
            self.assertFalse(score["strict"])
        self.assertNotIn("learning_rate", material.canonical(left))
        self.assertIsNone(left["provenance"]["context_tokens"])

    def test_cli_fresh_only_and_json_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.json"
            command = [sys.executable, "-B", str(PATH), "--skill", "contradiction", "--output", str(path)]
            completed = subprocess.run(command, capture_output=True, text=True, timeout=15, check=True)
            self.assertEqual(json.loads(completed.stdout)["sha256"], material.sha(path.read_bytes()))
            self.assertEqual(path.read_bytes(), material.encoded(self.datasets["contradiction"]))
            row = json.loads(path.read_bytes())["training"][0]
            self.assertTrue(material.score_row(row, row["raw_target"], "stop")["passed"])
            self.assertNotEqual(subprocess.run(command, capture_output=True, timeout=15).returncode, 0)

    def test_counterfactual_selected_outcome_changes_labels(self):
        for skill, dataset in self.datasets.items():
            label = "verdict" if skill == "contradiction" else "decision"
            start = "agree" if skill == "contradiction" else "admit"
            stop = "disagree" if skill == "contradiction" else "reject"
            original = next(row for row in dataset["training"] if json.loads(row["raw_target"])[label] == start)
            source = copy.deepcopy(original["source"])
            final = source["events"][-1]
            final["raw_outcome"] = final["raw_outcome"].replace("True", "OTHER").replace("False", "True").replace("OTHER", "False")
            self.helper._identify(source)
            self.assertEqual(material.expected(source, skill, self.helper)[label], stop)
            source = copy.deepcopy(original["source"])
            source["events"][0]["raw_outcome"] = source["events"][0]["raw_outcome"].replace("True", "OTHER").replace("False", "True").replace("OTHER", "False")
            self.helper._identify(source)
            self.assertEqual(material.expected(source, skill, self.helper)[label], start)

    def test_source_pin_rejects_before_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "organism_v6").mkdir()
            (root / "organism_v6/birth_skill_corpus.py").write_text("raise RuntimeError('must not execute')")
            result = subprocess.run([sys.executable, "-B", str(PATH), "--skill", "contradiction", "--output", str(root / "out.json")],
                                    env={**os.environ, "ASTRA_LEVEL1_SOURCE_ROOT": directory}, capture_output=True, text=True, timeout=10)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((root / "out.json").exists())
            command = [sys.executable, "-B", "-c", "import importlib.util; spec=importlib.util.spec_from_file_location('m'," + repr(str(PATH)) + "); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); module.build_dataset('contradiction')"]
            result = subprocess.run(command, env={**os.environ, "ASTRA_LEVEL1_SOURCE_ROOT": directory}, capture_output=True, text=True, timeout=10)
            self.assertIn("source pin mismatch", result.stderr)
            self.assertNotIn("RuntimeError: must not execute", result.stderr)

    def test_content_primary_format_secondary(self):
        for dataset in self.datasets.values():
            row = dataset["training"][0]
            target = row["raw_target"]
            reordered = dict(reversed(list(json.loads(target).items())))
            for raw, format_name, strict in (
                (target, "exact", True),
                (" \n" + target + "\t", "json_noncanonical", False),
                (json.dumps(reordered), "json_noncanonical", False),
                (json.dumps(json.loads(target), indent=2), "json_noncanonical", False),
                ("```json\n" + target + "\n```", "fenced", False),
                (" \n```\n" + target + "\n```\n", "fenced", False),
            ):
                score = material.score_row(row, raw, "stop")
                self.assertIs(score["passed"], True)
                self.assertIs(score["content_correct"], True)
                self.assertIs(score["strict"], strict)
                self.assertIs(score["strict_pass"], strict)
                self.assertEqual(score["format"], format_name)
                self.assertEqual(score["raw"], raw)
                self.assertEqual(score["raw_sha256"], material.sha(raw.encode()))
                for reason in ("length", "error"):
                    unfinished = material.score_row(row, raw, reason)
                    self.assertFalse(unfinished["passed"] or unfinished["content_correct"] or unfinished["strict"] or unfinished["strict_pass"])

    def test_fence_is_only_enclosing_wrapper_no_repair(self):
        row = self.datasets["contradiction"]["training"][0]
        target = row["raw_target"]
        for raw in ("answer: " + target, target + " after", "```json\n" + target + "\n```\nextra",
                    "```json\n" + target + "\n```\n```json\n" + target + "\n```",
                    "```python\n" + target + "\n```", "```json\n{bad}\n```",
                    "```json\n" + target, target[:-1] + ",}", "null"):
            score = material.score_row(row, raw, "stop")
            self.assertFalse(score["content_correct"] or score["strict"])
            self.assertTrue(score["syntax_errors"] or score["schema_errors"])
        for changes in ({"event_id": 1}, {"event_id": True}, {"event_id": "e0"}, {"extra": "value"}, {"reason": "Agreement"}):
            response = json.loads(target)
            response.update(changes)
            score = material.score_row(row, "```json\n" + json.dumps(response) + "\n```", "stop")
            self.assertFalse(score["content_correct"] or score["strict"])
            self.assertTrue(score["schema_errors"] or score["source_errors"])
        response = json.loads(target)
        response["event_id"] = "e0"
        score = material.score_row(row, material.canonical(response), "stop")
        self.assertEqual(score["format"], "exact")
        self.assertFalse(score["content_correct"] or score["strict"])

    def test_arithmetic_typed_json_no_bool_int_alias(self):
        row = next(row for row in self.datasets["contradiction"]["evaluation"]["canary"] if row["skill"] == "addition")
        for raw in ("true", "false", "null", row["raw_target"] + ".0", json.dumps(row["raw_target"]), "[" + row["raw_target"] + "]"):
            score = material.score_row(row, raw, "stop")
            self.assertFalse(score["content_correct"] or score["strict"])
            self.assertTrue(score["schema_errors"])
        for raw in (" \n" + row["raw_target"], "```json\n" + row["raw_target"] + "\n```"):
            score = material.score_row(row, raw, "stop")
            self.assertTrue(score["content_correct"])
            self.assertFalse(score["strict"])

    def test_raw35_changes_scoring_not_dataset_rows(self):
        pins = {"contradiction": "db9d807fb58cd9ac7dbaf437eb54bf4dd203ba0846dba023bf33cfcfbd7a9eab",
                "update_judgement": "4c48ce2df6b5bbbb3f04169e00e5dc4ab0fb99b4e4a96871a3543da026967dcf"}
        for skill, dataset in self.datasets.items():
            self.assertEqual(material.sha(material.encoded({"training": dataset["training"], "evaluation": dataset["evaluation"]})), pins[skill])


if __name__ == "__main__":
    unittest.main()
