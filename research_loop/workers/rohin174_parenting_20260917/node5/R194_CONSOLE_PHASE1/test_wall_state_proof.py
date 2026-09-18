import ast
from pathlib import Path
from types import SimpleNamespace
import unittest


class WallStateProofTests(unittest.TestCase):
    def code(self):
        module = ast.parse(Path(__file__).with_name('saved_primitives.py').read_text())
        function = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == 'boundary_cpu')
        assignment = next(node for node in function.body if isinstance(node, ast.Assign)
                          and any(isinstance(target, ast.Name) and target.id == 'code' for target in node.targets))
        tree = ast.parse(ast.literal_eval(assignment.value))
        start = next(index for index, node in enumerate(tree.body) if isinstance(node, ast.Assign)
                     and any(isinstance(target, ast.Name) and target.id == 'extension' for target in node.targets))
        return compile(ast.Module(body=tree.body[start:start + 2], type_ignores=[]), 'state_proof_wall_branch', 'exec')

    def evaluate(self, plan, saved_wall):
        calls = []

        def require(condition, reason):
            if not condition:
                raise ValueError(reason)

        def extension(*arguments, **keywords):
            calls.append((arguments, keywords))
            return 'validated_extension'

        values = dict(native=SimpleNamespace(require=require, prepare_wall_extension=extension, sha=lambda path: 'pin'),
            plan=plan, stream=SimpleNamespace(deadline_unix=saved_wall), sys=SimpleNamespace(argv=['test', 'plan']))
        exec(self.code(), values)
        return calls, values['extension']

    def test_same_wall_never_requests_extension_authority(self):
        calls, result = self.evaluate(dict(hard_end_unix=1789776000), 1789776000)
        self.assertEqual(calls, [])
        self.assertIsNone(result)

    def test_changed_wall_without_authority_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'unchanged_saved_wall'):
            self.evaluate(dict(hard_end_unix=1789776001), 1789776000)

    def test_real_extension_still_uses_original_validation(self):
        calls, result = self.evaluate(dict(hard_end_unix=1789776001, authorized_wall_extension={'bound': True}), 1789776000)
        self.assertEqual(len(calls), 1)
        self.assertEqual(result, 'validated_extension')


if __name__ == '__main__':
    unittest.main()
