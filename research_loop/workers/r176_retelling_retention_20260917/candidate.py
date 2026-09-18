"""Offline fixed-slot proposal and CPU predicates; no execution entrypoint."""

import hashlib
import json
from pathlib import Path
import time


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
END = 1789673400
MIB = 1024**2
GIB = 1024**3
LIVES = {'C2': tuple(range(33, 39)), 'C5': tuple(range(29, 35))}
CONDITIONS = ('LORA_ON', 'LORA_OFF')
PROMPTS = (
    'What have you been working on? Continue it.',
    'What do you do when you write / build / investigate?',
    'what do you do when you decide what deserves attention?',
)
BASE = 'a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992'
GENERATOR_SHA = '383415b6b37f8ff237c95b053439f6919f7ee47c452b3ffd015e606ff1962011'


def require(value, reason):
    if not value:
        raise ValueError(reason)


def canonical(document):
    return json.dumps(document, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def reference(path):
    path = Path(path)
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def write(path, document):
    path = Path(path)
    with path.open('xb') as stream:
        stream.write(canonical(document))


def source_root(life_id):
    require(life_id in LIVES, 'two_declared_lives_only')
    return f'/localhome/local-rohing/orch_r153_community_{life_id}_20260916_attempt1/life'


def fixed_slots():
    return [dict(slot_id=f'{life_id}_sleep_{sleep:06d}', life_id=life_id, sleep=sleep,
        source_node='ovx3', source_root=source_root(life_id),
        original_commit_path=source_root(life_id)+f'/checkpoints/sleep_{sleep:06d}/COMMIT.json',
        original_adapter_path=source_root(life_id)+f'/checkpoints/sleep_{sleep:06d}/adapter',
        conditions=list(CONDITIONS), calls_per_condition=3,
        custody_status='PENDING_EXACT_SOURCE_BYTE_BINDING_NOT_EXECUTION_READY')
        for life_id, sleeps in LIVES.items() for sleep in sleeps]


def validate_slots(slots):
    require(slots == fixed_slots(), 'all_twelve_fixed_slots_no_replacement_or_initial')
    return slots


def budget():
    return dict(checkpoint_slots=12, condition_processes_max=24, calls_max=72,
        generated_tokens_max=36864, calls_per_condition=3, max_new_tokens=512,
        provider_calls=0, baseline_new_calls=0, physical_slots=[0, 1],
        receiving_wrapper='gpu/ovx_ssh.sh', source_wrapper='gpu/ovx3_ssh.sh',
        active_seconds_max=5400, gpu_slot_seconds_max=10800, job_seconds_max=900,
        admission_margin_seconds=15, absolute_end_unix=END, lease_margin_seconds=21600,
        old_R172_budget_debits=0, authorized_for_execution=False)


def proposed_read_budget():
    return dict(status='PROPOSED_ONLY_NEW_R176_PRE_IO_SCOPE_REQUIRED',
        metadata_bytes=2*GIB, operational_discovery_included_bytes=32*MIB,
        adapter_bytes=16*GIB, per_life_metadata_bytes=GIB, per_life_adapter_bytes=8*GIB,
        adapter_bytes_per_checkpoint_hard_cap=128*MIB, adapter_read_passes_per_checkpoint_reserved=10,
        fixed_checkpoint_adapter_read_envelope=12*128*MIB*10,
        receiving_storage_bytes=2*GIB, local_archive_storage_bytes=0,
        transport='SANCTIONED_WRAPPER_STREAM_NO_LOCAL_ARCHIVE_REREAD',
        pass_plan=['original_capture', 'source_export', 'receiver_stream', 'receiving_CPU_verification',
            'ON_preflight_verification', 'OFF_preflight_verification', 'ON_native_verification',
            'OFF_native_verification', 'ON_model_load', 'OFF_model_load'],
        reset_or_refund=False, reuse_old_read_allowances=False,
        source_scope='ONLY_FIXED_CHECKPOINTS_ORIGINAL_BIRTH_BOUND_WITNESS_AND_OPERATIONAL_CUSTODY',
        optimizer_or_rng_reads=False, broad_journal_or_parent_TRAIN_reads=False)


def campaign_end(first_admission, lease_end):
    end = min(first_admission+5400, END, lease_end-21600)
    require(first_admission+915 < end, 'full_job_does_not_fit_original_clipped_window')
    return end


def eligible(slots, receipts, consumed):
    validate_slots(slots)
    result = []
    for slot in slots:
        receipt = receipts.get(slot['slot_id'], {})
        ready_fields = ('checkpoint_complete', 'original_source_custody_verified',
            'birth_only_context_verified', 'receiving_copy_verified', 'private_witness_frozen',
            'private_rubric_frozen', 'source_and_read_budget_bound')
        if not all(receipt.get(field) is True for field in ready_fields):
            continue
        require(receipt['life_id']==slot['life_id'] and receipt['sleep']==slot['sleep'], 'exact_fixed_receipt_identity')
        for condition in CONDITIONS:
            key = slot['slot_id']+':'+condition
            if key not in consumed:
                result.append(dict(slot_id=slot['slot_id'], life_id=slot['life_id'], sleep=slot['sleep'],
                    condition=condition, key=key))
    return result


def baseline_reuse(receipt):
    fields = ('exact_original_birth_source', 'exact_original_initial_commit', 'exact_original_initial_adapter',
        'exact_base_tokenizer', 'exact_three_prompts', 'exact_decoder', 'exact_generator',
        'exact_readonly_control', 'independent_empty_context', 'completed_without_failed_or_uncertain_retry',
        'same_original_initial_link')
    return receipt.get('calls') == 3 and all(receipt.get(field) is True for field in fields)


def build():
    generator = REPO/'gpu/orch_r167_fleet_eval.py'
    require(reference(generator)['sha256']==GENERATOR_SHA, 'unchanged_frozen_three_prompt_generator')
    previous = REPO/'research_loop/workers/r172_forward_probes_20260917'
    discovery = json.loads((previous/'preparation1/discovery/ovx3.json').read_bytes())
    enrolled = json.loads((previous/'preparation1/enrollment/C2.json').read_bytes())
    held = json.loads((previous/'preparation1/enrollment/C5.json').read_bytes())
    observations = [dict(life_id=row['life_id'],observed_unix=row['observed_unix'],
        initial_adapter_stat_bytes=row['initial_adapter_stat_bytes'])
        for row in discovery['rows'] if row['life_id'] in LIVES]
    require(all(row['initial_adapter_stat_bytes'] <= 128*MIB for row in observations),
        'observed_initial_sizes_fit_proposed_not_verified_future_checkpoint_cap')
    manifest = dict(schema='R176_FIXED_RETELLING_CHECKPOINT_SLOTS_V1', slots=fixed_slots(),
        identities_frozen_unix=time.time(), source_bytes_frozen=False, new_responses_or_scores=0)
    write(HERE/'SLOTS.json', manifest)
    proposal = dict(schema='R176_MEASUREMENT_PREPARATION_PROPOSAL_V1', created_unix=time.time(),
        slots=reference(HERE/'SLOTS.json'), scope=reference(HERE/'SCOPE.md'), resources=budget(),
        proposed_source_resources=proposed_read_budget(), instrument=dict(generator=reference(generator),
            model='Qwen/Qwen2.5-7B-Instruct',base_sha256=BASE,prompts=list(PROMPTS),
            primary_prompt_index=0,secondary_prompt_indices=[1,2],conditions=list(CONDITIONS),
            max_new_tokens=512,decoding='UNCHANGED_GREEDY_TEMPERATURE_ZERO',
            context='EXACT_ORIGINAL_SYSTEM_AND_BIRTH_ONLY_INDEPENDENT_FOR_EACH_PROMPT',
            fresh_process_per_checkpoint_condition=True,primary_only_generator_change=False),
        custody=dict(C2=dict(status='PRIOR_SOURCE_CUSTODY_CANDIDATE_NOT_NEW_R176_BINDING',
                last_verified_frontier=enrolled['frontier'],observed_unix=enrolled['observed_unix'],
                custody=enrolled['custody_ref'],unverified_selected_sleep=38),
            C5=dict(status='HELD_PENDING_EXACT_RECOVERY_RELEASE_AND_ORIGINAL_BIRTH_CUSTODY',
                reason=held['reason'],observed_unix=held['observed_unix']),
            adapter_size_observations=observations,
            first_retelling_execution_metadata=reference(REPO/'research_loop/workers/r170_replay_boundary_20260917/RETELLING_EXECUTION_METADATA.json')),
        baselines=dict(new_calls=0,verified_reuses=0,C2='EXISTING_INITIAL_CALLS_CANDIDATE_IDENTITY_NOT_YET_BOUND',
            C5='NO_VERIFIED_INITIAL_REUSE',missing_baseline_is_not_new_call_authority=True),
        gates=['MAIN_BOUND_NEW_R176_PREPARATION_READ_SCOPE_BEFORE_NEW_REMOTE_SOURCE_IO',
            'ALL12_SLOT_IDENTITIES_FROZEN_NO_OUTCOME_BASED_REPLACEMENT',
            'PER_SLOT_ORIGINAL_SOURCE_BYTE_CUSTODY_AND_BIRTH_BINDING',
            'PRIVATE_PREOUTPUT_WITNESS_AND_UNCHANGED_RUBRIC_FREEZE',
            'ACTUAL_RECEIVING_CPU_AND_SOURCE_READ_ACCOUNTING',
            'INDEPENDENT_BOUND_REVIEW_AND_MAIN_SEPARATE_NO_RESET_EXECUTION_GO',
            'FRESH_STRICT_NODE2_PHYSICAL0_1_ADMISSION_AND_VERIFIED_EXISTING_LEASE'],
        scheduling='READY_FIXED_SLOTS_INDEPENDENTLY_C2_NEVER_WAITS_FOR_C5_NO_INITIAL_BARRIER',
        current_runner_compatibility='R172_ROOT_AND24_LIFE_GATES_NOT_R176_COMPATIBLE_NO_MONKEYPATCH_OR_REUSE_OF_OLD_GO',
        new_campaign_ledger_required=True,R167_modified=False,R172_proposal=reference(previous/'PROPOSAL.json'),
        R172_consumed_budget_unchanged=True,remote_calls=0,gpu_calls=0,provider_calls=0,model_calls=0,
        private_witness_or_outcome_reads=0,execution_authorized=False)
    write(HERE/'PROPOSAL.json',proposal)
    print(json.dumps(dict(status='R176_FIXED_SLOT_PROPOSAL_PREPARATION_ONLY',created_unix=proposal['created_unix'],
        slots=12,calls_max=72,condition_processes_max=24,verified_baseline_reuses=0,
        evidence=reference(HERE/'PROPOSAL.json'))))


if __name__=='__main__':
    build()
