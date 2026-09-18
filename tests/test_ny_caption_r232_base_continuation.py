from copy import deepcopy
from types import SimpleNamespace

import pytest

from research_loop.workers.rohin221_continuous_caption_20260918 import continue_base_epoch as epoch


def fixture():
    backend = dict(kind='FROZEN_BASE_NO_LORA_NO_LEARNING', source={'fixed': 'bytes'},
        identity=dict(visible_device='old-device', all_parameters_frozen=True,
            optimizer_created=False, lora_parameters=0, base_sha256='a' * 64))
    binding = dict(plan=dict(opportunities=96, think_tokens=384, act_tokens=768,
        context_tokens=2048), controller={'sha256': 'b' * 64}, parser={'sha256': 'c' * 64})
    state = dict(pending=None, stage='ACT', opportunity=81, attempt=0, completed_opportunities=80,
        events=[dict(source=dict(request_id='prior-act'))], history=[dict(role='assistant', content='saved thought')],
        generations=[dict(request_id='prior-think')], think_source={'request_id': 'prior-think'},
        total_generated_tokens=123, binding=binding, backend_state=backend)
    scorer = dict(phase='COMPLETE', session_binding=dict(controller=binding, backend=backend),
        seen=['prior-act'], game={'novelty': 'preserved'}, policy={'accepted': 9})
    new_backend = deepcopy(backend)
    new_backend['identity']['visible_device'] = 'actual-new-device'
    new_binding = deepcopy(binding)
    new_binding['plan']['opportunities'] = 512
    return state, scorer, new_backend, new_binding


def test_new_allocation_preserves_mid_opportunity_THINK_history_ids_and_novelty():
    state, scorer, backend, binding = fixture()
    before = deepcopy((state, scorer))
    migrated, restored = epoch.migrate(state, scorer, backend, binding, 'actual-new-device', 'epoch3')
    assert (state, scorer) == before
    assert epoch.retained_summary(migrated, restored) == epoch.retained_summary(state, scorer)
    assert migrated['stage'] == 'ACT' and migrated['think_source'] == state['think_source']
    assert migrated['backend_state']['identity']['visible_device'] == 'actual-new-device'
    assert restored['seen'] == ['prior-act']


@pytest.mark.parametrize('change', ['pending', 'scene_budget', 'model', 'source', 'novelty_prefix'])
def test_unrelated_or_inflight_changes_rejected(change):
    state, scorer, backend, binding = fixture()
    if change == 'pending':
        state['pending'] = {'kind': 'GENERATION'}
    elif change == 'scene_budget':
        binding['plan']['context_tokens'] = 4096
    elif change == 'model':
        backend['identity']['base_sha256'] = 'd' * 64
    elif change == 'source':
        backend['source'] = {'unfrozen': 'different'}
    else:
        scorer['seen'] = []
    with pytest.raises(ValueError):
        epoch.migrate(state, scorer, backend, binding, 'actual-new-device', 'epoch3')


def transition_fixture(monkeypatch, opportunity=81):
    predecessor = dict(kind='STANDALONE_GENERATION', request_id='exact-old-think')
    transition = dict(predecessor_think_origin=predecessor, previous_binding='old-binding',
        previous_backend='old-backend', opportunity=81)
    calls = []
    def validator(origin, **arguments):
        calls.append((origin, arguments))
        if arguments.get('stage') == 'THINK':
            return dict(generated_tokens=62, finished_unix=100,
                request=dict(opportunity=81, attempt=0), think=None)
        return dict(raw='actual caption', generated_tokens=10, finished_unix=200,
            request=dict(opportunity=opportunity, attempt=1), think=None)
    monkeypatch.setattr(epoch, 'validate_generation_origin', validator)
    monkeypatch.setattr(epoch, 'verified_active_scene', lambda request, scenes: 'same-scene')
    session = SimpleNamespace(session_binding=dict(controller='new-binding', backend='new-backend'),
        life_root='actual-root', scene_ids=['same-scene'])
    request = dict(origin=dict(request_id='new-act', think=predecessor), metrics=dict(THINK=62, ACT=10, LEARN=0))
    return session, request, transition, calls


def test_exact_saved_predecessor_validated_against_historical_binding_not_forged(monkeypatch):
    session, request, transition, calls = transition_fixture(monkeypatch)
    verified, active = epoch.verified_request(request, session, transition)
    assert verified['think']['generated_tokens'] == 62 and active == 'same-scene'
    assert calls[0][1]['expected_backend_state'] == 'new-backend'
    assert calls[1][1]['expected_backend_state'] == 'old-backend'


def test_predecessor_cannot_be_reused_for_a_later_opportunity(monkeypatch):
    session, request, transition, calls = transition_fixture(monkeypatch, opportunity=82)
    with pytest.raises(ValueError, match='same_opportunity_THINK'):
        epoch.verified_request(request, session, transition)


def test_unregistered_predecessor_gets_normal_current_source_validation(monkeypatch):
    session, request, transition, calls = transition_fixture(monkeypatch)
    request['origin']['think'] = dict(request_id='another-old-think')
    request['metrics']['THINK'] = 0
    epoch.verified_request(request, session, transition)
    assert len(calls) == 1
    assert calls[0][0] == request['origin']
    assert calls[0][1]['expected_backend_state'] == 'new-backend'
