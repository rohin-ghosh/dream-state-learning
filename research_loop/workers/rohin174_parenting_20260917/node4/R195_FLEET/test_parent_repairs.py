import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from parent_repairs import evidence_prompt, new_opening, single_parent, tick_once


class ParentRepairTests(unittest.TestCase):
    def test_duplicate_completed_boundary_never_replays_provider(self):
        with tempfile.TemporaryDirectory() as temporary:
            attempts = Path(temporary)
            (attempts / 'parent_000000000006').mkdir()
            policy = Mock()
            result = tick_once(policy, None, {}, attempts, {}, dict(request_count=6))
            self.assertEqual(result['status'], 'EXISTING_BOUNDARY_ATTEMPT_PRESERVED')
            policy.local_attempts.assert_called_once_with(attempts)
            policy.tick.assert_not_called()

    def test_unfinished_attempt_still_fails_closed_without_replay(self):
        with tempfile.TemporaryDirectory() as temporary:
            attempts = Path(temporary)
            (attempts / 'parent_000000000006').mkdir()
            policy = Mock()
            policy.local_attempts.side_effect = ValueError('unfinished_attempt_no_replay')
            with self.assertRaisesRegex(ValueError, 'unfinished_attempt_no_replay'):
                tick_once(policy, None, {}, attempts, {}, dict(request_count=6))
            policy.tick.assert_not_called()

    def test_new_boundary_uses_unchanged_policy(self):
        with tempfile.TemporaryDirectory() as temporary:
            policy = Mock()
            state = dict(request_count=7)
            tick_once(policy, 'repository', {}, temporary, {}, state)
            policy.tick.assert_called_once_with('repository', {}, temporary, {}, state)

    def test_single_parent_attachment_lock(self):
        with tempfile.TemporaryDirectory() as temporary:
            with single_parent(temporary):
                with self.assertRaises(BlockingIOError):
                    with single_parent(temporary):
                        self.fail('duplicate parent lock')
            with single_parent(temporary):
                pass

    def test_evidence_choices_are_only_exact_child_responses(self):
        state = dict(events=[dict(actor='environment', record_index=31, record_sha256='b' * 64,
            text='Tool output'), dict(actor='child', record_index=33, record_sha256='a' * 64,
            text='My actual question?')])
        instruction, payload = evidence_prompt('Original policy', 'Original payload', state)
        choices = json.loads(instruction.split('Exact child evidence choices: ', 1)[1])
        self.assertEqual(choices, [dict(record_index=33, record_sha256='a' * 64, quote='My actual question?')])
        self.assertEqual(payload, 'Original payload')
        self.assertIn('not evidence of an adapter change', instruction)

    def test_nonmath_openers_explicitly_invite_new_objects(self):
        for environment in ('CPU_STDLIB_ALGORITHM_CORRECTNESS', 'READ_ONLY_REPOSITORY_TRACE', 'CREATIVE_OWN_OBJECT'):
            with self.subTest(environment=environment):
                text = new_opening(dict(arm='test', effective_environment=environment), 120)
                self.assertIn('NEW', text)
                self.assertIn('not a requirement to continue inherited V', text)
                self.assertNotIn('story test', text)
                self.assertLessEqual(len(text.split()), 120)

    def test_opening_limit_is_not_weakened(self):
        with self.assertRaisesRegex(ValueError, 'bounded_actual_new_parent_opening'):
            new_opening(dict(arm='test', effective_environment='CREATIVE_OWN_OBJECT'), 3)


if __name__ == '__main__':
    unittest.main()
