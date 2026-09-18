from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from gpu import orch_r118_route_crash_boundary as recovery
from gpu import orch_r118_route_parallel_boundary as boundary
from gpu import orch_r118_route_parallel_client as client
from gpu import orch_r118_route_parallel_lifecycle as lifecycle
from gpu import orch_r118_route_parallel_run as run
from test_orch_r118_route_parallel import completed, put
from test_orch_r111_route_pair import native_shape_engine


@pytest.fixture
def crashed(completed, monkeypatch):
    root, common, cycle = completed.root, completed.common, completed.cycle
    config = dict(branches={'F1': dict(root=str(root), train_ids=['F1-one', 'F1-two'])}, excluded_ids=['FINAL'])
    put(common/'CONFIG.json', config)
    state = deepcopy(completed.state)
    state['config_sha256'] = boundary.sha(common/'CONFIG.json')
    put(common/'STATE.json', state)
    put(common/'generation_000000/sleep/COMPLETE.json', dict(state=state, same_optimizer=True,
        source_checkpoint=state['checkpoint'], completed_unix=1))
    put(cycle/'SHARED_SLEEP.json', dict(status='COMPLETE', state=state, branch='F1'))
    rows = []
    for number, task in enumerate(config['branches']['F1']['train_ids'], 1):
        response = run.generate(native_shape_engine(), [dict(role='user', content='Actual fixture task')], cap=8)
        call = dict(task_id=task, phase='experience', finished_unix=3, response=response,
            shared_generation=0, shared_checkpoint_sha256=state['checkpoint']['path_sha256'])
        path = cycle/f'CALL_{number:06d}.json'
        put(path, call)
        rows.append(run.causal.replay_row(call, path, boundary.sha(path)))
    put(cycle/'ROWS.json', rows)
    submission = common/'generation_000000/F1.json'
    put(submission, dict(branch='F1', generation=0, checkpoint_sha256=state['checkpoint']['path_sha256'],
                        episode_ids=['F1-one', 'F1-two'], rows=rows))
    put(cycle/'SHARED_SUBMISSION.json', dict(generation=0, **boundary.ref(submission)))
    put(common/'generation_000000/sleep/ENCODING.json', dict(new=2, old=0, rejected=[]))
    (cycle/'COMPLETE.json').unlink()
    (root/'readout_0007/COMPLETE.json').unlink()
    (root/'readout_0007/CALL_000002.json').unlink()
    (root/'open_readouts/readout_0007/COMPLETE.json').unlink()
    put(root/'readout_0007/LAUNCH.json', dict(pid=2000000002, parent_free=True))
    put(root/'readout_0007/CALL_000003.json', dict(started_unix=4, phase='readout'))
    put(root/'CRASH_100.json', dict(error_type='TimeoutError', finished_unix=5, all_charges_preserved=True))
    ledger = [dict(kind='NATIVE', number=1, cycle=7, phase='experience'),
              dict(kind='NATIVE', number=2, cycle=7, phase='experience'),
              dict(kind='PARENT', number=1, cycle=7, phase='experience'),
              dict(kind='NATIVE', number=3, sleep=7, phase='readout')]
    (root/'RESERVATIONS.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in ledger))
    plan = dict(physical=0, uuid=boundary.prior.UUIDS[0], parent_wait_seconds=120,
        bounds=dict(native_calls=32768, parent_calls=16384, cycles=512,
                    hard_end_unix=1789596240, lease_end_unix=1789617840),
        shared_learner=dict(branch='F1', root=str(common), config_sha256=state['config_sha256']))
    put(root/'PLAN.json', plan)
    directory = root/'old_control'
    identities = [dict(pid=2000000000+index, uid=os.getuid(), start_ticks=str(index), boot_id='fixture',
                       command_sha256='a'*64, ppid=1) for index in range(3)]
    control = directory/'CONTROL.json'
    put(control, dict(directory=str(directory), source=boundary.ref(Path(recovery.old_cutoff.__file__).resolve()),
        routes={'F1': dict(root=str(root), plan=boundary.ref(root/'PLAN.json'), uuid=plan['uuid'],
                          supervisor=identities[0], initial_actor=identities[1])}))
    disposition = directory/'F1/DISPOSITION.json'
    put(disposition, dict(status='RELEASED', reason='PEER_CANNOT_COMPLETE_BARRIER', no_fake_terminal=True,
        released_unix=6, processes=[dict(role=role, identity=identity) for role, identity in
                                   zip(('supervisor', 'actor', 'readout'), identities)]))
    authorization = root/'AUTHORIZATION.json'
    put(authorization, dict(purpose=recovery.MODE, authorized=True, allow_missing_postcommit_readouts=True,
        no_train_replay=True, no_fake_complete=True, dispatch_authorized=False, roots=[str(root)],
        canonical_checkpoint_sha256=state['checkpoint']['path_sha256']))
    monkeypatch.setattr(boundary.prior, 'ROOT_TEMPLATE', str(root))
    return SimpleNamespace(root=root, common=common, cycle=cycle, state=state, plan=plan,
        control=control, disposition=disposition, authorization=authorization, optimizer=completed.optimizer)


def capture(crashed):
    return recovery.capture(crashed.root, boundary.ref(crashed.authorization), boundary.ref(crashed.control),
                            boundary.ref(crashed.disposition))


def test_crash_snapshot_preserves_interrupted_eval_and_accepted_train(crashed):
    original = {str(path):path.read_bytes() for path in crashed.root.rglob('*') if path.is_file()}
    result = capture(crashed)
    snapshot = boundary.released(crashed.root, result)
    assert snapshot['next_cycle'] == 8 and snapshot['trained_generation'] == 0
    assert len(snapshot['accepted_train_hashes']) == 2
    assert snapshot['charged'] == {'NATIVE': 3, 'PARENT': 1}
    assert snapshot['eval_reservations'][0]['capture_finished'] is False
    assert snapshot['cycle_completion_claimed'] is False
    assert all(Path(path).read_bytes()==data for path,data in original.items())
    assert not (crashed.cycle/'COMPLETE.json').exists()
    assert not (crashed.root/'readout_0007/COMPLETE.json').exists()
    assert not (crashed.common/'generation_000001/F1.json').exists()
    assert boundary.successor_cycle(crashed.root, result) == 8
    with pytest.raises(ValueError, match='no_overwrite'):
        capture(crashed)


@pytest.mark.parametrize('damage', ['complete_absent', 'state_partial', 'optimizer_bytes', 'optimizer_incomplete',
                                    'train_pending', 'parent_pending', 'new_train', 'new_submission'])
def test_reject_uncommitted_optimizer_or_unsettled_train(crashed, damage):
    if damage == 'complete_absent':
        (crashed.common/'generation_000000/sleep/COMPLETE.json').unlink()
    elif damage == 'state_partial':
        state = boundary.read(crashed.common/'STATE.json'); state['generation']=0
        put(crashed.common/'STATE.json', state)
    elif damage == 'optimizer_bytes':
        crashed.optimizer.write_bytes(b'uncommitted replacement')
    elif damage == 'optimizer_incomplete':
        path = crashed.common/'generation_000000/sleep/COMPLETE.json'
        value=boundary.read(path); value['same_optimizer']=False; put(path,value)
    elif damage in ('train_pending', 'parent_pending'):
        path = (crashed.cycle/'CALL_000001.json' if damage=='train_pending' else
                crashed.root/'parent_queue/000001_F1_C0007.observed.json')
        value=boundary.read(path); value.pop('finished_unix' if damage=='train_pending' else 'observed_unix')
        put(path,value)
    elif damage == 'new_train':
        with (crashed.root/'RESERVATIONS.jsonl').open('a') as stream:
            stream.write(json.dumps(dict(kind='NATIVE',number=4,cycle=8,phase='experience'))+'\n')
    else:
        put(crashed.common/'generation_000001/F1.json', dict(already_submitted=True))
    with pytest.raises((ValueError,FileNotFoundError)):
        capture(crashed)
    assert not (crashed.root/recovery.DIRECTORY).exists()


def test_live_recorded_identity_blocks_without_signals(crashed, monkeypatch):
    identity = recovery.old_cutoff.identity(os.getpid())
    doc = boundary.read(crashed.disposition); doc['processes'][1]['identity']=identity; put(crashed.disposition,doc)
    monkeypatch.setattr(os,'pidfd_open',lambda *args:pytest.fail('no pidfds in crash capture'))
    with pytest.raises(ValueError,match='still_alive'):
        capture(crashed)


def test_partial_canonical_document_rejected_even_with_matching_hashes(crashed, monkeypatch):
    original = recovery.read
    checkpoint = Path(crashed.state['checkpoint']['path'])

    def incomplete_document(path):
        value = original(path)
        return dict(value, complete=False) if Path(path) == checkpoint else value

    monkeypatch.setattr(recovery, 'read', incomplete_document)
    with pytest.raises(ValueError, match='canonical_checkpoint_complete'):
        capture(crashed)
    assert not (crashed.root/recovery.DIRECTORY).exists()


def test_missing_eval_capture_remains_charged_no_retry(crashed):
    (crashed.root/'readout_0007/CALL_000003.json').unlink()
    result=capture(crashed)
    snapshot=boundary.released(crashed.root,result)
    assert snapshot['eval_reservations'][0]['capture'] is None
    assert snapshot['eval_reservations'][0]['retry'] is False
    assert snapshot['charged']['NATIVE']==3


def test_encoding_rejection_is_retained_not_promoted_or_resubmitted(crashed):
    rows=boundary.read(crashed.cycle/'ROWS.json')
    put(crashed.common/'generation_000000/sleep/ENCODING.json',dict(new=1,old=0,
        rejected=[dict(kind='NEW',source=rows[0]['source_call_sha256'],error='fixture encoding rejection')]))
    snapshot=boundary.released(crashed.root,capture(crashed))
    assert snapshot['accepted_train_hashes']==[rows[1]['source_call_sha256']]
    assert snapshot['rejected_train_hashes']==[rows[0]['source_call_sha256']]
    assert snapshot['generation_zero_resubmitted'] is False


def test_real_Herschel_postcommit_contract_accepts_export_without_success_claim(crashed, monkeypatch):
    release=capture(crashed)
    plan=dict(crashed.plan,route_boundary_release=release,parallel_source=str(Path(run.__file__).resolve().parents[1]),
              source_files={str(Path(run.__file__).resolve()):boundary.sha(run.__file__)})
    monkeypatch.setattr(lifecycle,'verify_plan',lambda *args:plan)
    exported=lifecycle.export_fresh_owner(crashed.root,crashed.root/'export',sys.executable)
    owner=boundary.bound(exported['owner']); envelope=boundary.bound(owner['handoff'])
    assert 'fresh_dev' not in owner['boundary'] and owner['boundary']['mounted_checkpoint_sha256'] is None
    assert owner['boundary']['canonical_reload_required'] is True
    client.backend.postcommit_evaluation_boundary(crashed.common,'F1',owner,envelope,
        boundary.read(crashed.common/'CONFIG.json'),crashed.state)
    disposition=boundary.bound(owner['boundary']['postcommit_eval_disposition'])
    assert disposition['evaluations']=={'DEV':'INTERRUPTED','OPEN':'INTERRUPTED'}
    assert disposition['counted_as_success'] is False
    assert len(envelope['predecessors'])==3


def test_capture_cli_help_has_no_native_or_provider_call():
    result=subprocess.run([sys.executable,'-B','-m',recovery.__name__,'--help'],capture_output=True,text=True,timeout=10)
    assert result.returncode==0 and 'capture' in result.stdout and 'verify' in result.stdout


def test_broker_Python_source_is_hash_checked_not_JSON_parsed(tmp_path, monkeypatch):
    source = tmp_path/'broker.py'; source.write_text('provider = "fixture"\n')
    put(tmp_path/lifecycle.PLAN, {})
    put(tmp_path/'R118_PARALLEL_BROKER_BINDING.json', dict(root=str(tmp_path),
        plan=boundary.ref(tmp_path/lifecycle.PLAN), terminal=lifecycle.TERMINAL, parent_wait_seconds=120,
        identity={}, source=boundary.ref(source), provider='fixture'))
    monkeypatch.setattr(lifecycle,'identity_exited',lambda *args:False)
    lifecycle.validate_broker_binding(tmp_path, {'provider':'fixture'})
    source.write_text('changed = True\n')
    with pytest.raises(ValueError,match='source_bytes'):
        lifecycle.validate_broker_binding(tmp_path, {'provider':'fixture'})


def prestage_ready(crashed):
    release = capture(crashed)
    cpu = crashed.root/'candidate_CPU.json'
    put(cpu, dict(returncode=0))
    source = Path(lifecycle.__file__).resolve().parents[1]
    names = ['orch_r118_route_parallel_run.py', 'orch_r118_route_parallel_client.py',
             'orch_r118_route_parallel_lifecycle.py', 'orch_r118_route_crash_boundary.py']
    ready = crashed.root/'CANDIDATE_READY.json'
    put(ready, dict(status='CPU_READY_NOT_ACTIVATED', requires_campaign=True, branch='F1',
        original_plan=boundary.ref(crashed.root/'PLAN.json'), release=release, cpu=boundary.ref(cpu),
        backend_source=boundary.ref(Path(client.backend.__file__).resolve()), source_root=str(source),
        source_files={str(source/'gpu'/name): boundary.sha(source/'gpu'/name) for name in names}))
    return release, ready


def test_prestage_owner_real_contract_no_PLAN_or_ledger_mutation(crashed):
    release, ready = prestage_ready(crashed)
    original = {name: (crashed.root/name).read_bytes() for name in ('PLAN.json','RESERVATIONS.jsonl','OWN_CARRY.json')}
    result = lifecycle.prepare_fresh_owner(crashed.root, crashed.root/'prepared', sys.executable,
                                           release, boundary.ref(ready))
    owner = boundary.bound(result['owner'])
    assert owner['runtime_staged'] is False and owner['requires_coordinated_stage_before_dispatch'] is True
    assert owner['command'][3:] == [boundary.SUCCESSOR, 'launch', '--root', str(crashed.root)]
    assert not (crashed.root/lifecycle.PLAN).exists()
    assert all((crashed.root/name).read_bytes() == value for name,value in original.items())
    client.backend.postcommit_evaluation_boundary(crashed.common, 'F1', owner,
        boundary.bound(owner['handoff']), boundary.read(crashed.common/'CONFIG.json'), crashed.state)


@pytest.mark.parametrize('damage', ['backend', 'source', 'cpu', 'release'])
def test_prestage_rejects_stale_candidate(crashed, damage):
    release, ready = prestage_ready(crashed)
    document = boundary.read(ready)
    if damage == 'backend':
        document['backend_source']['sha256'] = '0'*64
    elif damage == 'source':
        document['source_files'][next(iter(document['source_files']))] = '0'*64
    elif damage == 'cpu':
        put(Path(document['cpu']['path']), dict(returncode=1))
        document['cpu'] = boundary.ref(document['cpu']['path'])
    else:
        document['release']['sha256'] = '0'*64
    put(ready, document)
    with pytest.raises(ValueError):
        lifecycle.prepare_fresh_owner(crashed.root, crashed.root/'prepared', sys.executable,
                                      release, boundary.ref(ready))
    assert not (crashed.root/'prepared').exists() and not (crashed.root/lifecycle.PLAN).exists()
