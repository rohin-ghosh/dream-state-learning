import importlib.util
from pathlib import Path

import pytest


def diagnostic():
    spec = importlib.util.spec_from_file_location('selection_diagnostic', Path(__file__).with_name('selection_diagnostics.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_oracle_uses_ceiling_not_floor_and_does_not_change_threshold():
    result = diagnostic().threshold_oracle([0.4]+[0.1]*20, 0.3, 0.05)
    assert result['minimum_accepted_count'] == 2
    assert result['maximum_mean_positive_vote_mass_at_minimum_coverage'] == 0.25
    assert not result['quality_objective_possible_under_perfect_ranking']
    assert not result['threshold_changed']


def test_oracle_feasibility_is_not_learned_precision():
    result = diagnostic().threshold_oracle([0.5]+[0.1]*19, 0.3, 0.05)
    assert result['quality_objective_possible_under_perfect_ranking']
    assert not result['fit_filter_considered'] and not result['rows_disclosed']


@pytest.mark.parametrize('values', [[], [float('nan')], [-0.1], [1.1]])
def test_oracle_rejects_invalid_mass(values):
    with pytest.raises(ValueError):
        diagnostic().threshold_oracle(values, 0.3, 0.05)
