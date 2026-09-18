import ast
from copy import deepcopy
import importlib.util
import inspect
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / 'research_loop/workers/r143_node5_allocator_20260916t1427z'
SPEC = importlib.util.spec_from_file_location('node5_suffix_test', ROOT / 'node5_suffix_confined_20260916t1626z.py')
stage = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(stage)


class Node5SuffixConfinedTests(unittest.TestCase):
    def test_inherits_exact_operator_all_recovery_functions(self):
        inherited = stage.operator()
        for name in ('supervise', 'contained', 'monitor', 'preserved_pilot', 'restore_pilot', 'handoff_run1'):
            self.assertEqual(Path(getattr(inherited, name).__code__.co_filename), stage.ORIGINAL)
        self.assertEqual(inherited.__file__, str(Path(stage.__file__).resolve()))
        self.assertEqual(inherited.CONTROLS, stage.CONTROLS)

    def test_existing_attempts_never_reused(self):
        self.assertEqual(set(stage.CONTROLS), {2, 6})
        self.assertFalse(set(stage.CONTROLS.values()) & set(stage.PREVIOUS.values()))

    def test_plan_allows_only_relocated_source_and_same_startup(self):
        original = dict(source_root='/old', startup_context=dict(path='/old/birth', sha256='same'),
                        root='/life', context_limit=16384, anchor_lambda=.25, new_presentations=16)
        proposed = deepcopy(original)
        proposed['source_root'] = '/new'
        proposed['startup_context']['path'] = '/new/birth'
        stage.plan_delta(original, proposed)
        for key, value in [('root', '/other'), ('context_limit', 8192), ('anchor_lambda', .2), ('new_presentations', 1)]:
            changed = deepcopy(proposed)
            changed[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                stage.plan_delta(original, changed)

    def test_guard_keeps_all_device_and_lease_fields(self):
        original = dict(attempt_dir='/old', source_pins={}, plan_path='/p', plan_sha256='p', allocation_path='/a',
            allocation_sha256='a', resume=True, hard_end_unix=999, device_containment=dict(uid=2524,gid=2524,minor=2,unit='old'))
        proposed = deepcopy(original)
        proposed['attempt_dir'] = '/new'
        proposed['device_containment']['unit'] = 'new'
        stage.guard_delta(original, proposed)
        for key, value in [('minor', 6), ('uid', 0), ('gid', 0)]:
            changed = deepcopy(proposed)
            changed['device_containment'][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                stage.guard_delta(original, changed)
        proposed['hard_end_unix'] += 1
        with self.assertRaises(ValueError):
            stage.guard_delta(original, proposed)

    def test_stage_has_no_signals_or_model_creation(self):
        source = inspect.getsource(stage.stage)
        for forbidden in ('pidfd_send_signal', 'os.kill', 'NativeChild(', 'Popen('):
            self.assertNotIn(forbidden, source)
        self.assertIn('same_live_run1_during_staging', source)
        self.assertIn('preserved_pilot', source)

    def test_patch_calls_only_generic_proof_bound_patcher(self):
        source = inspect.getsource(stage.patch_copy)
        self.assertIn('boundary.patch_source(original, NATIVE_SHA, RUNTIME_SHA, proof, PROOF_SHA)', source)
        self.assertNotIn('.replace(', source)
        self.assertEqual(stage.PROOF_SHA, '3d4e5ed2e7acf7501ab21a1361c511f5db9fe4ad25f96dd1e691fbc47277b281')

    def test_receiving_rows_use_original_encoder_and_original_train_anchors(self):
        source = inspect.getsource(stage.rows)
        for gate in ('native.encode_own', 'eligible_rows', 'encode_sleep_targets', 'build_inventory',
                     'capacity.validate_rows', 'not torch.cuda.is_initialized()', 'actual_TRAIN_state_hash'):
            self.assertIn(gate, source)
        self.assertNotIn('installed_runtime_pins()', source)
        self.assertNotIn('model(', source)


if __name__ == '__main__':
    unittest.main()
