"""Synthetic CPU capture/replay tests, not evidence of native collection."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import subprocess
import sys
import unittest
from unittest.mock import Mock

from organism_v6 import experienced_event_goal_scale as scale
from organism_v6 import experienced_event_goal_breadth as breadth
from organism_v6 import experienced_event_goal_pairs as goal
from organism_v6 import experienced_event_two_hop as hop
from organism_v6 import experienced_event_two_hop_lesson as lesson
from tests.test_experienced_event_goal_pairs import coached_child, reseal
from tests.test_experienced_event_two_hop import exposed_child, generation
from tests.test_experienced_event_two_hop_lesson import Tokenizer


class GoalScaleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        old_worlds = [hop.build_world(), hop.build_world(hop.TRANSFER_MASTER)]
        old_worlds += [goal.build_world(master) for master in goal.MASTERS]
        old_worlds += [breadth.build_world(master) for master in breadth.MASTERS]
        cls.old_ids = set().union(*(scale.identifiers(world) for world in old_worlds))
        cls.registry = scale.validate_registry(old_ids=cls.old_ids)
        cls.collections, cls.documents = [], []
        for shard in scale.SHARDS:
            runtime = scale.runtime(shard)
            collections = [runtime['collect_world'](world, exposed_child, old_ids=cls.old_ids)
                           for world in cls.registry[shard]['TRAIN'] + cls.registry[shard]['PROBE']]
            cls.collections.append(collections)
            cls.documents.append(runtime['collect_lessons'](collections[:8], coached_child, old_ids=cls.old_ids))
        cls.aggregate = scale.aggregate_lessons(cls.documents)

    def test_import_without_model_tokenizer_or_torch(self):
        script = """
import builtins
original = builtins.__import__
def checked(name, *args, **kwargs):
    if name.split('.')[0] in ('torch', 'transformers', 'peft', 'tokenizers'):
        raise AssertionError(name)
    return original(name, *args, **kwargs)
builtins.__import__ = checked
from organism_v6 import experienced_event_goal_scale
"""
        completed = subprocess.run([sys.executable, '-B', '-c', script], capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_fixed_registry_64_train_16_probe_all_disjoint_including_old_ids(self):
        self.assertEqual(scale.SHARDS, tuple(range(8)))
        seen = set(self.old_ids)
        for shard, worlds in self.registry.items():
            runtime = scale.runtime(shard)
            self.assertEqual(runtime['PREFIX'], 'ASTRA-GOALSCALE-20260914-V1-SHARD-' + str(shard))
            self.assertEqual(worlds, scale.build_worlds(shard, old_ids=self.old_ids))
            self.assertEqual([len(worlds[split]) for split in ('TRAIN', 'PROBE')], [8, 2])
            self.assertEqual(tuple(world['master'] for world in worlds['TRAIN'] + worlds['PROBE']), runtime['MASTERS'])
            for world in worlds['TRAIN'] + worlds['PROBE']:
                identities = scale.identifiers(world)
                self.assertEqual(len(identities), 17)
                self.assertTrue(identities.isdisjoint(seen))
                seen.update(identities)
            with self.assertRaises(ValueError):
                runtime['build_world'](runtime['PREFIX'] + '-BLOCK-1-PROBE-A')
        self.assertEqual(len(seen - self.old_ids), 1360)
        for shard in scale.SHARDS:
            for split in ('TRAIN', 'PROBE'):
                collision = self.registry[shard][split][-1]['nodes'][0]
                with self.assertRaisesRegex(ValueError, 'identifier_collision'):
                    scale.build_worlds(0, old_ids=self.old_ids | {collision})
        for shard in (-1, 8, True, False, '0', None, 0.0):
            with self.subTest(shard=shard), self.assertRaises(ValueError):
                scale.runtime(shard)

    def test_shard_cache_binding_concurrent_dispatch_and_unchanged_originals(self):
        original_worlds = breadth.build_worlds()
        original_cache = breadth._block.cache_info()
        with ThreadPoolExecutor(max_workers=8) as pool:
            worlds = list(pool.map(lambda shard: scale.runtime(shard)['build_worlds'](), scale.SHARDS))
        self.assertEqual(worlds, list(self.registry.values()))
        caches = []
        for shard in scale.SHARDS:
            runtime = scale.runtime(shard)
            caches.append(runtime['_block'])
            self.assertIs(runtime['_block'].__wrapped__.__globals__, runtime)
            self.assertIs(runtime['_block'].__wrapped__.__code__, breadth._block.__wrapped__.__code__)
            for name in ('collect_world', 'replay_collection', 'build_cases', 'run_episode',
                         'collect_lessons', 'replay_lessons', 'encode_rows'):
                self.assertIs(runtime[name].__globals__, runtime)
                self.assertIs(runtime[name].__code__, getattr(breadth, name).__code__)
            with self.assertRaises(ValueError):
                runtime['build_world'](scale.runtime((shard + 1) % 8)['TRAIN_MASTERS'][0])
            self.assertEqual(runtime['CAPS'], scale.CAPS)
            self.assertEqual((runtime['EXPOSE_CALLS'], runtime['TEACH_CALLS'], runtime['BASELINE_CALLS'],
                              runtime['TOTAL_CALLS']), (80, 192, 288, 560))
        self.assertEqual(len(set(caches)), 8)
        self.assertEqual(breadth._block.cache_info(), original_cache)
        self.assertEqual(breadth.build_worlds(), original_worlds)
        self.assertEqual((breadth.PREFIX, breadth.MAX_ROWS, goal.MAX_ROWS, lesson.MAX_ROWS),
                         ('ASTRA-GOALBREADTH-20260914-V1', 192, 48, 12))

    def test_source_task_episode_apis_across_all_shards_and_probes(self):
        self.assertEqual(sum(collection['model_calls'] for shard in self.collections for collection in shard), 640)
        for shard in scale.SHARDS:
            runtime = scale.runtime(shard)
            for collection in self.collections[shard]:
                self.assertEqual(runtime['replay_collection'](collection, old_ids=self.old_ids), collection)
                self.assertEqual(collection['accepted_events'], 4)
                store = runtime['exact_text_store'](collection)
                cases = runtime['build_cases'](collection)['cases']
                self.assertEqual([case['task'] for case in cases], runtime['build_tasks'](collection['world']))
                episodes = []
                for case in cases:
                    commands = iter(step['command'] for step in case['plan'])
                    episode = runtime['run_episode'](collection['world'], case['task'],
                        lambda messages: generation(next(commands), messages), store.__getitem__)
                    self.assertEqual(runtime['replay_episode'](collection['world'], case['task'], episode), episode)
                    episodes.append(episode)
                summary = runtime['summarize_pairs'](collection, episodes)
                self.assertEqual(summary['paired'], dict(correct=2, denominator=2))

    def test_1536_actual_rows_order_hash_joins_and_target_bytes(self):
        document = self.aggregate
        self.assertEqual(scale.replay_lessons(document), document['rows'])
        self.assertEqual((document['model_calls'], document['expected_calls'], document['fits']), (1536, 1536, 0))
        self.assertEqual((scale.EXPOSE_CALLS, scale.TEACH_CALLS, scale.BASELINE_CALLS, scale.MAX_CALLS),
                         (640, 1536, 2304, 4480))
        self.assertTrue(document['fit_ready'])
        self.assertEqual(document['state_binding'], 'NATIVE_CALLER_REQUIRED_NOT_VERIFIED_HERE')
        self.assertEqual(document['old_ids'], sorted(self.old_ids))
        self.assertEqual(len(set(document['masters'])), 64)
        self.assertEqual([row['row_index'] for row in document['rows']], list(range(1536)))
        for index, row in enumerate(document['rows']):
            shard, local_index = divmod(index, 192)
            source = self.documents[shard]['rows'][local_index]
            self.assertEqual((row['shard'], row['shard_row_index']), (shard, local_index))
            self.assertEqual(row['shard_row_sha256'], source['row_sha256'])
            self.assertEqual(row['shard_evidence_sha256'], source['evidence_sha256'])
            self.assertEqual(row['evidence_sha256'], document['evidence_sha256'])
            self.assertEqual((row['assistant'], row['prefix'], row['call_sha256']),
                             (source['assistant'], source['prefix'], source['call_sha256']))
            self.assertIn(row['master'], scale.runtime(shard)['TRAIN_MASTERS'])

    def test_missing_duplicate_shuffled_and_probe_teaching_rejected(self):
        for documents in (self.documents[:-1], self.documents[::-1], self.documents[:-1] + [self.documents[0]]):
            with self.assertRaises(ValueError):
                scale.aggregate_lessons(documents)
        for shard in scale.SHARDS:
            runtime = scale.runtime(shard)
            for probe in self.collections[shard][8:]:
                child = Mock(side_effect=coached_child)
                with self.assertRaises(ValueError):
                    runtime['collect_lessons'](self.collections[shard][:7] + [probe], child)
                child.assert_not_called()

    def test_negative_shard_kept_but_no_aggregate_rows_admitted(self):
        documents = list(self.documents)
        runtime = scale.runtime(7)
        root = self.registry[7]['TRAIN'][7]['nodes'][0]

        def child(messages):
            return generation('STOP', messages) if root in messages[1]['content'] else coached_child(messages)

        failed = runtime['collect_lessons'](self.collections[7][:8], child, old_ids=self.old_ids)
        self.assertEqual(failed['model_calls'], 172)
        self.assertEqual([capture['response']['raw'] for capture in failed['captures'][-4:]], ['STOP'] * 4)
        self.assertFalse(failed['fit_ready'])
        self.assertEqual(runtime['replay_lessons'](failed), [])
        documents[7] = failed
        aggregate = scale.aggregate_lessons(documents)
        self.assertEqual(aggregate['shard_documents'][7], failed)
        self.assertEqual(aggregate['model_calls'], 1516)
        self.assertEqual(len(aggregate['shard_documents'][0]['rows']), 192)
        self.assertFalse(aggregate['fit_ready'])
        self.assertEqual(aggregate['rows'], [])
        self.assertEqual(scale.replay_lessons(aggregate), [])
        with self.assertRaises(ValueError):
            scale.encode_rows(aggregate['rows'], Tokenizer())

    def test_reseal_cannot_hide_last_shard_capture_or_global_row_drift(self):
        documents = list(self.documents)
        documents[-1] = deepcopy(documents[-1])
        documents[-1]['blocks'][-1]['captures'][-1]['response']['raw'] = 'STOP'
        reseal(documents[-1], 'lesson_sha256')
        with self.assertRaises(ValueError):
            scale.aggregate_lessons(documents)
        aggregate = deepcopy(self.aggregate)
        aggregate['rows'][-1]['prefix'][-1]['content'] += '\n' + lesson.PARENT_GUIDANCE
        reseal(aggregate, 'lesson_sha256')
        with self.assertRaises(ValueError):
            scale.replay_lessons(aggregate)

    def test_aggregate_encoder_exact_actual_targets_and_masks_without_hints(self):
        tokenizer = Tokenizer()
        encoded = scale.encode_rows(self.aggregate['rows'], tokenizer)
        self.assertEqual(len(encoded), 1536)
        for row, tokens in zip(self.aggregate['rows'], encoded):
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
            for marker in (lesson.PARENT_GUIDANCE, 'CAPTURED SOURCE EVENT (raw)', 'Execute only this next command'):
                self.assertNotIn(marker, tokenizer.decode(tokens.input_ids))
        for rows in (self.aggregate['rows'][:192], self.aggregate['rows'][:-1]):
            with self.assertRaises(ValueError):
                scale.encode_rows(rows, Tokenizer())
        shuffled = list(self.aggregate['rows'])
        shuffled[-1], shuffled[-2] = shuffled[-2], shuffled[-1]
        with self.assertRaises(ValueError):
            scale.encode_rows(shuffled, Tokenizer())


if __name__ == '__main__':
    unittest.main()
