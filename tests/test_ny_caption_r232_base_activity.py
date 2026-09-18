from copy import deepcopy

import pytest

from research_loop.workers.rohin221_continuous_caption_20260918.base_activity import supplement, verified_empty


def evidence():
    return dict(complete_controller_and_scorer_history=True, observed_unix=7201,
        hard_end_unix=3500, player_present=False, scorer_present=False,
        units={role: dict(main_pid=0, result='timeout', exit_unix=3500) for role in ('player', 'scorer')},
        controller_event_times=[3000])


def primary():
    return dict(observed_cut_utc='1970-01-01T02:00:01+00:00', players=[
        dict(player=name, UTC_windows=[]) for name in ('frozen_base_no_optimizer', 'P3_parented_C2')])


def test_verified_retained_inactivity_not_omitted_or_inferred_for_other_players():
    original = primary()
    before = deepcopy(original)
    report = supplement(original, evidence(), 'a' * 64)
    base, parented = report['players']
    assert base['status'] == 'VERIFIED_NO_ACTIVITY_EXPIRED_BUDGET'
    assert base['counts']['ACT_attempts'] == base['counts']['newly_scored_strings'] == 0
    assert base['counts']['acceptance_rate']['fraction'] is None
    assert parented['status'] == 'MISSING_NOT_ZERO' and parented['counts'] is None
    assert original == before


@pytest.mark.parametrize('change', [dict(complete_controller_and_scorer_history=False),
    dict(observed_unix=7199), dict(player_present=True), dict(scorer_present=True),
    dict(hard_end_unix=4000), dict(controller_event_times=[3600])])
def test_missing_or_contradictory_evidence_never_manufactures_zero(change):
    assert not verified_empty(dict(evidence(), **change), 3600, 7200)


def test_missing_remote_collection_preserves_unknown():
    report = supplement(primary(), dict(complete_controller_and_scorer_history=False), 'b' * 64)
    assert all(row['counts'] is None for row in report['players'])


def test_observed_activity_contradiction_fails_closed():
    document = primary()
    document['players'][0]['UTC_windows'] = [dict(window_start_utc='1970-01-01T01:00:00+00:00',
        window_end_utc='1970-01-01T02:00:00+00:00', ACT_attempts=1)]
    with pytest.raises(ValueError, match='contradicts'):
        supplement(document, evidence(), 'c' * 64)
