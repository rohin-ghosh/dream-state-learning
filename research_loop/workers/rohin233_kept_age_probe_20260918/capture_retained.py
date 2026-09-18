"""Immutable bounded copy of one retained completed adapter; never a life writer."""

import hashlib
import json
from pathlib import Path
import shutil
import time


BASE = 'a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def record(life, index, journal, checksum):
    path = life / 'stream/records' / f'{index:020d}.json'
    value = json.loads(path.read_bytes())
    if value['journal_id'] != journal or value['sha256'] != checksum or value['sha256'] != digest(
            {key: item for key, item in value.items() if key != 'sha256'}):
        raise ValueError('exact_canonical_source_record')
    return value


def capture(target, entry, output):
    life = Path(target['root'])
    if life.resolve() != life or not life.is_absolute():
        raise ValueError('pinned_physical_life')
    loaded = record(life, target['initial_loaded']['index'], target['journal_id'], target['initial_loaded']['sha256'])
    if loaded['kind'] != 'LOADED' or loaded['document']['base_sha256'] != BASE:
        raise ValueError('source_base_identity')
    complete = record(life, entry['record_index'], target['journal_id'], entry['record_sha256'])
    document = complete['document']
    if complete['kind'] != 'SLEEP_COMPLETE' or document['status'] != 'COMPLETE':
        raise ValueError('completed_only')
    checkpoint = life / 'checkpoints' / f"sleep_{document['cycle']:06d}"
    if checkpoint.resolve() != checkpoint:
        raise ValueError('no_checkpoint_symlink')
    commit = json.loads((checkpoint / 'COMMIT.json').read_bytes())
    if (commit['base_sha256'] != BASE or commit['adapter_state_sha256'] != document['after_adapter_sha256']
            or commit['optimizer_steps'] != document['total_optimizer_steps']
            or set(commit['adapter_files']) != {'README.md', 'adapter_config.json', 'adapter_model.safetensors'}):
        raise ValueError('completed_adapter_commit_join')
    names = ['COMMIT.json'] + ['adapter/' + name for name in commit['adapter_files']]
    before = {name: dict(sha256=sha(checkpoint / name), bytes=(checkpoint / name).stat().st_size) for name in names}
    if any(before['adapter/' + name]['sha256'] != checksum for name, checksum in commit['adapter_files'].items()):
        raise ValueError('retained_adapter_commit_hashes')
    key = target['label'] + '_sleep_' + str(document['cycle']).zfill(6) + '_' + entry['record_sha256'][:16]
    destination = output / key
    if destination.exists():
        existing = json.loads((destination / 'SOURCE.json').read_bytes())
        if existing['sleep_complete_sha256'] != entry['record_sha256'] or any(sha(destination / name) != row['sha256'] for name, row in existing['copy_files'].items()):
            raise ValueError('immutable_prior_capture_changed')
        return existing
    staging = output / (key + '.staging')
    staging.mkdir(parents=True, exist_ok=False, mode=0o700)
    for name in names:
        copied = staging / name
        copied.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(checkpoint / name, copied)
        if sha(copied) != before[name]['sha256'] or sha(checkpoint / name) != before[name]['sha256']:
            raise ValueError('source_before_copy_after_mismatch')
    optimizer = checkpoint / 'optimizer_rng.pt'
    optimizer_provenance = dict(sha256=sha(optimizer), bytes=optimizer.stat().st_size) if optimizer.is_file() else None
    result = dict(schema='R233_RETAINED_IMMUTABLE_SOURCE_V1', captured_unix=time.time(),
        source_name=target['label'], source_relative=key, journal_id=target['journal_id'],
        absolute_sleep=document['cycle'], relative_sleep=None, optimizer_steps=commit['optimizer_steps'],
        relative_optimizer_steps=None, base_sha256=BASE, adapter_state_sha256=commit['adapter_state_sha256'],
        sleep_complete_index=entry['record_index'], sleep_complete_sha256=entry['record_sha256'],
        source_cut_index=entry['record_index'], copy_files=before, before_after_equal=True,
        optimizer_rng_provenance=optimizer_provenance, optimizer_rng_copied_or_loaded=False,
        source_context_copied_or_loaded=False, resume_state_sha256=digest(document.get('resume_state', {})),
        cumulative_training_tokens=None, cumulative_training_seconds=None,
        eligibility='PENDING_SOURCE_AND_INHERITED_EXPOSURE_AUDIT', evaluation='PENDING', learner_signals=[])
    (staging / 'SOURCE.json').write_text(json.dumps(result, sort_keys=True))
    staging.rename(destination)
    return result
