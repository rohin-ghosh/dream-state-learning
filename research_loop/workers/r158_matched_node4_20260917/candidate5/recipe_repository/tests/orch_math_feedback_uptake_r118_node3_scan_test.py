from copy import deepcopy
import hashlib
import unittest
from unittest.mock import Mock

from gpu import orch_math_feedback_uptake_r118_node3_scan as scanner


class ScanTests(unittest.TestCase):
    def identity(self, command='first'):
        return dict(pid=12, uid=0, start_ticks='1', boot_id='boot', command_sha256=command, exe_device=1, exe_inode=10)

    def snapshot(self, process=None):
        return dict(scanner_euid=0, gpu=dict(index=0, uuid=scanner.UUID, memory_used_mib=1, utilization_percent=0),
            compute_processes=[], processes=[] if process is None else [process])

    def test_mutable_title_requires_fresh_exact_sample(self):
        before, after = self.identity(), self.identity('second')
        first = dict(before, cvd=None, target_device_open=False)
        second = dict(after, cvd=None, target_device_open=False)
        sample = Mock(side_effect=[(before, first, after), (after, second, after)])
        entry, attempts = scanner.stable_capture(sample)
        self.assertTrue(entry['identity_consistent'])
        self.assertEqual(len(attempts), 2)
        self.assertEqual(attempts[0]['before']['command_sha256'], 'first')

    def test_uid_pid_reuse_and_boot_drift_fail(self):
        for field, value in (('pid', 13), ('uid', 4), ('start_ticks', '2'), ('boot_id', 'other')):
            with self.subTest(field=field):
                before = self.identity()
                after = dict(before, **{field:value})
                entry, unused = scanner.stable_capture(Mock(return_value=(before, before, after)))
                self.assertIn('unreadable', entry)

    def test_unstable_command_never_admitted(self):
        entry, unused = scanner.stable_capture(Mock(return_value=(self.identity(), self.identity(), self.identity('changed'))))
        self.assertEqual(entry['unreadable'], 'unstable_process_identity')

    def test_exec_with_same_argv_and_pid_is_rejected(self):
        before = self.identity()
        after = dict(before, exe_inode=11)
        entry, unused = scanner.stable_capture(Mock(return_value=(before, before, after)))
        self.assertEqual(entry['unreadable'], 'kernel_process_identity_changed')

    def test_gpu_fd_transitions_never_disappear(self):
        for opened in ([True, False], [False, True], [True, True]):
            entry = scanner.reservation(self.identity(), [None, None], opened)
            self.assertTrue(scanner.evaluate(self.snapshot(entry)))

    def test_environment_transition_never_disappears(self):
        for cvds in ([scanner.UUID, None], [None, scanner.UUID], ['1', None]):
            entry = scanner.reservation(self.identity(), cvds, [False, False])
            self.assertTrue(scanner.evaluate(self.snapshot(entry)))

    def test_each_genuine_owner_and_unknown_still_blocks(self):
        for extra in (dict(cvd=scanner.UUID), dict(cvd=scanner.UUID[:16]), dict(cvd='0'), dict(cvd='1'),
                dict(cvd='all'), dict(target_device_open=True), dict(unreadable='PermissionError')):
            with self.subTest(extra=extra):
                self.assertTrue(scanner.evaluate(self.snapshot(dict(pid=12, **extra))))

    def test_memory_compute_and_nonroot_block(self):
        for key, value in (('memory_used_mib', 33), ('utilization_percent', 1), ('index', 1), ('uuid', 'wrong')):
            snapshot = self.snapshot();snapshot['gpu'][key] = value
            self.assertTrue(scanner.evaluate(snapshot))
        snapshot = self.snapshot();snapshot['scanner_euid'] = 2524
        self.assertTrue(scanner.evaluate(snapshot))
        snapshot = self.snapshot();snapshot['compute_processes'] = [dict(pid=12, gpu_uuid=scanner.UUID)]
        self.assertTrue(scanner.evaluate(snapshot))

    def test_observed_owner_in_failed_attempt_still_blocks(self):
        before, after = self.identity(), self.identity('changed')
        entry, attempts = scanner.stable_capture(Mock(side_effect=[
            (before, dict(before, cvd=scanner.UUID), after), (after, dict(after, cvd=None), after)]))
        snapshot = self.snapshot();snapshot['processes'] = [attempt['observation'] for attempt in attempts] + [entry]
        self.assertTrue(scanner.evaluate(snapshot))

    def test_only_verified_service_fd_exception(self):
        self.assertFalse(scanner.evaluate(self.snapshot(dict(pid=12, target_device_open=True, verified_persistence_service=True))))
        self.assertTrue(scanner.evaluate(self.snapshot(dict(pid=12, target_device_open=True, verified_persistence_service=False))))

    def test_kernel_and_zombie_classification_requires_empty_fds(self):
        empty = hashlib.sha256(b'').hexdigest()
        self.assertIsNotNone(scanner.inactive_kind(empty, 'S', 0x00200000, 0))
        self.assertIsNotNone(scanner.inactive_kind(empty, 'Z', 0, 0))
        self.assertIsNone(scanner.inactive_kind(empty, 'Z', 0, 1))
        self.assertIsNone(scanner.inactive_kind(empty, 'S', 0x00200000, 1))

    def test_live_empty_argv_is_not_exempt(self):
        empty = hashlib.sha256(b'').hexdigest()
        self.assertIsNone(scanner.inactive_kind(empty, 'S', 0, 0))
        self.assertIsNone(scanner.inactive_kind('nonempty', 'Z', 0, 0))


if __name__ == '__main__':
    unittest.main()
