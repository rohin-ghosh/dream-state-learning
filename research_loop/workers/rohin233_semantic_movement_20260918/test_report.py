import copy
import json
import unittest

from prepare import CANON, act_pairs, sha
from report import caption_matches, life_report, response_link, verify_bytes


def event(text, event_id='environment:fixture', actor='environment'):
    return dict(text=text, event_id=event_id, actor=actor, phase='feedback', source_sha256=CANON.text_sha(text))


def fixture():
    records = []
    feedback = event('Astra: Check your arithmetic.', 'parent:fixture', 'parent')
    for index, stage, text in ((10, 'THINK', 'Synthetic thought.'), (20, 'ACT', 'Synthetic first artifact.'),
                               (30, 'THINK', 'Synthetic corrected thought.'), (40, 'ACT', 'Synthetic second artifact.')):
        request_digest = 'request_' + str(index)
        source = CANON.text_sha(text)
        records.extend([
            dict(index=index, sha256=str(index), kind='REQUEST', request_digest=request_digest,
                 masked=True, cycle=index // 10, external=[feedback], time_unix=index),
            dict(index=index + 1, sha256=str(index + 1), kind='RESPONSE', request_digest=request_digest,
                 document_sha256=source, text=text, time_unix=index + 1),
            dict(index=index + 2, sha256=str(index + 2), kind='COMMITTED', source_sha256=source),
            dict(index=index + 3, sha256=str(index + 3), kind='R184_STAGE', source_sha256=source, stage=stage)])
    return dict(journal_id='synthetic', records=records)


class ParserTests(unittest.TestCase):
    def test_canonical_last_two_acts_ignore_think(self):
        self.assertEqual([frame['response']['index'] for frame in act_pairs(fixture())], [21, 41])

    def test_uncommitted_or_unstaged_response_is_not_an_act(self):
        for removed in (42, 43):
            evidence = fixture()
            evidence['records'] = [row for row in evidence['records'] if row['index'] != removed]
            self.assertEqual([frame['response']['index'] for frame in act_pairs(evidence)], [21])

    def test_missing_request_is_not_an_act(self):
        evidence = fixture()
        evidence['records'] = [row for row in evidence['records'] if row['index'] != 40]
        self.assertEqual([frame['response']['index'] for frame in act_pairs(evidence)], [21])

    def test_unmasked_request_rejected(self):
        evidence = fixture()
        evidence['records'][0]['masked'] = False
        with self.assertRaisesRegex(ValueError, 'masked'):
            act_pairs(evidence)

    def test_out_of_order_commit_rejected(self):
        evidence = fixture()
        evidence['records'][6]['index'] = 19
        with self.assertRaisesRegex(ValueError, 'order'):
            act_pairs(evidence)

    def test_context_commit_accepted(self):
        evidence = fixture()
        evidence['records'][6]['kind'] = 'CONTEXT_COMMITTED'
        self.assertEqual(len(act_pairs(evidence)), 2)

    def test_changed_source_rejected(self):
        verify_bytes(b'original', sha(b'original'))
        with self.assertRaisesRegex(ValueError, 'source_hash_changed'):
            verify_bytes(b'changed', sha(b'original'))

    def test_exact_response_link(self):
        frame = act_pairs(fixture())[1]
        payload = dict(response_record=41, response_digest='41', observations=[],
                       error='no caption found', format_status=dict(recovered_count=0))
        linked = response_link(event('Tool: ' + json.dumps(payload)), frame)
        self.assertEqual(linked['recovered_count'], 0)
        for field, wrong in (('response_record', 21), ('response_digest', 'older')):
            altered = dict(payload, **{field: wrong})
            with self.assertRaisesRegex(ValueError, 'identity_mismatch'):
                response_link(event('Tool: ' + json.dumps(altered)), frame)

    def test_exact_caption_text_not_near_match(self):
        frame = act_pairs(fixture())[1]
        message = event('Tool: Existing caption-game feedback.\nCaption 1, scene fixture, source ACT: "Synthetic second artifact."\nRank 63/65; accepted=false; novelty=rejected;')
        self.assertEqual(caption_matches(message, frame, [1])[0]['rank'], 63)
        old_frame = act_pairs(fixture())[0]
        with self.assertRaisesRegex(ValueError, 'not_in_selected'):
            caption_matches(message, old_frame, [1])

    def test_scored_meta_is_not_automatically_counted_as_caption(self):
        frame = act_pairs(fixture())[1]
        message = event('Tool: Existing caption-game feedback.\nCaption 1, scene fixture, source ACT: "Synthetic second artifact."\nRank 63/65; accepted=false; novelty=rejected;\nCaption 2, scene fixture, source ACT: "artifact"\nRank 1/65; accepted=true; novelty=new;')
        self.assertEqual(len(caption_matches(message, frame, [1])), 1)

    def test_peer_or_child_tool_wrapper_is_not_a_judge(self):
        frame = act_pairs(fixture())[1]
        payload = json.dumps(dict(response_record=41, response_digest='41'))
        for text in ('Tool: Peer synthetic: ' + payload, 'Tool: Your child says: ' + payload):
            with self.assertRaisesRegex(ValueError, 'not_attributed'):
                response_link(event(text), frame)
        with self.assertRaisesRegex(ValueError, 'not_attributed'):
            response_link(event('Tool: ' + payload, actor='parent'), frame)

    def test_manual_classification_is_bound_not_keyword_derived(self):
        evidence = fixture()
        note = dict(acts=[dict(index=21, category='meta_only', summary='Synthetic non-artifact.'),
                          dict(index=41, category='concrete', summary='Synthetic attempt.')],
                    checked_result='Unknown.', recent_parent='Observed.', next_artifact='Unknown.',
                    movement_status='unknown', event_ids=['parent:fixture'])
        public, _, _ = life_report(evidence, note)
        self.assertEqual(public['acts'][0]['category'], 'meta_only')
        self.assertEqual(public['recent_rendered_parent_event_count'], 1)
        self.assertEqual(public['newly_visible_guidance_or_Tool_between_ACTs'], [])
        serialized = json.dumps(public)
        self.assertNotIn('Synthetic first artifact.', serialized)
        self.assertNotIn('Astra: Check your arithmetic.', serialized)
        self.assertEqual(public['adapter_improvement'], 'unknown_not_tested_by_this_review')
        incorrect = copy.deepcopy(note)
        incorrect['acts'][1]['index'] = 31
        with self.assertRaisesRegex(ValueError, 'ACT_identity'):
            life_report(evidence, incorrect)

    def test_observer_arithmetic_is_not_child_execution(self):
        self.assertEqual(sum(range(1, 6)), 6 + 6 + 3)
        self.assertEqual(5 * 6 // 2, 15)
        self.assertEqual(17 + 8 - 6, 19)
        self.assertEqual(19 - 8 + 6, 17)
        self.assertEqual(34 - 15 + 7, 26)
        self.assertEqual(23 + 9 - 7, 25)
        self.assertEqual(sum((left + right) % 3 == 0 for left in range(6) for right in range(6)), 12)
        self.assertEqual(sum((left + right) % 4 == 0 for left in range(10) for right in range(10)), 25)
        edges = {(1, 2), (2, 3), (3, 4), (4, 5), (5, 1)}
        proposed = {1, 3, 5}
        self.assertTrue(any(left in proposed and right in proposed for left, right in edges))


if __name__ == '__main__':
    unittest.main()
