"""Separate prospectively registered FULL256 32-row arm; historical64 unchanged."""

from organism_v6 import orch_continual_batch as policy


ARM = 'ROHIN101_FULL256_MATH32_V1'
STATE = '93a036b93e2d41d2715230aaf2f2fa5382f4cbe404c743fd36dc37aba7f7c0d8'
SEED = 'ROHIN101_FULL256_MATH32_SAMPLE_20260915'


def first32(rows):
    policy.require(len(rows) == 39, 'frozen39_verified_cohort_required')
    policy.require(len({row['target_sha256'] for row in rows}) == 39, 'distinct_frozen39_required')
    return sorted(rows, key=lambda row: (row['provenance']['native_finished_unix'],
                                        row['provenance']['source_native_path']))[:32]


def sample(rows):
    policy.require(len(rows) == 32 and len({row['target_sha256'] for row in rows}) == 32, 'distinct32_required')
    return sorted(rows, key=lambda row: policy.text_sha(SEED + ':' + row['target_sha256']))[:12]


def adjudicate(rows, reviews):
    selected = sample(rows)
    policy.validate_review(selected, dict(reviews=reviews))
    passed = sum(review['status'] == 'PASS' for review in reviews)
    fatal = any(review['gold_status'] != 'VALID' or review['grounded_operations'] is not True or
                review['neutral_prefix_compatible'] is not True for review in reviews)
    accepted = passed >= 10 and not fatal
    review_map = {review['target_sha256']: review for review in reviews}
    exported = []
    for row in rows:
        review = review_map.get(row['target_sha256'])
        if review and review['status'] != 'PASS':
            continue
        exported.append(dict(row, semantic_status='PASS' if review else 'UNREVIEWED', admitted=False,
            trainingAllowed=False, batch_training_allowed=accepted, review=review, admission_mode=policy.MODE,
            eligibility_version='ROHIN98_SOURCE_BACKED_V2', original_semantic_status=row['semantic_status'],
            first_person_is_measurement_not_gate=True))
    return dict(arm=ARM, accepted=accepted, sample_size=12, sample_pass=passed, fatal_grounding_or_gold=fatal,
                population=32, exported_rows=len(exported)), exported
