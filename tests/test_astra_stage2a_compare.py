"""Focused synthetic CLI comparison tests; real custody/replay/scoring, no models."""

from contextlib import redirect_stderr, redirect_stdout
import builtins
from hashlib import sha256
import io
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import astra_stage2a_compare as source
from tests import test_astra_stage2a_replay_baseline as fixtures


CLOSED_ID = "STAGE2A-EXPLORATORY-CLOSED-D1-20260914-A1"


class CapturedComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixtures.ReplayStateTests.setUpClass()

    def setUp(self):
        self.fixture = fixtures.ReplayStateTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root
        self.original = self.root / "original"
        self.original.mkdir()
        self.fitted_root = self.root / "fitted"
        self.fitted_root.mkdir()
        self.original_request = dict(master_hex=fixtures.MASTER.hex(), base_state_id=fixtures.BASE_ID,
            atom_state_id=fixtures.ATOM_ID, method="original-ATOM_LOCAL", lineage_id="original-lineage")
        (self.original / "REQUEST.json").write_text(json.dumps(self.original_request))
        self.fixture.capture("original/BASE")
        self.bound = object()
        held = self.fixture.held
        self.held = SimpleNamespace(chains=held.chains, interventions=held.interventions,
            canaries=held.canaries, receipt_sha256=sha256(b"synthetic-held-receipt").hexdigest())
        self.allocate = self.patch(source.prepare, "allocate_source", return_value=self.bound)
        self.prepare = self.patch(source.prepare, "prepare_reduced_held", return_value=self.held)

    def patch(self, target, name, **options):
        patcher = patch.object(target, name, **options)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def fitted(self, *, state_id=fixtures.ATOM_ID, stage="D1", successful=False):
        label = "CLOSED" if state_id == CLOSED_ID else "ATOM_LOCAL"
        return self.fixture.capture("fitted/" + label, state_id, stage=stage, successful=successful)[0]

    def invoke(self, fitted, *, state_id=fixtures.ATOM_ID, stage="D1", output=None):
        output = output or self.root / "comparison.json"
        stdout = io.StringIO()
        original_import = builtins.__import__

        def guarded_import(name, *args, **kwargs):
            if name.split(".")[0] in {"torch", "transformers", "peft", "pickle", "tokenizers"}:
                raise AssertionError("forbidden import:" + name)
            return original_import(name, *args, **kwargs)

        with redirect_stdout(stdout), patch("builtins.__import__", side_effect=guarded_import):
            status = source.main(["--original-run", str(self.original), "--fitted-custody", str(fitted),
                "--fitted-state-id", state_id, "--stage", stage, "--output", str(output)])
        return status, json.loads(output.read_bytes()), json.loads(stdout.getvalue())

    def test_d1_cli_preserves_numerical_misses_exact_criteria_and_inputs(self):
        fitted = self.fitted()
        before = {path: path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
        reductions = []
        reduce_state = source.reducer.reduce_base_d1

        def capture_reduction(**options):
            result = reduce_state(**options)
            reductions.append(result)
            return result

        selected = self.patch(source.reducer, "reduce_base_d1", side_effect=capture_reduction)
        wrong = self.patch(source.reducer, "reduce_base_d2", side_effect=AssertionError("wrong stage reducer"))
        status, report, stdout = self.invoke(fitted)
        self.assertEqual(status, 0)
        self.assertTrue(report["reportable"])
        self.assertFalse(report["criteria_passed"])
        selected.assert_called_once()
        wrong.assert_not_called()
        self.assertEqual(report["criteria"], [dict(source.asdict(row), passed=row.passed)
                                             for row in reductions[0].criteria])
        self.assertEqual([(row["name"], row["denominator"], row["minimum"]) for row in report["criteria"]],
            [(name, 4, 3) for name in fixtures.primitives.TRANSITIONS] + [
                ("typed_interventions", 32, 30), ("whole_chains", 8, 6), ("useful_reads", 8, 7),
                ("typed_steps", 8, 7), ("canaries", 16, 15), ("chain_gain", 8, 2)])
        self.assertEqual(report["states"]["FITTED"]["metrics"]["whole_chains"], 0)
        self.assertEqual(report["states"]["BASE"]["accounting"]["physical_calls"], 56)
        self.assertIsNone(report["provenance"]["fitted_request"])
        self.assertEqual(report["provenance"]["original_request"]["values"], self.original_request)
        self.assertEqual(stdout["sha256"], sha256((self.root / "comparison.json").read_bytes()).hexdigest())
        self.assertEqual(before, {path: path.read_bytes() for path in before})
        self.allocate.assert_called_once_with(master=fixtures.MASTER)
        self.prepare.assert_called_once_with(bound_allocation=self.bound)

    def test_d2_selects_separate_stage_and_original_d1_baseline(self):
        fitted = self.fitted(stage="D2", successful=True)
        selected = self.patch(source.reducer, "reduce_base_d2", wraps=source.reducer.reduce_base_d2)
        wrong = self.patch(source.reducer, "reduce_base_d1", side_effect=AssertionError("wrong stage reducer"))
        status, report, unused = self.invoke(fitted, stage="D2")
        self.assertEqual(status, 0)
        self.assertTrue(report["criteria_passed"])
        selected.assert_called_once()
        wrong.assert_not_called()
        self.assertEqual(selected.call_args.kwargs["base"].stage, "D1")
        self.assertEqual(selected.call_args.kwargs["atom_local"].stage, "D2")
        self.assertEqual(report["states"]["FITTED"]["stage"], "D2")

    def test_closed_provenance_is_not_merged_or_labeled_primary_atom(self):
        fitted = self.fitted(state_id=CLOSED_ID, successful=True)
        declared = dict(closed_state_id=CLOSED_ID, lineage_id="exploratory-closed-lineage", arm="CLOSED")
        request_path = self.fitted_root / "REQUEST.json"
        request_path.write_text(json.dumps(declared))
        status, report, unused = self.invoke(fitted, state_id=CLOSED_ID)
        self.assertEqual(status, 0)
        self.assertEqual(set(report["states"]), {"BASE", "FITTED"})
        self.assertEqual(report["states"]["FITTED"]["state_id"], CLOSED_ID)
        self.assertEqual(report["provenance"]["original_request"]["values"], self.original_request)
        self.assertEqual(report["provenance"]["fitted_request"]["values"], declared)
        self.assertEqual(report["provenance"]["fitted_request"]["sha256"], sha256(request_path.read_bytes()).hexdigest())
        self.assertIn("CLOSED remains exploratory", report["limitations"][0])
        for name in ("native_authorized", "persisted_custody_verified", "qualification", "science_gates"):
            self.assertNotIn(name, report)

    def test_output_must_be_fresh_and_outside_custody_before_replaying(self):
        fitted = self.fitted()
        output = self.root / "existing.json"
        output.write_bytes(b"retained")
        compare = self.patch(source, "compare_captured", side_effect=AssertionError("must not replay"))
        for destination in (output, fitted / "comparison.json", self.original / "BASE" / "comparison.json"):
            with self.subTest(destination=destination), redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as caught:
                    self.invoke(fitted, output=destination)
                self.assertEqual(caught.exception.code, 2)
        compare.assert_not_called()
        self.assertEqual(output.read_bytes(), b"retained")

    def test_wrong_stage_id_and_missing_custody_never_publish(self):
        fitted = self.fitted(stage="D2")
        for stage, state_id in (("D1", fixtures.ATOM_ID), ("D2", "foreign")):
            with self.subTest(stage=stage, state_id=state_id), redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    self.invoke(fitted, stage=stage, state_id=state_id)
                self.assertFalse((self.root / "comparison.json").exists())
        (fitted / "COMPLETE").unlink()
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            self.invoke(fitted, stage="D2")
        self.assertFalse((self.root / "comparison.json").exists())

    def test_rejects_duplicate_request_fields_before_binding(self):
        fitted = self.fitted()
        (self.original / "REQUEST.json").write_text('{"master_hex":"00","master_hex":"11"}')
        with self.assertRaisesRegex(ValueError, "duplicate_request_field"):
            source.compare_captured(original_run=self.original, fitted_custody=fitted,
                                    fitted_state_id=fixtures.ATOM_ID, stage="D1")
        self.allocate.assert_not_called()

    def test_input_drift_is_rejected_before_output(self):
        fitted = self.fitted()
        reduce_state = source.reducer.reduce_base_d1

        def mutate_request(**options):
            result = reduce_state(**options)
            (self.original / "REQUEST.json").write_text(json.dumps(dict(self.original_request, method="changed")))
            return result

        self.patch(source.reducer, "reduce_base_d1", side_effect=mutate_request)
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            self.invoke(fitted)
        self.assertFalse((self.root / "comparison.json").exists())

    def test_import_and_help_have_no_model_or_deserializer_imports(self):
        script = """
import builtins
original_import = builtins.__import__
def guarded(name, *args, **kwargs):
    if name.split('.')[0] in {'torch', 'transformers', 'peft', 'pickle', 'tokenizers'}:
        raise AssertionError('forbidden import:' + name)
    return original_import(name, *args, **kwargs)
builtins.__import__ = guarded
from gpu import astra_stage2a_compare
astra_stage2a_compare.main(['--help'])
"""
        completed = subprocess.run([sys.executable, "-B", "-c", script],
            cwd=Path(source.__file__).resolve().parent.parent, capture_output=True, text=True, timeout=30)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("--fitted-state-id", completed.stdout)
        self.assertIn("--stage {D1,D2}", completed.stdout)


if __name__ == "__main__":
    unittest.main()
