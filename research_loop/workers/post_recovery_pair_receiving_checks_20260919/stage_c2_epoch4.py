"""Stage a pinned C2 receiving bundle without activating or changing a native."""

import base64
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import tarfile
import time


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def validated_members(archive, expected_sha256):
    require(hashlib.sha256(archive).hexdigest() == expected_sha256, 'exact_prepared_archive')
    result = []
    names = set()
    total = 0
    with tarfile.open(fileobj=io.BytesIO(archive), mode='r:gz') as bundle:
        for member in bundle.getmembers():
            relative = PurePosixPath(member.name)
            require(not relative.is_absolute() and '..' not in relative.parts
                    and relative.parts[:2] == ('C2', 'epoch4')
                    and member.name not in names and (member.isdir() or member.isfile()),
                    'only_unique_regular_epoch4_paths')
            require(member.mode & 0o7000 == 0, 'no_special_file_modes')
            names.add(member.name)
            total += member.size
            require(len(names) <= 400 and total <= 16 * 1024 * 1024,
                    'bounded_receiving_bundle')
            content = bundle.extractfile(member).read() if member.isfile() else None
            result.append((relative, member.mode, content))
    require(any(str(relative) == 'C2/epoch4/EPOCH4_SOURCE.json'
                for relative, mode, content in result), 'receiving_manifest_required')
    return result


def stage(request, checks):
    observation = request['observation']
    require(observation['life'] == 'C2', 'C2_only')
    checks['exact_native'](observation)
    require(checks['inventory'](Path(observation['native']['cwd'])) == observation['source_pins'],
            'exact_original_native_source_closure')
    archive = base64.b64decode(request['archive'], validate=True)
    members = validated_members(archive, request['archive_sha256'])
    manifest_bytes = next(content for relative, mode, content in members
                          if str(relative) == 'C2/epoch4/EPOCH4_SOURCE.json')
    require(hashlib.sha256(manifest_bytes).hexdigest() == request['manifest_sha256'],
            'exact_prepared_manifest')
    manifest = json.loads(manifest_bytes)
    require(manifest['old_source_pins'] == observation['source_pins']
            and manifest['old_guard_sha256'] == observation['guard_sha256']
            and manifest['journal_id'] == observation['journal_id']
            and manifest['deadline_unix'] == observation['plan']['hard_end_unix'],
            'same_old_native_journal_source_and_deadline')
    root = Path('/localhome/local-rohing/orch_retention_20260919')
    target = root / 'C2/epoch4'
    require(manifest['new_source'] == str(target / 'source'), 'exact_declared_epoch4_destination')
    require((root / 'C2').resolve() == root / 'C2' and not target.exists(),
            'fresh_literal_receiving_destination')
    target.mkdir(mode=0o700)
    for relative, mode, content in members:
        path = root.joinpath(*relative.parts)
        if content is None:
            path.mkdir(parents=True, exist_ok=True)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('xb') as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
    for relative, mode, content in sorted(members, key=lambda item: len(item[0].parts), reverse=True):
        path = root.joinpath(*relative.parts)
        path.chmod(mode)
    require(checks['inventory'](target / 'source') == manifest['new_source_pins'],
            'whole_receiving_source_closure_matches')
    for name, metadata in manifest['additional_assets'].items():
        require(hashlib.sha256((target / 'source' / name).read_bytes()).hexdigest() == metadata['sha256'],
                'exact_additional_asset')
    checks['exact_native'](observation)
    require(checks['inventory'](Path(observation['native']['cwd'])) == observation['source_pins'],
            'original_source_untouched')
    return dict(status='C2_EPOCH4_STAGED_NOT_ADMITTED_NOT_DEPLOYED', observed_unix=time.time(),
                source=str(target / 'source'), archive_sha256=request['archive_sha256'],
                manifest_sha256=request['manifest_sha256'], native_unchanged=True,
                native_signals=[], GPU_calls=0, journal_writes=0, live_adoption=False,
                original_source_unchanged=True, hard_end_unix=manifest['deadline_unix'],
                source_file_count=len(manifest['new_source_pins']))
