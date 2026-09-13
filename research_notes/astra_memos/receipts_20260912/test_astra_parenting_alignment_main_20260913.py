import importlib.util
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


specification = importlib.util.spec_from_file_location('alignment_main_tested', '/tmp/astra_parenting_alignment_main_20260913.py')
main = importlib.util.module_from_spec(specification)
specification.loader.exec_module(main)


class HolderTests(unittest.TestCase):
    def invoke(self, controller_code, collector_code=0):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            (base / 'seed0_prepared.json').write_text(json.dumps({'plan_sha256': 'plan'}))
            controller = SimpleNamespace(pid=12345, wait=Mock(return_value=controller_code))
            collector = SimpleNamespace(pid=12346, wait=Mock(return_value=collector_code))
            with patch.object(main, 'BASE', base), patch.object(main, 'runtime'), patch.object(main.previous, 'digest', return_value='completion'):
                with patch.object(main.previous, 'write') as write, patch.object(main.subprocess, 'Popen', side_effect=[controller, collector]) as popen:
                    with patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES': main.GPUS[0]}):
                        with self.assertRaises(SystemExit) as exited:
                            main.hold(0, 'runner')
                        self.assertEqual(os.environ['CUDA_VISIBLE_DEVICES'], main.GPUS[0])
                    return exited.exception.code, popen.call_args_list, write.call_args_list

    def test_collect_once_after_success_with_empty_cuda_children(self):
        code, calls, writes = self.invoke(0)
        self.assertEqual(code, 0)
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0].args[0][3], 'controller')
        self.assertEqual(calls[1].args[0][3], 'collect')
        for call in calls:
            self.assertEqual(call.kwargs['env']['CUDA_VISIBLE_DEVICES'], '')
            self.assertTrue(call.kwargs['start_new_session'])
        names = [call.args[0].name for call in writes]
        self.assertLess(names.index('controller_exit.json'), names.index('collector.json'))
        self.assertEqual(names.count('collector.json'), 1)

    def test_controller_failure_never_collects_or_retries(self):
        code, calls, writes = self.invoke(9)
        self.assertEqual(code, 9)
        self.assertEqual(len(calls), 1)
        self.assertNotIn('collector.json', [call.args[0].name for call in writes])
        self.assertEqual(writes[-1].args[1]['returncode'], 9)

    def test_collector_failure_propagates_without_retry(self):
        code, calls, writes = self.invoke(0, 7)
        self.assertEqual(code, 7)
        self.assertEqual(len(calls), 2)
        self.assertEqual(writes[-1].args[1]['returncode'], 7)

    def test_distinct_seed_roots_and_invalid_seed_rejected(self):
        self.assertEqual(len({main.root_for(seed) for seed in range(3)}), 3)
        self.assertEqual(len(set(main.GPUS.values())), 3)
        for seed in (True, -1, 3, '0'):
            with self.assertRaises(AssertionError):
                main.root_for(seed)

    def test_runner_pin_checked_before_module_execution(self):
        with patch.object(main.previous, 'digest', return_value='actual'), patch.object(main.previous.importlib.util, 'spec_from_file_location') as loader:
            with self.assertRaises(AssertionError):
                main.runtime('incorrect')
            loader.assert_not_called()


if __name__ == '__main__':
    unittest.main()
