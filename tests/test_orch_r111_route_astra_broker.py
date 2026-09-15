import json

import pytest

from gpu import orch_r111_route_astra_broker as astra


def envelope(text):
    return dict(model=astra.MODEL, status='completed', usage={'output_tokens': 10},
                output=[dict(type='message', content=[dict(type='output_text', text=text)])])


def test_actual_astra_envelope_explicit_text_plan_conversion():
    parsed = astra.parse(envelope(json.dumps(dict(guidance='What did you notice?',
        tag='SHIFT', intervention_class='perception', rationale='Actual child context.'))))
    assert parsed['status'] == 'COMPLETE'
    assert parsed['actual_model'] == astra.MODEL
    assert parsed['plan']['message'] == 'What did you notice?'


def test_astra_silent_and_wrong_model():
    assert astra.parse(envelope('[SILENT]'))['status'] == 'SILENT'
    wrong = envelope('[SILENT]')
    wrong['model'] = 'different-model'
    with pytest.raises(ValueError):
        astra.parse(wrong)
