"""Local-only R127 pilot inbox and create-only notes; no execution or delivery.

The caller supplies a NEW pilot root with an existing stream/inbox. This module
does not open a journal, start a child, or automatically publish workspace data.
Notes live in an existing or newly created workspace; immutable result receipts
and retained staging links live in its owner-private sibling NAME.receipts.
Publication errors can leave evidence or an already-published file: never retry
automatically. The pilot journal owns rendering speaker prefixes, not this writer.
"""

import argparse
from contextlib import contextmanager, ExitStack
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import uuid

from gpu.orch_r125_stream_console import _open_stream_directory
from gpu.orch_r125_stream_journal import INBOX_LIMIT, _decode, require

SCHEMA = 'R127_ATTRIBUTED_INBOX_V1'
WORKSPACE_SCHEMA = 'R127_WORKSPACE_RESULT_V1'
NOTE_LIMIT = 16 * 1024
FILE_LIMIT = 64
TOTAL_LIMIT = 1024 * 1024
RECEIPT_LIMIT = 1024 * 1024
SUMMARY_LIMIT = 2048


@contextmanager
def _directory(path):
    path = Path(path)
    require('..' not in path.parts, 'parent_path_component_forbidden')
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK
    with ExitStack() as stack:
        descriptor = os.open(path.anchor if path.is_absolute() else '.', flags)
        stack.callback(os.close, descriptor)
        for component in (path.parts[1:] if path.is_absolute() else path.parts):
            descriptor = os.open(component, flags, dir_fd=descriptor)
            stack.callback(os.close, descriptor)
        yield descriptor


def _bytes(document):
    return (json.dumps(document, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode('utf-8')


def _stage(directory, name, raw):
    descriptor = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                         0o600, dir_fd=directory)
    with os.fdopen(descriptor, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fchmod(stream.fileno(), 0o400)
        os.fsync(stream.fileno())
    os.fsync(directory)


def _publish(directory, path, document):
    raw = _bytes(document)
    identifier = document['id']
    partial, name = identifier + '.partial', identifier + '.json'
    _stage(directory, partial, raw)
    os.link(partial, name, src_dir_fd=directory, dst_dir_fd=directory, follow_symlinks=False)
    os.fsync(directory)
    return dict(id=identifier, path=str(path / name), sha256=hashlib.sha256(raw).hexdigest())


def _inbox(root, speaker, text, source):
    require(type(text) is str and len(text) <= INBOX_LIMIT, 'inbox_size_or_text_type')
    document = dict(schema=SCHEMA, id=uuid.uuid4().hex, text=text, split='TRAIN',
                    actor='parent' if source is None else 'environment',
                    speaker=speaker, source_receipt=source)
    require(len(_bytes(document)) <= INBOX_LIMIT, 'inbox_size_limit')
    with _open_stream_directory(root, 'inbox') as (directory, path):
        return _publish(directory, path, document)


def publish_parent(root, speaker, text):
    """Publish attributed user text without adding metadata to that text."""
    require(type(speaker) is str and speaker in ('Astra', 'Fable', 'Rohin'), 'parent_speaker')
    return _inbox(root, speaker, text, None)


def _read(directory, name, limit):
    descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                         dir_fd=directory)
    with os.fdopen(descriptor, 'rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode), 'regular_file_required')
        require(before.st_size <= limit, 'file_size_limit')
        raw = stream.read(limit + 1)
        after = os.fstat(stream.fileno())
        current = os.stat(name, dir_fd=directory, follow_symlinks=False)
    identities = {(entry.st_dev, entry.st_ino, entry.st_mode, entry.st_size,
                   entry.st_mtime_ns, entry.st_ctime_ns) for entry in (before, after, current)}
    require(len(identities) == 1 and len(raw) == before.st_size, 'file_changed_during_read')
    return raw


def _summary(result):
    require(type(result) is dict, 'receipt_object')
    schema = result.get('schema')
    require(schema in ('R125_CPU_EXPERIMENT_RESULT_V1', WORKSPACE_SCHEMA), 'receipt_schema')
    status = result.get('status')
    require(type(status) is str and status in (
        'COMPLETE', 'DISPATCH_INCOMPLETE', 'PROCESS_FAILED', 'TIMEOUT', 'OUTPUT_LIMIT',
        'TEARDOWN_UNVERIFIED', 'DISPATCH_FAILED_NO_RETRY'), 'receipt_status')
    for field in ('stdout', 'stderr', 'path', 'content', 'error'):
        require(field not in result or type(result[field]) is str, 'receipt_text_field')
    require('returncode' not in result or result['returncode'] is None
            or type(result['returncode']) is int, 'receipt_returncode')
    if schema == WORKSPACE_SCHEMA:
        require(set(result) == {'schema', 'id', 'operation', 'status', 'path', 'content', 'sha256'},
                'workspace_receipt_fields')
        require(type(result['id']) is str and re.fullmatch(r'[0-9a-f]{32}', result['id'])
                and result['operation'] in ('write-note', 'read-note') and status == 'COMPLETE',
                'workspace_receipt_operation')
        require(Path(result['path']).is_absolute() and '..' not in Path(result['path']).parts,
                'workspace_receipt_path')
        _name(Path(result['path']).name)
        content = result['content'].encode('utf-8')
        require(len(content) <= NOTE_LIMIT and result['sha256'] == hashlib.sha256(content).hexdigest(),
                'workspace_receipt_content')
    elif status == 'COMPLETE':
        require(result.get('returncode') == 0 and type(result.get('returncode')) is int
                and 'stdout' in result and 'stderr' in result, 'cpu_complete_evidence')
    else:
        require(any(field in result for field in ('stdout', 'stderr', 'error', 'started_utc')),
                'cpu_result_evidence')
    lines = ['Tool result status: ' + status]
    if 'returncode' in result:
        lines.append('returncode: ' + str(result['returncode']))
    if schema == WORKSPACE_SCHEMA:
        lines.append('operation: ' + result['operation'])
    for field in ('stdout', 'stderr', 'error', 'path', 'content'):
        if result.get(field):
            value = result[field]
            lines.append(field + ': ' + value[:SUMMARY_LIMIT]
                         + ('\n[truncated]' if len(value) > SUMMARY_LIMIT else ''))
    return '\n'.join(lines)


def publish_tool(root, result_path):
    """Explicitly publish a bounded result snapshot, preserving its exact hash."""
    path = Path(result_path)
    require('..' not in path.parts, 'parent_path_component_forbidden')
    with _directory(path.parent) as directory:
        raw = _read(directory, path.name, RECEIPT_LIMIT)
    try:
        text = _summary(_decode(raw))
    except (UnicodeError, RecursionError, TypeError, KeyError) as error:
        raise ValueError('malformed_receipt') from error
    return _inbox(root, 'Tool', text,
                  dict(path=str(path.absolute()), sha256=hashlib.sha256(raw).hexdigest()))


def _name(name):
    require(type(name) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,119}\.(md|txt|py)', name),
            'note_filename')


@contextmanager
def _workspace(workspace):
    path = Path(workspace)
    require('..' not in path.parts and path.name not in ('', '.', '..'), 'workspace_path')
    receipts = path.with_name(path.name + '.receipts')
    with _directory(path.parent) as parent:
        for name in (path.name, receipts.name):
            try:
                os.mkdir(name, mode=0o700, dir_fd=parent)
            except FileExistsError:
                pass
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
        with ExitStack() as stack:
            directory = os.open(path.name, flags, dir_fd=parent)
            stack.callback(os.close, directory)
            receipt_directory = os.open(receipts.name, flags, dir_fd=parent)
            stack.callback(os.close, receipt_directory)
            for descriptor, forbidden in ((directory, 0o022), (receipt_directory, 0o077)):
                metadata = os.fstat(descriptor)
                require(metadata.st_uid == os.geteuid() and not metadata.st_mode & forbidden,
                        'workspace_owner_permissions_required')
            fcntl.flock(directory, fcntl.LOCK_EX)
            yield directory, receipt_directory, path.absolute(), receipts.absolute()


def _inventory(directory):
    total, count = 0, 0
    with os.scandir(directory) as entries:
        for entry in entries:
            _name(entry.name)
            metadata = entry.stat(follow_symlinks=False)
            require(stat.S_ISREG(metadata.st_mode), 'regular_note_required')
            require(metadata.st_size <= NOTE_LIMIT, 'note_size_limit')
            count += 1
            total += metadata.st_size
            require(count <= FILE_LIMIT and total <= TOTAL_LIMIT, 'workspace_capacity')
    return count, total


def _note(workspace, name, text=None):
    _name(name)
    raw = None
    if text is not None:
        require(type(text) is str, 'note_text_type')
        raw = text.encode('utf-8')
        require(len(raw) <= NOTE_LIMIT, 'note_size_limit')
    with _workspace(workspace) as (directory, receipt_directory, path, receipts):
        count, total = _inventory(directory)
        identifier = uuid.uuid4().hex
        if raw is not None:
            require(count < FILE_LIMIT and total + len(raw) <= TOTAL_LIMIT, 'workspace_capacity')
            try:
                os.stat(name, dir_fd=directory, follow_symlinks=False)
            except FileNotFoundError:
                pass
            else:
                raise FileExistsError('note_already_exists')
            partial = identifier + '.note.partial'
            _stage(receipt_directory, partial, raw)
            os.link(partial, name, src_dir_fd=receipt_directory, dst_dir_fd=directory,
                    follow_symlinks=False)
            os.fsync(directory)
        else:
            raw = _read(directory, name, NOTE_LIMIT)
        result = dict(schema=WORKSPACE_SCHEMA, id=identifier,
                      operation='write-note' if text is not None else 'read-note', status='COMPLETE',
                      path=str(path / name), content=raw.decode('utf-8'), sha256=hashlib.sha256(raw).hexdigest())
        return _publish(receipt_directory, receipts, result)


def write_note(workspace, name, text):
    """Create one immutable note and return a receipt reference, never an inbox message."""
    require(type(text) is str, 'note_text_type')
    return _note(workspace, name, text)


def read_note(workspace, name):
    """Snapshot one existing note into a separate immutable receipt; never execute it."""
    return _note(workspace, name)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    parent = commands.add_parser('parent')
    parent.add_argument('--root', required=True)
    parent.add_argument('--speaker', choices=('Astra', 'Fable', 'Rohin'), required=True)
    parent.add_argument('--text', required=True)
    tool = commands.add_parser('tool')
    tool.add_argument('--root', required=True)
    tool.add_argument('--result-path', required=True)
    for command in ('write-note', 'read-note'):
        note = commands.add_parser(command)
        note.add_argument('--workspace', required=True)
        note.add_argument('--name', required=True)
        if command == 'write-note':
            note.add_argument('--text', required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'parent':
            receipt = publish_parent(args.root, args.speaker, args.text)
        elif args.command == 'tool':
            receipt = publish_tool(args.root, args.result_path)
        elif args.command == 'write-note':
            receipt = write_note(args.workspace, args.name, args.text)
        else:
            receipt = read_note(args.workspace, args.name)
        print(json.dumps(receipt, sort_keys=True))
    except (OSError, ValueError) as error:
        print(f'pilot console: operation failed ({type(error).__name__}); inspect artifacts before retrying',
              file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
