"""Qualification launch custody and detector specificity, without a corpus run."""

from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import astra_stage2a_v6_cpu_qualification as runner


class QualificationHarnessTests(unittest.TestCase):
    def test_import_does_not_load_implementation_before_snapshot_pins(self):
        command = [sys.executable, "-B", "-c", "import sys; from gpu import astra_stage2a_v6_cpu_qualification; "
                   "assert not any(name.startswith('organism_v6') for name in sys.modules)"]
        subprocess.run(command, cwd=runner.ROOT, check=True)

    def test_bootstrap_detaches_readonly_source_before_child_launch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "checkout"
            (root / "gpu").mkdir(parents=True)
            source = root / "gpu/astra_stage2a_v6_cpu_qualification.py"
            source.write_bytes(b"original source")
            out = Path(directory) / "fresh_attempt"
            options = SimpleNamespace(out=str(out), master="FIXTURE", snapshot_manifest=None)

            def launched(command, **kwargs):
                source.write_bytes(b"later repair")
                snapshot = out / "source"
                staged = snapshot / "gpu" / source.name
                self.assertEqual(staged.read_bytes(), b"original source")
                self.assertEqual(staged.stat().st_mode & 0o222, 0)
                self.assertEqual(snapshot.stat().st_mode & 0o222, 0)
                self.assertEqual(kwargs["cwd"], snapshot)
                self.assertEqual(kwargs["env"]["PYTHONPATH"], str(snapshot))
                self.assertEqual(kwargs["env"]["CUDA_VISIBLE_DEVICES"], "")
                manifest = json.loads((out / "SNAPSHOT.json").read_bytes())
                self.assertEqual(manifest["source_pins"]["gpu/" + source.name],
                                 sha256(b"original source").hexdigest())
                self.assertIn(str(staged), command)
                return SimpleNamespace(returncode=0)

            with patch.object(runner, "ROOT", root), patch.object(runner.subprocess, "run", side_effect=launched):
                self.assertEqual(runner.bootstrap(options), 0)
                with self.assertRaises(FileExistsError):
                    runner.bootstrap(options)

    def test_pin_mismatch_precedes_any_implementation_import(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            snapshot = out / "source"
            (snapshot / "gpu").mkdir(parents=True)
            (snapshot / "gpu/astra_stage2a_v6_cpu_qualification.py").write_bytes(b"unexpected")
            manifest = out / "SNAPSHOT.json"
            manifest.write_text(json.dumps({"source_pins": {"gpu/astra_stage2a_v6_cpu_qualification.py": "0" * 64}}))
            options = SimpleNamespace(out=str(out), master="FIXTURE", snapshot_manifest=str(manifest))
            with patch.object(runner, "ROOT", snapshot), patch.object(runner, "load_implementation") as loader:
                with self.assertRaisesRegex(ValueError, "pin_mismatch_before_import"):
                    runner.run(options)
                loader.assert_not_called()

    def test_an_unrelated_failure_cannot_satisfy_intended_detector(self):
        source = SimpleNamespace(FORBIDDEN_EDGE_LABELS=(b"LINK", b"OLD", b"NEW"))
        wrong = SimpleNamespace(category="operand", value=b"SECRET", start=50)
        report = SimpleNamespace(content_scan=SimpleNamespace(issues=(wrong,)),
                                 private_issues=(), route_scan=SimpleNamespace(issues=()), typed_issues=())
        with patch.object(runner, "typed_scan", source, create=True):
            self.assertFalse(runner.intended_detector(report, "full_target", b"SECRET", 40))
            self.assertFalse(runner.intended_detector(report, "operand", b"SECRET", 51))
            self.assertTrue(runner.intended_detector(report, "operand", b"SECRET", 40))


if __name__ == "__main__":
    unittest.main()
