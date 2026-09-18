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
EXPECTED = {
    'C2': dict(pid=4068493, start_ticks='17152921', child_pid=4077607, child_start_ticks='17169229',
        argv_sha256='74072825c0bf9d4c7d8abee661a48c156a17c0e936df512a90cee0b212d14db4',
        child_argv_sha256='98eb7b55c5c9797ae3cb2ecb4b77e58a66f43319059a692ed01902f7320bd6c7',
        cwd=str(BASE / 'orch_r166_retelling_C2_20260917_activation4/source')),
    'C5': dict(pid=4015531, start_ticks='17063460', child_pid=4018094, child_start_ticks='17067566',
        argv_sha256='7deeda8ff55b5588f686dcd2248e73049ac55ae0bebc18e64b6e6d3d4582c0af',
        child_argv_sha256='e91e9a82722e3643d5f9aec256e400a66c2d04b3de367da84ee55f91bba83ba3',
        cwd=str(BASE / 'orch_r166_retelling_C5_20260917_recovery2/source')),
}


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
    require(label in EXPECTED and os.getuid() == 2524, 'explicit_two_controller_scope')
    expected = EXPECTED[label]
    holder = process_identity(expected['pid'])
    require(all(holder[key] == expected[key] for key in ('pid', 'start_ticks', 'argv_sha256', 'cwd')),
            'exact_holder_identity_argv_cwd')
    require(holder['uid'] == 2524 and holder['parent'] == 1
            and holder['group'] == holder['session'] == holder['pid'], 'orphan_outer_owned_session_only')
    require(holder['signals'] == dict(SigCgt='0000000000000002', SigIgn='0000000001001000',
            SigBlk='0000000000000000', Threads='1'), 'exact_default_unblocked_SIGTERM_single_thread')
    child = process_identity(expected['child_pid'])
    require(child['start_ticks'] == expected['child_start_ticks'] and child['uid'] == 0
            and child['parent'] == holder['pid'] and child['group'] == child['session'] == holder['pid']
            and child['argv_sha256'] == expected['child_argv_sha256'], 'exact_untouched_sudo_wait_child')
    children = (Path('/proc') / str(holder['pid']) / 'task' / str(holder['pid']) / 'children').read_text().split()
    require(children == [str(child['pid'])], 'one_exact_wait_child_only')
    require(child['argv'][:6] == ['sudo', '-n', 'systemd-run', '--quiet', '--wait', '--pipe']
            and '--unit=' + config['device_containment']['unit'] in child['argv'], 'actual_wait_pipe_service_unit')
    recorded = read(Path(config['attempt_dir']) / 'CONTAINED_COMMAND.json')
    require(child['argv'] == recorded['command'], 'actual_wait_command_matches_original_receipt')
    for process in pair.values():
        actual = process_identity(process['pid'])
        require(actual['start_ticks'] == process['start_ticks'] and actual['session'] != holder['session']
                and actual['cgroup'] == '0::/system.slice/' + config['device_containment']['unit'] + '.service',
                'native_service_outside_CPU_controller_session')
    source = passive_source(Path(holder['cwd']) / 'gpu/orch_r166_retelling_handoff.py')
    lock = lock_identity(BASE / ('orch_r157_' + label + '_HANDOFF.lock'))
    require(flock_owners(lock) == [holder['pid']], 'genuine_same_inode_legacy_holder')
    return dict(label=label, holder=holder, wait_child=child, lock=lock, source_proof=source)


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


def authorize(output, go_path, go_sha256):
    require(go_path is not None and go_sha256 is not None and sha(go_path) == go_sha256,
            'explicit_Main_controller_addendum_exact_bytes_before_signals')
    go = read(go_path)
    require(go['schema'] == 'R179_NODE5_CONTROLLER_TRANSFER_ADDENDUM_V1' and go['approved'] is True
            and go['output'] == str(output) and go['label'] in EXPECTED
            and time.time() < go['expires_unix'] <= read(output / 'PLAN.json')['hard_end_unix'],
            'bound_unexpired_narrow_controller_addendum')
    names = ('READY.json', 'controller_transfer.py', 'rollout_operator.py', 'CONTROLLER_BINDING.json',
             'CONTROLLER_PREFLIGHT.json', 'DEVICE_CPU.json', 'DETACH_CPU_INTEGRATION.json')
    require(set(go['files']) == set(names) and all(sha(output / name) == go['files'][name] for name in names),
            'Main_bound_operator_helper_receiving_preflight_bytes')
    require(read(output / 'CONTROLLER_BINDING.json')['label'] == go['label'], 'addendum_matches_life')
    device, integration = read(output / 'DEVICE_CPU.json'), read(output / 'DETACH_CPU_INTEGRATION.json')
    require(device['status'] == integration['status'] == 'PASS' and device['model_loaded'] is False
            and integration['real_systemd_wait_pipe'] is True and integration['service_survived_outer_SIGTERM'] is True,
            'receiving_device_and_real_CPU_detach_proofs')
    return reference(go_path)


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
