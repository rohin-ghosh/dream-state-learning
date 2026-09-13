import copy
from collections import Counter, defaultdict
import hashlib
import json
import unittest

import astra_level1_prediction_goal_material_20260913 as material


class AuthoredMaterialTests(unittest.TestCase):
    def test_counts_disjoint_sources_and_fixed_skins(self):
        for skill in material.SKILLS:
            data = material.build_dataset(skill)
            self.assertEqual(len(data["training"]), 96)
            self.assertEqual(len(data["evaluation"]["held"]), 48)
            self.assertEqual(len(data["evaluation"]["canary"]), 12)
            seen = []
            actions = []
            for rows, count in ((data["training"], 96), (data["evaluation"]["held"], 48)):
                situations = defaultdict(set)
                action_set = set()
                for row in rows:
                    source = row["source"]
                    situations[source["situation_id"]].add(source["skin_id"])
                    self.assertIn("source_group_id", source)
                    self.assertEqual(source["parent_source_ids"], [])
                    facts = source["public_facts"]
                    selected = [facts["selected_action"]] if skill == "prediction" else [entry["action"] for entry in facts["goal"]]
                    action_set.update(tuple(action) for action in selected)
                self.assertEqual(len(situations), count)
                self.assertTrue(all(len(skins) == 1 for skins in situations.values()))
                self.assertEqual(Counter(row["source"]["skin_id"] for row in rows), {skin: count // 4 for skin in range(4)})
                self.assertEqual(len({material._json(row["source"]["public_facts"]) for row in rows}), count)
                self.assertEqual(len({row["input_messages"][0]["content"] for row in rows}), len(rows))
                seen.append(set(situations))
                actions.append(action_set)
            self.assertFalse(seen[0] & seen[1])
            self.assertFalse(actions[0] & actions[1])

    def test_source_fact_targets_and_strict_scoring(self):
        for skill in material.SKILLS:
            data = material.build_dataset(skill)
            for row in data["training"] + data["evaluation"]["held"] + data["evaluation"]["canary"]:
                target = json.loads(row["raw_target"])
                facts = row["source"]["public_facts"]
                task = row["source"]["task"]
                if task == "prediction":
                    observed = {entry["outcome"] for entry in facts["belief_card"] if entry["action"] == facts["selected_action"]}
                    self.assertEqual(target["prediction"], next(iter(observed)) if len(observed) == 1 else None)
                    self.assertEqual(target["decision"], "predict" if len(observed) == 1 else "abstain")
                    self.assertNotEqual(facts["selected_action"], facts["earlier_action"])
                elif task == "goal_completion":
                    actual = defaultdict(set)
                    for entry in facts["verified_state"]:
                        actual[tuple(entry["action"])].add(entry["outcome"])
                    completed = all(actual[tuple(entry["action"])] == {entry["outcome"]} for entry in facts["goal"])
                    self.assertEqual(target["goal_complete"], completed)
                elif task == "arithmetic":
                    self.assertEqual(target["answer"], facts["left"] + facts["right"])
                else:
                    self.assertEqual(target["answer"], facts["text"])
                self.assertEqual(row["target_sha256"], hashlib.sha256(row["raw_target"].encode()).hexdigest())
                self.assertTrue(material.score_row(row, row["raw_target"], "stop")["strict"])

    def test_balance_and_no_earlier_prediction_shortcut(self):
        data = material.build_dataset("prediction")
        for rows, expected in ((data["training"], 32), (data["evaluation"]["held"], 16)):
            outcomes = Counter(json.loads(row["raw_target"])["prediction"] for row in rows)
            self.assertEqual(outcomes, {False: expected, True: expected, None: expected})
            crossed = defaultdict(Counter)
            for row in rows:
                facts = row["source"]["public_facts"]
                crossed[(row["source"]["skin_id"], facts["earlier_outcome"], facts["earlier_prediction"])][json.loads(row["raw_target"])["prediction"]] += 1
            self.assertEqual(len(crossed), 16)
            self.assertTrue(all(len(counts) == 3 and len(set(counts.values())) == 1 for counts in crossed.values()))
        self.assertEqual({row["source"]["case"] for row in data["training"]}, {"uniquely_supported_card", "missing_evidence", "conflicting_evidence"})
        data = material.build_dataset("goal_completion")
        for rows in (data["training"], data["evaluation"]["held"]):
            crossed = defaultdict(Counter)
            for row in rows:
                facts = row["source"]["public_facts"]
                crossed[(row["source"]["skin_id"], facts["goal"][0]["outcome"], facts["earlier_outcome"], row["source"]["case"])][json.loads(row["raw_target"])["decision"]] += 1
            self.assertTrue(all(counts["complete"] == counts["continue"] > 0 for counts in crossed.values()))
            self.assertEqual(Counter(json.loads(row["raw_target"])["decision"] for row in rows), {"complete": len(rows) // 2, "continue": len(rows) // 2})

    def test_reproducible_seed_only_order_and_no_metadata_in_prompt(self):
        for skill in material.SKILLS:
            first = material.build_dataset(skill, 0)
            self.assertEqual(first, material.build_dataset(skill, 0))
            changed = material.build_dataset(skill, 71)
            self.assertNotEqual(first["training"], changed["training"])
            self.assertEqual(sorted(first["training"], key=lambda row: row["row_id"]), sorted(changed["training"], key=lambda row: row["row_id"]))
            for row in first["training"] + first["evaluation"]["held"]:
                prompt = row["input_messages"][0]["content"]
                for forbidden in (row["row_id"], row["source"]["situation_id"], row["source"]["case"], "source_proof", "target_sha256"):
                    self.assertNotIn(forbidden, prompt)
            first["training"][0]["source"]["case"] = "mutated"
            self.assertNotEqual(first, material.build_dataset(skill))
        for bad in (True, 1.5, "0"):
            with self.assertRaises(ValueError):
                material.build_dataset("prediction", bad)
        with self.assertRaises(ValueError):
            material.build_dataset("unrelated_benchmark")

    def test_scorer_rejects_errors_without_repair(self):
        row = next(row for row in material.build_dataset("prediction")["training"] if '"prediction":true' in row["raw_target"])
        invalid = (None, "", row["raw_target"] + " trailing", "[]", "null", "{}",
                   '{"decision":"predict","prediction":1,"reason":"public_evidence"}',
                   '{"decision":"predict","prediction":true,"prediction":false,"reason":"public_evidence"}',
                   '{"decision":"predict","prediction":NaN,"reason":"public_evidence"}',
                   row["raw_target"].replace("true", "false"))
        for raw in invalid:
            result = material.score_row(row, raw, "stop")
            self.assertFalse(result["strict"], raw)
            self.assertFalse(result["passed"], raw)
            self.assertFalse(result["content_correct"], raw)
            self.assertTrue(result["errors"])
        result = material.score_row(row, " " + row["raw_target"], "stop")
        self.assertTrue(result["content_correct"])
        self.assertFalse(result["strict"])
        for reason in (None, "length", "eos", "tool_calls"):
            self.assertIn("finish_reason_not_stop", material.score_row(row, row["raw_target"], reason)["errors"])
        for field in ("raw_target", "target_sha256", "source_proof", "input_messages"):
            altered = copy.deepcopy(row)
            altered[field] = None
            self.assertIn("row_integrity_error", material.score_row(altered, row["raw_target"], "stop")["errors"])
        self.assertIn("row_integrity_error", material.score_row({}, "{}", "stop")["errors"])

    def test_permissive_content_and_independent_format(self):
        for skill in material.SKILLS:
            row = material.build_dataset(skill)["training"][0]
            target = row["raw_target"]
            reversed_json = json.dumps(dict(reversed(list(json.loads(target).items()))), indent=2)
            examples = ((target, "exact"), (" \n" + target + "\t", "json_noncanonical"),
                        (reversed_json, "json_noncanonical"),
                        ("```json\n" + target + "\n```", "fenced"),
                        ("```\n" + reversed_json + "\n```", "fenced"),
                        (" \r\n```json\r\n" + target + "\r\n```\t", "fenced"))
            for raw, format_kind in examples:
                result = material.score_row(row, raw, "stop")
                self.assertEqual(result["raw"], raw)
                self.assertEqual(result["format"], format_kind)
                self.assertTrue(result["content_correct"])
                self.assertTrue(result["passed"])
                self.assertEqual(result["strict"], format_kind == "exact")
                self.assertEqual(result["errors"], [])
                self.assertEqual(result["strict_errors"], [] if format_kind == "exact" else ["not_exact_canonical_format"])
                for finish in ("length", None):
                    truncated = material.score_row(row, raw, finish)
                    self.assertFalse(truncated["passed"])
                    self.assertFalse(truncated["content_correct"])
                    self.assertFalse(truncated["strict"])
                    self.assertEqual(truncated["format"], format_kind)
                    self.assertIn("finish_reason_not_stop", truncated["errors"])

    def test_fences_do_not_repair_prose_types_or_values(self):
        row = next(row for row in material.build_dataset("prediction")["training"] if '"prediction":true' in row["raw_target"])
        target = row["raw_target"]
        invalid = ("Here:\n" + target, "```json\n" + target + "\n```\nDone.",
                   "Here:\n```json\n" + target + "\n```", "```python\n" + target + "\n```",
                   "```json\n" + target, "```json\n" + target[:-1] + "\n```",
                   "```json\n" + target + "\n```\n```json\n" + target + "\n```",
                   "```json\n" + target + ",\n```", target[:-1])
        for raw in invalid:
            result = material.score_row(row, raw, "stop")
            self.assertEqual(result["format"], "unparseable", raw)
            self.assertFalse(result["passed"])
            self.assertFalse(result["strict"])
            self.assertIn("invalid_json", result["errors"])
            self.assertEqual(result["raw"], raw)
        for replacement in (1, 1.0, "true", None):
            wrong = json.loads(target)
            wrong["prediction"] = replacement
            result = material.score_row(row, "```json\n" + material._json(wrong) + "\n```", "stop")
            self.assertEqual(result["format"], "fenced")
            self.assertFalse(result["passed"])
            self.assertIn("wrong_types", result["errors"])
        wrong = json.loads(target)
        wrong["reason"] = "I reasoned from the evidence"
        result = material.score_row(row, material._json(wrong), "stop")
        self.assertEqual(result["format"], "exact")
        self.assertFalse(result["passed"])
        self.assertIn("wrong_values", result["errors"])
        arithmetic = next(row for row in material.build_dataset("prediction")["evaluation"]["canary"] if row["source"]["task"] == "arithmetic")
        self.assertIn("wrong_types", material.score_row(arithmetic, '{"answer":true}', "stop")["errors"])

    def test_raw35_does_not_change_dataset_rows(self):
        expected = {"prediction": "aa8544ddc17fe8e4f04af70c31587934c167c2bc4063ac5c861f886d981fea3b",
                    "goal_completion": "e0198ba31097b97b2ecaf21c6bdc27334ec73ced9e67d4c59469978bbf4e6441"}
        for skill, digest in expected.items():
            data = material.build_dataset(skill)
            self.assertEqual(data["provenance"]["rowset_sha256"], digest)
            self.assertEqual(data["provenance"]["primary_pass"], "content_correct")
            self.assertEqual(data["provenance"]["scoring_version"], material.SCORING_VERSION)

    def test_counterexamples_and_canary_isolation(self):
        for skill in material.SKILLS:
            data = material.build_dataset(skill)
            self.assertTrue(all(row["source"]["task"] == skill for row in data["training"]))
            canaries = data["evaluation"]["canary"]
            self.assertEqual(Counter(row["source"]["task"] for row in canaries), {"arithmetic": 6, "copy": 6})
        rows = material.build_dataset("goal_completion")["training"]
        for earlier in (True, False):
            decisions = {json.loads(row["raw_target"])["decision"] for row in rows if row["source"]["public_facts"]["earlier_outcome"] is earlier}
            self.assertEqual(decisions, {"complete", "continue"})
        missing = [row for row in rows if row["source"]["case"] == "claim_requires_verification" and json.loads(row["raw_target"])["decision"] == "continue"]
        self.assertTrue(missing)
        self.assertTrue(all(all(entry["action"] != row["source"]["public_facts"]["goal"][0]["action"] for entry in row["source"]["public_facts"]["verified_state"]) for row in missing))


if __name__ == "__main__":
    unittest.main()
