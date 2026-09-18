import json
from pathlib import Path
from unittest.mock import patch

import pytest

from gpu import orch_r111_route_pair as route
from gpu import orch_r110_claude_broker as broker
from test_orch_r111_route_pair import native_shape_engine
from test_orch_r110_claude_broker import ClaudeBrokerTests


def test_open_inspection_executes_actual_environment_and_feeds_response():
    world = dict(edges=[])
    record = dict(task={'events': ['real-address']}, current='terminal', messages=[
        dict(role='system', content='old'), dict(role='user', content='public task')])
    received = []
    def child(messages):
        received.append(json.loads(json.dumps(messages)))
        return dict(raw='I want to inspect this.\nREAD EVENT real-address' if len(received)==1 else 'STOP')
    result = route.open_turn(world, record, {'real-address': 'actual stored observation'}, child)
    assert len(result['environment_calls']) == 1
    assert result['environment_calls'][0]['actual_environment_call'] is True
    assert result['environment_calls'][0]['response'] == 'MEMORY RESULT\nactual stored observation'
    assert received[1][-1]['content'] == result['environment_calls'][0]['response']
    assert result['continuation_after_inspection'] is True
    assert result['initiative'] == 'UNKNOWN_PENDING_SHARED_JUDGE'


@pytest.mark.parametrize('phase', ['dev', 'final', 'open_readout', 'readout'])
def test_readouts_cannot_enter_replay_buffer(phase):
    rows = []
    with patch.object(route.causal, 'replay_row', side_effect=AssertionError('must not encode held')):
        with pytest.raises(ValueError, match='readouts_never_training_buffer'):
            route.append_training_row(rows, phase, {}, Path('/must-not-read'))
    assert rows == []
    locations = [route.readout_directory(Path('/life'), 1, scope) for scope in ('dev', 'final', 'open')]
    assert len(set(locations)) == 3
    assert all('cycle_' not in str(path) for path in locations)


def test_head_reflection_reread_through_real_broker_changes_native_cap():
    fixture = ClaudeBrokerTests()
    fixture.setUp()
    try:
        engine = native_shape_engine()
        for mode, cap in (('short', 512), ('long', 2048)):
            fields = dict(fixture.head_fields, REFLECTION=dict(mode=mode, max_new_tokens=cap))
            prompt = broker.render_parent_prompt(fields)
            (fixture.prompts/'F1.md').write_text(prompt)
            (fixture.prompts/'F1.fields.json').write_text(json.dumps(dict(
                schema='ORCH_R114_HEAD_FIELDS_V1', fields=fields,
                prompt_sha256=broker.sha(fixture.prompts/'F1.md'))))
            reply, directory = fixture.evaluate()
            assert reply['status'] == 'COMPLETE'
            reply['transcript_receipt'] = dict(node_only=True, all_verified=True)
            observed = route.parent_result(reply, fixture.request, broker.MODEL)
            assert observed['status'] == 'COMPLETE'
            requested = route.reflection_cap(observed['head_settings'])
            response = route.generate(engine, [dict(role='user', content='actual experience')],
                                      cap=requested, reflection=True)
            assert response['effective_generation_cap'] == cap
            assert engine.model.actual_configs[-1]['max_new_tokens'] == cap
    finally:
        fixture.doCleanups()


def test_v4_birth_deadline_and_judge_are_not_seeded_legacy_values():
    import inspect
    source = inspect.getsource(route.prepare)
    assert 'fresh_adapter(root/' in source
    assert 'initial_source_receipt' not in source
    assert 'FROZEN_BASE_FRESH_RANK8_NO_L1_NO_L2_SEED' in source
    assert route.MORNING_CUT == 1789491600
    assert route.HARD_WALL == 1789596240
    assert route.JUDGE_SHA == '0466c6fa8bbd8c75f8e2d4c625498423835b2b5285e58c4f703069e8b6c532fd'


def test_no_protocol_only_system_or_forced_prose_length():
    assert 'Reason in ordinary prose' in route.EPISODE_PROMPT
    assert '150' not in route.EPISODE_PROMPT
    assert 'first-person' not in route.EPISODE_PROMPT


def test_normalized_rope_config_accepts_loader_defaults_not_mutations():
    from types import SimpleNamespace
    expected = SimpleNamespace(max_position_embeddings=32768,
        rope_parameters={'rope_type': 'default', 'rope_theta': 1000000.0})
    actual = SimpleNamespace(**vars(expected))
    route.verify_rope_config(actual, expected)
    actual.rope_parameters = {'rope_type': 'linear', 'factor': 2.0}
    with pytest.raises(ValueError, match='no_rope_modification'):
        route.verify_rope_config(actual, expected)
