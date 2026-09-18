"""Supplemental, exact-size I1 CPU proofs; nominal execution passes stay reserved."""

import json
from pathlib import Path
import sys
import time


WORKER = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WORKER))
import preparation_io as common


ADAPTER_BYTES = 80798775
PURPOSE = 'R179_I1_FOUR_COMPLETE_ACTUAL_VALIDATOR_CPU_PROOFS'


def reserve(root, authority, execution_sha, phase):
    common.require(time.time() < common.END, 'preparation_window_ended')
    raw = Path(authority['path']).read_bytes()
    common.require(common.sha(raw) == authority['sha256'], 'exact_supplemental_authority')
    document = json.loads(raw)
    common.require(document['scope_sha256'] == common.SCOPE_SHA and document['purpose'] == PURPOSE
        and document['execution_authorized'] is False and document['adapter_bytes_per_proof'] == ADAPTER_BYTES
        and document['max_proofs'] == 4 and len(set(document['execution_sha256s'])) == 2
        and execution_sha in document['execution_sha256s'] and phase in ('preflight', 'native'),
        'exact_fixed_pair_four_CPU_proofs')
    operation = 'C2_sleep33_I1_proof1_' + execution_sha + '_' + phase
    root = Path(root)
    with common.lock(root / 'ledger.lock'):
        rows = [json.loads(path.read_bytes()) for path in (root / 'reservations').glob('*.json')]
        common.require(all(row['status'] == 'PRECHARGED_NO_REFUND' and row['scope_sha256'] == common.SCOPE_SHA
            for row in rows), 'persistent_authority_integrity')
        common.require(not any(row['operation'] == operation for row in rows), 'attempt_consumed_no_retry')
        supplemental = [row for row in rows if row.get('supplemental_repair_authority')]
        common.require(len(supplemental) < 4 and all(row['supplemental_repair_authority'] == authority
            for row in supplemental), 'one_explicit_four_proof_scope')
        adapter_rows = [row for row in rows if row['kind'] == 'adapter']
        repairs = [row for row in adapter_rows if row.get('repair_authority')
            or row.get('supplemental_repair_authority')]
        common.require(sum(row['bytes'] for row in adapter_rows) + ADAPTER_BYTES <= 16 * common.GIB,
            'global_resource_cap')
        common.require(sum(row['bytes'] for row in adapter_rows if row['life_id'] == 'C2')
            + ADAPTER_BYTES <= 8 * common.GIB, 'per_life_kind_cap')
        common.require(15 * common.GIB + sum(row['bytes'] for row in repairs) + ADAPTER_BYTES <= 16 * common.GIB
            and 7680 * common.MIB + sum(row['bytes'] for row in repairs if row['life_id'] == 'C2')
            + ADAPTER_BYTES <= 8 * common.GIB, 'preserve_all_nominal_twelve_checkpoint_passes')
        reservation = dict(status='PRECHARGED_NO_REFUND', operation=operation, life_id='C2', kind='adapter',
            bytes=ADAPTER_BYTES, discovery=False, sleep=33, read_pass='SUPPLEMENTAL_R179_I1_CPU_VALIDATION',
            scope_sha256=common.SCOPE_SHA, reserved_unix=time.time(), supplemental_repair_authority=authority,
            execution_sha256=execution_sha, phase=phase, model_calls=0, provider_calls=0)
        reference = common.write(root / 'reservations' / (common.sha(operation.encode()) + '.json'), reservation)
        return dict(document=reservation, reference=reference)
