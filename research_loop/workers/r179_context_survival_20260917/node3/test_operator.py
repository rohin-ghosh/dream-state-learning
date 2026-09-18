"""Exact-scope adapters and preserved lifecycle, CPU only."""

import ast
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
spec = importlib.util.spec_from_file_location('node3_context_operator_tests', HERE / 'OPERATOR.py')
operator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(operator)


class OperatorTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.bootstrap = Path(self.directory.name) / 'bootstrap'
        self.bootstrap.mkdir()
        package = json.loads((HERE / 'SOURCE_PACKAGE.json').read_text())
        import base64
        for name, item in package['files'].items():
            (self.bootstrap / name).write_bytes(base64.b64decode(item['base64']))
        self.patcher = patch.object(operator, 'HERE', self.bootstrap)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        self.file_patcher = patch.object(operator, '__file__', str(self.bootstrap / 'OPERATOR.py'))
        self.file_patcher.start()
        self.addCleanup(self.file_patcher.stop)
        self.family = operator.family_namespace()
        self.original = dict(__name__='private_reference', __file__=str(self.bootstrap / 'OPERATOR.py'))
        exec(compile((self.bootstrap / 'FAMILY.py').read_bytes(), str(self.bootstrap / 'OPERATOR.py'), 'exec'), self.original)

    def test_frozen_functions_unchanged_and_namespaces_private(self):
        for name in ('stage', 'supervise', 'contained', 'contained_command', 'direct_command',
                     'direct_minor', 'guard_delta', 'plan_delta', 'validate_fresh', 'validate_new',
                     'old_modules', 'new_modules', 'verify_legacy_state', 'claim_boundary'):
            with self.subTest(name=name):
                self.assertEqual(self.family[name].__code__, self.original[name].__code__)
                self.assertIs(self.family[name].__globals__, self.family)
        self.assertNotIn('pause_recovery', self.original)
        self.assertIsNot(self.family, self.original)

    def test_handoff_exact_recovery_AST_reverse_parity(self):
        source = (self.bootstrap / 'FAMILY.py').read_bytes()
        captured = []
        real_compile = compile
        def capture(tree, *args, **kwargs):
            if isinstance(tree, ast.Module):
                captured.append(deepcopy(tree))
            return real_compile(tree, *args, **kwargs)
        with patch('builtins.compile', side_effect=capture):
            operator.load('RECOVERY_ADAPTER.py').repaired_handoff(self.family, source)
        transformed = next(tree for tree in captured if tree.body and isinstance(tree.body[0], ast.FunctionDef)
                           and tree.body[0].name == 'handoff').body[0]
        original = next(node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef) and node.name == 'handoff')
        transformed.body[-1].finalbody = deepcopy(original.body[-1].finalbody)
        class Reverse(ast.NodeTransformer):
            def visit_Call(self, node):
                if ast.unparse(node.func) == 'pause_recovery.pause':
                    return ast.parse("helper.pause_exact(request['processes'][name], descriptors[name])", mode='eval').body
                if ast.unparse(node.func) == 'pause_recovery.resume':
                    return ast.parse('helper.resume_paused(paused, descriptors)', mode='eval').body
                return self.generic_visit(node)
        self.assertEqual(ast.dump(Reverse().visit(transformed)), ast.dump(original))

    def test_legacy_saved_state_only_native_pin_changes(self):
        before = self.original['saved_evidence'].__code__
        after = self.family['saved_evidence'].__code__
        self.assertEqual(before.co_code, after.co_code)
        old = '7626d13974a78c713b9e966093e285e1e8a4f194301dd8b69ec68cfcae656526'
        new = '106be5bd8bde805c092bbbf49233391b799c2b0641d3c41fdd75cb66d75ebc45'
        self.assertEqual(tuple(new if item == old else item for item in before.co_consts), after.co_consts)

    def test_dependency_poison_refused_before_lifecycle(self):
        for name in ('FAMILY.py', 'RECOVERY.py', 'RECOVERY_ADAPTER.py', 'BOUNDARY_API.py', 'SEED.json', 'BUILDER_SCOPE.json'):
            with self.subTest(name=name):
                path = self.bootstrap / name
                original = path.read_bytes()
                path.write_bytes(original+b' ')
                with self.assertRaisesRegex(ValueError, 'dependency_pin'):
                    operator.family_namespace()
                path.write_bytes(original)

    def test_exact_plan_scope_rejects_recipe_source_wall_changes(self):
        lane = operator.lane_for(1)
        plan = json.loads((HERE / 'CURRENT_PREPARATION.json').read_text())['lanes'][1]['plan']
        with patch.object(operator, 'read', return_value=plan), patch.object(operator, 'sha', return_value=lane['plan_ref']['sha256']), \
                patch.object(operator, 'lane_for', return_value=lane):
            self.assertEqual(operator.scope(plan), 1)
            for key, value in (('source_root', '/tmp/wrong'), ('root', '/tmp/wrong'), ('gpu_uuid', 'GPU-wrong'),
                               ('hard_end_unix', plan['hard_end_unix']+1), ('seed', 42), ('authorized_wall_extension', {})):
                with self.subTest(key=key), self.assertRaises(ValueError):
                    operator.scope(dict(plan, **{key: value}))

    def direct_fixture(self):
        row = json.loads((HERE / 'DIRECT_DETAILS.json').read_text())[0]
        lane = operator.lane_for(row['physical'])
        processes = {role: {key: value for key, value in process.items() if key != 'state'}
                     for role, process in row['processes'].items()}
        config, plan = row['config'], row['plan']
        timer = processes['timer']
        helper = SimpleNamespace(PYTHON=Path('/localhome/local-rohing/v2/venv/bin/python'),
            process_record=lambda pid: next(process for process in processes.values() if process['pid'] == pid),
            read=lambda path: dict(pid=timer['pid'], parent_start_ticks=timer['start_ticks'],
                guard_sha256=lane['guard_ref']['sha256'], plan_sha256=config['plan_sha256']),
            sha=lambda path: lane['guard_ref']['sha256'])
        return row, lane, processes, helper

    def test_current_contained_direct_argv_and_ownership(self):
        row, lane, processes, helper = self.direct_fixture()
        with patch.object(operator, 'scope', return_value=0), patch.object(operator, 'lane_for', return_value=lane), \
                patch.object(operator, 'sha', return_value=operator.DEPENDENCIES['FAMILY.py']), patch.object(operator.os, 'getuid', return_value=2524):
            self.assertEqual(operator.current_direct_processes(helper, lane['identity']['pid'], lane['guard_ref']['path'],
                row['config'], row['plan']), processes)
            for role, key, replacement in (('supervisor', 'argv', ['wrong']), ('actor', 'uid', 0),
                    ('actor', 'cvd', ['0']), ('timer', 'cgroup', '0::/wrong'), ('actor', 'start_ticks', '1'),
                    ('supervisor', 'parent', 8), ('actor', 'cwd', '/tmp/wrong')):
                with self.subTest(role=role, key=key):
                    original = processes[role][key]
                    processes[role][key] = replacement
                    with self.assertRaises(ValueError):
                        operator.current_direct_processes(helper, lane['identity']['pid'], lane['guard_ref']['path'], row['config'], row['plan'])
                    processes[role][key] = original

    def test_actual_cli_contains_inherited_entry_transitions(self):
        result = subprocess.run([sys.executable, '-B', str(HERE / 'OPERATOR.py'), '--help'], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        for action in ('supervise', 'contained', 'validate', 'handoff'):
            self.assertIn(action, result.stdout)
        self.assertNotIn('readmit', result.stdout)


if __name__ == '__main__':
    unittest.main()
