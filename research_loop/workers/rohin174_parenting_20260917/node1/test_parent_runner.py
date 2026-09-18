import ast
import inspect
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from parent_runner import compile_parent, instrument


HERE = Path(__file__).resolve().parent
PREP = HERE / 'ACTIVATION_PREP_1789677032315502264/ASSIGNMENTS.json'


class ActualAdapterTests(unittest.TestCase):
    def test_all_six_actual_loops_keep_guards_and_reserved_cursor(self):
        rows = json.loads(PREP.read_text())['rows']
        for row in rows:
            with self.subTest(physical=row['physical']):
                raw = Path(row['original']['source']['path']).read_text()
                tree = ast.parse(raw)
                serve = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'serve')
                guards = [ast.unparse(node) for node in serve.body
                          if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
                          and isinstance(node.value.func, ast.Name) and node.value.func.id == 'require']
                self.assertTrue(any('bound_parent_resume' in guard for guard in guards))
                self.assertTrue(any('same_parented_life' in guard for guard in guards))
                self.assertTrue(any('preserved_predecessor_started' in guard for guard in guards))
                compiled = compile_parent(raw, str(row['physical']), 100000)
                serve_code = next(value for value in compiled.co_consts if inspect.iscode(value) and value.co_name == 'serve')
                self.assertIn(100000, serve_code.co_consts)
                self.assertIn('max', serve_code.co_names)
                self.assertIn('bound_parent_resume', serve_code.co_consts)

    def test_cursor_not_bool_negative_or_float(self):
        for cursor in (True, -1, 1.0):
            with self.subTest(cursor=cursor), self.assertRaisesRegex(ValueError, 'reserved_cursor'):
                compile_parent('def serve():\n last_count = 0\n', 'fixture', cursor)

    def test_missing_or_ambiguous_cursor_rejected(self):
        for raw in ('def serve():\n pass\n', 'def serve():\n last_count=0\n last_count=1\n'):
            with self.assertRaisesRegex(ValueError, 'one_preserved'):
                compile_parent(raw, 'fixture', 12)

    def test_publication_independent_caps_before_transport(self):
        for words in (90, 120, 160, 240):
            with self.subTest(words=words):
                parent = dict(strong=mock.Mock(), publish=mock.Mock())
                instrument(parent, dict(output='/CPU_ONLY/parent'), dict(words=words))
                for message in (' '.join(['word'] * (words + 1)), 'x' * 4097, '\u00e9' * 2049):
                    with self.assertRaisesRegex(ValueError, 'child_facing_cap'):
                        parent['publish']('/CPU_ONLY', {}, message)

    def test_explicit_withdrawal_blocks_provider_not_child(self):
        with tempfile.TemporaryDirectory(dir=HERE, prefix='cpu_withdrawal_') as directory:
            Path(directory, 'PARENT_WITHDRAWAL.json').write_text('{}')
            provider = mock.Mock()
            parent = dict(strong=provider, publish=mock.Mock())
            instrument(parent, dict(output=str(Path(directory, 'parent'))), dict(words=90))
            with self.assertRaisesRegex(ValueError, 'withdrawal'):
                parent['strong']('fixture', Path(directory), 0, 'fixture')
            provider.assert_not_called()


if __name__ == '__main__':
    unittest.main(verbosity=2)
