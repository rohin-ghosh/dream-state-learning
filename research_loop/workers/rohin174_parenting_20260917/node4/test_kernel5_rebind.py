"""CPU confinement command and exact routing tests; no GPU or service calls."""

import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch


HOME = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('kernel5', HOME / 'kernel5_rebind.py')
kernel5 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(kernel5)


class Kernel5Tests(unittest.TestCase):
    def test_only_kernel_children_on_physical5_minor6(self):
        for physical, root in kernel5.ROOTS.items():
            kernel5.target(physical, root, 5, kernel5.UUID, 6)
        for target in (0, 1, 2, 3, 4, 6, 7):
            with self.subTest(target=target), self.assertRaisesRegex(ValueError, 'physical5'):
                kernel5.target(0, kernel5.ROOTS[0], target, kernel5.UUID, 6)
        with self.assertRaisesRegex(ValueError, 'no_raw_or_control'):
            kernel5.target(1, '/localhome/local-rohing/orch_r136_raw_unparented_a40r1_20260916_attempt1/run1', 5, kernel5.UUID, 6)

    def module(self):
        source = (kernel5.REPO / 'gpu/orch_r132_kernel_executor.py').read_text()
        module = types.ModuleType('cpu_only_patched_executor')
        module.__file__ = str(HOME / 'CPU_ONLY_NOT_DEPLOYED.py')
        closure = HOME / 'kernel5_cpu_stage_20260917T2203Z/source'
        with patch.dict(sys.modules), patch.object(sys, 'path', [str(closure)] + sys.path):
            for name in list(sys.modules):
                if name in ('gpu', 'organism_v6') or name.startswith(('gpu.', 'organism_v6.')):
                    del sys.modules[name]
            exec(compile(kernel5.rebind(source), module.__file__, 'exec'), module.__dict__)
        return module

    def test_strict_sandbox_denies_every_other_GPU_by_policy(self):
        executor = self.module()
        command = executor.command(Path('/tmp/kernel5_cpu_fixture'), Path('/tmp/kernel5_cpu_runtime'), 'orch-r132-kernel-' + 'a' * 32)
        self.assertIn('--property=DevicePolicy=strict', command)
        self.assertIn('--property=NoNewPrivileges=yes', command)
        self.assertIn('--property=PrivateNetwork=yes', command)
        self.assertIn('--property=DeviceAllow=/dev/nvidia6 rw', command)
        for minor in (0, 1, 2, 3, 4, 5, 7):
            self.assertNotIn('--property=DeviceAllow=/dev/nvidia' + str(minor) + ' rw', command)
        self.assertIn('CUDA_VISIBLE_DEVICES=' + kernel5.UUID, command)
        self.assertEqual(executor.GPU_MINOR, 6)
        self.assertIn('physical5_minor6', str(executor.LOCK_PATH))

    def test_still_requires_real_fresh_admission(self):
        executor = self.module()
        self.assertIn('Main_custody_and_fresh_census_required', executor.validate_admission.__code__.co_consts)
        self.assertIn('assigned_GPU_must_be_idle_before_trusted_probes', executor.run_trusted_probes.__code__.co_consts)

    def test_unknown_or_already_modified_source_refused(self):
        source = (kernel5.REPO / 'gpu/orch_r132_kernel_executor.py').read_text()
        for value in (source + '\n', kernel5.rebind(source)):
            with self.assertRaisesRegex(ValueError, 'exact_reviewed'):
                kernel5.rebind(value)

    def test_fixture_binding_changes_only_historical_target(self):
        name = 'tests/test_orch_r148_kernel_tool_service.py'
        source = (kernel5.REPO / name).read_text()
        patched = kernel5.rebind_test_fixture(name, source)
        self.assertIn('physical_index=5', patched)
        self.assertIn("nodes={'/dev/nvidia6': [195, 6]}", patched)
        self.assertIn('device_minor=6, executor_lock=', patched)
        for value in (patched, source.replace('physical_index=2', 'physical_index=3')):
            with self.assertRaisesRegex(ValueError, 'exact_historical_fixture_device_binding'):
                kernel5.rebind_test_fixture(name, value)

    def test_non_target_tests_unchanged(self):
        name = 'tests/test_orch_r158_kernel_execution.py'
        source = (kernel5.REPO / name).read_text()
        self.assertEqual(kernel5.rebind_test_fixture(name, source), source)

    def test_campaign_retains_both_admission_identity_assertions(self):
        name = 'tests/test_orch_r148_kernel_service_campaign.py'
        source = (kernel5.REPO / name).read_text()
        patched = kernel5.rebind_test_fixture(name, source)
        self.assertEqual(patched.count("admission['device_minor'] == 6"), 2)
        self.assertIn("device_identity.return_value['physical_index'] == 5", patched)


if __name__ == '__main__':
    unittest.main()
