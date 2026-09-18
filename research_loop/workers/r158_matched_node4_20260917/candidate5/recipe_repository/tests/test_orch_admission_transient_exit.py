"""CPU-only adversarial tests; no scanners, subprocesses, devices or signals."""

from contextlib import ExitStack
from copy import deepcopy
from datetime import datetime, timezone
import errno
import hashlib
import json
import os
from pathlib import Path
import select
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from gpu import orch_admission_transient_exit as candidate


def historical_identity(process_id=101):
    return dict(pid=process_id, uid=1000, start_ticks='12345', boot_id='test-boot',
                command_sha256=hashlib.sha256(b'unrelated').hexdigest())


def report_fixture(reason='minor_scan_identity_changed:101'):
    identity = historical_identity()
    process = {key: identity[key] for key in candidate.IDENTITY_FIELDS if key != 'boot_id'}
    process.update(pinned_identity=deepcopy(identity), cvd=None, target_device_open=False)
    return dict(scanner_pid=os.getpid(), scanner_euid=0, created_utc='', clear=False,
                blocking_reasons=[reason], processes=[process], compute_processes=[],
                gpu=dict(index=2, uuid='GPU-test', memory_used_mib=0, utilization_percent=0),
                device_minor=5, device_path='/dev/nvidia5',
                original_index_assumption_blocking_reasons=['original-evidence'],
                opaque_evidence=dict(retain=['unaltered']))


class FakeSession:
    def __init__(self):
        self.events = []
        self.process_ids = [101]
        self.pins = {101: dict(identity=historical_identity(), descriptor=41,
                              captured_monotonic_ns=1)}
        self.capture_error = None
        self.observations = []
        self.context_error = None

    def pids(self):
        return self.process_ids

    def pin(self, process_id):
        self.events.append(('pin', process_id))
        if self.capture_error is not None:
            raise self.capture_error
        return self.pins.get(process_id)

    def check_context(self):
        if self.context_error is not None:
            raise self.context_error

    def prove_exit(self, pin):
        self.events.append(('proof', pin['identity']['pid']))
        if self.observations:
            observation = self.observations.pop(0)
            if isinstance(observation, Exception):
                raise observation
            return observation
        return dict(proven=True, disposition='pidfd_exited_and_pid_absent',
                    pidfd_pollin=True, proc_lookup_errno=errno.ENOENT,
                    kernel_pidfd_open_errno=errno.ESRCH, observed_monotonic_ns=2)


class ReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.session = FakeSession()
        self.report = report_fixture()

    def run_candidate(self, **options):
        def scan():
            self.session.events.append(('scan',))
            self.report['created_utc'] = datetime.now(timezone.utc).isoformat()
            return self.report

        with patch.object(candidate, '_ProcSession', return_value=self.session):
            return candidate.reconcile_scan(scan, **options)

    def assert_blocked(self, result):
        self.assertFalse(result['reconciliation']['candidate_clear'])
        self.assertFalse(result['launch_authorized'])
        self.assertEqual(result['reconciliation']['cleared_reasons'], [])
        for reason in self.report['blocking_reasons']:
            self.assertIn(reason, result['reconciliation']['blocking_reasons'])

    def test_short_lived_unrelated_exit_has_bound_proof_not_launch_permission(self):
        result = self.run_candidate()
        audit = result['reconciliation']
        self.assertTrue(audit['candidate_clear'])
        self.assertEqual(audit['cleared_reasons'], self.report['blocking_reasons'])
        self.assertEqual(self.session.events, [('pin', 101), ('scan',), ('proof', 101), ('proof', 101)])
        self.assertEqual(audit['decisions'][0]['historical_identity'], historical_identity())
        self.assertEqual(audit['decisions'][0]['final_observation']['kernel_pidfd_open_errno'], errno.ESRCH)
        self.assertNotIn('clear', result)
        self.assertFalse(result['launch_authorized'])
        self.assertEqual(result['binding_status'], 'UNBOUND_REQUIRES_MAIN_REVIEW_AND_TESTS')

    def test_original_report_preserved_and_hashed_without_aliasing(self):
        result = self.run_candidate()
        self.assertEqual(result['original_report'], self.report)
        self.assertFalse(self.report['clear'])
        encoded = json.dumps(self.report, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
        self.assertEqual(result['original_report_sha256'], hashlib.sha256(encoded).hexdigest())
        result['original_report']['opaque_evidence']['retain'].append('new')
        self.assertEqual(self.report['opaque_evidence']['retain'], ['unaltered'])

    def test_process_identity_drift_can_clear_only_with_matching_history(self):
        self.report['blocking_reasons'] = ['process_identity_drift:101']
        self.assertTrue(self.run_candidate()['reconciliation']['candidate_clear'])

    def test_every_other_reason_is_preserved_even_when_transient_clears(self):
        for blocker in ('open_device_pid:101', 'unknown_process_visibility:101',
                        'unknown_minor_process_visibility:101:PermissionError',
                        'reserved_cvd_pid:101', 'uuid_reservation:101',
                        'unknown_numeric_or_special_cvd:101', 'active_compute_pid:101',
                        'foreign_owned_pid:101', 'kernel_uuid_minor_changed',
                        'physical_allocation_mismatch', 'device_not_idle',
                        'unexplained_device_memory', 'minor_scan_process_drift:101',
                        'future_unknown_reason:101'):
            with self.subTest(blocker=blocker):
                self.report = report_fixture()
                self.report['blocking_reasons'].append(blocker)
                audit = self.run_candidate()['reconciliation']
                self.assertEqual(audit['blocking_reasons'], [blocker])
                self.assertFalse(audit['candidate_clear'])

    def test_live_process_or_replacement_remains_blocking(self):
        for disposition in ('historical_process_not_exited', 'pid_present_including_replacement_or_zombie',
                            'kernel_pid_present_including_hidden_replacement'):
            with self.subTest(disposition=disposition):
                self.session.observations = [dict(proven=False, disposition=disposition)]
                self.assert_blocked(self.run_candidate())

    def test_replacement_appearing_between_observations_is_not_cleared(self):
        self.session.observations = [dict(proven=True, disposition='initial_absence'),
                                     dict(proven=False, disposition='live_replacement')]
        self.assert_blocked(self.run_candidate())

    def test_unreadable_proc_never_means_absent(self):
        for error in (PermissionError(errno.EACCES, 'test'), OSError(errno.EIO, 'test')):
            with self.subTest(error=type(error).__name__):
                self.session.observations = [error]
                self.assert_blocked(self.run_candidate())

    def test_identity_mismatch_pid_reuse_exec_uid_boot_and_missing_pin(self):
        for key, value in (('pid', 102), ('uid', 2000), ('start_ticks', '54321'),
                           ('boot_id', 'different-boot'), ('command_sha256', 'different-command')):
            for location in ('capture', 'report'):
                with self.subTest(key=key, location=location):
                    self.session = FakeSession()
                    self.report = report_fixture()
                    identity = (self.session.pins[101]['identity'] if location == 'capture'
                                else self.report['processes'][0]['pinned_identity'])
                    identity[key] = value
                    self.assert_blocked(self.run_candidate())
        self.report = report_fixture()
        self.report['processes'][0].pop('pinned_identity')
        self.assert_blocked(self.run_candidate())

    def test_live_gpu_holder_or_reservation_facts_cannot_be_exempted(self):
        for key, value in (('target_device_open', True), ('cvd', '2'), ('cvd', 'GPU-test'),
                           ('cvd', 'GPU-other'), ('cvd', 'MIG-test'), ('cvd', 'all'),
                           ('unreadable', 'PermissionError'), ('vanished', True), ('foreign_owned', True)):
            with self.subTest(key=key, value=value):
                self.report = report_fixture()
                self.report['processes'][0][key] = value
                self.assert_blocked(self.run_candidate())
        self.report = report_fixture()
        self.report['compute_processes'] = [dict(pid=101, gpu_uuid='GPU-test')]
        self.assert_blocked(self.run_candidate())

    def test_missing_facts_do_not_mean_negative_facts(self):
        for key in ('cvd', 'target_device_open', 'start_ticks'):
            with self.subTest(key=key):
                self.report = report_fixture()
                self.report['processes'][0].pop(key)
                self.assert_blocked(self.run_candidate())

    def test_unpinned_new_process_and_exit_during_capture_stay_blocked(self):
        for error in (None, FileNotFoundError(errno.ENOENT, 'gone'), ProcessLookupError(errno.ESRCH, 'gone')):
            with self.subTest(error=error):
                self.session.pins = {}
                self.session.capture_error = error
                self.assert_blocked(self.run_candidate())

    def test_capture_errors_and_resource_exhaustion_fail_closed(self):
        for error in (PermissionError(errno.EACCES, 'test'), OSError(errno.EMFILE, 'test'),
                      OSError(errno.ENOSYS, 'test'), OSError(errno.EPERM, 'test')):
            with self.subTest(error=error.errno):
                self.session.capture_error = error
                self.assert_blocked(self.run_candidate())
        self.session = FakeSession()
        self.session.process_ids = [101, 102]
        self.assert_blocked(self.run_candidate(max_pins=1))
        self.assertEqual(self.session.events, [('scan',)])

    def test_unavailable_session_still_preserves_original_scan(self):
        def scan():
            self.report['created_utc'] = datetime.now(timezone.utc).isoformat()
            return self.report

        with patch.object(candidate, '_ProcSession', side_effect=ValueError('unsupported')):
            result = candidate.reconcile_scan(scan)
        self.assert_blocked(result)
        self.assertEqual(result['original_report'], self.report)

    def test_context_error_revokes_all_tentative_clears(self):
        self.session.check_context = Mock(side_effect=[None, ValueError('namespace changed')])
        result = self.run_candidate()
        self.assert_blocked(result)
        self.assertFalse(result['reconciliation']['decisions'][0]['cleared'])

    def test_second_pid_proof_error_revokes_first_pid_clear(self):
        self.session.process_ids.append(102)
        self.session.pins[102] = dict(identity=historical_identity(102), descriptor=42,
                                     captured_monotonic_ns=1)
        second = deepcopy(self.report['processes'][0])
        second.update(pid=102, pinned_identity=historical_identity(102))
        self.report['processes'].append(second)
        self.report['blocking_reasons'].append('process_identity_drift:102')
        self.session.observations = [dict(proven=True, disposition='absent'),
                                     dict(proven=True, disposition='absent'),
                                     PermissionError(errno.EACCES, 'test')]
        result = self.run_candidate()
        self.assert_blocked(result)
        self.assertFalse(any(item['cleared'] for item in result['reconciliation']['decisions']))

    def test_duplicate_records_or_inconsistent_clear_fail_closed(self):
        self.report['processes'].append(deepcopy(self.report['processes'][0]))
        self.assert_blocked(self.run_candidate())
        self.report = report_fixture()
        self.report['clear'] = True
        self.assert_blocked(self.run_candidate())

    def test_noncanonical_and_unknown_reason_names_are_not_relaxed(self):
        for reason in ('minor_scan_identity_changed:0101', 'minor_scan_identity_changed:101:extra',
                       'minor_scan_identity_changed:-101', 'minor_scan_identity_changed',
                       'process_identity_drift_extra:101', 'minor_scan_process_drift:101'):
            with self.subTest(reason=reason):
                self.report = report_fixture(reason)
                self.assert_blocked(self.run_candidate())

    def test_saved_report_and_subprocess_report_are_rejected(self):
        self.report['created_utc'] = '2000-01-01T00:00:00+00:00'
        with patch.object(candidate, '_ProcSession', return_value=self.session):
            self.assert_blocked(candidate.reconcile_scan(lambda: self.report))
        self.report = report_fixture()
        self.report['scanner_pid'] = os.getpid() + 1
        self.assert_blocked(self.run_candidate())

    def test_callback_failure_closes_session_resources_and_propagates(self):
        closed = Mock()

        def session_factory(stack):
            stack.callback(closed)
            return self.session

        with patch.object(candidate, '_ProcSession', side_effect=session_factory):
            with self.assertRaisesRegex(RuntimeError, 'scanner_failed'):
                candidate.reconcile_scan(Mock(side_effect=RuntimeError('scanner_failed')))
        closed.assert_called_once_with()

    def test_no_blockers_is_still_not_launch_authorization(self):
        self.report['blocking_reasons'] = []
        self.report['clear'] = True
        result = self.run_candidate()
        self.assertTrue(result['reconciliation']['candidate_clear'])
        self.assertFalse(result['launch_authorized'])


class KernelProofTests(unittest.TestCase):
    def setUp(self):
        self.session = object.__new__(candidate._ProcSession)
        self.session.root = 12
        self.session.check_context = Mock()
        self.pin = dict(identity=historical_identity(), descriptor=41)

    def proof(self, *, dead=True, proc_error=None, kernel_error=None):
        proc_error = FileNotFoundError(errno.ENOENT, 'test') if proc_error is None else proc_error
        kernel_error = ProcessLookupError(errno.ESRCH, 'test') if kernel_error is None else kernel_error
        with patch.object(candidate, '_exited', return_value=dead), \
                patch.object(candidate.os, 'stat', side_effect=proc_error) as lookup, \
                patch.object(candidate.os, 'pidfd_open', side_effect=kernel_error) as kernel:
            result = self.session.prove_exit(self.pin)
        return result, lookup, kernel

    def test_exit_requires_both_enoent_and_esrch(self):
        result, lookup, kernel = self.proof()
        self.assertTrue(result['proven'])
        lookup.assert_called_once_with('101', dir_fd=12, follow_symlinks=False)
        kernel.assert_called_once_with(101, 0)

    def test_live_pidfd_short_circuits_absence_check(self):
        result, lookup, kernel = self.proof(dead=False)
        self.assertFalse(result['proven'])
        lookup.assert_not_called()
        kernel.assert_not_called()

    def test_live_replacement_and_zombie_proc_entry_block(self):
        with patch.object(candidate, '_exited', return_value=True), \
                patch.object(candidate.os, 'stat', return_value=object()), \
                patch.object(candidate.os, 'pidfd_open') as kernel:
            self.assertFalse(self.session.prove_exit(self.pin)['proven'])
        kernel.assert_not_called()

    def test_hidden_or_racing_replacement_is_found_by_kernel(self):
        with patch.object(candidate, '_exited', return_value=True), \
                patch.object(candidate.os, 'stat', side_effect=FileNotFoundError(errno.ENOENT, 'test')), \
                patch.object(candidate.os, 'pidfd_open', return_value=77), \
                patch.object(candidate.os, 'close') as close:
            self.assertFalse(self.session.prove_exit(self.pin)['proven'])
        close.assert_called_once_with(77)

    def test_permission_io_and_wrong_errno_are_not_absence(self):
        for error in (PermissionError(errno.EACCES, 'test'), OSError(errno.EIO, 'test'),
                      FileNotFoundError(errno.ENOTDIR, 'test')):
            with self.subTest(error=error.errno), self.assertRaises(OSError):
                self.proof(proc_error=error)
        for error in (PermissionError(errno.EPERM, 'test'), OSError(errno.ENOSYS, 'test'),
                      FileNotFoundError(errno.ENOENT, 'test'), ProcessLookupError(errno.EIO, 'test')):
            with self.subTest(error=error.errno), self.assertRaises(OSError):
                self.proof(kernel_error=error)

    def test_pidfd_poll_errors_do_not_prove_exit(self):
        for mask, expected in ((select.POLLIN, True), (select.POLLIN | select.POLLHUP, True),
                               (select.POLLHUP, False), (0, False)):
            with self.subTest(mask=mask), patch.object(candidate.select, 'poll') as poll:
                poll.return_value.poll.return_value = [(41, mask)]
                self.assertEqual(candidate._exited(41), expected)
                poll.return_value.poll.assert_called_once_with(0)
        for mask in (select.POLLNVAL, select.POLLERR, select.POLLIN | select.POLLERR):
            with self.subTest(mask=mask), patch.object(candidate.select, 'poll') as poll:
                poll.return_value.poll.return_value = [(41, mask)]
                with self.assertRaises(OSError):
                    candidate._exited(41)


class CaptureTests(unittest.TestCase):
    def test_stat_parser_handles_spaces_and_parentheses_in_command(self):
        raw = ('101 (name ) with ( parens) ' + ' '.join(['S'] + ['0'] * 18 + ['12345'])).encode()
        self.assertEqual(candidate._stat_identity(raw), (101, '12345'))

    def test_capture_binds_stable_proc_directory_to_pidfd_and_closes_it(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            process = root / '101'
            process.mkdir()
            (process / 'stat').write_text('101 (test) ' + ' '.join(['S'] + ['0'] * 18 + ['12345']))
            (process / 'cmdline').write_bytes(b'unrelated')
            session = object.__new__(candidate._ProcSession)
            session.root = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
            stack.callback(os.close, session.root)
            session.context = ('test-boot',)
            reader = candidate._read_at

            def read_at(directory, name):
                if name.startswith('self/fdinfo/'):
                    return b'Pid:\t101\n'
                return reader(directory, name)

            with ExitStack() as pins:
                session.stack = pins
                with patch.object(candidate, '_read_at', side_effect=read_at), \
                        patch.object(candidate, '_exited', return_value=False), \
                        patch.object(candidate.os, 'pidfd_open', side_effect=lambda *_: os.open('/dev/null', os.O_RDONLY)):
                    pin = session.pin(101)
                self.assertEqual(pin['identity']['start_ticks'], '12345')
                os.fstat(pin['descriptor'])
            with self.assertRaises(OSError):
                os.fstat(pin['descriptor'])

    def test_capture_rejects_changed_identity_or_wrong_pidfd_namespace(self):
        for changed, fd_pid in ((True, 101), (False, 102)):
            with self.subTest(changed=changed, fd_pid=fd_pid), ExitStack() as stack:
                session = object.__new__(candidate._ProcSession)
                session.stack = stack
                session.root = 12
                first = historical_identity()
                second = dict(first, start_ticks='999') if changed else first
                session._identity = Mock(side_effect=[first, second])
                with patch.object(candidate.os, 'open', return_value=21), \
                        patch.object(candidate.os, 'close'), \
                        patch.object(candidate.os, 'pidfd_open', return_value=41), \
                        patch.object(candidate, '_read_at', return_value=f'Pid:\t{fd_pid}\n'.encode()), \
                        patch.object(candidate, '_exited', return_value=False):
                    if fd_pid == 101:
                        self.assertIsNone(session.pin(101))
                    else:
                        with self.assertRaisesRegex(ValueError, 'pidfd_namespace'):
                            session.pin(101)

    def test_proc_visibility_requires_root_ptrace_and_matching_namespaces(self):
        session = object.__new__(candidate._ProcSession)
        session.root = 12
        with patch.object(candidate.os, 'geteuid', return_value=1000):
            with self.assertRaisesRegex(ValueError, 'root_and_pidfd'):
                session._context()
        with patch.object(candidate.os, 'geteuid', return_value=0), \
                patch.object(candidate, '_read_at', return_value=b'CapEff:\t0\n'):
            with self.assertRaisesRegex(ValueError, 'cap_sys_ptrace'):
                session._context()
        with patch.object(candidate.os, 'geteuid', return_value=0), \
                patch.object(candidate, '_read_at', return_value=b'CapEff:\t80000\n'), \
                patch.object(candidate.os, 'readlink', side_effect=['pid:a', 'pid:b', 'user:a', 'user:a']):
            with self.assertRaisesRegex(ValueError, 'namespace_mismatch'):
                session._context()

    def test_proc_context_binds_boot_namespaces_pid_and_mount(self):
        session = object.__new__(candidate._ProcSession)
        session.root = 12
        stat_text = (str(os.getpid()) + ' (test) ' + ' '.join(['S'] + ['0'] * 18 + ['12345'])).encode()
        records = {'self/status': b'CapEff:\t80000\n', 'self/stat': stat_text,
                   'sys/kernel/random/boot_id': b'test-boot\n'}
        namespaces = {'self/ns/pid': 'pid:a', '1/ns/pid': 'pid:a',
                      'self/ns/user': 'user:a', '1/ns/user': 'user:a'}
        with patch.object(candidate.os, 'geteuid', return_value=0), \
                patch.object(candidate, '_read_at', side_effect=lambda _, name: records[name]), \
                patch.object(candidate.os, 'readlink', side_effect=lambda name, **_: namespaces[name]), \
                patch.object(candidate.os, 'fstat', return_value=SimpleNamespace(st_dev=1, st_ino=2)), \
                patch.object(candidate.os, 'stat', return_value=SimpleNamespace(st_dev=1, st_ino=2)) as stat:
            session.context = session._context()
            self.assertEqual(session.context[0], 'test-boot')
            session.check_context()
            records['sys/kernel/random/boot_id'] = b'changed-boot'
            with self.assertRaisesRegex(ValueError, 'context_changed'):
                session.check_context()
            records['sys/kernel/random/boot_id'] = b'test-boot'
            stat.return_value = SimpleNamespace(st_dev=9, st_ino=2)
            with self.assertRaisesRegex(ValueError, 'mount_changed'):
                session.check_context()


if __name__ == '__main__':
    unittest.main()
