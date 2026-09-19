"""Private, append-only exploration rows; no evaluation or instruction execution.

ExplorationDataset(root, life_id).append(row) returns True for a new row and
False for an identical retry. Required caller fields are row_id, cycle, stage,
state_before, state_after, source. schema/life_id default to this dataset;
action/outcome/parent_turns/transition default to None (unrecorded, not success
or confirmed absence). An explicit [] means no parent turns. Supplied JSON
values and extra fields are preserved without summaries or normalization.

Parent turns are attributed input, never targets. A later reinterpretation is
a new row with record_kind='reinterpretation' and reinterpretation_of pointing
to an existing row_id. New factual observations likewise need new row IDs.
Each life uses root/<life_id>.jsonl. Writers use flock, not a custody protocol.
Exports are new local mode0600 files; nothing is published or overwritten.
CSV cells contain JSON, with additional caller fields in extra_fields.
"""

import argparse
from contextlib import contextmanager
import csv
import fcntl
import json
import math
import os
from pathlib import Path
import re
import stat
import tempfile


SCHEMA = 'R191_EXPLORATION_DATASET_V1'
MAX_ROW_BYTES = 8 * 1024 * 1024
FIELDS = ('schema', 'row_id', 'life_id', 'cycle', 'stage', 'action', 'outcome',
          'state_before', 'state_after', 'parent_turns', 'source', 'transition')


def _require(condition, reason):
    if not condition:
        raise ValueError(reason)


def _plain_json(value, depth=0):
    _require(depth <= 64, 'JSON nesting exceeds 64')
    if type(value) is dict:
        _require(all(type(key) is str for key in value), 'JSON object keys must be strings')
        for item in value.values():
            _plain_json(item, depth + 1)
    elif type(value) is list:
        for item in value:
            _plain_json(item, depth + 1)
    elif type(value) is float:
        _require(math.isfinite(value), 'JSON numbers must be finite')
    else:
        _require(type(value) in (str, int, bool, type(None)), 'plain JSON values required')


def _json(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False,
                      sort_keys=True, separators=(',', ':'))


def _object(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, 'duplicate JSON object key')
        result[key] = value
    return result


def _line(stream, end):
    raw = stream.readline(min(MAX_ROW_BYTES + 1, end - stream.tell()))
    _require(raw.endswith(b'\n') and len(raw) <= MAX_ROW_BYTES,
             'incomplete or oversized dataset row; original bytes retained')
    return raw


def _decode(raw):
    return json.loads(raw, object_pairs_hook=_object)


class ExplorationDataset:
    def __init__(self, root, life_id):
        _require(type(life_id) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}', life_id),
                 'life_id must be a bounded filename-safe identifier')
        self.root = Path(root)
        self.life_id = life_id
        self.path = self.root / (life_id + '.jsonl')
        self._identity = None
        self._offset = 0
        self._index = {}

    def _validate(self, row):
        _require(type(row) is dict and set(FIELDS) <= set(row), 'exploration row fields required')
        _plain_json(row)
        _require(row['schema'] == SCHEMA and row['life_id'] == self.life_id, 'schema or life_id mismatch')
        _require(type(row['row_id']) is str and 0 < len(row['row_id'].encode()) <= 1024, 'bounded row_id required')
        _require(type(row['cycle']) is int and row['cycle'] >= 0, 'nonnegative integer cycle required')
        _require(type(row['stage']) is str and 0 < len(row['stage'].encode()) <= 128, 'bounded stage required')
        _require(all(row[key] is None or type(row[key]) is dict for key in ('state_before', 'state_after')),
                 'state snapshots must be exact JSON objects or explicit None')
        _require(type(row['source']) is dict and row['source'], 'source provenance object required')
        parents = row['parent_turns']
        _require(parents is None or type(parents) is list, 'parent_turns must be a list or unrecorded None')
        for turn in parents or []:
            _require(type(turn) is dict and type(turn.get('text')) is str,
                     'parent turns must preserve attributed text objects')
            _require(any(type(turn.get(key)) is str and turn[key] for key in ('speaker', 'source_id')),
                     'parent speaker or source attribution required')
            _require(all(key not in turn or turn[key] is False for key in ('target_loss', 'is_target')),
                     'parent turns are input, never targets')
        kind = row.get('record_kind', 'observation')
        _require(kind in ('observation', 'reinterpretation'), 'unknown record_kind')
        reference = row.get('reinterpretation_of')
        _require((kind == 'observation' and reference is None) or
                 (kind == 'reinterpretation' and type(reference) is str and reference
                  and reference != row['row_id']), 'reinterpretations need a separate original row_id')

    @contextmanager
    def _open(self, write=False):
        flags = os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK
        if write:
            self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
            flags |= os.O_RDWR | os.O_CREAT | os.O_APPEND
        else:
            flags |= os.O_RDONLY
        descriptor = os.open(self.path, flags, 0o600)
        try:
            _require(stat.S_ISREG(os.fstat(descriptor).st_mode), 'regular dataset file required')
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, 'r+b' if write else 'rb', buffering=0, closefd=False) as stream:
                yield stream
        finally:
            os.close(descriptor)

    def _refresh(self, stream):
        metadata = os.fstat(stream.fileno())
        identity = metadata.st_dev, metadata.st_ino
        if self._identity != identity:
            self._identity, self._offset, self._index = identity, 0, {}
        _require(metadata.st_size >= self._offset, 'dataset was truncated; no automatic repair')
        stream.seek(self._offset)
        while stream.tell() < metadata.st_size:
            offset = stream.tell()
            raw = _line(stream, metadata.st_size)
            row = _decode(raw)
            self._validate(row)
            _require(row['row_id'] not in self._index, 'duplicate stored row_id')
            if row.get('record_kind') == 'reinterpretation':
                _require(row['reinterpretation_of'] in self._index, 'original observation not present')
            self._index[row['row_id']] = offset, len(raw)
            self._offset = stream.tell()

    def append(self, row):
        _require(type(row) is dict, 'plain row dictionary required')
        document = dict(schema=SCHEMA, life_id=self.life_id, action=None, outcome=None,
                        parent_turns=None, transition=None)
        document.update(row)
        self._validate(document)
        raw = (_json(document) + '\n').encode('utf-8')
        _require(len(raw) <= MAX_ROW_BYTES, 'dataset row exceeds byte limit')
        with self._open(write=True) as stream:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
            self._refresh(stream)
            prior = self._index.get(document['row_id'])
            if prior is not None:
                stream.seek(prior[0])
                _require(_json(_decode(stream.read(prior[1]))) == _json(document), 'row_id content conflict')
                return False
            if document.get('record_kind') == 'reinterpretation':
                _require(document['reinterpretation_of'] in self._index, 'original observation not present')
            stream.seek(0, os.SEEK_END)
            offset = stream.tell()
            remaining = memoryview(raw)
            while remaining:
                written = stream.write(remaining)
                if not written:
                    raise OSError('incomplete dataset append')
                remaining = remaining[written:]
            os.fsync(stream.fileno())
            self._index[document['row_id']] = offset, len(raw)
            self._offset = offset + len(raw)
        return True

    def iter_rows(self):
        """Yield detached dictionaries from a complete-prefix snapshot, without a long writer lock."""
        try:
            with self._open() as stream:
                fcntl.flock(stream.fileno(), fcntl.LOCK_SH)
                end = os.fstat(stream.fileno()).st_size
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
                while stream.tell() < end:
                    row = _decode(_line(stream, end))
                    self._validate(row)
                    yield row
        except FileNotFoundError:
            return

    def _export(self, destination, format):
        destination = Path(destination)
        temporary = None
        count = 0
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='',
                    dir=destination.parent, prefix='.' + destination.name + '.', delete=False) as output:
                temporary = Path(output.name)
                os.fchmod(output.fileno(), 0o600)
                writer = csv.writer(output) if format == 'csv' else None
                if writer:
                    writer.writerow(FIELDS + ('extra_fields',))
                for row in self.iter_rows():
                    if writer:
                        extras = {key: value for key, value in row.items() if key not in FIELDS}
                        writer.writerow([_json(row[key]) for key in FIELDS] + [_json(extras)])
                    else:
                        output.write(_json(row) + '\n')
                    count += 1
                output.flush()
                os.fsync(output.fileno())
            os.link(temporary, destination)
            return count
        finally:
            if temporary is not None:
                temporary.unlink()

    def export_jsonl(self, destination):
        return self._export(destination, 'jsonl')

    def export_csv(self, destination):
        return self._export(destination, 'csv')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--life-id', required=True)
    parser.add_argument('--format', choices=('jsonl', 'csv'), default='jsonl')
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args(argv)
    dataset = ExplorationDataset(arguments.root, arguments.life_id)
    count = dataset._export(arguments.output, arguments.format)
    print(json.dumps(dict(rows=count, format=arguments.format, output=str(arguments.output), private=True)))


if __name__ == '__main__':
    main()
