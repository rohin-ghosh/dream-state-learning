"""CPU-only prehash/probe with explicit pinned input; no locks, signals or launches."""

import argparse
from contextlib import contextmanager
import importlib
import json
import os
from pathlib import Path
import sys
import threading
import time

import immutable_prefix_proof as bootstrap


REQUEST_SCHEMA = 'R233_PREFIX_PRODUCER_REQUEST_V1'


@contextmanager
def readonly_journal(base, root):
    journal = object.__new__(base)
    journal.root = bootstrap._path(root)
    journal.inbox = journal.root / 'inbox'
    journal._owner = os.getpid()
    journal._mutex = threading.RLock()
    journal._fds = []
    journal._closed = False
    journal._failed = False
    journal._checkpoint_tail = None
    try:
        with bootstrap._directory(journal.root) as (descriptor, chain):
            journal._root_fd = os.dup(descriptor)
            journal._fds.append(journal._root_fd)
        journal._lock_fd = journal._open('WRITER.lock', os.O_RDONLY, journal._root_fd)
        journal._records_fd = journal._open('records', os.O_RDONLY | os.O_DIRECTORY, journal._root_fd)
        journal._inbox_fd = journal._open('inbox', os.O_RDONLY | os.O_DIRECTORY, journal._root_fd)
        journal._manifest = journal._read_json(journal._root_fd, 'JOURNAL.json')
        bootstrap._fields(journal._manifest, ('schema', 'journal_id'), 'manifest_schema')
        bootstrap.require(journal._manifest['schema'] == 'R125_STREAM_JOURNAL_V1', 'manifest_version')
        yield journal
    finally:
        journal.close()


def _output(path, value):
    raw = bootstrap.encoded(value)
    with Path(path).open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return bootstrap.sha(raw)


def execute(arguments):
    bootstrap.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only_environment_required')
    if arguments.command == 'produce':
        request, snapshot = bootstrap.read_pinned(arguments.request, arguments.request_sha256)
        bootstrap._fields(request, ('schema', 'selection', 'source', 'journal_type'), 'producer_request_schema')
        bootstrap.require(request['schema'] == REQUEST_SCHEMA, 'producer_request_version')
        source = request['source']
        journal_type = request['journal_type']
        selection = request['selection']
    elif arguments.command == 'probe':
        guard, snapshot = bootstrap.read_pinned(arguments.guard, arguments.guard_sha256)
        bootstrap._fields(guard, ('schema', 'proof_path', 'proof_sha256', 'binding', 'resume',
            'consumer_context_mode'), 'guard_schema')
        bootstrap.require(guard['schema'] == bootstrap.GUARD_SCHEMA, 'guard_version')
        source = guard['binding']['source']
        journal_type = guard['binding']['journal_type']
        selection = guard['resume']['selection']
    else:
        proof, snapshot = bootstrap.read_pinned(arguments.proof, arguments.proof_sha256, bootstrap.MAX_PROOF_BYTES)
        bootstrap._fields(proof, ('schema', 'binding', 'locations', 'records', 'source_objects', 'sealing_clock'), 'proof_schema')
        bootstrap.require(proof['schema'] == bootstrap.SCHEMA, 'proof_version')
        selection, selection_snapshot = bootstrap.read_pinned(arguments.selection, arguments.selection_sha256)
        source = proof['binding']['source']
        journal_type = proof['binding']['journal_type']
    bootstrap.validate_source(source)
    sys.path.insert(0, source['root'])
    helper = importlib.import_module('gpu.immutable_prefix_proof')
    base = helper.journal_class(source, journal_type)
    helper.validate_source(source)
    started = time.monotonic()
    if arguments.command == 'bind-resume':
        guard = helper.guard_candidate(proof, arguments.proof, arguments.proof_sha256,
            resume_selection=selection, max_advance_records=arguments.max_advance_records,
            max_advance_bytes=arguments.max_advance_bytes, consumer_context_mode=arguments.consumer_context_mode)
        bootstrap._recheck_path(snapshot)
        bootstrap._recheck_path(selection_snapshot)
        guard_sha256 = _output(arguments.guard_candidate_output, guard)
        return dict(status='CANDIDATE_NOT_AUTHORIZATION', guard_candidate_path=arguments.guard_candidate_output,
            guard_candidate_sha256=guard_sha256, prefix_body_reads=0, journal_writes=0,
            selected_complete_index=selection['complete_index'], elapsed_seconds=time.monotonic() - started)
    with readonly_journal(base, selection['root']) as journal:
        if arguments.command == 'produce':
            proof = helper.produce(journal, selection, source, journal_type)
            bootstrap._recheck_path(snapshot)
            proof_sha256 = _output(arguments.proof_output, proof)
            guard = helper.guard_candidate(proof, str(Path(arguments.proof_output).absolute()), proof_sha256)
            guard_sha256 = _output(arguments.guard_candidate_output, guard)
            return dict(status='CANDIDATE_NOT_AUTHORIZATION', proof_path=guard['proof_path'],
                proof_sha256=proof_sha256, guard_candidate_path=str(Path(arguments.guard_candidate_output).absolute()),
                guard_candidate_sha256=guard_sha256, prefix_records=len(proof['records']),
                raw_prefix_bytes_hashed=sum(record['hashed']['bytes'] for record in proof['records']),
                elapsed_seconds=time.monotonic() - started, writer_lock_acquired=False, journal_writes=0)
        from gpu.checkpoint_tail_runtime import scan
        authority = dict(guard_path=arguments.guard, guard_sha256=arguments.guard_sha256)
        admission = None
        if arguments.admission is not None:
            admission = dict(path=arguments.admission, sha256=arguments.admission_sha256,
                field_path=json.loads(arguments.admission_field_path))
        state = scan(journal, selection, prefix_proof=authority, prefix_admission=admission)
        bootstrap._recheck_path(snapshot)
        return dict(status='READ_ONLY_PROBE_NOT_LOADED_OR_DISPATCH', receipt=journal.checkpoint_tail_receipt,
            pending={key: state[key] is not None for key in ('request', 'response', 'sleep_request')},
            inbox_count=len(state['inbox']), elapsed_seconds=time.monotonic() - started,
            writer_lock_acquired=False, journal_writes=0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    producer = commands.add_parser('produce')
    for name in ('request', 'request-sha256', 'proof-output', 'guard-candidate-output'):
        producer.add_argument('--' + name, required=True)
    probe = commands.add_parser('probe')
    for name in ('guard', 'guard-sha256'):
        probe.add_argument('--' + name, required=True)
    for name in ('admission', 'admission-sha256', 'admission-field-path'):
        probe.add_argument('--' + name)
    bind = commands.add_parser('bind-resume')
    bind.add_argument('--consumer-context-mode', default=bootstrap.SAME_NAMESPACE,
        choices=(bootstrap.SAME_NAMESPACE, bootstrap.CROSS_NAMESPACE))
    for name in ('proof', 'proof-sha256', 'selection', 'selection-sha256', 'guard-candidate-output'):
        bind.add_argument('--' + name, required=True)
    for name in ('max-advance-records', 'max-advance-bytes'):
        bind.add_argument('--' + name, type=int, required=True)
    print(json.dumps(execute(parser.parse_args()), sort_keys=True, allow_nan=False))
