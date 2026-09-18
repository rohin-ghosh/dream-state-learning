from copy import deepcopy

import pytest

from organism_v6 import orch_math_feedback_uptake as history
from organism_v6 import orch_r108_guided as policy


TASK = dict(id='R108_TRAIN_000', split='TRAIN', question='What is 2 plus 3?', gold='5')
PLAN = dict(intervention_class='metacognition', guidance='Does your current approach still fit?',
    rationale='The attempt needs to judge where further effort belongs.')


def record(purpose, records=(), text='I add two and three.\nFINAL: 5'):
    messages = policy.messages(TASK, purpose, records, PLAN if records else None)
    response = dict(raw=text, messages=messages, prompt_tokens=10, token_ids=[9, 10],
        input_truncated=False, terminal=True, truncated=False)
    return history.record(TASK, purpose, response)


def sequence():
    records = [record('experience')]
    records.append(record('check', records))
    records.append(record('revision', records, 'The arithmetic was sufficient; no change was needed.'))
    return records


def test_payload_contains_actual_state_without_gold():
    payload = policy.parent_payload(TASK, record('experience'), 'a' * 64, 1, 1)
    policy.validate_parent_payload(payload)
    assert set(payload['task']) == {'id', 'question'}
    assert payload['child_state']['call_sha256'] == policy.digest(record('experience'))


@pytest.mark.parametrize('field', ['sealed_score', 'reference_answer', 'held'])
def test_extra_parent_fields_rejected(field):
    payload = policy.parent_payload(TASK, record('experience'), 'a' * 64, 1, 1)
    payload[field] = 5
    with pytest.raises(ValueError, match='parent_schema'):
        policy.validate_parent_payload(payload)


def test_held_task_rejected():
    with pytest.raises(ValueError, match='train_only_task'):
        policy.messages(dict(TASK, split='HELD', id='R108_HELD_000'), 'experience')


def test_episode_is_sequential_and_original_parent_free():
    first = policy.messages(TASK, 'experience')
    assert 'PARENT INTERVENTION' not in str(first)
    with pytest.raises(ValueError, match='sequential_episode_history'):
        policy.messages(TASK, 'revision', [record('experience')], PLAN)


@pytest.mark.parametrize('kind', policy.INTERVENTIONS)
def test_all_intervention_classes(kind):
    policy.validate_plan(dict(PLAN, intervention_class=kind), [TASK])


def test_plan_has_no_solution_field():
    with pytest.raises(ValueError, match='intervention_plan_schema'):
        policy.validate_plan(dict(PLAN, answer=5), [TASK])


def test_replay_preserves_tokens_and_outcome_tags():
    records = sequence()
    rows = policy.replay_rows(TASK, records, PLAN)
    assert len(rows) == 3
    assert [row['teacher_in_prefix'] for row in rows] == [False, True, True]
    assert rows[2]['outcome'] == 'INCORRECT'
    for row, source in zip(rows, records):
        assert row['source_generated_token_ids'] == source['response']['token_ids']
        assert row['student_prefix'] == source['response']['messages']
        assert row['objective'].endswith('not_unlikelihood')


def test_parent_copy_rejected_but_prior_child_phrase_allowed():
    records = sequence()
    records[1] = record('check', records[:1], PLAN['guidance'] + '\nFINAL: 5')
    with pytest.raises(ValueError, match='teacher_text_in_target'):
        policy.replay_rows(TASK, records, PLAN)


def test_truncated_prefix_does_not_gain_eos():
    records = sequence()
    response = deepcopy(records[2]['response'])
    response.update(terminal=False, truncated=True)
    records[2] = history.record(TASK, 'revision', response)
    row = policy.replay_rows(TASK, records, PLAN)[2]
    assert not row['append_eos'] and row['continuation_only']


def test_triple_does_not_infer_helpfulness_from_outcome():
    triple = policy.intervention_triple(TASK, sequence(), PLAN, 'a' * 64, {'node_only': True})
    assert triple['functional_change'] == triple['helpfulness'] == 'UNASSESSED'
    assert triple['outcome_change_is_not_functional_change']
