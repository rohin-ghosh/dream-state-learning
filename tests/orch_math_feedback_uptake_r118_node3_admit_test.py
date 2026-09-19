import time
import unittest
from unittest.mock import Mock

from gpu import orch_math_feedback_uptake_r118_node3_admit as admit


class AdmissionTests(unittest.TestCase):
    def test_no_filter_complete_rescans(self):
        rejected = dict(clear=False, scanner_euid=0, blocking_reasons=['process_identity_drift:3082'])
        accepted = dict(clear=True, scanner_euid=0, blocking_reasons=[])
        scan = Mock(side_effect=[rejected, accepted])
        write = Mock()
        self.assertEqual(admit.scan_until_clear(scan, write, time.time()+5, pause=lambda unused: None), accepted)
        self.assertEqual(write.call_args_list[0].args, (0, rejected))
        self.assertEqual(scan.call_count, 2)

    def test_nonroot_never_admitted(self):
        scan = Mock(return_value=dict(clear=True, scanner_euid=2524, blocking_reasons=[]))
        with self.assertRaisesRegex(ValueError, 'no_waiver'):
            admit.scan_until_clear(scan, Mock(), time.time()+5, pause=lambda unused: None)
        self.assertEqual(scan.call_count, 60)

    def test_blocking_owner_never_admitted(self):
        scan = Mock(return_value=dict(clear=True, scanner_euid=0, blocking_reasons=['actual_owner']))
        with self.assertRaisesRegex(ValueError, 'no_waiver'):
            admit.scan_until_clear(scan, Mock(), time.time()+5, pause=lambda unused: None)

    def test_deadline_no_scan(self):
        scan = Mock()
        with self.assertRaises(TimeoutError):
            admit.scan_until_clear(scan, Mock(), time.time()-1)
        scan.assert_not_called()


if __name__ == '__main__':
    unittest.main()
