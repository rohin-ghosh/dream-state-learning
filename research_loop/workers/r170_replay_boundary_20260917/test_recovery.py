"""Owned CPU-process death probes; no model, network, GPU, or existing process signals."""

import ast
import builtins
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

import pytest


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
FAMILY = REPO / 'gpu/orch_r144_node3_target_handoff.py'
API = REPO / 'research_loop/workers/r144_node3_target_handoff_20260916t1541z_operator5/BOUNDARY_API.py'


def load(path):
    specification = importlib.util.spec_from_file_location('r170_test_' + path.stem, path)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


@pytest.fixture
def recovery():
    return load(HERE / 'RECOVERY.py')


@pytest.fixture
def adapter(tmp_path):
    for name in ('OPERATOR.py', 'OPERATOR_RECOVERY_V2.py', 'RECOVERY.py'):
        tmp_path.joinpath(name).write_bytes(HERE.joinpath(name).read_bytes())
    tmp_path.joinpath('FAMILY.py').write_bytes(FAMILY.read_bytes())
    tmp_path.joinpath('BOUNDARY_API.py').write_bytes(API.read_bytes())
    module = load(tmp_path / 'OPERATOR_RECOVERY_V2.py')
    return module, module.adapter_namespace()


@pytest.fixture
def targets():
    processes = [subprocess.Popen([sys.executable, '-B', '-c', 'import time; time.sleep(120)'],
                  stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                 for unused in range(3)]
    descriptors = {role: os.pidfd_open(process.pid) for role, process in
                   zip(('supervisor', 'timer', 'actor'), processes)}
    try:
        yield processes, descriptors
    finally:
        for process, descriptor in zip(processes, descriptors.values()):
            if process.poll() is None:
                signal.pidfd_send_signal(descriptor, signal.SIGCONT)
                signal.pidfd_send_signal(descriptor, signal.SIGTERM)
            process.wait(timeout=5)
            os.close(descriptor)


def test_reference_repair_parity(adapter, tmp_path):
    from gpu import orch_r168_targeted_replay_driver as driver

    module, namespace = adapter
    source = (REPO / 'gpu/orch_r125_continual_guard.py').read_bytes()
    reference = dict(path=str(tmp_path / 'binding'), sha256='a' * 64)
    assert namespace['patched_guard'](source, reference) == driver.patch_guard(source, reference)
    for bad in (dict(path='relative', sha256='a' * 64),
                dict(path=str(tmp_path / 'binding'), sha256='invalid')):
        with pytest.raises(ValueError):
            namespace['patched_guard'](source, bad)


def test_only_three_recovery_sites_differ(adapter):
    module, namespace = adapter
    family = namespace['family_namespace']()
    assert family['handoff'].__globals__ is family
    assert family['lane_scope'] is namespace['scope']
    for name in ('supervise', 'stage', 'monitor', 'contained_command', 'claim_boundary'):
        assert family[name].__globals__ is family
    original = next(node for node in ast.parse(FAMILY.read_bytes()).body
                    if isinstance(node, ast.FunctionDef) and node.name == 'handoff')
    with pytest.raises(ValueError, match='frozen_cleanup_structure'):
        wrong = deepcopy(original)
        wrong.body[-1].finalbody = ast.parse('pass').body
        module.repaired_handoff(family, ast.unparse(ast.Module(body=[wrong], type_ignores=[])))
    assert namespace['sha'](HERE / 'OPERATOR.py') == module.V1_SHA256
    assert namespace['sha'](module.HERE / 'RECOVERY.py') == module.RECOVERY_SHA256


def test_full_handoff_AST_equivalence_except_declared_recovery(adapter):
    module, unused = adapter
    captured = {}

    def capture(tree, filename, mode):
        captured['tree'] = deepcopy(tree)
        return builtins.compile(tree, filename, mode)

    module.compile = capture
    module.repaired_handoff({'__file__': str(module.HERE / 'OPERATOR_RECOVERY_V2.py')}, FAMILY.read_bytes())
    modified = captured['tree'].body[0]
    original = next(node for node in ast.parse(FAMILY.read_bytes()).body
                    if isinstance(node, ast.FunctionDef) and node.name == 'handoff')
    assert ast.dump(modified.body[-1].finalbody[0]) == ast.dump(ast.parse(
        'pause_recovery.cleanup(paused, descriptors, lock, handlers, output)').body[0])
    modified.body[-1].finalbody = deepcopy(original.body[-1].finalbody)

    class Reverse(ast.NodeTransformer):
        def visit_Call(self, node):
            if ast.dump(node.func) == ast.dump(ast.parse('pause_recovery.pause', mode='eval').body):
                return ast.parse("helper.pause_exact(request['processes'][name], descriptors[name])", mode='eval').body
            if ast.dump(node.func) == ast.dump(ast.parse('pause_recovery.resume', mode='eval').body):
                return ast.parse('helper.resume_paused(paused, descriptors)', mode='eval').body
            return self.generic_visit(node)

    assert ast.dump(Reverse().visit(modified)) == ast.dump(original)


def test_failed_CONT_does_not_skip_remaining_roles(recovery):
    called = []

    def signaler(descriptor, signum):
        called.append((descriptor, signum))
        if descriptor == 12:
            raise PermissionError(1, 'fixture-only')

    recovery.signal = SimpleNamespace(SIGCONT=signal.SIGCONT, pidfd_send_signal=signaler)
    guard = recovery.Recovery()
    paused = ['supervisor', 'timer', 'actor']
    with pytest.raises(RuntimeError, match='other_handles_attempted'):
        guard.resume(paused, dict(supervisor=11, timer=12, actor=13))
    assert [descriptor for descriptor, unused in called] == [13, 12, 11]
    assert paused == ['timer']
    assert guard.errors[0]['role'] == 'timer'


def test_cleanup_every_handle_lock_and_handler_despite_failures(recovery, tmp_path):
    closed = []
    restored = []
    resumed = []

    def close(descriptor):
        closed.append(descriptor)
        if descriptor in (11, 21):
            raise OSError(9, 'fixture-only')

    def signaler(descriptor, signum):
        resumed.append(descriptor)
        if descriptor == 12:
            raise PermissionError(1, 'fixture-only')

    def restore(signum, handler):
        restored.append(signum)
        if signum == signal.SIGTERM:
            raise ValueError('fixture-only')

    recovery.os = SimpleNamespace(close=close)
    recovery.signal = SimpleNamespace(SIGCONT=signal.SIGCONT,
                                      pidfd_send_signal=signaler, signal=restore)
    guard = recovery.Recovery()
    with pytest.raises(RuntimeError, match='incomplete_preserve_failure'):
        guard.cleanup(['supervisor', 'timer', 'actor'], dict(supervisor=11, timer=12, actor=13),
                      21, {signal.SIGTERM: signal.SIG_DFL, signal.SIGHUP: signal.SIG_DFL}, tmp_path)
    assert resumed == [13, 12, 11]
    assert closed == [11, 12, 13, 21]
    assert restored == [signal.SIGTERM, signal.SIGHUP]
    receipt = json.loads(next(tmp_path.glob('RECOVERY_*.json')).read_text())
    assert receipt['status'] == 'RECOVERY_INCOMPLETE' and receipt['retry'] is False


def test_watcher_CONT_attempts_every_exact_handle(recovery):
    attempts = []

    def signaler(descriptor, signum):
        attempts.append((descriptor, signum))
        if descriptor == 11:
            raise PermissionError(1, 'fixture-only')
        if descriptor == 12:
            raise ProcessLookupError(3, 'fixture-only')

    recovery.signal = SimpleNamespace(SIGCONT=signal.SIGCONT, pidfd_send_signal=signaler)
    errors = recovery.continue_all(dict(supervisor=11, timer=12, actor=13))
    assert attempts == [(11, signal.SIGCONT), (12, signal.SIGCONT), (13, signal.SIGCONT)]
    assert len(errors) == 1 and errors[0]['role'] == 'supervisor'


OWNER = '''
import importlib.util,json,os,select,signal,sys,time
from pathlib import Path
from types import SimpleNamespace
specification=importlib.util.spec_from_file_location('owned_cpu_recovery',sys.argv[1])
module=importlib.util.module_from_spec(specification); specification.loader.exec_module(module)
output=Path(sys.argv[2]); descriptors=json.loads(sys.argv[3]); identities=json.loads(sys.argv[4])
pause_count=int(sys.argv[5]); retire_count=int(sys.argv[6]); close_control=sys.argv[7]=='1'
def identity(identifier):
    fields=Path('/proc',str(identifier),'stat').read_text().rsplit(')',1)[1].split()
    return dict(pid=identifier,start_ticks=fields[19])
def write(path,value):
    with path.open('x') as handle: json.dump(value,handle)
helper=SimpleNamespace(process_record=identity,write=write,
    pause_exact=lambda expected,descriptor: signal.pidfd_send_signal(descriptor,signal.SIGSTOP))
guard=module.Recovery(); guard.arm(helper,identities,descriptors,output)
for role in module.ROLES[:pause_count]:
    guard.pause(helper,identities[role],descriptors[role],identities,descriptors,output)
for role in module.ROLES[:retire_count]:
    signal.pidfd_send_signal(descriptors[role],signal.SIGTERM)
    signal.pidfd_send_signal(descriptors[role],signal.SIGCONT)
    assert select.select([descriptors[role]],[],[],5)[0]
if close_control:
    os.close(guard.control); guard.control=None
print(json.dumps(dict(watcher_pid=guard.process.pid,owner_pid=os.getpid())),flush=True)
sys.stdin.read()
'''


@pytest.mark.parametrize('paused,retired,close_control',
    [(0, 0, False), (1, 0, False), (2, 0, False), (3, 0, False),
     (3, 1, False), (3, 2, False), (3, 3, False), (3, 0, True)])
def test_operator_death_recovers_every_surviving_pause_prefix(recovery, targets, tmp_path,
                                                            paused, retired, close_control):
    processes, descriptors = targets
    identities = {role: dict(pid=process.pid, start_ticks=Path('/proc', str(process.pid),
                  'stat').read_text().rsplit(')', 1)[1].split()[19])
                  for role, process in zip(recovery.ROLES, processes)}
    owner = subprocess.Popen([sys.executable, '-B', '-c', OWNER, str(HERE / 'RECOVERY.py'),
        str(tmp_path), json.dumps(descriptors), json.dumps(identities), str(paused), str(retired),
        '1' if close_control else '0'], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True, pass_fds=tuple(descriptors.values()))
    owner_fd = os.pidfd_open(owner.pid)
    try:
        assert select.select([owner.stdout], [], [], 8)[0]
        text = owner.stdout.readline()
        assert text, owner.stderr.read() if owner.poll() is not None else 'owner_ready_missing'
        receipt = json.loads(text)
        watcher_keys = {entry.split(b'=', 1)[0] for entry in
                        Path('/proc', str(receipt['watcher_pid']), 'environ').read_bytes().split(b'\0')}
        assert b'NVIDIA_API_KEY' not in watcher_keys
        time.sleep(0.15)
        assert owner.poll() is None
        for process in processes[retired:paused]:
            assert Path('/proc', str(process.pid), 'stat').read_text().rsplit(')', 1)[1].split()[0] in ('T', 't')
        signal.pidfd_send_signal(owner_fd, signal.SIGKILL)
        owner.wait(timeout=5)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and not all(recovery.not_stopped(handle) for handle in descriptors.values()):
            time.sleep(0.02)
        assert all(recovery.not_stopped(handle) for handle in descriptors.values())
        for process in processes[retired:]:
            assert process.poll() is None
        for process in processes[:retired]:
            assert process.wait(timeout=5) == -signal.SIGTERM
        log = tmp_path / 'DEATH_WATCHER.log'
        while time.monotonic() < deadline and not log.stat().st_size:
            time.sleep(0.02)
        assert json.loads(log.read_text())['status'] == 'OPERATOR_DIED_CONT_ATTEMPTED'
    finally:
        if owner.poll() is None:
            signal.pidfd_send_signal(owner_fd, signal.SIGKILL)
            owner.wait(timeout=5)
        os.close(owner_fd)


def test_failed_watcher_launch_prevents_STOP(recovery, targets, tmp_path):
    processes, descriptors = targets
    identities = {role: dict(pid=process.pid) for role, process in zip(recovery.ROLES, processes)}
    pauses = []
    helper = SimpleNamespace(process_record=lambda identifier: dict(pid=identifier),
                             pause_exact=lambda *args: pauses.append(args))

    def failed(*args, **kwargs):
        raise OSError('fixture_launch_failure')

    recovery.subprocess = SimpleNamespace(Popen=failed, DEVNULL=subprocess.DEVNULL, STDOUT=subprocess.STDOUT)
    guard = recovery.Recovery()
    try:
        with pytest.raises(OSError, match='fixture_launch_failure'):
            guard.pause(helper, identities['actor'], descriptors['actor'], identities, descriptors, tmp_path)
        assert pauses == []
        assert all(recovery.not_stopped(handle) for handle in descriptors.values())
    finally:
        if guard.control is not None:
            os.close(guard.control)


def test_disarm_after_confirmed_resume(recovery, targets, tmp_path):
    processes, descriptors = targets
    owned = {role: os.dup(descriptor) for role, descriptor in descriptors.items()}
    identities = {role: dict(pid=process.pid) for role, process in zip(recovery.ROLES, processes)}

    def write(path, value):
        path.write_text(json.dumps(value))

    helper = SimpleNamespace(process_record=lambda identifier: dict(pid=identifier), write=write,
        pause_exact=lambda expected, descriptor: signal.pidfd_send_signal(descriptor, signal.SIGSTOP))
    guard = recovery.Recovery()
    guard.pause(helper, identities['actor'], owned['actor'], identities, owned, tmp_path)
    lock = os.open(tmp_path / 'lock', os.O_RDWR | os.O_CREAT, 0o600)
    guard.cleanup(['actor'], owned, lock, {}, tmp_path)
    assert guard.process.returncode == 0
    assert json.loads((tmp_path / 'DEATH_WATCHER.log').read_text())['status'] == 'DISARMED_TARGETS_EXITED_OR_RUNNING'
    assert all(recovery.not_stopped(handle) for handle in descriptors.values())


def test_watcher_refuses_disarm_while_target_stopped(recovery, targets, tmp_path):
    processes, descriptors = targets
    identities = {role: dict(pid=process.pid) for role, process in zip(recovery.ROLES, processes)}
    helper = SimpleNamespace(process_record=lambda identifier: dict(pid=identifier),
        write=lambda path, value: path.write_text(json.dumps(value)),
        pause_exact=lambda expected, descriptor: signal.pidfd_send_signal(descriptor, signal.SIGSTOP))
    guard = recovery.Recovery()
    try:
        guard.pause(helper, identities['actor'], descriptors['actor'], identities, descriptors, tmp_path)
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline and recovery.not_stopped(descriptors['actor']):
            time.sleep(0.01)
        assert not recovery.not_stopped(descriptors['actor'])
        os.write(guard.control, b'D')
        time.sleep(0.15)
        assert guard.process.poll() is None
        assert not recovery.not_stopped(descriptors['actor'])
        signal.pidfd_send_signal(descriptors['actor'], signal.SIGCONT)
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline and not recovery.not_stopped(descriptors['actor']):
            time.sleep(0.01)
        os.write(guard.control, b'D')
        assert guard.process.wait(timeout=5) == 0
    finally:
        signal.pidfd_send_signal(descriptors['actor'], signal.SIGCONT)
        if guard.process is not None and guard.process.poll() is None:
            guard.process.terminate()
            guard.process.wait(timeout=5)
        if guard.control is not None:
            os.close(guard.control)
