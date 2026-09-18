"""Seal a future publisher outside git; mirror completed evidence without mutation."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import threading
import time
import uuid


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def exclusive_json(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)


def outside_git(path, workspace):
    resolved = Path(path).resolve()
    if resolved.is_relative_to(Path(workspace).resolve()) or any((parent / '.git').exists() for parent in (resolved, *resolved.parents)):
        raise ValueError('runtime_must_be_outside_git_worktrees')


def copy_bound(source, destination, digest):
    source, destination = Path(source), Path(destination)
    if source.is_symlink() or sha(source) != digest:
        raise ValueError('source_copy_hash_or_symlink_mismatch')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with source.open('rb') as reader, destination.open('xb') as writer:
        shutil.copyfileobj(reader, writer)
    if sha(destination) != digest:
        raise ValueError('source_changed_during_copy')


def mirror_files(files, destination):
    if any('/raw/' in str(path) or str(path).endswith(('.tar', '.tar.gz')) for path in files.values()):
        raise ValueError('disk_policy_forbids_raw_or_archive_mirroring_to_VM')
    destination = Path(destination)
    inventory = {name: sha(path) for name, path in sorted(files.items())}
    digest = hashlib.sha256(json.dumps(inventory, sort_keys=True).encode()).hexdigest()
    object_root = destination / 'objects' / digest
    if (object_root / 'MIRROR_MANIFEST.json').exists():
        if read(object_root / 'MIRROR_MANIFEST.json')['files'] != inventory or any(
                not (object_root / name).is_file() or sha(object_root / name) != expected for name, expected in inventory.items()):
            raise ValueError('published_mirror_missing_or_changed_no_overwrite')
        return object_root / 'MIRROR_MANIFEST.json'
    object_root.mkdir(parents=True, exist_ok=False)
    for name, path in files.items():
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('unsafe_mirror_relative_path')
        copy_bound(path, object_root / relative, inventory[name])
    exclusive_json(object_root / 'MIRROR_MANIFEST.json', dict(files=inventory,
        object_sha256=digest, runtime_paths={name: str(path) for name, path in files.items()},
        immutable=True, archive_contains_expanded_raw=True))
    return object_root / 'MIRROR_MANIFEST.json'


def seal(prepared_root, workspace, runtime_parent=Path('/tmp')):
    raise ValueError('superseded_by_native_disk_pipeline_do_not_copy_raw_to_VM')
    prepared_root, workspace, runtime_parent = map(Path, (prepared_root, workspace, runtime_parent))
    outside_git(runtime_parent, workspace)
    if (prepared_root / 'WATCH_LIFETIME.json').exists() or list(prepared_root.glob('batch_*/REVIEW_RESERVATION.json')):
        raise ValueError('do_not_restart_or_reseal_existing_live_segment')
    prepared, ready = read(prepared_root / 'PREPARED.json'), read(prepared_root / 'READY.json')
    if not ready['cpu_tests_passed'] or ready['prepare_sha256'] != sha(prepared_root / 'PREPARED.json'):
        raise ValueError('bound_readiness_required')
    if ready['builder_receipt_sha256'] != sha(prepared_root / 'BUILDER_RECEIPT.md'):
        raise ValueError('bound_builder_receipt_required')
    registration = read(prepared_root / 'REGISTRATION.json')
    if registration['segment_deadline_unix'] <= time.time():
        raise ValueError('deadline_expired_no_reset')
    runtime = Path(tempfile.mkdtemp(prefix='orch_continual_batch_runtime_', dir=runtime_parent))
    os.chmod(runtime, 0o700)
    inventory = {}

    def copy(source, relative, digest=None):
        digest = digest or sha(source)
        copy_bound(source, runtime / relative, digest)
        inventory[relative] = digest

    for name, digest in prepared['source_inventory'].items():
        copy(Path(prepared['pinned_source']) / name, 'source/' + name, digest)
    required = dict(prepared['files'])
    required.update({name: sha(prepared_root / name) for name in
        ('PREPARED.json', 'READY.json', 'BUILDER_RECEIPT.md', 'SEEN.json', 'FIRST_CAPTURE.json')})
    for name, digest in required.items():
        copy(prepared_root / name, 'evidence/' + name, digest)
    for folder in ('review_workspace', 'provider_bin'):
        for source in sorted((prepared_root / folder).rglob('*')):
            if source.is_file():
                copy(source, 'evidence/' + str(source.relative_to(prepared_root)))
    for batch in sorted(prepared_root.glob('batch_[0-9][0-9][0-9]')):
        for source in sorted(batch.rglob('*')):
            if source.is_file():
                copy(source, 'evidence/' + str(source.relative_to(prepared_root)))
    os.chmod(runtime / 'evidence/provider_bin/codex', 0o700)
    pilot = Path(registration['pilot_root'])
    for name, digest in read(prepared_root / 'PILOT_INVENTORY.json').items():
        copy(pilot / name, 'pilot/' + name, digest)
    old_relative = 'research_notes/analysis/orch_continual_ingest_20260915/batch_math_content_readmission473'
    old = workspace / old_relative
    old_manifest = read(old / 'MANIFEST.json')
    copy(old / 'MANIFEST.json', 'project/' + old_relative + '/MANIFEST.json')
    copy(old / old_manifest['rows_path'], 'project/' + old_relative + '/' + old_manifest['rows_path'], old_manifest['rows_sha256'])
    manifest = dict(schema='ORCH_CONTINUAL_EXTERNAL_RUNTIME_V1', files=inventory,
        original_workspace=str(workspace.resolve()), original_prepared_root=str(prepared_root.resolve()),
        mirror_root=str(prepared_root / 'IMMUTABLE_RUNTIME_MIRROR'),
        registration_sha256=sha(prepared_root / 'REGISTRATION.json'),
        deadline_unix=registration['segment_deadline_unix'], max_batches=registration['max_batches'],
        max_provider_calls=registration['max_provider_calls'], provider_binary_sha256=sha(prepared['codex_real']),
        transport='SSH_TARGET_ENV_ONLY_NO_HOSTS_ENV_OR_SECRET_COPY', budgets_reset=False)
    exclusive_json(runtime / 'RUNTIME_MANIFEST.json', manifest)
    mirror_files({name: runtime / name for name in inventory if not name.startswith('pilot/') and '/raw/' not in name} |
                 {'RUNTIME_MANIFEST.json': runtime / 'RUNTIME_MANIFEST.json'}, prepared_root / 'IMMUTABLE_RUNTIME_MIRROR')
    return runtime, sha(runtime / 'RUNTIME_MANIFEST.json')


def verify(runtime, expected_sha256):
    runtime = Path(runtime)
    if sha(runtime / 'RUNTIME_MANIFEST.json') != expected_sha256:
        raise ValueError('runtime_manifest_binding_mismatch')
    manifest = read(runtime / 'RUNTIME_MANIFEST.json')
    outside_git(runtime, manifest['original_workspace'])
    if any(sha(runtime / name) != digest for name, digest in manifest['files'].items()):
        raise ValueError('immutable_runtime_hash_mismatch')
    registration = read(runtime / 'evidence/REGISTRATION.json')
    if any(registration[key] != manifest[target] for key, target in
           (('segment_deadline_unix', 'deadline_unix'), ('max_batches', 'max_batches'), ('max_provider_calls', 'max_provider_calls'))):
        raise ValueError('runtime_budget_or_deadline_drift')
    prepared = read(runtime / 'evidence/PREPARED.json')
    outside_git(Path(prepared['codex_real']).resolve(), manifest['original_workspace'])
    if sha(prepared['codex_real']) != manifest['provider_binary_sha256']:
        raise ValueError('provider_binary_drift')
    return manifest


def mirror_completed(runtime, destination):
    evidence = runtime / 'evidence'
    for batch in sorted(evidence.glob('batch_[0-9][0-9][0-9]')):
        number = batch.name.split('_')[1]
        if not any(path.exists() for path in (batch / 'MANIFEST.json', batch / 'BATCH_DECISION.json',
                                             batch / 'INSUFFICIENT.json', evidence / f'BATCH_{number}_FAILED.json')):
            continue
        files = {}
        directories = [batch, batch.with_name(batch.name + '_ingest_v2'),
                       *sorted((evidence / 'review_workspace').glob(batch.name + '_*'))]
        for directory in directories:
            for path in sorted(directory.rglob('*')):
                if path.is_file() and 'raw' not in path.relative_to(directory).parts and not path.name.endswith('.partial'):
                    files[str(path.relative_to(evidence))] = path
        mirror_files(files, destination)
    status = {path.name: path for path in evidence.glob('*.json') if path.name not in ('SEEN.json', 'PILOT_INVENTORY.json')}
    if (evidence / 'JOURNAL.md').exists():
        status['JOURNAL.md'] = evidence / 'JOURNAL.md'
    if status:
        mirror_files(status, destination)


def execute(runtime, expected_sha256):
    raise ValueError('superseded_by_native_disk_pipeline_do_not_launch_local_snapshot_runtime')
    from gpu import orch_continual_batch_segment as segment
    from gpu import orch_continual_batch_publish as publisher
    runtime = Path(runtime).resolve()
    manifest = verify(runtime, expected_sha256)
    if not Path(__file__).resolve().is_relative_to(runtime / 'source'):
        raise ValueError('launch_module_from_external_pinned_source')
    if not os.environ.get('ORCH_CONTINUAL_BATCH_SSH_TARGET'):
        raise ValueError('transport_environment_required_no_worktree_fallback')
    segment.ROOT, segment.WORKSPACE, segment.PILOT = runtime / 'evidence', runtime / 'project', runtime / 'pilot'
    segment.JOURNAL = runtime / 'evidence/JOURNAL.md'
    segment.configure()
    publisher.RUNTIME_ROOT, publisher.RUNTIME_SOURCE = runtime, runtime / 'source'
    publisher.REMOTE = '/localhome/local-rohing/orch_continual_batch_' + runtime.name.removeprefix('orch_continual_batch_runtime_')
    segment.select_node2()
    segment.REMOTE = publisher.REMOTE
    source = '/localhome/local-rohing/orch_rich_hot_node2_20260915_attempt1'
    publisher.remote(f'mkdir -p {publisher.REMOTE}/source; tar -xf {source}/source.tar -C {publisher.REMOTE}/source')
    publisher.upload([runtime / 'source/gpu/orch_continual_batch_snapshot.py',
                      runtime / 'source/gpu/orch_continual_batch_snapshot_node2.py'], publisher.REMOTE + '/source/gpu/')
    publisher.upload([runtime / 'source/organism_v6/orch_continual_batch.py'], publisher.REMOTE + '/source/organism_v6/')
    publisher.upload([segment.ROOT / 'EXCLUSIONS.json', segment.ROOT / 'SOURCE_REGISTRY.json'], publisher.REMOTE + '/')
    stopped = threading.Event()

    def mirror_loop():
        while True:
            try:
                mirror_completed(runtime, Path(manifest['mirror_root']))
            except Exception as error:
                exclusive_json(runtime / ('MIRROR_ERROR_' + uuid.uuid4().hex + '.json'),
                    dict(observed_unix=time.time(), type=type(error).__name__, error=str(error)))
            if stopped.wait(30):
                return

    mirror = threading.Thread(target=mirror_loop, daemon=True)
    mirror.start()
    try:
        segment.watch()
    finally:
        stopped.set()
        mirror.join()
        try:
            mirror_completed(runtime, Path(manifest['mirror_root']))
        except Exception as error:
            exclusive_json(runtime / 'FINAL_MIRROR_ERROR.json', dict(error=str(error)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('seal', 'execute'))
    parser.add_argument('--prepared-root', type=Path)
    parser.add_argument('--workspace', type=Path)
    parser.add_argument('--runtime', type=Path)
    parser.add_argument('--manifest-sha256')
    options = parser.parse_args()
    if options.phase == 'seal':
        runtime, digest = seal(options.prepared_root, options.workspace)
        print(json.dumps(dict(runtime=str(runtime), manifest_sha256=digest,
            launch='Run execute from outside git with PYTHONPATH=<runtime>/source and SSH target in environment; no new deadline/caps assigned.')))
    else:
        execute(options.runtime, options.manifest_sha256)
