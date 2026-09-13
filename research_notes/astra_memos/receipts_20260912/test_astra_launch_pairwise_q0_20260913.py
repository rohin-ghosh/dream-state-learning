import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('q0_main_launcher', '/tmp/astra_launch_pairwise_q0_20260913.py')
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


class LauncherTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.source = self.directory / 'source'
        (self.source / 'gpu').mkdir(parents=True)
        self.executor = self.source / 'gpu/astra_pairwise_q0.py'
        self.executor.write_text('CPU fixture only\n')
        self.root = self.directory / 'root'
        self.root.mkdir()
        self.manifest = dict(ready=True, config=dict(gpu_uuid='GPU-fixture-only', lease_cutoff_unix=10000))
        self.pin_manifest()
        self.kwargs = dict(source=self.source, root=self.root, stdout=self.directory/'controller.log',
            executor_sha256=launcher.digest(self.executor), manifest_sha256=launcher.digest(self.root/'manifest.json'), allow_gpu=True)
        self.spawn = patch.object(launcher.subprocess, 'Popen', return_value=SimpleNamespace(pid=55123)).start()
        self.clock = patch.object(launcher.time, 'time', return_value=1000).start()
        self.addCleanup(patch.stopall)

    def pin_manifest(self):
        (self.root/'manifest.json').write_text(json.dumps(self.manifest))
        (self.root/'PREPARED.json').write_text(json.dumps(dict(manifest_sha256=launcher.digest(self.root/'manifest.json'))))

    def reject(self, **changes):
        with self.assertRaises(ValueError):
            launcher.launch(**(self.kwargs | changes))
        self.spawn.assert_not_called()

    def test_detached_command_and_fixed_environment(self):
        result = launcher.launch(**self.kwargs)
        command = self.spawn.call_args.args[0]
        self.assertEqual(command[2:], [str(self.executor), 'execute', '--out', str(self.root), '--allow-gpu'])
        options = self.spawn.call_args.kwargs
        self.assertTrue(options['start_new_session'])
        self.assertEqual(options['cwd'], self.source)
        self.assertEqual(options['env']['CUDA_VISIBLE_DEVICES'], 'GPU-fixture-only')
        self.assertEqual(options['env']['CUBLAS_WORKSPACE_CONFIG'], ':4096:8')
        self.assertEqual(options['env']['PYTHONPATH'], str(self.source))
        self.assertEqual(options['env']['PYTHONHASHSEED'], '0')
        self.assertEqual(options['env']['TOKENIZERS_PARALLELISM'], 'false')
        self.assertEqual(result['status'], 'CONTROLLER_STARTED_NOT_SCIENTIFIC_RESULT')
        self.assertEqual(result['controller_pid'], 55123)

    def test_opt_in(self):
        self.reject(allow_gpu=False)

    def test_relative_source(self):
        self.reject(source='relative')

    def test_executor_drift(self):
        self.executor.write_text('changed')
        self.reject()

    def test_manifest_drift(self):
        (self.root/'manifest.json').write_text('{}')
        self.reject()

    def test_prepared_pin_drift(self):
        (self.root/'PREPARED.json').write_text('{"manifest_sha256":"wrong"}')
        self.reject()

    def test_not_ready(self):
        self.manifest['ready'] = False
        self.pin_manifest()
        self.reject(manifest_sha256=launcher.digest(self.root/'manifest.json'))

    def test_started_or_sealed_root(self):
        (self.root/'STARTED.json').write_text('{}')
        self.reject()

    def test_existing_stdout(self):
        self.kwargs['stdout'].write_text('preserve')
        self.reject()
        self.assertEqual(self.kwargs['stdout'].read_text(), 'preserve')

    def test_stdout_in_run(self):
        self.reject(stdout=self.root/'log')

    def test_symlink_stdout(self):
        self.kwargs['stdout'].symlink_to(self.directory/'absent')
        self.reject()

    def test_insufficient_lease_window(self):
        self.clock.return_value = 7300
        self.reject()


if __name__ == '__main__':
    unittest.main()
