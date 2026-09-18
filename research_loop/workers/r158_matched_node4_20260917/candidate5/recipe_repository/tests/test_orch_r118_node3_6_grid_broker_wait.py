import pytest

from gpu import orch_r118_node3_6_grid_broker_wait as broker


def test_wait_reuses_exact_lock_and_reserves_provider_time(monkeypatch):
    calls = []
    clock = [10.0]
    def acquire(lock, flags):
        calls.append((lock, flags))
        if len(calls) < 3:
            raise BlockingIOError()
    monkeypatch.setattr(broker.wait_source.fcntl, 'flock', acquire)
    lock = object()
    receipt = broker.wait_source.acquire_parent_lock(lock, 50, clock=lambda: clock[0],
        pause=lambda seconds: clock.__setitem__(0, clock[0] + seconds))
    assert len(calls) == 3 and all(item[0] is lock for item in calls)
    assert receipt == dict(collisions=2, waited_seconds=.5, provider_attempts=0,
                           provider_time_reserved_seconds=20)


def test_contention_does_not_extend_original_cutoff(monkeypatch):
    clock = [10.0]
    def busy(*args):
        raise BlockingIOError()
    monkeypatch.setattr(broker.wait_source.fcntl, 'flock', busy)
    with pytest.raises(ValueError, match='parent_lock_wait_expired'):
        broker.wait_source.acquire_parent_lock(object(), 31, clock=lambda: clock[0],
            pause=lambda seconds: clock.__setitem__(0, clock[0] + seconds))
    assert clock[0] == 11


def test_evaluator_changes_family_only_keeps_grid_parser():
    old = broker.wait_source.evaluate.__code__.co_consts
    new = broker.evaluate.__code__.co_consts
    assert set((before, after) for before, after in zip(old, new) if before != after) == {
        ('F1', 'F4'), ('route', 'grid'), ('F1_only', 'F4_only')}
    assert broker.evaluate.__globals__['parse'] is broker.astra.parse
    assert broker.evaluate.__globals__['acquire_parent_lock'] is broker.wait_source.acquire_parent_lock
    assert broker.evaluate.__kwdefaults__ == broker.wait_source.evaluate.__kwdefaults__


def test_other_root_rejected_before_provider(tmp_path):
    path = tmp_path / 'config.json'
    path.write_text('{"remote_root":"/other", "life_id":"other"}')
    with pytest.raises(ValueError, match='exact_new_node3_6_parent_lane'):
        broker.serve(path, None, None, None)
