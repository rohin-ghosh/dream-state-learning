"""Pure goal-pair source, failure, paired-endpoint and masking proofs."""

from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import subprocess
import sys
import unittest
from unittest.mock import Mock

from organism_v6 import experienced_event_goal_pairs as pairs
from organism_v6 import experienced_event_two_hop as hop
from organism_v6 import experienced_event_two_hop_lesson as lesson
from tests.test_experienced_event_two_hop import exposed_child, generation
from tests.test_experienced_event_two_hop_lesson import Tokenizer


def coached_child(messages):
    command = messages[-1]['content'].split('Execute only this next command, then wait for actual feedback:\n')[1]
    return generation(command + '\n\n', messages)


def reseal(document, key):
    document.pop(key, None)
    document[key] = pairs.document_sha256(document)


class GoalPairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.worlds = pairs.build_worlds()
        cls.collections = [pairs.collect_world(world, exposed_child) for world in cls.worlds['TRAIN']]
        cls.document = pairs.collect_lessons(cls.collections, coached_child)

    def test_import_has_no_model_or_tokenizer_runtime(self):
        script = """
import builtins
original = builtins.__import__
def checked(name, *args, **kwargs):
    if name.split('.')[0] in ('torch', 'transformers', 'peft', 'tokenizers'):
        raise AssertionError(name)
    return original(name, *args, **kwargs)
builtins.__import__ = checked
from organism_v6 import experienced_event_goal_pairs
"""
        completed = subprocess.run([sys.executable, '-B', '-c', script], capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_four_closed_worlds_and_caller_old_identifiers_are_disjoint(self):
        self.assertEqual(pairs.TRAIN_MASTERS, ('ASTRA-GOALPAIR-20260914-V1-TRAIN-A', 'ASTRA-GOALPAIR-20260914-V1-TRAIN-B'))
        self.assertEqual(pairs.PROBE_MASTERS, ('ASTRA-GOALPAIR-20260914-V1-PROBE-A', 'ASTRA-GOALPAIR-20260914-V1-PROBE-B'))
        old_ids = pairs.identifiers(hop.build_world()) | pairs.identifiers(hop.build_world(hop.TRANSFER_MASTER))
        worlds = pairs.build_worlds(old_ids=old_ids)
        seen = set(old_ids)
        for world in worlds['TRAIN'] + worlds['PROBE']:
            identities = pairs.identifiers(world)
            self.assertEqual(len(identities), 17)
            self.assertTrue(identities.isdisjoint(seen))
            seen.update(identities)
            nodes = world['nodes']
            self.assertEqual([(edge['node'], edge['outcome']) for edge in world['edges']],
                             [(nodes[0], nodes[1]), (nodes[0], nodes[2]), (nodes[1], nodes[3]), (nodes[2], nodes[4])])
            for identity in identities:
                self.assertRegex(identity, r'^[NPER]_[A-Z2-7]{10}$')
        collision = worlds['PROBE'][1]['edges'][0]['receipt']
        with self.assertRaisesRegex(ValueError, 'identifier_collision'):
            pairs.build_worlds(old_ids={collision})
        for master in (hop.MASTER, hop.TRANSFER_MASTER, pairs.PREFIX + '-TRAIN-C', '', None):
            with self.subTest(master=master), self.assertRaises(ValueError):
                pairs.build_world(master)
        with self.assertRaises(ValueError):
            pairs.build_worlds(old_ids='not-a-set')

    def test_private_runtime_reuses_code_without_changing_frozen_globals(self):
        before = (hop.build_world(), hop.build_world(hop.TRANSFER_MASTER), hop.MASTER, hop.TRANSFER_MASTER,
                  lesson.TASK_INDEXES, lesson.MAX_ROWS, lesson.MAX_CALLS)
        with ThreadPoolExecutor(max_workers=4) as pool:
            collections = list(pool.map(lambda master: pairs.collect_world(pairs.build_world(master), exposed_child), pairs.MASTERS))
        for master, collection in zip(pairs.MASTERS, collections):
            runtime = pairs._runtime(master)
            self.assertEqual(collection, pairs.replay_collection(collection))
            self.assertEqual(collection['master'], master)
            for name in ('build_world', 'build_tasks', 'collect_world', 'replay_collection', '_run', 'replay_episode'):
                self.assertIs(runtime[name].__code__, getattr(hop, name).__code__)
                self.assertIsNot(runtime[name].__globals__, hop.__dict__)
            with self.assertRaises(ValueError):
                hop.validate_world(collection['world'])
        self.assertEqual(before, (hop.build_world(), hop.build_world(hop.TRANSFER_MASTER), hop.MASTER,
                                  hop.TRANSFER_MASTER, lesson.TASK_INDEXES, lesson.MAX_ROWS, lesson.MAX_CALLS))

    def test_source_replay_and_goal_pairs_have_identical_displays_opposite_ports(self):
        for collection in self.collections:
            self.assertEqual((collection['model_calls'], collection['accepted_events']), (8, 4))
            self.assertEqual(pairs.replay_collection(collection), collection)
            cases = pairs.build_cases(collection)['cases']
            store = pairs.exact_text_store(collection)
            for first_index, second_index in pairs.GOAL_PAIRS:
                first, second = cases[first_index], cases[second_index]
                self.assertNotEqual(first['task']['goal'], second['task']['goal'])
                self.assertEqual({key: value for key, value in first['task'].items() if key != 'goal'},
                                 {key: value for key, value in second['task'].items() if key != 'goal'})
                self.assertNotEqual(first['plan'][4]['command'], second['plan'][4]['command'])
                for case in (first, second):
                    self.assertEqual(case['plan'], lesson._plan(case['task'], store))
                    first_edge, second_edge = [hop.micro.parse_event_line(hop.micro.canonical_event(store[address]))
                                              for address in case['plan'][4]['source_events']]
                    self.assertEqual(first_edge['source'], case['task']['node'])
                    self.assertEqual(first_edge['destination'], second_edge['source'])
                    self.assertEqual(second_edge['destination'], case['task']['goal'])

    def test_complete_bundle_has_48_actual_targets_and_all_four_tasks_per_world(self):
        document = self.document
        self.assertTrue(document['ready'] and document['fit_ready'])
        self.assertEqual((document['fits'], document['model_calls'], document['expected_calls']), (0, 48, 48))
        self.assertEqual(len(document['episodes']), 8)
        self.assertEqual(Counter(capture['master'] for capture in document['captures']), dict.fromkeys(pairs.TRAIN_MASTERS, 24))
        self.assertEqual([capture['call_index'] for capture in document['captures']], list(range(48)))
        self.assertEqual(pairs.replay_lessons(document), document['rows'])
        for world_index in range(2):
            entries = [entry for entry in document['episodes'] if entry['world_index'] == world_index]
            self.assertEqual([entry['task_index'] for entry in entries], [0, 1, 2, 3])
            self.assertTrue(all(entry['complete'] and entry['failure'] is None for entry in entries))
            self.assertEqual(document['summaries'][world_index]['paired'], dict(correct=2, denominator=2))
        for row, capture in zip(document['rows'], document['captures']):
            self.assertEqual(row['assistant'], capture['response']['raw'])
            self.assertTrue(row['assistant'].endswith('\n\n'))
            self.assertEqual(row['prefix'], capture['student_prefix'])
            self.assertEqual(capture['response']['messages'], capture['messages'])
            self.assertEqual(row['loss_policy'], lesson.LOSS_POLICY)
            self.assertEqual(row['evidence_sha256'], document['evidence_sha256'])

    def test_guidance_sources_retained_only_in_evidence_not_student_sleep_bytes(self):
        encoded = pairs.encode_rows(self.document['rows'], tokenizer := Tokenizer())
        for row, capture, tokens in zip(self.document['rows'], self.document['captures'], encoded):
            self.assertIn(lesson.PARENT_GUIDANCE, capture['messages'][-1]['content'])
            for marker in (lesson.PARENT_GUIDANCE, 'CAPTURED SOURCE EVENT (raw)', 'Execute only this next command'):
                self.assertNotIn(marker, str(row['prefix']))
                self.assertNotIn(marker, tokenizer.decode(tokens.input_ids))
            self.assertEqual(capture['messages'][:-1], row['prefix'][:-1])
            self.assertEqual([message['role'] for message in row['prefix']],
                             ['system', 'user'] + ['assistant', 'user'] * row['episode_call_index'])
            if row['episode_call_index'] == 4:
                self.assertEqual(capture['messages'][-1]['content'].count('CAPTURED SOURCE EVENT (raw)'), 2)
        self.assertEqual(len(encoded), 48)

    def test_goal_independent_first_port_is_two_of_four_but_zero_of_two_pairs(self):
        for collection in self.collections:
            world = collection['world']
            store = pairs.exact_text_store(collection)
            records = [hop.micro.parse_event_line(hop.micro.canonical_event(raw)) for raw in store.values()]
            episodes = []
            for task in pairs.build_tasks(world):
                first = next(record for record in records if record['source'] == task['node'] and record['port'] == task['ports'][0])
                second = next(record for record in records if record['source'] == first['destination'])
                commands = iter(['READ EVENT ' + address for address in task['events']]
                                + ['ROUTE ' + first['port'], 'ROUTE ' + second['port']])
                episodes.append(pairs.run_episode(world, task, lambda messages: generation(next(commands), messages), store.__getitem__))
            summary = pairs.summarize_pairs(collection, episodes)
            self.assertEqual(summary['individual'], dict(correct=2, denominator=4))
            self.assertEqual(summary['paired'], dict(correct=0, denominator=2))
            for pair in summary['pairs']:
                self.assertFalse(pair['both_goals_correct'])
                self.assertFalse(pair['distinct_source_correct_first_ports'])
                self.assertTrue(pair['two_legal_commits'])

    def test_wrong_goal_actual_commands_and_real_dead_ends_are_preserved(self):
        commands = []
        for collection in self.collections:
            cases = pairs.build_cases(collection)['cases']
            for index in range(4):
                commands.extend(step['command'] for step in cases[index ^ 2]['plan'])
        pending = iter(commands)
        document = pairs.collect_lessons(self.collections, lambda messages: generation(next(pending), messages))
        self.assertEqual([capture['response']['raw'] for capture in document['captures']], commands)
        self.assertEqual(document['model_calls'], 48)
        self.assertFalse(document['ready'] or document['fit_ready'])
        self.assertEqual(pairs.replay_lessons(document), [])
        self.assertTrue(all(entry['failure'] == 'dead_end' and entry['episode']['route_calls'] == 2 for entry in document['episodes']))

    def test_malformed_second_world_keeps_first_world_evidence_but_emits_no_rows(self):
        count = 0

        def child(messages):
            nonlocal count
            count += 1
            return coached_child(messages) if count <= 24 else generation('STOP', messages)

        document = pairs.collect_lessons(self.collections, child)
        self.assertEqual(document['model_calls'], 28)
        self.assertFalse(document['fit_ready'])
        self.assertEqual(pairs.replay_lessons(document), [])
        self.assertTrue(all(entry['complete'] for entry in document['episodes'][:4]))
        self.assertTrue(all(capture['response']['raw'] == 'STOP' for capture in document['captures'][24:]))
        self.assertTrue(all(entry['failure'] == 'invalid_command' for entry in document['episodes'][4:]))

    def test_incomplete_source_skips_that_world_without_fabricating_feedback(self):
        failed = pairs.collect_world(self.worlds['TRAIN'][0], lambda messages: generation('STOP', messages))
        child = Mock(side_effect=coached_child)
        document = pairs.collect_lessons([failed, self.collections[1]], child)
        self.assertEqual(child.call_count, 24)
        self.assertEqual(document['collections'][0], failed)
        self.assertIsNone(document['summaries'][0])
        self.assertFalse(document['fit_ready'])
        self.assertEqual(pairs.replay_lessons(document), [])

    def test_probe_duplicate_missing_reordered_and_source_drift_reject_before_actor(self):
        probe = pairs.collect_world(self.worlds['PROBE'][0], exposed_child)
        drift = deepcopy(self.collections[0])
        drift['captures'][0]['response']['raw'] = 'ROUTE P_AAAAAAAAAA'
        for collections in ([probe, self.collections[1]], self.collections[:1], self.collections[::-1],
                            [self.collections[0]] * 2, [drift, self.collections[1]]):
            with self.subTest(masters=[collection['master'] for collection in collections]):
                actor = Mock(side_effect=coached_child)
                with self.assertRaises(ValueError):
                    pairs.collect_lessons(collections, actor)
                actor.assert_not_called()
        with self.assertRaisesRegex(ValueError, 'identifier_collision'):
            pairs.collect_lessons(self.collections, coached_child, old_ids={self.worlds['PROBE'][0]['nodes'][0]})

    def test_native_errors_prompt_drift_and_token_overruns_remain_captured(self):
        for mutation in ('exception', 'prompt', 'tokens', 'context', 'nonterminal'):
            with self.subTest(mutation=mutation):
                def child(messages):
                    if mutation == 'exception':
                        raise RuntimeError('actual captured child failure')
                    response = coached_child(messages)
                    if mutation == 'prompt':
                        response['messages'] = []
                    elif mutation == 'tokens':
                        response['token_ids'] = [1] * 161
                    elif mutation == 'context':
                        response['prompt_tokens'] = 2049
                    else:
                        response['terminal'] = False
                    return response

                document = pairs.collect_lessons(self.collections, child)
                self.assertFalse(document['fit_ready'])
                self.assertEqual(document['model_calls'], 8)
                self.assertEqual(pairs.replay_lessons(document), [])
                if mutation == 'exception':
                    self.assertEqual(document['captures'][0]['error']['message'], 'actual captured child failure')
                elif mutation == 'tokens':
                    self.assertEqual(len(document['captures'][0]['response']['token_ids']), 161)

    def test_tampered_prompts_responses_transitions_rows_and_missing_calls_fail_replay(self):
        for mutation in ('prompt', 'response', 'transition', 'row', 'missing'):
            with self.subTest(mutation=mutation):
                document = deepcopy(self.document)
                if mutation == 'prompt':
                    document['captures'][0]['messages'][-1]['content'] += ' altered'
                elif mutation == 'response':
                    document['captures'][0]['response']['raw'] = 'STOP'
                elif mutation == 'transition':
                    document['episodes'][0]['episode']['routes'][0]['destination'] = 'N_AAAAAAAAAA'
                elif mutation == 'row':
                    document['rows'][0]['prefix'][-1]['content'] += '\n' + lesson.PARENT_GUIDANCE
                else:
                    document['captures'].pop()
                reseal(document, 'lesson_sha256')
                with self.assertRaises(ValueError):
                    pairs.replay_lessons(document)

    def test_encoder_exact_actual_target_eot_history_and_suffix_masks(self):
        tokenizer = Tokenizer()
        encoded = pairs.encode_rows(self.document['rows'], tokenizer)
        for row, encoded_row in zip(self.document['rows'], encoded):
            target = tuple(tokenizer.encode(row['assistant']) + [tokenizer.eos_token_id])
            self.assertEqual(encoded_row.target_ids, target)
            active = [index for index, label in enumerate(encoded_row.labels) if label != -100]
            self.assertEqual(active, list(range(active[0], active[0] + len(target))))
            self.assertGreater(active[0], 0)
            self.assertEqual(tuple(encoded_row.labels[index] for index in active), target)
            self.assertTrue(all(encoded_row.input_ids[index] == encoded_row.labels[index] for index in active))
            self.assertEqual(encoded_row.labels[-1], -100)
            self.assertLessEqual(len(encoded_row.input_ids), 2048)
            self.assertLessEqual(len(target), 160)
        for rows in (self.document['rows'][:-1], self.document['rows'][24:], self.document['rows'][::-1]):
            with self.assertRaises(ValueError):
                pairs.encode_rows(rows, Tokenizer())
        changed = deepcopy(self.document['rows'])
        changed[12]['assistant'] = 'ROUTE P_AAAAAAAAAA'
        with self.assertRaises(ValueError):
            pairs.encode_rows(changed, Tokenizer())

    def test_encoder_rejects_special_eot_boundary_and_context_drift(self):
        for mutation in ('eot', 'template', 'context'):
            with self.subTest(mutation=mutation):
                tokenizer = Tokenizer()
                if mutation == 'eot':
                    tokenizer.eos_token = '<wrong>'
                else:
                    original = tokenizer.apply_chat_template

                    def template(messages, *, tokenize, add_generation_prompt, **kwargs):
                        value = original(messages, tokenize=tokenize, add_generation_prompt=add_generation_prompt, **kwargs)
                        if mutation == 'context':
                            return tokenizer.encode('X ' * 2049) + value if tokenize else 'X ' * 2049 + value
                        return value if add_generation_prompt or tokenize else value + 'bad suffix'

                    tokenizer.apply_chat_template = template
                with self.assertRaises(ValueError):
                    pairs.encode_rows(self.document['rows'], tokenizer)


if __name__ == '__main__':
    unittest.main()
