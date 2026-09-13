"""Pure CPU corpus/export/scoring checks, not native tokenizer or learning proof."""
from collections import Counter, defaultdict
import copy
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import unittest
from unittest.mock import patch

from organism_v6 import birth_reflection_probe as probe
from organism_v6 import birth_skill_corpus as corpus


class BirthReflectionProbeTests(unittest.TestCase):
    def build(self, panel="restatement", split="train", parent="present"):
        return probe.build_panel(panel, split=split, parent_condition=parent)

    def application(self, parent="withdrawn"):
        return self.build("application", "dev", parent)

    def test_explicit_panel_split_and_parent_required(self):
        with self.assertRaises(TypeError):
            probe.build_panel("restatement")
        for panel in (None, "reflection", "both", "mixture"):
            with self.subTest(panel=panel), self.assertRaises(ValueError):
                self.build(panel=panel)
        for split in (None, "test", "held", "TRAIN"):
            with self.subTest(split=split), self.assertRaises(ValueError):
                self.build(split=split)
        for parent in (None, True, "absent", "", "Present"):
            with self.subTest(parent=parent), self.assertRaises(ValueError):
                self.build(parent=parent)
        with self.assertRaisesRegex(ValueError, "DEV only"):
            self.build("application", "train")

    def test_dependency_pins_are_verified_before_construction(self):
        self.assertEqual(probe.verify_sources(), probe.SOURCE_PINS)
        changed = dict(probe.SOURCE_PINS, **{"birth_skill_corpus.py": "0" * 64})
        with patch.object(probe, "SOURCE_PINS", changed):
            with self.assertRaisesRegex(ValueError, "historical source pin mismatch"):
                self.build()

    def test_historical_targets_and_event_bytes_preserved_with_labeled_prompt_transform(self):
        for split in ("train", "dev"):
            original = corpus.build_slice("reflection", split=split, system_anchor=probe.GENERIC_SYSTEM)
            built = self.build(split=split)
            self.assertEqual(len(built["rows"]), 12)
            for before, after in zip(original["rows"], built["rows"]):
                self.assertEqual(after["historical_row_id"], before["row_id"])
                self.assertEqual(after["source"], before["source"])
                self.assertEqual(after["source_proof"], before["source_proof"])
                expected_user = before["input_messages"][-1]["content"]
                expected_user = (expected_user[len(probe.HISTORICAL_PARENT_FRAMING):-len(probe.HISTORICAL_RESTATEMENT_TASK)]
                                 + probe.RESTATEMENT_TASK)
                self.assertEqual(after["input_messages"][0], before["input_messages"][0])
                self.assertEqual(after["input_messages"][-1]["content"], expected_user)
                self.assertEqual(after["response_target"], before["raw_target"])
                self.assertTrue(after["input_messages"][-1]["content"].endswith(probe.RESTATEMENT_TASK))
            self.assertEqual(built["manifest"]["audit"]["prompt_transform"], "nondeictic_event_procedure_v1")
            self.assertFalse(built["manifest"]["audit"]["historical_prompt_bytes_preserved"])

    def test_both_restatement_conditions_have_well_posed_nondeictic_task(self):
        expected_task = "Summarize the selected public event and state a reusable recording procedure in 2-3 sentences."
        for split in ("train", "dev"):
            for parent in probe.PARENT_CONDITIONS:
                for row in self.build(split=split, parent=parent)["rows"]:
                    user = row["input_messages"][-1]["content"]
                    self.assertTrue(user.endswith(expected_task))
                    self.assertEqual(user.count(expected_task), 1)
                    self.assertNotIn("Your parent said:", user)
                    self.assertNotIn("Restate", user)
                    self.assertNotIn("that message", user)
                    for event in row["source"]["events"]:
                        self.assertIn(event["raw_response"], user)
                        self.assertIn(event["raw_outcome"], user)
                    if parent == "withdrawn":
                        self.assertNotIn(corpus.PUBLIC_CORRECTION, user)

    def test_prompt_transform_rejects_historical_framing_or_task_drift(self):
        original = corpus.build_slice("reflection", split="train", system_anchor=probe.GENERIC_SYSTEM)
        for change in (lambda text: text.replace("Your parent said:\n", "Other framing:\n", 1),
                       lambda text: text.replace(probe.HISTORICAL_RESTATEMENT_TASK, "Different task.")):
            changed = copy.deepcopy(original)
            changed["rows"][0]["input_messages"][-1]["content"] = change(changed["rows"][0]["input_messages"][-1]["content"])
            with patch.object(corpus, "build_slice", return_value=changed):
                with self.assertRaisesRegex(ValueError, "historical restatement framing/task drift"):
                    self.build()

    def test_explicit_withdrawal_is_only_input_difference_all_panels(self):
        for panel, split in (("restatement", "train"), ("restatement", "dev"), ("application", "dev")):
            present = self.build(panel, split, "present")
            withdrawn = self.build(panel, split, "withdrawn")
            for before, after in zip(present["rows"], withdrawn["rows"]):
                with self.subTest(panel=panel, split=split, row=before["row_id"]):
                    self.assertEqual(before["row_id"], after["row_id"])
                    self.assertEqual(before["response_target"], after["response_target"])
                    self.assertEqual(before["source"], after["source"])
                    self.assertEqual(before["source_proof"], after["source_proof"])
                    self.assertEqual(before["input_messages"][0], after["input_messages"][0])
                    self.assertEqual(after["input_messages"][0], {"role": "system", "content": probe.GENERIC_SYSTEM})
                    before_user = before["input_messages"][1]["content"]
                    after_user = after["input_messages"][1]["content"]
                    self.assertEqual(before_user.count(corpus.PUBLIC_CORRECTION), 1)
                    self.assertNotIn(corpus.PUBLIC_CORRECTION, after_user)
                    self.assertEqual(after_user, before_user.replace("\n" + corpus.PUBLIC_CORRECTION + "\n", "\n", 1))
                    for event in after["source"]["events"]:
                        self.assertIn(event["raw_response"], after_user)
                        self.assertIn(event["raw_outcome"], after_user)

    def test_system_anchor_none_does_not_withdraw_parent_regression(self):
        old = corpus.build_slice("reflection", split="train", system_anchor=None)
        self.assertIn(corpus.PUBLIC_CORRECTION, old["rows"][0]["input_messages"][0]["content"])
        new = self.build(parent="withdrawn")
        self.assertEqual(len(new["rows"][0]["input_messages"]), 2)
        self.assertNotIn(corpus.PUBLIC_CORRECTION, new["rows"][0]["input_messages"][1]["content"])

    def test_withdrawal_rejects_missing_duplicate_or_nonstandalone_correction(self):
        for bad in (None, "no parent", corpus.PUBLIC_CORRECTION,
                    "x" + corpus.PUBLIC_CORRECTION + "\ny",
                    "x\n" + corpus.PUBLIC_CORRECTION + "\ny\n" + corpus.PUBLIC_CORRECTION + "\nz"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                probe.withdraw_parent_correction(bad)

    def test_frozen_rows_have_exact_output_blind_digests(self):
        expected = {
            ("restatement", "train", "present"): "a8be4cd7c7639ef65f720641e8232734d61cac693c54f6f0277229d9848cef90",
            ("restatement", "train", "withdrawn"): "edf53877c01c97cb3a8132a2281c68546900a5c63f8b5e6dc5040f6fbd7e157b",
            ("restatement", "dev", "present"): "6696fdb8cdd6d3db6678dee711ef0cf55cda6aad968a235a1af00ba0f6120cd1",
            ("restatement", "dev", "withdrawn"): "e2779a635202bfa92463cb8596c894ed4caa304cd3b9b41e5ffeee933cc93031",
            ("application", "dev", "present"): "d7eafee8ffbe87d3ba3eb89d7bfa687f6614dd3c5f1b82062a2e85cf39a0a988",
            ("application", "dev", "withdrawn"): "ad79320b909b23f8644c99f5a64278a66b79b05553eb3fbe1c42cc5f8a4bcd29",
        }
        for arguments, digest in expected.items():
            with self.subTest(arguments=arguments):
                self.assertEqual(self.build(*arguments)["manifest"]["rows_sha256"], digest)

    def test_construction_is_deterministic_and_does_not_change_random_state(self):
        before = random.getstate()
        self.assertEqual(self.application(), self.application())
        self.assertEqual(self.build(), self.build())
        self.assertEqual(before, random.getstate())

    def test_returned_mutations_cannot_change_future_construction(self):
        expected = self.application()
        changed = self.application()
        changed["rows"][0]["source"]["events"][0]["raw_response"] = "altered"
        changed["rows"][0]["choices"]["A"]["procedure"] = "altered"
        changed["manifest"]["historical_source_sha256"].clear()
        self.assertEqual(self.application(), expected)

    def test_application_cases_and_choice_labels_are_balanced(self):
        rows = self.application()["rows"]
        self.assertEqual(len(rows), 12)
        self.assertEqual(Counter(row["source"]["case"] for row in rows), {case[0]: 2 for case in probe.APPLICATION_CASES})
        self.assertEqual(Counter(row["response_target"] for row in rows), {"A": 6, "B": 6})
        for case, _, _ in probe.APPLICATION_CASES:
            self.assertEqual(Counter(row["response_target"] for row in rows if row["source"]["case"] == case), {"A": 1, "B": 1})
        for box in (0, 1):
            self.assertEqual(Counter(row["response_target"] for row in rows if row["source"]["situation_index"] == box), {"A": 3, "B": 3})

    def test_application_all_literal_events_and_triples_disjoint_from_old_splits(self):
        historical = corpus.public_sources("train") + corpus.public_sources("dev")
        application = [row["source"] for row in self.application()["rows"]]
        event_sets = []
        triple_sets = []
        for sources in (historical, application):
            event_sets.append({(event["raw_response"], event["raw_outcome"]) for source in sources for event in source["events"]})
            triple_sets.append({tuple(corpus._interface().parse_action(event["raw_response"], "interaction_v3")["values"])
                                for source in sources for event in source["events"]})
        self.assertFalse(event_sets[0] & event_sets[1])
        self.assertFalse(triple_sets[0] & triple_sets[1])
        self.assertTrue(self.build()["manifest"]["audit"]["historical_split_audit"]["disjoint"])

    def test_overlap_is_rejected_including_distractor_events(self):
        with patch.object(probe, "APPLICATION_TRIPLES", (corpus.SITUATIONS["train"][0], (-23, 19, 6))):
            with self.assertRaisesRegex(ValueError, "overlaps historical split"):
                self.application()
        with patch.object(probe, "DISTRACTOR_TRIPLES", ((20, 21, 22), (-31, -32, -33))):
            with self.assertRaisesRegex(ValueError, "overlaps historical split"):
                self.application()

    def test_application_proof_agrees_with_hand_authored_case_table(self):
        cases = {name: (prediction, observed) for name, prediction, observed in probe.APPLICATION_CASES}
        for row in self.application()["rows"]:
            prediction, observed = cases[row["source"]["case"]]
            expected_prediction = None if prediction is None else prediction == "T"
            relation = "unavailable" if prediction is None else "matched" if expected_prediction == observed else "mismatched"
            supported = row["choices"][row["response_target"]]
            self.assertIs(supported["predicted"], expected_prediction)
            self.assertIs(supported["observed"], observed)
            self.assertEqual(supported["relation"], relation)
            self.assertEqual(supported["try"], list(probe.APPLICATION_TRIPLES[row["source"]["situation_index"]]))
            self.assertEqual(supported["procedure"], probe.PROCEDURES[relation])
            proof = probe.semantic_choice_proof(row["source"], row["choices"])
            self.assertEqual(proof, row["source_proof"])
            self.assertEqual(proof["supported_choice"], row["response_target"])
            self.assertEqual(sum(option["supported"] for option in proof["options"].values()), 1)

    def test_source_proof_binds_final_event_not_distractor(self):
        for row in self.application()["rows"]:
            final = row["source"]["events"][-1]
            for field in ("try", "predicted", "observed", "relation"):
                proof = row["source_proof"]["source_fields"][field]
                self.assertEqual(proof["event_id"], final["event_id"])
                self.assertEqual(proof["source_id"], row["source"]["source_id"])
            other = "B" if row["response_target"] == "A" else "A"
            self.assertFalse(row["source_proof"]["options"][other]["supported"])
            self.assertTrue(row["source_proof"]["options"][other]["mismatched_fields"])

    def test_semantic_proof_rejects_ambiguous_pairs_and_malformed_source(self):
        row = self.application()["rows"][0]
        correct = row["choices"][row["response_target"]]
        other = "B" if row["response_target"] == "A" else "A"
        wrong = row["choices"][other]
        for choices in ({"A": correct, "B": correct}, {"A": wrong, "B": wrong}, {"A": correct}):
            with self.assertRaises(ValueError):
                probe.semantic_choice_proof(row["source"], choices)
        bad = copy.deepcopy(row["source"])
        bad["events"][-1]["raw_outcome"] = None
        bad = corpus._identify(bad)
        with self.assertRaisesRegex(ValueError, "publicly admissible"):
            probe.semantic_choice_proof(bad, row["choices"])
        bad["origin"] = "MODEL_GENERATED"
        bad = corpus._identify(bad)
        with self.assertRaisesRegex(ValueError, "author-sourced"):
            probe.semantic_choice_proof(bad, row["choices"])

    def test_semantic_proof_checks_types_not_python_bool_int_equality(self):
        row = self.application()["rows"][0]
        choices = copy.deepcopy(row["choices"])
        choices[row["response_target"]]["observed"] = int(choices[row["response_target"]]["observed"])
        with self.assertRaisesRegex(ValueError, "exactly one"):
            probe.semantic_choice_proof(row["source"], choices)

    def test_choice_order_swap_swaps_semantic_target_not_source(self):
        for row in self.application()["rows"]:
            swapped = {"A": row["choices"]["B"], "B": row["choices"]["A"]}
            proof = probe.semantic_choice_proof(row["source"], swapped)
            self.assertNotEqual(proof["supported_choice"], row["response_target"])
            self.assertEqual(proof["source_fields"], row["source_proof"]["source_fields"])

    def test_single_factor_baselines_and_residual_composite_shortcuts_reported(self):
        audit = self.application()["manifest"]["audit"]
        baselines = audit["single_factor_and_memorization_baselines"]
        for feature in ("constant", "case", "triple", "prediction", "outcome", "relation"):
            self.assertEqual(baselines[feature], {"correct": 6, "total": 12, "accuracy": 0.5})
        self.assertEqual(baselines["case_and_triple_memorization"]["correct"], 12)
        self.assertEqual(baselines["triple_and_prediction"]["correct"], 10)
        self.assertEqual(baselines["triple_and_outcome"]["correct"], 8)
        self.assertEqual(baselines["triple_and_relation"]["correct"], 6)
        self.assertEqual(baselines["ordered_choices_without_event"]["correct"], 10)
        self.assertIn("no universal shortcut", audit["scope"])

    def test_identical_ordered_choices_can_require_opposite_source_backed_answers(self):
        groups = defaultdict(list)
        for row in self.application()["rows"]:
            groups[probe._json(row["option_texts"])].append(row)
        ambiguous = [rows for rows in groups.values() if {row["response_target"] for row in rows} == {"A", "B"}]
        self.assertEqual(len(ambiguous), 2)
        for rows in ambiguous:
            self.assertEqual(len(rows), 2)
            self.assertNotEqual(rows[0]["source"]["events"][-1], rows[1]["source"]["events"][-1])

    def test_audit_detects_answer_imbalance_duplicates_and_single_factor_shortcut(self):
        rows = self.application()["rows"]
        changed = copy.deepcopy(rows)
        changed[0]["response_target"] = "B" if changed[0]["response_target"] == "A" else "A"
        with self.assertRaisesRegex(ValueError, "imbalance"):
            probe._application_audit(changed)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            probe._application_audit(rows[:-1] + [rows[0]])
        changed = copy.deepcopy(rows)
        for row in changed:
            row["response_target"] = "A" if row["source"]["situation_index"] == 0 else "B"
        with self.assertRaisesRegex(ValueError, "single-factor"):
            probe._application_audit(changed)

    def test_no_metadata_proofs_or_training_target_annotations_in_messages(self):
        for panel, split in (("restatement", "train"), ("restatement", "dev"), ("application", "dev")):
            for row in self.build(panel, split)["rows"]:
                text = probe._json(row["input_messages"])
                for hidden in (row["row_id"], row["source"]["source_id"], row["source"]["case"],
                               row["input_sha256"], row["target_sha256"], "supported_choice",
                               "source_proof", "mismatched_fields", "response_target"):
                    self.assertNotIn(hidden, text)
                self.assertEqual([message["role"] for message in row["input_messages"]], ["system", "user"])
                self.assertTrue(all(set(message) == {"role", "content"} for message in row["input_messages"]))

    def test_two_training_exports_have_same_order_targets_and_only_clean_payload(self):
        present = probe.export_training(self.build())
        withdrawn = probe.export_training(self.build(parent="withdrawn"))
        self.assertEqual(present["report"]["row_ids_in_order"], withdrawn["report"]["row_ids_in_order"])
        self.assertEqual(present["report"]["targets_sha256"], withdrawn["report"]["targets_sha256"])
        for exported in (present, withdrawn):
            self.assertEqual(exported["report"]["record_count"], 12)
            self.assertEqual(exported["report"]["application_rows"], 0)
            self.assertEqual(exported["report"]["dev_rows"], 0)
            self.assertTrue(all(set(record) == {"input_messages", "response_target"} for record in exported["records"]))
            self.assertEqual(exported["report"]["records_sha256"], probe._digest(exported["records"]))
        self.assertNotEqual(present["report"]["records_sha256"], withdrawn["report"]["records_sha256"])

    def test_train_export_rejects_all_dev_and_appended_application_rows(self):
        for built in (self.build(split="dev"), self.application()):
            with self.assertRaisesRegex(ValueError, "only historical restatement TRAIN"):
                probe.export_training(built)
        tampered = self.build()
        tampered["rows"].append(self.application()["rows"][0])
        tampered["manifest"]["row_count"] = 13
        tampered["manifest"]["rows_sha256"] = probe._digest(tampered["rows"])
        with self.assertRaisesRegex(ValueError, "integrity mismatch"):
            probe.export_training(tampered)

    def test_dev_cannot_be_relabelled_as_training(self):
        tampered = self.application()
        tampered["manifest"].update(panel="restatement", split="train", training_export_allowed=True)
        for row in tampered["rows"]:
            row.update(panel="restatement", split="train")
        tampered["manifest"]["rows_sha256"] = probe._digest(tampered["rows"])
        with self.assertRaisesRegex(ValueError, "integrity mismatch"):
            probe.export_training(tampered)

    def test_full_assistant_mask_contract_reference_is_not_suffix_training(self):
        exported = probe.export_training(self.build(parent="withdrawn"))
        self.assertFalse(exported["report"]["mask_contract"]["native_tokenization_verified"])
        self.assertFalse(exported["report"]["mask_contract"]["eos_in_response_target"])
        for record in exported["records"]:
            prompt = probe._json(record["input_messages"]) + "<assistant>"
            context_ids = list(prompt.encode())
            target_ids = list(record["response_target"].encode())
            eos_id = 256
            input_ids = context_ids + target_ids + [eos_id]
            labels = [-100] * len(context_ids) + target_ids + [eos_id]
            self.assertEqual(len(input_ids), len(labels))
            self.assertEqual(labels[:len(context_ids)], [-100] * len(context_ids))
            self.assertEqual(bytes(labels[len(context_ids):-1]).decode(), record["response_target"])
            self.assertEqual(labels.count(eos_id), 1)
            self.assertGreater(len(target_ids), len("For later records"))
            self.assertNotIn("<|im_end|>", record["response_target"])

    def test_development_export_separates_requests_from_scoring_rows(self):
        for panel in ("restatement", "application"):
            exported = probe.export_development(self.build(panel, "dev"))
            self.assertEqual(len(exported["requests"]), 12)
            self.assertFalse(exported["report"]["training_allowed"])
            self.assertFalse(exported["report"]["scoring_rows_are_model_input"])
            for request, scoring in zip(exported["requests"], exported["scoring_rows"]):
                self.assertEqual(set(request), {"input_messages"})
                self.assertEqual(request["input_messages"], scoring["input_messages"])
            exported["requests"][0]["input_messages"][0]["content"] = "mutated"
            self.assertEqual(exported["scoring_rows"][0]["input_messages"][0]["content"], probe.GENERIC_SYSTEM)
        with self.assertRaisesRegex(ValueError, "requires DEV"):
            probe.export_development(self.build())

    def test_manifest_and_row_tampering_rejected_even_with_recomputed_hashes(self):
        for field in ("response_target", "input_messages", "source_proof", "option_texts", "choices"):
            changed = self.application()
            changed["rows"][0][field] = "altered"
            changed["manifest"]["rows_sha256"] = probe._digest(changed["rows"])
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "integrity mismatch"):
                probe.validate_panel(changed)
        changed = self.application()
        changed["manifest"]["scientific_claim"] = True
        with self.assertRaisesRegex(ValueError, "integrity mismatch"):
            probe.validate_panel(changed)

    def test_score_rejects_tampered_target_or_proof_before_response(self):
        row = copy.deepcopy(self.application()["rows"][0])
        row["response_target"] = "B" if row["response_target"] == "A" else "A"
        row["target_sha256"] = probe._text_hash(row["response_target"])
        with self.assertRaisesRegex(ValueError, "row integrity mismatch"):
            probe.score_response(row, row["response_target"])
        row = copy.deepcopy(self.application()["rows"][0])
        row["source_proof"]["supported_choice"] = "tampered"
        with self.assertRaisesRegex(ValueError, "row integrity mismatch"):
            probe.score_response(row, "A")

    def test_strict_application_scores_correct_and_wrong_choice_separately(self):
        for row in self.application()["rows"]:
            correct = probe.score_response(row, row["response_target"])
            self.assertTrue(correct["passed"])
            self.assertTrue(correct["syntax_valid"])
            self.assertIsNone(correct["failure"])
            other = "B" if row["response_target"] == "A" else "A"
            incorrect = probe.score_response(row, other)
            self.assertFalse(incorrect["passed"])
            self.assertTrue(incorrect["syntax_valid"])
            self.assertEqual(incorrect["failure"], "wrong_choice")

    def test_strict_scorer_never_strips_fences_whitespace_or_explanations(self):
        row = self.application()["rows"][0]
        target = row["response_target"]
        invalid = [None, True, 1, [target], {"answer": target}, target.encode(), "", target.lower(),
                   " " + target, target + "\n", target + ".", "```\n" + target + "\n```",
                   json.dumps(target), target + " because it is correct", "Ａ", "Β", "A/B"]
        for raw in invalid:
            with self.subTest(raw=raw):
                score = probe.score_response(row, raw)
                self.assertFalse(score["passed"])
                self.assertFalse(score["syntax_valid"])
                self.assertEqual(score["failure"], "invalid_choice_syntax")
                self.assertEqual(score["raw_response"], raw)

    def test_restatement_keeps_historical_exact_scorer_and_no_semantic_score(self):
        for row in self.build(split="dev", parent="withdrawn")["rows"]:
            original = {"skill": "reflection", "source": row["source"]}
            for raw in (row["response_target"], row["response_target"] + "\n", "Truthful paraphrase.", None):
                expected = corpus.score_response(original, raw)
                scored = probe.score_response(row, raw)
                self.assertEqual(scored["passed"], expected["passed"])
                self.assertEqual(scored["score_kind"], "exact_authored_restatement_only")
                self.assertIsNone(scored["semantic_prose_score"])
                self.assertEqual(scored["raw_response"], raw)

    def test_restatement_cannot_pass_by_substring_or_reusable_suffix_only(self):
        row = self.build(split="dev")["rows"][0]
        target = row["response_target"]
        suffix = target[target.index("For later records"):]
        for raw in (suffix, "wrong event. " + suffix, "prefix " + target, target + " suffix"):
            self.assertFalse(probe.score_response(row, raw)["passed"])

    def test_panel_reducer_retains_raw_failures_and_does_not_promote(self):
        built = self.application()
        responses = {row["row_id"]: row["response_target"] for row in built["rows"]}
        responses[built["rows"][0]["row_id"]] += "\n"
        report = probe.score_panel(built, responses)
        self.assertEqual((report["passed_count"], report["total"]), (11, 12))
        self.assertFalse(report["scientific_claim"])
        self.assertFalse(report["auto_promotion"])
        self.assertTrue(report["results"][0]["raw_response"].endswith("\n"))
        self.assertEqual(report["results"][0]["failure"], "invalid_choice_syntax")

    def test_panel_reducer_rejects_missing_extra_or_list_inventory(self):
        built = self.application()
        complete = {row["row_id"]: row["response_target"] for row in built["rows"]}
        missing = dict(complete)
        missing.pop(built["rows"][0]["row_id"])
        for responses in (missing, {**complete, "extra": "A"}, list(complete), None):
            with self.subTest(responses=type(responses)), self.assertRaisesRegex(ValueError, "complete exact response inventory"):
                probe.score_panel(built, responses)

    def test_json_round_trip_validates_without_coercing_raw_fields(self):
        for built in (self.build(), self.application()):
            self.assertEqual(probe.validate_panel(json.loads(json.dumps(built))), built)
        built = self.application()
        built["rows"][0]["source"]["situation_index"] = float(built["rows"][0]["source"]["situation_index"])
        with self.assertRaisesRegex(ValueError, "integrity mismatch"):
            probe.validate_panel(built)

    def test_native_and_claim_flags_remain_false(self):
        for built in (self.build(), self.build(split="dev"), self.application()):
            self.assertFalse(built["manifest"]["native_ready"])
            self.assertFalse(built["manifest"]["scientific_claim"])
            self.assertFalse(built["manifest"]["auto_promotion"])
            self.assertEqual(built["manifest"]["origin"], "AUTHOR_SOURCED_DEVELOPMENT_ONLY")
            self.assertIn("not teacher generations", built["manifest"]["curriculum"])

    def test_cli_emits_clean_export_without_native_imports(self):
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        result = subprocess.run(
            [sys.executable, "-B", "-m", "organism_v6.birth_reflection_probe", "training",
             "--panel", "restatement", "--parent", "withdrawn"],
            cwd=Path(__file__).resolve().parents[1], env=environment,
            capture_output=True, text=True, check=True,
        )
        exported = json.loads(result.stdout)
        self.assertEqual(exported["report"]["record_count"], 12)
        self.assertEqual(result.stderr, "")
        code = (
            "import sys; from organism_v6 import birth_reflection_probe as probe; "
            "probe.build_panel('application', split='dev', parent_condition='withdrawn'); "
            "assert not {'torch','transformers','peft','vllm'} & set(sys.modules)"
        )
        subprocess.run([sys.executable, "-B", "-c", code], cwd=Path(__file__).resolve().parents[1],
                       env=environment, capture_output=True, text=True, check=True)

    def test_cli_rejects_application_training(self):
        result = subprocess.run(
            [sys.executable, "-B", "-m", "organism_v6.birth_reflection_probe", "training",
             "--panel", "application", "--parent", "present"],
            cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True,
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertIn("DEV only", result.stderr)


if __name__ == "__main__":
    unittest.main()
