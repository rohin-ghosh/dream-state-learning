from copy import deepcopy
import json
from pathlib import Path
import signal
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from gpu import orch_r137_parent_exposure_diagnostic as diagnostic
from gpu import orch_r137_parent_exposure_periodic as periodic


class PeriodicTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.helper = self.root / 'CUMULATIVE.py'
        self.helper.write_bytes(b'exact unchanged helper')
        self.old = dict(helper_path='/old/helper.py', helper_sha256=periodic.sha(self.helper),
            interval_seconds=30, stop_after_unix=1000, items=[dict(label='SUPPORT_PERSISTENT_PREFETCH_POLL025', segments=[])],
            remote_source='/old/remote', remote_source_receipt_sha256='same', monitor_source='/old/local', notebook='/same/notebook')
        self.config = dict(self.old, helper_path=str(self.helper))
        self.config.update({key: 'unused' for key in periodic.ADDED_KEYS})
        self.config.update(repair_policy=periodic.POLICY, snapshot_max_bytes=periodic.BUDGET,
            approval='explicit synthetic approval', baseline_measurements={'SUPPORT_PERSISTENT_PREFETCH_POLL025': {}})

    def test_only_approved_delta(self):
        periodic.config_delta(self.old, self.config)

    def test_cadence_stop_and_all_original_fields_unchanged(self):
        for key, value in [('interval_seconds', 31), ('stop_after_unix', 2000), ('items', []),
                           ('remote_source', '/changed'), ('notebook', '/other'), ('helper_sha256', 'different')]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                periodic.config_delta(self.old, dict(self.config, **{key: value}))

    def test_exact_fixed_budget_no_automatic_growth(self):
        for value in (True, 128 * 1024 * 1024, periodic.BUDGET + 1, '536870912'):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'fixed512'):
                periodic.config_delta(self.old, dict(self.config, snapshot_max_bytes=value))

    def test_no_new_record_limit_or_baseline_reset(self):
        with self.assertRaisesRegex(ValueError, 'only_approved'):
            periodic.config_delta(self.old, dict(self.config, max_records=20000))
        with self.assertRaisesRegex(ValueError, 'same_lineages'):
            periodic.config_delta(self.old, dict(self.config, baseline_measurements={}))

    def test_helper_bytes_not_current_full_native_or_changed_logic(self):
        self.helper.write_bytes(b'changed logic')
        with self.assertRaisesRegex(ValueError, 'byte_identical'):
            periodic.config_delta(self.old, self.config)

    def test_atomic_receipt_never_overwrites(self):
        path = self.root / 'AUDIT.json'
        periodic.write(path, dict(value=1))
        with self.assertRaises(FileExistsError):
            periodic.write(path, dict(value=2))
        self.assertEqual(json.loads(path.read_text()), dict(value=1))

    def test_unchanged_post_pass_cadence_and_stop_cap(self):
        self.assertEqual(periodic.sleep_duration(self.config, 900), 30)
        self.assertEqual(periodic.sleep_duration(self.config, 990), 10)
        self.assertEqual(periodic.sleep_duration(self.config, 1001), 0)

    def test_identity_failure_sends_no_signal(self):
        with patch.object(periodic, 'identity', return_value={'pid': 2}), patch.object(periodic.signal, 'pidfd_send_signal') as send:
            with self.assertRaisesRegex(ValueError, 'exact_observer_identity'):
                periodic.pause_if_idle({'pid': 1}, 20)
            send.assert_not_called()

    def test_busy_observer_not_stopped(self):
        expected = dict(pid=1)
        with patch.object(periodic, 'identity', return_value=expected), patch.object(periodic, 'idle', return_value=False), \
             patch.object(periodic.signal, 'pidfd_send_signal') as send:
            self.assertFalse(periodic.pause_if_idle(expected, 20))
            send.assert_not_called()

    def test_exited_zombie_must_be_same_identity(self):
        fields = ['Z'] + ['0'] * 18 + ['123']
        with patch.object(Path, 'read_text', return_value='1 (python3) ' + ' '.join(fields)):
            self.assertTrue(periodic.observer_exited(dict(pid=1, start_ticks='123')))
            self.assertFalse(periodic.observer_exited(dict(pid=1, start_ticks='other')))

    def test_absent_observer_is_exited(self):
        with patch.object(Path, 'read_text', side_effect=FileNotFoundError):
            self.assertTrue(periodic.observer_exited(dict(pid=1, start_ticks='123')))

    def test_exact_idle_pause(self):
        expected = dict(pid=1)
        with patch.object(periodic, 'identity', return_value=expected), patch.object(periodic, 'idle', return_value=True), \
             patch.object(periodic, 'paused_clean', return_value=True), patch.object(periodic.signal, 'pidfd_send_signal') as send:
            self.assertTrue(periodic.pause_if_idle(expected, 20))
            send.assert_called_once_with(20, signal.SIGSTOP)

    def test_late_child_or_writer_restores_only_observer(self):
        expected = dict(pid=1)
        with patch.object(periodic, 'identity', return_value=expected), patch.object(periodic, 'idle', return_value=True), \
             patch.object(periodic, 'paused_clean', return_value=False), patch.object(periodic.time, 'monotonic', side_effect=[0, 3]), \
             patch.object(periodic.signal, 'pidfd_send_signal') as send:
            self.assertFalse(periodic.pause_if_idle(expected, 20))
            self.assertEqual([call.args for call in send.call_args_list], [(20, signal.SIGSTOP), (20, signal.SIGCONT)])

    def test_paused_proof_error_restores_observer(self):
        expected = dict(pid=1)
        with patch.object(periodic, 'identity', side_effect=[expected, ValueError('identity drift')]), \
             patch.object(periodic, 'idle', return_value=True), patch.object(periodic.signal, 'pidfd_send_signal') as send:
            with self.assertRaisesRegex(ValueError, 'identity drift'):
                periodic.pause_if_idle(expected, 20)
            self.assertEqual([call.args for call in send.call_args_list], [(20, signal.SIGSTOP), (20, signal.SIGCONT)])

    def sample_fixture(self):
        from tests.test_orch_r137_parent_exposure_diagnostic import DiagnosticTests
        fixture = DiagnosticTests()
        previous, current = fixture.historical_rows()
        path = self.root / 'BASELINE.json'
        path.write_text(json.dumps(previous))
        label = 'SUPPORT_PERSISTENT_PREFETCH_POLL025'
        self.config['baseline_measurements'][label] = dict(path=str(path), sha256=periodic.sha(path), baseline=0)
        monitor = SimpleNamespace(remote='original callback')
        transport = Mock(executions=1)
        helper = SimpleNamespace(cumulative_sample=lambda item, config: deepcopy(current))
        return previous, current, label, monitor, transport, helper

    def test_success_keeps_exact_measurement_and_both_comparisons(self):
        previous, current, label, monitor, transport, helper = self.sample_fixture()
        with patch.object(diagnostic, 'OneShotTransport', return_value=transport) as factory:
            row = periodic.sample_once(helper, monitor, diagnostic, self.config, dict(label=label), self.root / 'sample', previous)
        self.assertEqual(row, current)
        self.assertEqual(monitor.remote, 'original callback')
        self.assertEqual(factory.call_args.kwargs['max_bytes'], periodic.BUDGET)
        self.assertTrue((self.root / 'sample/COMPARISONS.json').exists())

    def test_error_retains_message_traceback_and_no_stale_coverage(self):
        previous, current, label, monitor, transport, helper = self.sample_fixture()
        helper.cumulative_sample = Mock(side_effect=diagnostic.WrapperFailure('snapshot_byte_limit; full error preserved'))
        with patch.object(diagnostic, 'OneShotTransport', return_value=transport):
            row = periodic.sample_once(helper, monitor, diagnostic, self.config, dict(label=label), self.root / 'failed', previous)
        self.assertNotIn('coverage', row)
        self.assertIn('snapshot_byte_limit', row['error_message'])
        self.assertFalse(row['measurement_available'])
        self.assertEqual(monitor.remote, 'original callback')
        self.assertIn('WrapperFailure', (self.root / 'failed/TRACEBACK.txt').read_text())

    def test_historical_change_is_failure_not_partial_success(self):
        previous, current, label, monitor, transport, helper = self.sample_fixture()
        current['snapshot_state']['parent_consumptions'].append(dict(record_index=3))
        current['coverage'].update(covered_boundaries=2, missing_boundaries=0)
        helper.cumulative_sample = lambda item, config: current
        with patch.object(diagnostic, 'OneShotTransport', return_value=transport):
            row = periodic.sample_once(helper, monitor, diagnostic, self.config, dict(label=label), self.root / 'changed', previous)
        self.assertNotIn('coverage', row)
        self.assertIn('historical_closed_boundary', row['error_message'])
        self.assertFalse((self.root / 'changed/MEASUREMENT.json').exists())


if __name__ == '__main__':
    unittest.main()
