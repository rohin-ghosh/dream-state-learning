from pathlib import Path

import pytest

from gpu import orch_r118_code_parallel_loop as loop
from test_orch_r118_code_parallel_handoff import ready, write


@pytest.fixture
def runtime(ready, tmp_path, monkeypatch):
    root, common = ready
    plan = dict(physical=2, gpu_uuid='GPU-synthetic', started_unix=0, hard_deadline_unix=loop.handoff.HARD_END + 3600,
        lease_end_unix=loop.handoff.HARD_END + 21600 + 3600, cycles=100, native_cap=8192, parent_cap=1000)
    write(root / 'PLAN.json', plan)
    source = tmp_path / 'frozen/source'
    source.mkdir(parents=True)
    (source / 'fixture.py').write_text('synthetic CPU fixture\n')
    monkeypatch.setattr(loop, 'SOURCE_ROOT', source)
    write(source.parent / 'SOURCE_SHA256.json', {'fixture.py': loop.io.sha(source / 'fixture.py')})
    write(source.parent / 'CPU_TESTS.json', dict(passed=True, cuda_initialized=False,
        source_manifest_sha256=loop.io.sha(source.parent / 'SOURCE_SHA256.json')))
    released = root / 'release/HANDOFF.json'
    write(released, dict(schema='R118_CODE_PARALLEL_RELEASE_V1', root=str(root),
        bounds={key: plan[key] for key in loop.client.BOUND_FIELDS}, all_original_processes_exited=True,
        native=dict(identity=dict(pid=1), boundary=loop.handoff.boundary(root, common)), guardian=dict(pid=2)))
    monkeypatch.setattr(loop.handoff, 'alive', lambda identity: False)
    own = dict(root=str(root), plan_sha256=loop.io.sha(root / 'PLAN.json'),
        common_root=str(common), checkpoint_sha256='a' * 64,
        source_manifest_sha256=loop.io.sha(source.parent / 'SOURCE_SHA256.json'),
        activation_directory=str(common / 'activations'), anchor_root=str(tmp_path / 'anchor'),
        anchor_task_ids=[f'ANCHOR_{index}' for index in range(42)])
    campaign = tmp_path / 'Main_CAMPAIGN.json'
    write(campaign, dict(schema=loop.consolidation.CAMPAIGN_SCHEMA, status='PREPARED_NOT_ACTIVE',
        root=str(common), mode='CUDA_INPLACE', first_generation=1,
        activation_directory=own['activation_directory'], deadline_unix=loop.handoff.TRAIN_END,
        pins={}, source_files={}))
    own['campaign'] = loop.handoff.ref(campaign)
    authorized = tmp_path / 'MAIN.json'
    write(authorized, dict(schema=loop.handoff.SCHEMA, status='MAIN_ALL8_COORDINATED_GO', action='LAUNCH',
        issued_unix=0, expires_unix=loop.handoff.TRAIN_END,
        branches={branch: own for branch in loop.io.BRANCHES}))
    service = root / 'parallel_service'
    loop.prepare_runtime(service, root, loop.handoff.ref(authorized), loop.handoff.ref(released), clock=lambda: 100)
    return service, root, common, source


def test_owner_command_uses_strict_guard_Main_injected_session_and_no_dispatch(runtime):
    service, root, common, source = runtime
    value = loop.io.read(service / 'RUNTIME.json')
    write(Path(value['handoff']['path']).with_name('OWNER_RELEASE.json'), dict(status='RELEASED',
        release=value['handoff'], bounds=dict(native_cap=8192, parent_cap=1000)))
    result = loop.owner_request(service, '/synthetic/python', clock=lambda: 100)
    assert result['command'] == ['/synthetic/python', '-B', '-m', loop.MODULE, 'guard', '--service', str(service)]
    assert result['bootstrap_path'] == str(service / 'FRESH_BOOTSTRAP.json')
    assert not any(name.startswith('R118_PARALLEL_') for name in result['env'])
    assert result['env']['CUDA_VISIBLE_DEVICES'] == ''
    assert not (service / 'GUARD_ONCE').exists()


def test_preparation_preserves_caps_carry_and_charges_without_launch(runtime):
    service, root, common, source = runtime
    value, released, plan = loop.validate_runtime(service, clock=lambda: 100)
    assert value['next_cycle'] == 2
    assert value['train_end_unix'] == loop.handoff.TRAIN_END
    assert value['hard_end_unix'] == loop.handoff.HARD_END
    assert released['native']['boundary']['carry']['reflection_settings']['effective_max_new_tokens'] == 3072
    assert not (service / 'LAUNCH.json').exists() and not (service / 'GUARD_ONCE').exists()
    assert plan['native_cap'] == 8192 and plan['parent_cap'] == 1000


@pytest.mark.parametrize('field,value', [('next_cycle', 3),
    ('hard_end_unix', loop.handoff.HARD_END + 1), ('anchor_task_ids', ['changed'])])
def test_runtime_tampering_rejected(runtime, field, value):
    service, root, common, source = runtime
    path = service / 'RUNTIME.json'
    document = loop.io.read(path)
    document[field] = value
    write(path, document)
    with pytest.raises(ValueError):
        loop.validate_runtime(service, clock=lambda: 100)


def test_post_handoff_new_charge_cannot_be_replayed(runtime):
    service, root, common, source = runtime
    write(root / 'reservations/C002_E0_ORIGINAL.json', dict(kind='NATIVE', split='TRAIN', status='STARTED'))
    with pytest.raises(ValueError, match='post_handoff_reservation'):
        loop.validate_runtime(service, clock=lambda: 100)


def test_running_or_stale_common_state_cannot_activate(runtime):
    service, root, common, source = runtime
    value = loop.io.read(common / 'STATE.json')
    value['generation'] += 1
    write(common / 'STATE.json', value)
    with pytest.raises(ValueError, match='stale_launch_checkpoint'):
        loop.validate_runtime(service, clock=lambda: 100)


def test_same_STATE_but_new_sleep_START_cannot_activate(runtime):
    service, root, common, source = runtime
    write(common / 'generation_000001/sleep/START.json', dict(started=True))
    with pytest.raises(ValueError, match='running_or_failed_sleep'):
        loop.validate_runtime(service, clock=lambda: 100)


def test_source_mutation_rejected_without_weakening_guard(runtime):
    service, root, common, source = runtime
    (source / 'fixture.py').write_text('different bytes')
    with pytest.raises(ValueError, match='frozen_source_closure'):
        loop.validate_runtime(service, clock=lambda: 100)


def test_old_actor_alive_prevents_launch(runtime, monkeypatch):
    service, root, common, source = runtime
    monkeypatch.setattr(loop.handoff, 'alive', lambda identity: True)
    with pytest.raises(ValueError, match='actual_CODE_predecessor_release'):
        loop.validate_runtime(service, clock=lambda: 100)


def test_preparation_cannot_overwrite_previous_attempt(runtime):
    service, root, common, source = runtime
    value = loop.io.read(service / 'RUNTIME.json')
    with pytest.raises(ValueError, match='new_service'):
        loop.prepare_runtime(service, root, value['authorization'], value['handoff'], clock=lambda: 100)
