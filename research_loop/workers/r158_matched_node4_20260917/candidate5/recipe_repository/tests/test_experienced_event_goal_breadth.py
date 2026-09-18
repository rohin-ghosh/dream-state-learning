"""CPU-only proofs for isolated breadth blocks and all-or-none actual targets."""

from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import subprocess
import sys
import unittest
from unittest.mock import Mock

from organism_v6 import experienced_event_goal_breadth as breadth
from organism_v6 import experienced_event_goal_pairs as goal
from organism_v6 import experienced_event_two_hop as hop
from organism_v6 import experienced_event_two_hop_lesson as lesson
from tests.test_experienced_event_goal_pairs import coached_child, reseal
from tests.test_experienced_event_two_hop import exposed_child, generation
from tests.test_experienced_event_two_hop_lesson import Tokenizer


class GoalBreadthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.worlds = breadth.build_worlds()
        cls.collections = [breadth.collect_world(world, exposed_child)
                           for world in cls.worlds['TRAIN'] + cls.worlds['PROBE']]
        cls.document = breadth.collect_lessons(cls.collections[:8], coached_child)

    def test_import_without_model_or_tokenizer_dependencies(self):
        script = """
import builtins
original = builtins.__import__
def checked(name, *args, **kwargs):
    if name.split('.')[0] in ('torch', 'transformers', 'peft', 'tokenizers'):
        raise AssertionError(name)
    return original(name, *args, **kwargs)
builtins.__import__ = checked
from organism_v6 import experienced_event_goal_breadth
"""
        completed = subprocess.run([sys.executable, '-B', '-c', script], capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_closed_ten_world_split_and_old_identifier_exclusion(self):
        old_worlds = [hop.build_world(), hop.build_world(hop.TRANSFER_MASTER)]
        old_worlds += [goal.build_world(master) for master in goal.MASTERS]
        old_ids = set().union(*(goal.identifiers(world) for world in old_worlds))
        worlds = breadth.build_worlds(old_ids=old_ids)
        self.assertEqual([len(worlds[split]) for split in ('TRAIN', 'PROBE')], [8, 2])
        self.assertEqual(breadth.PREFIX, 'ASTRA-GOALBREADTH-20260914-V1')
        seen = set(old_ids)
        for master, world in zip(breadth.MASTERS, worlds['TRAIN'] + worlds['PROBE']):
            identities = breadth.identifiers(world)
            self.assertEqual(len(identities), 17)
            self.assertTrue(identities.isdisjoint(seen))
            seen.update(identities)
            self.assertEqual(world['master'], master)
            self.assertEqual(world, breadth.validate_world(world, old_ids=old_ids))
        self.assertEqual(len(seen - old_ids), 170)
        for world in worlds['TRAIN'] + worlds['PROBE']:
            with self.assertRaisesRegex(ValueError, 'identifier_collision'):
                breadth.build_worlds(old_ids={world['nodes'][0]})
        rejected = list(goal.MASTERS) + [None, '', hop.MASTER]
        rejected += [prefix + '-PROBE-A' for prefix in breadth.BLOCK_PREFIXES[1:]]
        for master in rejected:
            with self.subTest(master=master), self.assertRaises(ValueError):
                breadth.build_world(master)
        with self.assertRaises(ValueError):
            breadth.build_worlds(old_ids='not-an-identifier-set')

    def test_private_cached_runtime_binding_and_concurrent_dispatch(self):
        before = (goal.build_worlds(), goal._runtime.cache_info(), hop.build_world(), lesson.MAX_ROWS)
        with ThreadPoolExecutor(max_workers=4) as pool:
            actual = list(pool.map(lambda master: breadth.collect_world(breadth.build_world(master), exposed_child),
                                   breadth.MASTERS))
        self.assertEqual(actual, self.collections)
        runtimes = []
        for index in range(4):
            block = breadth._block(index)
            runtime = block['_runtime']
            runtimes.append(runtime)
            self.assertIsNot(runtime, goal._runtime)
            self.assertIs(runtime.__wrapped__.__code__, goal._runtime.__wrapped__.__code__)
            self.assertIs(runtime.__wrapped__.__globals__, block)
            self.assertEqual(block['PROBE_MASTERS'], breadth.PROBE_MASTERS if index == 0 else ())
            self.assertIs(block['collect_lessons'].__code__, goal.collect_lessons.__code__)
            for master in block['MASTERS']:
                self.assertEqual(runtime(master)['build_world']()['master'], master)
                self.assertIs(runtime(master)['_run'].__code__, hop._run.__code__)
            with self.assertRaises(ValueError):
                runtime(breadth.TRAIN_MASTERS[2 * ((index + 1) % 4)])
        self.assertEqual(len(set(runtimes)), 4)
        self.assertEqual(before[1], goal._runtime.cache_info())
        self.assertEqual((before[0], before[2], before[3]),
                         (goal.build_worlds(), hop.build_world(), lesson.MAX_ROWS))

    def test_all_public_source_and_episode_apis_use_collection_master(self):
        self.assertEqual(sum(collection['model_calls'] for collection in self.collections), breadth.EXPOSE_CALLS)
        for collection in self.collections:
            self.assertEqual(breadth.replay_collection(collection), collection)
            self.assertEqual(collection['accepted_events'], 4)
            world = collection['world']
            store = breadth.exact_text_store(collection)
            cases = breadth.build_cases(collection)['cases']
            self.assertEqual([case['task'] for case in cases], breadth.build_tasks(world))
            episodes = []
            for case in cases:
                self.assertEqual(case['plan'], lesson._plan(case['task'], store))
                commands = iter(step['command'] for step in case['plan'])
                episode = breadth.run_episode(world, case['task'],
                    lambda messages: generation(next(commands), messages), store.__getitem__)
                self.assertEqual(episode, breadth.replay_episode(world, case['task'], episode))
                self.assertEqual(episode['protocol'], 'turnbound')
                episodes.append(episode)
            for first_index, second_index in breadth.GOAL_PAIRS:
                first, second = cases[first_index], cases[second_index]
                self.assertNotEqual(first['task']['goal'], second['task']['goal'])
                self.assertEqual({key: value for key, value in first['task'].items() if key != 'goal'},
                                 {key: value for key, value in second['task'].items() if key != 'goal'})
                self.assertNotEqual(first['plan'][4]['command'], second['plan'][4]['command'])
            summary = breadth.summarize_pairs(collection, episodes)
            self.assertEqual(summary['individual'], dict(correct=4, denominator=4))
            self.assertEqual(summary['paired'], dict(correct=2, denominator=2))
            self.assertTrue(all(pair['two_legal_commits'] and pair['distinct_source_correct_first_ports']
                                for pair in summary['pairs']))

    def test_complete_192_target_bundle_block_and_global_joins(self):
        document = self.document
        self.assertTrue(document['ready'] and document['fit_ready'])
        self.assertEqual((document['model_calls'], document['expected_calls'], document['fits']), (192, 192, 0))
        self.assertEqual((breadth.EXPOSE_CALLS, breadth.TEACH_CALLS, breadth.BASELINE_CALLS), (80, 192, 288))
        self.assertEqual((breadth.BASELINE_TRAIN_CALLS, breadth.BASELINE_PROBE_CALLS), (192, 96))
        self.assertEqual(breadth.replay_lessons(document), document['rows'])
        self.assertEqual(len(document['episodes']), 32)
        self.assertEqual(len(document['blocks']), 4)
        self.assertEqual(Counter(capture['master'] for capture in document['captures']),
                         dict.fromkeys(breadth.TRAIN_MASTERS, 24))
        self.assertEqual([capture['call_index'] for capture in document['captures']], list(range(192)))
        for block_index, block in enumerate(document['blocks']):
            self.assertEqual(block['model_calls'], 48)
            self.assertEqual(len(block['rows']), 48)
            self.assertEqual([collection['master'] for collection in block['collections']],
                             list(breadth.TRAIN_MASTERS[2 * block_index:2 * block_index + 2]))
        for world_index, summary in enumerate(document['summaries']):
            entries = [entry for entry in document['episodes'] if entry['world_index'] == world_index]
            self.assertEqual([entry['task_index'] for entry in entries], [0, 1, 2, 3])
            self.assertTrue(all(entry['complete'] and entry['failure'] is None for entry in entries))
            self.assertEqual(summary['paired'], dict(correct=2, denominator=2))
        for index, (row, capture) in enumerate(zip(document['rows'], document['captures'])):
            self.assertEqual(row['row_index'], index)
            self.assertEqual(row['call_index'], index)
            self.assertEqual(row['world_index'], index // 24)
            self.assertEqual(row['block_index'], index // 48)
            self.assertEqual(row['block_row_index'], index % 48)
            self.assertEqual(row['call_sha256'], capture['call_sha256'])
            original = document['blocks'][index // 48]['captures'][index % 48]
            self.assertEqual(row['block_call_sha256'], original['call_sha256'])
            self.assertEqual(capture['block_call_sha256'], original['call_sha256'])
            self.assertEqual(row['assistant'], capture['response']['raw'])
            self.assertTrue(row['assistant'].endswith('\n\n'))
            self.assertEqual(row['prefix'], capture['student_prefix'])
            self.assertEqual(capture['response']['messages'], capture['messages'])
            self.assertEqual(row['evidence_sha256'], document['evidence_sha256'])

    def test_goal_independent_first_port_fails_pairs_on_every_world(self):
        for collection in self.collections:
            world = collection['world']
            store = breadth.exact_text_store(collection)
            records = [hop.micro.parse_event_line(hop.micro.canonical_event(raw)) for raw in store.values()]
            episodes = []
            for task in breadth.build_tasks(world):
                first = next(record for record in records
                             if record['source'] == task['node'] and record['port'] == task['ports'][0])
                second = next(record for record in records if record['source'] == first['destination'])
                commands = iter(['READ EVENT ' + address for address in task['events']]
                                + ['ROUTE ' + first['port'], 'ROUTE ' + second['port']])
                episodes.append(breadth.run_episode(world, task,
                    lambda messages: generation(next(commands), messages), store.__getitem__))
            summary = breadth.summarize_pairs(collection, episodes)
            self.assertEqual(summary['individual'], dict(correct=2, denominator=4))
            self.assertEqual(summary['paired'], dict(correct=0, denominator=2))
            self.assertTrue(all(pair['two_legal_commits'] for pair in summary['pairs']))

    def test_invalid_source_in_last_block_rejected_before_any_actor_call(self):
        sources = self.collections[:8]
        drift = deepcopy(sources[-1])
        drift['captures'][0]['response']['raw'] = 'STOP'
        invalid = [sources[:-1], sources[::-1], sources[:-1] + [sources[0]],
                   sources[:-1] + [self.collections[8]], sources[:-1] + [drift]]
        for collections in invalid:
            child = Mock(side_effect=coached_child)
            with self.assertRaises(ValueError):
                breadth.collect_lessons(collections, child)
            child.assert_not_called()
        child = Mock(side_effect=coached_child)
        with self.assertRaisesRegex(ValueError, 'identifier_collision'):
            breadth.collect_lessons(sources, child, old_ids={self.worlds['PROBE'][1]['nodes'][0]})
        child.assert_not_called()

    def test_failed_source_keeps_all_blocks_and_no_partial_admission(self):
        sources = list(self.collections[:8])
        sources[4] = breadth.collect_world(self.worlds['TRAIN'][4], lambda messages: generation('STOP', messages))
        child = Mock(side_effect=coached_child)
        document = breadth.collect_lessons(sources, child)
        self.assertEqual(child.call_count, 168)
        self.assertEqual(document['model_calls'], 168)
        self.assertEqual(document['collections'][4], sources[4])
        self.assertIsNone(document['summaries'][4])
        self.assertEqual([block['fit_ready'] for block in document['blocks']], [True, True, False, True])
        self.assertEqual(len(document['blocks'][3]['rows']), 48)
        self.assertFalse(document['fit_ready'])
        self.assertEqual(document['rows'], [])
        self.assertEqual(breadth.replay_lessons(document), [])

    def test_malformed_child_preserved_and_later_blocks_still_collected(self):
        root = self.worlds['TRAIN'][4]['nodes'][0]

        def child(messages):
            return generation('STOP', messages) if root in messages[1]['content'] else coached_child(messages)

        document = breadth.collect_lessons(self.collections[:8], child)
        self.assertEqual(document['model_calls'], 172)
        failed = [capture for capture in document['captures'] if capture['world_index'] == 4]
        self.assertEqual([capture['response']['raw'] for capture in failed], ['STOP'] * 4)
        self.assertEqual([block['fit_ready'] for block in document['blocks']], [True, True, False, True])
        self.assertEqual(document['captures'][-1]['world_index'], 7)
        self.assertEqual(document['captures'][-1]['call_index'], 171)
        self.assertFalse(document['fit_ready'])
        self.assertEqual(breadth.replay_lessons(document), [])

    def test_legal_wrong_goal_actual_trajectories_never_repaired(self):
        commands = []
        for collection in self.collections[:8]:
            cases = breadth.build_cases(collection)['cases']
            for index in range(4):
                commands.extend(step['command'] for step in cases[index ^ 2]['plan'])
        pending = iter(commands)
        document = breadth.collect_lessons(self.collections[:8], lambda messages: generation(next(pending), messages))
        self.assertEqual([capture['response']['raw'] for capture in document['captures']], commands)
        self.assertEqual(document['model_calls'], 192)
        self.assertFalse(document['fit_ready'])
        self.assertTrue(all(not entry['complete'] and entry['failure'] for entry in document['episodes']))
        self.assertTrue(all(entry['episode']['route_calls'] == 2 for entry in document['episodes']))
        self.assertEqual(breadth.replay_lessons(document), [])

    def test_late_native_errors_and_bounds_preserved_without_partial_rows(self):
        root = self.worlds['TRAIN'][7]['nodes'][0]
        for mutation in ('exception', 'prompt', 'tokens', 'context'):
            with self.subTest(mutation=mutation):
                def child(messages):
                    response = coached_child(messages)
                    if root not in messages[1]['content']:
                        return response
                    if mutation == 'exception':
                        raise RuntimeError('actual last-world child failure')
                    if mutation == 'prompt':
                        response['messages'] = []
                    elif mutation == 'tokens':
                        response['token_ids'] = [1] * 161
                    else:
                        response['prompt_tokens'] = 2049
                    return response

                document = breadth.collect_lessons(self.collections[:8], child)
                self.assertEqual(document['model_calls'], 172)
                self.assertFalse(document['fit_ready'])
                capture = document['captures'][-1]
                if mutation == 'exception':
                    self.assertEqual(capture['error']['message'], 'actual last-world child failure')
                elif mutation == 'prompt':
                    self.assertEqual(capture['response']['messages'], [])
                elif mutation == 'tokens':
                    self.assertEqual(len(capture['response']['token_ids']), 161)
                else:
                    self.assertEqual(capture['response']['prompt_tokens'], 2049)
                self.assertEqual(breadth.replay_lessons(document), [])

    def test_outer_reseal_cannot_hide_late_block_or_projection_drift(self):
        for mutation in ('block', 'response', 'transition', 'capture', 'row', 'missing', 'old_ids', 'source'):
            with self.subTest(mutation=mutation):
                document = deepcopy(self.document)
                if mutation == 'block':
                    document['blocks'][2], document['blocks'][3] = document['blocks'][3], document['blocks'][2]
                elif mutation == 'response':
                    document['blocks'][3]['captures'][-1]['response']['raw'] = 'STOP'
                elif mutation == 'transition':
                    document['blocks'][3]['episodes'][-1]['episode']['routes'][0]['destination'] = 'N_AAAAAAAAAA'
                elif mutation == 'capture':
                    document['captures'][-1]['messages'][-1]['content'] += ' changed'
                elif mutation == 'row':
                    document['rows'][-1]['assistant'] = 'STOP'
                elif mutation == 'missing':
                    document['blocks'].pop()
                elif mutation == 'old_ids':
                    document['blocks'][3]['old_ids'] = ['N_AAAAAAAAAA']
                else:
                    document['blocks'][3]['collections'][-1] = deepcopy(self.collections[9])
                reseal(document, 'lesson_sha256')
                with self.assertRaises(ValueError):
                    breadth.replay_lessons(document)

    def test_encoder_actual_target_eot_only_and_all_student_guidance_removed(self):
        tokenizer = Tokenizer()
        encoded = breadth.encode_rows(self.document['rows'], tokenizer)
        self.assertEqual(len(encoded), 192)
        for row, capture, tokens in zip(self.document['rows'], self.document['captures'], encoded):
            self.assertIn(lesson.PARENT_GUIDANCE, capture['messages'][-1]['content'])
            for marker in (lesson.PARENT_GUIDANCE, 'CAPTURED SOURCE EVENT (raw)', 'Execute only this next command'):
                self.assertNotIn(marker, str(row['prefix']))
                self.assertNotIn(marker, tokenizer.decode(tokens.input_ids))
            if row['episode_call_index'] == 4:
                self.assertEqual(capture['messages'][-1]['content'].count('CAPTURED SOURCE EVENT (raw)'), 2)
            self.assertEqual([message['role'] for message in row['prefix']],
                             ['system', 'user'] + ['assistant', 'user'] * row['episode_call_index'])
            target = tuple(tokenizer.encode(row['assistant']) + [tokenizer.eos_token_id])
            self.assertEqual(tokens.target_ids, target)
            active = [index for index, label in enumerate(tokens.labels) if label != -100]
            self.assertGreater(active[0], 0)
            self.assertEqual(active, list(range(active[0], active[0] + len(target))))
            self.assertEqual(tuple(tokens.labels[index] for index in active), target)
            self.assertTrue(all(tokens.input_ids[index] == tokens.labels[index] for index in active))
            self.assertEqual(tokens.labels[-1], -100)
            self.assertLessEqual(len(tokens.input_ids), 2048)
            self.assertLessEqual(len(target), 160)
        for rows in (self.document['rows'][:48], self.document['rows'][:-1], self.document['rows'][::-1]):
            with self.assertRaises(ValueError):
                breadth.encode_rows(rows, Tokenizer())
        changed = deepcopy(self.document['rows'])
        changed[-1]['assistant'] = 'STOP'
        with self.assertRaises(ValueError):
            breadth.encode_rows(changed, Tokenizer())


if __name__ == '__main__':
    unittest.main()
