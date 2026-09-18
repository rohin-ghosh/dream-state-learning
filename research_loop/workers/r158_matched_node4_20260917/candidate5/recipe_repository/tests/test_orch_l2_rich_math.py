import unittest
from unittest.mock import patch

from organism_v6 import orch_l2_rich_math as policy
from organism_v6.experienced_event_goal_replay_layout import GoalReplayLayout
from gpu import orch_l2_rich_math_parent as parent


class RichMathTests(unittest.TestCase):
    def test_fixed_unique_stage_cohort_and_reference(self):
        cohort = policy.cohort()
        self.assertEqual(cohort, policy.cohort())
        self.assertEqual([len(stage) for stage in cohort['train']], [8] * 3)
        self.assertEqual([len(stage) for stage in cohort['held']], [8] * 4)
        tasks = [task for groups in (cohort['train'], cohort['held']) for group in groups for task in group]
        self.assertEqual(len({task['question'] for task in tasks}), 56)
        for task in tasks:
            answer = policy.reference(task)
            self.assertTrue(policy.judge(task, f'My calculation.\nFINAL: {answer}')['correct'])
            self.assertFalse(policy.judge(task, f'FINAL: {answer + 1}')['correct'])
            self.assertFalse(policy.judge(task, f'The answer is {answer}')['correct'])
            self.assertEqual(task['family'], 'PM_CONGRUENCE_JOIN_V1')

    def test_same_bootstrap_schedule_new_labels_only_masked(self):
        layout = GoalReplayLayout(16, policy.BOOTSTRAP_PRESENTATIONS)
        self.assertEqual(layout.updates, 224)
        full = layout.manifest('FULL_TARGET')
        off = layout.manifest('NEW_TRAJECTORY_LOSS_OFF')
        self.assertEqual(full['row_presentations'], off['row_presentations'])
        self.assertEqual(full['row_presentations'][-16:], [16] * 16)
        self.assertEqual(off['masked_row_indexes'], list(range(222, 238)))
        self.assertEqual(full['new_supervised_presentations'], 256)
        self.assertEqual(off['new_supervised_presentations'], 0)

    def test_declared_global_budget_has_room_for_fixed_retention(self):
        experiences = 3 * 3 * 8 * 4
        held_and_retention = 4 * 4 * (8 + 48)
        self.assertEqual(experiences + held_and_retention, 1184)
        self.assertLessEqual(experiences + held_and_retention, policy.LEARNER_CALLS)
        self.assertEqual((48 + 36) * 2, 168)
        self.assertLessEqual((48 + 36) * 2, policy.PARENT_CALLS)

    def test_actual_history_parent_stripping_and_bounded_requests(self):
        task = policy.cohort()['train'][0][0]
        calls, coaches = [], []

        def generate(messages, **metadata):
            response = dict(raw=f'I checked both given constraints.\nFINAL: {task["reference_answer"]}',
                            token_ids=[7] * 200 + [8], terminal=True, truncated=False, prompt_tokens=200)
            calls.append(messages)
            return response, len(calls)

        def coach(payload):
            parent.validate(payload)
            coaches.append(payload)
            return dict(speak=True, message='PRIVATE COACH WORDS', rationale='check constraints')

        result = policy.experience(task, generate, coach)
        self.assertEqual(len(calls), 4)
        self.assertEqual(len(coaches), 1)
        self.assertIn('PRIVATE COACH WORDS', str(calls[1]))
        self.assertNotIn('PRIVATE COACH WORDS', str([row['student_prefix'] for row in result['captures']]))
        self.assertNotIn(policy.GUIDANCE, str([row['student_prefix'] for row in result['captures']]))
        self.assertEqual(result['captures'][1]['student_prefix'][1]['content'], result['captures'][0]['target'])
        self.assertNotIn('exact-answer checker', str(result['captures'][-1]['student_prefix']))
        parent.validate(policy.review_payload(result['captures']))

    def test_no_reflection_after_failed_final_and_no_unread_admission(self):
        task = policy.cohort()['train'][0][0]

        def generate(messages, **metadata):
            return dict(raw='FINAL: -1', token_ids=[7] * 200 + [8], terminal=True,
                        truncated=False, prompt_tokens=200), metadata.get('attempt', 3)

        result = policy.experience(task, generate)
        self.assertEqual(len(result['captures']), 3)
        self.assertFalse(result['final_correct'])
        self.assertEqual(policy.review_payload(result['captures'])['candidates'], [])
        self.assertFalse(any(row['admitted'] for row in policy.admit_reviews(result['captures'], {})))

    def test_parent_rejects_sealed_or_solution_metadata(self):
        task = policy.cohort()['held'][0][0]
        payload = dict(kind='coach', task_id=task['id'], question=task['question'],
                       messages=[], outcome_correct=False, learner={})
        with self.assertRaises(AssertionError):
            parent.validate(payload)
        payload['task_id'] = policy.cohort()['train'][0][0]['id']
        payload['reference_answer'] = task['reference_answer']
        with self.assertRaises(AssertionError):
            parent.validate(payload)

    def test_admission_keeps_exact_existing_prefix_and_gold_contract(self):
        row = dict(index=7, candidate=True)
        response = dict(reviews=[dict(index=7)])
        with patch.object(policy.admission, 'admit', return_value=dict(admitted=False)) as admit:
            self.assertEqual(policy.admit_reviews([row], response), [dict(admitted=False)])
            admit.assert_called_once_with(row, response['reviews'][0], dict(status='VALID'))


if __name__ == '__main__':
    unittest.main()
