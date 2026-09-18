import json
from copy import deepcopy
import unittest
from unittest.mock import Mock, patch

from organism_v6 import experienced_event_microloop as micro
from organism_v6 import experienced_event_read_route as route


def generation(raw, **fields):
    return dict(raw=raw, terminal=True, truncated=False, **fields)


class ReadRouteTests(unittest.TestCase):
    def setUp(self):
        self.bank = micro.build_bank('scripted-read-route')
        self.fact = self.bank[0]
        self.task = route.public_task(self.fact)

    def test_public_projection_and_goal_pair_have_no_hidden_fields(self):
        self.assertEqual(set(self.task), {'node', 'goal', 'ports', 'events'})
        other = route.public_task(self.bank[1])
        self.assertEqual({key: value for key, value in self.task.items() if key != 'goal'},
                         {key: value for key, value in other.items() if key != 'goal'})
        actor = Mock(return_value=generation('ROUTE ' + self.fact['port']))
        result = route.run_episode(self.task, actor, Mock(), lambda port: self.fact['outcome'])
        messages = actor.call_args.args[0]
        self.assertEqual(len(actor.call_args.args), 1)
        self.assertEqual(messages[0]['content'], route.PUBLIC_SYSTEM)
        self.assertNotIn(self.fact['receipt'], json.dumps(messages))
        self.assertNotIn('correctport', json.dumps(messages))
        self.assertTrue(result['reached_goal'])
        self.task['ports'].clear()
        self.assertEqual(len(self.fact['public_ports']), 2)
        with self.assertRaisesRegex(ValueError, 'public_task_keys'):
            route.run_episode(dict(other, correctport=self.fact['port']), Mock(), Mock(), Mock())

    def test_read_then_route_actual_raw_flags_and_commit_before_transition(self):
        command = 'READ EVENT ' + self.fact['event'] + '\n\n'
        memory_raw = '  actual malformed memory\r\nNO REPAIR\n\n'
        seen = []

        def actor(messages):
            seen.append(deepcopy(messages))
            if len(seen) == 1:
                return generation(command, native={'tokens': [1, 2]})
            self.assertEqual(messages[-2], dict(role='assistant', content=command))
            self.assertEqual(messages[-1], dict(role='user', content='MEMORY RESULT\n' + memory_raw))
            self.assertEqual(transition.call_count, 0)
            return generation('ROUTE ' + self.fact['port'] + '\n')

        def actual_transition(port):
            self.assertEqual(len(seen), 2)
            return self.fact['outcome']

        transition = Mock(side_effect=actual_transition)
        reader = Mock(return_value=generation(memory_raw, native={'mode': 'reader'}))
        result = route.run_episode(self.task, actor, reader, transition)
        reader.assert_called_once_with(self.fact['event'])
        transition.assert_called_once_with(self.fact['port'])
        self.assertEqual((result['action_calls'], result['memory_calls']), (2, 1))
        self.assertEqual(result['traces'][0]['command']['trailing_lfs'], 2)
        self.assertEqual(result['traces'][1]['raw'], memory_raw)
        self.assertTrue(result['traces'][-2]['committed'])
        self.assertEqual(result['messages'][-1]['content'], 'ROUTE ' + self.fact['port'] + '\n')
        self.assertEqual(json.loads(json.dumps(result)), result)

    def test_optional_final_lfs_only(self):
        for command in ('READ EVENT ' + self.fact['event'], 'ROUTE ' + self.fact['port']):
            for count in (0, 1, 2, 5):
                self.assertEqual(route.parse_command(command + '\n' * count)['trailing_lfs'], count)
            for invalid in (' ' + command, command + ' ', command + '\r\n', '\n' + command,
                            command.replace(' ', '  ', 1), command.lower(), command + '\nexplanation',
                            command.replace(' ', '\t', 1), command[:-1] + '0'):
                with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                    route.parse_command(invalid)

    def test_unsupported_duplicate_and_invalid_port_stop(self):
        cases = [(['READ EVENT ' + self.bank[2]['event']], 'unsupported_address', 0),
                 (['READ EVENT ' + self.fact['event']] * 2, 'duplicate_address', 1),
                 (['ROUTE ' + self.bank[2]['port']], 'invalid_route', 0),
                 (['READ EVENT E_BAD'], 'invalid_command', 0)]
        for commands, reason, reads in cases:
            with self.subTest(reason=reason):
                actor = Mock(side_effect=[generation(command) for command in commands])
                reader, transition = Mock(return_value=generation('MISS')), Mock()
                result = route.run_episode(self.task, actor, reader, transition)
                self.assertEqual(result['terminal_reason'], reason)
                self.assertEqual(result['memory_calls'], reads)
                transition.assert_not_called()

    def test_three_actor_two_read_bound_and_direct_route_allowed(self):
        commands = ['READ EVENT ' + address for address in self.task['events']]
        reader = Mock(return_value=generation('MISS'))
        transition = Mock(return_value=self.fact['outcome'])
        actor = Mock(side_effect=[generation(command) for command in commands + ['ROUTE ' + self.fact['port']]])
        result = route.run_episode(self.task, actor, reader, transition)
        self.assertTrue(result['reached_goal'])
        self.assertEqual((result['action_calls'], result['memory_calls']), (3, 2))
        actor = Mock(side_effect=[generation(command) for command in commands + commands[:1]])
        result = route.run_episode(self.task, actor, reader, transition)
        self.assertFalse(result['reached_goal'])
        self.assertLessEqual(result['action_calls'], 3)
        self.assertLessEqual(result['memory_calls'], 2)
        with patch.object(route, 'MAX_ACTOR_CALLS', 2):
            result = route.run_episode(self.task, Mock(side_effect=[generation(command) for command in commands]),
                                       Mock(return_value=generation('MISS')), Mock())
        self.assertEqual(result['terminal_reason'], 'actor_call_cap')
        with patch.object(route, 'MAX_READS', 1):
            reader = Mock(return_value=generation('MISS'))
            result = route.run_episode(self.task, Mock(side_effect=[generation(command) for command in commands]),
                                       reader, Mock())
        self.assertEqual(result['terminal_reason'], 'memory_call_cap')
        reader.assert_called_once()

    def test_nonterminal_truncated_and_invalid_flags_retain_raw_fail_closed(self):
        for phase in ('actor', 'memory'):
            for fields in (dict(terminal=False), dict(truncated=True), dict(terminal=1), dict(truncated=None)):
                with self.subTest(phase=phase, fields=fields):
                    response = generation('READ EVENT ' + self.fact['event'] + '\n')
                    response.update(fields)
                    actor = Mock(return_value=response if phase == 'actor' else
                                 generation('READ EVENT ' + self.fact['event']))
                    reader, transition = Mock(return_value=response), Mock()
                    result = route.run_episode(self.task, actor, reader, transition)
                    self.assertTrue(result['terminal_reason'].startswith(phase + '_'))
                    self.assertEqual(result['traces'][-1]['response'], response)
                    self.assertFalse(result['reached_goal'])
                    transition.assert_not_called()
                    self.assertEqual(result['action_calls'], 1)
                    if phase == 'memory':
                        self.assertEqual(result['messages'][-1]['content'], 'MEMORY RESULT\n' + response['raw'])

    def test_invalid_response_transport_is_plain_json_and_retains_available_raw(self):
        for response, reason in ((None, 'actor_invalid_response'),
                                 ({'raw': 'STOP'}, 'actor_invalid_response'),
                                 (generation('STOP', native=object()), 'actor_non_json_response')):
            with self.subTest(reason=reason):
                transition = Mock()
                result = route.run_episode(self.task, Mock(return_value=response), Mock(), transition)
                self.assertEqual(result['terminal_reason'], reason)
                self.assertEqual(json.loads(json.dumps(result, allow_nan=False)), result)
                if type(response) is dict:
                    self.assertEqual(result['traces'][0]['raw'], 'STOP')
                transition.assert_not_called()

    def test_actual_outcome_not_hidden_target_and_no_actor_after_commit(self):
        actor = Mock(return_value=generation('ROUTE ' + self.fact['port']))
        transition = Mock(return_value=self.bank[1]['outcome'])
        result = route.run_episode(self.task, actor, Mock(), transition)
        self.assertFalse(result['reached_goal'])
        self.assertEqual(result['terminal_reason'], 'wrong_outcome')
        self.assertEqual(result['outcome'], self.bank[1]['outcome'])
        actor.assert_called_once()
        transition.assert_called_once()

    def test_callback_errors_and_mutation_do_not_leak_or_retry(self):
        transition = Mock(side_effect=RuntimeError('transition failed'))

        def mutating_actor(messages):
            messages[0]['content'] = 'mutated'
            return generation('ROUTE ' + self.fact['port'])

        result = route.run_episode(self.task, mutating_actor, Mock(), transition)
        self.assertEqual(result['terminal_reason'], 'transition_error')
        self.assertEqual(result['messages'][0]['content'], route.PUBLIC_SYSTEM)
        self.assertEqual(result['traces'][0]['messages'][0]['content'], route.PUBLIC_SYSTEM)
        self.assertEqual(result['chosen_port'], self.fact['port'])
        transition.assert_called_once()
        result = route.run_episode(self.task, Mock(side_effect=RuntimeError('actor failed')), Mock(), Mock())
        self.assertEqual(result['terminal_reason'], 'actor_callback_error')
        result = route.run_episode(self.task, Mock(return_value=generation('READ EVENT ' + self.fact['event'])),
                                   Mock(side_effect=RuntimeError('reader failed')), Mock())
        self.assertEqual(result['terminal_reason'], 'memory_callback_error')
        self.assertEqual(result['memory_calls'], 1)


if __name__ == '__main__':
    unittest.main()
