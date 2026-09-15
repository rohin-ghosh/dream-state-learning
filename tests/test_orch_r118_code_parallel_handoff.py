from copy import deepcopy
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from gpu import orch_r118_code_parallel_handoff as handoff


def write(path, value):
    handoff.io.write(path, value, replace=path.exists())


@pytest.fixture
def ready(tmp_path):
    root, common = tmp_path / 'F3', tmp_path / 'common'
    state = dict(generation=1, checkpoint=dict(path_sha256='a' * 64))
    write(root / 'PLAN.json', dict(physical=2))
    write(root / 'SHARED_ACTIVATION.json', {})
    (root / 'COHORT.json').write_text('Sealed metadata is hashed, never parsed by this fixture.')
    for index in (0, 1):
        write(root / 'reservations' / f'C001_E{index}_ORIGINAL.json', dict(id=f'C001_E{index}_ORIGINAL',
            split='TRAIN', kind='NATIVE', status='COMPLETE', cycle=1))
    parent = dict(id='C001_E1_PARENT', split='TRAIN', kind='PARENT', status='MISSING', cycle=1,
        finished_unix=10, reflection_settings=dict(effective_max_new_tokens=3072))
    write(root / 'reservations/C001_E1_PARENT.json', parent)
    write(root / 'parent_queue/C001_E1_PARENT.request.json', dict(public=True))
    write(root / 'parent_claude/C001_E1_PARENT.claim/PUBLISHED.json', dict(status='MISSING'))
    write(root / 'cycles/C001_COMPLETE.json', dict(shared_generation=1))
    write(root / 'shared_cycles/C001/SHARED_SLEEP.json', dict(state=state))
    submission = common / 'generation_000000/F3.json'
    write(submission, dict(branch='F3', generation=0,
        episode_ids=[task['task_id'] for task in handoff.previous.client.run.policy.tasks('TRAIN')[:2]]))
    write(root / 'shared_cycles/C001/SHARED_SUBMISSION.json', dict(path=str(submission), sha256=handoff.io.sha(submission)))
    write(common / 'STATE.json', state)
    write(common / 'generation_000000/sleep/COMPLETE.json', dict(state=state, same_optimizer=True))
    write(root / 'shared_readout_bindings/C001_DEV.json', dict(state=state, checkpoint=state['checkpoint']))
    write(root / 'readouts/C001_DEV/COMPLETE.json', dict(cycle=1, scope='DEV', fresh_process=True,
        optimizer_steps=0, sleep_buffer_rows=0))
    for scope, count in (('DEV', 8), ('FOCUS', 2), ('OLD', 16), ('AUDIT', 2)):
        for index in range(count):
            write(root / 'reservations' / f'R001_DEV_{scope}_{index}.json', dict(kind='NATIVE', split='DEV',
                status='FAILED', routes=dict(parent=False, sleep=False)))
    return root, common


def test_all_scheduled_failed_DEV_cells_still_settle_no_quality_gate(ready):
    root, common = ready
    result = handoff.boundary(root, common)
    assert result['next_cycle'] == 2 and result['all_pending_DEV_settled']
    assert result['charges'] == dict(native_used=30, parent_used=1)
    assert result['carry']['reflection_settings']['effective_max_new_tokens'] == 3072


def test_different_two_episodes_cannot_advance_cursor(ready):
    root, common = ready
    path = common / 'generation_000000/F3.json'
    value = handoff.io.read(path)
    value['episode_ids'].reverse()
    write(path, value)
    write(root / 'shared_cycles/C001/SHARED_SUBMISSION.json', handoff.ref(path))
    with pytest.raises(ValueError, match='original_scheduled_TRAIN_order'):
        handoff.boundary(root, common)


def test_older_unsettled_DEV_also_blocks_release(ready):
    root, common = ready
    write(root / 'reservations/R000_DEV_DEV_0.json', dict(status='STARTED'))
    assert handoff.boundary(root, common) is None


@pytest.mark.parametrize('missing', ['readouts/C001_DEV/COMPLETE.json',
    'shared_readout_bindings/C001_DEV.json', 'reservations/R001_DEV_DEV_7.json',
    'reservations/R001_DEV_OLD_15.json', 'reservations/R001_DEV_AUDIT_1.json'])
def test_old_cycle_COMPLETE_never_sufficient(ready, missing):
    root, common = ready
    (root / missing).unlink()
    assert handoff.boundary(root, common) is None


def test_next_cycle_charge_blocks_release_even_when_previous_DEV_done(ready):
    root, common = ready
    write(root / 'reservations/C002_E0_ORIGINAL.json', dict(kind='NATIVE', split='TRAIN',
        status='COMPLETE', cycle=2))
    assert handoff.boundary(root, common) is None


def test_async_readout_child_blocks_cursor(ready):
    assert handoff.boundary(*ready, children=['synthetic_live_readout']) is None


def test_attached_open_and_observation_must_finish(ready):
    root, common = ready
    path = root / 'reservations/R001_DEV_DEV_0.json'
    row = handoff.io.read(path)
    write(path, dict(row, status='COMPLETE'))
    assert handoff.boundary(root, common) is None
    write(root / 'reservations/R001_DEV_DEV_OPEN.json', dict(status='COMPLETE'))
    write(root / 'environment/R001_DEV_DEV_OPEN.json', dict(observation=dict(status='COMPLETE')))
    assert handoff.boundary(root, common) is None
    write(root / 'reservations/R001_DEV_DEV_OPEN_OBSERVE.json', dict(status='FAILED'))
    assert handoff.boundary(root, common)['next_cycle'] == 2


def test_unpublished_late_parent_blocks_without_new_request(ready):
    root, common = ready
    (root / 'parent_claude/C001_E1_PARENT.claim/PUBLISHED.json').unlink()
    assert handoff.boundary(root, common) is None


def test_running_common_sleep_blocks(ready):
    root, common = ready
    write(common / 'generation_000001/sleep/START.json', dict(uncommitted=True))
    with pytest.raises(ValueError, match='no_running'):
        handoff.boundary(root, common)


def test_ledger_hashes_but_never_parses_sealed_FINAL(ready, monkeypatch):
    root, common = ready
    sealed = root / 'reservations/R000_ZERO_FINAL_0.json'
    sealed.write_text('sealed bytes must not be parsed')
    original = handoff.io.read
    monkeypatch.setattr(handoff.io, 'read', lambda path: pytest.fail('sealed_read') if Path(path) == sealed else original(path))
    result = handoff.boundary(root, common)
    assert result['charges']['native_used'] == 31
    assert 'reservations/R000_ZERO_FINAL_0.json' in result['preserved_files']


def test_authorization_requires_all8_Main_go(ready, tmp_path):
    root, common = ready
    document = dict(schema=handoff.SCHEMA, status='CPU_READY_ONLY', action='DRAIN', issued_unix=10,
        expires_unix=100, branches={branch: dict(root=str(root), plan_sha256=handoff.io.sha(root / 'PLAN.json'))
            for branch in handoff.io.BRANCHES})
    path = tmp_path / 'MAIN.json'
    write(path, document)
    with pytest.raises(ValueError, match='explicit_Main'):
        handoff.authorize(handoff.ref(path), root, 'DRAIN', lambda: 50)
    write(path, dict(document, status='MAIN_ALL8_COORDINATED_GO'))
    assert handoff.authorize(handoff.ref(path), root, 'DRAIN', lambda: 50)[2]['physical'] == 2


@pytest.fixture
def actor():
    process = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])
    try:
        yield process
    finally:
        if process.poll() is None:
            os.kill(process.pid, 18)
            process.terminate()
        process.wait(timeout=5)


def test_pidfd_inspection_failure_resumes_only_owned_CPU_actor(ready, actor, monkeypatch):
    foreign = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])
    try:
        monkeypatch.setattr(handoff, 'authorize', lambda *args: ({}, {}, {}))
        monkeypatch.setattr(handoff, 'checked', lambda value: dict(expires_unix=time.time() + 30))
        monkeypatch.setattr(handoff, 'live_children', lambda value: [])
        monkeypatch.setattr(handoff, 'boundary', lambda *args, **kwargs: None)
        assert handoff.hold_release(handoff.identities.identity(actor.pid), *ready, authorization={}) is None
        assert actor.poll() is None and foreign.poll() is None
        state = Path(f'/proc/{actor.pid}/stat').read_text().rsplit(') ', 1)[1].split()[0]
        assert state not in ('T', 't')
    finally:
        foreign.terminate()
        foreign.wait(timeout=5)


def test_hold_waits_for_existing_async_DEV_before_release(ready, actor, monkeypatch):
    calls = []
    monkeypatch.setattr(handoff, 'authorize', lambda *args: ({}, {}, {}))
    monkeypatch.setattr(handoff, 'checked', lambda value: dict(expires_unix=time.time() + 30))
    command = [str(ready[0]).encode(), b'readout', b'gpu.orch_r108_code_parent_r116_shared_run']
    pending = [[({}, command)], []]
    monkeypatch.setattr(handoff, 'live_children', lambda value: pending.pop(0))
    def boundary(*args, children):
        calls.append(bool(children))
        return None if children else dict(next_cycle=2)
    monkeypatch.setattr(handoff, 'boundary', boundary)
    result = handoff.hold_release(handoff.identities.identity(actor.pid), *ready, authorization={})
    assert result['boundary']['next_cycle'] == 2 and calls == [True, False]
    actor.wait(timeout=5)
