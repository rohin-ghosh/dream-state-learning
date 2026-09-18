from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

from gpu import orch_r116_grid_shared_client as client


shared = client.shared


def checkpoint(folder, label):
    folder.mkdir(parents=True)
    adapter = folder / 'adapter'
    adapter.mkdir()
    shared.write(adapter / 'adapter_config.json', dict(label=label))
    identity = client.native.bridge.AdapterIdentity(str(adapter), shared.digest(label),
        client.grid.policy.game.BASE_SHA, (('adapter_config.json', shared.sha(adapter / 'adapter_config.json')),))
    optimizer = folder / 'optimizer_rng.pt'
    optimizer.write_bytes(b'opaque owner optimizer: ' + label.encode())
    path = folder / 'CHECKPOINT.json'
    shared.write(path, dict(complete=True, adapter=identity.document(),
        optimizer_rng_sha256=shared.sha(optimizer), source_process=['boot', 3, 4]))
    return dict(path=str(path), path_sha256=shared.sha(path), optimizer_path=str(optimizer),
                optimizer_path_sha256=shared.sha(optimizer))


class Decoder(client.SharedDecoder):
    def __init__(self, session):
        identity = client.native.bridge.AdapterIdentity.from_document(session['adapter'])
        binding = client.native.bridge.StageBinding('F4', client.native.bridge.ARMS[0], 0,
            'collection', identity, True, False, session['config_sha256'])
        self.loaded = SimpleNamespace(optimizer=None, binding=binding, engine=SimpleNamespace(),
                                      observed=identity, verify_unchanged=lambda: identity)
        self.prompts = []
        self.before_batch = lambda: None

    def batch(self, messages, cap):
        self.before_batch()
        self.prompts.extend(deepcopy(messages))
        return [dict(raw='child', token_ids=[7, 8, 9], prompt_tokens=2, terminal=True,
                     truncated=False) for prompt in messages]


@pytest.fixture
def setup(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp('gridshared')
    specs = {branch: dict(root=str(tmp_path / branch), train_ids=[branch + '_one', branch + '_two'])
             for branch in shared.BRANCHES}
    reference = checkpoint(tmp_path / 'initial', 'initial')
    root = tmp_path / 'shared'
    shared.initialize(root, specs, reference, excluded_ids=['sealed'],
        prior_metrics={name: 0 for name in shared.METRICS}, initial_history={})
    session = client.prepare(root, 'F4', config_sha256=shared.sha(root / 'CONFIG.json'))
    branch_root = Path(session['branch_root'])
    branch_root.mkdir()
    decoder = Decoder(session)
    life = client.SharedLife(branch_root, decoder, {}, 1, session)
    tasks = [dict(id=identifier, split='TRAIN') for identifier in specs['F4']['train_ids']]
    return SimpleNamespace(root=root, session=session, life=life, decoder=decoder,
                           tasks=tasks, tmp=tmp_path)


def capture(setup, task, purpose, **options):
    messages = [dict(role='system', content='Solve.'),
                dict(role='user', content='Actual environment feedback and parent intervention.')]
    return setup.life.generate(task, purpose, messages, 384, **options)


def complete_cycle(setup):
    first = capture(setup, setup.tasks[0], 'episode')
    capture(setup, setup.tasks[0], 'continuation')
    capture(setup, setup.tasks[0], 'open_turn')
    capture(setup, setup.tasks[1], 'episode')
    capture(setup, setup.tasks[1], 'presleep')
    reflection = capture(setup, setup.tasks[1], 'reflection')
    shared.write(setup.life.root / 'cycles/0001/TRAIN_COMPLETE.json', dict(
        outcomes=[dict(task_id=task['id'], split='TRAIN', original_task_success=False)
                  for task in setup.tasks], reflection=reflection['reference']))
    return first, reflection


def advance(setup, generation=1):
    state = shared.read(setup.root / 'STATE.json')
    state.update(generation=generation, checkpoint=checkpoint(setup.tmp / f'next{generation}', 'next'))
    shared.write(setup.root / 'generation_000000/sleep/COMPLETE.json', dict(state=state))
    shared.write(setup.root / 'STATE.json', state, replace=True)
    return state


def test_prepare_hash_bound_cpu_only_without_optimizer_load(setup):
    assert setup.session['optimizer_owner'] == 'F1'
    assert setup.session['generation'] == 0
    with pytest.raises(ValueError, match='shared_config_hash'):
        client.prepare(setup.root, 'F4', config_sha256='wrong')


def test_extra_A100_lane_not_in_eight_branch_pool(setup):
    with pytest.raises(ValueError, match='grid_branch_only'):
        client.prepare(setup.root, 'R118_A1004_ASTRA', config_sha256=setup.session['config_sha256'])


def test_metadata_bound_before_native_dispatch_and_source_hash_stable(setup):
    def before():
        row = shared.read(setup.life.root / 'calls/N00001.json')
        assert row['status'] == 'STARTED'
        assert row['shared_generation'] == 0
        assert row['shared_checkpoint_sha256'] == setup.session['checkpoint_sha256']
    setup.decoder.before_batch = before
    response = capture(setup, setup.tasks[0], 'episode')
    path = Path(response['reference']['path'])
    row = shared.read(path)
    assert row['response']['messages'] == row['messages'] == setup.decoder.prompts[0]
    assert row['response']['token_ids'] == [7, 8, 9]
    assert shared.sha(path) == response['reference']['sha256']
    assert 'reference' not in row['response']


def test_no_sequential_episode_batching(setup):
    with pytest.raises(ValueError, match='sequential_known_grid_train_phase'):
        setup.life.calls(setup.tasks, 'episode', [[dict(role='user', content='input')]] * 2, 384)
    assert not (setup.life.root / 'LEDGER.jsonl').exists()


def test_complete_failed_episodes_and_all_child_phases_export_exactly_once(setup):
    complete_cycle(setup)
    first = client.export_cycle(setup.session, 1)
    assert client.export_cycle(setup.session, 1) == first
    packet = shared.read(first['packet']['path'])
    assert len(packet['rows']) == 6
    assert packet['child_source_tokens'] == 18
    assert packet['actual_presentations'] == 0
    assert shared.barrier_status(setup.root)['present'] == ['F4']
    assert {shared.read(row['source_call_path'])['purpose'] for row in packet['rows']} == client.TRAIN_PHASES


@pytest.mark.parametrize('split,purpose,attached', [
    ('TRAIN', 'open_readout', True), ('DEV', 'dev', True), ('FINAL', 'final0', True)])
def test_readouts_never_enter_packet_even_same_train_task(setup, split, purpose, attached):
    task = dict(setup.tasks[0], split=split)
    capture(setup, task, purpose, attached_readout=attached)
    complete_cycle(setup)
    packet = shared.read(client.export_cycle(setup.session, 1)['packet']['path'])
    assert len(packet['rows']) == 6
    assert all(Path(row['source_call_path']).parent.name == 'calls' for row in packet['rows'])


def test_old_base_capture_never_forged_into_shared_history(setup):
    response = capture(setup, setup.tasks[0], 'episode')
    path = Path(response['reference']['path'])
    call = shared.read(path)
    call['adapter'] = None
    shared.write(path, call, replace=True)
    with pytest.raises(ValueError, match='actual_shared_child_binding'):
        client.canonical_row(path, setup.session, 1, [task['id'] for task in setup.tasks])


@pytest.mark.parametrize('field,value', [
    ('shared_generation', 1), ('shared_checkpoint_sha256', 'other'), ('attached_readout', True),
    ('status', 'STARTED'), ('purpose', 'open_readout')])
def test_capture_scope_or_state_mismatch_rejected(setup, field, value):
    response = capture(setup, setup.tasks[0], 'episode')
    path = Path(response['reference']['path'])
    call = shared.read(path)
    call[field] = value
    shared.write(path, call, replace=True)
    with pytest.raises(ValueError):
        client.canonical_row(path, setup.session, 1, [task['id'] for task in setup.tasks])


def test_reserved_incomplete_call_cannot_be_silently_dropped(setup):
    complete_cycle(setup)
    client.grid.reserve(setup.life.root, 'NATIVE', dict(cycle=1, task_id=setup.tasks[0]['id'],
        split='TRAIN', purpose='episode', attached_readout=False))
    with pytest.raises(ValueError, match='all_cycle_captures_accounted'):
        client.export_cycle(setup.session, 1)


def test_actual_native_eos_and_prefix_mask_reused(setup):
    response = capture(setup, setup.tasks[0], 'episode')
    row = client.canonical_row(response['reference']['path'], setup.session, 1,
                               [task['id'] for task in setup.tasks])
    tokenizer = SimpleNamespace(eos_token_id=9, all_special_ids=[9],
        apply_chat_template=lambda *args, **kwargs: 'prompt', encode=lambda *args, **kwargs: [3, 4],
        decode=lambda *args, **kwargs: 'child')
    encoded = shared.replay.encode_row(row, tokenizer, 10)
    assert encoded.input_ids == (3, 4, 7, 8, 9)
    assert encoded.labels == (-100, -100, 7, 8, 9)
    with pytest.raises(ValueError, match='no_truncation'):
        shared.replay.encode_row(row, tokenizer, 4)


def test_parent_text_not_substituted_for_child_target(setup):
    response = capture(setup, setup.tasks[0], 'episode')
    row = client.canonical_row(response['reference']['path'], setup.session, 1,
                               [task['id'] for task in setup.tasks])
    row['target'] = 'Parent instruction'
    with pytest.raises(ValueError, match='actual_target_binding'):
        shared.replay.verify_source(row, shared.read(response['reference']['path']))


def test_wait_bounded_without_optimizer_fallback(setup):
    complete_cycle(setup)
    client.export_cycle(setup.session, 1)
    result = client.wait_for_next(setup.session, deadline=0, check=lambda label: None)
    assert result['status'] == 'DEADLINE_WAITING_SHARED_CHECKPOINT'
    assert result['optimizer_steps'] == 0 and result['no_branch_fallback_update']


def test_exact_completed_next_generation_required(setup):
    complete_cycle(setup)
    client.export_cycle(setup.session, 1)
    advance(setup)
    result = client.wait_for_next(setup.session, deadline=client.grid.END, check=lambda label: None)
    assert result['generation'] == 1
    with pytest.raises(ValueError, match='shared_generation_changed'):
        capture(setup, setup.tasks[0], 'episode')


def test_skip_generation_rejected(setup):
    complete_cycle(setup)
    client.export_cycle(setup.session, 1)
    advance(setup, generation=2)
    with pytest.raises(ValueError, match='no_skipped_shared_generation'):
        client.wait_for_next(setup.session, deadline=client.grid.END, check=lambda label: None)


def test_load_only_collection_not_training_or_optimizer(setup, monkeypatch):
    seen = []
    def load(binding, **kwargs):
        seen.append(binding)
        return setup.decoder.loaded
    monkeypatch.setattr(client.native, 'load_stage', load)
    decoder = client.load_shared(setup.session, model_dir='/model', gpu_uuid='GPU-test', check=lambda label: None)
    assert seen[0].phase == 'collection'
    assert decoder.loaded.optimizer is None


def test_readout_load_has_no_private_or_carry_context(setup, monkeypatch):
    def load(binding, **kwargs):
        assert binding.phase == 'sealed_readout' and binding.fresh_process
        assert kwargs['context'].private_guidance == ()
        assert kwargs['context'].transient_context == ()
        return setup.decoder.loaded
    monkeypatch.setattr(client.native, 'load_stage', load)
    client.load_shared(setup.session, model_dir='/model', gpu_uuid='GPU-test',
                       check=lambda label: None, readout=True)


def test_plain_base_engine_cannot_claim_shared_capture(setup):
    with pytest.raises(ValueError, match='actually_loaded_shared_adapter_required'):
        client.SharedLife(setup.life.root, SimpleNamespace(), {}, 1, setup.session)


def test_resident_reload_keeps_nonowner_optimizer_absent(setup, monkeypatch):
    from gpu import orch_r111_route_shared as route
    complete_cycle(setup)
    client.export_cycle(setup.session, 1)
    advance(setup)
    next_session = client.wait_for_next(setup.session, deadline=client.grid.END, check=lambda label: None)
    seen = []
    def reload(engine, reference):
        seen.append(engine)
        return shared.read(reference['path'])
    monkeypatch.setattr(route, 'reload_adapter', reload)
    monkeypatch.setattr(client.native, 'observe_adapter', lambda engine, identity: identity)
    result = client.reload_shared(setup.decoder, setup.session, next_session)
    assert seen == [setup.decoder.loaded.engine]
    assert result['generation'] == 1 and result['local_optimizer_steps'] == 0
    assert setup.decoder.loaded.optimizer is None
    assert setup.decoder.loaded.binding.adapter.document() == next_session['adapter']


def test_missing_published_sleep_blocks_even_with_advanced_state(setup):
    complete_cycle(setup)
    client.export_cycle(setup.session, 1)
    advance(setup)
    complete = setup.root / 'generation_000000/sleep/COMPLETE.json'
    document = shared.read(complete)
    document['state']['generation'] = 99
    shared.write(complete, document, replace=True)
    with pytest.raises(ValueError, match='completed_shared_sleep_state_binding'):
        client.wait_for_next(setup.session, deadline=client.grid.END, check=lambda label: None)
