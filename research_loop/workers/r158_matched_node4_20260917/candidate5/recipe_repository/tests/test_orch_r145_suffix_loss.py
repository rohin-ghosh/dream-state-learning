from copy import deepcopy
from types import SimpleNamespace
import unittest

from gpu.orch_r145_suffix_loss import loss_window


class SuffixLossTests(unittest.TestCase):
    def sample(self, prefix=4, target=(5, 6)):
        return SimpleNamespace(input_ids=(1,) * prefix + target,
            labels=(-100,) * prefix + target, target_ids=target)

    def test_keeps_preceding_predictor_and_all_original_labels(self):
        for prefix in (1, 20, 16300):
            sample = self.sample(prefix)
            before = deepcopy(sample)
            self.assertEqual(loss_window(sample), dict(logits_to_keep=3, labels=(-100, 5, 6)))
            self.assertEqual(sample.__dict__, before.__dict__)

    def test_rejects_holes_changed_targets_and_absent_prefix(self):
        variants = [self.sample(0), self.sample(target=()),
            SimpleNamespace(input_ids=(1, 5, 6), labels=(1, 5, 6), target_ids=(5, 6)),
            SimpleNamespace(input_ids=(1, 5, 7), labels=(-100, 5, 6), target_ids=(5, 6)),
            SimpleNamespace(input_ids=(1, 5, 6), labels=(-100, -100, 6), target_ids=(5, 6))]
        for sample in variants:
            with self.subTest(sample=sample), self.assertRaises(ValueError):
                loss_window(sample)


if __name__ == '__main__':
    unittest.main()
