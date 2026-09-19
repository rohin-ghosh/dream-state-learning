from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

from gpu import orch_r157_node5_keepalive as keepalive


@pytest.fixture
def fixture():
    plan = dict(physical=2, gpu_uuid=keepalive.LANES[2][1],
                root=str(keepalive.BASE / keepalive.LANES[2][0] / 'run1'),
                hard_end_unix=1789617240.0, lease_end_unix=1789617840.0,
                source_root='/frozen/source', experiment={'seed': 17}, context_limit=16384,
                anchor_weight=0.25, readout_revision=2,
                authorized_wall_extension={'previous': 'already consumed'})
    state = dict(deadline_unix=plan['hard_end_unix'], pending=None, rows=[{'own': 'text'}],
                 sleep_frontier=1, sleep_receipts=[{'status': 'COMPLETE'}],
                 model_state_sha256='a' * 64, history={'tokens': [1, 2, 3]}, own_carry='next inquiry')
    return plan, state


def test_only_runtime_fields_change_and_inputs_untouched(fixture):
    plan, state = fixture
    original_plan, original_state = deepcopy(plan), deepcopy(state)
    successor = keepalive.extension_plan(plan, state)
    assert plan == original_plan and state == original_state
    assert successor['hard_end_unix'] == 1789776000
    assert successor['source_root'] == plan['source_root']
    assert successor['experiment'] == plan['experiment']
    assert successor['context_limit'] == 16384 and successor['anchor_weight'] == 0.25
    assert {key for key in plan if plan[key] != successor[key]} == {
        'hard_end_unix', 'lease_end_unix', 'authorized_wall_extension'}
    authorization = successor['authorized_wall_extension']
    assert authorization['previous_stream_sha256'] == keepalive.digest(state)
    assert authorization['new_deadline_unix'] == successor['lease_end_unix'] - 600


@pytest.mark.parametrize('field,value', [('pending', {'generation': 'unfinished'}), ('sleep_frontier', 0),
    ('sleep_receipts', []), ('sleep_receipts', [{'status': 'FAILED'}]), ('deadline_unix', 0)])
def test_unsaved_or_wrong_state_rejected(fixture, field, value):
    plan, state = fixture
    state[field] = value
    with pytest.raises(ValueError):
        keepalive.extension_plan(plan, state)


@pytest.mark.parametrize('field,value', [('physical', 7), ('gpu_uuid', 'foreign'), ('root', '/other/life')])
def test_other_lives_cannot_be_modified(fixture, field, value):
    plan, state = fixture
    plan[field] = value
    with pytest.raises(ValueError):
        keepalive.extension_plan(plan, state)


def test_unsaved_replay_plan_rejected(fixture):
    plan, state = fixture
    plan['preupdate_recovery'] = {'unsafe': True}
    with pytest.raises(ValueError, match='no_unsaved_replay'):
        keepalive.extension_plan(plan, state)


def test_containment_has_one_gpu_and_preserves_allocator(fixture):
    plan, unused_state = fixture
    config = dict(device_containment=dict(uid=2524, gid=2524, minor=2, unit='orch-r136-native-' + 'a' * 32))
    command = keepalive.contained_command(config, plan, Path('/operator.py'), Path('/output'))
    assert '--property=DevicePolicy=strict' in command
    assert '--property=DeviceAllow=/dev/nvidia2 rw' in command
    assert not any('--property=DeviceAllow=/dev/nvidia6 ' in argument for argument in command)
    assert 'CUDA_VISIBLE_DEVICES=' + plan['gpu_uuid'] in command
    assert 'PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True' in command
    assert '--property=NoNewPrivileges=yes' in command


def test_boundary_requires_verified_record_and_envelope(tmp_path, fixture):
    unused_plan, state = fixture
    directory = tmp_path / 'stream/records'
    directory.mkdir(parents=True)
    record = dict(kind='SLEEP_COMPLETE', document=dict(status='COMPLETE', cycle=3,
        resume_state=dict(state=state, sha256=keepalive.digest(state))))
    record['sha256'] = keepalive.digest(record)
    path = directory / '00000000000000000001.json'
    keepalive.write(path, record)
    assert keepalive.boundary(tmp_path)['state'] == state
    record['document']['resume_state']['state']['own_carry'] = 'tampered'
    path.write_bytes(keepalive.encoded(record))
    with pytest.raises(ValueError, match='record_hash'):
        keepalive.boundary(tmp_path)


@pytest.fixture
def readmission(tmp_path, monkeypatch):
    previous = tmp_path / 'failed'
    previous.mkdir()
    output = tmp_path / 'readmit'
    authority = tmp_path / 'AUTHORIZATION.json'
    keepalive.write(authority, {'authorized': True})
    real_sha = keepalive.sha
    monkeypatch.setattr(keepalive, 'sha', lambda path: keepalive.AUTH_SHA if Path(path) == authority else real_sha(path))
    cpu = tmp_path / 'CPU.json'
    keepalive.write(cpu, {'passed': True, 'operator_sha256': real_sha(keepalive.__file__)})
    checkpoint = tmp_path / 'COMMIT.json'
    keepalive.write(checkpoint, {'optimizer_steps': 3618})
    state = {'history': ['unchanged'], 'optimizer_steps': 3618}
    boundary = {'record_sha256': 'saved-record', 'state_sha256': keepalive.digest(state), 'checkpoint_path': str(checkpoint)}
    config = {'source_pins': {'frozen.py': 'abc'}, 'device_containment': {'unit': 'previous', 'minor': 6}}
    plan = {'root': str(tmp_path / 'life'), 'hard_end_unix': keepalive.NEW_WALL}
    for name, value in {
        'ADMISSION.json': {'clear': False, 'blocking_reasons': ['process_identity_drift:999999991']},
        'OLD_STOPPED.json': {'old_actor': {'pid': 999999992}, 'old_timer': {'pid': 999999993}},
        'SUPERVISOR_STARTED.json': {'pid': 999999994}, 'BOUNDARY.json': boundary,
        'GUARD.json': config, 'PLAN.json': plan, 'ALLOCATION.json': {'physical': 6},
        'LEASE_BUDGET.json': {'hard_end_unix': keepalive.NEW_WALL},
    }.items():
        keepalive.write(previous / name, value)
    verified = []
    guard = SimpleNamespace(child=SimpleNamespace(NativeChild=SimpleNamespace(verify_checkpoint=lambda value: verified.append(value))),
                            validate=lambda path: None)
    monkeypatch.setattr(keepalive, 'modules', lambda path: (config, plan, guard))
    monkeypatch.setattr(keepalive, 'boundary', lambda root: {'record': {'sha256': 'saved-record'}, 'state': state})
    return previous, output, authority, cpu, verified


def test_readmission_preserves_failed_attempt_and_checkpoint(readmission):
    previous, output, authority, cpu, verified = readmission
    hashes = {path.name: keepalive.sha(path) for path in previous.iterdir()}
    keepalive.readmit_stage(previous, output, authority, cpu)
    assert {path.name: keepalive.sha(path) for path in previous.iterdir()} == hashes
    assert verified == [{'optimizer_steps': 3618}]
    assert keepalive.read(output / 'PLAN.json') == keepalive.read(previous / 'PLAN.json')
    assert keepalive.read(output / 'GUARD.json')['source_pins'] == {'frozen.py': 'abc'}
    assert keepalive.read(output / 'READMISSION.json')['scanner_checks_unchanged'] is True
    assert not (output / 'LAUNCH.json').exists()


@pytest.mark.parametrize('name', ['LAUNCH.json', 'CONTAINED_COMMAND.json', 'ADMISSION_TIME.json', 'CONTAINMENT_VERIFIED.json'])
def test_readmission_rejects_possible_prior_dispatch(readmission, name):
    previous, output, authority, cpu, unused = readmission
    keepalive.write(previous / name, {})
    with pytest.raises(ValueError, match='failed_before_any_native_dispatch'):
        keepalive.readmit_stage(previous, output, authority, cpu)
    assert not output.exists()


def test_readmission_never_waives_another_scanner_reason(readmission):
    previous, output, authority, cpu, unused = readmission
    (previous / 'ADMISSION.json').write_text('{"clear": false, "blocking_reasons": ["foreign_GPU_holder"]}')
    with pytest.raises(ValueError, match='transient_identity_or_owned_cleanup_only'):
        keepalive.readmit_stage(previous, output, authority, cpu)


def test_readmission_rejects_advanced_journal(readmission, monkeypatch):
    previous, output, authority, cpu, unused = readmission
    monkeypatch.setattr(keepalive, 'boundary', lambda root: None)
    with pytest.raises(ValueError, match='same_unconsumed_saved_boundary'):
        keepalive.readmit_stage(previous, output, authority, cpu)
    assert not output.exists()


def test_readmission_allows_departed_owned_cleanup_only(readmission):
    previous, output, authority, cpu, unused = readmission
    (previous / 'ADMISSION.json').write_text('{"clear": false, "blocking_reasons": ["active_compute_pid:999999992", "reserved_cvd_pid:999999993", "unexplained_device_memory"]}')
    keepalive.readmit_stage(previous, output, authority, cpu)
    assert keepalive.read(output / 'READMISSION.json')['scanner_checks_unchanged']


@pytest.mark.parametrize('reasons', [['unexplained_device_memory'], ['active_compute_pid:999999995'],
                                   ['reserved_cvd_pid:999999993', 'uuid_reservation:999999995']])
def test_readmission_rejects_unattributed_cleanup(readmission, reasons):
    previous, output, authority, cpu, unused = readmission
    (previous / 'ADMISSION.json').write_bytes(keepalive.encoded({'clear': False, 'blocking_reasons': reasons}))
    with pytest.raises(ValueError, match='transient_identity_or_owned_cleanup_only'):
        keepalive.readmit_stage(previous, output, authority, cpu)
    assert not output.exists()
