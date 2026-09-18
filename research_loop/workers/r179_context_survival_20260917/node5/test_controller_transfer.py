import ast
from copy import deepcopy
import importlib.util
from pathlib import Path
import signal
import tempfile
import time
import unittest
from unittest.mock import Mock, patch


SPEC = importlib.util.spec_from_file_location('node5_controller_transfer', Path(__file__).with_name('controller_transfer.py'))
transfer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(transfer)


class ControllerTransferTests(unittest.TestCase):
    def test_flock_matches_device_and_inode_not_just_inode(self):
        identity = dict(major=8, minor=2, inode=123)
        text = '1: FLOCK ADVISORY WRITE 10 08:02:123 0 EOF\n2: FLOCK ADVISORY WRITE 20 08:03:123 0 EOF\n'
        self.assertEqual(transfer.flock_owners(identity, text), [10])

    def test_blocked_competing_writer_refused(self):
        with self.assertRaisesRegex(ValueError, 'without_waiting_competitors'):
            transfer.flock_owners(dict(major=8, minor=2, inode=123), '1: -> FLOCK ADVISORY WRITE 20 08:02:123 0 EOF')

    def test_non_flock_ownership_refused(self):
        with self.assertRaisesRegex(ValueError, 'exclusive_flock'):
            transfer.flock_owners(dict(major=8, minor=2, inode=123), '1: POSIX ADVISORY WRITE 20 08:02:123 0 EOF')

    def test_unknown_owner_scope_refused(self):
        with self.assertRaisesRegex(ValueError, 'explicit_two_controller_scope'):
            transfer.inspect_holder('C1', {}, {})

    def test_missing_Main_addendum_does_not_signal(self):
        with patch.object(transfer.signal, 'pidfd_send_signal') as sent:
            with self.assertRaisesRegex(ValueError, 'Main_controller_addendum'):
                transfer.authorize(Path('/not-real'), None, None)
            sent.assert_not_called()

    def test_original_source_requires_exact_reviewed_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'altered.py'
            path.write_text('def supervise():\n    pass\n')
            with self.assertRaisesRegex(ValueError, 'exact_audited_R166'):
                transfer.passive_source(path)

    def test_controller_binding_drift_refused(self):
        expected = {'label': 'C2', 'holder': {'pid': 1}}
        with patch.object(transfer, 'inspect_holder', return_value={'label': 'C2', 'holder': {'pid': 2}}):
            with self.assertRaisesRegex(ValueError, 'unchanged_controller_binding'):
                transfer.verify_binding(expected, {}, {})

    def test_prior_stop_intent_is_never_repeated(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            old = root / 'orch_r179_context_C2_old'
            old.mkdir()
            holder = dict(pid=100, start_ticks='200')
            transfer.write(old / 'CONTROLLER_STOP_INTENT.json', {'holder': holder})
            with self.assertRaisesRegex(ValueError, 'consumed_never_repeat'):
                transfer.no_previous_stop(root / 'orch_r179_context_C2_new', dict(label='C2', holder=holder))

    def exercise(self, root, failure=None, flock_error=None):
        binding = dict(label='C2', holder={'pid': 100, 'start_ticks': '200'}, lock={'path': 'test'},
            wait_child=dict(pid=101, start_ticks='201', uid=0, group=100, session=100, argv_sha256='child'))
        transfer.write(root / 'ACTUAL_BOUNDARY_READY.json', {})
        transfer.write(root / 'CONTROLLER_BINDING.json', binding)
        transfer.write(root / 'TEST_GO.json', {'expires_unix': time.time() + 100})
        authorization = transfer.reference(root / 'TEST_GO.json')
        events = []
        verify_native = Mock(side_effect=lambda: events.append('native_verified'))
        real_write = transfer.write

        def write(path, value):
            events.append(path.name)
            real_write(path, value)

        with patch.object(transfer, 'verify_binding', side_effect=failure), \
             patch.object(transfer, 'verify_descriptor'), patch.object(transfer, 'no_previous_stop'), \
             patch.object(transfer.os, 'pidfd_open', return_value=10), patch.object(transfer.os, 'close'), \
             patch.object(transfer.signal, 'pidfd_send_signal', side_effect=lambda *args: events.append('SIGTERM')) as sent, \
             patch.object(transfer.select, 'select', return_value=([10], [], [])), \
             patch.object(transfer.fcntl, 'flock', side_effect=flock_error or (lambda *args: events.append('flock'))), \
             patch.object(transfer, 'flock_owners', return_value=[transfer.os.getpid()]), \
             patch.object(transfer, 'process_identity', return_value=binding['wait_child']), \
             patch.object(transfer, 'write', side_effect=write):
            if failure:
                with self.assertRaisesRegex(ValueError, 'precheck_failed'):
                    transfer.transfer(root, binding, 20, {}, {}, verify_native, authorization)
                sent.assert_not_called()
            elif flock_error:
                with self.assertRaises(BlockingIOError):
                    transfer.transfer(root, binding, 20, {}, {}, verify_native, authorization)
                sent.assert_called_once_with(10, signal.SIGTERM)
            else:
                transfer.transfer(root, binding, 20, {}, {}, verify_native, authorization)
                sent.assert_called_once_with(10, signal.SIGTERM)
        return events

    def test_precheck_failure_leaves_all_processes_untouched(self):
        with tempfile.TemporaryDirectory() as directory:
            events = self.exercise(Path(directory), ValueError('precheck_failed'))
            self.assertNotIn('SIGTERM', events)

    def test_receipt_order_and_real_lock_before_native_continuation(self):
        with tempfile.TemporaryDirectory() as directory:
            events = self.exercise(Path(directory))
        expected = ['CONTROLLER_STOP_INTENT.json', 'SIGTERM', 'CONTROLLER_EXITED.json', 'flock',
                    'CONTROLLER_LOCK_ACQUIRED.json', 'CONTROLLER_TRANSFER_VERIFIED.json']
        self.assertEqual([entry for entry in events if entry in expected], expected)
        self.assertEqual(events.count('native_verified'), 3)

    def test_after_controller_exit_lock_failure_preserves_receipts_and_no_second_stop(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            events = self.exercise(root, flock_error=BlockingIOError('test_competitor'))
            self.assertTrue((root / 'CONTROLLER_STOP_INTENT.json').exists())
            self.assertTrue((root / 'CONTROLLER_EXITED.json').exists())
            self.assertFalse((root / 'CONTROLLER_LOCK_ACQUIRED.json').exists())
            self.assertEqual(events.count('SIGTERM'), 1)
            self.assertEqual(events.count('native_verified'), 2)

    def test_only_one_exact_holder_pidfd_SIGTERM_no_group_signal(self):
        source = Path(transfer.__file__).read_text()
        calls = [node for node in ast.walk(ast.parse(source)) if isinstance(node, ast.Call)
                 and ast.unparse(node.func) == 'signal.pidfd_send_signal']
        self.assertEqual(len(calls), 1)
        self.assertEqual(ast.unparse(calls[0]), 'signal.pidfd_send_signal(holder_descriptor, signal.SIGTERM)')
        for forbidden in ('os.kill(', 'killpg', '.unlink(', 'os.remove(', 'O_CREAT', 'StreamJournal'):
            self.assertNotIn(forbidden, source)


if __name__ == '__main__':
    unittest.main()
