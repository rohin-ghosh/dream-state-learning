"""Authenticated saved-boundary continuation for the original P3 journal."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path


KIND = 'R233_P3_RECOVERED_BOUNDARY'


def restored_state(record):
    from organism_v6.orch_r125_continual_stream import digest, require
    require(record['kind'] == 'SLEEP_COMPLETE' and record['sha256'] ==
        digest({key: value for key, value in record.items() if key != 'sha256'}),
        'complete_record_integrity')
    document = record['document']
    saved = document['resume_state']
    require(document['status'] == 'COMPLETE' and saved['sha256'] == digest(saved['state'])
        and saved['state']['pending'] is None
        and saved['state']['sleep_frontier'] == len(saved['state']['rows'])
        and saved['state']['model_state_sha256'] == digest(document['checkpoint_sha256'])
        and document['checkpoint_sha256'] == document['checkpoint']['checkpoint_sha256'],
        'coherent_adapter_optimizer_RNG_working_state')
    return deepcopy(saved)


def activate():
    from gpu import orch_r125_stream_journal as journal_module
    from organism_v6.orch_r125_continual_stream import require
    if getattr(journal_module.StreamJournal, '_r233_p3_recovery', False):
        return journal_module.StreamJournal
    original = journal_module.StreamJournal

    class RecoveryJournal(original):
        _r233_p3_recovery = True

        def _advance(self, state, kind, document):
            if kind != KIND:
                return super()._advance(state, kind, document)
            receipt_path = Path(document['receipt_path'])
            root = Path('/localhome/local-rohing/orch_r201_node4_20260918/node4/R195_FLEET/SCALE_physical3')
            allowed = {root / 'r233_lease_continuation/control': (237705, '27878033'),
                root / 'r233_lease_continuation_retry1/control': (598987, '32509102')}
            require(receipt_path.parent in allowed, 'exact_P3_operator_receipt')
            old_pid, old_ticks = allowed[receipt_path.parent]
            data = receipt_path.read_bytes()
            require(hashlib.sha256(data).hexdigest() == document['receipt_sha256'],
                'immutable_recovery_receipt')
            receipt = json.loads(data)
            require(receipt['old_native_absent'] and receipt['old_native_pid'] == old_pid
                and receipt['old_native_start_ticks'] == old_ticks
                and receipt['journal_id'] == '0727d448bca644bfa64f1a1f65c1f21f'
                and not receipt['uninterrupted_resident_continuity_claimed']
                and state['index'] == receipt['old_head_index'] + 1
                and state['previous'] == receipt['old_head_sha256'], 'exact_P3_preserved_tail')
            complete = json.loads(Path(receipt['complete_path']).read_bytes())
            require(complete['sha256'] == receipt['complete_sha256'], 'selected_completed_checkpoint')
            saved = restored_state(complete)
            require(document['state'] == saved, 'no_saved_state_changes_before_R131_extension')
            state['latest'] = self._checkpoint(saved)
            state['request'] = state['response'] = state['sleep_request'] = None

    journal_module.StreamJournal = RecoveryJournal
    return RecoveryJournal
