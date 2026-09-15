import unittest

from organism_v6 import orch_rich_hot_node1_prompt_v2 as policy


class NextPromptTests(unittest.TestCase):
    def test_no_voice_or_length_constraint(self):
        task = dict(question='How many are 6 groups of 7?', gold='HIDDEN_GOLD')
        for condition in policy.CONDITIONS:
            cases = [policy.messages(task, condition)]
            if condition in policy.SECOND:
                cases.append(policy.messages(task, condition, 'The actual earlier draft.'))
            for messages in cases:
                text = ' '.join(message['content'] for message in messages)
                self.assertNotIn('first-person', text)
                self.assertNotIn('150', text)
                self.assertNotIn('400', text)
                self.assertNotIn('HIDDEN_GOLD', text)
                self.assertIn('genuinely relevant', text)
                self.assertIn('Do not fabricate alternatives', text)
                instruction = messages[-1]['content'] if len(messages) > 2 else messages[0]['content']
                self.assertLess(instruction.index(policy.BRANCH), instruction.index(policy.FINAL))

    def test_own_previous_response_is_unmodified(self):
        raw = 'An unverified first answer. FINAL: 17'
        for condition in policy.SECOND:
            messages = policy.messages(dict(question='Task'), condition, raw)
            self.assertEqual(messages[-2], dict(role='assistant', content=raw))
            self.assertIn('not an external answer or a verified solution', messages[-1]['content'])

    def test_short_and_long_outputs_not_voice_or_length_gated(self):
        for count in (2, 100, 401, 3000):
            result = policy.outcome(dict(gold='42'), dict(raw='FINAL: 42', terminal=True,
                truncated=False, token_ids=[1] * count))
            self.assertTrue(result['correct'])
            self.assertFalse(result['admitted'] or result['trainingAllowed'])

    def test_semantics_not_keywords_and_no_review_hold(self):
        contract = policy.review_contract()
        self.assertFalse(contract['keyword_only_counting_allowed'])
        self.assertFalse(contract['review_blocks_generation'])
        self.assertFalse(contract['auto_admission'])
        self.assertTrue(contract['not_relevant_is_not_failure'])
        self.assertEqual((contract['raw_batch_size'], contract['sample_size']), (64, 12))
        self.assertEqual((policy.CAP, policy.CONTEXT), (8192, 16384))


if __name__ == '__main__':
    unittest.main()
