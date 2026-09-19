"""New-source-only C2 entry seam: adopt a source epoch under the original writer lock."""

import hashlib
import json
from pathlib import Path


def digest(document):
    return hashlib.sha256(json.dumps(document, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def bind_journal(base, plan):
    require(plan['hard_end_unix'] == 1789927200 and plan['physical'] == 1
        and plan['gpu_uuid'] == 'GPU-7fc4e5b2-060c-ada8-8f91-3fe262c3573c'
        and plan['think_act_learn']['trial_id'] == 'C2_R216_current_conversation_maintenance'
        and 'authorized_wall_extension' not in plan, 'same_learned_C2_no_reapplied_wall_authorization')
    control = Path(plan['source_root']).parent / 'control'
    token = json.loads((control / 'RETENTION_HANDOFF.json').read_bytes())
    require(token['schema'] == 'RETENTION_HANDOFF_TOKEN_V1'
        and token['sha256'] == digest({key: value for key, value in token.items() if key != 'sha256'})
        and token['old_native_exited'] is True and token['deadline_unix'] == plan['hard_end_unix']
        and token['no_cold_start'] is True and token['no_unresolved_work_replayed'] is True
        and token['epoch_record_required_before_first_THINK'] is True, 'exact_exited_C2_handoff_token')
    receiver, candidate = token['receiver'], token['exact_complete']
    require(receiver['plan'] == plan and receiver['plan_sha256'] == digest(plan)
        and receiver['source_epoch'] == token['epoch_id']
        and receiver['dispatcher_module'] == 'gpu.r188_node5_confinement'
        and receiver['same_journal_root'] == str(Path(plan['root']) / 'stream'), 'same_receiving_C2_plan_root_epoch')
    selection = plan['checkpoint_tail_recovery']
    require(selection['root'] == receiver['same_journal_root']
        and selection['journal_id'] == candidate['journal_id']
        and selection['complete_index'] == candidate['complete_index']
        and selection['complete_sha256'] == candidate['complete_sha256']
        and selection['persist_complete_anchors'] is True, 'exact_C2_complete_anchor_persistent_reader')
    source = Path(plan['source_root'])
    require(source.resolve() == source and all((source / name).resolve() == source / name
        and not Path(name).is_absolute() and '..' not in Path(name).parts for name in token['new_source_pins']),
        'literal_receiving_source_files')
    actual = {str(path.relative_to(source)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in source.rglob('*.py')}
    require(actual == token['new_source_pins'], 'exact_adopted_receiving_source_closure')

    class RetentionJournal(base):
        def __init__(self, root, *, create=False, checkpoint_tail=None):
            require(create is False and Path(root).absolute() == Path(selection['root'])
                and checkpoint_tail == selection, 'same_original_C2_journal_resume_only')
            super().__init__(root, create=False, checkpoint_tail=checkpoint_tail)
            try:
                state = self._state
                require(all(state[key] is None for key in ('request', 'response', 'sleep_request'))
                    and state['latest']['expected_sha256'] == candidate['resume_state']['sha256'],
                    'exact_resolved_C2_saved_state_before_model_load')
                prior = {record['index']: record['sha256'] for record in candidate['records']}
                learned = []
                for index in range(selection['complete_index'] + 1, state['index']):
                    record = self._read_json(self._records_fd, f'{index:020d}.json')
                    require(record['kind'] in ('INBOX', 'R184_LEARN_COMPLETE'), 'no_work_before_C2_source_adoption')
                    if index in prior:
                        require(record['sha256'] == prior[index], 'same_C2_selected_tail_records')
                    if record['kind'] == 'R184_LEARN_COMPLETE':
                        learned.append(record)
                require(state['index'] > candidate['head_index']
                    and len(learned) == 1 and learned[0]['index'] == candidate['learn_index']
                    and learned[0]['sha256'] == candidate['learn_sha256'], 'same_C2_driver_LEARN_completion')
                for path, entry in candidate['mailbox'].items():
                    mailbox = Path(path)
                    require(mailbox.parent == Path(root) / 'inbox' and mailbox.resolve() == mailbox
                        and hashlib.sha256(mailbox.read_bytes()).hexdigest() == entry['sha256'],
                        'preserve_C2_original_parent_mailbox_bytes')
                self.record('RETENTION_SOURCE_ADOPTED', dict(schema='RETENTION_SOURCE_ADOPTION_V1',
                    epoch_id=token['epoch_id'], handoff_sha256=token['sha256'],
                    source_pins_sha256=digest(token['new_source_pins']), complete_index=selection['complete_index'],
                    complete_sha256=selection['complete_sha256'], state_sha256=candidate['resume_state']['sha256'],
                    deadline_unix=plan['hard_end_unix'], wall_extended=False, historical_rows_changed=False))
            except BaseException:
                self.close()
                raise

    return RetentionJournal
