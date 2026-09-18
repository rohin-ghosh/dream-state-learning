"""Synthetic source binding tests; never open live journals or send signals."""

import ast
from pathlib import Path
import sys
import unittest


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r181_build
import r181_patch


class JournalOverlayTests(unittest.TestCase):
    def test_existing_R181_native_remains_byte_identical(self):
        source = (HERE.parents[3] / 'gpu/orch_r125_continual_native.py').read_text()
        self.assertEqual(r181_patch.patch_native(source), source)

    def test_partial_R181_is_rejected(self):
        source = (HERE.parents[3] / 'gpu/orch_r125_continual_native.py').read_text()
        damaged = source.replace('                respond_to_presleep_inbox(child, stream, journal, cycle)\n', '')
        with self.assertRaisesRegex(ValueError, 'incomplete_existing_R181_patch'):
            r181_patch.patch_native(damaged)

    def test_journal_only_added_to_immutable_stage(self):
        source = r181_build.operator_source('a' * 64, 'b' * 64)
        module = ast.parse(source)
        stage = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == 'stage')
        rendered = ast.unparse(stage)
        self.assertIn('journal.write_text(policy.patch_journal(', rendered)
        self.assertIn("journal = source / 'gpu/orch_r125_stream_journal.py'", rendered)
        self.assertIn('only_R181_native_policy_and_Main_journal_overlay', rendered)
        self.assertIn('original_files', rendered)
        self.assertIn('source_still_exact', rendered)
        self.assertIn('saved.freeze(source)', rendered)
        self.assertIn('(source / POLICY).chmod(420)', rendered)

    def test_authority_checks_exact_overlay_and_controls_remain_strict(self):
        source = r181_build.operator_source('a' * 64, 'b' * 64)
        self.assertIn("sha(output / 'MAIN_JOURNAL.py') == '" + 'b' * 64 + "'", source)
        self.assertIn("(attempt / 'DISPATCH_ONCE').mkdir()", source)
        self.assertIn('original_privileged_clear_admission', source)
        self.assertIn('no_boundary_race_after_pause', source)
        self.assertIn('same_saved_boundary_before_termination', source)
        self.assertIn('bound_successor_control', source)

    def test_already_cached_journal_preserves_all_bytes(self):
        source = (HERE.parents[3] / 'gpu/orch_r125_stream_journal.py').read_text()
        self.assertEqual(r181_patch.patch_journal(source, source), source)

    def test_partial_cache_is_rejected(self):
        source = (HERE.parents[3] / 'gpu/orch_r125_stream_journal.py').read_text()
        damaged = source.replace('def _record_snapshot(self):', 'def removed_snapshot(self):')
        with self.assertRaisesRegex(ValueError, 'partial_or_different'):
            r181_patch.patch_journal(damaged, source)


if __name__ == '__main__':
    unittest.main()
