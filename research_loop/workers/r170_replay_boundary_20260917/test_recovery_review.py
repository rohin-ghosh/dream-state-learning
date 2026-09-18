"""Independent V2 CPU probes; signals address only subprocesses created by these tests."""

import ast
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time
from types import SimpleNamespace
from unittest import mock

import pytest


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
FAMILY = REPO / 'gpu/orch_r144_node3_target_handoff.py'
API = REPO / 'research_loop/workers/r144_node3_target_handoff_20260916t1541z_operator5/BOUNDARY_API.py'
PINS = {
    'OPERATOR.py': 'e2c0307936d8be5cde38633464641e921761369bf5c2ca3f65f960f69dbdd69f',
    'OPERATOR_RECOVERY_V2.py': '1a9b78c6044014ad1b69929e9a65cd34bbdc79130c77861a4152491f072f0dd4',
    'RECOVERY.py': '4864af9e8e21aa3fa5fc0b141bddbb09900908aabf52d8141a730375b3c7553a',
    'FAMILY.py': '014e23e330db36f0ef6a8da23f75084a7685e7e0663a1e9540759dac7fc0da5c',
    'BOUNDARY_API.py': 'f128becb34d95b6875e4283baa49b3504e2c6c589e67b93e858e07c98f593e60',
}


def load(path):
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == PINS[path.name]
    specification = importlib.util.spec_from_file_location('independent_v2_' + path.stem, path)
    module = importlib.util.module_from_spec(specification)
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


@pytest.fixture
def package(tmp_path):
    directory = tmp_path / 'operator_package'
    directory.mkdir()
    for name in ('OPERATOR.py', 'OPERATOR_RECOVERY_V2.py', 'RECOVERY.py'):
        directory.joinpath(name).write_bytes(HERE.joinpath(name).read_bytes())
    directory.joinpath('FAMILY.py').write_bytes(FAMILY.read_bytes())
    directory.joinpath('BOUNDARY_API.py').write_bytes(API.read_bytes())
    return directory


@pytest.fixture
def adapter(package):
    module = load(package / 'OPERATOR_RECOVERY_V2.py')
    namespace = module.adapter_namespace()
    return module, namespace, namespace['family_namespace']()


@pytest.fixture
def recovery(package):
    return load(package / 'RECOVERY.py')


def test_exact_AST_delta_and_all_other_family_functions_unchanged(adapter):
    module, namespace, family = adapter
    original = dict(__name__='independent_original_family', __file__=family['__file__'])
    tree = ast.parse(FAMILY.read_bytes())
    exec(compile(tree, family['__file__'], 'exec'), original)
    v1 = dict(__name__='independent_v1', __file__=namespace['__file__'])
    exec(compile((module.HERE / 'OPERATOR.py').read_bytes(), namespace['__file__'], 'exec'), v1)
    baseline = v1['family_namespace']()
    for definition in tree.body:
        if not isinstance(definition, ast.FunctionDef) or definition.name == 'handoff':
            continue
        name = definition.name
        assert family[name].__code__ == baseline[name].__code__
        assert family[name].__defaults__ == baseline[name].__defaults__
        assert family[name].__kwdefaults__ == baseline[name].__kwdefaults__
        assert family[name].__globals__ is (namespace if name == 'lane_scope' else
            namespace if name in ('old_modules', 'saved_evidence', 'validate_new', 'verify_source') else family)
    expected = deepcopy(next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                             and node.name == 'handoff'))
    outer = expected.body[-1]
    outer.finalbody = ast.parse('pause_recovery.cleanup(paused, descriptors, lock, handlers, output)').body
    replacements = {
        "helper.pause_exact(request['processes'][name], descriptors[name])":
            "pause_recovery.pause(helper, request['processes'][name], descriptors[name], request['processes'], descriptors, output)",
        'helper.resume_paused(paused, descriptors)': 'pause_recovery.resume(paused, descriptors)',
    }
    replacement_nodes = {ast.dump(ast.parse(before, mode='eval').body): ast.parse(after, mode='eval').body
                         for before, after in replacements.items()}

    class ExpectedCalls(ast.NodeTransformer):
        def visit_Call(self, node):
            replacement = replacement_nodes.get(ast.dump(node))
            return ast.copy_location(deepcopy(replacement), node) if replacement else self.generic_visit(node)

    expected = ExpectedCalls().visit(expected)
    expected_module = ast.fix_missing_locations(ast.Module(body=[expected], type_ignores=[]))
    exec(compile(expected_module, family['__file__'], 'exec'), original)
    assert family['handoff'].__code__ == original['handoff'].__code__
    assert family['handoff'].__globals__ is family
    assert family['handoff'].__closure__ is None
    assert family['__file__'] == str(module.HERE / 'OPERATOR_RECOVERY_V2.py')
    assert family['pause_recovery'].__class__.__module__ == 'r170_recovery_v2'
    assert family['pause_recovery'].arm.__globals__['__file__'] == str(module.HERE / 'RECOVERY.py')


@pytest.mark.parametrize('name', list(PINS.keys() - {'OPERATOR_RECOVERY_V2.py'}))
def test_wrong_local_dependency_pin_refuses_before_any_bootstrap_action(package, name):
    module = load(package / 'OPERATOR_RECOVERY_V2.py')
    package.joinpath(name).write_bytes(b'raise RuntimeError("must_not_execute_unpinned_source")\n')
    with pytest.raises(ValueError, match='frozen_recovery_dependency|pinned_saved_boundary_lifecycle'):
        module.adapter_namespace()['family_namespace']()


@pytest.mark.parametrize('reference', [
    dict(path='relative', sha256='a' * 64), dict(path='/tmp/binding', sha256='A' * 64),
    dict(path='/tmp/../tmp/binding', sha256='a' * 64),
    dict(path='/tmp/binding', sha256='invalid'), dict(path='/tmp/binding', sha256=1),
    dict(path='/tmp/binding', sha256='a' * 64, extra=True), None,
])
def test_repaired_guard_reference_negative_parity(adapter, reference):
    from gpu import orch_r168_targeted_replay_driver as driver

    module, namespace, family = adapter
    source = (REPO / 'gpu/orch_r125_continual_guard.py').read_bytes()
    for patcher in (namespace['patched_guard'], driver.patch_guard):
        with pytest.raises(ValueError):
            patcher(source, reference)


def test_guard_alias_path_refuses_and_valid_AST_keeps_all_guard_checks(adapter, tmp_path):
    from gpu import orch_r168_targeted_replay_driver as driver

    module, namespace, family = adapter
    source = (REPO / 'gpu/orch_r125_continual_guard.py').read_bytes()
    regular = tmp_path / 'binding'
    regular.write_text('{}')
    alias = tmp_path / 'alias'
    alias.symlink_to(regular)
    for patcher in (namespace['patched_guard'], driver.patch_guard):
        with pytest.raises(ValueError, match='canonical_absolute_path'):
            patcher(source, dict(path=str(alias), sha256='a' * 64))
    reference = dict(path=str(regular), sha256='a' * 64)
    patched = namespace['patched_guard'](source, reference)
    assert patched == driver.patch_guard(source, reference)
    before, after = ast.parse(source), ast.parse(patched)
    original_entry = next(node for node in before.body if isinstance(node, ast.FunctionDef)
                          and node.name == 'native_entry')
    patched_entry = next(node for node in after.body if isinstance(node, ast.FunctionDef)
                         and node.name == 'native_entry')
    patched_entry.body[-1] = original_entry.body[-1]
    assert ast.dump(before) == ast.dump(after)


def test_real_V2_subprocess_supervise_bootstraps_V2_not_V1(package, tmp_path):
    hooks = tmp_path / 'hooks'
    hooks.mkdir()
    hooks.joinpath('sitecustomize.py').write_text('''
import json, os, sys
def trace(frame, event, argument):
    if event == 'call' and frame.f_code.co_name == 'supervise':
        family = frame.f_globals
        print(json.dumps(dict(file=family['__file__'], recovery=type(family['pause_recovery']).__module__,
            command=family['contained_command'].__code__.co_filename)), flush=True)
        os._exit(0)
    return trace
def forbid(event, arguments):
    if event in ('os.kill', 'os.killpg', 'subprocess.Popen', 'socket.connect'):
        raise RuntimeError('no_external_action_in_bootstrap_probe')
sys.addaudithook(forbid)
sys.settrace(trace)
''')
    script = package / 'OPERATOR_RECOVERY_V2.py'
    result = subprocess.run([sys.executable, '-B', str(script), '--action', 'supervise',
        '--output', str(tmp_path / 'unused_attempt')], capture_output=True, text=True, timeout=10,
        cwd=tmp_path, env=dict(os.environ, PYTHONPATH=str(hooks), PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES=''))
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == dict(file=str(script), recovery='r170_recovery_v2', command=str(script))
    assert not (tmp_path / 'unused_attempt').exists()


@pytest.fixture
def inert_arm(recovery, tmp_path):
    events = []
    process = SimpleNamespace(pid=1234, poll=lambda: None, wait=lambda timeout: 0)
    spawned = mock.Mock(return_value=process)
    identities = {role: dict(pid=100 + index) for index, role in enumerate(recovery.ROLES)}
    descriptors = dict(supervisor=11, timer=12, actor=13)
    helper = SimpleNamespace(process_record=lambda identifier: dict(pid=identifier),
        write=lambda *args: events.append('ready_receipt'), pause_exact=lambda *args: events.append('STOP'))
    pipe = mock.Mock(side_effect=[(21, 22), (23, 24)])
    closed = []
    recovery.os = SimpleNamespace(pidfd_open=lambda identifier: 20, getpid=lambda: 99,
        pipe2=pipe, O_CLOEXEC=os.O_CLOEXEC, close=closed.append, read=lambda *args: b'R',
        write=lambda *args: events.append('disarm'))
    recovery.subprocess = SimpleNamespace(Popen=spawned, DEVNULL=-3, STDOUT=-2)
    recovery.select = SimpleNamespace(select=lambda *args: ([21], [], []))
    recovery.signal = SimpleNamespace(SIGCONT=signal.SIGCONT,
        pidfd_send_signal=lambda descriptor, signum: events.append(('CONT', descriptor)),
        signal=lambda *args: events.append('restore'))
    return SimpleNamespace(module=recovery, helper=helper, descriptors=descriptors,
        identities=identities, events=events, closed=closed, spawned=spawned, output=tmp_path)


def test_ready_receipt_failure_prevents_STOP_but_still_disarms_and_cleans(inert_arm):
    fixture = inert_arm
    fixture.helper.write = mock.Mock(side_effect=OSError('poisoned_ready_logger'))
    guard = fixture.module.Recovery()
    with pytest.raises(OSError, match='poisoned_ready_logger'):
        guard.pause(fixture.helper, fixture.identities['supervisor'], 11,
            fixture.identities, fixture.descriptors, fixture.output)
    assert 'STOP' not in fixture.events
    guard.cleanup(['supervisor'], fixture.descriptors, 30, {}, fixture.output)
    assert fixture.closed == [22, 20, 21, 23, 11, 12, 13, 30, 24]
    assert ('CONT', 11) in fixture.events and 'disarm' in fixture.events
    assert guard.finished and guard.control is None


def test_arm_launches_only_bound_helper_with_exact_handles_and_clean_environment(inert_arm):
    fixture = inert_arm
    guard = fixture.module.Recovery()
    guard.pause(fixture.helper, fixture.identities['supervisor'], 11,
        fixture.identities, fixture.descriptors, fixture.output)
    command = fixture.spawned.call_args.args[0]
    assert command == [sys.executable, '-B', fixture.module.__file__, '--watchdog',
        '--operator-fd', '20', '--ready-fd', '22', '--control-fd', '23',
        '--supervisor-fd', '11', '--timer-fd', '12', '--actor-fd', '13']
    options = fixture.spawned.call_args.kwargs
    assert options['pass_fds'] == (20, 22, 23, 11, 12, 13)
    assert options['start_new_session'] is True
    assert options['env'] == dict(PATH='/usr/bin:/bin', PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='')
    assert fixture.events == ['ready_receipt', 'STOP']
    guard.cleanup(['supervisor'], fixture.descriptors, 30, {}, fixture.output)


@pytest.mark.parametrize('failure', ['timeout', 'eof', 'wrong_ack', 'watcher_exited'])
def test_nonready_watcher_never_reaches_STOP(inert_arm, failure):
    fixture = inert_arm
    if failure == 'timeout':
        fixture.module.select.select = lambda *args: ([], [], [])
    elif failure == 'eof':
        fixture.module.os.read = lambda *args: b''
    elif failure == 'wrong_ack':
        fixture.module.os.read = lambda *args: b'X'
    else:
        fixture.spawned.return_value.poll = lambda: 1
    guard = fixture.module.Recovery()
    with pytest.raises(ValueError, match='watcher_ready_before_any_STOP'):
        guard.pause(fixture.helper, fixture.identities['supervisor'], 11,
            fixture.identities, fixture.descriptors, fixture.output)
    assert 'STOP' not in fixture.events and not guard.armed
    assert fixture.closed == [22, 20, 21, 23]
    guard.cleanup(['supervisor'], fixture.descriptors, 30, {}, fixture.output)
    assert guard.control is None


def test_dead_watcher_before_next_pause_refuses_then_recovers_previous_pause(inert_arm):
    fixture = inert_arm
    guard = fixture.module.Recovery()
    guard.pause(fixture.helper, fixture.identities['supervisor'], 11,
        fixture.identities, fixture.descriptors, fixture.output)
    fixture.spawned.return_value.poll = lambda: 1
    fixture.spawned.return_value.wait = lambda timeout: 1
    with pytest.raises(ValueError, match='ready_live_watcher_before_STOP'):
        guard.pause(fixture.helper, fixture.identities['timer'], 12,
            fixture.identities, fixture.descriptors, fixture.output)
    assert fixture.events.count('STOP') == 1
    with pytest.raises(RuntimeError, match='incomplete_preserve_failure_no_retry'):
        guard.cleanup(['supervisor', 'timer'], fixture.descriptors, 30, {}, fixture.output)
    assert ('CONT', 12) in fixture.events and ('CONT', 11) in fixture.events


@pytest.mark.parametrize('failed_pipe', [1, 2])
@pytest.mark.xfail(strict=True, reason='setup pidfd/pipes acquired before try leak on pipe2 failure; before STOP')
def test_partial_pipe_setup_closes_every_acquired_descriptor(inert_arm, failed_pipe):
    fixture = inert_arm
    failure = OSError(24, 'fixture_descriptor_exhaustion')
    fixture.module.os.pipe2.side_effect = [failure] if failed_pipe == 1 else [(21, 22), failure]
    guard = fixture.module.Recovery()
    with pytest.raises(OSError, match='fixture_descriptor_exhaustion'):
        guard.pause(fixture.helper, fixture.identities['supervisor'], 11,
            fixture.identities, fixture.descriptors, fixture.output)
    fixture.spawned.assert_not_called()
    assert 'STOP' not in fixture.events
    guard.cleanup(['supervisor'], fixture.descriptors, 30, {}, fixture.output)
    expected_setup = {20} if failed_pipe == 1 else {20, 21, 22}
    assert expected_setup.issubset(fixture.closed)


def test_cleanup_logger_failure_occurs_only_after_all_cleanup_attempts(inert_arm):
    fixture = inert_arm
    guard = fixture.module.Recovery()
    fixture.output.joinpath('poison').mkdir()
    original_path = fixture.module.Path

    class PoisonedReceipt:
        def __truediv__(self, name):
            assert name.startswith('RECOVERY_')
            raise OSError('poisoned_cleanup_logger')

    fixture.module.Path = lambda path: PoisonedReceipt() if path == fixture.output else original_path(path)
    with pytest.raises(OSError, match='poisoned_cleanup_logger'):
        guard.cleanup(['supervisor', 'timer', 'actor'], fixture.descriptors, 30,
                      {signal.SIGTERM: signal.SIG_DFL}, fixture.output)
    assert fixture.closed == [11, 12, 13, 30]
    assert fixture.events == [('CONT', 13), ('CONT', 12), ('CONT', 11), 'restore']
    assert guard.finished


def test_watch_failure_receipt_blocks_success_without_replaying_CONT(inert_arm):
    fixture = inert_arm
    guard = fixture.module.Recovery()
    guard.process = SimpleNamespace(wait=lambda timeout: 7)
    guard.control = 24
    guard.armed = True
    with pytest.raises(RuntimeError, match='incomplete_preserve_failure_no_retry'):
        guard.cleanup([], fixture.descriptors, 30, {}, fixture.output)
    receipt = json.loads(next(fixture.output.glob('RECOVERY_*.json')).read_text())
    assert receipt['status'] == 'RECOVERY_INCOMPLETE' and receipt['retry'] is False
    assert any(error['operation'] == 'watcher_wait' for error in receipt['errors'])
    assert not any(isinstance(event, tuple) for event in fixture.events)


OWNER = '''
import importlib.util,json,os,select,signal,sys
from pathlib import Path
from types import SimpleNamespace
spec=importlib.util.spec_from_file_location('independent_owned_recovery',sys.argv[1])
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
descriptors=json.loads(sys.argv[3]); identities=json.loads(sys.argv[4]); mode=sys.argv[5]
def identity(identifier):
    return dict(pid=identifier,start_ticks=Path('/proc',str(identifier),'stat').read_text().rsplit(')',1)[1].split()[19])
def write(path,value):
    path.write_text(json.dumps(value))
helper=SimpleNamespace(process_record=identity,write=write,
    pause_exact=lambda expected,descriptor:signal.pidfd_send_signal(descriptor,signal.SIGSTOP))
guard=module.Recovery()
for role in module.ROLES:
    guard.pause(helper,identities[role],descriptors[role],identities,descriptors,Path(sys.argv[2]))
if mode=='disarm_stopped':
    os.write(guard.control,b'D');os.close(guard.control);guard.control=None
else:
    for role in ('actor','timer','supervisor')[:int(mode)]:
        signal.pidfd_send_signal(descriptors[role],signal.SIGTERM)
        signal.pidfd_send_signal(descriptors[role],signal.SIGCONT)
        assert select.select([descriptors[role]],[],[],5)[0]
print(json.dumps(dict(watcher_pid=guard.process.pid)),flush=True)
sys.stdin.read()
'''


@pytest.mark.parametrize('mode', ['1', '2', '3', 'disarm_stopped'])
def test_owned_CPU_death_actual_actor_first_retirement_and_denied_disarm(recovery, package, tmp_path, mode):
    targets = {}
    descriptors = {}
    owner = None
    owner_fd = None
    watcher_fd = None
    try:
        for role in recovery.ROLES:
            process = subprocess.Popen([sys.executable, '-B', '-c', 'import time; time.sleep(60)'],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            targets[role] = process
            descriptors[role] = os.pidfd_open(process.pid)
        identities = {role: dict(pid=process.pid, start_ticks=Path('/proc', str(process.pid), 'stat')
            .read_text().rsplit(')', 1)[1].split()[19]) for role, process in targets.items()}
        owner = subprocess.Popen([sys.executable, '-B', '-c', OWNER, str(package / 'RECOVERY.py'),
            str(tmp_path), json.dumps(descriptors), json.dumps(identities), mode],
            pass_fds=tuple(descriptors.values()), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, start_new_session=True)
        owner_fd = os.pidfd_open(owner.pid)
        assert select.select([owner.stdout], [], [], 8)[0]
        line = owner.stdout.readline()
        assert line, owner.stderr.read() if owner.poll() is not None else 'no_owner_ready'
        watcher_pid = json.loads(line)['watcher_pid']
        watcher_fd = os.pidfd_open(watcher_pid)
        assert os.getsid(watcher_pid) == watcher_pid != os.getsid(owner.pid)
        keys = {part.split(b'=', 1)[0] for part in Path('/proc', str(watcher_pid), 'environ')
                .read_bytes().split(b'\0') if part}
        assert keys == {b'PATH', b'PYTHONDONTWRITEBYTECODE', b'CUDA_VISIBLE_DEVICES'}
        retired = [] if mode == 'disarm_stopped' else ['actor', 'timer', 'supervisor'][:int(mode)]
        time.sleep(.1)
        assert owner.poll() is None and not recovery.exited(watcher_fd)
        for role, descriptor in descriptors.items():
            if role in retired:
                assert recovery.exited(descriptor)
            else:
                assert not recovery.not_stopped(descriptor)
        signal.pidfd_send_signal(owner_fd, signal.SIGKILL)
        owner.wait(timeout=5)
        assert select.select([watcher_fd], [], [], 5)[0]
        assert all(recovery.not_stopped(descriptor) for descriptor in descriptors.values())
        for role, process in targets.items():
            if role in retired:
                assert process.poll() == -signal.SIGTERM
            else:
                assert process.poll() is None
        receipt = json.loads(tmp_path.joinpath('DEATH_WATCHER.log').read_text())
        assert receipt['status'] == 'OPERATOR_DIED_CONT_ATTEMPTED'
        assert receipt['errors'] == [] and receipt['restart'] is False
    finally:
        if owner is not None and owner.poll() is None:
            if owner_fd is None:
                owner.kill()
            else:
                signal.pidfd_send_signal(owner_fd, signal.SIGKILL)
            owner.wait(timeout=5)
        for role, process in targets.items():
            descriptor = descriptors.get(role)
            if descriptor is not None and process.poll() is None:
                signal.pidfd_send_signal(descriptor, signal.SIGCONT)
                signal.pidfd_send_signal(descriptor, signal.SIGTERM)
            if descriptor is not None:
                process.wait(timeout=5)
                os.close(descriptor)
            elif process.poll() is None:
                process.terminate()
                process.wait(timeout=5)
        if watcher_fd is not None:
            select.select([watcher_fd], [], [], 5)
            os.close(watcher_fd)
        if owner_fd is not None:
            os.close(owner_fd)
