"""Regressions for the sole added subprocess permission; no receiving execution."""

from contextlib import contextmanager
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


HERE = Path(__file__).resolve().parent
specification = importlib.util.spec_from_file_location('r175_ldconfig_launcher', HERE / 'run_once.py')
launcher = importlib.util.module_from_spec(specification)
specification.loader.exec_module(launcher)
receiving = launcher.receiving


def options():
    return dict(stdin=receiving.subprocess.DEVNULL, stdout=receiving.subprocess.PIPE,
                stderr=receiving.subprocess.DEVNULL, env={'LC_ALL': 'C', 'LANG': 'C'})


@contextmanager
def scoped_probe(fence):
    token = fence.ldconfig_context.set(True)
    try:
        yield
    finally:
        fence.ldconfig_context.reset(token)


def test_clean_environment_is_explicit_and_original_env_not_changed(tmp_path):
    fence = receiving.RuntimeFence(tmp_path, {})
    incoming = options()
    incoming['env'].update(LD_PRELOAD='forbidden_fixture', LD_LIBRARY_PATH='/untrusted',
                           DPKG_MAINTSCRIPT_PACKAGE='fixture', TEST_SECRET='never_log')
    prepared = fence.prepare_ldconfig(receiving.LDCONFIG_COMMAND, (), incoming)
    assert prepared['env'] == dict(PATH='/usr/bin:/bin', LC_ALL='C', LANG='C')
    assert incoming['env']['TEST_SECRET'] == 'never_log'
    assert prepared['env'] is not receiving.LDCONFIG_ENVIRONMENT
    assert fence.allowed_runtime_probes == []
    assert fence.denied == []


def test_exact_scoped_ldconfig_is_allowed_and_bound(tmp_path, monkeypatch):
    monkeypatch.setenv('PATH', '/usr/bin:/bin')
    fence = receiving.RuntimeFence(tmp_path, {})
    bindings = [dict(requested_path=name, **reference) for name, reference in receiving.LDCONFIG_EXECUTABLES.items()]
    monkeypatch.setattr(fence, 'verify_ldconfig', lambda: bindings)
    with scoped_probe(fence):
        fence.audit('subprocess.Popen', ('/sbin/ldconfig', ['/sbin/ldconfig', '-p'],
                                         None, dict(receiving.LDCONFIG_ENVIRONMENT)))
    assert fence.denied == []
    assert len(fence.allowed_runtime_probes) == 1
    assert fence.allowed_runtime_probes[0]['binary_references'] == bindings
    assert fence.allowed_runtime_probes[0]['environment'] == receiving.LDCONFIG_ENVIRONMENT
    assert not fence.ldconfig_context.get()


@pytest.mark.parametrize('executable,command', [
    ('/sbin/ldconfig', ['/sbin/ldconfig']),
    ('/sbin/ldconfig', ['/sbin/ldconfig', '-p', '-v']),
    ('/sbin/ldconfig', ['/sbin/ldconfig', '-r', '/tmp']),
    ('/sbin/ldconfig', ['/sbin/ldconfig', '-p; echo forbidden']),
    ('/usr/sbin/ldconfig', ['/usr/sbin/ldconfig', '-p']),
    ('/sbin/ldconfig.real', ['/sbin/ldconfig.real', '-p']),
    ('ldconfig', ['ldconfig', '-p']),
    ('/usr/bin/gcc', ['/usr/bin/gcc', '-Wl,-t', '-ldl']),
    ('gcc', ['gcc']), ('ld', ['ld', '-t', '-ldl']),
    ('/bin/sh', ['/bin/sh', '-c', '/sbin/ldconfig -p']),
])
def test_no_alias_flags_compiler_linker_or_shell_permission(tmp_path, monkeypatch, executable, command):
    monkeypatch.setenv('PATH', '/usr/bin:/bin')
    fence = receiving.RuntimeFence(tmp_path, {})
    with scoped_probe(fence), pytest.raises(PermissionError):
        fence.audit('subprocess.Popen', (executable, command, None, dict(receiving.LDCONFIG_ENVIRONMENT)))
    assert fence.allowed_runtime_probes == []


@pytest.mark.parametrize('changed', [None, {}, {'PATH': '/tmp:/usr/bin:/bin', 'LANG': 'C', 'LC_ALL': 'C'},
                                   dict(receiving.LDCONFIG_ENVIRONMENT, LD_PRELOAD='never_log')])
def test_unbound_or_dirty_environment_denied_without_secret_logging(tmp_path, monkeypatch, changed):
    monkeypatch.setenv('PATH', '/usr/bin:/bin')
    fence = receiving.RuntimeFence(tmp_path, {})
    with scoped_probe(fence), pytest.raises(PermissionError):
        fence.audit('subprocess.Popen', ('/sbin/ldconfig', receiving.LDCONFIG_COMMAND, None, changed))
    assert 'never_log' not in json.dumps(fence.denied)


def test_unscoped_request_wrong_parent_PATH_and_cwd_denied(tmp_path, monkeypatch):
    fence = receiving.RuntimeFence(tmp_path, {})
    monkeypatch.setenv('PATH', '/usr/bin:/bin')
    request = ('/sbin/ldconfig', receiving.LDCONFIG_COMMAND, None, receiving.LDCONFIG_ENVIRONMENT)
    with pytest.raises(PermissionError):
        fence.audit('subprocess.Popen', request)
    with scoped_probe(fence), pytest.raises(PermissionError):
        fence.audit('subprocess.Popen', (request[0], request[1], '/tmp', request[3]))
    monkeypatch.setenv('PATH', '/tmp:/usr/bin:/bin')
    with scoped_probe(fence), pytest.raises(PermissionError):
        fence.audit('subprocess.Popen', request)


@pytest.mark.parametrize('changes', [dict(shell=True), dict(preexec_fn=lambda: None),
                                   dict(pass_fds=(3,)), dict(cwd='/tmp'),
                                   dict(executable='/bin/sh'), dict(stdout=None),
                                   dict(stdin=None), dict(stderr=None), dict(start_new_session=True)])
def test_no_dangerous_Popen_options_or_changed_stream_contract(tmp_path, changes):
    fence = receiving.RuntimeFence(tmp_path, {})
    with pytest.raises(PermissionError):
        fence.prepare_ldconfig(receiving.LDCONFIG_COMMAND, (), dict(options(), **changes))
    with pytest.raises(PermissionError):
        fence.prepare_ldconfig(receiving.LDCONFIG_COMMAND, (0,), options())


def test_canonical_and_byte_bound_probe_verification_uses_both_executables(tmp_path, monkeypatch):
    fence = receiving.RuntimeFence(tmp_path, {})
    metadata = SimpleNamespace(st_mode=0o100755, st_uid=0)
    original_resolve = receiving.Path.resolve
    original_stat = receiving.Path.stat
    canonical = {name: reference['path'] for name, reference in receiving.LDCONFIG_EXECUTABLES.items()}
    checked = []

    def resolve(path, *arguments, **keywords):
        if str(path) in canonical:
            return Path(canonical[str(path)])
        return original_resolve(path, *arguments, **keywords)

    def inspect(path, *arguments, **keywords):
        if str(path) in canonical.values():
            return metadata
        return original_stat(path, *arguments, **keywords)

    monkeypatch.setattr(receiving.Path, 'resolve', resolve)
    monkeypatch.setattr(receiving.Path, 'stat', inspect)
    monkeypatch.setattr(receiving.BoundReader, 'read', lambda reader, path, checksum: checked.append((str(path), checksum)))
    bindings = fence.verify_ldconfig()
    assert checked == [(reference['path'], reference['sha256']) for reference in receiving.LDCONFIG_EXECUTABLES.values()]
    assert len(bindings) == 2
    metadata.st_mode = 0o100777
    with pytest.raises(ValueError, match='root_owned_nonwritable'):
        fence.verify_ldconfig()
    metadata.st_mode = 0o100755
    metadata.st_uid = 1000
    with pytest.raises(ValueError, match='root_owned_nonwritable'):
        fence.verify_ldconfig()


def test_new_scratch_latch_single_invocation_and_failed_receipt_preserved(tmp_path):
    calls = []
    receipt = dict(schema='R175_ACTUAL_RECEIVING_CPU_V1', scratch=receiving.SCRATCH, success=False,
                   status='FAILED_NO_RETRY')

    def invoke(command, **keywords):
        calls.append(command)
        return SimpleNamespace(returncode=0, stdout=receiving.encoded(receipt), stderr=b'')

    assert launcher.run_once(tmp_path, invoke) == 1
    with pytest.raises(FileExistsError):
        launcher.run_once(tmp_path, invoke)
    assert len(calls) == 1
    assert json.loads((tmp_path / 'ACTUAL_RECEIVING_CPU.json').read_bytes()) == receipt
    assert receiving.SCRATCH == '/localhome/local-rohing/orch_r175_actual_replay_cpu_20260917_attempt1'


def test_R174_source_test_support_fixture_pins_and_original_files_unchanged():
    prior = HERE.parent / 'r174_receiving_cpu_repair_20260917'
    prior_spec = importlib.util.spec_from_file_location('r174_frozen_reference', prior / 'receiving_cpu.py')
    old = importlib.util.module_from_spec(prior_spec)
    prior_spec.loader.exec_module(old)
    for name in ('OLD_SOURCE', 'OLD_GUARD', 'GUARD_SHA256', 'NATIVE_SHA256', 'PLAIN_SHA256',
                 'HELPERS', 'TESTS', 'TEST_SUPPORT', 'DEPENDENCIES', 'FIXTURE', 'FIXTURE_SHA256',
                 'MAX_FILE_BYTES', 'MAX_OPERATIONAL_BYTES'):
        assert getattr(receiving, name) == getattr(old, name)
    assert hashlib.sha256((prior / 'receiving_cpu.py').read_bytes()).hexdigest() == '6ebeeed6786b2194f874cd1a66a3164b0c302a1054d0fed8f36b48e9cd09b2f2'
    assert hashlib.sha256((prior / 'ACTUAL_RECEIVING_CPU.json').read_bytes()).hexdigest() == 'd14cda179688a3d145ea1ae5e8039c4e5c4dd3f530ded4d28ac523051a2e28dd'


def test_installed_Popen_shim_cleans_only_exact_probe_without_launch(tmp_path, monkeypatch):
    monkeypatch.setenv('PATH', '/usr/bin:/bin')
    fence = receiving.RuntimeFence(tmp_path, {})
    hooks = []
    invocations = []

    class FakePopen:
        def __init__(self, command, **keywords):
            hooks[0]('subprocess.Popen', (command[0], command, keywords.get('cwd'), keywords.get('env')))
            invocations.append(dict(command=command, keywords=keywords))

    monkeypatch.setattr(receiving.subprocess, 'Popen', FakePopen)
    monkeypatch.setattr(receiving.os, 'open', receiving.os.open)
    monkeypatch.setattr(receiving.sys, 'addaudithook', hooks.append)
    for name in ('signal', 'setitimer', 'alarm', 'pthread_kill', 'pthread_sigmask'):
        if hasattr(receiving.signal, name):
            monkeypatch.setattr(receiving.signal, name, getattr(receiving.signal, name))
    monkeypatch.setattr(fence, 'verify_ldconfig', lambda: list(receiving.LDCONFIG_EXECUTABLES.values()))
    fence.install()
    incoming = options()
    incoming['env']['LD_PRELOAD'] = 'fixture_not_in_child'
    receiving.subprocess.Popen(receiving.LDCONFIG_COMMAND, **incoming)
    assert invocations[0]['keywords']['env'] == receiving.LDCONFIG_ENVIRONMENT
    assert incoming['env']['LD_PRELOAD'] == 'fixture_not_in_child'
    assert not fence.ldconfig_context.get()
    with pytest.raises(PermissionError):
        receiving.subprocess.Popen(['/usr/bin/gcc', '-ldl'], **options())
    assert len(invocations) == 1
    assert 'fixture_not_in_child' not in json.dumps(fence.allowed_runtime_probes + fence.denied)


def test_canonical_path_or_binary_hash_drift_does_not_allow_probe(tmp_path, monkeypatch):
    fence = receiving.RuntimeFence(tmp_path, {})
    monkeypatch.setenv('PATH', '/usr/bin:/bin')

    def reject():
        raise ValueError('source_hash_mismatch:fixture_ldconfig')

    monkeypatch.setattr(fence, 'verify_ldconfig', reject)
    with scoped_probe(fence), pytest.raises(ValueError, match='source_hash_mismatch'):
        fence.audit('subprocess.Popen', ('/sbin/ldconfig', receiving.LDCONFIG_COMMAND,
                                         None, receiving.LDCONFIG_ENVIRONMENT))
    assert fence.allowed_runtime_probes == []
    assert fence.denied[-1]['reason'] == 'ldconfig_executable_binding_failed'
