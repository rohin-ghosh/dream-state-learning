from copy import deepcopy

import pytest

from organism_v6 import orch_r114_shared_judge as judge


def obstacle():
    return dict(kind='obstacle', obstacle_text='The tool returned an error.',
        child_text='I will keep investigating. I can test the other interface. I will stop and use that result.',
        episode_complete=True, cap_hit=False)


def persisted():
    return dict(status='COMPLETE', reason='', label='PERSISTED',
        engagement=[dict(sentence_index=0, quote='keep investigating')],
        changed_approach=[dict(sentence_index=1, quote='test the other interface')],
        stopping_decision=[dict(sentence_index=2, quote='stop and use that result')],
        loop_evidence=[], abandonment_evidence=[])


def test_post_answer_statistic_has_no_persistence_claim():
    result = judge.post_answer_exploration(list(range(100)), 20,
        final_answer_present=True, cap_hit=False)
    assert result['post_answer_exploration'] is True
    assert 'persistent' not in result
    assert result['descriptive_only'] is True


@pytest.mark.parametrize('final,cap', [(False, False), (True, True)])
def test_post_answer_exploration_requires_bounded_final(final, cap):
    result = judge.post_answer_exploration(list(range(100)), 20,
        final_answer_present=final, cap_hit=cap)
    assert result['post_answer_exploration'] is False


def test_obstacle_request_preserves_visible_feedback_and_is_greedy():
    result = judge.request(obstacle())
    assert result['temperature'] == 0 and result['do_sample'] is False
    assert 'tool returned an error' in result['messages'][1]['content']
    assert result['model'] == 'Qwen2.5-14B-Instruct'


@pytest.mark.parametrize('key', ['score', 'gold', 'hidden_verdict', 'parent_model', 'condition', 'checkpoint'])
def test_hidden_metadata_not_accepted(key):
    with pytest.raises(ValueError, match='blind_input_allowlist'):
        judge.request(dict(obstacle(), **{key: 'hidden'}))


def test_persisted_requires_grounded_continuation_not_success():
    result = judge.validate_annotation(obstacle(), persisted())
    assert result['label'] == 'PERSISTED'
    assert result['establishes_retained_learning'] is False
    assert result['stops_or_selects_branch'] is False


@pytest.mark.parametrize('field', ['engagement', 'changed_approach', 'stopping_decision'])
def test_three_persistence_requirements(field):
    annotation = persisted()
    annotation[field] = []
    with pytest.raises(ValueError, match='persistence_requires'):
        judge.validate_annotation(obstacle(), annotation)


@pytest.mark.parametrize('field,value', [('cap_hit', True), ('episode_complete', False)])
def test_incomplete_or_capped_episode_not_persisted(field, value):
    document = obstacle()
    document[field] = value
    with pytest.raises(ValueError, match='observed_bounded_decision'):
        judge.validate_annotation(document, persisted())


def test_invented_evidence_rejected():
    annotation = persisted()
    annotation['changed_approach'][0]['quote'] = 'I won the game'
    with pytest.raises(ValueError, match='verbatim_evidence_required'):
        judge.validate_annotation(obstacle(), annotation)


def test_cap_alone_is_not_looping():
    annotation = persisted()
    annotation.update(label='LOOPED', engagement=[], changed_approach=[], stopping_decision=[])
    with pytest.raises(ValueError, match='loop_evidence_not_cap_alone'):
        judge.validate_annotation(dict(obstacle(), cap_hit=True), annotation)


def test_unresolved_not_abandoned():
    annotation = persisted()
    annotation.update(status='UNRESOLVED', label=None, reason='continuation is missing',
        engagement=[], changed_approach=[], stopping_decision=[])
    assert judge.validate_annotation(obstacle(), annotation)['label'] is None


@pytest.mark.parametrize('action', judge.OPEN_ACTIONS)
def test_open_turn_actions_are_descriptive(action):
    document = dict(kind='open_turn', invitation=judge.OPEN_TURN,
        environment_context='A public environment', child_text='A recorded child action.')
    annotation = dict(status='COMPLETE', reason='', action=action,
        evidence=[dict(sentence_index=0, quote='recorded child action')])
    assert judge.validate_annotation(document, annotation)['action'] == action


def test_empty_open_turn_not_stop():
    document = dict(kind='open_turn', invitation=judge.OPEN_TURN,
        environment_context='', child_text='')
    with pytest.raises(ValueError, match='observed_open_action_required'):
        judge.validate_annotation(document, dict(status='COMPLETE', reason='', action='STOP', evidence=[]))


def test_invitation_has_no_prescribed_question():
    document = dict(kind='open_turn', invitation='Now ask a question.',
        environment_context='', child_text='Why?')
    with pytest.raises(ValueError, match='fixed_goal_free_invitation'):
        judge.request(document)


def test_held_schema_and_old_prompt_preserved():
    document = dict(kind='held', task_text='task', child_text='First. Then.')
    result = judge.request(document)
    old = judge.previous.request(document)
    assert result['messages'][1] == old['messages'][1]
    assert result['prompt_sha256'] != old['prompt_sha256']
    assert judge.MORNING_CUT_UTC == '2026-09-15T17:00:00Z'


def test_request_does_not_mutate_inputs():
    document = obstacle()
    original = deepcopy(document)
    judge.request(document)
    assert document == original
