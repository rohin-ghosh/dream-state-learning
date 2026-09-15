import json

import pytest

from gpu import orch_r108_code_parent_r115_astra as astra


def envelope(text):
    return dict(model=astra.MODEL, status='completed', usage={'output_tokens': 10},
        output=[dict(type='message', content=[dict(type='output_text', text=text)])])


def test_actual_code_plan_binds_task_without_answer():
    result = astra.parse(envelope(json.dumps(dict(guidance='What did you notice?',
        tag='SHIFT', intervention_class=None, rationale='Actual child context.'))), 'TRAIN_EXACT')
    assert result['status'] == 'COMPLETE'
    assert result['actual_model'] == 'openai/openai/gpt-6-astra'
    assert result['plan']['order'] == ['TRAIN_EXACT']
    assert result['plan']['guidance'] == 'What did you notice?'


def test_silent_valid_and_wrong_model_rejected():
    assert astra.parse(envelope('[SILENT]'))['status'] == 'SILENT'
    wrong = envelope('[SILENT]')
    wrong['model'] = 'not-the-assigned-parent'
    with pytest.raises(ValueError):
        astra.parse(wrong)


def test_generated_implementation_is_not_parent_guidance():
    with pytest.raises(ValueError):
        astra.parse(envelope(json.dumps(dict(guidance='Use `sum(values)`.',
            tag='ADD', intervention_class=None, rationale='An implementation.'))))
