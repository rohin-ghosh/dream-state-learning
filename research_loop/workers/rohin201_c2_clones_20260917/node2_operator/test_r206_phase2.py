"""Focused phase-boundary integrity and arm-executor preservation tests."""

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'rohin174_parenting_20260917/node5/R193_MASKED_CE_PHASE1'))
specification = importlib.util.spec_from_file_location('phase2', HERE / 'r206_phase2.py')
module = importlib.util.module_from_spec(specification)
specification.loader.exec_module(module)


class Phase2Tests(unittest.TestCase):
    def test_only_owned_screen_arms(self):
        self.assertEqual(module.ARMS, {'math_d1': 1, 'repo_c1': 3, 'creative_d1': 4, 'math_transfer_c1': 6})

    def test_executor_is_preserved_without_replacing_released_fallback(self):
        previous = 'class Driver:\n    def _cpu(self, origin):\n        if self.config["trial_id"] == "MATH":\n            return bridge(origin)\n        return old(origin)\n'
        released = 'class Driver:\n    def _cpu(self, origin):\n        return new(origin)\n'
        changed = module.executor_patch(released, previous, 'MATH')
        self.assertIn('return bridge(origin)', changed)
        self.assertIn('return new(origin)', changed)
        self.assertNotIn('return old(origin)', changed)
        with self.assertRaises(ValueError):
            module.executor_patch(released, previous, 'OTHER')

    def fixture(self, root, terminal_status='R184_SCREEN_STOP', pending=None):
        directory = root / 'stream/records'
        directory.mkdir(parents=True)
        state = dict(pending=pending, sleep_frontier=0, rows=[])
        checkpoint = {'optimizer_steps': 5196}
        documents = [('SLEEP_COMPLETE', dict(cycle=57, status='COMPLETE', checkpoint=checkpoint,
            resume_state=dict(state=state, sha256=module.saved.digest(state)))),
            ('R184_LEARN_COMPLETE', dict(cycle=57, checkpoint=checkpoint)),
            ('TERMINAL', dict(completed_sleeps=57, status=terminal_status))]
        previous = 'prior'
        for index, (kind, document) in enumerate(documents):
            record = dict(kind=kind, document=document, index=index, previous_sha256=previous)
            record['sha256'] = module.saved.digest(record)
            (directory / f'{index:020d}.json').write_text(json.dumps(record))
            previous = record['sha256']

    def test_only_exact_normal_complete_screen_is_resumable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            self.fixture(root)
            self.assertEqual(module.terminal_boundary(root)['cycle'], 57)

    def test_crash_or_pending_rows_are_not_phase_boundary(self):
        for status, pending in [('CRASH', None), ('R184_SCREEN_STOP', 'unsaved')]:
            with self.subTest(status=status, pending=pending), tempfile.TemporaryDirectory() as directory:
                root = Path(directory).resolve()
                self.fixture(root, status, pending)
                with self.assertRaises(ValueError):
                    module.terminal_boundary(root)


if __name__ == '__main__':
    unittest.main()
