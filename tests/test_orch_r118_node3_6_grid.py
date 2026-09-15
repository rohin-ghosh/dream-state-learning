from pathlib import Path

import pytest

from gpu import orch_r118_node3_6_grid_run as run
from gpu import orch_r118_node3_6_grid_broker as broker


@pytest.mark.parametrize('physical', [0, 1, 2, 3, 4, 5, 7])
def test_no_other_node3_gpu(physical):
    with pytest.raises(ValueError, match='only_explicitly_allocated_node3'):
        run.allocation(physical)


def test_explicit_UUID_host_and_conservative_lease():
    run.allocation(6)
    assert run.UUID == 'GPU-1a83d900-1e95-c7b4-9b12-8117399697f8'
    assert run.HOST_SHA == '3e10ebcb89f013079c1e088fa82820188b1a805b879ebb85a7ffeb689e7b86e9'
    assert run.LEASE_END == 1789689600
    assert run.grid.END == 1789491720 < run.LEASE_END - 21600


def test_only_two_template_constants_changed_no_live_A100_mutation():
    old = run.template.prepare.__code__.co_consts
    new = run.prepare.__code__.co_consts
    differences = [(before, after) for before, after in zip(old, new) if before != after]
    assert differences == [(4, 6), ('R118_A1004_GRID_V1', 'R118_NODE3_6_GRID_V1')] or differences == [
        ('R118_A1004_GRID_V1', 'R118_NODE3_6_GRID_V1'), (4, 6)]
    assert run.template.ROOT != run.ROOT
    assert run.template.UUID != run.UUID
    assert run.prepare.__globals__['validate'] is run.validate
    assert run.guard.__globals__['scan'] is run.scan


def test_children_and_readouts_keep_new_module():
    for mode in ('resident', 'readout'):
        assert run.command(mode, run.ROOT)[3] == 'gpu.orch_r118_node3_6_grid_run'
    assert run.spawn_readout.__globals__['command'] is run.command


def test_parent_transport_only_node3(monkeypatch):
    calls = []
    monkeypatch.setattr(broker.subprocess, 'run', lambda argv, **kwargs: calls.append(argv))
    store = broker.Store(Path('/immutable'))
    store.shell('true')
    store.copy('/tmp/request', 'NODE:/owned/request')
    assert calls[0][1] == '/immutable/gpu/ovx2_ssh.sh'
    assert calls[1][1] == '/immutable/gpu/ovx2_scp.sh'


def test_all_scoped_scan_checks_stay_enabled(monkeypatch):
    monkeypatch.setattr(run.os, 'geteuid', lambda: 0)
    monkeypatch.setattr(run.grid.admission.minor.pinned, 'policy', None)
    seen = []
    monkeypatch.setattr(run.idle_baseline, 'scan', lambda index, path: seen.append((index, path)))
    run.scan(run.ROOT)
    assert seen == [(6, run.ROOT / 'SERVICE_IDENTITY.json')]
    assert run.grid.admission.minor.pinned.policy.DEVICES == {6: run.UUID}


def test_same_science_budget_and_parent_model():
    assert run.grid.MAX_NATIVE == 1858 and run.grid.MAX_PARENT == 298
    assert broker.template.astra.MODEL == 'openai/openai/gpt-6-astra'
    assert run.prepare.__globals__['grid'] is run.template.grid
