"""Caption-only explicit COMPLETE restore using the original RecoveryJournal rules."""

from pathlib import Path


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def verify_startup(journal, selection, deadline):
    from gpu.orch_r125_stream_journal import _digest
    from organism_v6.orch_r124_train_history import WORKING_STATE_SCHEMA
    state = journal._state
    anchor = journal._read_json(journal._records_fd, f'{selection["complete_index"]:020d}.json')
    saved = anchor['document']['resume_state']
    require(all(state[key] is None for key in ('request', 'response', 'sleep_request'))
        and state['latest']['document'] == saved and saved['state']['pending'] is None
        and saved['state']['deadline_unix'] == deadline, 'caption_exact_resolved_state_same_deadline')
    learned = []
    for index in range(selection['complete_index'] + 1, state['index']):
        record = journal._read_json(journal._records_fd, f'{index:020d}.json')
        require(record['kind'] in ('INBOX', 'R184_LEARN_COMPLETE'), 'caption_no_intervening_work')
        if record['kind'] == 'R184_LEARN_COMPLETE':
            learned.append(record['document'])
    require(len(learned) == 1, 'caption_one_durable_LEARN')
    learn = learned[0]
    checkpoint_working = saved['state']['history'].get('working_state',
        dict(schema=WORKING_STATE_SCHEMA, revision=0, entries=[]))
    active_working = {key: checkpoint_working[key] for key in ('schema', 'revision', 'entries')}
    require(learn['cycle'] == anchor['document']['cycle'] == len(saved['state']['sleep_receipts'])
        and learn['checkpoint'] == anchor['document']['checkpoint']
        and learn['working_state'] == active_working
        and learn['state_revision'] == learn['working_state']['revision']
        and saved['state']['model_state_sha256'] == _digest(learn['checkpoint']['checkpoint_sha256']),
        'caption_LEARN_COMPLETE_checkpoint_working_state_binding')


def journal_class(base, selection, deadline):
    from gpu.checkpoint_tail_runtime import scan

    class CaptionTailJournal(base):
        def _scan(self):
            if getattr(self, '_caption_full_audit', False):
                return super()._scan()
            return scan(self, selection)

        def audit(self):
            with self._mutex:
                self._caption_full_audit = True
                try:
                    return super().audit()
                finally:
                    self._caption_full_audit = False

        def __init__(self, root, *, create=False):
            require(create is False and Path(root).absolute() == Path(selection['root']),
                'caption_original_journal_resume_only')
            super().__init__(root, create=False)
            try:
                verify_startup(self, selection, deadline)
            except BaseException:
                self.close()
                raise

    return CaptionTailJournal


def bind_journal(base, plan):
    selection = plan.get('checkpoint_tail_recovery')
    if selection is None:
        return base
    from gpu.checkpoint_tail_runtime import validate_selection
    from gpu.r213_recovery_runtime import RecoveryJournal
    require(base is RecoveryJournal and plan['physical'] == 2
        and plan['gpu_uuid'] == 'GPU-d2db2a6a-a308-1782-bf41-e41411d8dc05'
        and Path(plan['source_root']).parent.name == 'r213_r226_caption_unparented_fork'
        and plan['think_act_learn']['trial_id'] == 'R226_CAPTION_UNPARENTED', 'caption_only_original_recovery_family')
    require('authorized_wall_extension' not in plan, 'caption_consumed_wall_authorization_must_be_removed')
    selection = validate_selection(selection, Path(plan['root']) / 'stream', 'R226_CAPTION_UNPARENTED')
    require(selection['persist_complete_anchors'] is False, 'caption_no_new_anchor_writes')
    return journal_class(base, selection, plan['hard_end_unix'])
