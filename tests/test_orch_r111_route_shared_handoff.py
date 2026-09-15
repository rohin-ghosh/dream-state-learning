import json
import os
from pathlib import Path

import pytest

from gpu import orch_r111_route_boundary as boundary
from gpu import orch_r111_route_shared_handoff as handoff
from test_orch_r111_route_boundary import cycle
from test_orch_r111_route_shared_ready import fixture, fixture_v2


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


@pytest.fixture
def released(cycle, monkeypatch):
    root, current = cycle
    bounds = dict(cycles=512, native_calls=32768, parent_calls=16384, hard_end_unix=1789596240)
    plan = dict(physical=4, uuid=boundary.UUIDS[4], bounds=bounds, parent_wait_seconds=120)
    put(root / 'PLAN.json', plan)
    identities = [dict(pid=2147483646, uid=2524, start_ticks='1', boot_id='fixture'),
                  dict(pid=2147483647, uid=2524, start_ticks='2', boot_id='fixture')]
    directory = root / 'handoff'
    put(directory / 'REQUEST.json', dict(root=str(root), purpose='SHARED_ADOPTION', bounds=bounds,
        actor=identities[0], supervisor=identities[1]))
    saved = boundary.completed_boundary(root, current)
    saved.update(bounds=bounds, request=boundary.reference(directory / 'REQUEST.json'))
    put(directory / 'BOUNDARY.json', saved)
    put(directory / 'RELEASED.json', dict(status='RELEASED', original_plan=boundary.reference(root / 'PLAN.json'),
        boundary=boundary.reference(directory / 'BOUNDARY.json'), actor=identities[0], supervisor=identities[1]))
    monkeypatch.setattr(handoff.client, 'checkpoint_reference', lambda path: dict(path=str(path),
        path_sha256=boundary.sha(path), optimizer_path=str(Path(path).parent / 'optimizer_rng.pt')))
    return root, directory


def test_export_requires_actual_release_not_candidate(cycle):
    root, unused = cycle
    with pytest.raises(FileNotFoundError):
        handoff.export(root, root / 'never-created/RELEASED.json')
    assert not (root / 'R118_SHARED_HANDOFF_BRANCH.json').exists()


def test_export_contains_Main_required_fields_and_preserves_plan(released):
    root, directory = released
    before = (root / 'PLAN.json').read_bytes()
    result = handoff.export(root, directory / 'RELEASED.json')
    receipt = boundary.read(result['path'])
    assert receipt['root'] == str(root)
    assert receipt['next_cycle'] == 4
    assert {'root', 'bounds', 'release', 'predecessors', 'preserved_files', 'next_cycle'} <= set(receipt)
    assert {'PLAN.json', 'RESERVATIONS.jsonl', 'OWN_CARRY.json', 'cycle_0003/COMPLETE.json',
            'cycle_0003/checkpoint/CHECKPOINT.json', 'cycle_0003/checkpoint/optimizer_rng.pt'} <= set(receipt['preserved_files'])
    assert receipt['charged'] == dict(NATIVE=1, PARENT=1)
    assert receipt['nonowner_optimizer_preserved_not_merged'] is True
    assert (root / 'PLAN.json').read_bytes() == before
    assert handoff.export(root, directory / 'RELEASED.json') == result


def test_live_predecessor_prevents_speculative_certificate(released):
    root, directory = released
    request = boundary.read(directory / 'REQUEST.json')
    request['actor']['pid'] = os.getpid()
    put(directory / 'REQUEST.json', request)
    saved = boundary.read(directory / 'BOUNDARY.json')
    saved['request'] = boundary.reference(directory / 'REQUEST.json')
    put(directory / 'BOUNDARY.json', saved)
    receipt = boundary.read(directory / 'RELEASED.json')
    receipt['actor']['pid'] = os.getpid()
    receipt['boundary'] = boundary.reference(directory / 'BOUNDARY.json')
    put(directory / 'RELEASED.json', receipt)
    with pytest.raises(ValueError, match='predecessor_not_reaped'):
        handoff.export(root, directory / 'RELEASED.json')


def test_changed_charges_prevent_export(released):
    root, directory = released
    with (root / 'RESERVATIONS.jsonl').open('a') as stream:
        stream.write(json.dumps(dict(kind='NATIVE', number=2, cycle=4)) + '\n')
    with pytest.raises(ValueError, match='preserved_file_hash'):
        handoff.export(root, directory / 'RELEASED.json')


def test_template_preserves_live_plan_and_is_not_launchable(fixture_v2):
    from gpu import orch_r111_route_shared_ready as ready

    root, source, tests = fixture_v2
    plan = boundary.read(root / 'PLAN.json')
    plan['source_files'] = {}
    put(root / 'PLAN.json', plan)
    ready.publish(root, source, tests, version=2)
    reference = boundary.reference(root / 'SHARED_CLIENT_READY_V2.json')
    before = (root / 'PLAN.json').read_bytes()
    result = handoff.prepare_successor(root, reference)
    template = boundary.read(result['path'])
    assert template['bound_and_launchable'] is False
    assert template['plan']['shared_learner'] is None
    assert template['plan']['route_boundary_release'] is None
    assert template['plan']['bounds'] == plan['bounds']
    assert template['plan']['parent_wait_seconds'] == 120
    assert (root / 'PLAN.json').read_bytes() == before


def test_late_exit_reconciliation_preserves_error_and_never_signals(released, monkeypatch):
    root, directory = released
    (directory / 'RELEASED.json').unlink()
    request = boundary.read(directory / 'REQUEST.json')
    request['plan'] = boundary.reference(root / 'PLAN.json')
    put(directory / 'REQUEST.json', request)
    saved = boundary.read(directory / 'BOUNDARY.json')
    saved['request'] = boundary.reference(directory / 'REQUEST.json')
    put(directory / 'BOUNDARY.json', saved)
    put(directory / 'ERROR.json', dict(after_supervisor_termination=True, error_type='ValueError'))
    (directory / 'CONTROLLER.log').write_text('ValueError: actor_exit_no_SIGKILL\n')
    put(directory / 'AUTH.json', dict(request_sha256=boundary.sha(directory / 'REQUEST.json'),
        all_eight_ready=True, common_handoff_coordinated=True))
    monkeypatch.setattr(boundary.signal, 'pidfd_send_signal', lambda *unused: pytest.fail('no further signals'))
    before = (directory / 'ERROR.json').read_bytes()
    result = handoff.reconcile_exit(directory / 'REQUEST.json')
    receipt = boundary.read(result['path'])
    assert receipt['status'] == 'RELEASED'
    assert receipt['exact_exit_unix'] is None
    assert receipt['additional_signals'] == 0
    assert (directory / 'ERROR.json').read_bytes() == before


def test_uncharged_signal_diagnostic_archived_byte_exact_for_same_cursor(cycle):
    root, current = cycle
    start = root / 'cycle_0004/START.json'
    put(start, dict(cycle=4))
    saved = boundary.completed_boundary(root, current)
    diagnostic = start.parent / 'EPISODE_0.json'
    put(diagnostic, dict(terminal_reason='generation_failure', actor_calls=1, reads=[], routes=[],
        captures=[dict(response=None, error=dict(type='TimeoutError', message='owned_lifetime_signal'))]))
    before = diagnostic.read_bytes()
    result = handoff.preserve_uncharged_teardown(root, saved)
    archived = boundary.read(result['path'])
    assert Path(archived['archived']['path']).read_bytes() == before
    assert not diagnostic.exists()
    assert start.exists()
    assert boundary.completed_boundary(root, current) == saved
    assert archived['native_calls_added'] == archived['parent_calls_added'] == 0


def test_real_episode_or_changed_charges_must_not_be_moved(cycle):
    root, current = cycle
    start = root / 'cycle_0004/START.json'
    put(start, dict(cycle=4))
    saved = boundary.completed_boundary(root, current)
    diagnostic = start.parent / 'EPISODE_0.json'
    put(diagnostic, dict(terminal_reason='generation_failure', actor_calls=1, reads=[], routes=[],
        captures=[dict(response={'raw': 'actual native text'},
                       error=dict(type='TimeoutError', message='owned_lifetime_signal'))]))
    with pytest.raises(ValueError, match='exact_administrative_signal'):
        handoff.preserve_uncharged_teardown(root, saved)
    assert diagnostic.exists()
