import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import tarfile

import pytest

from gpu import orch_r136_node4_launch as node4


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


@pytest.fixture
def route(tmp_path):
    root = tmp_path / 'route'
    lane = root / 'lease_r120_v2/campaign_node1_7'
    saved = dict(resident_pid=123, adapter=None, optimizer_updates=0, own_memory='retained context',
                 native_completed=12, finished_unix=50)
    put(lane/'CHECKPOINT_C42.json', saved)
    put(lane/'READY.json', dict(learned=False))
    put(lane/'RECOVERY.json', dict(first_cycle=41))
    put(lane/'sleeps/0042.json', dict(context_only=True, weight_updates=0))
    rows = [dict(kind='NATIVE', number=10, cycle=40, reserved_unix=10),
            dict(kind='NATIVE', number=11, cycle=41, reserved_unix=20),
            dict(kind='NATIVE', number=12, cycle=42, reserved_unix=30),
            dict(kind='PARENT', number=8, cycle=42, reserved_unix=40)]
    (root/'RESERVATIONS.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in rows))
    for number, cycle in ((11, 41), (12, 42)):
        put(lane/f'native/CALL_{number:06d}.json', dict(number=number, cycle=cycle, status='COMPLETE', finished_unix=45))
    put(lane/'PARENT_00008.json', dict(number=8, status='MISSING', observed_unix=44))
    return root, lane


@pytest.mark.parametrize('physical', [0, 2, -1, 8, True, False, '1', 1.0])
def test_protected_and_malformed_slots_never_admitted(physical):
    with pytest.raises(ValueError, match='protected'):
        node4.allocation(physical)


@pytest.mark.parametrize('physical', [1, 3, 4, 5, 6, 7])
def test_only_owned_slots_have_device_map(physical):
    assert node4.allocation(physical).startswith('GPU-')


@pytest.mark.parametrize('physical', [0, 2, 4, 5, 6, 7])
def test_unreviewed_frontiers_are_not_route_retirement(physical):
    with pytest.raises(ValueError):
        node4.route_root(physical)


def test_exact_saved_route_boundary(route):
    root, lane = route
    boundary = node4.route_frontier(root, 'CHECKPOINT_C42.json', {'pid': 123})
    assert boundary['cycle'] == 42
    assert boundary['saved']['own_memory'] == 'retained context'
    assert boundary['adapter'] == 'ABSENT_FROZEN_BASE'
    assert 'NO_BITWISE' in boundary['live_generation_rng']


@pytest.mark.parametrize('patch,reason', [({'optimizer_updates': 1}, 'BASE_context'),
    ({'adapter': {}}, 'BASE_context'), ({'resident_pid': 124}, 'BASE_context'),
    ({'native_completed': 11}, 'saved_cursor')])
def test_invalid_saved_state_rejected(route, patch, reason):
    root, lane = route
    path = lane/'CHECKPOINT_C42.json'
    put(path, dict(node4.read(path), **patch))
    with pytest.raises(ValueError, match=reason):
        node4.route_frontier(root, path.name, {'pid': 123})


@pytest.mark.parametrize('cycle,clock,reason', [(43, 49, 'later_cycle'), (42, 51, 'charge_after')])
def test_later_reservation_is_not_safe_boundary(route, cycle, clock, reason):
    root, lane = route
    with (root/'RESERVATIONS.jsonl').open('a') as output:
        output.write(json.dumps(dict(kind='NATIVE', number=13, cycle=cycle, reserved_unix=clock))+'\n')
    with pytest.raises(ValueError, match=reason):
        node4.route_frontier(root, 'CHECKPOINT_C42.json', {'pid': 123})


@pytest.mark.parametrize('patch', [{'status': 'STARTED'}, {'finished_unix': 51}, {'cycle': 43}])
def test_later_or_partial_call_rejected(route, patch):
    root, lane = route
    path = lane/'native/CALL_000012.json'
    put(path, dict(node4.read(path), **patch))
    with pytest.raises(ValueError, match='later_or_incomplete'):
        node4.route_frontier(root, 'CHECKPOINT_C42.json', {'pid': 123})


def test_missing_call_rejected(route):
    root, lane = route
    (lane/'native/CALL_000012.json').unlink()
    with pytest.raises(ValueError, match='all_current_native'):
        node4.route_frontier(root, 'CHECKPOINT_C42.json', {'pid': 123})


def test_missing_parent_rejected(route):
    root, lane = route
    (lane/'PARENT_00008.json').unlink()
    with pytest.raises(ValueError, match='all_parent'):
        node4.route_frontier(root, 'CHECKPOINT_C42.json', {'pid': 123})


def test_learned_actor_never_retired(route):
    root, lane = route
    put(lane/'READY.json', dict(learned=True))
    with pytest.raises(ValueError, match='no_training'):
        node4.route_frontier(root, 'CHECKPOINT_C42.json', {'pid': 123})


def test_archives_raw_bytes_and_symlink_without_following(tmp_path):
    root = tmp_path/'state'
    root.mkdir()
    (root/'raw.bin').write_bytes(b'\x00retained\xff')
    outside = tmp_path/'outside'
    outside.write_text('not copied by link')
    (root/'link').symlink_to(outside)
    result = node4.snapshot([root], tmp_path/'archive.tar')
    assert result['files'][str(root/'link')]['kind'] == 'symlink'
    assert str(outside) not in result['files']
    with tarfile.open(tmp_path/'archive.tar') as archive:
        assert archive.extractfile(str(root/'raw.bin').lstrip('/')).read() == b'\x00retained\xff'
    with pytest.raises(FileExistsError):
        node4.snapshot([root], tmp_path/'archive.tar')


def test_actual_owned_CPU_process_can_pause_and_resume_without_killing():
    process = subprocess.Popen([sys.executable, '-c', 'import time; print("READY", flush=True); time.sleep(30)'],
                               stdout=subprocess.PIPE, text=True)
    descriptor = os.pidfd_open(process.pid)
    try:
        assert select.select([process.stdout], [], [], 5)[0]
        assert process.stdout.readline() == 'READY\n'
        identity = node4.custody.identity(process.pid)
        node4.custody.pause(identity, descriptor)
        assert node4.custody.stopped(identity)
        signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        assert process.poll() is None
    finally:
        signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        process.terminate()
        process.wait(timeout=5)
        os.close(descriptor)
        process.stdout.close()


def test_cannot_signal_changed_identity(monkeypatch):
    monkeypatch.setattr(node4.custody, 'identity', lambda pid: {'pid': pid, 'start_ticks': 'new'})
    with pytest.raises(ValueError, match='identity_drift'):
        node4.custody.same({'pid': 123, 'start_ticks': 'old'})


@pytest.fixture
def code(tmp_path):
    root = tmp_path/'code'
    lane = root/'campaign_code_parent'
    put(root/'CARRY_PRIVATE.json', dict(own_context='old', lessons=['ancestral']))
    rows = []
    for cycle in (101, 102):
        for kind, phase in (('NATIVE', 'segment1'), ('PARENT', 'parent2')):
            identifier = f'cycle{cycle}_{phase}'
            row = dict(cell_id=identifier, cycle=cycle, kind=kind, phase=phase)
            rows.append(row)
            put(lane/'cells'/f'{identifier}.json', dict(row, started_unix=10,
                finished_unix=20, status='COMPLETE' if kind == 'NATIVE' else 'PENDING', lesson=''))
            if kind == 'PARENT':
                put(root/'parent_queue'/f'{identifier}.request.json', dict(id=identifier))
    put(root/'schedule.json', rows)
    put(root/'cohorts.json', dict(chunks=[dict(first_cycle=101, last_cycle=164, chunk=0,
        reservations=node4.ref(root/'schedule.json'))]))
    put(root/'PLAN.json', dict(adapter=None, optimizer_updates=0, parent_cadence='EPISODE',
        parent_wait_seconds=0, cohorts=node4.ref(root/'cohorts.json'),
        inputs={'context': node4.ref(root/'CARRY_PRIVATE.json')}))
    put(lane/'CYCLE_102_COMPLETE.json', dict(cycle=102, status='COMPLETE', updates=0,
        no_adapter={'optimizer_updates': 0}, finished_unix=30))
    put(lane/'CONTEXT_DISTILLATION_C102.json', dict(status='COMPLETE', weight_updates=0,
        parent_rounds=3, child_rounds=3, finished_unix=25, own_context='current exact context'))
    return root, lane


def test_CODE_reconstructs_exact_pinned_empty_lessons_and_retains_pending(code):
    root, lane = code
    boundary = node4.code_frontier(root, 'CYCLE_102_COMPLETE.json', {'pid': 123})
    assert boundary['reconstructed_carry'] == dict(own_context='current exact context',
                                                  lessons=['ancestral'] + ['']*10)
    assert len(boundary['pending_parents']) == 2


def test_CODE_requires_full_schedule_not_just_complete_marker(code):
    root, lane = code
    (lane/'cells/cycle102_segment1.json').unlink()
    with pytest.raises(ValueError, match='missing_or_later'):
        node4.code_frontier(root, 'CYCLE_102_COMPLETE.json', {'pid': 123})


def test_CODE_new_cell_after_saved_boundary_is_rejected(code):
    root, lane = code
    put(lane/'cells/later.json', dict(cycle=103))
    with pytest.raises(ValueError, match='missing_or_later'):
        node4.code_frontier(root, 'CYCLE_102_COMPLETE.json', {'pid': 123})


@pytest.mark.parametrize('patch,reason', [({'status': 'STARTED'}, 'inflight'),
    ({'started_unix': 31}, 'charge_after'), ({'finished_unix': 31}, 'inflight')])
def test_CODE_native_partial_or_late_blocks(code, patch, reason):
    root, lane = code
    path = lane/'cells/cycle102_segment1.json'
    put(path, dict(node4.read(path), **patch))
    with pytest.raises(ValueError, match=reason):
        node4.code_frontier(root, 'CYCLE_102_COMPLETE.json', {'pid': 123})


def test_CODE_nonempty_lesson_invalidates_reconstruction(code):
    root, lane = code
    path = lane/'cells/cycle102_parent2.json'
    put(path, dict(node4.read(path), lesson='not allowed'))
    with pytest.raises(ValueError, match='empty_parent_lesson'):
        node4.code_frontier(root, 'CYCLE_102_COMPLETE.json', {'pid': 123})


def test_CODE_schedule_hash_tampering_rejected(code):
    root, lane = code
    put(root/'schedule.json', [])
    with pytest.raises(ValueError, match='reference_hash'):
        node4.code_frontier(root, 'CYCLE_102_COMPLETE.json', {'pid': 123})


def test_CODE_training_actor_rejected(code):
    root, lane = code
    put(root/'PLAN.json', dict(node4.read(root/'PLAN.json'), optimizer_updates=1))
    with pytest.raises(ValueError, match='frozen_nonblocking'):
        node4.code_frontier(root, 'CYCLE_102_COMPLETE.json', {'pid': 123})


def test_R137_actual_combinations_are_distinct_and_unparented_is_explicit():
    rows = [node4.life_spec(physical, variants_ready=True) for physical in node4.LIVES]
    assert len({(row['programme'],row['cadence'],row['replay'],row['style']) for row in rows}) == 6
    assert all(not node4.life_spec(physical, variants_ready=True)['parent_enabled'] for physical in (1,5,6,7))
    assert node4.life_spec(3, variants_ready=True)['seed'] == 1


def test_only_explicit_kernel4_replay_fallback_allowed():
    row = node4.life_spec(4)
    assert row['replay'] == 'free_distillation'
    assert row['requested_replay'] == 'parent_guided_distillation'
    for physical in (3,6,7):
        with pytest.raises(ValueError, match='tested_seed_or_replay'):
            node4.life_spec(physical)


def test_raw_unparented_startup_does_not_claim_kernel_or_parent_results():
    text = node4.startup_text('Common situation\n### Kernel environment\nAdd task', node4.life_spec(1))
    assert text.startswith('Common situation') and 'Add task' not in text
    assert 'unparented raw comparison' in text and 'No scheduled parent' in text


def test_kernel_startup_preserves_task_and_does_not_claim_parent_delivery():
    text = node4.startup_text('Common\n### Kernel environment\nAdd task', node4.life_spec(4))
    assert 'Add task' in text and 'not a delivered message' in text


def test_release_recheck_never_signals_and_requires_exited_actors(monkeypatch, tmp_path):
    put(tmp_path/'REQUEST.json', dict(physical=1, actor={'pid':123}, supervisor={'pid':124}))
    monkeypatch.setattr(node4, 'check_pair', lambda *args: None)
    monkeypatch.setattr(node4.custody, 'alive', lambda *args: True)
    with pytest.raises(ValueError, match='must_have_exited'):
        node4.verify_retired(tmp_path, tmp_path/'newscan')
    assert not (tmp_path/'newscan').exists()


def test_startup_binds_own_workspace_GPU_source_and_preserves_wall():
    old = str(node4.BASE/'orch_r132_kernel_child_20260916_attempt1')
    original = old+'/workspace\n'+old+'/source1\nphysical 0 through the a40r wrapper\n'
    original += '### Kernel environment\nAdd task\nThe current allocation ends no later than lease margin.'
    text = node4.bind_startup(original, node4.life_spec(1), '/newlife', '/newsource')
    assert '/newlife/workspace' in text and '/newsource' in text and 'physical 1 through' in text
    assert old not in text and 'Add task' not in text and 'lease margin' in text
