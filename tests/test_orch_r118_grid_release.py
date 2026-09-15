from pathlib import Path

import pytest

from gpu import orch_r118_grid_release as release


def test_only_current_grid_predecessors_and_explicit_all8():
    assert set(release.SPECS) == {'F4', 'A4'}
    assert release.SPECS['F4']['native'] == 804107
    assert release.SPECS['F4']['guard'] == 804050
    assert release.SPECS['A4']['native'] == 374239
    assert release.ROSTER_SHA.startswith('595f91e7') and release.EIGHT_SHA.startswith('5bff8653')
    with pytest.raises(ValueError, match='owned_grid_pair'):
        release.authorization('F1')


def test_next_cycle_reservation_is_missed_boundary_not_release(monkeypatch, tmp_path):
    def reject(*args):
        raise ValueError('no_next_cycle_or_inflight_reservation')
    monkeypatch.setattr(release.successor, 'capture_boundary', reject)
    assert release.try_boundary(tmp_path, tmp_path/'complete') is None


def test_requires_actual_DEV_and_published_parent(monkeypatch, tmp_path):
    snapshot = dict(completed_cycle=7)
    monkeypatch.setattr(release.successor, 'capture_boundary', lambda *args: dict(snapshot))
    monkeypatch.setattr(release.successor, 'read_ledger', lambda *args: [dict(kind='PARENT', number=2)])
    assert release.try_boundary(tmp_path, tmp_path/'complete') is None
    dev = tmp_path/'readouts/0007/dev/COMPLETE.json'
    release.shared.write(dev, dict(status='COMPLETE'))
    assert release.try_boundary(tmp_path, tmp_path/'complete') is None
    release.shared.write(tmp_path/'parent_claude/P0002.claim/PUBLISHED.json', dict(status='MISSING'))
    assert release.try_boundary(tmp_path, tmp_path/'complete')['dev_complete'] == release.grid.ref(dev)


def test_preserves_queue_claims_without_filtering_failure(monkeypatch, tmp_path):
    snapshot = dict(captures={})
    for key in ('complete', 'train_complete', 'ledger', 'carry', 'dev_complete'):
        path=tmp_path/(key+'.json');release.shared.write(path, {'key': key})
        snapshot[key] = release.grid.ref(path)
    for name in ('CONFIG.json','SHARED_CLIENT_READY.json','parent_queue/P0001.response.json',
                 'parent_claude/P0001.claim/PUBLISHED.json'):
        release.shared.write(tmp_path/name, dict(status='MISSING'))
    files=release.preserved(tmp_path,snapshot)
    assert 'parent_queue/P0001.response.json' in files
    assert 'parent_claude/P0001.claim/PUBLISHED.json' in files
    assert all(not Path(name).is_absolute() for name in files)
