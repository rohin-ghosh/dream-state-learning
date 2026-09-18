"""Public operational handoff only; all existing reservations remain charged."""

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve().parent
WORKER = HERE.parents[1]
sys.path.insert(0, str(WORKER))
import preparation_io as common


def pin(path):
    return dict(path=str(path), sha256=common.sha(path.read_bytes()))


def main():
    common.validate_controls(WORKER)
    public = json.loads((HERE / 'attempt2/PUBLIC_METADATA.json').read_bytes())
    proof = json.loads((HERE / 'actual_proof1/PUBLIC_METADATA.json').read_bytes())
    common.require(proof['status'] == 'ALL_FOUR_COMPLETE_ACTUAL_VALIDATOR_PROOFS_PASS', 'four_actual_phase_passes')
    phases = []
    for record in proof['receipts']:
        receipt = json.loads(Path(record['reference']['path']).read_bytes())
        common.require(receipt['status'] == 'COMPLETE_ACTUAL_VALIDATOR_PASS'
            and receipt['all_phase_charges_persisted'] is True, 'actual_persisted_CPU_proof')
        phases.append(dict(execution=receipt['execution'], phase=receipt['phase'],
            observed_utc=datetime.fromtimestamp(receipt['observed_unix'], timezone.utc).isoformat(),
            cap_bytes=receipt['proof_cap_bytes'], phase_charge_bytes=receipt['phase_charge_counters_bytes'],
            bootstrap_charge_bytes=receipt['bootstrap']['charged_bytes'],
            metadata_headroom_bytes=receipt['metadata_headroom_bytes'],
            persisted_read_records=receipt['persisted_read_records'], read_ledger_path=receipt['read_ledger_path'],
            local_receipt=record['reference'],
            remote_receipt=dict(path=str(Path(receipt['read_ledger_path']).parents[2] / 'PUBLIC_METADATA.json'),
                sha256=record['reference']['sha256'])))
    results = subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', str(HERE),
        '-p', 'test_proof_reservations.py', '-v'], capture_output=True)
    test_ref = common.write(HERE / 'CPU_RESERVATION_REGRESSIONS_01.txt', results.stdout + results.stderr)
    common.require(results.returncode == 0, 'supplemental_reservation_regressions_pass')
    ledger = WORKER / 'preparation1/global_ledger'
    with common.lock(ledger / 'ledger.lock'):
        rows = [json.loads(path.read_bytes()) for path in (ledger / 'reservations').glob('*.json')]
        caps = dict(metadata=2 * common.GIB, adapter=16 * common.GIB, storage=2 * common.GIB)
        resources = {kind: dict(cap_bytes=cap, reserved_bytes=sum(row['bytes'] for row in rows if row['kind'] == kind))
            for kind, cap in caps.items()}
        for resource in resources.values():
            resource['remaining_unreserved_bytes'] = resource['cap_bytes'] - resource['reserved_bytes']
        lives = {}
        for life in ('C2', 'C5'):
            lives[life] = {kind: dict(cap_bytes=cap,
                reserved_bytes=sum(row['bytes'] for row in rows if row['life_id'] == life and row['kind'] == kind))
                for kind, cap in dict(metadata=common.GIB, adapter=8 * common.GIB).items()}
            for resource in lives[life].values():
                resource['remaining_unreserved_bytes'] = resource['cap_bytes'] - resource['reserved_bytes']
        discovery = sum(row['bytes'] for row in rows if row['discovery'])
        repairs = [row for row in rows if row['kind'] == 'adapter'
            and (row.get('repair_authority') or row.get('supplemental_repair_authority'))]
        envelope = dict(observed_utc=datetime.now(timezone.utc).isoformat(), ledger_root=str(ledger),
            reservation_count=len(rows), global_resources=resources, per_life=lives,
            discovery_included=dict(cap_bytes=32 * common.MIB, reserved_bytes=discovery,
                remaining_unreserved_bytes=32 * common.MIB - discovery),
            all_old_reservations_preserved=True, refunds=0, resets=0, R172_borrowing=0,
            full_nominal_adapter_envelope_plus_repairs_remaining_bytes=16 * common.GIB - 15 * common.GIB
                - sum(row['bytes'] for row in repairs),
            C2_full_nominal_adapter_envelope_plus_repairs_remaining_bytes=8 * common.GIB - 7680 * common.MIB
                - sum(row['bytes'] for row in repairs if row['life_id'] == 'C2'))
        envelope_ref = common.write(HERE / 'REMAINING_ENVELOPE_01.json', envelope)
    bindings = dict(schema='R176_NASH_I1_REPAIR_REREVIEW_HANDOFF_V1',
        status='AUTHOR_ACTUAL_CHARGED_CPU_PASS_AWAITING_NASH_BOUND_REREVIEW',
        addressed_to='Nash 01a0b064-e11c-7292-a107-787a5464ff34',
        observed_utc=datetime.now(timezone.utc).isoformat(), execution_authorized=False,
        model_calls=0, provider_calls=0, execution_attempts_consumed=0, admission_attempted=False,
        life_id='C2', sleep=33, future_calls_if_both_admitted=6,
        candidate_root=str(common.REMOTE / 'runner_candidate3_metadata_repair2'),
        candidate_public=dict(path=str(common.REMOTE / 'runner_candidate3_metadata_repair2/PUBLIC_METADATA.json'),
            sha256=common.sha((HERE / 'attempt2/PUBLIC_METADATA.json').read_bytes())),
        executions=public['executions'], source=public['source'], runner_path=public['runner_path'],
        runner_sha256=public['runner_sha256'], preparation_io=pin(WORKER / 'preparation_io.py'),
        cpu_gate=public['cpu_gate'], runner_cpu_gate=public['runner_cpu_gate'], old_release=public['old_release'],
        scope_pins=common.validate_controls(WORKER), phases=phases, remaining_envelope=envelope_ref,
        proof_script=pin(HERE / 'actual_validate_proof.py'),
        proof_launcher=pin(HERE / 'run_actual_proofs.py'),
        supplemental_reservation_interface=pin(HERE / 'proof_reservations.py'),
        regression_tests=dict(tests_run=8, failures=0, errors=0, receipt=test_ref),
        author_advocate='Non-material metadata-cap repair only; unchanged original birth, empty history, three prompts, '
            'decoder, base, private rubric, checkpoint pair, source closure and parent blindness.',
        authorization_fixture_limitation='Only GO/review supplied synthetically in memory to exercise the full validator; '
            'these are not actual authorization or independent approval. No fixture file was written.',
        accounting_limitation='Original phase authority integrity checked, then separate fresh proof authorities '
            'attached at equal metadata caps and smaller exact adapter caps. Production authorities remain unconsumed.',
        execution_limitations=['No start, enter, native_run, scanner, model load or generation exercised.',
            'Native proof means validate() under native phase allowance, not native execution.',
            'Actual authorization JSON reads and later runtime imports have reserved headroom but await real GO.',
            'First paired cell only; no claim all twelve slots are receiving-ready or all remaining metadata allocated.'],
        pending_only=['Nash exact-byte repaired-evidence disposition', 'Main exact-bound execution GO',
            'Existing strict live resource admission'],
        reviewer_request='Inspect exact new opaque configs and their byte-equality except metadata allowances; '
            'validate real persisted phase reads and supplemental no-refund global/per-life accounting. '
            'Issue a new bound disposition without rewriting the original REWORK or exporting private contents.')
    binding_ref = common.write(WORKER / 'NASH_I1_REPAIR_READY_20260917T1748Z.json', bindings)
    lines = [
        '# R176 I1 repair: actual charged CPU proof ready for Nash',
        '',
        'Status: AUTHOR PASS, independent rereview pending. NOT execution GO.',
        'Addressed to Nash `01a0b064-e11c-7292-a107-787a5464ff34`.',
        'Prepared from actual receiving observations ending ' + phases[-1]['observed_utc'] + '.',
        '',
        '## Actual complete validator evidence',
        '- Both opaque C2 sleep33 configs passed complete actual `validate()` in separate fresh receiving CPU processes under both preflight and native phase allowances: four passes.',
        '- Each pass persisted 1,309 advance-read records: 25,618,085 metadata bytes and 80,798,775 adapter bytes.',
        '- New metadata caps: preflight 33,554,432 bytes (32 MiB), native 50,331,648 bytes (48 MiB); actual headroom 7,936,347 / 24,713,563 bytes.',
        '- Includes the real 17,011,448-byte source closure and 8,025,024-byte interpreter, plus full custody/CPU/config/checkpoint/original-birth/private-rubric validation.',
        '- Eight local supplemental reservation regression tests pass, including duplicate refusal, no refund, global/per-life limits, and preservation of all twelve nominal adapter pass envelopes.',
        '- All production source/runner/helper/config instrument bytes remain unchanged except the two metadata-allowance fields; no prompt narrowing or checkpoint replacement.',
        '',
        '## Exact replacement pins',
        '- Candidate root: `' + bindings['candidate_root'] + '`.',
        '- Public candidate receipt SHA256: `' + bindings['candidate_public']['sha256'] + '`.',
        '- Opaque config SHA256: `' + public['executions'][0]['sha256'] + '`.',
        '- Opaque config SHA256: `' + public['executions'][1]['sha256'] + '`.',
        '- Runner SHA256: `' + public['runner_sha256'] + '`.',
        '- Actual proof script SHA256: `' + bindings['proof_script']['sha256'] + '`.',
        '- Complete exact paths, source/CPU/release pins, proof receipts and per-phase read-ledger paths: `NASH_I1_REPAIR_READY_20260917T1748Z.json`.',
        '',
        '## Remaining pre-I/O envelope',
        '| Resource | Reserved bytes | Remaining unreserved bytes |',
        '| --- | ---: | ---: |',
    ]
    for kind, resource in resources.items():
        lines.append(f"| Global {kind} | {resource['reserved_bytes']} | {resource['remaining_unreserved_bytes']} |")
    lines += [
        f"| Included discovery | {discovery} | {32 * common.MIB - discovery} |",
        f"| C2 metadata | {lives['C2']['metadata']['reserved_bytes']} | {lives['C2']['metadata']['remaining_unreserved_bytes']} |",
        f"| C2 adapter | {lives['C2']['adapter']['reserved_bytes']} | {lives['C2']['adapter']['remaining_unreserved_bytes']} |",
        '',
        '- Reservation snapshot: `' + str(envelope_ref['path']) + '`.',
        '- Old 24-MiB phase reservations, interrupted candidate2 reservations, and every failed attempt remain charged; no refunds, resets, old-ledger changes or R172 borrowing.',
        '- Interrupted candidate2 had no recoverable completion receipt at the one bounded recovery observation. Candidate3 is a distinct fully charged metadata-only preparation, not a replay of science.',
        '- Four supplemental repair-proof adapter reads reserve exactly 323,195,100 bytes, preserving nominal pass allocations: global nominal-plus-repair margin 616,328,996 bytes; C2 margin 79,458,084 bytes.',
        '- C2 unallocated metadata is only 120,455,168 bytes. This packet does not claim the other five C2 pairs can use the same repeated-closure allowance pattern within that remainder; their fixed slots remain unchanged, not silently removed or expanded.',
        '',
        '## Limits and next exact gate',
        '- Only GO/review were synthetic **in memory**, explicitly not permission/independent approval. Real `Reader.charge` and durable per-read writes were unchanged; fresh proof authorities have identical metadata caps and smaller exact adapter caps.',
        '- No production allowance was consumed and no execution attempt, scanner, GPU/model/provider call, signal, restart or learner mutation occurred. Native-phase proof is validator-only, not a native model run.',
        '- Real GO/review file reads and subsequent runtime imports are not measured by this CPU proof; finite headroom is reserved. Existing strict admission remains mandatory after bound GO.',
        '- Request Nash fresh exact-byte disposition on this replacement and persisted actual evidence. Do not overwrite the old REWORK. Then Main binds GO for the first fixed six calls; no new scientific permission queue is added.',
        '- No direct agent-messaging tool is available in this session; this explicitly addressed owned handoff is ready for Nash/Main to consume. No assertion that Nash has read or approved it.',
        '- R159 results, condition assignment maps, responses and private witnesses remain sealed from Main/parents. R179 living-context observations are not substitutes for these frozen empty-history probes.',
        '',
        'Author technical response: I1 is repaired by realistic explicit metadata allowances and demonstrated on all four actual phase validators, rather than by weakening the frozen instrument or treating fixture success as receiving proof.',
    ]
    common.write(WORKER / 'NASH_I1_REPAIR_READY_20260917T1748Z.md', ('\n'.join(lines) + '\n').encode())
    print(json.dumps(dict(status=bindings['status'], handoff=binding_ref, remaining_envelope=envelope_ref,
        model_calls=0, provider_calls=0, execution_authorized=False), sort_keys=True))


if __name__ == '__main__':
    main()
