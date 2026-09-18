import hashlib
import json

import pytest

from gpu import ny_caption_data as data
from research_loop.workers.r177_caption_game_stage1_20260917.data_judge import rank200_calibration_v3 as calibration


def row(index, mean=1.5, contest='fixture'):
    return dict(contest_id=contest, caption='synthetic fixture '+str(index), counts=[50, 50, 0], votes=100,
        mean=mean, published_rank=index, full_original_contest_rows=400,
        caption_family_sha256=hashlib.sha256(str(index).encode()).hexdigest())


def test_original_rank200_does_not_shift_when_earlier_rating_is_invalid():
    header='rank,caption,mean,precision,votes,not_funny,somewhat_funny,funny\n'
    lines=[f'{index},synthetic {index},1.5,0,100,50,50,0\n' for index in range(1, 241)]
    lines[0]='1,invalid fixture,1.5,0,0,0,0,0\n'
    summary, unique, ranks=calibration.raw_contest((header+''.join(lines)).encode(), '101')
    assert summary['original_rows']==240 and summary['invalid_rating_rows']==1
    assert ranks[200]['caption']=='synthetic 200'
    assert summary['literal_rank200_positive_vote_mass']==0.5
    assert summary['full_top200_positive_vote_mass'] is None
    assert summary['literal_rank200_coverage']==200/240


def test_invalid_or_repeated_rank_is_not_invented():
    with pytest.raises(ValueError, match='released_ranks|rank_index_origin'):
        calibration.raw_contest(b'rank,caption,mean,votes,not_funny,somewhat_funny,funny\n2,fixture,1.5,100,50,50,0\n', '101')


def test_read_budget_is_charged_before_content_and_rereads(tmp_path, monkeypatch):
    reference=data.private_write(tmp_path.resolve()/'fixture.json', {'value': 1})
    reader=calibration.Reader(reference['bytes'])
    assert reader.json(reference)=={'value': 1}
    with pytest.raises(ValueError, match='read_budget_before_IO'):
        reader.json(reference)
    reader=calibration.Reader(reference['bytes']-1)
    monkeypatch.setattr(type(tmp_path), 'read_bytes', lambda unused: pytest.fail('read before charge'))
    with pytest.raises(ValueError, match='read_budget_before_IO'):
        reader.json(reference)


def test_hash_changes_rejected(tmp_path):
    reference=data.private_write(tmp_path.resolve()/'fixture.json', {'value': 1})
    with pytest.raises(ValueError, match='exact_read_hash'):
        calibration.Reader().json(dict(reference, sha256='0'*64))


def test_missing_or_conflicting_rank_join_remains_missing():
    first=row(1)
    assert calibration.join_clean([first], {}, 400)[0]['published_rank'] is None
    different=dict(first, counts=[0, 0, 100])
    assert calibration.join_clean([first], {first['caption_family_sha256']: different}, 400)[0]['published_rank'] is None


def test_panel_fixed_small_and_from_fitting_only():
    groups={str(index): [row(rank, contest=str(index)) for rank in (190, 200, 210)] for index in range(8)}
    first=calibration.fixed_panel(groups)
    assert first==calibration.fixed_panel(dict(reversed(list(groups.items()))))
    assert len(first)==12 and len({item['contest_id'] for item in first})==4
    assert {item['published_rank'] for item in first}=={190, 200, 210}
    with pytest.raises(ValueError, match='panel_support'):
        calibration.fixed_panel({'only_one': [row(rank) for rank in (190, 200, 210)]})


def test_reference_transform_is_monotone_not_new_ranking_evidence():
    result=[calibration.reference_win(value, [-2, 0, 1]) for value in (-4, -1, 0, 2)]
    assert result==sorted(result) and len(set(result))==4
    assert calibration.CONTRACT['reference_transform_improves_ordering'] is False


def test_null_threshold_preserved_when_low_precision_or_coverage():
    assert calibration.select_quality_threshold([0.1]*100, [0]*100, ['a']*50+['b']*50)['threshold'] is None
    assert calibration.select_quality_threshold([0.9]+[0.1]*99, [1]+[0]*99, ['a']*50+['b']*50)['threshold'] is None
    assert calibration.CONTRACT['original_threshold_unchanged'] is True


def test_threshold_requires_contest_support_and_registered_confidence():
    output=calibration.select_quality_threshold([0.9]*40+[0.1]*60, [1]*40+[0]*60, ['a','b']*50)
    assert output['threshold']==0.9 and output['precision_wilson95_lower']>=0.8
    output=calibration.select_quality_threshold([0.9]*40+[0.1]*60, [1]*40+[0]*60, ['a']*40+['b','c','d']*20)
    assert output['threshold'] is None


def test_full_pool_precision_not_inverse_recall_or_sample_top5():
    rows=[row(index, mean=3-index/400) for index in range(1, 401)]
    output=calibration.full_pool_metrics(rows, [float(-index) for index in range(1,401)])
    assert output['macro_precision_predicted_top200_in_original_true_top_half']==1
    assert output['macro_recall_original_true_top200_in_predicted_clean_top_half']==1
    assert output['scored_clean_rows']==400 and output['sample64_top5_used'] is False
    assert output['all_raw_submissions_scored'] is False


def test_missing_rank_uses_verified_full_source_order_not_filtered_rows():
    raw=b'caption,mean,votes,not_funny,somewhat_funny,funny\nfirst fixture,1.8,100,20,80,0\nsecond fixture,1.5,100,50,50,0\n'
    summary, unique, ranks=calibration.raw_contest(raw, '101')
    assert summary['source_rank_origin']=='VERIFIED_MEAN_ORDERED_SOURCE_ROW_POSITION'
    assert ranks[2]['caption']=='second fixture'
    with pytest.raises(ValueError, match='verified_descending_mean'):
        calibration.raw_contest(b'caption,mean,votes,not_funny,somewhat_funny,funny\nfirst fixture,1.5,100,50,50,0\nsecond fixture,1.8,100,20,80,0\n', '101')


def test_zero_based_source_rank_normalizes_exactly_to_human_ordinal200():
    header='rank,caption,mean,precision,votes,not_funny,somewhat_funny,funny\n'
    raw=(header+''.join(f'{index},synthetic {index},1.5,0,100,50,50,0\n' for index in range(240))).encode()
    summary, unique, ranks=calibration.raw_contest(raw, '101')
    assert ranks[200]['caption']=='synthetic 199'
    assert summary['source_rank_origin']=='EXPLICIT_ZERO_BASED_RANK_PLUS_ONE'
