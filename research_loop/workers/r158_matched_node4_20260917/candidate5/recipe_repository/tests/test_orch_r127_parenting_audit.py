import unittest
from types import SimpleNamespace

from gpu.orch_r127_parenting_audit import dose_reduction, encoding_check, parent_presence, target_text_binding


class ParentingAuditTests(unittest.TestCase):
    def row(self, target):
        return dict(input_ids=[7]+target+[9],labels=[-100]+target+[-100],target_ids=target)

    def test_target_interval_excludes_prefix_suffix(self):
        self.assertEqual(encoding_check(self.row([2,3])),2)

    def test_parent_prefix_supervision_rejected(self):
        row=self.row([2,3]);row['labels'][0]=7
        with self.assertRaises(ValueError):
            encoding_check(row)

    def test_disjoint_target_intervals_rejected(self):
        row=self.row([2,3,4]);row['labels'][2]=-100
        with self.assertRaises(ValueError):
            encoding_check(row)

    def test_equal_updates_unequal_token_dose(self):
        first=dose_reduction([self.row([2])],[dict(update=1,rows=[0,0,0,0],active=4)])
        second=dose_reduction([self.row([2,3])],[dict(update=1,rows=[0,0,0,0],active=8)])
        self.assertEqual(first['updates'],second['updates'])
        self.assertNotEqual(first['total_supervised_token_presentations'],second['total_supervised_token_presentations'])

    def test_measured_active_tokens_checked(self):
        with self.assertRaises(ValueError):
            dose_reduction([self.row([2])],[dict(update=1,rows=[0,0,0,0],active=3)])

    def test_generation_presence_not_metadata_presence(self):
        self.assertFalse(parent_presence([dict(role='user',content='public experience')],'private guidance'))
        self.assertTrue(parent_presence([dict(role='user',content='public\nprivate guidance')],'private guidance'))

    def test_zero_yield_no_dose(self):
        self.assertEqual(dose_reduction([],[])['total_supervised_token_presentations'],0)

    def test_lossless_retokenization_is_not_changed_child_text(self):
        tokenizer=SimpleNamespace(decode=lambda ids,**kwargs:'same<|im_end|>',
            encode=lambda text,**kwargs:SimpleNamespace(ids=[2]),token_to_id=lambda text:3)
        self.assertFalse(target_text_binding(dict(target_ids=[2,3]),
            dict(response=dict(raw='same',token_ids=[8,3])),tokenizer))

    def test_changed_supervision_text_is_rejected(self):
        tokenizer=SimpleNamespace(decode=lambda ids,**kwargs:'different<|im_end|>')
        with self.assertRaisesRegex(ValueError,'supervised_child_bytes'):
            target_text_binding(dict(target_ids=[2,3]),dict(response=dict(raw='same',token_ids=[8,3])),tokenizer)


if __name__ == '__main__':
    unittest.main()
