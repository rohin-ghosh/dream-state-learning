from pathlib import Path

import pytest

from gpu import orch_r108_code_parent_r114_adapter as adapter
from gpu import orch_r110_claude_broker as broker


def fixture():
    task = adapter.policy.tasks('TRAIN')[0]
    events = []
    for actor, text in [('child', 'My initial response.'), ('environment', adapter.policy.OPEN_TURN_PROMPT),
            ('child', 'I have nothing further to pursue.')]:
        events.append(dict(actor=actor, text=text, source_sha256=adapter.policy.text_sha(text), split='TRAIN',
            visibility='CHILD_VISIBLE', task_id=task['task_id'], task_sha256=task['content_sha256'],
            completed_response=True, child_received=True, event_type='text'))
    return task, events


def build(task, events):
    return adapter.request(task, events, phase='open_turn', identifier='R114_F3_OPEN_C001_P1',
        life_id='f3_prospective', cycle=1, episode=0, lane_deadline_unix=1789491600)


def test_v4_open_turn_real_broker_compatibility_no_calls():
    task, events = fixture()
    request = build(task, events)
    config = dict(life_id='f3_prospective', family='code', train_tasks={task['task_id']:task['content_sha256']},
        excluded_task_ids=[], cohort_sha256=adapter.policy.digest(adapter.policy.tasks('TRAIN')))
    public = broker.validate_request(request, config)
    assert public['phase'] == 'open_turn'
    assert public['events'][1]['text'] == adapter.policy.OPEN_TURN_PROMPT
    assert public['events'][-1]['text'] == events[-1]['text']


def test_no_parent_opportunity_before_actual_open_response():
    task, events = fixture()
    with pytest.raises(ValueError, match='actual_open_invitation_then_child_response'):
        build(task, events[:-1])
    with pytest.raises(ValueError, match='actual_open_invitation_then_child_response'):
        build(task, [events[0], events[-1]])


def test_exact_prompt_renderer_matches_shared_broker_and_reflection_contract(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    bound = root / 'research_notes/analysis/orch_r108_code_parent_r114_f3_20260915_attempt1/BATTLE_PLAN_V4_BOUND.md'
    protocol = bound.read_text()
    monkeypatch.setattr(broker, 'BATTLEPLAN', bound)
    principles = (root / 'research_notes/analysis/orch_r108_code_parent_r113_f3_20260915_attempt1/PRINCIPLES_BOUND.md').read_text()
    assert adapter.policy.parent_prompt(protocol, principles) == broker.render_parent_prompt(adapter.policy.DEFAULT_FIELDS) + '\n\n' + principles
    broker.validate_head_update(adapter.policy.DEFAULT_FIELDS,
        dict(adapter.policy.DEFAULT_FIELDS, REFLECTION=dict(mode='short', max_new_tokens=512)))
