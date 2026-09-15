import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_rich_hot_node3_run as runner
from organism_v6 import orch_math_rich as original
from organism_v6 import orch_rich_hot_node3 as policy
from organism_v6 import orch_rich_intensity as prior


class RichHotNode3Tests(unittest.TestCase):
    def setUp(self):
        self.task = dict(id='train-test', question='Given 2 groups of 3, how many?',
                         gold='6', family='group_accounting')

    def test_owned_six_only(self):
        self.assertEqual([policy.allocation(index) for index in range(6)],
            [('original', 0), ('original', 1), ('light', 0), ('light', 1),
             ('hierarchical', 0), ('hierarchical', 1)])
        for invalid in (-1, 6, 7, True, '0'):
            with self.assertRaises(ValueError):
                policy.allocation(invalid)

    def test_caps_and_full_context_accounting(self):
        policy.context_check(8192)
        for length, cap in ((8193, 8192), (0, 8192), (30, 1536), (30, 8192.0)):
            with self.assertRaises(ValueError):
                policy.context_check(length, cap)

    def test_config_guard(self):
        config = dict(model_type='qwen2', max_position_embeddings=32768,
                      architectures=['Qwen2ForCausalLM'])
        policy.model_config_check(config)
        with self.assertRaises(ValueError):
            policy.model_config_check(dict(config, max_position_embeddings=8192))

    def test_original_prompt_and_oracle_unchanged(self):
        messages, student = policy.prompt(self.task, 'original', 'rich')
        self.assertEqual((messages, student), original.prompt(self.task, 'rich'))
        for text, expected in [('FINAL: 6', True), ('FINAL: 7', False),
                               ('FINAL: 6\nextra', False), ('6', False)]:
            result = dict(raw=text, token_ids=[1] * 1000, terminal=False,
                          truncated=False, prompt_tokens=120)
            row = policy.capture(self.task, 'rich', result, student)
            self.assertEqual(row['outcome_pass'], expected)
            self.assertFalse(row['admitted'] or row['candidate'] or row['trainingAllowed'])
            self.assertEqual(row['target'], text)
            self.assertEqual(row['generated_tokens'], 1000)

    def test_truthful_second_pass_never_receives_gold(self):
        task = dict(self.task, gold='999999_SECRET_GOLD')
        own = 'My own provisional answer is wrong. FINAL: 123'
        messages, _ = policy.prompt(task, 'hierarchical', 'self_evaluation', own)
        self.assertEqual(messages[-2], dict(role='assistant', content=own))
        self.assertIn('your own first pass', messages[-1]['content'])
        self.assertNotIn(task['gold'], json.dumps(messages))
        with self.assertRaises(ValueError):
            policy.prompt(task, 'hierarchical', 'self_evaluation')

    def test_followups_frozen_before_calls(self):
        for outcome in (True, False):
            self.assertEqual(policy.followup('hierarchical', outcome), 'self_evaluation')
            for condition in ('original', 'light'):
                self.assertEqual(policy.followup(condition, outcome), 'new_record' if outcome else None)
        self.assertEqual(policy.prompt(self.task, 'light', 'rich'),
                         policy.prompt(self.task, 'hierarchical', 'rich'))

    def test_own_record_routes_to_existing_record_class(self):
        own = 'I computed two groups of three.\nFINAL: 6'
        for condition in ('original', 'light'):
            self.assertEqual(policy.prompt(self.task, condition, 'new_record', own),
                             original.prompt(self.task, 'record', own))

    def test_cohort_is_fixed_training_only_paired(self):
        roster = Path('research_notes/analysis/orch_rich_intensity_20260915_attempt1/TASKS.json')
        self.assertEqual(runner.sha(roster), policy.TASKS_SHA)
        document = json.loads(roster.read_text())
        prior.validate(document)
        self.assertEqual(len(document['tasks'][0::2]), 128)
        self.assertTrue(all(task['id'].startswith('gsm8k-train-') for task in document['tasks']))

    def test_budget_persists_and_does_not_reset(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(policy, 'MAX_CALLS', 2):
                self.assertEqual(runner.reserve(root, dict(task_id='one'))['global_call'], 1)
                self.assertEqual(runner.reserve(root, dict(task_id='two'))['global_call'], 2)
                with self.assertRaises(RuntimeError):
                    runner.reserve(root, dict(task_id='three'))
            self.assertEqual(len((root / 'CALL_RESERVATIONS.jsonl').read_text().splitlines()), 2)

    def test_no_old_engine_cap_mutation(self):
        self.assertEqual(prior.generation_cap('control', 'rich'), 512)
        self.assertEqual(prior.CONTEXT_LIMIT, 4096)
        self.assertEqual(policy.protocol()['maximum_this_batch_calls'], 1536)
        self.assertLessEqual(1536, policy.MAX_CALLS)


if __name__ == '__main__':
    unittest.main()
