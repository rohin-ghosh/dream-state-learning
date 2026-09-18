from pathlib import Path
import sys
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import receiving_parent as receiver
import receiving_prepare


class ReachedFreshReceiverCheck(Exception):
    pass


class ReceivingPreparationTests(unittest.TestCase):
    def check_status(self, status, expected):
        handoff = dict(status='ACTUAL_RECEIVING_LOADED', source_original_physical=0,
            target_node='node2', physical_receiving_root='/receiving/root', source_root='/receiving/source',
            parent_rebind=dict(ssh_wrapper='gpu/ovx_ssh.sh'), loaded={}, native={}, guard_sha256='guard',
            rohin_console_source_sha256='console', hard_end_unix=time.time() + 60)
        with patch.object(receiver.base, 'read', side_effect=[handoff, dict(status=status), {}]), \
                patch.object(receiver.base, 'reference', return_value={}), \
                patch.object(receiver, 'verify', side_effect=ReachedFreshReceiverCheck):
            with self.assertRaises(expected):
                receiving_prepare.prepare(0, '/handoff')

    def test_exact_stopped_status_reaches_fresh_identity_check(self):
        self.check_status('SETTLED_ORIGINAL_PARENT_STOPPED', ReachedFreshReceiverCheck)

    def test_documented_already_absent_status_reaches_fresh_identity_check(self):
        self.check_status('ORIGINAL_PARENT_ALREADY_ABSENT', ReachedFreshReceiverCheck)

    def test_unknown_old_parent_state_is_rejected(self):
        self.check_status('WAITER_EXITED', ValueError)


if __name__ == '__main__':
    unittest.main()
