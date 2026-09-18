"""Produce canonical metadata-only retirement receipts after archival audits."""

from datetime import datetime, timezone
import json
from pathlib import Path
import time

from preserve_ended import ARMS, BASE, DESTINATION, identity, matching_processes, read, reference, require, sha, write


def main():
    rows = []
    for name, physical in ARMS.items():
        destination = DESTINATION / name
        original = read(destination / 'RETIRED.json')
        boundary = read(destination / 'BOUNDARY.json')
        manifest = read(destination / 'STATE_MANIFEST.json')
        active = read(BASE / name / 'ACTIVE_CONTROL.json')
        control = Path(active['control_root'])
        launch = read(control / 'LAUNCH.json')
        exited = read(control / 'EXIT.json')
        require(not matching_processes(name) and identity(launch['pid']) is None, 'selected_life_still_ended')
        require(exited['exit_code'] == 0 and exited['no_retry'], 'normal_nonretry_exit')
        require(original['journal_audit']['all_transitions_validated'], 'completed_full_journal_audit')
        require(sha(destination / 'STATE_MANIFEST.json') == original['state_manifest']['sha256'], 'archive_manifest_exact')
        require(sha(destination / 'BOUNDARY.json') == original['boundary']['sha256'], 'boundary_exact')
        saved_path = destination / 'snapshot/checkpoints' / f"sleep_{boundary['cycle']:06d}" / 'COMMIT.json'
        checkpoint = read(saved_path)
        artifacts = {str(path.relative_to(saved_path.parent)): reference(path)
                     for path in saved_path.parent.rglob('*') if path.is_file()}
        require(artifacts['optimizer_rng.pt']['sha256'] == checkpoint['checkpoint_sha256']['optimizer']
                == checkpoint['checkpoint_sha256']['rng'], 'optimizer_rng_binding')
        require(artifacts['adapter/adapter_model.safetensors']['sha256']
                == checkpoint['adapter_files']['adapter_model.safetensors'], 'adapter_binding')
        existing = destination / 'VERIFIED_RETIREMENT.json'
        if existing.exists():
            previous = read(existing)
            require(previous['name'] == name and previous['saved_artifacts'] == artifacts
                    and previous['active_control'] == str(control)
                    and previous['full_archive_manifest'] == reference(destination / 'STATE_MANIFEST.json'),
                    'existing_canonical_receipt_still_exact')
            rows.append(previous)
            continue
        result = dict(node='node1', name=name, physical_gpu=physical,
            disposition='ALREADY_ENDED_RETIRED_FROM_FLEET', user_authorization='R233 explicit node1 stale-life list',
            raw_root=original['raw_root'], active_control=str(control),
            launcher_pid=launch['pid'], launcher_start_ticks=launch['parent_start_ticks'],
            launcher_command_sha256=launch['command_sha256'], launcher_kind='timeout wrapper',
            native_pid=None, native_start_ticks=None,
            native_identity_limit='No surviving native /proc entry or saved final-native ticks; no signals attempted.',
            pid_field_correction=('Original archival receipt mislabeled LAUNCH wrapper pid as native; use this canonical receipt.'
                                  if original.get('native_pid') is not None else 'Correct launcher/native distinction in source receipt.'),
            exited_utc=datetime.fromtimestamp(exited['finished_unix'], timezone.utc).isoformat(),
            exit_code=exited['exit_code'], exit_receipt=reference(control / 'EXIT.json'),
            launch_receipt=reference(control / 'LAUNCH.json'), active_receipt=reference(BASE / name / 'ACTIVE_CONTROL.json'),
            checkpoint_cycle=boundary['cycle'], optimizer_steps=boundary['optimizer_steps'],
            saved_artifacts=artifacts, checkpoint_bindings=checkpoint['checkpoint_sha256'],
            original_checkpoint=boundary['checkpoint'], resume_state_record=boundary['resume_state_record'],
            working_state_record=boundary['working_state_record'], terminal_record=boundary['terminal_record'],
            resume_state_sha256=boundary['resume_state_sha256'], working_state_sha256=boundary['working_state_sha256'],
            optimizer_verification=boundary['optimizer'], private_namespace_mapping=boundary['private_namespace_mapping'],
            full_archive_manifest=reference(destination / 'STATE_MANIFEST.json'),
            archived_file_count=len(manifest['files']), archived_bytes=sum(entry['bytes'] for entry in manifest['files']),
            full_journal_audit=original['journal_audit'], original_archival_receipt=reference(destination / 'RETIRED.json'),
            original_root_retained=True, complete_stream_and_checkpoints_copied=True,
            no_resident_partial_state_lost=True, gpu_resume_not_executed=True,
            other_roots_modified=False, signals_sent=0, helpers_signalled=0, files_deleted=0, refills=0,
            verified_unix=time.time())
        write(destination / 'VERIFIED_RETIREMENT.json', result)
        rows.append(result)
    write(DESTINATION / 'VERIFIED_ALL_FIVE.json', dict(node='node1', lives=rows,
          signals_sent=0, files_deleted=0, refills=0, finished_unix=time.time()))
    print(json.dumps(dict(node='node1', completed_names=list(ARMS), receipt=reference(DESTINATION / 'VERIFIED_ALL_FIVE.json'))))


if __name__ == '__main__':
    main()
