from contextlib import redirect_stdout
import importlib.util
import io
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import orch_r167_object_survival_eval as evaluator
from gpu import orch_r130_benchmark_sidecar as sidecar


spec = importlib.util.spec_from_file_location('r167_launcher', Path(__file__).with_name('launch.py'))
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.go = self.root / 'synthetic_GO.json'
        evaluator.write(self.go, {'synthetic': True})
        self.directory = self.root / 'dispatch'

    def arguments(self, action):
        return [str(Path(launcher.__file__)), action, '--config', str(self.root / 'config'), '--go', str(self.go),
                '--go-sha256', evaluator.sha(self.go), '--source', str(self.root), '--directory', str(self.directory)]

    def test_start_is_detached_no_admission_in_initiator(self):
        with patch.object(sys, 'argv', self.arguments('start')), patch.object(evaluator, 'validate'), \
             patch.object(sidecar, 'identity', return_value={'pid': 12}), \
             patch.object(launcher.subprocess, 'Popen', return_value=SimpleNamespace(pid=12)) as popen, \
             patch.object(evaluator, 'dispatch') as dispatch, redirect_stdout(io.StringIO()):
            launcher.main()
        command = popen.call_args.args[0]
        self.assertEqual(command[3], 'worker')
        self.assertTrue(popen.call_args.kwargs['close_fds'])
        self.assertTrue(popen.call_args.kwargs['start_new_session'])
        dispatch.assert_not_called()
        self.assertTrue((self.directory / 'INITIATOR.json').exists())

    def test_worker_refuses_live_initiator(self):
        self.directory.mkdir()
        evaluator.write(self.directory / 'INITIATOR.json', dict(identity={'pid': 12}))
        with patch.object(sys, 'argv', self.arguments('worker')), patch.object(evaluator, 'validate'), \
             patch.object(sidecar, 'gone', return_value=False), patch.object(launcher.time, 'sleep') as sleep, \
             patch.object(evaluator, 'dispatch') as dispatch:
            with self.assertRaises(AssertionError):
                launcher.main()
        sleep.assert_called_once_with(5)
        dispatch.assert_not_called()

    def test_worker_one_dispatch_after_release(self):
        self.directory.mkdir()
        evaluator.write(self.directory / 'INITIATOR.json', dict(identity={'pid': 12}))
        with patch.object(sys, 'argv', self.arguments('worker')), patch.object(evaluator, 'validate'), \
             patch.object(sidecar, 'gone', return_value=True), patch.object(launcher.time, 'sleep'), \
             patch.object(sidecar, 'identity', return_value={'pid': 13}), \
             patch.object(evaluator, 'dispatch', return_value={'status': 'METADATA_ONLY'}) as dispatch:
            launcher.main()
        dispatch.assert_called_once()
        self.assertEqual(evaluator.read(self.directory / 'DISPOSITION.json')['status'], 'METADATA_ONLY')


if __name__ == '__main__':
    unittest.main()
