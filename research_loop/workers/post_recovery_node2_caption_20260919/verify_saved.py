"""Read-only committed-file verification; no research imports or native actions."""

import hashlib
import json
import os
from pathlib import Path
import time


BASE = Path('/localhome/local-rohing/orch_r229_unparented_caption_20260918/r213_r226_caption_unparented_fork')
GUARD_SHA = 'f17b2c06389e3ef2d1f9e6fac439c096aead14c788421ddc191039418b891ec2'
PLAN_SHA = '6588bfe99b0a491bb54cc608ca980842a13f66d3a24b61fb677f1286d18476e6'
COMMIT_SHA = 'a5d4034d71916d9f5af8eecd9653fb1be62ecd8c37e29259cf06448dd0008c44'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def identity(path):
    metadata = path.lstat()
    require(not path.is_symlink(), 'symlink_refused')
    return [metadata.st_dev, metadata.st_ino, metadata.st_size, metadata.st_mtime_ns, metadata.st_ctime_ns]


def sha(path):
    before = identity(path)
    checksum = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            checksum.update(chunk)
    require(identity(path) == before, 'file_changed_during_hash')
    return checksum.hexdigest()


def main():
    started = time.monotonic()
    guard_path = BASE / 'control_r233_recovery/GUARD.json'
    require(sha(guard_path) == GUARD_SHA, 'original_guard_changed')
    guard = json.loads(guard_path.read_bytes())
    plan_path = Path(guard['plan_path'])
    require(sha(plan_path) == PLAN_SHA, 'original_plan_changed')
    plan = json.loads(plan_path.read_bytes())
    raw = Path(guard['copy_raw'])
    require(raw == BASE / 'raw' and plan['hard_end_unix'] == 1789927200, 'original_root_deadline')
    commit_path = raw / 'checkpoints/sleep_000119/COMMIT.json'
    require(sha(commit_path) == COMMIT_SHA, 'original_COMMIT_changed')
    checkpoint = json.loads(commit_path.read_bytes())
    adapter = raw / Path(checkpoint['adapter_path']).relative_to(plan['root'])
    optimizer = raw / Path(checkpoint['optimizer_rng_path']).relative_to(plan['root'])
    files = {path.name: sha(path) for path in sorted(adapter.iterdir()) if path.is_file()}
    require(files == checkpoint['adapter_files'], 'adapter_files_mismatch')
    require(digest(files) == checkpoint['checkpoint_sha256']['adapter'], 'adapter_digest_mismatch')
    optimizer_sha = sha(optimizer)
    require(optimizer_sha == checkpoint['checkpoint_sha256']['optimizer']
            == checkpoint['checkpoint_sha256']['rng'], 'optimizer_rng_mismatch')
    matches = []
    for entry in Path('/proc').iterdir():
        if not entry.name.isdigit():
            continue
        try:
            if entry.stat().st_uid != os.getuid() or int(entry.name) == os.getpid():
                continue
            command = (entry / 'cmdline').read_bytes().replace(b'\0', b' ').decode(errors='replace')
            cwd = os.readlink(entry / 'cwd')
            if str(guard_path) in command or cwd == plan['source_root']:
                matches.append(int(entry.name))
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            pass
    require(not matches, 'original_guard_or_source_process_present')
    print(json.dumps(dict(schema='CAPTION_COMMITTED_BINARY_VERIFICATION_V1', observed_unix=time.time(),
        boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
        guard_sha256=GUARD_SHA, plan_sha256=PLAN_SHA, commit_sha256=COMMIT_SHA,
        adapter_files=files, checkpoint_sha256=checkpoint['checkpoint_sha256'],
        optimizer_identity=identity(optimizer), adapter_identity=identity(adapter),
        optimizer_steps=checkpoint['optimizer_steps'], hard_end_unix=plan['hard_end_unix'],
        matching_same_uid_processes=matches, original_source=plan['source_root'],
        seconds=time.monotonic()-started, node_writes=False, model_loaded=False,
        native_signals=[], admission_or_readiness_claimed=False), sort_keys=True))


if __name__ == '__main__':
    main()
