"""Synthetic CPU regressions; no calls to a model, journal writer or GPU."""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from audit import certify_level, rendered_parents, stages, trace, verify_projection
from reader import digest, message_match, verified


def fixture():
    event = dict(actor='parent', event_id='parent:inbox:feedback', text='Astra: Keep the subtraction sign.',
        source_id='/fake/stream/inbox/feedback.json', source_sha256='source-feedback', split='TRAIN',
        phase='feedback', rendered_message_indices=[0])
    records = []

    def append(kind, **fields):
        index = len(records)
        record = dict(index=index, kind=kind, sha256='sha-' + str(index),
            previous_sha256=records[-1]['sha256'] if records else 'anchor', document_sha256='doc-' + str(index))
        record.update(fields)
        records.append(record)
        return record

    def request():
        return append('REQUEST', request_digest='request-' + str(len(records)), masked=True,
            external=[deepcopy(event)], messages=[dict(role='user', content=event['text'])], cycle=1)

    def response_chain(request_row, kind, text):
        response = append('RESPONSE', request_digest=request_row['request_digest'], text=text)
        append('COMMITTED', source_sha256=response['document_sha256'])
        append('R184_STAGE', source_sha256=response['document_sha256'], stage=kind)
        return response

    append('SLEEP_COMPLETE')
    initial = request()
    candidate = response_chain(initial, 'THINK', 'I reversed the subtraction sign; I must keep it.')
    immediate = response_chain(request(), 'ACT', '8 - 6 = 2.')
    later = response_chain(request(), 'ACT', '9 - 6 = 3.')
    append('SLEEP_COMPLETE')
    cut = dict(window_complete=True, records=records, anchor_index=0,
        initial_head=dict(sha256=records[-1]['sha256']), parent_sources={'source-feedback':dict(backing_file_verified=True)})
    annotation = dict(id='synthetic', label='synthetic', feedback_request=initial['index'],
        feedback_event=event['event_id'], candidate=candidate['index'], identifies=True,
        identification_quote='I reversed the subtraction sign', next_act=immediate['index'], applies=True,
        later_act=later['index'], later_applies=True, later_relevant=True, reminders=[], reason='fixture only')
    return cut, annotation


class ReaderTests(unittest.TestCase):
    def test_plain_parent_render_and_assistant_quote_distinct(self):
        event = dict(actor='parent', text='Astra: correction')
        self.assertTrue(message_match(event, dict(role='user', content=event['text'])))
        self.assertFalse(message_match(event, dict(role='assistant', content=event['text'])))

    def test_structured_render_requires_exact_source_metadata(self):
        event = dict(actor='parent', text='Astra: correction', event_id='parent:test', source_id='/source',
            source_sha256='sha', split='TRAIN')
        content = 'Parent advice (not an observed fact)\n' + json.dumps(event) + '\n' + event['text']
        self.assertTrue(message_match(event, dict(role='user', content=content)))
        self.assertFalse(message_match(dict(event, source_sha256='other'), dict(role='user', content=content)))

    def test_canonical_record_corruption_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / '00000000000000000000.json'
            document = dict(journal_id='journal', index=0, kind='RESPONSE', previous_sha256=None, document=dict(text='one'))
            record = dict(document, sha256=digest(document))
            path.write_text(json.dumps(record))
            self.assertEqual(verified(path, 'journal')[0]['sha256'], record['sha256'])
            record['document']['text'] = 'tampered'
            path.write_text(json.dumps(record))
            with self.assertRaises(ValueError):
                verified(path, 'journal')

    def test_wrong_journal_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / '00000000000000000000.json'
            document = dict(journal_id='one', index=0, kind='RESPONSE', previous_sha256=None, document={})
            path.write_text(json.dumps(dict(document, sha256=digest(document))))
            with self.assertRaises(ValueError):
                verified(path, 'two')


class AuditTests(unittest.TestCase):
    def test_ordered_chain_needs_explicit_external_review_for_level3(self):
        cut, annotation = fixture()
        self.assertEqual(trace(cut, annotation)['level'], 2)
        annotation['external_dispositions'] = {}
        self.assertEqual(trace(cut, annotation)['level'], 3)

    def test_identification_without_next_act_application_is_level1(self):
        cut, annotation = fixture()
        annotation['applies'] = False
        self.assertEqual(trace(cut, annotation)['level'], 1)

    def test_self_claim_or_correct_number_does_not_infer_identification(self):
        cut, annotation = fixture()
        annotation.update(identifies=False, identification_quote=None)
        self.assertEqual(trace(cut, annotation)['level'], 0)

    def test_cannot_skip_failed_next_act(self):
        cut, annotation = fixture()
        annotation['next_act'] = annotation['later_act']
        with self.assertRaises(ValueError):
            trace(cut, annotation)

    def test_three_distinct_child_records_required(self):
        cut, annotation = fixture()
        annotation['later_act'] = annotation['next_act']
        with self.assertRaises(ValueError):
            trace(cut, annotation)

    def test_masking_required(self):
        cut, annotation = fixture()
        cut['records'][annotation['feedback_request']]['masked'] = False
        with self.assertRaises(ValueError):
            trace(cut, annotation)

    def test_missing_literal_identification_span_rejected(self):
        cut, annotation = fixture()
        annotation['identification_quote'] = 'Not present in own output'
        with self.assertRaises(ValueError):
            trace(cut, annotation)

    def test_uncommitted_response_not_evidence(self):
        cut, annotation = fixture()
        commit = next(row for row in cut['records'] if row['kind']=='COMMITTED')
        commit['source_sha256'] = 'other'
        with self.assertRaises(ValueError):
            stages(cut)

    def test_gapped_window_cannot_prove_absence(self):
        cut, annotation = fixture()
        cut['records'].pop(3)
        with self.assertRaises(ValueError):
            verify_projection(cut)

    def test_truncated_window_cannot_prove_absence(self):
        cut, annotation = fixture()
        cut['window_complete'] = False
        with self.assertRaises(ValueError):
            verify_projection(cut)

    def test_retained_parent_not_counted_as_new_reminder(self):
        cut, annotation = fixture()
        result = trace(cut, annotation)
        self.assertTrue(result['no_new_parent_between_identification_and_next_ACT']['proven'])
        self.assertEqual(result['reminder_count_before_later_ACT'], 0)
        self.assertTrue(result['original_parent_verbatim_in_next_ACT_request'])

    def test_new_unreviewed_parent_reminder_rejected(self):
        cut, annotation = fixture()
        request = [row for row in cut['records'] if row['kind']=='REQUEST'][-1]
        request['external'][0].update(event_id='parent:inbox:new', source_sha256='new')
        with self.assertRaises(ValueError):
            trace(cut, annotation)

    def test_ambiguous_plain_body_source_not_double_counted(self):
        cut, annotation = fixture()
        request = cut['records'][annotation['feedback_request']]
        second = dict(request['external'][0], source_sha256='other', event_id='parent:inbox:other')
        request['external'].append(second)
        with self.assertRaises(ValueError):
            rendered_parents(request)

    def test_unknown_or_solution_reminders_block_level3(self):
        self.assertEqual(certify_level(True, True, True, True, True, 1, True, False), 2)
        self.assertEqual(certify_level(True, True, True, True, True, 0, True, True), 2)
        self.assertEqual(certify_level(True, True, True, True, False, 0, True, False), 2)


if __name__ == '__main__':
    unittest.main()
