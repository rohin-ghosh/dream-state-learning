"""Snapshot/export harness checks; no complete population or native execution."""

from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import astra_stage2a_cpu_separation as runner


class SeparationHarnessTests(unittest.TestCase):
    def test_import_precedes_project_or_model_imports(self):
        subprocess.run([sys.executable, "-B", "-c", "import sys; from gpu import astra_stage2a_cpu_separation; "
                        "assert not any(key.startswith(('organism_v6', 'torch', 'transformers')) for key in sys.modules)"],
                       cwd=runner.ROOT, check=True)

    def test_snapshot_is_detached_and_readonly(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "checkout"
            original = root / "gpu/astra_stage2a_cpu_separation.py"
            original.parent.mkdir(parents=True)
            original.write_bytes(b"fixed source")
            out = Path(temporary) / "attempt"
            pins = {"gpu/astra_stage2a_cpu_separation.py": sha256(original.read_bytes()).hexdigest()}

            def child(command, **kwargs):
                original.write_bytes(b"new unrelated revision")
                snapshot = out / "source"
                retained = snapshot / "gpu/astra_stage2a_cpu_separation.py"
                self.assertEqual(retained.read_bytes(), b"fixed source")
                self.assertEqual(retained.stat().st_mode & 0o222, 0)
                self.assertEqual(snapshot.stat().st_mode & 0o222, 0)
                self.assertEqual(kwargs["cwd"], snapshot)
                self.assertEqual(kwargs["env"]["PYTHONPATH"], str(snapshot))
                self.assertEqual(kwargs["env"]["CUDA_VISIBLE_DEVICES"], "")
                self.assertEqual(json.loads((out / "SNAPSHOT.json").read_bytes())["source_pins"], pins)
                self.assertIn(str(retained), command)
                return SimpleNamespace(returncode=0)

            options = SimpleNamespace(out=str(out), master="fixed", snapshot_manifest=None)
            with patch.object(runner, "ROOT", root), patch.object(runner, "source_pins", return_value=pins), \
                    patch.object(runner.subprocess, "run", side_effect=child):
                self.assertEqual(runner.bootstrap(options), 0)
                with self.assertRaises(FileExistsError):
                    runner.bootstrap(options)

    def test_wrong_snapshot_rejected_before_construction(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary)
            options = SimpleNamespace(out=str(out), master="fixed", snapshot_manifest=str(out / "SNAPSHOT.json"))
            with self.assertRaisesRegex(ValueError, "snapshot_execution_required"):
                runner.execute(options)

    def test_write_once_preserves_existing_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "receipt.json"
            runner.write_once(destination, b"first")
            with self.assertRaises(FileExistsError):
                runner.write_once(destination, b"second")
            self.assertEqual(destination.read_bytes(), b"first")


if __name__ == "__main__":
    unittest.main()
