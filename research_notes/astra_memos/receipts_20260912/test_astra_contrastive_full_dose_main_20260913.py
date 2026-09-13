import importlib.util
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


specification = importlib.util.spec_from_file_location('contrastive_main_tested', '/tmp/astra_contrastive_full_dose_main_20260913.py')
main = importlib.util.module_from_spec(specification)
specification.loader.exec_module(main)


class LauncherTests(unittest.TestCase):
    def test_holder_keeps_reservation_and_starts_independent_controller_group(self):
        candidate = SimpleNamespace(read=Mock(return_value={'plan_sha256': 'plan'}), write=Mock())
        process = SimpleNamespace(pid=12345, wait=Mock(return_value=0))
        with patch.object(main, 'runtime', return_value=candidate), patch.object(main.subprocess, 'Popen', return_value=process) as popen:
            with patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES': main.GPUS[1]}):
                with self.assertRaises(SystemExit) as exited:
                    main.hold(1, 'source')
                self.assertEqual(os.environ['CUDA_VISIBLE_DEVICES'], main.GPUS[1])
        self.assertEqual(exited.exception.code, 0)
        self.assertTrue(popen.call_args.kwargs['start_new_session'])
        self.assertEqual(popen.call_args.kwargs['env']['CUDA_VISIBLE_DEVICES'], '')
        self.assertEqual(candidate.write.call_args_list[0].args[1]['pgid'], process.pid)
        self.assertEqual(candidate.write.call_args_list[-1].args[1]['returncode'], 0)

    def test_holder_rejects_wrong_uuid_before_starting_controller(self):
        candidate = SimpleNamespace(read=Mock(), write=Mock())
        with patch.object(main, 'runtime', return_value=candidate), patch.object(main.subprocess, 'Popen') as popen:
            with patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES': main.GPUS[0]}):
                with self.assertRaises(AssertionError):
                    main.hold(1, 'source')
        popen.assert_not_called()
        candidate.read.assert_not_called()

    def test_prepare_checks_expected_work_before_accepting_receipt(self):
        candidate = SimpleNamespace(digest=Mock(return_value='spec'), prepare=Mock(return_value={
            'status': 'PREPARED_NOT_GPU_APPROVAL', 'budget': {'updates': 12, 'calls': 96}}), write=Mock())
        with patch.object(main, 'runtime', return_value=candidate):
            with self.assertRaises(AssertionError):
                main.prepare(0, 'source')
        candidate.write.assert_not_called()
        self.assertTrue(candidate.prepare.call_args.kwargs['allow_native'])
        self.assertEqual(Path(candidate.prepare.call_args.args[0]).name, 'contrastive_full_dose_seed0_20260913_attempt1')


if __name__ == '__main__':
    unittest.main()
