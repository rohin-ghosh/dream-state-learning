import ast
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from takeover import HERE, REPO
from journal_cache_patch import METHODS, REPLACED, methods, patch_journal


class CacheTests(unittest.TestCase):
    def patched(self, physical):
        original = (HERE / 'r181' / ('physical' + str(physical)) / 'original_journal.py').read_text()
        canonical = (REPO / 'gpu/orch_r125_stream_journal.py').read_text()
        return original, patch_journal(original, canonical)

    def module(self, physical):
        import types
        module = types.ModuleType('owned_journal_' + str(physical))
        exec(compile(self.patched(physical)[1], '<owned-cache>', 'exec'), module.__dict__)
        return module

    def test_all_six_preserve_scan_transition_lock_and_fsync_code(self):
        for physical in (0, 1, 2, 3, 4, 7):
            original, result = self.patched(physical)
            before, after = methods(original), methods(result)
            self.assertEqual(set(after), set(before) | set(METHODS))
            for name in set(before) - set(REPLACED) - {'__init__'}:
                self.assertEqual(ast.dump(before[name]), ast.dump(after[name]))

    def test_update_cache_audit_and_reopen_both_actual_variants(self):
        for physical in (0, 1):
            module = self.module(physical)
            with tempfile.TemporaryDirectory(dir=HERE) as directory:
                root = Path(directory) / 'journal'
                with module.StreamJournal(root, create=True) as journal:
                    with patch.object(journal, '_scan', wraps=journal._scan) as scan:
                        for step in range(3):
                            journal.record('UPDATE', dict(optimizer_step=step))
                        self.assertEqual(scan.call_count, 0)
                        self.assertEqual(journal.audit()['record_count'], 3)
                        self.assertEqual(scan.call_count, 1)
                with module.StreamJournal(root, create=False) as reopened:
                    self.assertEqual(reopened.audit()['record_count'], 3)

    def test_old_bytes_change_with_restored_mtime_rejected(self):
        for physical in (0, 1):
            module = self.module(physical)
            with tempfile.TemporaryDirectory(dir=HERE) as directory:
                with module.StreamJournal(Path(directory) / 'journal', create=True) as journal:
                    result = journal.record('UPDATE', dict(optimizer_step=1))
                    path = Path(result['path'])
                    original_stat = path.stat()
                    path.write_bytes(path.read_bytes().replace(b'"optimizer_step":1', b'"optimizer_step":2'))
                    os.utime(path, ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns))
                    with self.assertRaises(ValueError):
                        journal.record('UPDATE', dict(optimizer_step=3))


if __name__ == '__main__':
    unittest.main()
