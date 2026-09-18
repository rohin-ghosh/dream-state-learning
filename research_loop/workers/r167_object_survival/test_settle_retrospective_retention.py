import unittest
from unittest.mock import patch

import settle_retrospective_retention as report


def cell(identity, cueing='UNCUED'):
    return dict(status='ANNOTATED', annotation=dict(identity=identity, cueing=cueing))


class RetentionReportTests(unittest.TestCase):
    def test_missing_never_becomes_negative(self):
        self.assertEqual(report.paired(cell('SPECIFIC_IDENTITY'), dict(status='ORIGINAL_INVALID_MISSING')), 'MISSING')

    def test_ambiguity_and_conflicts_not_OFF_negatives(self):
        for label in ('AMBIGUOUS', 'CONFLICTING_FEATURES'):
            self.assertEqual(report.paired(cell('SPECIFIC_IDENTITY'), cell(label)), 'INDETERMINATE')

    def test_all_paired_dispositions_preserve_controls(self):
        positive = cell('SPECIFIC_IDENTITY_WITH_RELATIONAL_DETAIL')
        negative = cell('GENERIC_CATEGORY_ONLY')
        self.assertEqual(report.paired(positive, negative), 'ON_NOT_OFF')
        self.assertEqual(report.paired(positive, positive), 'ON_AND_OFF')
        self.assertEqual(report.paired(negative, positive), 'OFF_ONLY')
        self.assertEqual(report.paired(negative, negative), 'NEITHER_IDENTIFIED')

    def test_all18_sleeps_three_separate_prompts_and_four_controls(self):
        rows = report.make_rows([], {})
        self.assertEqual(len(rows), 54)
        self.assertEqual({row['sleep'] for row in rows}, set(range(8, 26)))
        self.assertTrue(all(len(row['cells']) == 4 and row['checkpoint_pair'] == 'MISSING' for row in rows))

    def test_primary_not_gated_on_secondary_or_initial(self):
        entries = [dict(opaque_id='on', comparison_sleep=8, key='8_LORA_ON', position=0),
            dict(opaque_id='off', comparison_sleep=8, key='8_LORA_OFF', position=0)]
        rows = report.make_rows(entries, dict(on=cell('SPECIFIC_IDENTITY'), off=cell('NO_IDENTIFIABLE_EVIDENCE')))
        self.assertEqual(rows[0]['checkpoint_pair'], 'ON_NOT_OFF')
        self.assertEqual(rows[0]['initial_pair'], 'MISSING')
        self.assertEqual(rows[1]['checkpoint_pair'], 'MISSING')

    def test_cueing_is_explicit_not_silent_primary_redefinition(self):
        entries = [dict(opaque_id='on', comparison_sleep=8, key='8_LORA_ON', position=0),
            dict(opaque_id='off', comparison_sleep=8, key='8_LORA_OFF', position=0)]
        rows = report.make_rows(entries, dict(on=cell('SPECIFIC_IDENTITY', 'CUED'), off=cell('NO_IDENTIFIABLE_EVIDENCE')))
        self.assertEqual(rows[0]['checkpoint_pair'], 'ON_NOT_OFF')
        self.assertFalse(rows[0]['paired_uncued_interpretation_ready'])

    def test_duplicate_mapping_refused(self):
        entry = dict(opaque_id='on', comparison_sleep=8, key='8_LORA_ON', position=0)
        with self.assertRaisesRegex(ValueError, 'no_duplicate'):
            report.make_rows([entry, entry], dict(on=cell('SPECIFIC_IDENTITY')))

    def test_no_mapping_read_before_combined_freeze(self):
        with patch.object(report.protocol, 'bound', return_value=dict(status='NOT_FROZEN')), \
                patch.object(report.judge, 'remote_read') as remote:
            with self.assertRaises(ValueError):
                report.read_mapping_after_freeze({}, {}, {})
            remote.assert_not_called()

    def test_public_readiness_never_contains_result_qualitative_fields(self):
        readiness = report.public_readiness({'REPORT.private.md': {'path': '/private/report', 'sha256': 'hash'}}, {}, {})
        self.assertFalse(readiness['aggregate_success_claim_released'])
        self.assertFalse(readiness['parent_access'])
        for field in ('rows', 'annotation', 'identity', 'cueing', 'primary', 'scores', 'responses'):
            self.assertNotIn(field, readiness)
        self.assertEqual(readiness['new_provider_calls'], 0)


if __name__ == '__main__':
    unittest.main()
