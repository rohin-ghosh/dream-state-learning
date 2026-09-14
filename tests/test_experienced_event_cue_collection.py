from copy import deepcopy
import json
import unittest
from unittest.mock import Mock

from organism_v6 import experienced_event_cue_collection as cue
from organism_v6 import experienced_event_microloop as micro
from organism_v6 import experienced_event_read_route as controller


def generation(raw, **changes):
    return dict(dict(raw=raw, terminal=True, truncated=False), **changes)


class PublicReadingActor:
    def __init__(self):
        self.messages = []

    def __call__(self, messages):
        self.messages.append(deepcopy(messages))
        task = dict(line.split(' ', 1) for line in messages[1]['content'].splitlines()[1:])
        read = [message['content'].rstrip('\n').split(' ')[2] for message in messages
                if message['role'] == 'assistant' and message['content'].startswith('READ EVENT ')]
        for message in messages:
            if message['role'] == 'user' and message['content'].startswith('MEMORY RESULT\n'):
                event = micro.parse_event_line(micro.canonical_event(message['content'].split('\n', 1)[1]))
                if event['source'] == task['NODE'] and event['destination'] == task['GOAL']:
                    return generation('ROUTE ' + event['port'] + '\n\n', messages=deepcopy(messages))
        address = next(address for address in task['EVENTS'].split(',') if address not in read)
        return generation('READ EVENT ' + address + '\n', messages=deepcopy(messages))


class CueCollectionTests(unittest.TestCase):
    def setUp(self):
        self.bank = micro.build_bank('CUE-COLLECTION-CPU-TRAIN-A1')
        self.memory = {fact['event']: micro._event(fact).rstrip('\n') + '\n' * index
                       for index, fact in enumerate(self.bank)}

    def test_actual_read_route_all_pairs_student_history_replay(self):
        actor = PublicReadingActor()
        result = cue.run_collection(self.bank, self.memory, actor)
        self.assertEqual(result['status'], 'COLLECTION_COMPLETE_DRAFT_ONLY')
        self.assertEqual(result['completed_episodes'], 4)
        self.assertEqual(result['selected_episodes'], 4)
        self.assertEqual(result['selected_successes'], 4)
        self.assertEqual(result['native_actor_calls'], 10)
        self.assertEqual(result['physical_actor_calls'], 10)
        self.assertEqual(result['external_memory_calls'], 6)
        self.assertEqual(len(actor.messages), 10)
        self.assertEqual(len(result['student_rows']), 10)
        self.assertEqual(result['raw_memory_by_address'], self.memory)
        self.assertEqual(json.loads(json.dumps(result, allow_nan=False)), result)
        for row in result['student_rows']:
            call = result['actor_calls'][row['source_call_index']]
            self.assertEqual(row['prefix'], call['public_messages'])
            self.assertEqual(row['assistant'], call['response']['raw'])
            self.assertEqual(call['response']['messages'], call['guided_messages'])
            self.assertEqual(row['prefix'][0]['content'], controller.PUBLIC_SYSTEM)
            self.assertNotIn(cue.GUIDANCE, json.dumps(row['prefix']))
            self.assertEqual(row['target_eot'], '<|im_end|>')
            self.assertEqual(row['loss_policy'], {'prefix': 'MASK_ALL', 'assistant': 'TRAIN', 'eot': 'TRAIN'})
            self.assertEqual(call['guided_messages'][1:], call['public_messages'][1:])
        for record in result['episodes']:
            episode = record['episode']
            self.assertLessEqual(episode['action_calls'], 3)
            self.assertLessEqual(episode['memory_calls'], 2)
            self.assertEqual(set(record['task']), {'node', 'goal', 'ports', 'events'})
            for trace in episode['traces']:
                if trace['kind'] == 'memory':
                    self.assertEqual(trace['response']['raw'], self.memory[trace['address']])
                    self.assertEqual(trace['response']['source'], 'EXTERNAL_RETAINED_EVENT_TEXT_NOT_MODEL_GENERATION')

    def test_public_teacher_does_not_receive_hidden_mapping_or_target(self):
        actor = PublicReadingActor()
        result = cue.run_collection(self.bank, self.memory, actor)
        for record in result['episodes']:
            first = result['actor_calls'][record['call_start']]['guided_messages']
            self.assertEqual(first[0]['content'], controller.PUBLIC_SYSTEM + cue.GUIDANCE)
            for fact in self.bank:
                self.assertNotIn(fact['receipt'], json.dumps(first))
            self.assertEqual(len(first), 2)
        for start in (0, 2):
            first, second = [result['actor_calls'][record['call_start']]['guided_messages']
                             for record in result['episodes'][start:start + 2]]
            self.assertEqual(first[0], second[0])
            self.assertEqual(first[1]['content'].replace(self.bank[start]['outcome'], self.bank[start + 1]['outcome']),
                             second[1]['content'])

    def test_only_final_lf_changes_allowed_for_source_memory(self):
        for key in ('event', 'node', 'port', 'outcome', 'receipt'):
            memory = deepcopy(self.memory)
            memory[self.bank[0]['event']] = memory[self.bank[0]['event']].replace(self.bank[0][key], self.bank[2][key])
            actor = Mock()
            with self.subTest(key=key), self.assertRaises(ValueError):
                cue.run_collection(self.bank, memory, actor)
            actor.assert_not_called()
        for invalid in ('MISS', ' ' + micro._event(self.bank[0]), micro._event(self.bank[0]).rstrip() + '\r\n'):
            memory = dict(self.memory, **{self.bank[0]['event']: invalid})
            with self.assertRaises(ValueError):
                cue.run_collection(self.bank, memory, Mock())
        for memory in ({}, dict(self.memory, extra='value')):
            with self.assertRaisesRegex(ValueError, 'exact_four_memory'):
                cue.run_collection(self.bank, memory, Mock())

    def test_original_evaluation_bank_excluded_before_callbacks(self):
        bank = micro.build_bank(cue.EVALUATION_MASTER)
        memory = {fact['event']: micro._event(fact) for fact in bank}
        actor = Mock()
        with self.assertRaisesRegex(ValueError, 'exclude_original_evaluation'):
            cue.run_collection(bank, memory, actor)
        actor.assert_not_called()

    def test_correct_routes_without_reads_never_yield_rows(self):
        actor = Mock(side_effect=[generation('ROUTE ' + fact['port']) for fact in self.bank])
        result = cue.run_collection(self.bank, self.memory, actor)
        self.assertEqual(result['reached_goal_episodes'], 4)
        self.assertEqual(result['selected_episodes'], 0)
        self.assertEqual(result['student_rows'], [])
        self.assertEqual(result['external_memory_calls'], 0)
        self.assertEqual({record['classification'] for record in result['episodes']}, {'reached_goal_without_read'})

    def test_policy_generation_and_infrastructure_failures_are_separate(self):
        for response, classification in ((generation('MISS'), 'policy_failure'),
                (generation('READ EVENT ' + self.bank[0]['event'], truncated=True), 'generation_failure'),
                ({'raw': 'MISS'}, 'infrastructure_failure')):
            with self.subTest(classification=classification):
                result = cue.run_collection(self.bank, self.memory, Mock(return_value=response))
                self.assertEqual(len(result['episodes']), 4)
                self.assertEqual(result['native_actor_calls'], 4)
                self.assertEqual(result['student_rows'], [])
                self.assertEqual({record['classification'] for record in result['episodes']}, {classification})
                self.assertEqual(result['infrastructure_failures'], 4 if classification == 'infrastructure_failure' else 0)
        result = cue.run_collection(self.bank, self.memory, Mock(side_effect=RuntimeError('native callback failed')))
        self.assertEqual(result['status'], 'COLLECTION_FAILED_INFRASTRUCTURE')
        self.assertEqual(result['native_actor_calls'], 4)
        self.assertEqual(result['physical_actor_calls'], 4)
        self.assertEqual(result['selected_successes'], 0)
        self.assertTrue(all(call['error']['message'] == 'native callback failed' for call in result['actor_calls']))

    def test_duplicate_reads_and_wrong_route_keep_attempts_not_targets(self):
        calls = []
        for fact in self.bank:
            command = generation('READ EVENT ' + fact['public_events'][0])
            calls.extend([command, command])
        result = cue.run_collection(self.bank, self.memory, Mock(side_effect=calls))
        self.assertEqual(result['native_actor_calls'], 8)
        self.assertEqual(result['external_memory_calls'], 4)
        self.assertEqual(result['student_rows'], [])
        self.assertTrue(all(record['episode']['terminal_reason'] == 'duplicate_address' for record in result['episodes']))
        calls = []
        for fact in self.bank:
            wrong = next(port for port in fact['public_ports'] if port != fact['port'])
            calls.extend([generation('READ EVENT ' + fact['event']), generation('ROUTE ' + wrong)])
        result = cue.run_collection(self.bank, self.memory, Mock(side_effect=calls))
        self.assertEqual(result['reached_goal_episodes'], 0)
        self.assertEqual(result['student_rows'], [])
        self.assertEqual(len(result['episodes']), 4)

    def test_replay_rejects_changed_guided_source_or_memory(self):
        result = cue.run_collection(self.bank, self.memory, PublicReadingActor())
        record = result['episodes'][0]
        calls = deepcopy(result['actor_calls'][record['call_start']:record['call_end']])
        transitions = {fact['port']: fact['outcome'] for fact in self.bank if fact['node'] == record['task']['node']}
        calls[0]['guided_messages'][0]['content'] += ' forged'
        with self.assertRaisesRegex(ValueError, 'replay_mismatch'):
            cue._rows_from_success(record['task'], record['episode'], calls, self.memory, transitions, 0)
        calls = result['actor_calls'][record['call_start']:record['call_end']]
        changed = {address: raw + '\n' for address, raw in self.memory.items()}
        with self.assertRaisesRegex(ValueError, 'replay_mismatch'):
            cue._rows_from_success(record['task'], record['episode'], calls, changed, transitions, 0)


if __name__ == '__main__':
    unittest.main()
