"""CPU-only transfer memory provenance, LF serialization and encoder checks."""

from collections import Counter
from copy import deepcopy
from hashlib import sha256
import json
import unittest
from unittest.mock import patch

from gpu import astra_experienced_event_microloop as source
from organism_v6 import experienced_event_two_hop as hop
from organism_v6 import experienced_event_two_hop_memory as memory
from tests.test_experienced_event_two_hop import exposed_child
from tests.test_experienced_event_two_hop_lesson import Tokenizer


class MemoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.world = hop.build_world(hop.TRANSFER_MASTER)
        cls.collection = hop.collect_world(cls.world, lambda messages: exposed_child(messages, suffix='\n\n'))
        cls.rows = memory.compile_rows(cls.collection)

    def test_exact_32_rows_wrapper_major_layout_hashes_and_source_targets(self):
        self.assertEqual(len(self.rows), 32)
        self.assertEqual(Counter(row['event'] for row in self.rows),
                         Counter({edge['event']: 8 for edge in self.world['edges']}))
        self.assertEqual(Counter(row['wrapper'] for row in self.rows),
                         Counter({f'W{index}': 4 for index in range(8)}))
        for index, row in enumerate(self.rows):
            record = self.collection['records'][index % 4]
            event = record['edge']['event']
            raw = record['event']['raw']
            target = raw.rstrip('\n') + '\n'
            self.assertEqual(set(row), {'world', 'event', 'wrapper', 'messages', 'source_raw_sha256',
                'target_sha256', 'serialization', 'source_collection_sha256'})
            self.assertEqual((row['world'], row['event'], row['wrapper']),
                             (hop.TRANSFER_MASTER, event, f'W{index // 4}'))
            self.assertEqual(row['messages'], [
                dict(role='system', content=source.world.MEMORY_SYSTEM),
                dict(role='user', content=source.world.WRAPPERS[index // 4].format(REQUEST='READ EVENT ' + event)),
                dict(role='assistant', content=target)])
            self.assertEqual(row['source_raw_sha256'], sha256(raw.encode('utf-8')).hexdigest())
            self.assertEqual(row['target_sha256'], sha256(target.encode('utf-8')).hexdigest())
            self.assertEqual(row['serialization'], 'FINAL_LF_ONLY')
            self.assertEqual(row['source_collection_sha256'], self.collection['collection_sha256'])
            self.assertEqual(hop.micro.parse_event_line(target), dict(event=event, **record['transition']))
            self.assertEqual(self.collection['captures'][2 * (index % 4) + 1]['response'], record['event'])

    def test_queries_have_only_address_no_answer_parent_or_uncaptured_fields(self):
        for row in self.rows:
            question = row['messages'][1]['content']
            self.assertEqual(question.count('READ EVENT ' + row['event']), 1)
            self.assertNotIn(row['messages'][-1]['content'], question)
            self.assertNotIn('PARENT', json.dumps(row['messages']))
            for edge in self.world['edges']:
                for key in ('node', 'port', 'outcome', 'receipt'):
                    self.assertNotIn(edge[key], question)
                if edge['event'] != row['event']:
                    self.assertNotIn(edge['event'], question)
        self.assertEqual({row['event'] for row in self.rows}, set(hop.exact_text_store(self.collection)))

    def test_connected_records_do_not_use_old_disconnected_bank_validator(self):
        self.assertTrue({edge['node'] for edge in self.world['edges']}
                        & {edge['outcome'] for edge in self.world['edges']})
        with patch.object(hop.micro, '_check_bank', side_effect=AssertionError('not a disconnected bank')):
            self.assertEqual(memory.compile_rows(self.collection), self.rows)
            self.assertEqual(memory.replay_rows(self.rows, self.collection), self.rows)

    def test_deterministic_replay_isolated_from_input_and_output_mutations(self):
        saved = deepcopy(self.collection)
        rows = memory.compile_rows(self.collection)
        self.assertEqual(self.collection, saved)
        self.assertEqual(memory.compile_rows(self.collection), rows)
        restored = memory.replay_rows(json.loads(json.dumps(rows)), self.collection)
        self.assertEqual(restored, rows)
        restored[0]['messages'][-1]['content'] = 'mutated'
        self.assertEqual(rows, self.rows)
        self.assertEqual(self.collection, saved)

    def test_only_final_lf_count_is_normalized(self):
        for count in (0, 1, 2, 5):
            with self.subTest(count=count):
                collection = hop.collect_world(self.world, lambda messages: exposed_child(messages, suffix='\n' * count))
                rows = memory.compile_rows(collection)
                self.assertEqual(memory.replay_rows(rows, collection), rows)
                self.assertEqual([row['messages'] for row in rows], [row['messages'] for row in self.rows])
                for index, row in enumerate(rows):
                    raw = collection['records'][index % 4]['event']['raw']
                    self.assertEqual(len(raw) - len(raw.rstrip('\n')), count)
                    self.assertEqual(row['messages'][-1]['content'], raw.rstrip('\n') + '\n')
                    self.assertEqual(row['source_raw_sha256'], sha256(raw.encode('utf-8')).hexdigest())
        for flaw in ('leading_space', 'crlf', 'trailing_space', 'explanation', 'internal_space', 'duplicate'):
            def child(messages):
                response = exposed_child(messages)
                if len(messages) > 2:
                    raw = response['raw']
                    response['raw'] = {'leading_space': ' ' + raw, 'crlf': raw.rstrip('\n') + '\r\n',
                        'trailing_space': raw.rstrip('\n') + ' \n', 'explanation': raw + 'explanation',
                        'internal_space': raw.replace(' AT ', '  AT '), 'duplicate': raw + raw}[flaw]
                return response

            with self.subTest(flaw=flaw), self.assertRaises(ValueError):
                memory.compile_rows(hop.collect_world(self.world, child))

    def test_partial_and_source_invalid_native_formations_fail_closed(self):
        for flaw in ('action', 'field', 'terminal', 'truncated', 'prompt', 'exception'):
            calls = 0

            def child(messages):
                nonlocal calls
                calls += 1
                response = exposed_child(messages)
                if calls == (1 if flaw == 'action' else 2):
                    if flaw == 'action':
                        response['raw'] = 'STOP'
                    elif flaw == 'field':
                        response['raw'] = response['raw'].replace(self.world['edges'][0]['receipt'],
                                                                 self.world['edges'][1]['receipt'])
                    elif flaw in ('terminal', 'truncated'):
                        response[flaw] = not response[flaw]
                    elif flaw == 'prompt':
                        response['messages'][-1]['content'] += 'forged'
                    else:
                        raise RuntimeError('actual failed formation')
                return response

            with self.subTest(flaw=flaw):
                collection = hop.collect_world(self.world, child)
                self.assertEqual(collection['accepted_events'], 3)
                self.assertEqual(hop.replay_collection(collection), collection)
                with self.assertRaises(ValueError):
                    memory.compile_rows(collection)
                with self.assertRaises(ValueError):
                    memory.replay_rows(self.rows, collection)

    def test_forged_source_fields_raw_native_and_partial_capture_rejected(self):
        for flaw in ('field', 'raw', 'native', 'receipt', 'missing_capture', 'unknown_capture', 'record'):
            collection = deepcopy(self.collection)
            if flaw == 'field':
                collection['records'][0]['edge']['outcome'] = self.world['nodes'][4]
            elif flaw == 'raw':
                collection['records'][0]['event']['raw'] += '\n'
            elif flaw == 'native':
                collection['captures'][1]['response']['truncated'] = True
            elif flaw == 'receipt':
                collection['records'][0]['transition']['receipt'] = self.world['edges'][1]['receipt']
            elif flaw == 'missing_capture':
                collection['captures'].pop()
            elif flaw == 'unknown_capture':
                collection['captures'].append(deepcopy(collection['captures'][0]))
            else:
                collection['records'].pop()
            collection.pop('collection_sha256')
            collection = hop._seal(collection, 'collection_sha256')
            with self.subTest(flaw=flaw), self.assertRaises(ValueError):
                memory.compile_rows(collection)

    def test_row_replay_rejects_forgery_reordering_duplicates_and_partial_rows(self):
        for flaw in ('target', 'source_hash', 'target_hash', 'source_collection', 'world', 'event',
                     'wrapper', 'serialization', 'question', 'partial', 'duplicate', 'reordered', 'extra'):
            rows = deepcopy(self.rows)
            if flaw == 'target':
                rows[0]['messages'][-1]['content'] = rows[1]['messages'][-1]['content']
                rows[0]['target_sha256'] = sha256(rows[0]['messages'][-1]['content'].encode()).hexdigest()
            elif flaw == 'source_hash':
                rows[0]['source_raw_sha256'] = rows[0]['target_sha256']
            elif flaw == 'target_hash':
                rows[0]['target_sha256'] = 'forged'
            elif flaw == 'source_collection':
                rows[0]['source_collection_sha256'] = 'forged'
            elif flaw in ('world', 'event', 'wrapper', 'serialization'):
                rows[0][flaw] = 'forged'
            elif flaw == 'question':
                rows[0]['messages'][1]['content'] += rows[0]['messages'][-1]['content']
            elif flaw == 'partial':
                rows.pop()
            elif flaw == 'duplicate':
                rows[-1] = deepcopy(rows[0])
            elif flaw == 'reordered':
                rows.reverse()
            else:
                rows[0]['parent_guidance'] = 'not allowed'
            with self.subTest(flaw=flaw), self.assertRaises(ValueError):
                memory.replay_rows(rows, self.collection)
        with self.assertRaises(ValueError):
            memory.replay_rows([], self.collection)

    def test_transfer_only_and_full_native_source_binding(self):
        original = hop.collect_world(hop.build_world(), exposed_child)
        with self.assertRaisesRegex(ValueError, 'fresh_transfer_collection_required'):
            memory.compile_rows(original)

        def child(messages):
            return dict(exposed_child(messages, suffix='\n\n'), native_metadata='different actual collection')

        other = hop.collect_world(self.world, child)
        self.assertEqual(hop.replay_collection(other), other)
        other_rows = memory.compile_rows(other)
        self.assertEqual([row['messages'] for row in self.rows], [row['messages'] for row in other_rows])
        self.assertNotEqual(self.rows[0]['source_collection_sha256'], other_rows[0]['source_collection_sha256'])
        with self.assertRaises(ValueError):
            memory.replay_rows(self.rows, other)

    def test_existing_memory_encoder_compatible_and_masks_prefix_and_suffix(self):
        tokenizer = Tokenizer()
        encoded = source.encode_rows(memory.replay_rows(self.rows, self.collection), tokenizer)
        self.assertIsInstance(encoded, tuple)
        self.assertEqual(len(encoded), 32)
        for row, tokens in zip(self.rows, encoded):
            prefix = tokenizer.apply_chat_template(row['messages'][:2], tokenize=False, add_generation_prompt=True)
            prefix_ids = tuple(tokenizer.encode(prefix))
            target = tuple(tokenizer.encode(row['messages'][-1]['content'])) + (tokenizer.eos_token_id,)
            suffix = tuple(tokenizer.encode('\n'))
            self.assertEqual(tokens.input_ids, prefix_ids + target + suffix)
            self.assertEqual(tokens.labels, (-100,) * len(prefix_ids) + target + (-100,) * len(suffix))
            self.assertEqual(tokens.target_ids, target)
            self.assertLessEqual(len(tokens.input_ids), 2048)


if __name__ == '__main__':
    unittest.main()
