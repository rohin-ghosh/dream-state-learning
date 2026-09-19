import pytest

from research_loop.workers.rohin221_continuous_caption_20260918.hourly_report import rate, window_counts


def test_acceptance_denominator_not_attempts_and_repeats_not_novel():
    rows = [dict(unix=100,origin_sha256='ACT',parsed=158,scored=125,accepted=82,
                 new_pixels=27,cached=33,format_fault=1,routing_ambiguity=1)]
    result = window_counts(rows,rows,50,200,planned_unknown=1)
    assert result['ACT_attempts'] == 1
    assert result['accepted_semantic_repeats'] == 55
    assert result['acceptance_rate'] == dict(numerator=82,denominator=125,fraction=82/125)
    assert result['new_pixel_fraction']['fraction'] == 27/125
    assert result['format_fault_attempts'] == result['routing_ambiguity_attempts'] == 1
    assert result['planned_unknown_attempts'] == 1


def test_absolute_half_open_window_no_extrapolation():
    rows = [dict(unix=100,origin_sha256='first',scored=1,new_pixels=1),
            dict(unix=200,origin_sha256='next-hour',scored=1,new_pixels=1)]
    result = window_counts(rows,rows,100,200)
    assert result['ACT_attempts'] == result['new_pixels'] == 1
    assert result['window_end_utc'] == '1970-01-01T00:03:20+00:00'
    assert rate(0,0)['fraction'] is None


def test_transport_failure_not_miscounted_as_judge_or_format_failure():
    actual = [dict(unix=100,origin_sha256='ACT',transport_failure=True)]
    result = window_counts([],actual,50,200)
    assert result['ACT_attempts'] == result['transport_failure_attempts'] == 1
    assert result['ACTs_reaching_scorer'] == result['newly_scored_strings'] == result['format_fault_attempts'] == 0
    with pytest.raises(ValueError,match='duplicate_ACT'):
        window_counts([],actual+actual,50,200)
