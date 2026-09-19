"""Stage a non-running immutable retention source closure on its existing node."""

import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import time


FILES = {'gpu/orch_r184_think_act_learn.py', 'organism_v6/orch_r125_continual_stream.py',
    'organism_v6/orch_r124_train_history.py'}


def digest(content):
    return hashlib.sha256(content).hexdigest()


def inventory(root):
    return {str(path.relative_to(root)): digest(path.read_bytes()) for path in root.rglob('*.py')}


def stage(observation, overlay, epoch_root):
    if set(overlay) != FILES or observation['status'] != 'EXACT_GUARDED_SOURCE_VERIFIED':
        raise ValueError('three_file_source_bound_retention_overlay')
    native = observation['native']
    process = Path('/proc') / str(native['pid'])
    fields = (process / 'stat').read_text().rsplit(') ', 1)[1].split()
    if (fields[19] != native['start_ticks'] or fields[0] in ('Z', 'X')
            or str((process / 'cwd').resolve()) != native['cwd']
            or process.stat().st_uid != native['uid']
            or (process / 'cmdline').read_bytes().decode().rstrip('\0').split('\0') != native['argv']
            or Path('/proc/sys/kernel/random/boot_id').read_text().strip() != native['boot_id']):
        raise ValueError('same_live_native_before_staging')
    if digest(Path(observation['guard_path']).read_bytes()) != observation['guard_sha256']:
        raise ValueError('original_admitted_guard_changed')
    source = Path(native['cwd'])
    if inventory(source) != observation['source_pins']:
        raise ValueError('original_runtime_source_changed')
    epoch = Path(epoch_root)
    if not epoch.is_absolute() or '..' in epoch.parts or epoch.exists():
        raise ValueError('new_immutable_epoch_directory')
    epoch.mkdir(parents=True, mode=0o700)
    target = epoch / 'source'
    shutil.copytree(source, target, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    if inventory(target) != observation['source_pins']:
        raise ValueError('copied_original_source_mismatch')
    changed = {}
    for name, entry in overlay.items():
        if entry['before'] != observation['source_pins'][name] or digest(entry['text'].encode()) != entry['after']:
            raise ValueError('overlay_exact_pre_and_post_hash')
        ast.parse(entry['text'], filename=name)
        (target / name).write_text(entry['text'])
        changed[name] = dict(before=entry['before'], after=entry['after'])
    pins = inventory(target)
    if set(pins) != set(observation['source_pins']):
        raise ValueError('source_file_inventory_unchanged')
    if {name for name in pins if pins[name] != observation['source_pins'][name]} != FILES:
        raise ValueError('only_three_retention_files_changed')
    if any(pins[name] != changed[name]['after'] for name in FILES):
        raise ValueError('staged_overlay_hash_mismatch')
    if inventory(source) != observation['source_pins']:
        raise ValueError('live_source_never_modified')
    receipt = dict(status='IMMUTABLE_SOURCE_STAGED_NOT_DISPATCHABLE', life=observation['life'],
        observed_unix=time.time(), old_guard_sha256=observation['guard_sha256'],
        native=native, journal_id=observation['journal_id'], journal_root=observation['journal_root'],
        old_source=str(source), new_source=str(target), old_source_pins=observation['source_pins'],
        new_source_pins=pins, changed=changed, native_signals=[], new_GPU_processes=0,
        receiving_plan_ready=False, complete_boundary_reserved=False, historical_rows_changed=False)
    with (epoch / 'SOURCE_STAGED.json').open('x') as handle:
        json.dump(receipt, handle, sort_keys=True, indent=2)
        handle.write('\n')
        handle.flush()
        os.fsync(handle.fileno())
    return receipt
