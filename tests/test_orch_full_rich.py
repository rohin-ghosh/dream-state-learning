from copy import deepcopy
import unittest

from organism_v6 import orch_full_rich as screen


class FullRichTests(unittest.TestCase):
    def setUp(self):
        self.world = screen.cohort()['worlds'][0]
        self.task = screen.tasks(self.world)[0]

    def test_frozen_denominators_and_new_namespace(self):
        frozen = screen.cohort()
        self.assertEqual(len(frozen['worlds']), 8)
        self.assertEqual(sum(len(screen.tasks(world)) for world in frozen['worlds']), 16)
        with self.assertRaises(ValueError):
            screen.cohort([self.world['edges'][0]['event']])
        self.assertEqual(screen.SOURCE_CAP + 3 * screen.TRAJECTORY_CAP, screen.TOTAL_CAP)

    def test_native_reads_and_rich_final_action(self):
        first = self.world['edges'][0]
        second = self.world['edges'][2]
        commands = iter(['READ EVENT ' + first['event'], 'ROUTE ' + first['port'], 'ROUTE ' + second['port']])
        seen = []

        def generate(messages):
            seen.append(messages)
            return dict(raw='Reasoning belongs to the actual child.\n' + next(commands),
                        terminal=True, truncated=False, generated_text_tokens=170)

        record = screen.episode(self.world, self.task, generate, {first['event']: 'unaltered actual source'})
        self.assertTrue(record['correct'])
        self.assertEqual(len(seen), 3)
        self.assertEqual(record['reads'][0]['raw'], 'unaltered actual source')
        self.assertEqual(seen[1][-1]['content'], 'MEMORY RESULT\nunaltered actual source')
        self.assertIn(first['receipt'], seen[2][-1]['content'])

    def test_missing_source_retained_without_replacement(self):
        address = self.task['events'][0]
        record = screen.episode(self.world, self.task, lambda messages: dict(
            raw='READ EVENT ' + address, terminal=True, truncated=False), {})
        self.assertEqual(record['reads'][0]['raw'], 'MEMORY UNAVAILABLE')
        self.assertEqual(record['terminal_reason'], 'invalid_or_duplicate_read')

    def test_rubric_not_length_or_headings(self):
        capture = dict(prior_reads=[dict(address='source', raw='evidence')], command=dict(kind='ROUTE'),
                       response=dict(raw='I Evidence Goal Expectation Action', terminal=True,
                                     truncated=False, generated_text_tokens=170))
        record = dict(correct=True)
        self.assertFalse(screen.row_gate(record, capture)['admitted'])
        review = dict.fromkeys(screen.RUBRIC, True)
        review.update(raw_sha256=screen.digest(capture['response']['raw']),
                      capture_sha256=screen.digest(capture), rationale='CPU fixture only')
        self.assertTrue(screen.row_gate(record, capture, review)['admitted'])
        rejected = dict(review, no_unsupported_claim=False)
        self.assertEqual(screen.row_gate(record, capture, rejected)['semantic_status'], 'FAIL_SEMANTIC')
        self.assertFalse(screen.row_gate(record, capture, rejected)['admitted'])
        for field in ('truncated', 'terminal'):
            broken = deepcopy(capture)
            broken['response'][field] = field == 'truncated'
            self.assertFalse(screen.row_gate(record, broken, review)['admitted'])
        self.assertFalse(screen.row_gate(dict(correct=False), capture, review)['admitted'])
        capture['response']['generated_text_tokens'] = 149
        self.assertFalse(screen.row_gate(record, capture, review)['admitted'])

    def test_prefix_guidance_removed_target_unchanged(self):
        capture = dict(messages=[dict(role='system', content=screen.SYSTEM + '\n\n' + screen.GUIDANCE),
                                 dict(role='user', content='actual task')], response=dict(raw='unaltered target'))
        row = screen.student_row(capture)
        self.assertEqual(row['messages'][0]['content'], screen.SYSTEM)
        self.assertEqual(row['target'], capture['response']['raw'])
        self.assertIn(screen.GUIDANCE, capture['messages'][0]['content'])

    def test_fixed_decision_conjunction(self):
        full = dict(qualified_episodes=8, qualified_worlds=4, admitted_rows=16,
                    qualified_mask=[True] * 8 + [False] * 8)
        off = dict(qualified_episodes=0, qualified_worlds=0, admitted_rows=0, qualified_mask=[False] * 16)
        summaries = dict(FULL_TARGET=full, NEW_TRAJECTORY_LOSS_OFF=off, ORIGINAL37EC=off)
        self.assertEqual(screen.decision(summaries), 'POSITIVE')
        full['qualified_worlds'] = 3
        self.assertEqual(screen.decision(summaries), 'NULL')

    def test_no_extra_calls_after_failure(self):
        record = screen.episode(self.world, self.task, lambda messages: dict(
            raw='ROUTE wrong', terminal=True, truncated=False), {})
        self.assertEqual(record['actor_calls'], 1)
        self.assertFalse(record['correct'])

    def test_source_failures_replayed_and_never_fabricated(self):
        def generate(messages):
            public = messages[-1]['content']
            if public.startswith('EXPOSURE TASK'):
                port = next(line[6:] for line in public.splitlines() if line.startswith('PORTS '))
                return dict(raw='ROUTE ' + port, terminal=True, truncated=False)
            raise ValueError('CPU_test_missing_EVENT')

        frozen = screen.cohort()
        document = screen.collect(frozen, generate, lambda name, value: None)
        self.assertEqual(document['model_calls'], 64)
        self.assertEqual(document['event_denominator'], 32)
        self.assertEqual(screen.verify_source(frozen, document), {})
        document['store']['invented'] = 'synthetic not allowed'
        document['store_sha256'] = screen.digest(document['store'])
        with self.assertRaises(ValueError):
            screen.verify_source(frozen, document)

    def test_first_port_reference_same_sixteen_tasks(self):
        results = [screen.episode(world, task, screen.first_port, {})
                   for world in screen.cohort()['worlds'] for task in screen.tasks(world)]
        self.assertEqual(len(results), 16)
        self.assertEqual(sum(record['correct'] for record in results), 8)

    def test_control_states_and_resource_scope(self):
        from gpu import orch_full_rich as runner
        from gpu import orch_full_rich_guard as guard
        self.assertEqual(set(runner.STATES), set(screen.STATES))
        self.assertEqual({value[0] for value in runner.DEVICES.values()}, {0, 1, 2})
        self.assertEqual(runner.UNUSED[0], 3)
        self.assertEqual(guard.LEASE_CUTOFF, 1790463900.0)
        frozen = screen.cohort(runner.excluded_ids({'old_ids': []}))
        self.assertEqual(len(frozen['worlds']), 8)

    def test_author_replay_joins_actual_capture_and_tokens(self):
        from gpu import orch_full_rich_audit as audit
        calls = []

        def generate(messages):
            response = screen.first_port(messages)
            response.update(token_ids=[1, 2], generated_text_tokens=1)
            calls.append(dict(messages=deepcopy(messages), response=deepcopy(response), error=None))
            return response

        record = screen.episode(self.world, self.task, generate, {})
        replayed = audit.replay_episode(self.world, self.task, dict(episode=record, store={}), iter(calls))
        self.assertEqual(replayed, calls)
        changed = deepcopy(calls)
        changed[0]['response']['generated_text_tokens'] = 999
        with self.assertRaises(AssertionError):
            audit.replay_episode(self.world, self.task, dict(episode=record, store={}), iter(changed))


if __name__ == '__main__':
    unittest.main()
