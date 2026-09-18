"""CPU-only negative tests for clean-expiry admission, never learner signals."""

import importlib.util
from pathlib import Path
import unittest


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('rearm_node1', HERE / 'rearm_node1.py')
REARM = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REARM)


class RearmTests(unittest.TestCase):
    def check(self, names=None, expired=None, alive=False, remaining=-1, physical=5):
        REARM.clean_expiry(physical, names if names is not None else {'NO_BOUNDARY.json'},
                           expired if expired is not None else {'original_left_running': True}, alive, remaining)

    def test_clean_expiry(self):
        self.check()

    def test_active_operator_rejected(self):
        with self.assertRaisesRegex(ValueError, 'prior_waiter_still_live'):
            self.check(alive=True)

    def test_unexpired_operator_rejected_even_if_absent(self):
        with self.assertRaisesRegex(ValueError, 'prior_waiter_still_live'):
            self.check(remaining=1)

    def test_missing_timeout_rejected(self):
        with self.assertRaisesRegex(ValueError, 'explicit_clean_timeout'):
            self.check(names=set())

    def test_no_positive_original_left_running_receipt_rejected(self):
        with self.assertRaisesRegex(ValueError, 'explicit_clean_timeout'):
            self.check(expired={'original_left_running': False})

    def test_every_started_transaction_or_failure_rejected(self):
        for name in ('BOUNDARY.json', 'BOUNDARY_RECEIVING_CPU.json', 'RETIREMENT_STARTED.json',
                     'RETIRED.json', 'DISPATCHED.json', 'LOADED_RECEIPT.json', 'HANDOFF_COMPLETE.json', 'FAILURE_1.json'):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'no_boundary_transaction_or_failure'):
                self.check(names={'NO_BOUNDARY.json', name})

    def test_loaded_and_noop_lanes_are_not_rearm_targets(self):
        for physical in (0, 1, 3, 4, 7):
            with self.subTest(physical=physical), self.assertRaisesRegex(ValueError, 'only_remaining_learning_lives'):
                self.check(physical=physical)


if __name__ == '__main__':
    unittest.main()
