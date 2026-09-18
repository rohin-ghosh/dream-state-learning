import ast
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import orch_r145_suffix_boundary as boundary
from gpu.orch_r145_node3_capacity_recovery import GRAD_TOLERANCE, LOSS_TOLERANCE, SCHEMA


class Labels:
    def __getitem__(self, item):
        return item


class SuffixBoundaryTests(unittest.TestCase):
    def unpatched_native_fixture(self):
        source = Path('gpu/orch_r125_continual_native.py').read_text()
        if 'orch_r145_suffix_boundary' not in source:
            return source
        native_class = next(node for node in ast.parse(source).body
            if isinstance(node, ast.ClassDef) and node.name == 'NativeChild')
        method = next(node for node in native_class.body
            if isinstance(node, ast.FunctionDef) and node.name == 'sleep')
        remove = []
        for statement in method.body:
            if isinstance(statement, ast.ImportFrom) and statement.module == 'gpu.orch_r145_suffix_boundary':
                remove.append(statement)
            elif isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call):
                call = statement.value
                if isinstance(call.func, ast.Name) and call.func.id == 'r145_prepare_sleep':
                    remove.append(statement)
                elif any(isinstance(node, ast.keyword) and node.arg == 'runtime_memory_policy'
                         for node in ast.walk(call)):
                    remove.append(statement)
        self.assertEqual(len(remove), 4)
        lines = source.splitlines(keepends=True)
        for statement in reversed(remove):
            del lines[statement.lineno-1:statement.end_lineno]
        self.assertEqual(source.count(boundary.NEW_FORWARD), 1)
        unpatched = ''.join(lines).replace(boundary.NEW_FORWARD, boundary.OLD_FORWARD)
        self.assertNotIn('orch_r145_suffix_boundary', unpatched)
        from gpu.orch_r144_target_patch import without_sleep
        self.assertEqual(without_sleep(ast.parse(source)), without_sleep(ast.parse(unpatched)))
        return unpatched

    def proof(self):
        return dict(schema=SCHEMA, status='PASS', train_only=True, state_restored=True,
            optimizer_updates=0, exact_learning_trajectory_claim=False,
            runtime_pin_sha256='a' * 64, loss_tolerance=LOSS_TOLERANCE,
            gradient_tolerance=GRAD_TOLERANCE,
            comparisons=[dict(exact_rng=True, original_losses=[1.0] * 5, prospective_losses=[1.0] * 5,
                max_gradient_absolute_error=0.0,
                original_memory=dict(full_input_tokens=512, peak_allocated_bytes=10000),
                prospective_memory=dict(full_input_tokens=512, peak_allocated_bytes=5000))],
            longest_child_prospective_only=dict(source_sha256='b' * 64,
                original_long_forward_attempted=False, memory=dict(free_after_bytes=3 * 1024**3)))

    def test_anchor_labels_are_returned_by_identity_without_slicing(self):
        labels = Labels()
        self.assertIs(boundary.loss_arguments('ANCHOR:math', None, labels)['labels'], labels)

    def test_child_predictor_and_targets_kept(self):
        sample = SimpleNamespace(input_ids=(3, 4, 5, 6), labels=(-100, -100, 5, 6), target_ids=(5, 6))
        self.assertEqual(boundary.loss_arguments('NEW', sample, Labels()),
            dict(labels=(slice(None), slice(-3, None)), logits_to_keep=3))
        self.assertEqual(boundary.loss_arguments('REHEARSAL', sample, Labels())['logits_to_keep'], 3)
        with self.assertRaisesRegex(ValueError, 'known_child_presentation_kind'):
            boundary.loss_arguments('DEV', sample, Labels())

    def test_incomplete_or_wrong_runtime_proof_cannot_patch(self):
        for key, value in [('status', 'FAIL'), ('train_only', False), ('state_restored', False),
                ('optimizer_updates', 1), ('exact_learning_trajectory_claim', True),
                ('runtime_pin_sha256', 'c' * 64), ('comparisons', []),
                ('loss_tolerance', {}), ('gradient_tolerance', {}),
                ('longest_child_prospective_only', {})]:
            proof = self.proof()
            proof[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                boundary.validate_gpu_proof(proof, 'a' * 64)

    def test_missing_comparison_or_changed_context_rejected(self):
        for key, value in [('original_memory', {}), ('prospective_losses', [float('nan')] * 5),
                ('max_gradient_absolute_error', float('nan')),
                ('prospective_memory', dict(full_input_tokens=2, peak_allocated_bytes=5000))]:
            proof = self.proof()
            proof['comparisons'][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                boundary.validate_gpu_proof(proof, 'a' * 64)

    def test_new_patch_preserves_source_and_rejects_reapplication(self):
        source = self.unpatched_native_fixture()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'synthetic_GPU_proof.json'
            path.write_text(json.dumps(self.proof()))
            proof_sha = boundary.digest_bytes(path.read_bytes())
            source_sha = boundary.digest_bytes(source.encode())
            modified = boundary.patch_source(source, source_sha, 'a' * 64, path, proof_sha)
            self.assertIn('runtime_memory_policy=', modified)
            self.assertIn('orch_r144_sleep_targets', modified)
            for original, expected in [(modified, boundary.digest_bytes(modified.encode())),
                    (source, 'd' * 64), (source.replace('    def sleep(', '    def not_sleep('),
                     boundary.digest_bytes(source.replace('    def sleep(', '    def not_sleep(').encode()))]:
                with self.assertRaises(ValueError):
                    boundary.patch_source(original, expected, 'a' * 64, path, proof_sha)
            path.write_text('{}')
            with self.assertRaisesRegex(ValueError, 'exact_proof_bytes'):
                boundary.patch_source(source, source_sha, 'a' * 64, path, proof_sha)

    def test_runtime_binding_checked_at_sleep_without_lane_reassignment(self):
        from gpu import orch_r145_node3_capacity_recovery as capacity
        model = object()
        runtime = dict(synthetic=True)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / boundary.RUNTIME_FILE
            path.write_text(json.dumps(runtime))
            with patch.object(capacity, 'verify_model') as verify:
                boundary.prepare_sleep(model, Path(directory) / 'native.py', boundary.digest_bytes(path.read_bytes()))
                verify.assert_called_once_with(model, runtime)
            path.unlink()
            path.symlink_to(Path(directory) / 'missing')
            with self.assertRaisesRegex(ValueError, 'no_proof_symlinks'):
                boundary.prepare_sleep(model, Path(directory) / 'native.py', 'a' * 64)


if __name__ == '__main__':
    unittest.main()
