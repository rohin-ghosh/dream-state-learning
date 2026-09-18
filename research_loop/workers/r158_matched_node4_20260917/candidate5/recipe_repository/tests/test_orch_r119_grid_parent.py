import unittest

from gpu.orch_r119_grid_parent import replace_one


class ParentTests(unittest.TestCase):
    def test_only_one_exact_site(self):
        self.assertEqual(replace_one('old tail', 'old', 'new'), 'new tail')

    def test_missing_or_ambiguous_site_fails(self):
        for source in ('absent', 'old old'):
            with self.assertRaises(ValueError):
                replace_one(source, 'old', 'new')


if __name__ == '__main__':
    unittest.main()
