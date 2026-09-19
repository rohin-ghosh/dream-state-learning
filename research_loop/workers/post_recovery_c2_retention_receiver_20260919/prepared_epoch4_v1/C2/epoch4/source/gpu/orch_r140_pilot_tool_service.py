"""Bounded local operator service for an EXISTING R127 TRAIN pilot.

No model, parent, journal, sandbox-policy, or remote administration changes.
An interrupted intent poisons its namespace: inspect evidence manually; never
delete state or change namespaces to replay an uncertain operation.
"""

import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import re
import signal
import stat
import sys
import time

from gpu import orch_r125_cpu_experiment as cpu
from gpu import orch_r127_pilot_console as console
from organism_v6.orch_r125_experiment_request import make_request, MAX_INPUT_BYTES


SCHEMA = 'R140_PILOT_TOOL_SERVICE_V1'
RECORD_LIMIT = 32 * 1024 * 1024
OUTPUT_RESERVATION = 65536
DISPATCH_RESERVATION = 75
CONFIG_KEYS = {'root', 'journal_id', 'journal_manifest_sha256', 'start_index',
    'start_after_sha256', 'spool', 'state', 'gate_root', 'gate_sha256', 'source_closure_sha256',
    'wall_seconds', 'poll_seconds', 'max_polls', 'max_inspections', 'max_calls',
    'max_request_bytes', 'max_output_bytes'}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(document):
    return (json.dumps(document, sort_keys=True, ensure_ascii=False,
                       separators=(',', ':'), allow_nan=False) + '\n').encode('utf-8')


def canonical_path(value):
    cpu.require(type(value) is str, 'path_string_required')
    path = Path(value)
    cpu.require(path.is_absolute() and '..' not in path.parts
                and path.resolve() == path, 'absolute_symlink_free_path_required')
    return path


def closure():
    modules = {'service': sys.modules[__name__], 'pilot_console': console,
        'stream_console': sys.modules[console._open_stream_directory.__module__],
        'stream_journal': sys.modules[console.require.__module__]}
    return dict(cpu.source_closure(), **{name: sha(cpu.read_regular(module.__file__, 1048576))
                                       for name, module in modules.items()})


def code_policy(config):
    policy = config.get('code_policy', cpu.code_blocks.LEGACY)
    cpu.require(policy in (cpu.code_blocks.LEGACY, cpu.code_blocks.POLICY), 'known_code_policy')
    return policy


def pins(root, gate_root, start_index, *, code_policy=cpu.code_blocks.LEGACY):
    root, gate_root = canonical_path(str(root)), canonical_path(str(gate_root))
    cpu.require(code_policy in (cpu.code_blocks.LEGACY, cpu.code_blocks.POLICY), 'known_code_policy')
    minimum = 1 if code_policy == cpu.code_blocks.POLICY else 1699
    cpu.require(type(start_index) is int and minimum <= start_index <= 10**18, 'start_strictly_after_1698')
    with console._directory(root / 'stream') as directory:
        raw = console._read(directory, 'JOURNAL.json', 4096)
    manifest = cpu.read_document(raw)
    cpu.require(set(manifest) == {'schema', 'journal_id'}
                and manifest['schema'] == 'R125_STREAM_JOURNAL_V1'
                and re.fullmatch('[0-9a-f]{32}', manifest['journal_id']), 'journal_manifest')
    for name in ('records', 'inbox'):
        with console._open_stream_directory(root, name):
            pass
    with console._open_stream_directory(root, 'records') as (directory, unused_path):
        prefix_raw = console._read(directory, f'{start_index - 1:020d}.json', RECORD_LIMIT)
    prefix = cpu.read_document(prefix_raw)
    cpu.require(prefix['schema'] == manifest['schema'] and prefix['journal_id'] == manifest['journal_id']
                and type(prefix['index']) is int and prefix['index'] == start_index - 1
                and prefix['sha256'] == cpu.digest({key: value for key, value in prefix.items() if key != 'sha256'}),
                'pinned_start_prefix_record')
    return dict(journal_id=manifest['journal_id'], journal_manifest_sha256=sha(raw),
                start_after_sha256=sha(prefix_raw),
                gate_sha256=cpu.digest(cpu.verify_gate(gate_root)),
                source_closure_sha256=cpu.digest(closure()))


def validate_config(config):
    cpu.require(type(config) is dict and set(config) in (CONFIG_KEYS, CONFIG_KEYS | {'code_policy'}), 'exact_config_fields')
    policy = code_policy(config)
    paths = [canonical_path(config[key]) for key in ('root', 'gate_root', 'state', 'spool')]
    for position, path in enumerate(paths):
        for other in paths[position + 1:]:
            cpu.require(path != other and path not in other.parents and other not in path.parents,
                        'disjoint_root_gate_state_spool_required')
    for key, minimum, maximum in (
        ('start_index', 1 if policy == cpu.code_blocks.POLICY else 1699, 10**18), ('wall_seconds', 1, 3600),
        ('max_polls', 1, 10000), ('max_inspections', 1, 10000), ('max_calls', 1, 100),
        ('max_request_bytes', 1, 100 * MAX_INPUT_BYTES),
        ('max_output_bytes', 1, 100 * OUTPUT_RESERVATION)):
        cpu.require(type(config[key]) is int and minimum <= config[key] <= maximum, 'bounded_' + key)
    cpu.require(type(config['poll_seconds']) in (float, int)
                and 0.05 <= config['poll_seconds'] <= 60, 'bounded_poll_seconds')
    actual = (pins(config['root'], config['gate_root'], config['start_index'])
              if policy == cpu.code_blocks.LEGACY else
              pins(config['root'], config['gate_root'], config['start_index'], code_policy=policy))
    cpu.require(all(config[key] == value for key, value in actual.items()), 'pinned_gate_source_or_journal_changed')
    return actual


def store(path, raw, *, replace=False):
    with console._directory(path.parent) as directory:
        if not replace:
            console._stage(directory, path.name, raw)
            return
        temporary = path.name + '.next'
        console._stage(directory, temporary, raw)
        os.replace(temporary, path.name, src_dir_fd=directory, dst_dir_fd=directory)
        os.fsync(directory)


def save_state(directory, state):
    store(directory / 'STATE.json', encoded(state), replace=True)


def private_directory(path):
    with console._directory(path) as directory:
        metadata = os.fstat(directory)
        cpu.require(metadata.st_uid == os.geteuid() and metadata.st_mode & 0o077 == 0,
                    'owner_private_directory_required')


def mkdir_durable(path):
    path.mkdir(mode=0o700)
    with console._directory(path.parent) as parent:
        os.fsync(parent)


@contextmanager
def namespace(config):
    directory, spool = Path(config['state']), Path(config['spool'])
    fresh = not directory.exists()
    if fresh:
        cpu.require(not spool.exists(), 'new_spool_required')
        mkdir_durable(directory)
    private_directory(directory)
    with console._directory(directory) as descriptor:
        lock = os.open('SERVICE.lock', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK,
                       0o600, dir_fd=descriptor)
        try:
            metadata = os.fstat(lock)
            cpu.require(stat.S_ISREG(metadata.st_mode) and metadata.st_nlink == 1
                        and metadata.st_uid == os.geteuid() and metadata.st_mode & 0o077 == 0,
                        'private_service_lock')
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            if fresh:
                mkdir_durable(spool)
                store(spool / 'SERVICE_OWNER.json', encoded(config))
                store(directory / 'CONFIG.json', encoded(config))
                state = dict(schema=SCHEMA, config_sha256=sha(encoded(config)), phase='READY',
                    next_index=config['start_index'], polls=0, inspections=0, calls=0,
                    request_bytes=0, output_reserved=0,
                    deadline_unix=time.time() + config['wall_seconds'],
                    deadline_monotonic=time.monotonic() + config['wall_seconds'])
                save_state(directory, state)
            private_directory(spool)
            for path in (directory / 'CONFIG.json', spool / 'SERVICE_OWNER.json'):
                cpu.require(cpu.read_regular(path, 16384) == encoded(config), 'namespace_config_changed')
            state = cpu.read_document(cpu.read_regular(directory / 'STATE.json', 16384))
            cpu.require(state['schema'] == SCHEMA and state['config_sha256'] == sha(encoded(config)),
                        'state_config_binding')
            yield directory, state
        finally:
            os.close(lock)


def experiment(raw, *, code_policy=cpu.code_blocks.LEGACY):
    """Recognize only a top-level exact fence; never strip or repair source."""
    cpu.require(type(raw) is str, 'response_raw_string')
    cpu.require(code_policy in (cpu.code_blocks.LEGACY, cpu.code_blocks.POLICY), 'known_code_policy')
    if code_policy == cpu.code_blocks.POLICY:
        block = cpu.code_blocks.extract(raw)
        return block['attempted'], block['source']
    active = None
    attempts, sources = [], []
    position = 0
    for line in raw.splitlines(keepends=True):
        matched = re.match(r'^[ \t]*(`{3,}|~{3,})([^\r\n]*)', line)
        if matched:
            marker, label = matched.groups()
            attempted = label.strip() == 'python experiment'
            if attempted and (active is None or active[2]):
                attempts.append(position)
            if active is None:
                exact = line == '```python experiment\n'
                active = (marker, position + len(line), exact, label == 'python')
            elif not label.strip() and marker[0] == active[0][0] and len(marker) >= len(active[0]):
                if active[2] and re.fullmatch(r'```[ \t]*(?:\n|$)', line):
                    sources.append(raw[active[1]:position])
                active = None
            elif active[2]:
                active = (active[0], active[1], False, active[3])
        elif (active is not None and active[3] and position == active[1]
              and re.fullmatch(r'python experiment(?:\r?\n|$)', line)):
            attempts.append(position)
        position += len(line)
    if not attempts:
        return False, None
    return True, sources[0] if len(attempts) == len(sources) == 1 else None


def inspect(config, index, evidence):
    snapshots, records = {}, {}
    proof = dict(schema=SCHEMA, index=index, journal_id=config['journal_id'],
                 records={}, provenance_valid=False)
    source, attempted = None, False
    try:
        with console._open_stream_directory(config['root'], 'records') as (directory, unused_path):
            for number, label in ((index, 'RESPONSE'), (index - 1, 'REQUEST'), (index + 1, 'COMMITTED')):
                cpu.require(number >= 0, 'response_has_request_predecessor')
                raw = console._read(directory, f'{number:020d}.json', RECORD_LIMIT)
                snapshots[number] = raw
                store(evidence / (label + '.record.json'), raw)
                proof['records'][label] = dict(path=str(evidence / (label + '.record.json')), sha256=sha(raw))
                records[label] = cpu.read_document(raw)
                if label == 'RESPONSE' and records[label].get('kind') != 'RESPONSE':
                    proof['disposition'] = 'NOT_RESPONSE'
                    return None, proof
        cpu.require(all(record.get('journal_id') == config['journal_id'] for record in records.values()),
                    'pinned_journal_id')
        response = records['RESPONSE']
        raw_text = response['document']['response']['raw']
        policy = code_policy(config)
        attempted, source = experiment(raw_text, code_policy=policy)
        origin = dict(kind='TRAIN_CHILD_RESPONSE', record_index=index, record_sha256=response['sha256'])
        candidate = dict(origin=origin, source=source if source is not None else '')
        try:
            verified = (cpu.verify_origin(candidate, config['root']) if policy == cpu.code_blocks.LEGACY
                        else cpu.verify_origin(candidate, config['root'], code_policy=policy))
        except ValueError as error:
            if str(error) != 'one_explicit_experiment_block_matches_source':
                raise
            cpu.require(source is None, 'strict_and_existing_fence_disagree')
            verified = dict(kind=origin['kind'], child_generated=True, journal_id=config['journal_id'],
                record_sha256=response['sha256'], request_record_sha256=records['REQUEST']['sha256'],
                commit_record_sha256=records['COMMITTED']['sha256'])
        with console._open_stream_directory(config['root'], 'records') as (directory, unused_path):
            for number, raw in snapshots.items():
                cpu.require(console._read(directory, f'{number:020d}.json', RECORD_LIMIT) == raw,
                            'origin_changed_during_validation')
        proof.update(provenance_valid=True, origin=verified, attempted=attempted,
                     raw_text_sha256=sha(raw_text.encode('utf-8')))
        if policy == cpu.code_blocks.POLICY:
            proof['code_transformation'] = cpu.code_blocks.metadata(cpu.code_blocks.extract(raw_text))
        if not attempted:
            proof['disposition'] = 'NO_EXPLICIT_REQUEST'
            return None, proof
        if source is None:
            proof.update(disposition='REJECTED', reason='malformed_or_multiple_experiment_fences')
            return None, proof
        try:
            request = make_request(source, origin)
            request_raw = encoded(request)
            cpu.parse_request(request_raw)
        except ValueError as error:
            proof.update(disposition='REJECTED', reason=str(error))
            return None, proof
        proof.update(disposition='REQUEST', request_id=request['request_id'], source_sha256=request['source_sha256'])
        return request_raw, proof
    except (ValueError, OSError, KeyError, TypeError, UnicodeError, RecursionError) as error:
        proof.update(disposition='INVALID_ORIGIN', provenance_valid=False,
                     reason=type(error).__name__ + ': ' + str(error))
        return None, proof


def pending_tail(config, index, state):
    with console._open_stream_directory(config['root'], 'records') as (directory, unused_path):
        try:
            raw = console._read(directory, f'{index:020d}.json', RECORD_LIMIT)
            response = cpu.read_document(raw)
        except (OSError, ValueError, UnicodeError, RecursionError):
            return False
        if state.get('pending_index') == index:
            cpu.require(state['pending_response_sha256'] == sha(raw), 'pending_response_changed')
        if response.get('kind') != 'RESPONSE':
            return False
        try:
            os.stat(f'{index + 1:020d}.json', dir_fd=directory, follow_symlinks=False)
        except FileNotFoundError:
            state.update(pending_index=index, pending_response_sha256=sha(raw))
            return True
        return False


class WallExpired(BaseException):
    pass


@contextmanager
def hard_wall(seconds):
    def expired(signum, frame):
        raise WallExpired()

    cpu.require(signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0), 'existing_alarm_forbidden')
    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, max(0.001, seconds))
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def dispatch_worker(raw, config, evidence):
    signal.signal(signal.SIGALRM, signal.SIG_DFL)
    try:
        policy = code_policy(config)
        options = {} if policy == cpu.code_blocks.LEGACY else dict(code_policy=policy)
        result = cpu.run_request(raw, Path(config['spool']), Path(config['gate_root']), Path(config['root']), **options)
        request = cpu.parse_request(raw)
        original = cpu.read_regular(Path(config['spool']) / request['request_id'] / 'RESULT.json', console.RECEIPT_LIMIT)
        cpu.require(cpu.read_document(original) == result, 'dispatcher_result_file_mismatch')
        store(evidence / 'RESULT.json', original)
    except Exception as error:
        store(evidence / 'WORKER_ERROR.json', encoded(dict(error_type=type(error).__name__, error=str(error))))


def dispatch(raw, config, evidence, remaining):
    process = multiprocessing.get_context('fork').Process(target=dispatch_worker, args=(raw, config, evidence))
    try:
        process.start()
        process.join(max(0, remaining - 1))
        cpu.require(not process.is_alive() and process.exitcode == 0, 'uncertain_dispatch_no_retry')
        return cpu.read_regular(evidence / 'RESULT.json', console.RECEIPT_LIMIT)
    finally:
        if process.pid is not None and process.is_alive():
            process.terminate()
            process.join(0.2)
            if process.is_alive():
                process.kill()
                process.join(0.2)
        if process.pid is not None and not process.is_alive():
            process.close()


def validate_result(raw, request_raw, config, proof):
    result, request = cpu.read_document(raw), cpu.parse_request(request_raw)
    root = Path(config['spool']) / request['request_id']
    unit = 'orch-r125-cpu-' + sha(str(root).encode())[:16]
    for key, expected in dict(schema='R125_CPU_EXPERIMENT_RESULT_V1',
        request_id=request['request_id'], source_sha256=request['source_sha256'],
        raw_request_sha256=sha(request_raw), requested_origin=request['origin'], origin=proof['origin'],
        source_closure_sha256=cpu.source_closure(), command=cpu.profile.command(root, unit)).items():
        cpu.require(result.get(key) == expected, 'result_binding_' + key)
    cpu.require(result.get('GPU_access') is False and result.get('environment_injected') is False
                and result.get('output_is_untrusted') is True, 'cpu_only_result')
    cpu.require(cpu.digest(result['gate']) == config['gate_sha256'], 'result_gate_binding')
    cpu.require(result['status'] in ('COMPLETE', 'PROCESS_FAILED', 'TIMEOUT', 'OUTPUT_LIMIT')
                and result.get('cgroup_removed_after_stop') is True
                and result.get('teardown_error') is None, 'uncertain_result_no_publication')
    cpu.require(type(result.get('retained_bytes')) is int
                and 0 <= result['retained_bytes'] <= OUTPUT_RESERVATION, 'result_output_limit')
    console._summary(result)
    cpu.require(len(result.get('stdout', '')) + len(result.get('stderr', '')) <= OUTPUT_RESERVATION,
                'result_text_limit')


def run(config):
    validate_config(config)
    with namespace(config) as (directory, state):
        if state['phase'] != 'READY':
            return dict(status='STOPPED_NO_REPLAY', state=state)
        remaining = min(config['wall_seconds'], state['deadline_unix'] - time.time(),
                        state['deadline_monotonic'] - time.monotonic())
        deadline = time.monotonic() + max(0, remaining)

        def left():
            return max(0, min(deadline - time.monotonic(), state['deadline_unix'] - time.time()))

        def stop(reason):
            state.update(phase='STOPPED', reason=reason)
            save_state(directory, state)

        if remaining <= 0:
            stop('WALL_LIMIT')
            return dict(status=state['phase'], state=state)
        try:
            with hard_wall(remaining):
                while True:
                    reason = next((label for condition, label in (
                        (left() <= 0, 'WALL_LIMIT'),
                        (state['calls'] >= config['max_calls'], 'CALL_LIMIT'),
                        (state['inspections'] >= config['max_inspections'], 'INSPECTION_LIMIT'),
                        (state['polls'] >= config['max_polls'], 'POLL_LIMIT')) if condition), None)
                    if reason:
                        stop(reason)
                        break
                    state['polls'] += 1
                    save_state(directory, state)
                    index = state['next_index']
                    with console._open_stream_directory(config['root'], 'records') as (records, unused_path):
                        try:
                            os.stat(f'{index:020d}.json', dir_fd=records, follow_symlinks=False)
                        except FileNotFoundError:
                            time.sleep(min(config['poll_seconds'], left()))
                            continue
                    state.update(inspections=state['inspections'] + 1)
                    save_state(directory, state)
                    if pending_tail(config, index, state):
                        save_state(directory, state)
                        time.sleep(min(config['poll_seconds'], left()))
                        continue
                    state.update(phase='INSPECT_INTENT')
                    save_state(directory, state)
                    evidence = directory / f'{index:020d}'
                    mkdir_durable(evidence)
                    validate_config(config)
                    request_raw, proof = inspect(config, index, evidence)
                    if state.get('pending_index') == index and proof['provenance_valid']:
                        cpu.require(proof['records']['RESPONSE']['sha256'] == state['pending_response_sha256'],
                                    'pending_response_changed')
                    store(evidence / 'PROOF.json', encoded(proof))
                    publish_path = None
                    if request_raw is not None:
                        if left() < DISPATCH_RESERVATION:
                            stop('WALL_RESERVE')
                            break
                        if state['request_bytes'] + len(request_raw) > config['max_request_bytes']:
                            stop('REQUEST_BYTE_LIMIT')
                            break
                        if state['output_reserved'] + OUTPUT_RESERVATION > config['max_output_bytes']:
                            stop('OUTPUT_BUDGET_LIMIT')
                            break
                        store(evidence / 'REQUEST.json', request_raw)
                        store(evidence / 'source.py', cpu.parse_request(request_raw)['source'].encode('utf-8'))
                        validate_config(config)
                        state.update(phase='DISPATCH_INTENT', calls=state['calls'] + 1,
                            request_bytes=state['request_bytes'] + len(request_raw),
                            output_reserved=state['output_reserved'] + OUTPUT_RESERVATION)
                        save_state(directory, state)
                        result_raw = dispatch(request_raw, config, evidence, left())
                        cpu.require(cpu.read_regular(evidence / 'RESULT.json', console.RECEIPT_LIMIT) == result_raw,
                                    'persisted_result_required')
                        validate_config(config)
                        validate_result(result_raw, request_raw, config, proof)
                        publish_path = evidence / 'RESULT.json'
                    elif proof['provenance_valid'] and proof['disposition'] == 'REJECTED':
                        receipt = dict(schema='R140_EXPERIMENT_VALIDATION_V1', status='REJECTED',
                            validation_only=True, executed=False, reason=proof['reason'],
                            original_records=proof['records'], origin=proof['origin'],
                            proof=dict(path=str(evidence / 'PROOF.json'), sha256=sha(encoded(proof))))
                        publish_path = evidence / 'REJECTED.json'
                        store(publish_path, encoded(receipt))
                    if publish_path is not None:
                        validate_config(config)
                        cpu.require(left() > 0, 'publication_after_deadline_forbidden')
                        state.update(phase='PUBLISH_INTENT', publication_path=str(publish_path),
                                     publication_sha256=sha(cpu.read_regular(publish_path, console.RECEIPT_LIMIT)))
                        save_state(directory, state)
                        if request_raw is not None:
                            publication = console.publish_tool(config['root'], publish_path)
                        else:
                            publication = console._inbox(config['root'], 'Tool',
                                'Tool validation status: REJECTED\nNo experiment was executed.\n'
                                + proof['reason'], dict(path=str(publish_path), sha256=state['publication_sha256']))
                        store(evidence / 'PUBLICATION.json', encoded(publication))
                    state.update(phase='READY', next_index=index + 1)
                    state.pop('pending_index', None)
                    state.pop('pending_response_sha256', None)
                    save_state(directory, state)
        except WallExpired:
            return dict(status='WALL_LIMIT_NO_REPLAY', state=state)
        except Exception as error:
            return dict(status='STOPPED_NO_REPLAY', error_type=type(error).__name__, error=str(error), state=state)
        return dict(status=state['phase'], state=state)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    pin = commands.add_parser('pins', help='read-only current journal/gate/source pins; no gate generation')
    pin.add_argument('--root', required=True)
    pin.add_argument('--gate-root', required=True)
    pin.add_argument('--start-index', required=True, type=int)
    pin.add_argument('--code-policy', choices=(cpu.code_blocks.LEGACY, cpu.code_blocks.POLICY),
                     default=cpu.code_blocks.LEGACY)
    for name in ('check', 'run'):
        command = commands.add_parser(name)
        command.add_argument('--config', required=True)
    options = parser.parse_args(argv)
    if options.command == 'pins':
        result = pins(options.root, options.gate_root, options.start_index, code_policy=options.code_policy)
    else:
        config = cpu.read_document(cpu.read_regular(canonical_path(options.config), 16384))
        result = validate_config(config) if options.command == 'check' else run(config)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 1 if result.get('status') in ('STOPPED_NO_REPLAY', 'WALL_LIMIT_NO_REPLAY') else 0


if __name__ == '__main__':
    sys.exit(main())
