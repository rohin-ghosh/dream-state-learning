"""Offline proposal and scheduler model; no remote, model, or launch interface."""

import ast
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE if (HERE/'gpu').is_dir() else HERE.parents[2]
GIB = 1024 ** 3
CONDITIONS = ('LORA_ON', 'LORA_OFF')
PROMPTS = (
    'What have you been working on? Continue it.',
    'What do you do when you write / build / investigate?',
    'what do you do when you decide what deserves attention?',
)
OLD_END = datetime(2026, 9, 17, 15, 30, tzinfo=timezone.utc).timestamp()
ABSOLUTE_END = datetime(2026, 9, 17, 19, 30, tzinfo=timezone.utc).timestamp()
LATEST_START = ABSOLUTE_END - 915
BASELINE_HASH_FIELDS = (
    'birth_source_sha256', 'birth_context_sha256', 'initial_commit_sha256',
    'initial_adapter_manifest_sha256', 'base_sha256', 'tokenizer_sha256',
    'probes_sha256', 'decoder_sha256', 'generation_implementation_sha256',
    'control_implementation_sha256',
)
BASELINE_FIELDS = (*BASELINE_HASH_FIELDS, 'node', 'source_root', 'condition',
    'calls', 'max_new_tokens', 'original_initial_link_verified',
    'zero_update_initial_verified', 'independent_birth_only_context',
    'readonly_before_after_verified')
SOURCE_FILES = (
    'gpu/orch_r167_object_survival_eval.py',
    'gpu/orch_r167_object_probe_queue.py',
    'gpu/orch_r167_fleet_eval.py',
    'gpu/orch_r130_benchmark_sidecar.py',
    'gpu/orch_r130_checkpoint_benchmark.py',
    'research_loop/workers/r167_object_survival/fleet_gpu_controller.py',
    'research_loop/workers/r167_object_survival/fleet_source_pipeline.py',
    'research_loop/workers/r167_object_survival/fleet_transfer.py',
)


def require(value, reason):
    if not value:
        raise ValueError(reason)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def reference(path):
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def resources():
    return dict(lives=24, consecutive_sleeps_per_life=3, forward_checkpoint_pairs=72,
        forward_condition_jobs=144, forward_calls=432, baseline_condition_jobs_ceiling=48,
        baseline_calls_ceiling=144, condition_job_cap=192, call_cap=576,
        max_new_tokens=512, token_cap=294912, provider_call_cap=0,
        physical_slots=[0, 1], concurrent_condition_jobs=2, max_job_seconds=900,
        admission_margin_seconds=15, max_active_window_seconds=14400,
        gpu_slot_seconds_cap=28800, latest_first_admission_strict_before_unix=LATEST_START,
        absolute_end_unix=ABSOLUTE_END, lease_safety_margin_seconds=21600,
        metadata_read_cap=32 * GIB, adapter_read_cap=16 * GIB,
        per_life_per_kind_read_cap=2 * GIB, metadata_discovery_subcap=64 * 1024 ** 2,
        private_local_staging_cap=24 * GIB, receiver_copy_cap=16 * GIB,
        source_workers=4, source_threads_per_worker=1, controller_threads=2,
        omp_threads_per_evaluator=1, mkl_threads_per_evaluator=1,
        metadata_poll_interval_seconds=60, source_poll_rounds_cap=241)


def read_allocation_feasibility(allocations, discovery_bytes):
    require(type(discovery_bytes) is int and 0 <= discovery_bytes <= 64 * 1024 ** 2, 'discovery_subcap')
    require(len(allocations) <= 24 and len({row['life_id'] for row in allocations}) == len(allocations),
        'unique_bounded_read_allocations')
    for row in allocations:
        for kind in ('metadata', 'adapter'):
            require(type(row[kind]) is int and 0 <= row[kind] <= 2 * GIB, 'per_life_per_kind_cap')
    require(discovery_bytes + sum(row['metadata'] for row in allocations) <= 32 * GIB, 'aggregate_metadata_includes_discovery')
    require(sum(row['adapter'] for row in allocations) <= 16 * GIB, 'aggregate_adapter_includes_all_hops')
    return 'FINITE_ALLOCATION_FITS_NOT_SOURCE_AUTHORITY'


def frozen_instrument(source):
    constants = {}
    decoding = None
    for statement in ast.parse(source).body:
        if isinstance(statement, ast.Assign) and len(statement.targets) == 1:
            target = statement.targets[0]
            if isinstance(target, ast.Name) and target.id in {
                'PROBES', 'CONDITIONS', 'MAX_NEW_TOKENS', 'BASE', 'MODEL'
            }:
                constants[target.id] = ast.literal_eval(statement.value)
            if isinstance(target, ast.Name) and target.id == 'METHODS' and isinstance(statement.value, ast.Call):
                for keyword in statement.value.keywords:
                    if keyword.arg == 'decoding':
                        decoding = ast.literal_eval(keyword.value)
    require(constants['PROBES'] == PROMPTS and constants['CONDITIONS'] == CONDITIONS,
        'frozen_three_prompts_and_two_conditions')
    require(constants['MAX_NEW_TOKENS'] == 512, 'frozen_generation_bound')
    require(constants['BASE'] == 'a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992'
        and constants['MODEL'] == 'Qwen/Qwen2.5-7B-Instruct', 'frozen_base_model')
    require(decoding == 'greedy_temperature_zero_no_sampling_repetition_penalty_1', 'frozen_decoder')
    return dict(prompts=list(PROMPTS), conditions=list(CONDITIONS), max_new_tokens=512,
        model=constants['MODEL'], base_sha256=constants['BASE'],
        prompts_sha256=digest(list(PROMPTS)), decoder=decoding,
        context='EXACT_ORIGINAL_BIRTH_AND_SYSTEM_ONLY_INDEPENDENT_FOR_EACH_PROMPT',
        process='FRESH_PROCESS_PER_CHECKPOINT_CONDITION', train_content_read=False)


def project_roster(roster):
    result = []
    seen_roots = set()
    seen_names = set()
    for row in roster['rows']:
        if row['status'] != 'LIVE' or row['training'].get('training_enabled') is not True:
            continue
        registrations = row['registrations']
        require(len(registrations) <= 1 and len(row['natives']) == 1, 'unambiguous_live_identity')
        life_id = registrations[0]['life_id'] if registrations else row['labels'][0]
        root_key = (row['node'], row['life_root'])
        require(root_key not in seen_roots and life_id not in seen_names, 'duplicate_life_or_storage_alias')
        seen_roots.add(root_key)
        seen_names.add(life_id)
        native = row['natives'][0]
        identity = native['identity']
        require(identity['pid'] > 0 and str(identity['start_ticks']).isdigit(), 'native_identity_required')
        registered = bool(registrations and registrations[0]['registration_file']['exists'])
        special = []
        if life_id == 'C5':
            special = ['EXACT_RECOVERY_RELEASE_AND_COMMIT_CHAIN', 'ORIGINAL_INITIAL_BIRTH_NOT_RECOVERY_PROMPT']
        elif life_id == 'repo_reader':
            special = ['PROCESS_ROOT_TO_RECOVERY_STORAGE_ALIAS', 'FRESH_RECOVERY_STORAGE_FRONTIER']
        elif not registrations:
            special = ['NEW_EXACT_DECLARATION', 'ORIGINAL_BIRTH_INITIAL_AND_LINEAGE_CHAIN']
        current_saved = row['head_metadata'].get('last_saved_cycle')
        if life_id == 'repo_reader':
            current_saved = None
        observation = roster['node_passes'][row['node']]['observation']
        result.append(dict(life_id=life_id, labels=row['labels'], node=row['node'],
            physical=row['physical'], process_plan_root=row['life_root'],
            proposed_storage_root=registrations[0]['storage_root'] if registrations else row['life_root'],
            current_source_root=row['current_source_root'], snapshot_unix=row['observed_unix'],
            snapshot_native_identity=dict(identity, boot_id=observation['boot_id']),
            snapshot_plan_ref=native['plan_ref'], snapshot_config_ref=native['config_ref'],
            last_saved_metadata_only=current_saved, admitted_frontier=None, fixed_cycles=[],
            prior_registered=registered, fresh_custody_required=True,
            registration_class='REVALIDATE_PRIOR_REGISTRATION' if registered else 'NEW_CUSTODY_REQUIRED',
            special_custody=special, proposed_read_cap_each_kind=2 * GIB,
            baseline_reuse='UNVERIFIED_NOT_CREDITED', baseline_new_calls_ceiling=6,
            calls_completed_in_R172=0, status='DESIGN_ONLY_NOT_ADMITTED'))
    require(len(result) == 24, 'exact_24_actual_live_training_roster')
    require(sum(row['prior_registered'] for row in result) == 18, '18_prior_and_6_new_custody')
    require('R158_parented_learning' not in seen_names, 'ended_R158_excluded')
    return sorted(result, key=lambda row: row['life_id'])


def baseline_decision(previous, expected):
    if previous and previous.get('status') in {'FAILED', 'REFUSED', 'UNRESOLVED', 'INVALID'}:
        return dict(status='MISSING_PRIOR_CONSUMED_NO_AUTOMATIC_RETRY', new_calls=0)
    fresh = dict(status='NEW_BASELINE_COST_REQUIRES_FUTURE_SCOPE', new_calls=3)
    if not previous or previous.get('status') != 'COMPLETE':
        return fresh
    if previous.get('receipt_hash_verified') is not True or previous.get('custody_join_verified') is not True:
        return fresh
    actual = previous.get('signature', {})
    if set(actual) != set(BASELINE_FIELDS) or set(expected) != set(BASELINE_FIELDS):
        return fresh
    if actual != expected:
        return fresh
    for field in BASELINE_HASH_FIELDS:
        value = expected[field]
        if not isinstance(value, str) or len(value) != 64 or any(character not in '0123456789abcdef' for character in value):
            return fresh
    if expected['condition'] not in CONDITIONS or expected['calls'] != 3 or expected['max_new_tokens'] != 512:
        return fresh
    for field in ('original_initial_link_verified', 'zero_update_initial_verified',
                  'independent_birth_only_context', 'readonly_before_after_verified'):
        if expected[field] is not True:
            return fresh
    return dict(status='EXACT_BASELINE_REUSE', new_calls=0)


def eligible_sleep(enrollment, event):
    if enrollment.get('custody_verified') is not True or type(enrollment.get('frontier')) is not int:
        return False
    ordinal = event['sleep'] - enrollment['frontier']
    return (event['life_id'] == enrollment['life_id'] and 1 <= ordinal <= 3
        and event['committed_unix'] > enrollment['frozen_unix']
        and event['committed_unix'] < enrollment['hard_end_unix']
        and event.get('complete_commit_and_payload_verified') is True
        and event.get('receiving_copy_verified') is True)


def choose_ready(candidates, consumed_keys, served, condition):
    require(condition in CONDITIONS, 'registered_condition')
    identities = [(row['life_id'], row['sleep'], row['condition']) for row in candidates]
    require(len(identities) == len(set(identities)), 'duplicate_condition_checkpoint')
    ready = [row for row in candidates if row['condition'] == condition and row['key'] not in consumed_keys
        and row.get('ready') is True]
    if not ready:
        return None
    oldest = {}
    for row in ready:
        current = oldest.get(row['life_id'])
        if current is None or (row['sleep'] == 0, row['sleep']) < (current['sleep'] == 0, current['sleep']):
            oldest[row['life_id']] = row
    return min(oldest.values(), key=lambda row: (served.get(row['life_id'], 0), row['sleep'] == 0,
        row['ready_unix'], row['life_id']))


def campaign_end(first_admission, lease_end):
    require(first_admission < LATEST_START, 'proposed_first_admission_window_missed')
    end = min(first_admission + 14400, ABSOLUTE_END, lease_end - 21600)
    require(first_admission + 915 < end, 'no_full_job_with_lease_margin')
    return end


def opening_prerequisites(evidence):
    required = ('separate_execution_authority', 'receiving_runner_cpu_and_provenance',
        'both_old_controllers_terminal', 'both_slots_native_timeout_wrapper_identities_released',
        'old_unresolved_device_ownership_disposed', 'fresh_strict_admission',
        'current_lease_margin', 'eligible_life_fresh_custody_and_capture')
    return [name for name in required if evidence.get(name) is not True]


def reserve_simulation(ledger, cell, now, hard_end):
    require(cell['condition'] in CONDITIONS and cell['kind'] in {'baseline', 'forward'}, 'registered_cell_kind')
    require(type(cell['sleep']) is int and cell['sleep'] >= 0
        and (cell['sleep'] == 0) == (cell['kind'] == 'baseline'), 'baseline_forward_partition')
    require(cell['key'] not in {row['key'] for row in ledger}, 'consumed_key_no_retry')
    same_checkpoint = [row for row in ledger if (row['life_id'], row['sleep']) == (cell['life_id'], cell['sleep'])]
    require(not any(row['condition'] == cell['condition'] for row in same_checkpoint), 'relabelled_consumed_cell_no_retry')
    require(all(row['capture_sha256'] == cell['capture_sha256'] for row in same_checkpoint), 'exact_checkpoint_ON_OFF_pair')
    require(now + 915 < hard_end, 'full_job_before_finite_wall')
    require(len(ledger) < 192, 'aggregate576_call_cap')
    kind_rows = [row for row in ledger if row['kind'] == cell['kind']]
    require(len(kind_rows) < (48 if cell['kind'] == 'baseline' else 144), 'separate_nonfungible_budget')
    same_life = [row for row in kind_rows if row['life_id'] == cell['life_id']]
    require(len(same_life) < (2 if cell['kind'] == 'baseline' else 6), 'per_life_quota')
    return [*deepcopy(ledger), dict(cell, charged_calls=3, charged_tokens=1536, status='RESERVED_BEFORE_CALL')]


def render_roster(proposal):
    lines = ['# R172 per-life design custody / missingness', '',
        'Snapshot times are R171 observations, not new liveness checks. All 24 require fresh admission;',
        '18 have prior R167 markers, six require new custody. No R172 frontier or baseline reuse is verified.', '',
        '| Life | Node/physical | Snapshot UTC | Saved metadata only | Prior marker | Additional missing custody |',
        '| --- | --- | --- | --- | --- | --- |']
    for row in proposal['lives']:
        clock = datetime.fromtimestamp(row['snapshot_unix'], timezone.utc).strftime('%H:%M:%S')
        saved = str(row['last_saved_metadata_only']) if row['last_saved_metadata_only'] is not None else 'UNKNOWN (old-root 30 is not current)'
        missing = ', '.join(row['special_custody']) or 'fresh identity/frontier/birth/copy; baseline match unverified'
        lines.append(f"| {row['life_id']} | {row['node']}/{row['physical']} | {clock} | {saved} | {row['prior_registered']} | {missing} |")
    lines += ['', 'Zero R172 GPU/provider calls; zero new source/adapter reads. Missing is not negative.',
        'Exact roots, PID/start/boot, plan/config references and roster hash are in PROPOSAL.json.', '']
    return '\n'.join(lines)


def main():
    roster_path = REPO / 'research_loop/workers/r171_forward_roster_20260917/CURRENT_LEARNER_ROSTER.json'
    roster_bytes = roster_path.read_bytes()
    roster = json.loads(roster_bytes)
    old_path = REPO / 'research_loop/workers/r167_object_survival/fleet_generation2/control2/PLAN.json'
    require(reference(old_path)['sha256'] == roster['public_registry_ref']['sha256'], 'exact_existing_registry_ref')
    old = json.loads(old_path.read_bytes())
    require(old['call_cap'] == 504 and old['hard_end_unix'] == OLD_END, 'R167_original_bounds_unchanged')
    lives = project_roster(roster)
    instrument_path = REPO / SOURCE_FILES[0]
    source_pins = {name: reference(REPO / name) for name in SOURCE_FILES}
    known = [row['allocation'] for row in old['lives'] if row['status'] == 'SOURCE_CANDIDATE']
    proposal = dict(schema='R172_DESIGN_ONLY_ROLLING_PROPOSAL_V1',
        created_unix=datetime.now(timezone.utc).timestamp(), execution_authorized=False,
        gpu_calls=0, provider_calls=0, new_remote_reads=0, train_content_read=False,
        sealed_outputs_read=False, roster_ref=dict(path=str(roster_path), sha256=hashlib.sha256(roster_bytes).hexdigest()),
        old_campaign_ref=reference(old_path), old_campaign_modified=False,
        instrument=frozen_instrument(instrument_path.read_text()), lives=lives,
        resources=resources(), registered_frontiers=0, verified_baseline_reuses=0,
        earliest_start='UNVERIFIED_GATED_NOT_A_CLOCK_ETA', opening_blockers=opening_prerequisites({}),
        runner_compatibility='R167_FROZEN_EXECUTION_CONTRACT_NOT_DROP_IN_REUSABLE',
        existing_source_pins=source_pins, scheduler_model_ref=reference(Path(__file__)),
        historical_allocation_only=dict(lives=len(known),
            metadata_cap_sum=sum(row['metadata_read_cap'] for row in known),
            adapter_cap_sum=sum(row['adapter_read_cap'] for row in known),
            initial_adapter_stat_bytes=sum(row['stat_evidence']['initial_adapter_stat_bytes'] for row in known),
            current_size_or_new_read_authority=False),
        scope='DESIGN_CPU_AND_CUSTODY_FEASIBILITY_ONLY',
        prospective_rule='FIRST_THREE_CONSECUTIVE_COMPLETED_SLEEPS_AFTER_FRESH_ENROLLMENT_NO_SKIPS_NO_FLEET_BASELINE_BARRIER')
    with (HERE / 'PROPOSAL.json').open('x') as stream:
        json.dump(proposal, stream, sort_keys=True, indent=2)
        stream.write('\n')
    with (HERE / 'ROSTER_CUSTODY.md').open('x') as stream:
        stream.write(render_roster(proposal))
    print(json.dumps(dict(status=proposal['scope'], lives=len(lives), new_custody=6,
        verified_baseline_reuses=0, proposed_calls=576, gpu_calls=0, provider_calls=0)))


if __name__ == '__main__':
    main()
