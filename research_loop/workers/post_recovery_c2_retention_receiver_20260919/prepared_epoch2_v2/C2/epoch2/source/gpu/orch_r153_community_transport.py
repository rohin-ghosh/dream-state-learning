"""Trusted wrapper transport and remote CPU/inbox primitives; no child networking."""

import argparse
import ast
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import re
import selectors
import shlex
import stat
import subprocess
import sys
import tempfile
import time

from gpu import orch_r153_community_exchange as exchange
from gpu import orch_r153_code_blocks as blocks
from gpu import orch_r125_cpu_experiment as cpu
from gpu import orch_r127_pilot_console as console
from organism_v6.orch_r125_experiment_request import make_request


GATE_ROOT = '/localhome/local-rohing/orch_r153_cpu_smoke_20260916t2212z/gate'
WRAPPERS = {'a40r': 'gpu/a40r_ssh.sh', 'ovx2': 'gpu/ovx2_ssh.sh', 'ovx3': 'gpu/ovx3_ssh.sh'}
HOST_PROFILES = {'THREE_A40R_TWO_OVX2': frozenset(('a40r', 'ovx2')), 'ALL5_OVX3': frozenset(('ovx3',))}
MAX_WIRE_BYTES = 128 * 1024 * 1024
MAX_SCAN_RECORDS = 64
EXISTING_LIFE_CPU_POLICY = 'R184_EXISTING_TRAIN_LIFE_CPU_V1'
SOURCES = (
    'gpu/orch_r153_community_transport.py', 'gpu/orch_r153_community_exchange.py',
    'gpu/orch_r153_code_blocks.py', 'gpu/orch_r125_cpu_experiment.py',
    'gpu/orch_r125_cpu_confinement_probe.py', 'gpu/orch_r125_bounded_capture.py',
    'gpu/orch_r127_pilot_console.py', 'gpu/orch_r125_stream_console.py',
    'gpu/orch_r125_stream_journal.py', 'organism_v6/orch_r125_experiment_request.py',
    'organism_v6/orch_r125_continual_stream.py', 'organism_v6/orch_r124_train_history.py',
    'organism_v6/orch_r125_plain_context.py', 'organism_v6/orch_r194_code_target_filter.py',
    'organism_v6/orch_r195_receipt_target_filter.py', 'gpu/orch_r197_correction_ledger.py',
)


def source_pins(repository):
    repository = Path(repository)
    return {name: exchange.sha(cpu.read_regular(repository / name, 2 * 1024 * 1024)) for name in SOURCES}


def validate_gate_root(value):
    exchange.require(type(value) is str and re.fullmatch(
        r'/localhome/local-rohing/orch_r153_cpu_smoke_[0-9]{8}t[0-9]{4}z/gate', value), 'pinned_R153_gate_root')
    return value


def code_route(raw, *, code_policy=blocks.POLICY):
    report = blocks.extract(raw, policy=code_policy)
    if report['source'] is None:
        return 'NONE', report
    kernel = report.get('language') in ('triton', 'cuda', 'c++', 'cpp') or re.search(
            r'(?m)^\s*(?:import\s+triton\b|from\s+triton\b)', report['source'])
    if kernel:
        return 'KERNEL', report
    try:
        tree = ast.parse(report['source'])
    except SyntaxError:
        return 'CPU', report
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(alias.name.split('.')[0] == 'triton' for alias in node.names):
            return 'KERNEL', report
        if isinstance(node, ast.ImportFrom) and (node.module or '').split('.')[0] == 'triton':
            return 'KERNEL', report
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id in ('triton', 'tl'):
            return 'KERNEL', report
    return 'CPU', report


def remote_root(value):
    exchange.require(type(value) is str, 'remote_root_string')
    root = Path(value)
    exchange.require(root.is_absolute() and '..' not in root.parts and root.resolve() == root
                     and any('r153' in part.lower() for part in root.parts), 'new_canonical_R153_life_root')
    return root


def manifest_for(root, journal_id):
    with console._directory(root / 'stream') as directory:
        manifest = exchange.decode(exchange.read_regular(directory, 'JOURNAL.json', 4096))
    exchange.require(manifest == dict(schema='R125_STREAM_JOURNAL_V1', journal_id=journal_id),
                     'pinned_remote_journal')
    return manifest


def pull_committed(root, journal_id, cursor, head_sha256, *, max_records=12, max_bytes=16 * 1024 * 1024):
    root = remote_root(root)
    manifest = manifest_for(root, journal_id)
    exchange.require(type(cursor) is int and 0 <= cursor < 10**18, 'bounded_remote_cursor')
    exchange.identifier(head_sha256)
    exchange.require(type(max_records) is int and 1 <= max_records <= MAX_SCAN_RECORDS
                     and type(max_bytes) is int and 4096 <= max_bytes <= MAX_WIRE_BYTES // 2,
                     'bounded_snapshot_pull')
    snapshots, scanned, used, head = [], 0, 0, head_sha256
    cache = {}
    with console._open_stream_directory(root, 'records') as (directory, unused_path):
        def record_at(number):
            if number not in cache:
                raw = exchange.read_regular(directory, f'{number:020d}.json', exchange.RECORD_LIMIT)
                record = exchange.decode(raw)
                exchange.require(record.get('schema') == manifest['schema']
                    and record.get('journal_id') == journal_id and type(record.get('index')) is int
                    and record['index'] == number
                    and record.get('sha256') == exchange._digest({key: value for key, value in record.items()
                                                                 if key != 'sha256'}), 'remote_record_hash')
                cache[number] = (raw, record)
            return cache[number]

        if cursor:
            exchange.require(record_at(cursor - 1)[1]['sha256'] == head, 'remote_cursor_anchor_changed')
        else:
            exchange.require(head == '0' * 64, 'initial_zero_anchor')
            head = exchange._digest(manifest)
        for number in range(cursor, cursor + max_records):
            try:
                raw, record = record_at(number)
            except FileNotFoundError:
                break
            exchange.require(record['previous_sha256'] == head, 'remote_adjacent_chain')
            snapshot = None
            if record['kind'] == 'COMMITTED' and number >= 2:
                preceding = record_at(number - 1)[1]
                if preceding['kind'] == 'RESPONSE' and record_at(number - 2)[1]['document'].get(
                        'action_policy') != 'R205_CONSOLE_REPLY_ACT_V1':
                    triple = [record_at(index)[1] for index in (number - 2, number - 1, number)]
                    snapshot = dict(manifest=manifest, records=triple)
                    origin = dict(kind='TRAIN_CHILD_RESPONSE', record_index=number - 1,
                                  record_sha256=preceding['sha256'])
                    try:
                        exchange.verify_snapshot('C1', journal_id, origin, snapshot, {}, lambda text: {})
                    except ValueError as error:
                        if str(error) != 'complete_generated_response_required':
                            raise
                        generation = preceding['document']['response']
                        exchange.require(type(generation.get('raw')) is str
                            and generation.get('terminal') is False
                            and type(generation.get('truncated')) is bool,
                            'valid_incomplete_generated_response_required')
                        snapshot = None
            cost = len(raw) + (len(exchange.encoded(snapshot)) if snapshot is not None else 0)
            if used + cost > max_bytes:
                exchange.require(scanned > 0, 'single_record_exceeds_pull_budget')
                break
            used += cost
            scanned += 1
            head = record['sha256']
            if snapshot is not None:
                snapshots.append(snapshot)
        for number, (raw, unused_record) in cache.items():
            exchange.require(exchange.read_regular(directory, f'{number:020d}.json', exchange.RECORD_LIMIT) == raw,
                             'remote_snapshot_changed_during_pull')
    result = dict(schema='R153_COMMITTED_PULL_V1', manifest=manifest, start_cursor=cursor,
                  start_head_sha256=head_sha256, next_cursor=cursor + scanned,
                  head_sha256=head if scanned else head_sha256,
                  scanned_records=scanned, scanned_bytes=used, snapshots=snapshots)
    exchange.require(len(exchange.encoded(result)) <= MAX_WIRE_BYTES, 'wire_response_quota')
    return result


@contextmanager
def cpu_lock(root):
    path = root / 'community_cpu'
    with console._directory(root) as directory:
        try:
            os.mkdir(path.name, mode=0o700, dir_fd=directory)
        except FileExistsError:
            pass
        os.fsync(directory)
    with console._directory(path) as directory:
        current = os.fstat(directory)
        exchange.require(current.st_uid == os.geteuid() and current.st_mode & 0o077 == 0, 'private_cpu_state')
        descriptor = os.open('OWNER.lock', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC,
                             0o600, dir_fd=directory)
        try:
            current = os.fstat(descriptor)
            exchange.require(stat.S_ISREG(current.st_mode) and current.st_nlink == 1, 'regular_cpu_owner_lock')
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                yield None
            else:
                yield path
        finally:
            os.close(descriptor)


def stored_document(path, document=None):
    with console._directory(path.parent) as directory:
        if document is not None:
            exchange.immutable_file(directory, path.name, exchange.encoded(document))
        return exchange.decode(exchange.read_regular(directory, path.name, 2 * 1024 * 1024))


def find_cpu_publication(root, result_path, result_sha256):
    matches = {}
    incomplete = False
    with console._open_stream_directory(root, 'inbox') as (directory, path):
        with os.scandir(directory) as entries:
            names = []
            for position, entry in enumerate(entries):
                exchange.require(position < 16384, 'cpu_publication_scan_quota')
                names.append(entry.name)
        for name in names:
            if not re.fullmatch(r'[0-9a-f]{32}\.(?:json|partial)', name):
                continue
            try:
                raw = console._read(directory, name, console.INBOX_LIMIT)
                message = exchange.decode(raw)
            except (ValueError, OSError):
                incomplete = True
                continue
            source = message.get('source_receipt')
            if source != dict(path=str(result_path), sha256=result_sha256):
                continue
            exchange.require(set(message) == {'schema', 'id', 'text', 'split', 'actor', 'speaker', 'source_receipt'}
                and message['schema'] == console.SCHEMA and message['actor'] == 'environment'
                and message['split'] == 'TRAIN' and message['speaker'] == 'Tool'
                and name.startswith(message['id'] + '.'), 'actual_cpu_publication')
            final = message['id'] + '.json'
            if name.endswith('.partial'):
                try:
                    os.link(name, final, src_dir_fd=directory, dst_dir_fd=directory, follow_symlinks=False)
                    os.fsync(directory)
                except FileExistsError:
                    exchange.require(console._read(directory, final, console.INBOX_LIMIT) == raw,
                                     'cpu_publication_id_conflict')
            matches[message['id']] = dict(id=message['id'], path=str(path / final), sha256=exchange.sha(raw))
    exchange.require(len(matches) <= 1, 'duplicate_cpu_publications')
    return next(iter(matches.values()), None), incomplete


def cpu_once(root, journal_id, origin, gate_sha256, *, gate_root=GATE_ROOT, start=False, artifact_link=None,
             code_policy=blocks.POLICY, root_policy=None):
    exchange.require(code_policy in (blocks.POLICY, blocks.NFKC_POLICY), 'known_code_policy')
    if root_policy is None:
        root = remote_root(root)
    else:
        exchange.require(root_policy == EXISTING_LIFE_CPU_POLICY, 'known_CPU_root_policy')
        exchange.require(type(root) is str, 'remote_root_string')
        root = Path(root)
        exchange.require(root.is_absolute() and '..' not in root.parts and root.resolve() == root,
            'canonical_existing_TRAIN_life_root')
    gate_root = validate_gate_root(gate_root)
    manifest_for(root, journal_id)
    exchange.require(type(start) is bool, 'explicit_cpu_start')
    exchange.identifier(gate_sha256)
    with console._open_stream_directory(root, 'records') as (directory, unused_path):
        response = exchange.decode(exchange.read_regular(directory, f'{origin["record_index"]:020d}.json', exchange.RECORD_LIMIT))
    route, report = code_route(response['document']['response']['raw'], code_policy=code_policy)
    exchange.require(route == 'CPU', 'CPU_only_route_no_kernel_execution')
    request = make_request(report['source'], origin)
    proof = cpu.verify_origin(request, root, code_policy=code_policy)
    exchange.require(proof['journal_id'] == journal_id, 'actual_remote_CPU_origin')
    if artifact_link is not None:
        exchange.require(type(artifact_link) is dict
                         and artifact_link.get('execution_source_sha256') == request['source_sha256'],
                         'artifact_execution_source_join')
    base = dict(schema='R153_CPU_DELIVERY_V1', request_id=request['request_id'], journal_id=journal_id,
                source_sha256=request['source_sha256'], origin=proof, artifact_link=artifact_link, gate_root=gate_root)
    with cpu_lock(root) as state:
        if state is None:
            return dict(base, status='RUNNING', executed=None)
        attempt = state / request['request_id']
        intent = dict(schema='R153_CPU_INTENT_V1', request=request, gate_sha256=gate_sha256, gate_root=gate_root,
                      code_policy=code_policy, artifact_link=artifact_link)
        if root_policy is not None:
            intent['root_policy'] = root_policy
        if not attempt.exists():
            if not start:
                return dict(base, status='NOT_STARTED', executed=False)
            exchange.require(cpu.digest(cpu.verify_gate(gate_root)) == gate_sha256, 'pinned_CPU_gate_changed')
            attempt.mkdir(mode=0o700)
            with console._directory(state) as directory:
                os.fsync(directory)
            stored_document(attempt / 'INTENT.json', intent)
            try:
                cpu.run_request(exchange.encoded(request), state / 'spool', gate_root, root, code_policy=code_policy)
            except Exception as error:
                stored_document(attempt / 'ERROR.json', dict(error_type=type(error).__name__, status='DISPATCH_UNKNOWN_NO_RETRY'))
        else:
            try:
                exchange.require(stored_document(attempt / 'INTENT.json') == intent, 'CPU_intent_conflict')
            except FileNotFoundError:
                return dict(base, status='UNKNOWN_NO_RETRY', executed=None)
        result_path = state / 'spool' / request['request_id'] / 'RESULT.json'
        try:
            result_raw = cpu.read_regular(result_path, console.RECEIPT_LIMIT)
            result = cpu.read_document(result_raw)
        except (ValueError, OSError):
            return dict(base, status='UNKNOWN_NO_RETRY', executed=None)
        exchange.require(result.get('request_id') == request['request_id']
                         and result.get('source_sha256') == request['source_sha256']
                         and result.get('origin') == proof
                         and result.get('raw_request_sha256') == exchange.sha(exchange.encoded(request)),
                         'bound_actual_CPU_result')
        publication, incomplete = find_cpu_publication(root, result_path, exchange.sha(result_raw))
        if publication is None:
            if incomplete:
                return dict(base, status='PUBLICATION_UNKNOWN_NO_RETRY', executed=None)
            stored_document(attempt / 'PUBLISH_INTENT.json', dict(result_sha256=exchange.sha(result_raw)))
            publication = console.publish_tool(root, result_path)
        stored_document(attempt / 'PUBLISHED.json', publication)
        return dict(base, status='PUBLISHED', executed=result.get('launch_attempted'),
                    result_status=result['status'], result_sha256=exchange.sha(result_raw),
                    publication=publication, result=result)


def remote_dispatch(request):
    exchange.require(type(request) is dict and type(request.get('op')) is str, 'remote_operation_required')
    operation = request['op']
    fields = {
        'pull': {'root', 'journal_id', 'cursor', 'head_sha256', 'max_records', 'max_bytes'},
        'install': {'root', 'packet', 'document_sha256'},
        'cpu': {'root', 'journal_id', 'origin', 'gate_sha256', 'start', 'artifact_link'},
    }
    exchange.require(operation in fields and (set(request) == fields[operation] | {'op'}
                     or operation == 'cpu' and fields[operation] | {'op'} <= set(request)
                     <= fields[operation] | {'op', 'gate_root', 'code_policy', 'root_policy'}),
                     'exact_remote_operation')
    arguments = {key: value for key, value in request.items() if key != 'op'}
    if operation == 'pull':
        return pull_committed(**arguments)
    if operation == 'cpu':
        return cpu_once(**arguments)
    root = remote_root(arguments['root'])
    document = delivery_document(root, arguments['packet'])
    exchange.require(exchange.sha(exchange.encoded(document)) == arguments['document_sha256'],
                     'exact_outbound_environment_document')
    return exchange.install_delivery(root, arguments['packet'])


def delivery_document(root, packet):
    exchange.validate_packet(packet)
    return dict(schema=console.SCHEMA, id=packet['handle'], text=packet['text'], split='TRAIN',
                actor='environment', speaker='Tool', source_receipt=dict(
                    path=str(Path(root) / 'community_receipts' / (packet['handle'] + '.json')),
                    sha256=packet['source_sha256']))


def remote_main():
    raw = sys.stdin.buffer.read(MAX_WIRE_BYTES + 1)
    exchange.require(len(raw) <= MAX_WIRE_BYTES, 'bounded_remote_request')
    result = remote_dispatch(exchange.decode(raw))
    output = exchange.encoded(result)
    exchange.require(len(output) <= MAX_WIRE_BYTES, 'bounded_remote_response')
    sys.stdout.buffer.write(output + b'\n')


def run_wrapper(argv, payload, *, timeout=120, max_bytes=MAX_WIRE_BYTES):
    exchange.require(0 < timeout <= 180 and 0 < len(payload) <= MAX_WIRE_BYTES, 'bounded_wrapper_request')
    with tempfile.TemporaryFile() as source:
        source.write(payload)
        source.seek(0)
        process = subprocess.Popen(argv, stdin=source, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
        output, received = bytearray(), 0
        try:
            deadline = time.monotonic() + timeout
            with selectors.DefaultSelector() as selector:
                for name in ('stdout', 'stderr'):
                    pipe = getattr(process, name)
                    os.set_blocking(pipe.fileno(), False)
                    selector.register(pipe, selectors.EVENT_READ, name)
                while selector.get_map() or process.poll() is None:
                    exchange.require(time.monotonic() < deadline, 'wrapper_timeout_remote_effect_unknown')
                    for selected, unused_events in selector.select(0.05):
                        chunk = os.read(selected.fileobj.fileno(), 65536)
                        if not chunk:
                            selector.unregister(selected.fileobj)
                            continue
                        received += len(chunk)
                        exchange.require(received <= max_bytes, 'wrapper_output_limit_remote_effect_unknown')
                        if selected.data == 'stdout':
                            output.extend(chunk)
                exchange.require(process.wait(timeout=1) == 0, 'wrapper_failed_remote_effect_unknown')
        finally:
            if process.poll() is None:
                process.kill()
            process.wait(timeout=5)
            process.stdout.close()
            process.stderr.close()
    return exchange.decode(bytes(output))


class PinnedTransport:
    def __init__(self, repository, hosts):
        self.repository = Path(repository).absolute()
        exchange.require(self.repository.resolve() == self.repository and '..' not in self.repository.parts,
                         'canonical_local_repository')
        exchange.require(type(hosts) is dict and frozenset(hosts) in HOST_PROFILES.values(), 'exact_pinned_host_profile')
        self.hosts = json.loads(exchange.encoded(hosts))
        for host, config in self.hosts.items():
            fields = {'repository', 'wrapper_sha256', 'source_sha256', 'gate_sha256'}
            exchange.require(fields <= set(config) <= fields | {'gate_root', 'code_policy'}
                             and (host != 'ovx3' or 'gate_root' in config),
                             'exact_host_config')
            exchange.require(config.get('code_policy', blocks.POLICY) in (blocks.POLICY, blocks.NFKC_POLICY),
                             'known_code_policy')
            validate_gate_root(config.get('gate_root', GATE_ROOT))
            remote = Path(config['repository'])
            exchange.require(remote.is_absolute() and '..' not in remote.parts, 'absolute_remote_repository')
            exchange.identifier(config['wrapper_sha256'])
            exchange.identifier(config['gate_sha256'])
            exchange.require(set(config['source_sha256']) == set(SOURCES), 'exact_remote_source_closure')
            for value in config['source_sha256'].values():
                exchange.identifier(value)

    def call(self, host, request):
        exchange.require(host in self.hosts, 'only_pinned_host_labels')
        config = self.hosts[host]
        wrapper = self.repository / WRAPPERS[host]
        exchange.require(exchange.sha(cpu.read_regular(wrapper, 65536)) == config['wrapper_sha256'],
                         'trusted_wrapper_changed')
        bootstrap = (
            'import hashlib,json,os,pathlib,sys; '
            'root=pathlib.Path(' + repr(config['repository']) + '); '
            'assert root.is_absolute() and root.resolve()==root; '
            'pins=json.loads(' + repr(json.dumps(config['source_sha256'])) + '); '
            'assert all((root/name).resolve()==root/name and hashlib.sha256((root/name).read_bytes()).hexdigest()==value '
            'for name,value in pins.items()); '
            'os.chdir(root);sys.path.insert(0,str(root)); '
            'from gpu.orch_r153_community_transport import remote_main;remote_main()'
        )
        command = 'python3 -c ' + shlex.quote(bootstrap)
        return run_wrapper(['bash', str(wrapper), command], exchange.encoded(request))

    def pull(self, agent, cursor, head_sha256, *, max_records, max_bytes):
        return self.call(agent['host'], dict(op='pull', root=agent['root'], journal_id=agent['journal_id'],
                         cursor=cursor, head_sha256=head_sha256, max_records=max_records, max_bytes=max_bytes))

    def push(self, agent, packet):
        document = delivery_document(agent['root'], packet)
        return self.call(agent['host'], dict(op='install', root=agent['root'], packet=packet,
                         document_sha256=exchange.sha(exchange.encoded(document))))

    def cpu(self, agent, origin, *, start, artifact_link=None):
        return self.call(agent['host'], dict(op='cpu', root=agent['root'], journal_id=agent['journal_id'],
                         origin=origin, gate_sha256=self.hosts[agent['host']]['gate_sha256'],
                         gate_root=self.hosts[agent['host']].get('gate_root', GATE_ROOT),
                         start=start, artifact_link=artifact_link,
                         **({'code_policy': self.hosts[agent['host']]['code_policy']}
                            if 'code_policy' in self.hosts[agent['host']] else {})))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-pins', type=Path)
    options = parser.parse_args(argv)
    exchange.require(options.source_pins is not None, 'source_pin_command_required')
    print(json.dumps(source_pins(options.source_pins), sort_keys=True, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
