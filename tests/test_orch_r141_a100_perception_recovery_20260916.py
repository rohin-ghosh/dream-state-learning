from copy import deepcopy
import unittest

from gpu import orch_r141_a100_perception_recovery_20260916 as repair


class Tokenizer:
    all_special_ids = [90, 91, 92]
    eos_token_id = 92
    pad_token_id = 90

    def decode(self, tokens, **kwargs):
        return ''.join({90: '<pad>', 91: '<start>', 92: '<end>'}.get(token, chr(token)) for token in tokens)

    def encode(self, text, **kwargs):
        if kwargs.get('split_special_tokens') is not True:
            raise AssertionError('special recognition must be disabled')
        return [ord(character) for character in text]

    def apply_chat_template(self, messages, **kwargs):
        return [1, 2, 3]


class LiteralTargetTests(unittest.TestCase):
    def setUp(self):
        self.tokenizer = Tokenizer()
        self.row = dict(split='TRAIN', actor='child', prefix_loss=False, target_loss=True,
            token_ids=[97, 91, 91, 92], target='a<start><start>', terminal=True, truncated=False,
            prefix=[dict(role='user', content='question')])

    def test_literal_special_ids_preserve_raw_history_and_terminal(self):
        before = deepcopy(self.row)
        target, mappings = repair.literal_target(self.row, self.tokenizer)
        self.assertEqual(target[-1], 92)
        self.assertFalse(set(target[:-1]) & set(self.tokenizer.all_special_ids))
        self.assertEqual(self.tokenizer.decode(target[:-1]), self.row['target'])
        self.assertEqual([mapping['generated_offset'] for mapping in mappings], [1, 2])
        self.assertEqual(self.row, before)

    def test_prefix_mask_and_no_trim(self):
        encoded = repair.encode_own(self.row, self.tokenizer, 100)
        self.assertEqual(encoded.labels[:3], (-100, -100, -100))
        self.assertEqual(encoded.input_ids[:3], (1, 2, 3))
        with self.assertRaisesRegex(ValueError, 'no_training_trim'):
            repair.encode_own(self.row, self.tokenizer, 6)

    def test_ordinary_generated_ids_unchanged(self):
        self.row.update(token_ids=[97, 98, 92], target='ab')
        target, mappings = repair.literal_target(self.row, self.tokenizer)
        self.assertEqual(target, (97, 98, 92))
        self.assertEqual(mappings, [])

    def test_nonterminal_eos_is_literal_not_a_delimiter(self):
        self.row.update(token_ids=[97, 92], target='a<end>', terminal=False, truncated=True)
        target, unused = repair.literal_target(self.row, self.tokenizer)
        self.assertFalse(set(target) & set(self.tokenizer.all_special_ids))
        self.assertEqual(self.tokenizer.decode(target), 'a<end>')

    def test_bad_provenance_and_roundtrip_fail_closed(self):
        changes = [dict(split='HELD'), dict(actor='parent'), dict(prefix_loss=True),
            dict(target_loss=False), dict(target='modified'), dict(token_ids=[97]),
            dict(terminal=1), dict(token_ids=[True, 92])]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ValueError):
                repair.literal_target(dict(self.row, **change), self.tokenizer)

    def test_tokenizer_that_keeps_special_id_rejected(self):
        self.tokenizer.encode = lambda text, **kwargs: [91]
        with self.assertRaisesRegex(ValueError, 'no_special_ids'):
            repair.literal_target(self.row, self.tokenizer)

    def test_bad_literal_spelling_rejected(self):
        self.tokenizer.encode = lambda text, **kwargs: [97]
        with self.assertRaisesRegex(ValueError, 'spelling_roundtrip'):
            repair.literal_target(self.row, self.tokenizer)


class DurableBindingTests(unittest.TestCase):
    def fixture(self):
        checkpoint = dict(checkpoint_sha256={'adapter': 'a', 'optimizer': 'b', 'rng': 'b'},
            adapter_state_sha256='adapter', base_sha256='base', experiment={'seed': 1})
        plan = dict(presentation_version='plain', system_prompt='system', birth_prompt='birth',
            context_limit=100, hard_end_unix=1000, segment_tokens=4, decoder={'temperature': 0.7})
        state = dict(model_state_sha256=repair.digest(checkpoint['checkpoint_sha256']),
            experiment=checkpoint['experiment'], sleep_frontier=0, rows=[], deadline_unix=1000,
            segment_tokens=4, context_limit=100, presentation=dict(version='plain', system_prompt='system', birth_prompt='birth'))
        suffix = []
        for segment in range(3):
            request = dict(segment=segment, messages=[{'role': 'user', 'content': str(segment)}], split='TRAIN',
                retry_allowed=False, model_state_sha256=state['model_state_sha256'], max_new_tokens=4,
                deadline_unix=1000, prompt_tokens=3)
            output = dict(raw='ab', token_ids=[97, 98], terminal=False, truncated=True,
                decoder=plan['decoder'], adapter_state_sha256='adapter', base_sha256='base', prompt_tokens=3)
            response = dict(response=output, request_sha256=repair.digest(request), raw_saved_before_validation=True)
            source_sha = repair.digest(response)
            row = dict(source_sha256=source_sha, segment=segment, split='TRAIN', actor='child',
                prefix_loss=False, target_loss=True, prefix=request['messages'], model_state_sha256=state['model_state_sha256'],
                target='ab', token_ids=[97, 98], terminal=False, truncated=True)
            state['rows'].append(row)
            suffix.extend([dict(kind='REQUEST', document=request), dict(kind='RESPONSE', document=response),
                dict(kind='COMMITTED', document=dict(segment=segment, source_sha256=source_sha))])
        state['pending'] = 'sleep:' + repair.digest([row['source_sha256'] for row in state['rows']])
        return suffix, state, checkpoint, plan

    def test_exact_three_requests_and_responses_bound_without_mutation(self):
        arguments = self.fixture()
        before = deepcopy(arguments)
        requests, responses = repair.validate_replay_rows(*arguments)
        self.assertEqual(len(requests), 3)
        self.assertEqual(len(responses), 3)
        self.assertEqual(arguments, before)

    def test_learning_missing_response_or_changed_state_rejected(self):
        for mutation in ('update', 'missing', 'pending', 'presentation', 'deadline', 'prefix', 'token', 'checkpoint'):
            arguments = self.fixture()
            suffix, state, checkpoint, plan = arguments
            if mutation == 'update':
                suffix.append(dict(kind='UPDATE', document={}))
            elif mutation == 'missing':
                del suffix[1]
            elif mutation == 'pending':
                state['pending'] = None
            elif mutation == 'presentation':
                plan['system_prompt'] = 'changed'
            elif mutation == 'deadline':
                plan['hard_end_unix'] += 1
            elif mutation == 'prefix':
                suffix[0]['document']['messages'] = []
            elif mutation == 'token':
                state['rows'][0]['token_ids'] = [99]
            else:
                checkpoint['checkpoint_sha256']['optimizer'] = 'changed'
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                repair.validate_replay_rows(*arguments)

    def test_other_life_or_tail_cannot_enter_live_binding(self):
        with self.assertRaisesRegex(ValueError, 'exact_original_1250_tail'):
            repair.bind_live([], {}, {})


if __name__ == '__main__':
    unittest.main()
