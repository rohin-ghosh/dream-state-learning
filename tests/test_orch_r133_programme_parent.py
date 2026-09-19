import hashlib
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from gpu import orch_r133_programme_parent as parent


class ProgrammeParentTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name)/'programme.md'
        self.path.write_text('Talk about an actual draft and its revision.')
        digest = hashlib.sha256(self.path.read_bytes()).hexdigest()
        self.config = dict(schema='R133_PROGRAMME_PARENT_V1', node='ovx2',
            programme='creative_writing', branch='C1', root='/localhome/local-rohing/orch_test/run1',
            source_root='/localhome/local-rohing/orch_test/source1',
            programme_path=str(self.path), programme_sha256=digest,
            principles_path=str(self.path), principles_sha256=digest,
            cadence_responses=3, hard_end_unix=time.time()+600)

    def test_explicit_pinned_configuration(self):
        self.assertEqual(parent.validate(self.config), self.config)

    def test_transport_requires_read_and_publication_modules_before_start(self):
        config_path = self.path.parent/'config.json'
        parent.write(config_path, self.config)
        output = self.path.parent/'service'
        with patch.object(parent, 'remote', side_effect=ValueError('missing_console')) as remote, \
                patch.object(parent, 'strong') as provider:
            with self.assertRaisesRegex(ValueError, 'missing_console'):
                parent.serve(config_path, self.path.parent, output, once=True)
        self.assertFalse(output.exists())
        provider.assert_not_called()
        self.assertIn('orch_r127_pilot_console', remote.call_args.args[2])
        self.assertIn('callable(console.publish_parent)', remote.call_args.args[2])

    def test_transport_preflight_is_read_only_and_source_bound(self):
        root = self.config['source_root']
        modules = {'journal': root+'/gpu/orch_r125_stream_console.py',
                   'console': root+'/gpu/orch_r127_pilot_console.py'}
        with patch.object(parent, 'remote', return_value=modules) as remote:
            self.assertEqual(parent.transport_preflight(self.path.parent, self.config), modules)
        self.assertNotIn('publish_parent(', remote.call_args.args[2])
        for wrong in ({'journal': modules['journal']},
                      dict(modules, console='/tmp/other/gpu/console.py')):
            with patch.object(parent, 'remote', return_value=wrong), self.assertRaises(ValueError):
                parent.transport_preflight(self.path.parent, self.config)

    def test_persistent_requires_every_boundary_and_an_hour(self):
        config = dict(self.config, cadence_label='PERSISTENT', cadence_responses=1,
                      minimum_duration_seconds=3600, parent_style='warm and challenging')
        self.assertEqual(parent.validate(config), config)
        for changes in ({'cadence_responses': 3}, {'minimum_duration_seconds': 3599}):
            with self.assertRaises(ValueError):
                parent.validate(dict(config, **changes))

    def test_parent_effort_is_explicit_and_bounded(self):
        self.assertEqual(parent.validate(dict(self.config, parent_reasoning_effort='low'))[
            'parent_reasoning_effort'], 'low')
        with self.assertRaisesRegex(ValueError, 'known_parent_effort'):
            parent.validate(dict(self.config, parent_reasoning_effort='arbitrary'))

    def test_poll_interval_is_bounded_without_changing_default(self):
        self.assertNotIn('poll_interval_seconds', parent.validate(self.config))
        for interval in (0.25, 1, 5, 30):
            self.assertEqual(parent.validate(dict(self.config, poll_interval_seconds=interval))[
                'poll_interval_seconds'], interval)
        for interval in (True, 0, 0.24, 31, '1', float('nan'), float('inf')):
            with self.subTest(interval=interval), self.assertRaisesRegex(ValueError, 'bounded_parent_poll_interval'):
                parent.validate(dict(self.config, poll_interval_seconds=interval))

    def test_parent_handoff_cursor_cannot_rewind_below_zero(self):
        self.assertEqual(parent.validate(dict(self.config, start_after_response_count=3))[
            'start_after_response_count'], 3)
        for cursor in (-1, True, 1.5):
            with self.assertRaisesRegex(ValueError, 'valid_parent_resume_cursor'):
                parent.validate(dict(self.config, start_after_response_count=cursor))

    def test_prefetch_uses_generation_request_clock_only_in_persistent_arm(self):
        config = dict(self.config, schedule_on='request', start_after_request_count=8)
        with self.assertRaisesRegex(ValueError, 'prefetch_only_for_persistent'):
            parent.validate(config)
        config.update(cadence_label='PERSISTENT', cadence_responses=1, minimum_duration_seconds=3600)
        parent.validate(config)
        self.assertEqual(parent.resume_cursor(config), 8)
        instruction, unused = parent.prompt(config, dict(schema='R133_TRAIN_PARENT_SNAPSHOT_V1', events=[]))
        self.assertIn('do not invent its unfinished response', instruction)

    def test_cursor_preserves_unfinished_predecessor_attempt(self):
        predecessor = self.path.parent/'previous'
        (predecessor/'parent_000000').mkdir(parents=True)
        parent.write(predecessor/'STARTED.json', dict(branch='C1', programme='creative_writing'))
        parent.write(predecessor/'parent_000000/SOURCE.json', dict(response_count=5))
        config = dict(self.config, predecessor_output=str(predecessor),
                      predecessor_started_sha256=parent.sha(predecessor/'STARTED.json'))
        with self.assertRaisesRegex(ValueError, 'no_replay_of_reserved_parent_sources'):
            parent.resume_cursor(dict(config, start_after_response_count=3))
        self.assertEqual(parent.resume_cursor(dict(config, start_after_response_count=5)), 5)

    def test_cursor_relative_omissions_stay_in_denominator(self):
        state = dict(boundaries=[
            dict(response_count=4, record_index=10, next_request_index=12),
            dict(response_count=5, record_index=13, next_request_index=16)], parent_consumptions=[])
        self.assertEqual(parent.boundary_coverage(state, 3)['missing_boundaries'], 2)

    def test_coverage_counts_consumption_before_next_generation(self):
        state = dict(boundaries=[
            dict(response_count=1, record_index=3, next_request_index=8),
            dict(response_count=2, record_index=9, next_request_index=11),
            dict(response_count=3, record_index=12, next_request_index=None)],
            parent_consumptions=[dict(record_index=5), dict(record_index=11)])
        coverage = parent.boundary_coverage(state, 0)
        self.assertEqual(coverage['closed_boundaries'], 2)
        self.assertEqual(coverage['covered_boundaries'], 1)
        self.assertEqual(coverage['missing_boundaries'], 1)
        self.assertEqual(parent.boundary_coverage(state, 1)['covered_boundaries'], 0)

    def test_publication_is_not_boundary_coverage(self):
        state = dict(boundaries=[dict(response_count=1, record_index=3, next_request_index=8)],
                     consumed_inbox={}, parent_consumptions=[])
        self.assertEqual(parent.boundary_coverage(state, 0)['covered_boundaries'], 0)

    def test_persistent_prompt_is_responsive_not_repeated_template(self):
        state = dict(schema='R133_TRAIN_PARENT_SNAPSHOT_V1', events=[])
        instruction, unused = parent.prompt(dict(self.config, cadence_label='PERSISTENT'), state)
        self.assertIn('every generation boundary', instruction)
        self.assertIn('do not repeat a slogan', instruction)

    def test_changed_programme_rejected(self):
        self.path.write_text('different')
        with self.assertRaisesRegex(ValueError, 'fixed_parent_source'):
            parent.validate(self.config)

    def test_arbitrary_host_or_path_rejected(self):
        for field, value in [('node', 'arbitrary-host'), ('root', '/tmp/held'),
                             ('programme', 'unknown'), ('cadence_responses', 0)]:
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    parent.validate(dict(self.config, **{field: value}))

    def test_parent_uses_training_snapshot_only(self):
        with self.assertRaisesRegex(ValueError, 'training_snapshot_only'):
            parent.prompt(self.config, {'schema': 'HELD_READOUT'})

    def test_parent_no_unmarked_excerpt_or_thought_format(self):
        state = dict(schema='R133_TRAIN_PARENT_SNAPSHOT_V1', events=[dict(actor='child', text='x'*6100)])
        instruction, payload = parent.prompt(self.config, state)
        self.assertIn('Do not prescribe a recurring', instruction)
        self.assertIn('at most90 words', instruction)
        self.assertIn('[Parent-view excerpt truncated]', payload)
        self.assertLess(len(payload), 6500)

    def test_receipts_are_append_only(self):
        destination = self.path.parent/'receipt.json'
        parent.write(destination, {'status': 'original'})
        with self.assertRaises(FileExistsError):
            parent.write(destination, {'status': 'replacement'})

    def test_complete_requires_observed_consumption(self):
        output = self.path.parent/'parent_000000'
        output.mkdir()
        parent.write(output/'RESULT.json', dict(status='PUBLISHED', programme='creative_writing',
                     branch='C1', inbox_publication={'id': 'example'}))
        parent.record_deliveries(self.path.parent, {'consumed_inbox': {}})
        self.assertFalse((output/'DELIVERED.json').exists())
        state = {'consumed_inbox': {'example': {'record_index': 4, 'record_sha256': 'a'*64}}}
        parent.record_deliveries(self.path.parent, state)
        result = json.loads((output/'DELIVERED.json').read_text())
        self.assertEqual(result['status'], 'COMPLETE')
        parent.record_deliveries(self.path.parent, state)


if __name__ == '__main__':
    unittest.main()
