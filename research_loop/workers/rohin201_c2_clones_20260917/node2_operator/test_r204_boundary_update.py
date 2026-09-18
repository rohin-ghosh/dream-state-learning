"""Focused sequence-resume and exact source-edit regressions."""

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock


HERE = Path(__file__).resolve().parent
SHARED = HERE.parents[1] / 'rohin174_parenting_20260917/node5/R193_MASKED_CE_PHASE1'
sys.path.insert(0, str(SHARED))
specification = importlib.util.spec_from_file_location('boundary_update', HERE / 'r204_boundary_update.py')
module = importlib.util.module_from_spec(specification)
specification.loader.exec_module(module)


class BoundaryRepairTests(unittest.TestCase):
    def test_new_sequence_does_not_reuse_existing_action(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'ACTION_000000.json').touch()
            (root / 'ACTION_000003.json').touch()
            self.assertEqual(module.sequence_start(root), 4)

    def test_empty_sequence(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(module.sequence_start(directory), 0)

    def test_source_anchor_fails_closed_on_ambiguity(self):
        with self.assertRaises(ValueError):
            module.replace_once('repeat repeat', 'repeat', 'changed')

    def test_targets_exclude_original_c2_and_protected_creatives(self):
        self.assertEqual(set(module.TARGETS), {'repo_c1', 'birth1'})
        self.assertEqual(module.TARGETS['repo_c1'][2:], (2170067, '92935338'))
        self.assertEqual(module.TARGETS['birth1'][2:], (1815204, '91233592'))

    def test_restore_receives_complete_envelope_not_inner_state(self):
        document = {'state': {'pending': None}, 'sha256': 'a' * 64}
        restore_function = Mock(return_value='restored')
        self.assertEqual(module.restore_stream(restore_function, document), 'restored')
        restore_function.assert_called_once_with(document, expected_sha256='a' * 64)


if __name__ == '__main__':
    unittest.main()
