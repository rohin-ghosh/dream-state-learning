from copy import deepcopy
import unittest

import prepare_math_b_tail_manifest as repair


class TailManifestTests(unittest.TestCase):
    def setUp(self):
        self.original = dict(selection=dict(max_tail_bytes=128 * 1024 * 1024, max_tail_records=2048,
            complete_index=9476, complete_sha256='original'), staged_source_root='original',
            candidate=dict(path='original', sha256='original'))
        self.revised = deepcopy(self.original)
        self.revised['selection']['max_tail_bytes'] = repair.NEW_BOUND

    def test_measured_budget_only(self):
        repair.manifest_delta(self.original, self.revised)

    def test_complete_anchor_must_not_change(self):
        self.revised['selection']['complete_index'] = 9505
        with self.assertRaisesRegex(ValueError, 'only_measured'):
            repair.manifest_delta(self.original, self.revised)

    def test_record_bound_must_not_change(self):
        self.revised['selection']['max_tail_records'] = 99999
        with self.assertRaisesRegex(ValueError, 'only_measured'):
            repair.manifest_delta(self.original, self.revised)

    def test_source_must_not_change(self):
        self.revised['staged_source_root'] = 'other'
        with self.assertRaisesRegex(ValueError, 'only_measured'):
            repair.manifest_delta(self.original, self.revised)


if __name__ == '__main__':
    unittest.main()
