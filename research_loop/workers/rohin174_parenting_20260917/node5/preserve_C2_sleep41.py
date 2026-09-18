"""Preserve C2 sleep41 for R184 preparation only, excluding all generation suffixes."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import time


ROOT = Path('/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life')
OUTPUT = None
ANCHOR = 'adcbefb57e9598fe75dfadd294dec0ef6aa1530faefbc4574b8b47c7cd834cc9'
OPTIMIZER = '6ea6fa9ffdfe806308293f1e08749b6cfea08f1bf1cae07f6a86608af1db80df'


def digest(document):
    return hashlib.sha256(json.dumps(document, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    require(OUTPUT.parent == ROOT.parents[1] and OUTPUT.name.startswith('orch_r184_C2_sleep41_'), 'owned_preparation_only')
    require(not OUTPUT.exists(), 'new_preserved_directory')
    require(shutil.disk_usage(OUTPUT.parent).free > 2 * 1024 ** 3, 'copy_disk_headroom')
    source_checkpoint = ROOT / 'checkpoints/sleep_000041'
    require(sha(source_checkpoint / 'optimizer_rng.pt') == OPTIMIZER, 'fixed_optimizer_rng')
    OUTPUT.mkdir(mode=0o700)
    target_records = OUTPUT / 'stream/records'
    target_records.mkdir(parents=True)
    previous = None
    total_bytes = 0
    for index in range(5129):
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
    anchor = json.loads((target_records / '00000000000000005128.json').read_bytes())
    require(anchor['kind'] == 'SLEEP_COMPLETE' and anchor['document']['cycle'] == 41, 'complete41_only')
    state = anchor['document']['resume_state']
    require(digest(state['state']) == state['sha256'], 'saved_history_state_sha')
    with (OUTPUT / 'SAVED_STATE.json').open('x') as stream:
        json.dump(state, stream, sort_keys=True)
    with (OUTPUT / 'CHECKPOINT.json').open('x') as stream:
        json.dump(anchor['document']['checkpoint'], stream, sort_keys=True)
    for index in range(5129):
        name = f'{index:020d}.intent.json'
        source = ROOT / 'stream/records' / name
        require(source.is_file() and not source.is_symlink(), 'existing_intent_only')
        shutil.copyfile(source, target_records / name)
        require(sha(source) == sha(target_records / name), 'same_intent_bytes')
    shutil.copyfile(ROOT / 'stream/JOURNAL.json', OUTPUT / 'stream/JOURNAL.json')
    (OUTPUT / 'workspace').mkdir(mode=0o700)
    files = {}
    for source in sorted(source_checkpoint.rglob('*')):
        require(not source.is_symlink(), 'no_checkpoint_symlinks')
        if not source.is_file():
            continue
        relative = source.relative_to(source_checkpoint)
        destination = OUTPUT / 'checkpoints/sleep_000041' / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        expected = sha(source)
        shutil.copyfile(source, destination)
        require(sha(destination) == expected == sha(source), 'exact_unchanged_checkpoint_copy')
        destination.chmod(0o444)
        files[str(relative)] = expected
    require(files['optimizer_rng.pt'] == OPTIMIZER, 'copied_optimizer_rng')
    result = dict(status='R184_C2_COMPLETE41_CHECKPOINT_AND_PREFIX_PRESERVED_NOT_LAUNCHED', observed_unix=time.time(),
                  source=str(ROOT), output=str(OUTPUT), journal_prefix_records=5129, journal_prefix_end_sha256=ANCHOR,
                  transcript_bytes=total_bytes, checkpoint_files=files,
                  saved_state_sha256=state['sha256'], optimizer_steps=4428,
                  suffix_start_excluded=5129, inbox_not_transplanted=True,
                  saved_state_file_sha256=sha(OUTPUT / 'SAVED_STATE.json'),
                  workspace='Empty authoritative service workspace observed separately on VM; no workspace text manufactured',
                  source_root='/localhome/local-rohing/orch_r179_context_C2_20260917_attempt4/source',
                  cached_R181_source='/localhome/local-rohing/orch_r181_node5_c2_1789683406847361492/source',
                  launcher='/localhome/local-rohing/orch_r181_node5_c2_1789683406847361492/rollout_operator.py',
                  launcher_scope='NODE5 only; Main must use its Node2 R184 stage driver and fresh admission, not execute this launcher on Node2',
                  raw_visible_history_in_anchor_resume_state=True, child_signals=0, source_writes=0,
                  note='Evidence archive, not a new running life; restore through existing saved-state admission')
    receipt = OUTPUT / 'PRESERVATION_RECEIPT.json'
    with receipt.open('x') as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
    receipt.chmod(0o444)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    OUTPUT = parser.parse_args().output
    main()
