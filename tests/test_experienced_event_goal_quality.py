"""Synthetic CPU source failures and paired-quality filtering, not native data."""

from copy import deepcopy
from functools import lru_cache
import subprocess
import sys
import unittest

from organism_v6 import experienced_event_goal_quality as quality
from tests.test_experienced_event_two_hop import exposed_child, generation
from tests.test_experienced_event_goal_pairs import coached_child


@lru_cache(maxsize=1)
def fixtures():
    old_ids = {'E_A','N_B'}
    for worlds in quality.scale.breadth.build_worlds().values():
        for world in worlds:
            old_ids.update(quality.scale.identifiers(world))
    registry = quality.scale.validate_registry(old_ids=old_ids)
    exposures, teachings = [], {}
    for shard in range(8):
        goal = quality.runtime(shard)
        collections = []
        for world_index, world in enumerate(registry[shard]['TRAIN'] + registry[shard]['PROBE']):
            bad = (shard,world_index) in ((0,0),(1,8),(4,0),(6,0))

            def child(messages):
                response = exposed_child(messages)
                if bad and len(messages) == 4 and world['edges'][0]['event'] in response['raw']:
                    address = world['edges'][0]['event']
                    changed = address[:-1] + ('B' if address[-1] != 'B' else 'C')
                    response['raw'] = response['raw'].replace(address,changed)
                return response

            collections.append(goal.collect_world(world,child,old_ids=old_ids))
        ready = all(collection['ready'] for collection in collections)
        exposures.append(dict(collections=collections,source_ready=ready,
            case_failures=sum(not record['accepted'] for collection in collections for record in collection['records']),
            data_status='SOURCE_READY' if ready else 'PARTIAL_SOURCE_FAILURES'))
        if shard in quality.REUSED_SHARDS:
            call_index = 0

            def teacher(messages):
                nonlocal call_index
                response = coached_child(messages)
                if shard == 7 and call_index == 5:
                    response['raw'] = 'ROUTE P_AAAAAAAAAA\n\n'
                call_index += 1
                return response

            teachings[shard] = goal.collect_lessons(collections[:8],teacher,old_ids=old_ids)
    return dict(exposures=exposures,teachings=teachings,registry=registry,old_ids=sorted(old_ids))


def child(messages, **metadata):
    return coached_child(messages)


class QualityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = fixtures()

    def test_source_population_partial_probe_text_and_no_repair(self):
        plan = quality.source_plan(self.data['exposures'])
        self.assertEqual((len(plan['eligible_train']),len(plan['excluded_train']),len(plan['probes'])),(61,3,16))
        self.assertEqual([len(unit['masters']) for unit in plan['units']],[7,8,7,7])
        self.assertEqual((plan['original_train_tasks'],plan['source_eligible_train_tasks'],plan['source_excluded_train_tasks']),(256,244,12))
        self.assertEqual((plan['probe_goals'],plan['probe_pairs']),(64,32))
        partial = [probe for probe in plan['probes'] if not probe['source_ready']]
        self.assertEqual(len(partial),1)
        self.assertEqual(list(partial[0]['text'].values()).count(quality.UNAVAILABLE),1)
        source = self.data['exposures'][1]['collections'][8]
        for record in source['records']:
            self.assertEqual(partial[0]['text'][record['edge']['event']],record['event']['raw'] if record['accepted'] else quality.UNAVAILABLE)
        bad = deepcopy(self.data['exposures'])
        bad[0]['collections'][0]['records'][0]['accepted'] = True
        with self.assertRaises(ValueError):
            quality.source_plan(bad)
        with self.assertRaises(ValueError):
            quality.source_plan(self.data['exposures'][:-1])

    def test_reuses_756_actual_rows_without_promoting_old_failure(self):
        before = quality.document_sha256(self.data)
        reused = quality.reused_quality(self.data['exposures'],self.data['teachings'])
        self.assertEqual((len(reused['rows']),reused['reused_calls'],reused['new_calls']),(756,768,0))
        self.assertFalse(self.data['teachings'][7]['ready'])
        self.assertEqual(self.data['teachings'][7]['rows'],[])
        self.assertEqual(reused['original_statuses'][-1],dict(shard=7,ready=False,original_rows=0))
        master = quality.runtime(7).TRAIN_MASTERS[0]
        world = next(world for world in reused['worlds'] if world['master'] == master)
        self.assertEqual([pair['admitted'] for pair in world['pairs']],[False,True])
        self.assertEqual({row['task_index'] for row in world['rows']},{1,3})
        self.assertEqual(len(world['captures']),24)
        self.assertEqual(len([row for row in reused['rows'] if row['shard']==7]),180)
        for row in reused['rows']:
            capture = self.data['teachings'][row['shard']]['captures'][row['call_index']]
            self.assertEqual((row['prefix'],row['assistant']),(capture['student_prefix'],capture['response']['raw']))
            self.assertTrue(all(quality.lesson.PARENT_GUIDANCE not in message['content'] for message in row['prefix']))
            self.assertIn(quality.lesson.PARENT_GUIDANCE,capture['messages'][-1]['content'])
        self.assertEqual(quality.document_sha256(self.data),before)

    def test_new_units_exact_696_calls_1452_rows_and_fixed_order(self):
        calls, units = [], []

        def generate(messages, **metadata):
            calls.append(metadata)
            return child(messages,**metadata)

        for unit in quality.UNITS:
            document = quality.collect_unit(self.data['exposures'],unit,generate)
            self.assertEqual(document['model_calls'],quality.UNIT_CAPS[unit])
            self.assertEqual(len(document['rows']),quality.UNIT_CAPS[unit])
            units.append(document)
        self.assertEqual(len(calls),696)
        self.assertTrue(all(call['master'] in quality.runtime(unit).TRAIN_MASTERS for unit,document in zip(quality.UNITS,units)
                            for world in document['documents'] for call in world['evidence']['captures']))
        capsule = quality.assemble(self.data['exposures'],self.data['teachings'],units)
        self.assertEqual((capsule['row_count'],capsule['admitted_pairs'],capsule['rejected_eligible_pairs']),(1452,121,1))
        self.assertEqual((capsule['reused_calls'],capsule['new_calls']),(768,696))
        keys = [(row['shard'],row['world_index'],row['task_index'],row['episode_call_index']) for row in capsule['rows']]
        self.assertEqual(keys,sorted(keys))
        self.assertEqual([row['row_index'] for row in capsule['rows']],list(range(1452)))
        with self.assertRaisesRegex(ValueError,'all_four_ordered_quality_units_required'):
            quality.assemble(self.data['exposures'],self.data['teachings'],units[::-1])

    def test_native_error_rejects_pair_retains_attempts_and_replays(self):
        first = quality.source_plan(self.data['exposures'])['units'][0]['masters'][0]

        def failing(messages, **metadata):
            if metadata == dict(master=first,task_index=0,episode_call_index=0):
                raise RuntimeError('retained fixture native error')
            return child(messages,**metadata)

        document = quality.collect_unit(self.data['exposures'],0,failing)
        self.assertEqual((document['attempted_tasks'],document['model_calls'],document['native_error_calls']),(28,163,1))
        self.assertEqual((len(document['rows']),document['rejected_pairs']),(156,1))
        self.assertEqual(quality.replay_unit(self.data['exposures'],document),document)
        world = document['documents'][0]['quality']
        self.assertEqual({row['task_index'] for row in world['rows']},{1,3})
        self.assertEqual(world['episodes'][2]['complete'],True)
        self.assertEqual(world['captures'][0]['error']['message'],'retained fixture native error')
        altered = deepcopy(document)
        altered['documents'][0]['evidence']['captures'][0]['messages'][-1]['content'] += '\nforged'
        with self.assertRaises(ValueError):
            quality.replay_unit(self.data['exposures'],altered)
        for unit in (2,3,5,7,True):
            with self.assertRaises(ValueError):
                quality.collect_unit(self.data['exposures'],unit,child)

    def test_import_no_ml_runtime(self):
        script = '''
import builtins
original = builtins.__import__
def checked(name,*args,**kwargs):
    if name.split('.')[0] in ('torch','transformers','peft','tokenizers'):
        raise AssertionError(name)
    return original(name,*args,**kwargs)
builtins.__import__ = checked
from organism_v6 import experienced_event_goal_quality
'''
        result = subprocess.run([sys.executable,'-B','-c',script],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)


if __name__ == '__main__':
    unittest.main()
