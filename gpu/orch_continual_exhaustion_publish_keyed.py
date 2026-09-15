"""CPU-only prospective response binding; not wired into a live publisher."""

from copy import deepcopy
import hashlib
import json

from gpu import orch_continual_exhaustion_publish as original


HASH_FIELDS = ('target_sha256', 'raw_call_sha256', 'student_prefix_sha256')


def registry_digest(rows):
    return hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()


def keyed_schema(count):
    original.policy.require(type(count) is int and 1 <= count <= 6, 'bounded_review_group')
    schema = original.review_schema()
    item = schema['properties']['reviews']['items']
    for field in HASH_FIELDS:
        del item['properties'][field]
        item['required'].remove(field)
    item['properties']['row_key'] = dict(type='integer', enum=list(range(count)))
    item['required'].append('row_key')
    return schema


def validate_keyed_reviews(rows, result, expected_registry_sha256):
    original.policy.require(registry_digest(rows) == expected_registry_sha256,
                            'immutable_dispatch_registry_mismatch')
    original.policy.require(1 <= len(rows) <= 6, 'bounded_review_group')
    reviews = deepcopy(result['reviews'])
    keys = [review.get('row_key') for review in reviews]
    original.policy.require(all(type(key) is int for key in keys)
                            and sorted(keys) == list(range(len(rows))), 'exact_unique_response_keys')
    for review in reviews:
        original.policy.require(not any(field in review for field in HASH_FIELDS),
                                'model_hash_fields_forbidden')
        row = rows[review.pop('row_key')]
        review.update(target_sha256=row['target_sha256'],
                      raw_call_sha256=row['provenance']['raw_call_sha256'],
                      student_prefix_sha256=row['student_prefix_sha256'])
    return original.validate_reviews(rows, dict(reviews=reviews))
