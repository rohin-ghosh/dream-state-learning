import hashlib
import json
from pathlib import Path

import pytest

from organism_v6 import orch_r108_code_parent_r111_f3 as policy


def principles():
    return Path('research_notes/analysis/orch_r108_code_parent_r111_f3_20260915_attempt1/PRINCIPLES_V2_BOUND.md').read_text()


def test_same_pair_prompt_task_seed_decoder_only_parent_identity_differs():
    value = policy.artifact(principles())
    assert value['halves']['fable']['matched_shared_sha256'] == value['halves']['astra']['matched_shared_sha256']
    assert value['halves']['fable']['physical'] == 2 and value['halves']['astra']['physical'] == 6
    assert value['halves']['fable']['parent_model'] == 'claude-fable-5-1'
    assert value['halves']['astra']['parent_model'] == 'gpt-6-astra'
    assert value['sleep_count'] == value['native_calls'] == value['provider_calls'] == 0
    assert value['matched_shared']['sleep_enabled'] is False


def test_fixed_section6_text_exact_except_four_brackets():
    document = Path('research_notes/analysis/orch_r108_code_parent_r111_f3_20260915_attempt1/BATTLE_PLAN_V2_BOUND.md').read_text()
    assert hashlib.sha256(document.encode()).hexdigest() == policy.PROTOCOL_SHA256
    lines = document.split('**The fixed parent prompt', 1)[1].splitlines()
    quoted = []
    started = False
    for line in lines:
        if line.startswith('> You are the parent of a young model.'):
            started = True
        if started:
            if not line.startswith('> '):
                break
            quoted.append(line[2:])
    assert policy.PARENT_TEMPLATE == '\n'.join(quoted)
    assert policy.parent_prompt(principles()).endswith(principles())
    with pytest.raises(ValueError):
        policy.parent_prompt(principles() + 'altered')


def test_one_open_presleep_invitation_no_cognitive_checklist():
    assert policy.PRESLEEP_PROMPT == 'What would you like to carry forward from this experience?'
    assert policy.PRESLEEP_PROMPT.count('?') == 1
    assert '\n' not in policy.PRESLEEP_PROMPT
    assert policy.REFLECTION_PROMPT == 'Reflect freely on this experience in your own words.'


def test_eight_fixed_held_ids_and_disjoint_train_no_answer_leaks():
    held = policy.tasks('HELD', 8)
    assert [row['task_id'] for row in held] == [f'R111_F3_HELD_{index:04d}' for index in range(1, 9)]
    assert held == policy.tasks('HELD', 8)
    assert len({row['content_sha256'] for row in held}) == 8
    for row in held + policy.tasks('TRAIN', 200):
        messages = policy.messages(row)
        assert row['reference_expression'] not in json.dumps(messages)
        assert 'expected' not in json.dumps(policy.public_task(row))
        assert row['content_sha256'] == policy.digest({key:value for key,value in row.items() if key != 'content_sha256'})


@pytest.mark.parametrize('response,now,status', [(None, 1, 'MISSING'), ({'status':'FAILED'}, 1, 'MISSING'),
    ({'status':'COMPLETE','child_text':'Advice'}, 10, 'MISSING'),
    ({'status':'COMPLETE','child_text':'[SILENT]'}, 1, 'SILENT')])
def test_missing_late_and_silent_continue_without_retry(response, now, status):
    value = policy.classify_intervention(response, now, 10)
    assert value['status'] == status and value['child_text'] == '' and value['no_same_api_retry']


def test_r112_explicit_gate_no_grace_inference_and_gpu6_release_required():
    assert not policy.launch_conditions('fable', explicit_release=True, own_cpu_ready=True, source_ready=True)['allowed']
    assert policy.launch_conditions('fable', watcher_go=True, explicit_release=True, own_cpu_ready=True, source_ready=True)['allowed']
    assert not policy.launch_conditions('astra', own_cpu_ready=True, source_ready=True)['allowed']


@pytest.mark.parametrize('response', ['bad JSON', [], {}, {'status':'COMPLETE'},
    {'status':'COMPLETE', 'child_text':123}, {'status':'COMPLETE', 'child_text':' '},
    {'status':'SILENT', 'child_text':'contradictory advice'}])
def test_malformed_operational_parent_response_is_missing_not_life_failure(response):
    result = policy.classify_intervention(response, 1, 10)
    assert result == dict(status='MISSING', child_text='', usable=False, no_same_api_retry=True)


def test_explicit_silent_and_normal_completed_text():
    assert policy.classify_intervention({'status':'SILENT'}, 1, 10)['status'] == 'SILENT'
    response = dict(status='COMPLETE', child_text='What caught your attention?')
    assert policy.classify_intervention(response, 1, 10)['child_text'] == response['child_text']


@pytest.mark.parametrize('condition', ['receiver_ready', 'own_cycle_complete',
    'exact_identity_verified', 'artifacts_preserved', 'outstanding_requests'])
def test_handoff_requires_receiver_and_full_boundary_not_new_backend_wait(condition):
    values = dict(receiver_ready=True, own_cycle_complete=True, outstanding_requests=False,
        exact_identity_verified=True, artifacts_preserved=True)
    assert policy.handoff_conditions(**values)['allowed']
    values[condition] = condition == 'outstanding_requests'
    assert policy.handoff_conditions(**values)['action'] == 'KEEP_RUNNING'
    assert policy.handoff_conditions(**values)['sends_signals'] is False


def test_first_artifact_matches_exact_policy_prompts_and_held_hashes():
    saved = json.loads(Path('research_notes/analysis/orch_r108_code_parent_r111_f3_20260915_attempt1/FIRST_ARTIFACT.json').read_text())
    current = policy.artifact(principles())
    assert all(saved[key] == value for key, value in current.items())
    assert saved['handoff']['receiver_ready_required']
