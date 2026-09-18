"""CPU-only preflight contracts; no SSH, provider, CUDA, process launch or upload."""

import hashlib
import json
from pathlib import Path

from organism_v6 import orch_math_feedback_uptake as policy


SEED_CAMPAIGN = 'campaign_03_r102_micro5'
SEED_RULE = 'natural_terminal_cycle8_saved_adapter_and_optimizer_no_score_selection'
QUEUE_DIRECTORY = 'feedback_uptake_queue_v1'
REQUIRED_BINDINGS = (
    'published_main_allocation', 'natural_terminal_seed_and_optimizer', 'all_source_exclusion_registry',
    'frozen_cohort_and_retention', 'complete_seed_replay_and_old_mix_manifest',
    'new_native_driver_and_isolated_broker_cpu_tests', 'original_lifetime_and_aggregate_counters',
    'exact_owner_release', 'fresh_privileged_uuid_proc_admission',
)
REUSED_SEAMS = (
    'gpu/orch_math_pipeline_l2_r104_native.py',
    'gpu/orch_math_pipeline_l2_scan.py',
    'gpu/orch_math_pipeline_l2_run.py',
    'gpu/orch_math_pipeline_l2_parent_strong.py',
    'gpu/orch_math_pipeline_l2_parent_node.py',
    'gpu/orch_guided_native.py',
    'organism_v6/orch_guided_bridge.py',
    'organism_v6/orch_math_pipeline_l2.py',
)


def read_bound(reference):
    path = Path(reference['path'])
    policy.require(path.is_absolute() and path.resolve() == path, 'absolute_nonalias_reference')
    raw = path.read_bytes()
    policy.require(hashlib.sha256(raw).hexdigest() == reference['sha256'], 'artifact_hash_mismatch')
    return json.loads(raw)


def validate_allocation(document, ready_sha256, now):
    policy.require(document['schema'] == 'ORCH_MATH_FEEDBACK_UPTAKE_ALLOCATION_V1', 'allocation_schema')
    policy.require(document['ready_sha256'] == ready_sha256, 'allocation_binds_new_ready')
    policy.require(document['publication']['commit'] and document['publication']['path'], 'main_publication_required')
    policy.require(document['owner'] == 'MATH_FEEDBACK_UPTAKE' and len(document['devices']) == 1, 'one_treatment_slot')
    device = document['devices'][0]
    policy.require((device['physical'], device['uuid']) in policy.source.DEVICES.values(), 'known_uuid_index_binding')
    policy.require(document['host_sha256'] == policy.source.HOST_SHA, 'host_hash_binding')
    policy.require(document['additional_budget'] == policy.budget(), 'prospective_budget_not_implicit')
    policy.require(document['seed_campaign'] == SEED_CAMPAIGN and document['seed_rule'] == SEED_RULE, 'prospective_seed_not_score_selected')
    policy.require(document['aggregate_native_cap'] == 2140 and document['aggregate_parent_cap'] == 40, 'additive_accounting_2064_36_plus_76_4')
    policy.require(document['aggregate_gpu_hours_cap'] == 24, 'original_ceiling_preserved')
    policy.require(now < document['native_deadline_unix'] <= 1789472355.2727501, 'original_native_deadline')
    policy.require(document['native_deadline_unix'] < document['hard_deadline_unix'] <= 1789472535.2727501, 'original_hard_deadline')
    return device


def validate_seed(seed, complete, after, terminal):
    policy.require(seed['campaign_name'] == SEED_CAMPAIGN and seed['selection_rule'] == SEED_RULE, 'fixed_seed_rule')
    policy.require(terminal['status'] == 'COMPLETE', 'natural_terminal_required_no_failure_fallback')
    policy.require(complete['status'] == 'COMPLETE' and complete['cycle'] == 8, 'genuine_terminal_saved_l2')
    policy.require(complete['phase'] == 'experience' and complete['arm'] == 'GUIDED_SLEEP', 'correct_seed_phase')
    policy.require(complete['updates'] > 0 and len(complete['process']) == 3, 'actual_native_save')
    policy.require(seed['output_adapter'] == complete['output_adapter'] == after['output_adapter'], 'seed_adapter_join')
    policy.require(seed['output_adapter']['base_sha256'] == policy.source.BASE_SHA, 'base_invariant')
    policy.require(seed['optimizer_sha256'] == complete['optimizer_sha256'], 'optimizer_join')
    policy.require(after['actual_mounted_identity_verified'] is True and after['frozen_base_verified'] is True, 'native_after_required')
    policy.require(after['process'] == complete['process'], 'seed_after_process_join')
    policy.require(seed['reset_optimizer'] is False and seed['l2_into_l1'] is False, 'no_reset_no_l1_feed')


def validate_release(release, scan, device, now):
    policy.require(release['owner'] and release['next_owner'] == 'MATH_FEEDBACK_UPTAKE', 'actual_owner_release')
    policy.require(release['natural_completion'] is True and release['uuid'] == device['uuid'], 'natural_uuid_release')
    policy.require(release['physical'] == device['physical'], 'release_index')
    policy.require(release['terminal_receipt'] and release['after_receipt'], 'bound_terminal_after_required')
    policy.require(release['previous_processes'] and all(set(process) >= {'boot_id', 'pid', 'uid', 'start_ticks', 'command_sha256'}
        for process in release['previous_processes']), 'full_previous_process_identity')
    policy.require(release['released_unix'] <= scan['observed_unix'] <= now, 'release_before_admission')
    policy.require(now - scan['observed_unix'] <= 30, 'fresh_admission_not_memory_census')
    report = scan['report']
    policy.require(report['clear'] is True and report['scanner_euid'] == 0 and not report['blocking_reasons'], 'strict_full_proc_admission')
    policy.require(report['gpu']['uuid'] == device['uuid'] and report['gpu']['index'] == device['physical'], 'scan_device_binding')
    policy.require(report['host_sha256'] == policy.source.HOST_SHA and type(report['device_minor']) is int, 'pinned_host_minor')


def readiness():
    return dict(schema=policy.SCHEMA, status='CPU_PREPARATION_ONLY_NOT_NATIVE_LAUNCH_READY',
        launch_authorized=False, native_calls=0, parent_calls=0, gpu_reservation=False,
        prospective_budget=policy.budget(), missing_bindings=list(REQUIRED_BINDINGS),
        seed_campaign=SEED_CAMPAIGN, seed_rule=SEED_RULE,
        queue_directory=QUEUE_DIRECTORY, reused_seams=list(REUSED_SEAMS),
        native_driver_connected=False, live_parent_broker_modified=False)


if __name__ == '__main__':
    print(json.dumps(readiness(), indent=2, sort_keys=True))
