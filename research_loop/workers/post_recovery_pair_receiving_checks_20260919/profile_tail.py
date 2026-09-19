"""Instrument an isolated read-only observer, never the native writer."""

import argparse
import faulthandler
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time


def profile(request_path, expected_sha256, helper_path, helper_sha256):
    request_bytes = Path(request_path).read_bytes()
    helper_bytes = Path(helper_path).read_bytes()
    if hashlib.sha256(request_bytes).hexdigest() != expected_sha256:
        raise ValueError('exact_probe_request_required')
    if hashlib.sha256(helper_bytes).hexdigest() != helper_sha256:
        raise ValueError('exact_read_only_observer_required')
    request = json.loads(request_bytes)
    sys.path.insert(0, request['source'])
    started = time.monotonic()
    faulthandler.dump_traceback_later(15, repeat=True, file=sys.stderr)
    from gpu import checkpoint_tail_runtime as reader
    totals = dict(records=0, raw_bytes=0, hash_seconds=0.0, decode_seconds=0.0,
                  decoded_records=0, last_index=None)
    last_report = started
    original_hash = reader.hash_record
    original_decode = reader._decoded_record

    def emit(stage, **extra):
        print(json.dumps(dict(stage=stage, elapsed_seconds=time.monotonic() - started,
                              totals=totals, **extra), sort_keys=True), file=sys.stderr, flush=True)

    def measured_hash(journal, index):
        nonlocal last_report
        entered = time.monotonic()
        result = original_hash(journal, index)
        totals['records'] += 1
        totals['raw_bytes'] += result[1]['bytes']
        totals['hash_seconds'] += time.monotonic() - entered
        totals['last_index'] = index
        if time.monotonic() - last_report >= 5:
            emit('HASH_PROGRESS')
            last_report = time.monotonic()
        return result

    def measured_decode(journal, header):
        entered = time.monotonic()
        emit('DECODE_BEGIN', index=header['index'], kind=header['kind'])
        result = original_decode(journal, header)
        totals['decode_seconds'] += time.monotonic() - entered
        totals['decoded_records'] += 1
        emit('DECODE_END', index=header['index'], kind=header['kind'])
        return result

    reader.hash_record = measured_hash
    reader._decoded_record = measured_decode
    specification = importlib.util.spec_from_file_location('read_only_tail_observer', helper_path)
    observer = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(observer)
    emit('OBSERVER_BEGIN')
    try:
        result = observer.observe(request_path, expected_sha256)
        emit('OBSERVER_END')
        return dict(result, profile=totals)
    finally:
        reader.hash_record = original_hash
        reader._decoded_record = original_decode
        faulthandler.cancel_dump_traceback_later()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', required=True)
    parser.add_argument('--request-sha256', required=True)
    parser.add_argument('--helper', required=True)
    parser.add_argument('--helper-sha256', required=True)
    options = parser.parse_args()
    print(json.dumps(profile(options.request, options.request_sha256,
                             options.helper, options.helper_sha256), sort_keys=True))
