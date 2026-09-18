import copy
import json
import unittest

from audit import adjudicate
from review_queue import build_queue
from test_audit import fixture


class ReviewQueueTests(unittest.TestCase):
    def test_pending_never_assigns_semantic_level(self):
        evidence, _ = fixture()
        result, _ = build_queue(evidence, 'test')
        self.assertFalse(result['automatic_semantic_review'])
        self.assertEqual(result['new_semantic_judgments'], 0)
        self.assertNotIn('level', result['items'][0])

    def test_no_lexical_classifier_excludes_other_languages(self):
        evidence, _ = fixture()
        for row in evidence['records']:
            if row['kind'] == 'REQUEST':
                row['external'][0]['text'] = '这是新的中文信息。'
        result, _ = build_queue(evidence, 'test')
        self.assertEqual(result['pending_rendered_input_count'], 1)

    def test_validated_annotations_remove_input_but_not_new_followups(self):
        evidence, annotation = fixture()
        earlier = copy.deepcopy(evidence)
        earlier['records'] = [row for row in earlier['records'] if row['index'] < 30]
        earlier['through'] = {'index': 23}
        _, cursor = build_queue(earlier, 'test')
        trace = adjudicate(evidence, annotation)
        result, cursor = build_queue(evidence, 'test', [trace], cursor)
        self.assertEqual(result['pending_rendered_input_count'], 0)
        self.assertEqual(result['new_ACT_count'], 1)
        self.assertEqual(result['items'][0]['kind'], 'NEW_ACTS_REQUIRE_SEMANTIC_REVIEW')
        repeated, _ = build_queue(evidence, 'test', [trace], cursor)
        self.assertEqual(repeated['new_ACT_count'], 0)
        self.assertEqual(repeated['pending_output_windows'], 1)

    def test_bounded_queue_rotates_backlog(self):
        evidence, _ = fixture()
        template = evidence['records'][0]['external'][0]
        for number in range(8):
            event = dict(template, event_id=f'parent:inbox:extra{number}')
            evidence['records'][0]['external'].append(event)
        first, cursor = build_queue(evidence, 'test', limit=2)
        second, _ = build_queue(evidence, 'test', previous=cursor, limit=2)
        self.assertEqual(first['displayed'], 2)
        self.assertEqual(first['pending_total'], 9)
        self.assertTrue({item['queue_id'] for item in first['items']}.isdisjoint(
            {item['queue_id'] for item in second['items']}))

    def test_public_refs_do_not_include_raw_content(self):
        evidence, _ = fixture()
        result, _ = build_queue(evidence, 'test')
        encoded = json.dumps(result)
        self.assertNotIn('Incorrect. Check the sign', encoded)
        self.assertNotIn('"text":', encoded)
        self.assertIn('sha256', encoded)

    def test_wrong_journal_cursor_rejected(self):
        evidence, _ = fixture()
        with self.assertRaisesRegex(ValueError, 'incarnation'):
            build_queue(evidence, 'test', previous={'journal_id': 'other'})

    def test_cursor_cannot_rollback(self):
        evidence, _ = fixture()
        with self.assertRaisesRegex(ValueError, 'backwards'):
            build_queue(evidence, 'test', previous={'through_index': 50})

    def test_pending_input_without_child_output_is_not_proof(self):
        evidence, _ = fixture()
        evidence['records'] = evidence['records'][:1]
        evidence['through'] = {'index': 10}
        result, _ = build_queue(evidence, 'test')
        self.assertEqual(result['items'][0]['following_outputs'], [])
        self.assertIsNone(result['items'][0]['next_actual_ACT'])
        self.assertFalse(result['automatic_semantic_review'])


if __name__ == '__main__':
    unittest.main()
