import unittest
from types import SimpleNamespace

from native_games import NativeGame, feedback, parse_action


class FakeNativeEnvironment:
    def __init__(self):
        self.action_space = SimpleNamespace(n=2, contains=lambda action: action in (0, 1))
        self.unwrapped = self
        self.calls = []

    def reset(self, seed):
        self.calls.append(('reset', seed))
        return [0.0, 0.0, 0.0, 0.0], {}

    def step(self, action):
        self.calls.append(('step', action))
        return [0.1, 0.2, 0.3, 0.4], 1.0, True, False, {}


class GameBindingTests(unittest.TestCase):
    def setUp(self):
        self.environment = FakeNativeEnvironment()
        self.game = NativeGame(self.environment, 'CartPole-v1', 2061804, 'TEST_ONLY_FAKE', 'test')
        self.origin = dict(kind='TRAIN_CHILD_RESPONSE', record_index=5857, record_sha256='a' * 64)

    def test_one_real_call_per_accepted_action(self):
        self.game.reset()
        result = self.game.step('GAME_ACTION 1', self.origin)
        self.assertEqual(self.environment.calls, [('reset', 2061804), ('step', 1)])
        self.assertEqual(result['reward'], 1.0)
        self.assertTrue(result['terminated'])
        with self.assertRaises(ValueError):
            self.game.step('GAME_ACTION 1', self.origin)

    def test_bad_or_inherited_action_never_steps(self):
        self.game.reset()
        with self.assertRaises(ValueError):
            self.game.step('GAME_ACTION 9', self.origin)
        with self.assertRaises(ValueError):
            self.game.step('GAME_ACTION 0', dict(self.origin, record_index=5840))
        self.assertEqual(self.environment.calls, [('reset', 2061804)])

    def test_parser_does_not_execute_or_rewrite_child_code(self):
        for text in ['print(1)', 'GAME_ACTION 1\nGAME_ACTION 0', 'GAME_ACTION -1']:
            with self.assertRaises(ValueError):
                parse_action(text)

    def test_feedback_is_truthful_plain_external_text(self):
        self.game.reset()
        result = self.game.step('GAME_ACTION 0', self.origin)
        text = feedback(result)
        self.assertIn('Actual native game observation', text)
        self.assertNotIn('source_sha256', text)
        self.assertNotIn('receipt_sha256', text)


if __name__ == '__main__':
    unittest.main()
