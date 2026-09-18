import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import astra_pcfl_cpu_smoke as smoke


class CPUSmokeTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.source = Path(directory.name)
        self.output = self.source / "result"
        script = self.source / "gpu" / "astra_pcfl_cpu_smoke.py"
        script.parent.mkdir()
        script.write_bytes(Path(smoke.__file__).read_bytes())
        manifest = self.source / "cpu_source_manifest.json"
        manifest.write_text(json.dumps({"gpu/astra_pcfl_cpu_smoke.py": smoke.file_hash(script)}))
        self.manifest_hash = smoke.file_hash(manifest)
        self.environment = patch.dict(os.environ, CUDA_VISIBLE_DEVICES="", HF_HUB_OFFLINE="1", ASTRA_PCFL_TINY_CPU="1",
                                      TRANSFORMERS_OFFLINE="1")
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def execute(self, *, cuda=False, skip=False):
        test = unittest.FunctionTestCase(lambda: None)
        if skip:
            test = unittest.FunctionTestCase(lambda: self.skipTest("not numerical evidence"))
        fake_torch = SimpleNamespace(cuda=SimpleNamespace(is_available=lambda: cuda),
                                     set_num_threads=lambda count: None, get_num_threads=lambda: 1)
        with patch.dict("sys.modules", torch=fake_torch), \
             patch.object(smoke.importlib.metadata, "version", return_value="test"), \
             patch.object(unittest.defaultTestLoader, "discover", return_value=unittest.TestSuite([test])), \
             contextlib.redirect_stdout(io.StringIO()):
            return smoke.run(self.source, self.output, self.manifest_hash)

    def test_environment_rejects_before_claim(self):
        os.environ["CUDA_VISIBLE_DEVICES"] = "0"
        with self.assertRaisesRegex(ValueError, "CPU/offline"):
            self.execute()
        self.assertFalse(self.output.exists())

    def test_source_drift_rejects_before_claim(self):
        (self.source / "gpu" / "astra_pcfl_cpu_smoke.py").write_text("changed")
        with self.assertRaisesRegex(ValueError, "source mismatch"):
            self.execute()
        self.assertFalse(self.output.exists())

    def test_cpu_receipt_and_no_overwrite(self):
        self.assertEqual(self.execute(), 0)
        receipt = json.loads((self.output / "receipt.json").read_text())
        self.assertEqual(receipt["tests_run"], 1)
        self.assertTrue(receipt["fixture_only"])
        self.assertFalse(receipt["scientific_readiness"])
        self.assertEqual(receipt["tests_log_sha256"], smoke.file_hash(self.output / "tests.log"))
        with self.assertRaises(FileExistsError):
            self.execute()

    def test_skipped_numerical_work_is_not_pass(self):
        self.assertEqual(self.execute(skip=True), 1)
        receipt = json.loads((self.output / "receipt.json").read_text())
        self.assertEqual(receipt["status"], "FAIL")
        self.assertEqual(len(receipt["skips"]), 1)

    def test_cuda_availability_preserves_error(self):
        self.assertEqual(self.execute(cuda=True), 1)
        receipt = json.loads((self.output / "receipt.json").read_text())
        self.assertEqual(receipt["status"], "ERROR")
        self.assertIn("CUDA", receipt["error"])

    def test_only_known_dependency_absence_skip_is_expected(self):
        known = SimpleNamespace(id=lambda: "test_pcfl_vertical_train.WriterTests.test_missing_torch_preserves_failed_attempt_no_retry")
        self.assertTrue(smoke.expected_dependency_skip(known, "explicit missing-dependency path on this VM"))
        self.assertFalse(smoke.expected_dependency_skip(known, "Torch absent; no numerical/native qualification"))
        other = SimpleNamespace(id=lambda: "test_pcfl_vertical_train.TinyCPUWriterTests.test_real_bf16_qwen_lora_adamw_200_steps_save_reload")
        self.assertFalse(smoke.expected_dependency_skip(other, "explicit missing-dependency path on this VM"))


if __name__ == "__main__":
    unittest.main()
