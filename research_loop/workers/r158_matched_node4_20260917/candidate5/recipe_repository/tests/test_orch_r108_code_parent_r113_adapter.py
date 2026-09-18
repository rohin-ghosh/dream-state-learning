import json

import pytest

from gpu import orch_r108_code_parent_r113_adapter as adapter
from gpu import orch_r110_claude_broker as broker


def fixture():
    policy = adapter.policy
    task = policy.tasks('TRAIN')[0]
    events = []
    for actor, text in [('child', 'I expected a longer list.'), ('checker', 'The checker returned an empty list.')]:
        events.append(dict(actor=actor, text=text, source_sha256=policy.text_sha(text), split='TRAIN',
            visibility='CHILD_VISIBLE', task_id=task['task_id'], task_sha256=task['content_sha256'],
            completed_response=True, child_received=True, event_type='text' if actor == 'child' else 'checker_feedback'))
    events[1].update(outcome={'passed':False, 'answer_key':'HIDDEN'}, score=0)
    return task, events


def build(task, events):
    return adapter.request(task, events, identifier='R113_F3_C001_P1', life_id='F3_prospective',
        cycle=1, episode=0, phase='experience', lane_deadline_unix=1789500000)


def test_real_shared_broker_accepts_wire_and_retains_visible_checker_output():
    task, events = fixture()
    request = build(task, events)
    config = dict(life_id='F3_prospective', family='code', train_tasks={task['task_id']:task['content_sha256']},
        excluded_task_ids=[row['task_id'] for split in ('DEV','FINAL') for row in adapter.policy.tasks(split)],
        cohort_sha256=adapter.policy.digest(adapter.policy.tasks('TRAIN')))
    observed = broker.validate_request(request, config)
    assert observed['events'][1]['text'] == events[1]['text']
    assert observed['events'][1]['outcome'] == {'passed':False} and observed['events'][1]['score'] == 0
    assert 'HIDDEN' not in json.dumps(observed)
    assert request['lane_deadline_unix'] == 1789500000


@pytest.mark.parametrize('split', ['DEV','FINAL'])
def test_never_send_dev_final_task_to_parent(split):
    task, events = fixture()
    with pytest.raises(ValueError, match='fixed_train_task_only'):
        build(adapter.policy.tasks(split)[0], events)


def test_parent_only_after_completed_response_no_mid_generation():
    task, events = fixture()
    events[0]['completed_response'] = False
    with pytest.raises(ValueError, match='completed_child_response_required'):
        build(task, events)


def test_unreceived_environment_feedback_not_silently_public():
    task, events = fixture()
    events[1]['child_received'] = False
    with pytest.raises(ValueError, match='feedback_delivery_required'):
        build(task, events)
