import unittest
from unittest.mock import patch
from pathlib import Path
import sys

from gpu import orch_rich_hot_a100_minor_scan
sys.modules['orch_rich_hot_a100_minor_scan'] = orch_rich_hot_a100_minor_scan
from gpu import orch_rich_hot_a100_fill as fill


class FillTests(unittest.TestCase):
    def test_only_priority_lanes(self):
        self.assertEqual(fill.INDICES, (2, 3, 7))

    def test_original_budget_not_reset(self):
        lifetime = dict(native_deadline_unix=1000, hard_deadline_unix=1300, started_unix=1)
        with patch.object(fill.existing, 'read', return_value=lifetime):
            self.assertIs(fill.inherited_lifetime(Path('/tmp'), 500), lifetime)
            with self.assertRaises(ValueError):
                fill.inherited_lifetime(Path('/tmp'), 1000)

    def test_stop_does_not_signal_exited_process(self):
        from unittest.mock import Mock
        child = Mock()
        child.poll.return_value = 0
        with patch.object(fill.os, 'pidfd_open') as opened:
            fill.request_stop(child, {})
            opened.assert_not_called()

    def test_uuid_not_enumeration_index_selects_device(self):
        documents = ['GPU UUID: GPU-first\nDevice Minor: 3', 'GPU UUID: GPU-second\nDevice Minor: 0']
        self.assertEqual(orch_rich_hot_a100_minor_scan.minor_from_documents(documents, 'GPU-second'), 0)
        self.assertEqual(orch_rich_hot_a100_minor_scan.minor_from_documents(documents, 'GPU-first'), 3)

    def test_unknown_or_duplicate_kernel_uuid_rejected(self):
        for documents in ([], ['GPU UUID: GPU-first\nDevice Minor: 1'] * 2):
            with self.assertRaises(ValueError):
                orch_rich_hot_a100_minor_scan.minor_from_documents(documents, 'GPU-first')


if __name__ == '__main__':
    unittest.main()
