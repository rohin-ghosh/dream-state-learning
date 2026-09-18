"""Synthetic regressions for the read-only successor-observation repair."""

import ast
from pathlib import Path
import unittest

import build_r188_observer as observer


class ObserverTests(unittest.TestCase):
    def test_only_exact_bound_original_is_accepted(self):
        with self.assertRaisesRegex(ValueError, 'exact_existing_readonly_observer'):
            observer.patch('not the deployed observer')

    def test_both_recoveries_and_legacy_receipts_remain_distinct(self):
        source = observer.patch((Path(observer.HOME) / 'r185_node4_status.py').read_text())
        self.assertIn("'recovery0_attempt2' if physical == 0 else 'recovery1'", source)
        self.assertIn("'R188_SAVED_MODEL_LOADED' if physical in (0, 1) else 'EXACT_SAVED_SUCCESSOR_LOADED'", source)
        self.assertIn("plan['root'] == str(root) and plan['physical'] == physical", source)
        self.assertIn("plan['hard_end_unix'] == WALL", source)

    def test_identity_and_request_validation_are_unchanged(self):
        original = (Path(observer.HOME) / 'r185_node4_status.py').read_text()
        source = observer.patch(original)
        previous = {node.name: ast.dump(node) for node in ast.parse(original).body if isinstance(node, ast.FunctionDef)}
        current = {node.name: ast.dump(node) for node in ast.parse(source).body if isinstance(node, ast.FunctionDef)}
        for name in previous:
            if name != 'collect_remote':
                self.assertEqual(previous[name], current[name])
        self.assertIn("'render_record_pin'", source)
        self.assertIn("'actual_tail_chain'", source)
        self.assertIn("'tail_ends_at_verified_cursor'", source)

    def test_stopped_parent_cursor_catches_up_with_bounded_verified_polls(self):
        source = observer.patch((Path(observer.HOME) / 'r185_node4_status.py').read_text())
        self.assertIn('for cursor_step in range(7):', source)
        self.assertEqual(source.count('cursor_sha256=snapshots._digest(cursor)'), 2)
        self.assertIn("require(polled['snapshot']['caught_up'], 'bounded_cursor_caught_up')", source)


if __name__ == '__main__':
    unittest.main()
