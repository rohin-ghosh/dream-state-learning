import hashlib

import pytest

from research_loop.workers.rohin221_continuous_caption_20260918.seed_observer import (
    annotate_caption, exposure_epoch,
)


RENDER = dict(treatment_id='R230_FROZEN_BASE_JOKE_SEEDS_V1_N2',published_unix=1,
    first_rendered_request=dict(index=2295,sha256='a'*64,started_unix=2))


def test_generation_request_not_publication_or_scoring_time_sets_epoch():
    assert exposure_epoch(dict(index=2294,sha256='b'*64),RENDER)=='pre_seed'
    assert exposure_epoch(dict(index=2295,sha256='a'*64),RENDER).startswith('post_')
    assert exposure_epoch(dict(index=2296,sha256='c'*64),RENDER).startswith('post_')
    with pytest.raises(ValueError,match='same_REQUEST_hash'):
        exposure_epoch(dict(index=2295,sha256='d'*64),RENDER)
    assert exposure_epoch(None,RENDER)=='source_request_unknown'
    assert exposure_epoch(dict(index=2295),dict(first_rendered_request=None))=='rendering_unproven'


def test_seed_echo_is_descriptive_not_a_score_or_learn_filter():
    caption='Actual supplied caption.'
    packet=dict(examples=[dict(seed_id='seed',caption_sha256=hashlib.sha256(caption.encode()).hexdigest())])
    after=annotate_caption(caption,dict(index=2295,sha256='a'*64),RENDER,packet)
    assert after['exact_seed_reuse_after_exposure']
    assert after['raw_scoring_unchanged'] and after['training_eligibility_unchanged']
    before=annotate_caption(caption,dict(index=2200,sha256='b'*64),RENDER,packet)
    assert not before['exact_seed_reuse_after_exposure']
    different=annotate_caption('New wording.',dict(index=2296,sha256='b'*64),RENDER,packet)
    assert different['exploration_classification']=='not_established_by_this_observer'
