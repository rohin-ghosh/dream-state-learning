"""Deadline-only continuation, distinct authority and unchanged lifecycle checks."""

import ast
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import unittest


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('wall_operator_cpu', HERE / 'WALL_OPERATOR.py')
wall = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wall)
spec2 = importlib.util.spec_from_file_location('original_scope_cpu', HERE / 'OPERATOR.py')
original = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(original)


class WallTests(unittest.TestCase):
    def setUp(self):
        preparation = json.loads((HERE / 'CURRENT_PREPARATION.json').read_text())
        self.plan = preparation['lanes'][1]['plan']
        self.saved = dict(state=dict(deadline_unix=wall.OLD_WALL), state_sha256='a'*64)
        self.new = wall.proposed_plan(self.plan, Path('/localhome/local-rohing/candidate/source'), self.saved)
        import base64
        package = json.loads((HERE / 'SOURCE_PACKAGE.json').read_text())
        self.source = base64.b64decode(package['files']['FAMILY.py']['base64'])
        self.family = dict(__name__='test_original', __file__='/tmp/unused.py')
        exec(compile(self.source, '/tmp/unused.py', 'exec'), self.family)

    def test_exact_wall_and_ceiling(self):
        wall.wall_plan_delta(self.family['plan_delta'], self.plan, self.new)
        self.assertEqual(self.new['hard_end_unix'], 1789689000)
        self.assertEqual(self.new['lease_end_unix'], 1789689600)
        self.assertEqual(self.new['max_sleeps'], self.plan['max_sleeps'])

    def test_reject_any_other_plan_change(self):
        for key, value in (('root', '/tmp/reset'), ('seed', 42), ('lease_end_unix', 1789689601),
                           ('hard_end_unix', 1789689600), ('segments_per_sleep', 3)):
            with self.subTest(key=key), self.assertRaises(ValueError):
                wall.wall_plan_delta(self.family['plan_delta'], self.plan, dict(self.new, **{key: value}))

    def test_exact_authorization_fields(self):
        for key, value in (('previous_deadline_unix', 1), ('previous_stream_sha256', 'x'),
                           ('safety_margin_seconds', 0), ('lease_end_unix', 1789776600)):
            mutated = deepcopy(self.new)
            mutated['authorized_wall_extension'][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                wall.wall_plan_delta(self.family['plan_delta'], self.plan, mutated)

    def test_handoff_only_bound_cutoff_change(self):
        transformed = ast.parse(wall.handoff_source(self.source))
        old = ast.parse(self.source)
        function = next(node for node in transformed.body if isinstance(node, ast.FunctionDef) and node.name == 'handoff')
        deadlines = [node for node in ast.walk(function) if isinstance(node, ast.Assign)
                     and any(isinstance(target, ast.Name) and target.id == 'deadline' for target in node.targets)]
        matches = [node for node in ast.walk(deadlines[0]) if isinstance(node, ast.Constant) and node.value == 180]
        self.assertEqual(len(matches), 1)
        matches[0].value = 900
        self.assertEqual(ast.dump(transformed), ast.dump(old))

    def test_previous_scope_policy_remains_frozen(self):
        import hashlib
        self.assertEqual(hashlib.sha256((HERE / 'OPERATOR.py').read_bytes()).hexdigest(), wall.ADAPTER_SHA)
        self.assertEqual(hashlib.sha256((HERE.parent / 'NODE3_EXISTING_LEASE_CONTINUATION.md').read_bytes()).hexdigest(), wall.AUTH_SHA)
        self.assertEqual(hashlib.sha256((HERE.parent / 'BUILDER_SCOPE.json').read_bytes()).hexdigest(),
                         original.DEPENDENCIES['BUILDER_SCOPE.json'])


if __name__ == '__main__':
    unittest.main()
