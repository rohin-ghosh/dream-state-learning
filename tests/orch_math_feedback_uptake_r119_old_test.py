import ast
import json
from pathlib import Path
import tempfile
import unittest

from gpu import orch_math_feedback_uptake_r119_old as subject


class LeaseContinuationTests(unittest.TestCase):
    def test_original_lease_six_hour_margin(self):
        observed = subject.clock(1789689600, 1789491600)
        self.assertEqual(observed['hard_deadline_unix'], 1789668000)
        self.assertEqual(observed['native_deadline_unix'], 1789667700)

    def test_no_unknown_lease_or_expired_launch(self):
        for lease, now in [(1789689601, 1789491600), (1789689600, 1789667999)]:
            with self.assertRaises(ValueError):
                subject.clock(lease, now)

    def test_never_overwrite_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'receipt.json'
            subject.write(path, {'old': 1})
            with self.assertRaises(FileExistsError):
                subject.write(path, {'old': 2})
            self.assertEqual(subject.read(path), {'old': 1})

    def test_no_slot_zero_restore(self):
        with self.assertRaisesRegex(ValueError, 'only_current_owned_slots'):
            subject.reconstruct(Path('/missing'), 0, None)

    def test_sources_compile(self):
        for name in subject.SOURCE_NAMES:
            ast.parse(Path(subject.__file__).with_name(name).read_text())

    def test_one_bound_successor_namespace_and_library(self):
        for name in (subject.SOURCE_NAMES[1], subject.SOURCE_NAMES[3]):
            text = Path(subject.__file__).with_name(name).read_text()
            self.assertIn(subject.DIRECTORY, text)
            self.assertNotIn("'R119_LEASE'", text)
        self.assertIn("PYTHONPATH=str(old.LIBRARY / 'source')", Path(subject.__file__).read_text())

    def test_preserved_calls_and_parent_not_replayed(self):
        text = Path(subject.__file__).with_name(subject.SOURCE_NAMES[1]).read_text()
        self.assertIn('if position < existing_count:', text)
        self.assertIn('range(len(dialogue_records) + 1, 3)', text)
        broker = Path(subject.__file__).with_name(subject.SOURCE_NAMES[3]).read_text()
        self.assertIn("str(path.relative_to(lane)) in plan['preserved']", broker)

    def test_frozen_base_and_readout_parent_free(self):
        text = Path(subject.__file__).with_name(subject.SOURCE_NAMES[1]).read_text()
        self.assertIn('policy.base.verify_no_adapter(engine.model)', text)
        self.assertIn("state['teacher'] if phase == 'experience' else ''", text)
        self.assertIn('no_held_to_parent=True', text)

    def test_readout_first_restore_then_next_genuine_cycle(self):
        text = Path(subject.__file__).with_name(subject.SOURCE_NAMES[1]).read_text()
        self.assertIn("plan['next_phase'] == 'readout'", text)
        self.assertIn("cycle == plan['next_cycle'] + 1", text)
        self.assertIn("complete['process'] == list(process)", text)


if __name__ == '__main__':
    unittest.main()
