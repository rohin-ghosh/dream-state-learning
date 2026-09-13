import contextlib
import importlib.util
import io
import subprocess
import unittest
from types import SimpleNamespace
from unittest.mock import patch


spec = importlib.util.spec_from_file_location('checker', '/tmp/astra_node3_targeted_prelaunch_20260913.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class TargetedCheckTests(unittest.TestCase):
    def run_check(self, inventory='2, GPU-example\n', compute='', reservations=None):
        reservation = dict(matching_reservations=[], unresolved_same_user=[])
        reservation.update(reservations or {})
        with patch.object(checker.subprocess, 'run', side_effect=[SimpleNamespace(stdout=inventory), SimpleNamespace(stdout=compute)]) as run:
            with patch.object(checker, 'reservations', return_value=reservation) as scan:
                with contextlib.redirect_stdout(io.StringIO()):
                    checker.check(2, 'GPU-example')
                scan.assert_called_once_with(2, 'GPU-example')
        return run.call_args_list

    def test_selected_device_both_queries(self):
        calls = self.run_check()
        self.assertEqual(len(calls), 2)
        for call in calls:
            self.assertEqual(call.args[0][:3], ['nvidia-smi', '-i', '2'])
            self.assertEqual(call.kwargs['timeout'], 25)
            self.assertTrue(call.kwargs['check'])

    def test_wrong_uuid_refused(self):
        with self.assertRaisesRegex(ValueError, 'mismatch'):
            self.run_check(inventory='2, GPU-other\n')

    def test_wrong_index_refused(self):
        with self.assertRaisesRegex(ValueError, 'mismatch'):
            self.run_check(inventory='1, GPU-example\n')

    def test_compute_pid_refused(self):
        with self.assertRaisesRegex(ValueError, 'occupied'):
            self.run_check(compute='GPU-example, 45\n')

    def test_reserved_refused(self):
        with self.assertRaisesRegex(ValueError, 'occupied'):
            self.run_check(reservations={'matching_reservations': [46]})

    def test_unresolved_refused(self):
        with self.assertRaisesRegex(ValueError, 'unresolved'):
            self.run_check(reservations={'unresolved_same_user': [47]})

    def test_timeout_not_bypassed(self):
        with patch.object(checker.subprocess, 'run', side_effect=subprocess.TimeoutExpired('nvidia-smi', 25)):
            with self.assertRaises(subprocess.TimeoutExpired):
                checker.check(2, 'GPU-example')


if __name__ == '__main__':
    unittest.main()
