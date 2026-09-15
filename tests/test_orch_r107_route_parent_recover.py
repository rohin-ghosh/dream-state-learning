"""Pre-admission retries cannot replay actors or alter existing allocation."""

import json
from pathlib import Path
import tempfile
import unittest

from gpu.orch_r107_route_parent_recover import require_unlaunched, R108_PARENT, R108_REFLECTION


class RecoveryTests(unittest.TestCase):
    def test_R108_types_non_solution_and_multiangle(self):
        for name in ('perception', 'persistence', 'metacognition', 'curiosity',
                     'goal/meta-goal regulation', 'reflection', 'action steering', 'affective-value'):
            self.assertIn(name, R108_PARENT)
        self.assertIn('never prescribe the answer', R108_PARENT)
        self.assertIn('different perspectives', R108_REFLECTION)
        self.assertIn('not an observed behavioral change', R108_REFLECTION)

    def test_only_zero_call_admission_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); lane = root / 'campaign_route_parent_5'; lane.mkdir()
            (lane / 'GUARDIAN_FAILED.json').write_text(json.dumps(dict(error='strict_privileged_clear_required')))
            self.assertEqual(require_unlaunched(root), lane)
            (root / 'RESERVATIONS.jsonl').write_text(json.dumps(dict(index=1)) + '\n')
            self.assertEqual(require_unlaunched(root), lane)
            (root / 'RESERVATIONS.jsonl').write_text(json.dumps(dict(index=5)) + '\n')
            with self.assertRaises(ValueError):
                require_unlaunched(root)

    def test_existing_native_or_launch_forbids_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); lane = root / 'campaign_route_parent_5'; lane.mkdir()
            (lane / 'GUARDIAN_FAILED.json').write_text(json.dumps(dict(error='strict_privileged_clear_required')))
            (lane / 'LAUNCH.json').write_text('{}')
            with self.assertRaises(ValueError):
                require_unlaunched(root)


if __name__ == '__main__':
    unittest.main()
