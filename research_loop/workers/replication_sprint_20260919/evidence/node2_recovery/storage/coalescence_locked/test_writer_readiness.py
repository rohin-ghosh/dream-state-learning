import fcntl
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import node2_scope as scope
import pidfd_scan
import retired_coalescer as subject
import retired_writer_guard as guard
import test_node2_coalescer as base_tests
from test_node2_coalescer import clean_scan


class WriterGuardTests(unittest.TestCase):
    setUp = base_tests.Node2MutationTests.setUp
    invoke = base_tests.Node2MutationTests.invoke
    events = base_tests.Node2MutationTests.events
    assert_original_inodes = base_tests.Node2MutationTests.assert_original_inodes

    def test_one_scan_all_paths_with_four_original_locks_held(self):
        calls = []
        def scanner(paths):
            calls.append(paths)
            for binding in self.locks:
                descriptor = os.open(binding['path'], os.O_RDONLY | os.O_NOATIME)
                try:
                    with self.assertRaises(BlockingIOError):
                        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                finally:
                    os.close(descriptor)
            return clean_scan(paths)
        self.writer_scan = scanner
        before = {item['path']: Path(item['path']).stat() for item in self.locks}
        self.assertEqual(len(self.invoke()), 6)
        self.assertEqual(calls, [sorted(str(path) for path in self.paths)])
        for binding in self.locks:
            path = Path(binding['path'])
            self.assertEqual(path.stat(), before[str(path)])
            descriptor = os.open(path, os.O_RDONLY | os.O_NOATIME)
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            finally:
                os.close(descriptor)

    def test_writer_locks_opened_readonly_never_created(self):
        original = os.open
        observed = []
        def opening(path, flags, *args, **kwargs):
            if str(path).endswith('/WRITER.lock'):
                observed.append(str(path))
                self.assertEqual(flags & os.O_ACCMODE, os.O_RDONLY)
                self.assertEqual(flags & (os.O_CREAT | os.O_TRUNC), 0)
            return original(path, flags, *args, **kwargs)
        with patch.object(guard.os, 'open', side_effect=opening):
            self.invoke()
        self.assertEqual(len(observed), 4)

    def test_existing_WRITER_contention_releases_earlier_locks(self):
        descriptor = os.open(self.locks[2]['path'], os.O_RDONLY)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaises(BlockingIOError):
                self.invoke()
        finally:
            os.close(descriptor)
        self.assert_original_inodes()
        for binding in self.locks:
            descriptor = os.open(binding['path'], os.O_RDONLY)
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            finally:
                os.close(descriptor)

    def test_missing_WRITER_is_not_created(self):
        path = Path(self.locks[0]['path'])
        path.rename(self.work / 'preserved_WRITER')
        with self.assertRaises(FileNotFoundError):
            self.invoke()
        self.assertFalse(path.exists())
        self.assert_original_inodes()

    def test_changed_WRITER_inode_rejected(self):
        path = Path(self.locks[0]['path'])
        path.rename(self.work / 'preserved_WRITER')
        path.write_bytes(b'')
        with self.assertRaisesRegex(ValueError, 'exact_original_WRITER_identity'):
            self.invoke()
        self.assert_original_inodes()

    def test_WRITER_rebound_during_intent_halts_before_link(self):
        original = self.ledger.record
        def record(kind, document):
            result = original(kind, document)
            if kind == 'TEMP_LINK_INTENT':
                path = Path(self.locks[0]['path'])
                path.rename(self.work / 'preserved_original_WRITER')
                path.write_bytes(b'')
            return result
        with patch.object(self.ledger, 'record', side_effect=record):
            with self.assertRaisesRegex(ValueError, 'WRITER_identity_or_metadata_changed'):
                self.invoke()
        self.assert_original_inodes()
        self.assertEqual(list(self.root.rglob('.node2-coalesce-*')), [])

    def test_exact_memory_bound_WRITER_receipt_needs_no_source_staging(self):
        guard.bind_lock_bytes(guard.LOCKS_FILE.read_bytes())
        with patch.object(guard, 'LOCKS_FILE', self.work / 'absent_locks.json'):
            self.invoke()

    def test_bad_memory_bound_WRITER_receipt_rejected(self):
        with self.assertRaisesRegex(ValueError, 'exact_original_WRITER_binding_bytes'):
            guard.bind_lock_bytes(guard.LOCKS_FILE.read_bytes() + b' ')
        self.assert_original_inodes()

    def test_old_policy_cannot_run_with_new_helper(self):
        self.batch.pop('writer_protection')
        with self.assertRaisesRegex(ValueError, 'explicit_reviewed_lock_held_policy'):
            self.invoke()


class PidfdLifetimeTests(unittest.TestCase):
    def setUp(self):
        self.module = {'__name__': 'cpu_pidfd_fixture'}
        exec(compile(pidfd_scan.PROGRAM, 'pidfd_scan_cpu', 'exec'), self.module)

    def test_real_live_pidfd_cannot_be_cleared(self):
        descriptor = os.pidfd_open(os.getpid(), 0)
        try:
            start = self.module['process_start'](os.getpid())
            self.assertIsNone(self.module['confirmed_exit'](os.getpid(), descriptor, start))
        finally:
            os.close(descriptor)

    def test_real_exited_child_bound_by_pidfd_and_start_is_cleared(self):
        child = subprocess.Popen([sys.executable, '-B', '-c', 'import sys;sys.stdin.buffer.read()'], stdin=subprocess.PIPE)
        descriptor = os.pidfd_open(child.pid, 0)
        try:
            start = self.module['process_start'](child.pid)
            child.stdin.close()
            child.wait(timeout=10)
            proof = self.module['confirmed_exit'](child.pid, descriptor, start)
            self.assertEqual(proof['proof'], 'bound_pidfd_readable_no_new_lifetime')
            self.assertEqual(proof['start_ticks'], start)
        finally:
            os.close(descriptor)
            if child.poll() is None:
                child.stdin.close()
                child.wait(timeout=10)

    def test_reused_pid_is_not_cleared_by_old_exited_pidfd(self):
        with patch.dict(self.module, process_start=lambda pid: 200, pidfd_exited=lambda descriptor: True):
            self.assertIsNone(self.module['confirmed_exit'](123, 10, 100))

    def test_inaccessible_live_process_is_not_cleared(self):
        def denied(pid):
            raise PermissionError('CPU denied live stat')
        with patch.dict(self.module, process_start=denied, pidfd_exited=lambda descriptor: False):
            self.assertIsNone(self.module['confirmed_exit'](123, 10, 100))
            result = self.module['inspect_process'](123, set(), set())
            self.assertEqual(result['error']['error_type'], 'PermissionError')
            self.assertNotIn('verified_exit', result)

    def test_unresolved_missing_fd_on_live_process_is_not_cleared(self):
        with patch.dict(self.module, process_start=lambda pid: 100, pidfd_exited=lambda descriptor: False):
            self.assertIsNone(self.module['confirmed_exit'](123, 10, 100))

    def test_kernel_ESRCH_requires_absent_start_not_just_pid_number(self):
        def absent(pid):
            raise FileNotFoundError()
        with patch.dict(self.module, process_start=absent), patch.object(os, 'pidfd_open', side_effect=ProcessLookupError()):
            result = self.module['confirmed_exit'](123, None, 100)
            self.assertEqual(result['proof'], 'kernel_ESRCH_and_absent_start_after_enumeration')
        with patch.dict(self.module, process_start=lambda pid: 200), patch.object(os, 'pidfd_open', side_effect=ProcessLookupError()):
            self.assertIsNone(self.module['confirmed_exit'](123, None, 100))

    def test_exact_process_reader_detects_actual_open_writer(self):
        with tempfile.TemporaryFile() as handle:
            info = os.fstat(handle.fileno())
            result = self.module['inspect_process'](os.getpid(), {(info.st_dev, info.st_ino)}, set())
            self.assertTrue(any(item.get('fd') == handle.fileno() for item in result['writers']))
            self.assertNotIn('error', result)


if __name__ == '__main__':
    unittest.main(verbosity=2)
