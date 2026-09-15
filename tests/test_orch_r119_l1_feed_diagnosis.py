import unittest

from gpu.orch_r119_l1_feed_diagnosis import classify


class DiagnosisTests(unittest.TestCase):
    def setUp(self):
        self.reference = dict(eligible_task_ids=[],eligible_target_hashes=[],historical_target_hashes=[],
                              excluded_ids=[],excluded_question_hashes=[],bound_review_call_hashes=[],
                              tasks_sha256='tasks',legacy_plan=dict(supplement_archive_sha256='archive',
                              original_source_archive_sha256='original',policy_sha256='policy',generation_seed_unchanged='oldseed'))
        self.row = dict(split='TRAIN',parent_calls=0,source_label='R109_SELF_GENERATED_FUNCTIONAL',
                        family='math',source_task_id='task',response=dict(raw='FINAL: 2',terminal=True,truncated=False),
                        source_archive_sha256='archive',original_environment_archive_sha256='original',
                        prompt_policy_sha256='policy',source_state_sha256='newseed',source_tasks_sha256='tasks',
                        outcome=dict(correct=True))
        self.task = dict(id='task',question_sha256='question')

    def result(self):
        return classify(self.row,self.task,self.reference,'callhash',dict(correct=True))

    def test_correct_new_math_without_review_is_not_admitted(self):
        result=self.result()
        self.assertTrue(result['quality_screen_candidate'])
        self.assertFalse(result['admitted'])
        self.assertIn('missing_bound_author_review',result['reasons'])
        self.assertEqual(result['source_binding_drift'],['source_state_sha256'])

    def test_duplicate_source_is_separate_from_new_target(self):
        self.reference['eligible_task_ids']=['task']
        result=self.result()
        self.assertTrue(result['duplicate_task'])
        self.assertFalse(result['duplicate_target'])
        self.assertFalse(result['quality_screen_candidate'])

    def test_nonmath_cannot_be_reported_as_native_math_success(self):
        self.row['family']='route'
        result=self.result()
        self.assertFalse(result['math_native_correct'])
        self.assertIn('unsupported_family_for_existing_feed',result['reasons'])

    def test_parent_held_truncation_and_exclusion_block_candidates(self):
        for changes in (dict(parent_calls=1),dict(split='DEV'),dict(teacher_or_l2=True),
                        dict(response=dict(raw='FINAL: 2',terminal=True,truncated=True))):
            row=dict(self.row,**changes)
            result=classify(row,self.task,self.reference,'callhash',dict(correct=True))
            self.assertFalse(result['quality_screen_candidate'])
        self.reference['excluded_ids']=['task']
        self.assertFalse(self.result()['quality_screen_candidate'])

    def test_recorded_success_does_not_override_native_recompute(self):
        result=classify(self.row,self.task,self.reference,'callhash',dict(correct=False))
        self.assertFalse(result['math_native_correct'])
        self.assertFalse(result['outcome_matches_native_recompute'])
        self.assertFalse(result['admitted'])


if __name__=='__main__':
    unittest.main()
