import copy
import unittest

from audit import adjudicate, candidates, frames, report, text_sha


def fixture():
    feedback = dict(event_id='parent:inbox:feedback', source_sha256='f' * 64,
        actor='parent', phase='feedback', text='Astra: Incorrect. Check the sign rather than merely promising.')
    records = []
    for number, stage, text in ((10, 'THINK', 'I used the wrong sign; I need subtraction.'),
                               (20, 'ACT', '7 - 3 = 4.'), (30, 'ACT', '9 - 5 = 4.')):
        request = dict(index=number, sha256=str(number), kind='REQUEST', request_digest='request' + str(number),
            masked=True, cycle=number // 10, external=[feedback])
        response = dict(index=number + 1, sha256=str(number + 1), kind='RESPONSE', request_digest=request['request_digest'],
            document_sha256='source' + str(number), text=text)
        records.extend([request, response,
            dict(index=number + 2, sha256=str(number + 2), kind='COMMITTED', source_sha256=response['document_sha256']),
            dict(index=number + 3, sha256=str(number + 3), kind='R184_STAGE', source_sha256=response['document_sha256'], stage=stage)])
    records.append(dict(index=40, sha256='40', kind='SLEEP_COMPLETE', status='COMPLETE', cycle=3))
    evidence = dict(journal_id='life', records=records, observed_unix=1, coverage_start=10, through={'index': 40}, caught_up=True)
    annotation = dict(journal_id='life', feedback_key='parent:inbox:feedback:' + 'f' * 64,
        assessment='Synthetic fixture, not science evidence.', feedback_reviewed_as_correction=True,
        parent_supplied_solution=False, intervening_context={})
    for frame, key in zip(frames(evidence), ('identifies', 'applies_next_act', 'transfers')):
        row = frame['response']
        annotation[key] = dict(index=row['index'], sha256=row['sha256'], start=0, end=len(row['text']),
            span_sha256=text_sha(row['text']), substantive_correct=True, another_relevant_attempt=True, different_task=True)
    return evidence, annotation


class AuditTests(unittest.TestCase):
    def test_complete_has_three_distinct_actual_records(self):
        evidence, annotation = fixture()
        result = adjudicate(evidence, annotation)
        self.assertEqual(result['level'], 3)
        self.assertEqual([row['record']['index'] for row in result['child_records']], [11, 21, 31])
        self.assertTrue(result['context_exposure_at_transfer'])
        self.assertEqual(result['sleep_survival'], 1)
        self.assertEqual(result['first_following_complete']['index'], 40)

    def test_keywords_never_prove_level(self):
        evidence, _ = fixture()
        self.assertEqual(len(candidates(evidence)), 1)
        self.assertIsNone(report(evidence, 'test')['highest_verified_level'])

    def test_same_record_cannot_count_twice(self):
        evidence, annotation = fixture()
        annotation['applies_next_act'] = annotation['identifies']
        with self.assertRaisesRegex(ValueError, 'distinct'):
            adjudicate(evidence, annotation)

    def test_no_skipping_the_next_act(self):
        evidence, annotation = fixture()
        annotation['applies_next_act'] = annotation['transfers']
        with self.assertRaisesRegex(ValueError, 'NEXT_ACT'):
            adjudicate(evidence, annotation)

    def test_wrong_literal_span_rejected(self):
        evidence, annotation = fixture()
        annotation['identifies']['span_sha256'] = 'made up'
        with self.assertRaisesRegex(ValueError, 'span_hash'):
            adjudicate(evidence, annotation)

    def test_reminder_prevents_level_three(self):
        evidence, annotation = fixture()
        event = dict(event_id='parent:inbox:again', source_sha256='a', actor='parent', phase='feedback', text='Astra: Remember subtraction.')
        evidence['records'][8]['external'].append(event)
        annotation['intervening_context']['parent:inbox:again:a'] = dict(reminder=True, supplies_solution=False)
        result = adjudicate(evidence, annotation)
        self.assertEqual(result['level'], 2)
        self.assertEqual(result['reminders'], 1)

    def test_unknown_context_not_assumed_no_reminder(self):
        evidence, annotation = fixture()
        evidence['records'][8]['external'].append(dict(event_id='environment:new', source_sha256='n', actor='environment', text='Tool: new result'))
        self.assertEqual(adjudicate(evidence, annotation)['level'], 2)
        annotation['intervening_context']['environment:new:n'] = dict(reminder=None, supplies_solution=False)
        self.assertEqual(adjudicate(evidence, annotation)['level'], 2)

    def test_new_parent_solution_prevents_independent_transfer(self):
        evidence, annotation = fixture()
        evidence['records'][8]['external'].append(dict(event_id='parent:new', source_sha256='n', actor='parent', text='Astra: The answer is4.'))
        annotation['intervening_context']['parent:new:n'] = dict(reminder=False, supplies_solution=True)
        self.assertEqual(adjudicate(evidence, annotation)['level'], 2)

    def test_missing_durable_boundary_is_pending(self):
        evidence, annotation = fixture()
        evidence['records'].pop()
        self.assertTrue(adjudicate(evidence, annotation)['checkpoint_pending'])

    def test_uncommitted_output_excluded(self):
        evidence, _ = fixture()
        evidence['records'] = [row for row in evidence['records'] if row['index'] != 22]
        self.assertEqual(len(frames(evidence)), 2)

    def test_masking_mandatory(self):
        evidence, _ = fixture()
        evidence['records'][0]['masked'] = False
        with self.assertRaisesRegex(ValueError, 'masked'):
            frames(evidence)

    def test_false_substantive_flag_not_proof(self):
        evidence, annotation = fixture()
        annotation['applies_next_act']['substantive_correct'] = False
        self.assertEqual(adjudicate(evidence, annotation)['level'], 1)

    def test_other_incarnation_annotation_rejected(self):
        evidence, annotation = fixture()
        annotation['journal_id'] = 'other'
        with self.assertRaisesRegex(ValueError, 'same_life'):
            adjudicate(evidence, annotation)


if __name__ == '__main__':
    unittest.main()
