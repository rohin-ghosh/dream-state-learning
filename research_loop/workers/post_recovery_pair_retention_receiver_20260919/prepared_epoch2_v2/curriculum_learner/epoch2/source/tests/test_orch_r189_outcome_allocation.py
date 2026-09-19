"""Synthetic outcome accounting and effort heuristics, not learner results."""

from copy import deepcopy

import pytest

from gpu.orch_r189_outcome_allocation import OutcomeAllocation, counts


def test_new_failure_and_success_change_allowance_not_child_readiness():
    policy = OutcomeAllocation()
    assert policy.guidance('new')['mode'] == 'GUIDED_EXPLORATION'
    failed = counts(requested=5, evaluated=5)
    policy.record('new', failed)
    assert policy.guidance('new')['mode'] == 'GUIDED_EXPLORATION'
    policy.record('new', failed)
    assert policy.guidance('new')['mode'] == 'SUSTAINED_FAILURE'
    assert policy.guidance('new')['think_segments_budget'] == 3
    success = counts(requested=5, evaluated=5, successes=2, quality_accepted=2)
    policy.record('new', success)
    assert policy.guidance('new')['mode'] == 'ASSESS_EVIDENCE'
    policy.record('new', success)
    guidance = policy.guidance('new')
    assert guidance['mode'] == 'CONSOLIDATE_SUCCESS'
    assert guidance['think_segments_budget'] == 1
    assert 'small changes' in guidance['instruction']
    assert policy.guidance('other')['mode'] == 'GUIDED_EXPLORATION'


def test_unknowns_never_supply_or_dilute_evaluated_success_rate():
    policy = OutcomeAllocation()
    policy.record('a', counts(requested=4, evaluated=4, successes=1, quality_accepted=1))
    report = policy.record('a', counts(requested=100, unknown=1, not_dispatched=99))
    assert report['running_success_rate'] == 0.25
    assert report['guidance_next']['mode'] == 'UNOBSERVED_OUTCOME'
    assert report['think_token_share'] is None
    assert report['stage_tokens'] is None
    assert not report['retained_learning_claim']


def test_redundant_quality_does_not_earn_novel_progress():
    policy = OutcomeAllocation()
    report = policy.record('a', counts(requested=6, evaluated=4, quality_accepted=4,
                                     repeats=4, cached=2))
    assert report['running_success_rate'] == 0
    assert report['guidance_next']['rates']['recent']['quality_acceptance_rate'] == 1
    assert report['guidance_next']['mode'] == 'REDUNDANT_DATA'


def test_stage_shares_are_exact_and_state_persists_without_mutable_aliases():
    policy = OutcomeAllocation()
    observation = counts(requested=2, evaluated=2, successes=1, quality_accepted=1)
    report = policy.record('a', observation, cycle_metrics=dict(THINK=30, ACT=70, LEARN=20))
    assert report['think_token_share'] == 0.3
    assert report['think_share_including_learn'] == 0.25
    assert report['guess_volume'] == 2
    policy.record('a', observation)
    snapshot = policy.snapshot()
    restored = OutcomeAllocation(snapshot)
    assert restored.guidance('a') == policy.guidance('a')
    snapshot['environments']['a']['totals']['successes'] = 0
    observation['successes'] = 0
    report['observation']['successes'] = 0
    assert restored.guidance('a')['rates']['lifetime']['success_rate'] == 0.5
    for unused in range(5):
        policy.record('a', counts(requested=1, evaluated=1))
    assert len(policy.snapshot()['environments']['a']['recent']) == 3
    assert OutcomeAllocation(policy.snapshot()).snapshot() == policy.snapshot()


@pytest.mark.parametrize('value', [True, -1, 1.5, '1'])
def test_invalid_accounting_rejects_before_mutation(value):
    policy = OutcomeAllocation()
    before = policy.snapshot()
    with pytest.raises(ValueError):
        policy.record('a', dict(counts(), unknown=value))
    assert policy.snapshot() == before
    with pytest.raises(ValueError):
        policy.record('a', counts(), cycle_metrics=dict(THINK=value, ACT=0, LEARN=0))
    assert policy.snapshot() == before


def test_corrupt_snapshot_does_not_reset_to_exploration():
    policy = OutcomeAllocation()
    policy.record('a', counts(requested=1, evaluated=1))
    state = policy.snapshot()
    broken = deepcopy(state)
    broken['environments']['a']['cycles'] = 3
    with pytest.raises(ValueError, match='environment_state'):
        OutcomeAllocation(broken)
    broken = deepcopy(state)
    broken['environments']['a']['totals']['evaluated'] = 0
    with pytest.raises(ValueError):
        OutcomeAllocation(broken)


def test_boolean_success_requires_actual_evaluation_denominator():
    with pytest.raises(ValueError):
        counts(requested=1, unknown=1, successes=1)
    with pytest.raises(ValueError):
        counts(requested=1, evaluated=1, quality_accepted=1, repeats=1, successes=1)
