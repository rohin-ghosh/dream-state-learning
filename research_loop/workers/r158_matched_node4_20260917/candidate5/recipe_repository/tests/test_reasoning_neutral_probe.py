"""CPU protocol fixtures only; synthetic files never authenticate a real model."""
import json
from pathlib import Path
import tempfile
import unittest

from organism_v6.model_backend import configured_generation_identity
from organism_v6.reasoning_gym_gym import ReasoningGymGym
from organism_v6.reasoning_neutral_probe import file_hashes, run_probe


class FixtureGym(ReasoningGymGym):
    def __init__(self):
        self.strict_verifier = True
        self.cfg = {"fixture": "synthetic CPU verifier"}
        self.train_families = ["fixture"]
        self.gate_families = ["heldout"]
        self.exam_families = []
        self.seed_ranges = {"canary": (100, 200)}
        self.labels = {}
        self._bootstrap = "Solve the current puzzle."
        self.failure = None
        self.score = 0.5

    def _item(self, family, seed):
        return self, {"question": f"Puzzle {seed}: submit north.", "answer": "SEALED_KEY"}

    def score_answer(self, answer, entry):
        if self.failure:
            raise self.failure
        return self.score


class FixtureBackend:
    def __init__(self, model_path, adapter_path):
        self.identity = configured_generation_identity(model_path, adapter_path)
        self.note = 'I submitted "north"; the score was 0.50.'
        self.wake = "ACT: north"
        self.calls = []
        self.mutate = None

    def generation_identity(self):
        return dict(self.identity)

    def batch(self, prompts, max_tokens, seeds, temperature):
        self.calls.append((prompts, max_tokens, seeds))
        if self.mutate:
            self.mutate()
        return [self.note if prompt.endswith("Scratchpad:") else self.wake for prompt in prompts]


class NeutralProbeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.addCleanup(self.cleanup)
        self.model_path = self.root / "model"
        self.model_path.mkdir()
        (self.model_path / "config.json").write_text('{}')
        (self.model_path / "model.safetensors").write_bytes(b"SYNTHETIC CPU WEIGHTS")
        self.adapter_path = self.root / "adapter"
        self.adapter_path.mkdir()
        (self.adapter_path / "adapter_config.json").write_text('{}')
        (self.adapter_path / "adapter_model.safetensors").write_bytes(b"SYNTHETIC CPU ADAPTER")
        self.probes = self.root / "probes"
        self.probes.mkdir()
        self.gym = FixtureGym()
        self.model = FixtureBackend(str(self.model_path), str(self.adapter_path))
        self.options = dict(episode_ids=["rg/heldout/1"], output_dir=self.probes / "run",
                            probe_root=self.probes, training_life_roots=[self.root / "life"],
                            lineage_roots=[self.root / "lineage"], model_path=self.model_path,
                            adapter_path=self.adapter_path, expected_model_hashes=file_hashes(self.model_path),
                            expected_adapter_hashes=file_hashes(self.adapter_path), gen_seed=123,
                            budget_ticks=1, wake_max_tokens=80, scratchpad_max_tokens=50,
                            total_token_budget=1000, max_episodes=4)

    def cleanup(self):
        for path in self.root.rglob("*"):
            if path.is_dir():
                path.chmod(0o755)
        self.temp.cleanup()

    def run_probe(self, **overrides):
        return run_probe(self.model, self.gym, **(self.options | overrides))

    def test_valid_record_and_instrumentation(self):
        result = self.run_probe()
        self.assertEqual(result["evidence_label"], "EVALUATION_ONLY")
        self.assertEqual(result["n_measured_actions"], 1)
        self.assertEqual(result["n_correct_grounded_scratchpads"], 1)
        output = self.options["output_dir"]
        rows = [json.loads(line) for line in (output / "episode_0000.jsonl").read_text().splitlines()]
        scratchpad = next(row for row in rows if row["kind"] == "scratchpad")
        self.assertIn('Displayed verifier score: 0.50', scratchpad["generation"]["prompt"])
        self.assertEqual(scratchpad["generation"]["max_tokens"], 50)
        self.assertEqual(scratchpad["generation"]["seed"], self.model.calls[1][2][0])
        self.assertTrue((output / "generations.jsonl").read_text().find(self.model.wake) >= 0)
        self.assertEqual((output / "results.json").stat().st_mode & 0o222, 0)
        manifest = json.loads((output / "manifest.json").read_text())["sha256"]
        self.assertIn("episode_0000.jsonl", manifest)
        self.assertFalse((self.root / "life").exists())
        self.assertFalse((self.root / "lineage").exists())

    def test_invalid_child_records(self):
        for index, text in enumerate(("I will submit north.", 'I submitted "south"; score 0.50.',
                                      'I submitted "north"; score 1.00.', "", "The teacher says to reflect.")):
            with self.subTest(text=text):
                self.model.note = text
                result = self.run_probe(output_dir=self.probes / str(index))
                self.assertEqual(result["n_measured_actions"], 1)
                self.assertEqual(result["n_correct_grounded_scratchpads"], 0)

    def test_no_parent_history_or_cross_episode_recall(self):
        self.model.wake = "RECALL: previous\nNOTE: PRIVATE_PREVIOUS_EPISODE\nACT: north"
        self.run_probe(episode_ids=["rg/heldout/1", "rg/heldout/2"])
        for prompts, _, _ in self.model.calls:
            for prompt in prompts:
                self.assertTrue(prompt.startswith("=== YOU ===\n" + self.gym.birth_prompt()))
                for forbidden in ("PRIVATE_PREVIOUS_EPISODE", "SEALED_KEY", "NOTE_AFTER", "lesson"):
                    self.assertNotIn(forbidden, prompt)
        with self.assertRaises(TypeError):
            self.run_probe(parent_context="teacher")

    def test_wrong_identity_and_hashes(self):
        for field, value in (("model_input", str(self.adapter_path)), ("adapter_input", None),
                             ("backend", "test_mock")):
            original = self.model.identity[field]
            self.model.identity[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.run_probe()
            self.model.identity[field] = original
        with self.assertRaises(ValueError):
            self.run_probe(expected_model_hashes={})
        with self.assertRaises(ValueError):
            self.run_probe(expected_adapter_hashes={})
        self.assertFalse(self.options["output_dir"].exists())

    def test_conflicting_and_outside_roots(self):
        for overrides in (dict(output_dir=self.root / "outside"),
                          dict(training_life_roots=[self.probes]),
                          dict(lineage_roots=[self.options["output_dir"] / "descendant"]),
                          dict(training_life_roots=[])):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                self.run_probe(**overrides)
        (self.probes / "alias").symlink_to(self.root / "life", target_is_directory=True)
        with self.assertRaises(ValueError):
            self.run_probe(output_dir=self.probes / "alias" / "child")

    def test_artifact_no_overwrite(self):
        self.run_probe()
        before = file_hashes(self.options["output_dir"])
        with self.assertRaises(FileExistsError):
            self.run_probe()
        self.assertEqual(before, file_hashes(self.options["output_dir"]))

    def test_null_denominators(self):
        self.model.wake = "NOTE: considering the puzzle"
        result = self.run_probe()
        self.assertEqual(result["n_measured_actions"], 0)
        self.assertIsNone(result["articulation_rate"])
        result = self.run_probe(episode_ids=[], output_dir=self.probes / "empty")
        self.assertEqual(result["n_actions"], 0)
        self.assertIsNone(result["articulation_rate"])

    def test_strict_verifier_no_fabricated_zero(self):
        self.gym.strict_verifier = False
        with self.assertRaises(ValueError):
            self.run_probe()
        self.gym.strict_verifier = True
        self.gym.failure = RuntimeError("verifier unavailable")
        with self.assertRaises(RuntimeError):
            self.run_probe()
        self.assertFalse((self.options["output_dir"] / "results.json").exists())
        self.assertTrue((self.options["output_dir"] / "failure.json").exists())

    def test_changed_files_and_identity_preserve_failed_evidence(self):
        self.model.mutate = lambda: (self.model_path / "config.json").write_text('{"changed": true}')
        with self.assertRaisesRegex(ValueError, "hashes changed"):
            self.run_probe()
        self.assertFalse((self.options["output_dir"] / "results.json").exists())
        self.options["expected_model_hashes"] = file_hashes(self.model_path)
        self.model.mutate = lambda: self.model.identity.update(default_temperature=0.5)
        with self.assertRaisesRegex(ValueError, "identity changed"):
            self.run_probe(output_dir=self.probes / "identity_changed")

    def test_budget_and_train_ids_rejected(self):
        with self.assertRaises(ValueError):
            self.run_probe(episode_ids=["rg/fixture/1"])
        with self.assertRaises(ValueError):
            self.run_probe(gen_seed=None)
        with self.assertRaisesRegex(ValueError, "token budget"):
            self.run_probe(total_token_budget=79)
        self.assertEqual(self.model.calls, [])

    def test_base_only_selected_backend(self):
        self.model.identity = configured_generation_identity(str(self.model_path), None)
        result = self.run_probe(adapter_path=None, expected_adapter_hashes={})
        self.assertEqual(result["n_correct_grounded_scratchpads"], 1)

    def test_unmeasured_empty_action_is_not_zero_measurement(self):
        self.model.wake = "ACT:"
        result = self.run_probe()
        self.assertEqual(result["n_actions"], 1)
        self.assertEqual(result["n_measured_actions"], 0)
        self.assertEqual(result["n_correct_grounded_scratchpads"], 0)
        self.assertIsNone(result["articulation_rate"])

    def test_invalid_verifier_scores_fail_closed(self):
        for index, score in enumerate((float("nan"), float("inf"), -0.1, 1.1)):
            self.gym.score = score
            output = self.probes / str(index)
            with self.subTest(score=score), self.assertRaises(RuntimeError):
                self.run_probe(output_dir=output)
            self.assertFalse((output / "results.json").exists())
            self.assertTrue((output / "source_check.json").exists())

    def test_generation_cardinality_and_midrun_budget(self):
        self.model.batch = lambda *args, **kwargs: []
        with self.assertRaisesRegex(ValueError, "cardinality"):
            self.run_probe()
        self.model = FixtureBackend(str(self.model_path), str(self.adapter_path))
        with self.assertRaisesRegex(ValueError, "token budget"):
            self.run_probe(total_token_budget=80, output_dir=self.probes / "slot_budget")
        self.assertEqual(len(self.model.calls), 1)

    def test_adapter_file_mutation_detected(self):
        self.model.mutate = lambda: (self.adapter_path / "adapter_model.safetensors").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "hashes changed"):
            self.run_probe()

    def test_tick_and_episode_bounds(self):
        result = self.run_probe(budget_ticks=2)
        self.assertEqual(result["n_measured_actions"], 2)
        self.assertEqual(result["n_correct_grounded_scratchpads"], 2)
        self.assertEqual(result["reserved_output_tokens"], 260)
        self.assertEqual(len(self.model.calls), 4)
        with self.assertRaises(ValueError):
            self.run_probe(episode_ids=["rg/heldout/1", "rg/heldout/2"], max_episodes=1)

    def test_existing_dangling_output_symlink_rejected(self):
        self.options["output_dir"].symlink_to(self.probes / "target", target_is_directory=True)
        with self.assertRaises(FileExistsError):
            self.run_probe()
        self.assertFalse((self.probes / "target").exists())

    def test_feedback_identity_mismatch_fails_closed(self):
        self.gym.evaluate = lambda *args: (0.5, "attempt 1: verifier score 1.00 (accepted)")
        with self.assertRaises(ValueError):
            self.run_probe()
        self.assertFalse((self.options["output_dir"] / "results.json").exists())


if __name__ == "__main__":
    unittest.main()
