import unittest
from unittest.mock import patch
import tempfile
import json
from pathlib import Path
from organism_v6 import orch_r109_l1_generation_policy as policy
from gpu import orch_r109_l1_generation_v3 as runner


class GenerationV3Tests(unittest.TestCase):
    def test_discretion_no_forced_budget_or_revisitation(self):
        for condition in policy.GUIDANCE:
            text=policy.guidance(condition)
            self.assertIn('options, not required steps',text)
            self.assertNotIn('exhaust',text.lower())
            self.assertNotIn('linear',text.lower())
        self.assertIn('may simply finish',policy.opportunity())

    def test_markers_match_v3_and_no_code_json_substitution(self):
        self.assertEqual(policy.first_answer_end('FINAL: 4\nMore','math'),8)
        self.assertIsNone(policy.first_answer_end('{"expression":"x"}','code'))
        self.assertIsNotNone(policy.first_answer_end('```py\nx\n```','code'))

    def metric(self, ids, **changes):
        options=dict(final=True,terminal=True,cap_hit=False,total_generated=len(ids)+1,budget=256)
        options.update(changes)
        return policy.measure(ids,20,**options)

    def test_novel64_plus_final_within_budget(self):
        self.assertTrue(self.metric(list(range(84)))['persistence'])
        self.assertFalse(self.metric(list(range(83)))['persistence'])

    def test_cap_hit_counts_against_even_with_final(self):
        self.assertFalse(self.metric(list(range(100)),cap_hit=True)['persistence'])
        self.assertFalse(self.metric(list(range(100)),budget=101)['persistence'])
        self.assertFalse(self.metric(list(range(100)),terminal=False)['persistence'])
        self.assertFalse(self.metric(list(range(100)),final=False)['persistence'])

    def test_repetition_not_persistence_or_admission(self):
        value=self.metric(list(range(20))*5)
        self.assertFalse(value['persistence'])
        self.assertGreater(value['rep4_self'],.5)
        self.assertFalse(value['functional_admission'])

    def test_no_training_cards_gpu7_or_new_node(self):
        self.assertEqual(runner.LANES,{'node1':list(range(7)),'node2':[4]})
        self.assertEqual(runner.END,1789491360)

    def test_numeric_final_cannot_be_punctuation_only(self):
        self.assertFalse(policy.final_present('FINAL: $.,/','math'))
        self.assertTrue(policy.final_present('FINAL: 8','math'))

    def test_boundary_rejects_started_next_call(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'PROGRESS.json').write_text(json.dumps(dict(calls=2)))
            (root/'CALL_000002.json').write_text('{}')
            self.assertTrue(runner.complete_boundary(root)[0])
            (root/'INTENT_000003.json').write_text('{}')
            self.assertFalse(runner.complete_boundary(root)[0])

    def test_signal_acknowledged_before_boundary_recheck(self):
        with patch.object(runner,'stopped',side_effect=[False,True]) as check, patch.object(runner.time,'sleep'):
            runner.wait_stopped(123)
            self.assertEqual(check.call_count,2)
        with patch.object(runner,'stopped',return_value=False), patch.object(runner.time,'monotonic',side_effect=[0,3]):
            with self.assertRaises(TimeoutError):runner.wait_stopped(123)

    def test_actual_messages_are_discretionary(self):
        task = dict(family='math',payload=dict(question='What is 2 + 2?'))
        messages = runner.messages(task,'PERSISTENCE','FINAL: 4')
        self.assertIn('options, not required steps',messages[0]['content'])
        self.assertIn('may simply finish',messages[-1]['content'])
        self.assertNotIn('exhaust',' '.join(row['content'] for row in messages).lower())


if __name__ == '__main__':unittest.main()
