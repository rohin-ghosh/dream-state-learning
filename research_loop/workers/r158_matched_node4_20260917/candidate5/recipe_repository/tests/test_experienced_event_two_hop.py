"""Adversarial CPU tests for public connected EVENT exposure and continuation."""

from copy import deepcopy
import json
import re
import unittest
from unittest.mock import patch

from organism_v6 import experienced_event_microloop as micro
from organism_v6 import experienced_event_two_hop as hop


def generation(raw, messages=None):
    result = dict(raw=raw, terminal=True, truncated=False)
    if messages is not None:
        result['messages'] = deepcopy(messages)
    return result


def exposed_child(messages, suffix='\n'):
    text = messages[-1]['content']
    if len(messages) == 2:
        port = re.search(r'^PORTS (P_[A-Z2-7]{10})$', text, re.MULTILINE).group(1)
        return generation('ROUTE ' + port + '\n', messages)
    receipt, source, port, destination = re.match(
        r'RECEIPT (R_[A-Z2-7]{10}) AT (N_[A-Z2-7]{10}) DID (P_[A-Z2-7]{10}) GOT (N_[A-Z2-7]{10})\n', text).groups()
    address = re.search(r'AVAILABLE EVENT ADDRESS (E_[A-Z2-7]{10})', text).group(1)
    return generation(f'EVENT {address} AT {source} DID {port} GOT {destination} EVIDENCE {receipt}' + suffix, messages)


class TwoHopTests(unittest.TestCase):
    def setUp(self):
        self.world = hop.build_world()
        self.tasks = hop.build_tasks(self.world)

    def test_fixed_topology_opaque_ids_and_goal_independent_displays(self):
        self.assertEqual(self.world, hop.build_world())
        nodes, edges = self.world['nodes'], self.world['edges']
        self.assertEqual([(edge['node'], edge['outcome']) for edge in edges],
                         [(nodes[0], nodes[1]), (nodes[0], nodes[2]), (nodes[1], nodes[3]), (nodes[2], nodes[4])])
        for edge in edges:
            for key, prefix in (('event', 'E'), ('node', 'N'), ('port', 'P'), ('outcome', 'N'), ('receipt', 'R')):
                self.assertRegex(edge[key], '^' + prefix + r'_[A-Z2-7]{10}$')
        self.assertEqual(len(self.tasks), 4)
        for task in self.tasks:
            self.assertEqual(set(task), {'node', 'goal', 'ports', 'events'})
            self.assertEqual(len(task['ports']), 2)
            self.assertEqual(set(task['events']), {edge['event'] for edge in edges})
        for key in ('ports', 'events'):
            self.assertEqual(self.tasks[0][key], self.tasks[2][key])
            self.assertEqual(self.tasks[1][key], self.tasks[3][key])
            self.assertEqual(self.tasks[0][key], list(reversed(self.tasks[1][key])))
        old = micro.build_bank(hop.MASTER)
        with self.assertRaises(ValueError):
            micro._check_bank([dict(fact, outcome=old[0]['node']) if index == 0 else fact
                               for index, fact in enumerate(old)])

    def test_collection_replays_actual_receipts_and_never_rewrites_text(self):
        original = deepcopy(self.world)
        for suffix in ('', '\n', '\n\n\n'):
            with self.subTest(suffix=repr(suffix)):
                record = hop.collect_world(self.world, lambda messages: exposed_child(messages, suffix))
                self.assertTrue(record['ready'])
                self.assertEqual((record['model_calls'], len(record['captures']), len(record['records']), record['fits']), (8, 8, 4, 0))
                self.assertEqual(hop.replay_collection(json.loads(json.dumps(record))), record)
                store = hop.exact_text_store(record)
                for index, source in enumerate(record['records']):
                    self.assertEqual(store[source['edge']['event']], source['event']['raw'])
                    self.assertEqual(source['canonical_event'], source['event']['raw'].rstrip('\n') + '\n')
                    action_prompt = record['captures'][2 * index]['messages']
                    self.assertNotIn(source['edge']['outcome'], str(action_prompt))
                    self.assertNotIn(source['edge']['receipt'], str(action_prompt))
                    self.assertIn(source['edge']['receipt'], record['captures'][2 * index + 1]['messages'][-1]['content'])
                self.assertNotIn('rows', record)
        self.assertEqual(self.world, original)

    def test_collection_retains_every_failed_attempt_without_fake_events(self):
        first = self.world['edges'][0]

        def invalid_action(messages):
            if len(messages) == 2 and first['port'] in messages[-1]['content']:
                return generation('ROUTE ' + self.world['edges'][1]['port'])
            return exposed_child(messages)

        record = hop.collect_world(self.world, invalid_action)
        self.assertFalse(record['ready'])
        self.assertEqual((record['model_calls'], record['accepted_events'], len(record['records'])), (7, 3, 4))
        self.assertIsNone(record['records'][0]['transition'])
        self.assertIsNone(record['records'][0]['event'])
        self.assertEqual(hop.replay_collection(record), record)
        with self.assertRaisesRegex(ValueError, 'four_source_valid'):
            hop.exact_text_store(record)

        def wrong_event(messages):
            response = exposed_child(messages)
            if len(messages) > 2:
                response['raw'] = response['raw'].replace('EVIDENCE ', 'EVIDENCE R_AAAAAAAAAA ')
            return response

        failed = hop.collect_world(self.world, wrong_event)
        self.assertEqual((failed['model_calls'], failed['accepted_events']), (8, 0))
        self.assertTrue(all(source['transition'] is not None and source['event'] is not None for source in failed['records']))
        self.assertEqual(hop.replay_collection(failed), failed)

    def test_goal_dependent_branch_for_both_goals_and_orders_in_one_context(self):
        collection = hop.collect_world(self.world, exposed_child)
        store = hop.exact_text_store(collection)
        first_ports = []
        for task in self.tasks:
            seen = []

            def actor(messages):
                seen.append(deepcopy(messages))
                read_count = sum(message['role'] == 'assistant' and message['content'].startswith('READ EVENT ')
                                 for message in messages)
                if read_count < 4:
                    return generation('READ EVENT ' + task['events'][read_count], messages)
                records = [micro.parse_event_line(message['content'][len('MEMORY RESULT\n'):]) for message in messages
                           if message['content'].startswith('MEMORY RESULT\n')]
                public = next(message['content'] for message in reversed(messages) if message['content'].startswith('ROUTE TASK\n'))
                current = re.search(r'^CURRENT (\S+)$', public, re.MULTILINE).group(1)
                goal = re.search(r'^GOAL (\S+)$', public, re.MULTILINE).group(1)
                possible = [record for record in records if record['source'] == current]
                chosen = next(record for record in possible if record['destination'] == goal or
                    any(other['source'] == record['destination'] and other['destination'] == goal for other in records))
                return generation('ROUTE ' + chosen['port'], messages)

            episode = hop.run_episode(self.world, task, actor, store.__getitem__)
            score = hop.score_episode(self.world, task, episode)
            self.assertTrue(score['strict_success'])
            self.assertEqual((episode['actor_calls'], episode['memory_calls'], episode['route_calls']), (6, 4, 2))
            first_ports.append(episode['routes'][0]['port'])
            self.assertEqual(hop.replay_episode(self.world, task, episode), episode)
            for index, messages in enumerate(seen):
                self.assertEqual(messages[0], seen[0][0])
                if index:
                    self.assertEqual(messages[:len(seen[index - 1])], seen[index - 1])
                public_views = [message['content'] for message in messages if message['content'].startswith('ROUTE TASK\n')]
                self.assertTrue(all('\nGOAL ' + task['goal'] + '\n' in text for text in public_views))
                self.assertTrue(all(forbidden not in text for text in public_views for forbidden in ('FOR ', 'WITNESS', 'TARGET', 'PATH')))
            self.assertEqual(episode['current'], task['goal'])
        self.assertEqual(first_ports[0], first_ports[1])
        self.assertEqual(first_ports[2], first_ports[3])
        self.assertNotEqual(first_ports[0], first_ports[2])

    def test_no_automatic_reads_and_wrong_branch_is_real_dead_end(self):
        task = self.tasks[2]
        ports = iter([self.world['edges'][0]['port'], self.world['edges'][2]['port']])
        episode = hop.run_episode(self.world, task, lambda messages: generation('ROUTE ' + next(ports)),
                                  lambda address: self.fail('automatic read'))
        self.assertEqual((episode['actor_calls'], episode['memory_calls'], episode['route_calls']), (2, 0, 2))
        self.assertEqual(episode['terminal_reason'], 'dead_end')
        self.assertEqual(episode['current'], self.world['nodes'][3])
        self.assertFalse(hop.score_episode(self.world, task, episode)['correct'])

    def test_false_memory_cannot_fabricate_state_or_transition(self):
        task = self.tasks[0]
        commands = iter(['READ EVENT ' + task['events'][0], 'ROUTE ' + self.world['edges'][2]['port']])
        false_text = 'CURRENT ' + self.world['nodes'][1] + '\nGOAL ' + task['goal'] + '\nFOR goal PATH witness'
        episode = hop.run_episode(self.world, task, lambda messages: generation(next(commands)), lambda address: generation(false_text))
        self.assertEqual(episode['terminal_reason'], 'invalid_route')
        self.assertEqual(episode['current'], task['node'])
        self.assertEqual(episode['route_calls'], 0)
        self.assertIn(dict(role='user', content='MEMORY RESULT\n' + false_text), episode['messages'])
        self.assertFalse(hop.score_episode(self.world, task, episode)['correct'])

    def test_invalid_duplicate_unknown_and_callback_failures_are_replayable(self):
        task = self.tasks[0]
        for sequence, reason in ((['STOP'], 'invalid_command'),
                ([' ROUTE ' + task['ports'][0]], 'invalid_command'),
                (['ROUTE P_AAAAAAAAAA'], 'invalid_route'),
                (['READ EVENT E_AAAAAAAAAA'], 'unsupported_address'),
                (['READ EVENT ' + task['events'][0]] * 2, 'duplicate_address')):
            with self.subTest(reason=reason):
                commands = iter(sequence)
                record = hop.run_episode(self.world, task, lambda messages: generation(next(commands)), lambda address: 'MISS')
                self.assertEqual(record['terminal_reason'], reason)
                self.assertEqual(hop.replay_episode(self.world, task, record), record)
                self.assertEqual(record['route_calls'], 0)
        for kind in ('actor', 'memory'):
            def failure(argument):
                raise RuntimeError('captured ' + kind + ' failure')
            record = hop.run_episode(self.world, task,
                failure if kind == 'actor' else lambda messages: generation('READ EVENT ' + task['events'][0]),
                failure if kind == 'memory' else lambda address: 'MISS')
            self.assertEqual(record['terminal_reason'], kind + '_callback_error')
            self.assertEqual(hop.replay_episode(self.world, task, record), record)
        failed = hop.collect_world(self.world, failure)
        self.assertEqual((failed['model_calls'], failed['accepted_events']), (4, 0))
        self.assertEqual(hop.replay_collection(failed), failed)
        self.assertTrue(all(capture['error']['type'] == 'RuntimeError' for capture in failed['captures']))

    def test_nonterminal_outputs_and_budget_have_no_extra_callbacks(self):
        task = self.tasks[0]
        for response in (dict(raw='ROUTE ' + task['ports'][0], terminal=False, truncated=True), None):
            record = hop.run_episode(self.world, task, lambda messages: response, lambda address: self.fail('read'))
            self.assertFalse(record['reached_goal'])
            self.assertEqual(record['actor_calls'], 1)
            self.assertEqual(hop.replay_episode(self.world, task, record), record)
            collection = hop.collect_world(self.world, lambda messages: response)
            self.assertEqual((collection['model_calls'], collection['accepted_events']), (4, 0))
            self.assertEqual(hop.replay_collection(collection), collection)
        commands = iter('READ EVENT ' + address for address in task['events'])
        with patch.object(hop, 'MAX_ACTOR_CALLS', 4):
            record = hop.run_episode(self.world, task, lambda messages: generation(next(commands)), lambda address: 'MISS')
            self.assertEqual((record['actor_calls'], record['memory_calls'], record['route_calls']), (4, 4, 0))
            self.assertEqual(record['terminal_reason'], 'actor_call_cap')
            self.assertFalse(hop.score_episode(self.world, task, record)['correct'])

    def test_replay_rejects_fabricated_transitions_prompts_and_success_flags(self):
        task = self.tasks[0]
        commands = iter(['ROUTE ' + self.world['edges'][0]['port'], 'ROUTE ' + self.world['edges'][2]['port']])
        record = hop.run_episode(self.world, task, lambda messages: generation(next(commands)), lambda address: 'MISS')
        for field in ('transition', 'prompt', 'score', 'hash'):
            changed = deepcopy(record)
            if field == 'transition':
                changed['routes'][0]['destination'] = task['goal']
            elif field == 'prompt':
                changed['traces'][0]['messages'][1]['content'] += '\nFOR ' + task['goal']
            elif field == 'score':
                changed['route_calls'] = 1
            else:
                changed['episode_sha256'] = 'forged'
            with self.subTest(field=field), self.assertRaises(ValueError):
                hop.score_episode(self.world, task, changed)
        collection = hop.collect_world(self.world, exposed_child)
        collection['captures'][1]['response']['raw'] += 'repaired'
        with self.assertRaises(ValueError):
            hop.replay_collection(collection)


if __name__ == '__main__':
    unittest.main()
