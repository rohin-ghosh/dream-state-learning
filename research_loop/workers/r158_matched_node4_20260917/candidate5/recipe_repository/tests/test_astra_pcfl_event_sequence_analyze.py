"""Synthetic archives only; NATIVE fields imitate receipt schemas, not real runs."""

import copy
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gpu import astra_pcfl_event_sequence_analyze as api
import test_astra_pcfl_event_sequence_readout as fixtures


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.harness = fixtures.ReadoutTests("test_c0_exact16_order_tokens_no_training_or_history")
        self.harness.setUp()
        self.addCleanup(self.harness.doCleanups)
        self.root, self.states = self.harness.root, {}
        imported = copy.deepcopy(self.harness.imported)
        imported.pop("sha256")
        for generation in imported["generations"]:
            generation["origin"] = "CHILD_NATIVE"
        self.harness.imported = api.prefix.seal(imported)
        api.prefix.build_import.return_value = self.harness.imported
        self.harness.material = api.sequence.export_material(self.harness.imported, self.harness.imported["sha256"], self.harness.tokenizer)
        self.material = self.harness.store("material.json", self.harness.material)
        self.harness.inputs["material"] = self.material

    def write(self, path, value):
        Path(path).write_bytes(api.prefix.canonical(value) + b"\n")

    def refresh(self, state):
        root = Path(self.states[state]["outer"])
        completed = api.read(root / "readout/completed.json")
        completed.pop("sha256")
        completed["files"] = {name: entry["sha256"] for name, entry in api.inventory(root / "readout").items() if name != "completed.json"}
        completed = api.prefix.seal(completed)
        self.write(root / "readout/completed.json", completed)
        (root / "readout_completed.json").write_bytes((root / "readout/completed.json").read_bytes())
        collection = api.read(root / "collection.json")
        collection.pop("sha256")
        collection["completed_sha256"] = completed["sha256"]
        collection["stage_inventory"] = api.inventory(root / "readout")
        collection["files"] = {name: entry for name, entry in api.inventory(root).items() if name != "collection.json"}
        self.write(root / "collection.json", api.prefix.seal(collection))
        self.states[state]["collection_sha256"] = api.file_hash(root / "collection.json")

    def state(self, state, correct=(), *, bad_predecessor=False):
        root = self.root / ("outer_" + state)
        root.mkdir()
        phase = api.sequence.READ_STATES[state]
        fit_root = self.harness.completed_fit(phase) if phase else None
        if not phase:
            self.harness.inputs["fit_receipt"] = None
        self.harness.texts = [record["target"] if index in correct else "MISS"
                             for index, record in enumerate(self.harness.material["spec"]["records"] * 2)]
        self.harness.run_readout(state, output=root / "readout")
        inputs = api.read(root / "readout/inputs.json")
        completed = api.read(root / "readout/completed.json")
        if fit_root:
            receipt = api.read(fit_root / "completed.json")
            receipt.pop("sha256")
            receipt["kind"] = "NATIVE"
            receipt["predecessor"] = None
            if state in ("SEQ_REPLAY", "SEQ_NEW_ONLY"):
                receipt["predecessor"] = copy.deepcopy(api.read(self.root / "outer_S_A/readout/inputs.json")["fit_receipt"])
                if bad_predecessor:
                    receipt["predecessor"]["sha256"] = "0" * 64
            self.write(fit_root / "completed.json", api.prefix.seal(receipt))
            inputs["fit_receipt"] = self.harness.pin(fit_root / "completed.json")
            completed["fit_receipt"] = inputs["fit_receipt"]
        for name in ("actor/identity.json", "actor/load.json", "actor/close.json", "actor_close.json", "custody.json",
                     *[f"actor/call_{index:04d}.raw.json" for index in range(16)]):
            value = api.read(root / "readout" / name)
            value["kind"] = "NATIVE_OWN_WRITE_READOUT"
            self.write(root / "readout" / name, value)
        custody = api.read(root / "readout/custody.json")
        custody["identity_sha256"] = api.digest(api.read(root / "readout/actor/identity.json"))
        self.write(root / "readout/custody.json", custody)
        self.write(root / "readout/inputs.json", inputs)
        self.write(Path(completed["inputs"]["path"]), inputs)
        completed["inputs"]["sha256"] = api.file_hash(completed["inputs"]["path"])
        completed["kind"] = "NATIVE"
        self.write(root / "readout/completed.json", completed)
        self.write(root / "inputs.input.json", inputs)
        identity = {"pid": os.getpid(), "uid": os.getuid(), "boot_id": "SYNTHETIC", "pgid": os.getpid(), "sid": os.getpid()}
        self.write(root / "allocation.input.json", {"uid": identity["uid"], "boot_id": identity["boot_id"], "gpu_uuid": inputs["gpu_uuid"]})
        self.write(root / "binding.json", {"argv": ["SYNTHETIC", "--output", str(root / "readout")],
                                           "deadline_monotonic": 1060, "worker_deadline_monotonic": 1000})
        self.write(root / "context.json", {"schema": api.outer.SCHEMA, "stage": "readout", "state": state,
            "inputs": completed["inputs"], "outer_source_sha256": "a" * 64, "entry_monotonic": 0})
        self.write(root / "worker_start.json", {"identity": identity})
        self.write(root / "worker_exit.json", {"identity": identity, "pid": identity["pid"], "returncode": 0, "signal": None})
        observations = {"worker_wait": 0, "worker_release": {"identity": identity, "owned_group_released": True}}
        for when in ("pre", "post"):
            observations.update({when + "_queue": {"matched": True}, when + "_gpu": {"empty": True, "gpu_uuid": inputs["gpu_uuid"]},
                                 when + "_cvd": {"clear": True, "owners": [], "unresolved": []}})
        for name, value in observations.items():
            self.write(root / (name + ".json"), {"started_monotonic": 1, "ended_monotonic": 2, "value": value})
        self.write(root / "collection.json", api.prefix.seal({"schema": api.outer.SCHEMA + "/collection", "stage": "readout",
            "state": state, "status": "COMPLETED", "errors": [], "returncode": 0, "gpu_released": True, "retries": 0,
            "automatic_promotion": False, "full_contract_released": False, "original_status": "FORMATION_FAILED",
            "inputs": completed["inputs"], "allocation_file_sha256": api.file_hash(root / "allocation.input.json"),
            "outer_source_sha256": "a" * 64, "worker_identity": identity, "observations": observations,
            "elapsed_seconds": 100, "files": {}, "stage_inventory": {}, "completed_sha256": completed["sha256"]}))
        self.states[state] = {"outer": str(root), "collection_sha256": "0" * 64}
        self.refresh(state)
        return root

    def pair(self, correct=()):
        self.state("NO_WRITE")
        return self.state("S_A", correct)

    def analyze(self, **kwargs):
        return api.analyze(self.material, self.states, **kwargs)

    def test_zero_pair_partial_report_no_retention_denominator(self):
        self.pair()
        before = {state: api.inventory(Path(entry["outer"])) for state, entry in self.states.items()}
        with patch.object(api.sequence.trainer, "run_training", side_effect=AssertionError("no training")), \
                patch.object(api.outer, "controller", side_effect=AssertionError("no lifecycle")):
            result = self.analyze()
        self.assertEqual(result["missing_states"], ["SEQ_REPLAY", "SEQ_NEW_ONLY", "FRESH_MIX", "ALL_AVAILABLE"])
        for state in result["states"].values():
            for banks in state["panels"].values():
                for panel in banks.values():
                    self.assertEqual((panel["correct"], panel["denominator"]), (0, 4))
        panel = result["comparisons"]["S_A"]["panels"]["W8"]["A"]
        self.assertEqual(panel["pre_correct"], 0)
        self.assertIsNone(panel["retention_fraction"])
        self.assertIsNone(result["pass_threshold"])
        self.assertEqual(result["sa_pre_correct_A"], {"W0": 0, "W8": 0})
        self.assertIsNone(result["states"]["NO_WRITE"]["fit"])
        self.assertEqual(result["states"]["S_A"]["fit"]["updates"], 40)
        self.assertEqual(result["status"], "DESCRIPTIVE_ONLY")
        self.assertEqual(before, {state: api.inventory(Path(entry["outer"])) for state, entry in self.states.items()})
        self.assertEqual(result["states"]["S_A"]["collection_file_sha256"], self.states["S_A"]["collection_sha256"])

    def test_descendant_retention_and_fresh_control_overlap_differ(self):
        self.pair(correct=(8, 9))
        self.state("SEQ_REPLAY", correct=(8, 10))
        self.state("FRESH_MIX", correct=(8, 10))
        result = self.analyze()
        transition = result["comparisons"]["SEQ_REPLAY"]["panels"]["W8"]["A"]
        self.assertEqual(transition, {"pre_correct": 2, "post_correct": 2, "kept": 1, "lost": 1, "gained": 1, "retention_fraction": .5})
        self.assertIsNone(result["comparisons"]["FRESH_MIX"]["panels"]["W8"]["A"]["retention_fraction"])
        self.assertIsNone(result["comparisons"]["SEQ_REPLAY"]["panels"]["W0"]["A"]["retention_fraction"])

    def test_wrong_measured_sa_parent_is_not_retention(self):
        self.pair(correct=(8,))
        self.state("SEQ_NEW_ONLY", correct=(8,), bad_predecessor=True)
        with self.assertRaisesRegex(ValueError, "measured S_A checkpoint"):
            self.analyze()

    def test_resealed_false_scores_rejected_by_raw_recomputation(self):
        root = self.pair()
        scores = api.read(root / "readout/scores.json")
        scores["results"][8]["score"]["strict"] = True
        scores["results"][8]["strict_stop"] = True
        self.write(root / "readout/scores.json", scores)
        self.refresh("S_A")
        with self.assertRaisesRegex(ValueError, "raw recomputation"):
            self.analyze()

    def test_failed_outer_flags_or_unreleased_worker_rejected(self):
        root = self.pair()
        collection = api.read(root / "collection.json")
        for changes in ({"status": "FAILED"}, {"returncode": 7}, {"gpu_released": False}, {"errors": ["SYNTHETIC"]}):
            changed = {**collection, **changes}
            changed.pop("sha256")
            self.write(root / "collection.json", api.prefix.seal(changed))
            self.states["S_A"]["collection_sha256"] = api.file_hash(root / "collection.json")
            with self.assertRaisesRegex(ValueError, "outer completion/release"):
                self.analyze()

    def test_missing_capture_not_zero_filled(self):
        root = self.pair()
        (root / "readout/actor/call_0015.raw.json").unlink()
        self.refresh("S_A")
        with self.assertRaisesRegex(ValueError, "capture count"):
            self.analyze()

    def test_explicit_fit_receipt_remap_preserves_original_paths(self):
        self.pair()
        original = self.root / "fit_S_A"
        moved = self.root / "unpacked_fit"
        original.rename(moved)
        with self.assertRaises(FileNotFoundError):
            self.analyze()
        result = self.analyze(remap={str(original): str(moved)})
        self.assertEqual(result["states"]["S_A"]["fit_receipt"]["path"], str(original / "completed.json"))

    def test_material_tamper_and_missing_initial_state_fail(self):
        self.state("NO_WRITE")
        with self.assertRaisesRegex(ValueError, "NO_WRITE and S_A required"):
            self.analyze()
        self.state("S_A")
        Path(self.material["path"]).write_text("{}")
        with self.assertRaisesRegex(ValueError, "bound file hash"):
            self.analyze()


if __name__ == "__main__":
    unittest.main()
