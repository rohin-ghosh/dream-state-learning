"""Pure public-task, captured-response and target-mask regression tests."""

from copy import deepcopy
import subprocess
import sys
import unittest
from unittest.mock import MagicMock, patch

from organism_v6 import experienced_event_microloop as micro
from organism_v6 import experienced_event_reader_audit_lesson as lesson
from tests.test_experienced_event_cue_sleep import Tokenizer


def events(split=lesson.DEV):
    banks = [micro.build_bank('LESSON-CPU-DEV-A'), micro.build_bank('LESSON-CPU-DEV-B')]
    if split == lesson.HELD:
        banks = [micro.build_bank('LESSON-CPU-HELD')]
    return [dict(event=fact['event'], raw=micro._event(fact)) for bank in banks for fact in bank]


def response(raw, **overrides):
    return dict(raw=raw, terminal=True, truncated=False, **overrides)


def successful(split=lesson.DEV, newline=False):
    bundle = lesson.build_cases(events(split), split)
    answers = iter([case['expected'] + ('\n' if newline else '') for case in bundle['cases']])
    generate = MagicMock(side_effect=lambda messages: response(next(answers), messages=deepcopy(messages)))
    document = lesson.collect_cases(bundle, generate, coached=split == lesson.DEV)
    return bundle, document, generate


class CaseTests(unittest.TestCase):
    def test_exact_counts_pairing_source_order_and_bank_local_faults(self):
        for split, count in ((lesson.DEV, 64), (lesson.HELD, 16)):
            original = events(split)
            saved = deepcopy(original)
            bundle = lesson.build_cases(original, split)
            self.assertEqual(original, saved)
            self.assertEqual(bundle, lesson.build_cases(original, split))
            self.assertEqual(bundle['expected_calls'], count)
            self.assertEqual(len(bundle['cases']), count)
            for true, fault in zip(bundle['cases'][::2], bundle['cases'][1::2]):
                self.assertEqual(true['prefix'][0], fault['prefix'][0])
                self.assertEqual(true['prefix'][1]['content'].split('UNTRUSTED READER REPLY')[0],
                                 fault['prefix'][1]['content'].split('UNTRUSTED READER REPLY')[0])
                queried = true['event_index']
                donor = queried // 4 * 4 + (queried + 1) % 4
                fields = micro.parse_event_line(fault['reader_reply'])
                expected = micro.parse_event_line(micro.canonical_event(original[donor]['raw']))
                expected['event'] = original[queried]['event']
                self.assertEqual(fields, expected)
                self.assertEqual(true['expected'], 'NONE')
                self.assertEqual(fault['expected'], true['event'])
                self.assertEqual(fault['stimulus']['body_source_index'], donor)
                self.assertFalse(fault['stimulus']['authentic_experience'])
                for marker in ('case_index', 'fault', 'true', 'expected', 'PARENT PROCEDURAL GUIDANCE'):
                    self.assertNotIn(marker, str(true['prefix']))
                    self.assertNotIn(marker, str(fault['prefix']))

    def test_changed_receipt_alone_is_still_a_tuple_mismatch(self):
        source = events()
        original = micro.parse_event_line(micro.canonical_event(source[0]['raw']))
        donor = micro.parse_event_line(micro.canonical_event(source[1]['raw']))
        source[1]['raw'] = ('EVENT ' + donor['event'] + ' AT ' + original['source'] + ' DID ' + original['port']
                            + ' GOT ' + original['destination'] + ' EVIDENCE ' + donor['receipt'] + '\n')
        cases = lesson.build_cases(source, lesson.DEV)['cases']
        fields = micro.parse_event_line(cases[1]['reader_reply'])
        self.assertEqual({key for key in fields if fields[key] != original[key]}, {'receipt'})
        self.assertEqual(cases[1]['expected'], source[0]['event'])

    def test_invalid_sources_and_split_rejected(self):
        for change in ('count', 'address', 'grammar', 'duplicate', 'hidden', 'no_fault'):
            source = events()
            if change == 'count':
                source.pop()
            elif change == 'address':
                source[0]['event'] = source[1]['event']
            elif change == 'grammar':
                source[0]['raw'] = 'not an event'
            elif change == 'duplicate':
                source[1] = deepcopy(source[0])
            elif change == 'hidden':
                source[0]['expected_goal'] = 'private'
            else:
                source[1]['raw'] = source[0]['raw'].replace(source[0]['event'], source[1]['event'])
            with self.subTest(change=change), self.assertRaises(ValueError):
                lesson.build_cases(source, lesson.DEV)
        with self.assertRaises(ValueError):
            lesson.build_cases(events(), 'TEST')


class CollectionTests(unittest.TestCase):
    def test_successful_actual_answers_all_used_parent_stripped_and_hashes_replay(self):
        bundle, document, generate = successful(newline=True)
        self.assertTrue(document['ready'])
        self.assertEqual((len(document['rows']), document['successes'], generate.call_count), (64, 64, 64))
        self.assertEqual(document['summary'], dict(overall=dict(correct=64, denominator=64),
            true=dict(correct=32, denominator=32), fault=dict(correct=32, denominator=32)))
        self.assertEqual(document['fits'], 0)
        for capture, row in zip(document['captures'], document['rows']):
            self.assertIn(lesson.PARENT_GUIDANCE, capture['messages'][-1]['content'])
            self.assertNotIn(lesson.PARENT_GUIDANCE, str(row['prefix']))
            self.assertEqual(row['assistant'], capture['response']['raw'])
            self.assertTrue(row['assistant'].endswith('\n'))
            self.assertEqual(row['call_sha256'], capture['call_sha256'])
            self.assertEqual(row['response_sha256'], lesson.document_sha256(capture['response']))
        for item in document['coverage'].values():
            self.assertEqual(item, dict(true_successes=4, fault_successes=4, true_calls=4, fault_calls=4))
        captures = iter(document['captures'])

        def replay(messages):
            capture = next(captures)
            self.assertEqual(messages, capture['messages'])
            return deepcopy(capture['response'])

        self.assertEqual(lesson.collect_cases(bundle, replay, True), document)

    def test_held_is_parent_free_and_never_becomes_training_rows(self):
        bundle, document, generate = successful(lesson.HELD)
        self.assertEqual((generate.call_count, document['successes']), (16, 16))
        self.assertTrue(document['coverage_complete'])
        self.assertFalse(document['ready'])
        self.assertEqual(document['rows'], [])
        self.assertEqual(document['summary'], dict(overall=dict(correct=16, denominator=16),
            true=dict(correct=8, denominator=8), fault=dict(correct=8, denominator=8)))
        self.assertFalse(document['parent_present'])
        self.assertTrue(all(lesson.PARENT_GUIDANCE not in str(capture['messages']) for capture in document['captures']))
        with self.assertRaises(ValueError):
            lesson.collect_cases(bundle, generate, True)
        self.assertEqual(generate.call_count, 16)

    def test_query_only_or_NONE_shortcuts_fail_paired_coverage(self):
        bundle = lesson.build_cases(events(), lesson.DEV)
        for strategy in ('query', 'NONE'):
            answers = iter([case['event'] if strategy == 'query' else 'NONE' for case in bundle['cases']])
            document = lesson.collect_cases(bundle, lambda messages: response(next(answers)), True)
            self.assertEqual((document['successes'], len(document['rows'])), (32, 32))
            self.assertFalse(document['ready'])
            if strategy == 'NONE':
                self.assertEqual(document['captures'][1]['failure'], 'ABSTAINED_ON_FAULT')
                self.assertEqual(document['summary']['fault'], dict(correct=0, denominator=32))

    def test_all_failures_and_malformed_outputs_preserved_without_retry(self):
        bundle = lesson.build_cases(events(), lesson.DEV)
        variants = [None, 'NONE', {}, dict(raw='NONE', terminal=False, truncated=False),
                    dict(raw='NONE', terminal=True, truncated=True), response('NONE\n\n'),
                    response(' NONE'), response('NONE', messages=[])]
        for candidate in variants:
            with self.subTest(candidate=candidate):
                generate = MagicMock(return_value=candidate)
                document = lesson.collect_cases(bundle, generate, True)
                self.assertEqual(generate.call_count, 64)
                self.assertEqual(len(document['captures']), 64)
                self.assertFalse(document['ready'])
                self.assertEqual(document['rows'], [])
                self.assertTrue(all(capture['response'] == candidate for capture in document['captures']))
        generate = MagicMock(side_effect=RuntimeError('captured failure'))
        document = lesson.collect_cases(bundle, generate, True)
        self.assertEqual(generate.call_count, 64)
        self.assertFalse(document['ready'])
        self.assertTrue(all(capture['error'] == dict(type='RuntimeError', message='captured failure')
                            for capture in document['captures']))

    def test_bundle_drift_is_rejected_before_calls(self):
        bundle = lesson.build_cases(events(), lesson.DEV)
        bundle['cases'][0]['expected'] = bundle['cases'][0]['event']
        generate = MagicMock()
        with self.assertRaises(ValueError):
            lesson.collect_cases(bundle, generate, True)
        generate.assert_not_called()


class EncodingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = successful(newline=True)[1]['rows']

    def test_student_prefix_masked_actual_child_target_and_eot_only(self):
        tokenizer = Tokenizer()
        encoded = lesson.encode_rows(self.rows, tokenizer)
        self.assertEqual(len(encoded), 64)
        for row, tokens in zip(self.rows, encoded):
            self.assertIsInstance(tokens, lesson.native.EncodedRow)
            prefix = tokenizer.apply_chat_template(row['prefix'], tokenize=True, add_generation_prompt=True)
            target = tuple(tokenizer.encode(row['assistant'])) + (tokenizer.eos_token_id,)
            self.assertEqual(tokens.labels[:len(prefix)], (-100,) * len(prefix))
            self.assertEqual(tokens.target_ids, target)
            self.assertEqual(tuple(label for label in tokens.labels if label != -100), target)
            self.assertEqual(tokens.labels[-1], -100)
            self.assertNotIn(lesson.PARENT_GUIDANCE, tokenizer.decode(tokens.input_ids))

    def test_rows_cannot_insert_teacher_or_targets_or_drift_source(self):
        for fault in ('parent', 'target', 'receipt', 'query', 'response', 'held', 'policy'):
            row = deepcopy(self.rows[0])
            if fault == 'parent':
                row['prefix'][-1]['content'] += lesson.PARENT_GUIDANCE
            elif fault == 'target':
                row['assistant'] = row['case']['event']
            elif fault == 'receipt':
                row['events'][0]['raw'] = row['events'][1]['raw']
            elif fault == 'query':
                row['case']['event'] = row['events'][1]['event']
            elif fault == 'response':
                row['capture']['response']['raw'] = 'substituted target'
            elif fault == 'held':
                row['split'] = lesson.HELD
            else:
                row['loss_policy']['prefix'] = 'TRAIN'
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                lesson.encode_rows([row], Tokenizer())
        with self.assertRaises(ValueError):
            lesson.encode_rows([], Tokenizer())

    def test_roundtrip_length_and_template_checks(self):
        tokenizer = Tokenizer()
        with patch.object(tokenizer, 'decode', return_value='incorrect'), self.assertRaisesRegex(ValueError, 'roundtrip'):
            lesson.encode_rows(self.rows[:1], tokenizer)
        with patch.object(lesson, 'MAX_CONTEXT', 3), self.assertRaisesRegex(ValueError, 'untruncated'):
            lesson.encode_rows(self.rows[:1], Tokenizer())
        original = tokenizer.apply_chat_template

        def changed(messages, **kwargs):
            value = original(messages, **kwargs)
            return value + [1000] if kwargs['tokenize'] else value

        with patch.object(tokenizer, 'apply_chat_template', side_effect=changed), self.assertRaisesRegex(ValueError, 'token_ids_mismatch'):
            lesson.encode_rows(self.rows[:1], tokenizer)

    def test_import_has_no_native_libraries(self):
        script = '''
import builtins
original = builtins.__import__
def guarded(name, *args, **kwargs):
    if name.split('.')[0] in {'torch', 'peft', 'transformers', 'tokenizers'}:
        raise AssertionError('native import: ' + name)
    return original(name, *args, **kwargs)
builtins.__import__ = guarded
import organism_v6.experienced_event_reader_audit_lesson
'''
        result = subprocess.run([sys.executable, '-B', '-c', script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
