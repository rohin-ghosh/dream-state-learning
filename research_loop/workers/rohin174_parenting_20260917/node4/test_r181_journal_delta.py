"""Cache overlay preserves deployed validators and refuses unrelated source."""

import ast
from pathlib import Path
import sys
import unittest

HOME = Path(__file__).resolve().parent
sys.path.insert(0, str(HOME))
import r181_journal_delta as delta


class JournalDeltaTests(unittest.TestCase):
    def setUp(self):
        self.sources = HOME / 'journal_sources_20260917T2212Z'
        self.main = (self.sources / 'MAIN_JOURNAL.py').read_text()

    def test_both_actual_variants_keep_every_noncache_method(self):
        for name in ('DEPLOYED_014.py', 'DEPLOYED_3.py'):
            with self.subTest(name=name):
                original = (self.sources / name).read_text()
                patched = delta.patch_journal(original, self.main)
                before, after = delta.methods(original), delta.methods(patched)
                for method in set(before) - set(delta.REPLACED):
                    self.assertEqual(ast.dump(before[method]), ast.dump(after[method]))
                self.assertEqual('_advance' in after, True)
                self.assertEqual('journal_experiment_configuration_frozen' in original,
                    'journal_experiment_configuration_frozen' in patched)

    def test_no_blind_canonical_overwrite_or_repatch(self):
        original = (self.sources / 'DEPLOYED_014.py').read_text()
        for source in (original + '\n', delta.patch_journal(original, self.main), self.main):
            with self.assertRaisesRegex(ValueError, 'known_actual_journal_bytes'):
                delta.patch_journal(source, self.main)
        with self.assertRaisesRegex(ValueError, 'exact_Main_journal_cache_bytes'):
            delta.patch_journal(original, self.main + '\n')

    def test_cache_methods_are_exact_Main_AST(self):
        patched = delta.methods(delta.patch_journal((self.sources / 'DEPLOYED_3.py').read_text(), self.main))
        main = delta.methods(self.main)
        for name in delta.REPLACED + delta.ADDED:
            self.assertEqual(ast.dump(patched[name]), ast.dump(main[name]))


if __name__ == '__main__':
    unittest.main()
