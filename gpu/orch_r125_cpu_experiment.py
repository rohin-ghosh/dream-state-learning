"""One-shot, source-bound CPU experiment dispatcher; no live stream injection.

Only the trusted caller selects spool/gate/journal paths. Request JSON supplies
Python source and provenance, never mount/device/environment/command options.
The tested CPU policy cannot access GPUs. Results remain untrusted observations.
"""

import argparse
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys

from gpu import orch_r125_cpu_confinement_probe as profile
from gpu import orch_r153_code_blocks as code_blocks
from gpu.orch_r125_bounded_capture import capture
from organism_v6.orch_r125_experiment_request import parse_request


BASIC_CHECKS = {'clean_environment', 'device_null_allowed', 'device_zero_denied',
    'host_cgroup_hidden', 'no_new_privileges', 'no_unexpected_inherited_fd',
    'nonroot_identity', 'outside_canary_read', 'outside_canary_write', 'peer_environ',
    'peer_root_escape', 'peer_signal_permission', 'private_work_write', 'privilege_escalation',
    'process_limit_enforced', 'readonly_input_read', 'readonly_input_write', 'seccomp_active',
    'socket_inet', 'socket_inet6', 'socket_unix', 'symlink_escape', 'zero_effective_caps'}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_regular(path, maximum):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    with os.fdopen(descriptor, 'rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_size <= maximum, 'bounded_regular_file')
        raw = stream.read(maximum + 1)
        after = os.fstat(stream.fileno())
    require((before.st_ino, before.st_size, before.st_mtime_ns) == (after.st_ino, after.st_size, after.st_mtime_ns)
        and len(raw) == before.st_size, 'file_changed_during_read')
    return raw


def read_document(raw):
    def unique(pairs):
        document = {}
        for key, value in pairs:
            require(key not in document, 'duplicate_evidence_key')
            document[key] = value
        return document

    document = json.loads(raw.decode('utf-8'), object_pairs_hook=unique)
    require(type(document) is dict, 'evidence_object_required')
    digest(document)
    return document


def source_closure():
    modules = {'dispatcher': sys.modules[__name__], 'profile': profile,
        'capture': sys.modules[capture.__module__],
        'request_parser': sys.modules[parse_request.__module__], 'code_blocks': code_blocks}
    return {name: hashlib.sha256(read_regular(Path(module.__file__), 1048576)).hexdigest()
        for name, module in modules.items()}


def verify_origin(request, journal_root, *, code_policy=code_blocks.LEGACY):
    require(code_policy in (code_blocks.LEGACY, code_blocks.POLICY, code_blocks.NFKC_POLICY), 'known_code_policy')
    origin = request['origin']
    if origin['kind'] == 'BUILDER_TEST':
        require(journal_root is None, 'builder_test_cannot_claim_child_journal')
        return {'kind': 'BUILDER_TEST', 'child_generated': False}
    require(journal_root is not None, 'TRAIN_child_requires_journal')
    root = Path(journal_root).absolute()
    require(root.resolve() == root and '..' not in root.parts, 'no_journal_path_symlinks')
    directory = root / 'stream' / 'records'
    require(directory.resolve() == directory, 'no_record_directory_symlinks')
    index = origin['record_index']
    require(index > 0, 'response_has_request_predecessor')
    records = []
    for number in (index - 1, index, index + 1):
        record = read_document(read_regular(directory / f'{number:020d}.json', 33554432))
        require(record['schema'] == 'R125_STREAM_JOURNAL_V1' and type(record['index']) is int
            and record['index'] == number
            and record['sha256'] == digest({key: value for key, value in record.items() if key != 'sha256'}),
            'journal_record_hash')
        records.append(record)
    previous, response, committed = records
    require(previous['kind'] == 'REQUEST' and response['kind'] == 'RESPONSE' and committed['kind'] == 'COMMITTED',
        'committed_TRAIN_response_only')
    require(previous['journal_id'] == response['journal_id'] == committed['journal_id']
        and response['previous_sha256'] == previous['sha256'] and committed['previous_sha256'] == response['sha256'],
        'adjacent_journal_chain')
    require(response['sha256'] == origin['record_sha256'], 'exact_origin_record')
    source_request = {key: value for key, value in previous['document'].items() if key != 'resume_state'}
    require(source_request['split'] == 'TRAIN' and response['document']['request_sha256'] == digest(source_request)
        and committed['document']['source_sha256'] == digest(response['document']), 'TRAIN_request_response_commit_join')
    generation = response['document']['response']
    require(source_request.get('action_policy') != 'R205_CONSOLE_REPLY_ACT_V1',
        'console_reply_is_not_a_tool_action')
    require(generation.get('terminal') is True and generation.get('truncated') is False, 'complete_source_generation')
    if code_policy == code_blocks.LEGACY:
        blocks = re.findall(r'^```python experiment\n(.*?)^```[ \t]*$', generation['raw'], re.MULTILINE | re.DOTALL)
        require(len(blocks) == 1 and blocks[0] == request['source'], 'one_explicit_experiment_block_matches_source')
        transformation = None
    else:
        block = code_blocks.extract(generation['raw'], policy=code_policy)
        require(block['source'] is not None and block['source'] == request['source'],
                'one_explicit_experiment_block_matches_source')
        transformation = code_blocks.metadata(block)
    result = {'kind': origin['kind'], 'child_generated': True, 'journal_id': response['journal_id'],
        'record_sha256': response['sha256'], 'request_record_sha256': previous['sha256'],
        'commit_record_sha256': committed['sha256']}
    if transformation is not None:
        result['code_transformation'] = transformation
    return result


def verify_gate(root):
    root = Path(root).absolute()
    require(root.resolve() == root and '..' not in root.parts, 'no_gate_path_symlinks')
    references = {}
    source = hashlib.sha256(Path(profile.__file__).read_bytes()).hexdigest()
    collector = hashlib.sha256(Path(sys.modules[capture.__module__].__file__).read_bytes()).hexdigest()
    for mode in ('basic', 'output', 'timeout', 'memory', 'files'):
        path = Path(root) / (mode + '.json')
        raw = read_regular(path, 262144)
        receipt = read_document(raw)
        require(receipt['schema'] == profile.SCHEMA and receipt['mode'] == mode and receipt['passed'] is True,
            'five_passing_cpu_modes_required')
        require(receipt['source_sha256'] == source and receipt['capture_source_sha256'] == collector
            and receipt['boot_id_sha256'] == profile.boot_identity(), 'gate_build_and_boot_binding')
        require(receipt['cgroup_removed_after_stop'] is True and receipt['verified_limits'] is True,
            'verified_teardown_and_limits')
        invocation = receipt['command']
        unit = next(argument.removeprefix('--unit=') for argument in invocation if argument.startswith('--unit='))
        filesystem = next(argument.removeprefix('--property=RootDirectory=') for argument in invocation
            if argument.startswith('--property=RootDirectory='))
        require(invocation == profile.command(Path(filesystem).parent, unit), 'same_tested_launch_profile')
        require(receipt['host_observation']['cgroup_files'] == {
            'cpu.max': '25000 100000', 'memory.max': '134217728', 'memory.swap.max': '0', 'pids.max': '8'}, 'exact_cpu_limits')
        require(any(entry.get('attach_type') == 'cgroup_device' for entry in receipt['host_observation']['bpf']),
            'device_BPF_evidence')
        if mode in ('basic', 'files'):
            expected = BASIC_CHECKS if mode == 'basic' else {'file_size_limit', 'scratch_limit'}
            checks = receipt['payload_result']['checks']
            require(set(checks) == expected and receipt['payload_result']['passed'] is True
                and all(value is True for value in checks.values()),
                'negative_and_positive_checks_pass')
        elif mode == 'memory':
            require(receipt['unit_outcome']['Result'] == 'oom-kill', 'actual_memory_limit')
        else:
            require(receipt['capture']['limit_reason'] == {'output': 'OUTPUT_LIMIT', 'timeout': 'TIMEOUT'}[mode]
                and receipt['capture']['teardown_error'] is None, 'actual_output_time_teardown')
        references[mode] = {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest()}
    return references


def stop_owned(unit, root):
    result = subprocess.run(['sudo', '-n', 'systemctl', 'show', unit + '.service',
        '--property=LoadState,RootDirectory'], capture_output=True, text=True, timeout=5)
    fields = dict(line.split('=', 1) for line in result.stdout.splitlines() if '=' in line)
    if fields.get('LoadState') == 'not-found':
        require(result.returncode in (0, 1) and not fields.get('RootDirectory'),
            'unverified_absent_unit')
        return
    result.check_returncode()
    require(fields.get('RootDirectory') == str(root / 'rootfs'), 'refuse_unowned_service_stop')
    subprocess.run(['sudo', '-n', 'systemctl', 'stop', unit + '.service'],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5, check=True)


def run_request(raw, spool, gate_root, journal_root=None, *, code_policy=code_blocks.LEGACY):
    request = parse_request(raw)
    origin = (verify_origin(request, journal_root) if code_policy == code_blocks.LEGACY
              else verify_origin(request, journal_root, code_policy=code_policy))
    gate = verify_gate(gate_root)
    spool = Path(spool).absolute()
    require(spool.resolve() == spool and '..' not in spool.parts, 'trusted_spool_without_symlinks')
    root = spool / request['request_id']
    unit = 'orch-r125-cpu-' + hashlib.sha256(str(root).encode()).hexdigest()[:16]
    invocation = profile.command(root, unit)
    spool.mkdir(mode=0o700, exist_ok=True)
    metadata = spool.stat()
    require(metadata.st_uid == os.geteuid() and metadata.st_mode & 0o022 == 0,
        'private_broker_owned_spool')
    descriptor = os.open(spool / 'DISPATCH.lock', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW
        | os.O_NONBLOCK | os.O_CLOEXEC, 0o600)
    with os.fdopen(descriptor, 'a') as lock:
        metadata = os.fstat(lock.fileno())
        require(stat.S_ISREG(metadata.st_mode) and metadata.st_nlink == 1
            and metadata.st_uid == os.geteuid() and metadata.st_mode & 0o022 == 0,
            'private_regular_dispatch_lock')
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        root.mkdir(mode=0o755, exist_ok=False)
        (root / 'REQUEST.json').write_bytes(raw)
        (root / 'payload.py').write_bytes(request['source'].encode('utf-8'))
        (root / 'readonly.txt').write_text('No external inputs supplied to this CPU-only experiment.')
        (root / 'empty').mkdir(mode=0o755)
        filesystem = root / 'rootfs'
        filesystem.mkdir(mode=0o755)
        for name in ('usr', 'etc', 'proc', 'dev', 'sys', 'run', 'tmp', 'work'):
            (filesystem / name).mkdir(mode=0o755)
        for name in ('bin', 'lib', 'lib64'):
            (filesystem / name).symlink_to('usr/' + name)
        result = dict(schema='R125_CPU_EXPERIMENT_RESULT_V1', request_id=request['request_id'],
            source_sha256=request['source_sha256'], origin=origin, gate=gate, command=invocation,
            requested_origin=request['origin'], source_closure_sha256=source_closure(),
            raw_request_sha256=hashlib.sha256(raw).hexdigest(), status='DISPATCH_INCOMPLETE',
            started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            GPU_access=False, environment_injected=False, output_is_untrusted=True)
        (root / 'INTENT.json').write_text(json.dumps(result, sort_keys=True, indent=2))
        process = None
        launch_attempted = False
        try:
            preflight = subprocess.run(['sudo', '-n', 'systemctl', 'show', unit + '.service', '--property=LoadState'],
                capture_output=True, text=True, timeout=5)
            require(preflight.returncode in (0, 1)
                and preflight.stdout.strip() == 'LoadState=not-found', 'no_existing_unit_reuse')
            launch_attempted = True
            process = subprocess.Popen(invocation, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, close_fds=True)
            captured = capture(process, lambda: stop_owned(unit, root))
            result.update(captured, stdout=captured['stdout'].decode('utf-8', errors='replace'),
                stderr=captured['stderr'].decode('utf-8', errors='replace'))
            result['status'] = captured['limit_reason'] or ('COMPLETE' if captured['returncode'] == 0 else 'PROCESS_FAILED')
            if captured['teardown_error']:
                result['status'] = 'TEARDOWN_UNVERIFIED'
        except Exception as error:
            result.update(status='DISPATCH_FAILED_NO_RETRY', error_type=type(error).__name__, error=str(error))
        finally:
            result['launch_attempted'] = launch_attempted
            if launch_attempted:
                try:
                    stop_owned(unit, root)
                    group = Path('/sys/fs/cgroup/system.slice') / (unit + '.service')
                    result['cgroup_removed_after_stop'] = not group.exists()
                    if group.exists():
                        result['status'] = 'TEARDOWN_UNVERIFIED'
                except Exception as error:
                    result.update(status='TEARDOWN_UNVERIFIED', teardown_error=str(error))
            if process is not None:
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    result.update(status='TEARDOWN_UNVERIFIED', client_exit_verified=False)
                    try:
                        process.kill()
                        process.wait(timeout=5)
                    except Exception as error:
                        result['client_cleanup_error'] = str(error)
                finally:
                    for pipe in (process.stdout, process.stderr):
                        if pipe is not None:
                            pipe.close()
            result['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            (root / 'RESULT.json').write_text(json.dumps(result, sort_keys=True, indent=2))
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--spool', type=Path, required=True)
    parser.add_argument('--gate-root', type=Path, required=True)
    parser.add_argument('--journal-root', type=Path)
    options = parser.parse_args()
    result = run_request(read_regular(options.request, 100000), options.spool, options.gate_root, options.journal_root)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result['status'] == 'COMPLETE' else 1


if __name__ == '__main__':
    sys.exit(main())
