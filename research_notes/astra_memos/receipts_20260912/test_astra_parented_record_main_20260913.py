import importlib.util
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


specification = importlib.util.spec_from_file_location('parented_main_tested', '/tmp/astra_parented_record_main_20260913.py')
main = importlib.util.module_from_spec(specification)
specification.loader.exec_module(main)


class HolderTests(unittest.TestCase):
    def invoke(self, controller_code):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            (base / 'seed0_prepared.json').write_text(json.dumps({'plan_sha256': 'plan'}))
            controller = SimpleNamespace(pid=12345, wait=Mock(return_value=controller_code))
            collector = SimpleNamespace(pid=12346, wait=Mock(return_value=0))
            with patch.object(main, 'BASE', base), patch.object(main, 'runtime'), patch.object(main.previous, 'digest', return_value='completion'):
                with patch.object(main.previous, 'write') as write, patch.object(main.subprocess, 'Popen', side_effect=[controller, collector]) as popen:
                    with patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES': main.GPUS[0][1]}):
                        with self.assertRaises(SystemExit) as exited:
                            main.hold(0)
                        self.assertEqual(os.environ['CUDA_VISIBLE_DEVICES'], main.GPUS[0][1])
                    return exited.exception.code, popen.call_args_list, write.call_args_list

    def test_collect_once_after_success_with_separate_empty_cuda_processes(self):
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
        self.assertEqual(writes[-1].args[1]['returncode'], 0)

    def test_controller_failure_never_collects_or_retries(self):
        code, calls, writes = self.invoke(9)
        self.assertEqual(code, 9)
        self.assertEqual(len(calls), 1)
        self.assertNotIn('collector.json', [call.args[0].name for call in writes])
        self.assertEqual(writes[-1].args[1]['returncode'], 9)


if __name__ == '__main__':
    unittest.main()
