import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu import astra_mini_sudoku_diagnostic as diagnostic


class DiagnosticTests(unittest.TestCase):
    def fixture(self, root):
        material = root / "material"
        material.mkdir()
        source = root / "source.py"
        source.write_text("unchanged")
        (material / "source_hashes.json").write_text(json.dumps({str(source): diagnostic.digest(source)}))
        (material / "validation.json").write_text(json.dumps(
            {"boundary": {"validation_backend": "NATIVE_PACKAGE_CPU"}}))
        files = {path.name: diagnostic.digest(path) for path in material.iterdir()}
        (material / "manifest.json").write_text(json.dumps({"status": "PREPARED", "files": files}))
        return material, source

    def test_material_and_source_hash_binding(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            material, source = self.fixture(root)
            self.assertEqual(diagnostic.verify_material(root), material)
            source.write_text("changed")
            with self.assertRaisesRegex(ValueError, "preparation source"):
                diagnostic.verify_material(root)

    def test_changed_material_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            material, _ = self.fixture(root)
            (material / "validation.json").write_text("{}")
            with self.assertRaisesRegex(ValueError, "changed material"):
                diagnostic.verify_material(root)

    def test_synthetic_material_cannot_launch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            material, _ = self.fixture(root)
            (material / "validation.json").write_text(json.dumps(
                {"boundary": {"validation_backend": "SYNTHETIC_CPU_FIXTURE"}}))
            manifest = json.loads((material / "manifest.json").read_text())
            manifest["files"]["validation.json"] = diagnostic.digest(material / "validation.json")
            (material / "manifest.json").write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "native CPU"):
                diagnostic.verify_material(root)

    def test_outputs_are_exclusive(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "receipt.json"
            diagnostic.write_new(output, {"original": True})
            with self.assertRaises(FileExistsError):
                diagnostic.write_new(output, {"original": False})
            self.assertEqual(json.loads(output.read_text()), {"original": True})

    def test_occupied_gpu_rejected_before_proc_scan(self):
        with patch.object(diagnostic.subprocess, "run") as run, patch.object(
                diagnostic.supervisor, "gpu_processes_absent", return_value=False):
            run.return_value.stdout = "<nvidia_smi_log><gpu><uuid>GPU-test</uuid></gpu></nvidia_smi_log>"
            with self.assertRaisesRegex(ValueError, "GPU has processes"):
                diagnostic.check_free("1")


if __name__ == "__main__":
    unittest.main()
