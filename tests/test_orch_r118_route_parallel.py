from copy import deepcopy
import inspect
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from gpu import orch_r111_route_pair_shared as previous
from gpu import orch_r118_route_parallel_boundary as boundary
from gpu import orch_r118_route_parallel_client as client
from gpu import orch_r118_route_parallel_lifecycle as lifecycle
from gpu import orch_r118_route_parallel_run as run
from gpu import orch_r118_route_parallel_cutoff as cutoff
from test_orch_r111_route_pair import native_shape_engine
from test_orch_r111_route_shared import fixture as serial_fixture, capture


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


@pytest.fixture
def completed(tmp_path):
    root, common = tmp_path / 'life', tmp_path / 'common'
    payload = common / 'checkpoint1'
    adapter = payload / 'adapter'
    adapter.mkdir(parents=True)
    (adapter / 'weights.bin').write_bytes(b'CPU fixture preserved LoRA')
    optimizer = payload / 'optimizer_rng.pt'
    optimizer.write_bytes(b'CPU fixture preserved original optimizer RNG')
    identity = dict(path=str(adapter), state_sha256='a' * 64, base_sha256='b' * 64,
                    files=[['weights.bin', boundary.sha(adapter / 'weights.bin')]])
    checkpoint = payload / 'CHECKPOINT.json'
    document = dict(complete=True, adapter=identity, source_process=['boot', 91, 4],
                    optimizer_rng_sha256=boundary.sha(optimizer), sleeps=7, cycle=7)
    put(checkpoint, document)
    checkpoint_ref = dict(path=str(checkpoint), path_sha256=boundary.sha(checkpoint),
                          optimizer_path=str(optimizer), optimizer_path_sha256=boundary.sha(optimizer))
    state = dict(generation=1, checkpoint=checkpoint_ref, config_sha256='c' * 64,
                 optimizer_steps=3009, child_token_exposures=None, anchor_token_exposures=54000,
                 shared_optimizer_steps=1884, shared_child_token_exposures=300000, shared_anchor_token_exposures=33000)
    put(common / 'STATE.json', state)
    put(common / 'generation_000000/sleep/COMPLETE.json', dict(state=state, same_optimizer=True))
    cycle = root / 'cycle_0007'
    put(cycle / 'START.json', dict(cycle=7))
    put(cycle / 'checkpoint/CHECKPOINT.json', dict(document, shared_checkpoint=checkpoint_ref))
    wrapper_sha = boundary.sha(cycle / 'checkpoint/CHECKPOINT.json')
    put(cycle / 'SLEEP.json', dict(sleeps=7, checkpoint_sha256=wrapper_sha))
    put(cycle / 'SHARED_SLEEP.json', dict(status='COMPLETE', state=state))
    put(cycle / 'ROWS.json', [dict(actual_fixture=True)])
    put(root / 'OWN_CARRY.json', dict(reflection='unchanged actual carry', checkpoint_sha256=wrapper_sha))
    put(cycle / 'COMPLETE.json', dict(cycle=7, sleeps=7))
    put(root / 'readout_0007/COMPLETE.json', dict(fresh_process=True, parent_calls=0))
    put(root / 'readout_0007/LOADED.json', dict(parent_free=True, context_free=True,
        process=['boot', 92, 5], checkpoint_sha256=wrapper_sha, adapter=identity))
    put(root / 'open_readouts/readout_0007/COMPLETE.json', dict(parent_calls=0))
    put(root / 'PLAN.json', dict(shared_learner=dict(root=str(common))))
    rows = [dict(kind='NATIVE', number=1, cycle=7), dict(kind='PARENT', number=1, cycle=7),
            dict(kind='NATIVE', number=2, sleep=7)]
    (root / 'RESERVATIONS.jsonl').write_text(''.join(json.dumps(row) + '\n' for row in rows))
    put(cycle / 'CALL_000001.json', dict(finished_unix=1, status='FAILED'))
    put(root / 'readout_0007/CALL_000002.json', dict(finished_unix=2, status='COMPLETE'))
    put(root / 'parent_queue/000001_F1_C0007.observed.json', dict(observed_unix=3, status='MISSING'))
    return SimpleNamespace(root=root, common=common, cycle=cycle, state=state, optimizer=optimizer,
                           checkpoint=checkpoint, adapter=adapter)


def test_shared_wrapper_preserves_actual_common_optimizer_and_failed_charges(completed):
    result = boundary.settled(completed.root, completed.common, completed.cycle)
    assert result['checkpoint']['optimizer_path'] == str(completed.optimizer)
    assert not (completed.cycle / 'checkpoint/optimizer_rng.pt').exists()
    assert result['charged'] == {'NATIVE': 2, 'PARENT': 1}
    assert result['next_cycle'] == 8 and result['state']['child_token_exposures'] is None


@pytest.mark.parametrize('target', ['common_complete', 'dev_complete', 'open_complete', 'native', 'parent'])
def test_missing_commit_DEV_OPEN_or_settled_calls_blocks(completed, target):
    paths = dict(common_complete=completed.common / 'generation_000000/sleep/COMPLETE.json',
        dev_complete=completed.root / 'readout_0007/COMPLETE.json',
        open_complete=completed.root / 'open_readouts/readout_0007/COMPLETE.json',
        native=completed.cycle / 'CALL_000001.json',
        parent=completed.root / 'parent_queue/000001_F1_C0007.observed.json')
    paths[target].unlink()
    if target == 'dev_complete':
        put(completed.root / 'readout_0007/PROCESS_RESULT.json', dict(status='FAILED'))
    with pytest.raises((ValueError, FileNotFoundError)):
        boundary.settled(completed.root, completed.common, completed.cycle)


@pytest.mark.parametrize('target', ['optimizer', 'adapter', 'next_sleep', 'state', 'loaded'])
def test_mutated_or_uncommitted_state_cannot_release(completed, target):
    if target == 'optimizer':
        completed.optimizer.write_bytes(b'drift')
    elif target == 'adapter':
        (completed.adapter / 'weights.bin').write_bytes(b'drift')
    elif target == 'next_sleep':
        put(completed.common / 'generation_000001/sleep/START.json', dict(actual_training=True))
    elif target == 'state':
        put(completed.common / 'STATE.json', dict(completed.state, generation=0))
    else:
        path = completed.root / 'readout_0007/LOADED.json'
        put(path, dict(boundary.read(path), checkpoint_sha256='wrong'))
    with pytest.raises(ValueError):
        boundary.settled(completed.root, completed.common, completed.cycle)


def test_uncharged_START_preserved_and_charged_next_task_refused(completed):
    start = completed.root / 'cycle_0008/START.json'
    put(start, dict(cycle=8))
    snapshot = boundary.settled(completed.root, completed.common, completed.cycle)
    assert snapshot['empty_successor_start'] == boundary.ref(start)
    saved = completed.root / 'controller/BOUNDARY.json'
    put(saved, snapshot)
    release = completed.root / 'controller/RELEASED.json'
    put(release, dict(boundary=boundary.ref(saved)))
    resumed = boundary.successor_start(completed.root, start.parent, boundary.ref(release))
    assert resumed.name == 'R118_PARALLEL_RESUMED_START.json'
    assert start.exists()
    with (completed.root / 'RESERVATIONS.jsonl').open('a') as stream:
        stream.write(json.dumps(dict(kind='NATIVE', number=3, cycle=8)) + '\n')
    with pytest.raises(ValueError, match='next_cycle_charged'):
        boundary.settled(completed.root, completed.common, completed.cycle)


def test_candidate_catches_open_completion_before_cycle_COMPLETE(completed):
    (completed.cycle / 'COMPLETE.json').unlink()
    assert boundary.candidate(completed.root) == completed.cycle
    (completed.root / 'open_readouts/readout_0007/COMPLETE.json').unlink()
    assert boundary.candidate(completed.root) is None


def test_absent_Main_all8_gate_never_opens_pidfds(tmp_path, monkeypatch):
    request, auth = tmp_path / 'REQUEST.json', tmp_path / 'AUTH.json'
    put(request, dict(schema=boundary.SCHEMA))
    put(auth, dict(authorized=True))
    monkeypatch.setattr(os, 'pidfd_open', lambda *args: pytest.fail('no process access without authorization'))
    with pytest.raises(ValueError, match='Main_all8'):
        boundary.execute(request, auth)


def test_wrong_process_module_does_not_signal_foreign_sentinel(tmp_path):
    process = subprocess.Popen([sys.executable, '-c', 'import time;time.sleep(30)'])
    try:
        with pytest.raises(ValueError, match='exact_route_module'):
            boundary.actor(process.pid, tmp_path, 'run', 'GPU-fixture')
        assert process.poll() is None
    finally:
        process.terminate()
        process.wait(timeout=3)


def test_actual_cpu_pidfd_controller_releases_only_owned_pair(completed, monkeypatch):
    root, directory = completed.root, completed.root / 'controller'
    directory.mkdir()
    parent = subprocess.Popen([sys.executable, '-c', 'import time;time.sleep(30)'])
    child = subprocess.Popen([sys.executable, '-c', 'import time;time.sleep(30)'])
    foreign = subprocess.Popen([sys.executable, '-c', 'import time;time.sleep(30)'])
    try:
        ready = directory / 'READY.json'
        put(ready, dict(status='CPU_READY_NOT_ACTIVATED', source_files={boundary.__file__: boundary.sha(boundary.__file__)}))
        mapping = dict(physical=0, uuid='GPU-fixture', kernel_minor=0)
        monkeypatch.setattr(boundary.prior, 'ROOT_TEMPLATE', str(root))
        monkeypatch.setattr(boundary.prior, 'UUIDS', {0: 'GPU-fixture'})
        monkeypatch.setattr(boundary.prior, 'gpu_mapping', lambda *args: mapping)
        request = directory / 'REQUEST.json'
        put(request, dict(schema=boundary.SCHEMA, purpose=boundary.PURPOSE, root=str(root),
            directory=str(directory), common=str(completed.common), plan=boundary.ref(root / 'PLAN.json'),
            readiness=boundary.ref(ready), actor=boundary.prior.identity(child.pid),
            supervisor=boundary.prior.identity(parent.pid), mapping=mapping, bounds={}, expires_unix=time.time()+10))
        authorization = directory / 'AUTH.json'
        put(authorization, dict(request_sha256=boundary.sha(request), purpose=boundary.PURPOSE,
            authorized=True, all_eight_ready=True, common_handoff_coordinated=True,
            no_current_serial_interruption=True))
        before = (root / 'RESERVATIONS.jsonl').read_bytes()
        result = boundary.execute(request, authorization)
        assert result['status'] == 'RELEASED' and foreign.poll() is None
        assert (root / 'RESERVATIONS.jsonl').read_bytes() == before
    finally:
        for process in (parent, child, foreign):
            if process.poll() is None:
                process.send_signal(signal.SIGCONT)
                process.terminate()
            process.wait(timeout=3)


@pytest.fixture
def parallel_fixture(serial_fixture):
    fixture = serial_fixture
    common = fixture.shared_root
    state = client.read(common / 'STATE.json')
    state['generation'] = 1
    put(common / 'STATE.json', state)
    put(common / 'generation_000000/sleep/COMPLETE.json', dict(state=state, same_optimizer=True))
    adoption = client.read(fixture.plans['F1']['shared_learner']['adoption_path'])
    for branch, plan in fixture.plans.items():
        plan['bounds']['lease_end_unix'] = 9999999999
        adoption['branch_bounds'][branch] = deepcopy(plan['bounds'])
        plan['uuid'] = boundary.prior.UUIDS[plan['physical']]
        plan['parent_wait_seconds'] = 120
        plan['parallel_control'] = dict(backend_source=boundary.ref(Path(client.backend.__file__).resolve()),
            train_end_unix=boundary.TRAIN_END, activation_wait_end_unix=boundary.TRAIN_END,
            activation_directory=str(fixture.root / 'Main_activation_refs'), anchor_root='/anchors')
        root = fixture.root / branch
        put(root / 'PLAN.json', plan)
        put(root / lifecycle.PLAN, plan)
        put(root / 'OWN_CARRY.json', dict(reflection='preserved'))
        (root / 'RESERVATIONS.jsonl').write_text('')
    put(Path(fixture.plans['F1']['shared_learner']['adoption_path']), adoption)
    for plan in fixture.plans.values():
        plan['shared_learner']['adoption_sha256'] = boundary.sha(plan['shared_learner']['adoption_path'])
    return fixture


@pytest.mark.parametrize('branch', ['F1', 'A1'])
def test_actual_route_rows_submit_and_exact_Herschel_return(parallel_fixture, monkeypatch, branch):
    fixture = parallel_fixture
    session = client.Session(fixture.root / branch, fixture.plans[branch])
    root, output = fixture.root / branch, fixture.root / branch / 'cycle_0008'
    rows = []
    for ordinal, task in enumerate(fixture.specs[branch]['train_ids']):
        row = capture(root, task, branch, fixture.initial, ordinal=ordinal)
        path = Path(row['source_call_path'])
        call = client.read(path)
        call.update(shared_generation=1, shared_learner=session.capture_binding())
        put(path, call)
        rows.append(run.causal.replay_row(call, path, client.sha(path)))
        assert call['response']['input_truncated'] is False
    put(output / 'ROWS.json', rows)
    supervisor = dict(guard_identity=client.backend.process_identity(), native_identity=client.backend.process_identity(),
                      final_identity_bindings=[dict(identity=client.backend.process_identity(),
                          evidence=boundary.ref(root / 'PLAN.json'))], guard_binding=boundary.ref(root / 'PLAN.json'),
                      owner_verified_safe_for_parallel=True)
    put(root / 'R118_PARALLEL_SUPERVISION_BINDING.json', supervisor)
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', fixture.plans[branch]['uuid'])
    certificate_seen = []
    def wait(certificate, check):
        certificate_seen.append(certificate)
        return dict(path='/prospective/ACTIVATION.json', sha256='a' * 64)
    monkeypatch.setattr(session, 'wait_activation', wait)
    optimizer = object() if branch == 'F1' else None
    serializer = lambda *args: None
    actual = []
    def launch(**kwargs):
        actual.append(kwargs)
        state = client.read(fixture.shared_root / 'STATE.json')
        state['generation'] = 2
        state['shared_optimizer_steps'] = 236
        put(fixture.shared_root / 'STATE.json', state)
        put(fixture.shared_root / 'generation_000001/sleep/COMPLETE.json', dict(state=state))
        put(fixture.shared_root / 'generation_000001/sleep/ALL8_RELOAD.json', dict(state=state))
        return dict(status='COMPLETE_ALL8_INPLACE', state=state, metrics=dict(optimizer_steps=236))
    result = session.sleep(object(), optimizer, ['anchors'], rows, fixture.specs[branch]['train_ids'],
                           output, serializer, lambda stage: None, launch_call=launch)
    assert actual[0]['optimizer'] is optimizer
    assert actual[0]['save_checkpoint'] is (serializer if branch == 'F1' else None)
    assert actual[0]['anchor_module'].__name__ == 'gpu.orch_r107_base_anchors_inventory'
    assert 'group' not in actual[0]
    assert result['local_optimizer_steps'] == (236 if branch == 'F1' else 0)
    assert result['serial_adamw_equivalent'] is False and result['state']['child_token_exposures'] is None
    cert = boundary.bound(certificate_seen[0])
    assert cert['submission_sha256'] == client.sha(fixture.shared_root / f'generation_000001/{branch}.json')
    assert cert['bounds']['train_end_unix'] == boundary.TRAIN_END


def test_wait_for_missing_Main_activation_is_bounded_without_native_calls(parallel_fixture):
    fixture = parallel_fixture
    session = client.Session(fixture.root / 'F1', fixture.plans['F1'])
    clock = iter([boundary.TRAIN_END - 1, boundary.TRAIN_END - .5, boundary.TRAIN_END])
    before = (fixture.root / 'F1/RESERVATIONS.jsonl').read_bytes()
    with pytest.raises(TimeoutError, match='deadline'):
        session.wait_activation({}, lambda stage: None, clock=lambda: next(clock), pause=lambda seconds: None)
    assert (fixture.root / 'F1/RESERVATIONS.jsonl').read_bytes() == before


def test_wrong_A1_optimizer_rejected_before_submission(parallel_fixture):
    fixture = parallel_fixture
    session = client.Session(fixture.root / 'A1', fixture.plans['A1'])
    with pytest.raises(ValueError, match='F1_existing_optimizer'):
        session.sleep(None, object(), [], [], [], fixture.root, None, lambda stage: None)
    assert not (fixture.shared_root / 'generation_000001/A1.json').exists()


def test_original_prompt_decoder_response_preserved_no_initial_readout_replay():
    assert run.prompts() == previous.prompts()
    assert run.OPEN_PROMPT == previous.OPEN_PROMPT and run.HELD_PROMPT == previous.HELD_PROMPT
    messages = [dict(role='user', content='Visible fixture')]
    assert run.generate(native_shape_engine(), messages, cap=8) == previous.generate(native_shape_engine(), messages, cap=8)
    assert "run_readout(root, 0" not in inspect.getsource(run.run)
    assert 'shared_session.bootstrap(engine, optimizer)' in inspect.getsource(run.run)
    assert "root/'R118_PARALLEL_PLAN.json'" in inspect.getsource(run.reserve)
    assert cutoff.MODULE == boundary.SUCCESSOR
    assert 'prepare' not in inspect.getsource(run.main).split("choices=(", 1)[1].split(')', 1)[0]


def test_live_old_FINAL_waiter_prevents_successor_launch(tmp_path):
    receipt = tmp_path / 'RETIRED.json'
    identity = boundary.prior.identity(os.getpid())
    put(receipt, dict(status='RETIRED_FOR_COORDINATED_SUCCESSOR', identities={key: identity for key in
        ('cutoff_monitor', 'cutoff_fuse', 'F1_FINAL', 'A1_FINAL')}))
    with pytest.raises(ValueError, match='old_CPU_waiters'):
        lifecycle.verify_retirements(dict(old_CPU_lifecycle_retirement=boundary.ref(receipt)))


def test_stage_does_not_mutate_without_Main_authorization(tmp_path):
    auth, ready = tmp_path / 'auth.json', tmp_path / 'ready.json'
    put(auth, dict(authorized=False)); put(ready, {})
    before = set(tmp_path.iterdir())
    with pytest.raises(ValueError, match='Main_all8'):
        lifecycle.stage(tmp_path, {}, boundary.ref(ready), boundary.ref(auth), {})
    assert set(tmp_path.iterdir()) == before


def test_authorized_stage_preserves_original_PLAN_and_bounds(completed, monkeypatch):
    root, folder = completed.root, completed.root / 'candidate'
    original = dict(root=str(root), physical=0, uuid=boundary.prior.UUIDS[0], parent_wait_seconds=120,
        shared_learner=dict(root=str(completed.common), branch='F1'),
        bounds=dict(native_calls=32768, parent_calls=16384, cycles=512,
                    hard_end_unix=1789596240, lease_end_unix=1789617840))
    put(root / 'PLAN.json', original)
    snapshot = boundary.settled(root, completed.common, completed.cycle)
    put(folder / 'BOUNDARY.json', snapshot)
    put(folder / 'RELEASED.json', dict(boundary=boundary.ref(folder / 'BOUNDARY.json')))
    monkeypatch.setattr(boundary, 'released', lambda *args: snapshot)
    source = str(Path(client.__file__).resolve())
    ready = dict(branch='F1', status='CPU_READY_NOT_ACTIVATED', source_root=str(Path(source).parents[1]),
                 source_files={source: boundary.sha(source)}, backend_source=boundary.ref(Path(client.backend.__file__).resolve()))
    put(folder / 'READY.json', ready)
    put(folder / 'AUTH.json', dict(authorized=True, all_eight_released=True, common_handoff_coordinated=True,
        readiness_sha256=boundary.sha(folder / 'READY.json'), release_sha256=boundary.sha(folder / 'RELEASED.json'),
        lifecycle_rebinding_authorized=True, checkpoint_sha256=snapshot['checkpoint']['path_sha256']))
    before = (root / 'PLAN.json').read_bytes()
    result = lifecycle.stage(root, boundary.ref(folder / 'RELEASED.json'), boundary.ref(folder / 'READY.json'),
        boundary.ref(folder / 'AUTH.json'), dict(activation_wait_end_unix=boundary.TRAIN_END,
        train_end_unix=boundary.TRAIN_END, anchor_root='/localhome/local-rohing/orch_r107_base_anchors_20260915_attempt1',
        backend_source=ready['backend_source']))
    assert (root / 'PLAN.json').read_bytes() == before
    candidate = boundary.bound(result)
    assert candidate['bounds'] == original['bounds'] and candidate['parallel_stage']['prior_metrics']['optimizer_steps'] == 3009
    assert not (folder / 'RENDEZVOUS').exists()
    with pytest.raises(FileExistsError):
        lifecycle.stage(root, boundary.ref(folder / 'RELEASED.json'), boundary.ref(folder / 'READY.json'),
            boundary.ref(folder / 'AUTH.json'), candidate['parallel_control'])


def test_cutoff_parallel_identity_namespace_and_original_deadlines():
    assert cutoff.CUTOFF == boundary.TRAIN_END
    assert cutoff.DRAIN == 1789490700 and cutoff.FINAL == 1789491600
    source = inspect.getsource(cutoff.prepare)
    assert 'R118_PARALLEL_ACTOR_READY.json' in source
    assert 'R118_PARALLEL_PLAN.json' in source
    assert 'Main_actual_all8_successor_lifecycle_bindings' in source
    assert 'real_parallel_route_writer' in source
    peers = {branch: dict(bounds=dict(native_calls=100, parent_calls=50, cycles=43)) for branch in cutoff.BRANCHES}
    control = dict(peers=peers, drain_unix=cutoff.DRAIN, freeze_unix=cutoff.CUTOFF-60)
    observations = {branch: dict(counts=dict(native=2, parent=1), native=dict(pid=1),
                                terminal=None, completed_cycle=4) for branch in cutoff.BRANCHES}
    snapshot = dict(state=dict(generation=2), present=list(cutoff.BRANCHES), sleep_started=True)
    assert cutoff.decision(control, snapshot, observations, cutoff.DRAIN-10, {})['action'] == 'MONITOR'
    assert cutoff.decision(control, snapshot, observations, cutoff.CUTOFF-60, {})['reason'] == 'COMMON_TRAIN_DEADLINE'


def test_rebind_final_uses_actual_existing_consumer_no_selector_write(tmp_path, monkeypatch):
    from gpu import orch_r111_route_final as final
    root, runtime = tmp_path / 'original', tmp_path / 'runtime'
    executable = runtime / 'gpu/orch_r111_route_pair_shared.py'
    executable.parent.mkdir(parents=True)
    executable.write_text('preserved_decoder = True\n')
    plan = dict(root=str(root), physical=0, uuid=final.OWNED['F1'][1],
        final_sha256='hash_only_not_read', schema='R115V4_F1_MATCHED_FRESH_BASE_ROUTE',
        source_files={str(executable): boundary.sha(executable)},
        decoder=dict(do_sample=False, num_beams=1, readout_max_new_tokens=2048),
        bounds=dict(native_calls=32768, parent_calls=16384, cycles=512,
                    lease_end_unix=final.END+21601, hard_end_unix=final.END+1),
        shared_learner=dict(branch='F1'), parallel_stage=dict(authorization={}), parallel_source=str(runtime))
    put(root / lifecycle.PLAN, plan)
    monkeypatch.setattr(lifecycle, 'verify_plan', lambda *args, **kwargs: plan)
    monkeypatch.setattr(lifecycle, 'verify_retirements', lambda *args: None)
    auth = root / 'AUTH.json'
    put(auth, {})
    plan['parallel_stage']['authorization'] = boundary.ref(auth)
    common = tmp_path / 'common'
    put(common / 'CONFIG.json', dict(owner='F1'))
    selector = tmp_path / 'selector.py'
    selector.write_text('canonical_only = True\n')
    control = tmp_path / 'cutoff/CONTROL.json'
    put(control, dict(routes={'F1': dict(root=str(root), plan=boundary.ref(root/lifecycle.PLAN),
         source_root=str(runtime))}, common=str(common), immutable={'CONFIG.json': boundary.ref(common/'CONFIG.json')}))
    cpu = tmp_path / 'CPU.json'
    put(cpu, dict(exitcode=0, CUDA_VISIBLE_DEVICES='', model_calls=0, provider_calls=0, real_FINAL_reads=0,
                 source_sha256=boundary.sha(final.__file__), selector_sha256=boundary.sha(selector)))
    result = lifecycle.rebind_final('F1', root, tmp_path/'new_eval', boundary.ref(control),
                                   boundary.ref(selector), boundary.ref(cpu))
    config = boundary.bound(result)
    assert config['native_calls'] == 48 and config['start_unix'] == 1789491600
    assert config['predecessor_plan'] == boundary.ref(root/lifecycle.PLAN)
    assert not (common/'FINAL_SELECTION.json').exists()
    assert not (root/'SEALED_FINAL.json').exists()


def test_actual_torch_CPU_optimizer_restore_preserves_object_and_rng(tmp_path):
    torch = pytest.importorskip('torch')
    parameter = torch.nn.Parameter(torch.ones(2))
    optimizer = torch.optim.AdamW([parameter], lr=.01)
    parameter.grad = torch.ones_like(parameter)
    optimizer.step()
    before_id = id(optimizer)
    saved_rng = torch.get_rng_state().clone()
    path = tmp_path / 'optimizer_rng.pt'
    torch.save(dict(optimizer=optimizer.state_dict(), cpu_rng=saved_rng, cuda_rng=[]), path)
    checkpoint = tmp_path / 'CHECKPOINT.json'
    put(checkpoint, {})
    reference = dict(path=str(checkpoint), path_sha256=boundary.sha(checkpoint),
                     optimizer_path=str(path), optimizer_path_sha256=boundary.sha(path))
    torch.manual_seed(199)
    adapter = SimpleNamespace(torch=SimpleNamespace(load=torch.load, set_rng_state=torch.set_rng_state,
                              cuda=SimpleNamespace(set_rng_state_all=Mock())))
    client.restore_optimizer(adapter, optimizer, reference, owner='F1')
    assert id(optimizer) == before_id and optimizer.state[parameter]['step'].item() == 1
    assert torch.equal(torch.get_rng_state(), saved_rng)
    adapter.torch.cuda.set_rng_state_all.assert_called_once_with([])


def test_fresh_exec_AdamW_exact_momenta_steps_and_next_update(tmp_path):
    torch = pytest.importorskip('torch')
    predecessor_parameter = torch.nn.Parameter(torch.tensor([.5, -2.]))
    predecessor = torch.optim.AdamW([predecessor_parameter], lr=.007, betas=(.8, .97),
                                   weight_decay=.012, foreach=False)
    for gradient in ([.2, -.7], [.5, .8], [-.1, .3]):
        predecessor_parameter.grad = torch.tensor(gradient)
        predecessor.step()
    state = deepcopy(predecessor.state_dict())
    path = tmp_path/'optimizer_rng.pt'
    torch.save(dict(optimizer=state, cpu_rng=torch.get_rng_state(), cuda_rng=[]), path)
    checkpoint = tmp_path/'CHECKPOINT.json'
    put(checkpoint, {})
    fresh_parameter = torch.nn.Parameter(predecessor_parameter.detach().clone())
    successor = torch.optim.AdamW([fresh_parameter], lr=.1, foreach=False)
    engine = SimpleNamespace(torch=SimpleNamespace(load=torch.load, set_rng_state=torch.set_rng_state,
        cuda=SimpleNamespace(set_rng_state_all=Mock())))
    reference = dict(path=str(checkpoint), path_sha256=boundary.sha(checkpoint),
                     optimizer_path=str(path), optimizer_path_sha256=boundary.sha(path))
    client.restore_optimizer(engine, successor, reference, owner='F1')
    assert successor is not predecessor
    assert client.backend.state_hash(successor.state_dict()) == client.backend.state_hash(state)
    for parameter, optimizer in ((predecessor_parameter, predecessor), (fresh_parameter, successor)):
        parameter.grad = torch.tensor([.9, -.2])
        optimizer.step()
    assert torch.equal(predecessor_parameter, fresh_parameter)
    assert client.backend.state_hash(successor.state_dict()) == client.backend.state_hash(predecessor.state_dict())


def test_parallel_cutoff_observes_actual_backend_updates(tmp_path):
    folder = tmp_path / 'generation_000001/sleep'
    put(folder / 'START.json', dict(started_unix=100, planned_optimizer_steps=245))
    put(folder / 'ENCODING.json', dict(decisions=[
        dict(kind='NEW', status='ENCODED'), dict(kind='REHEARSAL', status='ENCODED'),
        dict(kind='NEW', status='REJECTED_ENCODING')]))
    def update(step):
        put(folder / 'updates' / f'{step:06d}.json', dict(observed_unix=100+step,
            metrics=dict(optimizer_steps=step, child_token_exposures=200*step, anchor_token_exposures=25*step)))
    snapshot = dict(state=dict(generation=1), sleep_started=True)
    memory = {}
    update(10)
    first = cutoff.serial_workload(tmp_path, snapshot, 110, memory)
    update(30)
    latest = cutoff.serial_workload(tmp_path, snapshot, 150, memory)
    assert first['completed_updates'] == 10 and latest['completed_updates'] == 30
    assert latest['seconds_per_update'] == 2 and latest['remaining_scheduled_updates'] == 215
    assert latest['encoded_new_rows'] == latest['encoded_history_rows'] == latest['rejected_rows'] == 1
    assert latest['serial_adamw_equivalent'] is False
    assert latest['latest_update'] == boundary.ref(folder / 'updates/000030.json')
    assert not (folder / 'UPDATES.jsonl').exists()


def test_cutoff_serial_progress_still_measures_actual_steps(tmp_path):
    folder = tmp_path / 'generation_000000/sleep'
    put(folder / 'START.json', dict(started_unix=100, row_count=114, rehearsal_rows=60))
    put(folder / 'ENCODING.json', dict(new=114, old=60, rejected=[]))
    (folder / 'UPDATES.jsonl').write_text(json.dumps(dict(step=1400, child_token_exposures=240000,
        anchor_token_exposures=25000))+'\n'+ '{"partial":')
    result = cutoff.serial_workload(tmp_path, dict(state=dict(generation=0), sleep_started=True), 200, {})
    assert result['scheduled_updates'] == 1884 and result['completed_updates'] == 1400
    assert result['serial_adamw_equivalent'] is True


def test_guard_stops_only_identity_pinned_children(monkeypatch):
    actor = dict(pid=1, uid=2, start_ticks='3', boot_id='boot', cwd='/old')
    readout = dict(pid=4, uid=2, start_ticks='5', boot_id='boot')
    signals, waits = [], []
    exited = set()
    def send(descriptor, identity, signum):
        assert 'cwd' not in identity
        signals.append((descriptor, identity['pid'], signum))
        if signum == signal.SIGTERM:
            exited.add(descriptor)
    monkeypatch.setattr(cutoff, 'signal_bound', send)
    monkeypatch.setattr(cutoff, 'wait_stopped', lambda *args: waits.append(args))
    monkeypatch.setattr(cutoff, 'exited', lambda descriptor, timeout=0: descriptor in exited)
    monkeypatch.setattr(lifecycle, 'pin_readout_children', lambda *args: None)
    result = lifecycle.stop_guard_children(10, actor, {}, {(4, '5', 'boot'): (20, readout)})
    assert result['all_exited'] is True and waits
    assert signals == [(10, 1, signal.SIGSTOP), (20, 4, signal.SIGTERM), (10, 1, signal.SIGTERM)]


@pytest.mark.parametrize('module', [boundary, lifecycle, run, cutoff])
def test_runnable_cli_help_has_no_activation(module):
    result = subprocess.run([sys.executable, '-B', '-m', module.__name__, '--help'],
                            capture_output=True, text=True, timeout=15)
    assert result.returncode == 0 and 'usage:' in result.stdout


def test_lifecycle_supervision_cli_dispatch(tmp_path, monkeypatch):
    root = tmp_path/'root'
    bindings, guard = tmp_path/'FINAL.json', tmp_path/'GUARD.json'
    put(bindings, [dict(identity='fixture')])
    put(guard, {})
    observed = []
    monkeypatch.setattr(lifecycle, 'bind_supervision', lambda *args: observed.append(args) or {'prepared': True})
    monkeypatch.setattr(sys, 'argv', ['controller', 'bind-supervision', '--root', str(root),
        '--final-bindings', str(bindings), '--guard-binding', str(guard)])
    lifecycle.main()
    assert observed == [(root, boundary.read(bindings), boundary.ref(guard))]


@pytest.mark.parametrize('branch', ['F1', 'A1'])
@pytest.mark.parametrize('sidecar', [False, True])
def test_route_uses_real_fresh_bootstrap_with_exact_rng(tmp_path, monkeypatch, branch, sidecar):
    torch = pytest.importorskip('torch')
    import test_orch_r118_parallel_consolidation as fixture_module
    request = fixture_module.fresh_fixture(tmp_path, parallel_rng=sidecar)
    published = client.backend.publish_fresh_sessions(**request)
    document, control = client.backend.fresh_session(published['path'], published['sha256'])
    client.write(control / 'START.json', dict(session_sha256=published['sha256'], identity=client.backend.process_identity()))
    state, owner = document['state'], document['owners'][branch]
    model = fixture_module.TinyModel()
    adapter = torch.load(Path(client.read(state['checkpoint']['path'])['adapter']['path']) / 'adapter_model.pt',
                         weights_only=False)
    with torch.no_grad():
        for name, parameter in model.named_parameters():
            if name in adapter:
                parameter.copy_(adapter[name])
    engine = SimpleNamespace(torch=torch, model=model, device='cpu', verify_base=lambda: None)
    optimizer = torch.optim.AdamW([parameter for name, parameter in model.named_parameters()
        if client.backend.parallel.is_lora(name)], lr=.001) if branch == 'F1' else None
    session = client.Session.__new__(client.Session)
    session.branch, session.owner = branch, branch == 'F1'
    session.root, session.shared_root = tmp_path / branch, Path(document['root'])
    session.state, session.loaded_reference = state, state['checkpoint']
    envelope = boundary.bound(owner['handoff'])
    session.plan = dict(route_boundary_release=envelope['release'], source_files=owner['source_files'],
                        parallel_source=owner['cwd'])
    monkeypatch.setenv('R118_PARALLEL_SESSION', published['path'])
    monkeypatch.setenv('R118_PARALLEL_SESSION_SHA256', published['sha256'])
    monkeypatch.setenv('R118_PARALLEL_BRANCH', branch)
    before = (session.shared_root / 'STATE.json').read_bytes()
    result = session.bootstrap(engine, optimizer)
    assert result['optimizer_count'] == int(branch == 'F1') and result['fresh_EXEC'] is True
    assert result['predecessor_object_reused'] is False
    assert result['optimizer_updates_replayed'] == 0
    if sidecar:
        assert result['rng_provenance'] == 'RESTORED_ALL8_PARALLEL_SIDECAR'
    elif branch == 'A1':
        assert result['rng_provenance'] == 'NEW_DETERMINISTIC_RANK_STREAM_NOT_OLD_PEER_RNG'
    if branch == 'F1':
        original = torch.load(state['checkpoint']['optimizer_path'], weights_only=False)
        assert client.backend.state_hash(optimizer.state_dict()) == client.backend.state_hash(original['optimizer'])
        assert torch.equal(torch.get_rng_state(), original['cpu_rng'])
    with pytest.raises(ValueError, match='fixture_deadline'):
        session.await_collection(lambda label: client.require(False, 'fixture_deadline'))
    assert (session.shared_root / 'STATE.json').read_bytes() == before


def test_runtime_fresh_bootstrap_and_GO_precede_collection():
    source = inspect.getsource(run.run)
    assert source.index('shared_session.bootstrap(engine, optimizer)') < source.index("root/'R118_PARALLEL_ACTOR_READY.json'")
    assert source.index('shared_session.await_collection(check)') < source.index('for cycle in range(')
    assert 'pooled.restore_optimizer(' not in source


def test_export_actual_release_to_Herschel_owner_contract(completed, monkeypatch):
    root = completed.root
    snapshot = boundary.settled(root, completed.common, completed.cycle)
    release_path = root/'RELEASED.json'
    identity = dict(boot_id='fixture', pid=123, start_ticks='45')
    put(release_path, dict(status='RELEASED', actor=identity, supervisor=dict(identity, pid=122)))
    source_files = {str(Path(run.__file__).resolve()): boundary.sha(run.__file__)}
    plan = dict(parallel_source=str(Path(run.__file__).resolve().parents[1]), source_files=source_files,
        shared_learner=dict(branch='F1'), physical=0, uuid=boundary.prior.UUIDS[0],
        route_boundary_release=boundary.ref(release_path), bounds=dict(hard_end_unix=1789596240,
            lease_end_unix=1789617840, native_calls=32768, parent_calls=16384))
    monkeypatch.setattr(lifecycle, 'verify_plan', lambda *args: plan)
    monkeypatch.setattr(boundary, 'released', lambda *args: snapshot)
    before = (root/'RESERVATIONS.jsonl').read_bytes()
    result = lifecycle.export_fresh_owner(root, root/'fresh-export', sys.executable)
    owner = boundary.bound(result['owner'])
    envelope = boundary.bound(owner['handoff'])
    assert owner['command'] == [sys.executable, '-B', '-m', boundary.SUCCESSOR, 'launch', '--root', str(root)]
    assert owner['inherited_bounds']['train_end_unix'] == boundary.TRAIN_END
    assert owner['inherited_bounds']['hard_end_unix'] == client.HARD_END
    assert envelope['next_cycle'] == 8 and envelope['preserved_files'] == snapshot['preserved_files']
    assert all(type(identity['start_ticks']) is int for identity in envelope['predecessors'])
    assert not any(name.startswith('R118_PARALLEL_') for name in owner['env'])
    assert (root/'RESERVATIONS.jsonl').read_bytes() == before


def test_campaign_callback_invoked_with_actual_certificate_and_check(tmp_path, monkeypatch):
    session = client.Session.__new__(client.Session)
    session.shared_root, session.branch = tmp_path/'common', 'F1'
    session.plan = dict(source_files={'/actual/source.py':'b'*64})
    campaign = dict(path=str(tmp_path/'CAMPAIGN.json'), sha256='a'*64)
    session.control = dict(campaign=campaign, requires_campaign=True,
        activation_directory=str(tmp_path/'activations'), activation_wait_end_unix=boundary.TRAIN_END)
    document = dict(root=str(session.shared_root), source_files=session.plan['source_files'],
        activation_directory=session.control['activation_directory'], deadline_unix=boundary.TRAIN_END)
    monkeypatch.setattr(client.backend, 'campaign_document', lambda *args: (document, tmp_path/'watch'))
    activation = dict(path=str(tmp_path/'ACTIVATION.json'), sha256='c'*64)
    callback = Mock(return_value=activation)
    monkeypatch.setattr(client.backend, 'await_campaign_activation', callback)
    check = Mock(); certificate = dict(path=str(tmp_path/'SAFE.json'),sha256='d'*64)
    assert session.wait_activation(certificate, check) == activation
    callback.assert_called_once_with(campaign['path'],campaign['sha256'],'F1',certificate,check=check)
    document['deadline_unix'] += 1
    with pytest.raises(ValueError,match='original_bounds'):
        session.wait_activation(certificate, check)
    assert callback.call_count == 1


def test_campaign_rejects_stale_source_before_publication(tmp_path, monkeypatch):
    control = dict(campaign=dict(path='fixture',sha256='a'*64),
        activation_directory=str(tmp_path/'activation'),activation_wait_end_unix=boundary.TRAIN_END)
    document = dict(root=str(tmp_path),activation_directory=control['activation_directory'],
        deadline_unix=boundary.TRAIN_END,source_files={})
    monkeypatch.setattr(client.backend,'campaign_document',lambda *args:(document,tmp_path/'watch'))
    with pytest.raises(ValueError,match='pins_actual_route_source'):
        client.validate_campaign(control,tmp_path,{'/actual/source.py':'b'*64})


def test_peer_terminal_does_not_interrupt_postcommit_fresh_DEV(completed):
    control = dict(routes={'F1': dict(root=str(completed.root))}, freeze_unix=cutoff.CUTOFF-60)
    (completed.cycle/'COMPLETE.json').unlink()
    action = dict(action='STOP', reason='PEER_CANNOT_COMPLETE_BARRIER', peers={'F2': 'ACTUAL_ERA_TERMINAL'})
    result = cutoff.protect_readouts(control, action, cutoff.DRAIN-100)
    assert result['action'] == 'DRAIN_READOUTS' and set(result['pending']) == {'F1'}
    assert cutoff.protect_readouts(control, action, control['freeze_unix']) == action
    put(completed.cycle/'COMPLETE.json', dict(cycle=7))
    assert cutoff.protect_readouts(control, action, cutoff.DRAIN-100) == action
