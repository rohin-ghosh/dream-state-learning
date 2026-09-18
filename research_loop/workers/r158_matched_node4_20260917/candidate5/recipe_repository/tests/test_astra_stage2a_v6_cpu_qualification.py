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
    def test_middle_mutation_always_changes_original_ascii_byte(self):
        for byte in range(128):
            raw = b"left" + bytes((byte,)) + b"rite"
            mutated = runner.boundary_byte_mutations(raw)
            self.assertNotEqual(mutated["middle"], raw)
            self.assertEqual(len(mutated["middle"]), len(raw))
            self.assertEqual(sum(left != right for left, right in zip(raw, mutated["middle"])), 1)
        self.assertNotEqual(runner.boundary_byte_mutations(b"abcdXefgh")["middle"], b"abcdXefgh")

    def test_independent_logical_slots_and_paired_seeds(self):
        from organism_v6 import composition_birth_stage2a_screen as screen
        with patch.object(runner, "screen", screen, create=True):
            receipt = runner.verify_reduced_pairing(b"qualification-regression")
            self.assertEqual(receipt["BASE"], receipt["D1_ATOM_LOCAL"])
            self.assertEqual(len(receipt["BASE"]["slots"]), 280)
            slots = receipt["BASE"]["slots"]
            self.assertEqual(slots[0][-1], 0)
            self.assertEqual(slots[29][-1], 116)
            self.assertEqual(slots[232][-1], 928)
            self.assertEqual(slots[-1][-1], 1007)
            with patch.object(screen, "reduced_screen", return_value=screen.reduced_screen("D1")[1:]):
                with self.assertRaisesRegex(ValueError, "independent_logical_slot_mismatch"):
                    runner.verify_reduced_pairing(b"qualification-regression")

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

    def test_route_detector_requires_both_injected_ports_and_exact_spans(self):
        probe = {"raw": b"STEP FIRST\nSTEP SECOND", "grammar": "actions",
                 "first_port": "FIRST", "second_port": "SECOND", "first_span": (0, 10), "second_span": (11, 22)}
        exact = dict(grammar="actions", first_port="FIRST", second_port="SECOND",
                     first_span=(100, 110), second_span=(111, 122))
        report = lambda values: SimpleNamespace(route_scan=SimpleNamespace(issues=(SimpleNamespace(**values),)))
        self.assertTrue(runner.intended_detector(report(exact), "route_actions_literal", probe["raw"], 100,
                                                 route_probe=probe))
        for replacement in ({"first_port": "OTHER"}, {"second_port": "OTHER"}, {"first_span": (0, 10)},
                            {"second_span": (111, 123)}, {"grammar": "event_rows"}):
            self.assertFalse(runner.intended_detector(report(dict(exact, **replacement)), "route_actions_literal",
                                                      probe["raw"], 100, route_probe=probe))
        with self.assertRaisesRegex(ValueError, "independent_route_probe_required"):
            runner.intended_detector(report(exact), "route_actions_literal", probe["raw"], 100)


if __name__ == "__main__":
    unittest.main()
