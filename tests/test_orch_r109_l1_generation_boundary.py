import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_r109_l1_generation_boundary as boundary


class GenerationBoundaryTests(unittest.TestCase):
    def test_fast_probe_does_not_census_before_signal(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'PROGRESS.json').write_text(json.dumps(dict(calls=5)))
            (root/'CALL_000005.json').write_text('{}')
            with patch.object(Path,'glob',side_effect=AssertionError('no_census_in_probe')):
                self.assertTrue(boundary.candidate(root)[0])
                (root/'INTENT_000006.json').write_text('{}')
                self.assertFalse(boundary.candidate(root)[0])

    def test_original_hard_deadline(self):
        self.assertEqual(boundary.END,1789491360)


if __name__ == '__main__':unittest.main()
