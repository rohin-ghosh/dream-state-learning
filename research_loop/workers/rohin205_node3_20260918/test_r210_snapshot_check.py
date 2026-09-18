"""Regression for physical archive replay with an unchanged logical inbox."""

import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch


class ArchiveBase:
    def __init__(self, root):
        self.root = Path(root)
        self.inbox = self.root / 'inbox'
        self.physical_inbox = self.inbox
        self._reload_state()

    def _reload_state(self, *arguments, **keywords):
        self.observed_inbox = self.inbox
        return arguments, keywords


class SnapshotTests(unittest.TestCase):
    def load_checker(self):
        path = Path(__file__).with_name('r210_snapshot_check.py')
        specification = importlib.util.spec_from_file_location('snapshot_test_subject', path)
        module = importlib.util.module_from_spec(specification)
        with patch.dict(sys.modules, {'gpu.r205_runtime': types.SimpleNamespace(ControlJournal=ArchiveBase)}):
            specification.loader.exec_module(module)
        return module

    def test_constructor_replay_keeps_physical_archive_and_logical_identity(self):
        checker = self.load_checker()
        journal = checker.SnapshotJournal('/archive/stream', '/original/life/stream/inbox')
        self.assertEqual(journal.root, Path('/archive/stream'))
        self.assertEqual(journal.physical_inbox, Path('/archive/stream/inbox'))
        self.assertEqual(journal.observed_inbox, Path('/original/life/stream/inbox'))

    def test_subsequent_replay_preserves_arguments_and_exact_logical_path(self):
        checker = self.load_checker()
        journal = checker.SnapshotJournal('/archive/stream', '/original/life/stream/inbox')
        journal.inbox = Path('/wrong/inbox')
        result = journal._reload_state({'snapshot': 'unchanged'}, force=True)
        self.assertEqual(result, (({'snapshot': 'unchanged'},), {'force': True}))
        self.assertEqual(journal.observed_inbox, Path('/original/life/stream/inbox'))


if __name__ == '__main__':
    unittest.main()
