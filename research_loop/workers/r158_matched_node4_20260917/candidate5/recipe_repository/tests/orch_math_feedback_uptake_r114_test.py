"""CPU regressions for the prospective F2 v4 delta."""

import tempfile
import unittest
from pathlib import Path

from organism_v6 import orch_math_feedback_uptake_r114 as policy


class V4Tests(unittest.TestCase):
    def test_exact_v4_template_extracted_from_snapshot(self):
        repository = Path(__file__).resolve().parents[1]
        text = (repository / policy.AREA / 'BATTLE_PLAN_V4.md').read_text()
        block = text.split('> You are the parent of a young model.', 1)[1].split('\n\nOutput:', 1)[0]
        expected = 'You are the parent of a young model.' + '\n'.join(
            line[2:] if line.startswith('> ') else line for line in block.split('\n')) + '\n'
        self.assertEqual((repository / policy.AREA / 'PARENT_TEMPLATE_V4.txt').read_text(), expected)
        prompt = policy.parent_template(repository)
        self.assertIn('Use the feedback the child itself received', prompt)
        self.assertIn('broad permission', prompt)
        self.assertIn("allow the child's own useful organisation", prompt)
        self.assertIn('[SILENT]', prompt)

    def test_reflection_is_config_not_unauthorized_fixed_prompt_edit(self):
        repository = Path(__file__).resolve().parents[1]
        self.assertEqual(policy.parent_template(repository),
            policy.parent_template(repository, dict(policy.FIELDS, REFLECTION='short')))
        with self.assertRaises(ValueError):
            policy.parent_template(repository, dict(policy.FIELDS, REFLECTION='score-selected'))

    def test_old_three_child_prompts_unchanged(self):
        for purpose, question in [('episode', 'Question'), ('presleep', None), ('reflection', None)]:
            self.assertEqual(policy.messages(purpose, question), policy.original.messages(purpose, question))

    def test_open_and_focused_exact_bytes(self):
        self.assertEqual(policy.messages('open_turn')[-1]['content'], 'The task is over; the environment is still here.')
        self.assertEqual(policy.messages('focused', 'Question')[-1]['content'], 'Question\n\nfocus and give the answer')
        with self.assertRaises(ValueError):
            policy.messages('open_turn', 'extra task')

    def test_two_episodes_each_open_parent_slot_then_boundary_without_parent(self):
        plan = policy.cycle_plan(1)
        self.assertEqual([item['phase'] for item in plan[:6]],
            ['episode', 'open_turn', 'episode', 'open_turn', 'presleep', 'reflection'])
        self.assertEqual(sum(item['parent_slot'] for item in plan), 6)
        for item in plan[6:8]:
            self.assertFalse(item['parent_slot'])
            self.assertFalse(item['parent_context_visible'])
            self.assertTrue(item['after_context_boundary'])

    def test_readout_and_task_decoders_not_reflection_constrained(self):
        for purpose in ('open_turn', 'focused', 'held', 'episode'):
            self.assertEqual(policy.decoder(purpose)['no_repeat_ngram_size'], 0)
        self.assertEqual(policy.decoder('reflection')['no_repeat_ngram_size'], 8)
        self.assertEqual(policy.decoder('focused')['max_new_tokens'], 2048)

    def test_focused_first_two_dev_independent_of_outcomes(self):
        tasks = [dict(id=str(index), split='DEV', question='Q', question_sha256='a' * 64) for index in range(8)]
        self.assertEqual([task['id'] for task in policy.focused_tasks(tasks)], ['0', '1'])
        with self.assertRaises(ValueError):
            policy.focused_tasks([dict(task, split='FINAL') for task in tasks])

    def test_all_calls_counted_without_extra_quota(self):
        self.assertEqual(policy.CYCLES, 63)
        self.assertEqual(len(policy.cycle_plan(1)), 18)
        self.assertEqual(policy.SLEEP0_CALLS + policy.CYCLES * policy.CYCLE_CALLS + policy.FINAL_CALLS, 1160)
        self.assertLessEqual(policy.CYCLES * 6, policy.PARENT_CAP)
        with self.assertRaises(ValueError):
            policy.cycle_plan(64)

    def test_final_corrected_date_and_same_hard_wall(self):
        self.assertEqual(policy.MORNING, 1789491600.0)
        with tempfile.TemporaryDirectory() as root:
            for now in (policy.MORNING - 1, policy.original.HARD_END, policy.previous.MORNING):
                with self.assertRaises(ValueError):
                    policy.reserve_final(root, 'morning', now, 'a' * 64, 100)
            policy.reserve_final(root, 'morning', policy.MORNING, 'a' * 64, 1152)
            with self.assertRaises(FileExistsError):
                policy.reserve_final(root, 'morning', policy.MORNING + 1, 'a' * 64, 1152)

    def test_final_budget_and_sleep0_order(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(ValueError):
                policy.reserve_final(root, 'morning', policy.MORNING, 'a' * 64, 1161)
            with self.assertRaises(ValueError):
                policy.reserve_final(root, 'sleep0', policy.MORNING - 3600, 'a' * 64, 0, episodes_started=1)
            with self.assertRaises(ValueError):
                policy.reserve_final(root, 'cycle', policy.MORNING - 3600, 'a' * 64, 0)

    def test_r112_gate_remains_explicit_exact_contract(self):
        release = dict(released=True, uuid=policy.original.MEMBERS['FABLE']['uuid'])
        with self.assertRaises(ValueError):
            policy.require_done('FABLE', release, {}, 'newhash')
        relay = dict(approved_by='Rohin', relayed_by='Fable', decision='DONE',
            common_contract_sha256='oldhash', source_reference='explicit relay')
        with self.assertRaises(ValueError):
            policy.require_done('FABLE', release, relay, 'newhash')
        policy.require_done('FABLE', release, dict(relay, common_contract_sha256='newhash'), 'newhash')

    def test_no_sleep_no_semantic_auto_admission_or_final_export(self):
        common = policy.contract(Path(__file__).resolve().parents[1])
        self.assertFalse(common['sleep_updates_implemented'])
        self.assertEqual(common['weight_updates'], 0)
        self.assertEqual(common['head_editable_fields'], ['FOCUS', 'STYLE', 'REFLECTION'])
        self.assertEqual(common['semantic_labels_default'], 'UNKNOWN_UNTIL_SHARED_JUDGE_OR_AUTHOR_REVIEW')
        self.assertTrue(common['no_outcome_quality_gate'])
        for surface in ('PARENT', 'HEAD', 'EXCHANGE'):
            self.assertFalse(policy.readout_access('FINAL', surface, 'morning'))


if __name__ == '__main__':
    unittest.main()
