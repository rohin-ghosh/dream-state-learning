import copy
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import p7_idle_handoff as subject


class HandoffTests(unittest.TestCase):
    def identity(self):
        return dict(pid=subject.OLD_PID, start_ticks=subject.OLD_START, argv=subject.OLD_ARGV)

    def test_exact_pid_start_argv_and_boot_are_required(self):
        subject.verify_identity(self.identity(), subject.BOOT_ID)
        for changes in (dict(pid=1), dict(start_ticks="0"), dict(argv=["python3", "native_life.py"])):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                subject.verify_identity(dict(self.identity(), **changes), subject.BOOT_ID)
        with self.assertRaises(ValueError):
            subject.verify_identity(self.identity(), "different-boot")

    def test_deadline_without_proven_idle_does_not_signal(self):
        with patch.object(subject.time, "monotonic", return_value=100), patch.object(subject.signal, "pidfd_send_signal") as send:
            result = subject.wait_fresh_idle(99, [])
        self.assertEqual(result, (None, None))
        send.assert_not_called()

    def test_busy_then_fresh_idle_is_required(self):
        samples = [dict(idle=True), dict(idle=False), dict(idle=True), dict(idle=True), dict(idle=True)]
        with patch.object(subject, "observe", side_effect=samples) as observe, patch.object(subject.time, "sleep"), patch.object(subject.time, "monotonic", return_value=0), patch.object(subject, "snapshot_files", return_value=[]), patch.object(subject, "lock_owners", return_value=[subject.OLD_PID, subject.OLD_PID]):
            sample, files = subject.wait_fresh_idle(10, [])
        self.assertTrue(sample["idle"])
        self.assertEqual(files, [])
        self.assertEqual(observe.call_count, 5)

    def test_bounded_wrapper_compacts_only_polls_and_keeps_full_turns(self):
        path = subject.OWNER / "p7_bounded.py"
        specification = importlib.util.spec_from_file_location("approved_bounded_p7_test", path)
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)
        original = dict(reply=dict(record_index=9, record_sha256="a" * 64, text="full child text"),
                        publications=[dict(message="actual parent turn")], reference=dict(next_index=10))
        unchanged = copy.deepcopy(original)
        recorded = []
        base = SimpleNamespace(write=lambda path, document: recorded.append((path, document)))

        def serve():
            for filename in ("POLL_1.json", "SOURCE.json", "RESPONSE.json", "NEXT.json"):
                base.write(Path(filename), original)

        replacement = SimpleNamespace(original=SimpleNamespace(base=base), serve=serve)
        with patch.dict(sys.modules, {"p7_restore": replacement}):
            module.main()
        self.assertEqual(original, unchanged)
        self.assertEqual(recorded[0][1]["schema"], "P7_POLL_RECEIPT_V1")
        self.assertNotIn("full child text", str(recorded[0][1]))
        self.assertEqual(len(recorded[0][1]["observation_sha256"]), 64)
        for unused, document in recorded[1:]:
            self.assertIs(document, original)


if __name__ == "__main__":
    unittest.main()
