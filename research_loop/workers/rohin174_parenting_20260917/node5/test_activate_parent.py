import copy
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from unittest.mock import patch

import pytest

from activate_parent import exposure, identity, install_private_errata, install_response_compatibility, validate_owner, watchdog
from gpu import orch_r166_parent_policy as policy
from gpu import orch_r175_parent_arms as arms


def selected():
    return json.loads((Path(policy.__file__).parents[1] / 'ARM_BUNDLE.json').read_bytes())['arm']


def state(count):
    return dict(schema=policy.community.SNAPSHOT_SCHEMA, split='TRAIN', caught_up=True,
        source_bytes=100, journal_id='a' * 32, head_sha256='b' * 64, response_count=count,
        request_count=count, sleep_count=4, delivered={}, events=[dict(actor='child',
        text='I counted three cases.', record_index=3, record_sha256='c' * 64,
        commit_record_index=4, commit_record_sha256='d' * 64)])


def seed():
    return dict(schema=policy.SCHEMA, journal_id='a' * 32, attempts=[], object_delivered_turns={},
        last_response_count=0, last_request_count=0, prospective_request_count=0,
        credits={}, grammar_delivered=False)


def config(tmp_path):
    text = tmp_path / 'principles.txt'
    text.write_text('Use actual TRAIN evidence.')
    template = {key + '_path': str(text) for key in ('programme', 'principles')}
    template.update({key + '_sha256': policy.parent.sha(text) for key in ('programme', 'principles')})
    original = policy.community.build_config(template, learner_id='C3', node='ovx3',
        root='/localhome/local-rohing/orch_r153_node5_test/C3',
        source_root='/localhome/local-rohing/orch_node5_test/source', hard_end_unix=time.time() + 7200)
    document = policy.build_config(original, seed_ref={},
        cursor_store='/localhome/local-rohing/orch_node5_test/cursor', community_learner=True)
    return arms.configure(document, selected())


def reply():
    return dict(speak=True, message='What did those three cases show, compared with your prediction?',
        rationale=json.dumps(dict(object_id='cases', source_records=[3], disposition='continue',
        next_task=None, perception=dict(record_index=3, record_sha256='c' * 64,
        quote='I counted three cases.'), credit=None, relapse_credit_id=None)))


def test_real_owned_tick_prompt_and_parser_provenance():
    root = Path(policy.__file__).parents[1]
    assert Path(policy.tick.__code__.co_filename).resolve() == (root / 'gpu/orch_r166_parent_policy.py').resolve()
    assert Path(policy.prompt.__code__.co_filename).resolve() == (root / 'gpu/orch_r166_parent_policy.py').resolve()
    assert 'bound_r175_arm' in (root / 'gpu/orch_r166_parent_policy.py').read_text()
    assert arms.SCHEMA + '_' + selected() == policy.PROMPT_POLICY_MARKER


def test_bound_sanctioned_transport_without_credentials_copy():
    root = Path(policy.__file__).parents[1]
    transport = json.loads((root / 'TRANSPORT_REFERENCE.json').read_bytes())
    assert transport['mode'] == 'SANCTIONED_EXISTING_HOST_WRAPPER_DELEGATION'
    assert transport['credentials_copied'] is False
    assert hashlib.sha256(Path(transport['path']).read_bytes()).hexdigest() == transport['sha256']
    assert 'exec bash ' in (root / 'gpu/ovx3_ssh.sh').read_text()
    assert not (root / 'gpu/hosts.env').exists()


def test_actual_configured_cap_and_response_clock(tmp_path):
    document = config(tmp_path)
    spec = arms.specification(selected())
    assert document['cadence_responses'] == spec['cadence']
    assert document['r175_word_limit'] == spec['words']
    assert document['schedule_on'] == 'response'
    assert document['object_turn_limit'] == 3


def test_private_errata_wraps_actual_r166_prompt_without_validator_change(tmp_path):
    root = Path(policy.__file__).parents[1]
    old_prompt, old_decision = policy.prompt, policy.decision
    try:
        base = install_private_errata(policy, root / 'PARENT_METADATA_ERRATA_V1.md')
        assert base is old_prompt
        current = state(arms.specification(selected())['cadence'])
        instruction, payload = policy.prompt(config(tmp_path), current, policy.memory(seed(), [], current))
        assert 'next_task' in instruction and 'MUST be JSON null' in instruction
        assert policy.decision is old_decision
        assert Path(base.__code__.co_filename).resolve() == (root / 'gpu/orch_r166_parent_policy.py').resolve()
    finally:
        policy.prompt = old_prompt


def test_request_clock_cannot_dispatch_and_pending_cannot_replay(tmp_path):
    document = config(tmp_path)
    output = tmp_path / 'output'
    output.mkdir()
    current = state(0)
    current['request_count'] = 100
    publication = dict(id='publication', path='/inbox/publication.json', sha256='d' * 64)
    with patch.object(policy.parent, 'strong', return_value=(reply(), 'CPU_MOCK', {})) as provider, \
            patch.object(policy.parent, 'publish', return_value=publication) as publish:
        assert policy.tick(tmp_path, document, output, seed(), current)['status'] == 'WAITING_FOR_NEW_CHILD_BOUNDARY'
        provider.assert_not_called()
        current = state(document['cadence_responses'])
        assert policy.tick(tmp_path, document, output, seed(), current)['status'] == 'PUBLISHED'
        assert policy.tick(tmp_path, document, output, seed(), state(100))['status'] == 'AWAITING_RENDER'
        assert provider.call_count == publish.call_count == 1


def test_lossless_rationale_object_wraps_both_strict_parsers(tmp_path):
    from gpu import orch_route_parent_campaign_providers as providers
    root = Path(policy.__file__).parents[1]
    original_provider, original_community = providers.response_schema, policy.community.response_schema
    original_decision = policy.decision
    try:
        provenance = install_response_compatibility(policy, root)
        response = reply()
        response['rationale'] = json.loads(response['rationale'])
        expected = copy.deepcopy(response)
        for parse in (providers.response_schema, policy.community.response_schema):
            parsed = parse(json.dumps(response))
            assert json.loads(parsed['rationale']) == expected['rationale']
            assert parsed['message'] == expected['message'] and parsed['speak'] == expected['speak']
        current = state(10)
        assert policy.decision(response, current, policy.memory(seed(), [], current)) == expected['rationale']
        assert policy.decision is original_decision
        assert set(provenance['effective_files'].values()) == {str(root / 'gpu/orch_r175_parent_response.py')}
        response['rationale']['object_id'] = 'UPPERCASE'
        with pytest.raises(ValueError):
            policy.decision(response, current, policy.memory(seed(), [], current))
        response['rationale']['object_id'] = expected['rationale']['object_id']
        response['rationale']['next_task'] = 'Not allowed on continue'
        with pytest.raises(ValueError, match='no_unbound_task'):
            policy.decision(response, current, policy.memory(seed(), [], current))
        response['message'] = ' '.join(['word'] * (arms.specification(selected())['words'] + 1))
        for parse in (providers.response_schema, policy.community.response_schema):
            with pytest.raises(ValueError):
                parse(json.dumps(response))
    finally:
        providers.response_schema, policy.community.response_schema = original_provider, original_community


def test_wrong_arm_fails_before_provider(tmp_path):
    document = config(tmp_path)
    document['r175_arm'] = 'H'
    with patch.object(policy.parent, 'strong') as provider:
        with pytest.raises(ValueError, match='bound_r175_arm'):
            policy.tick(tmp_path, document, tmp_path, seed(), state(100))
        provider.assert_not_called()


def test_parser_rejects_actual_arm_word_and_byte_overflow():
    from gpu.orch_route_parent_campaign_providers import response_schema
    words = arms.specification(selected())['words']
    response = dict(speak=True, message=' '.join(['word'] * words), rationale='CPU fixture')
    assert response_schema(json.dumps(response)) == response
    response['message'] += ' overflow'
    with pytest.raises(ValueError):
        response_schema(json.dumps(response))
    response['message'] = 'x' * 4097
    with pytest.raises(ValueError):
        response_schema(json.dumps(response))


def test_publication_without_render_is_not_exposure():
    assert exposure(dict(id='new'), 'message', state(1)) is None


def test_exact_render_starts_three_completed_sleep_clock():
    current = state(1)
    current['delivered']['new'] = dict(speaker='Astra', inbox_sha256='owned',
        text_sha256=hashlib.sha256(b'message').hexdigest(), record_index=75,
        record_sha256='e' * 64, request_count=10, sleep_count=4)
    proof = exposure(dict(id='new', sha256='owned'), 'message', current)
    assert proof['three_sleep_check_at'] == 7
    assert proof['withdrawal_complete_at'] == 8
    wrong = copy.deepcopy(current)
    wrong['delivered']['new']['inbox_sha256'] = 'other'
    with pytest.raises(ValueError):
        exposure(dict(id='new', sha256='owned'), 'message', wrong)


def test_C2_and_wrong_pid_start_are_never_signal_targets():
    actual = dict(pid=10, start_ticks=20, cwd='/cpu', argv_sha256='hash', uid=os.getuid(), state='S')
    row = dict(actual, label='C2')
    with pytest.raises(ValueError):
        validate_owner(row, actual)
    row.update(label='C3', start_ticks=21)
    with pytest.raises(ValueError):
        validate_owner(row, actual)


def test_CPU_pidfd_watchdog_resumes_only_exact_dummy_parent(tmp_path):
    process = subprocess.Popen([sys.executable, '-B', '-c',
        'import time; print("ready", flush=True); time.sleep(20)'], stdout=subprocess.PIPE, text=True)
    descriptor = None
    try:
        assert process.stdout.readline().strip() == 'ready'
        actual = identity(process.pid)
        row = dict(actual, label='C3')
        validate_owner(row, actual)
        descriptor = os.pidfd_open(process.pid)
        signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
        deadline = time.monotonic() + 2
        while identity(process.pid)['state'] not in ('T', 't') and time.monotonic() < deadline:
            time.sleep(.01)
        assert identity(process.pid)['state'] in ('T', 't')
        read_end, write_end = os.pipe()
        watcher = os.fork()
        if watcher == 0:
            os.close(write_end)
            watchdog(descriptor, read_end, tmp_path)
        os.close(read_end)
        os.close(write_end)
        os.waitpid(watcher, 0)
        deadline = time.monotonic() + 2
        while identity(process.pid)['state'] in ('T', 't') and time.monotonic() < deadline:
            time.sleep(.01)
        assert identity(process.pid)['start_ticks'] == actual['start_ticks']
        assert identity(process.pid)['state'] not in ('T', 't')
        assert (tmp_path / 'WATCHDOG_RESUMED_EXACT_PARENT.json').exists()
    finally:
        if descriptor is not None:
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
            os.close(descriptor)
        process.terminate()
        process.wait(timeout=5)
