import unittest
from copy import deepcopy
from unittest.mock import patch

from gpu import orch_math_feedback_uptake_r118_second_exit as repair


class SecondExitTests(unittest.TestCase):
    def fixture(self):
        guard = dict(pid=10, start_ticks='20', boot_id='boot')
        child = dict(pid=11, start_ticks='21', boot_id='boot')
        return dict(guard=guard, launch=dict(guardian=deepcopy(guard), identity=child),
            terminal=dict(status='FAILED', native_alive=False, no_retry=True, identity=deepcopy(child)),
            failure=dict(session_sha256=repair.FAILED_SESSION, retry_allowed=False),
            log='ValueError: failed_or_expired_session_must_not_start\n', absent=True,
            counters=dict(native=274, parent=60), expected=dict(native=274, parent=60))

    def test_actual_prebootstrap_exit_accepted(self):
        repair.validate_exit(**self.fixture())

    def test_live_actor_rejected(self):
        values = self.fixture()
        values['absent'] = False
        with self.assertRaisesRegex(ValueError, 'actors_absent'):
            repair.validate_exit(**values)

    def test_real_charge_change_rejected(self):
        values = self.fixture()
        values['counters']['native'] += 1
        with self.assertRaisesRegex(ValueError, 'charges'):
            repair.validate_exit(**values)

    def test_pid_reuse_and_different_child_rejected(self):
        for field in ('start_ticks', 'boot_id', 'pid'):
            values = self.fixture()
            values['launch']['guardian'][field] = 'different'
            with self.subTest(field=field), self.assertRaises(ValueError):
                repair.validate_exit(**values)
        values = self.fixture()
        values['terminal']['identity']['start_ticks'] = 'different'
        with self.assertRaises(ValueError):
            repair.validate_exit(**values)

    def test_wrong_failure_or_model_error_rejected(self):
        for key, value in [('failure', dict(session_sha256='other', retry_allowed=False)),
                ('log', 'ValueError: model_load_failed')]:
            values = self.fixture()
            values[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                repair.validate_exit(**values)

    def test_failed_session_rejected_without_dispatch(self):
        with patch.dict(repair.os.environ, R118_PARALLEL_SESSION_SHA256=repair.FAILED_SESSION), \
                patch.object(repair, 'original_session_open') as original:
            with self.assertRaisesRegex(ValueError, 'second_failed_session'):
                repair.session_open()
            original.assert_not_called()


if __name__ == '__main__':
    unittest.main()
