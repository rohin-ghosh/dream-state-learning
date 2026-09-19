"""Bounded unchanged native evidence transport, outside all child tool sandboxes."""

import argparse
import base64
import hashlib
import json
from pathlib import Path

from gpu import ny_caption_data as data
from gpu.ny_caption_life import child_act, latest_own_think
from gpu.orch_r125_stream_journal import _decode, _digest


MAX_BYTES = 8388608


def checked(raw, expected_journal):
    row = _decode(raw)
    data.require(row['journal_id'] == expected_journal and row['sha256'] ==
        _digest({key:value for key,value in row.items() if key != 'sha256'}), 'same_bound_journal_and_record_hash')
    return row


def export_records(root, origin, expected_journal):
    root = Path(root).resolve(strict=True)
    child_act(root, origin)
    think = latest_own_think(root, origin)
    first = think['origin']['record_index'] if think else origin['record_index']
    final = None
    for index in range(origin['record_index'] + 1, origin['record_index'] + 33):
        row = _decode((root / 'stream/records' / f'{index:020d}.json').read_bytes())
        if row['kind'] == 'R184_STAGE':
            final = index
            break
    data.require(final is not None and final - first <= 288, 'bounded_actual_stage_evidence')
    result, total = [], 0
    for index in range(first, final + 1):
        path = root / 'stream/records' / f'{index:020d}.json'
        data.require(path.is_file() and not path.is_symlink(), 'regular_actual_journal_file')
        raw = path.read_bytes()
        total += len(raw)
        data.require(total <= MAX_BYTES, 'bounded_journal_transfer')
        row = checked(raw, expected_journal)
        data.require(row['index'] == index, 'actual_record_index')
        result.append(dict(index=index, file_sha256=hashlib.sha256(raw).hexdigest(),
                           raw=base64.b64encode(raw).decode('ascii')))
    return result


def import_records(root, records, expected_journal):
    data.require(type(records) is list and 1 <= len(records) <= 289, 'bounded_record_count')
    validated, previous, total = [], None, 0
    for item in records:
        data.require(set(item) == {'index', 'file_sha256', 'raw'} and type(item['index']) is int
            and item['index'] >= 0, 'exact_record_envelope')
        raw = base64.b64decode(item['raw'], validate=True)
        total += len(raw)
        data.require(total <= MAX_BYTES and hashlib.sha256(raw).hexdigest() == item['file_sha256'],
                     'exact_transferred_record_bytes')
        row = checked(raw, expected_journal)
        data.require(row['index'] == item['index'], 'same_index')
        if previous is not None:
            data.require(row['index'] == previous['index'] + 1 and row['previous_sha256'] == previous['sha256'],
                         'contiguous_actual_records')
        previous = row
        validated.append((row['index'], raw))
    directory = Path(root) / 'stream/records'
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    for index, raw in validated:
        path = directory / f'{index:020d}.json'
        if path.exists():
            data.require(not path.is_symlink() and path.read_bytes() == raw, 'no_mirror_rewrite')
        else:
            with path.open('xb') as stream:
                stream.write(raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    parser.add_argument('--journal-id', required=True)
    parser.add_argument('--index', required=True, type=int)
    parser.add_argument('--sha256', required=True)
    args = parser.parse_args()
    origin = dict(kind='TRAIN_CHILD_RESPONSE', record_index=args.index, record_sha256=args.sha256)
    print(json.dumps(export_records(args.root, origin, args.journal_id), separators=(',', ':')))


if __name__ == '__main__':
    main()
