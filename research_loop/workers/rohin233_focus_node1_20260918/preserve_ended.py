"""Archive only the five authorized, already-ended node1 lives; never signal."""

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import random
import re
import stat
import subprocess
import sys
import time
from types import SimpleNamespace


BASE = Path('/localhome/local-rohing/rohin174_parenting_20260917/node1/R195_FLEET')
DESTINATION = Path('/localhome/local-rohing/rohin233_focus_node1_20260918')
ARMS = {'creative_b1': 7, 'r203_creative_structured_a4': 4,
        'r203_math_comm_b2': 2, 'r203_math_self_derive_c5': 5,
        'r203_repo_evidence_c3': 3}
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def read(path):
    return json.loads(path.read_bytes())


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def reference(path):
    return dict(path=str(path), sha256=sha(path), bytes=path.stat().st_size)


def identity(pid):
    path = Path('/proc') / str(pid)
    try:
        fields = (path / 'stat').read_text().rsplit(')', 1)[1].split()
        return dict(pid=pid, parent_pid=int(fields[1]), state=fields[0],
                    start_ticks=fields[19],
                    command_sha256=hashlib.sha256((path / 'cmdline').read_bytes()).hexdigest())
    except (FileNotFoundError, ProcessLookupError):
        return None


def selected_path(path, name):
    path = Path(path)
    if name not in ARMS or path.parent != BASE:
        return False
    return path.name == name or re.fullmatch(re.escape(name) + r'_r[0-9]+', path.name) is not None


def matching_processes(name):
    roots = [str(path) for path in BASE.iterdir() if selected_path(path, name)]
    matches = []
    for path in Path('/proc').glob('[0-9]*'):
        try:
            command = (path / 'cmdline').read_bytes()
            working_directory = str((path / 'cwd').resolve())
            if any(root.encode() in command or working_directory == root
                   or working_directory.startswith(root + '/') for root in roots):
                current = identity(int(path.name))
                if current:
                    matches.append(current)
        except (PermissionError, FileNotFoundError, ProcessLookupError):
            continue
    return matches


def validate_boundary(terminal, completed, learned, checkpoint):
    for record in (completed, learned, terminal):
        require(record['sha256'] == digest({key: value for key, value in record.items()
                                           if key != 'sha256'}), 'record_hash')
    require(terminal['kind'] == 'TERMINAL'
            and terminal['document']['status'] == 'R184_SCREEN_STOP', 'normal_screen_end')
    require(completed['kind'] == 'SLEEP_COMPLETE' and learned['kind'] == 'R184_LEARN_COMPLETE',
            'final_completed_sleep_and_working_state')
    require(terminal['previous_sha256'] == learned['sha256']
            and learned['previous_sha256'] == completed['sha256'], 'final_chain')
    require(terminal['index'] == learned['index'] + 1 == completed['index'] + 2,
            'consecutive_final_records')
    document = completed['document']
    state = document['resume_state']['state']
    require(document['status'] == 'COMPLETE'
            and state['pending'] is None and state['sleep_frontier'] == len(state['rows']),
            'no_pending_inference_or_sleep')
    require(digest(state) == document['resume_state']['sha256'], 'working_context_hash')
    require(document['checkpoint'] == learned['document']['checkpoint'] == checkpoint,
            'checkpoint_exactly_bound_to_final_sleep')
    require(document['cycle'] == learned['document']['cycle']
            == terminal['document']['completed_sleeps'], 'final_cycle_equal')
    require(state['model_state_sha256'] == digest(checkpoint['checkpoint_sha256']), 'model_state_binding')
    require(document['total_optimizer_steps'] == checkpoint['optimizer_steps'], 'optimizer_steps_binding')
    return dict(cycle=document['cycle'], optimizer_steps=checkpoint['optimizer_steps'],
                resume_state_sha256=document['resume_state']['sha256'],
                working_state_sha256=digest(learned['document']['working_state']),
                sleep_record_index=completed['index'], sleep_record_sha256=completed['sha256'],
                working_record_index=learned['index'], working_record_sha256=learned['sha256'],
                terminal_index=terminal['index'], terminal_sha256=terminal['sha256'])


def inventory(root):
    result = []
    for path in sorted(root.rglob('*')):
        require(not path.is_symlink(), 'snapshot_symlink_not_allowed')
        if path.is_dir():
            continue
        require(stat.S_ISREG(path.stat().st_mode), 'snapshot_regular_files_only')
        result.append(dict(path=str(path.relative_to(root)), sha256=sha(path), bytes=path.stat().st_size))
    return result


def check_checkpoint(checkpoint_path):
    import torch
    checkpoint = read(checkpoint_path)
    actual_adapter = {path.name: sha(path) for path in (checkpoint_path.parent / 'adapter').iterdir()
                      if path.is_file()}
    require(actual_adapter == checkpoint['adapter_files'], 'adapter_files_exact')
    require(digest(actual_adapter) == checkpoint['checkpoint_sha256']['adapter'], 'adapter_set_hash')
    payload_path = checkpoint_path.parent / 'optimizer_rng.pt'
    require(sha(payload_path) == checkpoint['checkpoint_sha256']['optimizer']
            == checkpoint['checkpoint_sha256']['rng'], 'optimizer_rng_hash')
    payload = torch.load(payload_path, map_location='cpu', weights_only=False)
    require(payload['optimizer_steps'] == checkpoint['optimizer_steps'], 'payload_optimizer_steps')
    require(payload['experiment'] == checkpoint['experiment'], 'payload_experiment_binding')
    require(bool(payload['optimizer']['state']) and bool(payload['optimizer']['param_groups']),
            'optimizer_nonempty')
    require(bool(payload['parameter_names']), 'optimizer_parameter_identity')
    torch.Generator(device='cpu').set_state(payload['cpu_rng'])
    random.Random().setstate(payload['python_rng'])
    require(bool(payload['cuda_rng']) and all(value.dtype == torch.uint8 and value.numel() > 0
                                             for value in payload['cuda_rng']), 'cuda_rng_stored')
    require(not torch.cuda.is_initialized(), 'no_gpu_initialized')
    return dict(cpu_payload_loaded=True, optimizer_parameter_count=len(payload['parameter_names']),
                optimizer_state_count=len(payload['optimizer']['state']), cpu_rng_restorable=True,
                python_rng_restorable=True, cuda_rng_tensor_count=len(payload['cuda_rng']),
                cuda_rng_structurally_valid=True, gpu_resume_attempted=False,
                adapter_model_sha256=actual_adapter['adapter_model.safetensors'],
                optimizer_rng_sha256=sha(payload_path), optimizer_steps=payload['optimizer_steps'])


def snapshot_journal_type(journal_type, logical_root):
    inbox = SimpleNamespace(inbox=Path(logical_root) / 'stream/inbox')

    class SnapshotJournal(journal_type):
        def _inbox_event(self, message, path, source_sha256):
            return journal_type._inbox_event(inbox, message, path, source_sha256)

    return SnapshotJournal


def audit_journal(source, raw, expected, logical_root):
    sys.path.insert(0, str(source))
    from gpu.orch_r125_stream_journal import StreamJournal
    journal = snapshot_journal_type(StreamJournal, logical_root)(raw / 'stream')
    try:
        latest = journal.latest_checkpoint()
        validated = journal._validated_state()
        audit = dict(record_count=validated['index'], head_sha256=validated['previous'])
        require(audit['head_sha256'] == expected['terminal_sha256']
                and audit['record_count'] == expected['terminal_index'] + 1, 'full_journal_head')
        require(latest['document']['sha256'] == expected['resume_state_sha256'], 'journal_latest_state')
        return dict(audit, all_transitions_validated=True, latest_state_matches=True,
                    namespace_method='Existing R144 verify_snapshot logical-inbox projection',
                    full_replay='StreamJournal constructor; validated cache checked afterwards')
    finally:
        journal.close()


def preserve(name):
    require(name in ARMS, 'exact_authorized_name')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'cpu_only')
    root = BASE / name
    active = read(root / 'ACTIVE_CONTROL.json')
    control = Path(active['control_root'])
    require(selected_path(control.parent, name) and control.name == 'control', 'same_life_control_only')
    raw = root / 'life'
    guard = read(control / 'GUARD.json')
    plan_path = Path(guard['plan_path'])
    plan = read(plan_path)
    require(active['unchanged_raw_root'] == str(raw) and guard['copy_raw'] == str(raw), 'same_raw_root')
    require(sha(control / 'GUARD.json') == active['guard_sha256']
            and sha(plan_path) == guard['plan_sha256'], 'active_guard_plan_hashes')
    require(plan['physical'] == ARMS[name], 'exact_physical_gpu')
    exit_receipt = read(control / 'EXIT.json')
    launch = read(control / 'LAUNCH.json')
    require(exit_receipt['exit_code'] == 0 and exit_receipt['no_retry'] is True, 'already_normal_exit')
    require(identity(launch['pid']) is None, 'historical_native_pid_absent')
    require(not matching_processes(name), 'no_selected_live_native_or_helper')
    records = sorted(path for path in (raw / 'stream/records').glob('*.json')
                     if re.fullmatch(r'[0-9]{20}\.json', path.name))
    completed, learned, terminal = [read(path) for path in records[-3:]]
    checkpoint_path = raw / 'checkpoints' / f"sleep_{completed['document']['cycle']:06d}" / 'COMMIT.json'
    boundary = validate_boundary(terminal, completed, learned, read(checkpoint_path))
    destination = DESTINATION / name
    destination.mkdir(mode=0o700)
    write(destination / 'IDENTITY.json', dict(node='node1', name=name, physical=ARMS[name],
        root=str(root), raw_root=str(raw), active_control=str(control),
        native_pid=None, native_start_ticks=None, launcher_pid=launch['pid'],
        launcher_start_ticks=launch['parent_start_ticks'],
        native_start_ticks_reason='Native already exited; no live /proc identity exists. LAUNCH identifies the timeout wrapper, not its native child.',
        launch_parent_start_ticks=launch['parent_start_ticks'], launch_command_sha256=launch['command_sha256'],
        launch=reference(control / 'LAUNCH.json'), exit=reference(control / 'EXIT.json'),
        active_control_receipt=reference(root / 'ACTIVE_CONTROL.json'),
        historical_launcher_pid_absent=True, matching_processes=[], observed_unix=time.time()))
    snapshot = destination / 'snapshot'
    snapshot.mkdir(mode=0o700)
    for origin, target in ((raw / 'stream', snapshot / 'stream'),
                           (raw / 'checkpoints', snapshot / 'checkpoints'),
                           (control, snapshot / 'control'),
                           (Path(plan['source_root']), snapshot / 'source')):
        subprocess.run(['cp', '-a', '--reflink=auto', str(origin), str(target)], check=True)
        require(inventory(origin) == inventory(target), 'independent_copy_hashes_equal_' + target.name)
    require(not matching_processes(name), 'no_concurrent_source_owner')
    require(reference(records[-1])['sha256'] == reference(snapshot / 'stream/records' / records[-1].name)['sha256'],
            'terminal_still_exact')
    optimizer = check_checkpoint(snapshot / 'checkpoints' / checkpoint_path.parent.name / 'COMMIT.json')
    manifest = dict(node='node1', root=str(snapshot), files=inventory(snapshot),
                    original_root_retained=str(root), observed_unix=time.time())
    write(destination / 'STATE_MANIFEST.json', manifest)
    write(destination / 'BOUNDARY.json', dict(boundary, checkpoint=reference(checkpoint_path),
          resume_state_record=reference(records[-3]), working_state_record=reference(records[-2]),
          terminal_record=reference(records[-1]), optimizer=optimizer,
          private_namespace_mapping={plan['root']:str(raw)},
          restore_note='Checkpoint absolute paths are the original private namespace. Restore using the bound receiver mapping; never mutate COMMIT.json.'))
    try:
        audit = audit_journal(Path(plan['source_root']), raw, boundary, plan['root'])
    except Exception as error:
        write(destination / 'JOURNAL_AUDIT_FAILED.json', dict(error_type=type(error).__name__,
              reason=str(error)[:500], snapshot_preserved=True))
        raise
    require(not matching_processes(name) and identity(launch['pid']) is None, 'final_absence_verified')
    receipt = dict(node='node1', name=name, physical=ARMS[name], disposition='ALREADY_ENDED_RETIRED_FROM_FLEET',
        existing_exit_code=exit_receipt['exit_code'], exited_unix=exit_receipt['finished_unix'],
        native_pid=None, native_start_ticks=None, launcher_pid=launch['pid'],
        launcher_start_ticks=launch['parent_start_ticks'], raw_root=str(raw), active_control=str(control),
        signals_sent=0, pauses=0, refills=0, files_deleted=0, helper_signals=0,
        original_root_retained=True, all_stream_records_copied=True, all_checkpoints_copied=True,
        archive_root=str(destination), state_manifest=reference(destination / 'STATE_MANIFEST.json'),
        boundary=reference(destination / 'BOUNDARY.json'), identity=reference(destination / 'IDENTITY.json'),
        checkpoint_cycle=boundary['cycle'], optimizer_steps=boundary['optimizer_steps'],
        journal_audit=audit, cpu_resume_components_verified=True, gpu_resume_not_attempted=True,
        completed_unix=time.time())
    write(destination / 'RETIRED.json', receipt)
    print(json.dumps(receipt), flush=True)


def finish_existing(name):
    require(name in ARMS and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'exact_scope_cpu_only')
    destination = DESTINATION / name
    snapshot = destination / 'snapshot'
    recorded = read(destination / 'IDENTITY.json')
    launcher_pid = recorded.get('launcher_pid', recorded.get('native_pid'))
    require(recorded['name'] == name and recorded['root'] == str(BASE / name), 'owned_snapshot_identity')
    require(not (destination / 'RETIRED.json').exists(), 'no_duplicate_finalization')
    require(not matching_processes(name) and identity(launcher_pid) is None, 'still_already_ended')
    require(sha(Path(recorded['active_control_receipt']['path']))
            == recorded['active_control_receipt']['sha256'], 'active_pointer_unchanged')
    manifest = read(destination / 'STATE_MANIFEST.json')
    require(inventory(snapshot) == manifest['files'], 'preserved_snapshot_still_exact')
    control = Path(recorded['active_control'])
    guard = read(control / 'GUARD.json')
    plan = read(Path(guard['plan_path']))
    raw = Path(recorded['raw_root'])
    for origin, target in ((raw / 'stream', snapshot / 'stream'),
                           (raw / 'checkpoints', snapshot / 'checkpoints'),
                           (control, snapshot / 'control'),
                           (Path(plan['source_root']), snapshot / 'source')):
        require(inventory(origin) == inventory(target), 'original_matches_snapshot_' + target.name)
    boundary = read(destination / 'BOUNDARY.json')
    audit = audit_journal(Path(plan['source_root']), snapshot, boundary, plan['root'])
    exit_receipt = read(control / 'EXIT.json')
    require(sha(control / 'EXIT.json') == recorded['exit']['sha256']
            and exit_receipt['exit_code'] == 0, 'same_normal_exit')
    require(not matching_processes(name) and identity(launcher_pid) is None, 'final_absence_verified')
    receipt = dict(node='node1', name=name, physical=ARMS[name], disposition='ALREADY_ENDED_RETIRED_FROM_FLEET',
        existing_exit_code=exit_receipt['exit_code'], exited_unix=exit_receipt['finished_unix'],
        native_pid=None, native_start_ticks=None, launcher_pid=launcher_pid,
        launcher_start_ticks=recorded['launch_parent_start_ticks'],
        raw_root=str(raw), active_control=str(control),
        signals_sent=0, pauses=0, refills=0, files_deleted=0, helper_signals=0,
        original_root_retained=True, all_stream_records_copied=True, all_checkpoints_copied=True,
        archive_root=str(destination), state_manifest=reference(destination / 'STATE_MANIFEST.json'),
        boundary=reference(destination / 'BOUNDARY.json'), identity=reference(destination / 'IDENTITY.json'),
        checkpoint_cycle=boundary['cycle'], optimizer_steps=boundary['optimizer_steps'],
        journal_audit=audit, cpu_resume_components_verified=True, gpu_resume_not_attempted=True,
        initial_audit_failure_preserved=reference(destination / 'JOURNAL_AUDIT_FAILED.json'),
        initial_failure_reason='Physical path used instead of saved private-namespace inbox; no evidence corruption.',
        finalizer_source_sha256=sha(Path(__file__)), completed_unix=time.time())
    write(destination / 'RETIRED.json', receipt)
    print(json.dumps(receipt), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('name', choices=list(ARMS))
    parser.add_argument('--finish-existing', action='store_true')
    options = parser.parse_args()
    DESTINATION.mkdir(mode=0o700, exist_ok=True)
    descriptor = os.open(DESTINATION / (options.name + '.lock'), os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if options.finish_existing:
            finish_existing(options.name)
        else:
            preserve(options.name)
    finally:
        os.close(descriptor)


if __name__ == '__main__':
    main()
