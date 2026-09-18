"""Publish immutable raw child-call batches without admitting training targets."""

import argparse
from collections import Counter
import fcntl
import hashlib
import json
import os
from pathlib import Path
import time
import uuid


SCHEMA = 'ORCH_RICH_HOT_NODE2_RAW_BATCH_V1'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def wire(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def read(path):
    return json.loads(Path(path).read_bytes())


def durable(path, raw):
    path = Path(path)
    with path.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def sync_directory(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def replace_json(path, value):
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    durable(temporary, wire(value))
    os.replace(temporary, path)
    sync_directory(path.parent)


def provenance(source):
    names = ('PREPARE.json', 'TASKS.json', 'INITIAL.json', 'DATA_PROVENANCE.json',
             'PROTOCOL.md', 'LIFETIME.json', 'READY.json')
    return {name: digest((source / name).read_bytes()) for name in names if (source / name).is_file()}


def descriptor(source, path, raw):
    row = json.loads(raw)
    for field in ('index', 'shard', 'task_id', 'stage', 'messages', 'finished_unix'):
        if field not in row:
            raise ValueError('incomplete_capture:' + str(path))
    if 'response' not in row and 'error' not in row:
        raise ValueError('capture_has_no_result')
    outcome = row.get('outcome', {})
    if row.get('trainingAllowed', False) or outcome.get('admitted', False) or outcome.get('trainingAllowed', False):
        raise ValueError('raw_export_must_not_include_admitted_rows')
    response = row.get('response', {})
    if response and response.get('messages') != row['messages']:
        raise ValueError('generation_message_mismatch')
    key = f"{source.name}:{row['shard']}:{row['task_id']}:{row['stage']}"
    return dict(key=key, source_root=str(source), source_relative_path=str(path.relative_to(source)),
                call_index=row['index'], shard=row['shard'], task_id=row['task_id'], stage=row['stage'],
                family=row.get('family', 'math'), condition=row['condition'], sha256=digest(raw),
                bytes=len(raw), category=outcome.get('category', 'execution_error'),
                content_tokens=outcome.get('content_tokens'),
                target_sha256=digest(response['raw'].encode()) if 'raw' in response else None,
                exact_messages_sha256=digest(wire(row['messages'])),
                semantic_status='UNREVIEWED', admitted=False, trainingAllowed=False)


def published(destination):
    seen = {}
    for path in sorted((destination / 'batches').glob('*/MANIFEST.json')):
        manifest = read(path)
        if path.parent.name != digest(path.read_bytes()):
            raise ValueError('manifest_identity_changed')
        if manifest['schema'] != SCHEMA or manifest['trainingAllowed'] is not False:
            raise ValueError('invalid_manifest_contract')
        for entry in manifest['rows']:
            raw = (path.parent / entry['file']).read_bytes()
            if digest(raw) != entry['sha256'] or len(raw) != entry['bytes']:
                raise ValueError('published_raw_changed')
            if entry['key'] in seen:
                raise ValueError('duplicate_published_capture')
            seen[entry['key']] = entry['sha256']
    return seen


def export(source, destination, batch_size=128):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if source == destination or source in destination.parents or destination in source.parents:
        raise ValueError('sidecar_root_must_be_separate')
    if not 1 <= batch_size <= 1024:
        raise ValueError('bounded_batch_size')
    destination.mkdir(parents=True, exist_ok=True)
    (destination / 'batches').mkdir(exist_ok=True)
    with (destination / 'EXPORT.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        seen = published(destination)
        pending, counts, captured_keys = [], Counter(), set()
        tokens, bound = [], provenance(source)
        for manifest_path in (destination / 'batches').glob('*/MANIFEST.json'):
            manifest = read(manifest_path)
            if manifest['source_root'] == str(source) and manifest['provenance'] != bound:
                raise ValueError('frozen_provenance_changed')
        for path in source.glob('shard*/*.json'):
            if path.name in ('LOADED.json', 'AFTER.json', 'AFTER_FAILED.json', 'TERMINAL.json', 'FAILED.json', 'BOUND.json'):
                continue
            raw = path.read_bytes()
            entry = descriptor(source, path, raw)
            if entry['key'] in captured_keys:
                raise ValueError('duplicate_source_capture')
            captured_keys.add(entry['key'])
            counts[entry['category']] += 1
            if entry['content_tokens'] is not None:
                tokens.append(entry['content_tokens'])
            if entry['key'] in seen:
                if seen[entry['key']] != entry['sha256']:
                    raise ValueError('previous_capture_changed')
            else:
                pending.append((entry, raw))
        if any(key.startswith(source.name + ':') and key not in captured_keys for key in seen):
            raise ValueError('previous_capture_missing')
        pending.sort(key=lambda pair: pair[0]['call_index'])
        created = []
        prepared = read(source / 'PREPARE.json')
        for offset in range(0, len(pending), batch_size):
            batch = pending[offset:offset + batch_size]
            temporary = destination / ('pending-' + uuid.uuid4().hex)
            temporary.mkdir()
            entries = []
            for entry, raw in batch:
                entry = dict(entry, file=entry['sha256'] + '.json')
                durable(temporary / entry['file'], raw)
                entries.append(entry)
            manifest = dict(schema=SCHEMA, source_root=str(source), provenance=bound,
                            identity=prepared.get('identity'), raw_count=len(entries), rows=entries,
                            state_after_status='SEE_NATIVE_AFTER_RECEIPT_NOT_ASSUMED',
                            semantic_status='UNREVIEWED', trainingAllowed=False, admitted=False,
                            review_contract='Sampled checks certify only explicitly reviewed rows; no batch-wide PASS.',
                            trajectory_contract='Exact messages, response and outcome in each raw JSON; no neutral-prefix rewrite.')
            manifest_bytes = wire(manifest)
            durable(temporary / 'MANIFEST.json', manifest_bytes)
            sync_directory(temporary)
            target = destination / 'batches' / digest(manifest_bytes)
            os.rename(temporary, target)
            sync_directory(destination / 'batches')
            created.append(str(target / 'MANIFEST.json'))
        status = dict(schema=SCHEMA, observed_unix=time.time(), source_root=str(source),
                      completed_captures=sum(counts.values()), categories=dict(counts),
                      raw_above_400=sum(value > 400 for value in tokens),
                      token_range=[min(tokens), max(tokens)] if tokens else None,
                      newly_published=len(pending), created_manifests=created,
                      reservation_count=len(list((source / 'reservations').glob('*.json'))),
                      provenance=bound, admitted_rows=0, semantic_status='UNREVIEWED')
        snapshot = destination / ('OBSERVATION_' + str(time.time_ns()) + '.json')
        durable(snapshot, wire(status))
        replace_json(destination / 'LATEST.json', status)
        return status


def export_evidence(source, destination):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    directory = destination / 'evidence'
    directory.mkdir(parents=True, exist_ok=True)
    with (destination / 'EVIDENCE.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        seen = {}
        for path in directory.glob('*/EVIDENCE_MANIFEST.json'):
            entry = read(path)
            if path.parent.name != digest(path.read_bytes()) or digest((path.parent / 'raw.json').read_bytes()) != entry['sha256']:
                raise ValueError('published_evidence_changed')
            seen[entry['key']] = entry['sha256']
        paths = list(source.glob('shard*/evidence/*.json')) + list(source.glob('shard*/AFTER.json'))
        created = []
        for path in sorted(paths):
            raw = path.read_bytes()
            key = source.name + ':' + str(path.relative_to(source))
            if key in seen:
                if seen[key] != digest(raw):
                    raise ValueError('native_evidence_changed')
                continue
            entry = dict(schema='ORCH_RICH_HOT_NODE2_ENVIRONMENT_EVIDENCE_V1', key=key,
                         source_root=str(source), source_relative_path=str(path.relative_to(source)),
                         sha256=digest(raw), file='raw.json', semantic_status='UNREVIEWED', trainingAllowed=False)
            temporary = destination / ('pending-evidence-' + uuid.uuid4().hex)
            temporary.mkdir()
            durable(temporary / 'raw.json', raw)
            durable(temporary / 'EVIDENCE_MANIFEST.json', wire(entry))
            sync_directory(temporary)
            target = directory / digest(wire(entry))
            os.rename(temporary, target)
            sync_directory(directory)
            created.append(str(target / 'EVIDENCE_MANIFEST.json'))
        return created


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--watch-until', type=float)
    parser.add_argument('--batch-size', type=int, default=128)
    options = parser.parse_args()
    while True:
        print(json.dumps(export(options.source, options.destination, options.batch_size)), flush=True)
        print(json.dumps(dict(environment_evidence=export_evidence(options.source, options.destination))), flush=True)
        if options.watch_until is None or time.time() >= options.watch_until:
            break
        time.sleep(min(60, max(0, options.watch_until - time.time())))
