from pathlib import Path
from types import SimpleNamespace

import pytest

from gpu import orch_r118_a1004_grid_run as run
from gpu import orch_r118_a1004_grid_broker as broker


@pytest.mark.parametrize('physical', [0, 1, 2, 3, 5, 6, 7])
def test_only_new_allocated_device(physical):
    with pytest.raises(ValueError, match='only_explicitly_allocated'):
        run.allocation(physical)


def test_exact_assignment_and_inherited_lease():
    run.allocation(4)
    assert run.UUID == 'GPU-31583768-d90f-520c-51ed-5dac761526d0'
    assert run.grid.END == 1789491720
    assert run.LEASE_END == 1790463900
    assert run.grid.END < run.LEASE_END - 21600


def test_child_and_readout_use_portability_entrypoint():
    for mode in ('resident', 'readout'):
        argv = run.command(mode, run.ROOT)
        assert argv[3] == 'gpu.orch_r118_a1004_grid_run'
        assert str(run.ROOT) in argv
        assert 'gpu.orch_r115_grid_native' not in argv


def test_queue_transport_never_node5(monkeypatch):
    calls = []
    monkeypatch.setattr(broker.subprocess, 'run', lambda argv, **kwargs: calls.append(argv))
    store = broker.Store(Path('/immutable'))
    store.shell('true')
    store.copy('/tmp/request', 'NODE:/owned/request')
    assert calls[0][1] == '/immutable/gpu/a100_ssh.sh'
    assert calls[1][1] == '/immutable/gpu/a100_scp.sh'


def test_scanner_retains_exact_device_and_service(monkeypatch):
    monkeypatch.setattr(run.os, 'geteuid', lambda: 0)
    seen = []
    monkeypatch.setattr(run.grid.admission, 'scan', lambda index, path: seen.append((index, path)))
    monkeypatch.setattr(run.grid.admission.minor.pinned, 'policy', SimpleNamespace())
    run.scan(run.ROOT)
    assert seen == [(4, run.ROOT / 'SERVICE_IDENTITY.json')]
    assert run.grid.admission.minor.pinned.policy.DEVICES == {4: run.UUID}


def test_existing_native_module_bytes_not_rewritten():
    assert run.grid.Life.__module__ == 'gpu.orch_r115_grid_native'
    assert run.grid.carry_rows.__module__ == 'gpu.orch_r115_grid_native'
    assert run.grid.MAX_NATIVE == 1858 and run.grid.MAX_PARENT == 298
    with pytest.raises(ValueError, match='never_carry'):
        run.grid.carry_rows([dict(split='TRAIN', purpose='reflection', attached_readout=True)])


def test_wrong_queue_rejected_before_provider(tmp_path):
    config = tmp_path / 'config.json'
    config.write_text('{"remote_root":"/wrong", "life_id":"wrong"}')
    with pytest.raises(ValueError, match='exact_new_A1004_parent_lane'):
        broker.serve(config, None, None, None)
