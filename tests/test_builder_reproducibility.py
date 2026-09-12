"""Non-material seed-forwarding and post-outcome isolation regressions."""
import random
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from organism_v6.model_backend import VLLMBackend
from organism_v6.run_life_v2 import (
    assert_split_hygiene, leak_scan_ledger, target_blind_check)
from organism_v6.train_adapter import seed_training


class SeedForwardingTests(unittest.TestCase):
    def test_life_passes_seed_to_each_sleep_fit(self):
        import golden_harness as harness
        from organism_v6 import run_life_v2

        transcript = harness.Transcript()
        commands = []
        with tempfile.TemporaryDirectory() as directory:
            with harness.fake_world(transcript):
                fake_train = run_life_v2.subprocess.run

                def capture(command, *args, **kwargs):
                    commands.append(list(command))
                    return fake_train(command, *args, **kwargs)

                argv = ["run_life_v2", "--life-dir", directory, "--arm", "B",
                        *harness.BASE_ARGS, "--train-seed", "23"]
                with patch.object(run_life_v2.subprocess, "run", capture):
                    with patch.object(sys, "argv", argv):
                        with contextlib.redirect_stdout(io.StringIO()):
                            run_life_v2.main()
        self.assertEqual(len(commands), 2)
        for command in commands:
            self.assertEqual(command[command.index("--seed") + 1], "23")
            self.assertEqual(command[command.index("--rank") + 1], "8")

    def test_single_generation_forwards_explicit_seed(self):
        backend = object.__new__(VLLMBackend)
        backend.batch = Mock(return_value=["answer"])
        self.assertEqual(backend("prompt", seed=123), "answer")
        backend.batch.assert_called_once_with(
            ["prompt"], max_tokens=400, temperature=0.7, seeds=[123])

    def test_unspecified_generation_seed_preserves_default(self):
        backend = object.__new__(VLLMBackend)
        backend.batch = Mock(return_value=["answer"])
        backend("prompt")
        self.assertIsNone(backend.batch.call_args.kwargs["seeds"])

    def test_training_seeds_python_and_torch(self):
        torch_module = Mock()
        previous_state = random.getstate()
        try:
            seed_training(7, torch_module)
            first_draw = random.random()
            seed_training(7, torch_module)
            self.assertEqual(first_draw, random.random())
            self.assertEqual(torch_module.manual_seed.call_count, 2)
            torch_module.manual_seed.assert_called_with(7)
        finally:
            random.setstate(previous_state)

    def test_unspecified_training_seed_changes_nothing(self):
        torch_module = Mock()
        previous_state = random.getstate()
        seed_training(None, torch_module)
        self.assertEqual(previous_state, random.getstate())
        torch_module.manual_seed.assert_not_called()


class PostOutcomeIsolationTests(unittest.TestCase):
    def test_old_clean_receipts_cannot_skip_newly_scanned_notes(self):
        gym = Mock()
        gym.exposure_domain.return_value = "reasoning_gym"
        rows = [{"kind": "note_after", "episode_id": "train/example",
                 "text": "I chose -mem2reg."}]
        for round_index in (1, 2):
            with self.subTest(round_index=round_index):
                with tempfile.TemporaryDirectory() as directory:
                    receipt = Path(directory) / "leak_scan.jsonl"
                    old = json.dumps(dict(round=1, clean=True, scanned_rows=1))
                    receipt.write_text(old + "\n")
                    with self.assertRaisesRegex(RuntimeError, "target-blindness"):
                        target_blind_check(gym, rows, directory, round_index, Mock())
                    lines = receipt.read_text().splitlines()
                    self.assertEqual(lines[0], old)
                    self.assertEqual(len(lines), 2)
                    self.assertEqual(json.loads(lines[-1])["scanned_from"], 0)

    def test_current_policy_receipts_retain_incremental_scanning(self):
        gym = Mock()
        gym.exposure_domain.return_value = "reasoning_gym"
        with tempfile.TemporaryDirectory() as directory:
            rows = [{"kind": "note_after", "text": "I checked the sum."}]
            first = target_blind_check(gym, rows, directory, 1, Mock())
            self.assertEqual(first["scan_schema"], "stored-child-text-v2")
            cached = target_blind_check(gym, rows, directory, 1, Mock())
            self.assertEqual(cached, first)
            rows.append({"kind": "note_after", "text": "I checked it again."})
            second = target_blind_check(gym, rows, directory, 2, Mock())
            self.assertEqual(second["scanned_from"], 1)
            self.assertEqual(second["scanned_rows"], 2)

    def test_post_outcome_text_is_scanned(self):
        result = leak_scan_ledger([
            {"kind": "note_after", "text": "I chose -mem2reg."}],
            terms=["-mem2reg"])
        self.assertEqual(result["n_hit_rows"], 1)
        self.assertEqual(result["hits"], {"-mem2reg": 1})

    def test_clean_record_does_not_create_a_hit(self):
        result = leak_scan_ledger([
            {"kind": "note_after", "text": "I checked the sum."}],
            terms=["-mem2reg"])
        self.assertEqual(result["n_hit_rows"], 0)

    def test_post_outcome_heldout_id_is_rejected(self):
        gym = Mock(spec=["exam_set", "gate_set"])
        gym.exam_set.return_value = ["benchmark://heldout/example"]
        gym.gate_set.return_value = []
        with self.assertRaisesRegex(RuntimeError, "split hygiene"):
            assert_split_hygiene(gym, [
                {"kind": "note_after", "episode_id": "heldout/example"}])

    def test_post_outcome_heldout_family_is_rejected(self):
        gym = Mock(spec=["exam_set", "gate_set", "split_of"])
        gym.exam_set.return_value = []
        gym.gate_set.return_value = []
        gym.split_of.return_value = "exam"
        with self.assertRaisesRegex(RuntimeError, "exam family"):
            assert_split_hygiene(gym, [
                {"kind": "note_after", "episode_id": "rg/exam/456"}])


if __name__ == "__main__":
    unittest.main()
