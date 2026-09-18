import unittest

from eligibility_audit import projection, receipt_projection


class EligibilityProjectionTests(unittest.TestCase):
    def records(self):
        exclusion = dict(reason='meta_only_target', policy='R195_CHILD_ROW_REVIEW_V1', cohort='NEW',
            source_sha256='own-source', raw_target_sha256='own-target', target='never export')
        complete = dict(index=13, sha256='complete', kind='SLEEP_COMPLETE', document=dict(cycle=4,
            optimizer_steps=16, total_optimizer_steps=64, new_row_sha256=['retained', 'own-source'],
            excluded_rows=[exclusion]))
        eligibility = dict(index=12, sha256='eligibility', kind='TARGET_ELIGIBILITY', document=dict(
            new_row_sha256=['retained'], excluded=[exclusion], learn_review_filter=dict(
                excluded=[exclusion], content_target_filter=dict(excluded=[exclusion], checks=[{}]))))
        recipe = dict(index=11, sha256='recipe', kind='SLEEP_RECIPE', document=dict(new_rows=2))
        return complete, eligibility, recipe

    def test_merged_semantic_exclusion_not_mislabeled_technical_or_double_counted(self):
        result = projection(*self.records())
        self.assertEqual(result['actual_excluded_rows'], 1)
        self.assertEqual(result['merged_exclusion_entries'], 1)
        self.assertEqual(result['actual_review_excluded'], 1)
        self.assertEqual(result['actual_content_excluded'], 1)
        self.assertNotIn('technical_excluded', result)
        self.assertNotIn('target', result['exclusion_receipts'][0])
        self.assertEqual(result['exclusion_receipts'][0]['reason'], 'meta_only_target')

    def test_zero_exclusions_does_not_prove_disabled_policy(self):
        complete, eligibility, recipe = self.records()
        complete['document']['excluded_rows'] = []
        complete['document']['new_row_sha256'] = ['retained']
        eligibility['document']['excluded'] = []
        result = projection(complete, eligibility, recipe)
        self.assertEqual(result['actual_excluded_rows'], 0)
        self.assertFalse(result['all_off_inferred_from_zero_exclusions'])
        self.assertIsNone(result['active_semantic_filters_receipt'])

    def test_mismatched_sleep_rows_rejected(self):
        complete, eligibility, recipe = self.records()
        complete['document']['new_row_sha256'] = ['different']
        with self.assertRaises(ValueError):
            projection(complete, eligibility, recipe)

    def test_out_of_order_receipts_rejected(self):
        complete, eligibility, recipe = self.records()
        recipe['index'] = complete['index'] + 1
        with self.assertRaises(ValueError):
            projection(complete, eligibility, recipe)

    def test_incomplete_current_eligibility_is_distinct_from_completed_sleep(self):
        complete, eligibility, recipe = self.records()
        result = receipt_projection(eligibility)
        self.assertEqual(result['kind'], 'TARGET_ELIGIBILITY')
        self.assertEqual(result['retained_new_rows'], 1)
        self.assertEqual(result['merged_exclusion_entries'], 1)
        self.assertNotIn('optimizer_steps', result)
        self.assertNotIn('excluded', result)


if __name__ == '__main__':
    unittest.main()
