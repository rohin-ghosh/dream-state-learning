from copy import deepcopy
from pathlib import Path

import pytest

from organism_v6 import orch_r111_grid_v4 as policy
from gpu import orch_r110_claude_broker as broker


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def tasks():
    return policy.cohort()


def test_v4_exact_parent_text_and_editable_fields():
    plan, unused = policy.snapshots(ROOT)
    text = policy.parent_fixed_text(plan)
    assert text == broker.render_parent_prompt(policy.PARENT_FIELDS)
    assert 'feedback the child itself received' in text
    assert 'catalogue you must enact' in text and "own useful organisation" in text
    changed = deepcopy(policy.PARENT_FIELDS)
    changed.update(FOCUS='Listen more.', STYLE='direct')
    changed['REFLECTION'] = dict(mode='long', max_new_tokens=2048)
    assert policy.validate_fields(changed, policy.PARENT_FIELDS) == changed
    changed['GAME'] = 'other'
    with pytest.raises(ValueError, match='only_FOCUS_STYLE_REFLECTION'):
        policy.validate_fields(changed, policy.PARENT_FIELDS)


def test_separate_DEV_FINAL_frozen_geometry(tasks):
    assert tasks == policy.cohort()
    assert {key: len(value) for key, value in tasks.items()} == dict(TRAIN=16, DEV=8, FINAL=8)
    flattened = [task for group in tasks.values() for task in group]
    assert len({task['id'] for task in flattened}) == 32
    assert len({policy.geometry(task) for task in flattened}) == 32
    assert not {policy.geometry(task) for task in flattened}.intersection(
        policy.geometry(task) for group in policy.previous.cohort().values() for task in group)
    for task in flattened:
        assert task['task_sha256'] == policy.digest({key: value for key, value in task.items() if key != 'task_sha256'})


def test_actual_feedback_preserved_hidden_fields_removed(tasks):
    task = tasks['TRAIN'][0]
    state = policy.game.initial(task)
    assert policy.public_observation(task, state) == policy.game.observation(task, state)
    event = policy.feedback_event(1, 'blocked; reward -0.1; terminal false', 'a' * 64,
        child_received=True, hidden={'gold': 'private'})
    assert event['text'] == 'blocked; reward -0.1; terminal false'
    assert 'hidden_evaluator_verdict' not in event
    with pytest.raises(ValueError, match='child_delivery'):
        policy.feedback_event(1, 'not delivered', 'a' * 64, child_received=False)


def test_wire_open_turn_and_feedback_no_hidden(tasks):
    task = tasks['TRAIN'][0]
    events = [policy.previous.public_event(0, 'child', 'I would look again.', 'a' * 64),
        policy.feedback_event(1, 'blocked', 'b' * 64, child_received=True)]
    request = policy.queue_request('F4_C01_OPEN', 'F4_FABLE', 1, 0, 'open_turn', task, events,
        policy.digest(tasks), 100)
    config = dict(life_id='F4_FABLE', family='grid', train_tasks={item['id']: item['task_sha256'] for item in tasks['TRAIN']},
        excluded_task_ids=[item['id'] for group in ('DEV', 'FINAL') for item in tasks[group]],
        cohort_sha256=policy.digest(tasks))
    assert broker.validate_request(request, config) == request['payload']
    assert request['lane_deadline_unix'] - 30 == 190


@pytest.mark.parametrize('split', ['DEV', 'FINAL'])
def test_held_never_parent_queued(tasks, split):
    with pytest.raises(ValueError, match='TRAIN_parent_only'):
        policy.queue_request('id', 'F4_FABLE', 1, 0, 'experience', tasks[split][0], [], 'a' * 64, 100)


@pytest.mark.parametrize('audience', ['parent', 'head', 'exchange'])
def test_FINAL_never_visible(audience):
    with pytest.raises(ValueError, match='FINAL_never_visible'):
        policy.validate_audience('FINAL', audience)


def test_DEV_head_exchange_not_parent():
    policy.validate_audience('DEV', 'head')
    policy.validate_audience('DEV', 'exchange')
    with pytest.raises(ValueError):
        policy.validate_audience('DEV', 'parent')


def test_cycle0_morning_only_final_no_repeated_final():
    before = policy.FINAL_UNIX - 60
    assert policy.readout_plan(0, before)['FINAL'] == 8
    assert policy.readout_plan(1, before)['FINAL'] == 0
    assert policy.readout_plan(3, policy.FINAL_UNIX)['FINAL'] == 8
    assert policy.readout_plan(4, policy.FINAL_UNIX, ['cycle0', 'morning'])['FINAL'] == 0
    assert policy.readout_plan(3, before)['focused_DEV'] == 2
    assert policy.readout_plan(3, before)['parent_free_open'] == 2
    with pytest.raises(ValueError, match='bounded_readout'):
        policy.readout_plan(3, policy.HARD_END_UNIX)


def test_manifest_honest_no_runtime_or_learning_claim():
    result = policy.manifest(ROOT)
    assert result['comparison'] == 'ELICITATION_ONLY_PARENTING_SYSTEMS'
    assert result['optimizer_steps'] == result['sleep_count'] == result['native_calls'] == 0
    assert result['morning_final_utc'] == '2026-09-15T17:00:00Z'
    assert not result['gpu_launch_ready'] and result['pending']
    assert policy.OPEN_PROMPT == 'The task is over; the environment is still here.'
    assert result['persistence']['postanswer_exploration_separate_descriptive']
    assert result['readout']['sleep0_status'] == 'NOT_RUN'
    assert 'FINAL_inventory' not in result


def test_fable_still_requires_explicit_go():
    with pytest.raises(ValueError, match='explicit_watcher_GO'):
        policy.previous.validate_fable_go(dict(authorized=True, authorization='SILENCE'), 'a' * 64, 100)
