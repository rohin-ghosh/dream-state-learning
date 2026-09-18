"""Four separately precharged, fresh receiving CPU processes; zero execution GO."""

import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time

import proof_reservations as supplemental


HERE = Path(__file__).resolve().parent
WORKER = HERE.parents[1]
sys.path.insert(0, str(WORKER))
import preparation_io as common


def main():
    os.umask(0o077)
    common.validate_controls(WORKER)
    root = HERE / 'actual_proof1'
    root.mkdir(mode=0o700, exist_ok=False)
    public_path = HERE / 'attempt2/PUBLIC_METADATA.json'
    public_raw = public_path.read_bytes()
    public = json.loads(public_raw)
    common.require(public['status'] == 'C2_SLEEP33_METADATA_REPAIR_CONFIGS_READY_FOR_ACTUAL_REVIEW'
        and public['runner_bytes_changed'] is False and public['execution_authorized'] is False,
        'new_immutable_metadata_only_candidate')
    review_path = WORKER / 'REVIEW_R179_PUBLIC_BINDINGS.json'
    authority = common.write(root / 'SUPPLEMENTAL_REPAIR_AUTHORITY.json', dict(
        scope_sha256=common.SCOPE_SHA, purpose=supplemental.PURPOSE, execution_authorized=False,
        adapter_bytes_per_proof=supplemental.ADAPTER_BYTES, max_proofs=4,
        execution_sha256s=[entry['sha256'] for entry in public['executions']],
        source_review=dict(path=str(review_path), sha256=common.sha(review_path.read_bytes())),
        user_directive_verbatim='Please repair immediately within existing2GiBmetadata/overallR176budgets, '
            'newappendonlycandidate + explicitlyreservedfinite phaseallowances using realclosure/interpreter sizes; '
            'no refunds/resets/noR172borrowing/no narrowingprobes. Exercise completeactualvalidate+readcharging '
            'perphase (notonlyfixtures) before re-review.',
        declaration='Four additional receiving CPU verification reads, not nominal phase reuse or execution permission',
        original_twelve_checkpoint_nominal_pass_envelopes_preserved=True, recorded_unix=time.time()))
    ledger_root = WORKER / 'preparation1/global_ledger'
    ledger = common.Ledger(ledger_root)
    script_path = HERE / 'actual_validate_proof.py'
    script = script_path.read_bytes()
    requests = []
    for execution in public['executions']:
        for phase, cap in (('preflight', 32), ('native', 48)):
            operation = execution['sha256'] + '_' + phase
            adapter = supplemental.reserve(ledger_root, authority, execution['sha256'], phase)
            metadata = ledger.reserve('C2_I1_proof1_' + operation + '_metadata', 'C2', 'metadata', cap * common.MIB)
            bootstrap = ledger.reserve('C2_I1_proof1_' + operation + '_bootstrap', 'C2', 'metadata', common.MIB)
            storage = ledger.reserve('C2_I1_proof1_' + operation + '_storage', '_campaign', 'storage', 2 * common.MIB)
            request = dict(execution=execution, phase=phase,
                proof_root=str(common.REMOTE / 'metadata_repair_actual_proof1' / operation),
                candidate_public=dict(path=str(common.REMOTE / 'runner_candidate3_metadata_repair2/PUBLIC_METADATA.json'),
                    sha256=common.sha(public_raw)), proof_allowances=dict(metadata=metadata, adapter=adapter),
                bootstrap=bootstrap, storage=storage, proof_script_sha256=common.sha(script),
                execution_authorized=False, model_calls=0, provider_calls=0, staging_charge_bytes=0)
            for iteration in range(4):
                size = len(common.canonical(request)) + len(script)
                if size == request['staging_charge_bytes']:
                    break
                request['staging_charge_bytes'] = size
            common.require(request['staging_charge_bytes'] == len(common.canonical(request)) + len(script),
                'exact_staging_size_fixed_point')
            common.write(root / (operation + '.REQUEST.json'), request)
            requests.append(request)
    common.write(root / 'PRE_IO_MANIFEST.json', dict(requests=requests, recorded_unix=time.time(),
        script_sha256=common.sha(script), model_calls=0, provider_calls=0, execution_authorized=False))
    command = "CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 "
    command += '/localhome/local-rohing/v2/venv/bin/python -B -c ' + shlex.quote(script.decode())
    receipts = []
    for request in requests:
        operation = request['execution']['sha256'] + '_' + request['phase']
        payload = common.canonical(request)
        common.require(len(payload) < 512 * 1024, 'finite_bootstrap_request')
        common.write(root / (operation + '.STAGING_CHARGE.json'), dict(
            bytes=request['staging_charge_bytes'], allowance=request['bootstrap']['reference'],
            status='CHARGED_BEFORE_TRANSMISSION_NO_REFUND'))
        try:
            result = subprocess.run(['bash', str(WORKER.parents[2] / 'gpu/ovx_ssh.sh'), command],
                input=payload, capture_output=True, timeout=90)
            receipt = json.loads(result.stdout) if result.stdout.strip() else dict(
                status='CPU_PROOF_NO_TERMINAL_PRESERVED_NO_RETRY', returncode=result.returncode,
                stderr_bytes=len(result.stderr), stderr_sha256=common.sha(result.stderr))
        except subprocess.TimeoutExpired:
            receipt = dict(status='CPU_PROOF_TIMEOUT_PRESERVED_NO_RETRY')
        reference = common.write(root / (operation + '.PUBLIC_METADATA.json'), receipt)
        receipts.append(dict(reference=reference, status=receipt['status'], execution=request['execution'], phase=request['phase']))
        print(json.dumps(dict(status=receipt['status'], execution_sha256=request['execution']['sha256'],
            phase=request['phase'], charged_bytes=receipt.get('phase_charge_counters_bytes'),
            reason=receipt.get('reason'), error_type=receipt.get('error_type')), sort_keys=True), flush=True)
    common.write(root / 'PUBLIC_METADATA.json', dict(status='ALL_FOUR_COMPLETE_ACTUAL_VALIDATOR_PROOFS_PASS'
        if all(receipt['status'] == 'COMPLETE_ACTUAL_VALIDATOR_PASS' for receipt in receipts)
        else 'ACTUAL_VALIDATOR_PROOF_FAILURE_PRESERVED_NO_RETRY', receipts=receipts,
        observed_unix=time.time(), proof_script_sha256=common.sha(script),
        model_calls=0, provider_calls=0, execution_authorized=False))


if __name__ == '__main__':
    main()
