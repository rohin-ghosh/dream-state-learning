"""Chunked authenticated mirror transport; preserves original journal bytes."""

import argparse
import base64
import hashlib
import json
from pathlib import Path
import sys

from gpu import ny_caption_data as data
from gpu.ny_caption_life import child_act, latest_own_think
from research_loop.workers.rohin221_continuous_caption_20260918.journal_bundle import (
    MAX_BYTES, checked, import_records,
)


MAX_TOTAL_BYTES = 67108864
MAX_ENVELOPE_BYTES = 100663296
SCHEMA = 'R227_ORIGINAL_JOURNAL_CHUNKS_V1'


def export_chunks(root, origin, journal_id):
    root = Path(root).resolve(strict=True)
    child_act(root, origin)
    think = latest_own_think(root, origin)
    first = think['origin']['record_index'] if think else origin['record_index']
    final = None
    for index in range(origin['record_index'] + 1, origin['record_index'] + 33):
        path = root / 'stream/records' / f'{index:020d}.json'
        data.require(path.is_file() and not path.is_symlink() and path.stat().st_size <= MAX_BYTES,
                     'bounded_regular_stage_record')
        record = checked(path.read_bytes(), journal_id)
        if record['kind'] == 'R184_STAGE':
            final = index
            break
    data.require(final is not None and final - first <= 288, 'bounded_actual_stage_evidence')
    chunks, chunk, chunk_bytes, total, previous = [], [], 0, 0, None
    for index in range(first, final + 1):
        path = root / 'stream/records' / f'{index:020d}.json'
        data.require(path.is_file() and not path.is_symlink() and path.stat().st_size <= MAX_BYTES,
                     'bounded_regular_original_record')
        raw = path.read_bytes()
        total += len(raw)
        data.require(len(raw) <= MAX_BYTES and total <= MAX_TOTAL_BYTES, 'bounded_total_journal_mirror')
        record = checked(raw, journal_id)
        data.require(record['index'] == index, 'actual_record_index')
        if previous is not None:
            data.require(record['previous_sha256'] == previous['sha256'], 'contiguous_exported_ancestry')
        if chunk_bytes + len(raw) > MAX_BYTES:
            chunks.append(chunk)
            chunk, chunk_bytes = [], 0
        chunk.append(dict(index=index, file_sha256=hashlib.sha256(raw).hexdigest(),
                          raw=base64.b64encode(raw).decode('ascii')))
        chunk_bytes += len(raw)
        previous = record
    if chunk:
        chunks.append(chunk)
    return dict(schema=SCHEMA, origin=origin, journal_id=journal_id, chunks=chunks,
                original_bytes=total, complete_THINK_ancestry=think is not None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    parser.add_argument('--journal-id', required=True)
    parser.add_argument('--index', type=int)
    parser.add_argument('--sha256')
    parser.add_argument('--import-chunk', action='store_true')
    args = parser.parse_args()
    if args.import_chunk:
        raw = sys.stdin.buffer.read(MAX_BYTES * 2 + 1)
        data.require(len(raw) <= MAX_BYTES * 2, 'bounded_encoded_chunk')
        records = json.loads(raw)
        import_records(args.root, records, args.journal_id)
        print(json.dumps(dict(imported=len(records), first=records[0]['index'], last=records[-1]['index'])))
    else:
        data.require(args.index is not None and args.sha256 is not None, 'actual_origin_required')
        origin = dict(kind='TRAIN_CHILD_RESPONSE', record_index=args.index, record_sha256=args.sha256)
        print(json.dumps(export_chunks(args.root, origin, args.journal_id), separators=(',', ':')))


if __name__ == '__main__':
    main()
