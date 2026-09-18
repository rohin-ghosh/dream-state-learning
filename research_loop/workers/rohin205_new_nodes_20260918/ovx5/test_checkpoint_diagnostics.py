"""Do not score partially saved adapters or confuse evaluation with checkpoints."""

import json
from pathlib import Path
import tempfile
import unittest
from checkpoint_diagnostics import checkpoints


class CheckpointTests(unittest.TestCase):
    def test_selection_export_waits_for_later_training_progress(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / 'training'
            (output / 'selected_step_000008').mkdir(parents=True)
            self.assertEqual(checkpoints(root), [])
            (output / 'PROGRESS_000010.json').write_text(json.dumps(dict(completed_updates=10)))
            self.assertEqual(checkpoints(root)[0][2], 8)

    def test_pilot_requires_completed_marker_not_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / 'training'
            (output / 'pilot_checkpoint/adapter').mkdir(parents=True)
            self.assertEqual(checkpoints(root), [])
            (output / 'PILOT_COMPLETE.json').write_text(json.dumps(dict(completed_updates=145)))
            self.assertEqual(checkpoints(root)[0][2], 145)


if __name__ == '__main__':
    unittest.main()
