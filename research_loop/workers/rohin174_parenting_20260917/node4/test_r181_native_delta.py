"""CPU source-level R181 regressions preserving the exact existing R179 suffix."""

import ast
import importlib.util
from pathlib import Path
import unittest


HOME = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('r181_delta', HOME / 'r181_native_delta.py')
delta = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(delta)


class DeltaTests(unittest.TestCase):
    def setUp(self):
        self.actual = (HOME / 'r181_reference/lane0/source/gpu/orch_r125_continual_native.py').read_text()
        self.main = (HOME.parents[3] / 'gpu/orch_r125_continual_native.py').read_text()

    def test_exact_helper_bytes_and_R179_preserved(self):
        patched = delta.patch_native(self.actual, self.main)
        for name in ('select_rehearsal_rows', 'respond_to_presleep_inbox'):
            self.assertEqual(delta.function(patched, name), delta.function(self.main, name))
        self.assertIn('from gpu.orch_r179_context_survival import retain_or_compact', patched)
        self.assertIn('r145_prepare_sleep(self.engine.model', patched)
        self.assertIn('gpu.orch_r138_kernel_recovery', patched)

    def test_selection_precedes_target_encoding(self):
        patched = delta.patch_native(self.actual, self.main)
        sleep = next(node for node in ast.walk(ast.parse(patched)) if isinstance(node, ast.FunctionDef) and node.name == 'sleep')
        text = ast.get_source_segment(patched, sleep)
        self.assertLess(text.index('select_rehearsal_rows'), text.index('encode_sleep_targets'))

    def test_no_idempotent_repatch_of_immutable_successor(self):
        patched = delta.patch_native(self.actual, self.main)
        with self.assertRaisesRegex(ValueError, 'fresh_R181_successor'):
            delta.patch_native(patched, self.main)

    def test_unknown_actual_seam_fails_without_overwriting(self):
        with self.assertRaisesRegex(ValueError, 'actual_source_seam_drift'):
            delta.patch_native(self.actual.replace("plan['rehearsal_presentations'] == 1", 'True'), self.main)


if __name__ == '__main__':
    unittest.main()
