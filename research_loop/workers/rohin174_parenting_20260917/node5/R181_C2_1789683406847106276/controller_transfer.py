"""Exact-owner R166 CPU-controller detach; never operates on stream writer locks."""

import ast
import fcntl
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import stat
import time


BASE = Path('/localhome/local-rohing')
R166_SHA = '655e72c553c934538b47e12987ffb9d493505f668721e0c432275b4617233681'
EXPECTED = {'C2': {'pid': 1581688, 'start_ticks': '20352107', 'argv_sha256': '8d41984fe384352941ee1f13ac6aa80d8abf5324ccfce83c122d749b5f3a44f7', 'cwd': '/localhome/local-rohing/orch_r179_context_C2_20260917_attempt4/source', 'child_pid': 1626777, 'child_start_ticks': '20440673', 'child_argv_sha256': 'd12118e9a3b647a4654e13c33a125511dcc238a9e6fd0b461f4cb7d770844492', 'source': {'path': '/localhome/local-rohing/orch_r179_context_C2_20260917_attempt4/rollout_operator.py', 'sha256': 'e59649d3fd1fde7514f75e7af9d557d6f7f1ecee504403d47a610ccac5405b80'}}}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def reference(path):
    return dict(path=str(path), sha256=sha(path))


def write(path, value):
    with Path(path).open('x') as handle:
        json.dump(value, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write('\n')
        handle.flush()
        os.fsync(handle.fileno())
        os.fchmod(handle.fileno(), 0o444)


def process_identity(process_id):
    process = Path('/proc') / str(process_id)
    fields = (process / 'stat').read_text().rsplit(') ', 1)[1].split()
    require(fields[0] not in ('Z', 'X'), 'controller_or_wait_child_live')
    status = dict(line.split(':', 1) for line in (process / 'status').read_text().splitlines() if ':' in line)
    command = (process / 'cmdline').read_bytes()
    return dict(pid=process_id, start_ticks=fields[19], uid=process.stat().st_uid,
        parent=int(fields[1]), group=int(fields[2]), session=int(fields[3]),
        cwd=os.readlink(process / 'cwd') if process.stat().st_uid == os.getuid() else None,
        argv_sha256=hashlib.sha256(command).hexdigest(),
        argv=command.rstrip(b'\0').decode().split('\0'), cgroup=(process / 'cgroup').read_text().strip(),
        signals={name: status[name].strip() for name in ('SigCgt', 'SigIgn', 'SigBlk', 'Threads')})


def lock_identity(path):
    metadata = Path(path).lstat()
    require(stat.S_ISREG(metadata.st_mode) and metadata.st_nlink == 1 and metadata.st_uid == 2524,
            'existing_regular_single_link_owned_handoff_lock')
    return dict(path=str(path), device=metadata.st_dev, inode=metadata.st_ino,
                major=os.major(metadata.st_dev), minor=os.minor(metadata.st_dev))


def flock_owners(identity, text=None):
    text = Path('/proc/locks').read_text() if text is None else text
    owners = []
    for line in text.splitlines():
        fields = line.split()
        for position, field in enumerate(fields):
            components = field.split(':')
            if len(components) != 3:
                continue
            try:
                matched = (int(components[0], 16), int(components[1], 16), int(components[2])) == (
                    identity['major'], identity['minor'], identity['inode'])
            except ValueError:
                continue
            if matched:
                require(position == 5 and fields[1:4] == ['FLOCK', 'ADVISORY', 'WRITE'],
                        'exclusive_flock_without_waiting_competitors')
                owners.append(int(fields[4]))
    return owners


def passive_source(path):
    require(sha(path) == R166_SHA, 'exact_audited_R166_controller_source')
    source = Path(path).read_text()
    functions = {node.name: node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef)}
    supervise = functions['supervise']
    require(not any(isinstance(node, (ast.For, ast.While, ast.AsyncFor)) for node in ast.walk(supervise)),
            'passive_supervise_has_no_retry_loop')
    calls = [node for node in ast.walk(supervise) if isinstance(node, ast.Call)
             and ast.unparse(node.func) == 'subprocess.run']
    require(len(calls) == 1 and ast.unparse(calls[0]) == 'subprocess.run(command, check=False)',
            'single_synchronous_service_wait')
    for name in ('execute', 'execute_recovery'):
        returns = [node for node in ast.walk(functions[name]) if isinstance(node, ast.Return)]
        require(len(returns) == 1 and ast.unparse(returns[0].value) == "supervise(output / 'control/GUARD.json')",
                'controller_returns_after_one_supervised_life')
    return dict(source=reference(path), functions={name: hashlib.sha256(
        ast.get_source_segment(source, functions[name]).encode()).hexdigest()
        for name in ('execute', 'execute_recovery', 'supervise')}, synchronous_wait=True, automatic_relaunch=False)


def inspect_holder(label, config, pair):
    require(label in EXPECTED and os.getuid() == 2524, 'bound_R181_controller_scope')
    expected = EXPECTED[label]
    holder = process_identity(expected['pid'])
    require(all(holder[key] == expected[key] for key in ('pid','start_ticks','argv_sha256','cwd')), 'exact_holder_identity')
    require(holder['uid'] == 2524 and holder['parent'] == 1 and holder['group'] == holder['session'] == holder['pid'], 'orphan_outer_CPU_only')
    require(holder['signals'] == dict(SigCgt='0000000000000002', SigIgn='0000000001001000', SigBlk='0000000000000000', Threads='1'), 'default_unblocked_SIGTERM')
    child = process_identity(expected['child_pid'])
    require(child['start_ticks'] == expected['child_start_ticks'] and child['uid'] == 0 and child['parent'] == holder['pid'] and child['argv_sha256'] == expected['child_argv_sha256'], 'exact_sudo_wait_child')
    children = (Path('/proc') / str(holder['pid']) / 'task' / str(holder['pid']) / 'children').read_text().split()
    require(children == [str(child['pid'])], 'one_wait_child')
    recorded = read(Path(config['attempt_dir']) / 'CONTAINED_COMMAND.json')
    require(child['argv'] == recorded['command'] and '--unit=' + config['device_containment']['unit'] in child['argv'], 'exact_waiting_unit_and_recorded_command')
    for process in pair.values():
        actual = process_identity(process['pid'])
        require(actual['start_ticks'] == process['start_ticks'] and actual['session'] != holder['session'] and actual['cgroup'] == '0::/system.slice/' + config['device_containment']['unit'] + '.service', 'native_survives_outer_CPU_detach')
    source = Path(expected['source']['path'])
    require(sha(source) == expected['source']['sha256'], 'bound_actual_controller_source')
    text = source.read_text()
    functions = {node.name:node for node in ast.parse(text).body if isinstance(node,ast.FunctionDef)}
    supervise = functions.get('supervise')
    if supervise is None:
        require(source.name in ('c1_readmission.py','c4_readmission.py'), 'only_known_R179_readmission_waiter')
        supervise = functions['execute']
    calls = [node for node in ast.walk(supervise) if isinstance(node,ast.Call) and ast.unparse(node.func)=='subprocess.run']
    require(len(calls)==1 and ast.unparse(calls[0])=='subprocess.run(command, check=False)', 'one_passive_service_wait')
    require(not any(any(descendant is calls[0] for descendant in ast.walk(node)) for node in ast.walk(supervise) if isinstance(node,(ast.For,ast.While,ast.AsyncFor))), 'no_service_wait_in_retry_loop')
    lock = lock_identity(BASE / ('orch_r157_' + label + '_HANDOFF.lock'))
    require(flock_owners(lock)==[holder['pid']], 'genuine_existing_lock_owner')
    return dict(label=label,holder=holder,wait_child=child,lock=lock,source_proof=dict(source=reference(source),passive_supervise=True,no_retry=True))


def verify_binding(binding, config, pair):
    actual = inspect_holder(binding['label'], config, pair)
    require(actual == binding, 'unchanged_controller_binding_before_detach')
    return actual


def verify_descriptor(descriptor, binding):
    metadata = os.fstat(descriptor)
    require(lock_identity(binding['lock']['path']) == binding['lock']
            and (metadata.st_dev, metadata.st_ino) == (binding['lock']['device'], binding['lock']['inode']),
            'genuine_existing_handoff_descriptor_same_inode')


def no_previous_stop(output, binding):
    paths = sorted(output.parent.glob('orch_r179_context_' + binding['label'] + '_*/CONTROLLER_STOP_INTENT.json'))
    require(len(paths) <= 100, 'bounded_controller_stop_history')
    for path in paths:
        prior = read(path)['holder']
        require((prior['pid'], prior['start_ticks']) != (binding['holder']['pid'], binding['holder']['start_ticks']),
                'controller_stop_intent_is_consumed_never_repeat')


def authorize(output, go_path=None, go_sha256=None):
    path = output / 'R181_AUTHORITY.json'
    authorization = read(path)
    require(authorization['recipe']=='R181_NEW_ONLY_V1' and authorization['outer_controller_transfer']=='same_existing_tested_pidfd_same_inode_transfer' and time.time()<authorization['expires_unix'], 'explicit_R181_scoped_authority')
    return reference(path)


def transfer(output, binding, descriptor, config, pair, verify_native, authorization):
    verify_binding(binding, config, pair)
    verify_descriptor(descriptor, binding)
    no_previous_stop(output, binding)
    require((output / 'ACTUAL_BOUNDARY_READY.json').is_file(), 'actual_saved_boundary_readout_CPU_receipt')
    verify_native()
    holder_descriptor = os.pidfd_open(binding['holder']['pid'])
    try:
        verify_binding(binding, config, pair)
        verify_native()
        require(sha(authorization['path']) == authorization['sha256']
                and time.time() < read(authorization['path'])['expires_unix'],
                'unchanged_unexpired_Main_addendum_at_exact_controller_stop')
        write(output / 'CONTROLLER_STOP_INTENT.json', dict(holder=binding['holder'],
            binding=reference(output / 'CONTROLLER_BINDING.json'), authorization=authorization,
            boundary=reference(output / 'ACTUAL_BOUNDARY_READY.json'), lock=binding['lock'],
            signal='SIGTERM', target='OUTER_CPU_CONTROLLER_ONLY', no_retry=True, recorded_unix=time.time()))
        signal.pidfd_send_signal(holder_descriptor, signal.SIGTERM)
        require(bool(select.select([holder_descriptor], [], [], 10)[0]), 'controller_exact_pidfd_exit_required')
        write(output / 'CONTROLLER_EXITED.json', dict(holder=binding['holder'], exited_unix=time.time(),
            exit_observed_by_pidfd=True, native_stop_intent=False))
        verify_descriptor(descriptor, binding)
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(flock_owners(binding['lock']) == [os.getpid()], 'genuine_transferred_kernel_flock_owner')
        write(output / 'CONTROLLER_LOCK_ACQUIRED.json', dict(lock=binding['lock'], holder_pid=os.getpid(),
            acquired_unix=time.time(), same_inode=True, native_stop_intent=False))
        verify_native()
        child = process_identity(binding['wait_child']['pid'])
        require(all(child[key] == binding['wait_child'][key] for key in
                    ('pid', 'start_ticks', 'uid', 'group', 'session', 'argv_sha256')),
                'sudo_systemd_wait_child_survives_CPU_detach')
        write(output / 'CONTROLLER_TRANSFER_VERIFIED.json', dict(status='PASS', native_unchanged=True,
            saved_boundary_unchanged=True, wait_child_unchanged=True, no_group_signals=True,
            no_writer_lock_access=True, recorded_unix=time.time()))
    finally:
        os.close(holder_descriptor)
