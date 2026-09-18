import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock


class LauncherTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).with_name('ACTIVATION3_MAIN_EXECUTION.py')
        spec = importlib.util.spec_from_file_location('activation3_launcher', path)
        self.launcher = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.launcher)
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.launcher.BASE = self.base
        self.launcher.SOURCE_PINS = {name: hashlib.sha256(name.encode()).hexdigest()
                                     for name in self.launcher.SOURCE_PINS}
        self.roots = []
        for agent in self.launcher.PINS:
            root = self.base / ('orch_r166_retelling_' + agent + '_20260917_activation3')
            self.roots.append(root)
            (root / 'readiness').mkdir(parents=True)
            for relative in self.launcher.SOURCE_PINS:
                target = root / 'source' / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(relative)
            ready = root / 'readiness/READY.json'
            ready.write_text(json.dumps(dict(required_GO_binding=dict(agent=agent, hard_end_unix=1789776000))))
            self.launcher.PINS[agent] = self.launcher.sha(ready)
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(self.launcher.socket, 'gethostname', return_value='[REDACTED_HOST]'))
        self.stack.enter_context(patch.object(self.launcher.time, 'time', return_value=1789634000.0))
        self.stack.enter_context(contextlib.redirect_stdout(io.StringIO()))

    def test_preparation_is_create_only_and_never_launches(self):
        with patch.object(self.launcher.subprocess, 'Popen') as launch:
            self.launcher.main('prepare-go')
            self.assertEqual(len(list(self.base.rglob('MAIN_GO.json'))), 4)
            self.assertRaises(ValueError, self.launcher.main, 'prepare-go')
            launch.assert_not_called()
        for root in self.roots:
            go = json.loads((root / 'MAIN_GO.json').read_text())
            self.assertEqual(go['expires_unix'] - go['not_before_unix'], 1800)

    def test_missing_fourth_pin_blocks_entire_batch_before_GO(self):
        (self.roots[-1] / 'source/tests/test_orch_r166_corrected_retelling.py').unlink()
        self.assertRaises(FileNotFoundError, self.launcher.main, 'prepare-go')
        self.assertFalse(list(self.base.rglob('MAIN_GO.json')))

    def test_invalid_last_GO_prevents_all_dispatch(self):
        self.launcher.main('prepare-go')
        target = self.roots[-1] / 'MAIN_GO.json'
        target.chmod(0o644)
        go = json.loads(target.read_text())
        go['issuer'] = 'other'
        target.write_text(json.dumps(go))
        with patch.object(self.launcher.subprocess, 'Popen') as launch:
            self.assertRaises(ValueError, self.launcher.main, 'dispatch')
            launch.assert_not_called()
        self.assertFalse(list(self.base.rglob('MAIN_DISPATCH_INTENT.json')))

    def test_detached_dispatch_uses_only_exact_successor_and_rejects_retry(self):
        self.launcher.main('prepare-go')
        with patch.object(self.launcher.subprocess, 'Popen', return_value=Mock(pid=os.getpid())) as launch:
            self.launcher.main('dispatch')
            self.assertEqual(launch.call_count, 4)
            for call, root in zip(launch.call_args_list, self.roots):
                self.assertEqual(call.kwargs['cwd'], root / 'source')
                self.assertEqual(call.kwargs['env']['PYTHONPATH'], str(root / 'source'))
                self.assertEqual(call.kwargs['env']['CUDA_VISIBLE_DEVICES'], '')
                self.assertTrue(call.kwargs['start_new_session'])
                self.assertEqual(call.args[0][-3], str(root / 'MAIN_GO.json'))
            self.assertRaises(ValueError, self.launcher.main, 'dispatch')
            self.assertEqual(launch.call_count, 4)

    def test_uncertain_dispatch_preserves_intent_and_blocks_retry(self):
        self.launcher.main('prepare-go')
        with patch.object(self.launcher.subprocess, 'Popen', side_effect=OSError('uncertain')) as launch:
            self.assertRaises(OSError, self.launcher.main, 'dispatch')
            self.assertTrue((self.roots[0] / 'MAIN_DISPATCH_INTENT.json').exists())
            self.assertRaises(ValueError, self.launcher.main, 'dispatch')
            self.assertEqual(launch.call_count, 1)

    def test_invalid_GO_times_and_binding_fail(self):
        binding = dict(hard_end_unix=1789776000)
        go = dict(schema='R166_SAVED_BOUNDARY_MAIN_GO_V1', issuer='Main', decision='GO',
                  binding=binding, not_before_unix=1789634000.0, expires_unix=1789635800.0)
        for delta in (dict(expires_unix=float('nan')), dict(not_before_unix=True),
                      dict(expires_unix=1789635801.0), dict(expires_unix=1789634000.0),
                      dict(binding={})):
            with self.subTest(delta=delta):
                self.assertRaises(ValueError, self.launcher.validate_go, dict(go, **delta), binding)


if __name__ == '__main__':
    unittest.main()
