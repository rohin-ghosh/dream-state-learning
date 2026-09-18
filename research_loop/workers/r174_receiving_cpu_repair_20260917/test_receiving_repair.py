"""Regression tests for the CPU harness fence, not learner or evaluation changes."""

import importlib.util
import os
from pathlib import Path

import pytest


HERE = Path(__file__).resolve().parent
specification = importlib.util.spec_from_file_location('r174_launcher', HERE / 'run_once.py')
launcher = importlib.util.module_from_spec(specification)
specification.loader.exec_module(launcher)
receiving = launcher.receiving


def test_readonly_directory_traversal_does_not_allow_foreign_files(tmp_path):
    fence = receiving.RuntimeFence(tmp_path, {})
    for path in tmp_path.parents:
        fence.audit('open', (str(path), None, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC))
    assert fence.denied == []
    for path in ('/root/.ssh/id_rsa', '/localhome/local-rohing/private_life/COMMIT.json'):
        with pytest.raises(PermissionError):
            fence.audit('open', (path, 'r', os.O_RDONLY))


@pytest.mark.parametrize('flags', [os.O_RDONLY, os.O_RDWR, os.O_WRONLY | os.O_CREAT | os.O_TRUNC])
def test_null_sink_opens_allowed_but_chmod_unlink_not_allowed(tmp_path, flags):
    fence = receiving.RuntimeFence(tmp_path, {})
    fence.audit('open', ('/dev/null', None, flags))
    with pytest.raises(PermissionError):
        fence.audit('os.remove', ('/dev/null', -1))
    with pytest.raises(PermissionError):
        fence.audit('os.chmod', ('/dev/null', 0o777, -1))


def test_self_proc_metadata_resolves_to_only_own_process(tmp_path):
    fence = receiving.RuntimeFence(tmp_path, {})
    for name in ('maps', 'status', 'stat'):
        fence.audit('open', ('/proc/self/' + name, 'r', os.O_RDONLY))
        fence.audit('open', ('/proc/' + str(os.getpid()) + '/' + name, 'r', os.O_RDONLY))
    with pytest.raises(PermissionError):
        fence.audit('open', ('/proc/1/environ', 'r', os.O_RDONLY))


def test_only_pinned_readonly_uname_probe_is_allowed(tmp_path, monkeypatch):
    monkeypatch.setenv('PATH', '/usr/bin:/bin')
    fence = receiving.RuntimeFence(tmp_path, {})
    fence.audit('subprocess.Popen', ('uname', ['uname', '-p'], None, None))
    assert fence.allowed_runtime_probes == [dict(executable='uname', command=['uname', '-p'])]
    for command in (['uname', '-p; touch /tmp/file'], ['bash', '-c', 'uname -p'],
                    ['nvidia-smi'], ['curl', 'example.invalid']):
        with pytest.raises(PermissionError):
            fence.audit('subprocess.Popen', (command[0], command, None, None))
    assert all('environment' not in item for item in fence.denied if isinstance(item, dict))


def test_untrusted_uname_PATH_is_refused(tmp_path, monkeypatch):
    monkeypatch.setenv('PATH', '/tmp:/usr/bin:/bin')
    fence = receiving.RuntimeFence(tmp_path, {})
    with pytest.raises(PermissionError):
        fence.audit('subprocess.Popen', ('uname', ['uname', '-p'], None, None))


@pytest.mark.parametrize('event,args', [('os.kill', (1, 15)), ('os.system', ('uname -p',)),
                                      ('socket.connect', (None, ('localhost', 80)))])
def test_real_signal_shell_and_network_stay_forbidden(tmp_path, event, args):
    with pytest.raises(PermissionError):
        receiving.RuntimeFence(tmp_path, {}).audit(event, args)


def test_negative_support_is_separate_from_runtime_and_hash_bound(tmp_path):
    source = tmp_path / 'source'
    source.mkdir()
    support = tmp_path / 'test_support/gpu'
    support.mkdir(parents=True)
    repository = HERE.parents[2]
    for name, checksum in receiving.TEST_SUPPORT.items():
        raw = repository.joinpath(name).read_bytes()
        assert receiving.sha(raw) == checksum
        support.joinpath(Path(name).name).write_bytes(raw)
    finder = receiving.CandidateImports(source, {})
    specification = finder.find_spec('gpu.orch_r145_suffix_boundary')
    assert Path(specification.origin).is_relative_to(tmp_path / 'test_support')
    assert not Path(specification.origin).is_relative_to(source)
    assert receiving.inventory(source, {}) == {}
    support.joinpath('orch_r145_suffix_boundary.py').write_bytes(b'changed')
    with pytest.raises(ValueError, match='exact_negative_test_support'):
        finder.find_spec('gpu.orch_r145_suffix_boundary')


def test_runtime_whitelist_still_forbids_suffix_and_unknown_source(tmp_path):
    pins = {receiving.NATIVE_PATH: receiving.NATIVE_SHA256,
            'gpu/orch_r125_continual_guard.py': receiving.ORIGINAL_GUARD_SHA256,
            'organism_v6/orch_r125_plain_context.py': receiving.PLAIN_SHA256}
    receiving.validate_pins(pins)
    for name, checksum in receiving.TEST_SUPPORT.items():
        with pytest.raises(ValueError, match='no_suffix_optimization_copy'):
            receiving.validate_pins(dict(pins, **{name: checksum}))


def test_payload_contains_exact_runtime_and_separate_support():
    payload = launcher.payload()
    unpacked = receiving.unpack_payload(payload)
    assert len(unpacked) == 10
    assert set(receiving.TEST_SUPPORT).isdisjoint(receiving.HELPERS)
    assert receiving.SCRATCH.endswith('orch_r174_actual_replay_cpu_20260917_attempt1')
    assert '/r173_' not in str(HERE)
