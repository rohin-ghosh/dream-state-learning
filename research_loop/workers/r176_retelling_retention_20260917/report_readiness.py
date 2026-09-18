"""Local, operational-only synthesis; never reads private evaluator payloads."""

import json
from pathlib import Path
import time

import preparation_io as common


def main():
    root = Path(__file__).resolve().parent
    common.validate_controls(root)
    rows = [json.loads(path.read_bytes()) for path in (root/'preparation1/global_ledger/reservations').glob('*.json')]
    totals = {kind:sum(row['bytes'] for row in rows if row['kind']==kind) for kind in ('metadata','adapter','storage')}
    totals['discovery_included'] = sum(row['bytes'] for row in rows if row['discovery'])
    per_life = {life:{kind:sum(row['bytes'] for row in rows if row['life_id']==life and row['kind']==kind)
        for kind in ('metadata','adapter')} for life in ('C2','C5')}
    source_path = root/'preparation1/source_capture2/PUBLIC_METADATA.json'
    receiving_path = root/'preparation1/receiving_cpu_continuation1/PUBLIC_METADATA.json'
    runner_path = root/'preparation1/narrow_runner1/PUBLIC_METADATA.json'
    source = json.loads(source_path.read_bytes())
    receiving = json.loads(receiving_path.read_bytes())
    runner = json.loads(runner_path.read_bytes())
    document = dict(status='ONE_C2_CHECKPOINT_PREPARED_INTEGRATION_REVIEW_AND_MAIN_GO_PENDING',
        recorded_unix=time.time(),life_id='C2',sleep=33,source_observed_unix=source['observed_unix'],
        receiving_CPU_observed_unix=receiving['observed_unix'],receiving_CPU_tests=receiving['tests_run'],
        runner_CPU_observed_unix=runner['observed_unix'],runner_CPU_tests=runner['tests_run'],
        candidate_condition_configs=runner['condition_config_count'],future_calls_if_both_admitted=6,
        model_calls=0,provider_calls=0,execution_authorized=False,private_outcome_reads=0,
        current_captured_slots=dict(C2=1,C5=0),fixed_slots=dict(C2=6,C5=6),
        C5_status='PRIOR_CUSTODY_HOLD_NO_NEW_R176_OBSERVATION',
        budgets_reserved_no_refund=totals,per_life_reserved=per_life,reservations=len(rows),
        fixed_proposal_sha256=common.PINS['PROPOSAL.json'],scope_sha256=common.SCOPE_SHA,
        R179_living_context_is_separate=True,instrument_changed=False,
        evidence=[str(source_path),str(receiving_path),str(runner_path)],
        blockers=['FRESH_BOUND_R176_INTEGRATION_REVIEW','MAIN_SEPARATE_BOUND_NO_RESET_EXECUTION_GO','FRESH_STRICT_NODE2_ADMISSION'])
    common.write(root/'READINESS_20260917T1701Z.json',document)
    print(json.dumps(document,sort_keys=True))


if __name__=='__main__':
    main()
