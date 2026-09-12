import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu import astra_mini_sudoku_diagnostic as diagnostic


class DiagnosticTests(unittest.TestCase):
    def test_paired_execution_is_sequential_on_one_reserved_device(self):
        with patch.object(diagnostic, "execute") as execute:
            diagnostic.execute_selected(Path("/unused"), "paired", "1", 2)
        self.assertEqual([call.args for call in execute.call_args_list], [
            (Path("/unused"), "useful", "1", 2), (Path("/unused"), "corrupt", "1", 2)])

    def test_single_arm_default_seed_path_is_preserved(self):
        with patch.object(diagnostic, "execute") as execute:
            diagnostic.execute_selected(Path("/unused"), "corrupt", "3", 0)
        execute.assert_called_once_with(Path("/unused"), "corrupt", "3", 0)

    def test_failed_first_arm_does_not_claim_paired_completion(self):
        with patch.object(diagnostic, "execute", side_effect=RuntimeError("worker failed")) as execute:
            with self.assertRaisesRegex(RuntimeError, "worker failed"):
                diagnostic.execute_selected(Path("/unused"), "paired", "1", 1)
        self.assertEqual(execute.call_count, 1)

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

    def test_wrong_interpreter_seed_or_destination_fails_before_training(self):
        for field in ("interpreter", "seed", "destination"):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                material, _ = self.fixture(root)
                argv = [diagnostic.sys.executable, "--out", str(root / "training/useful_seed0"),
                        "--seed", "0"]
                position = {"interpreter": 0, "destination": 2, "seed": 4}[field]
                argv[position] = "unexpected"
                command = dict(argv=argv, seed=0, cwd=str(diagnostic.SOURCE))
                command_path = material / "trainer_commands.json"
                command_path.write_text(json.dumps({"commands": {"useful": command}}))
                manifest = json.loads((material / "manifest.json").read_text())
                manifest["files"][command_path.name] = diagnostic.digest(command_path)
                (material / "manifest.json").write_text(json.dumps(manifest))
                with patch.object(diagnostic.supervisor, "run_worker") as worker:
                    with self.assertRaisesRegex(ValueError, "interpreter, seed, or destination"):
                        diagnostic.execute(root, "useful", "1", 0)
                    worker.assert_not_called()

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
        with patch.object(diagnostic.subprocess, "run") as run:
            run.return_value.stdout = ("<nvidia_smi_log><gpu><uuid>GPU-test</uuid>"
                                      "<processes><process_info /></processes></gpu></nvidia_smi_log>")
            with self.assertRaisesRegex(ValueError, "GPU has processes"):
                diagnostic.check_free("1")


if __name__ == "__main__":
    unittest.main()
