"""CPU-only read-only caption observation; never writer-lock, dispatch, or model load."""

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import random
import sys
import threading
import time

from verify_saved import BASE, GUARD_SHA, PLAN_SHA, COMMIT_SHA, digest, identity, require, sha


def inventories(root):
    inbox = {path.name: dict(identity=identity(path), sha256=sha(path))
        for path in sorted((root / 'inbox').iterdir()) if path.is_file()}
    sidecars = {str(path.relative_to(root)): dict(identity=identity(path), sha256=sha(path))
        for path in sorted(root.rglob('*')) if path.is_file()
        and not path.is_relative_to(root / 'records') and not path.is_relative_to(root / 'inbox')}
    return dict(inbox=inbox, sidecars=sidecars)


def old_bindings():
    guard_path = BASE / 'control_r233_recovery/GUARD.json'
    require(sha(guard_path) == GUARD_SHA, 'original_guard_pin')
    guard = json.loads(guard_path.read_bytes())
    require(sha(Path(guard['plan_path'])) == PLAN_SHA, 'original_plan_pin')
    plan = json.loads(Path(guard['plan_path']).read_bytes())
    for name, expected in guard['source_pins'].items():
        require(sha(Path(plan['source_root']) / name) == expected, 'original_source_changed:' + name)
    for entry in Path('/proc').iterdir():
        if not entry.name.isdigit() or int(entry.name) == os.getpid():
            continue
        try:
            if entry.stat().st_uid != os.getuid():
                continue
            command = (entry / 'cmdline').read_bytes().replace(b'\0', b' ').decode(errors='replace')
            require(str(guard_path) not in command and os.readlink(entry / 'cwd') != plan['source_root'],
                'matching_original_process_present')
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            pass
    return guard, plan


def probe(prepared):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'explicit_CPU_environment')
    started = time.monotonic()
    manifest = json.loads((prepared / 'MANIFEST.json').read_bytes())
    source = Path(manifest['source'])
    require({str(path.relative_to(source)): sha(path) for path in source.rglob('*') if path.is_file()}
        == manifest['all_files'], 'exact_staged_source_closure')
    guard, old_plan = old_bindings()
    plan = json.loads((prepared / 'PLAN_CANDIDATE.json').read_bytes())
    raw = Path(guard['copy_raw'])
    root = raw / 'stream'
    original_before = inventories(root)
    record_identities = {path.name: identity(path) for path in (root / 'records').iterdir()}
    sys.path.insert(0, str(source))
    from gpu import orch_r125_continual_native as native
    from gpu.r213_recovery_runtime import RecoveryJournal
    from gpu.caption_tail_runtime import bind_journal, verify_startup
    from gpu.checkpoint_tail_runtime import scan
    from gpu.orch_r125_stream_journal import _decode
    native.validate_plan(plan)
    family = bind_journal(RecoveryJournal, plan)
    require(issubclass(family, RecoveryJournal), 'original_recovery_family')
    selection = deepcopy(plan['checkpoint_tail_recovery'])
    selection['root'] = str(root)
    journal = object.__new__(RecoveryJournal)
    journal.root = root
    journal.inbox = Path(plan['root']) / 'stream/inbox'
    journal._owner = os.getpid()
    journal._mutex = threading.RLock()
    journal._fds = []
    journal._closed = journal._failed = False
    try:
        journal._root_fd = journal._open(root, os.O_RDONLY | os.O_DIRECTORY)
        journal._lock_fd = journal._open('WRITER.lock', os.O_RDONLY, journal._root_fd)
        journal._records_fd = journal._open('records', os.O_RDONLY | os.O_DIRECTORY, journal._root_fd)
        journal._inbox_fd = journal._open('inbox', os.O_RDONLY | os.O_DIRECTORY, journal._root_fd)
        journal._manifest = journal._read_json(journal._root_fd, 'JOURNAL.json')
        scan_started = time.monotonic()
        before = journal._record_snapshot()
        journal._state = scan(journal, selection)
        require(journal._record_snapshot() == before, 'record_changed_during_scan')
        scan_seconds = time.monotonic() - scan_started
        verify_started = time.monotonic()
        verify_startup(journal, selection, plan['hard_end_unix'])
        state = journal._state['latest']['document']
        require(state['sha256'] == '058e9001c3c2947163b8b3eb52fe5913ea8c83924462dfc5b2fd6329193f979e'
            and len(state['state']['rows']) == state['state']['sleep_frontier'] == 487
            and len(state['state']['sleep_receipts']) == 119
            and journal._state['index'] == 8529
            and journal._state['previous'] == '58177fb38f89c7ab66cfa79a4f7d1a8c30d4eb1e8385dc410fb8abcc70a45c39',
            'exact_assessed_clean_COMPLETE_LEARN_state')
        present = {}
        for name in sorted(os.listdir(journal._inbox_fd)):
            require(not (root / 'inbox' / name).is_symlink(), 'inbox_symlink_forbidden')
            if not name.endswith('.json'):
                continue
            raw_message = journal._read_bytes(journal._inbox_fd, name, 1024 * 1024)
            message = _decode(raw_message)
            source_id = str(journal.inbox / name)
            message_sha = hashlib.sha256(raw_message).hexdigest()
            journal._inbox_event(message, source_id, message_sha)
            existing = present.get(message['id'])
            require(existing is None or existing['sha256'] == message_sha, 'conflicting_inbox_id_bytes')
            present[message['id']] = dict(source_id=source_id, sha256=message_sha)
        for identifier, known in journal._state['inbox'].items():
            require(present.get(identifier) == dict(source_id=known['source_id'], sha256=known['source_sha256']),
                'registered_inbox_missing_or_changed')
        commit_path = raw / 'checkpoints/sleep_000119/COMMIT.json'
        require(sha(commit_path) == COMMIT_SHA, 'exact_COMMIT_pin')
        checkpoint = json.loads(commit_path.read_bytes())
        require(state['state']['sleep_receipts'][-1]['checkpoint'] == checkpoint, 'exact_saved_commit_document')
        mapped = deepcopy(checkpoint)
        for field in ('adapter_path', 'optimizer_rng_path'):
            mapped[field] = str(raw / Path(checkpoint[field]).relative_to(plan['root']))
        native.NativeChild.verify_checkpoint(mapped)
        integrity_seconds = time.monotonic() - verify_started
        payload_started = time.monotonic()
        import torch
        payload = torch.load(mapped['optimizer_rng_path'], map_location='cpu', weights_only=False)
        require(payload['optimizer_steps'] == checkpoint['optimizer_steps'] == 10236, 'exact_saved_optimizer_counter')
        require(payload.get('experiment') == checkpoint['experiment'] == state['state']['experiment'],
            'exact_saved_experiment')
        optimizer = payload['optimizer']
        parameters = [number for group in optimizer['param_groups'] for number in group['params']]
        require(len(parameters) == len(set(parameters)) == len(payload['parameter_names'])
            and len(set(payload['parameter_names'])) == len(parameters)
            and set(optimizer['state']) == set(parameters), 'complete_optimizer_parameter_structure')
        for parameter in parameters:
            values = optimizer['state'][parameter]
            require(int(values['step']) == 10236 and values['exp_avg'].shape == values['exp_avg_sq'].shape
                and values['exp_avg'].device.type == values['exp_avg_sq'].device.type == 'cpu',
                'saved_adamw_state_complete_on_CPU')
        torch.Generator(device='cpu').set_state(payload['cpu_rng'])
        random.Random().setstate(payload['python_rng'])
        require(len(payload['cuda_rng']) == 1 and payload['cuda_rng'][0].device.type == 'cpu'
            and payload['cuda_rng'][0].numel() > 0 and not torch.cuda.is_initialized(), 'saved_rng_CPU_only')
        payload_seconds = time.monotonic() - payload_started
        authorization = old_plan['authorized_wall_extension']
        require(authorization['new_deadline_unix'] == state['state']['deadline_unix'] == plan['hard_end_unix']
            == 1789927200 and 'authorized_wall_extension' not in plan, 'consumed_wall_metadata_no_new_wall')
        after = inventories(root)
        require(all(after['inbox'].get(name) == evidence for name, evidence in original_before['inbox'].items()),
            'existing_inbox_changed')
        require(after['sidecars'] == original_before['sidecars'], 'sidecar_changed')
        require(record_identities == {path.name: identity(path) for path in (root / 'records').iterdir()},
            'original_records_or_intents_changed')
        old_bindings()
        return dict(schema='CAPTION_ACTUAL_READ_ONLY_CPU_V1', observed_unix=time.time(), passed=True,
            source=str(source), source_manifest_sha256=sha(prepared / 'MANIFEST.json'),
            source_python_files=len(manifest['source_pins']), family='gpu.r213_recovery_runtime.RecoveryJournal',
            original_guard_sha256=GUARD_SHA, original_plan_sha256=PLAN_SHA, commit_sha256=COMMIT_SHA,
            checkpoint_sha256=checkpoint['checkpoint_sha256'], optimizer_steps=10236,
            complete_index=8527, head_index=8528, sleep_count=119, next_driver_cycle=120,
            rows=487, sleep_frontier=487, pending=None, state_sha256=state['sha256'],
            history_sha256=digest(state['state']['history']),
            working_state_sha256=digest(state['state']['history']['working_state']),
            rows_sha256=digest(state['state']['rows']), experiment_sha256=digest(state['state']['experiment']),
            raw_scan_seconds=scan_seconds, boundary_and_binary_seconds=integrity_seconds,
            optimizer_payload_seconds=payload_seconds, total_seconds=time.monotonic()-started,
            optimizer_parameter_count=len(parameters), saved_python_cpu_cuda_rng_verified=True,
            model_loaded=False, CUDA_initialized=False, checkpoint_tail_receipt=journal.checkpoint_tail_receipt,
            before=original_before, after=after, registered_inbox_count=len(journal._state['inbox']),
            unregistered_inbox_ids=sorted(set(present) - set(journal._state['inbox'])),
            consumed_wall_metadata_removal_proof=dict(original_plan_sha256=PLAN_SHA,
                authorization_sha256=digest(authorization), exact_state_sha256=state['sha256'],
                hard_end_unix=1789927200, row_prompt_control_deadline_changes=False),
            observer_path_mapping=dict(actual_root=str(root), original_identity_root=str(Path(plan['root']) / 'stream'),
                authority='original_guard.copy_raw', stored_source_paths_rewritten=False),
            all_old_records_intents_inbox_sidecars_preserved=True, matching_old_processes=[],
            writer_lock_acquired=False, journal_writes=0, native_signals=[], native_launches=0,
            original_admission_executed=False, startup_namespace_verified=False, launch_ready=False,
            adapter_tensor_state_recomputed=False, exact_resident_continuity_claimed=False)
    finally:
        journal.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--prepared', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(probe(args.prepared), sort_keys=True, allow_nan=False))
