"""Fake-decoder unit tests; no GPU/model loading or raw transcript fixtures.

Separate offline verification on 2026-09-15 replayed the two existing native
token arrays with the local tokenizers tokenizer, not a model. Both decoded
exactly to their stored raw strings. Original 8192-token truncated receipts
were untouched; the stop positions below are counterfactual, not live savings.
These native checks are recorded provenance, not executed by this unit suite.

Pinned safeguard SHA256:
1fe38d9fea6bed06f07c3a5eb0ccbb029635d7af148b38367d8cd51dddfc2ceb
Tokenizer JSON SHA256:
c0382117ea329cdf097041132f6d735924b697924d6f6fc3945713e96ce87539
Native root: /localhome/local-rohing/orch_math_pipeline_l2_20260915_attempt1

MICRO: campaign_03_r102_micro5/GUIDED_SLEEP/cycle7/experience/CALL_0075.json
Receipt SHA256: 224d091200d52ba6b674a1ed9d2b7eb2b4545a908303f9d2820ac7f347fe5b0c
Counterfactual stop: 848/8192 tokens, three complete three-paragraph blocks,
573 block characters including the short formula; partial next paragraph.

TRAINING: campaign_05_r104_training4/GUIDED_SLEEP/cycle3/experience/CALL_0027.json
Receipt SHA256: 96cf8b07dadb8fd168c4095482f0d12a3b73739cbabb68a0f148dc5f57313c9a
Counterfactual stop: 784/8192 tokens, three complete 431-character paragraphs,
followed by a partial next paragraph. Semantic novelty yield remained UNKNOWN
for both. No torch/transformers import, native generation, or provider call.
"""

import unittest

from gpu.orch_reflection_repetition_stop import (
    ExactParagraphRepetitionStop,
    RepeatPolicy,
    STOP_REASON,
    repeated_paragraph_tail,
)


PARAGRAPH = (
    'I will inspect the recorded evidence before choosing a route. '
    'The observed transition constrains the next decision, while a rejected '
    'alternative remains distinct from a confirmed successful path.'
)
SECOND = (
    'I will verify the current budget against the real receipt and retain '
    'the uncertainty explicitly. A conceptual check is not an extra action, '
    'and an unobserved possibility is not a recorded result.'
)


class FakeDecoder:
    eos_token_id = -1

    def __init__(self):
        self.calls = 0

    def decode(self, token_ids, *, skip_special_tokens, clean_up_tokenization_spaces):
        self.calls += 1
        assert skip_special_tokens is False
        assert clean_up_tokenization_spaces is False
        return ''.join('<eos>' if token == -1 else chr(token) for token in token_ids)


def encode(text):
    return [ord(character) for character in text]


class TensorLike:
    def __init__(self, rows):
        self.rows = rows

    def tolist(self):
        return self.rows


class ParagraphTailTests(unittest.TestCase):
    def test_three_complete_copies_without_final_separator(self):
        witness = repeated_paragraph_tail('\n\n'.join([PARAGRAPH] * 3))
        self.assertEqual(witness['complete_copies'], 3)
        self.assertEqual(witness['block_paragraphs'], 1)
        self.assertEqual(witness['repeated_content_characters'], 2 * len(PARAGRAPH))

    def test_partial_fourth_paragraph_does_not_hide_three_copies(self):
        partial = PARAGRAPH[:79]
        witness = repeated_paragraph_tail('\n\n'.join([PARAGRAPH] * 3 + [partial]))
        self.assertEqual(witness['complete_copies'], 3)
        self.assertTrue(witness['partial_final_paragraph'])
        self.assertEqual(witness['matched_next_copy_characters'], len(partial))
        self.assertEqual(witness['repeated_content_characters'], 2 * len(PARAGRAPH) + len(partial))

    def test_two_copies_and_partial_third_are_not_three_repeats(self):
        self.assertIsNone(repeated_paragraph_tail('\n\n'.join([PARAGRAPH] * 2 + [PARAGRAPH[:-1]])))

    def test_terminal_blank_separator_and_crlf(self):
        for separator in ('\n\n', '\r\n\r\n', '\n \n'):
            with self.subTest(separator=separator):
                witness = repeated_paragraph_tail(separator.join([PARAGRAPH] * 3) + separator)
                self.assertEqual(witness['complete_copies'], 3)

    def test_two_paragraph_block_and_partial_next_block(self):
        block = [PARAGRAPH, SECOND]
        for extra in ([], [PARAGRAPH[:81]], [PARAGRAPH, SECOND[:81]]):
            with self.subTest(extra=len(extra)):
                witness = repeated_paragraph_tail('\n\n'.join(block * 3 + extra))
                self.assertEqual(witness['block_paragraphs'], 2)
                self.assertEqual(witness['complete_copies'], 3)

    def test_short_lists_and_phrases_never_trigger(self):
        for text in ('\n\n'.join(['Check receipt.'] * 500), '\n'.join(['- Check the route'] * 500)):
            self.assertIsNone(repeated_paragraph_tail(text))

    def test_varied_checks_and_judgments_do_not_trigger(self):
        checks = [PARAGRAPH + f' Check {index}: the evidence changes this judgment.' for index in range(20)]
        self.assertIsNone(repeated_paragraph_tail('\n\n'.join(checks)))

    def test_internal_whitespace_and_case_are_not_normalized(self):
        for variant in (PARAGRAPH.upper(), PARAGRAPH.replace(' ', '  '), PARAGRAPH + '!'):
            self.assertIsNone(repeated_paragraph_tail('\n\n'.join([PARAGRAPH, variant, PARAGRAPH])))

    def test_productive_recovery_after_old_repeat_is_not_stopped(self):
        self.assertIsNone(repeated_paragraph_tail('\n\n'.join([PARAGRAPH] * 3 + [SECOND])))

    def test_short_paragraph_with_insufficient_aggregate_does_not_trigger(self):
        self.assertIsNone(repeated_paragraph_tail('\n\n'.join([PARAGRAPH, 'Check.'] * 3)))

    def test_long_short_formula_long_three_paragraph_loop(self):
        block = [PARAGRAPH, '96 * 9 = 864', SECOND]
        witness = repeated_paragraph_tail('\n\n'.join(block * 3))
        self.assertEqual(witness['block_paragraphs'], 3)
        self.assertEqual(witness['complete_copies'], 3)
        self.assertEqual(witness['long_paragraphs'], 2)
        self.assertEqual(witness['repeated_content_characters'], 2 * sum(map(len, block)))

    def test_long_short_long_loop_with_partial_final_paragraph(self):
        block = [PARAGRAPH, '96 * 9 = 864', SECOND]
        for tail in ([PARAGRAPH[:70]], [PARAGRAPH, '96 *'],
                     [PARAGRAPH, '96 * 9 = 864', SECOND[:70]]):
            with self.subTest(tail_paragraphs=len(tail)):
                witness = repeated_paragraph_tail('\n\n'.join(block * 3 + tail))
                self.assertEqual(witness['block_paragraphs'], 3)
                self.assertEqual(witness['complete_copies'], 3)
                self.assertTrue(witness['partial_final_paragraph'])

    def test_one_long_paragraph_is_enough_when_aggregate_sufficient(self):
        block = [PARAGRAPH * 2, '96 * 9 = 864', 'Check the units.']
        witness = repeated_paragraph_tail('\n\n'.join(block * 3))
        self.assertEqual(witness['long_paragraphs'], 1)
        self.assertEqual(witness['block_paragraphs'], 3)

    def test_all_short_blocks_fail_even_when_aggregate_exceeds_threshold(self):
        block = ['a' * 120, 'b' * 120, 'c' * 120]
        self.assertGreater(sum(map(len, block)), RepeatPolicy().min_block_chars)
        self.assertIsNone(repeated_paragraph_tail('\n\n'.join(block * 72)))

    def test_changing_formula_is_not_an_exact_repeated_block(self):
        paragraphs = []
        for index in range(10):
            paragraphs.extend([PARAGRAPH, f'96 * {index} = {96 * index}', SECOND])
        self.assertIsNone(repeated_paragraph_tail('\n\n'.join(paragraphs)))

    def test_two_long_short_long_copies_plus_partial_third_do_not_trigger(self):
        block = [PARAGRAPH, '96 * 9 = 864', SECOND]
        self.assertIsNone(repeated_paragraph_tail('\n\n'.join(block * 2 + [PARAGRAPH, block[1], SECOND[:-1]])))

    def test_policy_rejects_less_than_three_and_invalid_thresholds(self):
        for kwargs in ({'min_repeats': 2}, {'min_repeats': True}, {'min_generated_tokens': 0},
                       {'min_paragraph_chars': 0}, {'min_block_chars': 0},
                       {'check_every_tokens': 0}, {'max_block_paragraphs': 0}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                RepeatPolicy(**kwargs)

    def test_non_text_is_rejected(self):
        with self.assertRaises(TypeError):
            repeated_paragraph_tail(None)


class CallbackTests(unittest.TestCase):
    def test_default_catches_repeated_tail_before_8192_cap(self):
        decoder = FakeDecoder()
        criterion = ExactParagraphRepetitionStop(decoder, prompt_length=0)
        tokens = encode('\n\n'.join([PARAGRAPH] * 50))
        stopped_at = None
        for count in range(1, min(len(tokens), 8192) + 1):
            if criterion([tokens[:count]], None):
                stopped_at = count
                break
        self.assertIsNotNone(stopped_at)
        self.assertLess(stopped_at, 8192)
        result = criterion.finalize([tokens[:stopped_at]], max_new_tokens=8192)
        self.assertEqual(result['stop_reason'], STOP_REASON)
        self.assertTrue(result['early_stopped'])
        self.assertFalse(result['terminal'])
        self.assertFalse(result['truncated'])
        self.assertFalse(result['eos_reached'])
        self.assertEqual(result['raw_prefix'], ''.join(map(chr, tokens[:stopped_at])))
        self.assertEqual(result['generated_tokens_including_special'], stopped_at)
        self.assertEqual(result['semantic_novelty_yield'], 'UNKNOWN')
        self.assertEqual(result['semantic_review_status'], 'PENDING_AUTHOR_REVIEW')
        self.assertIsNone(result['repeated_content_tokens'])

    def test_prompt_tokens_and_repetitions_are_excluded(self):
        prompt = encode('\n\n'.join([PARAGRAPH] * 4))
        criterion = ExactParagraphRepetitionStop(FakeDecoder(), prompt_length=len(prompt))
        self.assertFalse(criterion([prompt + encode('A new and short reflection.')]))
        result = criterion.finalize([prompt + encode('A new and short reflection.')], max_new_tokens=8192)
        self.assertEqual(result['raw_prefix'], 'A new and short reflection.')
        self.assertEqual(result['stop_reason'], 'EXTERNAL_STOP')

    def test_token_minimum_is_independent_of_paragraph_counts(self):
        text = '\n\n'.join([PARAGRAPH] * 3)
        criterion = ExactParagraphRepetitionStop(FakeDecoder(), prompt_length=0,
            policy=RepeatPolicy(min_generated_tokens=len(encode(text)) + 1))
        self.assertFalse(criterion([encode(text)]))

    def test_eos_is_not_relabelled_as_repetition_stop(self):
        text = '\n\n'.join([PARAGRAPH] * 3)
        tokens = encode(text) + [-1]
        criterion = ExactParagraphRepetitionStop(FakeDecoder(), prompt_length=0)
        self.assertFalse(criterion([tokens]))
        result = criterion.finalize([tokens], max_new_tokens=8192)
        self.assertEqual(result['stop_reason'], 'EOS')
        self.assertTrue(result['terminal'])
        self.assertFalse(result['early_stopped'])
        self.assertEqual(result['raw_prefix'], text + '<eos>')
        self.assertEqual(result['generated_tokens_excluding_terminal_eos'], len(tokens) - 1)

    def test_final_scan_cannot_retroactively_claim_early_stop(self):
        tokens = encode('\n\n'.join([PARAGRAPH] * 3))
        criterion = ExactParagraphRepetitionStop(FakeDecoder(), prompt_length=0)
        result = criterion.finalize([tokens], max_new_tokens=len(tokens))
        self.assertEqual(result['stop_reason'], 'MAX_NEW_TOKENS')
        self.assertTrue(result['truncated'])
        self.assertFalse(result['early_stopped'])
        self.assertIsNotNone(result['final_repeat_witness'])

    def test_stop_coincident_with_cap_is_not_credited_as_early(self):
        tokens = encode('\n\n'.join([PARAGRAPH] * 3))
        criterion = ExactParagraphRepetitionStop(FakeDecoder(), prompt_length=0)
        self.assertTrue(criterion([tokens]))
        result = criterion.finalize([tokens], max_new_tokens=len(tokens))
        self.assertEqual(result['stop_reason'], 'MAX_NEW_TOKENS')
        self.assertTrue(result['length_cap_reached'])
        self.assertTrue(result['truncated'])
        self.assertTrue(result['repetition_stop_at_final_prefix'])
        self.assertTrue(result['repetition_stop_coincides_with_cap'])
        self.assertFalse(result['early_stopped'])

    def test_ignored_stop_preserves_later_text_and_actual_eos_reason(self):
        tokens = encode('\n\n'.join([PARAGRAPH] * 3))
        criterion = ExactParagraphRepetitionStop(FakeDecoder(), prompt_length=0)
        self.assertTrue(criterion([tokens]))
        continued = tokens + encode('\n\n' + SECOND) + [-1]
        result = criterion.finalize([continued], max_new_tokens=8192)
        self.assertEqual(result['stop_reason'], 'EOS')
        self.assertTrue(result['repetition_stop_requested'])
        self.assertFalse(result['repetition_stop_honored'])
        self.assertFalse(result['early_stopped'])
        self.assertEqual(result['stop_requested_at_generated_tokens'], len(tokens))
        self.assertTrue(result['raw_prefix'].endswith(SECOND + '<eos>'))

    def test_single_row_tensor_like_and_one_dimensional_tokens(self):
        tokens = encode('\n\n'.join([PARAGRAPH] * 3))
        for inputs in (tokens, [tokens], TensorLike([tokens])):
            criterion = ExactParagraphRepetitionStop(FakeDecoder(), prompt_length=0)
            self.assertTrue(criterion(inputs, scores=None))

    def test_batches_beams_and_state_reuse_are_rejected(self):
        criterion = ExactParagraphRepetitionStop(FakeDecoder(), prompt_length=0)
        with self.assertRaises(ValueError):
            criterion([[1], [2]])
        self.assertFalse(criterion([[65, 66]]))
        with self.assertRaises(ValueError):
            criterion([[65]])
        with self.assertRaises(ValueError):
            criterion([[65, 67, 68]])

    def test_invalid_prompt_eos_and_tokens_are_rejected(self):
        with self.assertRaises(ValueError):
            ExactParagraphRepetitionStop(FakeDecoder(), prompt_length=-1)
        with self.assertRaises(TypeError):
            ExactParagraphRepetitionStop(FakeDecoder(), prompt_length=0, eos_token_ids=['bad'])
        criterion = ExactParagraphRepetitionStop(FakeDecoder(), prompt_length=2)
        with self.assertRaises(ValueError):
            criterion([[65]])
        with self.assertRaises(TypeError):
            criterion([[65, 'bad']])

    def test_decode_cadence_skips_subminimum_and_small_increment(self):
        decoder = FakeDecoder()
        criterion = ExactParagraphRepetitionStop(decoder, prompt_length=0)
        self.assertFalse(criterion([encode('a' * 511)]))
        self.assertEqual(decoder.calls, 0)
        self.assertFalse(criterion([encode('a' * 512)]))
        self.assertEqual(decoder.calls, 1)
        self.assertFalse(criterion([encode('a' * 513)]))
        self.assertEqual(decoder.calls, 1)
        self.assertFalse(criterion([encode('a' * 528)]))
        self.assertEqual(decoder.calls, 2)

    def test_lexical_metadata_does_not_claim_semantic_yield(self):
        text = '\n\n'.join([PARAGRAPH] * 3)
        criterion = ExactParagraphRepetitionStop(FakeDecoder(), prompt_length=0)
        self.assertTrue(criterion([encode(text)]))
        result = criterion.finalize([encode(text)], max_new_tokens=8192)
        proxy = result['lexical_novelty_proxy']
        self.assertEqual(proxy['eligible_segments'], 3)
        self.assertEqual(proxy['exact_duplicate_segments'], 2)
        self.assertEqual(proxy['exact_duplicate_content_characters'], 2 * len(PARAGRAPH))
        self.assertAlmostEqual(proxy['unique_content_fraction'], 1 / 3)
        self.assertEqual(result['semantic_novelty_yield'], 'UNKNOWN')
        self.assertEqual(result['fit_eligibility'], 'NOT_DECIDED_BY_THIS_SAFEGUARD')

    def test_no_mutation_of_input_and_no_global_decoder_state(self):
        tokens = encode('\n\n'.join([PARAGRAPH] * 3))
        before = list(tokens)
        first = ExactParagraphRepetitionStop(FakeDecoder(), prompt_length=0)
        second = ExactParagraphRepetitionStop(FakeDecoder(), prompt_length=0)
        self.assertTrue(first([tokens]))
        self.assertFalse(second([encode('A distinct short beginning.')]))
        self.assertEqual(tokens, before)

    def test_empty_output_has_no_fabricated_novelty_fraction(self):
        criterion = ExactParagraphRepetitionStop(FakeDecoder(), prompt_length=0)
        self.assertFalse(criterion([[]]))
        result = criterion.finalize([[]], max_new_tokens=8192)
        self.assertEqual(result['stop_reason'], 'EXTERNAL_STOP')
        self.assertEqual(result['generated_tokens_including_special'], 0)
        self.assertIsNone(result['lexical_novelty_proxy']['unique_content_fraction'])

    def test_configured_eos_collection(self):
        criterion = ExactParagraphRepetitionStop(FakeDecoder(), prompt_length=0,
            eos_token_ids=[-1, 999])
        self.assertFalse(criterion([[65, 999]]))
        result = criterion.finalize([[65, 999]], max_new_tokens=8192)
        self.assertEqual(result['stop_reason'], 'EOS')
        self.assertEqual(result['generated_tokens_excluding_terminal_eos'], 1)

    def test_higher_repeat_minimum_is_respected(self):
        policy = RepeatPolicy(min_repeats=4)
        self.assertIsNone(repeated_paragraph_tail('\n\n'.join([PARAGRAPH] * 3), policy))
        witness = repeated_paragraph_tail('\n\n'.join([PARAGRAPH] * 4), policy)
        self.assertEqual(witness['complete_copies'], 4)

    def test_default_callback_catches_long_short_long_loop_before_cap(self):
        block = [PARAGRAPH, '96 * 9 = 864', SECOND]
        tokens = encode('\n\n'.join(block * 72))
        criterion = ExactParagraphRepetitionStop(FakeDecoder(), prompt_length=0)
        for count in range(1, 8193):
            if criterion([tokens[:count]]):
                result = criterion.finalize([tokens[:count]], max_new_tokens=8192)
                self.assertLess(count, 8192)
                self.assertEqual(result['trigger_witness']['block_paragraphs'], 3)
                self.assertGreaterEqual(result['trigger_witness']['complete_copies'], 3)
                self.assertEqual(result['semantic_novelty_yield'], 'UNKNOWN')
                self.assertEqual(result['stop_reason'], STOP_REASON)
                break
        else:
            self.fail('Mixed-length repetition was not stopped before the cap')


if __name__ == '__main__':
    unittest.main()
