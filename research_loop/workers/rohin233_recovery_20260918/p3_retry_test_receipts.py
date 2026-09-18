import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from p3_retry_receipts import learning_projection, merge
import p3_retry_receipts as receipts
from p3_renewed_receipts import proof


class RetryReadinessTests(unittest.TestCase):
    def setUp(self):
        self.anchor = dict(journal_id='same', loaded_index=20, loaded_sha256='load')
        self.chunk = dict(journal_id='same', through=dict(index=21, sha256='next'), caught_up=True,
            continuity=[dict(index=21, previous_sha256='load')], bytes_read=123, records=[], learning=[])

    def test_incremental_window_anchored_in_actual_retry_LOAD(self):
        result = merge(None, self.chunk, self.anchor)
        self.assertEqual(result['through']['index'], 21)
        self.assertEqual(result['bytes_read'], 123)

    def test_wrong_journal_or_chain_cannot_be_ready(self):
        for chunk in (dict(self.chunk, journal_id='old'),
                dict(self.chunk, continuity=[dict(index=22, previous_sha256='load')]),
                dict(self.chunk, continuity=[dict(index=21, previous_sha256='wrong')])):
            with self.assertRaises(ValueError):
                merge(None, chunk, self.anchor)

    def test_empty_window_preserves_cursor_without_rescanning(self):
        prior = merge(None, self.chunk, self.anchor)
        empty = dict(self.chunk, continuity=[], through=None, bytes_read=0)
        result = merge(prior, empty, self.anchor)
        self.assertEqual(result['through'], prior['through'])
        self.assertEqual(result['bytes_read'], prior['bytes_read'])

    def test_other_incarnation_cache_rejected(self):
        prior = merge(None, self.chunk, self.anchor)
        prior['loaded_sha256'] = 'old'
        with self.assertRaises(ValueError):
            merge(prior, dict(self.chunk, continuity=[]), self.anchor)

    def test_actual_recipe_policy_not_assumed_from_source(self):
        record = dict(index=25, kind='SLEEP_RECIPE', sha256='bound',
            document=dict(new_rows=3, new_presentations=16, secret_target='not exported'))
        projected = learning_projection(record)
        self.assertNotIn('learn_row_policy', projected)
        self.assertNotIn('secret_target', projected)
        record['document'].update(learn_row_policy='R227_ALL_AUTHENTIC_CHILD_ROWS_V1',
            active_semantic_filters=[], semantic_row_exclusion=False)
        self.assertFalse(learning_projection(record)['semantic_row_exclusion'])

    def test_technical_exclusions_remain_visible(self):
        record = dict(index=26, kind='TARGET_ELIGIBILITY', sha256='eligibility', document=dict(
            new_row_sha256=['first', 'second'], rehearsal_row_sha256=[],
            excluded=[dict(reason='technical', target='private')], raw_modified=False))
        projected = learning_projection(record)
        self.assertEqual(projected['eligible_new'], 2)
        self.assertEqual(projected['excluded_count'], 1)
        self.assertNotIn('excluded', projected)

    def test_COMPLETE_is_receipt_not_binary_rehash_claim(self):
        record = dict(index=40, kind='SLEEP_COMPLETE', sha256='complete', document=dict(
            cycle=154, status='COMPLETE', total_optimizer_steps=600, checkpoint_sha256={'adapter': 'hash'}))
        projected = learning_projection(record)
        self.assertEqual(projected['cycle'], 154)
        self.assertFalse(projected['durable_binary_rehash'])

    def test_publication_without_actual_render_or_ACT_is_not_readiness(self):
        loaded = dict(original_journal_id='same', loaded=dict(index=20))
        publication = dict(id='new-parent', sha256='source')
        evidence = dict(journal_id='same', records=[])
        self.assertEqual(proof(publication, 'parent', evidence, [], loaded)['status'],
            'PUBLISHED_NOT_YET_RENDERED_IN_WINDOW')

    def test_authenticated_preload_turn_counts_even_before_live_parent_start(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            attempt = root / 'turns/parent_000000000315'
            attempt.mkdir(parents=True)
            row = dict(status='PUBLISHED', message='Historical source; recovery is not feedback.',
                publication=dict(id='own-parent', sha256='source'))
            (attempt / 'RESULT.json').write_text(json.dumps(row))
            (attempt / 'PUBLISH_INTENT.json').write_text(json.dumps(dict(speaker='Astra', message=row['message'])))
            (root / 'P3_RETRY_PRELOAD_RESULT.json').write_text(json.dumps(dict(status='PUBLISHED',
                attempt=attempt.name, result_sha256=receipts.observer.digest(attempt / 'RESULT.json'))))
            with patch.object(receipts, 'HERE', root), patch.object(receipts.previous.p3_receipts, 'PARENT', root / 'turns'):
                evidence = receipts.actual_parent_attempts(float('inf'))
            self.assertEqual(evidence[0]['generation_phase'], 'PRELOAD_PARENT_QUEUE')
            self.assertEqual(evidence[0]['publication'], row['publication'])
            self.assertFalse(evidence[0]['provider_request'])


if __name__ == '__main__':
    unittest.main()
