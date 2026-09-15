import json
import time
from contextlib import contextmanager

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


@pytest.fixture
def delivery(tmp_path, monkeypatch):
    config = dict(branch='F3', family='code', deadline_unix=time.time()+120,
        min_available_bytes=1024)
    launch = dict(authorized=True, authorization='BUILDER_PUBLISHED_PAIRED_ASTRA',
        config_sha256=astra.transport.digest(config), source_reference='cpu_test',
        not_before_unix=time.time()-1)
    request = dict(id='TRAIN_PARENT', lane_deadline_unix=time.time()+90,
        payload_sha256='a'*64)
    monkeypatch.setattr(astra.transport, 'validate_config', lambda config: None)
    monkeypatch.setattr(astra.transport, 'validate_request', lambda request, config: {'task_id':'TRAIN'})
    monkeypatch.setattr(astra.transport, 'build_system',
        lambda *args: ('system', b'prompt', {'bound':True}))
    return dict(request=request, directory=tmp_path/'packet', deadline=config['deadline_unix'],
        config=config, launch=launch, prompt_root=tmp_path, principles_path=tmp_path/'principles',
        slot_root=tmp_path/'slots', memory=lambda: 1024)


def test_http_delivery_one_attempt_unchanged_cutoff_and_bounded_slot(delivery):
    calls = []

    def provider(prompt, directory, cutoff, system):
        receipt = json.loads((directory/'HTTP_SLOT.json').read_text())
        assert receipt['maximum_http_concurrency'] == 4
        assert receipt['provider_time_reserved_seconds'] == 20
        assert receipt['cli_lock_used'] is False
        assert cutoff == delivery['request']['lane_deadline_unix']-30
        calls.append(cutoff)
        return astra.parse(envelope('[SILENT]'))

    result = astra.evaluate(**delivery, runner=provider)
    assert len(calls) == 1 and result['provider_dispatched'] is True
    assert result['status'] == 'SILENT' and result['retry'] is False
    assert result['request_sha256'] == astra.transport.digest(delivery['request'])


def test_slot_exhaustion_missing_without_provider_or_retry(delivery, monkeypatch):
    @contextmanager
    def unavailable(*args, **kwargs):
        raise TimeoutError('http_slot_deadline_preserves_provider_margin')
        yield

    monkeypatch.setattr(astra.http_slots, 'acquire', unavailable)
    result = astra.evaluate(**delivery, runner=lambda *args: pytest.fail('provider must not dispatch'))
    assert result['status'] == 'MISSING' and result['provider_dispatched'] is False
    assert result['retry'] is False


def test_http_memory_floor_remains_and_slot_released(delivery):
    delivery['memory'] = lambda: 1023
    result = astra.evaluate(**delivery, runner=lambda *args: pytest.fail('below memory floor'))
    assert result['status'] == 'MISSING' and result['provider_dispatched'] is False
    with astra.http_slots.acquire(time.time()+60, root=delivery['slot_root']) as receipt:
        assert receipt['slot'] == 0


def test_http_provider_failure_charged_once_and_never_retried(delivery):
    calls = []

    def provider(*args):
        calls.append(True)
        raise OSError('simulated transport failure')

    result = astra.evaluate(**delivery, runner=provider)
    assert len(calls) == 1 and result['provider_dispatched'] is True
    assert result['status'] == 'MISSING' and result['retry'] is False
