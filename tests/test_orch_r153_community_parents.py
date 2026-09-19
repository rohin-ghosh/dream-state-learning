"""CPU-only community parent tests; providers and remote publication are mocked."""

from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import time
from unittest.mock import patch

import pytest

from gpu import orch_r153_community_parents as community
from gpu.orch_r125_stream_journal import StreamJournal
from gpu.orch_r127_pilot_console import publish_parent
from organism_v6.orch_r124_train_history import TrainHistory
from organism_v6.orch_r125_continual_stream import ContinualStream


REPOSITORY = Path(__file__).resolve().parents[1]


@pytest.fixture
def config(tmp_path):
    source = tmp_path/'principles.md'
    source.write_text('Use actual TRAIN work. No recurring child formats.')
    template = {name+'_path': str(source) for name in ('programme', 'principles')}
    template.update({name+'_sha256': community.parent.sha(source) for name in ('programme', 'principles')})
    return community.build_config(template, learner_id='C1', node='ovx2',
        root='/localhome/local-rohing/orch_r153_community/C1',
        source_root='/localhome/local-rohing/orch_r153_source', hard_end_unix=time.time()+600)


def state(count=3, delivered=None, sleeps=0):
    return dict(schema=community.SNAPSHOT_SCHEMA, split='TRAIN', response_count=count,
        sleep_count=sleeps, journal_id='a'*32, head_sha256='b'*64,
        events=[dict(actor='child', text='The story ending contradicts the earlier scene.',
            record_index=count*3, record_sha256='c'*64)], delivered=delivered or {})


def reply(object_id='story-ending', source_record=9, disposition='continue'):
    message = 'Could you check the ending against the earlier scene?'
    if disposition == 'set_aside':
        message = "Let's set this aside for now and leave room for your next interest."
    return dict(speak=True, message=message, rationale=json.dumps(dict(object_id=object_id,
        source_records=[source_record], disposition=disposition)))


def provider(response):
    return response, community.parent.STRONG, dict(output_tokens=20)


def publication(identifier='own-turn'):
    return dict(id=identifier, sha256='d'*64, path='/not/read/inbox.json')


def exposure(response, identifier='own-turn', speaker='Astra'):
    return {identifier: dict(speaker=speaker, inbox_sha256='d'*64,
        text_sha256=hashlib.sha256(response['message'].encode()).hexdigest(),
        record_index=11, record_sha256='e'*64)}


def tick(config, output, snapshot, response=None, provider_error=None, publish_error=None):
    with patch.object(community, 'snapshot', return_value=snapshot), \
            patch.object(community.parent, 'strong', return_value=provider(response or reply()),
                         side_effect=provider_error) as strong, \
            patch.object(community.parent, 'publish', return_value=publication(),
                         side_effect=publish_error) as publish:
        status = community.tick(REPOSITORY, config, output)
    return status, strong, publish


def test_config_is_existing_validator_compatible_and_sparse(config):
    assert community.parent.validate(config) == config
    assert config['parent_reasoning_effort'] == 'low'
    assert config['cadence_responses'] == 3
    for changes in ({'branch': 'R127'}, {'root': '/localhome/local-rohing/orch_r127/run'},
                    {'cadence_responses': 1}, {'parent_reasoning_effort': 'high'},
                    {'object_turn_limit': 4}, {'schedule_on': 'request'}):
        with pytest.raises(ValueError):
            community.validate(dict(config, **changes))


def test_gate_missing_or_unbound_prevents_any_transport(config, tmp_path):
    config_path = tmp_path/'config.json'
    community.parent.write(config_path, config)
    gate = tmp_path/'gate.json'
    community.parent.write(gate, dict(schema=community.GATE_SCHEMA, status='PREPARED'))
    with patch.object(community.parent, 'remote') as remote, patch.object(community.parent, 'strong') as strong:
        with pytest.raises(ValueError, match='Main_exact_roots'):
            community.serve(config_path, REPOSITORY, tmp_path/'output', gate, community.parent.sha(gate), True)
    remote.assert_not_called()
    strong.assert_not_called()
    assert not (tmp_path/'output').exists()


def test_exact_gate_pins_config_roots_and_sources(config, tmp_path):
    config_path = tmp_path/'config.json'
    community.parent.write(config_path, config)
    parents = {learner: dict(root='/localhome/local-rohing/orch_r153_community/'+learner,
        node='ovx2', source_root=config['source_root'], config_sha256='0'*64,
        output=str(tmp_path/learner)) for learner in community.LEARNERS}
    parents['C1']['config_sha256'] = community.parent.sha(config_path)
    sources = {name: community.parent.sha(REPOSITORY/name)
        for name in (*community.SOURCE_FILES, 'gpu/ovx2_ssh.sh')}
    gate = dict(schema=community.GATE_SCHEMA, status='MAIN_BOUND', parents=parents, source_pins=sources)
    gate_path = tmp_path/'gate.json'
    community.parent.write(gate_path, gate)
    assert community.verify_gate(config_path, REPOSITORY, tmp_path/'C1', gate_path,
        community.parent.sha(gate_path))[0] == config
    with pytest.raises(ValueError, match='exact_parent_binding'):
        community.verify_gate(config_path, REPOSITORY, tmp_path/'other', gate_path, community.parent.sha(gate_path))
    config_path.write_text(json.dumps(dict(config, parent_style='changed')))
    with pytest.raises(ValueError, match='exact_parent_binding'):
        community.verify_gate(config_path, REPOSITORY, tmp_path/'C1', gate_path, community.parent.sha(gate_path))


@pytest.fixture
def dual_gate(config, tmp_path):
    config_path = tmp_path/'config.json'
    community.parent.write(config_path, config)
    bindings = {learner: dict(root='/localhome/local-rohing/orch_r153_community/'+learner,
        node='ovx2' if learner in ('C1', 'C2') else 'a40r', source_root=config['source_root'],
        config_sha256=community.parent.sha(config_path) if learner == 'C1' else '0'*64,
        output=str(tmp_path/learner)) for learner in community.LEARNERS}
    sources = {name: community.parent.sha(REPOSITORY/name)
        for name in (*community.SOURCE_FILES, 'gpu/ovx2_ssh.sh', 'gpu/a40r_ssh.sh')}
    remote = {node: dict(sources) for node in ('ovx2', 'a40r')}
    for node, marker in (('ovx2', '1'), ('a40r', '2')):
        remote[node]['organism_v6/orch_r125_plain_context.py'] = marker*64
        remote[node]['gpu/orch_route_parent_campaign_providers.py'] = '3'*64
    gate = dict(schema=community.GATE_SCHEMA, status='MAIN_BOUND', parents=bindings,
        source_pins=sources, remote_source_pins=remote)
    return config_path, tmp_path/'gate.json', tmp_path/'C1', gate


def test_two_closures_allow_explicit_dependency_hashes_but_keep_local_checks(dual_gate):
    config_path, gate_path, output, gate = dual_gate
    community.parent.write(gate_path, gate)
    assert community.verify_gate(config_path, REPOSITORY, output, gate_path,
        community.parent.sha(gate_path))[1] == gate
    assert community.remote_source_pins(gate, 'a40r') == gate['remote_source_pins']['a40r']
    dependency = 'organism_v6/orch_r125_plain_context.py'
    gate['source_pins'][dependency] = gate['remote_source_pins']['ovx2'][dependency]
    changed = gate_path.with_name('bad_local.json')
    community.parent.write(changed, gate)
    with pytest.raises(ValueError, match='pinned_parent_source'):
        community.verify_gate(config_path, REPOSITORY, output, changed, community.parent.sha(changed))


@pytest.mark.parametrize('change', ['missing_node', 'extra_node', 'missing_dependency',
    'extra_dependency', 'short_hash', 'reader_changed', 'publisher_changed'])
def test_two_closures_reject_incomplete_or_ambiguous_remote_bindings(dual_gate, change):
    config_path, gate_path, output, gate = dual_gate
    remote = gate['remote_source_pins']
    if change == 'missing_node':
        del remote['a40r']
    elif change == 'extra_node':
        remote['ovx3'] = dict(remote['ovx2'])
    elif change == 'missing_dependency':
        del remote['a40r']['organism_v6/orch_r125_plain_context.py']
    elif change == 'extra_dependency':
        remote['a40r']['unexpected.py'] = '4'*64
    elif change == 'short_hash':
        remote['a40r']['organism_v6/orch_r125_plain_context.py'] = 'b3859e'
    elif change == 'reader_changed':
        remote['a40r']['gpu/orch_r153_community_parents.py'] = '4'*64
    else:
        remote['a40r']['gpu/orch_r127_pilot_console.py'] = '4'*64
    community.parent.write(gate_path, gate)
    with patch.object(community.parent, 'remote') as transport, patch.object(community.parent, 'strong') as provider:
        with pytest.raises(ValueError):
            community.serve(config_path, REPOSITORY, output, gate_path, community.parent.sha(gate_path), True)
    transport.assert_not_called()
    provider.assert_not_called()
    assert not output.exists()


@pytest.mark.parametrize('remote_drift', [False, True])
def test_remote_hash_script_uses_node_closure_and_rejects_drift_before_dispatch(dual_gate, remote_drift):
    config_path, gate_path, output, gate = dual_gate
    community.parent.write(gate_path, gate)
    source_root = Path(gate['parents']['C1']['source_root'])
    checked_names = []
    def remote_hash(path):
        name = str(Path(path).relative_to(source_root))
        checked_names.append(name)
        expected = gate['remote_source_pins']['ovx2'][name]
        return 'f'*64 if remote_drift and name == 'organism_v6/orch_r125_plain_context.py' else expected
    def simulated_remote(repository, config, script):
        stdout = io.StringIO()
        with patch.object(community.parent, 'sha', side_effect=remote_hash), redirect_stdout(stdout):
            exec(script, {})
        return json.loads(stdout.getvalue())
    with patch.object(community.parent, 'remote', side_effect=simulated_remote), \
            patch.object(community.parent, 'transport_preflight') as transport, \
            patch.object(community, 'tick', return_value='SPARSE_WAIT') as poll, \
            patch.object(community.parent, 'strong') as provider:
        if remote_drift:
            with pytest.raises(AssertionError):
                community.serve(config_path, REPOSITORY, output, gate_path, community.parent.sha(gate_path), True)
            transport.assert_not_called()
            poll.assert_not_called()
        else:
            assert community.serve(config_path, REPOSITORY, output, gate_path,
                community.parent.sha(gate_path), True) == 'SPARSE_WAIT'
            assert set(checked_names) == set(gate['source_pins'])
            poll.assert_called_once()
        provider.assert_not_called()


def test_eval_paths_are_rejected(tmp_path):
    directory = tmp_path/'FINAL'
    directory.mkdir()
    path = directory/'data.json'
    path.write_text('{}')
    with pytest.raises(ValueError, match='no_evaluation_input'):
        community.local_file(path)


def test_cadence_and_failed_provider_do_not_spend_delivered_budget(config, tmp_path):
    status, strong, publish = tick(config, tmp_path, state(2))
    assert status == 'SPARSE_WAIT'
    strong.assert_not_called()
    publish.assert_not_called()
    status, strong, publish = tick(config, tmp_path, state(3), provider_error=RuntimeError('test'))
    assert status == 'PROVIDER_FAILED'
    assert strong.call_args.kwargs['reasoning_effort'] == 'low'
    publish.assert_not_called()
    assert community.ledger(tmp_path, state(3))['object_delivered_turns'] == {}
    assert tick(config, tmp_path, state(5))[0] == 'SPARSE_WAIT'
    assert tick(config, tmp_path, state(6), reply(source_record=18))[0] == 'PUBLISHED'


def test_only_exact_rendered_own_Astra_turns_count_across_sleep(config, tmp_path):
    response = reply()
    assert tick(config, tmp_path, state(), response)[0] == 'PUBLISHED'
    assert community.ledger(tmp_path, state(6, sleeps=1))['object_delivered_turns'] == {}
    assert tick(config, tmp_path, state(6))[0] == 'AWAITING_RENDER'
    delivered = exposure(response)
    delivered.update(exposure(response, identifier='direct-console-turn', speaker='Rohin'))
    memory = community.ledger(tmp_path, state(6, delivered, sleeps=2))
    assert memory['object_delivered_turns'] == {'story-ending': 1}
    assert community.ledger(tmp_path, state(9, delivered, sleeps=3))['object_delivered_turns'] == {
        'story-ending': 1}
    assert list(tmp_path.glob('parent_*/DELIVERED.json'))
    with pytest.raises(ValueError, match='exact_rendered_Astra'):
        community.ledger(tmp_path, state(6, exposure(response, speaker='Rohin')))


def test_three_delivered_turns_require_release_then_reject_same_object():
    memory = dict(object_delivered_turns={'story-ending': 2})
    with pytest.raises(ValueError, match='third_turn_releases_object'):
        community.decision(reply(), state(), memory)
    releasing = reply(disposition='set_aside')
    assert community.decision(releasing, state(), memory)['disposition'] == 'set_aside'
    memory['object_delivered_turns']['story-ending'] = 3
    with pytest.raises(ValueError, match='object_delivered_budget_exhausted'):
        community.decision(releasing, state(), memory)
    assert community.decision(reply(object_id='different-project'), state(), memory)


def test_budget_reconstructed_over_three_sleeps_rejects_fourth_delivery(config, tmp_path):
    delivered = {}
    for count in (3, 6, 9):
        response = reply(source_record=count*3, disposition='set_aside' if count == 9 else 'continue')
        identifier = 'turn-'+str(count)
        current = state(count, delivered, sleeps=count//3)
        with patch.object(community, 'snapshot', return_value=current), \
                patch.object(community.parent, 'strong', return_value=provider(response)), \
                patch.object(community.parent, 'publish', return_value=publication(identifier)):
            assert community.tick(REPOSITORY, config, tmp_path) == 'PUBLISHED'
        assert community.ledger(tmp_path, current)['object_delivered_turns'].get('story-ending', 0) == count//3-1
        delivered.update(exposure(response, identifier))
        assert community.ledger(tmp_path, state(count, delivered))['object_delivered_turns']['story-ending'] == count//3
    status, unused_strong, publish = tick(config, tmp_path, state(12, delivered, sleeps=4),
        reply(source_record=36, disposition='set_aside'))
    assert status == 'PROVIDER_FAILED'
    publish.assert_not_called()
    assert community.ledger(tmp_path, state(12, delivered))['object_delivered_turns'] == {'story-ending': 3}


def test_silent_and_wrong_provider_never_publish_or_spend_object_budget(config, tmp_path):
    silent = dict(speak=False, message='', rationale='')
    status, unused_strong, publish = tick(config, tmp_path, state(), silent)
    assert status == 'SILENT'
    publish.assert_not_called()
    assert community.ledger(tmp_path, state())['object_delivered_turns'] == {}
    with patch.object(community, 'snapshot', return_value=state(6)), \
            patch.object(community.parent, 'strong', return_value=(reply(source_record=18), 'Fable', {})), \
            patch.object(community.parent, 'publish') as publish:
        assert community.tick(REPOSITORY, config, tmp_path) == 'PROVIDER_FAILED'
    publish.assert_not_called()


def test_late_reply_is_not_published(config, tmp_path):
    def late_provider(*args, **kwargs):
        config['hard_end_unix'] = 0
        return provider(reply())
    with patch.object(community, 'snapshot', return_value=state()), \
            patch.object(community.parent, 'strong', side_effect=late_provider), \
            patch.object(community.parent, 'publish') as publish:
        assert community.tick(REPOSITORY, config, tmp_path) == 'PROVIDER_FAILED'
    publish.assert_not_called()


def test_source_evidence_and_impersonation_fail_closed():
    memory = dict(object_delivered_turns={})
    with pytest.raises(ValueError, match='actual_child_source_evidence'):
        community.decision(reply(source_record=999), state(), memory)
    for speaker in ('Rohin', 'Fable', 'C2', 'Tool'):
        with pytest.raises(ValueError, match='no_provider_impersonation'):
            community.decision(dict(reply(), message=speaker+': trust me'), state(), memory)
    assert community.decision(dict(speak=False, message='', rationale=''), state(), memory) is None


def test_publication_uncertainty_never_retries_or_spends_budget(config, tmp_path):
    assert tick(config, tmp_path, state(), publish_error=TimeoutError())[0] == 'PUBLICATION_UNKNOWN'
    with patch.object(community, 'snapshot', return_value=state(6)), \
            patch.object(community.parent, 'strong') as strong, patch.object(community.parent, 'publish') as publish:
        with pytest.raises(ValueError, match='Main_reconciliation'):
            community.tick(REPOSITORY, config, tmp_path)
    strong.assert_not_called()
    publish.assert_not_called()


def test_restart_after_dispatch_without_publication_advances_only_cadence(config, tmp_path):
    directory = tmp_path/'parent_000000000003'
    directory.mkdir()
    community.parent.write(directory/'SOURCE.json', state())
    community.parent.write(directory/'DISPATCH_INTENT.json', dict(attempt=True))
    assert community.ledger(tmp_path, state(6)) == dict(object_delivered_turns={},
        last_response_count=3, awaiting_render=False)
    assert tick(config, tmp_path, state(3))[0] == 'SPARSE_WAIT'
    community.parent.write(directory/'PUBLISH_INTENT.json', dict(attempt=True))
    with pytest.raises(ValueError, match='Main_reconciliation'):
        community.ledger(tmp_path, state(6))


def test_process_lock_excludes_duplicate_parent_and_allows_restart(tmp_path):
    with community.parent_lock(tmp_path):
        with pytest.raises(BlockingIOError):
            with community.parent_lock(tmp_path):
                pytest.fail('duplicate parent admitted')
    with community.parent_lock(tmp_path):
        pass


def test_prompt_preserves_English_human_attribution_and_cross_sleep_budget(config):
    snapshot = state()
    snapshot['events'].append(dict(actor='parent', speaker='Rohin', text='Try a new question.',
        record_index=10, record_sha256='f'*64))
    memory = dict(object_delivered_turns={'story-ending': 3})
    instruction, payload = community.prompt(config, snapshot, memory)
    assert 'in English' in instruction and 'not your own' in instruction
    assert 'across sleep' in instruction and 'never child-facing' in instruction
    document = json.loads(payload)
    assert document['visible_training_events'][-1]['speaker'] == 'Rohin'
    assert document['object_delivered_turns'] == memory['object_delivered_turns']


def token_count(messages):
    return sum(len(message['content'].split())+4 for message in messages)


def generate(messages, **kwargs):
    return dict(raw='I will test this observation.', token_ids=[10, 2], terminal=True, truncated=False)


def test_real_journal_commits_rendered_delivery_masking_and_no_evaluation_reads(tmp_path):
    root = tmp_path/'life'
    root.mkdir()
    with StreamJournal(root/'stream', create=True) as journal:
        stream = ContinualStream(TrainHistory(system_prompt='System.', birth_prompt='Birth.'),
            context_limit=4096, segment_tokens=128, segments_per_sleep=20,
            deadline_unix=1000, model_state_sha256='f'*64)
        journal.record('COMMITTED', dict(kind='BIRTH', state=stream.checkpoint()))
        own = publish_parent(root, 'Astra', 'Check the result.')
        human = publish_parent(root, 'Rohin', 'Choose your own next step.')
        before = community.read_train_snapshot(root)
        assert before['response_count'] == 0 and before['delivered'] == {}
        incoming = journal.read_inbox()
        consumed = community.read_train_snapshot(root)
        assert consumed['delivered'] == {}
        stream.step(generate, token_count, journal.record, incoming=incoming, now=lambda: 100)
        snapshot = community.read_train_snapshot(root)
        assert snapshot['response_count'] == 1
        assert snapshot['delivered'][own['id']]['speaker'] == 'Astra'
        assert snapshot['delivered'][human['id']]['speaker'] == 'Rohin'
        assert stream.rows[-1]['target'] == 'I will test this observation.'
        assert stream.rows[-1]['prefix_loss'] is False and stream.rows[-1]['target_loss'] is True
        secret = root/'FINAL'
        secret.mkdir()
        (secret/'readout.json').write_text('MUST NEVER ENTER PROMPT')
        assert 'MUST NEVER' not in json.dumps(community.read_train_snapshot(root))
        def interrupted(kind, document):
            if kind == 'COMMITTED':
                raise RuntimeError('crash before commit')
            return journal.record(kind, document)
        with pytest.raises(RuntimeError, match='crash before commit'):
            stream.step(generate, token_count, interrupted, now=lambda: 100)
        snapshot = community.read_train_snapshot(root)
        assert snapshot['response_count'] == 1
        assert len([event for event in snapshot['events'] if event['actor'] == 'child']) == 1


def test_non_train_request_rejected_without_payload_exposure():
    record = dict(kind='REQUEST', document=dict(split='FINAL'), index=0, sha256='a'*64)
    with patch.object(community.transcript, '_records', return_value=iter([(record, 0, 'b'*64)])):
        with pytest.raises(ValueError, match='TRAIN_request_only'):
            community.read_train_snapshot('/unused')


def test_unmasked_parent_context_rejected():
    record = dict(kind='REQUEST', document=dict(split='TRAIN', render_receipt=dict(
        all_history_tokens_masked=False)), index=0, sha256='a'*64)
    with patch.object(community.transcript, '_records', return_value=iter([(record, 0, 'b'*64)])):
        with pytest.raises(ValueError, match='external_context_never_loss_targets'):
            community.read_train_snapshot('/unused')


def test_non_train_inbox_rejected():
    record = dict(kind='INBOX', document=dict(message=dict(id='example', actor='parent',
        split='FINAL', text='not allowed'), source_id='/unused', source_sha256='b'*64),
        index=0, sha256='a'*64)
    with patch.object(community.transcript, '_records', return_value=iter([(record, 0, 'b'*64)])):
        with pytest.raises(ValueError, match='TRAIN_inbox_text'):
            community.read_train_snapshot('/unused')
