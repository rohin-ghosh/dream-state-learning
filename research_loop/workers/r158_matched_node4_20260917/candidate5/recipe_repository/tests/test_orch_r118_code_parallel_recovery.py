from copy import deepcopy
from pathlib import Path

import pytest

from gpu import orch_r118_code_parallel_recovery as recovery
from gpu import orch_r118_code_parallel_recovery_final as timer


def write(path, value):
    recovery.io.write(path, value, replace=path.exists())


@pytest.fixture
def failed(tmp_path, monkeypatch):
    root = tmp_path / 'F3'
    service = root / 'parallel/service_2'
    release_dir = root / 'release'
    source = tmp_path / 'source'
    common = tmp_path / 'common'
    campaign = tmp_path / 'campaign'
    final_root = root / 'final_2'
    source.mkdir()
    (source / 'actor.py').write_text('frozen actor\n')
    write(tmp_path / 'MANIFEST.json', {'actor.py': recovery.io.sha(source / 'actor.py')})
    manifest = recovery.handoff.ref(tmp_path / 'MANIFEST.json')
    write(tmp_path / 'CPU.json', dict(passed=True, cuda_initialized=False,
        source_manifest_sha256=manifest['sha256']))
    checkpoint = tmp_path / 'CHECKPOINT.json'
    optimizer = tmp_path / 'optimizer.pt'
    checkpoint.write_text('frozen checkpoint')
    optimizer.write_bytes(b'frozen optimizer')
    monkeypatch.setattr(recovery, 'CHECKPOINT_SHA256', recovery.io.sha(checkpoint))
    state = dict(generation=1, checkpoint=dict(path=str(checkpoint), path_sha256=recovery.CHECKPOINT_SHA256,
        optimizer_path=str(optimizer), optimizer_path_sha256=recovery.io.sha(optimizer)))
    for name, value in (('STATE.json', state), ('CONFIG.json', {}), ('ADOPTION.json', {}), ('INITIALIZED.json', {})):
        write(common / name, value)
    write(root / 'SHARED_ACTIVATION.json', dict(shared_learner=dict(branch='F3')))
    write(root / 'reservations/C022_E0.json', dict(kind='NATIVE', split='TRAIN'))
    preserved = {'reservations/C022_E0.json': recovery.io.sha(root / 'reservations/C022_E0.json')}
    write(release_dir / 'HANDOFF.json', dict(schema='R118_CODE_PARALLEL_RELEASE_V1', status='RELEASED',
        native=dict(boundary=dict(kind='SETTLED_PENDING_CONSOLIDATION', state=state)),
        all_original_processes_exited=True))
    envelope = dict(root=str(root), release=recovery.handoff.ref(release_dir / 'HANDOFF.json'),
        preserved_files=preserved, predecessors=[dict(pid=1, start_ticks=1)],
        bounds=dict(native_used=1, parent_used=0, train_end_unix=1789491600, hard_end_unix=1789491720),
        next_cycle=23)
    write(release_dir / 'OWNER_RELEASE.json', envelope)
    owner = dict(handoff=recovery.handoff.ref(release_dir / 'OWNER_RELEASE.json'),
        bootstrap_path=str(service / 'FRESH_BOOTSTRAP.json'),
        command=['/python', '-B', '-m', 'gpu.orch_r118_code_parallel_loop', 'guard', '--service', str(service)],
        source_files={str(source / 'actor.py'): recovery.io.sha(source / 'actor.py')},
        boundary=dict(settled_pending_consolidation=dict(path='original_pending', sha256='p')))
    write(service / 'OWNER_REQUEST.json', owner)
    session = campaign / 'SESSION.json'
    write(session, dict(owners={'F3': owner}, pins={name: recovery.io.sha(common / name)
        for name in ('STATE.json', 'CONFIG.json', 'ADOPTION.json', 'INITIALIZED.json')}))
    monkeypatch.setattr(recovery, 'SESSION_SHA256', recovery.io.sha(session))
    write(campaign / 'SESSION.dispatch/FAILED.json', dict(session_sha256=recovery.SESSION_SHA256, retry_allowed=False))
    runtime = dict(root=str(root), common_root=str(common), handoff=envelope['release'],
        source_root=str(source), source_manifest=manifest, cpu_tests=recovery.handoff.ref(tmp_path / 'CPU.json'),
        hard_end_unix=1789491720)
    write(service / 'RUNTIME.json', runtime)
    native, guard = dict(pid=2, start_ticks='2'), dict(pid=3, start_ticks='3')
    write(service / 'LAUNCH.json', dict(identity=native, guardian=guard))
    write(service / 'GUARD_TERMINAL.json', dict(identity=native, native_alive=False, returncode=1))
    (service / 'GUARD_ONCE').mkdir()
    (service / 'NATIVE_ONCE').mkdir()
    write(service / 'FINAL_STAGER_COMPLETE.json', dict(final_root=str(final_root)))
    write(final_root / 'PLAN.json', dict(native_cap=8))
    write(final_root / 'CPU_DISPATCH.json', dict(identity=dict(pid=4), module=timer.final.MODULE))
    monkeypatch.setattr(recovery.final, 'unused_allocation', lambda path: recovery.io.read(Path(path) / 'PLAN.json'))
    monkeypatch.setattr(recovery.handoff, 'alive', lambda identity: identity['pid'] == 4)
    return root, service, session


def test_preparation_preserves_failed_service_and_pending_owner(failed):
    root, service, session = failed
    before = {str(path): recovery.io.sha(path) for path in root.rglob('*') if path.is_file()}
    prepared = recovery.prepare(service, session, root / 'recovery', root / 'parallel/service_3', clock=lambda: 100)
    assert all(recovery.io.sha(path) == value for path, value in before.items())
    assert prepared['GPU_started'] is False and prepared['next_cycle'] == 23
    assert not Path(prepared['service']).exists()
    envelope = recovery.handoff.checked(prepared['owner']['handoff'])
    assert [item['pid'] for item in envelope['predecessors']] == [1, 2, 3]
    assert prepared['owner']['command'][-1] == prepared['service']
    assert prepared['collection_end_unix'] == 1789491300


@pytest.mark.parametrize('marker', ['FRESH_BOOTSTRAP.json', 'BOOTSTRAP.json', 'ACTOR_READY.json'])
def test_reject_bootstrapped_actor_not_just_terminal(failed, marker):
    root, service, session = failed
    write(service / marker, {})
    with pytest.raises(ValueError, match='prebootstrap'):
        recovery.snapshot(service, session, clock=lambda: 100)


def test_reject_started_bootstrap_before_completion(failed):
    root, service, session = failed
    write(session.parent / 'SESSION.dispatch/F3.BOOTSTRAP_START.json', {})
    with pytest.raises(ValueError, match='prebootstrap'):
        recovery.snapshot(service, session, clock=lambda: 100)


def test_reject_added_reservation_even_if_failed(failed):
    root, service, session = failed
    write(root / 'reservations/C023_NEW.json', dict(kind='NATIVE', split='TRAIN', status='FAILED'))
    with pytest.raises(ValueError, match='no_new_calls'):
        recovery.snapshot(service, session, clock=lambda: 100)


def test_reject_changed_common_state(failed):
    root, service, session = failed
    common = Path(recovery.io.read(service / 'RUNTIME.json')['common_root'])
    write(common / 'STATE.json', dict(generation=2))
    with pytest.raises(ValueError, match='same_committed'):
        recovery.snapshot(service, session, clock=lambda: 100)


def test_reject_live_predecessor(failed, monkeypatch):
    root, service, session = failed
    monkeypatch.setattr(recovery.handoff, 'alive', lambda identity: True)
    with pytest.raises(ValueError, match='must_exit'):
        recovery.snapshot(service, session, clock=lambda: 100)


def test_actual_optimizer_bytes_not_just_unchanged_state(failed):
    root, service, session = failed
    (root.parent / 'optimizer.pt').write_bytes(b'modified optimizer')
    with pytest.raises(ValueError, match='checkpoint_or_optimizer'):
        recovery.snapshot(service, session, clock=lambda: 100)


def test_preserve_original_once_markers_and_preparation_deadline(failed):
    root, service, session = failed
    with pytest.raises(ValueError, match='bounded_CPU'):
        recovery.snapshot(service, session, clock=lambda: recovery.PREP_END)
    (service / 'GUARD_ONCE').rmdir()
    with pytest.raises(ValueError, match='once_markers'):
        recovery.snapshot(service, session, clock=lambda: 100)


def test_no_reuse_failed_or_existing_service(failed):
    root, service, session = failed
    with pytest.raises(ValueError, match='new_owned'):
        recovery.prepare(service, session, root / 'recovery', service, clock=lambda: 100)
    assert not (root / 'recovery').exists()


def test_parallel_timer_validation_no_signal(failed):
    root, service, session = failed
    final_root = root / 'final_2'
    command = [b'/python', b'-B', b'-m', timer.final.MODULE.encode(), b'schedule', b'--root', str(final_root).encode()]
    assert timer.validate_timer(final_root, dict(pid=4), clock=lambda: 100, command=command)['identity']['pid'] == 4
    with pytest.raises(ValueError, match='exact_parallel_FINAL'):
        timer.validate_timer(final_root, dict(pid=1519259), clock=lambda: 100, command=command)
    with pytest.raises(ValueError, match='schedule_command'):
        timer.validate_timer(final_root, dict(pid=4), clock=lambda: 100, command=command[:-1]+[b'/foreign'])


def test_failed_recovery_timer_requires_both_era_identities_dead(failed, monkeypatch):
    root, service, session = failed
    proof = recovery.snapshot(service, session, clock=lambda: 100)
    write(root / 'proof.json', proof)
    runtime = recovery.io.read(service / 'RUNTIME.json')
    released = recovery.handoff.checked(runtime['handoff'])
    released['failed_startup_recovery'] = recovery.handoff.ref(root / 'proof.json')
    write(root / 'new_release.json', released)
    write(service / 'RUNTIME.json', dict(runtime, handoff=recovery.handoff.ref(root / 'new_release.json')))
    monkeypatch.setattr(timer.handoff, 'alive', lambda identity: identity['pid'] == 2)
    with pytest.raises(ValueError, match='stays_exited'):
        timer.rebind(service, clock=lambda: 100)
