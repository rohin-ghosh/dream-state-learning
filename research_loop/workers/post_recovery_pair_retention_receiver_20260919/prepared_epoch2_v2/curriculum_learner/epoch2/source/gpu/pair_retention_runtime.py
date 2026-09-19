"""Receiving-source port: exact saved-state journal open, no historical body replay."""

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def bind_journal(base, plan):
    from gpu.checkpoint_tail_runtime import scan, validate_selection

    control = Path(plan['source_root']).parent / 'control'
    preservation = json.loads((control / 'PRESERVATION.json').read_bytes())
    token = json.loads((control / 'RETENTION_HANDOFF.json').read_bytes())
    require(token['sha256'] == digest({key: value for key, value in token.items() if key != 'sha256'})
        and token['old_native_exited'] is True, 'exact_exited_source_epoch_token')
    receiver = token['receiver']
    require(receiver['plan'] == plan and receiver['plan_sha256'] == digest(plan)
        and token['deadline_unix'] == plan['hard_end_unix'], 'same_receiving_plan_and_deadline')
    require(hashlib.sha256((control / 'PRESERVATION.json').read_bytes()).hexdigest()
        == receiver['preservation_sha256'], 'exact_receiving_preservation_bytes')
    boundary = token['exact_complete']
    require(preservation['checkpoint'] == boundary['checkpoint']
        and preservation['coherent_state'] == boundary['resume_state'], 'same_model_optimizer_rng_and_working_state')
    selection = validate_selection(preservation['checkpoint_tail_selection'],
        receiver['same_journal_root'], plan['think_act_learn']['trial_id'])
    require(selection['complete_index'] == boundary['complete_index']
        and selection['complete_sha256'] == boundary['complete_sha256'], 'exact_source_epoch_complete_anchor')

    class RetentionJournal(base):
        def _scan(self):
            if getattr(self, '_retention_full_audit', False):
                return super()._scan()
            self._ensure_open()
            require(not any(name.endswith('.partial') for name in os.listdir(self._root_fd)),
                'incomplete_journal_initialization')
            require(self._read_json(self._root_fd, 'JOURNAL.json') == self._manifest, 'journal_manifest_changed')
            return scan(self, selection)

        def audit(self):
            with self._mutex:
                self._retention_full_audit = True
                try:
                    return super().audit()
                finally:
                    self._retention_full_audit = False

        def __init__(self, root, *, create=False):
            require(create is False and Path(root).absolute() == Path(selection['root']), 'same_journal_resume_only')
            super().__init__(root, create=False)
            try:
                state = self._state
                require(all(state[key] is None for key in ('request', 'response', 'sleep_request'))
                    and state['latest']['expected_sha256'] == boundary['resume_state']['sha256'],
                    'exact_resolved_saved_state_before_model_load')
                learned = []
                for index in range(selection['complete_index'] + 1, state['index']):
                    record = self._read_json(self._records_fd, f'{index:020d}.json')
                    require(record['kind'] in ('INBOX', 'R184_LEARN_COMPLETE'), 'no_intervening_work_before_source_epoch')
                    if record['kind'] == 'R184_LEARN_COMPLETE':
                        learned.append(record)
                require(len(learned) == 1 and learned[0]['sha256'] == boundary['learn_sha256'], 'same_driver_completion')
                self.record('RETENTION_SOURCE_ADOPTED', dict(schema='RETENTION_SOURCE_ADOPTION_V1',
                    epoch_id=token['epoch_id'], handoff_sha256=token['sha256'],
                    source_pins_sha256=digest(token['new_source_pins']),
                    complete_index=selection['complete_index'], complete_sha256=selection['complete_sha256'],
                    state_sha256=boundary['resume_state']['sha256'], deadline_unix=plan['hard_end_unix'],
                    wall_extended=False, historical_rows_changed=False))
            except BaseException:
                self.close()
                raise

    return RetentionJournal
