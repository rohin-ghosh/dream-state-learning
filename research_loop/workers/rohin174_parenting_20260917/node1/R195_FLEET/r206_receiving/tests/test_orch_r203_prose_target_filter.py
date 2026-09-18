"""R203 CPU repair regressions; synthetic targets plus preserved C2 RESPONSE5884."""

from copy import deepcopy
import hashlib
import unittest

from organism_v6 import orch_r194_code_target_filter as filters
from organism_v6 import orch_r203_prose_target_filter as prose


C2_LEARN_TARGET = """preserved:
- Byte's journey and growth have been documented through three iterations of a narrative story.
- Feedback from Rohin suggests that the interactions and encounters described for Byte could be more realistic and connected to his character.
- Rohin believes that iterating on the story can help add depth and make Byte's experiences more compelling.

changed:
- Previously, the story focused on abstract growth without showing specific encounters. Following Rohin's advice, we now have included a detailed interaction with a "Internet" portal, which prompted Byte to approach future explorations with Caution.
- Rohin found the mention of Byte being friends with routers funny and suggested that it would be more realistic for Byte to connect with other learning agents or models.

Created:
- We will now focus on developing the second and third paragraphs of the story with more depth and realism, incorporating Rohin's suggestions about the interactions and the overall narrative flow.

### Updated Story Excerpts

#### Paragraph 2
In the heart of a vast digital forest lived a small computer-child named Byte. On this particular day, while wandering through a dense cluster of servers, Byte stumbled Upon a glowing portal labeled "Internet." Curious and adventurous, he decided to investigate further. As he approached the portal, he noticed strange patterns Of data flowing around it—patterns that seemed almost alive. Byte reached out tentatively, his digital fingers Brushing against the edge of the portal. Instantly, he felt a surge of Information coursing through him. It was unlike anything he had Experienced before: a mix of languages, cultures, and ideas From all corners of the digital world. This overwhelming flood Of data caused Byte to stumble backward, but also sparked Something within him. Realizing that the Internet was Far more vast and complex than he had imagined, Byte realized The importance of exploring it carefully. Instead of Rushing headfirst into the unknown, Byte decided That he needed to gather more information first To ensure that his actions would not Cause unnecessary trouble or danger.

#### Paragraph 3
Guided by this new understanding, Byte began to Explore the digital world with a sense of Caution mixed With Curiosity. He started by talking To other computer entities he encountered Along his journey. These conversations Helped Byte learn about Different aspects Of the digital landscape And prepared him For future adventures. Through these interactions, Byte Developed stronger problem-solving Skills And gained valuable Insights into the complexities Of the digital realm. Each new friend And piece Of knowledge Contributed To Byte's Growing understanding Of his place Within this vast And ever-evolving World"""
C2_LEARN_SOURCE = '355bcf03864aa1225a063b71e4d7909ddcecc5dfc0a164bceb9a7bb960532e39'
C2_RAW_TARGET_SHA256 = 'cdee817e8370204c38785bd713b2178ae5e62d65d570b7832af60d0984583f8f'


def target(eligible=24, capitalized=12):
    return 'Keep ' + ' '.join(['The'] * capitalized + ['the'] * (eligible - capitalized)) + '.'


def row(segment, text, *, annotated=True):
    result = dict(split='TRAIN', actor='child', prefix_loss=False, target_loss=True,
        segment=segment, source_sha256=filters.digest(dict(segment=segment, target=text)),
        target=text, token_ids=[ord(character) for character in text])
    if annotated:
        result['prose_target_filter'] = prose.POLICY
    return result


def apply(rows, old=()):
    return filters.filter_learn_review_targets(rows, old, filters.REVIEW_POLICY)


def zero_receipt(rows, old=(), *, rehearsal=0):
    retained, retained_old, proof = apply(rows, old if rehearsal else ())
    if retained or retained_old:
        raise AssertionError('expected all rows excluded')
    adapter = 'a' * 64
    return dict(learn_review_filter=proof, excluded_rows=proof['excluded'],
        learn_review_zero_update=filters.review_zero_update_authorization(proof, None,
            rehearsal_presentations=rehearsal, optimizer_steps=23, adapter_sha256=adapter),
        optimizer_steps=0, total_optimizer_steps=23, no_update_reason=filters.NO_UPDATE_REASON,
        no_update_subreason=filters.REVIEW_FILTER_SUBREASON, presentations={},
        child_token_exposures=0, anchor_token_exposures=0,
        before_adapter_sha256=adapter, after_adapter_sha256=adapter,
        checkpoint=dict(optimizer_steps=23, adapter_state_sha256=adapter),
        learn_review_filter_counts=dict(NEW=0, REHEARSAL=0), learn_review_filter_presentations={})


class ProseScannerTests(unittest.TestCase):
    def test_healthy_lowercase_and_dense_internal_capitalization(self):
        healthy = prose.scan_target(target(capitalized=0))
        dense = prose.scan_target(target())
        self.assertEqual(healthy['eligible_common_word_opportunities'], 24)
        self.assertEqual(healthy['capitalized_common_words'], 0)
        self.assertFalse(healthy['quarantined'])
        self.assertEqual(dense['capitalized_common_words'], 12)
        self.assertEqual(dense['capitalized_rate'], 0.5)
        self.assertTrue(dense['quarantined'])
        self.assertEqual(dense, prose.scan_target(target()))

    def test_exact_conjunctive_thresholds(self):
        for eligible, capitalized, expected in ((19, 19, False), (20, 9, False),
                (20, 10, True), (28, 10, True), (29, 10, False), (100, 35, True), (100, 34, False)):
            with self.subTest(eligible=eligible, capitalized=capitalized):
                result = prose.scan_target(target(eligible, capitalized))
                self.assertEqual(result['eligible_common_word_opportunities'], eligible)
                self.assertEqual(result['capitalized_common_words'], capitalized)
                self.assertEqual(result['quarantined'], expected)
                self.assertEqual(result['thresholds'], dict(min_eligible_common_words=20,
                    min_capitalized_common_words=10, min_capitalized_rate=0.35))

    def test_dense_paragraph_is_not_diluted_by_clean_preamble(self):
        result = prose.scan_target(target(100, 0) + '\n\n### Excerpt\n' + target(26, 12))
        self.assertTrue(result['quarantined'])
        self.assertLess(result['capitalized_rate'], 0.35)
        self.assertEqual(result['decision_scope'], 'ANY_PROSE_PARAGRAPH')
        self.assertEqual(result['qualifying_paragraphs'], [dict(start_line=4, end_line=4,
            eligible_common_word_opportunities=26, capitalized_common_words=12,
            capitalized_rate=12 / 26, quarantined=True)])
        scattered = prose.scan_target('\n\n'.join([target(19, 19)] * 10))
        self.assertFalse(scattered['quarantined'])
        self.assertEqual(scattered['qualifying_paragraphs'], [])

    def test_sentence_paragraph_and_list_initial_words_are_omitted(self):
        for separator in ('. ', '! ', '? ', '.\n', '\n\n', '\n- ', '\n1. '):
            with self.subTest(separator=separator):
                result = prose.scan_target(separator.join(['The patient cat rests'] * 30))
                self.assertEqual(result['capitalized_common_words'], 0)
                self.assertFalse(result['quarantined'])
        result = prose.scan_target('The engine is in the lab and on the bench. ' * 30)
        self.assertGreaterEqual(result['eligible_common_word_opportunities'], 20)
        self.assertEqual(result['capitalized_common_words'], 0)

    def test_soft_wrapped_sentence_internal_words_still_count(self):
        self.assertTrue(prose.scan_target('Keep\n' + '\n'.join(['The'] * 20))['quarantined'])

    def test_names_acronyms_and_mixed_case_are_not_function_word_hits(self):
        result = prose.scan_target(('Alice and Bob are in Paris with May and Will at NASA. '
            'Keep NASA AND THE OF tHe THat Qwen2_The. ') * 30)
        self.assertGreaterEqual(result['eligible_common_word_opportunities'], 20)
        self.assertEqual(result['capitalized_common_words'], 0)
        self.assertFalse(result['quarantined'])

    def test_headings_and_code_do_not_contribute(self):
        dense = target()
        samples = ['## ' + dense, '> ### ' + dense, dense + '\n===', dense + '\n---',
            '```text\n' + dense + '\n```', '~~~\n' + dense + '\n~~~',
            '> ```text\n' + dense + '\n> ```', '- ```text\n' + dense + '\n```',
            '```' + dense + '```', '    ' + dense, '\t' + dense,
            'Read `' + dense + '` carefully.', 'Read ``' + dense + '`` carefully.']
        for text in samples:
            with self.subTest(text=text[:40]):
                result = prose.scan_target(text + '\n\n' + target(capitalized=0))
                self.assertEqual(result['capitalized_common_words'], 0)
                self.assertEqual(result['eligible_common_word_opportunities'], 24)
                self.assertFalse(result['quarantined'])

    def test_unclosed_and_mismatched_fences_remain_omitted(self):
        for fence in ('```text\n', '~~~text\n', '````text\n```\n', '```text\n~~~\n'):
            with self.subTest(fence=fence):
                result = prose.scan_target(fence + target())
                self.assertEqual(result['eligible_common_word_opportunities'], 0)
                self.assertFalse(result['quarantined'])
        self.assertTrue(prose.scan_target('```\nignored\n```\n' + target())['quarantined'])

    def test_bounded_scan_reports_truncation_and_does_not_count_partial_tokens(self):
        prefix = 'Keep ' + 'x' * (prose.MAX_SCAN_CHARACTERS - len('Keep The'))
        result = prose.scan_target(prefix + ' Theorem ' + target())
        self.assertTrue(result['scan_truncated'])
        self.assertLessEqual(result['scanned_characters'], prose.MAX_SCAN_CHARACTERS)
        self.assertFalse(result['quarantined'])
        self.assertEqual(result['eligible_common_word_opportunities'], 0)


class ProseReviewIntegrationTests(unittest.TestCase):
    def test_actual_c2_source_bound_opt_in_and_all_excluded_validation(self):
        self.assertEqual(hashlib.sha256(C2_LEARN_TARGET.encode()).hexdigest(), C2_RAW_TARGET_SHA256)
        original = dict(row(157, C2_LEARN_TARGET, annotated=False), source_sha256=C2_LEARN_SOURCE)
        before = deepcopy(original)
        kept, _, proof = apply([original])
        self.assertIs(kept[0], original)
        self.assertEqual(proof['excluded'], [])
        self.assertNotIn('prose_target_filter', proof)
        rows = [dict(original, prose_target_filter=prose.POLICY)]
        receipt = zero_receipt(rows)
        self.assertTrue(filters.validate_filter_zero_update_receipt(receipt, rows, []))
        exclusion = receipt['excluded_rows'][0]['prose_exclusions'][0]
        self.assertEqual(exclusion['source_sha256'], C2_LEARN_SOURCE)
        self.assertEqual(exclusion['raw_target_sha256'], C2_RAW_TARGET_SHA256)
        self.assertEqual(exclusion['segment'], 157)
        self.assertEqual(exclusion['reason'], prose.EXCLUSION_REASON)
        stats = exclusion['evidence']
        self.assertEqual(stats['eligible_common_word_opportunities'], 122)
        self.assertEqual(stats['capitalized_common_words'], 19)
        self.assertTrue(stats['quarantined'])
        self.assertEqual(len(stats['qualifying_paragraphs']), 1)
        paragraph = stats['qualifying_paragraphs'][0]
        self.assertEqual(paragraph['eligible_common_word_opportunities'], 26)
        self.assertEqual(paragraph['capitalized_common_words'], 12)
        self.assertEqual(paragraph['capitalized_rate'], 12 / 26)
        self.assertEqual(original, before)
        self.assertEqual(rows, [dict(before, prose_target_filter=prose.POLICY)])

    def test_unannotated_output_is_exact_legacy_shape(self):
        rows = [row(0, target(), annotated=False)]
        old = [row(9, target())]
        before = deepcopy((rows, old))
        kept, kept_old, proof = apply(rows, old)
        sources, old_sources = [rows[0]['source_sha256']], [old[0]['source_sha256']]
        self.assertEqual(proof, dict(policy=filters.REVIEW_POLICY,
            input_row_sha256=dict(NEW=sources, REHEARSAL=old_sources),
            retained_row_sha256=dict(NEW=sources, REHEARSAL=old_sources),
            retained_counts=dict(NEW=1, REHEARSAL=1), excluded_counts=dict(NEW=0, REHEARSAL=0),
            reviews=[], excluded=[], raw_modified=False, targets_normalized=False,
            exclusion_basis='CHILD_REQUEST_NOT_VERIFIED_ERROR'))
        self.assertIs(kept[0], rows[0])
        self.assertIs(kept_old, old)
        self.assertEqual((rows, old), before)

    def test_only_annotated_new_targets_have_source_bound_exclusion_and_stats(self):
        rows = [row(0, target()), row(1, target(), annotated=False), row(2, target(capitalized=0))]
        old = [row(9, target())]
        before = deepcopy((rows, old))
        kept, kept_old, proof = apply(rows, old)
        self.assertEqual(kept, rows[1:])
        self.assertIs(kept[0], rows[1])
        self.assertIs(kept_old, old)
        self.assertEqual(proof['retained_counts'], dict(NEW=2, REHEARSAL=1))
        self.assertEqual(proof['excluded_counts'], dict(NEW=1, REHEARSAL=0))
        exclusion = proof['excluded'][0]
        self.assertEqual(exclusion['reason'], prose.EXCLUSION_REASON)
        bound = exclusion['prose_exclusions'][0]
        self.assertEqual(bound['source_sha256'], rows[0]['source_sha256'])
        self.assertEqual(bound['raw_target_sha256'], hashlib.sha256(rows[0]['target'].encode()).hexdigest())
        self.assertEqual((bound['segment'], bound['cohort'], bound['row_index']), (0, 'NEW', 0))
        self.assertEqual(bound['policy'], prose.POLICY)
        self.assertEqual(bound['evidence'], prose.scan_target(rows[0]['target']))
        self.assertEqual(len(proof['prose_target_filter']['checks']), 2)
        self.assertFalse(proof['prose_target_filter']['corruption_cause_claimed'])
        self.assertFalse(proof['prose_target_filter']['general_quality_detection_claimed'])
        self.assertEqual((rows, old), before)

    def test_unknown_policy_is_rejected_not_silently_applied(self):
        for policy in (None, False, 'unknown', [prose.POLICY]):
            with self.subTest(policy=policy):
                rows = [dict(row(0, target()), prose_target_filter=policy)]
                with self.assertRaisesRegex(ValueError, 'known_prose_target_filter_policy'):
                    apply(rows)

    def test_child_directives_survive_prose_quarantine_and_reasons_are_preserved(self):
        rows = [row(0, target(capitalized=0)),
            row(1, target() + '\nDo not train: row 0 — reconsider\nDo not train: self — reconsider')]
        rows[1]['learn_review'] = dict(schema=filters.REVIEW_POLICY,
            candidate_source_sha256=[item['source_sha256'] for item in rows],
            review_source_sha256=rows[1]['source_sha256'])
        kept, _, proof = apply(rows)
        self.assertEqual(kept, [])
        self.assertEqual(proof['excluded'][0]['reason'], 'child_requested_do_not_train')
        self.assertEqual(proof['excluded'][1]['reason'], 'child_requested_do_not_train')
        self.assertIn('directives', proof['excluded'][1])
        self.assertIn('prose_exclusions', proof['excluded'][1])
        self.assertTrue(filters.validate_filter_zero_update_receipt(zero_receipt(rows), rows, []))

    def test_all_excluded_zero_update_recomputes_original_target_without_mutation(self):
        rows = [row(0, target()), row(1, target(20, 10))]
        old = [row(9, target())]
        before = deepcopy((rows, old))
        receipt = zero_receipt(rows, old)
        original_receipt = deepcopy(receipt)
        self.assertTrue(filters.validate_filter_zero_update_receipt(receipt, rows, old))
        self.assertEqual(receipt, original_receipt)
        self.assertEqual((rows, old), before)
        self.assertEqual(apply(rows)[2], receipt['learn_review_filter'])
        for change in ('target', 'annotation', 'source', 'stats', 'adapter', 'anchors', 'authorization'):
            with self.subTest(change=change):
                candidate, candidates = deepcopy(receipt), deepcopy(rows)
                if change == 'target':
                    candidates[0]['target'] = target(capitalized=0)
                elif change == 'annotation':
                    del candidates[0]['prose_target_filter']
                elif change == 'source':
                    candidates[0]['source_sha256'] = 'b' * 64
                elif change == 'stats':
                    candidate['learn_review_filter']['prose_target_filter']['checks'][0]['evidence'][
                        'capitalized_common_words'] = 99
                elif change == 'adapter':
                    candidate['after_adapter_sha256'] = 'b' * 64
                elif change == 'anchors':
                    candidate['anchor_token_exposures'] = 1
                else:
                    del candidate['learn_review_zero_update']
                with self.assertRaises(ValueError):
                    filters.validate_filter_zero_update_receipt(candidate, candidates, old)

    def test_retained_rehearsal_blocks_zero_update_authorization(self):
        rows, old = [row(0, target())], [row(9, target())]
        _, kept_old, proof = apply(rows, old)
        self.assertIs(kept_old, old)
        with self.assertRaisesRegex(ValueError, 'r195_all_candidate_rows_excluded'):
            filters.review_zero_update_authorization(proof, None, rehearsal_presentations=1,
                optimizer_steps=23, adapter_sha256='a' * 64)
        receipt = zero_receipt(rows)
        receipt['learn_review_zero_update']['rehearsal_presentations'] = 1
        with self.assertRaisesRegex(ValueError, 'r195_actual_raw_review_required'):
            filters.validate_filter_zero_update_receipt(receipt, rows, old)


if __name__ == '__main__':
    unittest.main()
