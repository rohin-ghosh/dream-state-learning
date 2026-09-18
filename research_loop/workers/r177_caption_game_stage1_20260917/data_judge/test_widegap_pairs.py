import copy

import pytest

from research_loop.workers.r177_caption_game_stage1_20260917.data_judge import widegap_pairs as pairs


def row(index, counts, contest='101'):
    votes=sum(counts)
    return dict(contest_id=contest, scene='synthetic neutral scene '+contest, caption='fixture '+str(index),
        caption_family_sha256=str(index).zfill(64), counts=counts, votes=votes,
        mean=sum((position+1)*count for position,count in enumerate(counts))/votes)


def test_mean_order_explicitly_differs_from_old_positive_vote_mass():
    first=row(1,[60,0,40]); second=row(2,[30,70,0])
    target=pairs.pair_target(first,second)
    assert target['winner']==1 and target['mean_gap']>=0.10
    assert sum(first['counts'][1:])/first['votes'] < sum(second['counts'][1:])/second['votes']


def test_gap_votes_and_scene_guards():
    assert pairs.pair_target(row(1,[50,50,0]),row(2,[51,49,0])) is None
    assert pairs.pair_target(row(1,[1,0,9]),row(2,[100,0,0])) is None
    with pytest.raises(ValueError,match='within_contest'):
        pairs.pair_target(row(1,[0,0,100]),row(2,[100,0,0],contest='102'))


def test_balanced_full_contest_cycles_and_multiple_bucket_passes():
    rows=[row(index,[index,100-index,0],contest=name) for name in ('101','102','103') for index in range(3,99,3)]
    first=pairs.PairSchedule(rows,177); second=pairs.PairSchedule(copy.deepcopy(rows),177)
    outputs=[first.draw() for unused in range(360)]
    assert outputs==[second.draw() for unused in range(360)]
    counts={name:sum(left['contest_id']==name for left,right in outputs) for name in first.names}
    assert set(counts.values())=={120}
    assert all(min(values)>0 for values in first.bucket_passes.values())
    assert all(abs(left['mean']-right['mean'])>0.1 for left,right in outputs)
    assert all(left['contest_id']==right['contest_id'] and left['caption_family_sha256']!=right['caption_family_sha256'] for left,right in outputs)


def test_selection_uses_both_metrics_not_unused_top200():
    first=dict(macro_mean_rating_spearman=0.2,macro_precision_predicted_top200_in_original_true_top_half=0.9)
    second=dict(macro_mean_rating_spearman=0.3,macro_precision_predicted_top200_in_original_true_top_half=0.6)
    assert pairs.selection_key(first)>pairs.selection_key(second)
    assert pairs.EVALUATION_STEPS==[8,1563,3125,4688,6250]


def test_fixed_sample_is_not_full_top200_and_measured_total_budget():
    rows = [dict(row(index,[100-index,index,0]), published_rank=100-index, full_original_contest_rows=1000) for index in range(10,90)]
    result = pairs.sampled_selection_metrics(rows,list(range(len(rows))))
    assert result['role']=='FIXED_MODEL_SELECTION_SAMPLE_NOT_FULL_TOP200'
    assert result['full_contest_top200_measured'] is False
    assert result['sample_top_k_min']==16
    admitted = pairs.measured_budget(10,100,100000,130000,20000)
    assert admitted['can_complete'] and admitted['conservative_remaining_seconds']==15025
    rejected = pairs.measured_budget(6,20,100000,130000,20000)
    assert not rejected['can_complete']


def test_quality_never_passes_from_rank_only_or_null_threshold():
    rows=[dict(published_rank=1,contest_id=str(index%4)) for index in range(100)]
    assert pairs.quality_audit(rows,[0.9]*100,None)['status']=='BLOCKED_RANK200_QUALITY_POINT'
    result=pairs.quality_audit(rows,[0.9]*100,0.8)
    assert result['status'].startswith('PROVISIONAL_QUALITY_POINT') and result['full_judge_usable'] is False
