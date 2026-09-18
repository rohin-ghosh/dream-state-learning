"""Synthetic local CPU fixtures only; no parent provider or native imports."""

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_r127_pilot_console as inbox_api
from gpu import orch_r137_parent_exposure as exposure
from gpu.orch_r125_stream_journal import StreamJournal, _digest
from organism_v6.orch_r124_train_history import TrainEvent, TrainHistory
from organism_v6.orch_r125_continual_stream import ContinualStream
from organism_v6.orch_r125_plain_context import VERSION as PLAIN_VERSION


class ParentExposureTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.journal = StreamJournal(self.root / 'stream', create=True)
        self.addCleanup(self.journal.close)
        self.stream = ContinualStream(TrainHistory(system_prompt='System.', birth_prompt='Birth.'),
            context_limit=8192, segment_tokens=2, segments_per_sleep=2,
            deadline_unix=1000, model_state_sha256='f' * 64)
        self.journal.record('COMMITTED', dict(kind='BIRTH', state=self.stream.checkpoint()))

    def step(self, text='Actual child.', *, incoming=(), truncated=False, response_fields=None, record=None):
        def generate(messages, **kwargs):
            return dict(raw=text, token_ids=[10, 2], terminal=not truncated, truncated=truncated,
                **(response_fields or {}))
        return self.stream.step(generate, lambda messages: sum(len(item['content'].split()) + 4 for item in messages),
            record or self.journal.record, incoming=incoming, now=lambda: 100)

    def parent(self, speaker='Astra', text='A precise question.'):
        return inbox_api.publish_parent(self.root, speaker, text)

    def read(self, publications=None, **limits):
        return exposure.snapshot(self.root, publications=publications, **limits)

    def records(self):
        return [path for path in sorted((self.root / 'stream' / 'records').glob('*.json'))
            if not path.name.endswith('.intent.json')]

    def rewrite(self, kind, change):
        previous = _digest(json.loads((self.root / 'stream' / 'JOURNAL.json').read_bytes()))
        for path in self.records():
            record = json.loads(path.read_bytes())
            if record['kind'] == kind:
                change(record['document'])
            record['previous_sha256'] = previous
            record['sha256'] = _digest({key: value for key, value in record.items() if key != 'sha256'})
            path.write_text(json.dumps(record))
            path.with_name(path.stem + '.intent.json').write_text(json.dumps(StreamJournal._intent(record)))
            previous = record['sha256']

    def test_actual_bound_parent_exposure_and_compatible_fields(self):
        self.step()
        publication = self.parent()
        self.journal.read_inbox()
        before = self.read([publication])
        self.assertEqual(before['consumed_inbox'], {})
        self.assertEqual(before['unexposed_parent_inbox_count'], 1)
        self.step(incoming=self.journal.read_inbox())
        state = self.read([publication])
        self.assertEqual(state['schema'], 'R133_TRAIN_PARENT_SNAPSHOT_V1')
        self.assertEqual(state['response_count'], 2)
        observed = state['consumed_inbox'][publication['id']]
        self.assertEqual(observed['publication'], publication)
        self.assertTrue(observed['publication_bound'])
        self.assertEqual(observed['status'], 'IN_REQUEST')
        boundary = state['boundaries'][0]
        self.assertLess(boundary['record_index'], observed['record_index'])
        self.assertLess(observed['record_index'], boundary['next_request_index'])
        self.assertEqual(observed['request_index'], boundary['next_request_index'])
        self.assertEqual(state['parent_consumptions'], [observed])
        self.assertEqual(state['events'][-2]['actor'], 'parent')
        source = boundary['source_receipt']
        for key in ('request', 'response', 'committed'):
            self.assertEqual(source[key]['sha256'], hashlib.sha256(Path(source[key]['path']).read_bytes()).hexdigest())

    def test_foreign_parent_and_environment_are_not_programme_exposure(self):
        self.step()
        own = self.parent()
        self.parent('Fable')
        self.parent('Rohin')
        self.parent(text='Other Astra message.')
        inbox_api._inbox(self.root, 'Tool', 'Environment only.', dict(path='/never/read/held.json', sha256='a' * 64))
        self.step(incoming=self.journal.read_inbox())
        state = self.read([own])
        self.assertEqual(set(state['consumed_inbox']), {own['id']})
        self.assertEqual(len(state['parent_consumptions']), 1)
        self.assertEqual(state['registered_inbox_count'], 5)
        self.assertEqual(self.read([])['consumed_inbox'], {})
        self.assertEqual(self.read()['attribution_scope'], 'speaker_only')
        self.assertEqual(len(self.read()['consumed_inbox']), 2)

    def test_publication_hash_mismatch_rejected(self):
        publication = self.parent()
        self.journal.read_inbox()
        with self.assertRaisesRegex(ValueError, 'publication_exact_bytes_binding'):
            self.read([dict(publication, sha256='0' * 64)])

    def test_publication_path_mismatch_rejected_without_opening_it(self):
        publication = self.parent()
        with self.assertRaisesRegex(ValueError, 'publication_exact_inbox_path'):
            self.read([dict(publication, path='/never/read/FINAL.json')])

    def test_forged_journal_payload_cannot_retain_original_publication_hash(self):
        publication = self.parent()
        self.journal.read_inbox()
        self.rewrite('INBOX', lambda document: document['message'].update(text='Forged text'))
        with self.assertRaisesRegex(ValueError, 'publication_exact_bytes_binding'):
            self.read([publication])

    def test_registered_but_evicted_not_consumed(self):
        self.step()
        publication = self.parent()
        for event in self.journal.read_inbox():
            self.stream.history.append(event)
        self.stream.history.evict_oldest(self.stream.history.frontier(), reason='Synthetic eviction')
        self.step()
        state = self.read([publication])
        self.assertEqual(state['consumed_inbox'], {})
        self.assertEqual(state['parent_consumptions'], [])
        self.assertEqual(state['unexposed_parent_inbox_count'], 1)

    def test_plain_context_exposure_and_filtered_message(self):
        self.stream.set_presentation(dict(version=PLAIN_VERSION, system_prompt='Plain.', birth_prompt='Birth.'), 16384)
        self.journal.record('PRESENTATION', dict(state=self.stream.checkpoint()))
        self.step()
        visible = self.parent(text='Visible question.')
        filtered = self.parent(text='source_sha256 is filtered by existing plain rendering')
        self.step(incoming=self.journal.read_inbox())
        state = self.read([visible, filtered])
        self.assertEqual(set(state['consumed_inbox']), {visible['id']})

    def test_later_exposure_does_not_retrocredit_earlier_boundary(self):
        self.step()
        publication = self.parent()
        incoming = self.journal.read_inbox()
        self.step(text='Request did not include registered message.')
        self.step(incoming=incoming)
        state = self.read([publication])
        self.assertIn(publication['id'], state['consumed_inbox'])
        self.assertEqual(len(state['parent_exposures']), 1)
        self.assertEqual(state['parent_consumptions'], [])

    def test_retained_parent_context_does_not_duplicate_boundary_credit(self):
        self.step()
        publication = self.parent()
        self.step(incoming=self.journal.read_inbox())
        self.step(incoming=self.journal.read_inbox())
        state = self.read([publication])
        self.assertEqual(len(state['parent_consumptions']), 1)
        self.assertEqual(len(state['parent_exposures']), 1)

    def test_pre_sleep_request_closes_correct_boundary(self):
        self.step()
        self.step()
        publication = self.parent()
        invitation = TrainEvent(event_id='presleep:1', actor='environment', text='Reflect briefly.', split='TRAIN',
            phase='presleep', episode_id='continual_stream', source_id='R124_RUNTIME_INVITATION',
            source_sha256='a' * 64, origin='TRAIN_COLLECTION')
        self.step(incoming=[invitation] + self.journal.read_inbox())
        receipt = dict(status='COMPLETE', optimizer_steps=1,
            new_row_sha256=[row['source_sha256'] for row in self.stream.pending_rows()],
            checkpoint_sha256=dict(adapter='a' * 64, optimizer='b' * 64, rng='c' * 64))
        self.stream.commit_sleep(receipt, self.journal.record)
        state = self.read([publication])
        exposure_record, = state['parent_consumptions']
        self.assertEqual(exposure_record['request_index'], state['boundaries'][1]['next_request_index'])
        self.assertIsNone(state['boundaries'][2]['next_request_index'])

    def test_pending_request_is_exposure_not_completed_child_response(self):
        self.step()
        publication = self.parent()
        def stop_after_request(kind, document):
            self.journal.record(kind, document)
            if kind == 'REQUEST':
                raise RuntimeError('Synthetic pause')
        with self.assertRaises(RuntimeError):
            self.step(incoming=self.journal.read_inbox(), record=stop_after_request)
        state = self.read([publication])
        self.assertTrue(state['pending_request'])
        self.assertEqual(state['response_count'], 1)
        self.assertEqual(state['request_count'], 2)
        self.assertEqual(state['latest_request_index'], state['boundaries'][0]['next_request_index'])
        self.assertIn(publication['id'], state['consumed_inbox'])

    def test_uncommitted_response_never_shown_or_counted(self):
        def stop_before_commit(kind, document):
            if kind == 'COMMITTED':
                raise RuntimeError('Synthetic pause')
            return self.journal.record(kind, document)
        with self.assertRaises(RuntimeError):
            self.step(text='Uncommitted secret-looking text.', record=stop_before_commit)
        state = self.read()
        self.assertEqual(state['response_count'], 0)
        self.assertEqual(state['events'], [])
        self.assertTrue(state['pending_response'])
        self.assertEqual(state['request_count'], 1)
        self.assertEqual(state['latest_request_index'], 1)

    def test_request_count_and_latest_index_start_empty_then_include_committed_request(self):
        state = self.read()
        self.assertEqual(state['request_count'], 0)
        self.assertIsNone(state['latest_request_index'])
        self.assertIsNone(state['latest_request'])
        self.step()
        state = self.read()
        self.assertEqual(state['request_count'], 1)
        self.assertEqual(state['latest_request_index'], 1)
        self.assertEqual(state['latest_request'], state['boundaries'][0]['source_receipt']['request'])

    def test_held_or_parent_response_provenance_rejected(self):
        self.step(response_fields=dict(split='HELD'))
        with self.assertRaisesRegex(ValueError, 'source_TRAIN_child_provenance'):
            self.read()

    def test_explicit_parent_response_not_counted_as_child(self):
        self.step(response_fields=dict(actor='parent'))
        with self.assertRaisesRegex(ValueError, 'source_TRAIN_child_provenance'):
            self.read()

    def test_held_request_never_exposed_or_counted(self):
        self.step()
        self.rewrite('REQUEST', lambda document: document.update(split='HELD'))
        with self.assertRaisesRegex(ValueError, 'request_checkpoint_binding'):
            self.read()

    def test_mixed_journal_identity_rejected_even_with_valid_record_digest(self):
        self.step()
        path = self.records()[-1]
        record = json.loads(path.read_bytes())
        record['journal_id'] = 'f' * 32
        record['sha256'] = _digest({key: value for key, value in record.items() if key != 'sha256'})
        path.write_text(json.dumps(record))
        path.with_name(path.stem + '.intent.json').write_text(json.dumps(StreamJournal._intent(record)))
        with self.assertRaisesRegex(ValueError, 'journal_chain_integrity'):
            self.read()

    def test_response_request_binding_rejected(self):
        self.step()
        self.rewrite('RESPONSE', lambda document: document.update(request_sha256='0' * 64))
        with self.assertRaisesRegex(ValueError, 'response_request_binding'):
            self.read()

    def test_commit_binding_rejected(self):
        self.step()
        def change(document):
            if 'source_sha256' in document:
                document['source_sha256'] = '0' * 64
        self.rewrite('COMMITTED', change)
        with self.assertRaisesRegex(ValueError, 'commit_response_binding'):
            self.read()

    def test_intent_binding_and_journal_identity_rejected(self):
        self.step()
        path = self.records()[-1].with_suffix('.intent.json')
        path.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'journal_intent_binding'):
            self.read()

    def test_partial_commit_waits_without_repair(self):
        self.step()
        path = self.records()[-1]
        partial = path.with_suffix('.json.partial')
        path.rename(partial)
        before = partial.read_bytes()
        state = self.read()
        self.assertEqual(state['response_count'], 0)
        self.assertEqual(state['scan_status'], 'PENDING_TAIL')
        self.assertEqual(partial.read_bytes(), before)
        partial.rename(path)
        self.assertEqual(self.read()['response_count'], 1)

    def test_event_window_and_source_truncation_preserved(self):
        for number in range(10):
            self.step(text=str(number), truncated=True)
        state = self.read()
        self.assertEqual(state['response_count'], 10)
        self.assertEqual([event['text'] for event in state['events']], [str(number) for number in range(2, 10)])
        self.assertTrue(all(event['truncated'] for event in state['events']))

    def test_limits_raise_instead_of_returning_partial_coverage(self):
        self.step()
        with self.assertRaisesRegex(exposure.SnapshotLimitExceeded, 'record_limit'):
            self.read(max_records=1)
        with self.assertRaisesRegex(exposure.SnapshotLimitExceeded, 'byte_limit'):
            self.read(max_bytes=1)

    def test_only_journal_files_read_no_publication_or_held_paths(self):
        self.step()
        publication = self.parent()
        self.step(incoming=self.journal.read_inbox())
        before = {str(path): path.read_bytes() for path in (self.root / 'stream').rglob('*') if path.is_file()}
        original = inbox_api._read
        def guarded(directory, name, limit):
            path = Path(os.readlink('/proc/self/fd/' + str(directory))) / name
            self.assertTrue(path.parent == self.root / 'stream' / 'records'
                or path == self.root / 'stream' / 'JOURNAL.json', str(path))
            return original(directory, name, limit)
        with patch.object(inbox_api, '_read', side_effect=guarded):
            self.assertIn(publication['id'], self.read([publication])['consumed_inbox'])
        after = {str(path): path.read_bytes() for path in (self.root / 'stream').rglob('*') if path.is_file()}
        self.assertEqual(before, after)

    def test_exposure_predicate_requires_exact_visible_event_and_rendered_message(self):
        publication = self.parent()
        incoming = self.journal.read_inbox()
        self.step(incoming=incoming)
        request = next(json.loads(path.read_bytes())['document'] for path in self.records()
            if json.loads(path.read_bytes())['kind'] == 'REQUEST')
        self.assertTrue(exposure.request_exposes(request, incoming[0]))
        altered = deepcopy(request)
        altered['messages'] = [dict(role='user', content='merely mentions ' + incoming[0].text)]
        self.assertFalse(exposure.request_exposes(altered, incoming[0]))
        state = self.read([publication])
        self.assertIn(publication['id'], state['consumed_inbox'])
        self.assertEqual(state['parent_consumptions'], [])

    def result_output(self, publication, *, message='A precise question.', status='PUBLISHED'):
        output = self.root / 'parent_output'
        directory = output / 'parent_000000'
        directory.mkdir(parents=True)
        result = dict(status=status, programme='emotional_support', branch='support', speaker='Astra',
            response=dict(speak=True, message=message, rationale='Private rationale not returned'),
            inbox_publication=publication)
        (directory / 'RESULT.json').write_text(json.dumps(result))
        return output

    def test_result_publication_crossbinds_request_text_and_receipt_bytes(self):
        self.step()
        publication = self.parent()
        output = self.result_output(publication)
        self.step(incoming=self.journal.read_inbox())
        publications = exposure.publications_from_results(output, programme='emotional_support', branch='support')
        self.assertEqual(len(publications), 1)
        self.assertEqual(set(publications[0]), {'id', 'path', 'sha256', 'result_receipt'})
        state = self.read(publications)
        observed = state['consumed_inbox'][publication['id']]
        expected_path = output / 'parent_000000' / 'RESULT.json'
        self.assertEqual(observed['programme_result_receipt'], dict(path=str(expected_path),
            sha256=hashlib.sha256(expected_path.read_bytes()).hexdigest()))

    def test_result_text_hash_mismatch_rejected(self):
        output = self.result_output(self.parent(), message='Not what was published.')
        with self.assertRaisesRegex(ValueError, 'result_publication_text_hash'):
            exposure.publications_from_results(output, programme='emotional_support', branch='support')

    def test_result_branch_mismatch_rejected(self):
        output = self.result_output(self.parent())
        with self.assertRaisesRegex(ValueError, 'result_programme_branch_speaker'):
            exposure.publications_from_results(output, programme='emotional_support', branch='other')

    def test_silent_uncertain_and_absent_result_do_not_create_publications(self):
        output = self.result_output(self.parent(), status='MISSING')
        pending = output / 'parent_000001'
        pending.mkdir()
        (pending / 'DISPATCH_INTENT.json').write_text('never read')
        self.assertEqual(exposure.publications_from_results(output,
            programme='emotional_support', branch='support'), [])

    def test_result_loader_never_reads_private_provider_or_held_files(self):
        output = self.result_output(self.parent())
        for name in ('PROVIDER_RESPONSE.json', 'SYSTEM.txt', 'PROMPT.txt', 'FINAL.json', 'held.json'):
            (output / 'parent_000000' / name).write_text('do not read')
        original = inbox_api._read
        def guarded(directory, name, limit):
            self.assertEqual(name, 'RESULT.json')
            return original(directory, name, limit)
        with patch.object(inbox_api, '_read', side_effect=guarded):
            self.assertEqual(len(exposure.publications_from_results(output,
                programme='emotional_support', branch='support')), 1)

    def test_result_loader_bounds_and_partial_result_fail_closed(self):
        output = self.result_output(self.parent())
        with self.assertRaisesRegex(exposure.SnapshotLimitExceeded, 'result_byte_limit'):
            exposure.publications_from_results(output, programme='emotional_support', branch='support', max_bytes=1)
        (output / 'parent_000000' / 'RESULT.json').write_text('{')
        with self.assertRaises(ValueError):
            exposure.publications_from_results(output, programme='emotional_support', branch='support')


if __name__ == '__main__':
    unittest.main()
