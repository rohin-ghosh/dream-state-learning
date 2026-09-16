import json
import unittest

from gpu import orch_r140_grid_json as repair


class TextTokenizer:
    def apply_chat_template(self, messages, **kwargs):
        assert kwargs == dict(tokenize=True, add_generation_prompt=True, return_dict=False)
        return [1] * (5 + sum(len(message['content']) for message in messages))


class JsonEncodingTests(unittest.TestCase):
    def setUp(self):
        self.tokenizer = TextTokenizer()
        self.messages = [dict(role='system', content='unchanged'), dict(role='user',
            content=json.dumps(dict(reflection='观察' * 30), sort_keys=True))]

    def test_overflow_reencoded_without_losing_values(self):
        actual, metadata = repair.normalize_messages(self.tokenizer, self.messages, 10, 140)
        self.assertTrue(metadata['applied'])
        self.assertGreater(metadata['original_prompt_tokens'] + 10, 140)
        self.assertLessEqual(metadata['actual_prompt_tokens'] + 10, 140)
        self.assertEqual(json.loads(actual[1]['content']), json.loads(self.messages[1]['content']))
        self.assertEqual(actual[0], self.messages[0])
        self.assertEqual(repair.recover_original_messages(actual, metadata), self.messages)

    def test_within_budget_bytes_stay_unchanged(self):
        actual, metadata = repair.normalize_messages(self.tokenizer, self.messages, 10, 1000)
        self.assertEqual(actual, self.messages)
        self.assertFalse(metadata['applied'])

    def test_input_is_not_mutated(self):
        before = json.dumps(self.messages)
        actual, _ = repair.normalize_messages(self.tokenizer, self.messages, 10, 140)
        actual[0]['content'] = 'modified by caller'
        self.assertEqual(json.dumps(self.messages), before)

    def test_cap_and_limit_unchanged(self):
        _, metadata = repair.normalize_messages(self.tokenizer, self.messages, 10, 140)
        self.assertEqual((metadata['generation_cap'], metadata['context_limit']), (10, 140))
        self.assertFalse(metadata['content_removed'])
        self.assertFalse(metadata['model_budget_changed'])

    def test_ascii_overflow_fails_not_cropped(self):
        messages = [dict(role='user', content=json.dumps(dict(text='x' * 300)))]
        with self.assertRaises(repair.ContextCapacityError) as caught:
            repair.normalize_messages(self.tokenizer, messages, 10, 100)
        self.assertFalse(caught.exception.metadata['applied'])
        self.assertFalse(caught.exception.metadata['content_removed'])

    def test_partial_reencoding_still_overflow_fails(self):
        with self.assertRaises(repair.ContextCapacityError) as caught:
            repair.normalize_messages(self.tokenizer, self.messages, 10, 30)
        self.assertTrue(caught.exception.metadata['applied'])

    def test_noncanonical_duplicate_scalar_and_nonfinite_unchanged(self):
        for value in ('{"x": "\\u89c2", "x": "other"}', '[NaN]', '"\\u89c2"', '{ "x":"\\u89c2" }'):
            self.assertIsNone(repair.canonical_user_json(value))

    def test_unpaired_surrogate_not_decoded(self):
        self.assertIsNone(repair.canonical_user_json('{"x": "\\ud800"}'))

    def test_emoji_and_literal_backslash_roundtrip(self):
        original = json.dumps(dict(emoji='🌱', literal=r'\u89c2'), sort_keys=True)
        actual = repair.canonical_user_json(original)
        self.assertEqual(json.loads(actual), json.loads(original))
        self.assertIn(r'\\u89c2', actual)

    def test_assistant_and_system_never_reencoded(self):
        messages = [dict(role='assistant', content=self.messages[1]['content'])]
        with self.assertRaises(repair.ContextCapacityError) as caught:
            repair.normalize_messages(self.tokenizer, messages, 10, 140)
        self.assertEqual(caught.exception.metadata['reencoded_message_indices'], [])

    def test_batch_encoding_cannot_be_miscounted_as_two_tokens(self):
        class WrongTokenizer:
            def apply_chat_template(self, *args, **kwargs):
                return dict(input_ids=[1, 2], attention_mask=[1, 1])
        with self.assertRaisesRegex(ValueError, 'flat_token_ids'):
            repair.normalize_messages(WrongTokenizer(), self.messages, 10)

    def test_modified_actual_cannot_recover(self):
        actual, metadata = repair.normalize_messages(self.tokenizer, self.messages, 10, 140)
        actual[1]['content'] = '{}'
        with self.assertRaisesRegex(ValueError, 'actual_message_hash'):
            repair.recover_original_messages(actual, metadata)

    def test_recovery_metadata_drift_rejected(self):
        actual, metadata = repair.normalize_messages(self.tokenizer, self.messages, 10, 140)
        metadata['original_messages_sha256'] = 'invalid'
        with self.assertRaisesRegex(ValueError, 'original_message_hash'):
            repair.recover_original_messages(actual, metadata)

    def test_invalid_budget_rejected(self):
        for cap, limit in ((0, 16384), (384, 384), (True, 16384)):
            with self.assertRaisesRegex(ValueError, 'decoder_budget'):
                repair.normalize_messages(self.tokenizer, self.messages, cap, limit)


if __name__ == '__main__':
    unittest.main()
