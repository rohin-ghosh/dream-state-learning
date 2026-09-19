from copy import deepcopy
import unittest

from gpu import orch_math_feedback_uptake_r118_preinfer_stage as stage


class TimerCustodyTests(unittest.TestCase):
    def setUp(self):
        self.expected = dict(pid=123, uid=2524, start_ticks='100', boot_id='boot',
            command_sha256='cmd', cwd='/source', exe_device=1, exe_inode=2, ppid=456)

    def test_reparenting_only_preserves_authentic_identity(self):
        actual = dict(self.expected, ppid=1)
        stage.validate_timer_identity(self.expected, actual)
        self.assertEqual(self.expected['ppid'], 456)

    def test_reuse_exec_command_cwd_uid_never_accepted(self):
        for key in stage.IDENTITY_KEYS:
            with self.subTest(key=key):
                actual = deepcopy(self.expected)
                actual[key] = 'different'
                with self.assertRaises(ValueError):
                    stage.validate_timer_identity(self.expected, actual)

    def test_missing_identity_and_extra_changed_metadata_rejected(self):
        actual = deepcopy(self.expected)
        del actual['exe_inode']
        with self.assertRaises(ValueError):
            stage.validate_timer_identity(self.expected, actual)
        with self.assertRaises(ValueError):
            stage.validate_timer_identity(dict(self.expected, extra='pinned'), dict(self.expected,extra='changed'))

    def test_selector_never_a_retirement_target(self):
        identity = dict(self.expected, pid=1519259)
        with self.assertRaisesRegex(ValueError, 'selector'):
            stage.validate_timer_identity(identity, identity)


if __name__ == '__main__':
    unittest.main()
