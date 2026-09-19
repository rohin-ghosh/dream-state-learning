import base64
from copy import deepcopy
import io
import json
import subprocess
import unittest
from unittest.mock import patch

import prepare_continuation
import node2_scope as scope
import retired_coalescer as kernel
import test_node2_coalescer as fixtures
import scan_receipt as subject


class DiagnosticKernelTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.Node2MutationTests()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.setUp()
        self.scan = fixtures.clean_scan([str(path) for path in self.fixture.paths])
        self.stdout = json.dumps(self.scan).encode()

    def invoke(self):
        checksum = kernel.digest(self.fixture.batch)
        return kernel.execute_batch(self.fixture.batch, expected_sha256=checksum, root=self.fixture.root,
            ledger=self.fixture.ledger, approval=dict(status='MAIN_REVIEWED_EXECUTION', batch_sha256=checksum),
            writer_scan=lambda paths: subject.scan_with_receipt(paths, self.fixture.ledger, checksum))

    def events(self):
        return self.fixture.events()

    def unchanged_paths(self):
        self.assertEqual([path.stat().st_ino for path in self.fixture.paths], self.fixture.before)

    def completed(self, stdout=None, stderr=b'', returncode=0):
        return subprocess.CompletedProcess(['CPU_SCANNER_ONLY'], returncode,
                                           self.stdout if stdout is None else stdout, stderr)

    def test_success_records_raw_exact_result_before_unchanged_predicate_then_real_kernel_mutates_fixture(self):
        original = scope.validate_writer_scan
        def observe(scan):
            self.assertEqual(self.events()[0]['kind'], 'PRIVILEGED_WRITER_SCAN_RAW_RESULT')
            return original(scan)
        with patch.object(subject.subprocess, 'run', return_value=self.completed()) as process, \
                patch.object(scope, 'validate_writer_scan', side_effect=observe):
            result = self.invoke()
        self.assertEqual(len(result), 6)
        raw = self.events()[0]['document']
        self.assertEqual(base64.b64decode(raw['stdout_base64']), self.stdout)
        self.assertEqual(raw['parsed_result'], self.scan)
        self.assertEqual(raw['target_identity_before'], raw['target_identity_after'])
        self.assertTrue(raw['admission_predicate_not_yet_called'])
        self.assertEqual(process.call_args.args[0], ['sudo', '-n', 'python3', '-B', '-c', scope.PRIVILEGED_SCAN])
        self.assertEqual(process.call_args.kwargs['timeout'], 45)

    def test_live_uncertainty_is_logged_then_still_rejected(self):
        scan = deepcopy(self.scan)
        scan['inaccessible_or_exited'] = [dict(pid=123, start_ticks='456', error_type='FileNotFoundError',
            reason='live_or_unresolved_process_unreadable')]
        stdout = json.dumps(scan).encode()
        with patch.object(subject.subprocess, 'run', return_value=self.completed(stdout, b'CPU stderr preserved')):
            with self.assertRaisesRegex(ValueError, 'complete_privileged_no_writer_snapshot_required'):
                self.invoke()
        self.unchanged_paths()
        raw = self.events()[0]['document']
        self.assertEqual(raw['parsed_result'], scan)
        self.assertEqual(base64.b64decode(raw['stdout_base64']), stdout)
        self.assertEqual(base64.b64decode(raw['stderr_base64']), b'CPU stderr preserved')
        self.assertEqual(self.events()[-1]['kind'], 'BATCH_REJECTED_NO_MUTATION')

    def test_positive_writer_still_rejects(self):
        scan = dict(self.scan, writers=[dict(pid=123, fd=4, access_mode=1)])
        with patch.object(subject.subprocess, 'run', return_value=self.completed(json.dumps(scan).encode())):
            with self.assertRaisesRegex(ValueError, 'readable_writer_present'):
                self.invoke()
        self.unchanged_paths()
        self.assertEqual(self.events()[0]['document']['parsed_result'], scan)

    def test_ledger_failure_blocks_predicate_and_mutation(self):
        with patch.object(subject.subprocess, 'run', return_value=self.completed()), \
                patch.object(self.fixture.ledger, 'record', side_effect=OSError('CPU durable ledger failure')), \
                patch.object(scope, 'validate_writer_scan', wraps=scope.validate_writer_scan) as validate:
            with self.assertRaisesRegex(OSError, 'CPU durable ledger failure'):
                self.invoke()
        validate.assert_not_called()
        self.unchanged_paths()

    def test_missing_external_durable_ack_blocks_predicate_and_mutation(self):
        wire = io.StringIO()
        self.fixture.ledger = kernel.AcknowledgedLedger(io.StringIO(''), wire)
        with patch.object(subject.subprocess, 'run', return_value=self.completed()), \
                patch.object(scope, 'validate_writer_scan', wraps=scope.validate_writer_scan) as validate:
            with self.assertRaisesRegex(ValueError, 'durable_ack_connection_lost_halt'):
                self.invoke()
        validate.assert_not_called()
        self.unchanged_paths()
        first = json.loads(wire.getvalue().splitlines()[0])
        self.assertEqual(first['kind'], 'PRIVILEGED_WRITER_SCAN_RAW_RESULT')
        self.assertEqual(base64.b64decode(first['document']['stdout_base64']), self.stdout)

    def test_bad_json_preserved_before_parse_failure_no_predicate(self):
        with patch.object(subject.subprocess, 'run', return_value=self.completed(b'{not-json')), \
                patch.object(scope, 'validate_writer_scan', wraps=scope.validate_writer_scan) as validate:
            with self.assertRaises(json.JSONDecodeError):
                self.invoke()
        validate.assert_not_called()
        self.unchanged_paths()
        raw = self.events()[0]['document']
        self.assertEqual(raw['parse_status'], 'FAILED')
        self.assertEqual(base64.b64decode(raw['stdout_base64']), b'{not-json')

    def test_nonzero_process_preserved_then_rejected(self):
        with patch.object(subject.subprocess, 'run', return_value=self.completed(b'failed stdout', b'failed stderr', 2)):
            with self.assertRaises(subprocess.CalledProcessError):
                self.invoke()
        self.unchanged_paths()
        self.assertEqual(self.events()[0]['document']['returncode'], 2)

    def test_timeout_partial_stdout_and_stderr_preserved(self):
        error = subprocess.TimeoutExpired(['CPU_ONLY'], 45, output=b'partial stdout', stderr=b'partial stderr')
        with patch.object(subject.subprocess, 'run', side_effect=error):
            with self.assertRaises(subprocess.TimeoutExpired):
                self.invoke()
        self.unchanged_paths()
        raw = self.events()[0]['document']
        self.assertEqual(base64.b64decode(raw['stdout_base64']), b'partial stdout')
        self.assertEqual(base64.b64decode(raw['stderr_base64']), b'partial stderr')
        self.assertEqual(raw['process_failure']['type'], 'TimeoutExpired')

    def test_privilege_scope_and_protocol_predicate_unchanged(self):
        for key, value in [('scanner_euid', 2524), ('scope', 'owner_only'), ('lifetime_protocol', 'unchecked')]:
            scan = dict(self.scan, **{key: value})
            with self.subTest(key=key), patch.object(subject.subprocess, 'run', return_value=self.completed(json.dumps(scan).encode())):
                with self.assertRaisesRegex(ValueError, 'complete_privileged_no_writer_snapshot_required'):
                    self.invoke()
            self.unchanged_paths()


if __name__ == '__main__':
    unittest.main()
