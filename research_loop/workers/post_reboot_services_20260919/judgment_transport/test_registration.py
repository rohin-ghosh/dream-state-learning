import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import supervisor


class TransportRegistrationTests(unittest.TestCase):
    def setUp(self):
        self.entry = json.loads((HERE / "node3-judgment-transport.candidate.json").read_bytes())
        clock = patch.object(supervisor.time, "time", return_value=1790272700)
        clock.start()
        self.addCleanup(clock.stop)

    def test_existing_source_specific_deadline_and_owner_source_are_bound(self):
        checked = supervisor.validate(self.entry)
        self.assertEqual(checked["until_unix"], 1790272760)
        caps = json.loads(supervisor.repository_path(checked["lease_evidence"]["path"]).read_bytes())
        self.assertEqual(caps[1]["group"], "node3")
        self.assertEqual(caps[1]["actual_deadline"], checked["until_unix"])
        self.assertEqual(checked["argv"][-1], str(supervisor.repository_path(checked["entrypoint"])))

    def test_even_one_second_source_deadline_extension_is_rejected(self):
        entry = copy.deepcopy(self.entry)
        entry["until_unix"] += 1
        with self.assertRaisesRegex(ValueError, "cannot_extend_source_lease"):
            supervisor.validate(entry)

    def test_exact_existing_controller_is_adopted_without_spawn(self):
        manager = supervisor.Supervisor()
        matches = [dict(pid=425470, start_ticks="939654")]
        with patch.object(supervisor, "matching_processes", return_value=matches), \
             patch.object(supervisor, "record_event"), \
             patch.object(supervisor.subprocess, "Popen") as spawn:
            status = manager.tick([self.entry])
        spawn.assert_not_called()
        self.assertEqual(status[0]["status"], "RUNNING_ADOPTED_NO_SIGNALS")

    def test_inherited_component_lock_prevents_duplicate_if_controller_absent(self):
        manager = supervisor.Supervisor()
        with patch.object(supervisor, "matching_processes", return_value=[]), \
             patch.object(supervisor, "record_event"), \
             patch.object(supervisor, "lock_busy", return_value=True), \
             patch.object(supervisor.subprocess, "Popen") as spawn:
            status = manager.tick([self.entry])
        spawn.assert_not_called()
        self.assertEqual(status[0]["status"], "EXISTING_SINGLETON_LOCK_HELD_NO_LAUNCH")

    def test_readiness_does_not_assert_judging_or_gpu_dispatch(self):
        self.assertTrue(self.entry["readiness_is_not_judgment_success"])
        self.assertFalse(self.entry["historical_replay_allowed"])
        self.assertFalse(self.entry["synthetic_probe_allowed"])
        self.assertFalse(self.entry["child_native"])
        self.assertIn("NOT_MODEL_PARENT_OR_GPU_DISPATCHER", self.entry["service_role"])
        self.assertNotIn("env", self.entry)
        self.assertNotIn("environment", self.entry)


if __name__ == "__main__":
    unittest.main()
