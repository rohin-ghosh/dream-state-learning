from pathlib import Path
import tempfile
import unittest

from gpu import orch_r119_grid_learned_fork as subject


class LearnedForkTests(unittest.TestCase):
    def test_actual_checkpoint_required(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'CHECKPOINT.json'
            path.write_text('{}')
            with self.assertRaisesRegex(ValueError, 'actual_gen1'):
                subject.validate_checkpoint(path)

    def test_original_continuation_is_bound(self):
        base = subject.load_runtime()
        self.assertEqual(base.ERA, 'learned_fork_r119')
        self.assertEqual(base.TERMINAL, 'R119_LEARNED_GRID_TERMINAL.json')


if __name__ == '__main__':
    unittest.main()
