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

    def test_two_episode_missing_transition_keeps_declared_denominator(self):
        with tempfile.TemporaryDirectory() as directory:
            current = Path(directory) / 'GUIDED_SLEEP/cycle7/experience'
            current.mkdir(parents=True)
            (current / 'DENOMINATORS.json').write_text(json.dumps(dict(
                task_denominator=2, planned_tasks=['TRAIN_0', 'TRAIN_1'])))
            result = evidence.join_transition(Path(directory), 'GUIDED_SLEEP', 7)
        self.assertEqual((result['planned_denominator'], result['missing']), (2, 2))
        self.assertIsNone(result['saved_child_to_next_cycle_verified'])

    def test_two_episode_late_cycle_observer_writes_once(self):
        with tempfile.TemporaryDirectory() as directory:
            campaign = Path(directory) / 'campaign_fixture'
            previous = campaign / 'GUIDED_SLEEP/cycle6/experience'
            current = campaign / 'GUIDED_SLEEP/cycle7/experience'
            previous.mkdir(parents=True)
            current.mkdir(parents=True)
            (previous / 'COMPLETE.json').write_text(json.dumps(dict(status='COMPLETE',
                output_adapter=dict(state_sha256='saved'))))
            (current / 'REQUEST.json').write_text(json.dumps(dict(
                input_adapter=dict(state_sha256='saved'))))
            (current / 'DENOMINATORS.json').write_text(json.dumps(dict(
                task_denominator=2, planned_tasks=['TRAIN_0', 'TRAIN_1'])))
            for position in range(2):
                (current / f'EPISODE_{position:02d}.json').write_text(json.dumps(dict(
                    task=dict(id=f'TRAIN_{position}', split='TRAIN'), outcome=dict(correct=False))))
            written = measure.observe(Path(directory))
            self.assertEqual(len(written), 1)
            result = json.loads(Path(written[0]).read_text())
            self.assertEqual((result['planned_denominator'], result['captured'], result['missing']), (2, 2, 0))
            self.assertTrue(result['saved_child_to_next_cycle_verified'])
            self.assertEqual(measure.observe(Path(directory)), [])

    def test_rejects_wrong_preceding_child(self):
        with tempfile.TemporaryDirectory() as directory:
            previous = Path(directory) / 'GUIDED_SLEEP/cycle1/experience'
            current = Path(directory) / 'GUIDED_SLEEP/cycle2/experience'
            previous.mkdir(parents=True)
            current.mkdir(parents=True)
            (previous / 'COMPLETE.json').write_text(json.dumps(dict(status='COMPLETE',
                output_adapter=dict(state_sha256='saved'))))
            (current / 'REQUEST.json').write_text(json.dumps(dict(
                input_adapter=dict(state_sha256='wrong'))))
            with self.assertRaisesRegex(AssertionError, 'preceding saved child'):
                evidence.join_transition(Path(directory), 'GUIDED_SLEEP', 2)


if __name__ == '__main__':
    unittest.main()
