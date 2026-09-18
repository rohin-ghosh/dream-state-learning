"""Synthetic prompt and shape regressions; no provider or learner calls."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

HOME = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('r184_forward_test', HOME / 'r184_parent_forward.py')
forward = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(forward)


class ForwardTests(unittest.TestCase):
    def test_three_questions_only(self):
        forward.question_shape('1. What would further thinking distinguish?\n2. What would you try or keep doing?\n3. What observation would change that choice?')

    def test_answers_missing_questions_and_baselines_rejected(self):
        for message in ('Here is the answer.\n1. Why?\n2. What?\n3. How?', '1. Why?\n2. How?',
                        '1. Why? Because yes.\n2. How?\n3. What?', forward.raw.BASELINE_END):
            with self.assertRaises(ValueError):
                forward.question_shape(message)

    def test_effort_both_ways_and_child_choice_prompt_only(self):
        payload = {'synthetic': True}
        policy = SimpleNamespace(prompt=lambda *args: ('original private validators', payload),
            decision=lambda *args: {'valid': True})
        forward.bind(policy)
        instruction, returned = policy.prompt({}, {}, {})
        self.assertIs(returned, payload)
        self.assertIn('original private validators', instruction)
        self.assertIn('More thought is not automatically better', instruction)
        self.assertIn('acting sooner is not automatically better', instruction)
        self.assertIn('staying with the present approach', instruction)

    def test_silence_and_original_rejection_preserved(self):
        policy = SimpleNamespace(prompt=lambda *args: ('', {}), decision=lambda *args: None)
        forward.bind(policy)
        self.assertIsNone(policy.decision({'speak': False}, {}, {}))
        def rejected(*args):
            raise ValueError('original_private_evidence_rejected')
        policy = SimpleNamespace(prompt=lambda *args: ('', {}), decision=rejected)
        forward.bind(policy)
        with self.assertRaisesRegex(ValueError, 'original_private_evidence_rejected'):
            policy.decision({'message': '1. Why?\n2. How?\n3. What?'}, {}, {})

    def test_assignments_cadence_and_raw_release_unchanged(self):
        self.assertEqual(forward.ARMS, {0: ('B', 2), 1: ('B', 2), 3: ('D', 3), 4: ('A', 1)})
        self.assertEqual(forward.raw.ready(dict(caught_up=True, delivered={})), 'AWAITING_MAIN_ORIGINAL_BASELINE_RENDER')

    def test_three_sleep_withdrawal_preserves_original_exposure_clock(self):
        for physical in (0, 3, 4):
            self.assertTrue(forward.phase_hold(physical, {'baseline_completed_sleeps': 40},
                dict(delivered={}, sleep_count=43)))
            self.assertFalse(forward.phase_hold(physical, {'baseline_completed_sleeps': 40},
                dict(delivered={}, sleep_count=44)))
        state = dict(delivered={forward.raw.TURN: {'sleep_count': 41}}, sleep_count=44)
        self.assertTrue(forward.phase_hold(1, {'baseline_completed_sleeps': 43}, state))


if __name__ == '__main__':
    unittest.main()
