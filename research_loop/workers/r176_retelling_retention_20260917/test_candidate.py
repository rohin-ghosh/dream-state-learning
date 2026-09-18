from copy import deepcopy
import unittest

import candidate


class FixedRetellingCandidateTests(unittest.TestCase):
    def ready(self,life='C2',sleep=33):
        fields=('checkpoint_complete','original_source_custody_verified','birth_only_context_verified',
            'receiving_copy_verified','private_witness_frozen','private_rubric_frozen','source_and_read_budget_bound')
        return dict(life_id=life,sleep=sleep,**{field:True for field in fields})

    def test_exact_six_each_and_no_initial_or_later_replacement(self):
        slots=candidate.fixed_slots()
        self.assertEqual([row['sleep'] for row in slots if row['life_id']=='C2'],list(range(33,39)))
        self.assertEqual([row['sleep'] for row in slots if row['life_id']=='C5'],list(range(29,35)))
        changed=deepcopy(slots)
        changed[0]['sleep']=39
        with self.assertRaisesRegex(ValueError,'no_replacement'):
            candidate.validate_slots(changed)

    def test_fixed_full_instrument_budget(self):
        resources=candidate.budget()
        self.assertEqual(resources['calls_max'],12*2*3)
        self.assertEqual(resources['generated_tokens_max'],72*512)
        self.assertEqual(resources['condition_processes_max'],24)
        self.assertEqual(resources['baseline_new_calls'],0)
        self.assertFalse(resources['authorized_for_execution'])

    def test_c2_ready_without_c5_or_initial(self):
        result=candidate.eligible(candidate.fixed_slots(),{'C2_sleep_000033':self.ready()},set())
        self.assertEqual(len(result),2)
        self.assertEqual({row['life_id'] for row in result},{'C2'})

    def test_missing_first_sleep_does_not_replace_it_or_block_other_fixed_ready(self):
        receipts={'C2_sleep_000034':self.ready(sleep=34)}
        result=candidate.eligible(candidate.fixed_slots(),receipts,set())
        self.assertEqual({row['sleep'] for row in result},{34})
        self.assertIn(33,[row['sleep'] for row in candidate.fixed_slots() if row['life_id']=='C2'])

    def test_absent_last_checkpoint_never_claimed_ready(self):
        self.assertEqual(candidate.eligible(candidate.fixed_slots(),{},set()),[])

    def test_consumed_failed_or_successful_condition_never_retried(self):
        consumed={'C2_sleep_000033:LORA_ON'}
        rows=candidate.eligible(candidate.fixed_slots(),{'C2_sleep_000033':self.ready()},consumed)
        self.assertEqual([row['condition'] for row in rows],['LORA_OFF'])

    def test_receipt_cannot_relabel_life_or_sleep(self):
        with self.assertRaisesRegex(ValueError,'exact_fixed_receipt_identity'):
            candidate.eligible(candidate.fixed_slots(),{'C2_sleep_000033':self.ready('C5',29)},set())

    def test_private_witness_required_before_new_output(self):
        receipt=self.ready()
        receipt['private_witness_frozen']=False
        self.assertEqual(candidate.eligible(candidate.fixed_slots(),{'C2_sleep_000033':receipt},set()),[])

    def test_absolute_and_ninety_minute_and_lease_clipping(self):
        self.assertEqual(candidate.campaign_end(candidate.END-10000,candidate.END+21600),candidate.END-4600)
        self.assertEqual(candidate.campaign_end(candidate.END-2000,candidate.END+21600),candidate.END)
        self.assertEqual(candidate.campaign_end(candidate.END-4000,candidate.END+20000),candidate.END-1600)
        with self.assertRaisesRegex(ValueError,'full_job'):
            candidate.campaign_end(candidate.END-915,candidate.END+21600)

    def test_new_read_budget_is_finite_separate_and_not_authorized(self):
        resources=candidate.proposed_read_budget()
        self.assertLessEqual(resources['fixed_checkpoint_adapter_read_envelope'],resources['adapter_bytes'])
        self.assertEqual(len(resources['pass_plan']),10)
        self.assertFalse(resources['reuse_old_read_allowances'])
        self.assertFalse(resources['optimizer_or_rng_reads'])
        self.assertEqual(resources['status'],'PROPOSED_ONLY_NEW_R176_PRE_IO_SCOPE_REQUIRED')

    def test_baseline_reuse_requires_every_identity_no_new_generation(self):
        self.assertFalse(candidate.baseline_reuse(dict(calls=3,exact_original_initial_commit=True)))
        self.assertEqual(candidate.budget()['baseline_new_calls'],0)


if __name__=='__main__':
    unittest.main()
