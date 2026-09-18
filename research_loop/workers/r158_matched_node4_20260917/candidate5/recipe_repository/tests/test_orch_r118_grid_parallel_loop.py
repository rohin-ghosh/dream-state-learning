from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import pytest

from gpu import orch_r118_grid_parallel_loop as loop


@dataclass
class Identity:
    value: str

    def document(self):
        return {'value':self.value}


@dataclass
class Binding:
    adapter: Identity
    cycle: int


class Parameter:
    requires_grad = True

    def requires_grad_(self, value):
        self.requires_grad = value


class Model:
    def __init__(self):
        self.parameter = Parameter()
        self.moves = []

    def named_parameters(self):
        return [('lora', self.parameter)]

    def to(self, device):
        self.moves.append(device)
        return self


@pytest.fixture
def decoder():
    model = Model()
    loaded = SimpleNamespace(optimizer=None, binding=Binding(Identity('old'), 1), observed=Identity('old'),
        engine=SimpleNamespace(model=model, device='cuda:0',
            torch=SimpleNamespace(cuda=SimpleNamespace(empty_cache=lambda:None))))
    return SimpleNamespace(loaded=loaded, verify_base=lambda:None)


def test_fresh_DEV_offloads_restores_and_passes_exact_session(decoder, tmp_path):
    session = {'exact':'committed session'}
    calls = []

    def readout(root, cycle, scope, actual):
        assert decoder.loaded.engine.model.moves == ['cpu']
        calls.append((root, cycle, scope, actual))

    loop.fresh_dev(decoder, tmp_path, 6, session, readout=readout)
    assert calls == [(tmp_path, 6, 'dev', session)]
    assert decoder.loaded.engine.model.moves == ['cpu', 'cuda:0']


def test_failed_DEV_restores_without_retry(decoder, tmp_path):
    calls = []

    def fail(*args):
        calls.append(args)
        raise RuntimeError('preserve failed readout')

    with pytest.raises(RuntimeError, match='failed readout'):
        loop.fresh_dev(decoder, tmp_path, 6, {}, readout=fail)
    assert len(calls) == 1
    assert decoder.loaded.engine.model.moves == ['cpu', 'cuda:0']


@pytest.fixture
def committed(decoder, tmp_path, monkeypatch):
    session = dict(branch='A4', branch_root=str(tmp_path), shared_root=str(tmp_path), config_sha256='config',
        generation=1, checkpoint_sha256='old', adapter={'value':'old'})
    next_session = dict(session, generation=2, checkpoint_sha256='new', adapter={'value':'new'})
    state = {'committed':True}
    acknowledgments = [dict(branch=branch, identity={'fixture':branch}, checkpoint_sha256='new', in_place=True)
                       for branch in loop.shared.BRANCHES]
    loop.shared.write(tmp_path / 'generation_000001/sleep/ALL8_RELOAD.json',
                      dict(state=state, acknowledgments=acknowledgments))
    monkeypatch.setattr(loop.run.client, 'prepare', lambda *args, **kwargs:next_session)
    monkeypatch.setattr(loop.handoff, 'committed', lambda actual:state)
    monkeypatch.setattr(loop.parallel, 'process_identity', lambda:{'fixture':'A4'})
    monkeypatch.setattr(loop.run.client.native.bridge, 'AdapterIdentity',
                        SimpleNamespace(from_document=lambda doc:Identity(doc['value'])))
    monkeypatch.setattr(loop.run.client.native, 'observe_adapter', lambda engine, identity:identity)
    return session, dict(status='COMPLETE_ALL8_INPLACE', state=state), next_session


def test_inplace_commit_rebinds_without_second_reload(decoder, committed, monkeypatch):
    session, result, expected = committed
    monkeypatch.setattr(loop.run.client, 'reload_shared', lambda *args:pytest.fail('second load forbidden'))
    before = loop.model_objects(decoder)
    next_session, receipt = loop.adopt_in_place(decoder, session, result, before)
    assert next_session == expected
    assert loop.model_objects(decoder) == before
    assert decoder.loaded.binding == Binding(Identity('new'), 2)
    assert decoder.loaded.optimizer is None
    assert decoder.loaded.engine.model.parameter.requires_grad is False
    assert receipt['rng_reinitialized'] is False


def test_replaced_parameter_or_local_optimizer_rejected(decoder, committed):
    session, result, expected = committed
    before = loop.model_objects(decoder)
    decoder.loaded.engine.model.parameter = Parameter()
    with pytest.raises(ValueError, match='same_engine'):
        loop.adopt_in_place(decoder, session, result, before)
    decoder.loaded.optimizer = object()
    with pytest.raises(ValueError, match='optimizer'):
        loop.model_objects(decoder)


@pytest.mark.parametrize('mutation', ['missing_ack', 'wrong_state', 'wrong_identity', 'not_inplace'])
def test_bad_all8_ack_preserves_old_binding(decoder, committed, mutation):
    session, result, expected = committed
    path = Path(session['shared_root']) / 'generation_000001/sleep/ALL8_RELOAD.json'
    document = loop.shared.read(path)
    if mutation == 'missing_ack':
        document['acknowledgments'].pop()
    elif mutation == 'wrong_state':
        document['state'] = {}
    elif mutation == 'wrong_identity':
        document['acknowledgments'][-1]['identity'] = {}
    else:
        document['acknowledgments'][-1]['in_place'] = False
    loop.shared.write(path, document, replace=True)
    with pytest.raises(ValueError):
        loop.adopt_in_place(decoder, session, result, loop.model_objects(decoder))
    assert decoder.loaded.binding.adapter == Identity('old')


def test_no_go_no_collection_or_native_call(tmp_path, monkeypatch):
    path = tmp_path / 'not_go.json'
    loop.shared.write(path, dict(schema='R118_GRID_PARALLEL_ENTRY_V1', status='CPU_ONLY_NOT_ARMED',
                                branches=list(loop.shared.BRANCHES)))
    monkeypatch.setattr(loop.parallel, 'launch_at_boundary', lambda **kwargs:pytest.fail('must not launch'))
    with pytest.raises(ValueError, match='Main_all8'):
        loop.run_loop(root=tmp_path, decoder=None, session={}, boundary={},
            entry_reference=loop.handoff.reference(path), config={}, anchor_module=None,
            anchor_root=None, certificate_for_submission=None, activation_for_certificate=None)


@pytest.mark.parametrize('fail_hook', [False, True])
def test_real_loop_order_and_no_optimizer_or_retry(decoder, tmp_path, monkeypatch, fail_hook):
    session = dict(branch='A4', branch_root=str(tmp_path), generation=1, checkpoint_sha256='old',
                   config_sha256='unchanged')
    boundary = dict(session=session, next_cycle=6, bounds={})
    boundary_path = tmp_path / 'boundary.json'
    loop.shared.write(boundary_path, boundary)
    own = dict(boundary=loop.handoff.reference(boundary_path), rng_provenance='SAME_PROCESS_RETAINED')
    loop.shared.write(tmp_path / 'CONFIG.json', {})
    loop.shared.write(tmp_path / 'CARRY.json', ['existing carry'])
    loop.shared.write(tmp_path / 'TRAIN.json', ['exact roster'])
    certificate = dict(identity={'pid':123}, branch='A4', root=str(tmp_path), generation=1,
                       checkpoint_sha256='old')
    certificate_path = tmp_path / 'cert.json'
    loop.shared.write(certificate_path, certificate)
    events = []
    monkeypatch.setattr(loop, 'permit', lambda *args, **kwargs:own)
    monkeypatch.setattr(loop.handoff, 'validate_snapshot', lambda actual:actual)
    monkeypatch.setattr(loop.handoff, 'supervision', lambda actual:None)
    monkeypatch.setattr(loop.run, 'inherited_bounds', lambda config:{})
    monkeypatch.setattr(loop.run, 'can_train', lambda root:not events)
    monkeypatch.setattr(loop.run, 'life_class', lambda branch:lambda *args:'actual_life')
    monkeypatch.setattr(loop.run, 'cycle_tasks', lambda roster, cycle:['first', 'second'])
    monkeypatch.setattr(loop.parallel, 'process_identity', lambda:{'pid':123})

    def collect(life, tasks, memory):
        assert life == 'actual_life' and tasks == ['first', 'second'] and memory == ['existing carry']
        events.append('two_sequential_TRAIN')
        return {'actual':'submission'}

    def hook(**kwargs):
        assert kwargs['engine'] is decoder.loaded.engine
        assert kwargs['optimizer'] is None and kwargs['save_checkpoint'] is None
        events.append('collective')
        if fail_hook:
            raise RuntimeError('failed all8 no fallback')
        return {'committed':True}

    def adopt(*args):
        events.append('inplace_binding')
        return dict(session, generation=2, checkpoint_sha256='new'), {'reloaded':True}

    monkeypatch.setattr(loop.run.client, 'run_cycle_and_submit', collect)
    monkeypatch.setattr(loop.parallel, 'launch_at_boundary', hook)
    monkeypatch.setattr(loop, 'adopt_in_place', adopt)
    monkeypatch.setattr(loop, 'fresh_dev', lambda *args:events.append('fresh_DEV'))
    kwargs = dict(root=tmp_path, decoder=decoder, session=session, boundary=boundary, entry_reference={},
        config={}, anchor_module=None, anchor_root='original42', check=lambda stage:None, clock=lambda:1,
        certificate_for_submission=lambda *args:loop.handoff.reference(certificate_path),
        activation_for_certificate=lambda *args:dict(path='Main activation', sha256='pinned'))
    decoder.loaded.binding.adapter = SimpleNamespace(document=lambda:session.get('adapter', {}))
    session['adapter'] = {}
    boundary['session'] = session
    loop.shared.write(boundary_path, boundary, replace=True)
    own['boundary'] = loop.handoff.reference(boundary_path)
    if fail_hook:
        with pytest.raises(RuntimeError, match='no fallback'):
            loop.run_loop(**kwargs)
        assert events == ['two_sequential_TRAIN', 'collective']
        failure = loop.shared.read(tmp_path / 'parallel_cycles/0006/FAILED.json')
        assert failure['serial_fallback'] is False and failure['replay_permitted'] is False
    else:
        result = loop.run_loop(**kwargs)
        assert result['next_cycle'] == 7 and result['no_automatic_FINAL'] is True
        assert events == ['two_sequential_TRAIN', 'collective', 'inplace_binding', 'fresh_DEV']
