"""Only the new isolated reasoning policy is tested; no models or GPU calls."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from organism_v6 import preschool_reasoning as policy
from organism_v6.ledger import Ledger


def source_act(action="4 3 2 1", score=.5, attempt=1):
    verdict = "accepted" if score == 1 else "not accepted; partial credit" if score > 0 else "not accepted"
    return dict(kind="act", episode_id="rg/countdown/1000001",
                execution_id="rg/countdown/1000001#occ1#t1a1", tick=1,
                action=action, score=score,
                outcome=f"attempt {attempt}: verifier score {score:.2f} ({verdict})")


class ReasoningPolicyTests(unittest.TestCase):
    def setUp(self):
        self.facts = policy.facts_from_act(source_act())

    def check(self, text, eligible, facts=None, reason=None):
        judgement = policy.judge_record(text, facts or self.facts)
        self.assertEqual(judgement["content_eligible"], eligible, judgement)
        self.assertTrue(judgement["requires_external_source_match"])
        if reason is not None:
            self.assertEqual(judgement["reason"], reason)
        return judgement

    def test_multiple_faithful_noncanonical_phrasings(self):
        examples = (
            'I submitted "4 3 2 1". The verifier reported a score of 0.50; it was not accepted.',
            'My answer was `4 3 2 1`; I received 0.5 from the verifier.',
            'I tried 4 3 2 1 and got a verifier score of 0.50.',
            "After I submitted '4 3 2 1', the reported score was .50, partial credit.",
            'I entered “4 3 2 1”; the verifier returned 0.50.',
            'On attempt 1, I gave "4 3 2 1". The score was 0.50.',
        )
        for text in examples:
            with self.subTest(text=text):
                self.check(text, True)

    def test_wrong_scalar_and_conflicting_second_scalar(self):
        for text in ('I submitted "4 3 2 1"; the score was 0.75.',
                     'I tried "4 3 2 1"; score 0.50, but score 0.90.',
                     'I entered "4 3 2 1"; score -0.50.',
                     'I submitted "4 3 2 1"; score 50%.' ):
            with self.subTest(text=text):
                self.check(text, False, reason="score-mismatch")

    def test_wrong_action_and_prefix_extension_rejected(self):
        for text in ('I submitted "1 2 3 4"; score 0.50.',
                     'I tried "4 3 2 1 9"; score 0.50.',
                     'I entered 4 3 2 1 9 and the score was 0.50.',
                     'I tried "4 3 2 1"; score 0.50. I submitted "other".'):
            with self.subTest(text=text):
                self.check(text, False)
        facts = policy.facts_from_act(source_act("north"))
        for text in ('I submitted north,south; score 0.50.',
                     'I entered north.south; score 0.50.'):
            with self.subTest(text=text):
                self.check(text, False, facts, "ambiguous-action-description")

    def test_negated_observation_cannot_count_as_reported_score(self):
        self.check('I submitted "4 3 2 1". I did not get a score of 0.50.', False,
                   reason="unsupported-negated-score-claim")

    def test_first_person_and_measured_score_are_required(self):
        for text in ('The answer was "4 3 2 1"; score 0.50.',
                     'I submitted "4 3 2 1" and hoped to succeed.',
                     'I submitted "4 3 2 1"; it was not accepted.'):
            with self.subTest(text=text):
                self.check(text, False)

    def test_zero_and_full_feedback_are_valid_not_only_successes(self):
        for score, verdict in ((0, "not accepted"), (1, "accepted")):
            with self.subTest(score=score):
                facts = policy.facts_from_act(source_act("north", score))
                self.check(f'I tried "north"; the score was {score}. This attempt was {verdict}.', True, facts)

    def test_wrong_verdict_rejected(self):
        self.check('I tried "4 3 2 1"; score 0.50 and it was accepted.', False, reason="verdict-mismatch")
        full = policy.facts_from_act(source_act(score=1))
        self.check('I tried "4 3 2 1"; score 1.00 and it was not accepted.', False, full, "verdict-mismatch")
        self.check('I tried "4 3 2 1"; score 0.50 and no credit.', False, reason="verdict-mismatch")

    def test_display_rounding_never_implies_acceptance(self):
        for score in (.9996, .0004):
            with self.subTest(score=score):
                facts = policy.facts_from_act(source_act("north", score))
                self.check(f'I entered "north"; score {score:.2f}, not accepted; partial credit.', True, facts)
                wrong_verdict = "accepted" if score > .5 else "no credit"
                self.check(f'I entered "north"; score {score:.2f}, {wrong_verdict}.', False, facts, "verdict-mismatch")
        rounded = policy.facts_from_act(source_act("north", .33333))
        self.check('I submitted "north"; score 0.33.', True, rounded)
        self.check('I submitted "north"; score 0.33333.', False, rounded, "score-mismatch")

    def test_unmeasured_empty_attempt_has_no_numeric_evidence(self):
        action = dict(source_act(action=""), score=0, outcome="INVALID: attempt 1 was empty")
        facts = policy.facts_from_act(action)
        self.assertFalse(facts.measured)
        self.assertIsNone(facts.score)
        self.assertIsNone(facts.reported_score)
        self.assertNotIn("Displayed verifier score", policy.outcome_block(facts))
        self.check('I submitted ""; score 0.', False, facts, "unmeasured-feedback")

    def test_malformed_and_unmeasured_feedback_rejected(self):
        for outcome in ("score 0.50", "attempt 1: verifier score nan (accepted)",
                        "attempt 0: verifier score 0.50 (not accepted; partial credit)",
                        "attempt 1: verifier score 1.50 (accepted)",
                        "attempt 1: verifier score 0.50 (not accepted; partial credit) extra"):
            with self.subTest(outcome=outcome), self.assertRaises(policy.InvalidFeedback):
                policy.facts_from_act(dict(source_act(), outcome=outcome))

    def test_forged_scalar_and_verdict_in_feedback_rejected(self):
        for change in (dict(score=.75), dict(score=float("nan")), dict(score=float("inf")),
                       dict(score=True), dict(outcome="attempt 1: verifier score 0.50 (accepted)")):
            with self.subTest(change=change), self.assertRaises(policy.InvalidFeedback):
                policy.facts_from_act(dict(source_act(), **change))

    def test_only_act_rows_can_supply_facts(self):
        for kind in ("note_after", "teacher_illustration", "lesson"):
            with self.subTest(kind=kind), self.assertRaises(policy.InvalidFeedback):
                policy.facts_from_act(dict(source_act(), kind=kind))
        with self.assertRaises(policy.InvalidFeedback):
            policy.facts_from_act(policy.lesson_receipt("lesson", 0))

    def test_foreign_examples_actions_and_ids_rejected(self):
        for text in ('I ran -mem2reg; instructions fell from 1000 to 800.',
                     'I submitted "4 3 2 1"; score 0.50. LLVM helped.',
                     'I submitted "4 3 2 1"; score 0.50. See benchmark://npb-v0/10.'):
            with self.subTest(text=text):
                self.check(text, False, reason="foreign-domain-content")
        for action in (dict(source_act(), action="-mem2reg"),
                       dict(source_act(), episode_id="benchmark://cbench-v1/a")):
            with self.subTest(action=action), self.assertRaises(policy.InvalidFeedback):
                policy.facts_from_act(action)

    def test_prompt_never_reads_reference_answers_or_question(self):
        class ForbiddenValue:
            def __str__(self):
                raise AssertionError("reference field was read")
        action = dict(source_act(), reference_answer=ForbiddenValue(),
                      answer=ForbiddenValue(), question=ForbiddenValue(), metadata=ForbiddenValue())
        facts = policy.facts_from_act(action)
        block = policy.outcome_block(facts)
        self.assertIn('ACT submitted: "4 3 2 1"', block)
        self.assertIn("Displayed verifier score: 0.50", block)
        self.assertNotIn("ForbiddenValue", block)
        self.assertFalse(policy._FOREIGN.search(block))
        self.assertTrue(policy.outcome_block(facts, "Scratchpad").endswith("Scratchpad:"))
        with self.assertRaises(ValueError):
            policy.outcome_block(facts, "other")

    def test_extra_answer_claim_and_other_numbers_rejected(self):
        self.check('I submitted "4 3 2 1"; score 0.50. The correct answer is 9.', False,
                   reason="unsupported-reference-answer-claim")
        self.check('I submitted "4 3 2 1"; score 0.50. It took 7 seconds.', False,
                   reason="unsupported-numeric-claim")
        self.check('On attempt 2 I submitted "4 3 2 1"; score 0.50.', False,
                   reason="attempt-mismatch")

    def test_action_numbers_are_not_misclassified_as_scores(self):
        facts = policy.facts_from_act(source_act("17 -3 0.75 ; 9 2 4"))
        self.check('I entered "17 -3 0.75 ; 9 2 4". The reported score was 0.50.', True, facts)

    def test_real_adapter_step_feedback_projects_without_answer_key(self):
        from organism_v6.gym_backend import Episode
        from organism_v6.reasoning_gym_gym import ReasoningGymGym
        class Dataset:
            def score_answer(self, answer, entry):
                return .376
        gym = ReasoningGymGym(require_package=False)
        episode = Episode(eid="rg/countdown/1000001")
        with patch.object(gym, "_item", return_value=(Dataset(), {"answer": "SEALED_KEY_SENTINEL"})):
            observation = gym.step(episode, "my attempt")
        action = dict(source_act("my attempt"), score=observation.score, outcome=observation.text)
        facts = policy.facts_from_act(action)
        self.assertEqual(facts.reported_score, "0.38")
        self.assertNotIn("SEALED_KEY_SENTINEL", policy.outcome_block(facts))
        self.check('I tried "my attempt"; the verifier returned 0.38.', True, facts)

    def test_fixed_teacher_receipts_are_illustrative_and_sourced(self):
        for mode in ("lesson", "sham"):
            for phase in range(4):
                with self.subTest(mode=mode, phase=phase):
                    receipt = policy.lesson_receipt(mode, phase)
                    self.assertTrue(receipt["teacher_authored"])
                    self.assertFalse(receipt["factual_evidence"])
                    self.assertEqual(receipt["text_sha256"], hashlib.sha256(receipt["text"].encode()).hexdigest())
                    self.assertEqual(receipt["text"], policy.lesson_block(mode, phase))
                    self.assertFalse(policy._FOREIGN.search(receipt["text"]))
                    self.assertIn("actual tokenizer", receipt["token_budget_match"])
                    self.assertIn("invented, not observations", receipt["text"])
                    self.assertEqual(sum(line.startswith("- ") for line in receipt["text"].splitlines()),
                                     3 if phase == 0 else 1)
            self.assertIsNone(policy.lesson_receipt(mode, 4))
        self.assertIsNone(policy.lesson_block("none", 0))

    def test_active_sham_has_no_record_instruction(self):
        for phase in range(4):
            text = policy.lesson_block("sham", phase).lower()
            for forbidden in ("action record", "write", "verifier score", "first-person", "measured outcome"):
                self.assertNotIn(forbidden, text)
        for mode, phase in (("lesson10", 0), ("lesson", -1), ("lesson", True)):
            with self.subTest(mode=mode, phase=phase), self.assertRaises(ValueError):
                policy.lesson_block(mode, phase)

    def test_teacher_echo_excluded_even_when_its_numbers_match(self):
        facts = policy.facts_from_act(source_act("blue amber"))
        for text in (policy.LESSON_EXAMPLES[0], policy.LESSON_EXAMPLES[0].upper()):
            with self.subTest(text=text):
                self.check(text, False, facts, "teacher-illustration-echo")

    def test_common_words_not_an_echo_and_external_gates_remain_required(self):
        verdict = self.check('I submitted "4 3 2 1"; the score was 0.50. A poor result is still useful.', True)
        self.assertNotIn("admit_hi", verdict)
        self.assertNotIn("min_items", verdict)
        self.assertIn("not discretionary memory", verdict["scope"])
        families = json.loads(policy.FAMILIES_FILE.read_text())
        self.assertEqual(families["name"], "reasoning_gym_split_v1")
        self.assertFalse(hasattr(policy, "NEUTRAL_PANEL_DEFAULT"))
        self.assertFalse(policy._FOREIGN.search(policy.RECORD_ITEM))
        self.assertNotIn("Program", policy.RECORD_ITEM)

    def test_domain_wrapper_preserves_child_bytes_and_explicit_boundary(self):
        text = 'I submitted “4 3 2 1”; the score was 0.50.\nI may try again.'
        self.check(text, True)
        item = policy.RECORD_ITEM.format(eid=self.facts.episode_id, text=text)
        prefix = f"Situation {self.facts.episode_id}.\nMy measured action record: "
        self.assertTrue(item.startswith(prefix))
        self.assertEqual(item[len(prefix):], text)
        self.assertNotIn("Program", item)
        self.assertNotIn("teacher", item)

    def test_first_person_must_be_own_assertion_not_quoted_or_hypothetical(self):
        for prefix in ('The teacher said "', "If ", "I imagined that ", "I did not say "):
            with self.subTest(prefix=prefix):
                self.check(prefix + 'I submitted "4 3 2 1"; score 0.50.', False,
                           reason="unsupported-first-person-context")


class RecordModel:
    def __init__(self, response=None):
        self.response = response
        self.seeds = []
        self.prompts = []

    def generation_identity(self):
        return {"backend": "test_mock", "test_mock": True}

    def batch(self, prompts, max_tokens, seeds):
        self.prompts.extend(prompts)
        self.seeds.extend(seeds or [])
        results = []
        for prompt in prompts:
            action = json.loads(re.findall(r"^ACT submitted: (.+)$", prompt, re.M)[-1])
            results.append(self.response if self.response is not None else
                           f'I submitted {json.dumps(action)}; the score was 0.50.')
        return results


class BackendContractFixture(RecordModel):
    """Hypothetical wire-format fixture; never evidence of an actual loaded model.

    These tests exercise acceptance of the format separately from the tests that
    require real mock backends to be rejected. All generated bytes are synthetic.
    """

    def generation_identity(self):
        return dict(backend="vllm", model_input="CPU_PROTOCOL_FIXTURE_NOT_AUTHENTICATED_MODEL",
                    adapter_input=None, adapter_files={}, default_max_tokens=400, default_temperature=.7)


class ReasoningIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.life = Path(self.temp.name)
        self.ledger = Ledger(str(self.life / "ledger.jsonl"))
        Path(self.ledger.path).touch()
        self.sleep = self.life / "sleep_0032"
        self.sleep.mkdir()
        self.case_index = 0

    def stage(self, episodes=1, *, ledger=None, model=None, action=None, slot=None):
        ledger = ledger or self.ledger
        slot = slot or policy.PostOutcomeSlot()
        model = model or BackendContractFixture()
        drivers = [SimpleNamespace(ep=SimpleNamespace(eid=f"rg/countdown/{1000001 + index}"),
                                   pending_after=[], _last_prompt="Work on the current puzzle.")
                   for index in range(episodes)]
        slot.reserve_occurrences(drivers, ledger)
        for index, driver in enumerate(drivers):
            for attempt in (1, 2):
                submitted = action if action is not None else f"choice {index * 2 + attempt}"
                source = source_act(submitted, attempt=attempt)
                source.update(episode_id=driver.ep.eid, occurrence_id=driver.occurrence_id,
                              occurrence_index=driver.occurrence_index,
                              execution_id=slot.execution_id(driver.ep.eid, 1, attempt, driver.occurrence_id))
                source = ledger.append(source)
                pending = {key: source[key] for key in ("episode_id", "tick", "execution_id", "action",
                                                       "outcome", "occurrence_id", "occurrence_index")}
                pending.update(act_row=dict(source), facts={"before": None, "after": None})
                driver.pending_after.append(pending)
        slot.run_round(model, drivers, ledger, 9100)
        return slot, model, drivers

    def gate(self, *, sleep=None, mode="enforce", rows=None, **kwargs):
        return policy.gate_sleep(self.ledger.rows() if rows is None else rows,
                                 str(self.life), str(sleep or self.sleep), mode,
                                 ledger_path=self.ledger.path,
                                 previous_manifest_sha256="a" * 64,
                                 exposure_status="UNEXPOSED", **kwargs)

    def evaluate_rows(self, rows):
        self.case_index += 1
        life = self.life / f"case_{self.case_index}"
        life.mkdir()
        sleep = life / "sleep_0032"
        sleep.mkdir()
        ledger = Ledger(str(life / "ledger.jsonl"))
        Path(ledger.path).touch()
        for row in rows:
            ledger.append(row)
        return policy.gate_sleep(ledger.rows(), str(life), str(sleep), "enforce",
                                 ledger_path=ledger.path, previous_manifest_sha256="a" * 64,
                                 exposure_status="UNEXPOSED")

    def test_paired_32_episode_seed9100_slot_gate_receipt(self):
        slot, model, _drivers = self.stage(32)
        self.assertEqual(slot.stats()["n_generations"], 64)
        report = self.gate()
        self.assertTrue(report["source_gate_passed"])
        self.assertFalse(report["ancestry_authenticated"])
        self.assertFalse(report["training_skipped"])
        self.assertEqual(report["n_admitted_total"], 64)
        corpus = json.loads((self.sleep / "corpus.json").read_text())
        receipt = json.loads((self.sleep / "gate_receipt.json").read_text())
        self.assertEqual(set(corpus), {"recipe", "corpus", "principles", "n_new", "n_dropped_legacy"})
        self.assertEqual(corpus["recipe"], "preschool_records_v1")
        self.assertEqual(set(receipt), {"schema_version", "recipe", "decision", "exposure_status",
                                       "previous_manifest_sha256", "ledger_sha256", "corpus_sha256", "admissions"})
        self.assertEqual(receipt["decision"], "ADMIT")
        from organism_v6.train_adapter import load_gate_binding
        self.assertEqual(load_gate_binding(str(self.sleep / "gate_receipt.json"),
                                          report["gate_receipt_sha256"], "a" * 64,
                                          (self.sleep / "corpus.json").read_bytes()), receipt)
        self.assertEqual(receipt["corpus_sha256"], hashlib.sha256((self.sleep / "corpus.json").read_bytes()).hexdigest())
        self.assertEqual(report["gate_receipt_sha256"], hashlib.sha256((self.sleep / "gate_receipt.json").read_bytes()).hexdigest())
        lines = Path(self.ledger.path).read_bytes().splitlines(keepends=True)
        self.assertEqual(receipt["ledger_sha256"], hashlib.sha256(b"".join(lines)).hexdigest())
        for item, admission in zip(corpus["corpus"], receipt["admissions"]):
            self.assertLess(admission["source_line"], admission["record_line"])
            for prefix in ("source", "record"):
                self.assertEqual(admission[prefix + "_sha256"],
                                 hashlib.sha256(lines[admission[prefix + "_line"]]).hexdigest())
            record = json.loads(lines[admission["record_line"]])
            self.assertEqual(item, policy.RECORD_ITEM.format(eid=record["episode_id"], text=record["text"]))
            self.assertNotIn("before", record)
        second = self.life / "paired"
        second.mkdir()
        other_ledger = Ledger(str(second / "ledger.jsonl"))
        _other_slot, other_model, _drivers = self.stage(32, ledger=other_ledger)
        self.assertEqual(model.seeds, other_model.seeds)
        self.assertEqual(model.prompts, other_model.prompts)
        other_sleep = second / "sleep_0032"
        other_sleep.mkdir()
        other_report = policy.gate_sleep(other_ledger.rows(), str(second), str(other_sleep), "enforce",
                                        ledger_path=other_ledger.path, previous_manifest_sha256="b" * 64,
                                        exposure_status="UNEXPOSED")
        self.assertEqual(other_report["n_admitted_total"], 64)

    def test_slot_resume_occurrences_and_output_bytes_preserved(self):
        text = '  I submitted "north"; score 0.50.\n' + "I may reconsider. " * 180
        self.stage(model=BackendContractFixture(text), action="north")
        first_ids = {row["execution_id"] for row in self.ledger.rows() if row["kind"] == "act"}
        self.stage(model=BackendContractFixture(text), action="north", slot=policy.PostOutcomeSlot())
        rows = self.ledger.rows()
        later_ids = {row["execution_id"] for row in rows if row["kind"] == "act"} - first_ids
        self.assertEqual(len(later_ids), 2)
        for record in [row for row in rows if row["kind"] == "note_after"]:
            self.assertEqual(record["text"], text)
        report = self.gate()
        self.assertEqual(report["n_admitted_total"], 1)
        self.assertEqual(report["rejection_families"], {"duplicate-record": 3})
        self.assertTrue(policy.training_skipped(str(self.sleep)))

    def test_source_matching_adversaries(self):
        self.stage()
        original = self.ledger.rows()
        first_source = next(index for index, row in enumerate(original) if row["kind"] == "act")
        first_note = next(index for index, row in enumerate(original) if row["kind"] == "note_after")
        cases = [
            ("orphan", "provenance-orphan"),
            ("duplicate-act", "provenance-ambiguous-execution"),
            ("duplicate-note", "provenance-ambiguous-execution"),
            ("pre-outcome", "provenance-pre-outcome-record"),
            ("action", "provenance-mismatch-action"),
            ("score", "provenance-mismatch-score"),
            ("reported_score", "provenance-mismatch-reported_score"),
            ("occurrence_index", "provenance-mismatch-occurrence_index"),
            ("speaker", "provenance-not-current-child-record"),
        ]
        for mutation, reason in cases:
            with self.subTest(mutation=mutation):
                rows = json.loads(json.dumps(original))
                if mutation == "orphan":
                    rows.pop(first_source)
                elif mutation == "duplicate-act":
                    rows.append(dict(rows[first_source]))
                elif mutation == "duplicate-note":
                    rows.append(dict(rows[first_note]))
                elif mutation == "pre-outcome":
                    record = rows.pop(first_note)
                    rows.insert(first_source, record)
                else:
                    rows[first_note][mutation] = {"action": "forged", "score": .75,
                                                  "reported_score": "0.75", "occurrence_index": 999,
                                                  "speaker": "teacher"}[mutation]
                report = self.evaluate_rows(rows)
                self.assertIn(reason, report["rejection_families"])
                self.assertLessEqual(report["n_admitted_total"], 1)
                self.assertTrue(report["training_skipped"])

    def test_real_teaching_echo_and_resume_receipts(self):
        text = policy.deliver_lesson(str(self.life), "lesson", 0, ledger=self.ledger)
        before = (self.life / "lesson_deliveries.jsonl").read_bytes(), Path(self.ledger.path).read_bytes()
        self.assertEqual(text, policy.deliver_lesson(str(self.life), "lesson", 0, ledger=self.ledger))
        self.assertEqual(before, ((self.life / "lesson_deliveries.jsonl").read_bytes(),
                                  Path(self.ledger.path).read_bytes()))
        self.stage(action="blue amber", model=RecordModel(policy.LESSON_EXAMPLES[0]))
        report = self.gate()
        self.assertEqual(report["n_admitted_total"], 0)
        self.assertEqual(report["rejection_families"], {"provenance-lesson-echo": 2})
        self.assertNotIn(policy.LESSON_PARAGRAPH, (self.sleep / "corpus.json").read_text())
        with self.assertRaises(policy.ReasoningGateError):
            policy.deliver_lesson(str(self.life), "sham", 0, ledger=self.ledger)

    def test_teaching_requires_matching_influence_ledger(self):
        with self.assertRaises(policy.ReasoningGateError):
            policy.deliver_lesson(str(self.life), "lesson", 0)
        (self.life / "lesson_deliveries.jsonl").write_bytes(policy._encoded(policy.lesson_receipt("lesson", 0)))
        self.stage()
        with self.assertRaisesRegex(policy.ReasoningGateError, "inventory"):
            self.gate()

    def test_stamped_teacher_and_slot_rows_bind_actual_ledger_provenance(self):
        from organism_v6.clone_coordinator import ProvenanceLedger
        families = json.loads(policy.FAMILIES_FILE.read_text())
        self.ledger = ProvenanceLedger(self.ledger.path, clone_id=3, gym="reasoning_gym",
                                       exposure_domain="reasoning_gym:" + ",".join(families["train_families"]))
        policy.deliver_lesson(str(self.life), "lesson", 0, ledger=self.ledger)
        before = Path(self.ledger.path).read_bytes()
        policy.deliver_lesson(str(self.life), "lesson", 0, ledger=self.ledger)
        self.assertEqual(Path(self.ledger.path).read_bytes(), before)
        self.stage()
        report = self.gate()
        self.assertEqual(report["n_admitted_total"], 2)
        self.assertEqual(report["identity"]["ledger_provenance"], self.ledger.prov)
        for row in self.ledger.rows():
            for field, value in self.ledger.prov.items():
                self.assertEqual(row[field], value)
        before = Path(self.ledger.path).read_bytes()
        self.ledger.prov["clone_id"] = 4
        with self.assertRaisesRegex(policy.ReasoningGateError, "provenance stamps"):
            policy.deliver_lesson(str(self.life), "lesson", 0, ledger=self.ledger)
        self.assertEqual(Path(self.ledger.path).read_bytes(), before)

    def test_provenance_stamps_are_not_dropped_or_coerced(self):
        self.stage()
        families = json.loads(policy.FAMILIES_FILE.read_text())
        provenance = dict(gym="reasoning_gym", clone_id=3,
                          exposure_domain="reasoning_gym:" + ",".join(families["train_families"]))
        for field, wrong in (("gym", "other_gym"), ("exposure_domain", "reasoning_gym:countdown"),
                             ("clone_id", 3.0), ("clone_id", True), ("gym", None)):
            with self.subTest(field=field, wrong=wrong):
                rows = [dict(row, **provenance) for row in self.ledger.rows()]
                if wrong is None:
                    del rows[-1][field]
                else:
                    rows[-1][field] = wrong
                with self.assertRaises(policy.ReasoningGateError):
                    self.evaluate_rows(rows)

    def test_teacher_append_return_must_equal_expected_and_stored_row(self):
        class ContradictoryReturnLedger(Ledger):
            def append(self, row):
                stored = super().append(row)
                return dict(stored, gym="other_gym")
        ledger = ContradictoryReturnLedger(self.ledger.path)
        with self.assertRaisesRegex(policy.ReasoningGateError, "stored teacher row"):
            policy.deliver_lesson(str(self.life), "lesson", 0, ledger=ledger)
        self.assertEqual(len(ledger.rows()), 1)
        self.assertEqual((self.life / "lesson_deliveries.jsonl").read_bytes(), b"")

    def test_malformed_teaching_history_preserves_raw_evidence(self):
        self.stage()
        malformed = b'{"mode":"lesson","mode":"sham"}\n'
        (self.life / "lesson_deliveries.jsonl").write_bytes(malformed)
        with self.assertRaisesRegex(policy.ReasoningGateError, "duplicate JSON key"):
            self.gate()
        self.assertEqual((self.life / "lesson_deliveries.jsonl").read_bytes(), malformed)
        self.assertFalse((self.sleep / "gate_receipt.json").exists())

    def test_unmeasured_source_never_admitted_as_zero_credit(self):
        self.stage()
        rows = self.ledger.rows()
        first = next(row for row in rows if row["kind"] == "act")
        record = next(row for row in rows if row["kind"] == "note_after"
                      and row["execution_id"] == first["execution_id"])
        first.update(action="", score=0, outcome="INVALID: attempt 1 was empty")
        record.update(action="", score=0, outcome=first["outcome"],
                      **policy._measurement(policy.facts_from_act(first)))
        report = self.evaluate_rows(rows)
        self.assertIn("unmeasured-feedback", report["rejection_families"])
        self.assertEqual(report["n_admitted_total"], 0)

    def test_shadow_preserves_legacy_and_never_issues_admission(self):
        self.stage()
        original = b'{"corpus": ["legacy remains untouched"]}\n'
        (self.sleep / "corpus.json").write_bytes(original)
        report = self.gate(mode="shadow")
        self.assertEqual((self.sleep / "corpus.json").read_bytes(), original)
        self.assertFalse(report["source_gate_passed"])
        self.assertIsNone(report["gate_receipt_path"])
        self.assertFalse((self.sleep / "gate_receipt.json").exists())

    def test_minimum_and_raw_ledger_identity_fail_closed(self):
        self.stage()
        with self.assertRaisesRegex(policy.ReasoningGateError, "64"):
            self.gate(min_items=1)
        with self.assertRaisesRegex(policy.ReasoningGateError, "raw ledger"):
            self.gate(rows=[])
        with open(self.ledger.path, "ab") as target:
            target.write(b'{"kind":"thought"}')
        with self.assertRaisesRegex(policy.ReasoningGateError, "LF-delimited"):
            self.gate()

    def test_heldout_and_quarantined_influences_fail_globally(self):
        self.stage()
        for extra in (dict(kind="thought", episode_id="rg/n_queens/2000001"),
                      dict(kind="thought", episode_id="rg/countdown/1900001"),
                      dict(kind="thought", exposure_status="QUARANTINE_TASK_EXPOSED"),
                      dict(kind="scratchpad", text="probe must stay out"),
                      dict(kind="thought", text="LLVM")):
            with self.subTest(extra=extra), self.assertRaises(policy.ReasoningGateError):
                self.evaluate_rows(self.ledger.rows() + [extra])

    def stage_note_influence(self, episodes=1):
        from organism_v6.clone_coordinator import ProvenanceLedger

        families = json.loads(policy.FAMILIES_FILE.read_text())
        self.ledger = ProvenanceLedger(self.ledger.path, clone_id=3, gym="reasoning_gym",
                                       exposure_domain="reasoning_gym:" + ",".join(families["train_families"]))
        self.stage(episodes)
        return self.ledger.append(dict(kind="note", episode_id="rg/countdown/1000001", tick=1,
                                       note='I submitted "choice 1"; the score was 0.50.'))

    def test_visible_note_is_preserved_but_only_note_after_is_admitted(self):
        note = self.stage_note_influence(32)
        before = Path(self.ledger.path).read_bytes()
        report = self.gate()
        self.assertEqual(report["n_admitted_total"], 64)
        self.assertFalse(report["training_skipped"])
        self.assertEqual(Path(self.ledger.path).read_bytes(), before)
        self.assertEqual((self.sleep / "reasoning_ledger.jsonl").read_bytes(), before)
        rows = self.ledger.rows()
        receipt = json.loads((self.sleep / "gate_receipt.json").read_bytes())
        self.assertEqual(receipt["ledger_sha256"], hashlib.sha256(before).hexdigest())
        self.assertEqual(rows[-1], note)
        self.assertNotIn("generation", note)
        for admission in receipt["admissions"]:
            self.assertEqual(rows[admission["source_line"]]["kind"], "act")
            self.assertEqual(rows[admission["record_line"]]["kind"], "note_after")

    def test_notes_cannot_satisfy_grounded_record_minimum(self):
        note = self.stage_note_influence()
        reservations = [row for row in self.ledger.rows() if row["kind"] == "episode_occurrence"]
        report = self.evaluate_rows(reservations + [note] * 64)
        self.assertEqual(report["n_admitted_total"], 0)
        self.assertEqual(report["min_items"], 64)
        self.assertTrue(report["training_skipped"])

    def test_note_shape_and_episode_binding_fail_closed(self):
        self.stage_note_influence()
        original = self.ledger.rows()
        changes = ({"note": ""}, {"note": "   "}, {"note": 3}, {"tick": True},
                   {"tick": 1.0}, {"tick": 0}, {"speaker": "teacher"},
                   {"episode_id": None}, {"episode_id": "rg/countdown/1000999"},
                   {"episode_id": "rg/countdown/1900001"},
                   {"episode_id": "rg/n_queens/2000001"},
                   {"kind": "scratchpad"}, {"kind": "episode_end"},
                   {"generation": {}}, {"execution_id": "invented"},
                   {"teacher_authored": True})
        for change in changes:
            with self.subTest(change=change), self.assertRaises(policy.ReasoningGateError):
                self.evaluate_rows(original[:-1] + [dict(original[-1], **change)])
        for field in ("note", "episode_id", "tick", "gym", "exposure_domain", "clone_id"):
            note = dict(original[-1])
            del note[field]
            with self.subTest(missing=field), self.assertRaises(policy.ReasoningGateError):
                self.evaluate_rows(original[:-1] + [note])
        with self.assertRaisesRegex(policy.ReasoningGateError, "preceding episode reservation"):
            self.evaluate_rows([original[-1], *original[:-1]])

    def test_note_provenance_and_contamination_fail_closed(self):
        self.stage_note_influence()
        original = self.ledger.rows()
        changes = ({"gym": "other_gym"}, {"exposure_domain": "reasoning_gym:countdown"},
                   {"clone_id": 4}, {"clone_id": 3.0}, {"clone_id": True},
                   {"exposure_status": "UNKNOWN"},
                   {"exposure_status": "QUARANTINE_TASK_EXPOSED"},
                   {"note": "LLVM"}, {"note": "DEV_UNVERIFIED_PROVENANCE"},
                   {"note": "Remember rg/n_queens/2000001"})
        for change in changes:
            with self.subTest(change=change), self.assertRaises(policy.ReasoningGateError):
                self.evaluate_rows(original[:-1] + [dict(original[-1], **change)])
        unstamped = [{key: value for key, value in row.items()
                      if key not in ("gym", "exposure_domain", "clone_id")} for row in original]
        with self.assertRaisesRegex(policy.ReasoningGateError, "NOTE requires ledger provenance"):
            self.evaluate_rows(unstamped)

    def test_note_cannot_repair_corrupted_act_source_identity(self):
        self.stage_note_influence()
        rows = self.ledger.rows()
        for row in rows:
            if row["kind"] == "note_after":
                row["action"] = "substituted action"
        report = self.evaluate_rows(rows)
        self.assertEqual(report["n_admitted_total"], 0)
        self.assertEqual(report["rejection_families"], {"provenance-mismatch-action": 2})

    def test_immutable_receipts_and_revalidation_of_prior_admissions(self):
        self.stage(32)
        self.gate()
        receipt_before = (self.sleep / "gate_receipt.json").read_bytes()
        ledger_before = (self.sleep / "reasoning_ledger.jsonl").read_bytes()
        with self.assertRaisesRegex(policy.ReasoningGateError, "already exist"):
            self.gate()
        self.ledger.append(next(row for row in self.ledger.rows() if row["kind"] == "act"))
        later = self.life / "sleep_0064"
        later.mkdir()
        report = self.gate(sleep=later)
        self.assertEqual(report["n_admitted_total"], 63)
        self.assertTrue(report["training_skipped"])
        self.assertEqual((self.sleep / "gate_receipt.json").read_bytes(), receipt_before)
        self.assertEqual((self.sleep / "reasoning_ledger.jsonl").read_bytes(), ledger_before)
        latest = self.life / "sleep_0096"
        latest.mkdir()
        rows = self.ledger.rows()
        rows[1]["action"] = "changed"
        Path(self.ledger.path).write_bytes(b"".join(policy._encoded(row) for row in rows))
        with self.assertRaisesRegex(policy.ReasoningGateError, "append-only"):
            self.gate(sleep=latest)

    def test_slot_missing_raw_source_never_calls_model(self):
        driver = SimpleNamespace(pending_after=[{}])
        model = RecordModel()
        with self.assertRaisesRegex(policy.ReasoningGateError, "act_row"):
            policy.PostOutcomeSlot().run_round(model, [driver], self.ledger, 9100)
        self.assertFalse(model.prompts)
        self.assertEqual(driver.pending_after, [{}])
        with self.assertRaises(NotImplementedError):
            policy.neutral_probe()

    def test_generation_receipt_preserves_exact_prompt_output_and_requests(self):
        slot = policy.PostOutcomeSlot(max_tokens=137)
        _slot, model, _drivers = self.stage(slot=slot)
        records = [row for row in self.ledger.rows() if row["kind"] == "note_after"]
        for index, record in enumerate(records):
            generation = record["generation"]
            self.assertEqual(generation["prompt"], model.prompts[index])
            self.assertEqual(generation["prompt_sha256"], hashlib.sha256(model.prompts[index].encode()).hexdigest())
            self.assertEqual(generation["output_sha256"], hashlib.sha256(record["text"].encode()).hexdigest())
            self.assertEqual(generation["max_tokens"], 137)
            self.assertEqual(generation["seed"], model.seeds[index])
            self.assertEqual(generation["temperature"], .7)
            self.assertEqual(generation["backend_identity"], model.generation_identity())
            self.assertEqual(generation["batch_index"], index)
            self.assertEqual(generation["batch_size"], 2)

    def test_actual_backend_identity_helper_schema_and_adapter_hashes(self):
        from organism_v6.model_backend import configured_generation_identity
        base = configured_generation_identity("CPU_PROTOCOL_FIXTURE_NOT_AUTHENTICATED_MODEL", None)
        self.assertEqual(policy._identity_status(base), "RECORDED_BACKEND")
        adapter = self.life / "adapter_fixture"
        adapter.mkdir()
        (adapter / "adapter_config.json").write_text('{"fixture_only":true}')
        (adapter / "adapter_model.safetensors").write_bytes(b"CPU fixture; not usable model weights")
        identity = configured_generation_identity(base["model_input"], str(adapter))
        self.assertEqual(policy._identity_status(identity), "RECORDED_BACKEND")
        for name, digest in identity["adapter_files"].items():
            self.assertEqual(digest, hashlib.sha256((adapter / name).read_bytes()).hexdigest())
        identity["adapter_files"]["adapter_model.bin"] = "0" * 64
        self.assertEqual(policy._identity_status(identity), "UNAVAILABLE")

    def test_missing_or_mock_identity_is_not_real_provenance(self):
        for unavailable in (False, True):
            with self.subTest(unavailable=unavailable):
                model = RecordModel()
                if unavailable:
                    model.generation_identity = None
                life = self.life / ("missing_identity" if unavailable else "mock_identity")
                life.mkdir()
                ledger = Ledger(str(life / "ledger.jsonl"))
                self.stage(ledger=ledger, model=model)
                records = [row for row in ledger.rows() if row["kind"] == "note_after"]
                self.assertEqual(records[0]["generation"]["provenance_status"],
                                 "UNAVAILABLE" if unavailable else "TEST_MOCK")
                report = self.evaluate_rows(ledger.rows())
                self.assertEqual(report["n_admitted_total"], 0)
                self.assertFalse(report["source_gate_passed"])
                self.assertEqual(report["rejection_families"], {"generation-not-real-provenance": 2})

    def test_generation_hash_seed_and_batch_tampering_rejected(self):
        self.stage()
        original = self.ledger.rows()
        first_note = next(index for index, row in enumerate(original) if row["kind"] == "note_after")
        for field, value, reason in (
                ("prompt_sha256", "0" * 64, "generation-prompt-hash-mismatch"),
                ("output_sha256", "0" * 64, "generation-output-hash-mismatch"),
                ("backend_identity_sha256", "0" * 64, "generation-identity-hash-mismatch"),
                ("seed", -1, "generation-seed-mismatch"),
                ("max_tokens", 0, "generation-invalid-token-budget"),
                ("batch_size", 3, "generation-incomplete-batch")):
            with self.subTest(field=field):
                rows = json.loads(json.dumps(original))
                rows[first_note]["generation"][field] = value
                report = self.evaluate_rows(rows)
                self.assertIn(reason, report["rejection_families"])
        rows = json.loads(json.dumps(original))
        del rows[first_note]["generation"]
        self.assertIn("generation-missing", self.evaluate_rows(rows)["rejection_families"])

    def test_partial_generation_batch_cannot_admit_its_survivors(self):
        self.stage()
        rows = self.ledger.rows()
        rows.pop()
        report = self.evaluate_rows(rows)
        self.assertEqual(report["n_admitted_total"], 0)
        self.assertEqual(report["rejection_families"], {"generation-incomplete-batch": 1})

    def test_short_long_nontext_batches_leave_no_partial_notes(self):
        for output in (["one"], ["one", "two", "three"], ["one", None], "not a batch"):
            with self.subTest(output=output):
                model = BackendContractFixture()
                with patch.object(model, "batch", return_value=output):
                    with self.assertRaisesRegex(policy.ReasoningGateError, "incomplete slot generation"):
                        self.stage(model=model)
                self.assertFalse(any(row["kind"] == "note_after" for row in self.ledger.rows()))

    def test_backend_identity_drift_aborts_before_note_append(self):
        model = BackendContractFixture()
        first = model.generation_identity()
        second = dict(first, default_temperature=.8)
        with patch.object(model, "generation_identity", side_effect=[first, second]):
            with self.assertRaisesRegex(policy.ReasoningGateError, "identity changed"):
                self.stage(model=model)
        self.assertFalse(any(row["kind"] == "note_after" for row in self.ledger.rows()))

    def test_receipt_is_last_commit_and_interrupted_gate_cannot_resume_training(self):
        self.stage(32)
        raw_before = Path(self.ledger.path).read_bytes()
        write = policy._immutable
        def interrupt(path, content):
            if Path(path).name == "reasoning_gate_details.json":
                raise OSError("simulated interrupted transaction")
            return write(path, content)
        with patch.object(policy, "_immutable", side_effect=interrupt):
            with self.assertRaisesRegex(OSError, "interrupted transaction"):
                self.gate()
        self.assertTrue((self.sleep / "corpus.json").exists())
        self.assertFalse((self.sleep / "gate_receipt.json").exists())
        with self.assertRaises(policy.ReasoningGateError):
            policy.training_skipped(str(self.sleep))
        with self.assertRaisesRegex(policy.ReasoningGateError, "already exist"):
            self.gate()
        self.assertEqual(Path(self.ledger.path).read_bytes(), raw_before)

    def test_completed_transaction_rejects_corrupted_corpus(self):
        self.stage(32)
        report = self.gate()
        self.assertEqual(policy.verify_gate_commit(str(self.sleep)), report)
        original = policy._read
        with patch.object(policy, "_read", wraps=original) as read:
            read.side_effect = lambda path: b'{}\n' if Path(path).name == "corpus.json" else original(path)
            with self.assertRaisesRegex(policy.ReasoningGateError, "artifact mismatch"):
                policy.training_skipped(str(self.sleep))

    def test_actual_batch_loop_pending_contract_with_hypothetical_backend(self):
        from organism_v6.batch_loop import run_episodes_batch, NoEndTokenDriver
        from organism_v6.gym_backend import Episode
        class GymFixture:
            def evaluate(self, episode, action):
                episode.n_attempts += 1
                return .5, f"attempt {episode.n_attempts}: verifier score 0.50 (not accepted; partial credit)"
        class LoopFixture(BackendContractFixture):
            counter = 0
            def batch(self, prompts, max_tokens=400, temperature=.7, seeds=None):
                if prompts[0].endswith("NOTE_AFTER:"):
                    return super().batch(prompts, max_tokens, seeds)
                outputs = []
                for _prompt in prompts:
                    self.counter += 1
                    outputs.append(f"ACT: choice {self.counter}")
                return outputs
        episodes = [Episode(eid=f"rg/countdown/{1000001 + index}", goal="Find an answer.",
                            metric="Verifier score", intro="Try an answer.") for index in range(2)]
        run_episodes_batch(LoopFixture(), GymFixture(), episodes, "Work on the puzzle.", self.ledger,
                           budget_ticks=2, log=lambda _message: None, gen_seed=9100,
                           driver_cls=NoEndTokenDriver, note_after=policy.PostOutcomeSlot())
        report = self.gate()
        self.assertEqual(report["n_admitted_total"], 4)
        self.assertTrue(report["training_skipped"])


if __name__ == "__main__":
    unittest.main()
