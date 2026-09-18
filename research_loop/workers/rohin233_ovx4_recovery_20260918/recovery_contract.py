"""Finite recovery admission, with state continuity and no pair-device access."""

import hashlib
import json
from pathlib import Path
import time


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def allocation_guard(config, physical, now=None):
    now = time.time() if now is None else now
    if physical not in (2, 3, 4, 5, 6, 7):
        raise ValueError('only_assigned_devices_two_through_seven')
    allocation = config['allocation']
    if not (0 < config['deadline_unix'] - now
            and config['deadline_unix'] + 21600 <= allocation['conservative_lease_boundary_unix']
            and config['deadline_unix'] <= allocation['authorized_job_end_unix']):
        raise ValueError('finite_current_allocation_no_lease_extension')
    if not allocation.get('lease_source_sha256') or not allocation.get('authority_sha256'):
        raise ValueError('bound_allocation_source_required')


def restore_contract(previous, current):
    if previous['phase'] != 'COMPLETE' or current['phase'] != 'COMPLETE':
        raise ValueError('complete_saved_session_only')
    fields = ('life_root', 'scene_ids', 'session_binding', 'source_mode', 'format_policy')
    if any(previous.get(field) != current.get(field) for field in fields):
        raise ValueError('same_source_visibility_binding')
    for field in ('game', 'policy'):
        if digest(previous[field]) != digest(current[field]):
            raise ValueError('exact_game_policy_restore')
    if set(previous['seen']) != set(current['seen']) or len(previous['seen']) != len(set(previous['seen'])):
        raise ValueError('exact_unique_seen_restore')
    return dict(seen_count=len(previous['seen']), seen_sha256=digest(sorted(previous['seen'])),
        game_sha256=digest(previous['game']), policy_sha256=digest(previous['policy']),
        source_visibility_unchanged=True, historical_rescoring=False)


def verify_files(root, manifest):
    root = Path(root)
    for relative, expected in manifest.items():
        path = root / relative
        if path.is_symlink() or not path.is_file() or '..' in Path(relative).parts or Path(relative).is_absolute():
            raise ValueError('regular_confined_source')
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('immutable_runtime_source')


def relocated_reference(previous, current):
    if set(previous) != set(current) or {key: value for key, value in previous.items() if key != 'path'} != {
            key: value for key, value in current.items() if key != 'path'}:
        raise ValueError('byte_identical_reference_relocation_only')
    path = Path(current['path'])
    if not path.is_absolute() or path != path.resolve() or not path.is_file():
        raise ValueError('canonical_relocated_source')
    if hashlib.sha256(path.read_bytes()).hexdigest() != current['sha256'] or (
            'bytes' in current and path.stat().st_size != current['bytes']):
        raise ValueError('actual_relocated_source_hash')
    return current
