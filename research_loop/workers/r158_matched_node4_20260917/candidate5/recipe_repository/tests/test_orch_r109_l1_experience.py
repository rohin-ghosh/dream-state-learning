import unittest

from gpu import orch_r109_l1_experience as experience


class ExperienceTests(unittest.TestCase):
    def test_sparse_eligible_every8_updates_no_seed_reset(self):
        slots = [experience.positions(update,9444,3635,4) for update in range(9445,9573)]
        self.assertEqual(sum(row[3][0]=='eligible' for row in slots),16)
        self.assertEqual([row[3][1] for row in slots if row[3][0]=='eligible'],list(range(4))*4)
        self.assertTrue(all(row[2][0]=='anchor' for row in slots))
        self.assertEqual(slots[0][0],('legacy',9444%210))

    def test_control_masks_only_new_experience(self):
        labels=[-100,3,4]
        self.assertEqual(experience.labels_for('CONTROL','eligible',labels),[-100]*3)
        for source in ('anchor','legacy','prior'):
            self.assertEqual(experience.labels_for('CONTROL',source,labels),labels)
        self.assertEqual(experience.labels_for('FULL','eligible',labels),labels)
        self.assertEqual(labels,[-100,3,4])

    def test_boundary_requires_whole_task_and_no_pending_call(self):
        self.assertTrue(experience.boundary({'calls':10},10,10,0))
        self.assertFalse(experience.boundary({'calls':9},10,10,0))
        self.assertFalse(experience.boundary({'calls':10},10,11,0))
        self.assertFalse(experience.boundary({'calls':10},10,10,1))

    def test_no_extra_cards_or_lifetime(self):
        self.assertEqual(experience.SLOTS,{'FULL':5,'CONTROL':6})
        self.assertEqual(experience.END,1789491360)
        self.assertEqual(experience.CUTOFF,1789491060)

    def test_review_rejects_unknown_teacher_held_truncation(self):
        review=dict(full_text_read=True,functional_verdict='PASS',grounding_verdict='PASS',evidence='Actual operation used',property='TASK_CONSTRAINT_USED',source_task_id='train1')
        row=dict(source_label=experience.SOURCE_LABEL,split='TRAIN',parent_calls=0,family='math',source_task_id='train1',response=dict(terminal=True,truncated=False),outcome=dict(correct=True))
        experience.review_gate(review,row,{'id':'train1'})
        for change in (dict(full_text_read=False),dict(functional_verdict='UNKNOWN'),dict(evidence='')):
            with self.assertRaises(AssertionError):experience.review_gate(dict(review,**change),row,{'id':'train1'})
        for change in (dict(split='HELD'),dict(parent_calls=1),dict(source_label='R109_CORRECTED_L2_CHILD_CONTINUATION'),dict(response=dict(terminal=True,truncated=True))):
            with self.assertRaises(AssertionError):experience.review_gate(review,dict(row,**change),{'id':'train1'})

    def test_format_only_correction_is_not_arithmetic_correction(self):
        review=dict(full_text_read=True,functional_verdict='PASS',grounding_verdict='PASS',evidence='Check',property='ARITHMETIC_ERROR_CORRECTED',source_task_id='train1')
        row=dict(source_label=experience.SOURCE_LABEL,split='TRAIN',parent_calls=0,family='math',source_task_id='train1',task_id='call1',response=dict(terminal=True,truncated=False),outcome=dict(correct=True,answer='10'))
        draft=dict(task_id='call1',outcome=dict(category='missing_exact_FINAL',answer=None))
        with self.assertRaises(AssertionError):experience.review_gate(review,row,{'id':'train1'},draft)


if __name__=='__main__':
    unittest.main()
