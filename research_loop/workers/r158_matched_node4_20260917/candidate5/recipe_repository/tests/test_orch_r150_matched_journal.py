"""Matched CPU state transitions retain the original journal's custody rules."""

from copy import deepcopy
from functools import partial
import json
from pathlib import Path
import shutil
from unittest.mock import Mock, patch

import pytest

from gpu.orch_r125_stream_journal import StreamJournal
from gpu.orch_r150_matched_journal import MatchedJournal
from organism_v6.orch_r125_continual_stream import digest
from organism_v6.orch_r150_matched_stream import MODES
from test_orch_r150_matched_stream import COHORT, FakeChild, boundary, event, make_stream, model_checkpoint, restore, step


def journal_for(tmp_path, arm='parented_frozen'):
    return MatchedJournal(tmp_path / arm, arm=arm, cohort_sha256=COHORT, create=True)


def record_birth(journal, stream):
    journal.record('COMMITTED', dict(kind='BIRTH', state=stream.checkpoint()))


def saved_bytes(root):
    return {path.relative_to(root): path.read_bytes() for path in root.rglob('*') if path.is_file()}


def test_append_chain_custody_and_request_transitions_are_inherited_verbatim():
    for name in ('record', '_scan', '_publish', '_read_bytes', '_intent', '_validate_entry',
                 'read_inbox', 'latest_checkpoint', 'close', '_unchanged'):
        assert getattr(MatchedJournal, name) is getattr(StreamJournal, name)


@pytest.mark.parametrize('arm', MODES)
def test_common_native_prepare_finish_and_journal_reopen(tmp_path, arm):
    stream = make_stream(arm)
    child = FakeChild(arm)
    with journal_for(tmp_path, arm) as journal:
        record_birth(journal, stream)
        initial = journal.latest_checkpoint()
        assert initial['document'] == stream.checkpoint()
        for cycle in (1, 2):
            step(stream, child, journal.record)
            step(stream, child, journal.record)
            boundary(stream, child, journal, tmp_path, cycle)
            assert journal.latest_checkpoint()['document'] == stream.checkpoint()
            stream = restore(stream)
        root = journal.root
        records = [json.loads(path.read_text()) for path in sorted((root / 'records').glob('*.json'))
            if not path.name.endswith('.intent.json')]
        assert len([record for record in records if record['kind'] == 'SLEEP_REQUEST']) == 2
        assert len([record for record in records if record['kind'] == 'SLEEP_COMPLETE']) == 2
        assert len([record for record in records if record['kind'] == 'COMPACTION']) == 2
        assert stream.sleep_frontier == len(stream.rows) == 6
    with MatchedJournal(root, arm=arm, cohort_sha256=COHORT) as reopened:
        assert reopened.latest_checkpoint()['document'] == stream.checkpoint()
    with pytest.raises(ValueError, match='known_stream_schema'):
        StreamJournal(root)


@pytest.mark.parametrize('kind', ['UPDATE', 'TARGET_ELIGIBILITY'])
def test_frozen_journal_rejects_training_records_without_appending(tmp_path, kind):
    with journal_for(tmp_path) as journal:
        record_birth(journal, make_stream())
        before = saved_bytes(journal.root)
        with pytest.raises(ValueError, match='frozen_journal_no_training'):
            journal.record(kind, dict(optimizer_step=1))
        assert saved_bytes(journal.root) == before


@pytest.mark.parametrize('change', ['arm', 'cohort'])
def test_wrong_arm_or_cohort_reopen_refused_without_modifying_files(tmp_path, change):
    with journal_for(tmp_path) as journal:
        record_birth(journal, make_stream())
        root = journal.root
    before = saved_bytes(root)
    with pytest.raises(ValueError, match='resume_matched_policy_mismatch'):
        MatchedJournal(root, arm='parented_learning' if change == 'arm' else 'parented_frozen',
            cohort_sha256='d' * 64 if change == 'cohort' else COHORT)
    assert saved_bytes(root) == before


def test_frozen_completion_checks_outstanding_request_and_cycle(tmp_path):
    stream = make_stream()
    with journal_for(tmp_path) as journal:
        record_birth(journal, stream)
        step(stream, record=journal.record)
        pending = stream.checkpoint()
        pending['state']['pending'] = 'sleep:' + digest([row['source_sha256'] for row in stream.pending_rows()])
        pending['sha256'] = digest(pending['state'])
        journal.record('SLEEP_REQUEST', dict(cycle=1, resume_state=pending))
        before = saved_bytes(journal.root)
        with pytest.raises(ValueError, match='sleep_cycle_binding'):
            stream.commit_sleep(stream.frozen_boundary_receipt(model_checkpoint(), frozen_base_verified=True, cycle=2),
                journal.record)
        assert saved_bytes(journal.root) == before
        root = journal.root
    with MatchedJournal(root, arm=stream.arm, cohort_sha256=COHORT) as reopened:
        assert reopened.latest_checkpoint()['document'] == pending


def test_sleep_cannot_bypass_unresolved_generation(tmp_path):
    stream = make_stream()
    with journal_for(tmp_path) as journal:
        record_birth(journal, stream)
        step(stream, record=journal.record)
        valid = stream.frozen_boundary_receipt(model_checkpoint(), frozen_base_verified=True)
        completed = restore(stream)
        completed.commit_sleep(valid, Mock())
        with pytest.raises(RuntimeError, match='interrupted generation'):
            stream.step(Mock(side_effect=RuntimeError('interrupted generation')), lambda messages: 10,
                journal.record, now=lambda: 100)
        before = saved_bytes(journal.root)
        with pytest.raises(ValueError, match='sleep_cannot_bypass_request'):
            journal.record('SLEEP_COMPLETE', dict(valid, resume_state=completed.checkpoint()))
        assert saved_bytes(journal.root) == before


def test_unparented_inbox_parent_rejection_keeps_environment_and_raw_bytes_unregistered(tmp_path):
    stream = make_stream('unparented_learning')
    with journal_for(tmp_path, stream.arm) as journal:
        record_birth(journal, stream)
        environment = dict(schema='R127_ATTRIBUTED_INBOX_V1', id='environment', actor='environment', split='TRAIN',
            text='Actual tool observation.', speaker='Tool', source_receipt=dict(path='/fixture/tool.json', sha256='e' * 64))
        (journal.inbox / 'a-environment.json').write_text(json.dumps(environment))
        parent_path = journal.inbox / 'b-parent.json'
        parent_path.write_text(json.dumps(dict(id='parent', actor='parent', split='TRAIN', text='Parent-only input.')))
        before = saved_bytes(journal.root)
        with pytest.raises(ValueError, match='unparented_parent_channel_forbidden'):
            journal.read_inbox()
        assert saved_bytes(journal.root) == before
        assert journal.latest_checkpoint()['document'] == stream.checkpoint()
        parent_path.rename(journal.inbox / 'b-parent.quarantined')
        incoming = journal.read_inbox()
        assert len(incoming) == 1 and incoming[0].actor == 'environment'
        step(stream, record=journal.record, incoming=incoming)
        assert stream.history.events[0].text == 'Tool: Actual tool observation.'
        assert 'Parent-only' not in str(stream.checkpoint())


@pytest.mark.parametrize('response', [dict(raw='raw preserved but missing tokens'), 'not an object'])
def test_invalid_raw_response_is_preserved_and_not_redispatched(tmp_path, response):
    stream = make_stream()
    with journal_for(tmp_path) as journal:
        record_birth(journal, stream)
        with pytest.raises(ValueError):
            stream.step(Mock(return_value=response), lambda messages: 10, journal.record, now=lambda: 100)
        pending = journal.latest_checkpoint()
        root = journal.root
        records = sorted(path for path in (root / 'records').glob('*.json') if not path.name.endswith('.intent.json'))
        assert json.loads(records[-1].read_text())['document']['response'] == response
    before = saved_bytes(root)
    with MatchedJournal(root, arm=stream.arm, cohort_sha256=COHORT) as reopened:
        assert reopened.latest_checkpoint() == pending
        resumed = restore(stream, pending['document'])
        generate = Mock()
        with pytest.raises(ValueError, match='unresolved_request_never_redispatched'):
            resumed.step(generate, lambda messages: 10, reopened.record, now=lambda: 100)
        generate.assert_not_called()
    assert saved_bytes(root) == before


def test_failed_sleep_publish_preserves_intent_tail_and_refuses_reopen(tmp_path):
    stream = make_stream()
    with journal_for(tmp_path) as journal:
        record_birth(journal, stream)
        step(stream, record=journal.record)
        receipt = stream.frozen_boundary_receipt(model_checkpoint(), frozen_base_verified=True)
        root = journal.root
        original = journal._publish

        def fail_record(directory, name, document):
            if name.endswith('.intent.json'):
                return original(directory, name, document)
            raise OSError('fixture interrupted publish')

        with patch.object(journal, '_publish', side_effect=fail_record):
            with pytest.raises(OSError, match='interrupted publish'):
                stream.commit_sleep(receipt, journal.record)
        assert stream.pending == 'sleep:' + digest(receipt)
        assert len(list((root / 'records').glob('*.intent.json'))) == 5
    before = saved_bytes(root)
    with pytest.raises(ValueError, match='incomplete_journal_tail'):
        MatchedJournal(root, arm=stream.arm, cohort_sha256=COHORT)
    assert saved_bytes(root) == before


def test_corrupted_chain_and_second_writer_are_not_repaired(tmp_path):
    with journal_for(tmp_path) as journal:
        record_birth(journal, make_stream())
        root = journal.root
        with pytest.raises(BlockingIOError):
            MatchedJournal(root, arm='parented_frozen', cohort_sha256=COHORT)
    path = root / 'records' / '00000000000000000000.json'
    document = json.loads(path.read_text())
    document['previous_sha256'] = 'd' * 64
    path.write_text(json.dumps(document))
    before = saved_bytes(root)
    with pytest.raises(ValueError, match='journal_chain_integrity'):
        MatchedJournal(root, arm='parented_frozen', cohort_sha256=COHORT)
    assert saved_bytes(root) == before


@pytest.mark.parametrize('mutation', ['context_limit', 'initial_checkpoint', 'rows', 'history'])
def test_frozen_boundary_cannot_smuggle_unrelated_state_changes(tmp_path, mutation):
    stream = make_stream()
    with journal_for(tmp_path) as journal:
        record_birth(journal, stream)
        step(stream, record=journal.record)
        receipt = stream.frozen_boundary_receipt(model_checkpoint(), frozen_base_verified=True)
        completed = restore(stream)
        completed.commit_sleep(receipt, Mock())
        document = completed.checkpoint()
        if mutation == 'context_limit':
            document['state']['context_limit'] += 1
        elif mutation == 'initial_checkpoint':
            document['state']['initial_checkpoint']['extra_note'] = 'replacement clone'
        elif mutation == 'rows':
            document['state']['rows'][0]['target'] = 'forged target'
        else:
            history = deepcopy(completed.history)
            history.append(event('extra'))
            document['state']['history'] = history.checkpoint()
        document['sha256'] = digest(document['state'])
        before = saved_bytes(journal.root)
        with pytest.raises(ValueError, match='unexpected_stream_state_transition'):
            journal.record('SLEEP_COMPLETE', dict(receipt, resume_state=document))
        assert saved_bytes(journal.root) == before


class RelocatedMatchedJournal(MatchedJournal):
    def __init__(self, root, *, original_root, arm, cohort_sha256):
        self._receipt_inbox = Path(original_root) / 'inbox'
        super().__init__(root, arm=arm, cohort_sha256=cohort_sha256)

    def _inbox_event(self, message, path, source_sha256):
        return self._inbox_event_at(message, path, source_sha256, inbox=self._receipt_inbox)


def saved_journal(tmp_path, arm, relocated):
    stream = make_stream(arm)
    with journal_for(tmp_path, arm) as journal:
        record_birth(journal, stream)
        original_root = journal.root
    if relocated:
        snapshot = tmp_path / 'snapshot'
        shutil.copytree(original_root, snapshot)
        reopen = partial(RelocatedMatchedJournal, snapshot, original_root=original_root,
                         arm=arm, cohort_sha256=COHORT)
    else:
        reopen = partial(MatchedJournal, original_root, arm=arm, cohort_sha256=COHORT)
    return stream, reopen


@pytest.mark.parametrize('arm', MODES)
@pytest.mark.parametrize('relocated', [False, True])
@pytest.mark.parametrize('change', ['system_prompt', 'birth_prompt', 'context_limit', 'both', 'unchanged'])
def test_configuration_transitions_reject_presentation_before_publication(tmp_path, arm, relocated, change):
    stream, reopen = saved_journal(tmp_path, arm, relocated)
    original = stream.checkpoint()
    presentation = deepcopy(stream.presentation)
    context_limit = stream.context_limit
    if change in ('system_prompt', 'both'):
        presentation['system_prompt'] = 'DIFFERENT-SYSTEM-PROMPT'
    if change == 'birth_prompt':
        presentation['birth_prompt'] = 'DIFFERENT-BIRTH-PROMPT'
    if change in ('context_limit', 'both'):
        context_limit = 32768
    stream.set_presentation(presentation, context_limit)
    proposal = dict(state=stream.checkpoint())
    before = saved_bytes(tmp_path)
    with reopen() as journal:
        assert journal.latest_checkpoint()['document'] == original
        with patch.object(journal, '_publish') as publish:
            with pytest.raises(ValueError, match='matched_common_configuration_frozen'):
                journal.record('PRESENTATION', proposal)
            publish.assert_not_called()
    assert saved_bytes(tmp_path) == before
    with reopen() as journal:
        assert journal.latest_checkpoint()['document'] == original
    assert saved_bytes(tmp_path) == before


@pytest.mark.parametrize('arm', MODES)
@pytest.mark.parametrize('relocated', [False, True])
@pytest.mark.parametrize('kind', ['WALL_EXTENSION', 'WALL_EXTENDED'])
def test_configuration_transitions_reject_wall_extension_before_publication(tmp_path, arm, relocated, kind):
    from gpu.orch_r125_stream_journal import WALL_EXTENSION_SCHEMA

    stream, reopen = saved_journal(tmp_path, arm, relocated)
    child = FakeChild(arm)
    with reopen() as journal:
        step(stream, child, journal.record)
        step(stream, child, journal.record)
        boundary(stream, child, journal, tmp_path, 1)
        previous = stream.checkpoint()
        current = deepcopy(previous)
        current['state']['deadline_unix'] = 2000
        current['sha256'] = digest(current['state'])
        proposal = dict(schema='R131_WALL_EXTENDED_V1', plan_sha256='a' * 64, state=current,
            authorization=dict(schema=WALL_EXTENSION_SCHEMA, previous_deadline_unix=1000,
                previous_stream_sha256=previous['sha256'], new_deadline_unix=2000,
                lease_end_unix=2600, safety_margin_seconds=600))
        before = saved_bytes(tmp_path)
        with patch.object(journal, '_publish') as publish:
            with pytest.raises(ValueError, match='matched_common_configuration_frozen'):
                journal.record(kind, proposal)
            publish.assert_not_called()
    assert saved_bytes(tmp_path) == before
    with reopen() as journal:
        assert journal.latest_checkpoint()['document'] == previous
    assert saved_bytes(tmp_path) == before


@pytest.mark.parametrize('arm', MODES)
@pytest.mark.parametrize('relocated', [False, True])
def test_preexisting_presentation_escape_fails_replay_without_repairing_files(tmp_path, arm, relocated):
    stream = make_stream(arm)
    with journal_for(tmp_path, arm) as journal:
        record_birth(journal, stream)
        presentation = dict(stream.presentation, system_prompt='HISTORICAL-CONFIGURATION-DRIFT')
        stream.set_presentation(presentation, 32768)
        with patch.object(journal, '_advance', side_effect=partial(StreamJournal._advance, journal)):
            journal.record('PRESENTATION', dict(state=stream.checkpoint()))
        original_root = journal.root
    if relocated:
        snapshot = tmp_path / 'snapshot'
        shutil.copytree(original_root, snapshot)
        reopen = partial(RelocatedMatchedJournal, snapshot, original_root=original_root,
                         arm=arm, cohort_sha256=COHORT)
    else:
        reopen = partial(MatchedJournal, original_root, arm=arm, cohort_sha256=COHORT)
    before = saved_bytes(tmp_path)
    with pytest.raises(ValueError, match='matched_common_configuration_frozen'):
        reopen()
    assert saved_bytes(tmp_path) == before


def inbox_message(actor):
    if actor == 'environment':
        return dict(schema='R127_ATTRIBUTED_INBOX_V1', id='environment', actor=actor, split='TRAIN',
            text='Synthetic environment observation.', speaker='Tool',
            source_receipt=dict(path='/fixture/observation.json', sha256='e' * 64))
    if actor == 'attributed_parent':
        return dict(schema='R127_ATTRIBUTED_INBOX_V1', id='attributed-parent', actor='parent', split='TRAIN',
            text='Synthetic attributed parent observation.', speaker='Astra', source_receipt=None)
    return dict(id='parent', actor='parent', split='TRAIN', text='Synthetic parent observation.')


@pytest.mark.parametrize('arm', MODES)
def test_matched_snapshot_replays_relocated_inbox_receipts_without_changes(tmp_path, arm):
    stream = make_stream(arm)
    with journal_for(tmp_path, arm) as journal:
        record_birth(journal, stream)
        actors = ['environment'] if arm == 'unparented_learning' else ['environment', 'parent', 'attributed_parent']
        for actor in actors:
            (journal.inbox / f'{actor}.json').write_text(json.dumps(inbox_message(actor)))
        incoming = journal.read_inbox()
        assert len(incoming) == len(actors)
        step(stream, record=journal.record, incoming=incoming)
        expected = journal.latest_checkpoint()
        original_root = journal.root
    snapshot = tmp_path / 'snapshot'
    shutil.copytree(original_root, snapshot)
    before = saved_bytes(tmp_path)
    with pytest.raises(ValueError, match='inbox_source_path'):
        MatchedJournal(snapshot, arm=arm, cohort_sha256=COHORT)
    with RelocatedMatchedJournal(snapshot, original_root=original_root, arm=arm, cohort_sha256=COHORT) as journal:
        assert journal.latest_checkpoint() == expected
        state = journal._scan()
        assert len(state['inbox']) == len(actors)
        for receipt in state['inbox'].values():
            assert Path(receipt['source_id']).parent == original_root / 'inbox'
            replayed = journal._inbox_event(receipt['message'], receipt['source_id'], receipt['source_sha256'])
            assert replayed in incoming
    assert saved_bytes(tmp_path) == before


@pytest.mark.parametrize('actor', ['parent', 'attributed_parent'])
def test_matched_snapshot_rejects_unparented_parent_inbox_receipts(tmp_path, actor):
    with journal_for(tmp_path, 'unparented_learning') as journal:
        record_birth(journal, make_stream('unparented_learning'))
        for message_actor in ('environment', actor):
            (journal.inbox / f'{message_actor}.json').write_text(json.dumps(inbox_message(message_actor)))
        with patch.object(journal, '_inbox_event', side_effect=lambda *args: StreamJournal._inbox_event(journal, *args)):
            assert len(journal.read_inbox()) == 2
        original_root = journal.root
    snapshot = tmp_path / 'snapshot'
    shutil.copytree(original_root, snapshot)
    before = saved_bytes(tmp_path)
    with pytest.raises(ValueError, match='unparented_parent_channel_forbidden'):
        RelocatedMatchedJournal(snapshot, original_root=original_root, arm='unparented_learning', cohort_sha256=COHORT)
    assert saved_bytes(tmp_path) == before


@pytest.mark.parametrize('change,label', [('arm', 'resume_matched_policy_mismatch'),
                                        ('cohort', 'resume_matched_policy_mismatch'),
                                        ('original_root', 'inbox_source_path')])
def test_matched_snapshot_binds_arm_cohort_and_original_inbox_root(tmp_path, change, label):
    with journal_for(tmp_path) as journal:
        record_birth(journal, make_stream())
        (journal.inbox / 'environment.json').write_text(json.dumps(inbox_message('environment')))
        journal.read_inbox()
        original_root = journal.root
    snapshot = tmp_path / 'snapshot'
    shutil.copytree(original_root, snapshot)
    options = dict(original_root=original_root, arm='parented_frozen', cohort_sha256=COHORT)
    options[change if change != 'cohort' else 'cohort_sha256'] = {
        'arm': 'parented_learning', 'cohort': 'd' * 64, 'original_root': tmp_path / 'wrong-origin'}[change]
    before = saved_bytes(tmp_path)
    with pytest.raises(ValueError, match=label):
        RelocatedMatchedJournal(snapshot, **options)
    assert saved_bytes(tmp_path) == before
