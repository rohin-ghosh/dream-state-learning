from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import boundary
from boundary import ObservationRace, Refusal, SCHEMA, digest, read_boundary, same_boundary, validate_records


def inputs():
    pins = {f'gpu/patch_{number}.py': digest(['old', number]) for number in range(3)}
    newer = {name: digest(['new', name]) for name in pins}
    binding = dict(pid=12345, uid=1234, start_ticks='56789',
        boot_id='12345678-1234-1234-1234-123456789abc', guard_path='/control/GUARD.json',
        command=['python', '-B', '-m', 'gpu.native', '--guard', '/control/GUARD.json'],
        guard_sha256=digest('guard'), journal_id='a' * 32, journal_root='/life/stream',
        source_pins=pins, hard_end_unix=10000)
    old = dict(source_root='/source/old', hard_end_unix=10000, root='/life', targets=['TRAIN'],
        startup_context=dict(path='/source/old/startup.json', sha256=digest('startup')),
        learn_row_policy='unchanged', max_sleeps=None)
    new = deepcopy(old)
    new['source_root'] = '/source/new'
    new['startup_context']['path'] = '/source/new/startup.json'
    prepared = dict(old_guard_sha256=binding['guard_sha256'], old_source_pins=pins,
        new_source_pins=newer, old_plan=old, new_plan=new, cpu_passed=True, same_journal=True,
        same_checkpoint_payloads=True, same_confinement=True, epoch_id='retention-source-epoch')
    authority = dict(schema='RETENTION_SOURCE_CHANGE_AUTHORITY_V1', life_binding_sha256=digest(binding),
        wall_extension_authorized=False, epoch_id=prepared['epoch_id'], approved_source_changes={
            name: dict(before=pins[name], after=newer[name]) for name in pins})
    return binding, prepared, authority


def records_for(binding):
    checkpoint = dict(checkpoint_sha256={name: digest(name) for name in ('adapter', 'optimizer', 'rng')})
    state = dict(pending=None, rows=[dict(source_sha256=digest('row'))], sleep_frontier=1,
        deadline_unix=binding['hard_end_unix'], model_state_sha256=digest(checkpoint['checkpoint_sha256']),
        sleep_receipts=[dict(status='COMPLETE', cycle=4, checkpoint=checkpoint,
            checkpoint_sha256=checkpoint['checkpoint_sha256'])])
    documents = [('SLEEP_COMPLETE', dict(status='COMPLETE', cycle=4, checkpoint=checkpoint,
        resume_state=dict(state=state, sha256=digest(state)))),
        ('R184_LEARN_COMPLETE', dict(cycle=4, checkpoint=checkpoint))]
    records = []
    for kind, document in documents:
        append_record(records, binding, kind, document)
    return records


def append_record(records, binding, kind, document=None):
    record = dict(schema=SCHEMA, journal_id=binding['journal_id'], index=len(records), kind=kind,
        previous_sha256=records[-1]['sha256'] if records else digest(dict(schema=SCHEMA,
            journal_id=binding['journal_id'])), document=document or {})
    record['sha256'] = digest(record)
    records.append(record)
    return record


def rehash(records):
    for position, record in enumerate(records):
        if position:
            record['previous_sha256'] = records[position - 1]['sha256']
        record['sha256'] = digest({key: value for key, value in record.items() if key != 'sha256'})


def intents_for(records):
    return {record['index']: dict(schema=record['schema'], journal_id=record['journal_id'],
        index=record['index'], previous_sha256=record['previous_sha256'], record_sha256=record['sha256'])
        for record in records}


def selected(binding, records=None):
    records = records_for(binding) if records is None else records
    result = validate_records(records, binding, intents=intents_for(records))
    if result is not None:
        result.update(mailbox={}, journal_identity=dict(manifest_sha256=digest(binding['journal_id'])), durable=False)
    return result


class RecordTests(unittest.TestCase):
    def setUp(self):
        self.binding, _, _ = inputs()
        self.records = records_for(self.binding)

    def validate(self):
        return validate_records(self.records, self.binding, intents=intents_for(self.records))

    def test_both_durable_receipts_required(self):
        self.assertEqual(self.validate()['cycle'], 4)
        self.assertIsNone(validate_records([], self.binding))
        self.assertIsNone(validate_records(self.records[:1], self.binding, intents=intents_for(self.records)))
        with self.assertRaisesRegex(Refusal, 'durable_intents_required'):
            validate_records(self.records, self.binding)

    def test_pending_request_or_other_work_never_qualifies(self):
        for kind in ('REQUEST', 'CONTEXT_INPUT', 'CONTEXT_COMMITTED', 'UPDATE', 'SLEEP_REQUEST',
                'R184_THINK', 'TERMINAL', 'WALL_EXTENDED'):
            with self.subTest(kind=kind):
                records = deepcopy(self.records)
                append_record(records, self.binding, kind)
                self.assertIsNone(validate_records(records, self.binding, intents=intents_for(records)))

    def test_new_complete_without_learn_does_not_fall_back(self):
        append_record(self.records, self.binding, 'SLEEP_COMPLETE', self.records[0]['document'])
        self.assertIsNone(self.validate())

    def test_corrupt_hash_journal_chain_and_schema_refuse(self):
        for field, value in (('sha256', '0' * 64), ('journal_id', 'b' * 32), ('index', 9),
                ('schema', 'invented'), ('previous_sha256', '0' * 64)):
            with self.subTest(field=field):
                records = deepcopy(self.records)
                records[1][field] = value
                if field != 'sha256':
                    records[1]['sha256'] = digest({key: item for key, item in records[1].items() if key != 'sha256'})
                with self.assertRaises(Refusal):
                    validate_records(records, self.binding, intents=intents_for(records))

    def test_bad_genesis_and_missing_or_wrong_intent_refuse(self):
        for intents in ({}, {0: {}, 1: {}}):
            with self.assertRaisesRegex(Refusal, 'durable_record_intent_pair'):
                validate_records(self.records, self.binding, intents=intents)
        self.records[0]['previous_sha256'] = 'f' * 64
        rehash(self.records)
        with self.assertRaisesRegex(Refusal, 'genesis'):
            self.validate()

    def test_unresolved_or_different_saved_state_refuses(self):
        for key, value in (('pending', 'request:pending'), ('sleep_frontier', 0),
                ('deadline_unix', 20000), ('model_state_sha256', '0' * 64), ('sleep_receipts', [])):
            with self.subTest(key=key):
                self.records = records_for(self.binding)
                saved = self.records[0]['document']['resume_state']
                saved['state'][key] = value
                saved['sha256'] = digest(saved['state'])
                rehash(self.records)
                with self.assertRaises(Refusal):
                    self.validate()

    def test_bad_saved_state_hash_refuses(self):
        self.records[0]['document']['resume_state']['sha256'] = '0' * 64
        rehash(self.records)
        with self.assertRaisesRegex(Refusal, 'saved_state_hash'):
            self.validate()

    def test_mismatched_and_duplicate_driver_completion_refuse(self):
        self.records[1]['document']['cycle'] = 5
        rehash(self.records)
        with self.assertRaisesRegex(Refusal, 'driver_completion_same'):
            self.validate()
        self.records = records_for(self.binding)
        append_record(self.records, self.binding, 'R184_LEARN_COMPLETE', self.records[1]['document'])
        with self.assertRaisesRegex(Refusal, 'one_matching'):
            self.validate()

    def test_inbox_between_complete_and_learn_is_allowed(self):
        complete, learned = deepcopy(self.records)
        self.records = [complete]
        append_record(self.records, self.binding, 'INBOX', dict(message=dict(id='new', text='hello',
            split='TRAIN', actor='parent'), source_id='/life/stream/inbox/new.json', source_sha256=digest('mail')))
        append_record(self.records, self.binding, learned['kind'], learned['document'])
        self.assertEqual(len(self.validate()['preserved_INBOX_records']), 1)

    def test_only_source_location_may_change_in_plan(self):
        _, prepared, _ = inputs()
        boundary.verify_source_only_plans(prepared['old_plan'], prepared['new_plan'])
        for key, value in (('hard_end_unix', 10001), ('targets', ['EVAL']), ('max_sleeps', 1),
                ('learn_row_policy', 'different'), ('authorized_wall_extension', {})):
            changed = deepcopy(prepared['new_plan'])
            changed[key] = value
            with self.subTest(key=key), self.assertRaisesRegex(Refusal, 'source_only_plan'):
                boundary.verify_source_only_plans(prepared['old_plan'], changed)


class JournalFixture:
    def __init__(self, directory):
        self.binding, self.prepared, self.authority = inputs()
        self.root = Path(directory) / 'stream'
        self.root.mkdir()
        (self.root / 'records').mkdir()
        (self.root / 'inbox').mkdir()
        (self.root / 'WRITER.lock').touch()
        self.binding['journal_root'] = str(self.root)
        self.write(self.root / 'JOURNAL.json', dict(schema=SCHEMA, journal_id=self.binding['journal_id']))
        self.records = records_for(self.binding)
        self.publish()

    @staticmethod
    def write(path, value):
        path.write_text(json.dumps(value, sort_keys=True))

    def publish(self):
        intents = intents_for(self.records)
        for record in self.records:
            name = f"{record['index']:020d}"
            self.write(self.root / 'records' / (name + '.json'), record)
            self.write(self.root / 'records' / (name + '.intent.json'), intents[record['index']])

    def mail(self, identifier, *, register=True, filename=None):
        message = dict(id=identifier, text='keep this', split='TRAIN', actor='parent')
        path = self.root / 'inbox' / (filename or identifier + '.json')
        self.write(path, message)
        if register:
            append_record(self.records, self.binding, 'INBOX', dict(message=message, source_id=str(path),
                source_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
            self.publish()
        return path


class FilesystemTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(self.temporary.cleanup)
        self.fixture = JournalFixture(self.temporary.name)

    def observe(self, **kwargs):
        return read_boundary(self.fixture.binding, **kwargs)

    def test_durable_checkpoint_and_mailbox_do_not_modify_bytes(self):
        self.fixture.mail('registered')
        self.fixture.mail('arriving', register=False)
        (self.fixture.root / 'inbox' / 'incoming.partial').write_text('in flight')
        before = {str(path): path.read_bytes() for path in self.fixture.root.rglob('*') if path.is_file()}
        result = self.observe(durable=True)
        self.assertTrue(result['durable'])
        self.assertEqual(len(result['mailbox']), 2)
        self.assertEqual(before, {str(path): path.read_bytes() for path in self.fixture.root.rglob('*') if path.is_file()})

    def test_new_registered_and_unregistered_inbox_preserved(self):
        before = self.observe()
        self.fixture.mail('registered')
        self.fixture.mail('unregistered', register=False)
        after = same_boundary(before, self.observe())
        self.assertEqual(len(after['mailbox']), 2)
        self.assertEqual(len(after['preserved_INBOX_records']), 1)

    def test_identical_duplicate_mail_files_preserved_like_native(self):
        self.fixture.mail('duplicate')
        self.fixture.mail('duplicate', register=False, filename='copy.json')
        self.assertEqual(len(self.observe()['mailbox']), 2)

    def test_conflicting_duplicate_mail_refuses(self):
        self.fixture.mail('duplicate')
        path = self.fixture.mail('duplicate', register=False, filename='copy.json')
        message = json.loads(path.read_text())
        message['text'] = 'conflicting'
        self.fixture.write(path, message)
        with self.assertRaisesRegex(Refusal, 'conflicting_mailbox'):
            self.observe()

    def test_unregistered_mail_cannot_be_removed_or_changed(self):
        path = self.fixture.mail('new', register=False)
        before = self.observe()
        path.unlink()
        with self.assertRaisesRegex(Refusal, 'never_delete_or_rewrite'):
            same_boundary(before, self.observe())
        self.fixture.mail('new', register=False)
        path.write_text(path.read_text() + ' ')
        with self.assertRaisesRegex(Refusal, 'never_delete_or_rewrite'):
            same_boundary(before, self.observe())

    def test_registered_source_and_message_must_match(self):
        self.fixture.mail('new')
        self.fixture.records[-1]['document']['message']['text'] = 'not the source message'
        rehash(self.fixture.records)
        self.fixture.publish()
        with self.assertRaisesRegex(Refusal, 'registered_INBOX_source'):
            self.observe()

    def test_request_race_and_tail_rewrite_refuse(self):
        before = self.observe()
        append_record(self.fixture.records, self.fixture.binding, 'REQUEST')
        self.fixture.publish()
        with self.assertRaisesRegex(Refusal, 'raced_past_COMPLETE'):
            same_boundary(before, self.observe())
        after = deepcopy(before)
        after['records'][0]['sha256'] = '0' * 64
        with self.assertRaisesRegex(Refusal, 'prior_tail_not_rewritten'):
            same_boundary(before, after)

    def test_partial_and_unpaired_records_are_retryable(self):
        path = self.fixture.root / 'records' / '00000000000000000002.intent.json'
        path.write_text('{}')
        with self.assertRaisesRegex(ObservationRace, 'unpaired'):
            self.observe()
        path.rename(path.with_suffix('.partial'))
        with self.assertRaisesRegex(ObservationRace, 'partial'):
            self.observe()

    def test_filename_index_mismatch_refuses(self):
        self.fixture.records[0]['index'] = 9
        rehash(self.fixture.records)
        self.fixture.write(self.fixture.root / 'records' / '00000000000000000000.json', self.fixture.records[0])
        with self.assertRaisesRegex(Refusal, 'record_filename_index'):
            self.observe()

    def test_symlink_mailbox_refuses(self):
        path = self.fixture.mail('new', register=False)
        (path.parent / 'link.json').symlink_to(path)
        with self.assertRaises(OSError):
            self.observe()

    def test_replaced_journal_directory_refuses(self):
        before = self.observe()
        directory = self.fixture.root / 'inbox'
        directory.rename(self.fixture.root / 'old-inbox')
        directory.mkdir()
        with self.assertRaisesRegex(Refusal, 'journal_identity'):
            same_boundary(before, self.observe())

    def test_request_arriving_during_mail_scan_is_retryable(self):
        path = self.fixture.mail('new', register=False)
        original = boundary.file_bytes

        def raced(target, *args, **kwargs):
            content = original(target, *args, **kwargs)
            if Path(target) == path:
                append_record(self.fixture.records, self.fixture.binding, 'REQUEST')
                self.fixture.publish()
            return content

        with patch.object(boundary, 'file_bytes', side_effect=raced):
            with self.assertRaisesRegex(ObservationRace, 'observing_mailbox'):
                self.observe()

    def test_too_short_tail_fails_closed(self):
        with self.assertRaisesRegex(Refusal, 'two_records'):
            self.observe(max_records=1)
        for number in range(3):
            self.fixture.mail(str(number))
        self.assertIsNone(self.observe(max_records=2))


if __name__ == '__main__':
    unittest.main()
