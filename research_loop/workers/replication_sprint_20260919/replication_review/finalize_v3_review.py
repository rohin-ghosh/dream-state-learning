"""Finalize the bounded review from local primary exports, with no node calls."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import review_v3_receiving as custody_review


HERE = Path(__file__).resolve().parent
SPRINT = HERE.parent
OPERATIONS = SPRINT / 'operations'


def canonical_sha(value):
    raw = json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def utc(timestamp):
    return datetime.fromtimestamp(timestamp, timezone.utc).isoformat()


def main():
    result = custody_review.review()
    paths = {
        'main_tests': OPERATIONS / 'SAMPLING_V3_FINAL_MAIN_TESTS.txt',
        'launch': OPERATIONS / 'SAMPLING_V3_LAUNCH.txt',
        'progress': OPERATIONS / 'SAMPLING_V3_PROGRESS.json',
        'reviewer_tests': HERE / 'CPU_REVIEW_RECEIPT.json',
    }
    before = {name: custody_review.sha(path) for name, path in paths.items()}
    freeze = custody_review.read(SPRINT / 'replication/SAMPLING_SOURCE_FREEZE_V3.json')
    require = custody_review.require
    require(before['main_tests'] == freeze['main_test_log_sha256'], 'bound_main_cpu_test_log')
    main_tests = paths['main_tests'].read_text()
    require('Ran 72 tests' in main_tests and main_tests.rstrip().endswith('OK'), 'main_72_tests_pass')
    reviewer_tests = custody_review.read(paths['reviewer_tests'])
    require(reviewer_tests['tests_passed'] is True and reviewer_tests['tests_run'] == 83
        and reviewer_tests['candidate_stable_during_checks'] is True
        and reviewer_tests['executable_seal']['sha256'] == custody_review.FREEZE_SHA256
        and reviewer_tests['executable_seal']['mismatches'] == [], 'bound_independent_cpu_tests')
    for relative, expected in reviewer_tests['pins_after'].items():
        source = HERE.parents[3] / relative
        require(custody_review.sha(source) == expected, 'reviewed_source_still_matches:' + relative)
    launch = paths['launch'].read_text().splitlines()
    controller_pid = launch[0].removeprefix('controller_pid=')
    require(controller_pid == '1989482' and launch[1] == '2026-09-19T14:04:39Z'
        and launch[2].split()[0] == controller_pid, 'bound_main_controller_launch')
    progress = custody_review.read(paths['progress'])
    registry = custody_review.read(SPRINT / 'replication/SAMPLING_REGISTRY_V3.json')
    originals = custody_review.read(SPRINT / 'replication/ORIGINALS_RECEIPT.json')
    require(progress['root'] == registry['root'] and progress['controller_pid'] == controller_pid,
        'same_launched_progress_root')
    expected_jobs = {job['arm']: job for job in registry['jobs']}
    require(len(progress['rows']) == 3 and {row['arm'] for row in progress['rows']} == set(expected_jobs),
        'all_source_progress_denominators')
    loaded = []
    for row in progress['rows']:
        job = expected_jobs[row['arm']]
        require(row['job_id'] == job['job_id'], 'progress_matches_declared_source')
        for role in ('judge', 'player'):
            snapshot = row['snapshots'].get(role + '_loaded')
            if snapshot is None:
                continue
            value = snapshot['value']
            require(canonical_sha(value) == snapshot['sha256'], 'original_writer_loaded_receipt_hash')
            require(value['diagnostic_epoch_sha256'] == registry['diagnostic_epoch_sha256']
                and value['judge_epoch_sha256'] == registry['diagnostic_epoch']['judge_epoch_sha256'],
                'unchanged_diagnostic_and_judge_epochs')
            require(value['source_parent_text_loaded'] is False
                and value['sampling_replication_not_training_replication'] is True, 'loaded_scope_unchanged')
            view = Path(job['root']) / 'view'
            if role == 'judge':
                require(snapshot['path'] == str(view / 'JUDGE_LOADED.json'), 'judge_loaded_path')
                require(canonical_sha(value['binding']) == value['judge_epoch_sha256']
                    and value['reference_captions_visible_to_player'] is False, 'immutable_reference_judge_binding')
            else:
                require(snapshot['path'] == str(view / 'players' / value['condition'] / 'LOADED.json'),
                    'player_loaded_path')
                require(value['identity'] == originals['rows'][row['arm']]['identity'],
                    'unchanged_loaded_weights_decoder_tokenizer_libraries')
                require(value['actual_visible_device'] == registry['role_devices']['player']['uuid']
                    and value['snapshot_context_used'] is False and value['parent_tokens'] == 0,
                    'loaded_player_frozen_parent_free')
            loaded.append(dict(arm=row['arm'], role=role, pid=value['pid'],
                loaded_utc=utc(value['unix']), path=snapshot['path'], sha256=snapshot['sha256']))
    require({row['role'] for row in loaded if row['arm'] == 'base'} == {'judge', 'player'},
        'base_both_models_actually_loaded')
    require(before == {name: custody_review.sha(path) for name, path in paths.items()},
        'launch_test_progress_artifacts_stable')
    result.update(status='INDEPENDENT_V3_REVIEW_COMPLETE_PASS', independent_review_complete=True,
        finalization_utc=datetime.now(timezone.utc).isoformat(),
        main_cpu_tests=72, independent_cpu_tests=83, extra_artifact_sha256=before,
        controller_pid=int(controller_pid), launch_receipt_utc=launch[1], loaded_receipts=loaded,
        progress_observed_utc=utc(progress['observed_unix']),
        block_complete_at_progress_cut=progress['block_complete'],
        block_failed_at_progress_cut=progress['block_failed'],
        launch_and_loaded_verified=True, scientific_result_or_full_block_completion_claimed=False,
        reviewer_dispatches=0, reviewer_receiving_commands=0, reviewer_external_scope_mutations=0)
    destination = HERE / 'V3_FINAL_REVIEW.json'
    with destination.open('x') as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({key: result[key] for key in ('status', 'finalization_utc', 'main_cpu_tests',
        'independent_cpu_tests', 'controller_pid', 'launch_receipt_utc', 'progress_observed_utc',
        'loaded_receipts', 'block_complete_at_progress_cut', 'block_failed_at_progress_cut')}, indent=2))


if __name__ == '__main__':
    main()
