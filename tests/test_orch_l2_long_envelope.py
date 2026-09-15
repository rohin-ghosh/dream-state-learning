"""Lossless envelope repair, including the preserved native failures."""

import hashlib
import json
from pathlib import Path
import unittest

from gpu.orch_l2_long_envelope import parse_json_envelope


EVIDENCE = (Path(__file__).resolve().parents[1] / 'research_notes' / 'analysis'
            / 'orch_l2_long_20260914_attempt1')


class LongEnvelopeTests(unittest.TestCase):
    def test_plain_object_preserves_all_values(self):
        original = {'decision': 'decline', 'message': '', 'reason': 'unchanged',
                    'distillation': 'unchanged', 'reviews': [{'gate': False}],
                    'target': 'opaque PORT\nREAD abc', 'rubric': {'accept': False}}
        self.assertEqual(parse_json_envelope(json.dumps(original)), original)

    def test_full_fence_and_outer_json_whitespace(self):
        for newline in ('\n', '\r\n'):
            with self.subTest(newline=newline):
                self.assertEqual(parse_json_envelope(
                    ' \t' + '```json' + newline + '{"value":1}' + newline + '```\r\n'),
                    {'value': 1})

    def test_alias_only_renames_top_level_key(self):
        original = {'message': '  No edits.\n\tUnicode—é🙂  ',
                    'distillation_for_rohin': 'Keep exactly.\n',
                    'nested': {'distillation_for_rohin': 'do not rename'}}
        parsed = parse_json_envelope(json.dumps(original))
        expected = dict(original)
        expected['distillation'] = expected.pop('distillation_for_rohin')
        self.assertEqual(parsed, expected)
        for key in ('message', 'distillation'):
            source_key = 'distillation_for_rohin' if key == 'distillation' else key
            self.assertEqual(parsed[key].encode('utf-8'), original[source_key].encode('utf-8'))

    def test_rejects_ambiguous_alias_even_if_values_match(self):
        for value in ('same', 'different'):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'ambiguous'):
                parse_json_envelope(json.dumps({'distillation': 'same',
                                                'distillation_for_rohin': value}))

    def test_rejects_non_json_or_non_object_without_salvage(self):
        invalid = [None, {}, b'{}', '', '[]', 'null', 'true', '1', '"object"',
                   'prose\n{}', '{}\nprose', '{}{}', '{"message":}',
                   '{"message":"first","message":"second"}',
                   '{"reviews":[{"gate":true,"gate":false}]}',
                   '{"value":NaN}', '{"value":Infinity}', '{"value":-Infinity}',
                   '```\n{}\n```', '```JSON\n{}\n```', '```json {} ```',
                   '```json\n{}\n```\nexplanation', 'explanation\n```json\n{}\n```',
                   '```json\n{}\n```\n```json\n{}\n```', '```json\n{\n```',
                   '```json\n[]\n```', '{"value":1,}']
        for text in invalid:
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_json_envelope(text)

    def test_preserved_actual_0001_and_0002_semantics_and_bytes(self):
        for index in ('0001', '0002'):
            path = EVIDENCE / f'PARENT_C1_{index}_stdout.json'
            before = path.read_bytes()
            provider = json.loads(before)
            self.assertIs(provider['is_error'], False)
            text = provider['result']
            self.assertTrue(text.startswith('```json\n'))
            self.assertTrue(text.endswith('\n```'))
            original = json.loads(text[len('```json\n'):-len('\n```')])
            expected = {('distillation' if key == 'distillation_for_rohin' else key): value
                        for key, value in original.items()}
            parsed = parse_json_envelope(text)
            self.assertEqual(parsed, expected)
            for key, value in original.items():
                normalized_key = 'distillation' if key == 'distillation_for_rohin' else key
                self.assertEqual(json.dumps(parsed[normalized_key], ensure_ascii=False).encode('utf-8'),
                                 json.dumps(value, ensure_ascii=False).encode('utf-8'))
                if isinstance(value, str):
                    self.assertEqual(parsed[normalized_key].encode('utf-8'), value.encode('utf-8'))
            self.assertEqual(hashlib.sha256(path.read_bytes()).digest(), hashlib.sha256(before).digest())
            if index == '0001':
                self.assertEqual(parsed['reviews'], original['reviews'])
            else:
                self.assertEqual(parsed['decision'], original['decision'])
                self.assertEqual(parsed['message'], original['message'])


if __name__ == '__main__':
    unittest.main()
