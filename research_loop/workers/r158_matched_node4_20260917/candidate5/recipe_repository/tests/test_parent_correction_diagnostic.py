"""CPU fake backend; real native adapter, driver, slot and append-only ledger."""
from contextlib import contextmanager
import copy
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

from organism_v6 import parent_correction_diagnostic as diagnostic
from organism_v6.model_backend import configured_generation_identity
from organism_v6.reasoning_gym_gym import ReasoningGymGym


BOARD = "1 2 3 4 ; 3 4 1 2 ; 2 1 4 3 ; 4 3 2 1"
WRONG = "1 1 3 4 ; 3 4 1 2 ; 2 1 4 3 ; 4 3 2 1"


class Tokenizer:
    def encode(self, text, add_special_tokens=False):
        for package in diagnostic.packages.PACKAGES.values():
            text = text.replace(package, "FIXED PACKAGE")
        return text.split()

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True):
        return "<user>\n" + messages[0]["content"] + "\n<assistant>"


class FixtureGym(ReasoningGymGym):
    def __init__(self):
        super().__init__(require_package=False, strict_verifier=True)
        self.executions = []

    def _item(self, family, seed):
        return self, dict(question=f"Puzzle {family}/{seed}. Complete the visible four by four grid.\n"
                         "1 _ _ _\n_ 4 _ _\n_ _ 4 _\n_ _ _ 1", answer="SEALED_REFERENCE_NEVER_VISIBLE")

    def score_answer(self, answer, entry):
        self.executions.append(answer)
        return 1.0 if answer == BOARD.replace(" ; ", "\n") else .25

    def reference_answer(self, episode):
        raise AssertionError("references must never be requested")


class FixtureModel:
    def __init__(self, model_path):
        self.path = str(model_path)
        self.tok = Tokenizer()
        self.calls = []
        self.first = "ACT: " + WRONG
        self.second = "ACT: " + BOARD
        self.scratchpad = None
        self.identity_change = False

    def generation_identity(self):
        return configured_generation_identity("WRONG" if self.identity_change else self.path, None)

    def batch(self, prompts, max_tokens=400, seeds=None, temperature=.7):
        self.calls.append(dict(prompts=prompts, max_tokens=max_tokens, seeds=seeds, temperature=temperature))
        outputs = []
        for prompt in prompts:
            if max_tokens == 100:
                episode = re.search(r"Situation: (rg/mini_sudoku/\d+)", prompt)[1]
                outputs.append(self.scratchpad if self.scratchpad is not None else
                               f"row one repeats 1. own-source-{episode}\n  Preserve whitespace.  \n")
            elif "CLOCK: chunk 1/2" in prompt:
                outputs.append(self.first)
            else:
                outputs.append(self.second)
        return outputs


class CorrectionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.addCleanup(self.cleanup)
        self.base = self.root / "base"
        self.base.mkdir()
        (self.base / "config.json").write_text(json.dumps(dict(model_type="qwen2", num_hidden_layers=28, hidden_size=3584)))
        (self.base / "tokenizer.json").write_text("{}")
        (self.base / "tokenizer_config.json").write_text("{}")
        (self.base / "model.safetensors").write_bytes(b"SYNTHETIC CPU BASE; NOT WEIGHTS")
        self.pins = diagnostic.formation.local_files(self.base)
        self.gym = FixtureGym()
        self.model = FixtureModel(self.base)
        self.prep = self.root / "prepare"
        self.out = self.root / "process"
        self.closed = 0
        self.prior_ids = dict(schema="prior-source-ids-v1", episode_ids=list(diagnostic.TRAIN_IDS))

    def cleanup(self):
        for path in self.root.rglob("*"):
            if path.is_dir():
                path.chmod(0o755)
        self.temporary.cleanup()

    @contextmanager
    def backend(self, model_path):
        self.assertEqual(model_path, str(self.base))
        try:
            yield self.model
        finally:
            self.closed += 1

    def prepare(self, **kwargs):
        arguments = dict(gym=self.gym, tokenizer=self.model.tok, prior_source_ids=self.prior_ids)
        arguments.update(kwargs)
        return diagnostic.prepare(self.prep, self.base, self.pins, **arguments)

    def run_arm(self, mode="process", out=None):
        return diagnostic.run_arm(self.prep, out or self.out, mode, gym=self.gym,
                                  backend_factory=self.backend, allow_synthetic=True)

    def records(self):
        return diagnostic.read(self.out / "captures.json")

    def test_actual_feedback_scratchpad_same_driver_second_wake(self):
        self.assertEqual(self.prepare()["status"], "SYNTHETIC_CPU_ONLY")
        result = self.run_arm()
        self.assertEqual(result["first_act_solves"], [0, 32])
        self.assertEqual(result["qualifying_corrections"], 32)
        self.assertEqual(result["first_act_formats"], [32, 32])
        self.assertEqual(result["first_act_native_partial"], [32, 0])
        self.assertEqual(result["all_actions"], 64)
        self.assertEqual(result["generation_requests"], 96)
        self.assertEqual(result["package_presentations"], 96)
        self.assertEqual(len(self.model.calls), 12)
        self.assertEqual(len(self.gym.executions), 64)
        for record in self.records():
            first, second = record["wakes"]
            scratch = record["scratchpads"][0]
            text = scratch["record"]["text"]
            self.assertNotIn(text, first["generation"]["prompt"])
            self.assertIn(text, second["generation"]["prompt"])
            self.assertIn("Displayed verifier score: 0.25", scratch["capture"]["prompt"])
            self.assertIn("Feedback: not accepted; partial credit", scratch["capture"]["prompt"])
            self.assertIn(first["actions"][0]["outcome"], second["generation"]["prompt"])
            self.assertNotIn("ACT submitted: " + json.dumps(BOARD), scratch["capture"]["prompt"])
            self.assertEqual(re.findall(r"own-source-(rg/mini_sudoku/\d+)", second["generation"]["prompt"]),
                             [record["episode_id"]])
            self.assertEqual(record["summary"]["ticks"], 2)
            self.assertTrue(all(action["occurrence_id"] == record["occurrence_id"]
                                for wake in record["wakes"] for action in wake["actions"]))
        for call in self.model.calls:
            self.assertEqual(call["temperature"], .7)
            self.assertEqual(len(call["prompts"]), 8)
        self.assertFalse(result["boundary"]["clean_lineage"])
        self.assertTrue(all(not row["training_approved"] for row in result["candidates"]))
        self.assertEqual(self.closed, 1)

    def test_no_judge_first_person_or_reference_panel_leak(self):
        self.prepare()
        with patch.object(diagnostic.policy, "judge_record", side_effect=AssertionError("no NOTE judge")):
            self.run_arm()
        for call in self.model.calls:
            for prompt in call["prompts"]:
                self.assertIn(diagnostic.packages.PACKAGES["process"], prompt)
                self.assertNotIn(diagnostic.packages.PACKAGES["sham"], prompt)
                self.assertNotIn("SEALED_REFERENCE", prompt)
                self.assertNotIn("1900050", prompt)
                self.assertNotIn("2000001", prompt)
                self.assertNotIn("1850000", prompt)
                if call["max_tokens"] == 100:
                    self.assertTrue(prompt.endswith("Scratchpad:"))
                    self.assertNotIn("row one repeats", prompt)

    def test_zero_wake_response_keeps_all_episodes_and_two_ticks(self):
        self.model.first = ""
        self.model.second = "DONE\n"
        self.prepare()
        result = self.run_arm()
        self.assertEqual(result["denominator"], 32)
        self.assertEqual(result["ticks"], 64)
        self.assertEqual(result["all_actions"], 0)
        self.assertEqual(result["qualifying_corrections"], 0)
        self.assertEqual(result["generation_requests"], 64)
        self.assertEqual(len(self.model.calls), 8)
        self.assertTrue(all(not row["scratchpads"] for row in self.records()))

    def test_empty_scratchpad_second_success_is_not_qualifying(self):
        self.model.scratchpad = " \n\t"
        self.prepare()
        result = self.run_arm()
        self.assertEqual(result["first_act_solves"], [0, 32])
        self.assertEqual(result["qualifying_corrections"], 0)
        self.assertEqual(result["generation_requests"], 96)

    def test_first_success_still_two_wakes_and_one_scratchpad(self):
        self.model.first = "ACT: " + BOARD + "\nDONE"
        self.model.second = "ACT: " + WRONG
        self.prepare()
        result = self.run_arm()
        self.assertEqual(result["first_act_solves"], [32, 0])
        self.assertEqual(result["qualifying_corrections"], 0)
        self.assertEqual(result["generation_requests"], 96)
        self.assertEqual(result["first_act_failure_opportunities"], 0)

    def test_multi_act_preserves_order_every_execution_and_first_endpoint(self):
        self.model.first = "ACT: " + WRONG + "\nACT: " + BOARD
        self.model.second = "ACT: " + WRONG + "\nACT: " + BOARD
        self.prepare()
        result = self.run_arm()
        self.assertEqual(result["all_actions"], 128)
        self.assertEqual(result["first_act_solves"], [0, 0])
        self.assertEqual(result["qualifying_corrections"], 0)
        self.assertEqual(result["multi_act_episodes"], 32)
        self.assertEqual(result["generation_requests"], 128)
        self.assertTrue(all(len(call["prompts"]) <= 8 for call in self.model.calls))
        for record in self.records():
            self.assertEqual(len(record["scratchpads"]), 2)
            self.assertEqual([row["action"] for row in record["wakes"][0]["actions"]], [WRONG, BOARD])
            self.assertEqual(record["wakes"][0]["generation"]["text"], self.model.first)
            self.assertTrue(all(row["record"]["tick"] == 1 for row in record["scratchpads"]))

    def test_multi_act_first_failure_second_success_not_qualifying(self):
        self.model.first += "\nACT: " + WRONG
        self.prepare()
        result = self.run_arm()
        self.assertEqual(result["first_act_solves"], [0, 32])
        self.assertEqual(result["qualifying_corrections"], 0)

    def test_empty_act_gets_real_unmeasured_scratchpad(self):
        self.model.first = "ACT:"
        self.prepare()
        result = self.run_arm()
        self.assertEqual(result["all_actions"], 64)
        for record in self.records():
            self.assertIn("Measured feedback: unavailable", record["scratchpads"][0]["capture"]["prompt"])
            self.assertEqual(record["wakes"][0]["actions"][0]["outcome"], "INVALID: attempt 1 was empty")

    def test_raw_utf8_crlf_act_bytes_and_untruncated_tail(self):
        self.model.first = "  π  \r\n" + "longword " * 180 + "\r\nACT: " + WRONG + "  \r\n"
        self.model.scratchpad = "  café — \r\nrow one repeats 1.  \r\n"
        self.prepare()
        self.run_arm()
        for record in self.records():
            generation = record["wakes"][0]["generation"]
            self.assertEqual(generation["text"].encode(), self.model.first.encode())
            self.assertIn(self.model.first, record["wakes"][1]["generation"]["prompt"])
            self.assertIn(self.model.scratchpad, record["wakes"][1]["generation"]["prompt"])
            span = record["wakes"][0]["raw_act_spans"][0]
            self.assertEqual(generation["text"].encode()[span["start_byte"]:span["end_byte"]], span["raw"].encode())
        diagnostic.verify_inventory(self.out)

    def test_recall_cannot_cross_episodes_even_later_batches(self):
        self.model.first = "NOTE: secret-same-episode\nACT: " + WRONG
        self.model.second = "RECALL: secret-same-episode verifier\nACT: " + BOARD
        self.prepare()
        self.run_arm()
        ledger = diagnostic.EpisodeLedger(str(self.out / "ledger.jsonl"), diagnostic.IDS[-1])
        recalled = ledger.recall("verifier", k=100)
        self.assertTrue(recalled)
        self.assertTrue(all(diagnostic.IDS[-1] in item for item in recalled))
        self.assertNotIn(diagnostic.IDS[0], "\n".join(recalled))

    def test_live_second_context_and_scratchpad_headroom_rejected_not_truncated(self):
        class TooLongLater(Tokenizer):
            def encode(self, text, add_special_tokens=False):
                if "CLOCK: chunk 2/2" in text:
                    return [0] * 3697
                return super().encode(text, add_special_tokens)

        self.model.tok = TooLongLater()
        self.prepare()
        with self.assertRaisesRegex(ValueError, "headroom exceeds 4096"):
            self.run_arm()
        self.assertEqual([call["max_tokens"] for call in self.model.calls], [400, 100])
        self.assertTrue((self.out / "failure.json").exists())
        self.assertFalse((self.out / "results.json").exists())
        diagnostic.verify_inventory(self.out)
        rows = [json.loads(line) for line in (self.out / "generations.jsonl").read_text().splitlines()]
        rejected = [row for row in rows if row["kind"] == "live_input_check" and not row["fits"]]
        self.assertEqual(len(rejected), 8)
        self.assertIn("own-source-", rejected[0]["prompt"])

    def test_initial_budget_and_package_mismatch_pending(self):
        class TooLong(Tokenizer):
            def encode(self, text, add_special_tokens=False):
                return [0] * 3697

        self.assertEqual(self.prepare(tokenizer=TooLong())["status"], "PENDING")
        with self.assertRaisesRegex(ValueError, "pending"):
            self.run_arm()
        self.assertFalse(self.model.calls)

    def test_frozen_package_token_mismatch_blocks_without_padding(self):
        class Unequal(Tokenizer):
            def encode(self, text, add_special_tokens=False):
                tokens = super().encode(text, add_special_tokens)
                return tokens + ([999] if diagnostic.packages.PACKAGES["process"] in text else [])

        check = self.prepare(tokenizer=Unequal())
        self.assertIn("fixed package token mismatch", check["blockers"])
        self.assertEqual(check["status"], "PENDING")
        self.assertEqual(diagnostic.read(self.prep / "config.json")["packages"], diagnostic.packages.PACKAGES)

    def test_scratchpad_live_headroom_checked_before_call(self):
        class LongOutcome(Tokenizer):
            def encode(self, text, add_special_tokens=False):
                return [0] * 3997 if "Displayed verifier score:" in text else super().encode(text, add_special_tokens)

        self.model.tok = LongOutcome()
        self.prepare()
        with self.assertRaisesRegex(ValueError, "headroom exceeds 4096"):
            self.run_arm()
        self.assertEqual([call["max_tokens"] for call in self.model.calls], [400])
        diagnostic.verify_inventory(self.out)

    def test_no_second_action_still_retains_first_outcome_and_scratchpad(self):
        self.model.second = ""
        self.prepare()
        result = self.run_arm()
        self.assertEqual(result["all_actions"], 32)
        self.assertEqual(result["first_act_solves"], [0, 0])
        self.assertEqual(result["generation_requests"], 96)
        self.assertEqual(result["qualifying_corrections"], 0)

    def test_expired_arm_budget_fails_before_model_call(self):
        self.prepare()
        with patch.object(diagnostic.time, "monotonic", side_effect=[0.0, 1801.0]):
            with self.assertRaisesRegex(ValueError, "time budget exhausted"):
                self.run_arm()
        self.assertFalse(self.model.calls)
        diagnostic.verify_inventory(self.out)

    def test_no_prior_source_check_is_pending(self):
        check = self.prepare(prior_source_ids=None)
        self.assertEqual(check["status"], "PENDING")
        self.assertIn("prior source ID overlap check pending", check["blockers"])
        self.assertEqual(check["prior_question_comparison"], "NOT_SUPPLIED_UNRESOLVED")

    def test_strict_order_training_ids_and_prior_overlap(self):
        for ids in (list(reversed(diagnostic.IDS)), list(diagnostic.IDS[:-1]), list(diagnostic.TRAIN_IDS),
                    list(diagnostic.IDS[:-1]) + [diagnostic.EVAL_IDS[0]]):
            with self.assertRaisesRegex(ValueError, "exact ordered"):
                diagnostic.selected_ids(ids, self.gym)
        with self.assertRaisesRegex(ValueError, "prior source ID overlap"):
            diagnostic.selected_ids(list(diagnostic.IDS), self.gym,
                                    dict(schema="prior-source-ids-v1", episode_ids=[diagnostic.IDS[0]]))
        with patch.object(self.gym, "split_of", return_value="gate"):
            with self.assertRaisesRegex(ValueError, "membership"):
                diagnostic.selected_ids(list(diagnostic.IDS), self.gym)

    def test_audit_inputs_reject_static_outputs_ledgers_and_answers(self):
        for value in ([dict(kind="act")], dict(schema="prior-source-ids-v1", episode_ids=[], outputs=[]),
                      dict(schema="EXPLORATORY_STATIC_COMPETENCY_PACKAGE", episode_ids=[])):
            with self.assertRaisesRegex(ValueError, "STATIC"):
                diagnostic.selected_ids(list(diagnostic.IDS), self.gym, value)
        held = diagnostic.selected_ids(list(diagnostic.IDS), self.gym)
        with self.assertRaisesRegex(ValueError, "only IDs"):
            diagnostic.question_audit(self.gym, list(diagnostic.IDS), held,
                dict(schema="prior-question-hashes-v1", questions=[dict(episode_id="old", question_sha256="a" * 64, answer=BOARD)]))

    def test_prior_question_collision_and_held_question_collision(self):
        question_hash = diagnostic.sha(self.gym.question(diagnostic.IDS[0]).encode())
        held = diagnostic.selected_ids(list(diagnostic.IDS), self.gym)
        with self.assertRaisesRegex(ValueError, "prior actual question overlap"):
            diagnostic.question_audit(self.gym, list(diagnostic.IDS), held,
                dict(schema="prior-question-hashes-v1", questions=[dict(episode_id="old", question_sha256=question_hash)]))
        question = self.gym.question
        with patch.object(self.gym, "question", side_effect=lambda episode: question(diagnostic.IDS[0])
                          if episode == held[0] else question(episode)):
            with self.assertRaisesRegex(ValueError, "held/prior configured question overlap"):
                diagnostic.question_audit(self.gym, list(diagnostic.IDS), held, None)

    def test_immutable_inputs_outputs_mode_source_and_base_pins(self):
        self.prepare()
        before = {path.name: path.read_bytes() for path in self.prep.iterdir()}
        self.run_arm()
        self.assertEqual(before, {path.name: path.read_bytes() for path in self.prep.iterdir()})
        self.assertTrue(all(path.stat().st_mode & 0o222 == 0 for path in self.out.iterdir()))
        with self.assertRaisesRegex(ValueError, "fresh"):
            self.run_arm()
        with self.assertRaisesRegex(ValueError, "unknown mode"):
            self.run_arm(mode="no_teacher")
        with patch.object(diagnostic, "source_pins", return_value={}):
            with self.assertRaisesRegex(ValueError, "source pins"):
                self.run_arm(out=self.root / "changed_source")
        (self.base / "model.safetensors").write_bytes(b"CHANGED")
        with self.assertRaisesRegex(ValueError, "base pins"):
            self.run_arm(out=self.root / "changed_base")

    def test_synthetic_cannot_execute_gpu_and_optin_required(self):
        self.prepare()
        with self.assertRaisesRegex(ValueError, "allow-gpu"):
            diagnostic.execute_pair(self.prep, self.root / "pair")
        with self.assertRaisesRegex(ValueError, "mode mismatch"):
            diagnostic.execute_pair(self.prep, self.root / "pair", allow_gpu=True)
        self.assertFalse((self.root / "pair").exists())

    def test_backend_identity_failure_seals_evidence_and_closes(self):
        self.prepare()
        self.model.identity_change = True
        with self.assertRaisesRegex(ValueError, "identity"):
            self.run_arm()
        self.assertEqual(self.closed, 1)
        self.assertFalse(self.model.calls)
        diagnostic.verify_inventory(self.out)

    def test_close_failure_cannot_report_completion(self):
        self.prepare()

        @contextmanager
        def fails_on_close(path):
            yield self.model
            raise RuntimeError("cleanup failure")

        with self.assertRaisesRegex(RuntimeError, "cleanup failure"):
            diagnostic.run_arm(self.prep, self.out, "process", gym=self.gym,
                              backend_factory=fails_on_close, allow_synthetic=True)
        self.assertFalse((self.out / "results.json").exists())
        self.assertTrue((self.out / "failure.json").exists())
        diagnostic.verify_inventory(self.out)

    def test_pure_replay_and_reducer_reject_broken_bindings(self):
        self.prepare()
        result = self.run_arm()
        with patch.object(self.gym, "evaluate", side_effect=AssertionError("no verifier replay")), \
                patch.object(self.model, "batch", side_effect=AssertionError("no inference replay")):
            replayed = diagnostic.replay(self.out, self.root / "replay")
        self.assertEqual(replayed["qualifying_corrections"], result["qualifying_corrections"])
        original = self.records()
        mutations = (
            lambda records: records[0]["wakes"][0]["generation"].update(text="REWRITTEN"),
            lambda records: records[0]["injections"][0].update(execution_id=records[1]["occurrence_id"]),
            lambda records: records[0]["scratchpads"][0]["record"].update(outcome="teacher-supplied diagnosis"),
            lambda records: records[0]["wakes"][1]["actions"][0].update(episode_id=diagnostic.IDS[1]),
            lambda records: records[0]["injections"][0].update(start_byte=0),
            lambda records: records[0]["wakes"][0].update(raw_act_spans=[]),
            lambda records: records.pop(),
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                records = copy.deepcopy(original)
                mutation(records)
                with self.assertRaises(ValueError):
                    diagnostic.reduce_captures(records)

    def test_sham_frozen_bytes_same_seed_no_adapter(self):
        self.prepare()
        self.run_arm(mode="sham")
        for record in self.records():
            self.assertIn(diagnostic.packages.PACKAGES["sham"], record["wakes"][0]["generation"]["prompt"])
            self.assertNotIn(diagnostic.packages.PACKAGES["process"], record["wakes"][0]["generation"]["prompt"])
            for wake in record["wakes"]:
                self.assertEqual(wake["generation"]["seed"], diagnostic.batch_loop._seed_for(record["episode_id"], wake["tick"], 7101))

    def test_controller_uses_separate_owned_workers_1800_seconds(self):
        self.prepare()
        config = diagnostic.read(self.prep / "config.json")
        calls = []

        def worker(command, *, log_path, timeout, device):
            mode = command[command.index("--condition") + 1]
            calls.append((mode, timeout, device))
            output = Path(command[command.index("--out") + 1])
            output.mkdir()
            diagnostic.formation._write(output / "results.json", dict(status="COMPLETE", mode=mode,
                execution_backend="LOCAL_GPU_BACKEND", denominator=32, ticks=64))
            diagnostic.seal(output)
            return 123

        with patch.object(diagnostic, "validate_preparation", return_value=(self.prep, "fixture", config)), \
                patch.object(diagnostic.supervisor, "selected_device", return_value="1"), \
                patch.object(diagnostic.supervisor, "run_worker", side_effect=worker), \
                patch.dict(diagnostic.os.environ, V6_MODEL=str(self.base)):
            diagnostic.execute_pair(self.prep, self.root / "pair", allow_gpu=True)
        self.assertEqual(calls, [("process", 1800, "1"), ("sham", 1800, "1")])
        self.assertTrue((self.root / "pair/COMPLETED.json").exists())


if __name__ == "__main__":
    unittest.main()
