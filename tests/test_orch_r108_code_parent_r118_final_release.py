import os
from pathlib import Path
import subprocess
import sys

import pytest

from gpu import orch_r108_code_parent_r118_final_release as release


@pytest.fixture
def actor():
    process = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        yield process
    finally:
        if process.poll() is None:
            process.kill()
        process.wait(timeout=5)


def test_before_future_window_never_opens_pidfd_or_signals(actor, monkeypatch):
    expected = release.identity(actor.pid)
    monkeypatch.setattr(release.os, 'pidfd_open', lambda pid: pytest.fail('early pidfd acquisition'))
    with pytest.raises(ValueError, match='future_CODE_release_clock_gate'):
        release.drained_process(expected, lambda: {}, clock=lambda: release.RELEASE_START - 1)
    assert actor.poll() is None


def test_wrong_start_identity_never_signals(actor, monkeypatch):
    expected = dict(release.identity(actor.pid), start_ticks='wrong')
    monkeypatch.setattr(release.os, 'pidfd_open', lambda pid: pytest.fail('identity mismatch acquired'))
    with pytest.raises(ValueError, match='exact_owned_native_before_hold'):
        release.drained_process(expected, lambda: {}, clock=lambda: release.RELEASE_START + 1)
    assert actor.poll() is None


@pytest.mark.skipif(not hasattr(os, 'pidfd_open'), reason='Linux pidfd required')
def test_busy_boundary_resumes_same_actor_without_termination(actor):
    expected = release.identity(actor.pid)
    assert release.drained_process(expected, lambda: None, clock=lambda: release.RELEASE_START + 1) is None
    assert actor.poll() is None and release.identity(actor.pid) == expected


@pytest.mark.skipif(not hasattr(os, 'pidfd_open'), reason='Linux pidfd required')
def test_inspection_failure_always_resumes_actor(actor):
    def failed():
        raise ValueError('CPU inspection failure')

    with pytest.raises(ValueError, match='CPU inspection failure'):
        release.drained_process(release.identity(actor.pid), failed, clock=lambda: release.RELEASE_START + 1)
    assert actor.poll() is None


@pytest.mark.skipif(not hasattr(os, 'pidfd_open'), reason='Linux pidfd required')
def test_only_exact_actor_stopped_at_held_clean_boundary(actor):
    sentinel = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])
    try:
        expected = release.identity(actor.pid)

        def checked():
            state = (Path('/proc') / str(actor.pid) / 'stat').read_text().rsplit(') ', 1)[1].split()[0]
            assert state in ('T', 't')
            return dict(cycle=21, preserved_reservations={})

        result = release.drained_process(expected, checked, clock=lambda: release.RELEASE_START + 1)
        actor.wait(timeout=3)
        assert result['identity'] == expected and result['boundary']['cycle'] == 21
        assert result['not_natural_completion'] is True
        assert sentinel.poll() is None
    finally:
        sentinel.kill()
        sentinel.wait(timeout=5)


@pytest.fixture
def boundary(tmp_path, actor):
    root = tmp_path / 'original'
    common = tmp_path / 'common'
    release.io.write(root / 'SHARED_ACTIVATION.json', dict(shared_learner=dict(branch='F3', root=str(common))))
    for name, kind in [('C021_E0', 'NATIVE'), ('C021_E1', 'NATIVE'), ('C021_PARENT', 'PARENT')]:
        release.io.write(root / 'reservations' / (name + '.json'),
            dict(id=name, kind=kind, status='COMPLETE', cycle=21))
    release.io.write(root / 'parent_claude/C021_PARENT.claim/PUBLISHED.json', dict(status='COMPLETE'))
    common_path = common / 'generation_000000/F3.json'
    release.io.write(common_path, dict(branch='F3', episode_ids=['TRAIN_ONE', 'TRAIN_TWO']))
    release.io.write(root / 'shared_cycles/C021/SHARED_SUBMISSION.json',
        dict(path=str(common_path), sha256=release.io.sha(common_path), generation=0))
    return root


def test_boundary_needs_actual_two_episode_submission(boundary, actor):
    result = release.collection_boundary(boundary, actor.pid)
    assert result['cycle'] == 21 and len(result['preserved_reservations']) == 3
    (boundary / 'shared_cycles/C021/SHARED_SUBMISSION.json').unlink()
    assert release.collection_boundary(boundary, actor.pid) is None


@pytest.mark.parametrize('kind', ['NATIVE', 'PARENT'])
def test_inflight_train_or_parent_prevents_release(boundary, actor, kind):
    release.io.write(boundary / 'reservations/C021_PENDING.json',
        dict(id='C021_PENDING', kind=kind, status='STARTED', cycle=21))
    assert release.collection_boundary(boundary, actor.pid) is None


def test_unpublished_parent_prevents_release(boundary, actor):
    (boundary / 'parent_claude/C021_PARENT.claim/PUBLISHED.json').unlink()
    assert release.collection_boundary(boundary, actor.pid) is None


def test_original_partial_FINAL_prevents_release(boundary, actor):
    (boundary / 'readouts/C021_FINAL').mkdir(parents=True)
    assert release.collection_boundary(boundary, actor.pid) is None


def test_common_submission_hash_drift_is_not_a_release(boundary, actor):
    reference = release.io.read(boundary / 'shared_cycles/C021/SHARED_SUBMISSION.json')
    Path(reference['path']).write_text('{}')
    with pytest.raises(ValueError, match='actual_common_submission_changed'):
        release.collection_boundary(boundary, actor.pid)
