"""Read-only exporter for the pinned R231 birth and observed pair source."""

import hashlib
import io
import json
import os
from pathlib import Path
import stat
import sys
import tarfile


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def raw(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as handle:
        before = os.fstat(handle.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_size <= 256 * 1024**2, 'bounded_regular_asset')
        content = handle.read()
        after = os.fstat(handle.fileno())
    require((before.st_ino, before.st_size, before.st_mtime_ns) ==
        (after.st_ino, after.st_size, after.st_mtime_ns), 'asset_stable_during_read')
    return content


def digest(content):
    return hashlib.sha256(content).hexdigest()


def identity():
    process = Path('/proc') / str(EXPECTED['native']['pid'])
    fields = (process / 'stat').read_text().rsplit(') ', 1)[1].split()
    require(fields[19] == EXPECTED['native']['start_ticks'], 'exact_source_native_incarnation')
    require(str((process / 'cwd').resolve()) == EXPECTED['native']['cwd'], 'exact_source_native_cwd')
    require(digest(raw(EXPECTED['guard_path'])) == EXPECTED['guard_sha256'], 'exact_source_guard')


def main():
    identity()
    source = Path(EXPECTED['native']['cwd'])
    original = source.parents[1]
    plan_raw = raw(original / 'control/PLAN.json')
    plan = json.loads(plan_raw)
    initial = original / 'raw/checkpoints/initial'
    commit = json.loads(raw(initial / 'COMMIT.json'))
    require(commit['optimizer_steps'] == 0, 'initial_optimizer_zero_only')
    files = {'common/ORIGINAL_PLAN.json': plan_raw,
        'common/ORIGINAL_BIRTH_RECORD.json': raw(original / 'raw/stream/records/00000000000000000000.json')}
    for relative, expected in EXPECTED['source_pins'].items():
        path = source / relative
        require(path.resolve() == path, 'no_source_symlinks')
        content = raw(path)
        require(digest(content) == expected, 'exact_entire_observed_source:' + relative)
        files['source/' + relative] = content
    for path in initial.rglob('*'):
        require(not path.is_symlink(), 'no_initial_symlinks')
        if path.is_file():
            files['common/initial/' + str(path.relative_to(initial))] = raw(path)
    startup = Path(plan['startup_context']['path'])
    content = raw(startup)
    require(digest(content) == plan['startup_context']['sha256'], 'exact_original_birth_bytes')
    files['source/context/BIRTH_R231.txt'] = content
    anchor_root = Path(plan['anchors'])
    for path in anchor_root.rglob('*'):
        require(not path.is_symlink(), 'no_anchor_symlinks')
        if path.is_file():
            files['common/anchors/' + str(path.relative_to(anchor_root))] = raw(path)
    record = json.loads(files['common/ORIGINAL_BIRTH_RECORD.json'])
    require(record['kind'] == 'COMMITTED' and record['document']['kind'] == 'BIRTH', 'exact_original_birth')
    state = record['document']['state']['state']
    require(not state['rows'] and not state['sleep_receipts'] and state['pending'] is None, 'no_learned_birth_state')
    identity()
    manifest = dict(schema='EXACT_R231_INITIAL_AND_PAIR_CLOSURE_V1',
        source_observation_sha256=OBSERVATION_SHA256,
        source_guard_sha256=EXPECTED['guard_sha256'], source_pins=EXPECTED['source_pins'],
        original_root=str(original), initial_checkpoint=commit,
        original_plan_sha256=digest(plan_raw), original_context_limit=state['context_limit'],
        files={name: dict(sha256=digest(content), bytes=len(content)) for name, content in files.items()},
        remote_writes=0, GPU_calls=0)
    files['ASSET_MANIFEST.json'] = (json.dumps(manifest, sort_keys=True, indent=2) + '\n').encode()
    with tarfile.open(fileobj=sys.stdout.buffer, mode='w|') as archive:
        for name, content in files.items():
            metadata = tarfile.TarInfo(name)
            metadata.size = len(content)
            metadata.mode = 0o600
            archive.addfile(metadata, io.BytesIO(content))


if __name__ == '__main__':
    main()
