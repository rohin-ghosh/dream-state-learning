"""Exact new pair source staging and original-native checks; no process actions."""

import base64
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import stat
import tarfile
import time


ROOT = Path('/localhome/local-rohing/orch_retention_20260919')
LIVES = ('curriculum_learner', 'curriculum_frozen_sibling')


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def checksum(content):
    return hashlib.sha256(content).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def inventory(source):
    result = {}
    for path in sorted(Path(source).rglob('*')):
        require(not path.is_symlink(), 'source_symlink_refused')
        if path.is_file() and path.suffix == '.py':
            result[str(path.relative_to(source))] = checksum(path.read_bytes())
    return result


def exact_native(observation):
    expected = observation['native']
    process = Path('/proc') / str(expected['pid'])
    fields = (process / 'stat').read_text().rsplit(') ', 1)[1].split()
    actual = dict(pid=expected['pid'], start_ticks=fields[19], uid=process.stat().st_uid,
        argv=(process / 'cmdline').read_bytes().decode().rstrip('\0').split('\0'),
        cwd=str((process / 'cwd').resolve()), boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
    require(actual == {key: expected[key] for key in actual} and fields[0] not in ('Z', 'X', 'T', 't'),
        'exact_original_live_unstopped_native_required')
    guard_path = Path(observation['guard_path'])
    require(checksum(guard_path.read_bytes()) == observation['guard_sha256'], 'exact_old_guard_unchanged')
    guard = read(guard_path)
    require(guard['source_pins'] == observation['source_pins']
        and checksum(Path(guard['plan_path']).read_bytes()) == guard['plan_sha256']
        and read(guard['plan_path']) == observation['plan'], 'original_source_plan_guard_binding')
    require(inventory(Path(actual['cwd'])) == observation['source_pins'], 'exact_old_source_closure')
    require(str(Path(guard.get('copy_raw', observation['plan']['root'])) / 'stream') == observation['journal_root']
        and read(Path(observation['journal_root']) / 'JOURNAL.json')['journal_id'] == observation['journal_id'],
        'original_copy_raw_journal_identity')
    for name in ('allocation', 'lease'):
        require(checksum(Path(guard[name + '_path']).read_bytes()) == guard[name + '_sha256'],
            'original_' + name + '_bytes')
    actual.update(state=fields[0], guard_sha256=observation['guard_sha256'],
        source_pins_sha256=checksum(json.dumps(observation['source_pins'], sort_keys=True).encode()),
        mount_namespace=os.readlink(process / 'ns/mnt'), journal_id=observation['journal_id'],
        deadline_unix=observation['plan']['hard_end_unix'], observed_unix=time.time())
    return actual


def validated_members(archive, expected, roots):
    require(checksum(archive) == expected and len(archive) <= 32 * 1024**2, 'exact_bounded_staging_archive')
    names, result, total = set(), [], 0
    with tarfile.open(fileobj=io.BytesIO(archive), mode='r:gz') as bundle:
        for member in bundle.getmembers():
            path = PurePosixPath(member.name)
            require(str(path) == member.name and not path.is_absolute() and '..' not in path.parts
                and member.name not in names and (member.isdir() or member.isfile())
                and any(path == root or root in path.parents for root in roots), 'only_unique_regular_declared_paths')
            require(not member.mode & 0o7000, 'no_special_staging_modes')
            names.add(member.name)
            total += member.size
            require(len(names) <= 1800 and total <= 64 * 1024**2, 'bounded_staging_members')
            result.append((path, member.mode, bundle.extractfile(member).read() if member.isfile() else None))
    require(all(str(root) in names for root in roots), 'all_declared_roots_present')
    return result


def verify_existing(root, members):
    for relative, mode, content in members:
        path = ROOT / relative
        if relative != root and root not in relative.parents:
            continue
        require(path.exists() and path.resolve() == path and not path.is_symlink(), 'existing_path_mismatch_stop')
        require(stat.S_IMODE(path.stat().st_mode) == mode, 'existing_mode_mismatch_stop')
        require(path.is_dir() if content is None else path.is_file() and path.read_bytes() == content,
            'existing_bytes_mismatch_stop')


def stage(request):
    observations = request['observations']
    require(set(observations) == set(LIVES), 'pair_only')
    before = {life: exact_native(observations[life]) for life in LIVES}
    roots = [PurePosixPath(life) / 'epoch4' for life in LIVES]
    roots += [PurePosixPath('pair_operator_bundle_v4'), PurePosixPath('pair_prefix_producer_v4'),
        PurePosixPath(request['checks_name'])]
    require(request['checks_name'].startswith('pair_epoch4_cpu_20260919_')
        and len(PurePosixPath(request['checks_name']).parts) == 1, 'own_dated_checks_root')
    members = validated_members(base64.b64decode(request['archive'], validate=True), request['archive_sha256'], roots)
    mapping = {str(path): content for path, mode, content in members}
    for life in LIVES:
        manifest = json.loads(mapping[life + '/epoch4/EPOCH4_SOURCE.json'])
        observation = observations[life]
        require(manifest['new_source'] == str(ROOT / life / 'epoch4/source')
            and manifest['old_guard_sha256'] == observation['guard_sha256']
            and manifest['old_source_pins'] == observation['source_pins']
            and manifest['journal_id'] == observation['journal_id']
            and manifest['deadline_unix'] == observation['plan']['hard_end_unix'], 'exact_old_to_new_staging_binding')
    existing = []
    for root in roots:
        target = ROOT / root
        require(target.parent.resolve() == target.parent and ROOT.resolve() == ROOT, 'literal_staging_parent')
        if target.exists() or target.is_symlink():
            verify_existing(root, members)
            existing.append(root)
    for root in roots:
        if root not in existing:
            (ROOT / root).mkdir(mode=0o700)
    for relative, mode, content in members:
        if any(relative == root or root in relative.parents for root in existing):
            continue
        path = ROOT / relative
        if content is None:
            path.mkdir(parents=True, exist_ok=True)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('xb') as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
    for relative, mode, content in sorted(members, key=lambda entry: len(entry[0].parts), reverse=True):
        if not any(relative == root or root in relative.parents for root in existing):
            (ROOT / relative).chmod(mode)
    for root in roots:
        verify_existing(root, members)
    for life in LIVES:
        manifest = read(ROOT / life / 'epoch4/EPOCH4_SOURCE.json')
        source = ROOT / life / 'epoch4/source'
        require(inventory(source) == manifest['new_source_pins'], 'complete_211_file_source_match')
        for name, metadata in manifest['additional_assets'].items():
            require(checksum((source / name).read_bytes()) == metadata['sha256'], 'unchanged_additional_asset')
    after = {life: exact_native(observations[life]) for life in LIVES}
    return dict(status='PAIR_EPOCH4_STAGED_ONLY_NOT_ADMITTED', before=before, after=after,
        archive_sha256=request['archive_sha256'], checks_root=str(ROOT / request['checks_name']),
        roots=[str(ROOT / root) for root in roots], verified_existing=[str(root) for root in existing],
        native_signals=[], parent_actions=[], journal_writes=0, GPU_calls=0, admission_granted=False)
