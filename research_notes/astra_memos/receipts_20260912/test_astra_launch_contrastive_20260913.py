import importlib.util
import json
import os
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


specification = importlib.util.spec_from_file_location('launch_test', '/tmp/astra_launch_contrastive_20260913.py')
launch = importlib.util.module_from_spec(specification)
specification.loader.exec_module(launch)


class LaunchTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name) / 'run'
        self.root.mkdir()
        self.plan = dict(gpu_index=0, gpu_uuid='GPU-fixture', lease_end=time.time() + 100000)
        self.probe = SimpleNamespace(gpu_state=Mock(return_value=True))
        def write(path, value):
            with path.open('x') as stream:
                json.dump(value, stream)
        self.runtime = SimpleNamespace(offline=Mock(), verify=Mock(return_value=(self.plan, self.probe)), write=write)
        patches = [patch.object(launch, 'ROOT', self.root),
                   patch.object(launch, 'LOG', Path(self.directory.name) / 'log'),
                   patch.object(launch.importlib.util, 'module_from_spec', return_value=self.runtime),
                   patch.object(launch.importlib.util, 'spec_from_file_location', return_value=SimpleNamespace(loader=SimpleNamespace(exec_module=Mock())))]
        for item in patches:
            item.start()
            self.addCleanup(item.stop)

    def test_success_is_one_shot(self):
        with patch.object(launch.subprocess, 'run', return_value=SimpleNamespace(stdout='{}')) as precheck, patch.object(launch.subprocess, 'Popen', return_value=SimpleNamespace(pid=os.getpid())) as process:
            launch.launch()
            with self.assertRaises(FileExistsError):
                launch.launch()
            self.assertEqual(process.call_count, 1)
            self.assertEqual(precheck.call_count, 1)
            self.assertTrue(process.call_args.kwargs['start_new_session'])
            self.assertEqual(process.call_args.kwargs['env']['CUDA_VISIBLE_DEVICES'], '')

    def test_occupied_never_launches(self):
        self.probe.gpu_state.return_value = False
        with patch.object(launch.subprocess, 'run', return_value=SimpleNamespace(stdout='{}')), patch.object(launch.subprocess, 'Popen') as process:
            with self.assertRaises(ValueError):
                launch.launch()
            process.assert_not_called()

    def test_existing_run_never_prechecks(self):
        (self.root / 'controller_started.json').touch()
        with patch.object(launch.subprocess, 'run') as precheck:
            with self.assertRaises(ValueError):
                launch.launch()
            precheck.assert_not_called()

    def test_lease_failure_never_launches(self):
        self.plan['lease_end'] = time.time()
        with patch.object(launch.subprocess, 'run', return_value=SimpleNamespace(stdout='{}')), patch.object(launch.subprocess, 'Popen') as process:
            with self.assertRaises(ValueError):
                launch.launch()
            process.assert_not_called()


if __name__ == '__main__':
    unittest.main()
