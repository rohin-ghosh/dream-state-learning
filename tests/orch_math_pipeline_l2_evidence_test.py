import json
from pathlib import Path
import tempfile
import unittest

from gpu import orch_math_pipeline_l2_evidence as evidence
from gpu import orch_math_pipeline_l2_measure as measure


class EvidenceTest(unittest.TestCase):
    def test_observer_does_not_invent_missing_measurements(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / 'campaign_fixture').mkdir()
            self.assertEqual(measure.observe(Path(directory)), [])

    def test_missing_transition_retains_full_denominator(self):
        with tempfile.TemporaryDirectory() as directory:
            result = evidence.join_transition(Path(directory), 'GUIDED_SLEEP', 2)
        self.assertEqual((result['planned_denominator'], result['captured'], result['missing']), (8, 0, 8))
        self.assertFalse(result['prior_learning_complete'])
        self.assertEqual(result['new_native_calls'], 0)

    def test_transition_rejects_held_episode(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'FROZEN/cycle2/experience'
            path.mkdir(parents=True)
            (path / 'EPISODE_00.json').write_text(json.dumps(dict(task=dict(split='HELD'))))
            with self.assertRaises(AssertionError):
                evidence.join_transition(Path(directory), 'FROZEN', 2)


if __name__ == '__main__':
    unittest.main()
