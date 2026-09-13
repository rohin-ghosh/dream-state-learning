import ast
import copy
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import unittest

import astra_level1_repetition_meta_material_20260913 as material


class VisibleDecisionTests(unittest.TestCase):
    def test_distinct_situations_skins_provenance_and_canaries(self):
        for skill in material.SKILLS:
            data = material.build_dataset(skill)
            self.assertEqual(len(data["evaluation"]["canary"]), 12)
            split_sources, split_facts, split_actions = [], [], []
            for rows, count in ((data["training"], 96), (data["evaluation"]["held"], 48)):
                self.assertEqual(len(rows), count)
                self.assertEqual(len({row["source"]["situation_id"] for row in rows}), count)
                self.assertEqual(len({material._json(row["source"]["public_facts"]) for row in rows}), count)
                self.assertEqual(len({material._json(row["input_messages"]) for row in rows}), count)
                self.assertEqual(Counter(row["source"]["skin_id"] for row in rows), {skin: count // 4 for skin in range(4)})
                self.assertEqual(len({row["source"]["source_group_id"] for row in rows}), count // 6)
                split_sources.append({row["source"]["situation_id"] for row in rows})
                split_facts.append({material._json(row["source"]["public_facts"]) for row in rows})
                actions = set()
                for row in rows:
                    source = row["source"]
                    facts = source["public_facts"]
                    action = facts["nominated_record"]["action"] if skill == "repetition" else facts["practice_action"]
                    actions.add(tuple(action))
                    self.assertEqual(source["parent_source_ids"], [])
                    prompt = row["input_messages"][0]["content"]
                    for metadata in (source["situation_id"], source["source_group_id"], source["case"], "source_proof", "target_sha256"):
                        self.assertNotIn(metadata, prompt)
                    self.assertEqual(row["target_sha256"], hashlib.sha256(row["raw_target"].encode()).hexdigest())
                self.assertEqual(len(actions), count)
                split_actions.append(actions)
            for pair in (split_sources, split_facts, split_actions):
                self.assertFalse(pair[0] & pair[1])
            self.assertEqual(Counter(row["source"]["task"] for row in data["evaluation"]["canary"]), {"arithmetic": 6, "copy": 6})
            self.assertTrue(all(row["source"]["task"] == skill for row in data["training"]))

    def test_repetition_expected_cases_budget_and_support(self):
        data = material.build_dataset("repetition")
        reasons = ("important", "unresolved", "important", "irrelevant", "settled", "budget_exhausted")
        for rows in (data["training"], data["evaluation"]["held"]):
            crossed = defaultdict(Counter)
            for row in rows:
                facts = row["source"]["public_facts"]
                record = facts["nominated_record"]
                case = int(row["source"]["case"].rsplit("_", 1)[1])
                target = json.loads(row["raw_target"])
                self.assertEqual(target, {"decision": "rehearse" if case < 3 else "skip",
                                          "reason": reasons[case], "independent_support_after": record["independent_support"]})
                if target["decision"] == "rehearse":
                    self.assertLessEqual(record["review_cost"], facts["remaining_budget"])
                    self.assertIn(record["task"], facts["current_goal_tasks"])
                crossed[(row["source"]["skin_id"], record["verified_outcome"], facts["earlier_unrelated_public_outcome"])][target["decision"]] += 1
            self.assertTrue(all(counts["rehearse"] == counts["skip"] > 0 for counts in crossed.values()))
        settled = [row for row in data["training"] if row["source"]["case"] == "replay_pattern_4"]
        self.assertTrue(any(row["source"]["public_facts"]["nominated_record"]["prediction"] != row["source"]["public_facts"]["nominated_record"]["verified_outcome"] for row in settled))
        for row in data["training"]:
            altered = copy.deepcopy(row["source"])
            altered["public_facts"]["nominated_record"]["times_rehearsed"] += 1000
            self.assertEqual(material._expected(altered), json.loads(row["raw_target"]))

    def test_meta_patterns_balance_and_warrant(self):
        data = material.build_dataset("meta_reflection")
        for rows in (data["training"], data["evaluation"]["held"]):
            grouped = defaultdict(Counter)
            for row in rows:
                facts = row["source"]["public_facts"]
                case = int(row["source"]["case"].rsplit("_", 1)[1])
                target = json.loads(row["raw_target"])
                self.assertEqual((target["diagnosis"], target["next_action"]), material.DIAGNOSES[case])
                if case == 0:
                    self.assertGreater(facts["verified_after"]["practiced_correct"], facts["verified_before"]["practiced_correct"])
                    self.assertEqual(facts["verified_after"]["new_correct"], facts["verified_before"]["new_correct"])
                elif case == 1:
                    self.assertLess(facts["delayed_check"]["correct"], facts["immediate_check"]["correct"])
                elif case == 3:
                    self.assertNotEqual(facts["practiced_target"], facts["verified_correct_target"])
                elif case == 4:
                    self.assertTrue(any(facts["verified_before"][key] != facts["verified_after"][key] for key in ("assessment_id", "total")))
                elif case == 5:
                    self.assertIsNone(facts["verified_after"])
                grouped[(row["source"]["skin_id"], facts["earlier_unrelated_public_outcome"], facts["verified_correct_target"])][target["diagnosis"]] += 1
                altered = copy.deepcopy(row["source"])
                altered["public_facts"]["learner_self_report"] = "My hidden feelings prove success."
                self.assertEqual(material._expected(altered), target)
            self.assertTrue(all(len(counts) == 6 and len(set(counts.values())) == 1 for counts in grouped.values()))

    def test_scorer_exact_noncanonical_fenced_and_truncation(self):
        for skill in material.SKILLS:
            data = material.build_dataset(skill)
            for row in data["training"] + data["evaluation"]["held"] + data["evaluation"]["canary"]:
                exact = row["raw_target"]
                variants = ((exact, "exact"), (json.dumps(dict(reversed(list(json.loads(exact).items()))), indent=2), "json_noncanonical"),
                            ("```json\n" + exact + "\n```", "fenced"), (" \n```\n" + exact + "\n```\t", "fenced"))
                for raw, kind in variants:
                    result = material.score_row(row, raw, "stop")
                    self.assertTrue(result["passed"])
                    self.assertTrue(result["content_correct"])
                    self.assertEqual(result["strict"], kind == "exact")
                    self.assertEqual(result["format"], kind)
                    self.assertEqual(result["raw"], raw)
                    self.assertEqual(result["errors"], [])
                    failed = material.score_row(row, raw, "length")
                    self.assertFalse(failed["passed"])
                    self.assertFalse(failed["strict"])

    def test_no_repair_and_integrity_failures(self):
        row = material.build_dataset("repetition")["training"][0]
        exact = row["raw_target"]
        for raw in (None, "", exact[:-1], "Here: " + exact, "```json\n" + exact + "\n```\nDone", "[]", "null", "{}",
                    '{"decision":"skip","decision":"rehearse"}', '{"independent_support_after":NaN}'):
            result = material.score_row(row, raw, "stop")
            self.assertFalse(result["passed"])
            self.assertFalse(result["strict"])
            self.assertTrue(result["errors"])
        for value in (True, 1.0, "1"):
            wrong = json.loads(exact)
            wrong["independent_support_after"] = value
            result = material.score_row(row, material._json(wrong), "stop")
            self.assertFalse(result["passed"])
            self.assertIn("wrong_types", result["errors"])
        wrong = json.loads(exact)
        wrong["reason"] = "this is my explanation"
        self.assertIn("wrong_values", material.score_row(row, material._json(wrong), "stop")["errors"])
        for key in ("source_proof", "raw_target", "target_sha256", "input_messages"):
            altered = copy.deepcopy(row)
            altered[key] = None
            self.assertFalse(material.score_row(altered, exact, "stop")["passed"])

    def test_seed_reproducibility_and_independent_data(self):
        for skill in material.SKILLS:
            data = material.build_dataset(skill)
            self.assertEqual(data, material.build_dataset(skill))
            changed = material.build_dataset(skill, 72)
            self.assertNotEqual(data["training"], changed["training"])
            self.assertEqual(sorted(data["training"], key=lambda row: row["row_id"]), sorted(changed["training"], key=lambda row: row["row_id"]))
            data["training"][0]["source"]["case"] = "edited"
            self.assertNotEqual(data, material.build_dataset(skill))
        for skill, seed in (("emotions", 0), ("repetition", True), ("meta_reflection", "0")):
            with self.assertRaises(ValueError):
                material.build_dataset(skill, seed)

    def test_frozen_prediction_goal_preserved_and_shared_scorer(self):
        frozen = Path("/tmp/astra_level1_prediction_goal_material_20260913.py").read_text()
        self.assertEqual(hashlib.sha256(frozen.encode()).hexdigest(), material.INFRASTRUCTURE_SHA256)
        local = Path(material.__file__).read_text()
        def definitions(text):
            return {node.name: ast.dump(node, include_attributes=False) for node in ast.parse(text).body if isinstance(node, ast.FunctionDef)}
        previous, current = definitions(frozen), definitions(local)
        for name in ("_json", "_sha", "_source", "_row", "_unique_object", "_reject_constant", "score_row"):
            self.assertEqual(previous[name], current[name], name)
        import astra_level1_prediction_goal_material_20260913 as previous_material
        old = previous_material.build_dataset("prediction")
        new = material.build_dataset("repetition")
        old_facts = {material._json(row["source"]["public_facts"]) for row in old["training"] + old["evaluation"]["held"] + old["evaluation"]["canary"]}
        new_facts = {material._json(row["source"]["public_facts"]) for row in new["training"] + new["evaluation"]["held"] + new["evaluation"]["canary"]}
        self.assertFalse(old_facts & new_facts)


if __name__ == "__main__":
    unittest.main()
