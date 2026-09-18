from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_math_pipeline_l2_lane as lane


class LaneTest(unittest.TestCase):
    def test_completed_c1_not_in_frozen_continuation(self):
        self.assertEqual(lane.stages(2, 'experience'), [(2, 'experience'), (2, 'readout'), (3, 'experience'), (3, 'readout')])

    def test_owner_rejection_waits_for_new_full_clear_scan(self):
        blocked = dict(clear=False, scanner_euid=0, blocking_reasons=['open_device_pid:123'])
        cleared = dict(clear=True, scanner_euid=0, blocking_reasons=[])
        with tempfile.TemporaryDirectory() as directory, patch.object(lane.common, 'scan', side_effect=[blocked, cleared]) as scan, patch.object(lane.time, 'sleep'):
            self.assertEqual(lane.admit(Path(directory), 'FROZEN', 2, 'experience', lane.time.time() + 60), cleared)
            self.assertEqual(scan.call_count, 2)
            self.assertEqual(len(list(Path(directory).glob('LANE_ADMISSION*'))), 2)

    def test_no_acceptance_when_owner_remains_or_scan_not_privileged(self):
        for report in [dict(clear=False, scanner_euid=0, blocking_reasons=['open_device_pid:123']),
            dict(clear=True, scanner_euid=1000, blocking_reasons=[])]:
            with tempfile.TemporaryDirectory() as directory, patch.object(lane.common, 'scan', return_value=report), patch.object(lane.time, 'sleep'), patch.object(lane.time, 'time', side_effect=[0, 0, 181]):
                with self.assertRaises(TimeoutError):
                    lane.admit(Path(directory), 'FROZEN', 2, 'experience', 500)


if __name__ == '__main__':
    unittest.main()
