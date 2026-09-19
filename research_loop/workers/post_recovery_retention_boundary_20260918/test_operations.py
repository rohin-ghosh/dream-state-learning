from copy import deepcopy
import json
from pathlib import Path
import signal
import tempfile
import unittest
from unittest.mock import Mock, patch

from boundary import Refusal, digest, journal_identity, sha
from coordinator import coordinate, exclusive_lock
from operations import LinuxOperations, ReceivingHooks
import operations
from test_boundary import JournalFixture
from test_coordinator import FakeOperations


class OperationsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(self.temporary.cleanup)
        self.fixture = JournalFixture(self.temporary.name)
        self.control = Path(self.temporary.name) / 'control'
        self.control.mkdir()
        self.binding = self.fixture.binding
        self.prepared = self.fixture.prepared
        self.prepared['old_plan']['root'] = str(self.fixture.root.parent)
        self.prepared['new_plan']['root'] = str(self.fixture.root.parent)
        self.plan_path = self.control / 'PLAN.json'
        self.fixture.write(self.plan_path, self.prepared['old_plan'])
        self.guard_path = self.control / 'GUARD.json'
        self.fixture.write(self.guard_path, dict(source_pins=self.binding['source_pins'],
            hard_end_unix=self.binding['hard_end_unix'], plan_path=str(self.plan_path), plan_sha256=sha(self.plan_path)))
        self.binding['guard_path'] = str(self.guard_path)
        self.binding['command'][-1] = str(self.guard_path)
        self.binding['guard_sha256'] = sha(self.guard_path)
        self.prepared['old_guard_sha256'] = self.binding['guard_sha256']
        self.authority = self.fixture.authority
        self.authority['life_binding_sha256'] = digest(self.binding)
        self.execution = digest(dict(binding=self.binding, prepared=self.prepared, authority=self.authority))
        self.hooks = ReceivingHooks(**{name: Mock() for name in ReceivingHooks.__dataclass_fields__})
        self.operations = LinuxOperations(self.binding, self.hooks,
            approved_execution_sha256=self.execution, control_root=self.control)
        self.operations.require_execution_approval(self.execution)
        self.identity = {key: self.binding[key] for key in ('pid', 'uid', 'start_ticks', 'command')}
        self.identity['state'] = 'S'
        self.patchers = [
            patch.object(operations, 'process_identity', return_value=self.identity),
            patch.object(operations.os, 'pidfd_open', return_value=321),
            patch.object(operations.select, 'select', return_value=([], [], [])),
            patch.object(Path, 'read_text', return_value=self.binding['boot_id']),
            patch.object(signal, 'pidfd_send_signal', side_effect=AssertionError('no live signal')),
        ]
        for patcher in self.patchers:
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_exact_handle_guard_and_journal_binding(self):
        handle = self.operations.open_exact_handle(self.binding)
        self.assertEqual(handle.descriptor, 321)
        self.assertEqual(handle.binding_sha256, digest(self.binding))
        self.operations.require_exact_identity(handle, self.binding)
        self.operations.verify_prepared(self.prepared)
        self.hooks.verify_prepared.assert_called_once_with(self.prepared)
        self.assertEqual(self.operations.observe(self.binding)['cycle'], 4)

    def test_copy_raw_binds_actual_journal_with_absent_retained_plan_root(self):
        retained = str(self.control / 'absent-retained-C2-identity')
        for plan in (self.prepared['old_plan'], self.prepared['new_plan']):
            plan['root'] = retained
        self.fixture.write(self.plan_path, self.prepared['old_plan'])
        guard = json.loads(self.guard_path.read_bytes())
        guard.update(copy_raw=str(self.fixture.root.parent), plan_sha256=sha(self.plan_path))
        self.fixture.write(self.guard_path, guard)
        self.binding['guard_sha256'] = sha(self.guard_path)
        self.prepared['old_guard_sha256'] = self.binding['guard_sha256']
        self.operations = LinuxOperations(self.binding, self.hooks,
            approved_execution_sha256=self.execution, control_root=self.control)
        self.operations.require_execution_approval(self.execution)
        self.assertFalse(Path(retained).exists())
        handle = self.operations.open_exact_handle(self.binding)
        self.operations.require_exact_identity(handle, self.binding)
        self.operations.verify_prepared(self.prepared)
        self.assertEqual(self.operations._guard()['root'], retained)
        self.assertEqual(self.operations.observe(self.binding)['cycle'], 4)
        self.assertEqual(json.loads(self.guard_path.read_bytes())['copy_raw'], str(self.fixture.root.parent))

    def test_copy_raw_must_match_bound_journal_and_cannot_be_ignored(self):
        guard = json.loads(self.guard_path.read_bytes())
        guard['copy_raw'] = str(self.control / 'another-fork')
        self.fixture.write(self.guard_path, guard)
        self.binding['guard_sha256'] = sha(self.guard_path)
        self.operations = LinuxOperations(self.binding, self.hooks,
            approved_execution_sha256=self.execution, control_root=self.control)
        self.operations.require_execution_approval(self.execution)
        with self.assertRaisesRegex(Refusal, 'guard_plan_same_life_journal'):
            self.operations.open_exact_handle(self.binding)

    def test_reboot_rejected_before_opening_or_rebinding_pidfd(self):
        with patch.object(Path, 'read_text', return_value='another-boot'), \
                patch.object(operations.os, 'pidfd_open') as opened:
            with self.assertRaisesRegex(Refusal, 'same_host_boot'):
                self.operations.open_exact_handle(self.binding)
        opened.assert_not_called()

    def test_pid_reuse_uid_command_and_preexisting_stop_rejected(self):
        for key, value in (('start_ticks', '999'), ('uid', 999), ('command', ['not-the-native']), ('state', 'T')):
            with self.subTest(key=key), \
                    patch.object(operations, 'process_identity', return_value=dict(self.identity, **{key: value})), \
                    patch.object(operations.os, 'close') as closed:
                with self.assertRaises(Refusal):
                    self.operations.open_exact_handle(self.binding)
                closed.assert_called_once_with(321)

    def test_native_exit_rejected_and_descriptor_closed(self):
        with patch.object(operations.select, 'select', return_value=([321], [], [])), \
                patch.object(operations.os, 'close') as closed:
            with self.assertRaisesRegex(Refusal, 'old_native_not_exited'):
                self.operations.open_exact_handle(self.binding)
        closed.assert_called_once_with(321)

    def test_guard_bytes_plan_bytes_and_journal_changes_rejected(self):
        handle = self.operations.open_exact_handle(self.binding)
        original = self.guard_path.read_bytes()
        self.guard_path.write_bytes(original + b' ')
        with self.assertRaisesRegex(Refusal, 'guard_bytes'):
            self.operations.require_exact_identity(handle, self.binding)
        self.guard_path.write_bytes(original)
        original_plan = self.plan_path.read_bytes()
        self.plan_path.write_bytes(original_plan + b' ')
        with self.assertRaisesRegex(Refusal, 'plan_bytes'):
            self.operations.require_exact_identity(handle, self.binding)
        self.plan_path.write_bytes(original_plan)
        writer = self.fixture.root / 'WRITER.lock'
        writer.rename(self.fixture.root / 'old-writer.lock')
        writer.touch()
        with self.assertRaisesRegex(Refusal, 'journal_directories'):
            self.operations.require_exact_identity(handle, self.binding)

    def test_explicit_approval_and_per_life_binding_required(self):
        with self.assertRaisesRegex(Refusal, 'execution_approval'):
            self.operations.require_execution_approval('not-approved')
        wrong = deepcopy(self.binding)
        wrong['pid'] += 1
        with self.assertRaisesRegex(Refusal, 'exact_life_only'):
            self.operations.open_exact_handle(wrong)
        unapproved = LinuxOperations(self.binding, self.hooks,
            approved_execution_sha256=self.execution, control_root=self.control)
        with self.assertRaisesRegex(Refusal, 'approved_audit'):
            unapproved.record('INTENT', {})

    def test_life_and_writer_locks_are_exclusive_and_never_replace_writer(self):
        self.operations.bound_journal = journal_identity(self.binding)
        with self.operations.exclusive_life_lock(self.binding):
            with self.assertRaises(BlockingIOError):
                with self.operations.exclusive_life_lock(self.binding):
                    self.fail('second life lock acquired')
        writer = self.fixture.root / 'WRITER.lock'
        with exclusive_lock(writer, create=False):
            with self.assertRaises(BlockingIOError):
                with self.operations.exclusive_writer_check(self.binding):
                    self.fail('second writer acquired')
        with self.operations.exclusive_writer_check(self.binding):
            pass
        writer.unlink()
        with self.assertRaises(FileNotFoundError):
            with self.operations.exclusive_writer_check(self.binding):
                self.fail('missing writer replaced')
        self.assertFalse(writer.exists())

    def test_audit_is_fsynced_exclusive_and_does_not_write_native_journal(self):
        before = {str(path): path.read_bytes() for path in self.fixture.root.rglob('*') if path.is_file()}
        with patch.object(operations.os, 'fsync', wraps=operations.os.fsync) as synced:
            self.operations.record('RETENTION_HANDOFF_INTENT', dict(epoch='test-only'))
        self.assertEqual(synced.call_count, 2)
        paths = list(self.control.glob('*_RETENTION_HANDOFF_INTENT.json'))
        self.assertEqual(len(paths), 1)
        self.assertEqual(json.loads(paths[0].read_bytes())['document']['epoch'], 'test-only')
        self.assertEqual(before, {str(path): path.read_bytes() for path in self.fixture.root.rglob('*') if path.is_file()})

    def test_full_interface_with_mocked_process_control_and_real_journal(self):
        fake = FakeOperations(self.binding)
        hooks = ReceivingHooks(verify_prepared=lambda prepared: None, dependents_clear=lambda handle: True,
            verify_checkpoint=fake.verify_checkpoint, prepare_receiver=fake.prepare_receiver,
            recheck_checkpoint=fake.recheck_checkpoint, verify_receiver=fake.verify_receiver,
            dispatch_once=self.hooks.dispatch_once)
        self.operations.hooks = hooks
        reservation = Mock()
        reservation.__enter__ = Mock(return_value=reservation)
        reservation.__exit__ = Mock(return_value=False)
        reservation.commit_and_wait_exit.return_value = True
        with patch.object(self.operations, 'reserve', return_value=reservation), \
                patch.object(self.operations, 'require_exact_identity'), \
                patch.object(self.operations, 'require_handle_exited'), \
                patch.object(self.operations, 'close_handle'), \
                patch.object(self.operations, 'wall_time', return_value=1):
            token = coordinate(self.binding, self.prepared, self.authority, self.operations)
        self.hooks.dispatch_once.assert_called_once_with(token)
        self.assertTrue(token['exact_complete']['durable'])
        self.assertEqual(len(list(self.control.glob('*_RETENTION_HANDOFF_READY.json'))), 1)


if __name__ == '__main__':
    unittest.main()
