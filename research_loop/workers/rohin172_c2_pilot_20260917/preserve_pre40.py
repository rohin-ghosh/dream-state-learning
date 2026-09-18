"""Preserve C2's fixed pre-intervention checkpoint and complete journal prefix."""

import hashlib
import json
from pathlib import Path
import shutil
import time


ROOT = Path('/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life')
OUTPUT = Path('/localhome/local-rohing/orch_r172_c2_preserved_pre40_20260917')
ANCHOR = '9aef056e123b99e5fa5bbb9ce5e446391313a94b8d64acf342faf9aab1c34fee'
OPTIMIZER = '45cafa5a43f5975c9148b57329cdf9e5b43618b6fd0a4d77db829eb15fc6b4fb'


def digest(document):
    return hashlib.sha256(json.dumps(document, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    require(not OUTPUT.exists(), 'new_preserved_directory')
    source_checkpoint = ROOT / 'checkpoints/sleep_000040'
    require(sha(source_checkpoint / 'optimizer_rng.pt') == OPTIMIZER, 'fixed_optimizer_rng')
    OUTPUT.mkdir(mode=0o700)
    target_records = OUTPUT / 'stream/records'
    target_records.mkdir(parents=True)
    previous = None
    total_bytes = 0
    for index in range(4944):
        source = ROOT / 'stream/records' / f'{index:020d}.json'
        require(not source.is_symlink() and source.is_file() and source.stat().st_size <= 16 * 1024 * 1024,
                'bounded_regular_record')
        raw = source.read_bytes()
        total_bytes += len(raw)
        require(total_bytes <= 1024 * 1024 * 1024, 'bounded_transcript_prefix')
        record = json.loads(raw)
        require(record['journal_id'] == '260be8b8710a42559b291797c6e14983' and record['index'] == index,
                'same_C2_prefix')
        require(record['sha256'] == digest({key: value for key, value in record.items() if key != 'sha256'}),
                'record_digest')
        if previous is not None:
            require(record['previous_sha256'] == previous, 'record_chain')
        previous = record['sha256']
        destination = target_records / source.name
        with destination.open('xb') as stream:
            stream.write(raw)
        destination.chmod(0o444)
    require(previous == ANCHOR, 'exact_fixed_prefix_end')
    files = {}
    for source in sorted(source_checkpoint.rglob('*')):
        require(not source.is_symlink(), 'no_checkpoint_symlinks')
        if not source.is_file():
            continue
        relative = source.relative_to(source_checkpoint)
        destination = OUTPUT / 'checkpoints/sleep_000040' / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        expected = sha(source)
        shutil.copyfile(source, destination)
        require(sha(destination) == expected == sha(source), 'exact_unchanged_checkpoint_copy')
        destination.chmod(0o444)
        files[str(relative)] = expected
    require(files['optimizer_rng.pt'] == OPTIMIZER, 'copied_optimizer_rng')
    result = dict(status='PRE40_EXACT_CHECKPOINT_AND_TRANSCRIPT_PRESERVED', observed_unix=time.time(),
                  source=str(ROOT), output=str(OUTPUT), journal_prefix_records=4944, journal_prefix_end_sha256=ANCHOR,
                  transcript_bytes=total_bytes, checkpoint_files=files,
                  raw_visible_history_in_anchor_resume_state=True, child_signals=0, source_writes=0,
                  note='Evidence archive, not a new running life; restore through existing saved-state admission')
    receipt = OUTPUT / 'PRESERVATION_RECEIPT.json'
    with receipt.open('x') as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
    receipt.chmod(0o444)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
