import importlib.util
import unittest


specification = importlib.util.spec_from_file_location('profile_tested', '/tmp/astra_coaching_runtime_profile_20260913.py')
profile = importlib.util.module_from_spec(specification)
specification.loader.exec_module(profile)


class PercentileTests(unittest.TestCase):
    def test_single(self):
        self.assertEqual(profile.percentile([3], .95), 3)

    def test_interpolation(self):
        self.assertEqual(profile.percentile([10, 0], .95), 9.5)
        self.assertEqual(profile.percentile([0, 5, 10], .5), 5)

    def test_invalid(self):
        with self.assertRaises(AssertionError):
            profile.percentile([], .5)


if __name__ == '__main__':
    unittest.main()
