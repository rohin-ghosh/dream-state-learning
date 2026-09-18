from datetime import datetime, timezone
from pathlib import Path
import re
import time

from gpu import orch_r167_object_probe_queue as queue


protocol = queue.protocol
WORKER = Path(__file__).resolve().parent


def build():
    base_path = WORKER / 'LIVE_REPLAY_METADATA.json'
    clarification_path = WORKER / 'VARIANT_CLARIFICATION.json'
    base, clarification = protocol.read(base_path), protocol.read(clarification_path)
    resource_path = WORKER / 'FLEET_RESOURCE_OBSERVATION1.json'
    resource = protocol.read(resource_path)
    rows = []
    for node, entry in base['nodes'].items():
        fixes = {str(row['pid']): row for row in clarification['nodes'].get(node, {}).get('rows', [])}
        for original in entry['rows']:
            correction = fixes.get(str(original['pid']))
            merged = dict(original, **(correction or {}))
            source_root = original['root']
            if 'community_C' in source_root:
                life_id = re.search(r'community_(C[1-5])_', source_root)[1]
            elif '/parented_learning' in source_root:
                life_id = 'R158_parented_learning'
            elif 'repo_reader' in source_root:
                life_id = 'repo_reader'
            elif 'r127_pilot' in source_root:
                life_id = 'pilot'
            elif 'r125_continual' in source_root:
                life_id = 'continual_run1'
            else:
                life_id = re.search(r'orch_r(?:133|136)_(?:node3_|a100_)?(.+)_20260916_attempt1', source_root)[1]
            protocol.require(merged['status'].startswith('LIVE_NATIVE') and merged['start_ticks']
                             and merged['plan_ref'], 'merged_inventory_identity_required')
            observed = clarification['nodes'][node]['observed_unix'] if correction else entry['observed_unix']
            rows.append(dict(life_id=life_id, node=node, storage_root=source_root,
                process_plan_root=merged['root'], birth_plan={name: merged['plan_ref'][name] for name in ('path', 'sha256')},
                inventory_identity=dict(pid=merged['pid'], start_ticks=merged['start_ticks'], boot_id=None),
                inventory_observed_unix=observed,
                inventory_evidence=[protocol.ref(base_path)] + ([protocol.ref(clarification_path)] if correction else []),
                hold='RECOVERY_COMMIT_REQUIRED' if life_id == 'C5' else 'FRESH_IDENTITY_CUSTODY_REQUIRED'))
    protocol.require(len(rows) == 21, 'preserve_full_Linnaeus21_coverage')
    rows.sort(key=lambda row: row['life_id'])
    destination = WORKER / 'fleet_generation1'
    destination.mkdir(mode=0o700)
    timestamp = lambda value: datetime.fromisoformat(value).replace(tzinfo=timezone.utc).timestamp()
    exclusions = [dict(life_id=name, disposition=disposition, registered=False, model_calls=0)
        for name, disposition in [
            ('support_none', 'MISSING_FROM_VERIFIED_NATIVE_CENSUS_NOT_DEAD'),
            ('creative_none', 'MISSING_FROM_VERIFIED_NATIVE_CENSUS_NOT_DEAD'),
            ('frozen_control', 'EXACT_CURRENT_IDENTITY_AND_ALIAS_UNVERIFIED'),
            ('pending_frozen', 'EXACT_CURRENT_IDENTITY_AND_ALIAS_UNVERIFIED'),
            ('R165_frozen', 'FROZEN_OUTSIDE_LEARNING_WINDOW_REQUIRES_SEPARATE_CONTROL_SCHEDULE'),
            ('R158_unparented_learning', 'OUTSIDE_CENSUS_VERIFY_CURRENT_ROOT_AND_NATIVE_BEFORE_ADDING'),
            ('R136_raw_unparented', 'RETROSPECTIVE_ROOT_KNOWN_CURRENT_NATIVE_NOT_RECERTIFIED'),
            ('kernel_threads', 'NOT_IN_CENSUS_DO_NOT_INFER_DISTINCT_LEARNING_LIFE'),
            ('other_no_sleep_lives', 'NONE_IDENTITY_VERIFIED_NO_SLEEP_BASELINE_ONLY_NEEDS_EXPLICIT_REGISTRATION')]]
    plan = dict(schema=queue.BATCH_SCHEMA, queue_root=str(destination / 'metadata_queue'), frozen_unix=time.time(),
        lives=rows, unverified_coverage=exclusions, probes=list(queue.PROBES), conditions=list(queue.CONDITIONS),
        future_sleeps=3, model_call_cap=504, generated_token_cap=258048, physical_slots=[0, 1],
        not_before_unix=timestamp('2026-09-17T09:30:00'), hard_end_unix=timestamp('2026-09-17T15:30:00'),
        lease_deadline_unix=resource['hard_deadline_unix'], adapter_copy_cap=16 * 1024**3,
        metadata_read_cap=8 * 1024**3, resource_evidence=[protocol.ref(resource_path)],
        visibility='PRIVATE_EVALUATOR_ONLY_METADATA_TO_PARENTS')
    reference = protocol.write(destination / 'BATCH_PLAN.json', plan)
    result = queue.batch_initialize(reference['path'])
    protocol.write(destination / 'STATUS.json', result)
    proposal = dict(status='PROSPECTIVE_PREPARATION_NOT_SOURCE_OR_GPU_GO', plan=reference,
        helper=protocol.ref(Path(queue.__file__)), tests=protocol.ref(WORKER.parents[2] / 'tests/test_orch_r167_object_probe_queue.py'),
        CPU=protocol.ref(WORKER / 'PROSPECTIVE_QUEUE_CPU1.txt'), resource=protocol.ref(resource_path),
        calls=504, max_generated_tokens=258048, checkpoints=84, condition_processes=168,
        completed_model_calls=0, source_copies=0, observed_jobs=resource['throughput']['completed_condition_jobs'],
        estimate_seconds_at_observed_mean=84 * resource['throughput']['mean_seconds'],
        estimate_seconds_at_observed_max=84 * resource['throughput']['max_seconds'],
        conservative_service_seconds=84 * 180, remaining_window_for_arrival_copy_or_variance=21600 - 84 * 180,
        adapter_sizes='FLEET_UNVERIFIED_DO_NOT_INFER_FROM_SINGLE_RANK',
        admission_requirements=['current_exact_native_and_storage_root_birth_custody',
            'source_owner_read_copy_authority_and_next_sleep_frontier_before_outputs',
            'C5_exact_committed_recovery_and_release_witness', 'all_initial_baselines_or_explicit_missing_cells',
            'per_life_TRAIN_only_fingerprint_freeze_and_semantic_cue_audit',
            'new_receiving_runtime_exact_pins_CPU_provenance_and_execution_GOs',
            'current_R167_native_timeout_wrapper_release_then_full_unchanged_GPU_scan',
            'full_900_seconds_plus_teardown_before_absolute_wall_no_retry'],
        invariants=['no_existing_GO_reuse', 'no_source_or_model_mutation', 'no_child_blocking',
            'no_score_selection', 'missed_cells_remain_missing', 'additions_require_new_bounded_generation'])
    receipt = protocol.write(destination / 'ADMISSION_PROPOSAL.json', proposal)
    print(protocol.json.dumps(dict(status=proposal['status'], receipt=receipt, plan=reference,
        lives=21, calls=504, model_calls=0), sort_keys=True))


if __name__ == '__main__':
    build()
