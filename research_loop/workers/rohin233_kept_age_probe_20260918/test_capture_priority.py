from copy import deepcopy

import pytest

from research_loop.workers.rohin233_kept_age_probe_20260918.capture_priority import plan_round


def source(label):
    return dict(life=label, journal_id=label + '_journal', source_frontier=10)


def entry(label, index, status='JOINED_NOT_COPIED'):
    return dict(life=label, journal_id=label + '_journal', key=label + ':' + str(index),
        record_index=index, sleep=index, checkpoint_status=status)


def test_prospective_before_optional_history_and_one_per_life():
    entries = [entry('first', index) for index in range(1, 20)] + [entry('second', 11)]
    original = deepcopy(entries)
    result = plan_round(entries, [source('first'), source('second')], set(), historical=True)
    assert [row['key'] for row in result['selected']] == ['first:11', 'second:11']
    assert len(result['classified']) == len(entries) == result['enrolled_retained']
    assert entries == original


def test_all_sixteen_get_one_before_a_second_source():
    labels = ['life_' + str(number).zfill(2) for number in range(16)]
    entries = [entry(label, index) for label in labels for index in (11, 12, 13)]
    result = plan_round(entries, [source(label) for label in labels], set())
    assert len(result['selected']) == 16
    assert {row['life'] for row in result['selected']} == set(labels)
    assert {row['record_index'] for row in result['selected']} == {11}
    assert len(result['classified']) == 48


def test_persisted_attempt_order_and_captured_source_dedup():
    entries = [entry(label, index) for label in ('first', 'second') for index in (11, 12)]
    result = plan_round(entries, [source('first'), source('second')], {'second:11'},
        last_attempted={'first': 100, 'second': 50}, limit=1)
    assert [row['key'] for row in result['selected']] == ['second:12']


def test_history_is_explicit_opt_in_and_unavailable_remains_visible():
    entries = [entry('first', 2), entry('first', 11, 'MISSING')]
    assert not plan_round(entries, [source('first')], set())['selected']
    result = plan_round(entries, [source('first')], set(), historical=True)
    assert result['selected'][0]['key'] == 'first:2'
    assert result['classes']['prospective_source_unavailable_or_mismatched'] == 1
    assert len(result['classified']) == 2


def test_duplicate_or_unregistered_journal_fails_closed():
    row = entry('first', 11)
    with pytest.raises(ValueError, match='unique_registered_entry'):
        plan_round([row, row], [source('first')], set())
    row['journal_id'] = 'different'
    with pytest.raises(ValueError, match='unique_registered_entry'):
        plan_round([row], [source('first')], set())


def test_no_wall_clock_inference_required():
    row = entry('first', 11)
    row['recorded_unix'] = None
    result = plan_round([row], [source('first')], set())
    assert result['classified'][0]['age_class'] == 'prospective'
    assert not result['gpu_dispatch'] and result['learner_signals'] == []
