"""Finite operator-only R132 bridge sidecar with R145 journal compatibility.

An interrupted dispatch includes possible publication: never replay its intent.
The child, executor, runtime, gate and sandbox policy are never modified here.
"""

import argparse
from contextlib import contextmanager
import datetime
import fcntl
import json
import math
import os
from pathlib import Path
import stat
import subprocess
import sys
import time
from types import ModuleType
import xml.etree.ElementTree as element_tree

from gpu import orch_r125_cpu_experiment as cpu
from gpu import orch_r127_pilot_console as console
from gpu import orch_r132_kernel_bridge as bridge
from gpu import orch_r132_kernel_executor as executor
from gpu import orch_r140_pilot_tool_service as common


SCHEMA = 'R141_KERNEL_TOOL_SERVICE_V1'
RECORD_LIMIT = common.RECORD_LIMIT
OUTPUT_RESERVATION = 4 * 1048576
POLL_READ_BYTES = 160 * 1048576
CALL_READ_BYTES = 1024 * 1048576
DISPATCH_RESERVE = 180
PIN_KEYS = {'journal_id', 'journal_manifest_sha256', 'start_after_sha256',
            'gate_sha256', 'runtime_manifest_sha256', 'lease_receipt_sha256', 'source_closure'}
BASE_KEYS = {'root', 'state', 'spool', 'source_root', 'runtime_root', 'gate_path',
             'lease_receipt_path', 'start_index', 'gpu_uuid', 'device_minor',
             'executor_lock', 'main_authorized', 'exclusive_gpu_custody',
             'wall_seconds', 'poll_seconds', 'max_polls', 'max_calls', 'max_reads',
             'max_read_bytes', 'max_request_bytes', 'max_output_bytes',
             'max_runtime_files', 'max_runtime_bytes'}
sha = common.sha
encoded = common.encoded
store = common.store
require = cpu.require


def read(path, limit):
    path = common.canonical_path(str(path))
    with console._directory(path.parent) as directory:
        return console._read(directory, path.name, limit)


def closure():
    pending = [sys.modules[__name__], bridge, executor, common, console, cpu]
    modules = {}
    while pending:
        module = pending.pop()
        if module.__name__ in modules:
            continue
        modules[module.__name__] = module
        for value in vars(module).values():
            name = value.__name__ if isinstance(value, ModuleType) else getattr(value, '__module__', '')
            if isinstance(name, str) and name.startswith(('gpu.', 'organism_v6.')) and name in sys.modules:
                pending.append(sys.modules[name])
    for name in ('gpu', 'organism_v6'):
        if getattr(sys.modules.get(name), '__file__', None):
            modules[name] = sys.modules[name]
    require(len(modules) <= 32, 'bounded_source_closure')
    return {str(Path(module.__file__).resolve()): sha(read(Path(module.__file__).resolve(), 1048576))
            for module in modules.values()}


def base_config(config):
    require(type(config) is dict and set(config) in (BASE_KEYS, BASE_KEYS | PIN_KEYS,
            BASE_KEYS | {'code_policy'}, BASE_KEYS | PIN_KEYS | {'code_policy'}),
            'exact_static_config_fields')
    common.code_policy(config)
    for key in ('root', 'state', 'spool', 'source_root', 'runtime_root', 'gate_path',
                'lease_receipt_path', 'executor_lock'):
        executor.trusted_path(config[key])
    writable = [Path(config[key]) for key in ('state', 'spool')]
    protected = [Path(config[key]) for key in ('root', 'source_root', 'runtime_root',
                                               'gate_path', 'lease_receipt_path', 'executor_lock')]
    for path in writable:
        for other in protected + [item for item in writable if item != path]:
            require(path != other and path not in other.parents and other not in path.parents,
                    'disjoint_operator_paths')
    require(writable[0] != writable[1], 'disjoint_operator_paths')
    require(config['gpu_uuid'] == executor.GPU_UUID and type(config['device_minor']) is int
            and config['device_minor'] == executor.GPU_MINOR
            and config['executor_lock'] == str(executor.LOCK_PATH), 'unchanged_GPU_and_executor_lock')
    require(config['main_authorized'] is True and config['exclusive_gpu_custody'] is True,
            'Main_exclusive_reserved_GPU_custody_required')
    for key, lower, upper in (
        ('start_index', 1, 10**18), ('wall_seconds', 1, 1800), ('max_polls', 1, 10000),
        ('max_calls', 1, 100), ('max_reads', 1, 10**8), ('max_read_bytes', 1, 2**50),
        ('max_request_bytes', 1, 100 * 100000), ('max_output_bytes', 1, 100 * OUTPUT_RESERVATION),
        ('max_runtime_files', 1, 50000), ('max_runtime_bytes', 1, 64 * 1024**3)):
        require(type(config[key]) is int and lower <= config[key] <= upper, 'bounded_' + key)
    require(type(config['poll_seconds']) in (int, float)
            and math.isfinite(config['poll_seconds']) and 0.05 <= config['poll_seconds'] <= 60,
            'bounded_poll_seconds')


def record(config, index):
    raw = read(Path(config['root']) / 'stream/records' / f'{index:020d}.json', RECORD_LIMIT)
    value = cpu.read_document(raw)
    require(value.get('schema') == 'R125_STREAM_JOURNAL_V1'
            and type(value.get('index')) is int and value['index'] == index
            and value.get('sha256') == cpu.digest({key: item for key, item in value.items() if key != 'sha256'}),
            'journal_record_hash')
    if 'journal_id' in config:
        require(value.get('journal_id') == config['journal_id'], 'pinned_journal_id')
    return raw, value


def pin_config(config):
    base_config(config)
    raw = read(Path(config['root']) / 'stream/JOURNAL.json', 4096)
    manifest = cpu.read_document(raw)
    require(set(manifest) == {'schema', 'journal_id'}
            and manifest['schema'] == 'R125_STREAM_JOURNAL_V1'
            and type(manifest['journal_id']) is str and len(manifest['journal_id']) == 32,
            'journal_manifest')
    prefix_raw, prefix = record(config, config['start_index'] - 1)
    require(prefix['journal_id'] == manifest['journal_id'], 'prefix_journal_binding')
    sources = closure()
    require(all(Path(config['source_root']) in Path(path).parents for path in sources),
            'loaded_modules_under_pinned_source_root')
    return dict(config, journal_id=manifest['journal_id'], journal_manifest_sha256=sha(raw),
                start_after_sha256=sha(prefix_raw), source_closure=sources,
                gate_sha256=sha(read(config['gate_path'], 1048576)),
                runtime_manifest_sha256=sha(read(Path(config['runtime_root']) / 'MANIFEST.json', 4194304)),
                lease_receipt_sha256=sha(read(config['lease_receipt_path'], 65536)))


def validate_config(config):
    require(set(config) in (BASE_KEYS | PIN_KEYS, BASE_KEYS | PIN_KEYS | {'code_policy'}), 'pinned_config_required')
    require(pin_config(config) == config, 'static_pin_changed')
    return {'status': 'STATIC_PINS_CHECKED_NOT_ADMITTED', 'config_sha256': sha(encoded(config))}


def limits(config, now):
    gate_raw = read(config['gate_path'], 1048576)
    require(sha(gate_raw) == config['gate_sha256'], 'gate_hash_changed')
    gate = cpu.read_document(gate_raw)
    require(gate.get('schema') == 'R132_GPU_CONFINEMENT_GATE_V1' and gate.get('passed') is True,
            'existing_passing_GPU_gate_required')
    for key in ('observed_unix', 'expires_unix'):
        require(type(gate.get(key)) in (int, float) and math.isfinite(gate[key]), 'finite_gate_clock')
    require(0 <= now - gate['observed_unix'] <= 3600 and now + 150 < gate['expires_unix'],
            'fresh_gate_required_stop_service_only')
    lease_raw = read(config['lease_receipt_path'], 65536)
    require(sha(lease_raw) == config['lease_receipt_sha256'], 'lease_hash_changed')
    lease = cpu.read_document(lease_raw)
    end = datetime.datetime.fromisoformat(lease['conservative_lease_end_utc'])
    require(end.tzinfo is not None and type(lease['margin_seconds']) is int
            and lease['margin_seconds'] >= 21600, 'conservative_lease_margin_required')
    lease_wall = end.timestamp() - lease['margin_seconds']
    require(now + 150 < lease_wall, 'lease_wall_exhausted')
    return gate, lease_wall


@contextmanager
def lock_file(path):
    with console._directory(path.parent) as directory:
        descriptor = os.open(path.name, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                             0o600, dir_fd=directory)
    try:
        metadata = os.fstat(descriptor)
        require(stat.S_ISREG(metadata.st_mode) and metadata.st_nlink == 1
                and metadata.st_uid == os.geteuid() and metadata.st_mode & 0o077 == 0, 'private_lock_required')
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield descriptor
    finally:
        os.close(descriptor)


@contextmanager
def namespace(config):
    directory, spool = Path(config['state']), Path(config['spool'])
    fresh = not directory.exists()
    if fresh:
        require(not spool.exists(), 'fresh_spool_required')
        common.mkdir_durable(directory)
    common.private_directory(directory)
    with lock_file(directory / 'SERVICE.lock'):
        if fresh:
            common.mkdir_durable(spool)
            store(directory / 'CONFIG.json', encoded(config))
            store(spool / 'SERVICE_OWNER.json', encoded(config))
            prefix_raw, prefix = record(config, config['start_index'] - 1)
            store(directory / 'PREDECESSOR.record.json', prefix_raw)
            state = dict(schema=SCHEMA, phase='READY', config_sha256=sha(encoded(config)),
                         next_index=config['start_index'], previous_sha256=prefix['sha256'],
                         polls=0, calls=0, reads=0, read_bytes=0, request_bytes=0, output_reserved=0,
                         deadline_unix=time.time() + config['wall_seconds'],
                         deadline_monotonic=time.monotonic() + config['wall_seconds'])
            common.save_state(directory, state)
        common.private_directory(spool)
        require(read(directory / 'CONFIG.json', 65536) == encoded(config)
                and read(spool / 'SERVICE_OWNER.json', 65536) == encoded(config), 'namespace_config_binding')
        state = cpu.read_document(read(directory / 'STATE.json', 65536))
        require(state['schema'] == SCHEMA and state['config_sha256'] == sha(encoded(config)), 'state_binding')
        require(state['next_index'] >= config['start_index'], 'cursor_before_start')
        for key in ('polls', 'calls', 'reads', 'read_bytes', 'request_bytes', 'output_reserved'):
            require(type(state[key]) is int and state[key] >= 0, 'state_counter')
        yield directory, state


def reserve(config, state, directory, reads, byte_count):
    require(state['reads'] + reads <= config['max_reads'], 'READ_LIMIT')
    require(state['read_bytes'] + byte_count <= config['max_read_bytes'], 'READ_BYTE_LIMIT')
    state['reads'] += reads
    state['read_bytes'] += byte_count
    common.save_state(directory, state)


def inspect(config, index, raw, response):
    policy = common.code_policy(config)
    attempted, source = common.experiment(response['document']['response']['raw'], code_policy=policy)
    previous_raw, previous = record(config, index - 1)
    committed_raw, committed = record(config, index + 1)
    origin = dict(kind='TRAIN_CHILD_RESPONSE', record_index=index, record_sha256=response['sha256'])
    incomplete = False
    try:
        candidate = dict(origin=origin, source=source if source is not None else '')
        verified = (cpu.verify_origin(candidate, config['root']) if policy == cpu.code_blocks.LEGACY
                    else cpu.verify_origin(candidate, config['root'], code_policy=policy))
    except ValueError as error:
        incomplete = str(error) == 'complete_source_generation'
        require(incomplete or (str(error) == 'one_explicit_experiment_block_matches_source' and source is None),
                str(error))
        verified = None
    require(previous['journal_id'] == committed['journal_id'] == config['journal_id'], 'pinned_journal_id')
    snapshots = {'REQUEST': previous_raw, 'RESPONSE': raw, 'COMMITTED': committed_raw}
    for number, snapshot in ((index - 1, previous_raw), (index, raw), (index + 1, committed_raw)):
        require(record(config, number)[0] == snapshot, 'journal_changed_during_inspection')
    if incomplete:
        return None, snapshots, 'INCOMPLETE_GENERATION_NO_EXECUTION'
    if not attempted or source is None:
        return None, snapshots, 'NO_EXACT_REQUEST'
    request = (bridge.child_request(config['root'], index) if policy == cpu.code_blocks.LEGACY
               else bridge.child_request(config['root'], index, code_policy=policy))
    require(request['source'] == source and request['origin'] == origin and verified is not None,
            'exact_bridge_source_required')
    return request, snapshots, 'EXACT_REQUEST'


def runtime_budget(config):
    manifest = cpu.read_document(read(Path(config['runtime_root']) / 'MANIFEST.json', 4194304))
    files = manifest.get('files')
    require(type(files) is dict and 0 < len(files) <= config['max_runtime_files'], 'runtime_file_budget')
    total = 0
    for relative in files:
        require(type(relative) is str and not Path(relative).is_absolute() and '..' not in Path(relative).parts,
                'runtime_manifest_relative_path')
        path = common.canonical_path(str(Path(config['runtime_root']) / relative))
        metadata = path.lstat()
        require(stat.S_ISREG(metadata.st_mode), 'runtime_regular_file')
        total += metadata.st_size
        require(total <= config['max_runtime_bytes'], 'runtime_byte_budget')
    return len(files), total


def census():
    invocation = ['/usr/bin/nvidia-smi', '--id=' + executor.GPU_UUID, '-q', '-x']
    process = subprocess.Popen(invocation, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, close_fds=True)
    try:
        captured = executor.capture(process, process.kill, max_bytes=65536, timeout=10)
        require(captured['returncode'] == 0 and captured['limit_reason'] is None
                and captured['teardown_error'] is None, 'bounded_census_failed')
        tree = element_tree.fromstring(captured['stdout'])
        devices = tree.findall('gpu')
        require(len(devices) == 1 and devices[0].findtext('uuid') == executor.GPU_UUID, 'census_UUID_mismatch')
        processes = devices[0].find('processes')
        require(processes is not None and (processes.text or '').strip() in ('', 'None'),
                'census_process_visibility_required')
        require(not list(processes), 'reserved_GPU_not_empty')
        return captured['stdout']
    finally:
        if process.poll() is None:
            process.kill()
        process.wait(timeout=5)


def admission(config, state, evidence, request):
    runtime_hash = executor.validate_runtime(config['runtime_root'])
    require(runtime_hash == config['runtime_manifest_sha256'], 'runtime_manifest_changed')
    devices = executor.device_identity()
    identity = executor.policy_identity(Path(config['runtime_root']), runtime_hash, devices)
    require(executor.validate_gate(config['gate_path'], identity, time.time()) == config['gate_sha256'],
            'gate_changed_during_validation')
    with lock_file(Path(config['executor_lock'])) as descriptor:
        previous = os.read(descriptor, 65537)
        require(len(previous) <= 65536, 'bounded_executor_lock_receipt')
        observed = time.time()
        if previous:
            last = cpu.read_document(previous)
            require(type(last.get('last_finished_unix')) in (int, float)
                    and observed > last['last_finished_unix'], 'census_after_previous_job_required')
            require(last.get('result_status') not in ('ADMISSION_IN_PROGRESS', 'DISPATCH_INCOMPLETE',
                                                     'TEARDOWN_UNVERIFIED', 'DISPATCH_FAILED_NO_RETRY'),
                    'orphan_executor_intent_Main_reconciliation_required')
        store(evidence / 'EXECUTOR_LOCK_BEFORE.bin', previous)
        require(executor.device_identity() == devices, 'device_mapping_changed_before_census')
        census_raw = census()
        store(evidence / 'CENSUS.xml', census_raw)
        validate_config(config)
        gate, lease_wall = limits(config, time.time())
        require(time.time() - observed <= 30, 'census_too_old_after_validation')
        policy = common.code_policy(config)
        options = {} if policy == cpu.code_blocks.LEGACY else dict(code_policy=policy)
        require(bridge.child_request(config['root'], request['origin']['record_index'], **options) == request,
                'source_changed_before_admission')
        wall = min(lease_wall, state['deadline_unix'], time.time() +
                   max(0, state['deadline_monotonic'] - time.monotonic()))
        value = dict(schema='R132_KERNEL_ADMISSION_V1', main_authorized=True, census_clear=True,
                     gpu_uuid=config['gpu_uuid'], device_minor=config['device_minor'],
                     observed_unix=observed, expires_unix=min(observed + 210, gate['expires_unix'], wall),
                     hard_wall_unix=wall, lease_receipt_path=config['lease_receipt_path'],
                     lease_receipt_sha256=config['lease_receipt_sha256'],
                     request_id=request['request_id'], source_sha256=request['source_sha256'],
                     origin=request['origin'], config_sha256=sha(encoded(config)),
                     census_sha256=sha(census_raw), gate_sha256=config['gate_sha256'],
                     source_closure_sha256=cpu.digest(config['source_closure']))
        path = evidence / 'ADMISSION.json'
        store(path, encoded(value))
        executor.validate_admission(path, time.time())
    return path


def run(config):
    base_config(config)
    with namespace(config) as (directory, state):
        if state['phase'] != 'READY':
            return dict(status='STOPPED_NO_REPLAY', state=state)

        def left():
            return min(state['deadline_unix'] - time.time(), state['deadline_monotonic'] - time.monotonic(),
                       config['wall_seconds'])

        def stop(reason):
            state.update(phase='STOPPED', reason=reason)
            common.save_state(directory, state)

        try:
            require(left() > 0, 'WALL_LIMIT')
            with common.hard_wall(left()):
                while True:
                    require(left() > 0, 'WALL_LIMIT')
                    require(state['calls'] < config['max_calls'], 'CALL_LIMIT')
                    require(state['polls'] < config['max_polls'], 'POLL_LIMIT')
                    reserve(config, state, directory, 100, POLL_READ_BYTES)
                    state['polls'] += 1
                    common.save_state(directory, state)
                    validate_config(config)
                    limits(config, time.time())
                    index = state['next_index']
                    try:
                        raw, value = record(config, index)
                    except FileNotFoundError:
                        time.sleep(min(config['poll_seconds'], max(0, left())))
                        continue
                    require(value['previous_sha256'] == state['previous_sha256'], 'cursor_chain_changed')
                    if 'pending_response_sha256' in state:
                        require(state['pending_response_sha256'] == sha(raw), 'pending_response_changed')
                    if value['kind'] == 'REQUEST':
                        require(value['document']['split'] == 'TRAIN', 'TRAIN_only_stop_before_readout')
                    elif value['kind'] == 'RESPONSE':
                        previous_raw, previous = record(config, index - 1)
                        require(previous['kind'] == 'REQUEST' and previous['document']['split'] == 'TRAIN',
                                'TRAIN_request_required')
                        try:
                            read(Path(config['root']) / 'stream/records' / f'{index + 1:020d}.json', RECORD_LIMIT)
                        except FileNotFoundError:
                            state['pending_response_sha256'] = sha(raw)
                            common.save_state(directory, state)
                            time.sleep(min(config['poll_seconds'], max(0, left())))
                            continue
                        reserve(config, state, directory, 100, CALL_READ_BYTES)
                        request, snapshots, disposition = inspect(config, index, raw, value)
                        if request is None:
                            receipt = encoded(dict(schema=SCHEMA, record_index=index, disposition=disposition,
                                executed=False, published=False,
                                records_sha256={label: sha(snapshot) for label, snapshot in snapshots.items()}))
                            path = directory / f'NO_EXECUTION_{index:020d}.json'
                            if path.exists():
                                require(read(path, 65536) == receipt, 'existing_no_execution_receipt_mismatch')
                            else:
                                store(path, receipt)
                        if request is not None:
                            require(left() > DISPATCH_RESERVE, 'WALL_RESERVE')
                            request_raw = encoded(request)
                            require(state['request_bytes'] + len(request_raw) <= config['max_request_bytes'],
                                    'REQUEST_BYTE_LIMIT')
                            require(state['output_reserved'] + OUTPUT_RESERVATION <= config['max_output_bytes'],
                                    'OUTPUT_BUDGET_LIMIT')
                            reserve(config, state, directory, config['max_runtime_files'] + 1, 4194304)
                            file_count, byte_count = runtime_budget(config)
                            reserve(config, state, directory, 300 + 3 * file_count,
                                    CALL_READ_BYTES + 3 * byte_count)
                            evidence = directory / f'{index:020d}'
                            state.update(phase='INTENT', pending_index=index, request_id=request['request_id'],
                                         calls=state['calls'] + 1,
                                         request_bytes=state['request_bytes'] + len(request_raw),
                                         output_reserved=state['output_reserved'] + OUTPUT_RESERVATION)
                            common.save_state(directory, state)
                            common.mkdir_durable(evidence)
                            store(evidence / 'INTENT.json', encoded(state))
                            for label, snapshot in snapshots.items():
                                store(evidence / (label + '.record.json'), snapshot)
                            store(evidence / 'EXACT_REQUEST.json', request_raw)
                            store(evidence / 'source.py', request['source'].encode('utf-8'))
                            admission_path = admission(config, state, evidence, request)
                            require(left() > DISPATCH_RESERVE, 'WALL_RESERVE')
                            state['phase'] = 'DISPATCH_PUBLICATION_INTENT'
                            common.save_state(directory, state)
                            store(evidence / 'DISPATCH_PUBLICATION_INTENT.json', encoded(state))
                            policy = common.code_policy(config)
                            options = {} if policy == cpu.code_blocks.LEGACY else dict(code_policy=policy)
                            result = bridge.dispatch(config['root'], index, spool=config['spool'],
                                runtime_root=config['runtime_root'], gate_path=config['gate_path'],
                                admission_path=str(admission_path), **options)
                            require(len(encoded(result)) <= 1048576, 'bridge_receipt_output_limit')
                            store(evidence / 'BRIDGE_RECEIPT.json', encoded(result))
                            state['phase'] = 'READY'
                            if result['status'] in ('TEARDOWN_UNVERIFIED', 'DISPATCH_FAILED_NO_RETRY'):
                                stop('Main_reconciliation_required_' + result['status'])
                                break
                        state['last_disposition'] = disposition
                    elif value['kind'] not in ('COMMITTED', 'COMPACTION', 'PRESENTATION', 'INBOX',
                                               'SLEEP_REQUEST', 'SLEEP_COMPLETE', 'WALL_EXTENDED',
                                               'LOADED', 'UPDATE', 'CHECKPOINT', 'TERMINAL',
                                               'TARGET_ELIGIBILITY', 'COMPACTION_SKIPPED',
                                               'CHECKPOINT_METADATA'):
                        raise ValueError('unexpected_journal_kind')
                    state.update(next_index=index + 1, previous_sha256=value['sha256'])
                    state.pop('pending_index', None)
                    state.pop('pending_response_sha256', None)
                    common.save_state(directory, state)
        except common.WallExpired:
            if state['phase'] == 'READY':
                stop('WALL_LIMIT')
            return dict(status='WALL_LIMIT_NO_REPLAY', state=state)
        except Exception as error:
            if state['phase'] == 'READY':
                stop(str(error))
            return dict(status='STOPPED_NO_REPLAY', error_type=type(error).__name__, error=str(error), state=state)
        return dict(status=state['phase'], state=state)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('pins', 'check', 'run'))
    parser.add_argument('--config', required=True)
    options = parser.parse_args(argv)
    config = cpu.read_document(read(options.config, 65536))
    if options.command == 'pins':
        result = pin_config(config)
    elif options.command == 'check':
        result = validate_config(config)
    else:
        metadata = Path(options.config).stat()
        require(metadata.st_uid == os.geteuid() and metadata.st_mode & 0o077 == 0,
                'operator_private_config_required')
        result = run(config)
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))
    return 1 if result.get('status') in ('STOPPED_NO_REPLAY', 'WALL_LIMIT_NO_REPLAY') else 0


if __name__ == '__main__':
    sys.exit(main())
