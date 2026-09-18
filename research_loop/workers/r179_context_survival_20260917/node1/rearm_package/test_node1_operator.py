"""Bounded CPU-only tests for the A100-specific operator safety additions."""

import ast
import hashlib
import importlib.util
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("r179_node1_operator", HERE / "node1_operator.py")
OPERATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(OPERATOR)


class OperatorTests(unittest.TestCase):
    def test_exact_base_machinery_pin(self):
        self.assertEqual(OPERATOR.legacy().GUARD, "gpu.orch_r125_continual_guard")

    def test_source_cap_is_checked_before_content_hashing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / "large.py").write_bytes(b"12345")
            with patch.object(OPERATOR, "SOURCE_CAP", 4), patch.object(OPERATOR, "sha") as hashing:
                with self.assertRaisesRegex(ValueError, "source_byte_reservation"):
                    OPERATOR.source_inventory(root)
                hashing.assert_not_called()

    def test_source_links_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / "bad.py").symlink_to("/etc/passwd")
            with self.assertRaisesRegex(ValueError, "no_source_links_or_special_files"):
                OPERATOR.source_inventory(root)

    def test_noncode_inventory_does_not_read_contents(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / "opaque.json").write_text("not read by inventory")
            with patch.object(OPERATOR, "sha", side_effect=AssertionError("content read")):
                inventory = OPERATOR.source_inventory(root)
            self.assertNotIn("sha256", inventory["opaque.json"])

    def test_source_copy_preserves_opaque_bytes_without_opening(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            original, successor, package = root / "original", root / "successor", root / "package"
            (original / "gpu").mkdir(parents=True)
            package.mkdir()
            (original / OPERATOR.NATIVE).write_text("old = True\n")
            (original / "other.py").write_text("unchanged = True\n")
            (original / "opaque.json").write_text("opaque fixture")
            (package / "policy.py").write_text("policy = True\n")
            policy_hash = hashlib.sha256((package / "policy.py").read_bytes()).hexdigest()
            before = OPERATOR.source_inventory(original)
            with patch.object(OPERATOR, "HERE", package), patch.object(OPERATOR, "POLICY_SHA", policy_hash):
                OPERATOR.copy_source(original, successor, before, "patched = True\n")
                after = OPERATOR.source_inventory(successor)
                OPERATOR.verify_source_copy(original, successor, before, after)
            self.assertEqual((original / "opaque.json").stat().st_ino, (successor / "opaque.json").stat().st_ino)
            self.assertNotEqual((original / OPERATOR.NATIVE).stat().st_ino, (successor / OPERATOR.NATIVE).stat().st_ino)
            for path in sorted(successor.rglob("*"), reverse=True):
                if path.is_dir():
                    path.chmod(0o755)
            successor.chmod(0o755)

    def test_noop_lane_cannot_enter_handoff(self):
        with patch.object(OPERATOR, "authorize"):
            with self.assertRaisesRegex(ValueError, "five_noncompliant_learners_bounded_wait"):
                OPERATOR.handoff(7, 1)

    def test_bound_wait_rejects_excessive_duration(self):
        with patch.object(OPERATOR, "authorize"):
            with self.assertRaisesRegex(ValueError, "five_noncompliant_learners_bounded_wait"):
                OPERATOR.handoff(2, 5401)

    def test_watchdog_resumes_exact_actor_on_parent_loss(self):
        with patch.object(OPERATOR.select, "select", return_value=([], [], [])), \
             patch.object(OPERATOR.signal, "pidfd_send_signal") as send:
            OPERATOR.watchdog(77, 78, 1)
        send.assert_called_once_with(77, OPERATOR.signal.SIGCONT)

    def test_watchdog_does_not_signal_after_normal_completion(self):
        with patch.object(OPERATOR.select, "select", return_value=([78], [], [])), \
             patch.object(OPERATOR.os, "read", return_value=b"D"), \
             patch.object(OPERATOR.signal, "pidfd_send_signal") as send:
            OPERATOR.watchdog(77, 78, 1)
        send.assert_not_called()

    def test_preservation_budget_rejects_before_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / "fixture").write_bytes(b"12345")
            with self.assertRaisesRegex(ValueError, "precharged_preservation_cap"):
                OPERATOR.reserve_tree(root, 4)

    def test_original_guard_admission_calls_remain_present(self):
        tree = ast.parse((HERE / "node1_operator.py").read_text())
        methods = {node.func.attr for node in ast.walk(tree)
                   if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
        self.assertTrue({"originals", "check_scope", "process_pair", "actual_device",
                         "verify_resume_entrypoint", "saved_evidence", "verify_snapshot"} <= methods)
        self.assertNotIn("killpg", methods)

    def test_dispatch_without_started_request_cannot_pause_actor(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / "readouts").mkdir()
            (root / "readouts/sleep_000041_DISPATCH.json").write_text("{}")
            base = SimpleNamespace(identity=lambda process: self.fail("child not started"))
            native = SimpleNamespace(readout_name=lambda plan, cycle: "sleep_000041")
            self.assertIsNone(OPERATOR.readout_ready(base, dict(root=str(root)), {}, dict(cycle=41), {}, native))

    def test_readout_readiness_precedes_every_handoff_pause(self):
        tree = ast.parse((HERE / "node1_operator.py").read_text())
        handoff = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "handoff")
        ready = next(node for node in ast.walk(handoff) if isinstance(node, ast.Call)
                     and isinstance(node.func, ast.Name) and node.func.id == "readout_ready")
        pause = next(node for node in ast.walk(handoff) if isinstance(node, ast.Call)
                     and isinstance(node.func, ast.Attribute) and node.func.attr == "pause_exact")
        self.assertLess(ready.lineno, pause.lineno)
        checks = [node for node in ast.walk(handoff) if isinstance(node, ast.If)
                  and ast.unparse(node.test) == "ready is None"]
        self.assertEqual(len(checks), 1)
        self.assertTrue(any(isinstance(node, ast.Continue) for node in checks[0].body))


if __name__ == "__main__":
    unittest.main()
