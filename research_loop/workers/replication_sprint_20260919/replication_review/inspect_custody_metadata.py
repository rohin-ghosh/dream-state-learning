"""Receiving-host metadata only; no models, devices, services, writes or private text."""

import hashlib
import json
import os
from pathlib import Path
import stat
import time


ROOT = Path('/localhome/local-rohing/post_sampling_replication_20260919') / (
    '4df129caf0a0377ba91feec83923bc972e00b10dab13b5b198594db567689d95')


def read(path):
    if path.stat().st_size > 1_048_576 or path.is_symlink():
        raise ValueError('bounded_regular_metadata_only')
    return json.loads(path.read_bytes())


def metadata(path):
    try:
        info = path.lstat()
    except OSError as error:
        return dict(path=str(path), exists=False, error_type=type(error).__name__, errno=error.errno)
    return dict(path=str(path), exists=True, bytes=info.st_size, mode=oct(stat.S_IMODE(info.st_mode)),
        uid=info.st_uid, gid=info.st_gid, regular=stat.S_ISREG(info.st_mode),
        directory=stat.S_ISDIR(info.st_mode), symlink=stat.S_ISLNK(info.st_mode),
        inode=info.st_ino, contents_read=False)


def main():
    registry = read(ROOT / 'REGISTRY.json')
    prepared = read(ROOT / 'PREPARED.json')
    rows = []
    for job in registry['jobs']:
        config_path = Path(job['root']) / 'CONFIG.json'
        config = read(config_path)
        config_sha = hashlib.sha256(config_path.read_bytes()).hexdigest()
        expected = next(row['config_sha256'] for row in prepared['jobs'] if row['job_id'] == job['job_id'])
        if config_sha != expected:
            raise ValueError('actual_prepared_config_binding_changed')
        view = Path(config['root'])
        stages = {}
        for role in ('player', 'judge'):
            for phase in ('proof', 'run'):
                for suffix in ('STARTED', 'FAILED'):
                    path = view / (role + '_' + phase + '_' + suffix + '.json')
                    stages[path.name] = read(path) if path.exists() else None
        scientific = [str(path.relative_to(view)) for path in (view / 'players').rglob('*.json')]
        scientific += [name for name in ('JUDGE_LOADED.json', 'JUDGE_EXIT.json') if (view / name).exists()]
        original_refs = {}
        for name in ('CONFIG.json', 'CONDITION.json', 'SOURCE_MANIFEST.json', 'GAME_MANIFEST.json'):
            reference = config['original_files'][name]
            actual = hashlib.sha256(Path(reference['path']).read_bytes()).hexdigest()
            original_refs[name] = dict(expected=reference['sha256'], actual=actual, unchanged=actual == reference['sha256'])
        rows.append(dict(arm=job['arm'], job_id=job['job_id'], config_sha256=config_sha,
            common_forbidden=[metadata(Path(path)) for path in config['custody_forbidden']],
            player_private=[metadata(Path(path)) for path in config['player_private_paths']],
            stage_records=stages, scientific_receipts=scientific,
            queue_receipts=[path.name for path in (view / 'queue').glob('*.json')],
            original_source_metadata=original_refs))
    controls = {}
    for name in ('BLOCK_LAUNCH.json', 'BLOCK_FAILED.json', 'PROOFS_COMPLETE.json',
            'GPU_REVIEW.json', 'BLOCK_COMPLETE.json'):
        path = ROOT / name
        controls[name] = read(path) if path.exists() else None
    history = registry['original_history_ref']
    history_sha = hashlib.sha256(Path(history['path']).read_bytes()).hexdigest()
    claims = {}
    for role, device in registry['role_devices'].items():
        path = Path(registry['claims_namespace']) / (device['uuid'] + '.json')
        claims[role] = read(path) if path.exists() else None
    print(json.dumps(dict(observed_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        uid=os.getuid(), scope='HOST_METADATA_NOT_A_LIVE_ROLE_NAMESPACE_PROOF',
        no_writes=True, no_models=True, no_devices=True, no_service_submissions=True,
        private_contents_read=False, jobs=rows, control_records=controls, retained_claims=claims,
        source_freeze_sha256=hashlib.sha256((ROOT / 'SOURCE_FREEZE.json').read_bytes()).hexdigest(),
        original_no_retry_history=dict(path=history['path'], expected=history['sha256'], actual=history_sha,
            unchanged=history_sha == history['sha256'])), sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
