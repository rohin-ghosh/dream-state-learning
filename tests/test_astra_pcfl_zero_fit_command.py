"""CLI custody tests with mocked measurement APIs; no native model execution."""

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from gpu import astra_pcfl_zero_fit_command as command


class CommandTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest = self.root / "manifest.json"
        self.payload = {"test_only": False, "actor": {"gpu_uuid": "GPU-test", "model_path": "unused"},
                        "output_dir": str(self.root / "output")}

    def save(self):
        command.write_json(self.manifest, self.payload)
        return command.file_hash(self.manifest)

    def test_writes_are_exclusive(self):
        self.save()
        with self.assertRaises(FileExistsError):
            self.save()

    def test_hash_mismatch_precedes_load(self):
        self.save()
        with patch.object(command, "offline_tokenizer") as load:
            with self.assertRaisesRegex(ValueError, "manifest file drift"):
                command.run(self.manifest, "0" * 64)
            load.assert_not_called()

    def test_synthetic_manifest_rejected_before_load(self):
        self.payload["test_only"] = True
        expected = self.save()
        with patch.object(command, "offline_tokenizer") as load:
            with self.assertRaisesRegex(ValueError, "synthetic"):
                command.run(self.manifest, expected)
            load.assert_not_called()

    def test_wrong_gpu_rejected_before_load(self):
        expected = self.save()
        with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "GPU-other"}):
            with self.assertRaisesRegex(ValueError, "allocated GPU"):
                command.run(self.manifest, expected)

    def test_existing_attempt_rejected_before_load(self):
        expected = self.save()
        Path(self.payload["output_dir"]).mkdir()
        with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "GPU-test"}), patch.object(command, "offline_tokenizer") as load:
            with self.assertRaisesRegex(ValueError, "attempt already exists"):
                command.run(self.manifest, expected)
            load.assert_not_called()

    def test_run_calls_real_entry_api_once(self):
        expected = self.save()
        tokenizer = object()
        diagnostic = Mock()
        diagnostic.run.return_value = {"status": "FAILED"}
        with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "GPU-test"}), \
                patch.object(command, "offline_tokenizer", return_value=tokenizer), \
                patch.object(command.driver, "Diagnostic", return_value=diagnostic) as build:
            self.assertEqual(command.run(self.manifest, expected), {"status": "FAILED"})
        build.assert_called_once_with(self.payload, tokenizer)
        diagnostic.run.assert_called_once_with()

    def test_measure_requires_cpu_visibility(self):
        with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "GPU-test"}):
            with self.assertRaisesRegex(ValueError, "disable CUDA"):
                command.measure("absent", "absent", self.root / "measure")
        self.assertFalse((self.root / "measure").exists())

    def test_measure_failure_is_preserved(self):
        with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": ""}):
            with self.assertRaises(FileNotFoundError):
                command.measure("absent", "absent", self.root / "measure")
        receipt = json.loads((self.root / "measure/failure.json").read_bytes())
        self.assertEqual(receipt["model_calls"], 0)
        self.assertEqual(receipt["type"], "FileNotFoundError")
        with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": ""}):
            with self.assertRaises(FileExistsError):
                command.measure("absent", "absent", self.root / "measure")

    def test_prepare_rejects_unbounded_budget(self):
        with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": ""}):
            for cap in (0, 36001):
                with self.assertRaisesRegex(ValueError, "bounded time"):
                    command.prepare("absent", "absent", "GPU-test", self.root / "output", self.manifest, cap, 100)

    def test_loader_requires_offline_environment(self):
        with patch.dict(os.environ, {"HF_HUB_OFFLINE": "0"}):
            with self.assertRaisesRegex(ValueError, "offline environment"):
                command.offline_tokenizer("unused")


if __name__ == "__main__":
    unittest.main()
