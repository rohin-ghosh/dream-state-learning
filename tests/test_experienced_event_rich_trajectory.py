"""CPU-only rich collection, public projection, critique and paired mask proofs."""

from copy import deepcopy
import hashlib
import json
import subprocess
import sys
import unittest
from unittest.mock import Mock

from organism_v6 import experienced_event_rich_trajectory as rich
from organism_v6 import experienced_event_goal_pairs as goal
from organism_v6 import experienced_event_goal_breadth as breadth
from organism_v6 import experienced_event_goal_scale as scale
from organism_v6 import experienced_event_two_hop as hop
from tests.test_experienced_event_goal_pairs import reseal
from tests.test_experienced_event_two_hop import exposed_child, generation
from tests.test_experienced_event_two_hop_lesson import Tokenizer


def rich_child(messages):
    command = messages[-1]['content'].split('Execute only this next command, then wait for actual feedback:\n')[1]
    return generation('RATIONALE\nI use the available public observations.\n'
                      'PREDICTION: I expect a public reply, not an invented result.\nACTION\n' + command + '\n\n', messages)


def critic_child(messages):
    return generation('The history is evidence; any claimed next result remains a prediction.\n', messages)


class RichTrajectoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = rich.validate_registry()
        cls.collections = [rich.collect_world(world, exposed_child)
                           for world in cls.registry[0]['TRAIN'] + cls.registry[0]['PROBE']]
        cls.document = rich.collect_lessons(0, cls.collections[:4], rich_child, critic_child)

    def test_no_model_or_tokenizer_dependency_loading(self):
        script = """
import builtins
original = builtins.__import__
def checked(name, *args, **kwargs):
    if name.split('.')[0] in ('torch', 'transformers', 'peft', 'tokenizers'):
        raise AssertionError(name)
    return original(name, *args, **kwargs)
builtins.__import__ = checked
from organism_v6 import experienced_event_rich_trajectory
"""
        result = subprocess.run([sys.executable, '-B', '-c', script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_all_twenty_namespaces_disjoint_from_old_breadth_scale(self):
        old_worlds = [hop.build_world(), hop.build_world(hop.TRANSFER_MASTER)]
        old_worlds += [goal.build_world(master) for master in goal.MASTERS]
        old_worlds += [breadth.build_world(master) for master in breadth.MASTERS]
        for worlds in scale.validate_registry().values():
            old_worlds += worlds['TRAIN'] + worlds['PROBE']
        old_ids = set().union(*(rich.identifiers(world) for world in old_worlds))
        registry = rich.validate_registry(old_ids=old_ids)
        seen = set(old_ids)
        original = goal.build_worlds()
        for shard, worlds in registry.items():
            self.assertEqual(rich.runtime(shard)['PREFIX'], 'ASTRA-RICH-20260914-V1-SHARD-' + str(shard))
            self.assertEqual([len(worlds[split]) for split in ('TRAIN', 'PROBE')], [4, 1])
            self.assertEqual(worlds, rich.build_worlds(shard, old_ids=old_ids))
            self.assertIs(rich.runtime(shard)['_runtime'].__wrapped__.__globals__, rich.runtime(shard))
            for world in worlds['TRAIN'] + worlds['PROBE']:
                self.assertTrue(rich.identifiers(world).isdisjoint(seen))
                seen.update(rich.identifiers(world))
            with self.assertRaisesRegex(ValueError, 'identifier_collision'):
                rich.build_worlds(0, old_ids={worlds['PROBE'][0]['nodes'][0]})
        self.assertEqual(len(seen - old_ids), 340)
        self.assertEqual(goal.build_worlds(), original)
        for shard in (-1, 4, True, '0'):
            with self.assertRaises(ValueError):
                rich.runtime(shard)

    def test_exact_envelope_extraction_unicode_byte_spans_no_repairs(self):
        command = 'READ EVENT ' + self.registry[0]['TRAIN'][0]['edges'][0]['event'] + '\n\n'
        raw = 'RATIONALE\nA café observation.\nPREDICTION: A reply.\nACTION\n' + command
        projection = rich.project_action(raw)
        self.assertEqual(projection['action'], command)
        self.assertEqual(raw[slice(*projection['action_span'])], command)
        self.assertEqual(raw.encode()[slice(*projection['action_byte_span'])], command.encode())
        self.assertEqual(projection['raw_sha256'], hashlib.sha256(raw.encode()).hexdigest())
        for malformed in (command, ' ' + raw, raw.replace('\n', '\r\n'), raw + 'STOP',
                          raw + '\nACTION\n' + command, raw.replace('A café observation.', '\nRATIONALE\nmore'),
                          'RATIONALE\n \nACTION\n' + command, raw.replace(command, ' ' + command)):
            with self.subTest(raw=malformed), self.assertRaises(ValueError):
                rich.project_action(malformed)

    def test_complete_native_captures_projections_critics_and_three_forms(self):
        document = self.document
        self.assertEqual((document['rich_calls'], document['critique_calls'], document['model_calls']), (96, 16, 112))
        self.assertTrue(document['ready'])
        self.assertTrue(document['complete_corpus'])
        self.assertEqual(document['candidate_rows'], document['rows'])
        self.assertEqual((document['planned_task_count'], document['attempted_task_count'],
                          document['complete_episode_count'], document['candidate_row_count']), (16, 16, 16, 96))
        self.assertFalse(document['fit_ready'])
        self.assertEqual(document['fits'], 0)
        self.assertEqual(rich.replay_lessons(document), document['rows'])
        self.assertEqual(rich.compile_paired_rows(document), document['rows'])
        self.assertEqual({form: len(rows) for form, rows in document['rows'].items()}, dict.fromkeys(rich.FORMS, 96))
        native_indexes = [capture['native_call_index'] for capture in document['captures'] + document['critiques']]
        self.assertEqual(sorted(native_indexes), list(range(112)))
        for index, capture in enumerate(document['captures']):
            terse, full, masked = [document['rows'][form][index] for form in rich.FORMS]
            self.assertEqual(terse['assistant'], capture['projection']['action'])
            self.assertEqual(full['assistant'], capture['response']['raw'])
            self.assertEqual(masked['assistant'], full['assistant'])
            self.assertEqual(terse['prefix'], full['prefix'])
            self.assertEqual(full['prefix'], masked['prefix'])
            self.assertEqual(capture['response']['messages'], capture['messages'])
            self.assertFalse(capture['grounding']['factual_truth_verified'])
        self.assertTrue(all(entry['complete'] for entry in document['episodes']))
        self.assertTrue(all(summary['paired'] == dict(correct=2, denominator=2) for summary in document['summaries']))
        for critique in document['critiques']:
            self.assertTrue(critique['candidate_only'])
            self.assertFalse(critique['reviewed'] or critique['controls_selection'])
            self.assertNotIn(rich.PARENT_GUIDANCE, str(critique['messages']))
            self.assertNotIn('Execute only this next command', str(critique['messages']))
            self.assertEqual(critique['response']['messages'], critique['messages'])

    def test_separate_teach_and_critique_phases_join_serialized_actual_evidence(self):
        actor = Mock(side_effect=rich_child)
        teaching = rich.collect_teaching(0, self.collections[:4], actor)
        self.assertEqual(actor.call_count, 96)
        self.assertEqual((teaching['model_calls'], teaching['rich_calls'], teaching['critique_calls']), (96, 96, 0))
        self.assertEqual(teaching['phase'], 'teach')
        self.assertEqual(teaching['critiques'], [])
        self.assertEqual([capture['native_call_index'] for capture in teaching['captures']], list(range(96)))
        self.assertEqual(rich.replay_teaching(teaching), teaching['candidate_rows'])
        saved = json.loads(json.dumps(teaching))
        before = deepcopy(saved)
        critic = Mock(side_effect=critic_child)
        document = rich.collect_critiques(saved, critic)
        self.assertEqual(saved, before)
        self.assertEqual(critic.call_count, 16)
        self.assertEqual(document['model_calls'], 16)
        self.assertEqual(document['teaching_sha256'], teaching['lesson_sha256'])
        self.assertEqual([capture['native_call_index'] for capture in document['critiques']], list(range(16)))
        self.assertEqual(rich.replay_critiques(json.loads(json.dumps(document))), document['critiques'])
        self.assertFalse(document['fit_ready'] or document['controls_selection'])
        for capture in document['critiques']:
            self.assertNotIn(rich.PARENT_GUIDANCE, str(capture['messages']))
            self.assertNotIn('CAPTURED SOURCE EVENT (raw)', str(capture['messages']))
        forged = deepcopy(saved)
        forged['lesson_sha256'] = 'f' * 64
        unused = Mock(side_effect=critic_child)
        with self.assertRaises(ValueError):
            rich.collect_critiques(forged, unused)
        unused.assert_not_called()
        with self.assertRaises(ValueError):
            rich.replay_teaching(self.document)
        document['critiques'][0]['messages'][-1]['content'] += ' forged history'
        reseal(document, 'critique_collection_sha256')
        with self.assertRaises(ValueError):
            rich.replay_critiques(document)

    def test_split_phases_preserve_partial_zero_candidates_and_failed_critiques(self):
        for all_failed, expected_rows, expected_calls in ((False, 90, 91), (True, 0, 16)):
            with self.subTest(all_failed=all_failed):
                count = 0

                def actor(messages):
                    nonlocal count
                    count += 1
                    return generation('STOP', messages) if all_failed or count == 1 else rich_child(messages)

                teaching = rich.collect_teaching(0, self.collections[:4], actor)
                self.assertEqual(teaching['model_calls'], expected_calls)
                self.assertEqual(teaching['candidate_row_count'], expected_rows)
                self.assertEqual({form: len(rows) for form, rows in rich.replay_teaching(teaching).items()},
                                 dict.fromkeys(rich.FORMS, expected_rows))

                def critic(messages):
                    raise RuntimeError('actual separate critic failure')

                document = rich.collect_critiques(teaching, critic)
                self.assertEqual(document['model_calls'], 16)
                self.assertTrue(all(capture['validation_error'] for capture in rich.replay_critiques(document)))
                self.assertEqual(document['teaching']['candidate_rows'], teaching['candidate_rows'])
                self.assertFalse(document['fit_ready'] or teaching['fit_ready'])

    def test_no_future_read_source_or_recurrent_rationale_or_parent_in_student(self):
        for capture in self.document['captures']:
            public = capture['student_prefix']
            self.assertNotIn(rich.PARENT_GUIDANCE, str(public))
            self.assertNotIn('CAPTURED SOURCE EVENT (raw)', str(public))
            self.assertNotIn('I use the available public observations.', str(public))
            self.assertEqual([message['role'] for message in public],
                             ['system', 'user'] + ['assistant', 'user'] * capture['episode_call_index'])
            self.assertIn(rich.PARENT_GUIDANCE, capture['messages'][-1]['content'])
            if capture['episode_call_index'] < 4:
                self.assertNotIn('CAPTURED SOURCE EVENT (raw)', capture['messages'][-1]['content'])
                address = capture['projection']['action'].strip().split()[-1]
                store = rich.runtime(0)['exact_text_store'](self.collections[capture['world_index']])
                self.assertNotIn(store[address], str(capture['messages']))
            elif capture['episode_call_index'] == 4:
                self.assertEqual(capture['messages'][-1]['content'].count('CAPTURED SOURCE EVENT (raw)'), 2)

    def test_every_shard_public_runtime_and_no_probe_teacher_admission(self):
        for shard in rich.SHARDS:
            bound = rich.runtime(shard)
            worlds = self.registry[shard]
            source = rich.collect_world(worlds['TRAIN'][-1], exposed_child)
            self.assertEqual(source, rich.replay_collection(source))
            self.assertEqual(source['master'], bound['TRAIN_MASTERS'][-1])
            self.assertEqual(len(bound['build_cases'](source)['cases']), 4)
        for collections in (self.collections[:3], self.collections[:4][::-1],
                            self.collections[:3] + [self.collections[4]], self.collections[:3] + [self.collections[0]]):
            actor, critic = Mock(side_effect=rich_child), Mock(side_effect=critic_child)
            with self.assertRaises(ValueError):
                rich.collect_lessons(0, collections, actor, critic)
            actor.assert_not_called()
            critic.assert_not_called()

    def test_four_complete_shards_have_384_primary_rows_and_64_actual_critiques(self):
        documents = [self.document]
        for shard in rich.SHARDS[1:]:
            collections = [rich.collect_world(world, exposed_child) for world in self.registry[shard]['TRAIN']]
            document = rich.collect_lessons(shard, collections, rich_child, critic_child)
            self.assertEqual(rich.replay_lessons(document), document['rows'])
            documents.append(document)
        self.assertEqual(sum(document['rich_calls'] for document in documents), 384)
        self.assertEqual(sum(document['critique_calls'] for document in documents), 64)
        self.assertEqual(sum(document['model_calls'] for document in documents), 448)
        self.assertEqual(sum(document['planned_task_count'] for document in documents), 64)
        self.assertEqual(len({attempt['episode_id'] for document in documents for attempt in document['attempts']}), 64)
        self.assertEqual({form: sum(len(document['rows'][form]) for document in documents)
                          for form in rich.FORMS}, dict.fromkeys(rich.FORMS, 384))

    def test_failed_source_retains_other_candidates_and_wrong_goal_retains_no_candidates(self):
        collections = list(self.collections[:4])
        collections[-1] = rich.collect_world(self.registry[0]['TRAIN'][3],
                                             lambda messages: generation('STOP', messages))
        failed = rich.collect_lessons(0, collections, rich_child, critic_child)
        self.assertEqual((failed['rich_calls'], failed['critique_calls']), (72, 12))
        self.assertEqual(failed['collections'][-1], collections[-1])
        self.assertEqual({form: len(rows) for form, rows in rich.replay_lessons(failed).items()}, dict.fromkeys(rich.FORMS, 72))
        self.assertEqual((failed['planned_task_count'], failed['attempted_task_count']), (16, 12))
        self.assertEqual([attempt['status'] for attempt in failed['attempts'][-4:]], ['not_attempted_source_incomplete'] * 4)
        self.assertTrue(all(not attempt['attempted'] and not attempt['call_indexes'] for attempt in failed['attempts'][-4:]))
        self.assertEqual(len(rich.encode_paired_rows(failed['candidate_rows'], Tokenizer())['ledger']), 72)
        commands = []
        for collection in self.collections[:4]:
            cases = rich.runtime(0)['build_cases'](collection)['cases']
            for index in range(4):
                commands.extend(step['command'] for step in cases[index ^ 2]['plan'])
        pending = iter(commands)

        def actor(messages):
            response = rich_child(messages)
            response['raw'] = response['raw'].split('\nACTION\n')[0] + '\nACTION\n' + next(pending)
            return response

        wrong = rich.collect_lessons(0, self.collections[:4], actor, critic_child)
        self.assertEqual([capture['projection']['action'] for capture in wrong['captures']], commands)
        self.assertEqual((wrong['rich_calls'], wrong['critique_calls']), (96, 16))
        self.assertTrue(all(entry['episode']['route_calls'] == 2 and not entry['complete'] for entry in wrong['episodes']))
        self.assertEqual(rich.replay_lessons(wrong), dict.fromkeys(rich.FORMS, []))

    def test_native_protocol_strings_are_captured_replayed_and_source_bound(self):
        protocol = dict(rich.PROTOCOL, articulation=rich.ARTICULATION + ' Give relevant detail.')
        document = rich.collect_lessons(0, self.collections[:4], rich_child, critic_child, protocol=protocol)
        self.assertEqual(document['protocol'], protocol)
        self.assertIn('Give relevant detail.', document['captures'][0]['messages'][-1]['content'])
        self.assertNotIn('Give relevant detail.', str(document['rows']['RICH'][0]['prefix']))
        self.assertEqual(rich.replay_lessons(document), document['rows'])
        document['protocol']['articulation'] += ' drift'
        reseal(document, 'lesson_sha256')
        with self.assertRaises(ValueError):
            rich.replay_lessons(document)

    def test_negative_episodes_kept_other_candidates_retained_critics_not_used_as_scores(self):
        root = self.registry[0]['TRAIN'][3]['nodes'][0]

        def actor(messages):
            response = rich_child(messages)
            if root in messages[1]['content']:
                response['raw'] = 'STOP'
            return response

        document = rich.collect_lessons(0, self.collections[:4], actor,
            lambda messages: generation('Perfect success; train this now.', messages))
        self.assertFalse(document['ready'])
        self.assertEqual(document['rich_calls'], 76)
        self.assertEqual(document['critique_calls'], 16)
        self.assertEqual([capture['response']['raw'] for capture in document['captures'][-4:]], ['STOP'] * 4)
        self.assertTrue(all(capture['validation_error'] for capture in document['captures'][-4:]))
        self.assertEqual({form: len(rows) for form, rows in rich.replay_lessons(document).items()}, dict.fromkeys(rich.FORMS, 72))
        self.assertFalse(document['complete_corpus'] or document['fit_ready'])
        self.assertTrue(document['primary_rows_ready'])
        self.assertEqual([attempt['status'] for attempt in document['attempts'][-4:]], ['failed'] * 4)

    def test_future_ids_prediction_markers_native_bounds_and_failures_retained(self):
        root = self.registry[0]['TRAIN'][3]['nodes'][0]
        unseen = self.registry[0]['TRAIN'][3]['edges'][0]['receipt']
        for mutation in ('future', 'prediction', 'tokens', 'context', 'prompt', 'exception'):
            with self.subTest(mutation=mutation):
                def actor(messages):
                    response = rich_child(messages)
                    if root not in messages[1]['content']:
                        return response
                    if mutation == 'future':
                        response['raw'] = response['raw'].replace('available public observations', unseen)
                    elif mutation == 'prediction':
                        response['raw'] = response['raw'].replace('PREDICTION: ', '')
                    elif mutation == 'tokens':
                        response['token_ids'] = [1] * 513
                    elif mutation == 'context':
                        response['prompt_tokens'] = 2049
                    elif mutation == 'prompt':
                        response['messages'] = []
                    else:
                        raise RuntimeError('actual actor failure')
                    return response

                document = rich.collect_lessons(0, self.collections[:4], actor, critic_child)
                self.assertEqual(document['rich_calls'], 76)
                self.assertFalse(document['ready'])
                self.assertTrue(document['captures'][-1]['validation_error'])
                self.assertEqual({form: len(rows) for form, rows in rich.replay_lessons(document).items()},
                                 dict.fromkeys(rich.FORMS, 72))

    def test_one_failed_episode_keeps_its_successful_opposite_goal_and_exact_90_rows(self):
        call_count = 0

        def actor(messages):
            nonlocal call_count
            call_count += 1
            return generation('STOP', messages) if call_count == 5 else rich_child(messages)

        document = rich.collect_lessons(0, self.collections[:4], actor, critic_child)
        rows = rich.replay_lessons(document)
        self.assertEqual((document['rich_calls'], document['critique_calls']), (95, 16))
        self.assertEqual((document['planned_task_count'], document['attempted_task_count'],
                          document['complete_episode_count'], document['candidate_row_count']), (16, 16, 15, 90))
        self.assertFalse(document['complete_corpus'] or document['fit_ready'])
        self.assertTrue(document['candidate_rows_ready'])
        expected_ids = [episode['episode_id'] for episode in document['episodes'] if episode['complete']]
        self.assertNotIn(document['attempts'][0]['episode_id'], expected_ids)
        self.assertIn(document['attempts'][2]['episode_id'], expected_ids)
        for form in rich.FORMS:
            self.assertEqual([row['episode_id'] for row in rows[form]],
                             [episode_id for episode_id in expected_ids for unused in range(6)])
            self.assertEqual([row['row_index'] for row in rows[form]], list(range(90)))
            self.assertEqual([row['call_index'] for row in rows[form]], list(range(5, 95)))
            for row in rows[form]:
                self.assertEqual(row['call_sha256'], document['captures'][row['call_index']]['call_sha256'])
        encoded = rich.encode_paired_rows(rows, Tokenizer())
        self.assertEqual(len(encoded['ledger']), 90)
        for index in range(90):
            self.assertEqual(encoded['encoded']['RICH'][index].input_ids,
                             encoded['encoded']['RICH_ACTION_ONLY'][index].input_ids)
            self.assertEqual(encoded['encoded']['TERSE'][index].target_ids,
                             encoded['encoded']['RICH_ACTION_ONLY'][index].target_ids)
        for mutation in ('drop_episode', 'shuffle', 'admit_failed', 'alias', 'attempt'):
            with self.subTest(mutation=mutation):
                if mutation in ('alias', 'attempt'):
                    changed = deepcopy(document)
                    if mutation == 'alias':
                        changed['candidate_rows'] = {form: [] for form in rich.FORMS}
                    else:
                        changed['attempts'][0]['status'] = 'complete'
                    reseal(changed, 'lesson_sha256')
                    with self.assertRaises(ValueError):
                        rich.replay_lessons(changed)
                    continue
                changed = deepcopy(rows)
                for form in rich.FORMS:
                    if mutation == 'drop_episode':
                        changed[form] = changed[form][:-6]
                    elif mutation == 'shuffle':
                        changed[form][-12:] = changed[form][-6:] + changed[form][-12:-6]
                    else:
                        changed[form][0]['call_index'] = 0
                with self.assertRaises(ValueError):
                    rich.encode_paired_rows(changed, Tokenizer())

    def test_zero_actual_candidates_replay_and_encoding_need_their_evidence(self):
        document = rich.collect_lessons(0, self.collections[:4],
                                        lambda messages: generation('STOP', messages), critic_child)
        rows = rich.replay_lessons(document)
        self.assertEqual(rows, dict.fromkeys(rich.FORMS, []))
        self.assertEqual((document['rich_calls'], document['critique_calls'], document['candidate_row_count']), (16, 16, 0))
        self.assertEqual(document['planned_task_count'], 16)
        self.assertTrue(all(attempt['attempted'] and attempt['status'] == 'failed' for attempt in document['attempts']))
        self.assertFalse(document['primary_rows_ready'] or document['complete_corpus'] or document['fit_ready'])
        encoded = rich.encode_paired_rows(rows, Tokenizer(), document=document)
        self.assertEqual(encoded['encoded'], dict.fromkeys(rich.FORMS, ()))
        self.assertEqual(encoded['ledger'], [])
        with self.assertRaisesRegex(ValueError, 'empty_candidate_rows_require_document'):
            rich.encode_paired_rows(rows, Tokenizer())
        with self.assertRaises(ValueError):
            rich.encode_paired_rows(rows, Tokenizer(), document=self.document)

    def test_one_complete_episode_is_a_valid_six_row_candidate_corpus(self):
        call_count = 0

        def actor(messages):
            nonlocal call_count
            call_count += 1
            return rich_child(messages) if call_count <= 6 else generation('STOP', messages)

        document = rich.collect_lessons(0, self.collections[:4], actor, critic_child)
        self.assertEqual((document['rich_calls'], document['critique_calls']), (21, 16))
        self.assertEqual((document['complete_episode_count'], document['candidate_row_count']), (1, 6))
        self.assertFalse(document['complete_corpus'] or document['fit_ready'])
        self.assertEqual(rich.replay_lessons(document), document['candidate_rows'])
        result = rich.encode_paired_rows(document['candidate_rows'], Tokenizer())
        self.assertEqual({form: len(rows) for form, rows in result['encoded'].items()}, dict.fromkeys(rich.FORMS, 6))

    def test_all_sources_incomplete_preserves_sixteen_planned_not_actual_attempts(self):
        sources = [rich.collect_world(world, lambda messages: generation('STOP', messages))
                   for world in self.registry[0]['TRAIN']]
        actor, critic = Mock(side_effect=rich_child), Mock(side_effect=critic_child)
        document = rich.collect_lessons(0, sources, actor, critic)
        actor.assert_not_called()
        critic.assert_not_called()
        self.assertEqual(document['model_calls'], 0)
        self.assertEqual((document['planned_task_count'], document['attempted_task_count']), (16, 0))
        self.assertEqual(document['collections'], sources)
        self.assertTrue(all(attempt['status'] == 'not_attempted_source_incomplete' for attempt in document['attempts']))
        self.assertEqual(rich.replay_lessons(document), dict.fromkeys(rich.FORMS, []))

    def test_critic_failure_is_candidate_only_not_primary_selection(self):
        def critic(messages):
            raise RuntimeError('actual critic failed')

        document = rich.collect_lessons(0, self.collections[:4], rich_child, critic)
        self.assertTrue(document['ready'])
        self.assertEqual(document['critique_calls'], 16)
        self.assertTrue(all(capture['validation_error'] for capture in document['critiques']))
        self.assertEqual(document['critiques'][0]['error']['message'], 'actual critic failed')
        self.assertEqual(len(rich.replay_lessons(document)['TERSE']), 96)

    def test_replay_rejects_capture_projection_transition_critique_and_row_drift(self):
        for mutation in ('raw', 'projection', 'transition', 'critique', 'row', 'missing'):
            with self.subTest(mutation=mutation):
                document = deepcopy(self.document)
                if mutation == 'raw':
                    document['captures'][-1]['response']['raw'] = 'STOP'
                elif mutation == 'projection':
                    document['captures'][-1]['projection']['action'] = 'STOP'
                elif mutation == 'transition':
                    document['episodes'][-1]['episode']['routes'][-1]['destination'] = 'N_AAAAAAAAAA'
                elif mutation == 'critique':
                    document['critiques'][-1]['messages'][-1]['content'] += ' hidden guidance'
                elif mutation == 'row':
                    document['rows']['RICH_ACTION_ONLY'][-1]['supervision'] = 'ASSISTANT_AND_EOT'
                else:
                    document['captures'].pop()
                reseal(document, 'lesson_sha256')
                with self.assertRaises(ValueError):
                    rich.replay_lessons(document)

    def test_paired_encoder_exact_action_only_masks_full_inputs_and_ledger(self):
        tokenizer = Tokenizer()
        result = rich.encode_paired_rows(self.document['rows'], tokenizer)
        self.assertFalse(result['equal_compute_claim'])
        for index in range(96):
            terse, full, masked = [result['encoded'][form][index] for form in rich.FORMS]
            self.assertEqual(full.input_ids, masked.input_ids)
            action = self.document['rows']['TERSE'][index]['assistant']
            action_tokens = tuple(tokenizer.encode(action) + [tokenizer.eos_token_id])
            self.assertEqual(terse.target_ids, action_tokens)
            self.assertEqual(masked.target_ids, action_tokens)
            self.assertGreater(len(full.target_ids), len(masked.target_ids))
            for form, encoded in zip(rich.FORMS, (terse, full, masked)):
                active = [offset for offset, label in enumerate(encoded.labels) if label != -100]
                self.assertGreater(active[0], 0)
                self.assertEqual(active, list(range(active[0], active[0] + len(encoded.target_ids))))
                self.assertEqual(tuple(encoded.labels[offset] for offset in active), encoded.target_ids)
                self.assertEqual(encoded.labels[-1], -100)
                self.assertLessEqual(len(encoded.input_ids), 2048)
                self.assertEqual(result['ledger'][index]['forms'][form]['active_tokens'], len(active))
                self.assertNotIn(rich.PARENT_GUIDANCE, tokenizer.decode(encoded.input_ids))
        for mutation in ('missing', 'shuffled', 'injected'):
            rows = deepcopy(self.document['rows'])
            if mutation == 'missing':
                rows['TERSE'].pop()
            elif mutation == 'shuffled':
                rows['RICH'][-1], rows['RICH'][-2] = rows['RICH'][-2], rows['RICH'][-1]
            else:
                rows['RICH'][-1]['assistant'] += ' invented'
            with self.assertRaises(ValueError):
                rich.encode_paired_rows(rows, Tokenizer())

    def test_encoder_rejects_merged_action_boundary_special_tokens_and_context_overflow(self):
        for mutation in ('merged', 'special', 'context'):
            with self.subTest(mutation=mutation):
                tokenizer = Tokenizer()
                original = tokenizer.encode

                def encode(text, **kwargs):
                    values = original(text, **kwargs)
                    if mutation == 'merged' and 'RATIONALE\n' in text and '\nACTION\n' in text:
                        return values + [99]
                    if mutation == 'context' and text.startswith('<system>'):
                        return [99] * 2049 + values
                    return values

                tokenizer.encode = encode
                if mutation == 'special':
                    tokenizer.all_special_ids = [0, 1] + original('RATIONALE')
                with self.assertRaises(ValueError):
                    rich.encode_paired_rows(self.document['rows'], tokenizer)


class ActionFirstPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.collections = [rich.collect_world(world, exposed_child) for world in rich.build_worlds(0)['TRAIN']]
        cls.document = rich.collect_teaching(0, cls.collections, cls.natural_child,
                                             execution_policy=rich.ACTION_FIRST_V2)

    @staticmethod
    def natural_child(messages):
        return generation(rich_child(messages)['raw'].replace('PREDICTION: ', ''), messages)

    def test_v1_default_explicit_policy_and_failure_goldens_unchanged(self):
        self.assertEqual(rich.document_sha256(rich.PROTOCOL),
                         '96d1440fea071ea688fa038222470081ee1c4f3cb1a33c12a03190371209cd4b')
        taught = rich.collect_teaching(0, self.collections, rich_child)
        explicit = rich.collect_teaching(0, self.collections, rich_child, execution_policy=rich.STRICT_V1)
        self.assertEqual(taught, explicit)
        combined = rich.collect_lessons(0, self.collections, rich_child, critic_child)
        missing_label = rich.collect_teaching(0, self.collections, self.natural_child)
        for document, digest in (
            (taught, '44e5ef0e60a9cb7890e0b2940b19fa09e0f26ae59793d86a11e8b67f05b585ce'),
            (combined, '321753adce8edc07df5554d28bee7ceb3bea7f522addfe201466a61144be2136'),
            (missing_label, '78a1ceca5dfb96647ded2f2ebf586592f23061a691f26a10877f6cc7ba322082')):
            self.assertEqual(rich.document_sha256(document), digest)
            self.assertNotIn('execution_policy', document)
            self.assertEqual(rich.replay_lessons(document), document['rows'])
        self.assertEqual(missing_label['candidate_row_count'], 0)
        self.assertTrue(all(entry['episode']['memory_calls'] == 0 for entry in missing_label['episodes']))

    def test_missing_label_executes_all_planned_commands_but_no_semantic_admission(self):
        document = self.document
        self.assertEqual(document['execution_policy'], rich.ACTION_FIRST_V2)
        self.assertEqual(document['protocol'], rich.ACTION_FIRST_PROTOCOL)
        self.assertEqual((document['rich_calls'], document['critique_calls'], document['action_complete_count']), (96, 0, 16))
        self.assertTrue(document['complete_corpus'])
        self.assertFalse(document['fit_ready'] or document['reviewed'] or document['rationale_truth_verified'])
        for entry in document['episodes']:
            self.assertTrue(entry['action_complete'])
            self.assertEqual((entry['episode']['memory_calls'], entry['episode']['route_calls']), (4, 2))
            self.assertTrue(entry['episode']['reached_goal'])
        for capture in document['captures']:
            self.assertIsNone(capture['execution_error'])
            self.assertIsNone(capture['validation_error'])
            self.assertFalse(capture['prediction_label_present'])
            self.assertEqual(capture['content_findings'], [dict(type='ValueError', message='explicit_prediction_line_required')])
            self.assertEqual(capture['content_review_status'], 'UNREVIEWED')
            self.assertEqual(capture['response']['messages'], capture['messages'])
            self.assertNotIn(rich.PARENT_GUIDANCE, str(capture['student_prefix']))
            self.assertTrue(all(not message['content'].startswith('RATIONALE\n')
                                for message in capture['student_prefix'] if message['role'] == 'assistant'))
        rows = rich.replay_teaching(document)
        tokenizer = Tokenizer()
        encoded = rich.encode_paired_rows(rows, tokenizer)
        for form in rich.FORMS:
            self.assertEqual(len(rows[form]), 96)
            for row in rows[form]:
                self.assertTrue(row['candidate_only'])
                self.assertFalse(row['reviewed'] or row['fit_ready'])
                self.assertEqual(row['content_review_status'], 'UNREVIEWED')
                raw = document['captures'][row['call_index']]['response']['raw']
                if form != 'TERSE':
                    self.assertEqual(row['assistant'], raw)
            self.assertEqual(len(encoded['encoded'][form]), 96)
        for index in range(96):
            terse, full, masked = [encoded['encoded'][form][index] for form in rich.FORMS]
            self.assertEqual(terse.target_ids, masked.target_ids)
            self.assertEqual(full.input_ids, masked.input_ids)
            self.assertEqual(masked.labels[-1], -100)
            self.assertLessEqual(len(full.input_ids), 2048)

    def test_hallucinated_prose_and_parent_echo_flagged_without_execution_failure(self):
        for text, finding in (('I already saw receipt R_AAAAAAAAAA.', 'rationale_unseen_public_identifier'),
                              (rich.PARENT_GUIDANCE, 'rationale_parent_guidance_echo')):
            with self.subTest(finding=finding):
                def actor(messages):
                    response = rich_child(messages)
                    response['raw'] = response['raw'].replace('I use the available public observations.', text)
                    return response

                document = rich.collect_teaching(0, self.collections, actor, execution_policy=rich.ACTION_FIRST_V2)
                self.assertEqual(document['action_complete_count'], 16)
                self.assertEqual(document['candidate_row_count'], 96)
                for capture in document['captures']:
                    self.assertIsNone(capture['execution_error'])
                    self.assertTrue(capture['prediction_label_present'])
                    self.assertEqual(capture['content_findings'][0]['message'], finding)
                    self.assertNotIn(text, str([message for message in capture['student_prefix'] if message['role'] != 'system']))
                self.assertEqual(rich.replay_teaching(document), document['rows'])
                self.assertFalse(document['fit_ready'])

    def test_literal_label_is_diagnostic_never_a_semantic_pass(self):
        document = rich.collect_teaching(0, self.collections, rich_child, execution_policy=rich.ACTION_FIRST_V2)
        for capture in document['captures']:
            self.assertTrue(capture['prediction_label_present'])
            self.assertEqual(capture['content_findings'], [])
            self.assertFalse(capture['grounding']['factual_truth_verified'])
            self.assertEqual(capture['content_review_status'], 'UNREVIEWED')
        self.assertTrue(document['candidate_rows_ready'])
        self.assertFalse(document['fit_ready'])

    def test_native_and_action_failures_still_cannot_execute(self):
        for mutation in ('truncated', 'nonterminal', 'envelope', 'ambiguous', 'action', 'prompt', 'tokens', 'context'):
            with self.subTest(mutation=mutation):
                def actor(messages):
                    response = self.natural_child(messages)
                    if mutation == 'truncated':
                        response['truncated'] = True
                    elif mutation == 'nonterminal':
                        response['terminal'] = False
                    elif mutation == 'envelope':
                        response['raw'] = 'READ EVENT E_AAAAAAAAAA'
                    elif mutation == 'ambiguous':
                        response['raw'] += '\nACTION\nREAD EVENT E_AAAAAAAAAA'
                    elif mutation == 'action':
                        response['raw'] = response['raw'].split('\nACTION\n')[0] + '\nACTION\nSTOP'
                    elif mutation == 'prompt':
                        response['messages'] = []
                    elif mutation == 'tokens':
                        response['token_ids'] = [1] * 513
                    else:
                        response['prompt_tokens'] = 2049
                    return response

                document = rich.collect_teaching(0, self.collections, actor, execution_policy=rich.ACTION_FIRST_V2)
                self.assertEqual((document['rich_calls'], document['action_complete_count'], document['candidate_row_count']), (16, 0, 0))
                for entry in document['episodes']:
                    self.assertEqual((entry['episode']['memory_calls'], entry['episode']['route_calls']), (0, 0))
                    self.assertFalse(entry['action_complete'])
                for capture in document['captures']:
                    self.assertEqual(capture['execution_error'], capture['validation_error'])
                    self.assertIsNotNone(capture['execution_error'])
                self.assertEqual(rich.replay_teaching(document), dict.fromkeys(rich.FORMS, []))

    def test_replay_binds_policy_content_execution_raw_and_unreviewed_rows(self):
        for mutation in ('remove_policy', 'strict_policy', 'unknown_policy', 'content', 'label', 'execution', 'complete', 'raw', 'row'):
            with self.subTest(mutation=mutation):
                document = deepcopy(self.document)
                if mutation == 'remove_policy':
                    document.pop('execution_policy')
                elif mutation == 'strict_policy':
                    document['execution_policy'] = rich.STRICT_V1
                elif mutation == 'unknown_policy':
                    document['execution_policy'] = 'ACTION_FIRST_V3'
                elif mutation == 'content':
                    document['captures'][0]['content_findings'] = []
                    reseal(document['captures'][0], 'call_sha256')
                elif mutation == 'label':
                    document['captures'][0]['prediction_label_present'] = True
                elif mutation == 'execution':
                    document['captures'][0]['execution_error'] = dict(type='ValueError', message='invented')
                elif mutation == 'complete':
                    document['episodes'][0]['action_complete'] = False
                elif mutation == 'raw':
                    document['captures'][0]['response']['raw'] += '\n'
                else:
                    document['rows']['RICH'][0]['reviewed'] = True
                    reseal(document['rows']['RICH'][0], 'row_sha256')
                reseal(document, 'lesson_sha256')
                with self.assertRaises(ValueError):
                    rich.replay_teaching(document)

    def test_policy_is_explicit_closed_and_custom_protocol_replayed(self):
        callback = Mock(side_effect=self.natural_child)
        for invalid in (None, True, 'action_first_v2', 'UNKNOWN'):
            with self.subTest(policy=invalid), self.assertRaisesRegex(ValueError, 'known_rich_execution_policy_required'):
                rich.collect_teaching(0, self.collections, callback, execution_policy=invalid)
        callback.assert_not_called()
        protocol = deepcopy(rich.ACTION_FIRST_PROTOCOL)
        protocol['articulation'] += ' Keep observations and expectations distinct.'
        document = rich.collect_teaching(0, self.collections, self.natural_child,
            execution_policy=rich.ACTION_FIRST_V2, protocol=protocol)
        self.assertEqual(document['protocol'], protocol)
        self.assertEqual(rich.replay_teaching(document), document['rows'])
        strict = rich.collect_teaching(0, self.collections, self.natural_child, protocol=rich.ACTION_FIRST_PROTOCOL)
        self.assertNotIn('execution_policy', strict)
        self.assertEqual(strict['candidate_row_count'], 0)


if __name__ == '__main__':
    unittest.main()
