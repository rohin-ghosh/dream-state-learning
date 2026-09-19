import ast
import hashlib
import os
from pathlib import Path
import sys
import tempfile
import time
from types import FunctionType, ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import pending_sleep_contract as contract


HERE = Path(__file__).resolve().parent
PINS = {
    'r184_node2_confinement.py': '90231000e70c10fd64181e647eb57f7d8ad2d658d92e9f2e4b462fd30b3fc280',
    'r205_runtime.py': '0260ef226fbf9e1c5093f5d3a7fb92c03eea34e63146b92e49601b5648126522',
    'r226_math_runtime.py': '16be022c21dabc7c813038a477857a4db0e3862abaed1717eab06626aec10ed2',
    'orch_r125_continual_guard.py': '1b12ff40ae7d88c06b956cf8c624aa8b010781f66a4eb0f630455f1be5e9dab6',
}


def original_function(filename, name, namespace):
    path = HERE / 'source_evidence' / 'gpu' / filename
    raw = path.read_bytes()
    contract.require(hashlib.sha256(raw).hexdigest() == PINS[filename], 'original_confinement_source_pin')
    node = next(item for item in ast.parse(raw).body if isinstance(item, ast.FunctionDef) and item.name == name)
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), 'exec'), namespace)
    return namespace[name]


class OriginalConfinementTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(dir=HERE)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.config_path = self.root / 'GUARD.json'
        self.config_path.write_text('synthetic CPU binding, not a real admission')
        self.config = dict(attempt_dir=str(self.root), copy_raw=str(self.root / 'raw'),
            plan_path=str(self.root / 'PLAN.json'), plan_sha256='1' * 64, resume=True)
        self.plan = dict(source_root=str(self.root / 'r213_math_b_fork/source_ws6_pending_math_b_test'),
            root='/original/confined/guest/life', physical=2,
            gpu_uuid=contract.ORIGINAL_GPUS['r213_math_b_fork'][1], hard_end_unix=contract.HARD_END)

    def command(self):
        namespace = dict(Path=Path, time=SimpleNamespace(time=lambda: contract.HARD_END - 3600),
            sys=sys, digest=lambda raw: hashlib.sha256(raw).hexdigest(), require=contract.require,
            DEVICE=self.plan['gpu_uuid'], MODULE='gpu.ws6_math_b_pending_entry')
        template = SimpleNamespace(command=original_function('r184_node2_confinement.py', 'command', namespace))
        guard = SimpleNamespace(validate=Mock(return_value=(self.config, self.plan)))
        package = ModuleType('gpu')
        package.r184_node2_confinement, package.orch_r125_continual_guard = template, guard
        namespace = dict(FunctionType=FunctionType, require=contract.require,
            DEVICES={2: (self.plan['gpu_uuid'], '0000:56:00.0')}, MODULE='gpu.ws6_math_b_pending_entry')
        command = original_function('r205_runtime.py', 'contained_command', namespace)
        with patch.dict(sys.modules, gpu=package):
            return command(self.config_path, 'child')

    def test_original_device_and_namespace_controls_preserved(self):
        command = self.command()
        self.assertIn('--property=DevicePolicy=strict', command)
        self.assertIn('--property=NoNewPrivileges=yes', command)
        self.assertIn('--property=CapabilityBoundingSet=', command)
        self.assertIn('--property=User=2524', command)
        self.assertIn('--property=Group=2524', command)
        self.assertIn('--property=DeviceAllow=/dev/nvidia2 rw', command)
        self.assertNotIn('--property=DeviceAllow=/dev/nvidia3 rw', command)
        self.assertIn('--property=BindPaths=' + self.config['copy_raw'] + ':' + self.plan['root'], command)
        self.assertIn('CUDA_VISIBLE_DEVICES=' + self.plan['gpu_uuid'], command)
        self.assertIn('gpu.ws6_math_b_pending_entry', command)

    def test_original_wrapper_ceiling_uses_original_wall(self):
        command = self.command()
        bounded = original_function('r226_math_runtime.py', 'bounded_runtime', {})
        result = bounded(command, contract.HARD_END, contract.HARD_END - 10000)
        changes = [(left, right) for left, right in zip(command, result) if left != right]
        self.assertEqual(len(changes), 1)
        self.assertTrue(changes[0][0].startswith('--property=RuntimeMaxSec='))
        self.assertEqual(changes[0][1], '--property=RuntimeMaxSec=10000')

    def admission(self, scanner_euid=0, clear=True, age=0):
        (self.root / 'DISPATCH_ONCE').mkdir()
        ticks = Path('/proc', str(os.getppid()), 'stat').read_text().rsplit(')', 1)[1].split()[19]
        launch = dict(pid=os.getppid(), parent_start_ticks=ticks, guard_sha256='2' * 64,
            admission_sha256='2' * 64, admission_verified_unix=time.time() - age)
        admission = dict(scanner_euid=scanner_euid, clear=clear, blocking_reasons=[],
            gpu=dict(uuid=self.plan['gpu_uuid']))
        child = SimpleNamespace(require=contract.require, sha=lambda path: '2' * 64,
            read=lambda path: launch if path.name == 'LAUNCH.json' else admission, run=Mock())
        namespace = dict(validate=lambda path: (self.config, self.plan), await_startup=Mock(),
            Path=Path, child=child, os=os, time=time, sys=sys)
        entry = original_function('orch_r125_continual_guard.py', 'native_entry', namespace)
        return entry, child

    def test_nonprivileged_report_never_reaches_native(self):
        entry, child = self.admission(scanner_euid=2524)
        with self.assertRaisesRegex(ValueError, 'fresh_clear_admission'):
            entry(self.config_path)
        child.run.assert_not_called()

    def test_stale_report_never_reaches_native(self):
        entry, child = self.admission(age=130)
        with self.assertRaisesRegex(ValueError, 'fresh_clear_admission'):
            entry(self.config_path)
        child.run.assert_not_called()

    def test_original_guard_is_only_path_into_recovery_run(self):
        entry, child = self.admission()
        with patch.dict(os.environ, CUDA_VISIBLE_DEVICES=self.plan['gpu_uuid']):
            entry(self.config_path)
            self.assertEqual(os.environ['R125_ADMISSION_PLAN_SHA256'], self.config['plan_sha256'])
        child.run.assert_called_once_with(self.config['plan_path'], resume=True)


if __name__ == '__main__':
    unittest.main()
