import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu.orch_l2_budget_readout_run import call_plan, reserve
from gpu.orch_l2_budget_readout_scan import existing
from organism_v6 import orch_l2_budget_readout as policy


class BudgetReadoutTests(unittest.TestCase):
    def test_fresh_deterministic_cohort_excludes_original_56(self):
        previous = policy.original.cohort()
        cohort = policy.cohort(previous)
        self.assertEqual(cohort, policy.cohort(previous))
        keys = {policy.task_key(task) for task in cohort['tasks']}
        self.assertEqual(len(keys), 16)
        self.assertFalse(keys.intersection(map(tuple, cohort['excluded_keys'])))
        self.assertEqual(len(cohort['excluded_keys']), 56)
        self.assertEqual(len({task['question'] for task in cohort['tasks']}), 16)

    def test_original_oracle_and_exact_neutral_question(self):
        for task in policy.cohort(policy.original.cohort())['tasks']:
            self.assertEqual(task['question'], policy.original.question(task))
            solutions = [value for value in range(task['left_modulus'] * task['right_modulus'])
                         if value % task['left_modulus'] == task['left_residue']
                         and value % task['right_modulus'] == task['right_residue']]
            self.assertEqual(solutions, [task['reference_answer']])

    def test_cohort_survives_json_roundtrip_without_task_changes(self):
        cohort = policy.cohort(policy.original.cohort())
        self.assertEqual(json.loads(json.dumps(cohort)), cohort)

    def test_retention_once_with_all_cases_and_original_cap(self):
        legacy = dict(old_bank=[dict(event=str(index)) for index in range(16)], old_episodes=[{}] * 16,
                      held=dict(cases=[dict(case_sha256=str(index)) for index in range(16)]))
        with patch('gpu.orch_l2_budget_readout_run.old.memory.memory_messages', side_effect=lambda event, view: [dict(role='user', content=event + ':' + str(view))]), \
             patch('gpu.orch_l2_budget_readout_run.old.memory.audit._messages', side_effect=lambda case, coached: [dict(role='user', content=case['case_sha256'])]):
            order = call_plan(policy.cohort(policy.original.cohort()), legacy)
        self.assertEqual(len(order), 80)
        self.assertEqual([row['position'] for row in order], list(range(80)))
        self.assertEqual(sum(row['kind'] == 'math' for row in order), 32)
        self.assertEqual(sum(row['kind'] == 'retention' for row in order), 32)
        self.assertEqual(sum(row['kind'] == 'audit' for row in order), 16)
        self.assertTrue(all(row['max_new_tokens'] == 512 for row in order[32:]))
        for position in range(0, 32, 2):
            self.assertEqual(order[position]['messages'], order[position + 1]['messages'])
            self.assertEqual({order[position]['max_new_tokens'], order[position + 1]['max_new_tokens']}, {512, 1536})

    def test_missing_retention_case_is_rejected(self):
        legacy = dict(old_bank=[], old_episodes=[], held=dict(cases=[]))
        with self.assertRaisesRegex(ValueError, 'full_legacy_memory_required'):
            call_plan(policy.cohort(policy.original.cohort()), legacy)

    def test_alternating_budget_order_and_call_budget(self):
        cohort = policy.cohort(policy.original.cohort())
        for position, budgets in enumerate(cohort['budget_order']):
            self.assertEqual(budgets, [512, 1536] if position % 2 == 0 else [1536, 512])
        self.assertEqual(4 * (16 * 2 + 48), policy.MAX_CALLS)
        self.assertEqual(policy.CALLS_PER_ARM, 80)
        self.assertEqual(4 * policy.SECONDS / 3600, 4)

    def test_no_prose_inference_and_no_training_token_gate(self):
        task = policy.cohort(policy.original.cohort())['tasks'][0]
        response = dict(raw=f"Both conditions hold. FINAL: {task['reference_answer']}", terminal=True, truncated=False)
        self.assertEqual(policy.score(task, response)['category'], 'missing_exact_FINAL')
        response['raw'] = f"FINAL: {task['reference_answer']}"
        response['content_tokens'] = 800
        self.assertTrue(policy.score(task, response)['correct'])

    def test_truncated_wrong_and_nonterminal_remain_failures(self):
        task = policy.cohort(policy.original.cohort())['tasks'][0]
        response = dict(raw=f"FINAL: {task['reference_answer']}", terminal=False, truncated=True)
        self.assertEqual(policy.score(task, response)['category'], 'truncation')
        response['truncated'] = False
        self.assertEqual(policy.score(task, response)['category'], 'nonterminal_other')
        response.update(raw=f"FINAL: {task['reference_answer'] + 1}", terminal=True)
        self.assertEqual(policy.score(task, response)['category'], 'parsed_wrong')

    def test_duplicate_dispatch_is_rejected_without_budget_reset(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'reservations').mkdir()
            planned = dict(position=0, kind='math', max_new_tokens=512, messages=[])
            row = reserve(root, policy.ARMS[0], planned, 1, 2)
            self.assertEqual(row['global_index'], 0)
            with self.assertRaises(FileExistsError):
                reserve(root, policy.ARMS[0], planned, 1, 2)
            self.assertEqual(len((root / 'CALLS.jsonl').read_text().splitlines()), 1)
            with self.assertRaisesRegex(ValueError, 'global_deadline'):
                reserve(root, policy.ARMS[0], dict(planned, position=1), 2, 2)

    def test_call_321_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'reservations').mkdir()
            (root / 'CALLS.jsonl').write_text('{}\n' * 320)
            with self.assertRaisesRegex(ValueError, 'global_320_call_cap'):
                reserve(root, policy.ARMS[0], dict(position=0), 1, 2)
            self.assertFalse(list((root / 'reservations').iterdir()))

    def test_paired_summary_keeps_incomplete_denominators(self):
        records = [dict(arm=policy.ARMS[0], kind='math', task_id='new', max_new_tokens=512,
                        score=dict(correct=False, category='truncation')),
                   dict(arm=policy.ARMS[0], kind='math', task_id='new', max_new_tokens=1536,
                        score=dict(correct=True, category='registered_correct'))]
        summary = policy.summarize(records)[policy.ARMS[0]]
        self.assertEqual(summary['paired_outcomes'], {'1536_only': 1})
        self.assertEqual(summary['budgets']['512']['denominator'], 16)
        self.assertEqual(summary['budgets']['512']['completed'], 1)

    def test_privileged_scanner_never_waives_unreadable_process(self):
        snapshot = dict(gpu=dict(index=2, uuid=policy.DEVICES[policy.ARMS[2]][1], memory_used_mib=0,
                                utilization_percent=0), compute_processes=[], processes=[dict(pid=123, unreadable=True)])
        reasons = existing.evaluate_snapshot(snapshot, 2, policy.DEVICES[policy.ARMS[2]][1])
        self.assertIn('unknown_process_visibility:123', reasons)


if __name__ == '__main__':
    unittest.main()
