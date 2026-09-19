"""Stage an isolated CPU reader; neither a receiving guard nor a GPU entrypoint."""

import base64
import hashlib
import json
import os
from pathlib import Path
import re
import time


PREFIX = Path('/localhome/local-rohing/orch_retention_20260919/C2')
REPLACEMENTS = {'gpu/checkpoint_tail_runtime.py', 'gpu/immutable_prefix_proof.py'}
BOOTSTRAP = {'prefix_cli.py', 'immutable_prefix_proof.py', 'native_view_probe.py'}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def validated_payloads(entries, names):
    require(set(entries) == names, 'exact_CPU_observer_file_set')
    result = {}
    for name, entry in entries.items():
        raw = base64.b64decode(entry['base64'], validate=True)
        require(len(raw) < 1024 * 1024 and sha(raw) == entry['sha256'], 'bound_CPU_source_bytes')
        compile(raw, name, 'exec')
        result[name] = raw
    return result


def write_once(path, raw):
    with path.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode() + b'\n'


def stage(request):
    replacements = validated_payloads(request['replacements'], REPLACEMENTS)
    bootstrap = validated_payloads(request['bootstrap'], BOOTSTRAP)
    original = Path(request['original_source'])
    require(original == PREFIX / 'epoch3/source' and original.resolve() == original, 'exact_prior_C2_source')
    pins = request['original_pins']
    require({str(path.relative_to(original)): sha(path.read_bytes())
        for path in original.rglob('*.py')} == pins, 'complete_prior_source_closure')
    native = Path('/proc') / str(request['native_pid'])
    original_process = (native / 'stat').read_text().rsplit(') ', 1)[1].split()
    require(original_process[19] == str(request['native_start_ticks'])
        and original_process[0] not in ('Z', 'X', 'T', 't'), 'same_running_native')
    historical_raw = Path(request['historical_request']).read_bytes()
    require(sha(historical_raw) == request['historical_request_sha256'], 'pinned_historical_request')
    historical = json.loads(historical_raw)
    selection = dict(historical['plan']['checkpoint_tail_recovery'])
    records = Path(selection['root']) / 'records'
    pattern = re.compile(rb',"index":([0-9]+),"journal_id":"([0-9a-f]{32})","kind":"SLEEP_COMPLETE",'
        rb'"previous_sha256":"[0-9a-f]{64}","schema":"R125_STREAM_JOURNAL_V1","sha256":"([0-9a-f]{64})"}\n\Z')
    candidates = sorted(records.glob('[0-9]' * 20 + '.json'))[-512:]
    for path in reversed(candidates):
        metadata = path.stat()
        if max(metadata.st_ctime_ns, metadata.st_mtime_ns) > time.time_ns() - 10_000_000_000:
            continue
        with path.open('rb') as stream:
            stream.seek(max(0, metadata.st_size - 2048))
            match = pattern.search(stream.read())
        if match:
            require(match.group(2).decode() == selection['journal_id'], 'same_original_journal')
            selection.update(complete_index=int(match.group(1)), complete_sha256=match.group(3).decode())
            break
    else:
        raise ValueError('no_aged_COMPLETE_in_bounded_headers')
    root = PREFIX / ('prefix_observer_' + str(time.time_ns()))
    root.mkdir(mode=0o700)
    source = root / 'source'
    source.mkdir()
    new_pins = {}
    for relative in sorted(set(pins) | REPLACEMENTS):
        require(not Path(relative).is_absolute() and '..' not in Path(relative).parts, 'literal_source_relative_path')
        raw = replacements[relative] if relative in replacements else (original / relative).read_bytes()
        if relative not in replacements:
            require(sha(raw) == pins[relative], 'prior_source_unchanged_during_copy')
        target = source / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        write_once(target, raw)
        target.chmod(0o444)
        new_pins[relative] = sha(raw)
    for directory in sorted((path for path in source.rglob('*') if path.is_dir()),
            key=lambda path: len(path.parts), reverse=True):
        directory.chmod(0o555)
    source.chmod(0o555)
    epoch = encoded(dict(schema='CPU_PREFIX_OBSERVER_SOURCE_EPOCH_V1', source=str(source),
        source_pins=new_pins, native_adoption_authorized=False, GPU_calls=0))
    write_once(root / 'EPOCH.json', epoch)
    for name, raw in bootstrap.items():
        write_once(root / name, raw)
    producer = dict(schema='R233_PREFIX_PRODUCER_REQUEST_V1', selection=selection,
        source=dict(root=str(source), pins=new_pins,
            epoch=dict(path=str(root / 'EPOCH.json'), sha256=sha(epoch))),
        journal_type='gpu.orch_r125_stream_journal:StreamJournal')
    raw = encoded(producer)
    write_once(root / 'PRODUCER.json', raw)
    require((native / 'stat').read_text().rsplit(') ', 1)[1].split()[19] == original_process[19],
        'same_native_after_staging')
    return dict(status='CPU_ONLY_PREFIX_OBSERVER_STAGED_NOT_DISPATCHABLE', root=str(root),
        producer_sha256=sha(raw), source_pins_sha256=sha(encoded(new_pins)),
        complete_index=selection['complete_index'], complete_sha256=selection['complete_sha256'],
        no_native_signals=True, GPU_calls=0, journal_writes=0, live_adoption=False)
