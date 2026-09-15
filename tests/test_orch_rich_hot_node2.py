import unittest

from organism_v6 import orch_rich_hot_node2 as policy


class HotRichnessTests(unittest.TestCase):
    def test_eight_shards_cover_four_conditions_twice(self):
        self.assertEqual(len(policy.DEVICES), 8)
        self.assertEqual(len(set(policy.UUIDS)), 8)
        self.assertEqual([policy.CONDITIONS[index // 2] for index in range(8)],
                         [condition for condition in policy.CONDITIONS for unused in range(2)])

    def test_high_budget_no_forced_length_or_gold_in_prompts(self):
        task = dict(question='What is 6 times 7?', gold='42')
        self.assertEqual((policy.CAP, policy.CONTEXT, policy.SECONDS), (8192, 16384, 57600))
        for condition in policy.CONDITIONS:
            messages = policy.messages(task, condition)
            self.assertNotIn('150', str(messages))
            self.assertNotIn('400', str(messages))
            self.assertNotIn('42', str(messages))
        previous = 'My actual earlier draft.'
        for condition in ('TWO_PASS', 'META_EVALUATE'):
            self.assertEqual(policy.messages(task, condition, previous)[-2], dict(role='assistant', content=previous))

    def test_unreviewed_long_correct_target_is_not_admitted(self):
        response = dict(raw='FINAL: 42', terminal=True, truncated=False, token_ids=[1] * 900 + [2])
        outcome = policy.outcome(dict(gold='42'), response)
        self.assertTrue(outcome['correct'])
        self.assertEqual(outcome['content_tokens'], 900)
        self.assertFalse(outcome['admitted'])
        self.assertFalse(outcome['trainingAllowed'])
        self.assertEqual(outcome['semantic_status'], 'UNREVIEWED')

    def test_strict_final_and_truncation_are_preserved(self):
        response = dict(raw='Answer FINAL: 42', terminal=True, truncated=False, token_ids=[1, 2])
        self.assertEqual(policy.outcome(dict(gold='42'), response)['category'], 'missing_exact_FINAL')
        response.update(raw='FINAL: 42', terminal=False, truncated=True)
        self.assertEqual(policy.outcome(dict(gold='42'), response)['category'], 'truncation')

    def test_fresh_common_roster_excludes_id_and_question(self):
        records = [dict(question=f'Question {index}?', answer='working #### 42') for index in range(8)]
        roster = policy.roster(records, {'gsm8k-train-0'}, {policy.question_hash('Question 1?')})
        self.assertEqual(roster['denominator'], 6)
        self.assertEqual(roster['max_calls'], 36)
        self.assertEqual(roster, policy.roster(records, {'gsm8k-train-0'}, {policy.question_hash('Question 1?')}))


if __name__ == '__main__':
    unittest.main()
