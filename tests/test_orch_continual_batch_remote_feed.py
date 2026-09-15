from copy import deepcopy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from gpu import orch_continual_batch_publish as publisher
from gpu import orch_continual_batch_remote_feed as feed
from gpu.orch_continual_batch_handoff import wrap_row
from organism_v6 import orch_continual_batch as policy


class NativeFeedTests(unittest.TestCase):
    def test_inherits_used_quota(self):
        old = dict(reserved=52, limit=128)
        self.assertEqual(feed.reserve_budget(old, 10000, 100)['reserved'], 54)
        self.assertEqual(old['reserved'], 52)

    def test_cannot_reset_or_exceed_budget(self):
        with self.assertRaisesRegex(ValueError, 'call_cap'):
            feed.reserve_budget(dict(reserved=128, limit=128), 10000, 100)

    def test_original_deadline_enforced(self):
        with self.assertRaisesRegex(ValueError, 'deadline'):
            feed.reserve_budget(dict(reserved=52, limit=128), 700, 100)

    def test_no_temp_deletion_without_native_verified_hash(self):
        with tempfile.TemporaryDirectory(prefix='orch_continual_batch_test_') as directory:
            path = Path(directory) / 'review_batch_027'
            path.mkdir()
            (path / 'PACKET.json').write_text('preserved')
            for receipt in ({'verified': False}, {'verified': True, 'inventory_sha256': 'wrong'}):
                with self.assertRaisesRegex(ValueError, 'do_not_delete'):
                    feed.cleanup_verified_packets(path, receipt, 'expected')
            self.assertEqual((path / 'PACKET.json').read_text(), 'preserved')

    def test_cleanup_only_after_exact_native_inventory(self):
        with tempfile.TemporaryDirectory(prefix='orch_continual_batch_test_') as directory:
            path = Path(directory) / 'review_batch_027'
            path.mkdir()
            feed.cleanup_verified_packets(path, {'verified': True, 'inventory_sha256': 'exact'}, 'exact')
            self.assertFalse(path.exists())

    def test_transport_error_does_not_log_host_or_secrets(self):
        error = subprocess.CalledProcessError(1, ['ssh', 'private-host', 'SECRET'])
        rendered = json.dumps(feed.failure_summary(error))
        self.assertNotIn('private-host', rendered)
        self.assertNotIn('SECRET', rendered)

    def test_source_regime_and_unknown_unsampled_counts(self):
        row = dict(question_sha256='q', provenance=dict(raw_call_path='raw/call', raw_call_sha256='raw',
            instruction_regime='STEERED', instruction_amount_tokens=123), target_sha256='t',
            original_semantic_status='UNREVIEWED', generated_tokens=90, review=None)
        wrapper = wrap_row(row, 'bound')
        self.assertEqual(wrapper['eligibility']['instruction_regime'], 'STEERED')
        self.assertEqual(wrapper['eligibility']['branch_metrics']['measurement_status'], 'UNKNOWN')
        self.assertIsNone(wrapper['eligibility']['branch_metrics']['semantic_distinct_approaches_considered'])

    def test_future_branch_schema(self):
        original = publisher.BRANCH_V3
        try:
            publisher.BRANCH_V3 = True
            properties = publisher.schema()['properties']['reviews']['items']['properties']['branch_metrics']['properties']
            self.assertIn('semantic_distinct_approaches_considered', properties)
            self.assertIn('semantic_distinct_approaches_pursued', properties)
            self.assertIn('repetition_failure', properties)
        finally:
            publisher.BRANCH_V3 = original

    def branch_fixture(self):
        text = 'I considered subtraction but rejected it because the problem asks for a sum.\nI added 2+3=5.\nFINAL: 5'
        row = dict(target=text, target_sha256=policy.text_sha(text), gold='5', provenance=dict(raw_call_sha256='raw'), student_prefix_sha256='prefix')
        review = dict(target_sha256=row['target_sha256'], raw_call_sha256='raw', student_prefix_sha256='prefix',
            evidence_line_ids=[1, 2], independent_answer='5', gold_status='VALID', status='PASS',
            full_text_read=True, reason='Explicit rejected subtraction and correct sum.', **dict.fromkeys(policy.AXES, True),
            branch_metrics=dict(measurement_status='MEASURED', semantic_distinct_approaches_considered=2,
                semantic_distinct_approaches_pursued=1, repetition_failure=False, repetition_reason='', repetition_line_ids=[],
                approaches=[dict(approach_id='subtract', description='subtraction', considered_line_ids=[1], pursued_line_ids=[],
                    rejected=True, rejection_reason='The problem requests a sum.', rejection_line_ids=[1]),
                    dict(approach_id='add', description='addition', considered_line_ids=[2], pursued_line_ids=[2],
                         rejected=False, rejection_reason='', rejection_line_ids=[])]))
        return row, review

    def test_rejected_path_is_not_automatic_semantic_fail(self):
        row, review = self.branch_fixture()
        result = policy.resolve_line_reviews([row], {'reviews': [review]})
        policy.validate_review([row], result)
        self.assertEqual(result['reviews'][0]['status'], 'PASS')
        self.assertEqual(result['reviews'][0]['branch_evidence_spans'][0]['rejected_why'], [row['target'].splitlines(keepends=True)[0]])

    def test_branch_counts_and_evidence_not_invented(self):
        row, review = self.branch_fixture()
        for change in ('count', 'evidence'):
            altered = deepcopy(review)
            if change == 'count':
                altered['branch_metrics']['semantic_distinct_approaches_considered'] = 9
            else:
                altered['branch_metrics']['approaches'][0]['rejection_line_ids'] = []
            with self.assertRaises(ValueError):
                policy.resolve_line_reviews([row], {'reviews': [altered]})


if __name__ == '__main__':
    unittest.main()
