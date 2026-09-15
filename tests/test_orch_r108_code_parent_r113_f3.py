from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from organism_v6 import orch_r107_base_anchors as anchors
from organism_v6 import orch_r107_capability as capability
from organism_v6 import orch_r108_code_parent_r113_f3 as policy


ROOT = Path(__file__).resolve().parents[1] / 'research_notes/analysis/orch_r108_code_parent_r113_f3_20260915_attempt1'
BEFORE_CUT = datetime(2026, 9, 15, 12, tzinfo=timezone.utc)


def visible_event(actor='checker', text='The checker reported an empty list.', **changes):
    task = policy.tasks('TRAIN', 1)[0]
    row = dict(actor=actor, text=text, source_sha256=policy.text_sha(text), split='TRAIN',
        visibility='CHILD_VISIBLE', event_type='checker_feedback' if actor == 'checker' else 'text',
        task_id=task['task_id'], task_sha256=task['content_sha256'], child_received=True)
    return dict(row, **changes)


def readout(split, **changes):
    task = policy.tasks(split)[0]
    return dict(task_id=task['task_id'], split=split, content_sha256=task['content_sha256'],
        cycle=0, status='COMPLETE', correct=True, **changes)


def receipt(identifier, kind, status, **changes):
    return dict(call_id=identifier, life_id='prospective_f3', kind=kind, status=status,
        observed_unix=10, receipt_sha256='a' * 64, **changes)


def test_exact_v3_snapshot_principles_fixed_parent_and_fresh_prompts():
    document = (ROOT / 'BATTLE_PLAN_V3_BOUND.md').read_text()
    assert policy.text_sha(document) == policy.PROTOCOL_SHA256
    principles = (ROOT / 'PRINCIPLES_BOUND.md').read_text()
    artifact = policy.artifact(principles)
    block = document[document.index('> You are the parent of a young model.'):].split('\n\n', 1)[0]
    assert '\n'.join(line[2:] for line in block.splitlines()) == policy.previous.PARENT_TEMPLATE
    assert artifact['parent_prompt'].endswith(principles)
    assert artifact['comparison'] == 'PARENTING_SYSTEMS_NOT_PARENT_MODEL_ONLY'
    assert artifact['child_facing_prompts'] != policy.previous.artifact(principles)['child_facing_prompts']
    assert policy.PROMPTS['presleep'].count('?') == 1
    assert '\n' not in policy.PROMPTS['presleep']
    assert artifact['final']['status'] == artifact['cycle_zero']['status'] == 'NOT_RUN'
    assert artifact['optimizer'] is None and artifact['sleep_enabled'] is False
    assert artifact['optimizer_steps'] == artifact['new_native_calls'] == artifact['new_provider_calls'] == 0
    assert artifact['native_ready'] is False and artifact['old_deadlines_extended'] is False
    with pytest.raises(ValueError, match='exact_principles'):
        policy.artifact(principles + 'altered')


def test_disjoint_dev_final_train_and_bounded_historical_exclusions():
    previous = policy.previous.tasks('TRAIN', 200) + policy.previous.tasks('HELD', 8)
    historical = previous + policy.gym_policy.tasks() + anchors.tasks() + capability.tasks()
    result = policy.registry_exclusions(historical)
    assert result['status'] == 'PASS' and result['new_count'] == 216
    assert result['scope'] == 'SUPPLIED_REGISTRIES_ONLY'
    for split in ('DEV', 'FINAL'):
        assert len(policy.tasks(split)) == 8
        assert [row['task_id'] for row in policy.tasks(split)] == [f'R113_F3_{split}_{index:04d}' for index in range(1, 9)]
    row = policy.tasks('DEV')[0]
    with pytest.raises(ValueError, match='historical_prompt_collision'):
        policy.registry_exclusions([dict(id='different', prompt=row['prompt'], prompt_sha256=policy.digest(row['prompt']))])


def test_bounded_oracle_reproducible_no_answer_keys_in_model_messages():
    for split in policy.SPLITS:
        for task in policy.tasks(split):
            for case in task['tests']:
                assert policy.gym_policy.gym.evaluate(task['reference_expression'], case['arguments']) == case['expected']
            messages = policy.messages(task, phase='episode' if split == 'TRAIN' else 'readout')
            assert task['reference_expression'] not in json.dumps(messages)
            assert 'reference_expression' not in json.dumps(messages)
    with pytest.raises(ValueError, match='phase_split'):
        policy.messages(policy.tasks('FINAL')[0])


@pytest.mark.parametrize('audience', ['parent', 'head', 'exchange'])
def test_preserve_visible_checker_environment_child_text_strip_hidden_metadata(audience):
    checker = visible_event(hidden_outcome='PRIVATE_OUTCOME', answer_key='PRIVATE_KEY')
    environment = visible_event('environment', 'The tool returned []', event_type='environment_feedback')
    child = visible_event('child', 'I predicted a different checker result.')
    hidden = visible_event(visibility='HIDDEN_ORACLE', text='PRIVATE_HIDDEN')
    result = policy.context_for(audience, [checker, environment, child, hidden], [readout('FINAL', raw='PRIVATE_FINAL')])
    assert [row['text'] for row in result['train_events']] == [checker['text'], environment['text'], child['text']]
    assert not result['dev_readouts']
    assert 'PRIVATE_' not in json.dumps(result)
    assert policy.context_for(audience, [visible_event(split='FINAL')])['train_events'] == []


def test_dev_machine_summary_allowed_to_head_but_final_never_exposed():
    dev = readout('DEV', answer_key='PRIVATE_DEV_KEY', raw='PRIVATE_DEV_RAW')
    result = policy.context_for('head', [], [dev, readout('FINAL', raw='PRIVATE_FINAL')])
    assert len(result['dev_readouts']) == 1 and result['dev_readouts'][0]['correct'] is True
    assert 'PRIVATE_' not in json.dumps(result)
    assert policy.context_for('parent', [], [dev])['dev_readouts'] == []
    assert policy.context_for('exchange', [], [dev])['dev_readouts'] == []


def test_mislabelled_final_or_tampered_capture_fails_closed():
    final = readout('FINAL')
    final['split'] = 'DEV'
    with pytest.raises(ValueError, match='registered_dev_only'):
        policy.context_for('head', [], [final])
    with pytest.raises(ValueError, match='exact_child_visible_capture'):
        policy.public_events([visible_event(source_sha256='b' * 64)])
    with pytest.raises(ValueError, match='registered_train_event'):
        policy.public_events([visible_event(task_id=policy.tasks('FINAL')[0]['task_id'])])


def test_dev_every_cycle_final_only_zero_and_deduplicated_morning():
    initial = policy.readout_plan(0, BEFORE_CUT)
    assert [row['split'] for row in initial] == ['DEV', 'FINAL']
    for cycle in (1, 2, 9, 200):
        assert [row['split'] for row in policy.readout_plan(cycle, BEFORE_CUT)] == ['DEV']
    assert policy.readout_plan(0, BEFORE_CUT, completed=[row['key'] for row in initial]) == []
    with pytest.raises(ValueError, match='no_early_morning_final'):
        policy.readout_plan(1, BEFORE_CUT, stage='morning')
    morning = policy.readout_plan(42, policy.MORNING_CUT, stage='morning')
    assert [row['split'] for row in morning] == ['FINAL']
    assert not morning[0]['head_visible'] and not morning[0]['exchange_visible']
    assert policy.readout_plan(42, policy.MORNING_CUT, stage='morning', completed=[morning[0]['key']]) == []
    assert [row['split'] for row in policy.readout_plan(43, policy.MORNING_CUT)] == ['DEV']


def test_hourly_actual_provider_delivery_missing_late_and_child_tokens_not_caps():
    rows = [receipt('p1', 'parent', 'COMPLETE', provider_completed=True, late=False),
        receipt('p2', 'parent', 'MISSING', provider_completed=True, late=True),
        receipt('p3', 'parent', 'MISSING', provider_completed=False, late=False),
        receipt('p4', 'parent', 'SILENT', provider_completed=True, late=False),
        receipt('p5', 'parent', 'PENDING', provider_completed=False, late=False),
        receipt('c1', 'child', 'COMPLETE', output_tokens=500, max_new_tokens=4096),
        receipt('c2', 'child', 'FAILED', output_tokens=20),
        receipt('c3', 'child', 'COMPLETE'), receipt('c4', 'child', 'PENDING')]
    value = policy.hourly_exposure(rows, life_id='prospective_f3', start_unix=0, end_unix=20)
    assert value['parent_provider_completed'] == 3
    assert value['parent_delivered'] == value['parent_silent'] == value['parent_pending'] == 1
    assert value['parent_missing'] == 2 and value['parent_missing_late'] == 1
    assert value['child_tokens'] == 520 and value['child_token_counts_missing'] == 1
    assert value['child_completed'] == 2 and value['child_failed'] == value['child_pending'] == 1
    assert value['optimizer_steps'] == value['trained_child_token_exposures'] == value['sleep_count'] == 0
    assert value['semantic_effect'] == 'UNASSESSED'


@pytest.mark.parametrize('changes,code', [({'late':True}, 'late_is_missing'),
    ({'provider_completed':False}, 'delivery_requires_completion'),
    ({'optimizer_steps':1}, 'f3_has_no_optimizer'), ({'receipt_sha256':''}, 'native_receipt_provenance'),
    ({'life_id':'other'}, 'single_life_exposure'), ({'observed_unix':float('nan')}, 'receipt_time')])
def test_exposure_rejects_wrong_identity_unbound_receipts_or_fake_delivery(changes, code):
    row = receipt('p1', 'parent', 'COMPLETE', provider_completed=True, late=False)
    row.update(changes)
    with pytest.raises(ValueError, match=code):
        policy.hourly_exposure([row], life_id='prospective_f3', start_unix=0, end_unix=20)


def test_no_double_count_or_out_of_window_exposure():
    row = receipt('p1', 'parent', 'COMPLETE', provider_completed=True, late=False)
    with pytest.raises(ValueError, match='duplicate_receipt'):
        policy.hourly_exposure([row, deepcopy(row)], life_id='prospective_f3', start_unix=0, end_unix=20)
    assert policy.hourly_exposure([row], life_id='prospective_f3', start_unix=11, end_unix=20)['parent_delivered'] == 0


def test_r112_gate_and_receiver_ready_cycle_boundary_not_relaxed():
    assert not policy.previous.launch_conditions('fable', source_ready=True, own_cpu_ready=True, explicit_release=True)['allowed']
    assert policy.previous.handoff_conditions(own_cycle_complete=True, outstanding_requests=False,
        exact_identity_verified=True, artifacts_preserved=True)['action'] == 'KEEP_RUNNING'


def test_visible_oracle_checker_values_retained_hidden_nested_keys_removed():
    event = visible_event('oracle', 'Checker result', event_type='checker_output',
        outcome={'passed':False, 'answer_key':'HIDDEN'}, score=0,
        feedback=[{'actual':[], 'expected':'HIDDEN'}])
    captured = policy.public_events([event])[0]
    assert captured['outcome'] == {'passed':False}
    assert captured['score'] == 0 and captured['feedback'] == [{'actual':[]}]
    assert 'HIDDEN' not in json.dumps(captured)
    with pytest.raises(ValueError, match='feedback_delivery_required'):
        policy.public_events([dict(event, child_received=False)])
