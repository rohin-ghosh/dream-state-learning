import copy
import hashlib
import json
import unittest

from gpu import orch_r127_route_transfer_reduce as reducer


def fixture(world_count=2):
    source_hash = reducer.document_sha256('shared initial-generated source store')
    initial_hash = reducer.document_sha256('initial adapter')
    conditions = {condition: dict(checkpoint_state_sha256=initial_hash if condition == 'SEED'
        else reducer.document_sha256(condition), cycle=0 if condition == 'SEED' else int(condition[-1]),
        updates=0 if condition == 'SEED' else (112 if condition.startswith('GUIDED') else 56))
        for condition in reducer.CONDITIONS}
    plan = dict(evaluation_split='fresh_public_held', prospective=True, world_count=world_count,
                conditions=conditions, initial_state_sha256=initial_hash,
                source_store_sha256=source_hash, source_ready=True, store_size=world_count * 4, tasks=[])
    groups = {condition: [] for condition in reducer.CONDITIONS}
    for world_index in range(world_count):
        for task_index in range(2):
            world_id, task_id = f'world-{world_index}', f'task-{task_index}'
            task = dict(node=world_id, goal=f'goal-{task_index}', ports=['port'], events=['event'])
            messages = [dict(role='system', content='canonical'), dict(role='user', content=str(task))]
            bindings = dict(world_id=world_id, task_id=task_id, task_sha256=reducer.document_sha256(task),
                            initial_prompt_sha256=reducer.document_sha256(messages))
            plan['tasks'].append(bindings)
            for condition in reducer.CONDITIONS:
                commands = ['READ EVENT event', 'ROUTE port', 'ROUTE port']
                captures = []
                public = copy.deepcopy(messages)
                for turn, command in enumerate(commands):
                    response = dict(raw=command, prompt_tokens=20, token_ids=[11, 12, 0],
                                    generated_text_tokens=2, terminal=True, truncated=False)
                    captures.append(dict(turn=turn, command=command, messages=copy.deepcopy(public),
                                         response=response, error=None))
                    public.append(dict(role='assistant', content=command))
                    public.append(dict(role='user', content='child-written event' if turn == 0 else 'route receipt'))
                groups[condition].append(dict(bindings, condition=condition, task=task, captures=captures,
                    reads=['event'], routes=[], messages=public, parent_messages=[], actor_calls=3,
                    terminal_reason='reached_goal', correct=True, trainingAllowed=False,
                    checkpoint_state_sha256=conditions[condition]['checkpoint_state_sha256'],
                    source_store_sha256=source_hash))
    return copy.deepcopy(plan), copy.deepcopy(groups)


class RouteTransferReducerTests(unittest.TestCase):
    def setUp(self):
        self.plan, self.groups = fixture()

    def compare(self):
        return reducer.compare(self.plan, self.groups, bootstrap_samples=100, seed=17)

    def test_digest_matches_prospective_compact_json_not_historical_spaces(self):
        values = [dict(node='world', events=['first', 'second']),
                  [dict(role='system', content='opaque identifiers'),
                   dict(role='user', content='caf\u00e9 route')]]
        for value in values:
            with self.subTest(value=value):
                expected = hashlib.sha256(json.dumps(value, sort_keys=True,
                                          separators=(',', ':')).encode()).hexdigest()
                historical = hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
                self.assertEqual(reducer.document_sha256(value), expected)
                self.assertNotEqual(reducer.document_sha256(value), historical)

    def test_historical_spaced_bindings_rejected_even_when_plan_and_record_agree(self):
        for field, value in (('task_sha256', self.groups['GUIDED_C2'][0]['task']),
                             ('initial_prompt_sha256', self.groups['GUIDED_C2'][0]['captures'][0]['messages'])):
            with self.subTest(field=field):
                plan, groups = copy.deepcopy((self.plan, self.groups))
                historical = hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
                plan['tasks'][0][field] = historical
                for records in groups.values():
                    records[0][field] = historical
                with self.assertRaisesRegex(ValueError, 'content_hash_mismatch'):
                    reducer.compare(plan, groups, bootstrap_samples=100)

    def test_seven_conditions_nine_contrasts_one_seed(self):
        result = self.compare()
        self.assertEqual(len(result['conditions']), 7)
        self.assertEqual(len(result['comparisons']), 9)
        self.assertEqual(result['conditions']['SEED']['episodes'], 4)
        self.assertFalse(result['causal_claim'])
        self.assertIn('OBSERVATIONAL_SYSTEMS', result['interpretation'])
        self.assertIn('SAME_FAMILY', result['generalization'])
        self.assertEqual(result['conditions']['GUIDED_C2']['checkpoint']['updates'], 112)
        self.assertEqual(result['conditions']['UNPARENTED_C2']['checkpoint']['updates'], 56)

    def test_all_hashes_required_and_bound(self):
        for field in ('task_sha256', 'initial_prompt_sha256', 'checkpoint_state_sha256', 'source_store_sha256'):
            for value in (None, 'invalid', '0' * 64):
                with self.subTest(field=field, value=value):
                    groups = copy.deepcopy(self.groups)
                    groups['GUIDED_C2'][0][field] = value
                    with self.assertRaisesRegex(ValueError, 'hash|sha256'):
                        reducer.compare(self.plan, groups, bootstrap_samples=100)

    def test_recompute_actual_task_and_initial_prompt_hashes(self):
        self.groups['GUIDED_C2'][0]['task']['goal'] = 'changed'
        with self.assertRaisesRegex(ValueError, 'task_content_hash'):
            self.compare()
        self.plan, self.groups = fixture()
        self.groups['GUIDED_C2'][0]['captures'][0]['messages'][0]['content'] = 'changed'
        with self.assertRaisesRegex(ValueError, 'initial_prompt_content_hash'):
            self.compare()

    def test_missing_duplicate_or_extra_episode_rejected(self):
        for mode in ('missing', 'duplicate', 'extra'):
            with self.subTest(mode=mode):
                self.plan, self.groups = fixture()
                if mode == 'missing':
                    self.groups['GUIDED_C2'].pop()
                elif mode == 'duplicate':
                    self.groups['GUIDED_C2'].append(copy.deepcopy(self.groups['GUIDED_C2'][0]))
                else:
                    self.groups['GUIDED_C2'][0]['world_id'] = 'unplanned'
                with self.assertRaisesRegex(ValueError, 'missing_episode|duplicate_episode|unexpected_task'):
                    self.compare()

    def test_trace_repetition_includes_rejected_read(self):
        record = self.groups['GUIDED_C2'][0]
        record['captures'][1]['command'] = 'READ EVENT event'
        record['captures'][1]['error'] = dict(type='ValueError', message='invalid_or_repeated_read')
        record['captures'] = record['captures'][:2]
        record['actor_calls'] = 2
        record['terminal_reason'] = 'capture_error'
        record['correct'] = False
        metrics = reducer.episode_metrics(record)['metrics']
        self.assertEqual(metrics['read_attempts'], 2)
        self.assertEqual(metrics['accepted_reads'], 1)
        self.assertEqual(metrics['repeated_read_attempts'], 1)
        self.assertEqual(metrics['rejected_action_calls'], 1)
        self.assertIsNone(metrics['reads_before_first_route'])
        self.assertEqual(metrics['task_completed'], 0)
        self.assertIsNone(metrics['environment_feedback_reaction'])

    def test_no_read_before_route_is_zero_not_missing(self):
        record = self.groups['GUIDED_C2'][0]
        record['captures'][0]['command'] = 'ROUTE port'
        record['reads'] = []
        metrics = reducer.episode_metrics(record)['metrics']
        self.assertEqual(metrics['reads_before_first_route'], 0)
        self.assertEqual(metrics['any_read_before_first_route'], 0)
        self.assertEqual(metrics['accepted_reads'], 0)

    def test_missing_telemetry_is_not_zero_or_partial_sum(self):
        record = self.groups['GUIDED_C2'][0]
        del record['captures'][0]['response']['prompt_tokens']
        del record['captures'][0]['response']['truncated']
        del record['captures'][0]['error']
        record['correct'] = None
        result = reducer.episode_metrics(record)
        for name in ('prompt_tokens', 'truncated_responses', 'rejected_action_calls', 'accepted_reads', 'correct'):
            self.assertIsNone(result['metrics'][name])
        self.assertEqual(result['coverage']['prompt_tokens'], dict(observed=2, missing=1, total=3))
        self.assertEqual(result['metrics']['generated_tokens_including_eos'], 9)

    def test_missing_response_kept_in_attempt_denominator(self):
        record = self.groups['GUIDED_C2'][0]
        record['captures'][-1]['response'] = None
        result = reducer.episode_metrics(record)
        self.assertEqual(result['metrics']['action_calls'], 3)
        self.assertEqual(result['metrics']['missing_responses'], 1)
        self.assertIsNone(result['metrics']['generated_tokens_including_eos'])

    def test_missing_one_episode_metric_excludes_whole_world_pair(self):
        self.groups['GUIDED_C2'][0]['correct'] = None
        result = self.compare()
        summary = result['conditions']['GUIDED_C2']['metrics']['correct']
        self.assertEqual(summary['observed_episodes'], 3)
        self.assertEqual(summary['missing_episodes'], 1)
        paired = result['comparisons']['GUIDED_C2_minus_UNPARENTED_C2']['metrics']['correct']
        self.assertEqual(paired['paired_worlds'], 1)
        self.assertEqual(paired['excluded_worlds'], 1)
        self.assertIsNone(paired['ci95'])
        self.assertIsNone(paired['standard_error'])

    def test_uncertainty_clusters_two_episodes_within_world(self):
        for record in self.groups['GUIDED_C2'][:2]:
            record['correct'] = False
        paired = self.compare()['comparisons']['GUIDED_C2_minus_UNPARENTED_C2']['metrics']['correct']
        self.assertEqual(paired['paired_worlds'], 2)
        self.assertEqual(paired['world_differences'], {'world-0': -1, 'world-1': 0})
        self.assertEqual(paired['mean_difference'], -0.5)
        self.assertAlmostEqual(paired['standard_error'], 0.5)
        self.assertEqual(paired['ci95'], [-1, 0])

    def test_unknowns_not_false_and_outcomes_secondary(self):
        metrics = self.compare()['conditions']['GUIDED_C2']['metrics']
        for name in reducer.UNKNOWN:
            self.assertEqual(metrics[name]['status'], 'UNKNOWN')
            self.assertIsNone(metrics[name]['mean'])
        self.assertEqual(metrics['correct']['role'], 'SECONDARY')
        self.assertEqual(metrics['task_completed']['role'], 'SECONDARY')

    def test_training_parent_or_live_seed_rejected(self):
        self.groups['GUIDED_C2'][0]['trainingAllowed'] = True
        with self.assertRaisesRegex(ValueError, 'evaluation_only'):
            self.compare()
        self.plan, self.groups = fixture()
        self.groups['GUIDED_C2'][0]['parent_messages'] = [{'message': 'help'}]
        with self.assertRaisesRegex(ValueError, 'evaluation_only'):
            self.compare()
        self.plan, self.groups = fixture()
        self.plan['conditions']['SEED']['updates'] = 1
        with self.assertRaisesRegex(ValueError, 'fixed_initial'):
            self.compare()

    def test_reproducible_nonmutating_and_order_invariant(self):
        before = copy.deepcopy((self.plan, self.groups))
        first = self.compare()
        self.assertEqual((self.plan, self.groups), before)
        self.assertEqual(first, self.compare())
        for rows in self.groups.values():
            rows.reverse()
        second = self.compare()
        self.assertEqual(first['comparisons'], second['comparisons'])

    def test_full_prospective_panel_shape(self):
        plan, groups = fixture(world_count=16)
        result = reducer.compare(plan, groups, bootstrap_samples=100)
        self.assertEqual(result['world_count'], 16)
        self.assertEqual(result['conditions']['SEED']['episodes'], 32)
        self.assertEqual(len(result['episode_metrics']), 224)

    def test_source_readiness_and_size_are_required_and_reported(self):
        result = self.compare()
        self.assertTrue(result['source_ready'])
        self.assertEqual(result['store_size'], 8)
        for field in ('source_ready', 'store_size'):
            plan = copy.deepcopy(self.plan)
            del plan[field]
            with self.assertRaisesRegex(ValueError, 'source_'):
                reducer.compare(plan, self.groups, bootstrap_samples=100)

    def test_unavailable_source_worlds_never_filtered(self):
        self.plan['store_size'] = 0
        for records in self.groups.values():
            for record in records:
                record['messages'][3]['content'] = 'MEMORY UNAVAILABLE'
                for capture in record['captures'][1:]:
                    capture['messages'][3]['content'] = 'MEMORY UNAVAILABLE'
        result = self.compare()
        metrics = result['conditions']['GUIDED_C2']['metrics']
        self.assertEqual(metrics['unavailable_memory_reads']['mean'], 1)
        self.assertEqual(metrics['supplied_memory_reads']['mean'], 0)
        self.assertEqual(result['conditions']['GUIDED_C2']['worlds'], 2)
        self.assertEqual(result['store_size'], 0)

    def test_evidence_delivery_is_not_semantic_use(self):
        record = self.groups['GUIDED_C2'][0]
        metrics = reducer.episode_metrics(record)['metrics']
        self.assertEqual(metrics['supplied_memory_reads'], 1)
        self.assertEqual(metrics['unavailable_memory_reads'], 0)
        self.assertIsNone(metrics['supplied_evidence_content_use'])
        record['messages'] = record['messages'][:2]
        metrics = reducer.episode_metrics(record)['metrics']
        self.assertIsNone(metrics['unavailable_memory_reads'])

    def test_original_episode_cpu_scripted_responses_need_no_normalization_of_trace(self):
        from organism_v6 import orch_l2_guided as guided
        from organism_v6 import orch_l2_shared as shared

        world = guided.rich.hop.build_world()
        task = shared.tasks(world)[0]
        first_edge = world['edges'][0]
        second_edge = world['edges'][2]
        commands = iter(['READ EVENT ' + first_edge['event'], 'ROUTE ' + first_edge['port'],
                         'ROUTE ' + second_edge['port']])

        def scripted_response(messages):
            self.assertEqual(messages[0]['content'], guided.rich.SYSTEM)
            return dict(raw=next(commands), terminal=True, truncated=False,
                        prompt_tokens=0, token_ids=[1, 2], generated_text_tokens=1)

        episode = guided.episode(world, task, scripted_response, {}, parent=None, rich_contract=False)
        metrics = reducer.episode_metrics(episode)['metrics']
        self.assertEqual(metrics['unavailable_memory_reads'], 1)
        self.assertEqual(metrics['supplied_memory_reads'], 0)
        self.assertEqual(metrics['reads_before_first_route'], 1)
        self.assertEqual(metrics['prompt_tokens'], 0)
        self.assertEqual(metrics['correct'], 1)
        self.assertEqual(metrics['task_completed'], 1)

    def test_manifest_hash_omissions_rejected(self):
        for field in ('task_sha256', 'initial_prompt_sha256'):
            plan = copy.deepcopy(self.plan)
            del plan['tasks'][0][field]
            with self.assertRaisesRegex(ValueError, 'missing_or_invalid_hash'):
                reducer.compare(plan, self.groups, bootstrap_samples=100)
        del self.plan['conditions']['GUIDED_C2']['checkpoint_state_sha256']
        with self.assertRaisesRegex(ValueError, 'missing_or_invalid_hash'):
            self.compare()

    def test_incomplete_capture_trace_and_wrong_cycle_rejected(self):
        self.groups['GUIDED_C2'][0]['captures'].pop()
        with self.assertRaisesRegex(ValueError, 'actor_call_trace_count_mismatch'):
            self.compare()
        self.plan, self.groups = fixture()
        self.plan['conditions']['GUIDED_C2']['cycle'] = 4
        with self.assertRaisesRegex(ValueError, 'fixed_checkpoint_cycle'):
            self.compare()

    def test_missing_all_pairs_and_observed_zero_are_distinct(self):
        for record in self.groups['GUIDED_C2']:
            record['correct'] = None
        result = self.compare()
        missing = result['comparisons']['GUIDED_C2_minus_SEED']['metrics']['correct']
        zero = result['comparisons']['UNPARENTED_C2_minus_SEED']['metrics']['correct']
        self.assertEqual(missing['paired_worlds'], 0)
        self.assertIsNone(missing['mean_difference'])
        self.assertIsNone(missing['ci95'])
        self.assertEqual(zero['mean_difference'], 0)
        self.assertEqual(zero['ci95'], [0, 0])


if __name__ == '__main__':
    unittest.main()
