import json
from contextlib import ExitStack
import time
from unittest.mock import Mock, patch

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


def run_evaluation(tmp_path, *, memory=lambda: 2**31, runner=None, deadline=None):
    deadline = time.time()+90 if deadline is None else deadline
    request = dict(id='request', payload_sha256='hash', lane_deadline_unix=deadline+30)
    config = dict(branch='F1', family='route', deadline_unix=deadline, min_available_bytes=2**30)
    runner = runner or Mock(return_value=astra.parse(envelope('[SILENT]')))
    with ExitStack() as stack:
        stack.enter_context(patch.object(astra.transport, 'validate_config'))
        stack.enter_context(patch.object(astra, 'authorize'))
        stack.enter_context(patch.object(astra.transport, 'validate_request', return_value={}))
        stack.enter_context(patch.object(astra.transport, 'build_system', return_value=('system', b'prompt', {})))
        result = astra.evaluate(request, tmp_path/'call', deadline, config=config, launch={},
            prompt_root=tmp_path, principles_path=tmp_path/'principles', runner=runner,
            memory=memory, http_slot_root=tmp_path/'slots')
    return result, runner


def test_http_slot_replaces_cli_lock_and_preserves_one_attempt(tmp_path):
    import fcntl
    with (tmp_path/'cli.lock').open('w') as cli_lock:
        fcntl.flock(cli_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with patch.object(astra.transport.backend, 'LOCK_PATH', tmp_path/'cli.lock'):
            result, runner = run_evaluation(tmp_path)
    assert result['status'] == 'SILENT' and result['provider_dispatched'] is True
    assert result['retry'] is False
    runner.assert_called_once()
    receipt = json.loads((tmp_path/'call/HTTP_SLOT.json').read_text())
    assert receipt['maximum_http_concurrency'] == 4 and receipt['cli_lock_used'] is False
    assert receipt['helper_sha256'] == astra.transport.sha(astra.slots.__file__)


def test_memory_floor_still_prevents_dispatch_and_releases_http_slot(tmp_path):
    result, runner = run_evaluation(tmp_path, memory=lambda: 0)
    assert result['status'] == 'MISSING' and result['provider_dispatched'] is False
    runner.assert_not_called()
    with astra.slots.acquire(time.time()+60, root=tmp_path/'slots') as receipt:
        assert receipt['slot'] == 0


def test_original_cutoff_still_prevents_http_dispatch(tmp_path):
    result, runner = run_evaluation(tmp_path, deadline=time.time()+10)
    assert result['status'] == 'MISSING' and result['provider_dispatched'] is False
    runner.assert_not_called()
