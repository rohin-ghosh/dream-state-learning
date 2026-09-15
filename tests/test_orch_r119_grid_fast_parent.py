import unittest

from gpu import orch_r119_grid_fast_parent as subject


class FastParentTests(unittest.TestCase):
    def test_low_short_independent_no_claim_retry(self):
        source = subject.source()
        compile(source, 'fast_parent', 'exec')
        self.assertIn('"\'low\'"', source)
        self.assertNotIn('"\'high\'"', source)
        self.assertIn('max_output_tokens=1024', source)
        self.assertIn('R119_GRID_INDEPENDENT_TERMINAL.json', source)
        self.assertIn('EXISTING_CLAIM_NO_RETRY', source)
        self.assertIn("args.after_parent == 40", source)
        self.assertIn('non_episode_cadence_skip_no_provider_call', source)
        self.assertIn('transport.validate_request(request, kwargs["config"])', source)


if __name__ == '__main__':
    unittest.main()
