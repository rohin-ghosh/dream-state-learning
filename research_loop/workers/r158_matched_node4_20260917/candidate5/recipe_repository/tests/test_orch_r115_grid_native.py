from copy import deepcopy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from gpu import orch_r115_grid_native as native
from gpu import orch_r115_grid_astra as astra
from gpu import orch_r110_claude_broker as broker


@pytest.fixture(scope='module')
def tasks():
    return native.policy.cohort()


def test_OPEN_inspection_is_enacted_and_returned_to_child(tasks):
    task = tasks['TRAIN'][-1]
    state = native.policy.game.initial(task)
    state['done'] = True
    before = deepcopy(state)
    responses = iter(['INSPECT: 4,4', 'I have the new observation.'])
    prompts = []
    calls = []

    def generate(task, purpose, messages, cap, **options):
        prompts.append(deepcopy(messages))
        return dict(raw=next(responses), token_ids=[1], reference={})

    def environment(task, state, raw, purpose, sequence, **options):
        updated, response = native.enacted_environment(task, state, raw, open_turn=True)
        calls.append(response)
        return updated, response, dict(path='native-evidence', sha256='a' * 64)

    life = SimpleNamespace(generate=generate, environment=environment)
    outcome = native.open_opportunity(life, task, state, 0, parent=False, attached_readout=True)
    assert calls[0]['enacted'] and calls[0]['operation'] == 'INSPECT'
    assert calls[0]['value'] == task['cells'][4][4]
    assert json.loads(prompts[1][-1]['content'])['value'] == task['cells'][4][4]
    assert state == before and outcome['eligible_for_carry'] is False
    assert prompts[0][-1]['content'] == 'The task is over; the environment is still here.'


@pytest.mark.parametrize('split,purpose,attached', [
    ('DEV', 'reflection', False), ('FINAL', 'reflection', False),
    ('TRAIN', 'open_readout', True), ('TRAIN', 'reflection', True)])
def test_DEV_FINAL_attached_open_never_sleep_or_context_buffer(split, purpose, attached):
    with pytest.raises(ValueError, match='never_carry'):
        native.carry_rows([dict(split=split, purpose=purpose, attached_readout=attached)])


def test_broker_head_REFLECTION_changes_real_generation_cap(tmp_path, tasks):
    task = tasks['TRAIN'][0]
    request = native.policy.queue_request('P0001', 'F4_FABLE', 1, 1, 'presleep_metacognition', task,
        [native.policy.previous.public_event(0, 'child', 'I wonder what I learned.', 'a' * 64)],
        native.policy.digest(tasks), 100)
    config = dict(branch='F4', family='grid', life_id='F4_FABLE',
        train_tasks={task['id']: task['task_sha256'] for task in tasks['TRAIN']},
        excluded_task_ids=[task['id'] for split in ('DEV', 'FINAL') for task in tasks[split]],
        cohort_sha256=native.policy.digest(tasks), principles_sha256=native.policy.PRINCIPLES_SHA)
    principles = Path(native.policy.__file__).resolve().parents[1] / 'research_notes/PARENTING_PRINCIPLES_ROHIN_2026-09-15.md'
    actual_caps = []
    for cap in (512, 2048):
        fields = deepcopy(native.policy.PARENT_FIELDS)
        fields['REFLECTION'] = dict(mode='short' if cap == 512 else 'long', max_new_tokens=cap)
        text = broker.render_parent_prompt(fields)
        (tmp_path / 'F4.md').write_text(text)
        (tmp_path / 'F4.fields.json').write_text(json.dumps(dict(schema='ORCH_R114_HEAD_FIELDS_V1',
            fields=fields, prompt_sha256=hashlib.sha256(text.encode()).hexdigest())))
        system, unused, binding = broker.build_system(request['payload'], config, tmp_path, principles)
        binding_bytes = (json.dumps(binding, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()
        response = dict(id=request['id'], status='COMPLETE', finished_unix=150,
            request_sha256=broker.digest(request), payload_sha256=request['payload_sha256'],
            prompt_binding=binding, transcript_receipt=dict(node_only=True, all_verified=True,
                files={'PROMPT_BINDING.json': hashlib.sha256(binding_bytes).hexdigest()}))
        setting = native.reflection_settings(response, request, config, now=160)
        assert setting['status'] == 'BOUND_FOR_LANE_DECODER'
        class FakeEngine:
            def batch(self, messages, generation_cap):
                actual_caps.append(generation_cap)
                return [dict(raw='reflection', token_ids=[1], terminal=True)]
        life_root = tmp_path / str(cap)
        life_root.mkdir()
        life = native.Life(life_root, FakeEngine(), config, 1)
        life.generate(task, 'reflection', [{'role': 'user', 'content': 'Reflect.'}], setting['effective_max_new_tokens'])
    assert actual_caps == [512, 2048]


def test_no_provider_or_environment_on_prose_only_OPEN(tasks):
    task = tasks['TRAIN'][0]
    state = native.policy.game.initial(task)
    after, result = native.enacted_environment(task, state, 'I will stop now.', open_turn=True)
    assert after == state and result['enacted'] is False


def test_episode_inspection_costs_turn_and_preserves_state(tasks):
    task = tasks['TRAIN'][0]
    state = native.policy.game.initial(task)
    after, result = native.enacted_environment(task, state, 'INSPECT: 0,1')
    assert after['steps'] == state['steps'] + 1 and after['position'] == state['position']
    assert result['value'] == task['cells'][0][1]


def test_f4_astra_parser_uses_grid_plan():
    envelope = dict(model=astra.MODEL, status='completed', usage={'output_tokens': 20}, output=[
        dict(type='message', content=[dict(type='output_text', text=json.dumps(dict(
            guidance='What surprised you?', tag='ADD', intervention_class='reflection', rationale='Attend to experience.')))])])
    result = astra.parse(envelope)
    assert result['status'] == 'COMPLETE' and result['plan']['message'] == 'What surprised you?'


def test_same_state_postterminal_motion_not_new_task_score(tasks):
    task = tasks['TRAIN'][0]
    state = native.policy.game.initial(task)
    state['done'] = True
    after, response = native.enacted_environment(task, state, 'ACTION: WAIT', open_turn=True)
    assert after['steps'] == state['steps'] + 1
    assert response['enacted'] and response['post_task_exploration']
    assert not response['original_task_outcome_recomputed']


@pytest.mark.parametrize('split,folder', [('DEV', 'readout_calls'), ('FINAL', 'sealed_readout_calls'), ('TRAIN', 'readout_calls')])
def test_attached_readout_logs_separate_no_parent_events(tmp_path, tasks, split, folder):
    engine = SimpleNamespace(batch=lambda prompts, cap: [dict(raw='output', token_ids=[1])])
    life = native.Life(tmp_path, engine, {}, 0)
    life.generate(tasks[split][0], 'open_readout', [{'role': 'user', 'content': 'Look.'}], 4, attached_readout=True)
    assert not life.events and not (tmp_path / 'calls').exists()
    assert len(list((tmp_path / folder).glob('*.json'))) == 1


def test_handoff_rejects_foreign_pair():
    from gpu import orch_r115_grid_handoff as handoff
    assert handoff.target(7, 'F4_ASTRA').name.endswith('node5_7_20260915_attempt1')
    with pytest.raises(ValueError, match='owned_receiver_pair'):
        handoff.target(3, 'F4_FABLE')


def test_morning_reserve_stops_before_new_TRAIN_charge(tmp_path, monkeypatch, tasks):
    monkeypatch.setattr(native.time, 'time', lambda: native.TRAIN_END)
    life = native.Life(tmp_path, None, {}, 1)
    with pytest.raises(native.TrainWindowClosed):
        life.generate(tasks['TRAIN'][0], 'reflection', [], 1024)
    assert not (tmp_path / 'LEDGER.jsonl').exists()
