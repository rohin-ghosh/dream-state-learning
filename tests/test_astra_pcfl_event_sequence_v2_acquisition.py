"""Nonnative CPU fixtures only: no native outcomes, GPU run, or promotion."""

import copy
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gpu import astra_pcfl_event_sequence_v2_acquisition as api
import test_astra_pcfl_event_sequence_v2_readout as fixtures


class AcquisitionTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.ReadoutV2Tests("test_cold_c0_seed_bound_no_write_exact_roster")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.harness = self.fixture.harness
        self.material = self.fixture.material
        self.inputs = copy.deepcopy(self.fixture.inputs)
        self.roots = {}
        self.request = {"schema": api.SCHEMA + "/request"}

    def write(self, path, value):
        Path(path).write_bytes(api.prefix.canonical(value) + b"\n")

    def state(self, state, correct=(), overrides=None, finishes=None):
        root = self.harness.root / ("outer_" + state)
        root.mkdir()
        inputs = copy.deepcopy(self.inputs)
        self.harness.texts = [record["target"] if index in correct else "MISS"
                              for index, record in enumerate(self.material["spec"]["records"] * 2)]
        for index, text in (overrides or {}).items():
            self.harness.texts[index] = text
        self.harness.finishes = ["stop"] * 16
        for index, finish in (finishes or {}).items():
            self.harness.finishes[index] = finish
        if state == "A200":
            self.fit_root = self.fixture.completed_fit()
            inputs["fit_receipt"] = self.fixture.inputs["fit_receipt"]
        pin = self.harness.store(state + "_inputs.json", inputs)
        completed = fixtures.api.run_state(pin["path"], pin["sha256"], root / "readout", 1000,
            state=state, tokenizer_factory=lambda config: self.harness.tokenizer,
            actor_factory=self.harness.actor, environment_reader=lambda: self.harness.env,
            clock=self.harness.clock)
        self.assertEqual(completed["kind"], "INJECTED_CPU_TEST")
        identity = {"pid": os.getpid(), "uid": os.getuid(), "boot_id": "NONNATIVE_CPU_FIXTURE",
                    "pgid": os.getpid(), "sid": os.getpid()}
        self.write(root / "inputs.input.json", inputs)
        self.write(root / "allocation.input.json", {"uid": identity["uid"], "boot_id": identity["boot_id"]})
        self.write(root / "binding.json", {"argv": ["NONNATIVE", "--output", str(root / "readout")],
            "deadline_monotonic": 1060, "worker_deadline_monotonic": 1000})
        self.write(root / "context.json", {"schema": api.OUTER_SCHEMA, "stage": "readout", "state": state,
            "inputs": pin, "outer_source_sha256": "a" * 64, "entry_monotonic": 0})
        self.write(root / "worker_start.json", {"identity": identity})
        self.write(root / "worker_exit.json", {"identity": identity, "pid": identity["pid"], "returncode": 0, "signal": None})
        observations = {"worker_wait": 0, "worker_release": {"identity": identity, "owned_group_released": True}}
        for when in ("pre", "post"):
            observations.update({when + "_queue": {"matched": True},
                when + "_gpu": {"empty": True, "gpu_uuid": inputs["gpu_uuid"]},
                when + "_cvd": {"clear": True, "owners": [], "unresolved": []}})
        for name, value in observations.items():
            self.write(root / (name + ".json"), {"started_monotonic": 1, "ended_monotonic": 2, "value": value})
        self.write(root / "collection.json", api.prefix.seal({"schema": api.OUTER_SCHEMA + "/collection",
            "stage": "readout", "state": state, "status": "COMPLETED", "errors": [], "returncode": 0,
            "gpu_released": True, "retries": 0, "automatic_promotion": False, "full_contract_released": False,
            "original_status": "FORMATION_FAILED", "inputs": pin,
            "allocation_file_sha256": api.file_hash(root / "allocation.input.json"), "outer_source_sha256": "a" * 64,
            "worker_identity": identity, "observations": observations, "elapsed_seconds": 100,
            "files": {}, "stage_inventory": {}, "completed_sha256": completed["sha256"]}))
        self.roots[state] = root
        self.refresh(state)
        return root

    def refresh(self, state):
        root = self.roots[state]
        completed = api.read(root / "readout/completed.json")
        completed.pop("sha256")
        completed["files"] = {name: entry["sha256"] for name, entry in api.inventory(root / "readout").items()
                              if name != "completed.json"}
        completed = api.prefix.seal(completed)
        self.write(root / "readout/completed.json", completed)
        self.write(root / "readout_completed.json", completed)
        collection = api.read(root / "collection.json")
        collection.pop("sha256")
        collection.update(completed_sha256=completed["sha256"], stage_inventory=api.inventory(root / "readout"),
            files={name: entry for name, entry in api.inventory(root).items() if name != "collection.json"})
        self.write(root / "collection.json", api.prefix.seal(collection))
        key = "no_write_collection" if state == "NO_WRITE" else "a200_collection"
        self.request[key] = self.harness.pin(root / "collection.json")

    def pair(self, correct=range(8, 12), **kwargs):
        self.state("NO_WRITE")
        return self.state("A200", correct, **kwargs)

    def validate(self):
        return api.validate_collections(self.request, self.material, self.inputs, expected_kind="INJECTED_CPU_TEST")

    def test_bound_positive_cpu_receipt_is_not_native_or_promotion(self):
        self.pair()
        pin = self.harness.store("acquisition.json", self.request)
        before = {state: api.inventory(root) for state, root in self.roots.items()}
        with patch.object(api.reader, "ReadoutActor", side_effect=AssertionError("no model launch")), \
                patch.object(api.sequence.trainer, "run_training", side_effect=AssertionError("no training")):
            result = api.validate(pin, self.material, self.inputs, expected_kind="INJECTED_CPU_TEST")
        api.prefix.unseal(result, result["sha256"])
        self.assertTrue(result["observed_gate"])
        self.assertEqual(result["kind"], "INJECTED_CPU_TEST")
        self.assertEqual(result["acquisition_pin"], pin)
        self.assertEqual(result["request"], self.request)
        self.assertEqual(result["a200_fit_receipt"], self.fixture.inputs["fit_receipt"])
        self.assertFalse(result["automatic_promotion"])
        self.assertFalse(result["full_contract_released"])
        self.assertEqual(result["learner_seed"], 1)
        for state in result["states"].values():
            for banks in state["panels"].values():
                for panel in banks.values():
                    self.assertEqual(panel["denominator"], 4)
                    self.assertEqual(len(panel["strict_stop"]), 4)
        self.assertEqual(before, {state: api.inventory(root) for state, root in self.roots.items()})
        with self.assertRaises(ValueError):
            api.validate(pin, self.material, self.inputs)

    def test_w0_success_cannot_substitute_for_w8(self):
        self.pair(correct=range(4))
        result = self.validate()
        self.assertFalse(result["observed_gate"])
        self.assertEqual(result["states"]["A200"]["panels"]["W0"]["A"]["correct"], 4)

    def test_format_strict_stop_no_repair_and_denominators(self):
        records = self.material["spec"]["records"]
        self.pair(overrides={8: records[0]["target"].rstrip("\n"),
                             9: "explanation\n" + records[1]["target"], 10: records[2]["target"]},
                  finishes={10: "length"})
        result = self.validate()
        self.assertFalse(result["observed_gate"])
        self.assertEqual(result["states"]["A200"]["panels"]["W8"]["A"]["strict_stop"], [False, False, False, True])
        self.assertEqual(result["states"]["A200"]["truncated"], 1)

    def test_b_leakage_fails_gate(self):
        self.pair(correct=range(8, 13))
        self.assertFalse(self.validate()["observed_gate"])

    def test_c0_success_fails_gate(self):
        self.state("NO_WRITE", correct=(8,))
        self.state("A200", correct=range(8, 12))
        self.assertFalse(self.validate()["observed_gate"])

    def test_closed_requests_missing_and_boolean_bypasses_rejected(self):
        for request in (True, {}, {"schema": api.SCHEMA + "/request", "callerBoolean": True},
                        {"schema": api.SCHEMA + "/request", "no_write_collection": True, "a200_collection": True}):
            with self.subTest(request=request), self.assertRaises(ValueError):
                api.validate_collections(request, self.material, self.inputs)
        with self.assertRaises(ValueError):
            api.validate(True, self.material, self.inputs)

    def test_changed_artifact_and_missing_capture_rejected(self):
        root = self.pair()
        path = root / "readout/actor/call_0008.raw.json"
        path.write_bytes(path.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "inventory"):
            self.validate()
        path.unlink()
        with self.assertRaises(ValueError):
            self.validate()

    def test_resealed_score_lie_rejected(self):
        root = self.pair()
        scores = api.read(root / "readout/scores.json")
        scores["results"][8]["strict_stop"] = False
        self.write(root / "readout/scores.json", scores)
        self.refresh("A200")
        with self.assertRaisesRegex(ValueError, "score"):
            self.validate()

    def test_resealed_raw_and_request_join_drift_rejected(self):
        root = self.pair()
        for suffix, change in (("raw", lambda value: value["raw"].update(text="different")),
                               ("request", lambda value: value.update(request={"id": "wrong"})),
                               ("render", lambda value: value.update(route={"arm": "wrong"}))):
            path = root / f"readout/actor/call_0008.{suffix}.json"
            original = api.read(path)
            modified = copy.deepcopy(original)
            change(modified)
            self.write(path, modified)
            self.refresh("A200")
            with self.subTest(suffix=suffix), self.assertRaises(ValueError):
                self.validate()
            self.write(path, original)
            self.refresh("A200")

    def test_failed_release_v1_state_and_seed_rejected(self):
        root = self.pair()
        for filename, changes in (("collection.json", {"gpu_released": False}),
                                   ("collection.json", {"errors": ["failed"]}),
                                   ("collection.json", {"schema": "pcfl.event_sequence.outer.v1/collection"}),
                                   ("collection.json", {"state": "S_A40"}),
                                   ("readout/completed.json", {"learner_seed": 2}),
                                   ("readout/completed.json", {"import_sha256": "0" * 64}),
                                   ("readout/completed.json", {"status": "FAILED"})):
            path = root / filename
            original = api.read(path)
            self.write(path, {**original, **changes})
            self.refresh("A200")
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.validate()
            self.write(path, original)
            self.refresh("A200")

    def test_changed_fit_artifact_rejected(self):
        self.pair()
        path = self.fit_root / "checkpoint/adapter_model.safetensors"
        path.write_bytes(b"changed checkpoint")
        with self.assertRaisesRegex(ValueError, "fit file drift"):
            self.validate()

    def test_expected_model_and_material_pins_rejected(self):
        self.pair()
        for name in ("material", "model_binding", "base_state_receipt"):
            inputs = copy.deepcopy(self.inputs)
            inputs[name]["sha256"] = "0" * 64
            with self.subTest(name=name), self.assertRaises(ValueError):
                api.validate_collections(self.request, self.material, inputs, expected_kind="INJECTED_CPU_TEST")

    def test_import_has_no_v2_worker_cycle(self):
        command = "from gpu import astra_pcfl_event_sequence_v2_acquisition; import sys; assert not any('gpu.astra_pcfl_event_sequence_v2_' + name in sys.modules for name in ('fit', 'outer', 'readout'))"
        subprocess.run([sys.executable, "-c", command], check=True, cwd=Path(__file__).resolve().parents[1])


if __name__ == "__main__":
    unittest.main()
