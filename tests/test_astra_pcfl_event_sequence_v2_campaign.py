"""CPU orchestration fixtures do not certify native stage evidence."""

import argparse
import copy
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from gpu import astra_pcfl_event_sequence_v2_campaign as api


class CampaignTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.entries = []
        for seed in range(3):
            directory = self.root / f"seed{seed}"
            directory.mkdir()
            api.fit.write(directory / "allocation.json", {"outer_sha256": "a" * 64, "lease_end": time.time() + 86400,
                                                         "lease_margin_seconds": 21600, "gpu_index": seed + 1, "gpu_uuid": f"GPU-{seed}"})
            api.fit.write(directory / "material.json", {"spec": {"learner_seed": seed, "sha256": str(seed) * 64}})
            shared = dict.fromkeys(("model_path", "model_binding", "base_state_receipt", "replay_receipt", "archive", "environment"), "SYNTHETIC")
            shared.update(learner_seed=seed, gpu_uuid=f"GPU-{seed}", material=api.pin(directory / "material.json"))
            api.fit.write(directory / "fit_inputs.json", {**shared, "schema": api.fit.SCHEMA + "/inputs", "predecessor": None})
            api.fit.write(directory / "c0_inputs.json", {**shared, "schema": api.readout.SCHEMA + "/inputs", "fit_receipt": None})
            self.entries.append({"seed": seed, "gpu": seed + 1, "allocation": api.pin(directory / "allocation.json"),
                                 "fit_inputs": api.pin(directory / "fit_inputs.json"), "c0_inputs": api.pin(directory / "c0_inputs.json"),
                                 "material": api.pin(directory / "material.json"), "spec_sha256": str(seed) * 64})
        self.manifest = {"schema": api.SCHEMA, "status": "PREPARED_NOT_EXECUTED", "source_files": {}, "entries": self.entries, "budget": api.BUDGET}
        api.fit.write(self.root / "manifest.json", self.manifest)
        self.args = argparse.Namespace(root=str(self.root), manifest_sha256=api.pin(self.root / "manifest.json")["sha256"])
        self.calls = []

    def stage(self, inputs_path, inputs_sha, allocation_path, allocation_sha, output, **selection):
        self.calls.append(selection)
        api.fit.read_pin({"path": inputs_path, "sha256": inputs_sha})
        root = Path(output)
        root.mkdir()
        if selection["stage"] == "fit":
            (root / "fit").mkdir()
            api.fit.write(root / "fit/completed.json", {"synthetic": True})
        else:
            loaded = api.fit.read_pin({"path": inputs_path, "sha256": inputs_sha})
            self.assertEqual(bool(loaded["fit_receipt"]), selection["state"] == "A200")
        result = {"status": "COMPLETED", "gpu_released": True, "errors": []}
        api.fit.write(root / "collection.json", result)
        return result

    def test_nine_serial_stages_no_descendants_or_promotion(self):
        with patch.object(api.outer, "controller", side_effect=self.stage):
            api.run(self.args)
        result = api.outer.read(self.root / "completed.json")
        self.assertEqual(len(self.calls), 9)
        self.assertEqual([(call["stage"], call["state"]) for call in self.calls],
                         [("fit", None), ("readout", "NO_WRITE"), ("readout", "A200")] * 3)
        self.assertFalse(result["descendants_enabled"])
        self.assertFalse(result["automatic_promotion"])

    def test_failed_fit_stops_before_readout_without_retry(self):
        def failure(*args, **kwargs):
            result = self.stage(*args, **kwargs)
            return {**result, "status": "FAILED", "errors": ["synthetic failure"]}
        with patch.object(api.outer, "controller", side_effect=failure):
            with self.assertRaisesRegex(ValueError, "failed stage"):
                api.run(self.args)
        self.assertEqual(len(self.calls), 1)
        self.assertFalse((self.root / "completed.json").exists())
        self.assertTrue(api.outer.read(self.root / "stopped.json")["no_automatic_retry"])

    def test_manifest_drift_and_existing_start_refused(self):
        with patch.object(api.outer, "controller", side_effect=self.stage):
            api.run(self.args)
            with self.assertRaises(FileExistsError):
                api.run(self.args)
        self.assertEqual(len(self.calls), 9)
        self.args.manifest_sha256 = "f" * 64
        with self.assertRaisesRegex(ValueError, "drift"):
            api.run(self.args)

    def test_unreleased_stage_does_not_advance(self):
        def unreleased(*args, **kwargs):
            result = self.stage(*args, **kwargs)
            return {**result, "gpu_released": False}
        with patch.object(api.outer, "controller", side_effect=unreleased):
            with self.assertRaisesRegex(ValueError, "failed stage"):
                api.run(self.args)
        self.assertEqual(len(self.calls), 1)

    def test_repeated_seed_labels_gpu_or_extra_entries_refused(self):
        for change in ("seed", "gpu", "extra", "budget"):
            manifest = copy.deepcopy(self.manifest)
            if change in ("seed", "gpu"):
                manifest["entries"][1][change] = manifest["entries"][0][change]
            elif change == "extra":
                manifest["entries"].append(manifest["entries"][0])
            else:
                manifest["budget"]["fits"] = 4
            with self.subTest(change=change), self.assertRaises(ValueError):
                api.validate_campaign(manifest, self.root)

    def test_repinned_wrong_learner_input_and_gpu_binding_refused(self):
        path = self.root / "seed1/fit_inputs.json"
        original = api.outer.read(path)
        for key, value in (("learner_seed", 0), ("gpu_uuid", "GPU-0")):
            path.write_bytes(api.fit.prefix.canonical({**original, key: value}))
            manifest = copy.deepcopy(self.manifest)
            manifest["entries"][1]["fit_inputs"] = api.pin(path)
            with self.subTest(key=key), self.assertRaises(ValueError):
                api.validate_campaign(manifest, self.root)


if __name__ == "__main__":
    unittest.main()
