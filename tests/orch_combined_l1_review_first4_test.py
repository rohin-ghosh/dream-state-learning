"""The author review must not generalize to unread or changed output."""

import pytest

from gpu.orch_combined_l1_review_first4 import annotate, REVIEWED


@pytest.mark.parametrize('condition,arm', REVIEWED)
def test_unread_output_cannot_receive_author_review(condition, arm):
    with pytest.raises(AssertionError, match='not_an_author_reviewed_output'):
        annotate('An unread response', condition, arm, 0)


def test_only_sixteen_frozen_outputs_are_in_review():
    hashes = [digest for group in REVIEWED.values() for digest in group]
    assert len(hashes) == len(set(hashes)) == 16


@pytest.mark.parametrize('arm', ['FULL', 'OFF'])
def test_unread_dev_output_cannot_receive_author_review(arm):
    from gpu.orch_combined_l1_review_dev_first4 import annotate as annotate_dev
    with pytest.raises(AssertionError, match='not_an_author_reviewed_output'):
        annotate_dev('An unread response', arm, 0)
