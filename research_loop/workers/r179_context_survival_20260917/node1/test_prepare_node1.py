"""CPU-only proposal checks; no process, provider, model, or journal operations."""

from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest


SOURCE = Path(__file__).with_name("prepare_node1.py")
SPEC = importlib.util.spec_from_file_location("r179_node1_preparation", SOURCE)
PREPARE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PREPARE)


class PreparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.documents, cls.references = PREPARE.load_inputs()

    def setUp(self):
        self.documents = deepcopy(type(self).documents)

    def build(self):
        return PREPARE.build_proposal(self.documents, self.references)

    def test_exact_six_and_closed_execution_gates(self):
        result = self.build()
        self.assertEqual([life["physical"] for life in result["lives"]], list(range(2, 8)))
        for field in ("execution_authorized", "actor_pause_allowed", "rollout_ready",
                      "full_plan_bytes_loaded", "full_source_closure_verified"):
            self.assertIs(result[field], False)
        for life in result["lives"]:
            self.assertIsNone(life["saved_boundary"])
            self.assertIsNone(life["receiving_cpu_proof"])
            self.assertNotIn("frozen", life["life_root"])

    def test_recovery_guard_paths_are_not_inferred_from_plan(self):
        lives = {life["physical"]: life for life in self.build()["lives"]}
        self.assertIn("/lane6/readmission1/control/", lives[6]["original_guard"]["path"])
        self.assertIn("/orch_r147_a1007_recovery_", lives[7]["original_guard"]["path"])
        self.assertIn("/lane7/control/", lives[7]["original_plan"]["path"])

    def test_pid_reuse_fails_closed(self):
        self.documents["console"]["rows"][0]["start_ticks"] = "1"
        with self.assertRaisesRegex(ValueError, "cross_receipt_actor_identity"):
            self.build()

    def test_missing_life_fails_closed(self):
        self.documents["console"]["rows"].pop()
        with self.assertRaisesRegex(ValueError, "exact_six_learning_lives_no_controls"):
            self.build()

    def test_duplicate_life_fails_closed(self):
        self.documents["console"]["rows"].append(deepcopy(self.documents["console"]["rows"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate_life_root"):
            self.build()

    def test_frozen_control_cannot_enter_proposal(self):
        control = next(row for row in self.documents["roster"]["rows"]
                       if row["node"] == "a100" and "frozen" in row["life_root"])
        control["training"]["training_enabled"] = True
        with self.assertRaisesRegex(ValueError, "exact_six_learning_lives_no_controls"):
            self.build()

    def test_changed_plan_reference_fails_closed(self):
        current = next(node for node in self.documents["census"]["nodes"] if node["node"] == "a100")
        current["rows"][0]["plan_ref"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "exact_current_plan_reference"):
            self.build()

    def test_changed_native_source_fails_closed(self):
        self.documents["console"]["rows"][0]["source_files"][PREPARE.SOURCE_FILES["native"]]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "native_source_cross_check"):
            self.build()

    def test_proposal_does_not_mutate_inputs(self):
        original = deepcopy(self.documents)
        self.build()
        self.assertEqual(self.documents, original)


if __name__ == "__main__":
    unittest.main()
