"""Construct local, non-dispatchable replication configs from captured receipts."""

import argparse
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import time


HERE = Path(__file__).resolve().parent
ADOPTED_SOURCE = 'bcdd5adbcd03bc52e0ae20ca400cd6b328bc9d89aeb19a3f1d9fbae20b3e5c7b'
ADOPTED_EPOCH = '216f34224e27a2ced6671026c482041c3e6024aecbabd105341a365d2935268a'
ORIGINAL_SOURCE = 'a924b1079ab527719e676d095eea812e75e9e8f18d3b589492d2d91fc6d84db7'
ORIGINAL_SEEDS = (23201, 23202)
C2_PREPARATION_BOUND = 1790726400
BLOCKS = {
    'c2': ('base', 'c2sleep51', 'c2sleep117'),
    'pair24': ('adopted_learner24', 'adopted_sibling24'),
}
CONTRACT = 'research_loop/workers/rohin232_age_probe_20260918/contract.py'
INVARIANT_FILES = ('GAME_MANIFEST.json', 'SELECTION.json', 'assets/RULE.json',
    'assets/pixel_config.json', 'judge/REFERENCE_PANELS.private.json',
    'PRIMARY_PANELS.private.json', 'JUDGE_EPOCH.json')
BLOCKERS = (
    'Adopted runner and epoch.require_config hardcode 23201/23202; a separately '
    'sealed seed-parameterized adapter must bind this diagnostic epoch in both roles.',
    'V4 queue supports only pair journals, the original judge, and never-retried source keys; '
    'new diagnostic jobs need Main-owned admission in the SAME shared claims namespace.',
    'Receiving source/adapter/exposure verification, role-isolated private-panel custody, '
    'fresh lane/host/lease proof, and a new unconsumed intent have not been established.',
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(value):
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
    return hashlib.sha256(raw.encode()).hexdigest()


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def validate_source(row):
    require('error' not in row, 'completed_source_required')
    config = row['config']
    require(row['files']['SOURCE_MANIFEST.json']['sha256'] == ADOPTED_SOURCE
        and config['source_manifest_sha256'] == ADOPTED_SOURCE, 'original_adopted_source_closure')
    require(row['judge_epoch_sha256'] == ADOPTED_EPOCH
        and digest(row['judge_epoch']) == ADOPTED_EPOCH, 'original_adopted_judge_epoch')
    require(tuple(config['seeds']) == ORIGINAL_SEEDS and config['scenes'] == 3
        and config['token_budget'] == 6144, 'original_scenes_seeds_budget')
    require(config['parent_tokens'] == 0 and config['training_updates'] == 0
        and config['source_context_loaded'] is False, 'parent_free_frozen_evaluation')
    require((config['judge_rank'], config['judge_step']) == (8, 15625)
        and config['adapter_sha256'] == row['judge_epoch']['adapter_sha256']
        and config['primary_config_sha256'] == row['judge_epoch']['primary_config_sha256'],
        'same_adopted_judge_config_and_adapter')
    require(config['player_physical'] == 2 and config['judge_physical'] == 7,
        'original_physical_lane')
    require(config['root'] == row['root'], 'original_config_root')
    require(row['files']['FRESHNESS_VERIFIED.json']['sha256'] == config['freshness_sha256'],
        'original_source_exposure_binding')
    require(row['actual_generated_tokens'] == 6144
        and len(row['cell_budgets']) == 6, 'completed_equal_budget_source')
    cells = row['cell_budgets']
    scenes = {cell['contest_id'] for cell in cells}
    require(len(scenes) == 3 and {(cell['contest_id'], cell['seed']) for cell in cells}
        == {(scene, seed) for scene in scenes for seed in ORIGINAL_SEEDS}, 'all_six_original_cells')
    require(all(cell['generated_tokens'] == 1024
        and cell['status'] == 'COMPLETE_FIXED_ACTUAL_TOKEN_BUDGET' for cell in cells), 'complete_cells_only')
    require(row['identity']['all_parameters_frozen'] is True
        and row['unchanged_identity']['all_parameters_frozen'] is True, 'frozen_probe_parameters')
    for field in ('adapter_state_sha256', 'base_sha256'):
        require(row['unchanged_identity'].get(field) == row['identity'].get(field), 'unchanged_probe_identity')
    if config['plain_base']:
        require(row['source_age'] is None and row['identity']['adapter_state_sha256'] is None,
            'plain_base_not_an_adapter_age')
    else:
        source = row['source_age']
        require(source['adapter_state_sha256'] == row['identity']['adapter_state_sha256']
            and source['absolute_sleep'] == config['identity']['absolute_sleep']
            and source['sleep_complete_sha256'] == config['identity']['sleep_complete_sha256'],
            'same_captured_checkpoint')


def align_original_pair(receipt):
    learner, sibling = (receipt['rows'][name] for name in ('original_learner24', 'original_sibling24'))
    for name in ('SOURCE_MANIFEST.json', 'GAME_MANIFEST.json', 'SELECTION.json',
            'assets/RULE.json', 'assets/pixel_config.json', 'assets/adapter/adapter_model.safetensors',
            'judge/REFERENCE_PANELS.private.json'):
        require(learner['files'][name]['sha256'] == sibling['files'][name]['sha256'],
            'original_pair_same_protocol:' + name)
    require(learner['files']['SOURCE_MANIFEST.json']['sha256'] == ORIGINAL_SOURCE,
        'v4_original_scientific_closure_not_adopted_judge')
    for row in (learner, sibling):
        require(row['actual_generated_tokens'] == 6144 and row['source_age']['absolute_sleep'] == 24,
            'age24_complete_budget')
    require(learner['source_age']['optimizer_steps'] == 1152
        and sibling['source_age']['optimizer_steps'] == 0, 'original_pair_training_contrast')
    return dict(schema='ALIGNED_ORIGINAL_JUDGE_AGE24_V1',
        status='EXISTING_COMPLETED_RESULTS_NOT_A_NEW_REPLICATION',
        learner={name: learner[name] for name in ('root', 'per_seed', 'source_age', 'files')},
        sibling={name: sibling[name] for name in ('root', 'per_seed', 'source_age', 'files')},
        interpretation='Same recorded source ages, scenes, seeds and original judge; not an independently '
        'trained pair. Do not compare these counts with the adopted-judge block.')


def build(receipt, seeds, block, now):
    require(block in BLOCKS, 'declared_block')
    require(len(seeds) == 2 and all(type(seed) is int and 0 <= seed < 2**32 for seed in seeds)
        and len(set(seeds)) == 2 and not set(seeds) & set(ORIGINAL_SEEDS), 'two_new_sampling_seeds')
    policy = receipt['queue']['policy']
    hard_end = min(policy['lease_end_unix'], C2_PREPARATION_BOUND) if block == 'c2' else policy['lease_end_unix']
    require(policy['max_runtime_seconds'] == 2400 and policy['max_concurrent_jobs'] == 1,
        'unchanged_bounded_serial_lane')
    require(set(policy['role_devices']) == {'player', 'judge'}
        and policy['role_devices']['player']['physical'] == 2
        and policy['role_devices']['judge']['physical'] == 7
        and set(policy['protected_physical']) == {0, 1, 3, 4, 5, 6}, 'original_protected_lane')
    require(math.isfinite(now) and now + 2400 + policy['teardown_margin_seconds']
        < hard_end, 'existing_host_lease_and_source_bound_must_cover_one_full_job')
    rows = [receipt['rows'][name] for name in BLOCKS[block]]
    for row in rows:
        validate_source(row)
        require(row['identity']['base_sha256'] == rows[0]['identity']['base_sha256']
            and row['identity']['decoder'] == rows[0]['identity']['decoder'], 'same_base_and_decoder')
        require(row['source_closure'] == rows[0]['source_closure'], 'same_execution_source_across_arms')
        for name in INVARIANT_FILES:
            require(row['files'][name]['sha256'] == rows[0]['files'][name]['sha256'], 'same_protocol:' + name)
    sampling_epoch = dict(schema='SAMPLING_REPLICATION_DIAGNOSTIC_EPOCH_V1',
        block=block, arm_order=list(BLOCKS[block]), sampling_seeds=list(seeds),
        original_seeds=list(ORIGINAL_SEEDS), judge_epoch_sha256=ADOPTED_EPOCH,
        tokens_per_cell=1024, total_tokens_per_source=6144, parent_tokens=0, training_updates=0,
        source_manifest_sha256=ADOPTED_SOURCE,
        protocol_files={name: rows[0]['files'][name]['sha256'] for name in INVARIANT_FILES},
        decoder=deepcopy(rows[0]['identity']['decoder']),
        source_checkpoints={name: dict(base_sha256=row['identity']['base_sha256'],
            adapter_state_sha256=row['identity']['adapter_state_sha256'],
            source_age=row['source_age'], original_config_sha256=row['files']['CONFIG.json']['sha256'])
            for name, row in zip(BLOCKS[block], rows, strict=True)},
        claim='Sampling variability of preserved checkpoints; not independent training lineages '
            'or fresh-scene transfer. Seeds selected before new outcomes; no score-based source selection.')
    sampling_sha = digest(sampling_epoch)
    configs = {}
    for name, row in zip(BLOCKS[block], rows, strict=True):
        proposed = deepcopy(row['config'])
        proposed.pop('deadline_unix')
        proposed.pop('root')
        proposed['seeds'] = list(seeds)
        proposed['diagnostic_epoch_sha256'] = sampling_sha
        proposed['status'] = 'CPU_CONFIG_TEMPLATE_NOT_ADMITTED_NOT_DISPATCHABLE'
        proposed['proposed_condition'] = 'R233_REPLICATION_' + block + '_' + name
        proposed['original_config_ref'] = deepcopy(row['files']['CONFIG.json'])
        proposed['original_root'] = row['root']
        proposed['source_checkpoint'] = deepcopy(row['source_age'])
        proposed['runtime_deadline_rule'] = dict(max_runtime_seconds=policy['max_runtime_seconds'],
            hard_end_unix=hard_end, teardown_margin_seconds=policy['teardown_margin_seconds'],
            deadline_set_only_by_fresh_main_admission=True)
        proposed['source_closure'] = deepcopy(row['source_closure'])
        proposed['receive_verification_required'] = True
        configs[name] = proposed
    return dict(schema='CPU_REPLICATION_CANDIDATE_V1', created_unix=now,
        status='CPU_PREPARED_IMPLEMENTATION_BLOCKED_NOT_LAUNCH_READY',
        sampling_epoch=sampling_epoch, sampling_epoch_sha256=sampling_sha, configs=configs,
        resource_policy={name: deepcopy(policy[name]) for name in (
            'role_devices', 'protected_physical', 'claims_namespace', 'lease_end_unix',
            'lease_boundary_unix', 'max_runtime_seconds', 'max_concurrent_jobs',
            'receiving_hostname', 'expected_uid')},
        known_historical_source_no_retry=deepcopy(receipt['queue']['history']['attempts']),
        effective_hard_end_unix=hard_end,
        launch_intent=None, capsule=None, consumed_guard_reused=False,
        original_configs_modified=False, execution_allowed=False, implementation_blockers=list(BLOCKERS),
        runtime_estimate=dict(measured_seconds_by_arm={name: row['elapsed_seconds']
            for name, row in zip(BLOCKS[block], rows, strict=True)},
            measured_serial_seconds=sum(row['elapsed_seconds'] for row in rows),
            estimate_excludes_cold_custody_admission_and_content_variability=True,
            generated_tokens=len(rows) * 6144, actual_gpu_seconds_not_measured=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--receipt-sha256', required=True)
    parser.add_argument('--seeds', type=int, nargs=2, required=True)
    parser.add_argument('--block', choices=BLOCKS, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(sha(args.receipt) == args.receipt_sha256, 'bound_inspection_receipt')
    require(args.output.resolve().parent == HERE and not args.output.exists()
        and not args.output.is_symlink(), 'new_local_workstream_artifact_only')
    receipt = json.loads(args.receipt.read_bytes())
    result = build(receipt, args.seeds, args.block, time.time())
    result['inspection_receipt'] = dict(path=str(args.receipt), sha256=args.receipt_sha256)
    result['aligned_original_pair'] = align_original_pair(receipt)
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write('\n')
    print(json.dumps(dict(status=result['status'], artifact=str(args.output),
        sha256=sha(args.output), sampling_epoch_sha256=result['sampling_epoch_sha256'])))


if __name__ == '__main__':
    main()
