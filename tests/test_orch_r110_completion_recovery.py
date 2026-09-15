import json

import pytest

from gpu import orch_r110_completion_recovery as recovery


@pytest.fixture
def saved_sleep(tmp_path, monkeypatch):
    def write(name, document):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(document))
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', '')
    monkeypatch.setattr(recovery.run, 'validate', lambda root: {})
    monkeypatch.setattr(recovery.run.seed, 'validate', lambda document: document)
    monkeypatch.setattr(recovery.run, 'SOURCE_ROOT', tmp_path)
    write('READY.json', {})
    write('PLAN.json', {})
    write('REPAIR.json', {})
    write('INITIAL.json', dict(binding_sha256='seed', optimizer_summary=dict(step=8932)))
    write('cycle1/collection/COMPLETE.json', dict(status='COMPLETE'))
    write('cycle1/sleep/FAILED.json', dict(status='FAILED', phase='sleep', cycle=1,
        error_type='TypeError', error="dict() got multiple values for keyword argument 'started_unix'"))
    write('cycle1/sleep/REQUEST.json', dict(process=['different_boot', 99999999, 1]))
    write('cycle1/sleep/SLEEP.json', dict(optimizer_updates=2))
    write('cycle1/sleep/carry/CARRY.json', dict(generation=1, parent_binding_sha256='seed',
        optimizer_summary=dict(step=8934), adapter=dict(state_sha256='child')))
    for update in range(1, 3):
        write(f'cycle1/sleep/UPDATES/{update:06d}.json', dict(update=update))
    (tmp_path / 'RESERVATIONS.jsonl').write_text('\n'.join(
        json.dumps(dict(kind=kind)) for kind in ['NATIVE'] * 8 + ['PARENT'] * 3))
    write('TERMINAL.json', dict(status='FAILED'))
    return tmp_path, write


def test_recovery_binds_saved_updates_and_original_calls(saved_sleep):
    root, _ = saved_sleep
    evidence = recovery.recovery_evidence(root)
    assert evidence['preserved_updates'] == 2 and evidence['optimizer_step'] == 8934
    assert evidence['next_phase'] == 'cycle1/readout'
    assert evidence['repeated_training_updates'] == 0


@pytest.mark.parametrize('name,document,reason', [
    ('cycle1/sleep/FAILED.json', dict(status='FAILED', phase='sleep', cycle=1,
        error_type='RuntimeError', error='CUDA OOM'), 'exact_metadata_only_failure'),
    ('cycle1/sleep/carry/CARRY.json', dict(generation=1, parent_binding_sha256='seed',
        optimizer_summary=dict(step=8932), adapter=dict(state_sha256='child')), 'all_updates_saved_without_reset'),
    ('cycle1/sleep/UPDATES/000002.json', dict(update=3), 'continuous_update_receipts'),
    ('LAUNCH_1_readout.json', {}, 'no_repeated_calls_or_readout'),
    ('cycle1/sleep/COMPLETE.json', {}, 'original_evidence_preserved'),
])
def test_recovery_rejects_unsafe_states(saved_sleep, name, document, reason):
    root, write = saved_sleep
    write(name, document)
    with pytest.raises(ValueError, match=reason):
        recovery.recovery_evidence(root)


def test_recovery_preserves_terminal_then_launches_only_remaining_work(saved_sleep, monkeypatch):
    root, write = saved_sleep
    original = (root / 'TERMINAL.json').read_bytes()
    recovery.prepare(root)
    write('recovery_v2/PUBLICATION.json', dict(commit='published'))
    dispatched = []
    monkeypatch.setattr(recovery.supervisor, 'supervise', lambda path, recovery: dispatched.append((path, recovery)))
    recovery.resume(root)
    assert (root / 'recovery_v2/ORIGINAL_TERMINAL.json').read_bytes() == original
    assert not (root / 'TERMINAL.json').exists()
    assert (root / 'RECOVERY_V2_READY.json').exists()
    assert dispatched == [(root, True)]


def test_recovery_refuses_changed_reservations(saved_sleep):
    root, write = saved_sleep
    recovery.prepare(root)
    write('recovery_v2/PUBLICATION.json', {})
    with (root / 'RESERVATIONS.jsonl').open('a') as stream:
        stream.write('\n' + json.dumps(dict(kind='NATIVE')))
    with pytest.raises(ValueError, match='no_repeated_calls_or_readout'):
        recovery.resume(root)
