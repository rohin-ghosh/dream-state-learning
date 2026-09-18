import inspect
import unittest
from unittest.mock import patch

from gpu import orch_math_feedback_uptake_r122_a100 as runner


class ReadOnlyTests(unittest.TestCase):
    def test_allocation(self):
        self.assertEqual(set(runner.DEVICES), {5, 6, 7})
        self.assertEqual(len(set(runner.DEVICES.values())), 3)

    def test_lease_margin(self):
        self.assertEqual(runner.HARD, runner.LEASE_END - 21600)
        self.assertLess(runner.NATIVE, runner.HARD)

    def test_fresh_pair(self):
        first = runner.fresh_pair(5, 9, ())
        second = runner.fresh_pair(5, 9, [task['question_sha256'] for task in first])
        self.assertEqual(len(first), 2)
        self.assertFalse({task['question_sha256'] for task in first} & {task['question_sha256'] for task in second})
        self.assertTrue(all(task['split'] == 'TRAIN' for task in second))

    def test_no_optimizer_load_or_training(self):
        source = inspect.getsource(runner.load)
        self.assertNotIn('torch.load', source)
        self.assertNotIn('AdamW', source)
        self.assertIn("'collection'", source)

    def test_parent_is_nonblocking(self):
        self.assertNotIn('sleep(', inspect.getsource(runner.poll))
        source = inspect.getsource(runner.resident)
        self.assertIn('time.time() + 600', source)
        self.assertIn('episodes=2, weight_sleep=False', source)

    def test_readout_never_parent_or_context(self):
        source = inspect.getsource(runner.call)
        self.assertIn("if split == 'TRAIN':", source)
        self.assertIn("math.policy.readout_messages(task, 'held')", source)

    def test_full_scanner_no_clear_override(self):
        source = inspect.getsource(runner.scan)
        self.assertIn('admission.bind_scan', source)
        self.assertIn('argv_scan.scan', source)


if __name__ == '__main__':
    unittest.main()
