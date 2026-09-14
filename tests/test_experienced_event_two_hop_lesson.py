"""CPU-only source-grounded trajectory, fail-closed replay and chat-mask tests."""

from copy import deepcopy
import json
import re
import unittest
from unittest.mock import patch

from organism_v6 import experienced_event_two_hop as hop
from organism_v6 import experienced_event_two_hop_lesson as lesson
from tests.test_experienced_event_two_hop import exposed_child, generation


def coached_child(messages):
    command = messages[-1]['content'].split('Execute only this next command, then wait for actual feedback:\n')[1]
    return generation(command + '\n\n', messages)


def reseal(value, key):
    value.pop(key, None)
    value[key] = lesson.document_sha256(value)


class Tokenizer:
    eos_token = lesson.TARGET_EOT
    eos_token_id = 1
    all_special_ids = [0, 1]

    def __init__(self):
        self.tokens = {self.eos_token: self.eos_token_id}
        self.pieces = {self.eos_token_id: self.eos_token}

    def encode(self, text, **kwargs):
        pieces = re.findall(r'<\|im_end\|>|[A-Za-z0-9_]+|[^A-Za-z0-9_]', text)
        for piece in pieces:
            if piece not in self.tokens:
                index = len(self.tokens) + 1
                self.tokens[piece] = index
                self.pieces[index] = piece
        return [self.tokens[piece] for piece in pieces]

    def decode(self, values, **kwargs):
        return ''.join(self.pieces[value] for value in values)

    def apply_chat_template(self, messages, *, tokenize, add_generation_prompt, **kwargs):
        text = ''.join('<' + message['role'] + '>\n' + message['content'] + self.eos_token + '\n'
                       for message in messages)
        if add_generation_prompt:
            text += '<assistant>\n'
        return self.encode(text) if tokenize else text


class LessonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.world = hop.build_world()
        cls.collection = hop.collect_world(cls.world, exposed_child)
        cls.document = lesson.collect_lessons(cls.collection, coached_child)

    def test_exact_tasks_opposite_first_ports_and_source_only_path(self):
        document = self.document
        self.assertTrue(document['ready'])
        self.assertEqual(document['task_indexes'], [0, 2])
        self.assertEqual((document['model_calls'], len(document['rows']), document['fits']), (12, 12, 0))
        self.assertEqual(document['protocol'], 'turnbound')
        first_ports = []
        store = hop.exact_text_store(self.collection)
        for bundle in document['episodes']:
            episode = bundle['episode']
            task = hop.build_tasks(self.world)[bundle['task_index']]
            self.assertEqual([step['command'] for step in bundle['plan'][:4]],
                             ['READ EVENT ' + address for address in task['events']])
            self.assertEqual(episode['protocol'], 'turnbound')
            self.assertTrue(bundle['complete'])
            self.assertEqual(episode, hop.replay_episode(self.world, task, episode))
            self.assertEqual((episode['actor_calls'], episode['memory_calls'], episode['route_calls']), (6, 4, 2))
            self.assertTrue(hop.score_episode(self.world, task, episode)['strict_success'])
            routes = episode['routes']
            first_ports.append(routes[0]['port'])
            self.assertEqual(routes[0]['destination'], routes[1]['source'])
            self.assertEqual(routes[1]['destination'], task['goal'])
            for route, step in zip(routes, bundle['plan'][4:]):
                fields = hop.micro.parse_event_line(hop.micro.canonical_event(store[step['source_events'][0]]))
                self.assertEqual({key: route[key] for key in fields if key != 'event'},
                                 {key: fields[key] for key in fields if key != 'event'})
        self.assertNotEqual(*first_ports)
        task = hop.build_tasks(self.world)[0]
        with patch.object(hop, 'build_world', side_effect=AssertionError('no edge oracle')):
            self.assertEqual(lesson._plan(task, store), document['episodes'][0]['plan'])
        self.assertNotIn('score', document)

    def test_guidance_only_last_user_actual_targets_and_exact_memory(self):
        store = hop.exact_text_store(self.collection)
        for capture, row in zip(self.document['captures'], self.document['rows']):
            student, guided = capture['student_prefix'], capture['messages']
            self.assertEqual(student, row['prefix'])
            self.assertEqual(student[:-1], guided[:-1])
            self.assertEqual(student[-1]['role'], 'user')
            self.assertTrue(guided[-1]['content'].startswith(student[-1]['content'] + '\n\n'))
            self.assertEqual(sum(lesson.PARENT_GUIDANCE in message['content'] for message in guided), 1)
            self.assertNotIn(lesson.PARENT_GUIDANCE, str(student))
            self.assertEqual(capture['response']['messages'], guided)
            self.assertEqual(row['assistant'], capture['response']['raw'])
            self.assertTrue(row['assistant'].endswith('\n\n'))
            self.assertEqual(row['target_eot'], lesson.TARGET_EOT)
            bundle = self.document['episodes'][capture['episode_index']]
            actor_traces = [trace for trace in bundle['episode']['traces'] if trace['kind'] == 'actor']
            actor_trace = actor_traces[capture['episode_call_index']]
            self.assertEqual(actor_trace['messages'], student)
            self.assertEqual(actor_trace['response'], {key: capture['response'][key]
                             for key in ('raw', 'terminal', 'truncated')})
            self.assertNotIn('messages', actor_trace['response'])
            step = bundle['plan'][capture['episode_call_index']]
            for address in step['source_events']:
                self.assertIn(store[address], guided[-1]['content'])
            for message in student:
                if message['content'].startswith('MEMORY RESULT\n'):
                    self.assertIn(message['content'][len('MEMORY RESULT\n'):], store.values())
            self.assertEqual([message['role'] for message in student],
                             ['system', 'user'] + ['assistant', 'user'] * capture['episode_call_index'])

    def test_deterministic_full_replay_and_input_isolation(self):
        before = deepcopy(self.collection)
        calls = []

        def mutating_child(messages):
            calls.append(deepcopy(messages))
            result = coached_child(messages)
            messages[-1]['content'] = 'mutated callback copy'
            return result

        document = lesson.collect_lessons(self.collection, mutating_child)
        self.assertEqual(self.collection, before)
        self.assertEqual(document, self.document)
        self.assertEqual(calls, [capture['messages'] for capture in document['captures']])
        original = deepcopy(document)
        rows = lesson.replay_lessons(json.loads(json.dumps(document)))
        self.assertEqual(rows, document['rows'])
        rows[0]['prefix'][0]['content'] = 'external mutation'
        self.assertEqual(document, original)

    def test_flat_captures_exactly_join_saved_native_calls_including_errors(self):
        for fail_first in (False, True):
            saved = {}

            def child(messages):
                call_index = len(saved)
                record = dict(messages=deepcopy(messages), response=None, error=None)
                try:
                    if fail_first and call_index == 0:
                        raise RuntimeError('saved native failure')
                    record['response'] = dict(coached_child(messages),
                        generated_token_ids=[13, 21, 1], native_metadata=dict(call_index=call_index))
                    return record['response']
                except Exception as error:
                    record['error'] = dict(type=type(error).__name__, message=str(error))
                    raise
                finally:
                    saved['CALL_%03d.json' % call_index] = json.dumps(record)

            with self.subTest(fail_first=fail_first):
                document = lesson.collect_lessons(self.collection, child)
                self.assertEqual(document['model_calls'], 7 if fail_first else 12)
                self.assertEqual([capture['call_index'] for capture in document['captures']],
                                 list(range(len(saved))))
                for capture in document['captures']:
                    record = json.loads(saved['CALL_%03d.json' % capture['call_index']])
                    self.assertEqual({key: capture[key] for key in ('messages', 'response', 'error')}, record)
                    if capture['error'] is None:
                        self.assertEqual(capture['response']['messages'], capture['messages'])
                self.assertEqual(lesson.replay_lessons(document), document['rows'])

    def test_failures_retained_no_replacement_and_other_task_still_attempted(self):
        goal = hop.build_tasks(self.world)[0]['goal']
        failures = [generation('ROUTE ' + goal), generation(' READ EVENT invalid'),
                    generation('STOP'), generation('assistant\nROUTE ' + goal),
                    dict(raw='READ EVENT invalid', terminal=False, truncated=True),
                    'READ EVENT invalid', None, RuntimeError('native transport failed')]
        for failure in failures:
            count = 0

            def child(messages):
                nonlocal count
                count += 1
                if count == 1:
                    if isinstance(failure, Exception):
                        raise failure
                    return deepcopy(failure)
                return coached_child(messages)

            with self.subTest(failure=failure):
                document = lesson.collect_lessons(self.collection, child)
                self.assertFalse(document['ready'])
                self.assertEqual(document['rows'], [])
                self.assertEqual(document['model_calls'], 7)
                self.assertEqual(len(document['episodes']), 2)
                self.assertTrue(document['episodes'][1]['complete'])
                self.assertEqual(document['episodes'][0]['episode']['routes'], [])
                capture = document['captures'][0]
                if isinstance(failure, Exception):
                    self.assertEqual(capture['error'], dict(type='RuntimeError', message=str(failure)))
                else:
                    self.assertEqual(capture['response'], failure)
                self.assertEqual(lesson.replay_lessons(document), [])
                with self.assertRaises(ValueError):
                    lesson.encode_rows(document['rows'], Tokenizer())

    def test_wrong_legal_route_uses_actual_transition_not_parent_target(self):
        wrong = self.document['episodes'][1]['plan'][4]['command']
        count = 0

        def child(messages):
            nonlocal count
            count += 1
            return generation(wrong, messages) if count == 5 else coached_child(messages)

        document = lesson.collect_lessons(self.collection, child)
        episode = document['episodes'][0]['episode']
        expected_destination = self.document['episodes'][1]['episode']['routes'][0]['destination']
        self.assertEqual(episode['current'], expected_destination)
        self.assertEqual(episode['route_calls'], 1)
        self.assertEqual(episode['terminal_reason'], 'invalid_route')
        self.assertEqual(document['captures'][4]['response']['raw'], wrong)
        self.assertFalse(document['ready'])
        self.assertEqual(lesson.replay_lessons(document), [])

    def test_strict_success_without_exact_six_command_plan_is_not_admitted(self):
        for mode in ('reverse_reads', 'routes_only'):
            sequence = []
            for bundle in self.document['episodes']:
                commands = [step['command'] for step in bundle['plan']]
                sequence += commands[3::-1] + commands[4:] if mode == 'reverse_reads' else commands[4:]
            answers = iter(sequence)
            document = lesson.collect_lessons(self.collection, lambda messages: generation(next(answers), messages))
            self.assertTrue(all(bundle['episode']['reached_goal'] for bundle in document['episodes']))
            self.assertFalse(document['ready'])
            self.assertEqual(lesson.replay_lessons(document), [])

    def test_incomplete_source_collection_no_calls_no_rows(self):
        collection = hop.collect_world(self.world, lambda messages: generation('STOP'))
        document = lesson.collect_lessons(collection, lambda messages: self.fail('must not generate'))
        self.assertEqual((document['model_calls'], document['episodes'], document['rows']), (0, [], []))
        self.assertFalse(document['ready'])
        self.assertEqual(lesson.replay_lessons(document), [])

    def test_prompt_echo_drift_is_failed_capture_not_repaired(self):
        def child(messages):
            response = coached_child(messages)
            response['messages'][-1]['content'] = 'forged prompt'
            return response

        document = lesson.collect_lessons(self.collection, child)
        self.assertEqual(document['model_calls'], 2)
        self.assertEqual(document['captures'][0]['response']['messages'][-1]['content'], 'forged prompt')
        self.assertFalse(document['ready'])
        self.assertEqual(lesson.replay_lessons(document), [])

    def test_forged_rows_captures_plan_and_transitions_rejected_even_resealed(self):
        for field in ('row', 'student', 'guided', 'raw', 'call_index', 'task_index', 'plan',
                      'transition', 'memory', 'unknown_call', 'missing_call', 'source', 'ready',
                      'bridge_raw', 'bridge_terminal', 'bridge_truncated', 'bridge_messages'):
            changed = deepcopy(self.document)
            if field == 'row':
                changed['rows'][0]['assistant'] += '\n'
                reseal(changed['rows'][0], 'row_sha256')
            elif field in ('student', 'guided'):
                key = 'student_prefix' if field == 'student' else 'messages'
                changed['captures'][0][key][-1]['content'] += '\nforgery'
            elif field == 'raw':
                changed['captures'][0]['response']['raw'] += '\n'
            elif field in ('call_index', 'task_index'):
                changed['captures'][0][field] = 99
            elif field == 'plan':
                changed['episodes'][0]['plan'][4]['command'] = 'ROUTE forged'
            elif field == 'transition':
                changed['episodes'][0]['episode']['routes'][0]['destination'] = 'forged'
            elif field == 'memory':
                changed['episodes'][0]['episode']['traces'][1]['response'] = 'forged memory'
            elif field == 'unknown_call':
                changed['captures'].append(deepcopy(changed['captures'][-1]))
            elif field == 'missing_call':
                changed['captures'].pop()
            elif field == 'source':
                changed['collection']['records'][0]['event']['raw'] += 'forged'
            elif field.startswith('bridge_'):
                projection = changed['episodes'][0]['episode']['traces'][0]['response']
                key = field[len('bridge_'):]
                if key == 'raw':
                    projection[key] += '\n'
                elif key == 'messages':
                    projection[key] = deepcopy(changed['captures'][0]['student_prefix'])
                else:
                    projection[key] = not projection[key]
            else:
                changed['ready'] = False
            for capture in changed['captures']:
                reseal(capture, 'call_sha256')
            for bundle in changed['episodes']:
                reseal(bundle['episode'], 'episode_sha256')
            evidence = {key: value for key, value in changed.items() if key not in ('rows', 'lesson_sha256')}
            reseal(evidence, 'evidence_sha256')
            changed['evidence_sha256'] = evidence['evidence_sha256']
            reseal(changed, 'lesson_sha256')
            with self.subTest(field=field), self.assertRaises(ValueError):
                lesson.replay_lessons(changed)

    def test_multi_turn_masks_only_final_actual_assistant_and_eot(self):
        tokenizer = Tokenizer()
        rows = lesson.replay_lessons(self.document)
        encoded = lesson.encode_rows(rows, tokenizer)
        self.assertIsInstance(encoded, tuple)
        self.assertEqual(len(encoded), 12)
        for row, result in zip(rows, encoded):
            self.assertIsInstance(result, lesson.native.EncodedRow)
            self.assertLessEqual(len(result.input_ids), 2048)
            prefix = tokenizer.apply_chat_template(row['prefix'], tokenize=False, add_generation_prompt=True)
            prefix_ids = tuple(tokenizer.encode(prefix))
            supervised = tuple(tokenizer.encode(row['assistant'])) + (tokenizer.eos_token_id,)
            suffix = tuple(tokenizer.encode('\n'))
            self.assertEqual(result.input_ids, prefix_ids + supervised + suffix)
            self.assertEqual(result.labels, (-100,) * len(prefix_ids) + supervised + (-100,) * len(suffix))
            self.assertEqual(result.target_ids, supervised)
            self.assertEqual(tokenizer.decode(result.target_ids), row['assistant'] + lesson.TARGET_EOT)
            sleep_text = tokenizer.decode(result.input_ids)
            self.assertNotIn(lesson.PARENT_GUIDANCE, sleep_text)
            self.assertNotIn('researcher-prepared', sleep_text)
            self.assertNotIn('CAPTURED SOURCE EVENT', sleep_text)
            self.assertNotIn('source_sha256', sleep_text)
            self.assertGreater(prefix_ids.count(tokenizer.eos_token_id), 1)

    def test_encoder_rejects_partial_forged_reordered_or_duplicate_rows(self):
        for mode in ('partial', 'target', 'prefix', 'capture', 'reverse', 'duplicate'):
            rows = deepcopy(self.document['rows'])
            if mode == 'partial':
                rows.pop()
            elif mode == 'target':
                rows[0]['assistant'] = rows[0]['assistant'].rstrip('\n')
            elif mode == 'prefix':
                rows[0]['prefix'][-1]['content'] += lesson.PARENT_GUIDANCE
            elif mode == 'capture':
                rows[0]['provenance']['captures'][0]['response']['raw'] += '\n'
            elif mode == 'reverse':
                rows.reverse()
            else:
                rows[-1] = deepcopy(rows[0])
            for row in rows:
                reseal(row, 'row_sha256')
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                lesson.encode_rows(rows, Tokenizer())
        with self.assertRaises(ValueError):
            lesson.encode_rows([], Tokenizer())

    def test_encoder_rejects_context_template_token_and_roundtrip_drift(self):
        rows = self.document['rows']
        tokenizer = Tokenizer()
        maximum = max(len(row.input_ids) for row in lesson.encode_rows(rows, tokenizer))
        with patch.object(lesson, 'MAX_CONTEXT', maximum):
            self.assertEqual(len(lesson.encode_rows(rows, tokenizer)), 12)
        with patch.object(lesson, 'MAX_CONTEXT', maximum - 1), self.assertRaisesRegex(ValueError, 'sequence_required'):
            lesson.encode_rows(rows, tokenizer)
        for fault in ('template', 'token_ids', 'decode', 'eot', 'special_target', 'boundary'):
            tokenizer = Tokenizer()
            template = tokenizer.apply_chat_template
            encode = tokenizer.encode
            if fault == 'template':
                tokenizer.apply_chat_template = lambda *args, **kwargs: template(*args, **kwargs) + 'drift'
            elif fault == 'token_ids':
                tokenizer.apply_chat_template = lambda *args, **kwargs: (
                    template(*args, **kwargs) + [0] if kwargs['tokenize'] else template(*args, **kwargs))
            elif fault == 'decode':
                tokenizer.decode = lambda *args, **kwargs: 'wrong decode'
            elif fault == 'eot':
                tokenizer.eos_token = '<wrong>'
            elif fault == 'special_target':
                tokenizer.all_special_ids = [0, 1] + encode('READ')
            else:
                tokenizer.encode = lambda text, **kwargs: encode(text, **kwargs) + ([0] if '<system>' in text else [])
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                lesson.encode_rows(rows, tokenizer)


if __name__ == '__main__':
    unittest.main()
