"""CPU-only pre-inference admission binding regressions; no GPU or real scan."""

from copy import deepcopy
from datetime import datetime, timezone
from unittest.mock import patch
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from gpu import orch_math_feedback_uptake_r118_preinfer as repair
from tests.test_orch_admission_transient_exit import FakeSession, report_fixture


class PreInferenceTests(unittest.TestCase):
    def run_scan(self, session=None, change=None):
        session = session or FakeSession()
        report = report_fixture()
        if change:
            change(report)
        calls = []
        def scanner():
            calls.append(True)
            report['created_utc'] = datetime.now(timezone.utc).isoformat()
            return report
        with patch.object(repair.os, 'geteuid', return_value=0), \
                patch.object(repair.transient, '_ProcSession', return_value=session):
            result = repair.bind_scan(scanner)
        self.assertEqual(calls, [True])
        self.assertEqual(result['transient_exit_evidence']['original_report'], report)
        return result

    def test_dead_unrelated_pid_requires_two_proofs(self):
        result = self.run_scan()
        self.assertTrue(result['clear'])
        decisions = result['transient_exit_evidence']['reconciliation']['decisions']
        self.assertTrue(decisions[0]['first_observation']['proven'])
        self.assertTrue(decisions[0]['final_observation']['proven'])

    def test_live_sshd_cannot_be_cleared(self):
        session = FakeSession()
        session.observations = [dict(proven=False, disposition='pid_present_including_replacement_or_zombie')]
        self.assertFalse(self.run_scan(session)['clear'])

    def test_pid_reuse_or_exec_history_conflict_remains_blocking(self):
        for key, value in (('start_ticks', '999'), ('command_sha256', 'changed')):
            with self.subTest(key=key):
                def change(report):
                    report['processes'][0]['pinned_identity'][key] = value
                self.assertFalse(self.run_scan(change=change)['clear'])

    def test_gpu_fd_cvd_and_compute_history_remain_blocking(self):
        changes = [lambda doc: doc['processes'][0].update(target_device_open=True),
            lambda doc: doc['processes'][0].update(cvd='GPU-target'),
            lambda doc: doc['compute_processes'].append(dict(pid=101))]
        for change in changes:
            with self.subTest(change=change):
                self.assertFalse(self.run_scan(change=change)['clear'])

    def test_appearance_between_proofs_remains_blocking(self):
        session = FakeSession()
        session.observations = [session.prove_exit(session.pins[101]),
            dict(proven=False, disposition='kernel_pid_present_including_hidden_replacement')]
        self.assertFalse(self.run_scan(session)['clear'])

    def test_nontransient_device_ownership_never_removed(self):
        result = self.run_scan(change=lambda doc: doc['blocking_reasons'].append('open_device_pid:101'))
        self.assertFalse(result['clear'])
        self.assertEqual(result['blocking_reasons'], ['open_device_pid:101'])

    def test_unpinned_later_pid_never_cleared(self):
        session = FakeSession()
        session.pins = {}
        self.assertFalse(self.run_scan(session)['clear'])

    def test_nonroot_never_calls_scanner(self):
        with patch.object(repair.os, 'geteuid', return_value=1000):
            with self.assertRaisesRegex(ValueError, 'root_scan'):
                repair.bind_scan(lambda: self.fail('must not scan'))

    def test_forged_sidecar_cannot_remove_gpu_blocker(self):
        result = self.run_scan()
        envelope = deepcopy(result['transient_exit_evidence'])
        envelope['reconciliation']['blocking_reasons'] = ['invented']
        with patch.object(repair.os, 'geteuid', return_value=0), \
                patch.object(repair.transient, 'reconcile_scan', return_value=envelope):
            with self.assertRaisesRegex(ValueError, 'hidden_blocker'):
                repair.bind_scan(lambda: None)

    def test_failed_session_stops_before_guard(self):
        with TemporaryDirectory() as temporary:
            control = Path(temporary)
            (control/'FAILED.json').touch()
            with patch.dict(repair.os.environ, R118_PARALLEL_SESSION='new-session',
                    R118_PARALLEL_SESSION_SHA256='new-sha'), \
                    patch.object(repair.life.hook, 'fresh_session',
                        return_value=(dict(startup_deadline_unix=float('inf')), control)):
                with self.assertRaisesRegex(ValueError, 'failed_or_expired'):
                    repair.session_open()

    def test_old_failed_session_cannot_be_reused_without_marker(self):
        with TemporaryDirectory() as temporary, \
                patch.dict(repair.os.environ, R118_PARALLEL_SESSION='old-session',
                    R118_PARALLEL_SESSION_SHA256='e834ff7869f9309d70cf46f682adcc522f3120c8ac293ed7065708a6f50da94b'), \
                patch.object(repair.life.hook, 'fresh_session',
                    return_value=(dict(startup_deadline_unix=float('inf')), Path(temporary))):
            with self.assertRaisesRegex(ValueError, 'original_session'):
                repair.session_open()

    def test_runtime_binding_is_only_new_process_namespace(self):
        with patch.object(repair.life, 'SERVICES'), patch.object(repair.life, 'FINAL_ROOT'), \
                patch.object(repair.life, 'MODULE'), patch.object(repair.native, 'MODULE'), \
                patch.object(repair.native, 'scan'), patch.object(repair.final, 'MODULE'):
            repair.configure()
            self.assertEqual(repair.life.SERVICES, repair.SERVICES)
            self.assertEqual(repair.native.MODULE, repair.MODULE)
            self.assertIs(repair.native.scan, repair.scan)
            self.assertEqual(repair.final.MODULE, repair.MODULE)

    def test_one_live_blocker_survives_other_exact_exit_proofs(self):
        result = self.run_scan(change=lambda doc: doc['blocking_reasons'].append('minor_scan_identity_changed:3159'))
        self.assertFalse(result['clear'])
        self.assertEqual(result['blocking_reasons'], ['minor_scan_identity_changed:3159'])

    def test_proc_reader_uses_bounded_reads_for_native_boot_id(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root/'boot_id').write_bytes(b'actual-boot\n')
            descriptor = repair.os.open(root, repair.os.O_RDONLY | repair.os.O_DIRECTORY)
            try:
                self.assertEqual(repair.transient._read_at(descriptor, 'boot_id'), b'actual-boot\n')
            finally:
                repair.os.close(descriptor)

    def test_proc_reader_does_not_request_multi_megabyte_sysctl_read(self):
        class Sysctl:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self, amount):
                if amount > 4096:
                    raise OSError(12, 'Cannot allocate memory')
                return b''
        with patch.object(repair.transient.os, 'open', return_value=12), \
                patch.object(repair.transient.os, 'fdopen', return_value=Sysctl()):
            self.assertEqual(repair.transient._read_at(11, 'sys/kernel/random/boot_id'), b'')

    def test_proc_reader_retains_total_size_limit(self):
        class Oversized:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self, amount):
                return b'x' * amount
        with patch.object(repair.transient.os, 'open', return_value=12), \
                patch.object(repair.transient.os, 'fdopen', return_value=Oversized()):
            with self.assertRaisesRegex(ValueError, 'proc_record_too_large'):
                repair.transient._read_at(11, 'cmdline')

    def test_insufficient_hard_descriptor_limit_refuses_scan(self):
        with patch.object(repair.os, 'geteuid', return_value=0), \
                patch.object(repair.resource, 'getrlimit', return_value=(1024, 1024)):
            with self.assertRaisesRegex(ValueError, 'hard_pidfd_budget'):
                repair.bind_scan(lambda: self.fail('must not scan'))

    def test_own_soft_limit_restored_even_on_scan_failure(self):
        with patch.object(repair.os, 'geteuid', return_value=0), \
                patch.object(repair.resource, 'getrlimit', return_value=(1024, 1048576)), \
                patch.object(repair.resource, 'setrlimit') as setter, \
                patch.object(repair.transient, 'reconcile_scan', side_effect=OSError('scan failed')):
            with self.assertRaises(OSError):
                repair.bind_scan(lambda: None)
            self.assertEqual(setter.call_count, 2)
            self.assertGreaterEqual(setter.call_args_list[0].args[1][0], 4352)
            self.assertEqual(setter.call_args_list[1].args[1], (1024, 1048576))


if __name__ == '__main__':
    unittest.main()
