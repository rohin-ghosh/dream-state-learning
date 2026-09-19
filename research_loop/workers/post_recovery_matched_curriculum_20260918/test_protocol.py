from dataclasses import dataclass
import hashlib
from pathlib import Path
import tempfile
import unittest

from protocol import (ARMS, PARENT_INSTRUCTION, Session, TRAIN_IDS, answer_candidate,
    grade_train, parent_message_valid, parent_payload, public_contract, task_public)


@dataclass
class FakeEpisode:
    family: str = 'countdown'
    goal: str = 'Produce a concrete answer.'


@dataclass
class FakeObservation:
    score: float


class FakeGym:
    def split_of(self, identifier):
        return 'train' if identifier in TRAIN_IDS else 'gate'

    def episode_from_id(self, identifier):
        return FakeEpisode()

    def step(self, episode, answer):
        if answer == 'raise':
            raise RuntimeError('PRIVATE KEY MUST NOT BE EXPORTED')
        return FakeObservation(1 if answer == 'concrete answer' else 0)


RECORD = dict(index=10, sha256='a' * 64)


class CurriculumTests(unittest.TestCase):
    def setUp(self):
        self.gym = FakeGym()

    def grade(self, raw, identifier=TRAIN_IDS[0]):
        return grade_train(self.gym, identifier, raw, response_record=RECORD)

    def test_explicit_and_plain_answers_both_reach_native_verifier(self):
        self.assertEqual(answer_candidate('ACT: concrete answer'), ('concrete answer', 'EXPLICIT_SINGLE_ACT'))
        self.assertTrue(self.grade('ACT: concrete answer')['accepted'])
        self.assertTrue(self.grade('concrete answer')['accepted'])

    def test_plan_is_not_rejected_from_learning(self):
        result = self.grade('I will produce the concrete answer.')
        self.assertEqual(result['score'], 0)
        self.assertFalse(result['training_row_excluded'])

    def test_verifier_failure_is_not_zero_or_silence(self):
        result = self.grade('raise')
        self.assertIsNone(result['score'])
        self.assertIn('no judgment', result['feedback'])
        self.assertNotIn('PRIVATE KEY', str(result))

    def test_child_format_never_kills_opportunity(self):
        result = self.grade('ACT: first\nACT: second')
        self.assertEqual(result['parsing'], 'AMBIGUOUS_MARKERS_LITERAL_OUTPUT')
        self.assertEqual(result['status'], 'SCORED')

    def test_no_heldout_questions_or_scores_reach_parent(self):
        with self.assertRaisesRegex(ValueError, 'TRAIN_only'):
            task_public(self.gym, 'rg/n_queens/2000099')
        feedback = self.grade('wrong')
        feedback['task_id'] = 'rg/n_queens/2000099'
        with self.assertRaisesRegex(ValueError, 'TRAIN_only'):
            parent_payload(self.gym, ARMS[0], TRAIN_IDS[0], raw='wrong', feedback=feedback)

    def test_unparented_arm_has_no_parent_turn(self):
        self.assertIsNone(parent_payload(self.gym, 'unparented_learn', TRAIN_IDS[0]))

    def test_same_parenting_policy_does_not_disclose_weight_treatment(self):
        arguments = dict(raw='wrong', feedback=self.grade('wrong'))
        self.assertEqual(parent_payload(self.gym, 'guided_learn', TRAIN_IDS[0], **arguments),
            parent_payload(self.gym, 'guided_frozen', TRAIN_IDS[0], **arguments))

    def test_feedback_must_bind_actual_child_response(self):
        with self.assertRaisesRegex(ValueError, 'actual_child_output'):
            parent_payload(self.gym, ARMS[0], TRAIN_IDS[0], raw='different', feedback=self.grade('wrong'))

    def test_no_reference_answer_or_private_metadata_projection(self):
        result = self.grade('wrong')
        result['answer'] = 'PRIVATE'
        result['private_evaluation'] = 'PRIVATE'
        payload = parent_payload(self.gym, ARMS[0], TRAIN_IDS[0], raw='wrong', feedback=result)
        self.assertNotIn('PRIVATE', str(payload))

    def test_verifier_only_records_actual_response_receipts(self):
        with self.assertRaisesRegex(ValueError, 'actual_response_record'):
            grade_train(self.gym, TRAIN_IDS[0], 'wrong', response_record=dict(index=-1, sha256='bad'))

    def test_each_failed_attempt_has_feedback_and_two_then_branch(self):
        session = Session()
        first = session.apply(self.grade('wrong'))
        self.assertEqual(first['environment_decision'], 'continue')
        second = session.apply(self.grade('wrong'))
        self.assertEqual(second['environment_decision'], 'branch')
        self.assertEqual(session.current_id, TRAIN_IDS[1])

    def test_success_moves_on_without_forced_repetition(self):
        session = Session()
        self.assertEqual(session.apply(self.grade('concrete answer'))['environment_decision'], 'branch')

    def test_receipt_digest_is_not_claimed_corrected_behavior(self):
        result = self.grade('wrong')
        self.assertEqual(len(result['receipt_sha256']), 64)
        self.assertFalse(result['accepted'])

    def test_parent_is_short_and_has_no_evaluation_keys(self):
        self.assertTrue(parent_message_valid(dict(speak=True, message='Check your last step.', rationale='Actual failed attempt.')))
        self.assertFalse(parent_message_valid(dict(speak=True, message='word ' * 161, rationale='')))
        self.assertIn('No sealed results or answer', PARENT_INSTRUCTION)


if __name__ == '__main__':
    unittest.main()
