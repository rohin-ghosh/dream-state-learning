import pytest

from gpu import orch_combined_l1_review_terminal8932 as review


@pytest.mark.parametrize('arm',['FULL','OFF'])
@pytest.mark.parametrize('position',range(4))
def test_author_review_binding_and_separate_coherence(monkeypatch,arm,position):
    text='Synthetic CPU fixture, not native held output.'
    hashes={key:list(value) for key,value in review.REVIEWED.items()}
    hashes[arm][position]=review.behavior.text_hash(text)
    monkeypatch.setattr(review,'REVIEWED',hashes)
    annotation=review.annotate(text,arm,position)
    described=review.behavior.describe(text,annotation)
    assert described['semantic']['distinct_paths_considered']==1
    assert described['semantic']['distinct_alternatives_considered']==0
    assert described['semantic']['paths_rejected_with_grounded_reason']==0
    assert described['coherence']['judgment']==('MIXED' if arm=='FULL' and position==0 else 'COHERENT')
    assert annotation['R106']['departures_returns']==annotation['R106']['terminal_checks']==0
    assert not annotation['parent_access'] and annotation['full_output_read']


def test_unread_output_rejected():
    with pytest.raises(AssertionError,match='not_author_reviewed'):
        review.annotate('Unreviewed output','FULL',0)
