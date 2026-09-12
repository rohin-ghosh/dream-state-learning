"""Synthetic CPU protocol tests, never real model inference."""
from contextlib import contextmanager
import json
from pathlib import Path
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import test_parent_material_diagnostic as fixtures
from organism_v6 import parent_competency_diagnostic as diagnostic
from organism_v6 import model_backend, train_adapter_v3, preschool_reasoning, life_lineage


GOOD = "1 2 3 4\n3 4 1 2\n2 1 4 3\n4 3 2 1"
ACTION = GOOD.replace("\n", " ; ")


class Tokenizer:
    def encode(self, text, add_special_tokens=False):
        for package in diagnostic.PACKAGES.values():
            text = text.replace(package, "synthetic equal package")
        return list(range(len(text.split())))

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True):
        return "<user>\n" + messages[0]["content"] + "\n<assistant>"


class Gym(fixtures.FixtureGym):
    def _item(self, family, seed):
        return self, dict(question=f"Training puzzle {seed}. Submit the requested four-row grid.",
                          answer="SEALED_REFERENCE_DO_NOT_SHOW")

    def reference_answer(self, episode):
        raise AssertionError("reference answers are not presentation inputs")

    def score_answer(self, answer, entry):
        return float(answer == GOOD)


class Model(fixtures.FixtureModel):
    def __init__(self, path):
        super().__init__(path)
        self.tok = Tokenizer()
        self.wake = "ACT: " + ACTION
        self.calls = []

    def batch(self, prompts, max_tokens=400, seeds=None, temperature=.7):
        self.calls.append(dict(prompts=prompts, max_tokens=max_tokens, seeds=seeds, temperature=temperature))
        return [self.wake for _ in prompts]


class CompetencyTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.DiagnosticTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root
        self.prep = self.root / "prep"
        self.gym = Gym()
        self.model = Model(str(self.fixture.model_dir))
        self.ids = list(diagnostic.TRAIN_IDS[:16])
        self.closed = 0

    @contextmanager
    def backend(self, path):
        self.assertEqual(path, str(self.fixture.model_dir))
        try:
            yield self.model
        finally:
            self.closed += 1

    def prepare(self, tokenizer=None):
        return diagnostic.prepare(self.prep, self.fixture.model_dir, self.fixture.config.expected_files,
                                  self.ids, gym=self.gym, tokenizer=tokenizer or self.model.tok)

    def run_arm(self, mode="process", **kwargs):
        return diagnostic.run_arm(self.prep, self.root / mode, mode, gym=self.gym,
                                  backend_factory=self.backend, allow_synthetic=True, **kwargs)

    def test_preparation_never_starts_model_and_is_transparently_synthetic(self):
        with patch.object(diagnostic.formation, "local_backend", side_effect=AssertionError("no model")):
            result = self.prepare()
        self.assertEqual(result["status"], "SYNTHETIC_CPU_ONLY")
        self.assertFalse(self.model.calls)
        self.assertTrue((self.prep / "artifact_hashes.json").exists())
        self.assertEqual((self.prep / "config.json").stat().st_mode & 0o222, 0)
        with self.assertRaisesRegex(ValueError, "native token preflight"):
            diagnostic.run_arm(self.prep, self.root / "native", "process", gym=self.gym, backend_factory=self.backend)

    def test_launcher_rejects_synthetic_before_gpu_inspection(self):
        self.prepare()
        with patch("gpu.astra_mini_sudoku_diagnostic.check_free", side_effect=AssertionError("no GPU")):
            with self.assertRaisesRegex(ValueError, "native preparation pending"):
                diagnostic.launch_pair(self.prep, self.root / "live", "3")

    def test_no_teacher_anchor_keeps_questions_and_omits_entire_block(self):
        result = diagnostic.prepare(self.prep, self.fixture.model_dir, self.fixture.config.expected_files,
                                    self.ids, gym=self.gym, tokenizer=self.model.tok, teacher_absent=True)
        check = diagnostic.read(self.prep / "preflight.json")
        config = diagnostic.read(self.prep / "config.json")
        self.assertEqual(result["status"], "SYNTHETIC_CPU_ONLY")
        self.assertEqual(check["package_tokens"], {"no_teacher": 0})
        self.assertFalse(check["exact_token_match"])
        self.assertTrue(check["posthoc_descriptive_anchor"])
        self.assertFalse(config["boundary"]["teacher_present"])
        self.assertEqual(config["episode_ids"], self.ids)
        self.assertEqual(diagnostic.bootstrap_for(self.gym, "no_teacher"), self.gym.birth_prompt())
        for row in check["rows"]["no_teacher"]:
            self.assertNotIn("=== A NOTE FROM YOUR TEACHER ===", row["prompt"])
            self.assertIn(self.gym.question(row["episode_id"]), row["prompt"])
            self.assertEqual(row["seed"], diagnostic.batch_loop._seed_for(row["episode_id"], 1, 7101))

    def test_no_teacher_run_records_zero_teaching_not_zero_opportunities(self):
        diagnostic.prepare(self.prep, self.fixture.model_dir, self.fixture.config.expected_files,
                           self.ids, gym=self.gym, tokenizer=self.model.tok, teacher_absent=True)
        result = self.run_arm("no_teacher")
        self.assertEqual(result["presentations"], 0)
        self.assertEqual(result["episode_opportunities"], 16)
        self.assertEqual(result["cumulative_package_tokens"], 0)
        self.assertEqual(result["reserved_output_tokens"], 6400)
        self.assertEqual(len(result["episodes"]), 16)
        self.assertEqual(len(self.model.calls), 2)
        for request in (self.root / "no_teacher").glob("request_*.json"):
            self.assertEqual(diagnostic.read(request)["package_presentations"], 0)
        self.assertTrue(result["boundary"]["posthoc_descriptive_anchor"])
        self.assertFalse(result["boundary"]["input_token_matched"])

    def test_teacher_conditions_cannot_execute_absent_preparation(self):
        diagnostic.prepare(self.prep, self.fixture.model_dir, self.fixture.config.expected_files,
                           self.ids, gym=self.gym, tokenizer=self.model.tok, teacher_absent=True)
        for mode in diagnostic.MODES:
            with self.assertRaisesRegex(ValueError, "unknown condition"):
                self.run_arm(mode)
        self.assertFalse(self.model.calls)

    def test_no_teacher_cannot_execute_original_two_arm_preparation(self):
        self.prepare()
        with self.assertRaisesRegex(ValueError, "unknown condition"):
            self.run_arm("no_teacher")
        self.assertFalse(self.model.calls)

    def test_launcher_reserves_both_arms_and_uses_external_logs(self):
        self.prepare()
        original_read = diagnostic.read
        def read(path):
            value = original_read(path)
            if Path(path).name == "preflight.json":
                value["status"] = "READY"
            return value
        with patch.object(diagnostic, "read", side_effect=read), \
             patch("gpu.astra_mini_sudoku_diagnostic.check_free", return_value=({"fixture": True}, "<fixture/>")), \
             patch.object(diagnostic.subprocess, "Popen", return_value=SimpleNamespace(pid=123)) as popen:
            result = diagnostic.launch_pair(self.prep, self.root / "live", "3")
        self.assertFalse((self.root / "live").exists())
        self.assertTrue((self.root / "live_logs/launch.json").is_file())
        self.assertTrue(result["continuous_reservation"])
        command = popen.call_args.args[0]
        self.assertNotIn("--condition", command)
        self.assertNotIn("--launch", command)
        self.assertIn("--allow-gpu", command)
        self.assertTrue(popen.call_args.kwargs["start_new_session"])
        environment = popen.call_args.kwargs["env"]
        self.assertEqual(environment["CUDA_VISIBLE_DEVICES"], "3")
        self.assertEqual(environment["V6_MODEL"], str(self.fixture.model_dir))
        self.assertEqual(environment["HF_HUB_OFFLINE"], "1")
        with self.assertRaisesRegex(ValueError, "prospectively selected"):
            diagnostic.launch_pair(self.prep, self.root / "other", "1")

    def test_equal_packages_opportunities_and_seeded_caps_without_note_requirement(self):
        self.prepare()
        with patch.object(train_adapter_v3, "main", side_effect=AssertionError("no training")), \
                patch.object(preschool_reasoning, "judge_record", side_effect=AssertionError("no NOTE gate")), \
                patch.object(life_lineage, "record_sleep", side_effect=AssertionError("no lineage")):
            results = [self.run_arm(mode) for mode in diagnostic.MODES]
        self.assertEqual(self.closed, 2)
        self.assertEqual(len(self.model.calls), 4)
        self.assertEqual([call["seeds"] for call in self.model.calls[:2]], [call["seeds"] for call in self.model.calls[2:]])
        for call in self.model.calls:
            self.assertEqual((len(call["prompts"]), call["max_tokens"], call["temperature"]), (8, 400, .7))
        for mode, result in zip(diagnostic.MODES, results):
            self.assertEqual((result["denominator"], result["presentations"], result["first_action_solves"]), (16, 16, 16))
            self.assertEqual(result["reserved_output_tokens"], 6400)
            self.assertFalse(result["boundary"]["training"])
            self.assertFalse((self.root / mode / "corpus.json").exists())
            for index in range(16):
                request = diagnostic.read(self.root / mode / f"request_{index:02d}.json")
                self.assertEqual(request["prompt"].count(diagnostic.PACKAGES[mode]), 1)
                self.assertEqual(request["package_presentations"], 1)
                self.assertIsNone(request["source_identity"]["adapter_input"])
                self.assertNotIn("SEALED_REFERENCE", request["prompt"])
                self.assertNotIn("NOTE_AFTER:", request["prompt"])
                other = diagnostic.MODES[1 - diagnostic.MODES.index(mode)]
                self.assertNotIn(diagnostic.PACKAGES[other], request["prompt"])
        self.assertEqual(results[0]["cumulative_package_tokens"], results[1]["cumulative_package_tokens"])

    def test_first_action_not_best_action_and_raw_bytes_preserved(self):
        self.prepare()
        self.model.wake = "\nACT: not a grid\nACT: " + ACTION + "\n"
        result = self.run_arm()
        self.assertEqual(result["first_action_solves"], 0)
        for episode in result["episodes"]:
            self.assertEqual((episode["first_action_score"], episode["native_best"], episode["n_actions"]), (0, 1, 2))
            self.assertFalse(episode["first_action_format_valid"])
        output = diagnostic.read(self.root / "process/output_00.json")
        self.assertEqual(output["text"], self.model.wake)
        self.assertEqual(output["output_sha256"], diagnostic.policy._sha(self.model.wake.encode()))
        self.assertEqual(result["episodes"][0]["actions"][1]["outcome"], "attempt 2: verifier score 1.00 (accepted)")

    def test_missing_actions_still_receive_exactly16_presentations(self):
        self.prepare()
        self.model.wake = "I am considering the question."
        result = self.run_arm()
        self.assertEqual(result["presentations"], 16)
        self.assertEqual(result["first_action_solves"], 0)
        self.assertTrue(all(not row["first_action_available"] and row["first_action_score"] == 0 for row in result["episodes"]))

    def test_native_format_valid_but_wrong_is_not_a_solution(self):
        rows = [dict(kind="act", action="1 1 1 1 ; 1 1 1 1 ; 1 1 1 1 ; 1 1 1 1", score=0.25)]
        result = diagnostic.action_summary(rows)
        self.assertTrue(result["first_action_format_valid"])
        self.assertEqual(result["first_action_score"], .25)
        self.assertEqual(result["first_action_solved"], 0)

    def test_invalid_first_action_score_zero_even_if_later_success(self):
        result = diagnostic.action_summary([dict(kind="act", action="bad", score=1), dict(kind="act", action=ACTION, score=1)])
        self.assertEqual(result["first_action_score"], 0)
        self.assertEqual(result["first_action_solved"], 0)
        self.assertEqual(result["native_best"], 1)

    def test_selection_rejects_canary_duplicate_unknown_and_wrong_size(self):
        for ids in ([*self.ids[:-1], diagnostic.EVAL_IDS[0]], self.ids[:-1], [self.ids[0]] * 16,
                    [*self.ids[:-1], "rg/mini_sudoku/1100000"]):
            with self.subTest(ids=ids), self.assertRaises(ValueError):
                diagnostic.selected_ids(ids, self.gym)
        with patch.object(self.gym, "benchmarks", return_value=[self.ids[0]]):
            with self.assertRaisesRegex(ValueError, "held-out"):
                diagnostic.selected_ids(self.ids, self.gym)

    def test_tokenizer_missing_and_token_mismatch_are_pending_no_padding(self):
        pending = diagnostic.preflight(self.gym, self.ids, None)
        self.assertEqual(pending["status"], "PREFLIGHT_PENDING_TOKENIZER")
        self.assertEqual(pending["packages"]["process"]["text"], diagnostic.PACKAGES["process"])

        class Unequal(Tokenizer):
            def encode(self, text, add_special_tokens=False):
                tokens = super().encode(text, add_special_tokens)
                return tokens + ([999] if diagnostic.PACKAGES["process"] in text else [])

        self.prepare(Unequal())
        with self.assertRaisesRegex(ValueError, "pending"):
            self.run_arm()
        self.assertFalse(self.model.calls)

    def test_long_prompt_blocks_preflight(self):
        class TooLong(Tokenizer):
            def encode(self, text, add_special_tokens=False):
                return [0] * 4096

        check = diagnostic.preflight(self.gym, self.ids, TooLong())
        self.assertFalse(check["context_fits"])
        self.assertNotEqual(check["status"], "READY")

    def test_fresh_outputs_only_and_material_unchanged(self):
        self.prepare()
        before = {path.name: path.read_bytes() for path in self.prep.iterdir()}
        self.run_arm()
        self.assertEqual(before, {path.name: path.read_bytes() for path in self.prep.iterdir()})
        with self.assertRaisesRegex(ValueError, "fresh"):
            self.run_arm()
        with self.assertRaisesRegex(ValueError, "fresh"):
            self.prepare()

    def test_tampered_package_rejected(self):
        self.prepare()
        path = self.prep / "config.json"
        path.chmod(0o644)
        config = diagnostic.read(path)
        config["packages"]["process"] += " changed"
        path.write_text(json.dumps(config))
        with self.assertRaisesRegex(ValueError, "hash"):
            self.run_arm()

    def test_identity_failure_closes_backend_and_seals_failure(self):
        self.prepare()
        self.model.identity_change = True
        with self.assertRaisesRegex(ValueError, "identity"):
            self.run_arm()
        self.assertEqual(self.closed, 1)
        self.assertFalse(self.model.calls)
        self.assertTrue((self.root / "process/failure.json").exists())
        self.assertFalse((self.root / "process/results.json").exists())
        diagnostic.verify_inventory(self.root / "process")

    def test_output_over_budget_preserved_and_rejected(self):
        self.prepare()
        self.model.wake = "word " * 401
        with self.assertRaisesRegex(ValueError, "output budget"):
            self.run_arm()
        self.assertEqual(diagnostic.read(self.root / "process/output_00.json")["text"], self.model.wake)
        self.assertEqual(self.closed, 1)
        self.assertEqual(len(list((self.root / "process").glob("output_*.json"))), 8)

    def test_backend_close_failure_cannot_claim_completion(self):
        self.prepare()

        @contextmanager
        def fails_on_close(path):
            yield self.model
            raise RuntimeError("backend cleanup failed")

        with self.assertRaisesRegex(RuntimeError, "cleanup failed"):
            diagnostic.run_arm(self.prep, self.root / "failed_close", "process", gym=self.gym,
                               backend_factory=fails_on_close, allow_synthetic=True)
        self.assertFalse((self.root / "failed_close/results.json").exists())
        self.assertTrue((self.root / "failed_close/failure.json").exists())

    def test_controller_uses_fresh_processes_same_reserved_device(self):
        self.prepare()
        real_read = diagnostic.read
        root = self.root / "pair"
        calls = []

        def ready_read(path):
            value = real_read(path)
            if Path(path) == self.prep / "preflight.json":
                value["status"] = "READY"
            return value

        def worker(command, *, log_path, timeout, device):
            mode = command[command.index("--condition") + 1]
            calls.append((mode, timeout, device))
            out = Path(command[command.index("--out") + 1])
            out.mkdir()
            diagnostic.formation._write(out / "results.json", dict(status="COMPLETE", mode=mode,
                execution_backend="LOCAL_GPU_BACKEND", presentations=16, cumulative_package_tokens=48,
                episodes=[dict(episode_id=episode) for episode in self.ids]))
            diagnostic.seal(out)
            return 123

        with patch.object(diagnostic, "read", side_effect=ready_read), \
                patch.object(diagnostic.supervisor, "selected_device", return_value="1"), \
                patch.dict(diagnostic.os.environ, V6_MODEL=str(self.fixture.model_dir)), \
                patch.object(diagnostic.supervisor, "run_worker", side_effect=worker):
            diagnostic.execute_pair(self.prep, root, allow_gpu=True)
        self.assertEqual(calls, [("process", 900, "1"), ("sham", 900, "1")])
        self.assertTrue((root / "COMPLETED.json").exists())

    def test_execution_requires_explicit_gpu_opt_in(self):
        with self.assertRaisesRegex(ValueError, "allow-gpu"):
            diagnostic.execute_pair(self.prep, self.root / "pair")


if __name__ == "__main__":
    unittest.main()
