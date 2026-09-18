from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from organism_v6 import orch_r108_code_parent_r114_f3 as policy


ROOT = Path(__file__).resolve().parents[1]


def texts():
    protocol = (ROOT / 'research_notes/analysis/orch_r108_code_parent_r114_f3_20260915_attempt1/BATTLE_PLAN_V4_BOUND.md').read_text()
    principles = (ROOT / 'research_notes/analysis/orch_r108_code_parent_r113_f3_20260915_attempt1/PRINCIPLES_BOUND.md').read_text()
    return protocol, principles


def context(split='TRAIN', actor='child'):
    task = policy.tasks(split)[0]
    text = 'My response to the completed task.'
    return [dict(split=split, task_id=task['task_id'], task_sha256=task['content_sha256'],
        visibility='CHILD_VISIBLE', actor=actor, text=text, source_sha256=policy.text_sha(text),
        event_type='text', completed_response=True, child_received=True)]


def test_exact_v4_fixed_parent_useful_organisation_feedback_and_broad_permission():
    protocol, principles = texts()
    template = policy.parent_template(protocol)
    assert 'Use the feedback the child itself received' in template
    assert "allow the child's own useful organisation" in template
    assert 'nothing here is a catalogue you must enact' in template
    expected = template
    for key in ('GAME', 'STYLE', 'NUDGING', 'FOCUS'):
        expected = expected.replace('[' + key + ']', policy.DEFAULT_FIELDS[key])
    assert policy.parent_prompt(protocol, principles) == expected + '\n\n' + principles
    assert '[REFLECTION]' not in template
    with pytest.raises(ValueError, match='exact_v4_protocol'):
        policy.parent_prompt(protocol + 'edited', principles)
    with pytest.raises(ValueError, match='exact_principles'):
        policy.parent_prompt(protocol, principles + 'edited')


def test_head_mutates_only_focus_style_reflection_at_next_boundary_with_lineage():
    before = deepcopy(policy.DEFAULT_FIELDS)
    changes = dict(STYLE='Supportive but critical of unsupported reasoning.', FOCUS='Notice when you are supplying the next action.',
        REFLECTION=dict(mode='short', max_new_tokens=512))
    update = policy.head_update(before, changes, source_sha256='a' * 64, next_cycle=2)
    assert update['status'] == 'BOUND_FOR_NEXT_CYCLE' and update['next_cycle'] == 2
    assert before == policy.DEFAULT_FIELDS
    assert update['fields']['REFLECTION']['max_new_tokens'] == 512
    assert update['fields_sha256'] != update['previous_fields_sha256']
    assert update['changes_lifetime_caps'] is False and update['live_source_mutation'] is False
    assert update['stop_life'] is False


@pytest.mark.parametrize('changes', [dict(GAME='another game'), dict(CADENCE='mid-generation'),
    dict(REFLECTION=dict(mode='long', max_new_tokens=999999)), dict(STYLE=''),
    dict(FOCUS=False), dict(REFLECTION=dict(mode='short', max_new_tokens=True))])
def test_bad_head_plan_keeps_previous_not_life_failure_or_retry(changes):
    result = policy.head_update(policy.DEFAULT_FIELDS, changes, source_sha256='a' * 64, next_cycle=1)
    assert result['status'] == 'UNUSABLE_KEEP_PREVIOUS'
    assert result['fields'] == policy.DEFAULT_FIELDS
    assert result['stop_life'] is False and result['retry'] is False


def test_exact_goal_free_open_turn_parented_and_unparented_no_forced_json():
    for parent_present, split in [(True, 'TRAIN'), (False, 'DEV')]:
        observed = policy.open_turn_messages(context(split), parent_present=parent_present, task_finished=True)
        assert observed[-1] == dict(role='user', content='The task is over; the environment is still here.')
        assert observed[0]['content'] == context(split)[0]['text']
        assert not any(row['role'] == 'system' for row in observed)
    with pytest.raises(ValueError, match='actual_finished_task_context_required'):
        policy.open_turn_messages(context(), parent_present=True, task_finished=False)
    with pytest.raises(ValueError, match='open_after_completed_response'):
        policy.open_turn_messages([dict(context()[0], completed_response=False)], parent_present=True, task_finished=True)


def test_unparented_open_turn_has_no_parent_final_or_hidden_context():
    with pytest.raises(ValueError, match='unparented_context_has_no_parent'):
        policy.open_turn_messages(context('DEV', 'parent'), parent_present=False, task_finished=True)
    with pytest.raises(ValueError, match='open_context_split_no_final'):
        policy.open_turn_messages(context('FINAL'), parent_present=False, task_finished=True)
    with pytest.raises(ValueError, match='open_context_child_visible_only'):
        policy.open_turn_messages([dict(context()[0], visibility='HIDDEN_ORACLE')], parent_present=True, task_finished=True)


def test_focused_mode_exact_two_predeclared_dev_tasks_not_final():
    assert [task['task_id'] for task in policy.focused_tasks()] == ['R113_F3_DEV_0001', 'R113_F3_DEV_0002']
    for task in policy.focused_tasks():
        messages = policy.focused_messages(task)
        assert messages[0]['content'].endswith('\nfocus and give the answer')
        assert task['reference_expression'] not in str(messages)
    with pytest.raises(ValueError, match='fixed_two_dev_only'):
        policy.focused_messages(policy.tasks('FINAL')[0])
    with pytest.raises(ValueError, match='fixed_two_dev_only'):
        policy.focused_messages(policy.tasks('DEV')[2])


def test_final_cut_is_september15_1700_not_september16_and_deduplicated():
    assert policy.FINAL_CUT == datetime(2026, 9, 15, 17, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match='no_final_before_corrected_cut'):
        policy.readout_plan(3, policy.FINAL_CUT - timedelta(seconds=1), stage='final_cut')
    final = policy.readout_plan(3, policy.FINAL_CUT, stage='final_cut')
    assert final[0]['key'] == 'FINAL_CUT_20260915T170000Z' and final[0]['count'] == 8
    assert not final[0]['head_visible'] and not final[0]['exchange_visible']
    assert policy.readout_plan(3, policy.FINAL_CUT, stage='final_cut', completed=[final[0]['key']]) == []
    assert all(row['split'] != 'FINAL' for row in policy.readout_plan(3, policy.FINAL_CUT))


def test_cycle_plan_counts_new_calls_and_keeps_original_caps_unmodified():
    protocol, principles = texts()
    value = policy.artifact(protocol, principles)
    plan = policy.readout_plan(0, policy.FINAL_CUT - timedelta(hours=1))
    assert [row['count'] for row in plan] == [8, 8, 2, 1]
    assert sum(row['count'] for row in plan) + 16 + 2 == 37
    assert value['native_call_accounting']['later_cycle_readout'] == 29
    assert value['native_call_accounting']['existing_caps_not_increased']
    assert policy.readout_plan(0, policy.FINAL_CUT, completed=[row['key'] for row in plan]) == []
    assert value['comparison'] == 'PARENTING_SYSTEMS_NOT_PARENT_MODEL_ONLY'
    assert value['optimizer'] is None and value['sleep_enabled'] is False
    assert value['new_native_calls'] == value['new_provider_calls'] == 0
    assert value['final']['status'] == value['cycle_zero']['status'] == 'NOT_RUN'
    assert 'R112' in value['fable_launch'] and value['native_ready'] is False


def test_persistence_and_postanswer_metrics_are_main_judge_labels_not_heuristics():
    value = policy.artifact(*texts())
    assert value['metrics']['owner'] == 'MAIN_SHARED_JUDGE'
    assert value['metrics']['persistence_labels'] == ['PERSISTED', 'ABANDONED', 'LOOPED']
    assert value['metrics']['semantic_labels'] == 'UNASSESSED'
    assert value['metrics']['post_answer_exploration'] == 'DESCRIPTIVE_NOT_PERSISTENCE_PROOF'
    assert value['metrics']['causal_realisation_claim'] is False
