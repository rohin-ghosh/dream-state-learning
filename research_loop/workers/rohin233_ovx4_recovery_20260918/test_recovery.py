from copy import deepcopy
import hashlib

import pytest

from research_loop.workers.rohin233_ovx4_recovery_20260918.recovery_contract import allocation_guard, restore_contract
from research_loop.workers.rohin233_ovx4_recovery_20260918.recovery_contract import relocated_reference
from research_loop.workers.rohin233_ovx4_recovery_20260918.base_epoch import migrate, retained_summary
from research_loop.workers.rohin233_ovx4_recovery_20260918.transport_proxy import validate_deadline
from research_loop.workers.rohin233_ovx4_recovery_20260918.prepare_p3 import device_minor
from research_loop.workers.rohin233_ovx4_recovery_20260918.feedback_recovery import pending_paths


def test_incremental_feedback_does_not_rescan_processed_payload(tmp_path):
    target = tmp_path / 'attempts/only/RESULT.json'
    target.parent.mkdir(parents=True)
    target.write_text('{"synthetic":true}')
    pending = pending_paths(tmp_path, {})
    assert len(pending) == 1
    assert pending_paths(tmp_path, dict(pending)) == []
    target.write_text('{"changed":true}')
    with pytest.raises(ValueError, match='immutable_future_result_changed'):
        pending_paths(tmp_path, dict(pending))


def test_large_record_framing_keeps_aggregate_and_hash_guards(tmp_path, monkeypatch):
    import base64
    import json
    from research_loop.workers.rohin221_continuous_caption_20260918 import journal_bundle, journal_transport
    from research_loop.workers.rohin233_ovx4_recovery_20260918.transport_entry import configure
    from gpu import ny_caption_data as data
    monkeypatch.setattr(journal_bundle, 'MAX_BYTES', journal_bundle.MAX_BYTES)
    monkeypatch.setattr(journal_transport, 'MAX_BYTES', journal_transport.MAX_BYTES)
    configure()
    assert journal_bundle.MAX_BYTES == journal_transport.MAX_BYTES == 33554432
    assert journal_transport.MAX_TOTAL_BYTES == 67108864
    record = dict(index=0, journal_id='synthetic', kind='COMMITTED', previous_sha256=None,
        document=dict(padding='x' * (9 * 1024 * 1024)))
    record['sha256'] = data.digest(record)
    raw = json.dumps(record).encode()
    assert journal_bundle.checked(raw, 'synthetic')['sha256'] == record['sha256']
    altered = raw.replace(b'COMMITTED', b'COMMITTEZ', 1)
    with pytest.raises(Exception):
        journal_bundle.checked(altered, 'synthetic')


def test_uuid_device_minor_not_nvidia_enumeration_index():
    xml = '<nvidia_smi_log><gpu><uuid>intended</uuid><minor_number>3</minor_number></gpu><gpu><uuid>other</uuid><minor_number>0</minor_number></gpu></nvidia_smi_log>'
    assert device_minor(xml, 'intended') == 3
    with pytest.raises(AssertionError, match='exact_unique'):
        device_minor(xml, 'absent')


def test_transport_renewal_is_finite_not_lease_extension():
    validate_deadline(2300, 23900, 1000)
    validate_deadline(30001, 60000, 1000)
    for deadline, lease, now in [(2301, 23900, 1000), (1000, 23900, 1000)]:
        with pytest.raises(ValueError, match='finite_transport'):
            validate_deadline(deadline, lease, now)


def session():
    return dict(phase='COMPLETE', life_root='/synthetic/root', scene_ids=[{'scene': 'synthetic'}],
        session_binding={'journal': 'synthetic'}, source_mode='NATIVE_JOURNAL', format_policy='same',
        seen=['first', 'second'], game={'pixels': [1]}, policy={'attempts': 2})


def test_exact_restore_keeps_novelty_dedup_and_source():
    original = session()
    assert restore_contract(original, deepcopy(original))['seen_count'] == 2
    for field, value in [('seen', []), ('game', {'pixels': []}), ('session_binding', {}), ('phase', 'PENDING')]:
        changed = deepcopy(original)
        changed[field] = value
        with pytest.raises(ValueError):
            restore_contract(original, changed)


def test_expiry_and_other_owner_devices_fail_closed():
    config = dict(deadline_unix=2000, allocation=dict(conservative_lease_boundary_unix=23600,
        authorized_job_end_unix=2000, lease_source_sha256='a'*64, authority_sha256='b'*64))
    allocation_guard(config, 2, now=1000)
    for physical in (0, 1, 8):
        with pytest.raises(ValueError):
            allocation_guard(config, physical, now=1000)
    with pytest.raises(ValueError):
        allocation_guard(config, 2, now=2001)
    config['allocation']['conservative_lease_boundary_unix'] = 23599
    with pytest.raises(ValueError):
        allocation_guard(config, 2, now=1000)


def test_equal_horizon_renewal_preserves_history_and_counts():
    backend = dict(identity=dict(visible_device='assigned', all_parameters_frozen=True, optimizer_created=False, lora_parameters=0))
    previous = dict(pending=None, stage='THINK', opportunity=130, attempt=0, completed_opportunities=129,
        total_generated_tokens=101220, binding=dict(plan=dict(opportunities=512)), backend_state=backend,
        history=[{'synthetic': 'retained'}], events=[dict(source=dict(request_id='old'))], generations=[], think_source=None)
    scorer = dict(phase='COMPLETE', session_binding=dict(controller=previous['binding'], backend=backend),
        seen=['old'], game={'pixels': [1]}, policy={'attempts': 1})
    state, restored = migrate(previous, scorer, deepcopy(backend), deepcopy(previous['binding']), 'assigned', 'renewed')
    assert retained_summary(state, restored) == retained_summary(previous, scorer)
    assert previous['history'] == state['history'] and state['binding']['plan']['opportunities'] == 512
    assert not state['source_adoptions'][-1]['fresh_context_reset']
    previous['pending'] = {'unfinished': True}
    with pytest.raises(Exception):
        migrate(previous, scorer, backend, previous['binding'], 'assigned', 'bad')


def test_byte_identical_source_relocation_is_not_identity_weakening(tmp_path):
    original = tmp_path / 'old.py'
    moved = tmp_path / 'new.py'
    original.write_text('source = 1\n')
    moved.write_bytes(original.read_bytes())
    reference = dict(path=str(original), bytes=original.stat().st_size,
        sha256=hashlib.sha256(original.read_bytes()).hexdigest())
    actual = dict(reference, path=str(moved))
    assert relocated_reference(reference, actual) == actual
    moved.write_text('source = 2\n')
    with pytest.raises(ValueError, match='actual_relocated_source_hash'):
        relocated_reference(reference, actual)
    changed = dict(actual, sha256='f'*64)
    with pytest.raises(ValueError, match='byte_identical_reference'):
        relocated_reference(reference, changed)


def test_controller_reference_without_optional_size_still_checks_bytes(tmp_path):
    path = tmp_path / 'runtime.py'
    path.write_text('retained = True\n')
    reference = dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    assert relocated_reference(reference, reference) == reference
    path.write_text('retained = False\n')
    with pytest.raises(ValueError, match='actual_relocated_source_hash'):
        relocated_reference(reference, reference)
