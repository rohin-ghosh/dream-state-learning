"""Nonblocking every-completed-sleep custody; never opens a live writer lock."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import time


BASE_SHA = 'a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992'


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def file_hash(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def put(path, value):
    path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    temporary = path.with_name(path.name + f'.{os.getpid()}.tmp')
    with temporary.open('xb') as stream:
        stream.write(canonical(value) + b'\n')
        stream.flush()
        os.fsync(stream.fileno())
    try:
        os.link(temporary, path)
    finally:
        temporary.unlink()


def record_at(life, index, journal_id, expected_sha=None):
    path = life/'stream/records'/f'{index:020d}.json'
    value = json.loads(path.read_bytes())
    if value['index'] != index or value['journal_id'] != journal_id or value['sha256'] != digest(
            {key: item for key, item in value.items() if key != 'sha256'}):
        raise ValueError('canonical_source_record_binding')
    if expected_sha is not None and value['sha256'] != expected_sha:
        raise ValueError('registered_source_record_changed')
    return value, path


def validate_registration(registration):
    life = Path(registration['life_root'])
    if not life.is_absolute() or life.resolve() != life:
        raise ValueError('physical_canonical_life_root')
    anchor = registration['initial_loaded']
    record, _ = record_at(life, anchor['index'], registration['journal_id'], anchor['sha256'])
    if record['kind'] != 'LOADED' or record['document']['base_sha256'] != BASE_SHA:
        raise ValueError('actual_initial_frozen_base_binding')
    for epoch in registration['runtime_epochs']:
        if epoch.get('record_index') is not None:
            record_at(life, epoch['record_index'], registration['journal_id'], epoch['record_sha256'])
    for anchor in registration.get('additional_record_anchors', []):
        record_at(life, anchor['index'], registration['journal_id'], anchor['sha256'])
    for reference in registration.get('owner_metadata_files', []):
        if file_hash(Path(reference['path'])) != reference['sha256']:
            raise ValueError('owner_runtime_metadata_changed')
    return life


def completed_records(life, journal_id, maximum_index=None):
    paths = sorted(path for path in (life/'stream/records').iterdir()
        if re.fullmatch(r'\d{20}\.json', path.name))
    if not paths:
        raise ValueError('empty_journal')
    cut = int(paths[-1].stem) if maximum_index is None else maximum_index
    records = []
    for path in paths:
        index = int(path.stem)
        if index > cut:
            break
        value = json.loads(path.read_bytes())
        if value['kind'] == 'SLEEP_COMPLETE' and value['document'].get('status') == 'COMPLETE':
            verified=record_at(life,index,journal_id)[0]
            records.append(dict(index=verified['index'],sha256=verified['sha256'],journal_id=verified['journal_id'],
                kind=verified['kind'],document={key:verified['document'][key] for key in
                    ('status','cycle','total_optimizer_steps','after_adapter_sha256')}))
    return cut, records


def capture(registration, output, record, head_index):
    life = validate_registration(registration)
    record, record_path = record_at(life, record['index'], registration['journal_id'], record['sha256'])
    document = record['document']
    if record['kind'] != 'SLEEP_COMPLETE' or document['status'] != 'COMPLETE':
        raise ValueError('completed_sleep_only')
    cycle = document['cycle']
    checkpoint = life/'checkpoints'/f'sleep_{cycle:06d}'
    if checkpoint.resolve() != checkpoint:
        raise ValueError('physical_checkpoint_not_symlink')
    key = f"sleep_{cycle:06d}_{record['sha256'][:16]}"
    destination = output/'sources'/key
    if destination.exists():
        existing = json.loads((destination/'SOURCE.json').read_bytes())
        if existing['sleep_complete_sha256'] != record['sha256'] or existing['journal_id'] != registration['journal_id']:
            raise ValueError('immutable_queue_entry_changed')
        for relative, expected in existing['copy_files'].items():
            status = (destination/relative).stat()
            if status.st_size != expected['bytes']:
                raise ValueError('retained_queue_file_size_changed')
        return existing
    commit_path = checkpoint/'COMMIT.json'
    commit = json.loads(commit_path.read_bytes())
    if commit['base_sha256'] != BASE_SHA or commit['adapter_state_sha256'] != document['after_adapter_sha256'] or commit['optimizer_steps'] != document['total_optimizer_steps']:
        raise ValueError('completed_adapter_commit_join')
    if set(commit['adapter_files']) != {'README.md', 'adapter_config.json', 'adapter_model.safetensors'}:
        raise ValueError('explicit_native_adapter_files')
    names = ['COMMIT.json'] + ['adapter/'+name for name in commit['adapter_files']]
    before = {name:dict(sha256=file_hash(checkpoint/name), bytes=(checkpoint/name).stat().st_size,
        mtime_ns=(checkpoint/name).stat().st_mtime_ns) for name in names}
    if any(before['adapter/'+name]['sha256'] != checksum for name, checksum in commit['adapter_files'].items()):
        raise ValueError('adapter_bytes_not_committed')
    optimizer = checkpoint/'optimizer_rng.pt'
    optimizer_before = dict(sha256=file_hash(optimizer), bytes=optimizer.stat().st_size,
        mtime_ns=optimizer.stat().st_mtime_ns) if optimizer.exists() else None
    epochs = [epoch for epoch in registration['runtime_epochs'] if epoch['after_record_index'] < record['index']]
    if not epochs:
        raise ValueError('no_bound_runtime_epoch_for_source')
    epoch = max(epochs, key=lambda row: row['after_record_index'])
    staging = output/'staging'/key
    (staging/'adapter').mkdir(parents=True, mode=0o700, exist_ok=False)
    for name in names:
        shutil.copyfile(checkpoint/name, staging/name)
        os.chmod(staging/name, 0o600)
        if file_hash(staging/name) != before[name]['sha256']:
            raise ValueError('captured_byte_mismatch')
    after = {name:dict(sha256=file_hash(checkpoint/name),bytes=(checkpoint/name).stat().st_size,
        mtime_ns=(checkpoint/name).stat().st_mtime_ns) for name in names}
    optimizer_after = dict(sha256=file_hash(optimizer),bytes=optimizer.stat().st_size,
        mtime_ns=optimizer.stat().st_mtime_ns) if optimizer.exists() else None
    if before != after or optimizer_before != optimizer_after:
        raise ValueError('source_changed_during_read_only_capture')
    source = dict(schema='R232_EVERY_SLEEP_IMMUTABLE_SOURCE_V1', captured_unix=time.time(),
        source_name=registration['source_name'], journal_id=registration['journal_id'],
        absolute_sleep=cycle, relative_sleep=cycle-registration['baseline_cycle'],
        optimizer_steps=commit['optimizer_steps'], relative_optimizer_steps=commit['optimizer_steps']-registration['baseline_optimizer_steps'],
        adapter_state_sha256=commit['adapter_state_sha256'], base_sha256=BASE_SHA,
        checkpoint_created_unix=commit['created_unix'], sleep_complete_index=record['index'],
        sleep_complete_sha256=record['sha256'], sleep_complete_file_sha256=file_hash(record_path),
        source_cut_index=head_index, copy_files=before, optimizer_rng_provenance=optimizer_before,
        optimizer_rng_copied_or_loaded=False, resume_state_sha256=digest(document.get('resume_state')),
        before_after_equal=True, runtime_epoch=epoch, source_relative=key,
        cumulative_training_tokens=None, cumulative_training_seconds=None,
        queue_status='PENDING_VALIDATION', learner_signals=[], source_writer_lock_opened=False)
    put(staging/'SOURCE.json', source)
    destination.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    staging.rename(destination)
    put(output/'entries'/f'{key}.json', source)
    return source


def scan(registration, output, *, latest=False):
    life = validate_registration(registration)
    cut, records = completed_records(life, registration['journal_id'])
    if latest:
        if not records:
            raise ValueError('no_completed_sleep_available')
        records = records[-1:]
    bound_markers = {registration['initial_loaded']['index']}
    bound_markers.update(epoch['record_index'] for epoch in registration['runtime_epochs'] if epoch.get('record_index') is not None)
    bound_markers.update(anchor['index'] for anchor in registration.get('additional_record_anchors', []))
    unknown_markers=[]
    for path in sorted((life/'stream/records').iterdir()):
        if not re.fullmatch(r'\d{20}\.json',path.name) or int(path.stem)>cut:
            continue
        record=json.loads(path.read_bytes())
        if record['kind'] in ('LOADED','R232_RECOVERY_CONTEXT') and record['index'] not in bound_markers:
            unknown_markers.append(record['index'])
    allowed = [record for record in records if not unknown_markers or record['index']<min(unknown_markers)]
    blocked = [record for record in records if record not in allowed]
    entries = [capture(registration, output, record, cut) for record in allowed]
    for record in blocked:
        path=output/'pending_epoch'/f"{record['document']['cycle']:06d}_{record['sha256'][:16]}.json"
        if not path.exists():
            put(path,dict(status='PENDING_EPOCH_BINDING',cycle=record['document']['cycle'],
                record_index=record['index'],record_sha256=record['sha256'],unknown_epoch_markers=unknown_markers,
                model_or_GPU_calls=0))
    status = dict(schema='R232_BOUNDARY_QUEUE_STATUS_V1', unix=time.time(),
        source_name=registration['source_name'], source_cut_index=cut,
        enrollment='LATEST_COHERENT_CUT' if latest else 'EVERY_COMPLETED_SLEEP_NO_SUBSAMPLING',
        registered_epochs=registration['runtime_epochs'], captured_ages=[row['absolute_sleep'] for row in entries],
        pending_ages=[record['document']['cycle'] for record in records], launched_ages=[], learner_signals=[],
        pending_epoch_ages=[record['document']['cycle'] for record in blocked],
        unknown_epoch_markers=unknown_markers, queue_only=True, source_binding_verified=not unknown_markers)
    output.mkdir(parents=True, mode=0o700, exist_ok=True)
    temporary=output/'STATUS.tmp'
    temporary.write_bytes(canonical(status)+b'\n')
    temporary.replace(output/'STATUS.json')
    return status


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--registration', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--latest', action='store_true')
    parser.add_argument('--until-unix', type=float)
    parser.add_argument('--poll-seconds', type=float, default=60)
    args = parser.parse_args()
    registration = json.loads(args.registration.read_bytes())
    registration_sha = file_hash(args.registration)
    while True:
        if file_hash(args.registration) != registration_sha:
            raise ValueError('frozen_registration_changed')
        status = scan(registration, args.output, latest=args.latest)
        print(json.dumps(status), flush=True)
        if args.until_unix is None or time.time() >= args.until_unix:
            break
        time.sleep(min(args.poll_seconds, max(0,args.until_unix-time.time())))


if __name__ == '__main__':
    main()
