import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from gpu import orch_r137_parent_exposure_diagnostic as diagnostic
from gpu import orch_r133_programme_parent as parent


class DiagnosticTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / 'gpu').mkdir()
        (self.root / 'gpu/ovx2_ssh.sh').write_text('not executed')
        self.config = dict(node='ovx2', root='/exact/life', source_root='/exact/audit/source')
        self.script = 'state=snapshot("/exact/life",publications=[]); print(json.dumps(state))'

    def transport(self, **kwargs):
        return diagnostic.OneShotTransport(self.root, self.config['root'], self.config['source_root'], **kwargs)

    def test_default_local_only_never_invokes_wrapper(self):
        runner = Mock()
        transport = self.transport(runner=runner)
        with self.assertRaises(diagnostic.PreparedLocally):
            transport(self.root, self.config, self.script)
        runner.assert_not_called()
        self.assertFalse(json.loads((self.root / 'COMMAND.json').read_text())['executed'])

    def test_missing_clearance_never_invokes_wrapper(self):
        runner = Mock()
        with self.assertRaisesRegex(ValueError, 'clearance_required'):
            self.transport(execute=True, runner=runner)(self.root, self.config, self.script)
        runner.assert_not_called()

    def test_known_local_overlay_is_explicitly_reported_not_remote_pin(self):
        path = self.root / 'gpu/orch_r133_programme_parent.py'
        path.write_bytes(b'local overlay')
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        relative = 'gpu/orch_r133_programme_parent.py'
        with patch.object(diagnostic, 'LOCAL_OVERLAYS', {relative: digest}):
            result = diagnostic.verify_local_source(self.root, dict(files={relative: 'remote hash'}))
        self.assertFalse(result['local_snapshot_is_identical_to_remote_manifest'])
        self.assertEqual(result['local_remote_manifest_differences'][relative]['remote_manifest_sha256'], 'remote hash')

    def test_unknown_local_source_drift_rejected(self):
        path = self.root / 'gpu/unexpected.py'
        path.write_bytes(b'drift')
        with self.assertRaisesRegex(ValueError, 'original_local_snapshot_bytes'):
            diagnostic.verify_local_source(self.root, dict(files={'gpu/unexpected.py': 'expected'}))

    def test_preserves_complete_nonzero_streams(self):
        stderr = b'Traceback\nSnapshotLimitExceeded: snapshot_byte_limit\n' + b'x' * 200000
        runner = Mock(return_value=SimpleNamespace(returncode=1, stdout=b'prefix\x00', stderr=stderr))
        with self.assertRaises(diagnostic.WrapperFailure):
            self.transport(execute=True, clearance='synthetic clearance', runner=runner)(self.root, self.config, self.script)
        self.assertEqual((self.root / 'STDERR.bin').read_bytes(), stderr)
        self.assertEqual((self.root / 'STDOUT.bin').read_bytes(), b'prefix\x00')
        runner.assert_called_once()
        self.assertEqual(runner.call_args.kwargs['timeout'], 45)
        self.assertNotIn('text', runner.call_args.kwargs)

    def test_no_implicit_retry(self):
        transport = self.transport(runner=Mock())
        with self.assertRaises(diagnostic.PreparedLocally):
            transport(self.root, self.config, self.script)
        with self.assertRaisesRegex(ValueError, 'one_wrapper_call'):
            transport(self.root, self.config, self.script)

    def test_timeout_preserves_partial_streams(self):
        runner = Mock(side_effect=subprocess.TimeoutExpired(['synthetic'], 45, output=b'partial', stderr=b'trace'))
        with self.assertRaisesRegex(diagnostic.WrapperFailure, 'timeout'):
            self.transport(execute=True, clearance='synthetic clearance', runner=runner)(self.root, self.config, self.script)
        self.assertEqual((self.root / 'STDOUT.bin').read_bytes(), b'partial')
        self.assertEqual((self.root / 'STDERR.bin').read_bytes(), b'trace')

    def test_success_returns_original_snapshot_not_publication_counts(self):
        state = dict(consumed_inbox={}, parent_consumptions=[], parent_exposures=[], registered_inbox_count=3)
        runner = Mock(return_value=SimpleNamespace(returncode=0, stdout=json.dumps(state).encode(), stderr=b'warning'))
        result = self.transport(execute=True, clearance='synthetic clearance', runner=runner)(self.root, self.config, self.script)
        self.assertEqual(result, state)
        self.assertEqual((self.root / 'STDERR.bin').read_bytes(), b'warning')

    def test_invalid_json_is_not_a_measurement(self):
        runner = Mock(return_value=SimpleNamespace(returncode=0, stdout=b'not json', stderr=b''))
        with self.assertRaises(json.JSONDecodeError):
            self.transport(execute=True, clearance='synthetic clearance', runner=runner)(self.root, self.config, self.script)
        self.assertEqual((self.root / 'STDOUT.bin').read_bytes(), b'not json')

    def test_rejects_other_node_root_or_source(self):
        for changed in (dict(node='a40r'), dict(root='/other'), dict(source_root='/other')):
            runner = Mock()
            with self.assertRaisesRegex(ValueError, 'only_selected_node3'):
                self.transport(runner=runner)(self.root, dict(self.config, **changed), self.script)
            runner.assert_not_called()

    def test_original_script_bytes_unchanged_by_default(self):
        self.assertEqual(diagnostic.with_budget(self.script, None), self.script)

    def test_budget_changes_only_snapshot_keyword(self):
        actual = ast.parse(diagnostic.with_budget(self.script, diagnostic.MAX_BYTES))
        call = actual.body[0].value
        self.assertEqual(call.keywords.pop().arg, 'max_bytes')
        self.assertEqual(ast.dump(actual), ast.dump(ast.parse(self.script)))

    def test_budget_is_bounded_and_does_not_override_existing_keyword(self):
        for value in (True, 0, diagnostic.DEFAULT_BYTES - 1, diagnostic.MAX_BYTES + 1):
            with self.assertRaisesRegex(ValueError, 'bounded_explicit'):
                diagnostic.with_budget(self.script, value)
        with self.assertRaisesRegex(ValueError, 'exact_original'):
            diagnostic.with_budget('state=snapshot("root",publications=[],max_records=5)', diagnostic.MAX_BYTES)

    def test_original_wrapper_masks_remote_cause(self):
        result = SimpleNamespace(returncode=1, stdout='', stderr='SnapshotLimitExceeded: snapshot_byte_limit')
        with patch.object(parent.subprocess, 'run', return_value=result):
            with self.assertRaisesRegex(ValueError, '^node_transport_failed_no_implicit_retry$'):
                parent.remote(self.root, self.config, self.script)

    def test_real_snapshot_budget_preserves_matching_and_misses(self):
        from tests.test_orch_r137_parent_exposure import ParentExposureTests
        fixture = ParentExposureTests(methodName='test_limits_raise_instead_of_returning_partial_coverage')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.step()
        publication = fixture.parent()
        fixture.journal.read_inbox()
        state = fixture.read([publication])
        needed = state['journal_bytes_read']
        from gpu.orch_r137_parent_exposure import SnapshotLimitExceeded
        with self.assertRaisesRegex(SnapshotLimitExceeded, 'snapshot_byte_limit'):
            fixture.read([publication], max_bytes=needed - 1)
        adequate = fixture.read([publication], max_bytes=needed)
        self.assertEqual(adequate, state)
        self.assertEqual(adequate['parent_exposures'], [])
        fixture.step(incoming=fixture.journal.read_inbox())
        exposed = fixture.read([publication])
        adequate = fixture.read([publication], max_bytes=exposed['journal_bytes_read'])
        self.assertEqual(adequate, exposed)
        self.assertEqual(len(adequate['parent_exposures']), 1)

    def historical_rows(self):
        basis = 'verified_parent_REQUEST_exposure_not_registration'
        previous = dict(publications=[dict(id='old')], coverage=dict(closed_boundaries=1, covered_boundaries=0,
            missing_boundaries=1, coverage_basis=basis), snapshot_state=dict(coverage_basis=basis,
            boundaries=[dict(response_count=1, record_index=2, record_sha256='first', next_request_index=5)],
            parent_consumptions=[]))
        current = deepcopy(previous)
        current['publications'].append(dict(id='new'))
        current['snapshot_state']['boundaries'].append(dict(response_count=2, record_index=7, record_sha256='second', next_request_index=10))
        current['snapshot_state']['parent_consumptions'].append(dict(record_index=8))
        current['coverage'].update(closed_boundaries=2, covered_boundaries=1)
        return previous, current

    def test_historical_misses_not_reset(self):
        previous, current = self.historical_rows()
        result = diagnostic.compare_historical(previous, current, 0)
        self.assertEqual(result['historical_missing_boundaries'], [[2, 'first', 5]])
        self.assertEqual(result['new_covered_boundaries'], 1)

    def test_historical_retrocredit_rejected(self):
        previous, current = self.historical_rows()
        current['snapshot_state']['parent_consumptions'].append(dict(record_index=3))
        current['coverage'].update(covered_boundaries=2, missing_boundaries=0)
        with self.assertRaisesRegex(ValueError, 'historical_closed_boundary'):
            diagnostic.compare_historical(previous, current, 0)

    def test_baseline_reset_or_publication_loss_rejected(self):
        previous, current = self.historical_rows()
        with self.assertRaisesRegex(ValueError, 'same_original_baseline'):
            diagnostic.compare_historical(previous, current, 1)
        current['publications'] = [dict(id='new')]
        with self.assertRaisesRegex(ValueError, 'publication_union'):
            diagnostic.compare_historical(previous, current, 0)


if __name__ == '__main__':
    unittest.main()
