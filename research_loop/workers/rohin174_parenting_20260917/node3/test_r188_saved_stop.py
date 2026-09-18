import unittest
from pathlib import Path
from unittest.mock import patch

import r188_saved_stop as stop


class SavedStopTests(unittest.TestCase):
    def test_update_never_a_stop_boundary(self):
        self.assertFalse(stop.may_capture(stop.NOT_BEFORE + 1, dict(kind='UPDATE')))

    def test_before_window_does_not_stop(self):
        self.assertFalse(stop.may_capture(stop.NOT_BEFORE - 1, dict(kind='SLEEP_COMPLETE')))

    def test_complete_inside_window(self):
        self.assertTrue(stop.may_capture(stop.NOT_BEFORE, dict(kind='SLEEP_COMPLETE')))

    def test_late_capture_rejected(self):
        self.assertFalse(stop.may_capture(stop.QUIET_END, dict(kind='SLEEP_COMPLETE')))

    def test_zombie_child_not_active(self):
        with patch.object(Path, 'read_text', side_effect=['33', '33 (done) Z 1 2']):
            self.assertEqual(stop.present_children(11), [])


if __name__ == '__main__':
    unittest.main()
