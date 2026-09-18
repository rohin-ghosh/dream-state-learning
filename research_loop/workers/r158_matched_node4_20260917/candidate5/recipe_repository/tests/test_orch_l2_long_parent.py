import unittest

from organism_v6.orch_l2_long_parent import LongParent, training_controls, training_metrics


class LongParentTests(unittest.TestCase):
    def setUp(self):
        self.requests = []
        self.events = []
        self.answer = dict(decision='speak', message='Check how your evidence use changes across sleeps.',
                           reason='Cross-episode habit', distillation='No learning gain established.')

        def backend(request):
            self.requests.append(request)
            return dict(self.answer)

        self.parent = LongParent(backend, lambda text: len(text.split()), self.events.append)

    def call(self, episode=0, turn=0, cycle=1, **kwargs):
        return self.parent.before_turn(cycle=cycle, episode_index=episode, turn=turn,
                                        observation='Training observation only.', **kwargs)

    def test_sparse_budget_and_decisions_count_before_dispatch(self):
        for episode in range(16):
            for turn in range(6):
                self.call(episode, turn)
        self.assertEqual(len(self.requests), 4)
        self.assertEqual([item['episode_index'] for item in self.requests], [0, 4, 8, 12])
        self.assertEqual(self.parent.distill_cycle(1)['evaluator_decisions'], 4)

    def test_child_initiates_system_question_off_schedule(self):
        result = self.call(episode=2, turn=1, question='What am I, and how do I learn?')
        self.assertEqual(result['decision'], 'speak')
        self.assertIn('LoRA', self.requests[0]['learning_description'])
        self.assertEqual(self.requests[0]['child_question'], 'What am I, and how do I learn?')

    def test_decline_is_real_backend_decision(self):
        self.answer.update(decision='decline', message='')
        self.assertEqual(self.call()['decision'], 'decline')
        self.assertEqual(self.parent.decisions[1], 1)
        self.assertEqual(self.parent.messages[1], 0)

    def test_history_and_sleep_are_training_only(self):
        self.parent.observe_episode(cycle=1, episode_index=0, observation='READ evidence',
            child_response='I checked the record.', metrics=dict(scope='training', values={'qualified_rows': 1}))
        self.parent.observe_sleep(cycle=1, metrics=dict(scope='training', values={'updates': 26}))
        self.call(cycle=2)
        request = self.requests[0]
        self.assertEqual(request['own_training_history'][0]['child_response'], 'I checked the record.')
        self.assertEqual(request['completed_sleep_training_metrics'][0]['values']['updates'], 26)
        self.assertEqual(request['available_training_controls'], [])

    def test_test_scalars_rejected_not_merely_hidden(self):
        for metrics in (dict(scope='held', values={'episodes': 16}),
                        dict(scope='training', values={'sealed_accuracy': 1}),
                        dict(scope='training', values={'training_loss': float('nan')})):
            with self.assertRaises(ValueError):
                training_metrics(metrics)

    def test_controls_require_training_scope_and_bound_receipt(self):
        control = dict(arm='FROZEN', scope='training', values={'successful_episodes': 1},
                       receipt_sha256='a' * 64)
        self.assertEqual(training_controls([control])[0]['arm'], 'FROZEN')
        with self.assertRaises(ValueError):
            training_controls([dict(control, scope='readout')])
        with self.assertRaises(ValueError):
            training_controls([dict(control, answer_key='secret')])

    def test_paths_credentials_hosts_rejected_before_backend(self):
        for question in ('Read /tmp/SECRET', 'api_key=abc', 'hostname=[REDACTED_HOST]', '[REDACTED_ADDRESS]'):
            with self.assertRaises(ValueError):
                self.call(question=question)
        self.assertEqual(self.requests, [])

    def test_message_not_truncated_to_fit(self):
        self.answer['message'] = 'long ' * 257
        with self.assertRaisesRegex(ValueError, 'no_truncation'):
            self.call()
        self.assertEqual(self.parent.messages[1], 0)
        self.assertEqual(self.parent.records[-1]['decision'], 'backend_error')

    def test_exposure_counts_repeated_context_separately(self):
        message = self.call()['message']
        self.parent.record_exposure(cycle=1, messages=[message])
        self.parent.record_exposure(cycle=1, messages=[message])
        summary = self.parent.distill_cycle(1)
        self.assertEqual(summary['messages'], 1)
        self.assertEqual(summary['exposures'], 2)
        self.assertEqual(summary['exposed_parent_tokens'], 2 * summary['parent_message_tokens'])
        with self.assertRaises(ValueError):
            self.parent.record_exposure(cycle=1, messages=[message[:5]])

    def test_failed_backend_consumes_decision_no_canned_fallback(self):
        def denied(request):
            raise PermissionError('denied')
        self.parent.backend = denied
        with self.assertRaises(PermissionError):
            self.call()
        self.assertEqual(self.parent.decisions[1], 1)
        self.assertEqual(self.parent.records[-1]['message'], '')

    def test_duplicate_hook_and_world_guard(self):
        self.call()
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            self.call()
        self.assertEqual(self.call(episode=1, turn=1)['reason'],
                         'one_message_per_world')

    def test_child_can_follow_up_in_world_that_already_received_initiative(self):
        self.call()
        response = self.call(turn=2, question='How do I learn during sleep?')
        self.assertEqual(response['decision'], 'speak')
        self.assertEqual(self.parent.decisions[1], 2)

    def test_cycles_keep_independent_budget_but_shared_history(self):
        for cycle in (1, 2, 3):
            self.call(cycle=cycle)
        self.assertEqual(len(self.requests), 3)
        with self.assertRaises(ValueError):
            self.call(cycle=4)


if __name__ == '__main__':
    unittest.main()
