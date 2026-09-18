"""Read-only, record-only transcript reduction for R125/R127/R129 local runs.

Read only numbered stream/records/*.json, never the inbox, manifest, readouts,
held data, checkpoints, or referenced receipts. Snapshot the published filenames;
ignore intents/staging and validate a contiguous checksum chain. This verifies
internal consistency, not external authentication or completeness of a live run.

Text is exported exactly, including legacy speaker prefixes and empty responses.
Startup means no parent yet observed in actual REQUEST user messages; a parented
response first observes new parent inbox text; autonomous_downstream has no new
parent. These are timing/presence labels, not evidence of causal influence.
after_sleep is an overlapping label for requests following SLEEP_COMPLETE.
Tool observations are tracked separately and never mislabelled as parent input.
Ambiguous identical plain inbox texts are flagged, not assigned invented IDs.

RESPONSE timestamps use finished_unix; INBOX and SLEEP_COMPLETE use record mtime
when no finished_unix exists, explicitly labelled as filesystem time, not event
time. No timestamp is inferred from adjacent events or the current clock.

CLI: --root RUN_ROOT [--output NEW_LOCAL_JSONL]. Without output, emit JSONL to
stdout. A named export is create-only with a retained immutable staging hardlink;
failure never deletes evidence and may leave staging or a published export.
"""

import argparse
from collections import Counter, defaultdict
from contextlib import ExitStack, contextmanager
import hashlib
import math
import os
from pathlib import Path
import re
import stat
import sys
import uuid

from gpu.orch_r125_stream_console import _open_stream_directory
from gpu.orch_r125_stream_journal import SCHEMA, _decode, _digest, _encoded, require

TRANSCRIPT_SCHEMA = 'R127_PILOT_TRANSCRIPT_V1'
MAX_RECORDS = 100000
MAX_RECORD_BYTES = 64 * 1024 * 1024
MAX_TOTAL_BYTES = 2 * 1024 * 1024 * 1024
HEX64 = re.compile(r'[0-9a-f]{64}')


def _hash(value):
    return type(value) is str and HEX64.fullmatch(value) is not None


def _unix(value):
    require(type(value) in (int, float) and math.isfinite(value) and value >= 0, 'unix_timestamp')
    return value


def _records(root, stats, max_records, max_record_bytes, max_total_bytes):
    for value in (max_records, max_record_bytes, max_total_bytes):
        require(type(value) is int and value > 0, 'positive_export_limits')
    with _open_stream_directory(root, 'records') as (directory, _):
        indices = []
        with os.scandir(directory) as entries:
            for scanned, entry in enumerate(entries, start=1):
                require(scanned <= max_records * 4 + 1024, 'directory_entry_limit')
                if re.fullmatch(r'[0-9]{20}\.json', entry.name):
                    indices.append(int(entry.name[:20]))
                    require(len(indices) <= max_records, 'record_count_limit')
        indices.sort()
        require(indices == list(range(len(indices))), 'noncontiguous_records')
        stats['snapshot_records'] = len(indices)
        previous = None
        for index in indices:
            name = f'{index:020d}.json'
            descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                                 dir_fd=directory)
            with os.fdopen(descriptor, 'rb') as stream:
                before = os.fstat(stream.fileno())
                require(stat.S_ISREG(before.st_mode), 'regular_record_required')
                require(before.st_size <= max_record_bytes, 'record_byte_limit')
                require(stats['source_bytes'] + before.st_size <= max_total_bytes, 'total_byte_limit')
                raw = stream.read(before.st_size + 1)
                after = os.fstat(stream.fileno())
                current = os.stat(name, dir_fd=directory, follow_symlinks=False)
            identities = {(entry.st_dev, entry.st_ino, entry.st_mode, entry.st_size, entry.st_mtime_ns)
                          for entry in (before, after, current)}
            require(len(identities) == 1 and len(raw) == before.st_size, 'record_changed_during_read')
            record = _decode(raw)
            require(type(record) is dict and set(record) == {
                'schema', 'journal_id', 'index', 'kind', 'previous_sha256', 'document', 'sha256'},
                'record_fields')
            require(record['schema'] == SCHEMA and type(record['index']) is int and record['index'] == index
                    and type(record['journal_id']) is str
                    and re.fullmatch(r'[0-9a-f]{32}', record['journal_id'])
                    and type(record['document']) is dict and type(record['kind']) is str
                    and re.fullmatch(r'[A-Z][A-Z0-9_]{0,63}', record['kind'])
                    and _hash(record['previous_sha256']) and _hash(record['sha256'])
                    and record['sha256'] == _digest({key: value for key, value in record.items() if key != 'sha256'}),
                    'record_integrity')
            if previous is None:
                stats['journal_id'] = record['journal_id']
                previous = _digest(dict(schema=SCHEMA, journal_id=record['journal_id']))
            require(record['journal_id'] == stats['journal_id'] and record['previous_sha256'] == previous,
                    'record_chain_integrity')
            previous = record['sha256']
            stats['head_sha256'] = previous
            stats['source_bytes'] += len(raw)
            yield record, before.st_mtime, hashlib.sha256(raw).hexdigest()


def _inbox(document):
    require(set(document) == {'message', 'source_id', 'source_sha256'}
            and type(document['source_id']) is str and _hash(document['source_sha256']), 'inbox_receipt')
    message = document['message']
    require(type(message) is dict, 'inbox_message')
    attributed = message.get('schema') == 'R127_ATTRIBUTED_INBOX_V1'
    expected = {'id', 'actor', 'split', 'text'}
    require(set(message) == (expected | {'schema', 'speaker', 'source_receipt'} if attributed else expected),
            'inbox_fields')
    require(type(message['id']) is str and message['id'].strip() and type(message['text']) is str
            and message['split'] == 'TRAIN', 'TRAIN_inbox_text')
    require(message['actor'] in (('parent', 'environment') if attributed else ('parent',)), 'inbox_actor')
    source = message.get('source_receipt')
    if attributed:
        if message['actor'] == 'parent':
            require(message['speaker'] in ('Astra', 'Fable', 'Rohin') and source is None, 'parent_attribution')
        else:
            require(message['speaker'] == 'Tool' and type(source) is dict and set(source) == {'path', 'sha256'}
                    and type(source['path']) is str and Path(source['path']).is_absolute()
                    and _hash(source['sha256']), 'tool_attribution')
        speaker, attribution = message['speaker'], 'attributed_inbox'
        visible_text = speaker + ': ' + message['text']
    else:
        explicit = re.match(r'^(Astra|Fable|Rohin)(?::|\r?\n)', message['text'])
        speaker = explicit[1] if explicit else 'legacy parent'
        attribution = 'legacy_explicit_prefix' if explicit else 'legacy_parent'
        visible_text = message['text']
    return dict(inbox_id=message['id'], actor=message['actor'], speaker=speaker, attribution=attribution,
                text=message['text'], source_receipt=source, inbox_source_id=document['source_id'],
                inbox_source_sha256=document['source_sha256'], visible_text=visible_text)


def _visible(messages, inbox):
    require(type(messages) is list and len(messages) >= 2, 'request_messages')
    plain = defaultdict(list)
    for identifier, entry in inbox.items():
        plain[entry['visible_text']].append(identifier)
    counts, visible = Counter(), set()
    for position, message in enumerate(messages):
        require(type(message) is dict and type(message.get('content')) is str
                and message.get('role') in ('system', 'user', 'assistant'), 'request_message')
        if position < 2 or message['role'] != 'user':
            continue
        content = message['content']
        if content in plain:
            counts[content] += 1
            continue
        pieces = content.split('\n', 2)
        if len(pieces) != 3 or pieces[0] not in (
                'Parent advice (not an observed fact)', 'Recorded environment observation'):
            continue
        try:
            metadata = _decode(pieces[1].encode('utf-8'))
        except ValueError:
            continue
        if type(metadata) is not dict:
            continue
        for identifier, entry in inbox.items():
            if (metadata.get('event_id') == entry['actor'] + ':inbox:' + identifier
                    and metadata.get('actor') == entry['actor'] and metadata.get('split') == 'TRAIN'
                    and metadata.get('source_id') == entry['inbox_source_id']
                    and metadata.get('source_sha256') == entry['inbox_source_sha256']
                    and pieces[2] == entry['visible_text']):
                visible.add(identifier)
    ambiguous = set()
    for content, count in counts.items():
        candidates = plain[content]
        if count >= len(candidates):
            visible.update(candidates)
        else:
            ambiguous.update(set(candidates) - visible)
    return visible, ambiguous


def _events(root, stats, **limits):
    inbox, seen = {}, set()
    pending, parent_seen, sleep_count = None, False, 0
    for record, mtime, file_sha in _records(root, stats, **limits):
        document, kind = record['document'], record['kind']
        if kind == 'REQUEST':
            require(pending is None and document.get('split') == 'TRAIN', 'unique_TRAIN_request')
            visible, ambiguous = _visible(document.get('messages'), inbox)
            new = visible - seen
            new_parents = {identifier for identifier in new if inbox[identifier]['actor'] == 'parent'}
            ambiguous_parents = {identifier for identifier in ambiguous if inbox[identifier]['actor'] == 'parent'}
            category = ('parented_response' if new_parents else
                        'autonomous_downstream' if parent_seen else 'startup')
            if ambiguous_parents:
                category = 'unresolved_parent_attribution'
            pending = dict(request_sha256=_digest({key: value for key, value in document.items() if key != 'resume_state'}),
                request_record_index=record['index'], request_record_sha256=record['sha256'],
                request_started_unix=_unix(document.get('started_unix')), category=category,
                categories=[category] + (['after_sleep'] if sleep_count else []),
                after_sleep=bool(sleep_count), sleep_count=sleep_count,
                visible_inbox_ids=sorted(visible), newly_visible_inbox_ids=sorted(new),
                newly_visible_parent_ids=sorted(new_parents), ambiguous_inbox_ids=sorted(ambiguous))
            parent_seen = parent_seen or bool(new_parents)
            seen.update(visible)
            continue
        if kind not in ('INBOX', 'RESPONSE', 'SLEEP_COMPLETE'):
            continue
        timestamp = _unix(document['finished_unix']) if 'finished_unix' in document else _unix(mtime)
        event = dict(schema=TRANSCRIPT_SCHEMA, journal_id=record['journal_id'], kind=kind,
            record_index=record['index'], record_sha256=record['sha256'], record_file_sha256=file_sha,
            unix_timestamp=timestamp,
            timestamp_source='document.finished_unix' if 'finished_unix' in document else 'record_mtime_not_event_time')
        if kind == 'INBOX':
            entry = _inbox(document)
            require(entry['inbox_id'] not in inbox, 'duplicate_inbox_registration')
            inbox[entry['inbox_id']] = entry
            event.update({key: value for key, value in entry.items() if key != 'visible_text'})
        elif kind == 'RESPONSE':
            require(pending is not None and document.get('request_sha256') == pending['request_sha256'],
                    'response_request_binding')
            response = document.get('response')
            require(type(response) is dict and type(response.get('raw')) is str, 'exact_response_text')
            event.update(pending, actor='child', speaker='child', text=response['raw'])
            pending = None
        else:
            require(pending is None and document.get('status') == 'COMPLETE', 'completed_sleep_boundary')
            sleep_count += 1
            event.update(sleep_count=sleep_count, cycle=document.get('cycle'), status='COMPLETE')
        stats['event_counts'][kind] += 1
        if kind == 'RESPONSE':
            stats['response_categories'].update(event['categories'])
        yield event
    stats['pending_request_record_index'] = pending['request_record_index'] if pending else None


def _stats():
    return dict(snapshot_records=0, source_bytes=0, journal_id=None, head_sha256=None,
                event_counts=Counter(), response_categories=Counter())


def iter_transcript(root, *, max_records=MAX_RECORDS, max_record_bytes=MAX_RECORD_BYTES,
                    max_total_bytes=MAX_TOTAL_BYTES):
    """Yield exact-text events from a bounded, validated published-record snapshot."""
    yield from _events(root, _stats(), max_records=max_records, max_record_bytes=max_record_bytes,
                       max_total_bytes=max_total_bytes)


@contextmanager
def _output_directory(path):
    require('..' not in path.parts, 'output_parent_component_forbidden')
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    with ExitStack() as stack:
        directory = os.open(path.anchor if path.is_absolute() else '.', flags)
        stack.callback(os.close, directory)
        for component in (path.parts[1:] if path.is_absolute() else path.parts):
            directory = os.open(component, flags, dir_fd=directory)
            stack.callback(os.close, directory)
        yield directory


def export_transcript(root, output, *, max_records=MAX_RECORDS, max_record_bytes=MAX_RECORD_BYTES,
                      max_total_bytes=MAX_TOTAL_BYTES):
    """Create a local immutable JSONL export; return a text-free compact manifest."""
    path = Path(output).absolute()
    require(not path.is_relative_to(Path(root).absolute() / 'stream'), 'output_outside_stream')
    stats = _stats()
    checksum, size = hashlib.sha256(), 0
    with _output_directory(path.parent) as directory:
        try:
            os.stat(path.name, dir_fd=directory, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise FileExistsError('export_already_exists')
        partial = uuid.uuid4().hex + '.transcript.partial'
        descriptor = os.open(partial, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                             0o600, dir_fd=directory)
        with os.fdopen(descriptor, 'wb') as stream:
            for event in _events(root, stats, max_records=max_records, max_record_bytes=max_record_bytes,
                                 max_total_bytes=max_total_bytes):
                raw = _encoded(event) + b'\n'
                stream.write(raw)
                checksum.update(raw)
                size += len(raw)
            stream.flush()
            os.fchmod(stream.fileno(), 0o400)
            os.fsync(stream.fileno())
        os.fsync(directory)
        os.link(partial, path.name, src_dir_fd=directory, dst_dir_fd=directory, follow_symlinks=False)
        os.fsync(directory)
    return dict(schema='R127_PILOT_TRANSCRIPT_MANIFEST_V1', path=str(path), sha256=checksum.hexdigest(),
                bytes=size, **stats)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    parser.add_argument('--output')
    parser.add_argument('--max-records', type=int, default=MAX_RECORDS)
    parser.add_argument('--max-record-bytes', type=int, default=MAX_RECORD_BYTES)
    parser.add_argument('--max-total-bytes', type=int, default=MAX_TOTAL_BYTES)
    args = parser.parse_args(argv)
    limits = dict(max_records=args.max_records, max_record_bytes=args.max_record_bytes,
                  max_total_bytes=args.max_total_bytes)
    try:
        if args.output:
            print(_encoded(export_transcript(args.root, args.output, **limits)).decode())
        else:
            for event in iter_transcript(args.root, **limits):
                print(_encoded(event).decode())
    except (OSError, ValueError, RecursionError) as error:
        print(f'transcript export failed ({type(error).__name__}); output may be partial', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
