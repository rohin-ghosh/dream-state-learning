from copy import deepcopy
import unittest

from gpu import orch_r141_a100_perception_exclusion_20260916 as repair


class ExclusionTests(unittest.TestCase):
    def fixture(self):
        return dict(source_sha256=repair.OFFENDING, split='TRAIN', actor='child', prefix_loss=False,
            target_loss=True, token_ids=[1] * 64 + [151644, 151644] + [2] * 72,
            target='saved <|im_start|><|im_start|> raw', prefix=[{'role': 'user', 'content': 'unchanged'}])

    def original(self, rows, presentation):
        return deepcopy(rows), []

    def test_only_pinned_row_excluded_no_row_history_or_prefix_change(self):
        bad = self.fixture()
        other = dict(bad, source_sha256='different')
        rows = [other, bad]
        before = deepcopy(rows)
        accepted, excluded = repair.eligible_rows(rows, {}, self.original)
        self.assertEqual(accepted, [other])
        self.assertEqual(excluded, [dict(source_sha256=repair.OFFENDING, reason=repair.REASON)])
        self.assertEqual(rows, before)

    def test_excluded_during_later_rehearsal_too(self):
        for unused in range(2):
            accepted, excluded = repair.eligible_rows([self.fixture()], {}, self.original)
            self.assertFalse(accepted)
            self.assertEqual(len(excluded), 1)

    def test_original_exclusions_retained(self):
        original = lambda rows, presentation: ([], [dict(source_sha256='old', reason='old')])
        accepted, excluded = repair.eligible_rows([self.fixture()], {}, original)
        self.assertEqual(excluded[0], dict(source_sha256='old', reason='old'))
        self.assertEqual(excluded[1]['source_sha256'], repair.OFFENDING)

    def test_different_special_target_never_silently_excluded(self):
        other = dict(self.fixture(), source_sha256='different')
        accepted, excluded = repair.eligible_rows([other], {}, self.original)
        self.assertEqual(accepted, [other])
        self.assertFalse(excluded)

    def test_changed_pinned_row_or_nonchild_rejected(self):
        for changed in (dict(actor='parent'), dict(split='HELD'), dict(target_loss=False),
                        dict(token_ids=[151644]), dict(target='altered')):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                repair.eligible_rows([dict(self.fixture(), **changed)], {}, self.original)

    def test_original_mutation_is_rejected(self):
        other = dict(self.fixture(), source_sha256='different')
        def mutating(rows, presentation):
            rows[0]['target'] = 'changed'
            return rows, []
        with self.assertRaisesRegex(ValueError, 'unchanged'):
            repair.eligible_rows([other], {}, mutating)


if __name__ == '__main__':
    unittest.main()
