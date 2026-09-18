"""Exact-row TRAIN eligibility correction; native encoder and visibility unchanged."""

from copy import deepcopy
import json
import os
from pathlib import Path

if __package__:
    from gpu import orch_r141_a100_perception_recovery_20260916 as evidence
else:
    import orch_r141_a100_perception_recovery_20260916 as evidence


OFFENDING = '25fd6c6809fae42183092a7c6251cbf7f97ce1ca2c614957ae74d3573bea120a'
REASON = 'r141_pinned_generated_special_token_target_excluded'


def eligible_rows(rows, presentation, original):
    before = evidence.digest(rows)
    retained, corrections = [], []
    for row in rows:
        if row['source_sha256'] != OFFENDING:
            retained.append(row)
            continue
        evidence.require(row['split'] == 'TRAIN' and row['actor'] == 'child'
            and row['prefix_loss'] is False and row['target_loss'] is True, 'exact_child_exclusion_provenance')
        evidence.require(row['token_ids'][64:66] == [151644, 151644]
            and len(row['token_ids']) == 138 and '<|im_start|><|im_start|>' in row['target'],
            'exact_offending_generated_delimiters')
        corrections.append(dict(source_sha256=OFFENDING, reason=REASON))
    accepted, excluded = original(retained, presentation)
    evidence.require(evidence.digest(rows) == before, 'raw_history_carry_rows_unchanged')
    return accepted, excluded + corrections


def cpu_report():
    evidence.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only')
    from gpu.astra_pchain2_native import load_local_tokenizer
    from gpu.orch_r125_continual_native import encode_own
    from gpu.orch_r125_stream_console import _open_stream_directory, _read_record
    from organism_v6.orch_r125_plain_context import eligible_rows as original
    root = evidence.ROOT
    guard = json.loads((root / 'control2/GUARD.json').read_text())
    evidence.require(evidence.sha(guard['plan_path']) == evidence.PLAN_SHA, 'original_plan')
    evidence.require(evidence.sha(evidence.SOURCE / 'gpu/orch_r125_continual_native.py') == evidence.NATIVE_SHA,
        'unmodified_native_special_token_guard')
    plan = json.loads(Path(guard['plan_path']).read_text())
    commit_path = root / 'run1/checkpoints/sleep_000015/COMMIT.json'
    evidence.require(evidence.sha(commit_path) == evidence.COMMIT_SHA, 'original_checkpoint')
    checkpoint = json.loads(commit_path.read_text())
    evidence.require(evidence.sha(checkpoint['optimizer_rng_path']) == checkpoint['checkpoint_sha256']['optimizer']
        == checkpoint['checkpoint_sha256']['rng'], 'saved_optimizer_rng_bytes')
    records = []
    with _open_stream_directory(plan['root'], 'records') as (directory, unused):
        while True:
            record = _read_record(directory, len(records))
            if record is None:
                break
            if records:
                evidence.require(record['previous_sha256'] == records[-1]['sha256']
                    and record['journal_id'] == records[-1]['journal_id'], 'journal_chain')
            records.append(record)
    requests, responses = evidence.bind_live(records, checkpoint, plan)
    state = records[1248]['document']['resume_state']['state']
    before = deepcopy(state)
    tokenizer = load_local_tokenizer(plan['model_dir'])
    cohorts = [('NEW', state['rows'][state['sleep_frontier']:]), ('REHEARSAL', state['rows'][:state['sleep_frontier']])]
    encoded, exclusions = [], []
    for cohort, rows in cohorts:
        accepted, excluded = eligible_rows(rows, state['presentation'], original)
        prior_accepted, unused = original(rows, state['presentation'])
        evidence.require(accepted == [row for row in prior_accepted if row['source_sha256'] != OFFENDING],
            'all_other_prefixes_targets_eligibility_unchanged')
        exclusions.extend([dict(item, cohort=cohort) for item in excluded])
        for row in accepted:
            result = encode_own(row, tokenizer, plan['context_limit'])
            encoded.append(dict(cohort=cohort, source_sha256=row['source_sha256'], input_tokens=len(result.input_ids)))
    offending = next(row for row in state['rows'] if row['source_sha256'] == OFFENDING)
    try:
        encode_own(offending, tokenizer, plan['context_limit'])
    except ValueError as error:
        evidence.require(str(error) == 'no_special_token_target_injection', 'original_rejection_reason_unchanged')
    else:
        raise ValueError('native_special_token_guard_must_still_reject')
    import torch
    payload = torch.load(checkpoint['optimizer_rng_path'], map_location='cpu', weights_only=False)
    evidence.require(payload['optimizer_steps'] == evidence.STEPS and payload.get('experiment') == checkpoint.get('experiment'),
        'saved_optimizer_steps_experiment')
    evidence.require(len(payload['parameter_names']) == len(set(payload['parameter_names'])) > 0,
        'saved_parameter_order_unique')
    evidence.require(payload['cpu_rng'].dtype == torch.uint8 and len(payload['cuda_rng']) == 1
        and all(item.dtype == torch.uint8 for item in payload['cuda_rng']), 'saved_CPU_and_one_CUDA_rng')
    import random
    verifier = random.Random(0)
    verifier.setstate(payload['python_rng'])
    evidence.require(verifier.getstate() == payload['python_rng'], 'saved_python_rng_valid')
    evidence.require(state == before, 'raw_history_carry_pending_unchanged')
    evidence.require(evidence.sha(checkpoint['optimizer_rng_path']) == checkpoint['checkpoint_sha256']['optimizer'],
        'checkpoint_unchanged_after_CPU_read')
    return dict(schema='R141_PERCEPTION_TARGET_EXCLUSION_CPU_V1', status='CPU_EXCLUSION_PROVEN_ON_ACTUAL_TRAIN',
        exact_offending_source_sha256=OFFENDING, accepted_rows=encoded, exclusions=exclusions,
        native_guard_unchanged_and_still_rejects=True, raw_history_carry_pending_unchanged=True,
        all_other_prefixes_targets_eligibility_unchanged=True, model_loaded=False, GPU_replays=0,
        optimizer_steps=payload['optimizer_steps'], optimizer_state_entries=len(payload['optimizer']['state']),
        parameter_names_sha256=evidence.digest(payload['parameter_names']),
        cpu_rng_sha256=evidence.digest(payload['cpu_rng'].tolist()),
        cuda_rng_sha256=[evidence.digest(item.tolist()) for item in payload['cuda_rng']],
        python_rng_sha256=evidence.digest(payload['python_rng']),
        exact_replay_request_sha256=[evidence.digest(request) for request in requests],
        exact_replay_response_sha256=[evidence.digest(response) for response in responses],
        GPU_launch_ready=False, held_contents_read=False,
        limitation='Actual adapter/AdamW reload and three exact GPU generation matches are not yet established.')


if __name__ == '__main__':
    print(json.dumps(cpu_report(), sort_keys=True, indent=2))
