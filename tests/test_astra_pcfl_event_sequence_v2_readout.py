"""Synthetic v2 cold-state custody and seed binding, never native evidence."""

from dataclasses import asdict
from pathlib import Path
import unittest
from unittest.mock import patch

from gpu import astra_pcfl_event_sequence_v2_readout as api
import test_astra_pcfl_event_sequence_readout as fixtures


class ReadoutV2Tests(unittest.TestCase):
    def setUp(self):
        self.harness = fixtures.ReadoutTests("test_c0_exact16_order_tokens_no_training_or_history")
        self.harness.setUp()
        self.addCleanup(self.harness.doCleanups)
        self.material = api.sequence.export_material(self.harness.imported, self.harness.imported["sha256"],
                                                     self.harness.tokenizer, learner_seed=1)
        self.inputs = dict(self.harness.inputs)
        self.inputs.update(schema=api.SCHEMA + "/inputs", source_files=api.source_files(),
                           material=self.harness.store("v2_material.json", self.material))
        self.count = 0

    def run_readout(self, state="NO_WRITE"):
        self.count += 1
        pin = self.harness.store(f"v2_inputs{self.count}.json", self.inputs)
        self.output = self.harness.root / f"v2_read{self.count}"
        return api.run_state(pin["path"], pin["sha256"], self.output, 1000, state=state,
                             tokenizer_factory=lambda config: self.harness.tokenizer,
                             actor_factory=self.harness.actor, environment_reader=lambda: self.harness.env,
                             clock=self.harness.clock)

    def completed_fit(self):
        root = self.harness.completed_fit()
        checkpoint = root / "checkpoint"
        config = api.sequence.training_config("A200", self.harness.model, learner_seed=1, device="cpu")
        phase = self.material["phases"]["A200"]
        def replace(path, value):
            path.write_bytes(api.prefix.canonical(value) + b"\n")
        replace(root / "config.json", asdict(config))
        replace(root / "corpus.json", phase["items"])
        manifest = api.read(checkpoint / "train_manifest.json")
        manifest.update(config=asdict(config), steps=200, micro_batches=200,
                        corpus={"file": "corpus.json", "sha256": api.fit.file_hash(root / "corpus.json"),
                                "n_items": 800, "n_encoded": 800, "n_skipped_no_target": 0},
                        tokens={"target": phase["supervised_tokens"], "total": phase["input_tokens"]})
        replace(checkpoint / "train_manifest.json", manifest)
        receipt = api.read(root / "completed.json")
        receipt.update(schema=api.fit.SCHEMA + "/completed", phase="A200", updates=200, learner_seed=1,
                       parent_phase=None, predecessor=None, warm_start=None,
                       material_sha256=self.inputs["material"]["sha256"], export_sha256=self.material["sha256"],
                       spec_sha256=self.material["spec"]["sha256"], items_sha256=phase["items_sha256"],
                       encoding_sha256=phase["encoding_sha256"],
                       files={name: value for name, value in api.v3._warm_inventory(root).items() if name != "completed.json"})
        receipt.pop("sha256")
        replace(root / "completed.json", api.prefix.seal(receipt))
        self.inputs["fit_receipt"] = self.harness.pin(root / "completed.json")
        return root

    def test_cold_c0_seed_bound_no_write_exact_roster(self):
        with patch.object(api.v3, "run_training", side_effect=AssertionError("no training")):
            result = self.run_readout()
        self.assertEqual((result["schema"], result["learner_seed"], result["calls"], result["updates"]),
                         (api.SCHEMA + "/completed", 1, 16, 0))
        self.assertEqual(result["kind"], "INJECTED_CPU_TEST")
        self.assertIsNone(result["route"]["lora_request"])
        self.assertEqual(result["panels"]["W8"]["A"]["correct"], 4)
        self.assertFalse(result["gpu_released"])
        self.assertFalse(result["automatic_promotion"])
        self.assertEqual(len(self.harness.sessions[0].calls), 16)

    def test_exact_a200_checkpoint_copied_not_changed(self):
        root = self.completed_fit()
        before = api.v3._warm_inventory(root)
        result = self.run_readout("A200")
        self.assertEqual(result["state"], "A200")
        self.assertEqual(result["learner_seed"], 1)
        adapter = Path(result["route"]["lora_request"]["path"])
        self.assertNotEqual(adapter, root / "checkpoint")
        for path in adapter.iterdir():
            self.assertEqual(path.read_bytes(), (root / "checkpoint" / path.name).read_bytes())
        self.assertEqual(api.v3._warm_inventory(root), before)

    def test_wrong_seed_receipt_rejected(self):
        root = self.completed_fit()
        receipt = api.read(root / "completed.json")
        receipt.pop("sha256")
        receipt["learner_seed"] = 0
        (root / "completed.json").write_bytes(api.prefix.canonical(api.prefix.seal(receipt)))
        self.inputs["fit_receipt"] = self.harness.pin(root / "completed.json")
        with self.assertRaisesRegex(ValueError, "learner seed"):
            self.run_readout("A200")
        self.assertFalse(self.harness.sessions)

    def test_wrong_saved_config_seed_rejected(self):
        root = self.completed_fit()
        config = api.read(root / "checkpoint/train_manifest.json")
        config["config"]["seed"] = 0
        (root / "checkpoint/train_manifest.json").write_bytes(api.prefix.canonical(config))
        receipt = api.read(root / "completed.json")
        receipt.pop("sha256")
        receipt["files"] = {name: value for name, value in api.v3._warm_inventory(root).items() if name != "completed.json"}
        (root / "completed.json").write_bytes(api.prefix.canonical(api.prefix.seal(receipt)))
        self.inputs["fit_receipt"] = self.harness.pin(root / "completed.json")
        with self.assertRaisesRegex(ValueError, "config differs"):
            self.run_readout("A200")

    def test_v1_state_and_completion_refused(self):
        with self.assertRaisesRegex(ValueError, "unknown v2"):
            self.run_readout("S_A")
        root = self.harness.completed_fit()
        self.inputs["fit_receipt"] = self.harness.pin(root / "completed.json")
        with self.assertRaisesRegex(ValueError, "matching v2"):
            self.run_readout("A200")

    def test_repinned_warm_start_cannot_claim_cold_a200(self):
        root = self.completed_fit()
        receipt = api.read(root / "completed.json")
        receipt.pop("sha256")
        receipt["warm_start"] = {"unexpected": True}
        (root / "completed.json").write_bytes(api.prefix.canonical(api.prefix.seal(receipt)))
        self.inputs["fit_receipt"] = self.harness.pin(root / "completed.json")
        with self.assertRaisesRegex(ValueError, "clean C0"):
            self.run_readout("A200")

    def test_repinned_substituted_corpus_cannot_claim_registered_phase(self):
        root = self.completed_fit()
        corpus = api.read(root / "corpus.json")
        corpus[0]["meta"]["record"] = 7
        (root / "corpus.json").write_bytes(api.prefix.canonical(corpus))
        manifest = api.read(root / "checkpoint/train_manifest.json")
        manifest["corpus"]["sha256"] = api.fit.file_hash(root / "corpus.json")
        (root / "checkpoint/train_manifest.json").write_bytes(api.prefix.canonical(manifest))
        receipt = api.read(root / "completed.json")
        receipt.pop("sha256")
        receipt["files"] = {name: value for name, value in api.v3._warm_inventory(root).items() if name != "completed.json"}
        (root / "completed.json").write_bytes(api.prefix.canonical(api.prefix.seal(receipt)))
        self.inputs["fit_receipt"] = self.harness.pin(root / "completed.json")
        with self.assertRaisesRegex(ValueError, "registered phase"):
            self.run_readout("A200")

    def test_raw_stop_and_newline_rules_unchanged(self):
        self.harness.texts[0] = self.harness.texts[0].rstrip("\n")
        self.harness.finishes[1] = "length"
        self.harness.texts[2] = "MISS"
        self.harness.texts[3] = "explanation\n" + self.harness.texts[3]
        result = self.run_readout()
        self.assertEqual(result["panels"]["W0"]["A"]["strict_stop"], [False] * 4)
        self.assertEqual(result["truncated"], 1)

    def test_capture_drift_blocks_completion(self):
        self.harness.mutate = lambda raw: {**raw, "prompt_token_ids": [42]}
        with self.assertRaises(ValueError):
            self.run_readout()
        self.assertFalse((self.output / "completed.json").exists())


if __name__ == "__main__":
    unittest.main()
