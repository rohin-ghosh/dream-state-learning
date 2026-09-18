import ast
import json
from pathlib import Path
import tempfile
import unittest

import importlib.util

SPEC = importlib.util.spec_from_file_location('memory_operator', Path(__file__).with_name('memory_handoff.py'))
operator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(operator)


class BoundaryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name).resolve()
        (self.root / 'stream/records').mkdir(parents=True)
        state = dict(pending=None, sleep_frontier=1, rows=[{'preserved': True}])
        self.complete = self.record(1, 'SLEEP_COMPLETE', dict(cycle=48, status='COMPLETE', checkpoint={'pin': 'same'},
            resume_state=dict(state=state, sha256=operator.saved.digest(state))))

    def record(self, index, kind, document, previous='origin'):
        value = dict(index=index, kind=kind, document=document, previous_sha256=previous)
        value['sha256'] = operator.saved.digest(value)
        (self.root / 'stream/records' / f'{index:020d}.json').write_text(json.dumps(value))
        return value

    def test_complete_and_metadata_only_tail(self):
        self.assertEqual(operator.complete_boundary(self.root)['cycle'], 48)
        self.record(2, 'R184_LEARN_COMPLETE', dict(cycle=48, checkpoint={'pin': 'same'}), self.complete['sha256'])
        self.assertEqual(operator.complete_boundary(self.root)['index'], 1)

    def test_unsaved_request_is_not_boundary(self):
        self.record(2, 'REQUEST', {}, self.complete['sha256'])
        self.assertIsNone(operator.complete_boundary(self.root))

    def test_inbox_registration_is_not_boundary(self):
        self.record(2, 'INBOX', {}, self.complete['sha256'])
        self.assertIsNone(operator.complete_boundary(self.root))

    def test_wrong_cycle_or_checkpoint_rejected(self):
        self.record(2, 'R184_LEARN_COMPLETE', dict(cycle=49, checkpoint={'pin': 'same'}), self.complete['sha256'])
        with self.assertRaisesRegex(ValueError, 'exact_R184_postlearn_boundary'):
            operator.complete_boundary(self.root)

    def test_history_mask_recipe_and_other_native_methods_unchanged(self):
        directory = Path(__file__).parent
        original = (directory / 'ORIGINAL_NATIVE.py').read_text()
        changed = operator.patch_native(original, (directory / 'main/gpu/orch_r125_continual_native.py').read_text())
        before = ast.parse(original)
        after = ast.parse(changed)
        previous = {node.name: node for node in before.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
        current = {node.name: node for node in after.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
        for name, node in previous.items():
            if name not in ('validate_plan', 'NativeChild'):
                self.assertEqual(ast.dump(node), ast.dump(current[name]))
        old_methods = {node.name: node for node in previous['NativeChild'].body if isinstance(node, ast.FunctionDef)}
        new_methods = {node.name: node for node in current['NativeChild'].body if isinstance(node, ast.FunctionDef)}
        for name, node in old_methods.items():
            if name != 'sleep':
                self.assertEqual(ast.dump(node), ast.dump(new_methods[name]))
        self.assertIn('sample=sample', changed)
        self.assertIn('new_presentations=16', changed)


if __name__ == '__main__':
    unittest.main()
