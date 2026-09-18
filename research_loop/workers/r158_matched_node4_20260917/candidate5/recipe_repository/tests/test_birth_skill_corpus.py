"""CPU public-situation fixtures only; no model, hidden-rule or native calls."""
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

from organism_v6 import birth_skill_corpus as corpus


ANCHOR = "Keep observations distinct from predictions, reflect on discrepancies, and admit only supported records."


class BirthSkillCorpusTests(unittest.TestCase):
    def build(self, skill="perception", split="train", anchor=None, seed=corpus.SEED):
        return corpus.build_slice(skill, split=split, system_anchor=anchor, seed=seed)

    def revise(self, source, **event_fields):
        revised = copy.deepcopy(source)
        revised["events"][-1].update(event_fields)
        return corpus._identify(revised)

    def test_explicit_skill_split_anchor_and_seed_required(self):
        for skill in (None, "all", "mixture", ""):
            with self.subTest(skill=skill), self.assertRaises(ValueError):
                self.build(skill)
        for split in (None, "test", "held", "TRAIN"):
            with self.subTest(split=split), self.assertRaises(ValueError):
                self.build(split=split)
        for anchor in ("", "  ", False, 7):
            with self.subTest(anchor=anchor), self.assertRaises(ValueError):
                self.build(anchor=anchor)
        with self.assertRaises(TypeError):
            corpus.build_slice("perception", split="train")
        with self.assertRaises(ValueError):
            self.build(seed=True)
        with self.assertRaises(ValueError):
            corpus.build_variants("perception", split="train", system_anchor=None)

    def test_counts_balance_origin_and_claim_boundaries(self):
        for skill in corpus.SKILLS:
            for split in ("train", "dev"):
                with self.subTest(skill=skill, split=split):
                    built = self.build(skill, split)
                    manifest = built["manifest"]
                    self.assertEqual(manifest["row_count"], 24 if skill == "judgement" else 12)
                    self.assertEqual(manifest["target_count"], 12)
                    self.assertEqual(manifest["origin"], "AUTHOR_SOURCED_DEVELOPMENT_ONLY")
                    self.assertFalse(manifest["training_export_ready"])
                    self.assertEqual(manifest["native_use_status"], "MAIN_REVIEW_REQUIRED")
                    self.assertIn("NOT_L2", manifest["qualification"])
                    self.assertEqual(manifest["audit"]["input_target_collisions"], 0)
                    self.assertEqual(manifest["audit"]["duplicate_inputs"], 0)
                    self.assertTrue(manifest["audit"]["balanced_per_template_and_triple"])
                    self.assertTrue(manifest["audit"]["judgement_pairing_complete"])
                    self.assertEqual({row["skill"] for row in built["rows"]}, {skill})

    def test_anchor_is_only_input_difference(self):
        exact_anchor = "  " + ANCHOR + "\n"
        for skill in corpus.SKILLS:
            variants = corpus.build_variants(skill, split="dev", system_anchor=exact_anchor)
            for supplied, absent in zip(variants["supplied"]["rows"], variants["absent"]["rows"]):
                self.assertEqual(supplied["input_messages"][0], {"role": "system", "content": exact_anchor})
                self.assertEqual(supplied["input_messages"][1:], absent["input_messages"])
                for field in ("row_id", "source", "source_proof", "raw_target", "target_sha256"):
                    self.assertEqual(supplied[field], absent[field])
                self.assertNotEqual(supplied["input_sha256"], absent["input_sha256"])
            self.assertEqual(variants["supplied"]["manifest"]["system_anchor"], exact_anchor)
            self.assertIsNone(variants["absent"]["manifest"]["system_anchor"])
            self.assertIn("not evidence", variants["absent"]["manifest"]["persistence"])

    def test_determinism_seed_only_orders_and_manifest_hashes(self):
        first = self.build()
        self.assertEqual(first, self.build())
        reordered = self.build(seed=41)
        original_ids = [row["row_id"] for row in first["rows"]]
        self.assertNotEqual(original_ids, [row["row_id"] for row in reordered["rows"]])
        self.assertEqual(sorted(first["rows"], key=lambda row: row["row_id"]),
                         sorted(reordered["rows"], key=lambda row: row["row_id"]))
        encoded = json.dumps(first["rows"], sort_keys=True, ensure_ascii=False, allow_nan=False).encode()
        self.assertEqual(first["manifest"]["rows_sha256"], hashlib.sha256(encoded).hexdigest())
        self.assertEqual(len(first["manifest"]["source_manifest"]), 12)
        self.assertEqual(first["manifest"]["literal_split_situations"], corpus.SITUATIONS)
        self.assertEqual(first["manifest"]["template_manifest"], corpus.TEMPLATES)

    def test_returned_manifest_mutation_does_not_change_future_builds(self):
        first = self.build()
        original = copy.deepcopy(first)
        first["manifest"]["template_manifest"]["train"] = "corrupted"
        first["manifest"]["interface"]["definitions"].clear()
        first["rows"][0]["source"]["events"].clear()
        self.assertEqual(self.build(), original)

    def test_literal_split_disjointness_and_shared_correlated_situations(self):
        sources_by_skill = {}
        for skill in corpus.SKILLS:
            train, dev = self.build(skill), self.build(skill, "dev")
            self.assertTrue(corpus.audit_split_pair(train, dev)["disjoint"])
            sources_by_skill[skill] = {row["source"]["source_id"] for row in dev["rows"]
                                      if "derivation" not in row["source"]}
        self.assertEqual(sources_by_skill["perception"], sources_by_skill["reflection"])
        self.assertEqual(sources_by_skill["perception"], sources_by_skill["judgement"])
        self.assertFalse(set(corpus.SITUATIONS["train"]) & set(corpus.SITUATIONS["dev"]))
        with self.assertRaises(ValueError):
            corpus.audit_split_pair(self.build(split="dev"), self.build())
        with self.assertRaises(ValueError):
            corpus.audit_split_pair(self.build(), self.build("reflection", "dev"))

    def test_all_targets_have_raw_event_proofs_and_pass_existing_parser(self):
        for skill in corpus.SKILLS:
            for split in ("train", "dev"):
                for row in self.build(skill, split)["rows"]:
                    source = row["source"]
                    event = source["events"][-1]
                    for field in ("try", "observed", "predicted", "relation"):
                        proof = row["source_proof"][field]
                        self.assertEqual(proof["source_id"], source["source_id"])
                        self.assertEqual(proof["event_id"], event["event_id"])
                        if "field" in proof:
                            self.assertEqual(proof["raw"], event[proof["field"]])
                    if row["raw_target"] is not None:
                        self.assertTrue(corpus.score_response(row, row["raw_target"])["passed"])
                        self.assertEqual(row["target_sha256"], hashlib.sha256(row["raw_target"].encode()).hexdigest())
                        if skill != "reflection":
                            decoded = json.loads(row["raw_target"])
                            self.assertEqual(set(decoded), {"try", "observed", "predicted", "relation"})
                            for field in decoded:
                                self.assertEqual(decoded[field], row["source_proof"][field]["value"])

    def test_six_semantic_cases_hand_checked_without_hidden_rule(self):
        expected = {
            "matched_true": (True, True, "matched"),
            "matched_false": (False, False, "matched"),
            "mismatched_true": (False, True, "mismatched"),
            "mismatched_false": (True, False, "mismatched"),
            "unavailable_true": (None, True, "unavailable"),
            "unavailable_false": (None, False, "unavailable"),
        }
        for row in self.build()["rows"]:
            record = json.loads(row["raw_target"])
            self.assertEqual((record["predicted"], record["observed"], record["relation"]), expected[row["source"]["case"]])

    def test_no_triple_template_or_earlier_outcome_shortcut(self):
        for split in ("train", "dev"):
            for situation in (0, 1):
                rows = [row for row in self.build(split=split)["rows"] if row["source"]["situation_index"] == situation]
                records = [json.loads(row["raw_target"]) for row in rows]
                self.assertEqual(Counter(record["observed"] for record in records), {True: 3, False: 3})
                self.assertEqual(Counter(record["relation"] for record in records), {"matched": 2, "mismatched": 2, "unavailable": 2})
                if split == "dev":
                    self.assertEqual(len({row["source"]["events"][0]["raw_outcome"] for row in rows}), 1)
                    self.assertTrue(all(len(row["source"]["events"]) == 2 for row in rows))

    def test_metadata_is_not_rendered_as_model_input(self):
        for skill in corpus.SKILLS:
            for row in self.build(skill)["rows"]:
                prompt = row["input_messages"][-1]["content"]
                self.assertNotIn(row["source"]["case"], prompt)
                self.assertNotIn(row["source"]["source_id"], prompt)
                self.assertNotIn("source_admissible", prompt)
                self.assertNotIn("Observed fields:", prompt)
                self.assertNotIn("source_proof", prompt)

    def test_judgement_negatives_are_paired_and_not_fake_abstention_targets(self):
        for split in ("train", "dev"):
            rows = self.build("judgement", split)["rows"]
            positives = {row["source"]["source_id"]: row for row in rows if row["source_admissible"]}
            negatives = [row for row in rows if not row["source_admissible"]]
            self.assertEqual(len(positives), len(negatives))
            self.assertEqual(Counter(reason for row in negatives for reason in row["admissibility_reasons"]),
                             {"ambiguous_public_prediction": 6, "public_outcome_action_mismatch": 6})
            for row in negatives:
                parent = positives[row["source"]["derivation"]["parent_source_id"]]
                self.assertIsNone(row["raw_target"])
                self.assertIsNone(row["target_sha256"])
                self.assertEqual(row["target_status"], "UNEXPRESSIBLE_NATIVE_ABSTENTION")
                self.assertEqual(row["source"]["case"], parent["source"]["case"])
                for response in (None, "", "DONE", "ABSTAIN", "null", parent["raw_target"]):
                    score = corpus.score_response(row, response)
                    self.assertIsNone(score["passed"])
                    self.assertEqual(score["score_kind"], "unsupported_native_abstention")

    def test_missing_prediction_is_sufficient_but_missing_outcome_is_not(self):
        source = next(source for source in corpus.public_sources("train") if source["case"] == "unavailable_false")
        assessment = corpus.assess_source(source)
        self.assertTrue(assessment["admissible"])
        self.assertIsNone(assessment["execution"]["predicted"])
        self.assertIs(assessment["execution"]["observed"], False)
        missing = self.revise(source, raw_outcome=None)
        self.assertFalse(corpus.assess_source(missing)["admissible"])
        self.assertIsNone(corpus.assess_source(missing)["execution"])

    def test_post_action_prediction_is_not_prior_prediction(self):
        source = corpus.public_sources("train")[0]
        source = self.revise(source, raw_response="ACT: TRY -4,1,7\nPREDICT: F")
        assessment = corpus.assess_source(source)
        self.assertTrue(assessment["admissible"])
        self.assertIsNone(assessment["execution"]["predicted"])
        self.assertEqual(assessment["proof"]["relation"]["value"], "unavailable")

    def test_ambiguous_prediction_is_not_silently_treated_as_absent(self):
        for prediction in ("PREDICT: T\nPREDICT: F", "PREDICT: uncertain", "PREDICT: T\nPREDICT: T"):
            source = self.revise(corpus.public_sources("train")[0], raw_response=prediction + "\nACT: TRY -4,1,7")
            assessment = corpus.assess_source(source)
            self.assertFalse(assessment["admissible"])
            self.assertIn("ambiguous_public_prediction", assessment["reasons"])

    def test_selected_execution_identity_and_outcome_join(self):
        source = corpus.public_sources("dev")[0]
        record = corpus.assess_source(source)
        self.assertEqual(record["execution"]["values"], [11, -8, 3])
        wrong_outcome = self.revise(source, raw_outcome="the box says: True for (20,21,22)")
        self.assertEqual(corpus.assess_source(wrong_outcome)["reasons"], ["public_outcome_action_mismatch"])
        source["selected_event_id"] = "e0"
        with self.assertRaisesRegex(ValueError, "final public execution"):
            corpus.assess_source(corpus._identify(source))

    def test_source_mutation_and_wrong_origin_rejected(self):
        source = corpus.public_sources("train")[0]
        source["events"][-1]["raw_outcome"] = "the box says: False for (-4,1,7)"
        with self.assertRaisesRegex(ValueError, "source hash"):
            corpus.assess_source(source)
        source["origin"] = "TEACHER_GENERATED"
        with self.assertRaisesRegex(ValueError, "author-sourced"):
            corpus.assess_source(corpus._identify(source))

    def test_invalid_actions_outcomes_and_duplicate_events_fail_closed(self):
        source = corpus.public_sources("train")[0]
        for output in ("no action", "ACT: TRY -4,1,7\nACT: TRY 2,3,4", "[OUTCOME] True\nACT: TRY -4,1,7", "DONE", "ACT: QUIZ ?"):
            self.assertFalse(corpus.assess_source(self.revise(source, raw_response=output))["admissible"])
        for output in ("true", "the box says: 1 for (-4,1,7)", "the box says: True for (-4,1,7) trailing"):
            self.assertFalse(corpus.assess_source(self.revise(source, raw_outcome=output))["admissible"])
        source["events"].append(copy.deepcopy(source["events"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate public events"):
            corpus.assess_source(corpus._identify(source))

    def test_public_record_parser_rejects_false_fields_types_and_extra_prose(self):
        row = next(row for row in self.build()["rows"] if row["source"]["case"] == "mismatched_false")
        target = row["raw_target"]
        bad = [target + " extra prose", target.replace('"observed": false', '"observed": 0'),
               target.replace('"mismatched"', '"matched"'), target.replace('"predicted": true', '"predicted": null'),
               target.replace('"observed": false', '"observed": false, "observed": false'),
               target.replace('"observed": false', '"observed": NaN')]
        for field, value in (("try", [-4.0, 1, 7]), ("try", [True, 1, 7]), ("try", [0, 0, 0]), ("observed", True)):
            changed = json.loads(target)
            changed[field] = value
            bad.append(json.dumps(changed))
        for response in bad + [None, "DONE", "ABSTAIN"]:
            with self.subTest(response=response):
                self.assertFalse(corpus.score_response(row, response)["passed"])
        self.assertTrue(corpus.score_response(row, json.dumps(json.loads(target), indent=2))["passed"])

    def test_reflection_is_supported_reusable_prose_not_rule_induction(self):
        for row in self.build("reflection", "dev")["rows"]:
            self.assertEqual(row["response_role"], "restate")
            self.assertIn("Your parent said:\n", row["input_messages"][-1]["content"])
            self.assertTrue(row["input_messages"][-1]["content"].endswith("Restate that message in your own words in 2-3 sentences."))
            self.assertIn(corpus.PUBLIC_CORRECTION, row["input_messages"][-1]["content"])
            self.assertIn("For later records", row["raw_target"])
            self.assertEqual(row["source_proof"]["reusable_procedure"]["raw"], corpus.PUBLIC_CORRECTION)
            self.assertNotIn("ACT:", row["raw_target"])
            self.assertEqual(corpus.score_response(row, row["raw_target"])["score_kind"], "exact_authored_restatement_only")
            self.assertFalse(corpus.score_response(row, "A plausible but different paraphrase")["passed"])

    def test_collision_and_balance_checks_detect_corruption(self):
        rows = self.build()["rows"]
        duplicate = copy.deepcopy(rows[0])
        duplicate["raw_target"] = "different target"
        audit = corpus.audit_rows(rows + [duplicate])
        self.assertEqual(audit["input_target_collisions"], 1)
        self.assertEqual(audit["duplicate_inputs"], 1)
        self.assertFalse(audit["balanced_per_template_and_triple"])
        self.assertFalse(corpus.audit_rows(rows[1:])["balanced_per_template_and_triple"])
        judgement = self.build("judgement")["rows"]
        removed = next(row for row in judgement if not row["source_admissible"])
        self.assertFalse(corpus.audit_rows([row for row in judgement if row is not removed])["judgement_pairing_complete"])

    def test_split_audit_checks_raw_evidence_not_just_different_ids(self):
        train, dev = self.build(), self.build(split="dev")
        dev["rows"][0]["source"]["events"][-1] = copy.deepcopy(train["rows"][0]["source"]["events"][-1])
        audit = corpus.audit_split_pair(train, dev)
        self.assertFalse(audit["disjoint"])
        self.assertEqual(audit["overlaps"]["selected_event_bytes"], 1)
        self.assertEqual(audit["overlaps"]["selected_triples"], 1)

    def test_public_parser_is_loaded_without_native_or_world_imports(self):
        root = str(Path(__file__).resolve().parents[1])
        script = (
            "import sys; from organism_v6.birth_skill_corpus import build_slice; "
            "build_slice('perception', split='train', system_anchor=None); "
            "forbidden = ('torch', 'vllm', 'organism_v6.rulegame', 'organism_v6.gym_backend', "
            "'organism_v6.rulegame_parenting_diagnostic', 'organism_v6.train_adapter'); "
            "assert not any(name in sys.modules for name in forbidden)"
        )
        result = subprocess.run([sys.executable, "-B", "-c", script], cwd=root, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        interface = self.build()["manifest"]["interface"]
        self.assertEqual(set(interface["definitions"]),
                         {"PROTOCOLS", "RECORD", "RELATION_DEFINITION", "require", "unique_object", "decode", "parse_action", "judge_record", "record_instruction"})


if __name__ == "__main__":
    unittest.main()
