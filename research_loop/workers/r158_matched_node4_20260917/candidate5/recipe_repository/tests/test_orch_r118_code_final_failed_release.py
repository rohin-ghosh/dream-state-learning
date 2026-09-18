from copy import deepcopy
from pathlib import Path

import pytest

from gpu import orch_r118_code_final_failed_release as final


@pytest.fixture
def fixture(tmp_path, monkeypatch):
    original = tmp_path / 'life'
    root = original / 'parallel_v4/final_failed_recovery'
    old = original / 'parallel_v4/final_3'
    old.mkdir(parents=True)
    root.mkdir()
    write = final.io.write
    write(original / 'reservations/old.json', {'charged': True})
    hashes = {'reservations/old.json': final.io.sha(original / 'reservations/old.json')}
    proof = tmp_path / 'proof.json'
    write(proof, dict(root=str(original), new_calls=0, optimizer_steps=0, predecessors=[{'pid': 1}]))
    released = tmp_path / 'release.json'
    write(released, dict(native=dict(boundary=dict(preserved_files=hashes))))
    terminal = tmp_path / 'terminal.json'
    write(terminal, dict(native_alive=False))
    record = dict(original_root=str(original), proof=final.handoff.ref(proof),
        release=final.handoff.ref(released), predecessors=[{'pid': 1}], guard_terminal=final.handoff.ref(terminal),
        unused_service=str(original / 'service4'), old_root=str(old), old_timer={'pid': 2})
    write(root / 'PLAN.json', dict(original_root=str(original)))
    write(root / 'FAILED_RELEASE_FACTS.json', record)
    live = {2, 3}
    monkeypatch.setattr(final.handoff, 'alive', lambda identity: identity['pid'] in live)
    monkeypatch.setattr(final.handoff, 'ledger', lambda unused: ({'preserved': hashes}, []))
    monkeypatch.setattr(final, 'functions', lambda: {'validate_plan': lambda unused: None})
    write(root / 'REPLACEMENT_ARMED.json', dict(identity={'pid': 3}, plan=final.handoff.ref(root / 'PLAN.json'),
        facts=final.handoff.ref(root / 'FAILED_RELEASE_FACTS.json')))
    return root, original, old, live


def test_factual_exit_never_needs_or_fabricates_clean_release(fixture):
    root, original, old, live = fixture
    assert final.facts(root)['predecessors'] == [{'pid': 1}]
    assert not list(original.rglob('CLEAN_RELEASE.json'))


def test_live_predecessor_blocks(fixture):
    root, original, old, live = fixture
    live.add(1)
    with pytest.raises(ValueError, match='all_failed_guard_native_exited'):
        final.facts(root)


@pytest.mark.parametrize('name', ['ATTEMPT_ONCE', 'LAUNCH.json', 'reservations/FINAL.json'])
def test_any_sibling_attempt_blocks(fixture, name):
    root, original, old, live = fixture
    path = old / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()
    with pytest.raises(ValueError, match='no_sibling_FINAL_attempt'):
        final.facts(root)


def test_changed_charge_blocks(fixture):
    root, original, old, live = fixture
    (original / 'reservations/old.json').write_text('{}')
    with pytest.raises(ValueError, match='preserved_pending_and_charges'):
        final.facts(root)


def test_late_service4_launch_blocks(fixture):
    root, original, old, live = fixture
    final.io.write(original / 'service4/LAUNCH.json', {})
    with pytest.raises(ValueError, match='no_late_service4_actor'):
        final.facts(root)


def test_no_committed_custody_cannot_release(fixture):
    with pytest.raises(FileNotFoundError):
        final.validate_release(fixture[0])


def test_dead_replacement_never_stops_old(fixture):
    root, original, old, live = fixture
    live.remove(3)
    with pytest.raises(ValueError, match='replacement_custody_live'):
        final.transfer(root, clock=lambda: 100, cancel=lambda *args, **kwargs: pytest.fail('stop'))
    assert 2 in live


def test_transfer_two_phase_only_after_armed_and_exit(fixture):
    root, original, old, live = fixture
    def cancel(path, identity, **kwargs):
        assert path == old and identity == {'pid': 2}
        assert (root / 'TRANSFER_INTENT.json').exists()
        assert not (root / 'TRANSFER_COMMITTED.json').exists()
        live.remove(2)
        return {'actual_exit': True}
    final.transfer(root, clock=lambda: 100, cancel=cancel)
    assert final.validate_release(root)['fabricated_clean_release'] is False
    with pytest.raises(ValueError, match='no_transfer_retry'):
        final.transfer(root, clock=lambda: 100, cancel=cancel)


def test_cutoff_never_extended(fixture):
    with pytest.raises(ValueError, match='transfer_before1650'):
        final.transfer(fixture[0], clock=lambda: final.TRANSFER_END)


def test_original_evaluator_and_decoder_retained():
    functions = final.functions()
    assert functions['evaluate'].__code__ is final.previous.original.evaluate.__code__
    assert functions['final_tasks'].__code__ is final.previous.original.final_tasks.__code__
    assert functions['validate_binding'].__code__ is final.previous.original.validate_binding.__code__
    assert functions['DECODER'] == final.previous.original.DECODER
    assert functions['release'] is final
    assert functions['MODULE'] == final.MODULE
