import pytest

from gpu import orch_r125_cpu_confinement_probe as probe


def test_fixed_cpu_probe_never_accepts_child_command():
    command = probe.command('/localhome/test/r125', 'orch-r125-cpu-test')
    assert command[:3] == ['sudo', '-n', 'systemd-run']
    assert command[-4:] == ['PYTHONHASHSEED=0', '/usr/bin/python3', '-I', '/job.py']
    assert '--property=DynamicUser=yes' in command
    assert '--property=DevicePolicy=strict' in command
    assert '--property=DeviceAllow=/dev/null rw' in command
    assert '--property=CapabilityBoundingSet=' in command
    assert '--property=PrivateNetwork=yes' in command
    assert '--property=SystemCallErrorNumber=EPERM' in command
    assert '--property=InaccessiblePaths=/sys /sys/fs/cgroup' in command
    assert any('/localhome/test/r125/empty:/sys/fs/cgroup' in argument for argument in command)
    assert '--property=RootDirectory=/localhome/test/r125/rootfs' in command
    assert '--property=MemoryMax=128M' in command
    assert '--property=TasksMax=8' in command
    assert '--property=RuntimeMaxSec=15' in command
    assert '--property=OOMPolicy=kill' in command
    assert not any('bwrap' in argument or 'nvidia' in argument for argument in command)


@pytest.mark.parametrize('root', ['relative', '/tmp/../root', '/tmp/space here', '/tmp/x;id', '/tmp/a\nb'])
def test_reject_ambiguous_root(root):
    with pytest.raises(ValueError):
        probe.command(root, 'orch-r125-cpu-test')


@pytest.mark.parametrize('unit', ['shared-service', 'orch-r125-cpu-../x', 'orch-r125-cpu-', 'orch-r125-cpu-a;id'])
def test_only_owned_unit_prefix(unit):
    with pytest.raises(ValueError):
        probe.command('/tmp/r125', unit)


def test_payload_is_syntax_valid_and_only_synthetic():
    payload = probe.PAYLOAD.replace('__OUTSIDE__', repr('/synthetic/canary')).replace('__PEER__', '123')
    compile(payload, '<trusted-probe>', 'exec')
    assert "'peer_signal_permission', lambda: os.kill(peer, 0)" in payload
    assert "range(12)" in payload
    assert '/dev/nvidia' not in payload
    assert 'exec(' not in payload


@pytest.mark.parametrize('mode', list(probe.RESOURCE_PAYLOADS))
def test_resource_probe_is_fixed_and_syntax_valid(mode):
    compile(probe.RESOURCE_PAYLOADS[mode], '<trusted-resource-probe>', 'exec')


def test_unknown_mode_rejected_before_directory_creation(tmp_path):
    root = tmp_path / 'never-created'
    with pytest.raises(ValueError, match='trusted_probe'):
        probe.run(root, mode='arbitrary-command')
    assert not root.exists()
