import json

import pytest

from gpu import orch_r119_code_fable_parser as parser


def envelope(turns=4):
    return dict(type='result', subtype='success', is_error=False, num_turns=turns,
        modelUsage={parser.original.MODEL:{'inputTokens':10, 'outputTokens':20}},
        result='[SILENT]', total_cost_usd=.1)


def test_observed_utility_turns_preserved_not_mistaken_for_extra_attempts():
    value = envelope()
    raw = json.dumps(value)
    result = parser.parse_output(raw, 'code', 'task')
    assert result['status'] == 'SILENT'
    assert result['usage']['native_num_turns'] == 4
    assert result['usage']['provider_attempts'] == 1
    assert json.loads(raw) == value


@pytest.mark.parametrize('turns', [0, -1, True, 1.5, '4', None])
def test_invalid_turn_accounting_rejected(turns):
    with pytest.raises(ValueError):
        parser.parse_output(json.dumps(envelope(turns)), 'code', 'task')


def test_actual_provider_failure_still_rejected():
    value = envelope()
    value['is_error'] = True
    with pytest.raises(ValueError):
        parser.parse_output(json.dumps(value), 'code', 'task')


def test_no_other_family_parser_change():
    with pytest.raises(ValueError, match='CODE_only'):
        parser.parse_output(json.dumps(envelope()), 'math', 'task')
