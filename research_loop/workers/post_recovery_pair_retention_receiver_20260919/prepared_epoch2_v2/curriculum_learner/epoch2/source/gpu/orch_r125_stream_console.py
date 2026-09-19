"""Publish TRAIN messages or follow child responses without taking a journal lock.

Terminal 1 (read only; replay responses from the beginning, then follow):
  python3 -m gpu.orch_r125_stream_console --root NATIVE_RUN_ROOT --follow
Terminal 2 (publish one message, or omit --text for one message per stdin line):
  python3 -m gpu.orch_r125_stream_console --root NATIVE_RUN_ROOT --text MESSAGE

Follow prints only RESPONSE.document.response.raw, never requests or history.
It reads numbered published records only, not held/readout files or inbox data;
intent and partial files are ignored. Ctrl-C exits. This is not journal recovery.
The existing stream/inbox must be reachable without symlinks. Receipts contain
only the message ID, SHA-256 of the published bytes, and destination path.
Read-only staging hardlinks are retained: unlinking after publication changes
the inode ctime and can race StreamJournal's immutable-file read checks.
"""

import argparse
from contextlib import contextmanager, ExitStack
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import time
import uuid

from gpu.orch_r125_stream_journal import INBOX_LIMIT, SCHEMA, _decode, _digest, require


@contextmanager
def _open_stream_directory(root, name):
    path = Path(root)
    if '..' in path.parts:
        raise ValueError('parent_path_component_forbidden')
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK
    with ExitStack() as stack:
        directory = os.open(path.anchor if path.is_absolute() else '.', flags)
        stack.callback(os.close, directory)
        components = path.parts[1:] if path.is_absolute() else path.parts
        for component in (*components, 'stream', name):
            directory = os.open(component, flags, dir_fd=directory)
            stack.callback(os.close, directory)
        yield directory, path.absolute() / 'stream' / name


def publish(root, text):
    """Publish one immutable message; never inspect child context or journal data.

Failure can leave a staged file or an already-published message. No artifact is
overwritten or removed, and callers must not automatically retry uncertain I/O.
"""
    if type(text) is not str or len(text) > INBOX_LIMIT:
        raise ValueError('inbox_size_or_text_type')
    identifier = uuid.uuid4().hex
    message = dict(id=identifier, text=text, split='TRAIN', actor='parent')
    raw = (json.dumps(message, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode('utf-8')
    if len(raw) > INBOX_LIMIT:
        raise ValueError('inbox_size_limit')
    name = identifier + '.json'
    partial = identifier + '.partial'
    with _open_stream_directory(root, 'inbox') as (directory, inbox):
        descriptor = os.open(partial, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                             mode=0o600, dir_fd=directory)
        with os.fdopen(descriptor, 'wb') as staged:
            staged.write(raw)
            staged.flush()
            os.fchmod(staged.fileno(), 0o400)
            os.fsync(staged.fileno())
        os.fsync(directory)
        os.link(partial, name, src_dir_fd=directory, dst_dir_fd=directory, follow_symlinks=False)
        os.fsync(directory)
        return dict(id=identifier, sha256=hashlib.sha256(raw).hexdigest(), path=str(inbox / name))


def _read_record(directory, index):
    name = f'{index:020d}.json'
    try:
        descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                             dir_fd=directory)
    except FileNotFoundError:
        return None
    with os.fdopen(descriptor, 'rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode), 'regular_record_required')
        raw = stream.read(before.st_size + 1)
        after = os.fstat(stream.fileno())
        current = os.stat(name, dir_fd=directory, follow_symlinks=False)
    identities = {(entry.st_dev, entry.st_ino, entry.st_size, entry.st_mtime_ns)
                  for entry in (before, after, current)}
    require(len(identities) == 1 and len(raw) == before.st_size, 'record_changed_during_read')
    record = _decode(raw)
    require(type(record) is dict and set(record) == {
        'schema', 'journal_id', 'index', 'kind', 'previous_sha256', 'document', 'sha256'},
        'journal_record_fields')
    require(record['schema'] == SCHEMA and type(record['index']) is int and record['index'] == index
            and type(record['journal_id']) is str and re.fullmatch(r'[0-9a-f]{32}', record['journal_id'])
            and type(record['previous_sha256']) is str
            and re.fullmatch(r'[0-9a-f]{64}', record['previous_sha256'])
            and record['sha256'] == _digest({key: value for key, value in record.items() if key != 'sha256'}),
            'journal_record_integrity')
    require(type(record['kind']) is str and re.fullmatch(r'[A-Z][A-Z0-9_]{0,63}', record['kind'])
            and type(record['document']) is dict, 'journal_record_document')
    return record


def follow_responses(root, *, poll_interval=0.25, max_polls=None):
    """Yield raw responses once in order, waiting at the next unpublished index.

    max_polls bounds polling passes for callers that need a finite iterator.
    Validate envelopes, checksums and forward chain continuity, not scheduler
    state. A first record is not externally authenticated. ctime/link-count
    changes from the writer removing its staging hardlink are harmless.
    """
    require(type(poll_interval) in (int, float) and 0 < poll_interval < float('inf'), 'poll_interval')
    require(max_polls is None or type(max_polls) is int and max_polls >= 0, 'max_polls')
    index, polls = 0, 0
    previous, journal_id = None, None
    with _open_stream_directory(root, 'records') as (directory, _):
        while max_polls is None or polls < max_polls:
            while True:
                record = _read_record(directory, index)
                if record is None:
                    break
                require(previous is None or (record['previous_sha256'] == previous
                        and record['journal_id'] == journal_id), 'journal_chain_integrity')
                index += 1
                previous, journal_id = record['sha256'], record['journal_id']
                if record['kind'] == 'RESPONSE':
                    response = record['document'].get('response')
                    require(type(response) is dict and type(response.get('raw')) is str, 'response_raw_text')
                    yield response['raw']
            polls += 1
            if max_polls is None or polls < max_polls:
                time.sleep(poll_interval)


def _lines(stream):
    while True:
        line = stream.readline(INBOX_LIMIT + 1)
        if not line:
            return
        if len(line) > INBOX_LIMIT:
            raise ValueError('inbox_size_limit')
        if line.endswith('\n'):
            line = line[:-1]
            if line.endswith('\r'):
                line = line[:-1]
        yield line


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--root', required=True, help='existing native run root (not its stream directory)')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--text', help='publish exactly one message instead of reading stdin')
    mode.add_argument('--follow', action='store_true', help='read only: replay and follow raw child responses')
    args = parser.parse_args(argv)
    try:
        if args.follow:
            for response in follow_responses(args.root):
                print(response, flush=True)
            return 0
        messages = [args.text] if args.text is not None else _lines(sys.stdin)
        for text in messages:
            receipt = publish(args.root, text)
            print(json.dumps(receipt, sort_keys=True), flush=True)
    except KeyboardInterrupt:
        return 0 if args.follow else 130
    except (OSError, ValueError) as error:
        if args.follow:
            print(f'stream console: follow failed ({type(error).__name__})', file=sys.stderr)
        else:
            print('stream console: publication failed; delivery may be uncertain '
                  f'({type(error).__name__}); inspect inbox before retrying', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
