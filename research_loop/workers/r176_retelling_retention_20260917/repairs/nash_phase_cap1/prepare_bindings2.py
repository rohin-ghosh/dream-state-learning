"""Distinct config repair after attempt1 had no recoverable completion receipt."""

import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time

import prepare_bindings as previous


HERE = Path(__file__).resolve().parent
WORKER = HERE.parents[1]
sys.path.insert(0, str(WORKER))
import preparation_io as common


def main():
    os.umask(0o077)
    common.validate_controls(WORKER)
    recovered = json.loads((HERE / 'recovery_observation1/PUBLIC_METADATA.json').read_bytes())
    common.require(recovered['status'] == 'CANDIDATE_PUBLIC_RECEIPT_ABSENT', 'distinct_missing_completion_repair')
    root = HERE / 'attempt2'
    root.mkdir(mode=0o700, exist_ok=False)
    ledger = common.Ledger(WORKER / 'preparation1/global_ledger')
    allowances = {}
    for condition, prefix in (('LORA_ON', 'ON'), ('LORA_OFF', 'OFF')):
        allowances[condition] = {}
        for phase, amount in (('preflight', 32), ('native', 48)):
            allowances[condition][phase] = ledger.reserve(
                f'C2_sleep33_{prefix}_{phase}_metadata_repair2', 'C2', 'metadata', amount * common.MIB)
    reads = ledger.reserve('C2_metadata_repair2_config_read_stage', 'C2', 'metadata', common.MIB, discovery=True)
    storage = ledger.reserve('C2_metadata_repair2_control_storage', '_campaign', 'storage', common.MIB)
    public_path = WORKER / 'preparation1/narrow_runner1/PUBLIC_METADATA.json'
    review_path = WORKER / 'REVIEW_R179_PUBLIC_BINDINGS.json'
    request = dict(scope_sha256=common.SCOPE_SHA,
        original_public_receipt=dict(path=str(common.REMOTE / 'runner_candidate1/PUBLIC_METADATA.json'),
            sha256=common.sha(public_path.read_bytes())),
        Nash_rework=dict(path=str(review_path), sha256=common.sha(review_path.read_bytes())),
        new_metadata_allowances=allowances, metadata_read_allowance=reads, storage_allowance=storage,
        model_calls=0, provider_calls=0, execution_authorized=False, recorded_unix=time.time(),
        previous_attempt_preserved=True, previous_recovery=recovered)
    common.write(root / 'REQUEST.json', request)
    remote = previous.REMOTE.replace('runner_candidate2_metadata_repair1', 'runner_candidate3_metadata_repair2')
    remote = remote.replace('metadata_repair1:', 'metadata_repair2:')
    try:
        result = subprocess.run(['bash', str(WORKER.parents[2] / 'gpu/ovx_ssh.sh'),
            'python3 -c ' + shlex.quote(remote)], input=common.canonical(request),
            capture_output=True, timeout=90)
        receipt = json.loads(result.stdout) if result.returncode == 0 else dict(
            status='DISTINCT_METADATA_REPAIR_FAILED_PRESERVED_NO_RETRY', returncode=result.returncode,
            stderr_bytes=len(result.stderr), stderr_sha256=common.sha(result.stderr))
    except subprocess.TimeoutExpired:
        receipt = dict(status='DISTINCT_METADATA_REPAIR_TIMED_OUT_NO_RETRY')
    common.write(root / 'PUBLIC_METADATA.json', receipt)
    print(json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    main()
