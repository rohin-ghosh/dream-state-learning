import inspect
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from gpu import orch_r137_route_astra_switch as switch


class RouteSwitchTests(unittest.TestCase):
    def setUp(self):
        self.boundary = dict(highest_request=115, highest_cycle=52, observed_unix=1000.0)

    def test_exact_names_only(self):
        self.assertEqual(switch.sequence('000116_F1_C0053.request.json'), (116, 53))
        for name in ('../000116_F1_C0053.request.json', '000116_F2_C0053.request.json',
                     '116_F1_C0053.request.json', '000116_F1_C0053.response.json'):
            with self.assertRaises(ValueError):
                switch.sequence(name)

    def test_no_launch_with_incompatible_consumer_or_substitution(self):
        for plan in ({}, {'provider': 'claude-fable-5-1'},
                     {'provider': switch.astra.MODEL, 'parent_model_substitution': {'allowed_models': ['claude-opus-5']}}):
            with self.assertRaisesRegex(ValueError, 'consumer_Astra_authorization'):
                switch.consumer_ready(plan)
        switch.consumer_ready({'provider': switch.astra.MODEL})

    def test_prepare_does_not_create_state_when_consumer_rejects_model(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)/'switch'
            with patch.object(switch, 'RUNTIME', Path(temporary)), \
                    patch.object(switch.transport, 'Store'), \
                    patch.object(switch, 'snapshot', return_value={'consumer_plan': {'provider': 'claude-fable-5-1'}}):
                with self.assertRaisesRegex(ValueError, 'consumer_Astra_authorization'):
                    switch.prepare(directory, Path(temporary))
            self.assertFalse(directory.exists())

    def test_only_prospective_unclaimed_unanswered(self):
        self.assertTrue(switch.eligible('000116_F1_C0053.request.json', self.boundary, 1001))
        self.assertFalse(switch.eligible('000115_F1_C0053.request.json', self.boundary, 1001))
        self.assertFalse(switch.eligible('000116_F1_C0051.request.json', self.boundary, 1001))
        self.assertFalse(switch.eligible('000116_F1_C0053.request.json', self.boundary, 999))
        self.assertFalse(switch.eligible('000116_F1_C0053.request.json', self.boundary, 1001, True))
        self.assertFalse(switch.eligible('000116_F1_C0053.request.json', self.boundary, 1001, False, True))

    def test_config_retains_child_visibility_wall_and_total_cap(self):
        old = dict(remote_root=switch.ROOT, branch='F1', family='route', max_parent_calls=200,
            deadline_unix=9999, train_tasks={'task': 'hash'}, excluded_task_ids=['held'],
            cohort_sha256='cohort', life_id='same_life', principles_sha256='principles',
            predecessor_config={}, terminal_binding={}, allowed_substitute_models=['claude-opus-5'])
        with patch.object(switch.transport, 'source_pins', return_value={'source': 'pin'}):
            config = switch.new_config(old, 114)
        self.assertEqual(config['max_parent_calls'], 86)
        for key in ('remote_root', 'deadline_unix', 'train_tasks', 'excluded_task_ids',
                    'cohort_sha256', 'life_id', 'principles_sha256'):
            self.assertEqual(config[key], old[key])
        self.assertEqual((config['parent_effort'], config['max_output_tokens']), ('low', 512))
        self.assertNotIn('allowed_substitute_models', config)
        self.assertIn('allowed_substitute_models', old)

    def test_exhausted_or_invalid_cap_rejected(self):
        old = dict(remote_root=switch.ROOT, branch='F1', family='route', max_parent_calls=2)
        for count in (-1, 2, 3, True):
            with self.assertRaises(ValueError):
                switch.new_config(old, count)

    def test_data_evaluator_preserves_request_and_provider_validation(self):
        function = switch.data_evaluator()
        self.assertIn('/data/home/rohing/courier/runtime', function.__code__.co_consts)
        self.assertNotIn('/tmp', function.__code__.co_consts)
        self.assertIs(function.__globals__['existing'], switch.astra.existing)
        self.assertIs(function.__globals__['transport'], switch.transport)

    def test_processor_uses_new_ledger_and_truthful_model(self):
        function = switch.processor()
        self.assertIn('parent_astra_r137', function.__code__.co_consts)
        self.assertNotIn('parent_claude', function.__code__.co_consts)
        self.assertEqual(function.__globals__['MODEL'], switch.astra.MODEL)
        self.assertIs(function.__globals__['evaluate'], switch.evaluate)

    def test_gate_never_opens_old_packet(self):
        store = Mock()
        self.assertFalse(switch.gate(store, '000115_F1_C0052.request.json', self.boundary))
        store.shell.assert_not_called()
        store.exists.assert_not_called()

    def test_gate_rejects_old_claim_and_existing_response(self):
        for responses in ((True, False, False), (False, True, False), (False, False, True)):
            store = Mock()
            store.exists.side_effect = responses
            store.shell.return_value.stdout = '1001'
            self.assertFalse(switch.gate(store, '000116_F1_C0053.request.json', self.boundary))

    def test_evaluate_records_prospective_model_without_retry(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = dict(status='MISSING', actual_model=None, retry=False, provider_dispatched=False)
            evaluator = Mock(return_value=result)
            with patch.object(switch, 'data_evaluator', return_value=evaluator):
                observed = switch.evaluate({}, Path(temporary), 100, config={}, launch={})
            evaluator.assert_called_once()
            self.assertFalse(observed['historical_turn_replayed'])
            self.assertFalse(observed['retry'])
            self.assertTrue((Path(temporary)/'MODEL_CHOICE.json').exists())

    def test_failed_publication_preserves_local_capture_without_retry(self):
        with tempfile.TemporaryDirectory() as temporary:
            def fail(store, config, launch, name, buffer, prompt_root, principles):
                (buffer/'capture.json').write_text('{"preserved": true}')
                raise OSError('archive_failed')
            process = Mock(side_effect=fail)
            with self.assertRaisesRegex(OSError, 'archive_failed'):
                switch.process_one(process, None, {}, {}, 'name', Path(temporary), None, None)
            process.assert_called_once()
            captures = list(Path(temporary).glob('packet_*/capture.json'))
            self.assertEqual(len(captures), 1)
            self.assertEqual(captures[0].read_text(), '{"preserved": true}')

    def test_success_removes_only_empty_scratch_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            process = Mock(return_value='COMPLETE')
            self.assertEqual(switch.process_one(process, None, {}, {}, 'name', Path(temporary), None, None), 'COMPLETE')
            self.assertFalse(list(Path(temporary).iterdir()))


if __name__ == '__main__':
    unittest.main()
