import json
from pathlib import Path
import signal
import tempfile
import time
import unittest
from unittest.mock import patch

from gpu import orch_r137_parent_latency_handoff as handoff


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.config = dict(schedule_on='request', start_after_request_count=6,
            start_after_response_count=6, branch='SUPPORT_PERSISTENT', programme='emotional_support',
            minimum_duration_seconds=3600, hard_end_unix=time.time() + 7200,
            parent_reasoning_effort='low', cadence_responses=1, parent_style='unchanged')
        self.config_path = self.root / 'config.json'
        handoff.write(self.config_path, self.config)

    def call(self, number, status='PUBLISHED'):
        directory = self.root / ('parent_' + str(number).zfill(6))
        directory.mkdir()
        source = dict(request_count=number, response_count=number-1, head_sha256='head')
        handoff.write(directory / 'SOURCE.json', source)
        if status:
            handoff.write(directory / 'RESULT.json', dict(status=status, schedule_on='request',
                schedule_count=number, source_response_count=number-1, source_head_sha256='head',
                branch=self.config['branch'], programme=self.config['programme'],
                started_unix=1, finished_unix=2, inbox_publication={'id': 'preserved'}))
        return directory

    def test_cursor_is_reservation_not_latest_child_count(self):
        self.call(7)
        self.call(11)
        state = handoff.reservation(self.root, self.config)
        self.assertEqual(state['request_cursor'], 11)
        self.assertEqual(state['response_cursor'], 10)

    def test_terminal_failure_is_reserved_never_retried(self):
        self.call(7, 'MISSING')
        self.assertEqual(handoff.reservation(self.root, self.config)['request_cursor'], 7)

    def test_unfinished_reservation_blocks(self):
        self.call(7, None)
        with self.assertRaisesRegex(ValueError, 'unfinished_parent_call'):
            handoff.reservation(self.root, self.config)

    def test_empty_call_directory_blocks(self):
        (self.root / 'parent_000000').mkdir()
        with self.assertRaisesRegex(ValueError, 'unfinished_parent_call'):
            handoff.reservation(self.root, self.config)

    def test_mismatched_result_blocks(self):
        directory = self.call(7)
        result = handoff.read(directory / 'RESULT.json')
        result['schedule_count'] = 8
        (directory / 'RESULT.json').write_text(json.dumps(result))
        with self.assertRaisesRegex(ValueError, 'result_matches_source_reservation'):
            handoff.reservation(self.root, self.config)

    def test_cursor_cannot_rewind_or_duplicate(self):
        self.call(6)
        with self.assertRaisesRegex(ValueError, 'strict_source_reservations'):
            handoff.reservation(self.root, self.config)

    def test_successor_preserves_all_nonhandoff_fields(self):
        spec = dict(old_config=str(self.config_path), old_output=str(self.root), old_started_sha256='pin')
        config = handoff.successor_config(spec, dict(request_cursor=11, response_cursor=10))
        changed = {key for key in self.config if config[key] != self.config[key]}
        self.assertEqual(changed, {'start_after_request_count', 'start_after_response_count'})
        self.assertEqual(config['poll_interval_seconds'], 0.25)
        self.assertEqual(config['predecessor_started_sha256'], 'pin')
        self.assertEqual(config['hard_end_unix'], self.config['hard_end_unix'])

    def test_identity_failure_sends_no_signal(self):
        with patch.object(handoff, 'identity', side_effect=ValueError('exact_start_ticks')), \
             patch.object(signal, 'pidfd_send_signal') as send:
            with self.assertRaisesRegex(ValueError, 'exact_start_ticks'):
                handoff.paused_reservation({}, 123)
            send.assert_not_called()

    def test_pause_verification_failure_resumes_same_pidfd(self):
        with patch.object(handoff, 'identity', side_effect=['S', ValueError('identity changed')]), \
             patch.object(signal, 'pidfd_send_signal') as send:
            with self.assertRaises(ValueError):
                handoff.paused_reservation({}, 123)
            self.assertEqual(send.call_args_list, [unittest.mock.call(123, signal.SIGSTOP),
                                                  unittest.mock.call(123, signal.SIGCONT)])

    def test_idle_successor_uses_quarter_second_without_replay(self):
        from gpu import orch_r133_programme_parent as parent
        self.config.update(poll_interval_seconds=0.25, cadence_label='PERSISTENT')
        self.config_path.write_text(json.dumps(self.config))
        state = dict(request_count=6, response_count=6, record_count=10)
        with patch.object(parent, 'validate', side_effect=lambda config: config), \
             patch.object(parent, 'snapshot', return_value=state), \
             patch.object(parent, 'boundary_coverage', return_value={}), \
             patch.object(parent, 'record_deliveries'), \
             patch.object(parent, 'strong') as provider, \
             patch.object(parent.time, 'sleep', side_effect=InterruptedError('stop idle test')) as sleep:
            with self.assertRaisesRegex(InterruptedError, 'stop idle test'):
                parent.serve(self.config_path, self.root, self.root / 'successor')
            sleep.assert_called_once_with(0.25)
            provider.assert_not_called()

    def test_unfinished_pause_resumes_without_termination(self):
        with patch.object(handoff, 'identity', return_value='T'), \
             patch.object(handoff, 'Path') as path, \
             patch.object(handoff, 'read', return_value=self.config), \
             patch.object(handoff, 'reservation', side_effect=ValueError('unfinished_parent_call')), \
             patch.object(signal, 'pidfd_send_signal') as send:
            task = unittest.mock.MagicMock()
            (task / 'children').read_text.return_value = ''
            (path.return_value / '123' / 'task').iterdir.return_value = [task]
            with self.assertRaisesRegex(ValueError, 'unfinished_parent_call'):
                handoff.paused_reservation(dict(pid=123, old_output='/output', old_config='/config'), 456)
            self.assertEqual(send.call_args_list, [unittest.mock.call(456, signal.SIGSTOP),
                                                  unittest.mock.call(456, signal.SIGCONT)])

    def test_cumulative_monitor_unions_segments_and_keeps_baseline(self):
        from gpu import orch_r137_parent_monitor as monitor
        self.config.update(node='ovx2', root='/localhome/local-rohing/orch_test/run1')
        self.config_path.write_text(json.dumps(self.config))
        new_path = self.root / 'new.json'
        handoff.write(new_path, dict(self.config, start_after_response_count=10))
        segments = []
        for index, path in enumerate((self.config_path, new_path)):
            output = self.root / str(index)
            output.mkdir()
            handoff.write(output / 'STARTED.json', dict(started_unix=100 + index))
            segments.append(dict(parent_config=str(path), parent_output=str(output), config_sha256=handoff.sha(path)))
        state = dict(coverage_basis='verified_parent_REQUEST_exposure_not_registration',
                     request_count=12, response_count=11, parent_exposures=[{}, {}])
        with patch.object(monitor, 'publications_from_results', side_effect=[[{'id': 'old'}], [{'id': 'new'}]]), \
             patch.object(monitor, 'parent_alive', side_effect=[False, True]), \
             patch.object(monitor, 'remote', return_value=state) as remote, \
             patch.object(monitor, 'boundary_coverage', return_value=dict(covered_boundaries=3, closed_boundaries=5,
                 missing_boundaries=2)) as coverage:
            row = handoff.cumulative_sample(dict(segments=segments), dict(remote_source='/source',
                remote_source_receipt_sha256='pin', repository='/repo', historical_monitor_output='/history'))
            coverage.assert_called_once_with(state, 6)
            script = remote.call_args.args[2]
            self.assertIn("{'id': 'old'}", script)
            self.assertIn("{'id': 'new'}", script)
            self.assertEqual(row['coverage']['missing_boundaries'], 2)
            self.assertEqual(len(row['segments']), 2)


if __name__ == '__main__':
    unittest.main()
