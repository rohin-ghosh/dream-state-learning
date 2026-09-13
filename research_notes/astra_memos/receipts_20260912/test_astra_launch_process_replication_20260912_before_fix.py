"""Frozen Main launcher argparse/custody tests. CPU fixtures; Popen never executes."""
from contextlib import ExitStack
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.dont_write_bytecode = True
sys.path.insert(0, '/tmp')
import test_astra_process_replication_collectors_20260912 as fixtures
from gpu import astra_mini_sudoku_diagnostic as gpu_check

LAUNCHER = Path('/tmp/astra_launch_process_replication_20260912.py')
LAUNCHER_SHA = '0539d5eb8ae6c0c71b14fc80ce461d08d78e37993b544af7b07ae119e34688ce'
assert hashlib.sha256(LAUNCHER.read_bytes()).hexdigest() == LAUNCHER_SHA
spec = importlib.util.spec_from_file_location('tested_main_replication_launcher', LAUNCHER)
launcher = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = launcher
spec.loader.exec_module(launcher)
collector, replica = fixtures.collector, fixtures.replica


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.scenario = fixtures.CollectorTests()
        self.scenario.setUp()
        self.addCleanup(self.scenario.doCleanups)
        self.fixture = self.scenario.fixture
        self.logs = {
            Path('/tmp/astra_process_replication_native_cpu_20260912.log'): 'Ran 27 tests in 1.0s\n\nOK\n',
            Path('/tmp/astra_process_replication_collectors_native_cpu_20260912.log'): 'Ran 19 tests in 1.0s\n\nOK\n'}
        self.original_read_text, self.original_read_bytes = Path.read_text, Path.read_bytes
        self.seed, self.phase, self.previous = 0, 'write', None
        self.last_command = None
        self.popen = Mock(return_value=SimpleNamespace(pid=88001))
        self.free = Mock(return_value=(self.scenario.gpu, self.scenario.xml))
        self.source_override = None

    def prepare(self, phase='write', seed=0):
        self.phase, self.seed, self.previous = phase, seed, None
        if phase == 'write':
            self.fixture.prepare_write(seed)
            self.root, self.pin = self.fixture.write_root, self.fixture.prepared_write['plan_sha256']
        else:
            config = self.scenario.write_fixture(seed)
            self.scenario.invoke(config, 'finish')
            self.previous = config['out']/'validation.json'
            self.fixture.prepare_readout()
            self.root, self.pin = self.fixture.readout_root, self.fixture.prepared_readout['plan_sha256']
        self.plan = collector.read(self.root/'plan.json')
        self.launch_root = self.root.with_name(self.root.name+'_launch')

    def args(self):
        result = [self.phase, '--fit-seed', str(self.seed), '--root', str(self.root),
                  '--plan-sha256', self.pin, '--allow-gpu']
        if self.previous is not None:
            result += ['--write-release', str(self.previous), '--write-release-sha256', collector.digest(self.previous)]
        return result

    def invoke(self, argv=None):
        source = Path(self.source_override or self.plan['source_root'])
        testcase = self
        class NativeHome:
            def __truediv__(self, component):
                testcase.assertEqual(component, 'astra_sources')
                return NativeSources()
        class NativeSources:
            def __truediv__(self, component):
                testcase.assertEqual(component, '4c3064c1c3eef068951e9c3b2ca46630754564e7')
                return source
        class FixturePath:
            def __new__(cls, *args):
                return Path(*args)
            @staticmethod
            def home():
                return NativeHome()
        def read_text(path, *args, **kwargs):
            if path in self.logs:
                if self.logs[path] is None:
                    raise FileNotFoundError(str(path))
                return self.logs[path]
            return self.original_read_text(path, *args, **kwargs)
        def read_bytes(path):
            if path in self.logs:
                if self.logs[path] is None:
                    raise FileNotFoundError(str(path))
                return self.logs[path].encode()
            return self.original_read_bytes(path)
        def load(path, expected, name):
            self.assertEqual(launcher.digest(path), expected)
            if path == launcher.DRIVER:
                self.assertEqual(expected, launcher.DRIVER_SHA)
                return replica
            self.assertEqual(path, launcher.COLLECTOR)
            self.assertEqual(expected, launcher.COLLECTOR_SHA)
            return collector
        with ExitStack() as stack:
            stack.enter_context(patch.object(launcher, 'Path', FixturePath))
            stack.enter_context(patch.object(launcher, 'load', side_effect=load))
            stack.enter_context(patch.object(Path, 'read_text', read_text))
            stack.enter_context(patch.object(Path, 'read_bytes', read_bytes))
            stack.enter_context(patch.object(gpu_check, 'check_free', self.free))
            stack.enter_context(patch.object(launcher.subprocess, 'Popen', self.popen))
            stack.enter_context(patch.object(launcher.os, 'getpgid', return_value=88001))
            stack.enter_context(patch.object(sys, 'argv', [str(LAUNCHER)]+(self.args() if argv is None else argv)))
            output = stack.enter_context(patch('sys.stdout', new=io.StringIO()))
            launcher.main()
        return json.loads(output.getvalue())

    def validate_launch(self, printed):
        receipt = collector.read(self.launch_root/'launch.json')
        self.assertEqual(printed, dict(receipt, launch_sha256=collector.digest(self.launch_root/'launch.json')))
        self.assertEqual(receipt['pid'], receipt['pgid'])
        self.assertFalse(receipt['automatic_next_phase'])
        self.assertEqual(receipt['collector_sha256'], launcher.COLLECTOR_SHA)
        for path, text in self.logs.items():
            self.assertEqual(receipt['native_cpu_sha256'][path.name], hashlib.sha256(text.encode()).hexdigest())
        config = dict(phase=self.phase, fit_seed=self.seed, root=self.root, plan_sha256=self.pin,
            launch_root=self.launch_root, launch_sha256=collector.digest(self.launch_root/'launch.json'),
            launcher=LAUNCHER, launcher_sha256=LAUNCHER_SHA, out=self.root.with_name(self.root.name+'_collection'))
        if self.previous is not None:
            config.update(write_release=self.previous, write_release_sha256=collector.digest(self.previous))
        config = collector.settings(config)
        runner, phase, checked, previous = collector.bind(config, receipt)
        self.assertEqual(checked[0], self.root)
        self.assertEqual(phase.fit_seed, self.seed)
        self.assertEqual(previous is not None, self.phase == 'readout')
        observed = collector.status(config)
        self.assertFalse(observed['ready'])
        command, kwargs = self.popen.call_args.args[0], self.popen.call_args.kwargs
        self.assertEqual(command, receipt['command'])
        self.assertEqual(command[:3], [os.path.abspath(sys.executable), '-B', str(launcher.DRIVER)])
        self.assertEqual(kwargs['cwd'], Path(self.plan['source_root']))
        self.assertTrue(kwargs['start_new_session'])
        for key in ('CUDA_VISIBLE_DEVICES', 'HF_HUB_OFFLINE', 'TRANSFORMERS_OFFLINE', 'PYTHONDONTWRITEBYTECODE'):
            self.assertEqual(kwargs['env'][key], '2' if key == 'CUDA_VISIBLE_DEVICES' else '1')
        action = 'write_pair' if self.phase == 'write' else 'evaluate'
        method = Mock(return_value={'parser_dispatch_only': True})
        target = SimpleNamespace(**{action: method})
        class_name = 'WritePhase' if self.phase == 'write' else 'ReadoutPhase'
        with patch.object(replica, class_name, return_value=target) as factory, patch('sys.stdout', new=io.StringIO()):
            replica.main(command[3:])
        factory.assert_called_once_with(self.seed)
        method.assert_called_once_with(str(self.root), self.pin, True)
        return receipt

    def test_actual_write_parser_dispatch_and_collector_bind_both_seeds(self):
        for seed in (0, 1):
            self.prepare('write', seed)
            self.popen.reset_mock()
            receipt = self.validate_launch(self.invoke())
            self.assertEqual(receipt['controller_seconds'], 1200)
            self.assertEqual(receipt['arms'], ['P', 'A'])
            self.popen.assert_called_once()

    def test_actual_readout_parser_prior_release_keys_and_collector_bind_both_seeds(self):
        original = collector.write_release
        for seed in (0, 1):
            self.prepare('readout', seed)
            self.popen.reset_mock()
            calls = []
            def binding(config, plan, receipt):
                self.assertEqual(config['root'], self.root)
                self.assertEqual(config['launch_root'], self.launch_root)
                self.assertEqual(config['fit_seed'], seed)
                calls.append(config)
                return original(config, plan, receipt)
            with patch.object(collector, 'write_release', side_effect=binding):
                receipt = self.validate_launch(self.invoke())
            self.assertGreaterEqual(len(calls), 2)
            self.assertEqual(receipt['controller_seconds'], 1800)
            self.assertEqual(receipt['cells'], ['OFF', 'P_ON', 'A_ON'])
            self.popen.assert_called_once()

    def test_opt_in_and_parser_required_arguments_fail_before_popen(self):
        self.prepare()
        args = self.args()
        with self.assertRaisesRegex(ValueError, 'opt-in'):
            self.invoke([arg for arg in args if arg != '--allow-gpu'])
        for flag in ('--root', '--plan-sha256', '--fit-seed'):
            position = args.index(flag)
            with patch('sys.stderr', new=io.StringIO()), self.assertRaises(SystemExit) as stopped:
                self.invoke(args[:position]+args[position+2:])
            self.assertEqual(stopped.exception.code, 2)
        self.popen.assert_not_called()
        self.free.assert_not_called()

    def test_missing_or_wrong_readout_release_rejected(self):
        self.prepare('readout')
        args = self.args()
        for flag in ('--write-release', '--write-release-sha256'):
            position = args.index(flag)
            with self.subTest(missing=flag), self.assertRaisesRegex(ValueError, 'write release required'):
                self.invoke(args[:position]+args[position+2:])
        wrong = list(args)
        wrong[wrong.index('--write-release-sha256')+1] = '0'*64
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            self.invoke(wrong)
        self.popen.assert_not_called()
        self.assertFalse(self.launch_root.exists())

    def test_wrong_seed_or_incomplete_write_release_rejected(self):
        self.prepare('readout')
        original = collector.read(self.previous)
        for changed in (dict(original, fit_seed=1), dict(original, full_release=False),
                        dict(original, aggregate_available=False), dict(original, phase_within_bound=False),
                        dict(original, plan_sha256='0'*64)):
            self.scenario.replace(self.previous, changed)
            with self.assertRaisesRegex(ValueError, 'not complete/bounded/same-seed'):
                self.invoke()
        self.popen.assert_not_called()

    def test_write_rejects_prior_release_flags(self):
        self.prepare()
        for extra in (['--write-release', '/irrelevant'], ['--write-release-sha256', '0'*64]):
            with self.assertRaisesRegex(ValueError, 'write cannot use prior release'):
                self.invoke(self.args()+extra)
        self.popen.assert_not_called()

    def test_initial_window_rejects_controller_without_collection_margin(self):
        self.prepare()
        self.plan['deadline'] = time.time()+1450
        self.pin = self.fixture.reseal_plan(self.root, self.plan)
        with self.assertRaisesRegex(ValueError, 'controller and collection window'):
            self.invoke()
        self.free.assert_not_called()
        self.popen.assert_not_called()

    def test_window_rechecked_after_slow_preflight_before_popen(self):
        self.prepare()
        clock = [self.plan['deadline']-1501]
        def slow_free(device):
            clock[0] += 2
            return self.scenario.gpu, self.scenario.xml
        self.free.side_effect = slow_free
        with patch.object(launcher.time, 'time', side_effect=lambda: clock[0]), \
             self.assertRaisesRegex(ValueError, 'window'):
            self.invoke()
        self.popen.assert_not_called()

    def test_preexisting_run_and_launch_refused(self):
        self.prepare()
        (self.root/'run').mkdir()
        with self.assertRaisesRegex(ValueError, 'existing run or launch'):
            self.invoke()
        self.prepare(seed=1)
        self.launch_root.mkdir()
        with self.assertRaisesRegex(ValueError, 'existing run or launch'):
            self.invoke()
        self.popen.assert_not_called()

    def test_missing_or_wrong_native_logs_refused_without_reading_live_logs(self):
        self.prepare()
        for path in self.logs:
            original = self.logs[path]
            for bad in ('Ran 16 tests\nOK\n', original.replace('OK', 'FAILED'), None):
                self.logs[path] = bad
                with self.subTest(log=path.name, content=bad), self.assertRaises((ValueError, FileNotFoundError)):
                    self.invoke()
            self.logs[path] = original
        self.free.assert_not_called()
        self.popen.assert_not_called()

    def test_source_and_device_mismatch_refused(self):
        self.prepare()
        self.source_override = str(self.fixture.fixture.root/'wrong_source')
        with self.assertRaisesRegex(ValueError, 'source/device differs'):
            self.invoke()
        self.source_override = None
        self.plan['device'] = '1'
        self.pin = self.fixture.reseal_plan(self.root, self.plan)
        with self.assertRaisesRegex(ValueError, 'source/device differs'):
            self.invoke()
        self.popen.assert_not_called()

    def test_gpu_refusal_never_spawns_and_historical_bytes_unchanged(self):
        self.prepare()
        self.free.side_effect = RuntimeError('mock occupied GPU')
        with self.assertRaisesRegex(RuntimeError, 'occupied GPU'):
            self.invoke()
        self.popen.assert_not_called()
        self.assertEqual(launcher.digest(LAUNCHER), LAUNCHER_SHA)
        self.assertEqual(launcher.digest(launcher.DRIVER), launcher.DRIVER_SHA)
        self.assertEqual(launcher.digest(launcher.COLLECTOR), launcher.COLLECTOR_SHA)


if __name__ == '__main__':
    unittest.main()
