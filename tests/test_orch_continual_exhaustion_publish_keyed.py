from copy import deepcopy
import unittest

from gpu import orch_continual_exhaustion_publish_keyed as keyed
from tests.test_orch_continual_exhaustion_publish import ExhaustionPublisherTests


class KeyedReviewTests(unittest.TestCase):
    def setUp(self):
        row, review = ExhaustionPublisherTests().fixture()
        self.rows = [row]
        self.digest = keyed.registry_digest(self.rows)
        self.review = {key: value for key, value in review.items() if key not in keyed.HASH_FIELDS}
        self.review['row_key'] = 0

    def validate(self, review=None, rows=None, digest=None):
        return keyed.validate_keyed_reviews(rows or self.rows,
            dict(reviews=[review or self.review]), digest or self.digest)

    def test_binding_is_host_assembled_without_mutation(self):
        previous = deepcopy(self.review)
        bound = self.validate()[0]
        self.assertEqual(bound['target_sha256'], self.rows[0]['target_sha256'])
        self.assertEqual(self.review, previous)

    def test_model_hashes_rejected_not_repaired(self):
        for field in keyed.HASH_FIELDS:
            with self.assertRaisesRegex(ValueError, 'model_hash_fields_forbidden'):
                self.validate(dict(self.review, **{field: 'incorrect'}))

    def test_unknown_bool_missing_and_duplicate_keys_rejected(self):
        for key in [True, '0', -1, 1, None]:
            with self.assertRaises(ValueError):
                self.validate(dict(self.review, row_key=key))
        with self.assertRaises(ValueError):
            keyed.validate_keyed_reviews(self.rows, dict(reviews=[self.review, self.review]), self.digest)

    def test_dispatch_bytes_cannot_change(self):
        rows = deepcopy(self.rows)
        rows[0]['target'] += '\nchanged'
        with self.assertRaisesRegex(ValueError, 'immutable_dispatch_registry_mismatch'):
            self.validate(rows=rows)

    def test_fulltext_and_evidence_still_required(self):
        for changes in [dict(full_text_read=False), dict(evidence_line_ids=[999999])]:
            with self.assertRaises(ValueError):
                self.validate(dict(self.review, **changes))

    def test_schema_has_key_and_no_opaque_hashes(self):
        item = keyed.keyed_schema(6)['properties']['reviews']['items']
        self.assertEqual(item['properties']['row_key']['enum'], list(range(6)))
        self.assertFalse(set(keyed.HASH_FIELDS) & set(item['properties']))


if __name__ == '__main__':
    unittest.main()
