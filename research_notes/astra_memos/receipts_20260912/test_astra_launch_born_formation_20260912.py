import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from gpu import astra_mini_sudoku_diagnostic as vacancy


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


launcher = load('/tmp/astra_launch_born_formation_20260912.py', 'born_formation_launcher_test_target')
driver = load('/tmp/astra_born_rulegame_formation_run_20260912.py', 'born_formation_launcher_test_driver')


class LauncherTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.root = self.base / 'formation'
        self.root.mkdir()
        self.cpu = self.base / 'cpu.log'
        self.cpu.write_text('Ran 27 tests in 1.0s\n\nOK\n')
        self.args = SimpleNamespace(allow_gpu=True, driver_sha256=launcher.digest(launcher.DRIVER),
            phase='formation', root=self.root, plan_sha256='a'*64, native_cpu_log=self.cpu, native_test_count=27,
            stdout=self.base/'stdout.log', mode='_run')
        self.plan = dict(phase='formation', python=os.path.abspath(sys.executable), controller_seconds=900,
            deadline=time.time()+10000, lease_cutoff=time.time()+20000, source_root=str(self.base),
            model=str(self.base/'model'), sidecar_sha256=self.args.driver_sha256, device='0')
        self.process = Mock(pid=55001)
        self.process.wait.return_value = 0
        self.free = Mock(return_value=({'gpu_uuid':'GPU-CPU-FIXTURE'}, '<gpu/>'))

    def invoke(self):
        loader = SimpleNamespace(create_module=lambda spec: None,
            exec_module=lambda module: module.__dict__.update(driver.__dict__))
        spec = importlib.util.spec_from_loader('mock_native_born_formation_driver', loader)
        with patch.object(launcher.importlib.util, 'spec_from_file_location', return_value=spec), \
             patch.object(driver, 'checked_plan', return_value=(self.root, self.plan, None, None)), \
             patch.object(vacancy, 'check_free', self.free), \
             patch.object(launcher.subprocess, 'Popen', return_value=self.process) as popen, \
             patch.object(launcher.os, 'getpgid', return_value=55001), \
             patch.object(launcher.os, 'getsid', side_effect=lambda pid: 55001 if pid else 44001):
            launcher.run(self.args)
            return popen

    def test_actual_launch_and_exit_contract(self):
        popen = self.invoke()
        logs = self.root.with_name(self.root.name+'_launch')
        receipt = driver.read(logs/'launch.json')
        expected = driver.launch_contract(self.root, self.plan, self.args.plan_sha256,
            launcher.SELF, launcher.digest(launcher.SELF))
        for name, value in expected.items():
            self.assertEqual(receipt[name], value)
        self.assertEqual(set(receipt), set(expected) | {'pid', 'pgid', 'session',
            'launcher_pid', 'launcher_pgid', 'launcher_session', 'started_wall', 'gpu_uuid'})
        exited = driver.read(logs/'exit.json')
        self.assertEqual(exited['launch_sha256'], launcher.digest(logs/'launch.json'))
        self.assertEqual(exited['returncode'], 0)
        self.assertEqual(set(exited), {'launch_sha256', 'returncode', 'ended_wall'})
        self.assertEqual(popen.call_args.args[0], receipt['command'])
        self.assertTrue(popen.call_args.kwargs['start_new_session'])
        self.assertEqual(popen.call_args.kwargs['env']['CUDA_VISIBLE_DEVICES'], '0')
        self.assertEqual(self.process.wait.call_count, 1)

    def test_preflight_window_rechecked(self):
        clock = [self.plan['deadline']-1201]
        def slow(device):
            clock[0] += 2
            return {'gpu_uuid':'GPU-CPU-FIXTURE'}, '<gpu/>'
        self.free.side_effect = slow
        with patch.object(launcher.time,'time',side_effect=lambda:clock[0]), self.assertRaisesRegex(ValueError,'preflight'):
            self.invoke()
        self.process.wait.assert_not_called()

    def test_opt_in_required(self):
        self.args.allow_gpu = False
        with self.assertRaisesRegex(ValueError,'opt-in'):
            self.invoke()
        self.free.assert_not_called()

    def test_changed_driver_rejected(self):
        self.args.driver_sha256 = '0'*64
        with self.assertRaisesRegex(ValueError,'frozen driver'):
            self.invoke()

    def test_failed_native_tests_rejected(self):
        self.cpu.write_text('Ran 27 tests\nFAILED\n')
        with self.assertRaisesRegex(ValueError,'CPU'):
            self.invoke()
        self.free.assert_not_called()

    def test_existing_launch_preserved(self):
        self.root.with_name(self.root.name+'_launch').mkdir()
        with self.assertRaisesRegex(ValueError,'existing'):
            self.invoke()
        self.free.assert_not_called()

    def test_vacancy_failure_prevents_spawn(self):
        self.free.side_effect = ValueError('occupied')
        with self.assertRaisesRegex(ValueError,'occupied'):
            self.invoke()
        self.process.wait.assert_not_called()

    def test_wrong_phase_rejected(self):
        self.args.phase = 'readout'
        with self.assertRaisesRegex(ValueError,'phase'):
            self.invoke()

    def test_start_detaches_launcher_without_claiming_gpu(self):
        self.args.mode = 'start'
        with patch.object(launcher,'arguments',return_value=self.args), \
             patch.object(launcher.sys,'argv',[str(launcher.SELF),'start','--phase','formation']), \
             patch.object(launcher.subprocess,'Popen',return_value=self.process) as popen:
            launcher.main()
        self.assertEqual(popen.call_args.args[0][3], '_run')
        self.assertTrue(popen.call_args.kwargs['start_new_session'])
        self.assertNotIn('CUDA_VISIBLE_DEVICES',popen.call_args.kwargs['env'])
        self.process.wait.assert_not_called()


if __name__ == '__main__':
    unittest.main()
