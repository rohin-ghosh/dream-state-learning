import pytest

from gpu.orch_r108_code_parent_r115_release import eligible


def test_completed_cycle_only_and_receiver_required():
    rows = [dict(cycle=3, status='COMPLETE'), dict(cycle=3, status='MISSING')]
    assert eligible(3, rows, True)
    assert not eligible(3, rows, False)


@pytest.mark.parametrize('row', [dict(cycle=4, status='COMPLETE'),
    dict(cycle=3, status='STARTED'), dict(cycle=3), dict(status='COMPLETE')])
def test_new_cycle_or_unsettled_cell_prevents_release(row):
    assert not eligible(3, [row], True)


def test_outcome_not_used_for_release_selection():
    assert eligible(3, [dict(cycle=3, status='COMPLETE', correct=False)], True)
    assert eligible(3, [dict(cycle=3, status='COMPLETE', correct=True)], True)
