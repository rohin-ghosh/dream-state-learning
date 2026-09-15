"""Projection preserves full row and all publisher reporting metadata."""

from copy import deepcopy
import pytest
from gpu.orch_combined_l1_native_feed import project, REPORTING_FIELDS, validate_registry_source


def test_registry_purpose_matches_frozen_admission_policy():
    from organism_v6.orch_combined_l1_sampled_policy_v1 import PURPOSE
    validate_registry_source(dict(purpose=PURPOSE, family='math'))


@pytest.mark.parametrize('purpose,family', [('L1_EXTERNAL_GENERATION', 'math'),
    ('PARENTING', 'math'), ('L1_RICHNESS_GENERATION', 'route')])
def test_registry_purpose_does_not_waive_scope(purpose, family):
    with pytest.raises(AssertionError):
        validate_registry_source(dict(purpose=purpose, family=family))


def test_projection_is_lossless_and_does_not_requalify_or_edit_target():
    wrapped = dict(row=dict(target='unchanged', target_sha256='target', admitted=False,
        semantic_status='UNREVIEWED', student_prefix=[dict(role='user', content='question')]),
        eligibility=dict(policy='original', eligible=True, **{key: None for key in REPORTING_FIELDS}))
    before = deepcopy(wrapped)
    entry = project(wrapped, 'batch', 0)
    assert wrapped == before and entry['row'] == before['row']
    assert entry['publisher_original_eligibility'] == before['eligibility']
    assert dict(entry['eligibility'], **entry['publisher_reporting_metadata']) == before['eligibility']
    assert entry['row']['admitted'] is False and entry['row']['semantic_status'] == 'UNREVIEWED'


def test_unexpected_missing_reporting_metadata_blocks_projection():
    with pytest.raises(AssertionError):
        project(dict(row={}, eligibility={}), 'batch', 0)
