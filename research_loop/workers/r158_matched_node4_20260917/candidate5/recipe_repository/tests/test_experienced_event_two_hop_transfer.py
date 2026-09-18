"""CPU transfer namespace checks; original goldens from 0b495971f8ecb2353162757abbdb938effa4493b.

The committed helper SHA256 was
6b825c63ad2b1fc96ed5cf87a1a11f186afa23a9bf358b05330caf87596ca441.
Goldens were computed from that committed source, not the extended helper.
"""

from copy import deepcopy
import json
from pathlib import Path
import unittest

from organism_v6 import experienced_event_two_hop as hop
from tests.test_experienced_event_two_hop import exposed_child, generation


GOLDENS = {
    'world': '93c7d0a36916423a916812a72da04b699e0b6c351b2f3fdeaf051cb5b0edab0d',
    'tasks': '03fe01114e307c4b89eb30ed907b15feaa1d44785eb29a2da60a5825e488bcf3',
    'collection': '72f5ed8fe52cefb67ff2ae160c68e309ccf18e56dc5a5ca069cb818519dfe6b3',
    'failed_collection': '72c02ef149d7b4254c8e36f53e9ec57efcdd7243fc172f1b49ab5f4323317c1e',
    'prompts': '4db53afa355270cc19db63090daae3e741ae8a5458f987f29cc3818621b086d0',
    'original': [
        'dc237100993bf07dc29f5237e41171f465ff4063e646dab56c3ebd84644ce431',
        '97cd0b0d018403976f2ec1bcaf3466f712cbf06f89963e8b9044087074c533d3',
        '419a4d468cc6644232e95d236563454cba98125a1211ec3850b54e33d5a2a353',
        'a79efcaec9bc6553077b10d491faacc3ff87c8c8325df8c62566b8328ab5285f'],
    'original_failed': [
        'fa3764e9886c886017ff57d28e99b01dc673d3eadea4cff518df36a3fbeb8674',
        '92b0220cddc71ac736272074cd9cc72bb72d4132f5407cfa69a0948e81e51d1f',
        'c61fae6d8cfab4b7eb45ff602207860ee6e21a28d1cb745285dee732d85a62df',
        '6dad98b92e3cf6bfa00ba5d1535068efb91b4d6c70f352c7e740fc8d3559f56b'],
    'turnbound': [
        '4357fa15d81f845b9dfc7984a728c93b37031da82a9ecf7e8a2fb439b02b7afa',
        '89935528331a34da47d6da8c1e5c59635d44775fcea31cedbf69c1904a74c891',
        '33577b9ba3f9a18177c1e4edff252b1feb0f0a6280b327a674c987a2ec2e01c7',
        'f328f6baf13a39b51622b80f70bdf7332449e2af1389864bef914350b44f7322'],
    'turnbound_failed': [
        'e42e6de0ec4e0b058922d90db4afe61c248255b7c98beb3d98f3026bb147a783',
        '22a3599260cfd6e3a5b7f146221b02a79051ef24b1329c73647bd5167c6503d2',
        '00abc1260df8b7fe0cb24c2f2327a84464f08e44c9d32a84368499900e8eed35',
        '7d96bb0467ea1b1ecfcc5e5e58a56bbbcfbff33d3a91c6237a2b063305d6affd'],
}
OLD_MASTERS = (
    'ASTRA-EXPERIENCED-EVENT-MICROLOOP-20260914-A1',
    'ASTRA-CUE-ADULT-CYCLE-20260914-A1',
    'ASTRA-CUE-ADULT-CYCLE-20260914-A2',
    'ASTRA-READER-AUDIT-CONTINUATION-20260914-A3',
)


def source_actor(messages):
    public = next(message['content'] for message in reversed(messages)
                  if message['content'].startswith('ROUTE TASK\n'))
    task = dict(line.split(' ', 1) for line in public.splitlines()[1:])
    records = [hop.micro.parse_event_line(hop.micro.canonical_event(message['content'][14:]))
               for message in messages if message['content'].startswith('MEMORY RESULT\n')]
    if len(records) < 4:
        return generation('READ EVENT ' + task['EVENTS'].split(',')[len(records)], messages)
    edge = next(record for record in records if record['source'] == task['CURRENT'] and
                (record['destination'] == task['GOAL'] or any(other['source'] == record['destination'] and
                 other['destination'] == task['GOAL'] for other in records)))
    return generation('ROUTE ' + edge['port'], messages)


def identities(world):
    return set(world['nodes']) | {value for edge in world['edges'] for value in edge.values()}


class TransferTests(unittest.TestCase):
    def setUp(self):
        self.original = hop.build_world()
        self.transfer = hop.build_world(hop.TRANSFER_MASTER)

    def test_original_default_world_prompts_collection_and_episode_goldens(self):
        self.assertEqual(self.original, hop.build_world(hop.MASTER))
        tasks = hop.build_tasks(self.original)
        self.assertEqual(hop.document_sha256(self.original), GOLDENS['world'])
        self.assertEqual(hop.document_sha256(tasks), GOLDENS['tasks'])
        self.assertEqual(hop.document_sha256(dict(protocols=hop.PROTOCOLS, collection=hop.COLLECTION_SYSTEM)),
                         GOLDENS['prompts'])
        collection = hop.collect_world(self.original, exposed_child)
        failed = hop.collect_world(self.original, lambda messages: generation('STOP', messages))
        self.assertEqual(collection['collection_sha256'], GOLDENS['collection'])
        self.assertEqual(failed['collection_sha256'], GOLDENS['failed_collection'])
        self.assertEqual(hop.replay_collection(collection), collection)
        self.assertEqual(hop.replay_collection(failed), failed)
        store = hop.exact_text_store(collection)
        for protocol in hop.PROTOCOLS:
            for index, task in enumerate(tasks):
                with self.subTest(protocol=protocol, task=index):
                    episode = hop.run_episode(self.original, task, source_actor, store.__getitem__, protocol=protocol)
                    failed = hop.run_episode(self.original, task, lambda messages: generation('STOP', messages),
                                             store.__getitem__, protocol=protocol)
                    self.assertEqual(episode['episode_sha256'], GOLDENS[protocol][index])
                    self.assertEqual(failed['episode_sha256'], GOLDENS[protocol + '_failed'][index])
                    self.assertEqual(hop.replay_episode(self.original, task, episode), episode)
                    self.assertEqual(hop.replay_episode(self.original, task, failed), failed)
                    if protocol == 'original':
                        self.assertEqual(hop.run_episode(self.original, task, source_actor, store.__getitem__), episode)

    def test_transfer_exact_topology_grammar_and_disjoint_source_namespaces(self):
        self.assertEqual(hop.TRANSFER_MASTER, 'ASTRA-EVENT-TWOHOP-TRAJECTORY-TRANSFER-20260914-V1')
        self.assertEqual(self.transfer, hop.build_world(master=hop.TRANSFER_MASTER))
        self.assertEqual(hop.validate_world(self.transfer), self.transfer)
        self.assertEqual(set(self.transfer), set(self.original))
        self.assertEqual(self.transfer['schema'], self.original['schema'])
        nodes, edges = self.transfer['nodes'], self.transfer['edges']
        self.assertEqual([(edge['node'], edge['outcome']) for edge in edges],
                         [(nodes[0], nodes[1]), (nodes[0], nodes[2]), (nodes[1], nodes[3]), (nodes[2], nodes[4])])
        for index, node in enumerate(nodes):
            self.assertEqual(node, hop.micro._opaque(hop.TRANSFER_MASTER, 'N', index))
        for index, edge in enumerate(edges):
            for key, prefix in (('node', 'N'), ('outcome', 'N'), ('port', 'P'), ('event', 'E'), ('receipt', 'R')):
                self.assertRegex(edge[key], '^' + prefix + r'_[A-Z2-7]{10}$')
                if key not in ('node', 'outcome'):
                    self.assertEqual(edge[key], hop.micro._opaque(hop.TRANSFER_MASTER, prefix, index))
        self.assertEqual(len(identities(self.transfer)), 17)
        self.assertTrue(identities(self.transfer).isdisjoint(identities(self.original)))
        old_bank = [fact for master in OLD_MASTERS for fact in hop.micro.build_bank(master)]
        self.assertEqual(len(old_bank), 16)
        self.assertEqual(len({fact['event'] for fact in old_bank}), 16)
        old_ids = {fact[key] for fact in old_bank for key in ('world', 'event', 'node', 'port', 'outcome', 'receipt')}
        self.assertTrue(identities(self.transfer).isdisjoint(old_ids))

    def test_sixteen_old_fact_namespaces_match_available_local_source_binding(self):
        root = Path(__file__).resolve().parents[1] / 'gpu_artifacts_local'
        directory = root / 'astra_fresh_reader_cycle_terminal_20260914_attempt2/extracted/collect'
        if not all((directory / name).is_file() for name in ('INPUTS.json', 'COLLECTION.json')):
            self.skipTest('local sixteen-fact source binding unavailable')
        binding = json.loads((directory / 'INPUTS.json').read_text())
        collection = json.loads((directory / 'COLLECTION.json').read_text())
        prior = [fact for master in OLD_MASTERS[:3] for fact in hop.micro.build_bank(master)]
        self.assertEqual(binding['prior_event_ids'], [fact['event'] for fact in prior])
        self.assertEqual(collection['bank'], hop.micro.build_bank(OLD_MASTERS[3]))
        self.assertEqual(collection['master'], binding['master'])
        self.assertTrue(identities(self.transfer).isdisjoint(
            fact[key] for fact in prior + collection['bank']
            for key in ('world', 'event', 'node', 'port', 'outcome', 'receipt')))

    def test_two_goals_common_displays_reversed_orders_and_opposite_first_ports(self):
        tasks = hop.build_tasks(self.transfer)
        self.assertEqual(len(tasks), 4)
        for order in (0, 1):
            self.assertEqual(tasks[order]['events'], tasks[order + 2]['events'])
            self.assertEqual(tasks[order]['ports'], tasks[order + 2]['ports'])
            self.assertNotEqual(tasks[order]['goal'], tasks[order + 2]['goal'])
        for start in (0, 2):
            self.assertEqual(tasks[start]['ports'], sorted(tasks[start]['ports']))
            self.assertEqual(tasks[start]['events'], sorted(tasks[start]['events']))
            for key in ('ports', 'events'):
                self.assertEqual(tasks[start + 1][key], list(reversed(tasks[start][key])))
        collection = hop.collect_world(self.transfer, exposed_child)
        store = hop.exact_text_store(collection)
        for protocol in hop.PROTOCOLS:
            first_ports = []
            for task in tasks:
                self.assertEqual(set(task), {'node', 'goal', 'ports', 'events'})
                episode = hop.run_episode(self.transfer, task, source_actor, store.__getitem__, protocol=protocol)
                self.assertEqual(hop.replay_episode(self.transfer, task, episode), episode)
                self.assertTrue(hop.score_episode(self.transfer, task, episode)['strict_success'])
                self.assertEqual((episode['actor_calls'], episode['memory_calls'], episode['route_calls']), (6, 4, 2))
                self.assertEqual(episode['fits'], 0)
                self.assertEqual(episode['messages'][0]['content'], hop.PROTOCOLS[protocol])
                first_ports.append(episode['routes'][0]['port'])
                for message in episode['messages']:
                    self.assertNotIn('PARENT', message['content'])
                    if message['content'].startswith('ROUTE TASK\n'):
                        fields = dict(line.split(' ', 1) for line in message['content'].splitlines()[1:])
                        self.assertEqual(set(fields), {'CURRENT', 'GOAL', 'PORTS', 'EVENTS'})
                        self.assertEqual(fields['GOAL'], task['goal'])
                memory = [trace for trace in episode['traces'] if trace['kind'] == 'memory']
                self.assertEqual([trace['address'] for trace in memory], task['events'])
                self.assertTrue(all(trace['response'] == store[trace['address']] for trace in memory))
            self.assertEqual(first_ports[0], first_ports[1])
            self.assertEqual(first_ports[2], first_ports[3])
            self.assertNotEqual(first_ports[0], first_ports[2])

    def test_actual_transfer_collection_binds_four_actions_and_exact_child_events(self):
        saved = []

        def child(messages):
            response = exposed_child(messages, suffix='\n\n')
            saved.append(dict(messages=deepcopy(messages), response=deepcopy(response), error=None))
            return response

        original = deepcopy(self.transfer)
        collection = hop.collect_world(self.transfer, child)
        self.assertEqual(self.transfer, original)
        self.assertEqual(collection['master'], hop.TRANSFER_MASTER)
        self.assertEqual(collection['world'], self.transfer)
        self.assertEqual(collection['world_sha256'], hop.document_sha256(self.transfer))
        self.assertEqual((collection['accepted_events'], collection['model_calls'], collection['fits']), (4, 8, 0))
        self.assertTrue(collection['ready'])
        self.assertFalse(collection['parent_present'])
        self.assertEqual([{key: capture[key] for key in ('messages', 'response', 'error')}
                          for capture in collection['captures']], saved)
        self.assertEqual(hop.replay_collection(collection), collection)
        store = hop.exact_text_store(collection)
        for index, record in enumerate(collection['records']):
            self.assertEqual(record['action'], saved[2 * index]['response'])
            self.assertEqual(record['event'], saved[2 * index + 1]['response'])
            self.assertEqual(store[record['edge']['event']], record['event']['raw'])
            self.assertTrue(record['event']['raw'].endswith('\n\n'))
            fields = hop.micro.parse_event_line(hop.micro.canonical_event(record['event']['raw']))
            self.assertEqual(fields, dict(event=record['edge']['event'], **record['transition']))

    def test_transfer_failures_replay_without_invented_events_or_routes(self):
        collection = hop.collect_world(self.transfer, lambda messages: generation('STOP', messages))
        self.assertEqual((collection['accepted_events'], collection['model_calls']), (0, 4))
        self.assertEqual(collection['master'], hop.TRANSFER_MASTER)
        self.assertEqual(hop.replay_collection(collection), collection)
        self.assertTrue(all(record['transition'] is None and record['event'] is None for record in collection['records']))
        with self.assertRaises(ValueError):
            hop.exact_text_store(collection)
        task = hop.build_tasks(self.transfer)[0]
        episode = hop.run_episode(self.transfer, task, lambda messages: generation('STOP', messages),
                                  lambda address: self.fail('no memory call'), protocol='turnbound')
        self.assertEqual(episode['routes'], [])
        self.assertEqual(episode['terminal_reason'], 'invalid_command')
        self.assertEqual(hop.replay_episode(self.transfer, task, episode), episode)

    def test_unknown_and_forged_worlds_rejected_before_callbacks(self):
        for master in ('arbitrary', hop.MASTER + '-RELABEL', '', None, 0, True, [], {}):
            with self.subTest(master=master), self.assertRaises(ValueError):
                hop.build_world(master)
        for value in (None, [], {}, {'master': 'arbitrary'}):
            with self.subTest(world=value), self.assertRaises(ValueError):
                hop.validate_world(value)
        for field in ('master', 'node', 'port', 'outcome', 'event', 'receipt', 'nodes', 'edges', 'extra'):
            world = deepcopy(self.transfer)
            if field == 'master':
                world['master'] = hop.MASTER
            elif field in ('nodes', 'edges'):
                world[field].reverse()
            elif field == 'extra':
                world['witness'] = 'forbidden'
            else:
                world['edges'][0][field] = self.original['edges'][0][field]
            with self.subTest(field=field), self.assertRaises(ValueError):
                hop.collect_world(world, lambda messages: self.fail('no callback on forged world'))

    def test_cross_world_collection_and_episode_relabel_rejected_even_resealed(self):
        original_collection = hop.collect_world(self.original, exposed_child)
        store = hop.exact_text_store(original_collection)
        original_task = hop.build_tasks(self.original)[0]
        transfer_task = hop.build_tasks(self.transfer)[0]
        episode = hop.run_episode(self.original, original_task, source_actor, store.__getitem__, protocol='turnbound')
        with self.assertRaises(ValueError):
            hop.run_episode(self.transfer, original_task, source_actor, store.__getitem__, protocol='turnbound')
        with self.assertRaises(ValueError):
            hop.replay_episode(self.transfer, transfer_task, episode)
        for mode in ('master_only', 'world_rebind', 'foreign_capture'):
            changed = deepcopy(original_collection)
            if mode == 'master_only':
                changed['master'] = hop.TRANSFER_MASTER
            else:
                changed['world'] = deepcopy(self.transfer)
                changed['master'] = hop.TRANSFER_MASTER
                changed['world_sha256'] = hop.document_sha256(self.transfer)
                if mode == 'foreign_capture':
                    changed = hop.collect_world(self.transfer, exposed_child)
                    changed['captures'][1] = deepcopy(original_collection['captures'][1])
            changed.pop('collection_sha256')
            changed = hop._seal(changed, 'collection_sha256')
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                hop.replay_collection(changed)
        changed = deepcopy(episode)
        changed.update(task=transfer_task, task_sha256=hop.document_sha256(transfer_task),
                       world_sha256=hop.document_sha256(self.transfer))
        changed.pop('episode_sha256')
        changed = hop._seal(changed, 'episode_sha256')
        with self.assertRaises(ValueError):
            hop.replay_episode(self.transfer, transfer_task, changed)


if __name__ == '__main__':
    unittest.main()
