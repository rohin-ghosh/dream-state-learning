import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from gpu import astra_memory_preservation_diagnostic as diagnostic


class PreservationDiagnosticTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "run"
        self.root.mkdir()
        self.plan = dict(original="/fixture/original", model="/fixture/model",
                         coefficient=0.1, anchors_sha256="anchors",
                         token_preflight=dict(memory_order_sha256="order", anchor_input_ids=[[1]] * 48))

    def metadata(self):
        return dict(coefficient=self.plan["coefficient"], ce_coefficient=1.0, n_items=12924,
                    steps=9693, total_steps=9693, tokens=749985, supervised_tokens=711213,
                    rank=8, alpha=16, dropout=0.05, epochs=3, lr=1e-4, bsz=4, seed=2,
                    max_len=512, boundary_straddles=0, truncated_items=0,
                    cache_used=self.plan["coefficient"] > 0, native_source_sha256=diagnostic.preservation.SOURCE_SHA,
                    anchors_sha256="anchors", memory_order_sha256="order", final_loss=1.0,
                    final_objective=1.1, wall_seconds=1000, cache_metadata=dict(input_ids=[[1]] * 48),
                    anchor_visits=[202 if index < 45 else 201 for index in range(48)]
                    if self.plan["coefficient"] > 0 else [0] * 48)

    def write_fit(self, metadata):
        adapter = self.root / diagnostic.ADAPTER
        adapter.mkdir(parents=True, exist_ok=True)
        (adapter / "DONE").write_text("ok\n")
        (adapter / "train_meta.json").write_text(json.dumps(metadata))

    def test_matching_fit(self):
        self.write_fit(self.metadata())
        diagnostic.validate_fit(self.root, self.plan)

    def test_lambda_zero_skips_anchor_visits(self):
        self.plan["coefficient"] = 0
        self.write_fit(self.metadata())
        diagnostic.validate_fit(self.root, self.plan)

    def test_reject_fit_changes(self):
        for key, value in dict(coefficient=1.0, steps=9692, supervised_tokens=422925,
                               rank=16, seed=0, cache_used=False, anchors_sha256="changed",
                               memory_order_sha256="changed", final_loss=float("nan"),
                               anchor_visits=[201] * 48).items():
            with self.subTest(key=key):
                metadata = self.metadata()
                metadata[key] = value
                self.write_fit(metadata)
                with self.assertRaises(ValueError):
                    diagnostic.validate_fit(self.root, self.plan)

    def fake_run(self, command, **kwargs):
        self.assertTrue(kwargs["check"])
        if "cache" in command or "train" in command:
            self.assertEqual(command[command.index("--source-root") + 1], self.plan["original"])
            self.assertIn("--execute", command)
        if "train" in command:
            self.write_fit(self.metadata())
        if "evaluate" in command:
            directory = self.root / "eval"
            directory.mkdir()
            (directory / (diagnostic.TAG + "__lam1.json")).write_text(json.dumps(
                dict(n_cues=1313, template_check=True, abstain_check=dict(ok=True))))
        return subprocess.CompletedProcess(command, 0)

    def test_positive_coefficient_caches_before_fit_then_native_eval(self):
        with patch.object(diagnostic, "verify", return_value=self.plan) as verify, \
             patch.object(diagnostic.subprocess, "run", side_effect=self.fake_run) as run:
            diagnostic.run_stages(self.root)
        commands = [call.args[0] for call in run.call_args_list]
        self.assertEqual(len(commands), 4)
        self.assertIn("cache", commands[0])
        self.assertIn("train", commands[1])
        self.assertIn("--cache", commands[1])
        self.assertIn("evaluate", commands[2])
        self.assertIn("report", commands[3])
        self.assertEqual(verify.call_count, 2)

    def test_zero_coefficient_no_cache(self):
        self.plan["coefficient"] = 0
        with patch.object(diagnostic, "verify", return_value=self.plan), \
             patch.object(diagnostic.subprocess, "run", side_effect=self.fake_run) as run:
            diagnostic.run_stages(self.root)
        commands = [call.args[0] for call in run.call_args_list]
        self.assertEqual(len(commands), 3)
        self.assertIn("train", commands[0])
        self.assertNotIn("--cache", commands[0])

    def test_existing_fit_is_not_overwritten(self):
        self.write_fit(self.metadata())
        with patch.object(diagnostic, "verify", return_value=self.plan), \
             patch.object(diagnostic.subprocess, "run") as run:
            with self.assertRaises(ValueError):
                diagnostic.run_stages(self.root)
            run.assert_not_called()

    def test_failed_fit_never_evaluates(self):
        self.plan["coefficient"] = 0
        with patch.object(diagnostic, "verify", return_value=self.plan), \
             patch.object(diagnostic.subprocess, "run", side_effect=subprocess.CalledProcessError(1, "fit")) as run:
            with self.assertRaises(subprocess.CalledProcessError):
                diagnostic.run_stages(self.root)
            self.assertEqual(run.call_count, 1)

    def test_unselected_coefficient_rejected_before_source_reads(self):
        with patch.object(diagnostic.preservation, "read_source") as read:
            with self.assertRaises(ValueError):
                diagnostic.prepare(self.root, Path("/original"), Path("/model"), 1.0)
            read.assert_not_called()


if __name__ == "__main__":
    unittest.main()
