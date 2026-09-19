"""CPU fixture tests only; mocked publication is NOT real rendered parenting."""

import copy
import hashlib
import json
from pathlib import Path
import time
from unittest.mock import patch

import pytest

from gpu import orch_r166_parent_policy as policy
from gpu.orch_r125_stream_journal import _digest


def state(count=2, sleeps=0):
    return dict(schema=policy.community.SNAPSHOT_SCHEMA, split='TRAIN', caught_up=True,
        source_bytes=100, journal_id='a'*32, head_sha256='b'*64, response_count=count,
        request_count=count, sleep_count=sleeps, delivered={}, events=[dict(actor='child',
            text='I counted three cases.', record_index=3, record_sha256='c'*64,
            commit_record_index=4, commit_record_sha256='d'*64)])


def seed():
    return dict(schema=policy.SCHEMA, journal_id='a'*32, attempts=[], object_delivered_turns={},
        last_response_count=0, last_request_count=0, prospective_request_count=0,
        credits={}, grammar_delivered=False)


def quote():
    return dict(record_index=3, record_sha256='c'*64, quote='I counted three cases.')


def reply():
    return dict(speak=True, message='What did those three cases show, compared with your prediction?',
        rationale=json.dumps(dict(object_id='cases', source_records=[3], disposition='continue',
            next_task=None, perception=quote(), credit=None, relapse_credit_id=None)))


def change(response, **kwargs):
    details = json.loads(response['rationale'])
    details.update(kwargs)
    return dict(response, rationale=json.dumps(details))


def reference(path, value):
    policy.community.write(path, value)
    return dict(path=str(path.resolve()), sha256=policy.parent.sha(path))


@pytest.fixture
def config(tmp_path):
    text = tmp_path/'programme.txt'
    text.write_text('Responsive parenting; no fixed child ritual.')
    template = {key+'_path': str(text) for key in ('programme', 'principles')}
    template.update({key+'_sha256': policy.parent.sha(text) for key in ('programme', 'principles')})
    original = policy.community.build_config(template, learner_id='C1', node='ovx2',
        root='/localhome/local-rohing/orch_r153/C1', source_root='/localhome/local-rohing/orch_r166_source',
        hard_end_unix=time.time()+600)
    return policy.build_config(original, seed_ref=reference(tmp_path/'seed.json', seed()),
        cursor_store='/localhome/local-rohing/orch_r166_cursor/C1', community_learner=True)


def test_prospective_config_preserves_policy_and_requires_parent_validation(config):
    assert policy.validate(config) == config
    assert config['cadence_responses'] == 1
    assert config['object_turn_limit'] == 3
    assert config['community_schema'] == policy.community.SCHEMA
    for changes in ({'cadence_responses': 3}, {'object_turn_limit': 4}, {'branch': 'unparented'},
                    {'hard_end_unix': 1}, {'r166_schema': 'old'}):
        with pytest.raises(ValueError):
            policy.validate(dict(config, **changes))


def test_third_delivered_turn_releases_unresolved_and_concrete_task():
    current = state()
    memory = policy.memory(seed(), [], current)
    memory['object_delivered_turns']['cases'] = 2
    with pytest.raises(ValueError, match='third_turn'):
        policy.decision(reply(), current, memory)
    next_task = 'Continue comparing three cases from another angle.'
    response = change(reply(), disposition='set_aside', next_task=next_task,
        continuity=dict(chosen_object=dict(quote(), quote='three cases'), move_kind='perception',
            progress_basis='UNVERIFIED_NEXT_STEP', environment_receipts=[]))
    response['message'] = 'Set this correction aside, unresolved and not yet verified. ' + next_task
    policy.decision(response, current, memory)
    response['message'] = 'Set this aside for now.'
    with pytest.raises(ValueError, match='unresolved_and_next'):
        policy.decision(response, current, memory)
    memory['object_delivered_turns']['cases'] = 3
    with pytest.raises(ValueError, match='exhausted'):
        policy.decision(response, current, memory)


@pytest.mark.parametrize('mutation', ['foreign', 'parent_quote', 'quote_hash', 'unpaired_credit', 'invented_quote'])
def test_language_and_own_evidence_refusals(mutation):
    current, response = state(), reply()
    if mutation == 'foreign':
        response['message'] = '请继续。'
    elif mutation == 'parent_quote':
        current['events'][0]['actor'] = 'parent'
    elif mutation == 'quote_hash':
        response = change(response, perception=dict(quote(), record_sha256='e'*64))
    elif mutation == 'invented_quote':
        response = change(response, perception=dict(quote(), quote='I ran the GPU.'))
    else:
        response['message'] += ' CREDIT: You did it.'
    with pytest.raises(ValueError):
        policy.decision(response, current, policy.memory(seed(), [], current))


def attempt(response=None, **extra):
    response = response or reply()
    return dict(source=state(1), result=dict(status='PUBLISHED', object_id='cases',
        message=response['message'], publication=dict(id='turn1', sha256='e'*64), **extra))


def render(current, entry, request=2):
    receipt = entry['result']
    current['delivered'][receipt['publication']['id']] = dict(speaker='Astra', inbox_sha256='e'*64,
        text_sha256=hashlib.sha256(receipt['message'].encode()).hexdigest(), request_count=request,
        sleep_count=0, record_index=5, record_sha256='f'*64)


def test_publication_and_inbox_not_delivery_or_grammar():
    current, entry = state(), attempt(grammar_lesson=True)
    memory = policy.memory(seed(), [entry], current)
    assert memory['awaiting_render'] and not memory['grammar_delivered']
    assert memory['missed_floor_windows'] == [[1, 2]]
    assert memory['object_delivered_turns'] == {}
    render(current, entry)
    memory = policy.memory(seed(), [entry], current)
    assert not memory['awaiting_render'] and memory['grammar_delivered']
    assert memory['object_delivered_turns'] == {'cases': 1}
    assert memory['missed_floor_windows'] == []


def test_old_object_budget_preserved_across_sleeps():
    prior, current = seed(), state(sleeps=20)
    prior['object_delivered_turns'] = {'cases': 2}
    entry = attempt()
    render(current, entry)
    assert policy.memory(prior, [entry], current)['object_delivered_turns']['cases'] == 3


def test_credit_three_sleep_audits_and_relapse(tmp_path):
    current = state(sleeps=3)
    credit = dict(id='counted-cases', step='counted three cases', evidence=quote())
    response = change(reply(), credit=credit)
    response['message'] = 'CREDIT: You counted three cases. Which observation changes your judgment?'
    policy.decision(response, current, policy.memory(seed(), [], current))
    entry = attempt(response, credit=credit)
    render(current, entry)
    memory = policy.memory(seed(), [entry], current)
    assert [task['sleep_count'] for task in memory['audit_tasks']] == [1, 2, 3]
    assert all(task['status'] == 'DUE_UNREVIEWED' for task in memory['audit_tasks'])
    audit = dict(journal_id=current['journal_id'], credit_id=credit['id'], sleep_count=3,
        reviewer='External watcher fixture', verdict='RELAPSE', evidence=quote(),
        snapshot=reference(tmp_path/'snapshot.json', current))
    ref = reference(tmp_path/'review.json', audit)
    policy.bind_watcher_audits(memory, [ref], current)
    with pytest.raises(ValueError, match='respond_to_credit_relapse'):
        policy.decision(reply(), current, memory)
    response = change(reply(), relapse_credit_id=credit['id'])
    response['message'] = 'NOTICE this repeated correction: why did your judgment change without new observation?'
    policy.decision(response, current, memory)
    with pytest.raises(ValueError, match='three_sleep_window'):
        policy.bind_watcher_audits(memory, [ref, ref], current)


def test_grammar_matches_real_parser_without_tool_execution():
    from gpu.orch_r153_community_service import parse_action
    assert parse_action('{"op":"list_messages","cursor":0}') == {'op': 'list_messages', 'cursor': 0}
    assert 'no surrounding prose' in policy.GRAMMAR


def test_tick_once_then_pending_no_replay(config, tmp_path):
    output = tmp_path/'output'
    output.mkdir()
    with patch.object(policy.parent, 'strong', return_value=(reply(), 'CPU_MOCK', {})) as provider, \
            patch.object(policy.parent, 'publish', return_value=dict(id='turn1', sha256='e'*64)) as publish:
        result = policy.tick(tmp_path, config, output, seed(), state())
        assert result['status'] == 'PUBLISHED'
        message = publish.call_args.args[-1]
        assert message.endswith(policy.GRAMMAR)
        assert policy.tick(tmp_path, config, output, seed(), state(3))['status'] == 'AWAITING_RENDER'
        assert provider.call_count == publish.call_count == 1


def test_unknown_publication_and_inflight_refuse(config, tmp_path):
    output = tmp_path/'output'
    output.mkdir()
    with patch.object(policy.parent, 'strong', return_value=(reply(), 'CPU_MOCK', {})), \
            patch.object(policy.parent, 'publish', side_effect=TimeoutError):
        assert policy.tick(tmp_path, config, output, seed(), state())['status'] == 'PUBLICATION_UNKNOWN'
    with pytest.raises(ValueError, match='uncertain_publication'):
        policy.tick(tmp_path, config, output, seed(), state(3))
    list(output.glob('parent_*'))[0].joinpath('RESULT.json').unlink()
    with pytest.raises(ValueError, match='unfinished_attempt'):
        policy.tick(tmp_path, config, output, seed(), state(3))


def test_incomplete_bootstrap_does_not_dispatch(config, tmp_path):
    with patch.object(policy.parent, 'strong') as provider:
        assert policy.tick(tmp_path, config, tmp_path, seed(), dict(state(), caught_up=False))['status'] == 'VERIFIED_BOOTSTRAP_IN_PROGRESS'
    provider.assert_not_called()


def test_predecessor_export_is_read_only(config, tmp_path):
    output = tmp_path/'old'
    output.mkdir()
    directory = output/'parent_0001'
    directory.mkdir()
    source_ref = reference(directory/'SOURCE.json', state(1))
    entry = attempt()
    entry['result']['source_sha256'] = source_ref['sha256']
    reference(directory/'RESULT.json', entry['result'])
    before = {str(path): path.read_bytes() for path in directory.iterdir()}
    prior = policy.export_predecessor(output, state())
    assert {str(path): path.read_bytes() for path in directory.iterdir()} == before
    assert policy.memory(prior, [], state())['awaiting_render']
    assert not (directory/'DELIVERED.json').exists()


def test_gate_no_GO_no_transport(config, tmp_path):
    config_ref = reference(tmp_path/'config.json', config)
    gate_ref = reference(tmp_path/'gate.json', dict(schema=policy.SCHEMA, status='PREPARED'))
    with patch.object(policy.parent, 'remote') as remote, patch.object(policy.parent, 'strong') as provider:
        with pytest.raises(ValueError, match='Main_successor_GO'):
            policy.serve(config_ref, tmp_path, tmp_path/'output', gate_ref, once=True)
    remote.assert_not_called()
    provider.assert_not_called()
    assert not (tmp_path/'output').exists()


def test_English_prose_with_exact_Chinese_quote_and_accented_name():
    current = state()
    current['events'][0]['text'] = '我数了三个。'
    evidence = dict(quote(), quote='我数了三个。')
    response = change(reply(), perception=evidence)
    response['message'] = 'René, you wrote "我数了三个。" What observation supports that judgment?'
    policy.decision(response, current, policy.memory(seed(), [], current))
    response['message'] += ' 请继续。'
    with pytest.raises(ValueError, match='not_language_proof'):
        policy.decision(response, current, policy.memory(seed(), [], current))


def test_validation_failure_records_floor_misses_and_does_not_publish(config, tmp_path):
    output = tmp_path/'output'
    output.mkdir()
    response = dict(reply(), message='请继续。')
    with patch.object(policy.parent, 'strong', return_value=(response, 'CPU_MOCK', {})), \
            patch.object(policy.parent, 'publish') as publish:
        result = policy.tick(tmp_path, config, output, seed(), state())
    assert result['status'] == 'VALIDATION_FAILED'
    assert result['memory']['missed_floor_windows'] == [[1, 2]]
    publish.assert_not_called()
    stored = json.loads(next(output.glob('parent_*/RESULT.json')).read_text())
    assert 'not_language_proof' in stored['error']


def test_total_word_cap_includes_grammar_and_prompt_explains(config, tmp_path):
    current = state()
    instruction, unused = policy.prompt(config, current, policy.memory(seed(), [], current))
    assert str(90-len(policy.GRAMMAR.split()))+' whitespace-separated words' in instruction
    response = dict(reply(), message=' '.join(['word']*80))
    output = tmp_path/'output'
    output.mkdir()
    with patch.object(policy.parent, 'strong', return_value=(response, 'CPU_MOCK', {})), \
            patch.object(policy.parent, 'publish') as publish:
        assert policy.tick(tmp_path, config, output, seed(), current)['status'] == 'VALIDATION_FAILED'
    publish.assert_not_called()


def test_rolling_two_boundary_floor_not_disjoint_pairs():
    current = state(4)
    first = attempt()
    second = copy.deepcopy(first)
    second['result']['publication']['id'] = 'turn2'
    render(current, first, request=1)
    render(current, second, request=4)
    assert policy.memory(seed(), [first, second], current)['missed_floor_windows'] == [[2, 3]]


def test_valid_gate_and_real_serve_seam_with_mocked_remote(config, tmp_path):
    repository = Path(policy.__file__).resolve().parents[1]
    pins = {name: policy.parent.sha(repository/name) for name in
            (*policy.SOURCE_FILES, 'gpu/ovx2_ssh.sh')}
    tests = {name: policy.parent.sha(repository/name) for name in (
        'tests/test_orch_r166_parent_policy.py', 'tests/test_orch_r166_parent_snapshot.py')}
    cpu_ref = reference(tmp_path/'cpu.json', dict(status='PASS', execution_kind='CPU_ONLY',
        source_pins=pins, test_pins=tests))
    custody_ref = reference(tmp_path/'custody.json', dict(kind='CPU_ONLY_SYNTHETIC_CUSTODY'))
    intake_ref = reference(tmp_path/'intake.json', dict(kind='CPU_ONLY_SYNTHETIC_SCOPE'))
    output = tmp_path/'output'
    gate = dict(schema=policy.SCHEMA, status='MAIN_GO', confirmed_by='Main',
        config_sha256=_digest(config), output=str(output), parented_scope=True,
        expires_unix=time.time()+300, custody=dict(predecessor_terminal=True,
            no_competing_parent=True, pending_reconciled=True, receipt=custody_ref),
        cpu_receipt=cpu_ref, intake=intake_ref, source_pins=pins, remote_source_pins=pins)
    config_ref = reference(tmp_path/'config.json', config)
    gate_ref = reference(tmp_path/'gate.json', gate)
    with patch.object(policy.parent, 'remote', side_effect=[{'verified': True},
        dict(snapshot=state(), reference={'path': '/unused/cursor.json', 'sha256': 'a'*64})]), \
        patch.object(policy.parent, 'strong', return_value=(reply(), 'CPU_MOCK', {})), \
        patch.object(policy.parent, 'publish', return_value={'id': 'turn1', 'sha256': 'e'*64}):
        assert policy.serve(config_ref, repository, output, gate_ref, once=True)['status'] == 'PUBLISHED'
    assert (output/'BINDING.json').exists()
    assert (output/'POLL_00000000.json').exists()
    assert (output/'STATUS_00000000.json').exists()
    gate['custody']['no_competing_parent'] = False
    with pytest.raises(ValueError, match='clean_handoff'):
        policy.verify_gate(config, repository, output, gate)


def same_object_reply():
    task = 'Continue testing three cases from another angle.'
    return change(dict(reply(), message='Set this correction aside, unresolved and not yet verified. '+task),
        disposition='set_aside', next_task=task, continuity=dict(
            chosen_object=dict(quote(), quote='three cases'), move_kind='test',
            progress_basis='UNVERIFIED_NEXT_STEP', environment_receipts=[]))


def tool_evidence(current):
    text = 'The test returned a mismatch in case three.'
    evidence = dict(record_index=6, record_sha256='f'*64, quote=text,
                    inbox_id='tool-observation', inbox_sha256='a'*64)
    current['events'].append(dict(actor='environment', speaker='Tool', text=text,
                                record_index=6, record_sha256='f'*64))
    current['delivered']['tool-observation'] = dict(speaker='Tool', inbox_sha256='a'*64,
        text_sha256=hashlib.sha256(text.encode()).hexdigest(), record_index=6,
        record_sha256='f'*64, request_count=current['request_count'], sleep_count=0)
    return evidence


def test_release_rejects_automatic_new_world_and_missing_continuity():
    current = state()
    memory = policy.memory(seed(), [], current)
    response = same_object_reply()
    response['message'] = 'Set this mismatch aside, unresolved. Start a new world instead.'
    response = change(response, next_task='Start a new world instead.')
    with pytest.raises(ValueError, match='preserve_chosen_object'):
        policy.decision(response, current, memory)
    response = change(same_object_reply(), continuity=None)
    with pytest.raises(ValueError, match='same_chosen_object'):
        policy.decision(response, current, memory)


def test_repeated_move_across_sleep_requires_new_actual_receipt():
    current = state(3, sleeps=4)
    response = same_object_reply()
    details = json.loads(response['rationale'])
    old = attempt(response, continuity=details['continuity'], next_task=details['next_task'])
    render(current, old)
    memory = policy.memory(seed(), [old], current)
    assert memory['object_delivered_turns']['cases'] == 1
    with pytest.raises(ValueError, match='repeated_move_without_new'):
        policy.decision(response, current, memory)
    evidence = tool_evidence(current)
    details['continuity'].update(progress_basis='RENDERED_TOOL_OBSERVATION', environment_receipts=[evidence])
    updated = dict(response, rationale=json.dumps(details))
    policy.decision(updated, current, memory)
    current['delivered']['tool-observation']['inbox_sha256'] = 'b'*64
    with pytest.raises(ValueError, match='actual_rendered_Tool'):
        policy.decision(updated, current, memory)


def test_child_claim_not_environment_evidence_and_unverified_is_explicit():
    current = state()
    memory = policy.memory(seed(), [], current)
    response = same_object_reply()
    continuity = json.loads(response['rationale'])['continuity']
    continuity['progress_basis'] = 'RENDERED_TOOL_OBSERVATION'
    with pytest.raises(ValueError, match='no_invented_environment'):
        policy.decision(change(response, continuity=continuity), current, memory)
    response['message'] = response['message'].replace('not yet verified', 'successful')
    with pytest.raises(ValueError, match='unverified_step_explicit'):
        policy.decision(response, current, memory)


def test_minimal_prompt_payload_preserves_original_bytes_and_has_no_eval_target():
    original = 'Original instructions, including résumé and exact whitespace.\n '.encode()
    payload = policy.prompt_policy_bytes(original)
    assert payload == original + policy.PROMPT_POLICY.encode()
    assert 'Every parent turn invite rich re-perception' in policy.PROMPT_POLICY
    assert 'Every few turns connect perception to judgment' in policy.PROMPT_POLICY
    assert 'NOT a checklist' in policy.PROMPT_POLICY
    assert 'SAME object' in policy.PROMPT_POLICY
    assert 'ON' not in policy.PROMPT_POLICY.split()
    assert 'OFF' not in policy.PROMPT_POLICY.split()
    assert 'empty-context' not in policy.PROMPT_POLICY
    with pytest.raises(ValueError, match='already_present'):
        policy.prompt_policy_bytes(payload)


@pytest.mark.parametrize('frozen', [False, True])
def test_prompt_only_config_changes_only_principles_preserving_contrasts(config, tmp_path, frozen):
    original = dict(config, cadence_responses=3, frozen=frozen, training_enabled=not frozen)
    if frozen:
        original['branch'] = 'existing_parented_frozen'
    new_path = tmp_path/'NEW_PRINCIPLES.md'
    old_raw = Path(original['principles_path']).read_bytes()
    new_path.write_bytes(policy.prompt_policy_bytes(old_raw))
    ref = dict(path=str(new_path), sha256=policy.parent.sha(new_path))
    successor = policy.prompt_only_config(original, principles_ref=ref, existing_parented=True)
    assert {key for key in original if original[key] != successor[key]} == {
        'principles_path', 'principles_sha256'}
    assert successor['frozen'] == frozen and successor['training_enabled'] == (not frozen)
    assert successor['cadence_responses'] == 3
    assert Path(original['principles_path']).read_bytes() == old_raw
    if not frozen:
        policy.community.validate(successor)
    instruction, unused = policy.parent.prompt(successor, dict(
        schema='R133_TRAIN_PARENT_SNAPSHOT_V1', events=[]))
    assert policy.PROMPT_POLICY_MARKER in instruction
    with pytest.raises(ValueError, match='existing_parented_scope'):
        policy.prompt_only_config(original, principles_ref=ref, existing_parented=False)
    new_path.write_bytes(b'Rewritten historical principles.' + policy.PROMPT_POLICY.encode())
    ref['sha256'] = policy.parent.sha(new_path)
    with pytest.raises(ValueError, match='exact_append_only'):
        policy.prompt_only_config(original, principles_ref=ref, existing_parented=True)


def test_full_controller_prompt_contains_latest_instruction(config):
    current = state()
    instruction, payload = policy.prompt(config, current, policy.memory(seed(), [], current))
    assert policy.PROMPT_POLICY_MARKER in instruction
    assert 'not a new world each sleep' in instruction
    assert 'environment_deliveries' in json.loads(payload)


def test_rohin154_metacognition_is_attention_allocation_not_prose_volume():
    instruction = policy.PROMPT_POLICY
    for fragment in ('HOW MUCH and HOW to perceive', 'allocation of attention',
        'concrete discriminating observation', 'checking strategy',
        'not introspective prose volume', 'At every actual parent turn',
        'Every few turns ask an explicit, object-grounded question', 'SAME live object',
        'not turn these alternatives into recurring bullets'):
        assert fragment in instruction
    assert 'ROHIN154' in policy.PROMPT_POLICY_MARKER
    with pytest.raises(ValueError, match='already_present'):
        policy.prompt_policy_bytes(policy.PRIOR_PROMPT_POLICY_MARKER.encode())
